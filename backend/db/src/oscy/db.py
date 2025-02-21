import dataclasses
import os
import psycopg
import yaml
from . import match, scrape
from dotenv import load_dotenv, find_dotenv
from psycopg import sql
from tqdm import tqdm

load_dotenv()
load_dotenv(find_dotenv(".config"))

DB_NAME = os.getenv("PG_DBNAME") or ""


def create_db():
    with psycopg.connect(
        f"dbname=postgres user={os.getenv("PG_USER")} password={os.getenv("PG_PASSWORD")}",
        autocommit=True,
    ) as con:
        with con.cursor() as cur:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))

    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv("PG_USER")} password={os.getenv("PG_PASSWORD")}",
        autocommit=True,
    ) as con:
        with con.cursor() as cur:
            cur.execute("""CREATE TYPE award_type AS ENUM ('oscar', 'emmy')""")
            cur.execute(
                """CREATE TYPE entity_type AS ENUM ('person', 'company', 'country', 'network')"""
            )
            cur.execute("""CREATE EXTENSION IF NOT EXISTS pg_trgm""")


def drop_db():
    with psycopg.connect(
        f"dbname=postgres user={os.getenv("PG_USER")} password={os.getenv("PG_PASSWORD")}",
        autocommit=True,
    ) as con:
        with con.cursor() as cur:
            cur.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(DB_NAME))
            )


def create_tables():
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv("PG_USER")} password={os.getenv("PG_PASSWORD")}",
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
                        winner              boolean NOT NULL -- whether this particular title won (only important for 3rd oscars)
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
                        role                text NOT NULL -- entity's role on set (if applicable)
                )
                """
            )


def insert_editions(start: int | None = None, end: int | None = None) -> None:
    editions = scrape.scrape_editions(start, end)
    values = [dataclasses.asdict(e) for e in editions]
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv("PG_USER")} password={os.getenv("PG_PASSWORD")}"
    ) as con:
        with con.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO editions (award, iteration, official_year, ceremony_date)
                VALUES (%(award)s, %(iteration)s, %(official_year)s, %(ceremony_date)s);
            """,
                values,
            )


def insert_categories():
    with open("data/oscar_categories.yaml", encoding="utf-8") as fd:
        categories = yaml.safe_load(fd)

    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv("PG_USER")} password={os.getenv("PG_PASSWORD")}",
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


def insert_nominees():
    data = match.match_categories()

    # flatten to list of MatchedNominee dicts across all editions
    nominees = [
        dataclasses.asdict(n) for ed in data for c in data[ed] for n in c.nominees
    ]

    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv("PG_USER")} password={os.getenv("PG_PASSWORD")}",
        autocommit=True,
    ) as con:
        cur = con.cursor()
        with con.transaction():
            for nominee in tqdm(nominees):
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
                    WHERE e.award = 'oscar' AND e.iteration = %(edition)s AND cn.official_name = %(category_name)s
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
                def imdb_id_to_entity_type(id: str) -> str:
                    if id.startswith("nm"):
                        return "person"
                    elif id.startswith("co"):
                        return "company"
                    elif id.startswith("cc"):
                        return "country"
                    else:
                        raise ValueError("IMDb id is invalid:", id)

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


def init_db():
    drop_db()
    create_db()
    create_tables()
    insert_editions()
    insert_categories()
    insert_nominees()


if __name__ == "__main__":
    init_db()
