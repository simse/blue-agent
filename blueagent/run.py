from multiprocessing import Pool

from rq import Queue

from worker import conn
from blueagent.scrapers import *
from blueagent.logger import logger
from blueagent.event import new_item_event

# Connect to worker
q = Queue(connection=conn)

categories = [
    "https://www.dba.dk/billede-og-lyd/hi-fi-og-tilbehoer/",
    "https://www.dba.dk/billede-og-lyd/hi-fi-surround-og-tilbehoer/"
]


def sync():
    logger.info("Synchronizing with DBA")

    logger.info("Loading {} categories".format(len(categories)))

    logger.info("Checking all pages of all categories")

    # Check everything on DBA
    for cat in categories:
        run_category(cat)

    for item in Item.select():
        verify_item(item.dba_url)

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
    pool = Pool(10)
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
        item.save_to_database()

        logger.info("[NEW_ITEM] Loaded item: {}".format(url))
        new_item_event(item.item)


# Verify existence and remove from records if not
@db_session
def verify_item(url):
    item = ItemPage(url)

    try:
        item.fetch()
    except IndexError:
        logger.info("[REMOVE_ITEM] Removed item as it's no longer on DBA: {}".format(url))

        Item.get(dba_url=url).delete()
