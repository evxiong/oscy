from .nominations import Nominations
from pydantic import BaseModel


# for /categories
class CategoryRow(BaseModel):
    category_group_id: int
    category_group: str
    category_id: int
    category: str
    category_name_id: int
    official_name: str
    common_name: str


class CategoryName(BaseModel):
    category_name_id: int
    official_name: str
    common_name: str


class CategoryCategory(BaseModel):
    category_id: int
    category: str
    category_names: list[CategoryName]


class CategoryGroup(BaseModel):
    category_group_id: int
    category_group: str
    categories: list[CategoryCategory]


# for /categories/{id}
class CategoryNameInfo(BaseModel):
    category_name_id: int
    official_name: str
    common_name: str
    ranges: list[tuple[int, int]]  # iteration numbers, inclusive


class CategoryInfo(BaseModel):
    category_id: int
    category: str
    category_group_id: int
    category_group: str
    category_names: list[CategoryNameInfo]
    nominations: Nominations


class CategoryInfoRow(BaseModel):
    category_id: int
    category: str
    category_group_id: int
    category_group: str
    category_name_ids: list[int]
    official_names: list[str]
    common_names: list[str]
    ranges: list[list[int]]
