from ..dependencies import connect
from ..models.category import (
    CategoryGroup,
    CategoryCategory,
    CategoryName,
    CategoryRow,
    CategoryInfo,
    CategoryNameInfo,
    CategoryInfoRow,
)
from .nominations import get_nominations
from fastapi import APIRouter
from psycopg.rows import class_row

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", summary="Get category hierarchy")
async def get_category_hierarchy() -> list[CategoryGroup]:
    """
    oscy defines three levels in the category hierarchy, from broad to narrow:
    *category groups*, *categories*, and *category names*.

    *Category groups* group related categories. A single category can go by
    different names in different years. *Category name* refers to the actual
    name used at a given ceremony, while *category* refers to the underlying
    category, which remains unchanged.

    For example, the category group "Acting" includes the categories "Actor",
    "Supporting Actor", "Actress", and "Supporting Actress". The category
    "Actor" includes the category names "Best Actor" and "Best Actor in a
    Leading Role".

    This hierarchy allows oscy to compute aggregate stats at each level, and
    reconstruct a category's name history.
    """
    async with connect() as con:
        async with con.cursor(row_factory=class_row(CategoryRow)) as cur:  # type: ignore
            await cur.execute(
                """
                SELECT
                    cg.id AS category_group_id,
                    cg.name AS category_group,
                    c.id AS category_id,
                    c.name AS category,
                    cn.id AS category_name_id,
                    cn.official_name AS official_name,
                    cn.common_name AS common_name
                FROM category_groups cg
                JOIN categories c ON cg.id = c.category_group_id
                JOIN category_names cn ON c.id = cn.category_id;
                """
            )

            rows: list[CategoryRow] = await cur.fetchall()  # type: ignore
            res: list[CategoryGroup] = []

            seen_cg_ids = set()
            seen_c_ids = set()
            seen_cn_ids = set()

            for row in rows:
                if row.category_group_id not in seen_cg_ids:
                    res.append(
                        CategoryGroup(
                            category_group_id=row.category_group_id,
                            category_group=row.category_group,
                            categories=[],
                        )
                    )
                    seen_cg_ids.add(row.category_group_id)

                if row.category_id not in seen_c_ids:
                    res[-1].categories.append(
                        CategoryCategory(
                            category_id=row.category_id,
                            category=row.category,
                            category_names=[],
                        )
                    )
                    seen_c_ids.add(row.category_id)

                if row.category_name_id not in seen_cn_ids:
                    res[-1].categories[-1].category_names.append(
                        CategoryName(
                            category_name_id=row.category_name_id,
                            official_name=row.official_name,
                            common_name=row.common_name,
                        )
                    )
                    seen_cn_ids.add(row.category_name_id)

    return res


@router.get("/{id}", summary="Get category by id")
async def get_category_by_id(id: int) -> CategoryInfo | None:
    async with connect() as con:
        async with con.cursor(row_factory=class_row(CategoryInfoRow)) as cur:  # type: ignore
            await cur.execute(
                """
                SELECT
                    cg.id AS category_group_id,
                    cg.name AS category_group,
                    c.id AS category_id,
                    c.name AS category,
                    json_agg(cni.category_name_id ORDER BY cni.category_name_id) AS category_name_ids,
                    json_agg(cni.official_name ORDER BY cni.category_name_id) AS official_names,
                    json_agg(cni.common_name ORDER BY cni.category_name_id) AS common_names,
                    json_agg(cni.r ORDER BY cni.category_name_id) AS ranges
                FROM (
                    SELECT
                        cn.id AS category_name_id,
                        cn.official_name AS official_name,
                        cn.common_name AS common_name,
                        json_agg(iteration) AS r,
                        cn.category_id AS category_id -- for the join
                    FROM category_names cn
                    JOIN editions_category_names ecn ON ecn.category_name_id = cn.id
                    JOIN editions e ON e.id = ecn.edition_id
                    GROUP BY cn.id, cn.official_name, cn.common_name, cn.category_id
                ) cni
                JOIN categories c ON c.id = cni.category_id
                JOIN category_groups cg ON cg.id = c.category_group_id
                WHERE category_id = %s
                GROUP BY c.id, c.name, cg.id, cg.name;
                """,
                (id,),
            )
            rows: list[CategoryInfoRow] = await cur.fetchall()  # type: ignore
            if not rows:
                return None
            row: CategoryInfoRow = rows[0]

    nominations = await get_nominations(categories=row.category)

    category_info = CategoryInfo(
        category_id=row.category_id,
        category=row.category,
        category_group_id=row.category_group_id,
        category_group=row.category_group,
        category_names=[],
        nominations=nominations,
    )

    for i in range(len(row.category_name_ids)):
        c = CategoryNameInfo(
            category_name_id=row.category_name_ids[i],
            official_name=row.official_names[i],
            common_name=row.common_names[i],
            ranges=[],
        )
        iterations = row.ranges[i]
        start = iterations[0]
        for ind in range(1, len(iterations)):
            if iterations[ind] != iterations[ind - 1] + 1:
                c.ranges.append((start, iterations[ind - 1]))
                start = iterations[ind]
        c.ranges.append((start, iterations[-1]))
        category_info.category_names.append(c)

    return category_info
