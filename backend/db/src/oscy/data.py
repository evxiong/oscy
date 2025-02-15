from dataclasses import dataclass


@dataclass
class OfficialNominee:
    winner: bool
    films: list[str]  # some nominees involve multiple films
    nomination: str
    detail: list[
        str
    ]  # character, song title, dance number; some nominees involve multiple
    note: str


@dataclass
class OfficialCategory:
    category: str
    nominees: list[OfficialNominee]


@dataclass
class IMDbNominee:
    winner: bool
    films: list[tuple[str, str]]  # title, id
    people: list[tuple[str, str]]  # name, id
    detail: str  # song title or country (for foreign film)


@dataclass
class IMDbCategory:
    category: str
    nominees: list[IMDbNominee]


@dataclass
class MatchedNominee:
    edition: int
    category_name: str
    winner: bool
    statement: str
    films: list[
        tuple[str, str, bool, list[str]]
    ]  # title, imdb id, winner, detail (song titles or dance numbers assoc with title)
    people: list[
        tuple[str, str, int, str]
    ]  # name, imdb id, start index in nomination stmt, role on set (does not apply to oscars)
    is_person: bool
    note: str
    official: bool
    stat: bool
    pending: bool


@dataclass
class MatchedCategory:
    category: str
    nominees: list[MatchedNominee]
