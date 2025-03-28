from datetime import date
from pydantic import BaseModel


class TitleResult(BaseModel):
    id: int
    imdb_id: str
    type: str
    title: str
    iterations: list[int]
    noms: int
    wins: int
    word_dist: float
    dist: float


class EntityResult(BaseModel):
    id: int
    imdb_id: str
    type: str
    name: str
    aliases: list[str]
    occurrences: int
    iterations: list[int]
    noms: int
    wins: int
    word_dist: float
    dist: float


class EntityResultRow(BaseModel):
    id: int
    imdb_id: str
    type: str
    name: str
    aliases: list[str]
    occurrences: int
    iterations: list[list[int]]
    noms: int
    wins: int
    word_dist: float
    dist: float


class CategoryResult(BaseModel):
    id: int
    category: str
    category_group_id: int
    category_group: str
    word_dist: float
    dist: float


class CeremonyResult(BaseModel):
    id: int
    iteration: int
    official_year: str
    ceremony_date: date
    word_dist: float
    dist: float


class SearchGroup(BaseModel):
    page: int
    next_page: int | None
    page_size: int
    length: int
    results: list


class TitleSearchGroup(SearchGroup):
    results: list[TitleResult]


class EntitySearchGroup(SearchGroup):
    results: list[EntityResult]


class CategorySearchGroup(SearchGroup):
    results: list[CategoryResult]


class CeremonySearchGroup(SearchGroup):
    results: list[CeremonyResult]


class SearchResults(BaseModel):
    titles: TitleSearchGroup
    entities: EntitySearchGroup
    categories: CategorySearchGroup
    ceremonies: CeremonySearchGroup
