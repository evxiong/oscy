"""
Functions for interacting with database.

As a script, creates new database with `PG_DBNAME` and initializes it with data
spanning from edition 1 to edition specified in command. The `data/oscars/imdb`
and `data/oscars/official` directories should already be populated with data for
all editions prior to running this script. See `scrape.py` for details.

Usage:
    python -m src.oscy.db <edition>

    <edition> is the edition of the last Oscars ceremony to include; the
        db will be initialized with data from the 1st edition to this edition

Example:
    python -m src.oscy.db 98
"""

import argparse
import csv
import dataclasses
import os
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from functools import wraps

import psycopg
import yaml
from dotenv import load_dotenv
from psycopg import Connection, sql
from psycopg.rows import class_row, dict_row
from tqdm import tqdm

from . import match, scrape
from .data import MatchedCategory, MatchedNominee
from .enums import UpdateType

load_dotenv(override=True)

DB_NAME = os.getenv("PG_DBNAME") or ""

# global db connection (lazy)
_conn: Connection | None = None


def conn() -> Connection:
    """Lazily gets global db connection (great name).

    Connects to database `PG_DBNAME` using username `PG_USER` and password
    `PG_PASSWORD` specified in top-level `.env` file.

    Returns:
        Connection: Psycopg db connection
    """
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg.connect(
            f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
            autocommit=True,
        )
    return _conn


# context variable tracks whether we're in a transaction
_in_transaction = ContextVar("_in_transaction", default=False)


@contextmanager
def create_or_continue_transaction():
    """Creates or continues a db transaction.

    If this context manager is used inside a transaction context, this uses the
    existing transaction; otherwise, creates a new transaction.
    """
    if _in_transaction.get():
        yield
        return

    token = _in_transaction.set(True)

    try:
        with conn().transaction():
            yield
    finally:
        _in_transaction.reset(token)


