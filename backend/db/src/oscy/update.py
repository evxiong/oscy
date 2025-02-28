from . import db, match, scrape


def insert_pending_nominations(edition: int):
    # assumes no new categories
    matched_categories = match.match_categories(
        edition,
        pending=True,
        official_parser=scrape.scrape_official_page,
    )

    # check for no new category names
    existing_category_names = set(db.get_category_names_official())
    for c in matched_categories[edition]:
        if c.category not in existing_category_names:
            raise Exception(f"New category name: {c.category}")

    # insert new edition
    db.insert_editions(edition)

    # insert to editions_category_names
    db.insert_editions_category_names(edition, matched_categories)

    # insert nominees
    db.insert_nominees(matched_categories)


def update_completed():
    # match official results with existing in database
    pass
