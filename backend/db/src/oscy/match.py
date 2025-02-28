import dataclasses
import json
import numpy as np
import os
import re
import sys
import yaml
from . import parse, scrape
from .data import (
    MatchedCategory,
    MatchedNominee,
    OfficialCategory,
    OfficialNominee,
    IMDbCategory,
    IMDbNominee,
)
from dotenv import load_dotenv
from rapidfuzz import process, fuzz
from tqdm import tqdm
from typing import Callable

load_dotenv()

# hard-coded category equivalents that fuzzy matching doesn't handle well...put
# this in a yaml file
OFFICIAL_TO_IMDB = {
    "DIRECTING": {
        "best director",
    },
    "OUTSTANDING PRODUCTION": {
        "best picture",
    },
    "BEST PICTURE": {
        "best picture",
    },
    "BEST MOTION PICTURE": {
        "best picture",
    },
    "DOCUMENTARY (Feature)": {
        "best documentary feature",
    },
    "ASSISTANT DIRECTOR": {
        "best assistant director",
    },
    "SOUND": {
        "best sound",
    },
    "WRITING (Screenplay)": {
        "best writing screenplay",
    },
}

# hard-coded special award - international foreign film, 20th edition
SPECIAL_AWARD_20 = MatchedNominee(
    edition=20,
    category_name="SPECIAL AWARD",
    winner=True,
    statement="To Shoe-Shine - the high quality of this motion picture, brought to eloquent life in a country scarred by war, is proof to the world that the creative spirit can triumph over adversity.",
    films=[
        ("Shoe-Shine", "tt0038913", True, []),
    ],
    people=[
        ("Italy", "ccIT", -1, ""),
    ],
    is_person=False,
    note="",
    official=True,
    stat=False,
    pending=False,
)

# hard-coded special categories that fall under later main categories...put this
# in a yaml file
EDGE_CASES: dict[str, dict[int, list[IMDbNominee]]] = {
    "SPECIAL FOREIGN LANGUAGE FILM AWARD": {
        # international foreign film
        21: [
            IMDbNominee(
                winner=True,
                films=[
                    ("Monsieur Vincent", "tt0039632"),
                ],
                people=[
                    ("France", ""),
                ],
                detail="",
            ),
        ],
        22: [
            IMDbNominee(
                winner=True,
                films=[
                    ("The Bicycle Thief", "tt0040522"),
                ],
                people=[
                    ("Italy", ""),
                ],
                detail="",
            ),
        ],
    },
    "HONORARY FOREIGN LANGUAGE FILM AWARD": {
        # international foreign film
        23: [
            IMDbNominee(
                winner=True,
                films=[
                    ("The Walls of Malapaga", "tt0040137"),
                ],
                people=[
                    ("France", ""),
                    ("Italy", ""),
                ],
                detail="",
            ),
        ],
        24: [
            IMDbNominee(
                winner=True,
                films=[
                    ("Rashomon", "tt0042876"),
                ],
                people=[
                    ("Japan", ""),
                ],
                detail="",
            ),
        ],
        25: [
            IMDbNominee(
                winner=True,
                films=[
                    ("Forbidden Games", "tt0043686"),
                ],
                people=[
                    ("France", ""),
                ],
                detail="",
            ),
        ],
        27: [
            IMDbNominee(
                winner=True,
                films=[
                    ("Gate of Hell", "tt0045935"),
                ],
                people=[
                    ("Japan", ""),
                ],
                detail="",
            ),
        ],
        28: [
            IMDbNominee(
                winner=True,
                films=[
                    ("Samurai, The Legend of Musashi", "tt0047444"),
                ],
                people=[
                    ("Japan", ""),
                ],
                detail="",
            ),
        ],
    },
    "SPECIAL ACHIEVEMENT AWARD (Visual Effects)": {
        # visual effects
        45: [
            IMDbNominee(
                winner=True,
                films=[
                    ("The Poseidon Adventure", "tt0069113"),
                ],
                people=[
                    ("L. B. Abbott", "nm0008004"),
                    ("A. D. Flowers", "nm0283166"),
                ],
                detail="",
            ),
        ],
        47: [
            IMDbNominee(
                winner=True,
                films=[
                    ("Earthquake", "tt0071455"),
                ],
                people=[
                    ("Frank Brendel", "nm0107152"),
                    ("Glen Robinson", "nm0732656"),
                    ("Albert Whitlock", "nm0926087"),
                ],
                detail="",
            ),
        ],
        48: [
            IMDbNominee(
                winner=True,
                films=[
                    ("The Hindenburg", "tt0073113"),
                ],
                people=[
                    ("Albert Whitlock", "nm0926087"),
                    ("Glen Robinson", "nm0732656"),
                ],
                detail="",
            ),
        ],
        49: [
            IMDbNominee(
                winner=True,
                films=[
                    ("King Kong", "tt0074751"),
                ],
                people=[
                    ("Carlo Rambaldi", "nm0708058"),
                    ("Glen Robinson", "nm0732656"),
                    ("Frank Van der Veer", "nm0886440"),
                ],
                detail="",
            ),
            IMDbNominee(
                winner=True,
                films=[
                    ("Logan's Run", "tt0074812"),
                ],
                people=[
                    ("L. B. Abbott", "nm0008004"),
                    ("Glen Robinson", "nm0732656"),
                    ("Matthew Yuricich", "nm0951046"),
                ],
                detail="",
            ),
        ],
        51: [
            IMDbNominee(
                winner=True,
                films=[
                    ("Superman", "tt0078346"),
                ],
                people=[
                    ("Les Bowie", "nm0101155"),
                    ("Colin Chilvers", "nm0157670"),
                    ("Denys Coop", "nm0177813"),
                    ("Roy Field", "nm0276037"),
                    ("Derek Meddings", "nm0575439"),
                    ("Zoran Perisic", "nm0673830"),
                ],
                detail="",
            ),
        ],
        53: [
            IMDbNominee(
                winner=True,
                films=[
                    ("The Empire Strikes Back", "tt0080684"),
                ],
                people=[
                    ("Brian Johnson", "nm0424644"),
                    ("Richard Edlund", "nm0249430"),
                    ("Dennis Muren", "nm0613830"),
                    ("Bruce Nicholson", "nm0629785"),
                ],
                detail="",
            ),
        ],
        56: [
            IMDbNominee(
                winner=True,
                films=[
                    ("Return of the Jedi", "tt0086190"),
                ],
                people=[
                    ("Richard Edlund", "nm0249430"),
                    ("Dennis Muren", "nm0613830"),
                    ("Ken Ralston", "nm0707822"),
                    ("Phil Tippett", "nm0864138"),
                ],
                detail="",
            ),
        ],
        63: [
            IMDbNominee(
                winner=True,
                films=[
                    ("Total Recall", "tt0100802"),
                ],
                people=[
                    ("Eric Brevig", "nm0108094"),
                    ("Rob Bottin", "nm0001964"),
                    ("Tim McGovern", "nm0569601"),
                    ("Alex Funke", "nm0298754"),
                ],
                detail="",
            ),
        ],
    },
    "SPECIAL ACHIEVEMENT AWARD (Sound Effects)": {
        # sound editing
        48: [
            IMDbNominee(
                winner=True,
                films=[
                    ("The Hindenburg", "tt0073113"),
                ],
                people=[
                    ("Peter Berkos", "nm0075440"),
                ],
                detail="",
            ),
        ],
    },
    "SPECIAL ACHIEVEMENT AWARD (Sound Effects Editing)": {
        # sound editing
        50: [
            IMDbNominee(
                winner=True,
                films=[
                    ("Close Encounters of the Third Kind", "tt0075860"),
                ],
                people=[
                    ("Frank E. Warner", "nm0912466"),
                ],
                detail="",
            ),
        ],
        54: [
            IMDbNominee(
                winner=True,
                films=[
                    ("Raiders of the Lost Ark", "tt0082971"),
                ],
                people=[
                    ("Ben Burtt", "nm0123785"),
                    ("Richard L. Anderson", "nm0027328"),
                ],
                detail="",
            ),
        ],
        57: [
            IMDbNominee(
                winner=True,
                films=[
                    ("The River", "tt0088007"),
                ],
                people=[
                    ("Kay Rose", "nm0741515"),
                ],
                detail="",
            ),
        ],
        60: [
            IMDbNominee(
                winner=True,
                films=[
                    ("RoboCop", "tt0093870"),
                ],
                people=[
                    ("Stephen Flick", "nm0282276"),
                    ("John Pospisil", "nm0654897"),
                ],
                detail="",
            ),
        ],
    },
    "SPECIAL ACHIEVEMENT AWARD (Sound Editing)": {
        # sound editing
        52: [
            IMDbNominee(
                winner=True,
                films=[
                    ("The Black Stallion", "tt0078872"),
                ],
                people=[
                    ("Alan Splet", "nm0819263"),
                ],
                detail="",
            ),
        ],
    },
}


