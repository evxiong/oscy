"""
Functions for scraping data from IMDb and official source.
"""

import json
import os
import re
import time
from datetime import datetime

import minify_html
import requests
from dotenv import load_dotenv
from lxml import html
from playwright.sync_api import sync_playwright
from seleniumbase import SB
from tqdm import tqdm

from .data import Edition, OfficialCategory, OfficialNominee

load_dotenv(override=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) Gecko/20100101 Firefox/148.0"
}


def scrape_imdb(edition: int, save: bool = True, force: bool = False) -> dict:
    """Scrapes Oscar ceremony data from IMDb.

    If data already exists at `data/oscars/imdb/<edition>.json`, reads from file
    instead of scraping, unless `force` is True.

    Args:
        edition (int): edition of Oscar ceremony
        save (bool, optional): if True, save results to
            `data/oscars/imdb/<edition>.json`. Defaults to True.
        force (bool, optional): if True, scrape even if data already saved in
            file. Defaults to False.

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

    file_path = os.path.join("data", "oscars", "imdb", str(edition) + ".json")
    if not force and os.path.isfile(file_path):
        with open(file_path, mode="r", encoding="utf-8") as fd:
            data = fd.read()

    else:
        year, instance = edition_to_year(edition)

        with SB(uc=True, ad_block=True, incognito=True) as sb:
            sb.activate_cdp_mode(
                f"https://www.imdb.com/event/ev0000003/{year}/{instance}"
            )
            sb.wait_for_any_of_elements_present("script#__NEXT_DATA__", "div.article")
            doc = html.fromstring(sb.get_page_source())

            classic_div = doc.xpath("//div[@class='article']")
            if classic_div:  # classic version of html (nomineesWidgetModel)
                d = classic_div[0].text_content()
                data = re.search(r"'center-3-react',(.*)]\);", d).group(1)  # type: ignore - html should always have div with this class
            else:  # new version of html (props)
                data = doc.xpath("//script[@id='__NEXT_DATA__']")[0].text

            if save:
                os.makedirs("data/oscars/imdb", exist_ok=True)
                with open(file_path, mode="w", encoding="utf-8") as fd:
                    fd.write(data)

    return json.loads(data)


def save_imdb(
    start: int = 1,
    end: int = int(os.getenv("CURRENT_EDITION")),  # type: ignore
    sleep: int = 1,
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


def scrape_official_database(start: int | None = None, end: int | None = None) -> None:
    """Scrapes multiple Oscar ceremonies' data from official database.

    Each ceremony's data is saved to `data/oscars/official/<edition>.html`. If
    data already exists, compares data and warns on difference.

    Args:
        start (int | None, optional): edition of first Oscar ceremony to
            include. If None, starts from 1st edition. Defaults to None.
        end (int | None, optional): edition of last Oscar ceremony to include.
            If None, ends at `start` if specified; otherwise, ends at
            `CURRENT_EDITION` specified in top-level `.env`. Defaults to None.
    """
    if start is None:
        start = 1
        if end is None:
            end = int(os.getenv("CURRENT_EDITION"))  # type: ignore
    else:
        if end is None:
            end = start

    if start < 1 or end < start:
        raise ValueError

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://awardsdatabase.oscars.org")
        page.locator("#BasicSearchView_AwardShowNumberFrom").select_option(
            value=str(start), force=True, timeout=5000
        )
        page.locator("#BasicSearchView_AwardShowNumberTo").select_option(
            value=str(end), force=True, timeout=5000
        )
        page.locator("#btnbasicsearch").click()
        page.locator(
            f"//div[@class='result-group-title']/a[@href='/Search/Nominations?awardShowFrom={end}&view=3-Award%20Category-Chron']"
        ).wait_for()

        content = page.content()
        doc = html.fromstring(content, parser=html.HTMLParser(remove_blank_text=True))

        for edition in range(start, end + 1):
            # HTML fragment containing this edition's nominations
            ceremony_div = doc.xpath(
                f"//div[@class='result-group-title']/a[@href='/Search/Nominations?awardShowFrom={edition}&view=3-Award%20Category-Chron']/../../.."
            )[0]

            file_path = os.path.join(
                "data", "oscars", "official", str(edition) + ".html"
            )

            os.makedirs("data/oscars/official", exist_ok=True)

            new_html = minify_html.minify(
                html.tostring(
                    ceremony_div,  # type: ignore
                    encoding="unicode",
                    pretty_print=True,
                )
            )

            if os.path.isfile(file_path):
                # if this edition already saved, compare fragments and warn on
                # difference; do not overwrite
                with open(file_path, mode="r", encoding="utf-8") as fd:
                    saved_html = fd.read()
                if saved_html != new_html:
                    print(
                        f"WARNING: data/oscars/official/{edition}.html does not match current webpage. The current file will not be overwritten."
                    )
            else:
                with open(file_path, mode="w", encoding="utf-8") as fd:
                    fd.write(new_html)

        browser.close()


def scrape_official_ceremony_page(edition: int) -> list[OfficialCategory]:
    # should be used for pending nominations and unofficial results ONLY
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
