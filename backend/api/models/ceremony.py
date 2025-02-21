from ..enums import AwardType
from datetime import date
from pydantic import BaseModel


class CeremonyInfo(BaseModel):
    id: int
    award: AwardType
    iteration: int
    official_year: str
    ceremony_date: date
