from enum import Enum


class AwardType(str, Enum):
    oscar = "oscar"
    emmy = "emmy"


class FilterAwardType(str, Enum):
    all = "all"
    oscar = "oscar"
    emmy = "emmy"


class FilterType(str, Enum):
    all = "all"
    title_ = "title"
    entity = "entity"


class FilterEntityType(str, Enum):
    all = "all"
    person = "person"
    company = "company"
    country = "country"
