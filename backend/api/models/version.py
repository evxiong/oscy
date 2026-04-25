from datetime import datetime

from pydantic import BaseModel

from ..enums import AwardType, UpdateType


class Version(BaseModel):
    award: AwardType
    iteration: int
    update_stage: UpdateType
    updated_at: datetime
    tag: str
