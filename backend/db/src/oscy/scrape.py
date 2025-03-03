"""
Functions for scraping Oscar data from IMDb and official source.

`python -m src.oscy.scrape` saves all IMDb data into `data/imdb/...`
"""

import json
import os
import re
import requests
import time
from .data import OfficialCategory, OfficialNominee, Edition
from datetime import datetime
from dotenv import load_dotenv
from lxml import html
from tqdm import tqdm

load_dotenv(override=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0"
}


def scrape_imdb(edition: int, save: bool = True) -> dict:
    """Scrapes Oscar ceremony data from IMDb.

    If data already exists at `data/imdb/oscars/<edition>.json`, reads from file
    instead of scraping.

    Args:
        edition (int): edition of Oscar ceremony
        save (bool, optional): if True, save results to
            `data/imdb/oscars/<edition>.json`. Defaults to True.

    Raises:
        ValueError: invalid edition passed
        Exception: failed to scrape data

    Returns:
        dict: IMDb ceremony data
    """
    if edition <= 0:
        raise ValueError("Edition must be greater than 0.")

    def edition_to_year(e: int) -> tuple[int, int]:
        # returns year, instance
        if e == 3:
            return 1930, 2
        elif e == 4:
            return 1931, 1
        elif e == 5:
            return 1932, 1
        else:
            return 1928 + e, 1

    file_path = os.path.join("data", "imdb", "oscars", str(edition) + ".json")
    if os.path.isfile(file_path):
        with open(file_path, mode="r", encoding="utf-8") as fd:
            data = fd.read()

    else:
        year, instance = edition_to_year(edition)

        # Scrape imdb event data
        r = requests.get(
            "https://www.imdb.com/event/ev0000003/" + str(year) + "/" + str(instance),
            headers=HEADERS,
        )

        if r.status_code != 200:
            raise Exception("Failed to scrape data: status code", r.status_code)

        doc = html.fromstring(r.content)

        classic_div = doc.xpath("//div[@class='article']")
        if classic_div:  # classic version of html (nomineesWidgetModel)
            d = classic_div[0].text_content()
            data = re.search(r"'center-3-react',(.*)]\);", d).group(1)  # type: ignore - html should always have div with this class
        else:  # new version of html (props)
            data = doc.xpath("//script[@id='__NEXT_DATA__']")[0].text

        if save:
            os.makedirs("data/imdb/oscars", exist_ok=True)
            with open(file_path, mode="w", encoding="utf-8") as fd:
                fd.write(data)

    return json.loads(data)


def save_imdb(
    start: int = 1, end: int = int(os.getenv("CURRENT_EDITION")), sleep: int = 1  # type: ignore
) -> None:
    """Saves IMDb Oscar data for multiple ceremonies.

    Args:
        start (int, optional): first ceremony edition to include. Defaults to 1.
        end (int, optional): last ceremony edition to include. Defaults to
            `CURRENT_EDITION` specified in top-level `.env`.
        sleep (int, optional): time (s) between IMDb requests. Defaults to 1.
    """
    if start < 1 or end < start:
        raise ValueError

    for edition in tqdm(range(start, end + 1)):
        scrape_imdb(edition)
        time.sleep(sleep)


def scrape_official_page(edition: int) -> list[OfficialCategory]:
    # should be used for pending nominations ONLY
    r = requests.get(
        f"https://www.oscars.org/oscars/ceremonies/{1928 + edition}",
        headers=HEADERS,
    )
    doc = html.fromstring(r.text)
    categories: list[OfficialCategory] = []
    for category_div in doc.xpath(
        "//div[contains(@class,'field--name-field-award-categories')]/div[@class='field__item']"
    ):
        category_name = category_div.xpath(
            ".//div[contains(@class,'field--name-field-award-category-oscars')]"
        )[0].text

        nominees: list[OfficialNominee] = []
        for nominee_div in category_div.xpath(
            ".//div[contains(@class,'field--name-field-award-honorees')]/div[@class='field__item']"
        ):
            winner = (
                "winner"
                in nominee_div.xpath(
                    ".//div[contains(@class,'field--name-field-honoree-type')]"
                )[0].classes
            )

            title = nominee_div.xpath(
                ".//div[contains(@class,'field--name-field-award-film')]"
            )[0].text

            nomination = (
                nominee_div.xpath(
                    ".//div[contains(@class,'field--name-field-award-entities')]"
                )[0]
                .text_content()
                .strip()
            )

            if category_name.startswith("International" or "Foreign"):
                title, nomination = nomination, title

            if category_name == "Music (Original Song)":
                detail = [title]
                title = nomination.split("; ")[0][5:]
                nomination = nomination[nomination.find("; ") + 2 :]
            else:
                detail = []

            nominees.append(
                OfficialNominee(
                    winner=winner,
                    films=[title],
                    nomination=nomination,
                    detail=detail,
                    note="",
                )
            )

        categories.append(
            OfficialCategory(
                category=category_name,
                nominees=nominees,
            )
        )

    return categories


def scrape_editions(start: int | None = None, end: int | None = None) -> list[Edition]:
    if start is None:
        start = 1
        if end is None:
            end = int(os.getenv("CURRENT_EDITION"))  # type: ignore
    else:
        if end is None:
            end = start

    editions: list[Edition] = []

    for edition in range(start, end + 1):
        if edition < 7:
            year = str(1926 + edition) + "/" + str(1927 + edition)[2:]
        else:
            year = str(1927 + edition)

        r = requests.get(
            f"https://www.oscars.org/oscars/ceremonies/{1928 + edition}",
            headers=HEADERS,
        )
        if r.status_code != 200:
            raise Exception("Failed to scrape data: status code", r.status_code)

        doc = html.fromstring(r.content)
        date_string = doc.xpath("//div[@class='field--name-field-date-time']")[
            0
        ].text.strip()
        date_string = date_string[date_string.find(",") + 2 :]
        date = datetime.strptime(date_string, "%B %d, %Y").date()
        editions.append(
            Edition(
                award="oscar",
                iteration=edition,
                official_year=year,
                ceremony_date=date,
            )
        )

    return editions


if __name__ == "__main__":
    save_imdb()
