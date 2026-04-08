"""
Script for interactively updating database.

Usage:
    python -m src.oscy.update <stage> <edition>

    <stage> is one of `nominations`, `unofficial`, `official`
    <edition> is an integer from 1 to `CURRENT_EDITION` in `.env`

Example:
    python -m src.oscy.update nominations 98

Data updates should happen annually in 3 stages:
    1. Nominations (mid January) - after Academy releases nominations
    2. Unofficial results (day after ceremony) - after results are posted to
       IMDb
    3. Official results (weeks after ceremony) - after official Academy database
       is updated with results

If any stage is missed, run the missed stage(s) prior to running the current
stage.
"""

import argparse
import contextlib
import os
import re
import shutil
import subprocess
from collections import defaultdict
from collections.abc import Callable
from typing import Literal

from dotenv import load_dotenv
from rapidfuzz import fuzz, process

from . import db, match, parse, scrape
from .data import MatchedCategory, MatchedNominee, OfficialCategory

load_dotenv(override=True)


def insert_pending_nominations(edition: int):
    """Interactively inserts pending nominations to db.

    Based on data from IMDb and official ceremony page.

    Args:
        edition (int): edition of Oscars ceremony
    """
    data = interactive_match_categories(
        edition, pending=True, official_parser=official_ceremony_page_parser
    )

    print("The nominees will now be inserted into the database.")

    confirm = ""
    while confirm != "yes":
        confirm = input("Confirm (yes/no): ").lower()
        if confirm == "no":
            print("Cancelling insert.")
            return

    # insert new edition
    db.insert_editions(edition)

    # insert to editions_category_names
    db.insert_editions_category_names(edition, data)

    # insert nominees
    matched_nominees = [n for ed in data for c in data[ed] for n in c.nominees]
    db.insert_nominees(matched_nominees)

    print("Data insertion complete.")


def update_unofficial_results(edition: int):
    """Interactively updates db with unofficial results.

    Based on data from IMDb and official ceremony page. Matches IMDb/official
    data, then compares this to db data and suggests updates/inserts/deletes.

    Args:
        edition (int): edition of Oscars ceremony
    """
    matched_categories = interactive_match_categories(
        edition, pending=False, official_parser=official_ceremony_page_parser
    )[edition]
    compare_update_nominees(edition, matched_categories)
    print("Data update complete.")


def update_official_results(edition: int):
    """Interactively updates db with official results.

    Based on data from IMDb and official Academy Awards database. Matches
    IMDb/official data, then compares this to db data and suggests
    updates/inserts/deletes.

    Args:
        edition (int): edition of Oscars ceremony
    """
    matched_categories = interactive_match_categories(
        edition, pending=False, official_parser=official_database_parser
    )[edition]
    compare_update_nominees(edition, matched_categories)
    print("Data update complete.")


def interactive_match_categories(
    edition: int,
    pending: bool,
    official_parser: Callable[[int], list[OfficialCategory]],
) -> dict[int, list[MatchedCategory]]:
    """Interactively matches IMDb and official categories.

    Calls `match.match_categories()` with full debug output and warnings
    redirected to `output` file, which is opened for manual review by user and
    must be closed to continue.

    Args:
        edition (int): edition of Oscars ceremony
        pending (bool): True if ceremony hasn't occurred yet (nominations
            stage); otherwise, False (unofficial, official stages)
        official_parser (Callable[[int], list[OfficialCategory]]): parser passed
            to `match.match_categories()`, which may be interactive

    Returns:
        dict[int, list[MatchedCategory]]: edition -> matched categories
    """
    with open("output", "w+", encoding="utf-8") as fd:
        with contextlib.redirect_stderr(fd):
            matched_categories = match.match_categories(
                edition,
                pending=pending,
                official_parser=official_parser,
                suppress=False,
                show_warnings=True,
                imdb_force=True,
            )

    code_editor = shutil.which("code")
    if code_editor:
        editor = [code_editor, "--wait"]
    else:
        editor = ["vi"]

    print("Please review the output file and confirm its accuracy.")
    print("Waiting for your editor to close the file...")

    subprocess.call(editor + ["output"])

    return matched_categories


