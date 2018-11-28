from multiprocessing import Pool

from blueagent.scrapers import *
from blueagent.logger import logger

categories = [
    "https://www.dba.dk/billede-og-lyd/hi-fi-surround-og-tilbehoer/surroundsystemer/",
    "https://www.dba.dk/billede-og-lyd/dvd-afspillere-videomaskiner-projektorer-og-tilbehoer/dvd-og-harddiskoptagere/",
    "https://www.dba.dk/billede-og-lyd/analoge-kameraer/minolta/",
    "https://www.dba.dk/boliger/lejebolig/bofaellesskaber/"
]


def sync():
    logger.info("Synchronizing with DBA")

    logger.info("Loading {} categories".format(len(categories)))

    logger.info("Checking first page of all categories")

    # Check first page once
    for cat in categories:
        run_category_once(cat)

    logger.info("Checking all pages of all categories")

    # And then do a deep check
    for cat in categories:
        run_category(cat)

    logger.info("Blue Agent has finished sync with DBA")


def run_category_once(page):
    logger.info("Fetching category page: {}".format(page))
    category_page = CategoryPage(page)
    category_page.fetch()
    listings = category_page.listings()

    # Parallel scraping
    pool = Pool(5)
    items = pool.map(process_item, listings)
    pool.terminate()
    pool.join()


def run_category(base_url):
    category = CategoryPage(base_url)
    category.fetch()
    pages = category.all_pages()

    for page in pages:
        run_category_once(page)


# Utility functions
def process_item(url):
    item = ItemPage(url)

    if not item.exists():
        item.fetch()
        item.parse()
        item.save_to_database()