def match_from_scores(
    official: list, imdb: list, matrix: np.ndarray, suppress: bool = True
) -> dict[int, int]:
    """Matches official entries to IMDb entries based on similarity matrix.

    Args:
        official (list): official entries
        imdb (list): IMDb entries
        matrix (np.ndarray): len(official) x len(imdb) matrix of similarity
            scores.
        suppress (bool, optional): if True, suppress printing matched entries.
            Defaults to True.

    Raises:
        Exception: failure to match items

    Returns:
        dict[int, int]: official index -> imdb index
    """
    res = matrix.argmax(axis=1)
    imdb_to_official = {i: [] for i in range(len(matrix))}
    matches: dict[int, int] = {}  # official index -> imdb index

    for official_i, imdb_i in enumerate(res):
        if not suppress:
            print(
                official_i,
                official[official_i],
                "\t",
                imdb_i,
                imdb[imdb_i],
                matrix[official_i][imdb_i],
            )
        matches[official_i] = int(imdb_i)
        imdb_to_official[imdb_i].append(official_i)

    remaining_official = []
    remaining_imdb = []
    for i in range(len(matrix)):
        if len(imdb_to_official[i]) == 0:
            remaining_imdb.append((i, imdb[i]))
        elif len(imdb_to_official[i]) > 1:
            remaining_imdb.append((i, imdb[i]))
            for official_i in imdb_to_official[i]:
                remaining_official.append((official_i, official[official_i]))

    if remaining_official or remaining_imdb:
        raise Exception("Failed to match items:", remaining_official, remaining_imdb)

    return matches


def fuzzy_match(
    official: list[str],
    imdb: list[str],
    scorer=fuzz.token_set_ratio,
    preprocessor=None,
    match=True,
) -> tuple[dict[int, int], np.ndarray]:
    """Computes similarity matrix and optionally returns matches.

    Args:
        official (list[str]): official entries
        imdb (list[str]): IMDb entries
        scorer (optional): rapidfuzz.fuzz similarity scorer. Defaults to
            `fuzz.token_set_ratio`.
        preprocessor (optional): function applied to each element of official
            and imdb prior to computing similarity scores. Defaults to None.
        match (bool, optional): if True, calls `match_from_scores()` and
            computes matches; otherwise, only computes similarity matrix.
            Defaults to True.

    Raises:
        Exception: lengths of official and imdb do not match

    Returns:
        tuple[dict[int, int], np.ndarray]: matches (official ind -> imdb ind),
            similarity matrix
    """
    if len(official) != len(imdb):
        raise Exception(
            f"Lengths of official ({len(official)}) and imdb ({len(imdb)}) do not match:",
            official,
            imdb,
        )

    matrix = process.cdist(official, imdb, scorer=scorer, processor=preprocessor)
    matches = match_from_scores(official, imdb, matrix) if match else {}
    return matches, matrix


def match_nominees(
    official: OfficialCategory, imdb: IMDbCategory, edition: int, pending: bool
) -> tuple[MatchedCategory, list[tuple[str, str]]]:
    """Matches official and IMDb nominees for a single category.

    `official` and `imdb` should refer to the same category and contain the same
    number of nominees.

    Args:
        official (OfficialCategory): official Oscars database category
        imdb (IMDbCategory): IMDb category
        edition (int): edition of Oscar ceremony
        pending (bool): True if ceremony hasn't occurred yet; otherwise, False

    Returns:
        tuple[MatchedCategory, list[tuple[str, str]]]: (matched category
            containing matched nominees, inexact person matches between
            `official` and `imdb`)
    """
    # match winners first, then other nominees; potential for multiple winners
    # in single category
    official_winners: list[OfficialNominee] = []
    official_nominees: list[OfficialNominee] = []
    imdb_winners: list[IMDbNominee] = []
    imdb_nominees: list[IMDbNominee] = []

    for n in official.nominees:
        if n.winner:
            official_winners.append(n)
        else:
            official_nominees.append(n)

    for n in imdb.nominees:
        if n.winner:
            imdb_winners.append(n)
        else:
            imdb_nominees.append(n)

    competitive = len(official_nominees) > 0
    result = MatchedCategory(category=official.category, nominees=[])
    warnings: list[tuple[str, str]] = []

    for o, i in [(official_winners, imdb_winners), (official_nominees, imdb_nominees)]:
        if not o or not i:  # in case no winners yet
            continue

        # Calculate similarity for titles and people separately
        # Add scores and take lowest for best match, then match ids

        # join titles into one string per nominee
        # for songs, add song name to title (multiple songs from same film can be
        # nominated)
        official_films = [
            (
                ", ".join(n.films) + " | " + ", ".join(n.detail)
                if "Song" in official.category
                else ", ".join(n.films)
            )
            for n in o
        ]
        imdb_films = [
            (
                ", ".join([t[0] for t in n.films]) + " | " + n.detail
                if "Song" in official.category
                else ", ".join([t[0] for t in n.films])
            )
            for n in i
        ]
        _, films_matrix = fuzzy_match(
            official_films, imdb_films, scorer=fuzz.ratio, match=False
        )

        # join people into one string per nominee
        # substitute imdb names for official names via `NICKNAMES`
        official_noms = [n.nomination for n in o]
        imdb_people = [
            ", ".join([NICKNAMES.get(t[0], t[0]) for t in n.people]) for n in i
        ]
        _, people_matrix = fuzzy_match(
            official_noms, imdb_people, scorer=fuzz.ratio, match=False
        )

        # add similarity scores from title and people matching
        matrix = films_matrix + people_matrix

        # official ind -> matched imdb ind
        matches = match_from_scores(
            list(zip(official_films, official_noms)),
            list(zip(imdb_films, imdb_people)),
            matrix,
        )
        for official_i in matches:
            res, inexact_matches = match_ids(
                o[official_i],
                i[matches[official_i]],
                edition,
                official.category,
                competitive,
                pending,
            )
            result.nominees.append(res)
            warnings += inexact_matches

        if not official_nominees or not imdb_nominees:
            return result, warnings

    return result, warnings


NICKNAMES = {  # imdb nickname to oscar listed name
    "Common": "Lonnie R. Lynn",
    "Volker Bertelmann": "Hauschka",
    "Shellback": "Karl Johan Schuster",
    "DaHeala": "Jason Quenneville",
    "Belly": "Ahmad Balshe",
    "Bono": "Paul Hewson",
    "The Edge": "Dave Evans",
    "M.I.A.": "Maya Arulpragasam",
    "Juicy J": "Jordan Houston",
    "Sjón": "Sjon Sigurdsson",
    "Jimmy Jam": "James Harris III",
    "Jim Poynter": "Pat Pending",
    "Leila Rubin": "Vincent Korda",
    "Orville O. Dull": "Bunny Dull",
}

