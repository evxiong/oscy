import os
from ..dependencies import pool
from ..enums import FilterAwardType, SortType
from ..models.nominations import (
    Nominations,
    Edition,
    AggStats,
    EntityStats,
    TitleStats,
    EditionRow,
    Category,
    Nominee,
    NomineePerson,
    NomineeTitle,
)
from collections import defaultdict
from fastapi import APIRouter, Query
from psycopg import sql
from psycopg.rows import class_row
from typing import Annotated


router = APIRouter(tags=["nominations"])


@router.get("/", summary="Get nominations")
async def get_nominations(
    award: FilterAwardType = FilterAwardType.all,
    start_edition: Annotated[int, Query(ge=1, description="(inclusive)")] = 1,
    end_edition: Annotated[int, Query(description="(inclusive)")] = int(
        os.getenv("CURRENT_EDITION")  # type: ignore
    ),
    winners_only: bool = False,
    pending: Annotated[
        bool | None,
        Query(
            description=(
                """Include both pending and decided nominations (default), only
                pending (true), or only decided (false)."""
            )
        ),
    ] = None,
    categories: Annotated[
        str | None,
        Query(
            description=(
                """Comma-separated list of categories to filter by (must match
                `/categories`), ex. `Actor,International Feature,Actress`.
                Defaults to all categories."""
            ),
        ),
    ] = None,
    category_groups: Annotated[
        str | None,
        Query(
            description=(
                """Comma-separated list of category groups to filter by (must
                match `/categories`), ex. `Acting,Directing`. Defaults to all
                category groups."""
            ),
        ),
    ] = None,
    sort_editions: Annotated[
        SortType,
        Query(description=("Controls order of editions in returned object.")),
    ] = SortType.ASC,
    sort_categories: Annotated[
        SortType,
        Query(
            description=(
                """Controls order of categories within each edition in returned
                object. Sorting uses official category names, such as `WRITING
                (Original Screenplay)`."""
            )
        ),
    ] = SortType.ASC,
) -> Nominations:
    """
    Returned stats include all titles and entities matching the filtering
    criteria (no limit/pagination).

    `stats.title_stats` contains one element per title and is sorted by `noms`,
    then `wins`.

    `stats.entity_stats` contains one element per unique entity/category
    combination and is sorted by `total_noms`, then `total_wins`.

    Example use cases:
    - Who's won the most Oscars for Acting since 2000?
    > /?award=oscar&start_edition=72&category_groups=Acting
    - Which films have received the most nominations all-time?
    > /?award=oscar
    - Get winners from the 96th Academy Awards.
    > /?award=oscar&start_edition=96&end_edition=96&winners_only=true
    """
    async with pool.connection() as con:
        async with con.cursor(row_factory=class_row(EditionRow)) as cur:  # type: ignore
            filter_c_bool = True if categories else False
            filter_c = (
                [c.strip() for c in categories.split(",")] if categories else None
            )
            filter_cg_bool = True if category_groups else False
            filter_cg = (
                [cg.strip() for cg in category_groups.split(",")]
                if category_groups
                else None
            )

            order_clause = sql.SQL(
                "ORDER BY {}, n.winner DESC, n.id ASC, ne.statement_ind ASC, nt.winner DESC"
            ).format(
                sql.SQL(", ").join(
                    [
                        sql.SQL(" ").join(
                            [
                                sql.Identifier("e", "iteration"),
                                sql.SQL(sort_editions.name),
                            ]
                        ),
                        sql.SQL(" ").join(
                            [
                                sql.Identifier("cn", "official_name"),
                                sql.SQL(sort_categories.name),
                            ]
                        ),
                    ]
                )
            )

            await cur.execute(
                sql.SQL(
                    """
                    SELECT
                        e.id AS edition_id,
                        e.iteration,
                        e.official_year,
                        e.ceremony_date,
                        c.id AS category_id,
                        cn.id AS category_name_id,
                        cg.name AS category_group,
                        cn.official_name,
                        cn.common_name,
                        c.name AS short_name,
                        n.id AS nominee_id,
                        n.winner,
                        t.id AS title_id,
                        t.title,
                        t.imdb_id AS title_imdb_id,
                        nt.detail,
                        nt.winner AS title_winner,
                        en.id AS person_id,
                        ne.name,
                        en.imdb_id AS person_imdb_id,
                        ne.statement_ind,
                        n.statement,
                        n.is_person,
                        n.note,
                        n.official,
                        n.stat,
                        n.pending
                    FROM category_names cn
                    JOIN categories c ON c.id = cn.category_id
                    JOIN category_groups cg ON cg.id = c.category_group_id
                    JOIN editions_category_names ecn ON cn.id = ecn.category_name_id
                    JOIN editions e ON e.id = ecn.edition_id
                    JOIN nominees n ON n.edition_id = e.id AND n.category_name_id = cn.id
                    LEFT JOIN nominees_entities ne ON ne.nominee_id = n.id
                    LEFT JOIN entities en ON en.id = ne.entity_id
                    LEFT JOIN nominees_titles nt ON nt.nominee_id = n.id -- some nominations have no associated title
                    LEFT JOIN titles t ON nt.title_id = t.id
                    WHERE
                        (%(award)s::award_type IS NULL OR n.award = %(award)s) AND
                        e.iteration >= %(start_edition)s AND
                        e.iteration <= %(end_edition)s AND
                        (%(winners_only)s = FALSE OR n.winner = TRUE) AND
                        (%(filter_c_bool)s = FALSE OR c.name = ANY(%(filter_c)s)) AND
                        (%(filter_cg_bool)s = FALSE OR cg.name = ANY(%(filter_cg)s)) AND
                        (%(pending)s::boolean IS NULL OR (%(pending)s = FALSE AND n.pending = FALSE) OR (%(pending)s = TRUE AND n.pending = TRUE))
                    {}
                    """
                ).format(order_clause),
                {
                    "award": award if award != FilterAwardType.all else None,
                    "start_edition": start_edition,
                    "end_edition": end_edition,
                    "winners_only": winners_only,
                    "filter_c_bool": filter_c_bool,
                    "filter_c": filter_c,
                    "filter_cg_bool": filter_cg_bool,
                    "filter_cg": filter_cg,
                    "pending": pending,
                },
            )
            rows: list[EditionRow] = await cur.fetchall()  # type: ignore
            editions: list[Edition] = edition_rows_to_editions(rows, "")

        async with con.cursor(row_factory=class_row(EntityStats)) as cur:  # type: ignore
            await cur.execute(
                """
                SELECT id, imdb_id, aliases, category_id, category_noms, category_wins, total_noms, total_wins, career_category_noms, career_category_wins, career_total_noms, career_total_wins
                FROM (
                    SELECT
                        en.id,
                        en.imdb_id,
                        array_agg(DISTINCT ne.name) AS aliases,
                        cg.id AS category_group_id,
                        cg.name AS category_group,
                        c.id AS category_id,
                        c.name AS category,
                        SUM(CASE WHEN n.stat = TRUE AND e.iteration >= %(start_edition)s AND e.iteration <= %(end_edition)s THEN 1 ELSE 0 END) AS category_noms,
                        SUM(CASE WHEN n.winner = TRUE AND e.iteration >= %(start_edition)s AND e.iteration <= %(end_edition)s THEN 1 ELSE 0 END) AS category_wins,
                        SUM(SUM(CASE WHEN n.stat = TRUE AND e.iteration >= %(start_edition)s AND e.iteration <= %(end_edition)s THEN 1 ELSE 0 END)) OVER (PARTITION BY en.id) AS total_noms,
                        SUM(SUM(CASE WHEN n.winner = TRUE AND e.iteration >= %(start_edition)s AND e.iteration <= %(end_edition)s THEN 1 ELSE 0 END)) OVER (PARTITION BY en.id) AS total_wins,
                        SUM(CASE WHEN n.stat = TRUE THEN 1 ELSE 0 END) AS career_category_noms,
                        SUM(CASE WHEN n.winner = TRUE THEN 1 ELSE 0 END) AS career_category_wins,
                        SUM(SUM(CASE WHEN n.stat = TRUE THEN 1 ELSE 0 END)) OVER (PARTITION BY en.id) AS career_total_noms,
                        SUM(SUM(CASE WHEN n.winner = TRUE THEN 1 ELSE 0 END)) OVER (PARTITION BY en.id) AS career_total_wins,
                        SUM(CASE WHEN e.iteration >= %(start_edition)s AND e.iteration <= %(end_edition)s THEN 1 ELSE 0 END) > 0 AS valid
                    FROM category_names cn
                    JOIN categories c ON c.id = cn.category_id
                    JOIN category_groups cg ON cg.id = c.category_group_id
                    JOIN editions_category_names ecn ON cn.id = ecn.category_name_id
                    JOIN editions e ON e.id = ecn.edition_id
                    JOIN nominees n ON n.edition_id = e.id AND n.category_name_id = cn.id
                    JOIN nominees_entities ne ON ne.nominee_id = n.id
                    JOIN entities en ON ne.entity_id = en.id
                    WHERE
                        (%(award)s::award_type IS NULL OR n.award = %(award)s) AND
                        (%(winners_only)s = FALSE OR n.winner = TRUE) AND
                        (%(pending)s::boolean IS NULL OR (%(pending)s = FALSE AND n.pending = FALSE) OR (%(pending)s = TRUE AND n.pending = TRUE))
                    GROUP BY en.id, en.imdb_id, cg.id, cg.name, c.id, c.name
                )
                WHERE
                    valid = TRUE AND
                    (%(filter_c_bool)s = FALSE OR category = ANY(%(filter_c)s)) AND
                    (%(filter_cg_bool)s = FALSE OR category_group = ANY(%(filter_cg)s))
                ORDER BY total_noms DESC, total_wins DESC, aliases[0] ASC;
                """,
                {
                    "award": award if award != FilterAwardType.all else None,
                    "start_edition": start_edition,
                    "end_edition": end_edition,
                    "winners_only": winners_only,
                    "filter_c_bool": filter_c_bool,
                    "filter_c": filter_c,
                    "filter_cg_bool": filter_cg_bool,
                    "filter_cg": filter_cg,
                    "pending": pending,
                },
            )
            entity_stats: list[EntityStats] = await cur.fetchall()  # type: ignore

        async with con.cursor(row_factory=class_row(TitleStats)) as cur:  # type: ignore
            await cur.execute(
                """
                SELECT
                    t.id,
                    t.imdb_id,
                    t.title,
                    SUM(CASE WHEN n.stat = TRUE THEN 1 ELSE 0 END) AS noms,
                    SUM(CASE WHEN nt.winner = TRUE THEN 1 ELSE 0 END) AS wins
                FROM category_names cn
                JOIN categories c ON c.id = cn.category_id
                JOIN category_groups cg ON cg.id = c.category_group_id
                JOIN editions_category_names ecn ON cn.id = ecn.category_name_id
                JOIN editions e ON e.id = ecn.edition_id
                JOIN nominees n ON n.edition_id = e.id AND n.category_name_id = cn.id
                JOIN nominees_titles nt ON nt.nominee_id = n.id
                JOIN titles t ON nt.title_id = t.id
                WHERE
                    (%(award)s::award_type IS NULL OR n.award = %(award)s) AND
                    e.iteration >= %(start_edition)s AND
                    e.iteration <= %(end_edition)s AND
                    (%(winners_only)s = FALSE OR n.winner = TRUE) AND
                    (%(filter_c_bool)s = FALSE OR c.name = ANY(%(filter_c)s)) AND
                    (%(filter_cg_bool)s = FALSE OR cg.name = ANY(%(filter_cg)s)) AND
                    (%(pending)s::boolean IS NULL OR (%(pending)s = FALSE AND n.pending = FALSE) OR (%(pending)s = TRUE AND n.pending = TRUE))
                GROUP BY t.id, t.imdb_id, t.title
                ORDER BY noms DESC, wins DESC
                """,
                {
                    "award": award if award != FilterAwardType.all else None,
                    "start_edition": start_edition,
                    "end_edition": end_edition,
                    "winners_only": winners_only,
                    "filter_c_bool": filter_c_bool,
                    "filter_c": filter_c,
                    "filter_cg_bool": filter_cg_bool,
                    "filter_cg": filter_cg,
                    "pending": pending,
                },
            )
            title_stats: list[TitleStats] = await cur.fetchall()  # type: ignore

    res = Nominations(
        editions=editions,
        stats=AggStats(title_stats=title_stats, entity_stats=entity_stats),
    )

    return res


