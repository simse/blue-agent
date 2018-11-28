from multiprocessing import Pool
from datetime import datetime, timedelta

from rq import Queue

from worker import conn
from blueagent.scrapers import *
from blueagent.logger import logger
from blueagent.event import new_item_event

# Connect to worker
q = Queue(connection=conn)

categories = [
    "https://www.dba.dk/billede-og-lyd/hi-fi-og-tilbehoer/baandoptagere/",
    # "https://www.dba.dk/billede-og-lyd/hi-fi-og-tilbehoer/cd-afspillere/",
    # "https://www.dba.dk/billede-og-lyd/hi-fi-og-tilbehoer/forstaerkere-hi-fi/",
    # "https://www.dba.dk/billede-og-lyd/hi-fi-og-tilbehoer/hovedtelefoner/",
    # "https://www.dba.dk/billede-og-lyd/hi-fi-og-tilbehoer/hoejttalere-hi-fi/",
    # "https://www.dba.dk/billede-og-lyd/hi-fi-og-tilbehoer/pladespillere/",
    # "https://www.dba.dk/billede-og-lyd/hi-fi-og-tilbehoer/stereoanlaeg/"
]


def sync(verify=False):
    logger.info("Synchronizing with DBA")

    logger.info("Loading {} categories".format(len(categories)))

    logger.info("Checking all pages of all categories")

    # Check everything on DBA
    for cat in categories:
        run_category(cat)

    clean_items()

    logger.info("Blue Agent has finished sync with DBA")


def quick_sync():
    logger.info("Performing quick sync with DBA")

    logger.info("Loading {} categories".format(len(categories)))

    for cat in categories:
        q.enqueue(run_category_once, cat)

    logger.info("Quick sync completed")


def run_category_once(page):
    logger.info("[CATEGORY] Fetching category page: {}".format(page))
    category_page = CategoryPage(page)
    category_page.fetch()
    listings = category_page.listings()

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
            new_item_event(item.item)


@db_session
def clean_items():
    select(i for i in Item if i.date_added + timedelta(days=3) >= datetime.now()).delete()
