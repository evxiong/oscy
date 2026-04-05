import csv
import dataclasses
import os

import psycopg
import yaml
from dotenv import load_dotenv
from psycopg import sql
from psycopg.rows import class_row, dict_row
from tqdm import tqdm

from . import match, scrape
from .data import MatchedCategory, MatchedNominee

load_dotenv(override=True)

DB_NAME = os.getenv("PG_DBNAME") or ""

# official oscars ceremony page category name -> official name
# THIS SHOULD NOT BE USED
# OFFICIAL_PAGE_CONVERSIONS = {
#     "Animated Short Film": "short film (animated)",
#     "Live Action Short Film": "short film (live action)",
# }


def create_db():
    with psycopg.connect(
        f"dbname=postgres user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        with con.cursor() as cur:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))

    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        with con.cursor() as cur:
            cur.execute("""CREATE TYPE award_type AS ENUM ('oscar', 'emmy')""")
            cur.execute(
                """CREATE TYPE entity_type AS ENUM ('person', 'company', 'country', 'network')"""
            )
            cur.execute(
                """
                CREATE OR REPLACE FUNCTION integer_to_ordinal(num integer) RETURNS text AS $$
                    SELECT 
                        num::text ||
                        CASE
                            WHEN num % 100 IN (11,12,13) THEN 'th'
                            WHEN num % 10 = 1 THEN 'st'
                            WHEN num % 10 = 2 THEN 'nd'
                            WHEN num % 10 = 3 THEN 'rd'
                            ELSE 'th'
                        END;
                $$ LANGUAGE SQL;
                """
            )
            cur.execute("""CREATE EXTENSION IF NOT EXISTS pg_trgm""")


def drop_db():
    with psycopg.connect(
        f"dbname=postgres user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        with con.cursor() as cur:
            cur.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(DB_NAME))
            )


def create_tables():
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        with con.cursor() as cur:
            # create editions table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS editions (
                        id              serial PRIMARY KEY,
                        award           award_type NOT NULL, -- 'oscar' or 'emmy'
                        iteration       integer NOT NULL,
                        official_year   varchar(10) NOT NULL, -- listed year, ex. '1927/28'
                        ceremony_date   date NOT NULL
                )
                """
            )

            # create category tables
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS category_groups (
                        id              serial PRIMARY KEY,
                        award           award_type NOT NULL,
                        name            text NOT NULL -- ex. Acting
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS categories (
                        id                  serial PRIMARY KEY,
                        award               award_type NOT NULL,
                        name                text NOT NULL, -- nickname/description of category, ex. 'Animated Feature'
                        category_group_id   integer REFERENCES category_groups(id) ON DELETE SET NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS category_names (
                        id                  serial PRIMARY KEY,
                        award               award_type NOT NULL,
                        official_name       text NOT NULL, -- specific category name according to official source, ex. 'ANIMATED FEATURE FILM'
                        common_name         text NOT NULL, -- common category name, ex. 'Best Animated Feature Film'
                        category_id         integer NOT NULL REFERENCES categories(id)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS editions_category_names (
                        id                  serial PRIMARY KEY,
                        edition_id          integer NOT NULL REFERENCES editions(id),
                        category_name_id    integer NOT NULL REFERENCES category_names(id)
                )
                """
            )

            # create entities, titles tables
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS entities (
                        id                  serial PRIMARY KEY,
                        imdb_id             text UNIQUE NOT NULL,
                        type                entity_type NOT NULL,
                        name                text NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS titles (
                        id                  serial PRIMARY KEY,
                        imdb_id             text UNIQUE NOT NULL,
                        award               award_type NOT NULL,
                        title               text NOT NULL -- name of film or show
                )
                """
            )

            # create nominees, nominees_titles, nominations tables
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS nominees (
                        id                  serial PRIMARY KEY,
                        award               award_type NOT NULL,
                        edition_id          integer NOT NULL REFERENCES editions(id),
                        category_name_id    integer NOT NULL REFERENCES category_names(id),
                        statement           text NOT NULL,
                        is_person           boolean NOT NULL, -- whether the nominee is primarily a person (T) or a title (F)
                        pending             boolean NOT NULL DEFAULT FALSE, -- whether ceremony results are pending
                        winner              boolean NOT NULL, -- whether any title in this nominee won
                        note                text NOT NULL,
                        official            boolean NOT NULL, -- whether this nominee is considered official (for oscars)
                        stat                boolean NOT NULL -- whether this nominee counts towards aggregated nomination stats
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS nominees_titles ( -- associates nominee ids with title ids
                        id                  serial PRIMARY KEY,
                        nominee_id          integer NOT NULL REFERENCES nominees(id),
                        title_id            integer NOT NULL REFERENCES titles(id),
                        detail              text[] NOT NULL, -- characters, song titles, or dance numbers assoc. with this title
                        winner              boolean NOT NULL, -- whether this particular title won (only important for 3rd oscars)
                        UNIQUE (nominee_id, title_id)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS nominees_entities ( -- one entry per entity in each nominee entry
                        id                  serial PRIMARY KEY,
                        nominee_id          integer NOT NULL REFERENCES nominees(id),
                        entity_id           integer NOT NULL REFERENCES entities(id),
                        name                text NOT NULL, -- name listed on this nomination (could be alias)
                        statement_ind       integer NOT NULL, -- start index of name in nomination statement
                        role                text NOT NULL, -- entity's role on set (if applicable)
                        UNIQUE (nominee_id, entity_id)
                )
                """
            )


