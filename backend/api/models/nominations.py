from datetime import date
from pydantic import BaseModel


class NomineePerson(BaseModel):
    id: int | None
    name: str | None
    imdb_id: str | None
    statement_ind: int | None


class NomineeTitle(BaseModel):
    id: int | None
    title: str | None
    imdb_id: str | None
    detail: list[str] | None
    title_winner: bool | None


class Nominee(BaseModel):
    winner: bool
    titles: list[NomineeTitle]
    people: list[NomineePerson]
    statement: str
    is_person: bool
    note: str
    official: bool
    stat: bool
    pending: bool


class Category(BaseModel):
    category_id: int
    category_group: str
    official_name: str
    common_name: str
    short_name: str
    category_noms: int
    category_wins: int
    nominees: list[Nominee]


class TitleStats(BaseModel):
    id: int
    imdb_id: str
    title: str
    noms: int
    wins: int


class EntityStats(BaseModel):  # unique by combination of id, cat id
    id: int
    imdb_id: str
    aliases: list[str]
    category_id: int
    category_noms: int
    category_wins: int
    total_noms: int
    total_wins: int
    career_category_noms: int
    career_category_wins: int
    career_total_noms: int
    career_total_wins: int


class AggStats(BaseModel):
    title_stats: list[TitleStats]
    entity_stats: list[EntityStats]


class Edition(BaseModel):
    id: int
    iteration: int
    official_year: str
    ceremony_date: date
    edition_noms: int
    edition_wins: int
    categories: list[Category]


class Nominations(BaseModel):
    editions: list[Edition]
    stats: AggStats


class EditionRow(BaseModel):
    edition_id: int
    iteration: int
    official_year: str
    ceremony_date: date
    category_id: int
    category_name_id: int
    category_group: str
    official_name: str
    common_name: str
    short_name: str
    nominee_id: int
    winner: bool
    title_id: int | None
    title: str | None
    title_imdb_id: str | None
    detail: list[str] | None
    title_winner: bool | None
    person_id: int | None
    name: str | None
    person_imdb_id: str | None
    statement_ind: int | None
    statement: str
    is_person: bool
    note: str
    official: bool
    stat: bool
    pending: bool