STUDIOS = {  # oscar name to imdb id - NEED TO USE DIFFERENT IDS FOR SOUND AND BEST PICTURE
    # sound
    "20th Century-Fox Studio Sound Department": "co0000756",
    "Metro-Goldwyn-Mayer British Studio Sound Department": "co0071784",
    "Metro-Goldwyn-Mayer London Studio Sound Department": "co0071784",
    "Denham Studio Sound Department": "co0071784",
    "Metro-Goldwyn-Mayer Studio Sound Department": "co0007143",
    "Universal City Studio Sound Department": "co0005073",
    "Revue Studio Sound Department": "co0005073",
    "Universal-International Studio Sound Department": "co0005073",
    "Universal Studio Sound Department": "co0005073",
    "Todd-AO Sound Department": "co0016792",
    "Shepperton Studio Sound Department": "co0103344",
    "Walt Disney Studio Sound Department": "co0098836",
    "Columbia Studio Sound Department": "co0050868",
    "Glen Glenn Sound Department": "co0000175",
    "King Bros. Productions, Inc., Sound Department": "co0004893",
    "Westrex Sound Services, Inc.": "co0001880",
    "Radio Corporation of America Sound Department": "co0179360",
    "RCA Sound": "co0179360",
    "RKO Radio Studio Sound Department": "co0041421",
    "London Film Sound Department": "co0103018",
    "Pinewood Studios Sound Department": "co0041067",
    "Pinewood Studio Sound Department": "co0041067",
    "Republic Studio Sound Department": "co0020540",
    "Sound Service, Inc.": "co0116827",
    "General Service": "co0116827",
    "General Service Sound Department": "co0116827",
    "Hal Roach Studio Sound Department": "co0075561",
    "Grand National Studio Sound Department": "co0035646",
    "Warner Bros. Studio Sound Department": "co0002663",
    "Warner Bros.-First National Studio Sound Department": "co0002663",
    "Warner Bros.-Seven Arts Studio Sound Department": "co0002663",
    "Fox Studio Sound Department": "co0028775",
    "Paramount Studio Sound Department": "co0023400",
    "Paramount Publix Studio Sound Department": "co0023400",
    "Paramount Famous Lasky Studio Sound Department": "co0023400",
    "First National Studio Sound Department": "co0041460",
    "Samuel Goldwyn Studio Sound Department": "co0016710",
    "United Artists Studio Sound Department": "co0016710",
    "Samuel Goldwyn - United Artists Studio Sound Department": "co0016710",
    # special effects
    "Paramount Studio": "co0023400",
    "Paramount": "co0023400",
    "Associated British Picture Corporation, Ltd.": "co0103091",
    "20th Century-Fox Studio": "co0000756",
    "Walt Disney Studios": "co0098836",
    "Warner Bros. Studio": "co0002663",
    "Metro-Goldwyn-Mayer": "co0007143",
    "George Pal Productions": "co0012307",
    "Cecil B. DeMille Productions": "co_1",
    "ARKO Productions": "co_2",
    "Walter Wanger Pictures": "co0035064",
    # best picture
    "20th Century-Fox": "co0000756",
    "Columbia": "co0050868",
    "Robert Rossen Productions": "co_5",
    "J. Arthur Rank-Two Cities Films": "co0103139",
    "Two Cities": "co0103139",
    "J. Arthur Rank-Archers": "co0103153",
    "Warner Bros.": "co0002663",
    "Warner Bros.-First National": "co0002663",
    "RKO Radio": "co0041421",
    "J. Arthur Rank-Cineguild": "co0113550",
    "Samuel Goldwyn Productions": "co0016710",
    "Liberty Films": "co0196361",
    "Rainbow Productions": "co0130488",
    "Selznick International Pictures": "co0130901",
    "Ortus": "co0122163",
    "Mercury": "co0003016",
    "Walter Wanger (production company)": "co0035064",
    "Charles Chaplin Productions": "co0028083",
    "Argosy-Wanger": "co_3",
    "Sol Lesser (production company)": "co0027170",
    "Hal Roach (production company)": "co0075561",
    "Universal": "co0005073",
    "Cosmopolitan": "co0073404",
    "20th Century": "co0067247",
    "First National": "co0041460",
    "Jesse L. Lasky (production company)": "co_6",
    "Fox": "co0028775",
    "London Films": "co0103018",
    "The Caddo Company": "co0074827",
    "Paramount Publix": "co0023400",
    "Paramount Famous Lasky": "co0023400",
    "Feature Productions": "co0203140",
    "Romulus Films": "co0103121",
    # documentary
    "United States Army": "co0007320",
    "United States Army Air Force": "co0046209",
    "United States Air Force": "co0046209",
    "United States Department of State Office of Information and Educational Exchange": "co0002868",
    "United Nations Division of Films and Visual Information": "co0060016",
    "Australian News & Information Bureau": "co0054998",
    "United States Department of War": "co0007361",
    "The March of Time": "co0047855",
    "Artkino": "co0080235",
    "The Governments of Great Britain and the United States of America": "co0952077",
    "United States Office of War Information Overseas Motion Picture Bureau": "co0073032",
    "United States Marine Corps": "co0069196",
    "United States Navy": "co0047766",
    "British Ministry of Information": "co0103143",
    "United States Department of War Special Service Division": "co0038466",
    "United States Army Pictorial Service": "co0041860",
    "United States Office of Strategic Services Field Photographic Bureau": "co0019944",
    "United States Navy Bureau of Aeronautics": "co0252896",
    "United States Army Special Services": "co0038466",
    "United States Army Signal Corps": "co0041860",
    "United States Department of Agriculture": "co0019457",
    "National Film Board of Canada": "co0006414",
    "The Netherlands Information Bureau": "co0004402",
    "United States Office of War Information": "co0020185",
    "Belgian Ministry of Information": "co0069344",
    "United States Merchant Marine": "co_4",
    "Concanen Films": "co0191745",
    "Film Associates": "co0033921",
    "United States Office for Emergency Management Film Unit": "co0063999",
    "Philadelphia Housing Association": "co0329990",
    "Amkino": "co0003677",
    "Realization D'Art Cinematographique": "co0053790",
    "Comite Organizador de los Juegos de la XIX Olimpiada": "co0119316",
    "Mafilm Studio": "co0014531",
    "Mafilm Productions": "co0014531",
    "Vision Associates Productions": "co0074919",
    "dell Istituto Nazionale Luce, Comitato Organizzatore Del Giochi Della XVII Olimpiade": "co0033240",
    "Dido-Film-GmbH": "co0057535",
    "United States Information Agency": "co0020570",
    "Statens Filmcentral, The Danish Government Film Office": "co0079434",
    "The Government Film Committee of Denmark": "co0147202",
    "World Wide Pictures": "co0104697",
    "Morse Films": "co0048405",
    "Film Documents, Inc.": "co0017787",
    "French Cinema General Cooperative": "co0020379",
    "St. Francis-Xavier University, Antigonish, Nova Scotia": "co0076128",
    # cartoon
    "United Productions of America": "co0018897",
    "Screen Gems": "co0010568",
    "Harman-Ising": "co0639824",
    "Zagreb Film": "co0055124",
    # short-subject
    "Les Films du Compass": "co0192387",
    "Woodard Productions, Inc.": "co0146265",
    "Skibo Productions": "co0019661",
    "Gaumont British": "co0053065",
    "Educational": "co0050385",
    "Templar Film Studios": "co0127441",
    "Ciné-Documents": "co0027834",
    "New Zealand Screen Board": "co0032927",
    "Dublin Gate Theatre Productions": "co0044998",
    "Crown Film Unit": "co0103148",
    "London Film Production": "co0103018",
    "Falcon Films, Inc.": "co0048144",
}

SPLIT_EXCEPTIONS = {  # keep these phrases together as one unit when parsing nomination statements
    "dell Istituto Nazionale Luce, Comitato Organizzatore Del Giochi Della XVII Olimpiade",
    "Charles Guggenheim & Associates, Inc.",
    "King Bros. Productions, Inc., Sound Department",
    "Westrex Sound Services, Inc.",
    "To Samurai, The Legend of Musashi - Best Foreign Language Film first released in the United States during 1955.",
    "Associated British Picture Corporation, Ltd.",
    "To Rashomon - voted by the Board of Governors as the most outstanding foreign language film released in the United States during 1951.",
    "To The Walls of Malapaga - voted by the Board of Governors as the most outstanding foreign language film released in the United States in 1950.",
    "Film Documents, Inc.",
    "Falcon Films, Inc.",
    "To The Bicycle Thief - voted by the Academy Board of Governors as the most outstanding foreign language film released in the United States during 1949.",
    "St. Francis-Xavier University, Antigonish, Nova Scotia",
    "To Monsieur Vincent - voted by the Academy Board of Governors as the most outstanding foreign language film released in the United States during 1948.",
    "United States Department of State Office of Information and Educational Exchange",
    "United Nations Division of Films and Visual Information",
    "Australian News & Information Bureau",
    "Sound Service, Inc.",
    "The Governments of Great Britain and the United States of America",
    "Woodard Productions, Inc.",
    "Walter Wanger (production company)",
    "Sol Lesser (production company)",
    "Hal Roach (production company)",
    "Jesse L. Lasky (production company)",
    "Harry Perry",
    "Maxwell Anderson",
    "Del Andrews",
    "Charlie Kaufman and Donald Kaufman",
    "Bosnia & Herzegovina",
    "Bosnia and Herzegovina",
    "Statens Filmcentral, The Danish Government Film Office",
}

NOMINATION_TO_PERSON = {
    "To Samurai, The Legend of Musashi - Best Foreign Language Film first released in the United States during 1955.": "Japan",
    "To Gate of Hell - Best Foreign Language Film first released in the United States during 1954.": "Japan",
    "Forbidden Games - Best Foreign Language Film first released in the United States during 1952.": "France",
    "To Rashomon - voted by the Board of Governors as the most outstanding foreign language film released in the United States during 1951.": "Japan",
    "Fred Zinnemann with the cooperation of Paramount Pictures Corporation for the Los Angeles Orthopaedic Hospital": "Fred Zinnemann",
    "To The Walls of Malapaga - voted by the Board of Governors as the most outstanding foreign language film released in the United States in 1950.": "France",
    "To The Bicycle Thief - voted by the Academy Board of Governors as the most outstanding foreign language film released in the United States during 1949.": "Italy",
    "To Monsieur Vincent - voted by the Academy Board of Governors as the most outstanding foreign language film released in the United States during 1948.": "France",
}