def official_ceremony_page_parser(edition: int) -> list[OfficialCategory]:
    """Scrapes and parses official ceremony page.

    Official parsers take an edition as input and output a list of parsed
    categories using data from an official source; they are passed to
    `match.match_categories()`. This parser gets data from the Academy's
    official ceremony page and should be used for the nomination and unofficial
    update stages.

    This function calls `compare_insert_category_names()`, allowing the user to
    interactively change category names and potentially insert new category
    names/categories/category groups to db.

    Args:
        edition (int): edition of Oscars ceremony

    Returns:
        list[OfficialCategory]: parsed categories
    """
    official_categories = scrape.scrape_official_ceremony_page(edition)
    return compare_insert_category_names(edition, official_categories)


def official_database_parser(edition: int) -> list[OfficialCategory]:
    """Scrapes and parses official database.

    Official parsers take an edition as input and output a list of parsed
    categories using data from an official source; they are passed to
    `match.match_categories()`. This parser gets data from the Academy's
    official database and should be used for the official update stage.

    This function calls `compare_insert_category_names()`, allowing the user to
    interactively change category names and potentially insert new category
    names/categories/category groups to db.

    Args:
        edition (int): edition of Oscars ceremony

    Returns:
        list[OfficialCategory]: parsed categories
    """
    scrape.scrape_official_database(edition)
    official_categories = parse.parse_official(edition)
    return compare_insert_category_names(edition, official_categories)