def edition_rows_to_editions(rows: list[EditionRow], imdb_id: str) -> list[Edition]:
    res: list[Edition] = []  # list[Edition]

    edition_id_to_edition_row = defaultdict(list)  # edition id -> EditionRow
    for row in rows:
        edition_id_to_edition_row[row.edition_id].append(row)

    for edition_id in edition_id_to_edition_row:
        e_row_0 = edition_id_to_edition_row[edition_id][0]
        res.append(
            Edition(
                id=e_row_0.edition_id,
                iteration=e_row_0.iteration,
                official_year=e_row_0.official_year,
                ceremony_date=e_row_0.ceremony_date,
                edition_noms=0,
                edition_wins=0,
                categories=[],
            )
        )

        category_name_id_to_edition_row = defaultdict(list)
        for e_row in edition_id_to_edition_row[edition_id]:
            category_name_id_to_edition_row[e_row.category_name_id].append(e_row)

        for category_name_id in category_name_id_to_edition_row:
            c_row_0 = category_name_id_to_edition_row[category_name_id][0]
            res[-1].categories.append(
                Category(
                    category_id=c_row_0.category_id,
                    category_group=c_row_0.category_group,
                    official_name=c_row_0.official_name,
                    common_name=c_row_0.common_name,
                    short_name=c_row_0.short_name,
                    category_noms=0,
                    category_wins=0,
                    nominees=[],
                )
            )

            nominee_id_to_edition_row = defaultdict(list)
            for c_row in category_name_id_to_edition_row[category_name_id]:
                nominee_id_to_edition_row[c_row.nominee_id].append(c_row)

            for nominee_id in nominee_id_to_edition_row:
                n_row_0 = nominee_id_to_edition_row[nominee_id][0]
                res[-1].categories[-1].nominees.append(
                    Nominee(
                        winner=n_row_0.winner,
                        titles=[],
                        people=[],
                        statement=n_row_0.statement,
                        is_person=n_row_0.is_person,
                        note=n_row_0.note,
                        official=n_row_0.official,
                        stat=n_row_0.stat,
                        pending=n_row_0.pending,
                    )
                )
                if n_row_0.stat:
                    res[-1].edition_noms += 1
                    res[-1].categories[-1].category_noms += 1
                if not imdb_id.startswith("tt") and n_row_0.winner:
                    res[-1].edition_wins += 1
                    res[-1].categories[-1].category_wins += 1

                title_id_set = set()
                person_id_set = set()

                for n_row in nominee_id_to_edition_row[nominee_id]:
                    if (
                        n_row.title_id is not None
                        and n_row.title_id not in title_id_set
                    ):
                        res[-1].categories[-1].nominees[-1].titles.append(
                            NomineeTitle(
                                id=n_row.title_id,
                                title=n_row.title,
                                imdb_id=n_row.title_imdb_id,
                                detail=n_row.detail,
                                title_winner=n_row.title_winner,
                            )
                        )
                        if (
                            imdb_id.startswith("tt")
                            and n_row.title_imdb_id == imdb_id
                            and n_row.title_winner
                        ):
                            res[-1].edition_wins += 1
                            res[-1].categories[-1].category_wins += 1
                        title_id_set.add(n_row.title_id)

                    if (
                        n_row.person_id is not None
                        and n_row.person_id not in person_id_set
                    ):
                        res[-1].categories[-1].nominees[-1].people.append(
                            NomineePerson(
                                id=n_row.person_id,
                                name=n_row.name,
                                imdb_id=n_row.person_imdb_id,
                                statement_ind=n_row.statement_ind,
                            )
                        )
                        person_id_set.add(n_row.person_id)

    return res