def match_ids(
    official: OfficialNominee,
    imdb: IMDbNominee,
    edition: int,
    category_name: str,
    competitive: bool,
    pending: bool,
) -> tuple[MatchedNominee, list[tuple[str, str]]]:
    """Matches official and IMDb titles and entities for a single nominee.

    `official` and `imdb` should refer to the same nominee.

    Args:
        official (OfficialNominee): official database nominee
        imdb (IMDbNominee): IMDb nominee
        edition (int): edition of Oscar ceremony
        category_name (str): official category name
        competitive (bool): True if at least one non-winner in this nominee's
            category; otherwise, False
        pending (bool): True if ceremony hasn't occurred yet; otherwise, False

    Raises:
        Exception: films/details mismatch

    Returns:
        tuple[MatchedNominee, list[tuple[str, str]]]: (matched nominee, inexact
            matches (name from official nomination statement, IMDb name))
    """
    # match imdb ids to people in nomination and title ids to films
    # match titles first

    with open("data/country_codes.yaml", encoding="utf-8") as fd:
        COUNTRY_CODES = yaml.safe_load(fd)

    inexact_matches: list[tuple[str, str]] = []

    # Preprocess official nomination statement
    preprocess = [
        (", Jr.", " Jr."),
        (", Sr.", " Sr."),
        (", III", " III"),
        (
            "'Made by Fred Zinnemann with the cooperation of Paramount Pictures Corporation for the Los Angeles Orthopaedic Hospital'",
            "Made by Fred Zinnemann with the cooperation of Paramount Pictures Corporation for the Los Angeles Orthopaedic Hospital",
        ),
    ]
    nom = official.nomination
    for old, new in preprocess:
        nom = nom.replace(old, new)
    official.nomination = nom

    person_nominees = {
        "actor",
        "actor in a leading role",
        "actor in a supporting role",
        "actress",
        "actress in a leading role",
        "actress in a supporting role",
    }

    # MatchedNominee stat is whether nomination should count towards aggregated nomination stats, not winner stats
    #  if official and competitive (at least one non-winner in category), True
    #  if official and non-competitive (only winners in category, ex. special award), False
    #  if unofficial, False

    # (old criteria - unused):
    # if official, stat is True
    # if not official and not winner, stat is False
    # if not official and is winner and not write-in, stat is True
    # if not official and is winner and is write-in, stat is False
    # True
    # if official_nomination
    # or (official["winner"] and "Write-in candidate" not in official["note"])
    # else False

    # Build MatchedNominee
    official_nomination = "THIS IS NOT AN OFFICIAL NOMINATION" not in official.note

    result = MatchedNominee(
        edition=edition,
        category_name=category_name,
        winner=official.winner,
        statement=nom,
        films=[],
        people=[],
        is_person=category_name.lower() in person_nominees,
        note=official.note,
        official=official_nomination,
        stat=official_nomination and competitive,
        pending=pending,
    )

    # Match official and imdb nominee films

    # films: list[tuple[str, str, bool, list[str]]] # title, imdb id, winner, detail (song titles or dance numbers assoc with title)

    if official.films:
        matches, _ = fuzzy_match(
            official.films, [t[0] for t in imdb.films], scorer=fuzz.ratio
        )

        for official_i in range(len(official.films)):
            # if official.films[official_i] != imdb.films[matches[official_i]][0]:
            #     inexact_matches.append(
            #         (official.films[official_i], imdb.films[matches[official_i]][0])
            #     )

            if (
                edition == 3
                and (category_name == "ACTOR" or category_name == "ACTRESS")
                and official.winner
            ):
                # if multiple films and winner, only first film is winner
                film_winner = official_i == 0
            else:
                film_winner = official.winner

            # if one film and multiple details, all details belong to film
            # if more than one film and multiple details, allocate one detail per film
            # if more than one film and # of details != # of films, raise exception
            if len(official.films) > 1 and len(official.detail) > 0:
                if len(official.films) != len(official.detail):
                    raise Exception(
                        f"Nominee's number of films ({len(official.films)}) and details ({len(official.detail)}) differ:",
                        official.films,
                        official.detail,
                    )
                film_detail = [official.detail[official_i]]
            else:
                film_detail = official.detail

            result.films.append(
                (
                    official.films[official_i],
                    imdb.films[matches[official_i]][1],
                    film_winner,
                    film_detail,
                )
            )

    # Match official and imdb entities
    titles_to_ignore = {
        "head of department",
        "musical director",
        "Producer",
        "Producers",
        "Sound Director",
        "Co-Producer",
        "Co-Producers",
        "Executive Producer",
        "Producer.",
        "Associate Producer",
        "Principal Productions",
    }
    replaced = [
        "Production Design: ",
        "Set Decoration: ",
        "Screenplay - ",
        "Art Direction: ",
        "Musical Settings: ",
        "Interior Decoration: ",
        "in collaboration with ",
        "In collaboration with ",
    ]

    # parse names from official nomination stmt:
    #   note split exceptions first
    #   split by semicolon, then ignore everything before "by"
    #   split by ",", "and", "&"
    #   ignore/replace phrases

    names = set()
    nom = official.nomination

    for e in SPLIT_EXCEPTIONS:
        if e in nom:
            names.add(e)
            nom = nom.replace(e, "")

    groups = re.sub(r"\s\([^)]*\)", "", nom)
    for g1 in groups.split("; and "):
        for group in g1.split("; "):
            # group = group.strip()
            ind = group.find(" by ")
            if ind != -1:
                group = group[ind + 4 :]
            for subgroup in group.split(","):
                subgroup = subgroup.strip()
                for subsubgroup in subgroup.split(" and "):
                    for subsubsubgroup in subsubgroup.split(" & "):
                        for r in replaced:
                            subsubsubgroup = subsubsubgroup.replace(r, "")
                        if subsubsubgroup != "" and subsubsubgroup[0] == "(":
                            subsubsubgroup = subsubsubgroup[1:]
                        if subsubsubgroup != "" and subsubsubgroup[-1] == ")":
                            subsubsubgroup = subsubsubgroup[:-1]
                        if subsubsubgroup == "Roderick Jaynes":
                            names.add("Joel Coen")
                            names.add("Ethan Coen")
                            continue
                        if (
                            subsubsubgroup != ""
                            and subsubsubgroup not in titles_to_ignore
                            and "Music Department" not in subsubsubgroup
                        ):
                            names.add(subsubsubgroup)

    # add missing studios to imdb people
    names = list(names)
    for name in names:
        if name in STUDIOS and len(imdb.people) < len(names):
            imdb.people.append((name, STUDIOS[name]))

    # shared between France and Italy
    if official.nomination.startswith("To The Walls of Malapaga"):
        names.append("Italy")

    # remove duplicates from imdb people
    remove_dups = {(p[1] if p[1] != "" else i): p for i, p in enumerate(imdb.people)}
    imdb.people = list(remove_dups.values())

    # people: list[tuple[str, str, int, str]] # name, imdb id, start index in
    # nomination stmt, role (does not apply to oscars)

    if names or imdb.people:
        matches, _ = fuzzy_match(
            names, [NICKNAMES.get(t[0], t[0]) for t in imdb.people], scorer=fuzz.ratio
        )
        for i, name in enumerate(names):
            if name != imdb.people[matches[i]][0]:
                inexact_matches.append((name, imdb.people[matches[i]][0]))

            final_name = NOMINATION_TO_PERSON.get(name, name)
            imdb_id = COUNTRY_CODES.get(final_name, imdb.people[matches[i]][1])
            if imdb_id == "":
                raise Exception(
                    "Empty IMDb id in match_ids:", category_name, official, imdb
                )
            result.people.append(
                (
                    final_name,
                    imdb_id,
                    official.nomination.find(final_name),
                    "",
                )
            )

    return result, inexact_matches


def merge_official_nominees(
    o1: OfficialNominee, o2: OfficialNominee
) -> OfficialNominee:
    # used for oscars 1-3 where single
    if o1.nomination != o2.nomination:
        print("Warning: merged nomination statements differ:", o1, o2)
        # raise Exception("Cannot merge official nominees: o1 and o2 nom stmts differ:", o1, o2)

    return OfficialNominee(
        winner=o1.winner,
        films=(o1.films + o2.films if o1.films != o2.films else o1.films),
        nomination=(
            o1.nomination
            if o1.nomination == o2.nomination
            else o1.nomination + " and " + o2.nomination
        ),
        detail=o1.detail + o2.detail,
        note=o1.note,
    )


def merge_imdb_nominees(i1: IMDbNominee, i2: IMDbNominee) -> IMDbNominee:
    if i1.people != i2.people:
        raise Exception("Cannot merge imdb nominees: i1 and i2 people differ", i1, i2)

    return IMDbNominee(
        winner=i1.winner,
        films=i1.films + i2.films,
        people=i1.people,
        detail=i1.detail,
    )


official_nominee_replacements = {  # for bad html, ex. borat (93rd)
    93: [  # edition -> category ind
        {
            "category_ind": 3,
            "nominee_ind": 0,
            "nominee": OfficialNominee(
                winner=False,
                films=[
                    "Borat Subsequent Moviefilm: Delivery of Prodigious Bribe to American Regime for Make Benefit Once Glorious Nation of Kazakhstan"
                ],
                nomination="Maria Bakalova",
                detail=["Tutar Sagdiyev"],
                note="",
            ),
        },
        {
            "category_ind": 21,
            "nominee_ind": 0,
            "nominee": OfficialNominee(
                winner=False,
                films=[
                    "Borat Subsequent Moviefilm: Delivery of Prodigious Bribe to American Regime for Make Benefit Once Glorious Nation of Kazakhstan"
                ],
                nomination="Screenplay by Sacha Baron Cohen & Anthony Hines & Dan Swimer & Peter Baynham & Erica Rivinoja & Dan Mazer & Jena Friedman & Lee Kern; Story by Sacha Baron Cohen & Anthony Hines & Dan Swimer & Nina Pedrad",
                detail=[],
                note="",
            ),
        },
    ]
}

