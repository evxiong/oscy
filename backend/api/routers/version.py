from fastapi import APIRouter

from ..enums import AwardType
from ..models.version import Version
from ..services.version import get_current_version

router = APIRouter(tags=["version"])


@router.get("/version", summary="Get current data version")
async def get_version(award: AwardType = AwardType.oscar) -> Version | None:
    """
    The returned tag identifies the current version of the award's data, which
    is useful for caching. This tag is updated alongside any data update, and is
    included by the API as an `ETag` response header in all other routes.
    """
    return await get_current_version(award)
