"""
Functions for matching IMDb data with official data.

As a script, matches data for multiple editions with full debug output and
warnings to stderr.

Usage:
    python -m src.oscy.match [<start>] [<end>]

    <start> (optional) is the first edition to match; if empty, starts from 1st
        edition.
    <end> (optional) is the last edition to match; if empty, ends at <start> if
        specified; otherwise, ends at `CURRENT_EDITION` specified in top-level
        `.env`.
"""

import contextlib
import dataclasses
import json
import os
import re
import sys
from typing import Callable

import numpy as np
import yaml
from dotenv import load_dotenv
from rapidfuzz import fuzz, process
from tqdm import tqdm

from . import parse, scrape
from .data import (
    IMDbCategory,
    IMDbNominee,
    MatchedCategory,
    MatchedNominee,
    OfficialCategory,
    OfficialNominee,
)
from .match_constants import (
    EDGE_CASES,
    IMDB_ADDITIONS,
    IMDB_NEW_TITLES,
    IMDB_NOMINEE_ADDITIONS,
    IMDB_NOMINEE_MERGES,
    IMDB_NOMINEE_REMOVALS,
    IMDB_REMOVALS,
    NICKNAMES,
    NOMINATION_TO_PERSON,
    OFFICIAL_NEW_TITLES,
    OFFICIAL_NOMINEE_MERGES,
    OFFICIAL_NOMINEE_REMOVALS,
    OFFICIAL_NOMINEE_REPLACEMENTS,
    OFFICIAL_TO_IMDB,
    SPECIAL_AWARD_20,
    SPLIT_EXCEPTIONS,
    STUDIOS,
)

load_dotenv(override=True)


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

    longest_official = max(len(str(s)) for s in official)
    longest_imdb = max(len(str(s)) for s in imdb)

    if not suppress:
        print(
            "official".ljust(longest_official + 3), "\t", "imdb".ljust(longest_imdb + 3)
        )

    for official_i, imdb_i in enumerate(res):
        if not suppress:
            print(
                str(official_i).ljust(3),
                str(official[official_i]).ljust(longest_official),
                "\t",
                str(imdb_i).ljust(3),
                str(imdb[imdb_i]).ljust(longest_imdb),
                "\t",
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
    match: bool = True,
    suppress: bool = True,
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
        suppress (bool, optional): if True, suppress printing matched entries.
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
    matches = match_from_scores(official, imdb, matrix, suppress) if match else {}
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
        "Script collaborators - ",
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


def match_categories(
    start: int | None = None,
    end: int | None = None,
    pending: bool = False,
    suppress: bool = True,
    show_warnings: bool = False,
    imdb_force: bool = False,
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
        imdb_force (bool, optional): if True, force fresh scrape of IMDb data
            even if data already saved in file. Defaults to False.
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
    for ed in tqdm(range(start, end + 1), file=sys.stdout):
        try:
            official_categories = official_parser(ed)
            imdb_categories = parse.parse_imdb(scrape.scrape_imdb(ed, force=imdb_force))
            pre_matched: list[tuple[OfficialCategory, IMDbCategory]] = []

            with contextlib.redirect_stdout(sys.stderr):
                # Preprocess categories
                if ed in OFFICIAL_NOMINEE_REPLACEMENTS:
                    for d in OFFICIAL_NOMINEE_REPLACEMENTS[ed]:
                        official_categories[d["category_ind"]].nominees[
                            d["nominee_ind"]
                        ] = d["nominee"]

                if ed in OFFICIAL_NEW_TITLES:
                    for a in OFFICIAL_NEW_TITLES[ed]:
                        official_categories[a["category_ind"]].nominees[
                            a["nominee_ind"]
                        ].films = a["new_titles"]

                if ed in OFFICIAL_NOMINEE_REMOVALS:
                    for a in OFFICIAL_NOMINEE_REMOVALS[ed]:
                        official_categories[a["category_ind"]].nominees = [
                            n
                            for n in official_categories[a["category_ind"]].nominees
                            if a["films"] != n.films or a["nomination"] != n.nomination
                        ]

                # NOMINEE REMOVALS AND MERGES SHOULD NOT BE USED IN CONJUNCTION
                if (
                    ed in OFFICIAL_NOMINEE_MERGES
                ):  # for oscars 1-3 w/ winner nomination split
                    for category_ind in OFFICIAL_NOMINEE_MERGES[ed]:
                        merged_inds = set()
                        for group in OFFICIAL_NOMINEE_MERGES[ed][category_ind]:
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

                if ed in IMDB_NEW_TITLES:
                    for a in IMDB_NEW_TITLES[ed]:
                        imdb_categories[a["category_ind"]].nominees[
                            a["nominee_ind"]
                        ].films = a["new_titles"]

                if ed in IMDB_REMOVALS:
                    for a in IMDB_REMOVALS[ed]:
                        imdb_categories[a["category_ind"]].nominees[
                            a["nominee_ind"]
                        ].people.remove(a["removal"])

                if ed in IMDB_ADDITIONS:
                    for a in IMDB_ADDITIONS[ed]:
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

                if ed in IMDB_NOMINEE_ADDITIONS:
                    for cat_ind in IMDB_NOMINEE_ADDITIONS[ed]:
                        imdb_categories[cat_ind].nominees.extend(
                            IMDB_NOMINEE_ADDITIONS[ed][cat_ind]
                        )

                if ed in IMDB_NOMINEE_REMOVALS:
                    for a in IMDB_NOMINEE_REMOVALS[ed]:
                        imdb_categories[a["category_ind"]].nominees = [
                            n
                            for n in imdb_categories[a["category_ind"]].nominees
                            if a["films"] != n.films or a["people"] != n.people
                        ]

                # NOMINEE REMOVALS AND MERGES SHOULD NOT BE USED IN CONJUNCTION
                if (
                    ed in IMDB_NOMINEE_MERGES
                ):  # for oscars 1-3 w/ winner nomination split
                    for category_ind in IMDB_NOMINEE_MERGES[ed]:
                        merged_inds = set()
                        for group in IMDB_NOMINEE_MERGES[ed][category_ind]:
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
                            imdb_categories[category_ind].nominees.append(
                                merged_nominee
                            )
                        imdb_categories[category_ind].nominees = [
                            c
                            for i, c in enumerate(
                                imdb_categories[category_ind].nominees
                            )
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

                official_categories = [
                    c for c in official_categories if not prematched(c)
                ]

                imdb = [c.category for c in imdb_categories]
                official = [c.category for c in official_categories]

                post_matched = fuzzy_match(
                    official,
                    imdb,
                    scorer=fuzz.token_set_ratio,
                    preprocessor=(
                        lambda x: (
                            x.lower()
                            .replace("(", "")
                            .replace(")", "")
                            .replace("-", " ")
                            .replace(",", "")
                        )
                    ),
                    suppress=suppress,
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

    with contextlib.redirect_stdout(sys.stderr):
        if not suppress:
            res = {ed: [dataclasses.asdict(c) for c in results[ed]] for ed in results}
            print()
            print("Editions throwing exceptions:", exception_count)
            print("Total editions:", total)
            print()
            print(json.dumps(res, indent=4, ensure_ascii=False))
            print()
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
    match_categories(
        start, end, pending=False, suppress=False, show_warnings=True, imdb_force=False
    )
