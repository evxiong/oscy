from ..dependencies import pool
from ..models.entity_title import (
    EntityOrTitle,
    Rankings,
    OverallRankings,
    CategoryGroupRankings,
    CategoryRankings,
    RankingsRow,
)
from ..models.nominations import EditionRow
from .nominations import edition_rows_to_editions
from fastapi import APIRouter
from psycopg.rows import class_row

router = APIRouter(tags=["entities and titles"])


@router.get("/entities/{id}", summary="Get entity by id")
async def get_entity_by_id(id: int) -> EntityOrTitle | None:
    async with pool.connection() as con:
        async with con.cursor(row_factory=class_row(RankingsRow)) as cur:  # type: ignore
            await cur.execute(
                """
                WITH a AS (
                    SELECT
                        en.id,
                        en.imdb_id,
                        en.type,
                        en.name,
                        cg.id AS category_group_id,
                        cg.name AS category_group,
                        c.id AS category_id,
                        c.name AS category,
                        SUM(CASE WHEN n.stat = TRUE THEN 1 ELSE 0 END) AS category_noms,
                        SUM(CASE WHEN n.winner = TRUE THEN 1 ELSE 0 END) AS category_wins,
                        SUM(SUM(CASE WHEN n.stat = TRUE THEN 1 ELSE 0 END)) OVER (PARTITION BY en.id, cg.id) AS category_group_noms,
                        SUM(SUM(CASE WHEN n.winner = TRUE THEN 1 ELSE 0 END)) OVER (PARTITION BY en.id, cg.id) AS category_group_wins,
                        SUM(SUM(CASE WHEN n.stat = TRUE THEN 1 ELSE 0 END)) OVER (PARTITION BY en.id) AS overall_noms,
                        SUM(SUM(CASE WHEN n.winner = TRUE THEN 1 ELSE 0 END)) OVER (PARTITION BY en.id) AS overall_wins
                    FROM category_names cn
                    JOIN categories c ON c.id = cn.category_id
                    JOIN category_groups cg ON cg.id = c.category_group_id
                    JOIN editions_category_names ecn ON cn.id = ecn.category_name_id
                    JOIN editions e ON e.id = ecn.edition_id
                    JOIN nominees n ON n.edition_id = e.id AND n.category_name_id = cn.id
                    JOIN nominees_entities ne ON ne.nominee_id = n.id
                    JOIN entities en ON ne.entity_id = en.id
                    GROUP BY en.id, en.imdb_id, en.type, en.name, cg.id, cg.name, c.id, c.name
                ), b AS (
                    SELECT id, category_group_id, category_group_noms, category_group_wins		
                    FROM a
                    GROUP BY id, category_group_id, category_group_noms, category_group_wins
                ), c AS (
                    SELECT
                        id, category_group_id,
                        rank() OVER (PARTITION BY b.category_group_id ORDER BY b.category_group_noms DESC) AS category_group_noms_rank,
                        rank() OVER (PARTITION BY b.category_group_id ORDER BY b.category_group_wins DESC) AS category_group_wins_rank
                    FROM b
                ), d AS (
                    SELECT id, overall_noms, overall_wins		
                    FROM a
                    GROUP BY id, overall_noms, overall_wins
                ), e AS (
                    SELECT
                        id,
                        rank() OVER (ORDER BY overall_noms DESC) AS overall_noms_rank,
                        rank() OVER (ORDER BY overall_wins DESC) AS overall_wins_rank
                    FROM d
                ), f AS (
                    SELECT
                        a.id, a.imdb_id, a.type, a.name,
                        overall_noms, overall_wins, overall_noms_rank, overall_wins_rank,
                        a.category_group_id, category_group, category_group_noms, category_group_wins, category_group_noms_rank, category_group_wins_rank,
                        category_id, category, category_noms, category_wins,
                        rank() OVER (PARTITION BY category_id ORDER BY category_noms DESC) AS category_noms_rank,
                        rank() OVER (PARTITION BY category_id ORDER BY category_wins DESC) AS category_wins_rank
                    FROM a
                    JOIN c ON a.id = c.id AND a.category_group_id = c.category_group_id
                    JOIN e ON a.id = e.id
                )
                SELECT *
                FROM f
                WHERE id = %s
                ORDER BY category_id;
                """,
                (id,),
            )
            rankings_rows: list[RankingsRow] = await cur.fetchall()  # type: ignore

            if not rankings_rows:
                return None

            imdb_id = rankings_rows[0].imdb_id
            type = rankings_rows[0].type
            name = rankings_rows[0].name
            rankings = rankings_rows_to_rankings(rankings_rows)

        async with con.cursor(row_factory=class_row(EditionRow)) as cur:  # type: ignore
            await cur.execute(
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
                JOIN nominees_entities ne ON ne.nominee_id = n.id
                JOIN entities en ON en.id = ne.entity_id
                LEFT JOIN nominees_titles nt ON nt.nominee_id = n.id -- some nominations have no associated title
                LEFT JOIN titles t ON nt.title_id = t.id
                WHERE n.id IN (
                    SELECT nominee_id
                    FROM nominees_entities
                    WHERE nominees_entities.entity_id = %s
                )
                ORDER BY e.iteration ASC, cn.official_name ASC, n.winner DESC, n.id ASC, ne.statement_ind ASC, nt.winner DESC;
                """,
                (id,),
            )
            rows: list[EditionRow] = await cur.fetchall()  # type: ignore
            editions = edition_rows_to_editions(rows, "")

            if not editions:
                return None

            aliases = [
                p.name
                for e in editions
                for c in e.categories
                for n in c.nominees
                for p in n.people
                if p.imdb_id == imdb_id
            ]

        return EntityOrTitle(
            id=id,
            imdb_id=imdb_id,
            type=type,
            name=name,
            aliases=list(set(aliases)),
            total_noms=sum(e.edition_noms for e in editions),
            total_wins=sum(e.edition_wins for e in editions),
            nominations=editions,
            rankings=rankings,
        )


@router.get("/titles/{id}", summary="Get title by id")
async def get_title_by_id(id: int) -> EntityOrTitle | None:
    async with pool.connection() as con:
        async with con.cursor(row_factory=class_row(RankingsRow)) as cur:  # type: ignore
            await cur.execute(
                """
                WITH a AS (
                    SELECT
                        t.id,
                        t.imdb_id,
                        'title' AS type,
                        t.title AS name,
                        cg.id AS category_group_id,
                        cg.name AS category_group,
                        c.id AS category_id,
                        c.name AS category,
                        SUM(CASE WHEN n.stat = TRUE THEN 1 ELSE 0 END) AS category_noms,
                        SUM(CASE WHEN nt.winner = TRUE THEN 1 ELSE 0 END) AS category_wins,
                        SUM(SUM(CASE WHEN n.stat = TRUE THEN 1 ELSE 0 END)) OVER (PARTITION BY t.id, cg.id) AS category_group_noms,
                        SUM(SUM(CASE WHEN nt.winner = TRUE THEN 1 ELSE 0 END)) OVER (PARTITION BY t.id, cg.id) AS category_group_wins,
                        SUM(SUM(CASE WHEN n.stat = TRUE THEN 1 ELSE 0 END)) OVER (PARTITION BY t.id) AS overall_noms,
                        SUM(SUM(CASE WHEN nt.winner = TRUE THEN 1 ELSE 0 END)) OVER (PARTITION BY t.id) AS overall_wins
                    FROM category_names cn
                    JOIN categories c ON c.id = cn.category_id
                    JOIN category_groups cg ON cg.id = c.category_group_id
                    JOIN editions_category_names ecn ON cn.id = ecn.category_name_id
                    JOIN editions e ON e.id = ecn.edition_id
                    JOIN nominees n ON n.edition_id = e.id AND n.category_name_id = cn.id
                    JOIN nominees_titles nt ON nt.nominee_id = n.id
                    JOIN titles t ON nt.title_id = t.id
                    GROUP BY t.id, t.imdb_id, type, t.title, cg.id, cg.name, c.id, c.name
                ), b AS (
                    SELECT id, category_group_id, category_group_noms, category_group_wins		
                    FROM a
                    GROUP BY id, category_group_id, category_group_noms, category_group_wins
                ), c AS (
                    SELECT
                        id, category_group_id,
                        rank() OVER (PARTITION BY b.category_group_id ORDER BY b.category_group_noms DESC) AS category_group_noms_rank,
                        rank() OVER (PARTITION BY b.category_group_id ORDER BY b.category_group_wins DESC) AS category_group_wins_rank
                    FROM b
                ), d AS (
                    SELECT id, overall_noms, overall_wins		
                    FROM a
                    GROUP BY id, overall_noms, overall_wins
                ), e AS (
                    SELECT
                        id,
                        rank() OVER (ORDER BY overall_noms DESC) AS overall_noms_rank,
                        rank() OVER (ORDER BY overall_wins DESC) AS overall_wins_rank
                    FROM d
                ), f AS (
                    SELECT
                        a.id, a.imdb_id, a.type, a.name,
                        overall_noms, overall_wins, overall_noms_rank, overall_wins_rank,
                        a.category_group_id, category_group, category_group_noms, category_group_wins, category_group_noms_rank, category_group_wins_rank,
                        category_id, category, category_noms, category_wins,
                        rank() OVER (PARTITION BY category_id ORDER BY category_noms DESC) AS category_noms_rank,
                        rank() OVER (PARTITION BY category_id ORDER BY category_wins DESC) AS category_wins_rank
                    FROM a
                    JOIN c ON a.id = c.id AND a.category_group_id = c.category_group_id
                    JOIN e ON a.id = e.id
                )
                SELECT *
                FROM f
                WHERE id = %s
                ORDER BY category_id;
                """,
                (id,),
            )
            rankings_rows: list[RankingsRow] = await cur.fetchall()  # type: ignore

            if not rankings_rows:
                return None

            imdb_id = rankings_rows[0].imdb_id
            type = rankings_rows[0].type
            name = rankings_rows[0].name
            rankings = rankings_rows_to_rankings(rankings_rows)

        async with con.cursor(row_factory=class_row(EditionRow)) as cur:  # type: ignore
            await cur.execute(
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
                JOIN nominees_titles nt ON nt.nominee_id = n.id
                JOIN titles t ON nt.title_id = t.id
                LEFT JOIN nominees_entities ne ON ne.nominee_id = n.id
                LEFT JOIN entities en ON en.id = ne.entity_id
                WHERE n.id IN (
                    SELECT nominee_id
                    FROM nominees_titles
                    WHERE nominees_titles.title_id = %s
                )
                ORDER BY e.iteration ASC, cn.official_name ASC, n.winner DESC, n.id ASC, ne.statement_ind ASC, nt.winner DESC;
                """,
                (id,),
            )
            rows: list[EditionRow] = await cur.fetchall()  # type: ignore
            editions = edition_rows_to_editions(rows, imdb_id)

            if not editions:
                return None

            aliases = [
                t.title
                for t in editions[0].categories[0].nominees[0].titles
                if t.imdb_id == imdb_id
            ]

        return EntityOrTitle(
            id=id,
            imdb_id=imdb_id,
            type=type,
            name=name,
            aliases=list(set(aliases)),
            total_noms=sum(e.edition_noms for e in editions),
            total_wins=sum(e.edition_wins for e in editions),
            nominations=editions,
            rankings=rankings,
        )


