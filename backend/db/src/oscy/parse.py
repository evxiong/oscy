"""
Functions for parsing IMDb and official data.
"""

from .data import OfficialCategory, OfficialNominee, IMDbCategory, IMDbNominee
from lxml import html


def parse_official(
    edition: int, file_path: str = "data/oscars.html"
) -> list[OfficialCategory]:
    """Gets edition's categories from official Oscars database HTML file.

    Before running this function, go to https://awardsdatabase.oscars.org/,
    select all award years, and save HTML page to data/oscars.html.

    Args:
        edition (int): edition of Oscar ceremony
        file_path (str, optional): location of official Oscars database HTML
            file. Defaults to "data/oscars.html".

    Raises:
        ValueError: invalid edition passed

    Returns:
        list[OfficialCategory]: list of category info from given edition
    """
    if edition < 1:
        raise ValueError("Edition must be >= 1")

    official_categories: list[OfficialCategory] = []
    excluded_category_ids = set(
        [
            99,  # humanitarian
            100,  # special
            101,  # honorary
            102,  # gordon e. sawyer
            103,  # sci-tech class i
            104,  # sci-tech class ii
            105,  # sci-tech class iii
            106,  # sci-tech award of merit
            107,  # award of merit
            108,  # sci-tech sci-eng
            109,  # sci-eng
            110,  # sci-tech tech achievement
            111,  # technical achievement
            112,  # award of commendation
            113,  # john a. bonner
            114,  # special achievement award
            119,  # irving g. thalberg
            121,  # medal of commendation
            125,  # sci-tech special
        ]
    )

    with open(file_path, mode="r", encoding="utf-8") as fd:
        content = fd.read()

    doc = html.fromstring(content)

    def xpath_to_text(elm, xp):
        e = elm.xpath(xp)
        return e[0].text_content() if e else ""

    def xpath_to_list(elm, xp, mapper=lambda x: x):
        e = elm.xpath(xp)
        return [mapper(x.text_content()) for x in e]

    for ceremony_div in doc.xpath(
        f"//div[contains(@class, 'awards-result-chron')][{edition}]"
    ):
        for category_div in ceremony_div.xpath(
            "./div[contains(@class, 'subgroup-awardcategory-chron')]"
        ):
            category_a = category_div.xpath(".//div[@class='result-subgroup-title']/a")[
                0
            ]
            link = category_a.get("href")
            cat_id = int(link[36 : link.index("&")])
            if cat_id not in excluded_category_ids:
                category_name = category_a.text
                nominees: list[OfficialNominee] = []

                for nominee_div in category_div.xpath(
                    ".//div[contains(@class, 'result-details')]"
                ):
                    winner = True if nominee_div.xpath("./span") else False
                    films = xpath_to_list(
                        nominee_div,
                        ".//div[@class='awards-result-film-title']",
                        lambda x: x[:-1] if x[-1] == ";" else x,
                    )
                    nomination_statement = xpath_to_text(
                        nominee_div,
                        ".//div[@class='awards-result-nominationstatement']",
                    )
                    characters = xpath_to_list(
                        nominee_div,
                        ".//div[@class='awards-result-character-name']",
                        lambda x: x[2:-3] if x[-1] == ";" else x[2:-2],
                    )
                    citation = xpath_to_text(
                        nominee_div, ".//div[@class='awards-result-citation']"
                    )
                    # description = xpath_to_text(
                    #     nominee_div, ".//div[@class='awards-result-description']"
                    # )
                    note = xpath_to_text(
                        nominee_div, ".//div[@class='awards-result-publicnote']"
                    )
                    songs = xpath_to_list(
                        nominee_div,
                        ".//div[@class='awards-result-songtitle']",
                        lambda x: x[1:-1],
                    )
                    dance_numbers = xpath_to_list(
                        nominee_div,
                        ".//div[@class='awards-result-dancenumber']",
                        lambda x: x[1:-1],
                    )

                    if nomination_statement == "" and citation == "":
                        print(
                            "WARNING: no nomination statement (potentially bad HTML):",
                            edition,
                            category_name,
                            nominee_div.text_content(),
                        )

                    nominees.append(
                        OfficialNominee(
                            winner=winner,
                            films=films,
                            nomination=nomination_statement or citation,
                            detail=characters or songs or dance_numbers,
                            note=note,
                        )
                    )

                official_categories.append(
                    OfficialCategory(category=category_name, nominees=nominees)
                )

    if not official_categories:
        raise ValueError("Invalid edition passed to parse_oscars")

    return official_categories