def create_indexes():
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        with con.cursor() as cur:
            cur.execute(
                "CREATE INDEX title_trgm_idx ON titles USING GIST (title gist_trgm_ops)"
            )
            cur.execute(
                "CREATE INDEX entity_trgm_idx ON entities USING GIST (name gist_trgm_ops)"
            )


def insert_editions(start: int | None = None, end: int | None = None) -> None:
    editions = scrape.scrape_editions(start, end)
    values = [dataclasses.asdict(e) for e in editions]
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}"
    ) as con:
        with con.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO editions (award, iteration, official_year, ceremony_date)
                VALUES (%(award)s, %(iteration)s, %(official_year)s, %(ceremony_date)s);
            """,
                values,
            )


def insert_category_name(
    category_name_official: str,
    category_name_common: str,
    category: str,
    new_category: bool,
    category_group: str,
    new_category_group: bool,
):
    """Inserts new category name and potentially new category, category group.

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
    """
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        cur = con.cursor()
        with con.transaction():
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
                """,
                (category_name_official, category_name_common, category_id),
            )


def insert_categories():
    with open("data/oscar_categories.yaml", encoding="utf-8") as fd:
        categories = yaml.safe_load(fd)

    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        cur = con.cursor()
        with con.transaction():
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
                                    r[1] = int(os.getenv("CURRENT_EDITION"))  # type: ignore
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


def insert_editions_category_names(
    edition: int, data: dict[int, list[MatchedCategory]]
):
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        cur = con.cursor()
        with con.transaction():
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
                    # "category_name": OFFICIAL_PAGE_CONVERSIONS.get(
                    #     c.category, c.category
                    # ).lower(),
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


def imdb_id_to_entity_type(id: str) -> str:
    if id.startswith("nm"):
        return "person"
    elif id.startswith("co"):
        return "company"
    elif id.startswith("cc"):
        return "country"
    else:
        raise ValueError("IMDb id is invalid:", id)


def insert_nominees(matched_nominees: list[MatchedNominee]):
    # flatten to list of MatchedNominee dicts across all editions
    nominees = [dataclasses.asdict(n) for n in matched_nominees]

    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        cur = con.cursor()
        with con.transaction():
            for nominee in tqdm(nominees):
                # nominee["category_name"] = OFFICIAL_PAGE_CONVERSIONS.get(
                #     nominee["category_name"], nominee["category_name"]
                # ).lower()
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


def upsert_nominee_title(
    nominee_id: int, title: str, imdb_id: str, winner: bool, detail: list[str]
):
    # upsert to titles and nominees_titles
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        with con.cursor() as cur:
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


def delete_nominee_title(nominee_id: int, imdb_id: str):
    # delete from nominees_titles and potentially titles
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        cur = con.cursor()
        with con.transaction():
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


def upsert_nominee_entity(
    nominee_id: int, name: str, imdb_id: str, statement_ind: str, role: str
):
    # upsert to entities and nominees_entities
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        with con.cursor() as cur:
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


def delete_nominee_entity(nominee_id: int, imdb_id: str):
    # delete from nominee_entities and potentially entities
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        cur = con.cursor()
        with con.transaction():
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


def update_nominee(nominee_id: int, matched_nominee: MatchedNominee):
    nominee = dataclasses.asdict(matched_nominee)
    nominee["category_name"] = nominee["category_name"].lower()
    nominee["id"] = nominee_id

    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        with con.cursor() as cur:
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


def update_pending(edition: int):
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        with con.cursor() as cur:
            cur.execute(
                """
                UPDATE nominees
                SET pending = FALSE
                FROM editions
                WHERE nominees.award = 'oscar' AND nominees.edition_id = editions.id AND editions.iteration = %s
                """,
                (edition,),
            )