def compare_insert_category_names(
    edition: int,
    official_categories: list[OfficialCategory],
) -> list[OfficialCategory]:
    """Interactively compares and inserts official category names to db.

    Compares official category names against db category names used in current
    or previous edition, depending on stage. Allows user to edit non-matching
    OfficialCategory names and insert new category names, categories, and
    category groups to db.

    Args:
        edition (int): edition of Oscars ceremony
        official_categories (list[OfficialCategory]): list of categories, whose
            names will be compared against db

    Returns:
        list[OfficialCategory]: list of categories with updated category names
    """
    official_category_names = [c.category for c in official_categories]

    # all official category names in db
    db_category_names = db.get_category_names_official()

    # category names used in current and prev edition, lowercase
    db_category_names_current = set(
        c.lower() for c in db.get_category_names_official(edition)
    )
    db_category_names_prev = set(
        c.lower() for c in db.get_category_names_official(edition - 1)
    )
    compare_current_category_names = True
    if len(db_category_names_current) != len(official_category_names):
        compare_current_category_names = False

    # all categories in db
    db_categories = db.get_categories()

    # all category groups in db
    db_category_groups = db.get_category_groups()

    print()
    print("OSCARS", edition)

    if compare_current_category_names:
        if len(official_category_names) != len(db_category_names_current):
            print()
            print(
                f"WARNING: lengths of official_category_names ({len(official_category_names)}) and db_category_names from current edition ({len(db_category_names_current)}) do not match"
            )
    else:
        if len(official_category_names) != len(db_category_names_prev):
            print()
            print(
                f"WARNING: lengths of official_category_names ({len(official_category_names)}) and db_category_names from prev edition ({len(db_category_names_prev)}) do not match"
            )

    for i, c in enumerate(official_category_names):
        if (
            compare_current_category_names
            and c.lower() not in db_category_names_current
        ) or (
            not compare_current_category_names
            and c.lower() not in db_category_names_prev
        ):
            confirm = ""
            input_category_name_official = ""
            input_category_name_common = ""
            input_category = ""
            input_category_group = ""
            print()

            while confirm != "yes":
                confirm = ""
                input_category_name_official = ""
                input_category_name_common = ""
                input_category = ""
                input_category_group = ""

                print(
                    f"The category name '{c}' was not used in the {'current' if compare_current_category_names else 'previous'} edition."
                )
                print()

                # get closest category name matches
                matrix = process.cdist(
                    [c],
                    db_category_names,
                    scorer=fuzz.token_set_ratio,
                    processor=lambda x: (
                        x.lower()
                        .replace("(", "")
                        .replace(")", "")
                        .replace("-", " ")
                        .replace(",", "")
                    ),
                )
                scores = matrix[0]
                indices = scores.argsort()[
                    ::-1
                ]  # indices of scores sorted in desc order

                print("The closest matches are...")
                for ind in indices[:3]:
                    print(db_category_names[ind], "--", scores[ind])
                print()

                # Input the desired official category name (case-sensitive). If your
                # input does not match any existing category name in the database,
                # you will be prompted to insert a new one.
                while input_category_name_official.strip() == "":
                    input_category_name_official = input(
                        "Input the desired official category name (case-sensitive):\n"
                    )

                if input_category_name_official not in db_category_names:
                    # <input> is a new category name. Input the common name of this
                    # category name.
                    print()
                    while input_category_name_common.strip() == "":
                        input_category_name_common = input(
                            f"'{input_category_name_official}' is a new category name. Input its common name (case-sensitive):\n"
                        )

                    # Input the category it belongs to (case-sensitive). If your
                    # input does not match any existing category in the database,
                    # you will be prompted to insert a new one.
                    print()
                    while input_category.strip() == "":
                        input_category = input(
                            "Input the category it belongs to (case-sensitive):\n"
                        )

                    if input_category not in db_categories:
                        # <input> is a new category. Input the category group it
                        # belongs to (case-sensitive). If your input does not match
                        # any existing category group in the database, you will be
                        # prompted to insert a new one.
                        print()
                        while input_category_group.strip() == "":
                            input_category_group = input(
                                f"'{input_category}' is a new category. Input the category group it belongs to (case-sensitive):\n"
                            )

                    # You are about to insert the following entries into the database:
                    # table (columns)                                       values
                    # category_names (award, official_name, common_name)    ('oscar', <input1>, <input2>)
                    # categories (award, name)                              ('oscar', <input3>)
                    # category_groups (award, name)                         ('oscar', <input4>)
                    #
                    # Confirm (yes/no)
                    width = 54
                    print()
                    print(
                        "You are about to insert the following entries into the database:"
                    )
                    print()
                    print("table (columns)".ljust(width), end="")
                    print("values")
                    print(
                        "category_names (award, official_name, common_name)".ljust(
                            width
                        ),
                        end="",
                    )
                    print(
                        f"('oscar', '{input_category_name_official}', '{input_category_name_common}')"
                    )
                    if input_category not in db_categories:
                        print("categories (award, name)".ljust(width), end="")
                        print(f"('oscar', '{input_category}')")

                        if input_category_group not in db_category_groups:
                            print("category_groups (award, name)".ljust(width), end="")
                            print(f"('oscar', '{input_category_group}')")

                    print()
                    while confirm != "yes" and confirm != "no":
                        confirm = input("Confirm (yes/no): ").lower()

                    print()

                    # insert new category name/category/category group
                    db.insert_category_name(
                        category_name_official=input_category_name_official,
                        category_name_common=input_category_name_common,
                        category=input_category,
                        new_category=(input_category not in db_categories),
                        category_group=input_category_group,
                        new_category_group=(
                            input_category_group not in db_category_groups
                        ),
                    )

                else:
                    confirm = "yes"

            print()
            print(
                f"'{input_category_name_official}' will replace '{c}' as the official category name."
            )
            print()

            official_categories[i].category = input_category_name_official

    return official_categories