official_nominee_merges: dict[int, dict[int, list[list[int]]]] = {
    3: {  # edition -> category ind
        # category ind -> nominee inds
        0: [
            [0, 1],
        ],
        1: [
            [3, 4],
        ],
    },
    1: {
        3: [
            [1, 2],
        ]
    },
}

official_new_titles = {
    28: [
        {
            "category_ind": 26,
            "nominee_ind": 0,
            "new_titles": ["Samurai, The Legend of Musashi"],
        }
    ],
    27: [{"category_ind": 26, "nominee_ind": 0, "new_titles": ["Gate of Hell"]}],
    25: [
        {"category_ind": 26, "nominee_ind": 0, "new_titles": ["Forbidden Games"]},
    ],
    24: [
        {"category_ind": 26, "nominee_ind": 0, "new_titles": ["Rashomon"]},
    ],
    23: [
        {"category_ind": 26, "nominee_ind": 0, "new_titles": ["The Walls of Malapaga"]},
    ],
    22: [
        {"category_ind": 26, "nominee_ind": 0, "new_titles": ["The Bicycle Thief"]},
    ],
    21: [
        {"category_ind": 25, "nominee_ind": 0, "new_titles": ["Monsieur Vincent"]},
    ],
}

official_nominee_removals = {
    16: [  # preliminary list
        {
            "category_ind": 9,
            "films": ["For God and Country"],
            "nomination": "United States Army Pictorial Service",
        },
        {
            "category_ind": 9,
            "films": ["Silent Village"],
            "nomination": "British Ministry of Information",
        },
        {
            "category_ind": 9,
            "films": ["We've Come a Long, Long Way"],
            "nomination": "Negro Marches On, Inc.",
        },
        {
            "category_ind": 10,
            "films": ["Bismarck Convoy Smashed"],
            "nomination": "Australian Department of Information Film Unit",
        },
        {
            "category_ind": 10,
            "films": ["Day of Battle"],
            "nomination": "United States Office of War Information Domestic Motion Picture Bureau",
        },
        {
            "category_ind": 10,
            "films": ["The Dutch Tradition"],
            "nomination": "National Film Board of Canada",
        },
        {
            "category_ind": 10,
            "films": ["Kill or Be Killed"],
            "nomination": "British Ministry of Information",
        },
        {
            "category_ind": 10,
            "films": ["The Labor Front"],
            "nomination": "National Film Board of Canada",
        },
        {
            "category_ind": 10,
            "films": ["Land of My Mother"],
            "nomination": "Polish Information Centre",
        },
        {
            "category_ind": 10,
            "films": ["Letter from Livingston"],
            "nomination": "United States Army 4th Signal Photographic Unit",
        },
        {
            "category_ind": 10,
            "films": ["Life Line"],
            "nomination": "United States Army Pictorial Service",
        },
        {
            "category_ind": 10,
            "films": ["The Rear Gunner"],
            "nomination": "United States Department of War",
        },
        {
            "category_ind": 10,
            "films": ["Servant of a Nation"],
            "nomination": "Union of South Africa",
        },
        {
            "category_ind": 10,
            "films": ["Task Force"],
            "nomination": "United States Coast Guard",
        },
        {
            "category_ind": 10,
            "films": ["The Voice That Thrilled the World"],
            "nomination": "Warner Bros.",
        },
        {
            "category_ind": 10,
            "films": ["Water--Friend or Enemy"],
            "nomination": "Walt Disney, Producer",
        },
        {
            "category_ind": 10,
            "films": ["Wings Up"],
            "nomination": "United States Army Air Force 1st Motion Picture Unit",
        },
    ],
    12: [  # preliminary list
        {"category_ind": 5, "films": ["First Love"], "nomination": "Joseph Valentine"},
        {
            "category_ind": 5,
            "films": ["The Great Victor Herbert"],
            "nomination": "Victor Milner",
        },
        {"category_ind": 5, "films": ["Gunga Din"], "nomination": "Joseph H. August"},
        {"category_ind": 5, "films": ["Intermezzo"], "nomination": "Gregg Toland"},
        {"category_ind": 5, "films": ["Juarez"], "nomination": "Tony Gaudio"},
        {
            "category_ind": 5,
            "films": ["Lady of the Tropics"],
            "nomination": "George Folsey",
        },
        {
            "category_ind": 5,
            "films": ["Of Mice and Men"],
            "nomination": "Norbert Brodine",
        },
        {
            "category_ind": 5,
            "films": ["Only Angels Have Wings"],
            "nomination": "Joseph Walker",
        },
        {"category_ind": 5, "films": ["The Rains Came"], "nomination": "Arthur Miller"},
        {
            "category_ind": 6,
            "films": ["Drums along the Mohawk"],
            "nomination": "Ray Rennahan, Bert Glennon",
        },
        {
            "category_ind": 6,
            "films": ["Four Feathers"],
            "nomination": "Georges Perinal, Osmond Borradaile",
        },
        {
            "category_ind": 6,
            "films": ["The Mikado"],
            "nomination": "William V. Skall, Bernard Knowles",
        },
        {"category_ind": 6, "films": ["The Wizard of Oz"], "nomination": "Hal Rosson"},
    ],
}

imdb_nominee_merges: dict[int, dict[int, list[list[int]]]] = {
    3: {  # edition -> category ind
        0: [  # category ind -> groups of nominee inds to merge
            [0, 1],
            [3, 4],
            [5, 6],
        ],
        1: [
            [0, 5],
            [3, 4],
        ],
        4: [
            [1, 2],
        ],
    },
    2: {
        4: [
            [4, 5],
        ],
        2: [
            [1, 2],
        ],
        3: [
            [2, 5],
        ],
        6: [
            [1, 4, 6, 7],
            [2, 8],
            [9, 10],
        ],
    },
    1: {
        0: [
            [1, 2],
        ],
        2: [
            [0, 1],
        ],
        3: [
            [1, 2, 3],
        ],
    },
}

imdb_nominee_additions: dict[int, dict[int, list[IMDbNominee]]] = {
    # edition -> category ind -> list of IMDbNominee to add to category
    36: {
        11: [
            IMDbNominee(
                winner=False,
                films=[("Terminus", "tt0055514")],
                people=[("Edgar Anstey", "nm0030693")],
                detail="",
            )
        ]
    },
    19: {
        12: [
            IMDbNominee(
                winner=False,
                films=[("Three Little Girls in Blue", "tt0039026")],
                people=[("Harry Warren", "nm0912851"), ("Mack Gordon", "nm0330418")],
                detail="This is Always",
            )
        ]
    },
    17: {
        4: [
            IMDbNominee(
                winner=False,
                films=[("Song of the Open Road", "tt0037297")],
                people=[],
                detail="",
            )
        ]
    },
    14: {
        10: [
            IMDbNominee(
                winner=False,
                films=[("Dive Bomber", "tt0033537")],
                people=[
                    ("Byron Haskin", "nm0005738"),
                    ("Nathan Levinson", "nm0506080"),
                ],
                detail="",
            )
        ]
    },
}

imdb_nominee_removals = {
    8: [
        {
            "category_ind": 5,
            "films": [
                ("Folies Bergère de Paris", "tt0026373"),
            ],
            "people": [
                ("Dave Gould", "nm0332346"),
            ],
        },
        {
            "category_ind": 5,
            "films": [
                ("Broadway Hostess", "tt0026143"),
            ],
            "people": [
                ("Bobby Connolly", "nm0175265"),
            ],
        },
        {
            "category_ind": 5,
            "films": [
                ("All the King's Horses", "tt0024823"),
            ],
            "people": [
                ("LeRoy Prinz", "nm0697895"),
            ],
        },
    ],
}