@router.get("/imdb/{imdb_id}", summary="Get entity or title by IMDb id")
async def get_entity_or_title_by_imdb_id(imdb_id: str) -> EntityOrTitle | None:
    async with pool.connection() as con:
        async with con.cursor() as cur:
            if imdb_id.startswith("tt"):
                await cur.execute(
                    """
                    SELECT id
                    FROM titles
                    WHERE imdb_id = %s
                    """,
                    (imdb_id,),
                )
            else:
                await cur.execute(
                    """
                    SELECT id
                    FROM entities
                    WHERE imdb_id = %s
                    """,
                    (imdb_id,),
                )
            res = await cur.fetchall()
            if not res:
                return None
            id: int = res[0][0]

    return (
        await get_title_by_id(id)
        if imdb_id.startswith("tt")
        else await get_entity_by_id(id)
    )


def rankings_rows_to_rankings(rankings_rows: list[RankingsRow]) -> Rankings:
    rankings = Rankings(
        category_rankings=[],
        category_group_rankings=[],
        overall_rankings=OverallRankings(
            overall_noms=rankings_rows[0].overall_noms,
            overall_wins=rankings_rows[0].overall_wins,
            overall_noms_rank=rankings_rows[0].overall_noms_rank,
            overall_wins_rank=rankings_rows[0].overall_wins_rank,
        ),
    )
    seen_cg_ids = set()
    for row in rankings_rows:
        rankings.category_rankings.append(
            CategoryRankings(
                category_id=row.category_id,
                category=row.category,
                category_noms=row.category_noms,
                category_wins=row.category_wins,
                category_noms_rank=row.category_noms_rank,
                category_wins_rank=row.category_wins_rank,
            )
        )
        if row.category_group_id not in seen_cg_ids:
            rankings.category_group_rankings.append(
                CategoryGroupRankings(
                    category_group_id=row.category_group_id,
                    category_group=row.category_group,
                    category_group_noms=row.category_group_noms,
                    category_group_wins=row.category_group_wins,
                    category_group_noms_rank=row.category_group_noms_rank,
                    category_group_wins_rank=row.category_group_wins_rank,
                )
            )
            seen_cg_ids.add(row.category_group_id)

    return rankings
