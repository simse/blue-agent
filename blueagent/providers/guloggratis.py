import re
from datetime import datetime
from multiprocessing import Pool
from types import SimpleNamespace

import requests
from bs4 import BeautifulSoup

from blueagent.filters import evaluate_filter
from blueagent.event import new_item_event
from blueagent.logger import logger
from blueagent.models import *


class GulOgGratis:
    def __init__(self):
        self.categories = [
            "https://www.guloggratis.dk/elektronik?order=desc&sort=created&type=1&usertype=1"
        ]

    def sync(self):
        logger.info("[GUL&GRATIS] Performing full sync")
        logger.info("[GUL&GRATIS] Scraping {} categories".format(len(self.categories)))

        # Perform a thorough sync
        for cat in self.categories:
            for x in range(1,5):
                self.load_category(cat, page=x)

        logger.info("[GUL&GRATIS] Full sync completed")

    def quick_sync(self):
        logger.info("[GUL&GRATIS] Performing quick sync")
        logger.info("[GUL&GRATIS] Scraping {} categories".format(len(self.categories)))

        for cat in self.categories:
            self.load_category(cat)

        logger.info("[GUL&GRATIS] Quick sync completed")

    def investigate(self):
        """ Add item history if updates are detected """
        pass

    def load_category(self, url, page=1):
        pool = Pool(5)
        pool.map(self.process_item, GGCategory(url, page).listings())
        pool.terminate()
        pool.join()

    @db_session
    def process_item(self, url):
        item = GGItem(url)

        if not item.exists():
            try:
                item.fetch()
            except IndexError:
                return False

            item.parse()

            if item.save_to_database():
                commit()
                logger.info("[GUL&GRATIS] Loaded item: {}".format(url))
                new_item_event(Item.get(url=item.url))


class GGCategory:
    def __init__(self, url, page=1):
        self.url = url
        self.page = page - 1
        self.parsed = None
        self.source = None

        self.fetch()


    def fetch(self):
        headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        }
        url = self.url + "&n={}".format(str(self.page * 60))
        logger.info("[GUL&GRATIS] Fetching category page: " + url)
        self.source = requests.get(url, headers=headers).content # On GG, page number is defined by listing offset e.g. 60, 120, 180...
        self.parsed = BeautifulSoup(self.source, 'lxml')


    def listings(self):
        links = []

        for a in self.parsed.find_all('a', class_='e1oturvy0'):
            links.append('https://www.guloggratis.dk' + a['href'])

        return links


class GGItem:
    def __init__(self, url):
        self.url = url
        self.parsed = None
        self.source = None
        self.item = None
        self.fetch()


    def fetch(self):
        headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        }
        self.source = requests.get(self.url, headers=headers).content
        self.parsed = BeautifulSoup(self.source, 'lxml')


    @db_session
    def exists(self):
        return Item.get(url=self.url) is not None


    def parse(self):
        item = SimpleNamespace(**{
            "id": None,
            "url": self.url,
            "title": None,
            "description": None,
            "price": None,
            "item_data": None,
            "images": None,
            "seller": SimpleNamespace(**{
                "name": None,
                "street": None,
                "postal_code": None,
                "phone_url": None
            })
        })

        # Determine ID from URL
        item.id = item.url.split('/')[-1].split('-')[0]

        # exit(self.source)

        # Determine listing title from source
        item.title = self.parsed.select_one('.top h1').text

        # Determine description
        item.description = self.parsed.select_one('div.seller_info_description').text

        try:
            # Determine price
            item.price = int(self.parsed.select_one('.price').text.replace('Kr. ', '').replace(',-', '').replace('.', ''))
        except ValueError:
            item.price = 0

        # TODO: Parse table
        item.item_data = []

        # TODO: Find a picture
        item.images = []

        try:
            # Determine seller name
            item.seller.name = self.parsed.select_one('.seller_details .title').text

            # Determine seller postal code
            item.seller.street = self.parsed.select_one('.address').text

            # Determine seller phone URL
            item.seller.phone_url = 'https://www.guloggratis.dk/modules/gulgratis/ajax/ad_showphone_click.php?adid=' + item.id

            # Convert seller to dict
            item.seller = vars(item.seller)
        except(AttributeError):
            item.seller = {}

        self.item = item

    
    def save_to_database(self):
        return Item(
            provider="GULOGGRATIS",
            provider_id=self.item.id,
            url=self.item.url,
            title=self.item.title,
            description=self.item.description,
            price=self.item.price,
            images=self.item.images,
            item_data=self.item.item_data,
            seller=self.item.seller,
            date_added=datetime.now().strftime("%Y-%m-%d %H:%M")
        )