def compare_update_nominees(edition: int, matched_categories: list[MatchedCategory]):
    """Interactively compares and updates scraped nominees to db.

    Matches categories, then fuzzy matches nominees. If number of nominees
    within a category differs, suggests inserts/deletes. Compares matched
    nominee properties for exactness and interactively suggests
    updates/upserts/deletes.

    Args:
        edition (int): edition of Oscars ceremony
        matched_categories (list[MatchedCategory]): scraped, matched categories
            returned by `match.match_categories()`

    Raises:
        Exception: failure to match items
    """
    # matched_categories should have matching category names with same edition
    # already inserted into db; sorting by lowercase official name should match
    # category indices with db
    matched_categories.sort(key=lambda c: c.category.lower())
    db_matched_categories = db.get_matched_categories_by_edition(edition)

    if len(matched_categories) != len(db_matched_categories):
        print(
            f"# of categories scraped ({len(matched_categories)}) and in db ({len(db_matched_categories)}) do not match"
        )
        return

    for i in range(len(matched_categories)):
        matched_nominees = matched_categories[i].nominees
        db_matched_nominees = db_matched_categories[i].nominees

        # handle cases where matched_nominees and db_matched_nominees have
        # different lengths
        matched_longer_than_db = False
        shorter_nominees = matched_nominees
        longer_nominees = db_matched_nominees

        if len(matched_nominees) < len(db_matched_nominees):
            print(
                f"WARNING: {db_matched_categories[i].category}: there are less scraped nominees ({len(matched_nominees)}) than in database ({len(db_matched_nominees)})"
            )
        elif len(matched_nominees) > len(db_matched_nominees):
            matched_longer_than_db = True
            shorter_nominees, longer_nominees = longer_nominees, shorter_nominees
            print(
                f"WARNING: {db_matched_categories[i].category}: there are more scraped nominees ({len(matched_nominees)}) than in database ({len(db_matched_nominees)})"
            )

        # fuzzy match nominees: calculate similarity for titles/detail and
        # statements separately, add scores and take max for best match
        titles = [
            " | ".join(t[0] + " - " + ", ".join(t[3]) for t in n.films)
            for n in matched_nominees
        ]
        db_titles = [
            " | ".join(t[0] + " - " + ", ".join(t[3]) for t in n.films)
            for n in db_matched_nominees
        ]
        statements = [n.statement for n in matched_nominees]
        db_statements = [n.statement for n in db_matched_nominees]

        titles_matrix = process.cdist(titles, db_titles, scorer=fuzz.ratio)
        statements_matrix = process.cdist(statements, db_statements, scorer=fuzz.ratio)

        matrix = titles_matrix + statements_matrix
        if matched_longer_than_db:
            # transpose matrix s.t. # rows is always <= # cols; rows always
            # corresponds to shorter of matched_nominees or db_matched_nominees
            matrix = matrix.T

        # res[i] is col ind of highest score in row i
        res = matrix.argmax(axis=1)

        # there should now be len(longer_nominees)-len(shorter_nominees)
        # remaining unmatched elements in longer_nominees, which should then be
        # inserted or deleted; if there are more unmatched elements, multiple
        # elements in shorter_nominees had best match to same element in
        # longer_nominees, so throw error
        matches: defaultdict[int, list[int]] = defaultdict(
            list
        )  # longer nominee list ind -> matching inds in shorter nominee list

        for i, j in enumerate(res):
            matches[j].append(i)

        shorter_remaining_inds = []
        longer_remaining_inds = []

        for j in range(len(matrix[0])):
            if len(matches[j]) == 0:
                # nominee in longer list unmatched
                longer_remaining_inds.append(j)
            elif len(matches[j]) > 1:
                # nominee in longer list matched more than once
                longer_remaining_inds.append(j)
                for i in matches[j]:
                    shorter_remaining_inds.append(i)

        if len(longer_remaining_inds) > len(longer_nominees) - len(shorter_nominees):
            raise Exception(
                "Failed to match items:",
                "scraped:" if not matched_longer_than_db else "db:",
                shorter_nominees,
                "db:" if not matched_longer_than_db else "scraped:",
                longer_nominees,
            )

        # # warn on inexact matches
        # for i, j in enumerate(res):
        #     if matrix[i][res[i]] != 200:
        #         print("WARNING: inexact nominee match:")
        #         print("- ", shorter_nominees[i])
        #         print("- ", longer_nominees[res[i]])
        #         print("--", matrix[i][res[i]])
        #         print()

        if len(matched_nominees) > len(db_matched_nominees):
            # suggest nominee insertions from longer_remaining_inds
            insert_matched_nominees = [
                matched_nominees[i] for i in longer_remaining_inds
            ]
            print(
                f"The following {len(insert_matched_nominees)} nominees were scraped but are not in the db. They will be inserted:",
                insert_matched_nominees,
            )
            confirm = ""
            while confirm != "yes":
                confirm = input("Confirm (yes/no): ").lower()
                if confirm == "no":
                    print("Cancelling insert.")
                    return
            db.insert_nominees(insert_matched_nominees)

        elif len(matched_nominees) < len(db_matched_nominees):
            # suggest nominee deletions from longer_remaining_inds
            delete_matched_nominees = [
                db_matched_nominees[i] for i in longer_remaining_inds
            ]
            print(
                f"The following {len(delete_matched_nominees)} are in the db but were not scraped. They will be deleted from the db:",
                delete_matched_nominees,
            )
            confirm = ""
            while confirm != "yes":
                confirm = input("Confirm (yes/no): ").lower()
                if confirm == "no":
                    print("Cancelling delete.")
                    return
            db.delete_nominees(delete_matched_nominees)

        # for each pair of matching scraped/db nominees, compare and update
        # properties in db (except pending)
        for shorter_ind, longer_ind in enumerate(res):
            if len(matched_nominees) <= len(db_matched_nominees):
                compare_update_nominee_properties(
                    matched_nominees[shorter_ind], db_matched_nominees[longer_ind]
                )
            else:
                compare_update_nominee_properties(
                    matched_nominees[longer_ind], db_matched_nominees[shorter_ind]
                )

    # bulk update pending=FALSE for all nominees in this edition
    db.update_nominees_pending_false(edition)


