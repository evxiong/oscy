import os
from ..dependencies import pool
from ..enums import FilterAwardType, FilterType, FilterEntityType
from ..models.search import (
    SearchResults,
    SearchGroup,
    TitleResult,
    EntityResult,
    CategoryResult,
    CeremonyResult,
    EntityResultRow,
)
from fastapi import APIRouter, Query
from psycopg.rows import class_row
from typing import Annotated

router = APIRouter(prefix="/search", tags=["search"])


# search entities (all aliases), titles, categories (groups, categories,
# category names), ceremonies (date, official year, iteration/ordinal)
@router.get("", summary="Search titles, entities, categories, and ceremonies")
async def search_all(
    page: int = Query(default=1, ge=1),
    award: FilterAwardType = FilterAwardType.all,
    type: FilterType = FilterType.all,
    entity_type: FilterEntityType = FilterEntityType.all,
    query: str | None = None,
    min_noms: int = Query(default=0, ge=0),
    max_noms: int | None = Query(default=None, ge=0),
    min_wins: int = Query(default=0, ge=0),
    max_wins: int | None = Query(default=None, ge=0),
    noms_eq_wins: bool | None = None,
    noms_in_categories: str | None = None,
    # comma-separated list of categories. to be returned, the entity/title must have received
    # at least one nomination in each category
    no_noms_in_categories: str | None = None,
    # comma-separated list of categories. to be returned, the entity/title must have received
    # zero nominations in each category
    wins_in_categories: str | None = None,
    # comma-separated list of categories. to be returned, the entity/title must have
    # at least one win in each category
    no_wins_in_categories: str | None = None,
    # comma-separated list of categories. to be returned, the entity/title must have
    # zero wins in each category
    single_ceremony: bool = False,
    # requires that all of the above conditions (min_noms to no_wins_in_categories) occur in single ceremony
    # (only impacts results of entity search)
    # pre-filtering
    start_edition: int = Query(default=1, ge=1),
    end_edition: int = int(os.getenv("CURRENT_EDITION")),  # type: ignore
    categories: Annotated[  # usage: search for all ppl with min_noms=1 across Actor,Director (this is diff from noms_in_categories, which requires at least 1 nom per category)
        str | None,
        Query(
            description="Comma-separated list of categories to filter by (must match `/categories`), ex. `Actor,International Feature,Actress`. Defaults to all categories. ",
        ),
    ] = None,
    category_groups: Annotated[
        str | None,
        Query(
            description="Comma-separated list of category groups to filter by (must match `/categories`), ex. `Acting,Directing`. Defaults to all category groups.",
        ),
    ] = None,
    # sort results by
    # sort_search_results_by: SortByResults = SortByResults.default,
    # sort nominations by
    # sort_editions_by: SortByDate = SortByDate.asc,
    # sort_categories_by: SortByName = SortByName.asc,
    # sort_nominees_by: SortByName = SortByName.id,
    # sort_winners_first: bool = True,
) -> SearchResults:
    """
    Results are sorted primarily by text match. Each page has up to 10 results.

    Example use cases:
    - Get people who have received at least 2 nominations in a single ceremony.
    > /search?award=oscar&type=entity&entity_type=person&min_noms=2&single_ceremony=true
    - Get films that won all of their nominations.
    > /search?award=oscar&type=title&min_noms=1&noms_eq_wins=true
    - Get films nominated for Best Picture but not Best Director since 2000.
    > /search?award=oscar&type=title&noms_in_categories=Picture&no_noms_in_categories=Director&start_edition=72
    """
    async with pool.connection() as con:
        PAGE_SIZE = 10

        filter_c = (
            list({c.strip() for c in categories.split(",")}) if categories else None
        )
        filter_cg = (
            list({cg.strip() for cg in category_groups.split(",")})
            if category_groups
            else None
        )
        filter_nic = (
            list({c.strip() for c in noms_in_categories.split(",")})
            if noms_in_categories
            else None
        )
        filter_nnic = (
            list({c.strip() for c in no_noms_in_categories.split(",")})
            if no_noms_in_categories
            else None
        )
        filter_wic = (
            list({c.strip() for c in wins_in_categories.split(",")})
            if wins_in_categories
            else None
        )
        filter_nwic = (
            list({c.strip() for c in no_wins_in_categories.split(",")})
            if no_wins_in_categories
            else None
        )

        async with con.cursor(row_factory=class_row(TitleResult)) as cur:  # type: ignore
            titles_res: list[TitleResult] = []
            if type != FilterType.entity:
                await cur.execute(
                    """
                    SELECT
                        t.id,
                        t.imdb_id,
                        'title' AS type,
                        t.title,
                        array_agg(DISTINCT e.iteration) AS iterations,
                        SUM(CASE WHEN n.stat = TRUE THEN 1 ELSE 0 END) AS noms,
                        SUM(CASE WHEN nt.winner = TRUE THEN 1 ELSE 0 END) AS wins,
                        (CASE WHEN %(query)s::text IS NULL THEN 0+0 ELSE (%(query)s <<-> t.title) END) AS word_dist,
                        (CASE WHEN %(query)s::text IS NULL THEN 0+0 ELSE (%(query)s <-> t.title) END) AS dist
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
                        (%(query)s::text IS NULL OR %(query)s <%% t.title) AND
                        e.iteration >= %(start_edition)s AND
                        e.iteration <= %(end_edition)s AND
                        (%(filter_c)s::text[] IS NULL OR c.name = ANY(%(filter_c)s)) AND
                        (%(filter_cg)s::text[] IS NULL OR cg.name = ANY(%(filter_cg)s))
                    GROUP BY t.id, t.imdb_id, t.title
                    HAVING
                        SUM(CASE WHEN n.stat = TRUE THEN 1 ELSE 0 END) >= %(min_noms)s AND
                        (%(max_noms)s::integer IS NULL OR SUM(CASE WHEN n.stat = TRUE THEN 1 ELSE 0 END) <= %(max_noms)s) AND
                        SUM(CASE WHEN nt.winner = TRUE THEN 1 ELSE 0 END) >= %(min_wins)s AND
                        (%(max_wins)s::integer IS NULL OR SUM(CASE WHEN nt.winner = TRUE THEN 1 ELSE 0 END) <= %(max_wins)s) AND
                        (%(noms_eq_wins)s::boolean IS NULL OR
                        (%(noms_eq_wins)s = TRUE AND SUM(CASE WHEN n.stat = TRUE THEN 1 ELSE 0 END) = SUM(CASE WHEN nt.winner = TRUE THEN 1 ELSE 0 END)) OR
                        (%(noms_eq_wins)s = FALSE AND SUM(CASE WHEN n.stat = TRUE THEN 1 ELSE 0 END) != SUM(CASE WHEN nt.winner = TRUE THEN 1 ELSE 0 END))
                        ) AND
                        (%(noms_in_categories)s::text[] IS NULL OR array_agg(c.name) FILTER (WHERE n.stat = TRUE) @> %(noms_in_categories)s) AND
                        (%(no_noms_in_categories)s::text[] IS NULL OR array_agg(c.name) FILTER (WHERE n.stat = TRUE) && %(no_noms_in_categories)s = FALSE) AND
                        (%(wins_in_categories)s::text[] IS NULL OR array_agg(c.name) FILTER (WHERE nt.winner = TRUE) @> %(wins_in_categories)s) AND
                        (%(no_wins_in_categories)s::text[] IS NULL OR array_agg(c.name) FILTER (WHERE nt.winner = TRUE) && %(no_wins_in_categories)s = FALSE)
                    ORDER BY
                        word_dist,
                        dist,
                        noms DESC,
                        wins DESC
                    LIMIT %(limit)s
                    OFFSET %(offset)s;
                    """,
                    {
                        "award": award if award != FilterAwardType.all else None,
                        "query": query,
                        "min_noms": min_noms,
                        "max_noms": max_noms,
                        "min_wins": min_wins,
                        "max_wins": max_wins,
                        "noms_eq_wins": noms_eq_wins,
                        "noms_in_categories": filter_nic,
                        "no_noms_in_categories": filter_nnic,
                        "wins_in_categories": filter_wic,
                        "no_wins_in_categories": filter_nwic,
                        "start_edition": start_edition,
                        "end_edition": end_edition,
                        "filter_c": filter_c,
                        "filter_cg": filter_cg,
                        "limit": PAGE_SIZE + 1,
                        "offset": (page - 1) * PAGE_SIZE,
                    },
                )
                titles_res = await cur.fetchall()  # type: ignore

        async with con.cursor(row_factory=class_row(EntityResultRow)) as cur:  # type: ignore
            entities_res: list[EntityResult] = []
            if type != FilterType.title_:
                await cur.execute(
                    """
                    WITH a AS (
                        SELECT en.id, ARRAY_AGG(DISTINCT ne.name) AS aliases
                        FROM nominees_entities ne
                        JOIN entities en ON ne.entity_id = en.id
                        GROUP BY en.id
                    )
                    SELECT
                        en.id,
                        en.imdb_id,
                        en.type,
                        en.name,
                        a.aliases,
	                    cardinality(array_agg(array_agg(DISTINCT e.iteration)) OVER w) AS occurrences,
                        array_agg(array_agg(DISTINCT e.iteration)) OVER w AS iterations,
                        SUM(SUM(CASE WHEN n.stat = TRUE THEN 1 ELSE 0 END)) OVER w AS noms,
	                    SUM(SUM(CASE WHEN n.winner = TRUE THEN 1 ELSE 0 END)) OVER w AS wins,
                        (CASE WHEN %(query)s::text IS NULL THEN 0+0 ELSE (%(query)s <<-> en.name) END) AS word_dist,
                        (CASE WHEN %(query)s::text IS NULL THEN 0+0 ELSE (%(query)s <-> en.name) END) AS dist
                    FROM category_names cn
                    JOIN categories c ON c.id = cn.category_id
                    JOIN category_groups cg ON cg.id = c.category_group_id
                    JOIN editions_category_names ecn ON cn.id = ecn.category_name_id
                    JOIN editions e ON e.id = ecn.edition_id
                    JOIN nominees n ON n.edition_id = e.id AND n.category_name_id = cn.id
                    JOIN nominees_entities ne ON ne.nominee_id = n.id
                    JOIN entities en ON ne.entity_id = en.id
                    JOIN a ON a.id = en.id
                    WHERE
                        (%(award)s::award_type IS NULL OR n.award = %(award)s) AND
                        (%(entity_type)s::entity_type IS NULL OR en.type = %(entity_type)s) AND
                        (%(query)s::text IS NULL OR %(query)s <%% ANY(a.aliases)) AND
                        e.iteration >= %(start_edition)s AND
                        e.iteration <= %(end_edition)s AND
                        (%(filter_c)s::text[] IS NULL OR c.name = ANY(%(filter_c)s)) AND
                        (%(filter_cg)s::text[] IS NULL OR cg.name = ANY(%(filter_cg)s))
                    GROUP BY
                        (CASE WHEN %(single_ceremony)s = TRUE THEN e.id ELSE 0+0 END),
                        en.id,
                        en.imdb_id,
                        en.type,
                        en.name,
                        a.aliases
                    HAVING
                        SUM(CASE WHEN n.stat = TRUE THEN 1 ELSE 0 END) >= %(min_noms)s AND
                        (%(max_noms)s::integer IS NULL OR SUM(CASE WHEN n.stat = TRUE THEN 1 ELSE 0 END) <= %(max_noms)s) AND
                        SUM(CASE WHEN n.winner = TRUE THEN 1 ELSE 0 END) >= %(min_wins)s AND
                        (%(max_wins)s::integer IS NULL OR SUM(CASE WHEN n.winner = TRUE THEN 1 ELSE 0 END) <= %(max_wins)s) AND
                        (%(noms_eq_wins)s::boolean IS NULL OR
                        (%(noms_eq_wins)s = TRUE AND SUM(CASE WHEN n.stat = TRUE THEN 1 ELSE 0 END) = SUM(CASE WHEN n.winner = TRUE THEN 1 ELSE 0 END)) OR
                        (%(noms_eq_wins)s = FALSE AND SUM(CASE WHEN n.stat = TRUE THEN 1 ELSE 0 END) != SUM(CASE WHEN n.winner = TRUE THEN 1 ELSE 0 END))
                        ) AND
                        (%(noms_in_categories)s::text[] IS NULL OR array_agg(c.name) FILTER (WHERE n.stat = TRUE) @> %(noms_in_categories)s) AND
                        (%(no_noms_in_categories)s::text[] IS NULL OR array_agg(c.name) FILTER (WHERE n.stat = TRUE) && %(no_noms_in_categories)s = FALSE) AND
                        (%(wins_in_categories)s::text[] IS NULL OR array_agg(c.name) FILTER (WHERE n.winner = TRUE) @> %(wins_in_categories)s) AND
                        (%(no_wins_in_categories)s::text[] IS NULL OR array_agg(c.name) FILTER (WHERE n.winner = TRUE) && %(no_wins_in_categories)s = FALSE)
                    WINDOW w AS (PARTITION BY en.id)
                    ORDER BY
                        word_dist,
                        dist,
                        occurrences DESC,
                        noms DESC,
                        wins DESC
                    LIMIT %(limit)s
                    OFFSET %(offset)s;
                    """,
                    {
                        "award": award if award != FilterAwardType.all else None,
                        "entity_type": (
                            entity_type if entity_type != FilterEntityType.all else None
                        ),
                        "query": query,
                        "min_noms": min_noms,
                        "max_noms": max_noms,
                        "min_wins": min_wins,
                        "max_wins": max_wins,
                        "noms_eq_wins": noms_eq_wins,
                        "noms_in_categories": filter_nic,
                        "no_noms_in_categories": filter_nnic,
                        "wins_in_categories": filter_wic,
                        "no_wins_in_categories": filter_nwic,
                        "single_ceremony": single_ceremony,
                        "start_edition": start_edition,
                        "end_edition": end_edition,
                        "filter_c": filter_c,
                        "filter_cg": filter_cg,
                        "limit": PAGE_SIZE + 1,
                        "offset": (page - 1) * PAGE_SIZE,
                    },
                )
                temp: list[EntityResultRow] = await cur.fetchall()  # type: ignore
                entities_res: list[EntityResult] = [
                    EntityResult(
                        id=t.id,
                        imdb_id=t.imdb_id,
                        type=t.type,
                        name=t.name,
                        aliases=t.aliases,
                        occurrences=t.occurrences,
                        iterations=[i for sub in t.iterations for i in sub],
                        noms=t.noms,
                        wins=t.wins,
                        word_dist=t.word_dist,
                        dist=t.dist,
                    )
                    for t in temp
                ]

        async with con.cursor(row_factory=class_row(CategoryResult)) as cur:  # type: ignore
            categories_res: list[CategoryResult] = []
            if query is not None:
                await cur.execute(
                    """
                    WITH a AS (
                        SELECT
                            c.id,
                            c.name,
                            c.category_group_id,
                            array_agg(cn.official_name) AS official_names,
                            array_agg(cn.common_name) AS common_names
                        FROM categories c
                        JOIN category_names cn ON c.id = cn.category_id
                        GROUP BY c.id, c.name, c.category_group_id
                    )
                    SELECT
                        a.id AS id,
                        a.name AS category,
                        cg.id AS category_group_id,
                        cg.name AS category_group,
                        %(query)s <<-> (cg.name || ' ' || a.name || ' ' || array_to_string(a.official_names, ' ') || ' ' || array_to_string(a.common_names, ' ')) AS word_dist,
                        %(query)s <-> (cg.name || ' ' || a.name || ' ' || array_to_string(a.official_names, ' ') || ' ' || array_to_string(a.common_names, ' ')) AS dist
                    FROM category_groups cg
                    JOIN a ON a.category_group_id = cg.id
                    WHERE %(query)s <%% (cg.name || ' ' || a.name || ' ' || array_to_string(a.official_names, ' ') || ' ' || array_to_string(a.common_names, ' '))
                    ORDER BY word_dist, a.id
                    LIMIT %(limit)s
                    OFFSET %(offset)s;
                    """,
                    {
                        "query": query,
                        "limit": PAGE_SIZE + 1,
                        "offset": (page - 1) * PAGE_SIZE,
                    },
                )
                categories_res = await cur.fetchall()  # type: ignore

        async with con.cursor(row_factory=class_row(CeremonyResult)) as cur:  # type: ignore
            ceremonies_res: list[CeremonyResult] = []
            if query is not None:
                await cur.execute(
                    """
                    SELECT
                        id,
                        iteration,
                        official_year,
                        ceremony_date,
                        %(query)s <<-> (iteration || ' ' || iteration || 'th ' || iteration || 'rd ' || iteration || 'nd ' || iteration || 'st ' || official_year || to_char(ceremony_date, ' YYYY')) AS word_dist,
                        %(query)s <-> (iteration || ' ' || iteration || 'th ' || iteration || 'rd ' || iteration || 'nd ' || iteration || 'st ' || official_year || to_char(ceremony_date, ' YYYY')) AS dist
                    FROM editions
                    WHERE word_similarity(%(query)s, (iteration || ' ' || iteration || 'th ' || iteration || 'rd ' || iteration || 'nd ' || iteration || 'st ' || official_year || to_char(ceremony_date, ' YYYY'))) > 0.4
                    ORDER BY word_dist, dist
                    LIMIT %(limit)s
                    OFFSET %(offset)s;
                    """,
                    {
                        "query": query,
                        "limit": PAGE_SIZE + 1,
                        "offset": (page - 1) * PAGE_SIZE,
                    },
                )
                ceremonies_res = await cur.fetchall()  # type: ignore

        def res_to_search_group(res: list) -> SearchGroup:
            return SearchGroup(
                page=page,
                next_page=page + 1 if len(res) == PAGE_SIZE + 1 else None,
                page_size=PAGE_SIZE,
                length=(PAGE_SIZE if len(res) == PAGE_SIZE + 1 else len(res)),
                results=(res[:-1] if len(res) == PAGE_SIZE + 1 else res),
            )

        titles_obj = (
            res_to_search_group(titles_res) if type != FilterType.entity else None
        )
        entities_obj = (
            res_to_search_group(entities_res) if type != FilterType.title_ else None
        )
        categories_obj = (
            res_to_search_group(categories_res) if query is not None else None
        )
        ceremonies_obj = (
            res_to_search_group(ceremonies_res) if query is not None else None
        )

        res = SearchResults(
            titles=titles_obj,
            entities=entities_obj,
            categories=categories_obj,
            ceremonies=ceremonies_obj,
        )

    return res
