from multiprocessing import Pool
from datetime import datetime, timedelta

from blueagent.scrapers import *
from blueagent.logger import logger
from blueagent.event import event

categories = [
    "https://www.dba.dk/billede-og-lyd/hi-fi-surround-og-tilbehoer/",
    "https://www.dba.dk/billede-og-lyd/hi-fi-og-tilbehoer/",
    "https://www.dba.dk/musikinstrumenter/forstaerkere-pedaler-anlaeg-mm/"
]


def sync():
    logger.info("[WALSINGHAM] Performing full sync with DBA")
    logger.info("[WALSINGHAM] Scraping {} categories".format(len(categories)))

    # Check everything on DBA
    for cat in categories:
        run_category(cat)

    logger.info("[WALSINGHAM] Full sync completed")


def quick_sync():
    logger.info("[WALSINGHAM] Performing quick sync with DBA")

    logger.info("[WALSINGHAM] Scraping {} categories".format(len(categories)))

    for cat in categories:
        run_category_once(cat)

    logger.info("[WALSINGHAM] Quick sync completed")


@db_session
def welcome_users():
    profiles = Profile.select(lambda p: not p.welcomed)

    for profile in profiles:
        event.trigger('new_user', profile)


def run_category_once(page):
    logger.info("[CATEGORY] Fetching category page: {}".format(page))
    category_page = CategoryPage(page)
    category_page.fetch()
    listings = category_page.listings()

    #for listing in listings:
    #    process_item(listing)

    # Parallel scraping
    pool = Pool(5)
    pool.map(process_item, listings)
    pool.terminate()
    pool.join()


def run_category(base_url):
    category = CategoryPage(base_url)
    category.fetch()
    pages = category.all_pages()

    for page in pages:
        run_category_once(page)


# Utility functions
@db_session
def process_item(url):
    item = ItemPage(url)

    if not item.exists():
        try:
            item.fetch()
        except IndexError:
            return False

        item.parse()

        if item.save_to_database():
            commit()
            logger.info("[NEW_ITEM] Loaded item: {}".format(url))
            event.trigger('new_item_event', item)


@db_session
def clean_items():
    items = select(
        i for i in Item if i.date_added + timedelta(days=3) <= datetime.now()
    ).delete()