def compare_update_nominee_properties(
    n1: MatchedNominee, n2: MatchedNominee, ignored_properties: list[str] = []
) -> bool:
    """Interactively compares and updates scraped nominee properties to db.

    Compares for exactness across all unignored properties, except for
    `pending`.

    Args:
        n1 (MatchedNominee): scraped nominee
        n2 (MatchedNominee): db nominee
        ignored_properties (list[str], optional): nominee properties to ignore
            during comparison. Defaults to [].

    Raises:
        ValueError: at least one of n1, n2 must have a database id

    Returns:
        bool: True if nominees are equal across all compared properties;
            otherwise, False
    """
    properties = [
        "edition",
        # "category_name",
        "winner",
        "statement",
        "films",
        "people",
        "is_person",
        "note",
        "official",
        "stat",
        # "pending",
    ]

    checked_properties = set(properties) - set(ignored_properties)

    # n1 should always be scraped, n2 from db
    if n1.id is not None:
        n1, n2 = n2, n1

    if n2.id is None:
        raise ValueError(
            "At least one of the MatchedNominee's must have a database id."
        )

    if n1.category_name.lower() != n2.category_name.lower():
        print(
            f"Category names do not match: '{n1.category_name}', '{n2.category_name}'"
        )
        return False

    # sort films and people by name (matches db query)
    n1.films.sort(key=lambda t: t[0])
    n1.people.sort(key=lambda t: t[0])

    # compare for exactness across all properties
    update_nominee_row = False
    unequal_properties: set[str] = set()
    for p in checked_properties:
        p1 = getattr(n1, p)
        p2 = getattr(n2, p)
        if isinstance(p1, list) and isinstance(p2, list):
            p1_set = {
                tuple(tuple(e) if isinstance(e, list) else e for e in elm) for elm in p1
            }
            p2_set = {
                tuple(tuple(e) if isinstance(e, list) else e for e in elm) for elm in p2
            }
            if p1_set != p2_set:
                print()
                print(
                    f"ACTION REQUIRED: nominees do not match on property `{p}`:\n-  {n1}\n-  {n2}\n"
                )
                unequal_properties.add(p)
        else:
            if p1 != p2:
                print()
                print(
                    f"ACTION REQUIRED: nominees do not match on property `{p}`:\n-  {n1}\n-  {n2}\n"
                )
                update_nominee_row = True
                unequal_properties.add(p)

    if len(unequal_properties) > 0:
        if update_nominee_row:
            print("Update scraped nominee -> db (excludes films and people)?")
            print("new:", n1)
            print("old:", n2)

            confirm = ""
            while confirm != "yes" and confirm != "no":
                confirm = input("Confirm (yes/no): ").lower()

            if confirm == "yes":
                db.update_nominee(n2.id, n1)

            print()

        # if films or people in unequal_properties, prompt user to manually
        # match elements, then prompt to upsert/delete
        if "films" in unequal_properties:
            match_update_films_or_people("films", n1.films, n2.films, n2.id)

        if "people" in unequal_properties:
            match_update_films_or_people("people", n1.people, n2.people, n2.id)

        return False

    return True


