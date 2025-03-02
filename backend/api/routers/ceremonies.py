from ..dependencies import connect
from ..models.ceremony import CeremonyInfo
from ..models.nominations import Nominations
from .nominations import get_nominations
from fastapi import APIRouter
from psycopg.rows import class_row, dict_row


router = APIRouter(prefix="/ceremonies", tags=["ceremonies"])


@router.get("", summary="Get all ceremonies")
async def list_ceremonies() -> list[CeremonyInfo]:
    async with connect() as con:
        async with con.cursor(row_factory=class_row(CeremonyInfo)) as cur:  # type: ignore
            await cur.execute(
                """
                SELECT id, award, iteration, official_year, ceremony_date
                FROM editions
                ORDER BY iteration ASC;
                """
            )
            res: list[CeremonyInfo] = await cur.fetchall()  # type: ignore
    return res


@router.get("/{id}", summary="Get ceremony by id")
async def get_ceremony_by_id(id: int) -> Nominations | None:
    async with connect() as con:
        async with con.cursor(row_factory=dict_row) as cur:  # type: ignore
            await cur.execute(
                """
                SELECT award, iteration
                FROM editions
                WHERE id = %s
                ORDER BY iteration ASC;
                """,
                (id,),
            )
            res = await cur.fetchall()

            if not res:
                return None

    return await get_nominations(
        award=res[0]["award"],
        start_edition=res[0]["iteration"],
        end_edition=res[0]["iteration"],
    )
