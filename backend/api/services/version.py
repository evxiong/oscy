from psycopg.rows import class_row

from ..dependencies import connect
from ..enums import AwardType
from ..models.version import Version


async def get_current_version(award: AwardType) -> Version | None:
    async with connect() as con:
        async with con.cursor(row_factory=class_row(Version)) as cur:  # type: ignore
            await cur.execute(
                """
                SELECT award, iteration, update_stage, updated_at, tag
                FROM current_versions
                WHERE award = %s
                """,
                (award,),
            )
            res: Version | None = await cur.fetchone()  # type: ignore
            return res