def transaction(fn):
    """Wraps a db function in a transaction.

    If a function decorated with @transaction is called when already inside a
    transaction context, uses the existing transaction; otherwise, creates a new
    transaction.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if _in_transaction.get():
            return fn(*args, **kwargs)

        with create_or_continue_transaction():
            return fn(*args, **kwargs)

    return wrapper


def close():
    """Closes global db connection."""
    if _conn is not None and not _conn.closed:
        _conn.close()


def create_db():
    """Creates new database `PG_DBNAME` by connecting to `postgres` db."""
    with psycopg.connect(
        f"dbname=postgres user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        with con.cursor() as cur:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))


def drop_db():
    """Deletes database `PG_DBNAME` by connecting to `postgres` db."""
    with psycopg.connect(
        f"dbname=postgres user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        with con.cursor() as cur:
            cur.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(DB_NAME))
            )


@transaction
def create_schema():
    """Creates database objects by executing `schema.sql`."""
    with conn().cursor() as cur:
        with open("schema.sql") as fd:
            script = fd.read()

        cur.execute(script)  # type: ignore


@transaction
def insert_editions(start: int = 1, end: int | None = None) -> None:
    """Inserts to `editions` based on official ceremony pages.

    Tables impacted: `editions`.

    Args:
        start (int, optional): first ceremony edition to include. Defaults to 1.
        end (int | None, optional): last ceremony edition to include. If None,
            ends at `start`. Defaults to None.
    """
    editions = scrape.scrape_editions(start, end)
    values = [dataclasses.asdict(e) for e in editions]
    with conn().cursor() as cur:
        cur.executemany(
            """
            INSERT INTO editions (award, iteration, official_year, ceremony_date)
            VALUES (%(award)s, %(iteration)s, %(official_year)s, %(ceremony_date)s);
        """,
            values,
        )


@transaction
def insert_categories(current_edition: int):
    """Inserts to category tables based on `data/oscar_categories.yaml`.

    Should only be used at db initialization. Tables impacted:
    `category_groups`, `categories`, `category_names`,
    `editions_category_names`.

    Args:
        current_edition (int): edition of most recent Oscars ceremony, used to
            replace `present` values in YAML file
    """
    with open("data/oscar_categories.yaml", encoding="utf-8") as fd:
        categories = yaml.safe_load(fd)

        with conn().cursor() as cur:
            for group in categories:
                cur.execute(
                    """
                    INSERT INTO category_groups (award, name)
                    VALUES ('oscar', %s)
                    RETURNING id;
                    """,
                    (group,),
                )
                category_group_id = cur.fetchone()[0]  # type: ignore
                for category in categories[group]:
                    cur.execute(
                        """
                        INSERT INTO categories (award, name, category_group_id)
                        VALUES ('oscar', %s, %s)
                        RETURNING id;
                        """,
                        (category, category_group_id),
                    )
                    category_id = cur.fetchone()[0]  # type: ignore
                    for official_name in categories[group][category]:
                        editions, common_name = categories[group][category][
                            official_name
                        ]
                        eds = []
                        for g in editions.split(", "):
                            r = g.split("-")
                            if len(r) == 2:
                                if r[1] == "present":
                                    r[1] = current_edition
                                eds += [i for i in range(int(r[0]), int(r[1]) + 1)]
                            else:
                                eds.append(int(r[0]))

                        cur.execute(
                            """
                            INSERT INTO category_names (award, official_name, common_name, category_id)
                            VALUES ('oscar', %s, %s, %s)
                            RETURNING id;
                            """,
                            (official_name, common_name, category_id),
                        )
                        category_name_id = cur.fetchone()[0]  # type: ignore

                        values = [
                            {
                                "category_name_id": category_name_id,
                                "edition": e,
                            }
                            for e in eds
                        ]

                        cur.executemany(
                            """
                            INSERT INTO editions_category_names (edition_id, category_name_id)
                            SELECT id, %(category_name_id)s
                            FROM editions
                            WHERE award = 'oscar' AND iteration = %(edition)s;
                            """,
                            values,
                        )


@transaction
def insert_category_name(
    category_name_official: str,
    category_name_common: str,
    category: str,
    new_category: bool,
    category_group: str,
    new_category_group: bool,
) -> int:
    """Inserts new category name and potentially new category, category group.

    Tables impacted: `category_names`, `categories`, `category_groups`.

    Args:
        category_name_official (str): official category name to insert
        category_name_common (str): common category name to insert
        category (str): name of category that category name belongs to
        new_category (bool): if True, insert new category; otherwise, use
            existing category with name `category`
        category_group (str): name of category group that category name belongs
            to
        new_category_group (bool): if True, insert new category group;
            otherwise, use existing category group with name `category_group`

    Returns:
        int: database id of newly inserted category name
    """
    with conn().cursor() as cur:
        if new_category_group:
            cur.execute(
                """
                INSERT INTO category_groups (award, name)
                VALUES ('oscar', %s)
                RETURNING id
                """,
                (category_group,),
            )
        else:
            cur.execute(
                """
                SELECT id
                FROM category_groups
                WHERE award = 'oscar' AND name = %s
                """,
                (category_group,),
            )
        category_group_id = cur.fetchone()[0]  # type: ignore

        if new_category:
            cur.execute(
                """
                INSERT INTO categories (award, name, category_group_id)
                VALUES ('oscar', %s, %s)
                RETURNING id
                """,
                (category, category_group_id),
            )
        else:
            cur.execute(
                """
                SELECT id
                FROM categories
                WHERE award = 'oscar' AND name = %s
                """,
                (category,),
            )
        category_id = cur.fetchone()[0]  # type: ignore

        cur.execute(
            """
            INSERT INTO category_names (award, official_name, common_name, category_id)
            VALUES ('oscar', %s, %s, %s)
            RETURNING id
            """,
            (category_name_official, category_name_common, category_id),
        )
        category_name_id = cur.fetchone()[0]  # type: ignore

        return category_name_id


@transaction
def insert_editions_category_names(
    edition: int, data: dict[int, list[MatchedCategory]]
):
    """Inserts to `editions_category_names` for new edition.

    Tables impacted: `editions_category_names`.

    Args:
        edition (int): edition of Oscars ceremony
        data (dict[int, list[MatchedCategory]]): edition -> matched categories
    """
    with conn().cursor() as cur:
        cur.execute(
            """
            SELECT id
            FROM editions
            WHERE award = 'oscar' AND iteration = %s
            """,
            (edition,),
        )
        edition_id = cur.fetchone()[0]  # type: ignore
        category_names = [
            {
                "category_name": c.category.lower(),
                "edition_id": edition_id,
            }
            for c in data[edition]
        ]
        cur.executemany(
            """
            INSERT INTO editions_category_names (edition_id, category_name_id)
            SELECT %(edition_id)s, id
            FROM category_names
            WHERE award = 'oscar' AND LOWER(official_name) = %(category_name)s
            ORDER BY id
            LIMIT 1
            """,
            category_names,
        )


def imdb_id_to_entity_type(imdb_id: str) -> str:
    """Converts IMDb id to database entity type.

    Args:
        imdb_id (str): IMDb id

    Raises:
        ValueError: invalid IMDb id

    Returns:
        str: db entity type
    """
    if imdb_id.startswith("nm"):
        return "person"
    elif imdb_id.startswith("co"):
        return "company"
    elif imdb_id.startswith("cc"):
        return "country"
    else:
        raise ValueError("IMDb id is invalid:", imdb_id)


@transaction
def insert_nominees(matched_nominees: list[MatchedNominee]):
    """Inserts matched nominees to db.

    Tables impacted: `nominees`, `titles`, `nominees_titles`, `entities`,
    `nominees_entities`.

    Args:
        matched_nominees (list[MatchedNominee]): matched nominees to insert
    """
    # flatten to list of MatchedNominee dicts across all editions
    nominees = [dataclasses.asdict(n) for n in matched_nominees]

    with conn().cursor() as cur:
        for nominee in tqdm(nominees):
            nominee["category_name"] = nominee["category_name"].lower()
            # insert nominee
            cur.execute(
                """
                INSERT INTO nominees (award, edition_id, category_name_id, statement, is_person, pending, winner, note, official, stat)
                SELECT
                    'oscar',
                    e.id,
                    cn.id,
                    %(statement)s,
                    %(is_person)s,
                    %(pending)s,
                    %(winner)s,
                    %(note)s,
                    %(official)s,
                    %(stat)s
                FROM editions e
                JOIN editions_category_names ecn ON e.id = ecn.edition_id
                JOIN category_names cn ON cn.id = ecn.category_name_id
                WHERE e.award = 'oscar' AND e.iteration = %(edition)s AND LOWER(cn.official_name) = %(category_name)s
                RETURNING id;
                """,
                nominee,
            )
            nominee_id = cur.fetchone()[0]  # type: ignore

            # films: list[tuple[str, str, bool, list[str]]]
            # title, imdb id, winner, detail (song titles or dance numbers
            # assoc with title)

            # people: list[tuple[str, str, int, str]]
            # name, imdb id, start index in nomination stmt, role on set
            # (does not apply to oscars)

            # upsert titles
            if nominee["films"]:
                cur.executemany(
                    """
                    WITH ins AS (
                        INSERT INTO titles (imdb_id, award, title)
                        VALUES (%(imdb_id)s, 'oscar', %(title)s)
                        ON CONFLICT (imdb_id)
                        DO UPDATE SET title = EXCLUDED.title
                        RETURNING id                        
                    )
                    INSERT INTO nominees_titles (nominee_id, title_id, detail, winner)
                    SELECT %(nominee_id)s, ins.id, %(detail)s, %(winner)s
                    FROM ins;
                    """,
                    [
                        {
                            "imdb_id": t[1],
                            "title": t[0],
                            "nominee_id": nominee_id,
                            "detail": t[3],
                            "winner": t[2],
                        }
                        for t in nominee["films"]
                    ],
                )

            # upsert entities
            if nominee["people"]:
                cur.executemany(
                    """
                    WITH ins AS (
                        INSERT INTO entities (imdb_id, type, name)
                        VALUES (%(imdb_id)s, %(entity_type)s, %(name)s)
                        ON CONFLICT (imdb_id)
                        DO UPDATE SET name = EXCLUDED.name
                        RETURNING id                        
                    )
                    INSERT INTO nominees_entities (nominee_id, entity_id, name, statement_ind, role)
                    SELECT %(nominee_id)s, ins.id, %(name)s, %(statement_ind)s, ''
                    FROM ins;
                    """,
                    [
                        {
                            "imdb_id": t[1],
                            "entity_type": imdb_id_to_entity_type(t[1]),
                            "name": t[0],
                            "nominee_id": nominee_id,
                            "statement_ind": t[2],
                        }
                        for t in nominee["people"]
                    ],
                )


@transaction
def upsert_nominee_title(
    nominee_id: int, title: str, imdb_id: str, winner: bool, detail: list[str]
):
    """Upserts nominee title to db.

    Upserts title, then uses returned id to upsert entry in associative table.
    Tables impacted: `titles`, `nominees_titles`.

    Args:
        nominee_id (int): db nominee id
        title (str): name of title
        imdb_id (str): IMDb id of title
        winner (bool): whether this particular title within the nominee won
        detail (list[str]): characters, song titles, dance numbers associated
            with the nominee's title
    """
    with conn().cursor() as cur:
        cur.execute(
            """
            WITH ins AS (
                INSERT INTO titles (imdb_id, award, title)
                VALUES (%(imdb_id)s, 'oscar', %(title)s)
                ON CONFLICT (imdb_id)
                DO UPDATE SET title = EXCLUDED.title
                RETURNING id
            )
            INSERT INTO nominees_titles (nominee_id, title_id, detail, winner)
            SELECT %(nominee_id)s, ins.id, %(detail)s, %(winner)s
            FROM ins
            ON CONFLICT (nominee_id, title_id)
            DO UPDATE SET
                detail = EXCLUDED.detail,
                winner = EXCLUDED.winner
            """,
            {
                "imdb_id": imdb_id,
                "title": title,
                "nominee_id": nominee_id,
                "detail": detail,
                "winner": winner,
            },
        )


@transaction
def delete_nominee_title(nominee_id: int, imdb_id: str):
    """Deletes from `nominees_titles` and potentially `titles`.

    Deletes entry from associative table, then deletes title if it has no more
    entries in associative table. Tables impacted: `nominees_titles`, `titles`.

    Args:
        nominee_id (int): db nominee id
        imdb_id (str): IMDb id of nominee title
    """
    with conn().cursor() as cur:
        cur.execute(
            """
            SELECT id
            FROM titles
            WHERE imdb_id = %s
            """,
            (imdb_id,),
        )
        title_id = cur.fetchone()[0]  # type: ignore

        cur.execute(
            """
            DELETE FROM nominees_titles
            WHERE nominee_id = %s AND title_id = %s
            """,
            (nominee_id, title_id),
        )

        cur.execute(
            """
            DELETE FROM titles
            WHERE id = %s AND NOT EXISTS (
                SELECT 1
                FROM nominees_titles nt
                WHERE titles.id = nt.title_id
            )
            RETURNING id, imdb_id, title
            """,
            (title_id,),
        )
        deleted_titles = [(r[0], r[1], r[2]) for r in cur.fetchall()]
        if deleted_titles:
            print(f"Deleted {len(deleted_titles)} titles from db: {deleted_titles}")


@transaction
def upsert_nominee_entity(
    nominee_id: int, name: str, imdb_id: str, statement_ind: str, role: str
):
    """Upserts nominee entity to db.

    Upserts entity, then uses returned id to upsert entry in associative table.
    Tables impacted: `entities`, `nominees_entities`.

    Args:
        nominee_id (int): db nominee id
        name (str): name of entity listed on nomination
        imdb_id (str): IMDb id of entity
        statement_ind (str): start index of name in nomination statement
        role (str): entity's role on set (does not apply to Oscars)
    """
    with conn().cursor() as cur:
        cur.execute(
            """
            WITH ins AS (
                INSERT INTO entities (imdb_id, type, name)
                VALUES (%(imdb_id)s, %(entity_type)s, %(name)s)
                ON CONFLICT (imdb_id)
                DO UPDATE SET name = EXCLUDED.name
                RETURNING id
            )
            INSERT INTO nominees_entities (nominee_id, entity_id, name, statement_ind, role)
            SELECT %(nominee_id)s, ins.id, %(name)s, %(statement_ind)s, %(role)s
            FROM ins
            ON CONFLICT (nominee_id, entity_id)
            DO UPDATE SET
                name = EXCLUDED.name,
                statement_ind = EXCLUDED.statement_ind,
                role = EXCLUDED.role
            """,
            {
                "imdb_id": imdb_id,
                "entity_type": imdb_id_to_entity_type(imdb_id),
                "name": name,
                "nominee_id": nominee_id,
                "statement_ind": statement_ind,
                "role": role,
            },
        )


@transaction
def delete_nominee_entity(nominee_id: int, imdb_id: str):
    """Deletes from `nominees_entities` and potentially `entities`.

    Deletes entry from associative table, then deletes entity if it has no more
    entries in associative table. Tables impacted: `nominees_entities`,
    `entities`.

    Args:
        nominee_id (int): db nominee id
        imdb_id (str): IMDb id of nominee entity
    """
    with conn().cursor() as cur:
        cur.execute(
            """
            SELECT id
            FROM entities
            WHERE imdb_id = %s
            """,
            (imdb_id,),
        )
        entity_id = cur.fetchone()[0]  # type: ignore

        cur.execute(
            """
            DELETE FROM nominees_entities
            WHERE nominee_id = %s AND entity_id = %s
            """,
            (nominee_id, entity_id),
        )

        cur.execute(
            """
            DELETE FROM entities
            WHERE id = %s AND NOT EXISTS (
                SELECT 1
                FROM nominees_entities ne
                WHERE entities.id = ne.entity_id
            )
            RETURNING id, imdb_id, name
            """,
            (entity_id,),
        )
        deleted_entities = [(r[0], r[1], r[2]) for r in cur.fetchall()]
        if deleted_entities:
            print(
                f"Deleted {len(deleted_entities)} entities from db: {deleted_entities}"
            )


@transaction
def update_nominee(nominee_id: int, matched_nominee: MatchedNominee):
    """Updates existing entry in `nominees` based on `matched_nominee` data.

    Tables impacted: `nominees`.

    Args:
        nominee_id (int): db nominee id
        matched_nominee (MatchedNominee): matched nominee to update db with
    """
    nominee = dataclasses.asdict(matched_nominee)
    nominee["category_name"] = nominee["category_name"].lower()
    nominee["id"] = nominee_id

    with conn().cursor() as cur:
        cur.execute(
            """
            UPDATE nominees
            SET
                category_name_id = category_names.id,
                statement = %(statement)s,
                is_person = %(is_person)s,
                pending = %(pending)s,
                winner = %(winner)s,
                note = %(note)s,
                official = %(official)s,
                stat = %(stat)s
            FROM category_names
            WHERE nominees.id = %(id)s AND LOWER(category_names.official_name) = %(category_name)s
            """,
            nominee,
        )


@transaction
def update_nominees_pending_false(edition: int):
    """Sets `pending=FALSE` for all nominees in specified `edition`.

    Tables impacted: `nominees`.

    Args:
        edition (int): edition of Oscars ceremony
    """
    with conn().cursor() as cur:
        cur.execute(
            """
            UPDATE nominees
            SET pending = FALSE
            FROM editions
            WHERE nominees.award = 'oscar' AND nominees.edition_id = editions.id AND editions.iteration = %s
            """,
            (edition,),
        )


@transaction
def delete_nominees(matched_nominees: list[MatchedNominee]):
    """Deletes matched nominees from db.

    For each nominee: deletes entries from associative tables, then deletes
    corresponding titles/entities if they have no more entries in associative
    table, then deletes entry in `nominees`. Tables impacted: `nominees_titles`,
    `titles`, `nominees_entities`, `entities`, `nominees`.

    Args:
        matched_nominees (list[MatchedNominee]): matched nominees to delete

    Raises:
        Exception: all nominees in `matched_nominees` must have an integer id
    """
    nominees = [n for n in matched_nominees if n.id is not None]

    if len(nominees) < len(matched_nominees):
        raise Exception("All nominees in `matched_nominees` must have an integer id")

    with conn().cursor() as cur:
        for nominee in nominees:
            # delete from nominees_titles and potentially titles
            cur.execute(
                """
                DELETE FROM nominees_titles
                WHERE nominee_id = %s
                RETURNING title_id
                """,
                (nominee.id,),
            )
            title_ids = [r[0] for r in cur.fetchall()]

            cur.execute(
                """
                DELETE FROM titles
                WHERE id = ANY(%s) AND NOT EXISTS (
                    SELECT 1
                    FROM nominees_titles nt
                    WHERE titles.id = nt.title_id
                )
                RETURNING id, imdb_id, title
                """,
                (title_ids,),
            )
            deleted_titles = [(r[0], r[1], r[2]) for r in cur.fetchall()]
            if deleted_titles:
                print(f"Deleted {len(deleted_titles)} titles from db: {deleted_titles}")

            # delete from nominees_entities and potentially entities
            cur.execute(
                """
                DELETE FROM nominees_entities
                WHERE nominee_id = %s
                RETURNING entity_id
                """,
                (nominee.id,),
            )
            entity_ids = [r[0] for r in cur.fetchall()]

            cur.execute(
                """
                DELETE FROM entities
                WHERE id = ANY(%s) AND NOT EXISTS (
                    SELECT 1
                    FROM nominees_entities ne
                    WHERE entities.id = ne.entity_id
                )
                RETURNING id, imdb_id, name
                """,
                (entity_ids,),
            )
            deleted_entities = [(r[0], r[1], r[2]) for r in cur.fetchall()]
            if deleted_entities:
                print(
                    f"Deleted {len(deleted_entities)} entities from db: {deleted_entities}"
                )

            # delete from nominees
            cur.execute(
                """
                DELETE FROM nominees
                WHERE id = %s
                """,
                (nominee.id,),
            )


@transaction
def replace_edition_category_name(
    edition: int, old_category_name_id: int, new_category_name_official: str
):
    """Replaces an edition's category name with a different one.

    The new category name must already exist in the db and its official name
    must match `new_category_name_official`. Updates entries in both
    `editions_category_names` and `nominees` with new category name. If this
    causes the old category name (as well as its parent category and category
    group) to no longer have entries in `nominees`, they will be deleted.

    Tables impacted: `editions_category_names`, `nominees`, `category_names`,
    `categories`, `category_groups`.

    Args:
        edition (int): edition of Oscars ceremony
        old_category_name_id (int): db id of category name to be replaced
        new_category_name_official (str): official name of new category name
            that will replace the old one for this edition
    """
    with conn().cursor() as cur:
        cur.execute(
            """
            SELECT id
            FROM editions
            WHERE award = 'oscar' AND iteration = %s
            """,
            (edition,),
        )
        edition_id = cur.fetchone()[0]  # type: ignore

        cur.execute(
            """
            SELECT id
            FROM category_names
            WHERE award = 'oscar' AND LOWER(official_name) = %s
            """,
            (new_category_name_official.lower(),),
        )
        new_category_name_id = cur.fetchone()[0]  # type: ignore

        cur.execute(
            """
            UPDATE editions_category_names
            SET category_name_id = %s
            WHERE edition_id = %s AND category_name_id = %s
            """,
            (new_category_name_id, edition_id, old_category_name_id),
        )

        cur.execute(
            """
            UPDATE nominees
            SET category_name_id = %s
            WHERE edition_id = %s AND category_name_id = %s
            """,
            (new_category_name_id, edition_id, old_category_name_id),
        )

        cur.execute(
            """
            SELECT c.id, cg.id
            FROM category_names cn
            JOIN categories c ON cn.category_id = c.id
            LEFT JOIN category_groups cg ON c.category_group_id = cg.id
            WHERE cn.id = %s
            """,
            (old_category_name_id,),
        )
        old_category_id, old_category_group_id = cur.fetchone()  # type: ignore

        cur.execute(
            """
            WITH nc AS (
                SELECT DISTINCT
                    cn.id AS category_name_id,
                    c.id AS category_id,
                    cg.id AS category_group_id
                FROM nominees n
                LEFT JOIN category_names cn ON n.category_name_id = cn.id
                LEFT JOIN categories c ON cn.category_id = c.id
                LEFT JOIN category_groups cg ON c.category_group_id = cg.id
            ),
            deleted_cn AS (
                DELETE FROM category_names
                WHERE id = %s AND NOT EXISTS (
                    SELECT 1
                    FROM nc
                    WHERE category_names.id = nc.category_name_id
                )
                RETURNING id, official_name AS name
            ),
            deleted_c AS (
                DELETE FROM categories
                WHERE id = %s AND NOT EXISTS (
                    SELECT 1
                    FROM nc
                    WHERE categories.id = nc.category_id
                )
                RETURNING id, name
            ),
            deleted_cg AS (
                DELETE FROM category_groups
                WHERE id = %s AND NOT EXISTS (
                    SELECT 1
                    FROM nc
                    WHERE category_groups.id = nc.category_group_id
                )
                RETURNING id, name
            )
            SELECT 'category_names' AS level, id, name FROM deleted_cn
            UNION
            SELECT 'categories' AS level, id, name FROM deleted_c
            UNION
            SELECT 'category_groups' AS level, id, name FROM deleted_cg
            """,
            (
                old_category_name_id,
                old_category_id,
                old_category_group_id,
            ),
        )
        deleted_entries = cur.fetchall()
        if deleted_entries:
            print(f"Deleted {len(deleted_entries)} entries from db:")
            for entry in deleted_entries:
                print(entry)


@transaction
def upsert_current_version(edition: int, update_stage: UpdateType):
    """Upserts info about the data's current version to db.

    Tables impacted: `current_versions`.

    Args:
        edition (int): edition of Oscars ceremony
        update_stage (UpdateType): current update stage
    """
    updated_at = datetime.now(UTC)
    tag = f"o{edition}{update_stage.name[0]}{int(updated_at.timestamp())}"

    with conn().cursor() as cur:
        cur.execute(
            """
            INSERT INTO current_versions (award, iteration, update_stage, updated_at, tag)
            VALUES ('oscar', %(iteration)s, %(update_stage)s, %(updated_at)s, %(tag)s)
            ON CONFLICT (award)
            DO UPDATE SET
                iteration = EXCLUDED.iteration,
                update_stage = EXCLUDED.update_stage,
                updated_at = EXCLUDED.updated_at,
                tag = EXCLUDED.tag
            """,
            {
                "iteration": edition,
                "update_stage": update_stage,
                "updated_at": updated_at,
                "tag": tag,
            },
        )
        print("Upserted current version with tag:", tag)


@transaction
def get_current_edition() -> int:
    """Gets current edition iteration from db."""
    with conn().cursor() as cur:
        cur.execute(
            """
            SELECT iteration
            FROM current_versions
            WHERE award = 'oscar'
            """
        )
        edition: int = cur.fetchone()[0]  # type: ignore
        return edition


@transaction
def get_category_groups() -> list[str]:
    """Gets names of all category groups in db."""
    with conn().cursor() as cur:
        cur.execute(
            """
            SELECT name
            FROM category_groups
            WHERE award = 'oscar'
            """
        )
        return [r[0] for r in cur.fetchall()]


@transaction
def get_categories() -> list[str]:
    """Gets names of all categories in db."""
    with conn().cursor() as cur:
        cur.execute(
            """
            SELECT name
            FROM categories
            WHERE award = 'oscar'
            """
        )
        return [r[0] for r in cur.fetchall()]


@transaction
def get_category_names_official(edition: int | None = None) -> list[tuple[int, str]]:
    """Gets ids and official names of category names in db.

    Args:
        edition (int | None, optional): if None, gets all category names;
            otherwise, gets category names from specified edition. Defaults to
            None.

    Returns:
        list[tuple[int, str]]: list of (id, category name official name)
    """
    with conn().cursor() as cur:
        if edition is None:
            cur.execute(
                """
                SELECT id, official_name
                FROM category_names
                WHERE award = 'oscar'
                """
            )
        else:
            cur.execute(
                """
                SELECT cn.id, cn.official_name
                FROM category_names cn
                JOIN editions_category_names ecn ON ecn.category_name_id = cn.id
                JOIN editions e ON e.id = ecn.edition_id
                WHERE cn.award = 'oscar' AND e.iteration = %s
                """,
                (edition,),
            )
        return [(r[0], r[1]) for r in cur.fetchall()]


@transaction
def get_matched_categories_by_edition(edition: int) -> list[MatchedCategory]:
    """Gets edition's data from db, converted to `MatchedCategory` format.

    Args:
        edition (int): edition of Oscars ceremony

    Returns:
        list[MatchedCategory]: matched categories from this edition
    """
    with conn().cursor(row_factory=class_row(MatchedNominee)) as cur:  # type: ignore
        cur.execute(
            """
            WITH filtered_nominees AS (
                SELECT
                    n.id,
                    e.iteration,
                    cn.official_name,
                    n.winner,
                    n.statement,
                    n.is_person,
                    n.note,
                    n.official,
                    n.stat,
                    n.pending
                FROM nominees n
                JOIN editions e ON e.id = n.edition_id
                JOIN category_names cn ON cn.id = n.category_name_id 
                WHERE e.iteration = %s
            ),
            films as (
                SELECT
                    nt.nominee_id AS nominee_id,
                    json_agg(json_build_array(t.title, t.imdb_id, nt.winner, nt.detail) ORDER BY t.title) AS films
                FROM filtered_nominees fn
                LEFT JOIN nominees_titles nt ON nt.nominee_id = fn.id 
                LEFT JOIN titles t ON t.id = nt.title_id
                GROUP BY nt.nominee_id
            ),
            people as (
                SELECT
                    ne.nominee_id AS nominee_id,
                    json_agg(json_build_array(ne.name, en.imdb_id, ne.statement_ind, ne.role) ORDER BY ne.name) AS people
                FROM filtered_nominees fn
                LEFT JOIN nominees_entities ne ON ne.nominee_id = fn.id 
                LEFT JOIN entities en ON en.id = ne.entity_id
                GROUP BY ne.nominee_id
            )
            SELECT
                fn.id,
                fn.iteration AS edition,
                fn.official_name AS category_name,
                fn.winner,
                fn.statement,
                fn.is_person,
                fn.note,
                fn.official,
                fn.stat,
                fn.pending,
                COALESCE(films.films, '[]'::json) AS films,
                COALESCE(people.people, '[]'::json) AS people
            FROM filtered_nominees fn
            LEFT JOIN films ON films.nominee_id = fn.id
            LEFT JOIN people ON people.nominee_id = fn.id
            ORDER BY category_name
            """,
            (edition,),
        )

        matched_nominees: list[MatchedNominee] = cur.fetchall()  # type: ignore

        category_name_to_matched_category: dict[str, MatchedCategory] = {}
        for n in matched_nominees:
            if n.category_name not in category_name_to_matched_category:
                category_name_to_matched_category[n.category_name] = MatchedCategory(
                    category=n.category_name, nominees=[]
                )
            category_name_to_matched_category[n.category_name].nominees.append(n)

        return list(category_name_to_matched_category.values())


@transaction
def export_nominations_to_csv():
    """Exports nomination data from all editions to `data/oscars.csv`."""
    with conn().cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
                e.iteration, e.official_year, e.ceremony_date,
                cg.name AS category_group, c.name AS category, official_name, common_name,
                n.id AS nomination_id, n.statement, n.pending, n.winner, n.official, n.stat,
                ne.name AS statement_name, ne.statement_ind,
                en.imdb_id AS entity_imdb_id, en.type AS entity_type, en.name,
                t.imdb_id AS title_imdb_id, t.title,
                nt.detail, nt.winner AS title_winner, n.note
            FROM category_names cn
            JOIN categories c ON c.id = cn.category_id
            JOIN category_groups cg ON cg.id = c.category_group_id
            JOIN editions_category_names ecn ON ecn.category_name_id = cn.id
            JOIN editions e ON e.id = ecn.edition_id
            JOIN nominees n ON n.edition_id = e.id AND n.category_name_id = cn.id
            LEFT JOIN nominees_entities ne ON ne.nominee_id = n.id
            LEFT JOIN entities en ON en.id = ne.entity_id
            LEFT JOIN nominees_titles nt ON nt.nominee_id = n.id
            LEFT JOIN titles t ON t.id = nt.title_id
            WHERE n.award = 'oscar'
            ORDER BY e.iteration, c.id, n.winner DESC, n.id ASC, ne.statement_ind ASC, nt.winner DESC
            """
        )
        results: list[dict] = cur.fetchall()

        with open(
            "../../data/oscars.csv", "w", encoding="utf-8", newline=""
        ) as output_file:
            dict_writer = csv.DictWriter(output_file, list(results[0].keys()))
            dict_writer.writeheader()
            dict_writer.writerows(results)


def initialize_db(current_edition: int):
    """Initializes database after initial creation.

    Creates db objects and initializes it with data spanning from the 1st
    edition to `current_edition`. The `data/oscars/imdb` and
    `data/oscars/official` directories should already be populated with data for
    all editions prior to calling this function.

    This function should not be used to update the db with new data. See
    `update.py` for details.

    Args:
        current_edition (int): edition of last Oscars ceremony to include
    """
    with create_or_continue_transaction():
        create_schema()
        insert_editions(end=current_edition)
        insert_categories(current_edition)
        data = match.match_categories(end=current_edition)
        matched_nominees = [n for ed in data for c in data[ed] for n in c.nominees]
        insert_nominees(matched_nominees)
        upsert_current_version(current_edition, UpdateType.official)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("edition", type=int)

        args = parser.parse_args()

        edition: int = args.edition
        if edition <= 0:
            raise ValueError("edition must be >= 1")

        create_db()
        initialize_db(edition)
    finally:
        close()
