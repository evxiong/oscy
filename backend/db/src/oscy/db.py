import csv
import dataclasses
import os
import psycopg
import yaml
from . import match, scrape
from .data import MatchedCategory
from dotenv import load_dotenv
from psycopg import sql
from psycopg.rows import dict_row
from tqdm import tqdm

load_dotenv(override=True)

DB_NAME = os.getenv("PG_DBNAME") or ""

# official oscars ceremony page category name -> official name
OFFICIAL_PAGE_CONVERSIONS = {
    "Animated Short Film": "short film (animated)",
    "Live Action Short Film": "short film (live action)",
}


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


def create_indexes():
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv("PG_USER")} password={os.getenv("PG_PASSWORD")}",
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


def insert_editions_category_names(
    edition: int, data: dict[int, list[MatchedCategory]]
):
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv("PG_USER")} password={os.getenv("PG_PASSWORD")}",
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
                    "category_name": OFFICIAL_PAGE_CONVERSIONS.get(
                        c.category, c.category
                    ).lower(),
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


def insert_nominees(data: dict[int, list[MatchedCategory]]):
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
                nominee["category_name"] = OFFICIAL_PAGE_CONVERSIONS.get(
                    nominee["category_name"], nominee["category_name"]
                ).lower()
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


def get_category_names_official() -> list[str]:
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv("PG_USER")} password={os.getenv("PG_PASSWORD")}",
        autocommit=True,
    ) as con:
        with con.cursor() as cur:
            cur.execute("SELECT official_name FROM category_names")
            return [r[0] for r in cur.fetchall()]


def nominations_to_csv():
    with psycopg.connect(
        f"dbname={DB_NAME} user={os.getenv("PG_USER")} password={os.getenv("PG_PASSWORD")}",
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
    insert_nominees(match.match_categories())


if __name__ == "__main__":
    init_db()