imdb_new_titles = {
    41: [
        {
            "category_ind": 18,
            "nominee_ind": 2,
            "new_titles": [
                ("Duo", "tt0063417"),
            ],
        }
    ],
    37: [
        {
            "category_ind": 12,
            "nominee_ind": 4,
            "new_titles": [
                ("Kenojuak", "tt0058260"),
            ],
        }
    ],
    33: [
        {
            "category_ind": 12,
            "nominee_ind": 2,
            "new_titles": [
                ("A City Called Copenhagen", "tt0053685"),
            ],
        }
    ],
    23: [
        {
            "category_ind": 12,
            "nominee_ind": 1,
            "new_titles": [
                ("The Stairs", "tt0042996"),
            ],
        }
    ],
    17: [
        {
            "category_ind": 10,
            "nominee_ind": 1,
            "new_titles": [
                ("Arturo Toscanini", "tt0036023"),
            ],
        }
    ],
    15: [
        {
            "category_ind": 9,
            "nominee_ind": 3,
            "new_titles": [
                ("Prelude to War", "tt0035209"),
            ],
        },
        {
            "category_ind": 9,
            "nominee_ind": 18,
            "new_titles": [
                ("We Refuse to Die", "tt0035536"),
            ],
        },
        {
            "category_ind": 9,
            "nominee_ind": 19,
            "new_titles": [
                ("The Price of Victory", "tt0035210"),
            ],
        },
        {
            "category_ind": 15,
            "nominee_ind": 1,
            "new_titles": [
                ("The Invaders", "tt0033627"),
            ],
        },
    ],
    14: [
        {
            "category_ind": 16,
            "nominee_ind": 6,
            "new_titles": [
                ("Superman", "tt0034247"),
            ],
        },
    ],
    9: [
        {
            "category_ind": 14,
            "nominee_ind": 2,
            "new_titles": [
                ("Popular Science J-6-2", "tt_1"),
            ],
        },
    ],
    8: [
        {
            "category_ind": 5,
            "nominee_ind": 0,
            "new_titles": [
                ("Broadway Melody of 1936", "tt0026144"),
                ("Folies Bergere", "tt0026373"),
            ],
        },
        {
            "category_ind": 5,
            "nominee_ind": 4,
            "new_titles": [
                ("Go Into Your Dance", "tt0026418"),
                ("Broadway Hostess", "tt0026143"),
            ],
        },
        {
            "category_ind": 5,
            "nominee_ind": 8,
            "new_titles": [
                ("Big Broadcast of 1936", "tt0026113"),
                ("All the King's Horses", "tt0024823"),
            ],
        },
    ],
}

imdb_additions = {
    90: [
        {"category_ind": 20, "nominee_ind": 4, "addition": ("Lori Forte", "nm1000858")}
    ],
    71: [{"category_ind": 20, "nominee_ind": 2, "addition": ("JJ Keith", "nm0445249")}],
    69: [
        {
            "category_ind": 19,
            "nominee_ind": 1,
            "addition": ("Chris Peterson", "nm1470929"),
        }
    ],
    65: [
        {
            "category_ind": 19,
            "nominee_ind": 4,
            "addition": ("David Parfitt", "nm0661406"),
        }
    ],
    63: [
        {
            "category_ind": 8,
            "nominee_ind": 4,
            "addition": ("Eugene Corr", "nm0180644"),
        }
    ],
    61: [
        {
            "category_ind": 19,
            "nominee_ind": 1,
            "addition": ("Abbee Goldstein", "nm0326152"),
        },
        {
            "category_ind": 19,
            "nominee_ind": 2,
            "addition": ("George deGolian", "nm1480937"),
        },
    ],
    59: [
        {
            "category_ind": 18,
            "nominee_ind": 2,
            "addition": ("Bob Stenhouse", "nm0826598"),
        }
    ],
    58: [
        {
            "category_ind": 19,
            "nominee_ind": 0,
            "addition": ("Chris Pelzer", "nm0671410"),
        }
    ],
    57: [
        {"category_ind": 4, "nominee_ind": 1, "addition": ("Les Bloom", "nm0089193")},
        {
            "category_ind": 4,
            "nominee_ind": 2,
            "addition": ("James J. Murakami", "nm0613468"),
        },
        {
            "category_ind": 4,
            "nominee_ind": 2,
            "addition": ("Speed Hopkins", "nm0394279"),
        },
        {
            "category_ind": 4,
            "nominee_ind": 3,
            "addition": ("Leslie Tomkins", "nm0866777"),
        },
    ],
    54: [
        {"category_ind": 16, "nominee_ind": 1, "addition": ("John Kemeny", "nm0447190")}
    ],
    51: [{"category_ind": 4, "nominee_ind": 3, "addition": ("Bruce Kay", "nm0443008")}],
    49: [
        {"category_ind": 4, "nominee_ind": 1, "addition": ("Peter Howitt", "nm0398184")}
    ],
    48: [
        {"category_ind": 16, "nominee_ind": 2, "addition": ("René Jodoin", "nm0423520")}
    ],
    47: [
        {"category_ind": 15, "nominee_ind": 3, "addition": ("Fred Roos", "nm0740407")}
    ],
    43: [
        {
            "category_ind": 15,
            "nominee_ind": 1,
            "addition": ("Tylwyth Kymry", "nm0439506"),
        }
    ],
    38: [
        {
            "category_ind": 17,
            "nominee_ind": 3,
            "addition": ("Norman Gimbel", "nm0319757"),
        },
    ],
    37: [
        {
            "category_ind": 12,
            "nominee_ind": 0,
            "addition": ("Charles Guggenheim", "nm0346549"),
        },
        {
            "category_ind": 12,
            "nominee_ind": 3,
            "addition": ("Charles Guggenheim", "nm0346549"),
        },
    ],
    34: [
        {
            "category_ind": 21,
            "nominee_ind": 2,
            "addition": ("Robert Gaffney", "nm0300759"),
        },
    ],
    33: [
        {
            "category_ind": 21,
            "nominee_ind": 0,
            "addition": ("Ezra R. Baker", "nm0048441"),
        },
    ],
    29: [
        {
            "category_ind": 12,
            "nominee_ind": 1,
            "addition": ("Charles Guggenheim & Associates, Inc.", "co0214448"),
        },
    ],
    23: [
        {"category_ind": 12, "nominee_ind": 2, "addition": ("Guy Glover", "nm0323123")},
    ],
    19: [
        {
            "category_ind": 9,
            "nominee_ind": 4,
            "addition": ("Herbert Morgan", "nm0604712"),
        },
    ],
    18: [
        {
            "category_ind": 10,
            "nominee_ind": 0,
            "addition": ("Gordon Hollingshead", "nm0391121"),
        },
        {
            "category_ind": 18,
            "nominee_ind": 0,
            "addition": ("Jerry Bresler", "nm0107724"),
        },
        {
            "category_ind": 19,
            "nominee_ind": 1,
            "addition": ("Jerry Bresler", "nm0107724"),
        },
    ],
    17: [
        {
            "category_ind": 19,
            "nominee_ind": 2,
            "addition": ("Herbert Moulton", "nm0609764"),
        },
    ],
    16: [
        {
            "category_ind": 23,
            "nominee_ind": 0,
            "addition": ("Philip G. Epstein", "nm_1"),
        },
        {
            "category_ind": 10,
            "nominee_ind": 4,
            "addition": ("Walter Wanger", "nm0911137"),
        },
    ],
    15: [
        {
            "category_ind": 9,
            "nominee_ind": 19,
            "addition": ("William H. Pine", "nm0683993"),
        },
    ],
    14: [
        {
            "category_ind": 9,
            "nominee_ind": 6,
            "addition": ("Truman Talley", "nm1210908"),
        },
        {
            "category_ind": 9,
            "nominee_ind": 9,
            "addition": ("Truman Talley", "nm1210908"),
        },
        {
            "category_ind": 12,
            "nominee_ind": 1,
            "addition": ("Lloyd B. Norlind", "nm11004638"),
        },
        {
            "category_ind": 16,
            "nominee_ind": 6,
            "addition": ("Max Fleischer", "nm0281502"),
        },
    ],
    13: [
        {
            "category_ind": 12,
            "nominee_ind": 7,
            "addition": ("Arthur Freed", "nm0006085"),
        },
    ],
    11: [
        {
            "category_ind": 15,
            "nominee_ind": 8,
            "addition": ("John Aalberg", "nm0007356"),
        },
    ],
    9: [
        {
            "category_ind": 14,
            "nominee_ind": 1,
            "addition": ("Lewis Lewyn", "nm0507937"),
        },
        {
            "category_ind": 17,
            "nominee_ind": 3,
            "addition": ("Thomas T. Moulton", "nm0609771"),
        },
    ],
    5: [
        {
            "category_ind": 9,
            "nominee_ind": 0,
            "addition": ("Paramount Publix Studio Sound Department", "co0023400"),
        },
        {
            "category_ind": 9,
            "nominee_ind": 1,
            "addition": ("Metro-Goldwyn-Mayer Studio Sound Department", "co0007143"),
        },
        {
            "category_ind": 9,
            "nominee_ind": 2,
            "addition": ("RKO Radio Studio Sound Department", "co0041421"),
        },
        {
            "category_ind": 9,
            "nominee_ind": 3,
            "addition": (
                "Warner Bros.-First National Studio Sound Department",
                "co0002663",
            ),
        },
    ],
    4: [
        {
            "category_ind": 6,
            "nominee_ind": 0,
            "addition": ("Paramount Publix Studio Sound Department", "co0023400"),
        },
        {
            "category_ind": 6,
            "nominee_ind": 1,
            "addition": ("Metro-Goldwyn-Mayer Studio Sound Department", "co0007143"),
        },
        {
            "category_ind": 6,
            "nominee_ind": 2,
            "addition": ("RKO Radio Studio Sound Department", "co0041421"),
        },
        {
            "category_ind": 6,
            "nominee_ind": 3,
            "addition": (
                "Samuel Goldwyn - United Artists Studio Sound Department",
                "co0016710",
            ),
        },
    ],
}

