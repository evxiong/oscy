from enum import Enum


class AwardType(str, Enum):
    oscar = "oscar"
    emmy = "emmy"


class SortType(str, Enum):
    ASC = "asc"
    DESC = "desc"


class FilterAwardType(str, Enum):
    all = "all"
    oscar = "oscar"
    emmy = "emmy"


class FilterType(str, Enum):
    all = "all"
    title_ = "title"
    entity = "entity"
    category = "category"
    ceremony = "ceremony"


class FilterEntityType(str, Enum):
    all = "all"
    person = "person"
    company = "company"
    country = "country"