def delete_nominees(matched_nominees: list[MatchedNominee]):
    # delete from nominees_titles, then nominees_entities, then nominees; delete
    # titles and entities if they have no other rows in nominees_titles or
    # nominees_entities, respectively

    nominees = [n for n in matched_nominees if n.id is not None]

    if len(nominees) < len(matched_nominees):
        raise Exception("All nominees in `matched_nominees` must have an integer id")

    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        cur = con.cursor()
        with con.transaction():
            # nominee_ids = [{"nominee_id": nominee.id} for nominee in nominees]
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

                # cur.execute(
                #     """
                #     SELECT title_id, COUNT(*)
                #     FROM nominees_titles
                #     WHERE title_id = ANY(%s)
                #     GROUP BY title_id
                # """,
                #     (title_ids,),
                # )
                # print(cur.fetchall())

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
                    print(
                        f"Deleted {len(deleted_titles)} titles from db: {deleted_titles}"
                    )

                # cur.executemany(
                #     """
                #     WITH deleted_nt AS (
                #         DELETE FROM nominees_titles
                #         WHERE nominee_id = %(nominee_id)s
                #         RETURNING title_id
                #     )
                #     DELETE FROM titles
                #     WHERE id IN (
                #         SELECT title_id FROM deleted_nt
                #     )
                #     AND NOT EXISTS (
                #         SELECT 1
                #         FROM nominees_titles nt
                #         JOIN deleted_nt dnt ON dnt.title_id = nt.title_id
                #         WHERE titles.id = nt.title_id
                #     )
                #     """,
                #     nominee_ids,
                # )

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

                # cur.executemany(
                #     """
                #     WITH deleted_ne AS (
                #         DELETE FROM nominees_entities
                #         WHERE nominee_id = %(nominee_id)s
                #         RETURNING entity_id
                #     )
                #     DELETE FROM entities
                #     WHERE id IN (
                #         SELECT entity_id FROM deleted_ne
                #     )
                #     AND NOT EXISTS (
                #         SELECT 1
                #         FROM nominees_entities ne
                #         WHERE entities.id = ne.entity_id
                #     )
                #     """,
                #     nominee_ids,
                # )

                # delete from nominees
                cur.execute(
                    """
                    DELETE FROM nominees
                    WHERE id = %s
                    """,
                    (nominee.id,),
                )


def get_category_groups() -> list[str]:
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        with con.cursor() as cur:
            cur.execute(
                """
                SELECT name
                FROM category_groups
                WHERE award = 'oscar'
                """
            )
            return [r[0] for r in cur.fetchall()]


def get_categories() -> list[str]:
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        with con.cursor() as cur:
            cur.execute(
                """
                SELECT name
                FROM categories
                WHERE award = 'oscar'
                """
            )
            return [r[0] for r in cur.fetchall()]


def get_category_names_official(edition: int | None = None) -> list[str]:
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        with con.cursor() as cur:
            if edition is None:
                cur.execute(
                    """
                    SELECT official_name
                    FROM category_names
                    WHERE award = 'oscar'
                    """
                )
            else:
                cur.execute(
                    """
                    SELECT cn.official_name
                    FROM category_names cn
                    JOIN editions_category_names ecn ON ecn.category_name_id = cn.id
                    JOIN editions e ON e.id = ecn.edition_id
                    WHERE cn.award = 'oscar' AND e.iteration = %s
                    """,
                    (edition,),
                )
            return [r[0] for r in cur.fetchall()]


def get_matched_categories_by_edition(edition: int) -> list[MatchedCategory]:
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        with con.cursor(row_factory=class_row(MatchedNominee)) as cur:  # type: ignore
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
                    category_name_to_matched_category[n.category_name] = (
                        MatchedCategory(category=n.category_name, nominees=[])
                    )
                category_name_to_matched_category[n.category_name].nominees.append(n)

            return list(category_name_to_matched_category.values())


def nominations_to_csv():
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv('PG_USER')} password={os.getenv('PG_PASSWORD')}",
        autocommit=True,
    ) as con:
        with con.cursor(row_factory=dict_row) as cur:
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


def init_db():
    drop_db()
    create_db()
    create_tables()
    create_indexes()
    insert_editions()
    insert_categories()
    data = match.match_categories()
    matched_nominees = [n for ed in data for c in data[ed] for n in c.nominees]
    insert_nominees(matched_nominees)


if __name__ == "__main__":
    init_db()
