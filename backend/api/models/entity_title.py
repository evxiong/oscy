from .nominations import Edition
from pydantic import BaseModel


class CategoryRankings(BaseModel):
    category_id: int
    category: str
    category_noms: int
    category_wins: int
    category_noms_rank: int
    category_wins_rank: int


class CategoryGroupRankings(BaseModel):
    category_group_id: int
    category_group: str
    category_group_noms: int
    category_group_wins: int
    category_group_noms_rank: int
    category_group_wins_rank: int


class OverallRankings(BaseModel):
    overall_noms: int
    overall_wins: int
    overall_noms_rank: int
    overall_wins_rank: int


class Rankings(BaseModel):
    category_rankings: list[CategoryRankings]
    category_group_rankings: list[CategoryGroupRankings]
    overall_rankings: OverallRankings


class EntityOrTitle(BaseModel):  # could be title, person, company, country
    id: int
    imdb_id: str
    type: str
    name: str
    aliases: list[str | None]
    total_noms: int
    total_wins: int
    nominations: list[Edition]
    rankings: Rankings
    # rankings: total noms (all and among same type), total wins (all and among same type), wins by cat, noms by cat


class RankingsRow(BaseModel):  # used for both entities and titles
    id: int
    imdb_id: str
    type: str
    name: str
    overall_noms: int
    overall_wins: int
    overall_noms_rank: int
    overall_wins_rank: int
    category_group_id: int
    category_group: str
    category_group_noms: int
    category_group_wins: int
    category_group_noms_rank: int
    category_group_wins_rank: int
    category_id: int
    category: str
    category_noms: int
    category_wins: int
    category_noms_rank: int
    category_wins_rank: int