imdb_removals = {
    89: [
        {
            "category_ind": 15,
            "nominee_ind": 1,
            "removal": ("Greg P. Russell", "nm0751169"),
        }
    ],
    75: [
        {
            "category_ind": 7,
            "nominee_ind": 2,
            "removal": ("Charlie Kaufman", "nm0442109"),
        }
    ],
    63: [
        {
            "category_ind": 8,
            "nominee_ind": 4,
            "removal": ("Eugene X", "nm0944310"),
        }
    ],
    59: [
        {
            "category_ind": 18,
            "nominee_ind": 2,
            "removal": ("Hugh Macdonald", "nm0531754"),
        },
        {
            "category_ind": 18,
            "nominee_ind": 2,
            "removal": ("Martin Townsend", "nm0870158"),
        },
    ],
    56: [
        {
            "category_ind": 4,
            "nominee_ind": 0,
            "removal": ("Susanne Lingheim", "nm0512801"),
        }
    ],
    50: [
        {
            "category_ind": 11,
            "nominee_ind": 2,
            "removal": ("Marcel Durham", "nm0244091"),
        }
    ],
    43: [
        {
            "category_ind": 15,
            "nominee_ind": 0,
            "removal": ("Paul McCartney", "nm0005200"),
        },
        {"category_ind": 15, "nominee_ind": 0, "removal": ("John Lennon", "nm0006168")},
        {
            "category_ind": 15,
            "nominee_ind": 0,
            "removal": ("George Harrison", "nm0365600"),
        },
        {"category_ind": 15, "nominee_ind": 0, "removal": ("Ringo Starr", "nm0823592")},
    ],
    41: [
        {
            "category_ind": 19,
            "nominee_ind": 0,
            "removal": ("Shepperton Studios", "co0103344"),
        },
        {
            "category_ind": 19,
            "nominee_ind": 1,
            "removal": ("Warner Bros./Seven Arts", "co0076018"),
        },
        {
            "category_ind": 19,
            "nominee_ind": 2,
            "removal": ("Warner Bros./Seven Arts", "co0076018"),
        },
        {
            "category_ind": 19,
            "nominee_ind": 3,
            "removal": ("Columbia Pictures", "co0050868"),
        },
        {
            "category_ind": 19,
            "nominee_ind": 4,
            "removal": ("Twentieth Century Fox", "co0000756"),
        },
    ],
    40: [
        {
            "category_ind": 20,
            "nominee_ind": 0,
            "removal": ("Samuel Goldwyn Sound Department", "co0007899"),
        },
        {
            "category_ind": 20,
            "nominee_ind": 1,
            "removal": ("Warner Bros./Seven Arts", "co0076018"),
        },
        {
            "category_ind": 20,
            "nominee_ind": 2,
            "removal": ("Metro-Goldwyn-Mayer Studios", "co0071194"),
        },
        {
            "category_ind": 20,
            "nominee_ind": 3,
            "removal": ("Twentieth Century Fox", "co0000756"),
        },
        {
            "category_ind": 20,
            "nominee_ind": 4,
            "removal": ("Universal Studios", "co0000534"),
        },
    ],
    33: [
        {
            "category_ind": 21,
            "nominee_ind": 0,
            "removal": ("Robert P. Davis", "nm0205366"),
        },
    ],
    31: [
        {
            "category_ind": 17,
            "nominee_ind": 1,
            "removal": ("Jack L. Warner", "nm0912491"),
        },
    ],
    29: [
        {
            "category_ind": 22,
            "nominee_ind": 0,
            "removal": ("George K. Arthur", "nm0037761"),
        },
    ],
    24: [
        {
            "category_ind": 21,
            "nominee_ind": 1,
            "removal": ("Les Films du Compass", "co0071214"),
        },
    ],
    23: [
        {
            "category_ind": 18,
            "nominee_ind": 0,
            "removal": ("Darryl F. Zanuck", "nm0953123"),
        },
        {
            "category_ind": 18,
            "nominee_ind": 1,
            "removal": ("S. Sylvan Simon", "nm0800373"),
        },
        {
            "category_ind": 18,
            "nominee_ind": 2,
            "removal": ("Pandro S. Berman", "nm0075825"),
        },
        {
            "category_ind": 18,
            "nominee_ind": 3,
            "removal": ("Sam Zimbalist", "nm0956547"),
        },
        {
            "category_ind": 18,
            "nominee_ind": 4,
            "removal": ("Charles Brackett", "nm0102818"),
        },
    ],
    20: [
        {
            "category_ind": 16,
            "nominee_ind": 1,
            "removal": ("Twentieth Century Fox", "co0000756"),
        },
        {
            "category_ind": 16,
            "nominee_ind": 2,
            "removal": ("Samuel Goldwyn Productions", "co0065482"),
        },
    ],
    18: [
        {
            "category_ind": 9,
            "nominee_ind": 0,
            "removal": ("Government of Great Britain", "co0027243"),
        },
        {"category_ind": 17, "nominee_ind": 6, "removal": ("Columbia", "co0004426")},
    ],
    16: [
        {"category_ind": 16, "nominee_ind": 6, "removal": ("Columbia", "co0004426")},
    ],
    13: [
        {
            "category_ind": 12,
            "nominee_ind": 7,
            "removal": ("George Stoll", "nm0006303"),
        },
        {"category_ind": 15, "nominee_ind": 0, "removal": ("Fred Quimby", "nm0703642")},
        {
            "category_ind": 15,
            "nominee_ind": 0,
            "removal": ("Rudolf Ising", "nm0411208"),
        },
        {
            "category_ind": 15,
            "nominee_ind": 2,
            "removal": ("Rudolf Ising", "nm0411208"),
        },
        {
            "category_ind": 16,
            "nominee_ind": 3,
            "removal": ("Julien Bryan", "nm0116964"),
        },
    ],
    12: [
        {
            "category_ind": 13,
            "nominee_ind": 4,
            "removal": ("Columbia", "co0004426"),
        },
        {
            "category_ind": 13,
            "nominee_ind": 9,
            "removal": ("Samuel Goldwyn Productions", "co0065482"),
        },
    ],
    11: [
        {
            "category_ind": 15,
            "nominee_ind": 8,
            "removal": ("James Wilkinson", "nm0929408"),
        },
        {
            "category_ind": 11,
            "nominee_ind": 0,
            "removal": ("Columbia", "co0004426"),
        },
    ],
    10: [
        {
            "category_ind": 11,
            "nominee_ind": 1,
            "removal": ("Frank Churchill", "nm0161430"),
        },
        {
            "category_ind": 11,
            "nominee_ind": 1,
            "removal": ("Paul J. Smith", "nm1345229"),
        },
        {
            "category_ind": 12,
            "nominee_ind": 1,
            "removal": ("Columbia", "co0004426"),
        },
        {
            "category_ind": 12,
            "nominee_ind": 3,
            "removal": ("Samuel Goldwyn Productions", "co0065482"),
        },
        {
            "category_ind": 12,
            "nominee_ind": 6,
            "removal": ("Columbia", "co0004426"),
        },
    ],
    9: [
        {
            "category_ind": 12,
            "nominee_ind": 2,
            "removal": ("Samuel Goldwyn Productions", "co0065482"),
        },
        {
            "category_ind": 12,
            "nominee_ind": 4,
            "removal": ("Columbia", "co0004426"),
        },
        {"category_ind": 13, "nominee_ind": 2, "removal": ("Hugh Harman", "nm0363414")},
        {
            "category_ind": 13,
            "nominee_ind": 2,
            "removal": ("Rudolf Ising", "nm0411208"),
        },
        {
            "category_ind": 17,
            "nominee_ind": 3,
            "removal": ("Oscar Lagerstrom", "nm0481264"),
        },
        {
            "category_ind": 13,
            "nominee_ind": 1,
            "removal": ("Max Fleischer", "nm0281502"),
        },
    ],
    8: [
        {"category_ind": 11, "nominee_ind": 1, "removal": ("Hugh Harman", "nm0363414")},
        {
            "category_ind": 11,
            "nominee_ind": 1,
            "removal": ("Rudolf Ising", "nm0411208"),
        },
    ],
    5: [
        {
            "category_ind": 9,
            "nominee_ind": 0,
            "removal": ("Paramount Publix Corporation", "co0025751"),
        },
        {
            "category_ind": 9,
            "nominee_ind": 1,
            "removal": ("Metro-Goldwyn-Mayer (MGM)", "co0007143"),
        },
        {
            "category_ind": 9,
            "nominee_ind": 2,
            "removal": ("RKO Radio Pictures", "co0041421"),
        },
        {
            "category_ind": 9,
            "nominee_ind": 3,
            "removal": ("Warner Bros.-First National Pictures", "co0152143"),
        },
    ],
    2: [
        {
            "category_ind": 5,
            "nominee_ind": 1,
            "removal": ("Feature Productions", "co0045856"),
        },
    ],
}