NomineeItem = Literal["films", "people"]


def match_update_films_or_people(
    item: NomineeItem, n1_items: list, n2_items: list, nominee_id: int
):
    """Interactively matches nominee films or people and updates db.

    Args:
        item (NomineeItem): "films" or "people"
        n1_items (list): scraped nominee's list of films or people
        n2_items (list): db nominee's list of films or people
        nominee_id (int): db nominee's database id
    """
    longest_n1 = max(len(str(f)) for f in n1_items)

    print(f"nominee {item} do not match:")
    print("scraped".ljust(longest_n1 + 3), "\t", "db")
    for i in range(max(len(n1_items), len(n2_items))):
        print(
            str(i).ljust(3),
            (str(n1_items[i]) if i < len(n1_items) else "").ljust(longest_n1),
            "\t",
            str(i).ljust(3),
            str(n2_items[i]) if i < len(n2_items) else "",
        )

    valid_input = False
    pattern = r"(?:\s*\d+\s*,\s*\d+\s*(?:;\s*\d+\s*,\s*\d+\s*)*)?"

    while not valid_input:
        input_pairs = input(
            f"Match the {item} by indices. Pairs should be separated by a semicolon. For example: 0,1; 1,0; 2,2\n"
        )
        if re.fullmatch(pattern, input_pairs):
            matched_inds: dict[int, int] = {}  # n1 (scraped) ind -> n2 (db) ind
            n1_used_inds: set[int] = set()
            n2_used_inds: set[int] = set()
            pairs = input_pairs.split(";")

            valid_input = True
            for pair in pairs:
                indices = pair.split(",")
                indices = [int(i.strip()) for i in indices]

                if (
                    indices[0] < len(n1_items)
                    and indices[1] < len(n2_items)
                    and indices[0] not in n1_used_inds
                    and indices[1] not in n2_used_inds
                ):
                    n1_used_inds.add(indices[0])
                    n2_used_inds.add(indices[1])
                    matched_inds[indices[0]] = indices[1]
                else:
                    valid_input = False
                    print("Invalid input: invalid index or duplicate indices used")
                    break

            if not valid_input:
                continue

            print()
            print(f"Matches ({len(matched_inds)}):")
            for n1_ind, n2_ind in matched_inds.items():
                print(
                    str(n1_ind).ljust(3),
                    str(n1_items[n1_ind]).ljust(longest_n1),
                    "\t",
                    str(n2_ind).ljust(3),
                    str(n2_items[n2_ind]),
                )

            print()
            print(
                f"Unmatched {item} ({len(n1_items) + len(n2_items) - 2 * len(matched_inds)}):"
            )
            for i in range(max(len(n1_items), len(n2_items))):
                print(
                    str(i).ljust(3),
                    (
                        str(n1_items[i])
                        if i < len(n1_items) and i not in n1_used_inds
                        else ""
                    ).ljust(longest_n1),
                    "\t",
                    str(i).ljust(3),
                    str(n2_items[i])
                    if i < len(n2_items) and i not in n2_used_inds
                    else "",
                )

            # prompt each pair of matched_inds for upsert with n1 or ignore
            for n1_ind, n2_ind in matched_inds.items():
                n1_item = tuple(
                    tuple(e) if isinstance(e, list) else e for e in n1_items[n1_ind]
                )
                n2_item = tuple(
                    tuple(e) if isinstance(e, list) else e for e in n2_items[n2_ind]
                )

                if n1_item != n2_item:
                    print()
                    print(f"Update scraped.{item}[{n1_ind}] -> db.{item}[{n2_ind}]?")
                    print("new:", n1_items[n1_ind])
                    print("old:", n2_items[n2_ind])

                    confirm = ""
                    while confirm != "yes" and confirm != "no":
                        confirm = input("Confirm (yes/no): ").lower()

                    if confirm == "yes":
                        dispatch_upsert(
                            item=item,
                            nominee_id=nominee_id,
                            data=n1_items[n1_ind],
                        )

                        # if imdb id differs, delete entry from associative
                        # table (nominees_titles or nominees_entities) and
                        # potentially from titles/entities
                        if n1_items[n1_ind][1] != n2_items[n2_ind][1]:
                            dispatch_delete(
                                item=item,
                                nominee_id=nominee_id,
                                imdb_id=n2_items[n2_ind][1],
                            )

            # prompt each unmatched ind in n1_items for upsert or ignore
            for i in range(len(n1_items)):
                if i not in n1_used_inds:
                    print()
                    print(f"Upsert scraped.{item}[{i}]?")
                    print("new:", n1_items[i])

                    confirm = ""
                    while confirm != "yes" and confirm != "no":
                        confirm = input("Confirm (yes/no): ").lower()

                    if confirm == "yes":
                        dispatch_upsert(
                            item=item,
                            nominee_id=nominee_id,
                            data=n1_items[i],
                        )

            # prompt each unmatched ind in n2_items for delete or ignore
            for i in range(len(n2_items)):
                if i not in n2_used_inds:
                    print()
                    print(f"Delete db.{item}[{i}]?")
                    print("current:", n2_items[i])

                    confirm = ""
                    while confirm != "yes" and confirm != "no":
                        confirm = input("Confirm (yes/no): ").lower()

                    if confirm == "yes":
                        dispatch_delete(
                            item=item, nominee_id=nominee_id, imdb_id=n2_items[i][1]
                        )

        else:
            print("Invalid input: follow the example format")