def parse_imdb(data: dict) -> list[IMDbCategory]:
    """Gets categories from data returned by scrape.scrape_imdb().

    Args:
        data (dict): dict of IMDb data returned by scrape.scrape_imdb()

    Raises:
        ValueError: invalid data passed

    Returns:
        list[IMDbCategory]: list of category info from data
    """
    imdb_categories: list[IMDbCategory] = []

    if "nomineesWidgetModel" in data:  # classic version of data
        for award in data["nomineesWidgetModel"]["eventEditionSummary"]["awards"]:
            if award["awardName"] == "Oscar":
                for category in award["categories"]:
                    nominees: list[IMDbNominee] = []
                    for nominee in category["nominations"]:
                        winner = nominee["isWinner"]
                        titles = []
                        names = []
                        for primary in nominee["primaryNominees"]:
                            titles.append((primary["name"], primary["const"]))
                        for secondary in nominee["secondaryNominees"]:
                            names.append((secondary["name"], secondary["const"]))
                        if not titles[0][1].startswith("tt"):
                            titles, names = names, titles

                        if (
                            "International" in category["categoryName"]
                            or "Foreign" in category["categoryName"]
                        ):
                            names.append((nominee["notes"], ""))

                        nominees.append(
                            IMDbNominee(
                                winner=winner,
                                films=titles,
                                people=names,
                                detail=nominee["notes"] or "",
                            )
                        )

                    imdb_categories.append(
                        IMDbCategory(
                            category=category["categoryName"], nominees=nominees
                        )
                    )

    elif "props" in data:  # new version of data
        for award_type in data["props"]["pageProps"]["edition"]["awards"]:
            # award_type can be oscar, honorary, humanitarian, technical achievement, etc.
            if award_type["text"] == "Oscar":
                for category in award_type["nominationCategories"]["edges"]:
                    category_name = (
                        category["node"]["category"]["text"]
                        if category["node"]["category"]
                        else ""
                    )
                    nominees: list[IMDbNominee] = []
                    for nominee in category["node"]["nominations"]["edges"]:
                        winner = nominee["node"]["isWinner"]
                        titles = []
                        names = []

                        if (
                            nominee["node"]["awardedEntities"]["__typename"]
                            == "AwardedTitles"
                        ):
                            for title in nominee["node"]["awardedEntities"][
                                "awardTitles"
                            ]:
                                titles.append(
                                    (
                                        title["title"]["titleText"]["text"],
                                        title["title"]["id"],
                                    )
                                )

                            if nominee["node"]["awardedEntities"][
                                "secondaryAwardNames"
                            ]:
                                for name in nominee["node"]["awardedEntities"][
                                    "secondaryAwardNames"
                                ]:
                                    names.append(
                                        (
                                            name["name"]["nameText"]["text"],
                                            name["name"]["id"],
                                        )
                                    )

                            if nominee["node"]["awardedEntities"][
                                "secondaryAwardCompanies"
                            ]:
                                for company in nominee["node"]["awardedEntities"][
                                    "secondaryAwardCompanies"
                                ]:
                                    names.append(
                                        (
                                            company["company"]["companyText"]["text"],
                                            company["company"]["id"],
                                        )
                                    )

                        elif (
                            nominee["node"]["awardedEntities"]["__typename"]
                            == "AwardedNames"
                        ):
                            if nominee["node"]["awardedEntities"][
                                "secondaryAwardTitles"
                            ]:
                                for title in nominee["node"]["awardedEntities"][
                                    "secondaryAwardTitles"
                                ]:
                                    titles.append(
                                        (
                                            title["title"]["titleText"]["text"],
                                            title["title"]["id"],
                                        )
                                    )

                            for name in nominee["node"]["awardedEntities"][
                                "awardNames"
                            ]:
                                names.append(
                                    (
                                        name["name"]["nameText"]["text"],
                                        name["name"]["id"],
                                    )
                                )

                        if (
                            "International" in category_name
                            or "Foreign" in category_name
                        ):
                            names.append((nominee["node"]["notes"]["plainText"], ""))

                        nominees.append(
                            IMDbNominee(
                                winner=winner,
                                films=titles,
                                people=names,
                                detail=(
                                    nominee["node"]["notes"]["plainText"]
                                    if nominee["node"]["notes"]
                                    else ""
                                ),
                            )
                        )

                    imdb_categories.append(
                        IMDbCategory(category=category_name, nominees=nominees)
                    )

    else:
        raise ValueError("Invalid data passed to parse_imdb")

    return imdb_categories
