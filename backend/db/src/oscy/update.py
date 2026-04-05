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
from typing import Callable, Literal

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
    # - scrape nominations from official ceremony page
    # - within a custom parser that's passed to match.match_categories:
    #   - match category names against official names in db
    #   - flag if number of category names this year differs from prev year
    #   - if category names do not match, ask for user input on official names
    #     - if user inputs a new category name, ask user input for category
    #     - if user inputs a new category, ask user input for category group
    #     - upsert category name/category/category group

    data = interactive_match(
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

    # NEED TO FORCE REVIEW OF WARNINGS AND JSON PRIOR TO INSERTION, AND WRAP
    # EVERYTHING IN A SINGLE TX

    print("Data insertion complete.")


def update_unofficial_results(edition: int):
    """Interactively updates db with unofficial results.

    Based on data from IMDb and official ceremony page. Matches IMDb/official
    data, then compares this to db data and suggests updates/inserts/deletes.

    Args:
        edition (int): edition of Oscars ceremony
    """
    matched_categories = interactive_match(
        edition, pending=False, official_parser=official_ceremony_page_parser
    )[edition]
    update_db(edition, matched_categories)
    print("Data update complete.")


def update_official_results(edition: int):
    """Interactively updates db with official results.

    Based on data from IMDb and official Academy Awards database. Matches
    IMDb/official data, then compares this to db data and suggests
    updates/inserts/deletes.

    Args:
        edition (int): edition of Oscars ceremony
    """
    matched_categories = interactive_match(
        edition, pending=False, official_parser=official_database_parser
    )[edition]
    update_db(edition, matched_categories)
    print("Data update complete.")


def official_ceremony_page_parser(edition: int) -> list[OfficialCategory]:
    # used for nomination and unofficial updates
    official_categories = scrape.scrape_official_ceremony_page(edition)
    return interactive_category_match(edition, official_categories)


def official_database_parser(edition: int) -> list[OfficialCategory]:
    # used for official updates
    scrape.scrape_official_database(edition)
    official_categories = parse.parse_official(edition)
    return interactive_category_match(edition, official_categories)


def interactive_category_match(
    edition: int,
    official_categories: list[OfficialCategory],
) -> list[OfficialCategory]:
    # match category names for exactness against official names in db and check
    # against category names used in current or prev year; allow user to insert
    # new category name/category/category group
    official_category_names = [c.category for c in official_categories]

    # all official category names in db
    db_category_names = db.get_category_names_official()

    # category names used in current or prev edition, lowercase
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
                    # category_names (award, official_name, common_name)    ('oscar', <input1> <input2>)
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


def interactive_match(
    edition: int,
    pending: bool,
    official_parser: Callable[[int], list[OfficialCategory]],
) -> dict[int, list[MatchedCategory]]:
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


def update_db(edition: int, matched_categories: list[MatchedCategory]):
    # compare scraped data against db via python objects (ignore pending status,
    # winner status);
    # if imdb id has changed, and this id is only used in the current year, suggest deletion and insertion
    # if official name has changed, but imdb id still same, update name in both entities and nominees_entities
    # tick off pendings in nominees
    # mark winners

    matched_categories.sort(key=lambda c: c.category.lower())
    db_matched_categories = db.get_matched_categories_by_edition(edition)

    if len(matched_categories) != len(db_matched_categories):
        print(
            f"# of categories scraped ({len(matched_categories)}) and in db ({len(db_matched_categories)}) do not match"
        )
        return

    # before checking for nominee exact matches, do fuzzy matching; then compare
    # for exactness and suggest updates, deletions, and insertions
    # - warn on any exact field change except pending (no matter how small,
    #   regardless of fuzzy match results)
    # - update winner (both nominees.winner and nominees_titles.winner)
    # - update statement
    # - update note
    # - update official
    # - update stat
    # - update pending in bulk at end
    # - fuzzy match films
    #   - if imdb id has changed: (1) find corresponding row in nominees_titles
    #     and delete; if this title now has no rows in nominees_titles, then
    #     delete it; (2) create new entries in nominees_titles and titles
    #   - if title or detail have changed, update titles or nominees_titles
    # - fuzzy match people
    #   - if more scraped people than db people, suggest insertions
    #   - if less scraped people than db people, suggest deletions
    #   - if imdb id has changed: (1) find corresponding row in
    #     nominees_entities and delete; if this title now has no rows in
    #     nominees_entities, then delete it; (2) create new entries in
    #     nominees_entities and entities
    #   - if name, statement index, or role have changed update
    #     nominees_entities and entities
    # if there are more scraped nominees than db nominees, suggest insertions
    # if there are less scraped nominees than db nominees, suggest deletions

    # after sorting matched_categories, matched_categories and
    # db_matched_categories should be in same order such that ith elm represents
    # same category

    # within each category, match nominees: calculate similarity for titles and
    # nomination statements (people) separately (for characters/songs/dance
    # numbers, add detail to title), then add scores to find best match

    for i in range(len(matched_categories)):
        matched_nominees = matched_categories[i].nominees
        db_matched_nominees = db_matched_categories[i].nominees

        # need to handle cases where matched_nominees and db_matched_nominees
        # have different lengths
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
            # number of rows is always <= number of cols
            # rows always corresponds to shorter of matched_nominees or db_matched_nominees
            matrix = matrix.T

        # res[i] is col ind of highest score in row i
        res = matrix.argmax(axis=1)

        # before using process.cdist, swap such that first array is smaller than
        # second if different lengths; then take argmax along axis=1; there
        # should be len(b)-len(a) remaining unmatched elements in b, which
        # should then be inserted or deleted; if there are more unmatched
        # elements, it means multiple elements in a had best match to same
        # element in b, which is a problem;

        # if the two arrays match one-to-one except for len(b)-len(a) unmatched
        # elements, then fuzzy match films and people, then determine what to
        # insert/delete; otherwise, throw error

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

        # fuzzy match films and people, consider what happens if number of films
        # or number of people differ between matched and db; same process as
        # above for nominees... actually, do we need to even fuzzy match films
        # and people? can we just exact match each, then determine what to
        # insert/delete based on difference??? well, if the tuples do differ, we
        # won't know which to insert/delete unless they are fuzzy matched,
        # either manually by human or by program... probably better to just
        # prompt user to do matches if there's a difference; in both
        # matched_nominees and db_matched_nominees, within each nominee sort
        # films by title, and sort people by name, then pray that they match
        # exactly and if they don't, then prompt the user

        for shorter_ind, longer_ind in enumerate(res):
            if len(matched_nominees) <= len(db_matched_nominees):
                matched_nominees_equal(
                    matched_nominees[shorter_ind], db_matched_nominees[longer_ind]
                )
            else:
                matched_nominees_equal(
                    matched_nominees[longer_ind], db_matched_nominees[shorter_ind]
                )

    # bulk update pending=FALSE for all nominees
    db.update_pending(edition)


def matched_nominees_equal(
    n1: MatchedNominee, n2: MatchedNominee, ignored_properties: list[str] = []
) -> bool:
    # check if n1 and n2 are exactly equal; if films or people are unequal,
    # prompt for user input; for any other properties, suggest appropriate
    # updates
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
        # match, then prompt to insert/delete/update
        if "films" in unequal_properties:
            update_films_or_people("films", n1.films, n2.films, n2.id)

        if "people" in unequal_properties:
            update_films_or_people("people", n1.people, n2.people, n2.id)

        return False

    return True


NomineeItem = Literal["films", "people"]


def update_films_or_people(
    item: NomineeItem, n1_items: list, n2_items: list, nominee_id: int
):
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

            # prompt each pair of matched_inds for update with n1 or
            # stay with n2; if imdb id differs, upsert new entry and
            # delete old one
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

                        # if imdb id differs, delete old one
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
    if item == "films":
        db.delete_nominee_title(nominee_id=nominee_id, imdb_id=imdb_id)
    else:
        db.delete_nominee_entity(nominee_id=nominee_id, imdb_id=imdb_id)


if __name__ == "__main__":
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