def match_categories(
    start: int | None = None,
    end: int | None = None,
    pending: bool = False,
    suppress: bool = True,
    show_warnings: bool = False,
    official_parser: Callable[[int], list[OfficialCategory]] = parse.parse_official,
) -> dict[int, list[MatchedCategory]]:
    """Matches official and IMDb categories for multiple editions.

    Args:
        start (int | None, optional): edition of first Oscar ceremony to
            include. If None, starts from 1st edition. Defaults to None.
        end (int | None, optional): edition of last Oscar ceremony to include.
            If None, ends at `start` if specified; otherwise, ends at
            `CURRENT_EDITION` specified in top-level `.env`. Defaults to None.
        pending (bool, optional): True if ceremony hasn't occurred yet;
            otherwise, False. Defaults to False.
        suppress (bool, optional): if True, suppress printing matched entries.
            Defaults to True.
        show_warnings (bool, optional): if True, print warnings. Defaults to
            False.
        official_parser (Callable[[int], list[OfficialCategory]], optional):
            function that accepts edition number and returns that edition's
            parsed list of OfficialCategory. Defaults to parse.parse_official.

    Returns:
        dict[int, list[MatchedCategory]]: edition -> matched categories
    """
    if start is None:
        start = 1
        if end is None:
            end = int(os.getenv("CURRENT_EDITION"))  # type: ignore
    else:
        if end is None:
            end = start

    exception_count = 0
    total = 0
    all_warnings: dict[int, list[tuple[str, str]]] = {}  # edition -> warnings
    results: dict[int, list[MatchedCategory]] = {}
    for ed in tqdm(range(start, end + 1)):
        try:
            official_categories = official_parser(ed)
            imdb_categories = parse.parse_imdb(scrape.scrape_imdb(ed))
            pre_matched: list[tuple[OfficialCategory, IMDbCategory]] = []

            # Preprocess categories
            if ed in official_nominee_replacements:
                for d in official_nominee_replacements[ed]:
                    official_categories[d["category_ind"]].nominees[
                        d["nominee_ind"]
                    ] = d["nominee"]

            if ed in official_new_titles:
                for a in official_new_titles[ed]:
                    official_categories[a["category_ind"]].nominees[
                        a["nominee_ind"]
                    ].films = a["new_titles"]

            if ed in official_nominee_removals:
                for a in official_nominee_removals[ed]:
                    official_categories[a["category_ind"]].nominees = [
                        n
                        for n in official_categories[a["category_ind"]].nominees
                        if a["films"] != n.films or a["nomination"] != n.nomination
                    ]

            # NOMINEE REMOVALS AND MERGES SHOULD NOT BE USED IN CONJUNCTION
            if (
                ed in official_nominee_merges
            ):  # for oscars 1-3 w/ winner nomination split
                for category_ind in official_nominee_merges[ed]:
                    merged_inds = set()
                    for group in official_nominee_merges[ed][category_ind]:
                        merged_inds.add(group[0])
                        merged_nominee = official_categories[category_ind].nominees[
                            group[0]
                        ]
                        for i in group[1:]:
                            merged_nominee = merge_official_nominees(
                                merged_nominee,
                                official_categories[category_ind].nominees[i],
                            )
                            merged_inds.add(i)
                        official_categories[category_ind].nominees.append(
                            merged_nominee
                        )
                    official_categories[category_ind].nominees = [
                        c
                        for i, c in enumerate(
                            official_categories[category_ind].nominees
                        )
                        if i not in merged_inds
                    ]

            if ed in imdb_new_titles:
                for a in imdb_new_titles[ed]:
                    imdb_categories[a["category_ind"]].nominees[
                        a["nominee_ind"]
                    ].films = a["new_titles"]

            if ed in imdb_removals:
                for a in imdb_removals[ed]:
                    imdb_categories[a["category_ind"]].nominees[
                        a["nominee_ind"]
                    ].people.remove(a["removal"])

            if ed in imdb_additions:
                for a in imdb_additions[ed]:
                    if a["addition"][1] not in [
                        t[1]
                        for t in (
                            imdb_categories[a["category_ind"]]
                            .nominees[a["nominee_ind"]]
                            .people
                        )
                    ]:
                        imdb_categories[a["category_ind"]].nominees[
                            a["nominee_ind"]
                        ].people.append(a["addition"])

            if ed in imdb_nominee_additions:
                for cat_ind in imdb_nominee_additions[ed]:
                    imdb_categories[cat_ind].nominees.extend(
                        imdb_nominee_additions[ed][cat_ind]
                    )

            if ed in imdb_nominee_removals:
                for a in imdb_nominee_removals[ed]:
                    imdb_categories[a["category_ind"]].nominees = [
                        n
                        for n in imdb_categories[a["category_ind"]].nominees
                        if a["films"] != n.films or a["people"] != n.people
                    ]

            # NOMINEE REMOVALS AND MERGES SHOULD NOT BE USED IN CONJUNCTION
            if ed in imdb_nominee_merges:  # for oscars 1-3 w/ winner nomination split
                for category_ind in imdb_nominee_merges[ed]:
                    merged_inds = set()
                    for group in imdb_nominee_merges[ed][category_ind]:
                        merged_inds.add(group[0])
                        merged_nominee = imdb_categories[category_ind].nominees[
                            group[0]
                        ]
                        for i in group[1:]:
                            merged_nominee = merge_imdb_nominees(
                                merged_nominee,
                                imdb_categories[category_ind].nominees[i],
                            )
                            merged_inds.add(i)
                        imdb_categories[category_ind].nominees.append(merged_nominee)
                    imdb_categories[category_ind].nominees = [
                        c
                        for i, c in enumerate(imdb_categories[category_ind].nominees)
                        if i not in merged_inds
                    ]

            # print()
            # for i, c in enumerate(imdb_categories):
            #     print(i, c.category)
            #     for j, n in enumerate(c.nominees):
            #         print("  ", j, n)

            # prior to fuzzy matching, remove all matches in OFFICIAL_TO_IMDB and EDGE_CASES from category lists
            def prematched(c: OfficialCategory) -> bool:
                nonlocal imdb_categories
                if c.category in OFFICIAL_TO_IMDB:
                    for i, ic in enumerate(imdb_categories):
                        if (
                            ic.category.lower()
                            .replace("(", "")
                            .replace(")", "")
                            .replace("-", " ")
                            .replace(",", "")
                            in OFFICIAL_TO_IMDB[c.category]
                        ):
                            pre_matched.append((c, ic))
                            imdb_categories.pop(i)
                            return True
                if c.category in EDGE_CASES:
                    if ed in EDGE_CASES[c.category]:
                        pre_matched.append(
                            (
                                c,
                                IMDbCategory(
                                    category=c.category,
                                    nominees=EDGE_CASES[c.category][ed],
                                ),
                            )
                        )
                        return True
                return False

            official_categories = [c for c in official_categories if not prematched(c)]

            imdb = [c.category for c in imdb_categories]
            official = [c.category for c in official_categories]

            post_matched = fuzzy_match(
                official,
                imdb,
                scorer=fuzz.token_set_ratio,
                preprocessor=(
                    lambda x: x.lower()
                    .replace("(", "")
                    .replace(")", "")
                    .replace("-", " ")
                    .replace(",", "")
                ),
            )[0]

            results[ed] = []

            if ed == 20:
                results[ed].append(
                    MatchedCategory(
                        category="SPECIAL AWARD", nominees=[SPECIAL_AWARD_20]
                    )
                )

            all_warnings[ed] = []

            # match nominees in pre-matched categories
            for o, i in pre_matched:
                res, warnings = match_nominees(o, i, ed, pending)
                results[ed].append(res)
                all_warnings[ed] += warnings

            # match nominees in post-matched categories
            for o_ind in post_matched:
                res, warnings = match_nominees(
                    official_categories[o_ind],
                    imdb_categories[post_matched[o_ind]],
                    ed,
                    pending,
                )
                results[ed].append(res)
                all_warnings[ed] += warnings

        except Exception as e:
            print(ed, e)
            exception_count += 1
            raise e

        total += 1

    if not suppress:
        output = {ed: [dataclasses.asdict(c) for c in results[ed]] for ed in results}
        print(exception_count, total)
        print(json.dumps(output, indent=4, ensure_ascii=False))
    if show_warnings:
        for edition in all_warnings:
            print(edition, ":", len(all_warnings[edition]), "warnings")
            for warning in all_warnings[edition]:
                print(" > ", edition, "\t", warning)
            print()

    return results


def print_imdb_categories(ed: int):
    imdb_categories = parse.parse_imdb(scrape.scrape_imdb(ed))
    for i, c in enumerate(imdb_categories):
        print(i, c.category)
        for j, n in enumerate(c.nominees):
            print("  ", j, n)


if __name__ == "__main__":
    start = int(sys.argv[1]) if len(sys.argv) > 1 else None
    end = int(sys.argv[2]) if len(sys.argv) > 2 else None
    match_categories(start, end, pending=False, suppress=False, show_warnings=True)