def dispatch_upsert(item: NomineeItem, nominee_id: int, data: list):
    """Calls appropriate db upsert function based on `item`.

    Upserts title or entity, then uses returned id to upsert entry in
    associative table.

    Args:
        item (NomineeItem): "films" or "people"
        nominee_id (int): db nominee id
        data (list): list of films or people (see `data.MatchedNominee` for
            details)
    """
    if item == "films":
        db.upsert_nominee_title(
            nominee_id=nominee_id,
            title=data[0],
            imdb_id=data[1],
            winner=data[2],
            detail=data[3],
        )
    else:
        db.upsert_nominee_entity(
            nominee_id=nominee_id,
            name=data[0],
            imdb_id=data[1],
            statement_ind=data[2],
            role=data[3],
        )


def dispatch_delete(item: NomineeItem, nominee_id: int, imdb_id: str):
    """Calls appropriate db delete function based on `item`.

    Deletes entry from associative table, then deletes title or entity if it has
    no more entries in associative table.

    Args:
        item (NomineeItem): "films" or "people"
        nominee_id (int): db nominee id
        imdb_id (str): IMDb id of title or entity
    """
    if item == "films":
        db.delete_nominee_title(nominee_id=nominee_id, imdb_id=imdb_id)
    else:
        db.delete_nominee_entity(nominee_id=nominee_id, imdb_id=imdb_id)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage", type=str, choices=["nominations", "unofficial", "official"]
    )
    parser.add_argument("edition", type=int)

    args = parser.parse_args()

    edition = args.edition
    if edition <= 0 or edition > int(os.getenv("CURRENT_EDITION")):  # type: ignore
        raise ValueError(
            f"edition must be between 1 and {os.getenv('CURRENT_EDITION')}"
        )

    if args.stage == "nominations":
        insert_pending_nominations(edition)
    elif args.stage == "unofficial":
        update_unofficial_results(edition)
    elif args.stage == "official":
        update_official_results(edition)
    else:
        raise ValueError("stage must be one of: nominations, unofficial, official")


if __name__ == "__main__":
    try:
        with db.create_or_continue_transaction():
            main()
    finally:
        db.close()
