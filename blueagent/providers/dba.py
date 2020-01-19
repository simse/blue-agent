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


class Dba:
    def __init__(self):
        self.categories = [
            "https://www.dba.dk/billede-og-lyd/hi-fi-surround-og-tilbehoer/",
            "https://www.dba.dk/billede-og-lyd/hi-fi-og-tilbehoer/",
            "https://www.dba.dk/musikinstrumenter/forstaerkere-pedaler-anlaeg-mm/"
        ]

    def sync(self):
        logger.info("[DBA] Performing full sync")
        logger.info("[DBA] Scraping {} categories".format(len(self.categories)))

        # Check everything on DBA
        for cat in self.categories:
            self.category_page_full(cat)

        logger.info("[DBA] Full sync completed")

    def quick_sync(self):
        logger.info("[DBA] Performing quick sync")
        logger.info("[DBA] Scraping {} categories".format(len(self.categories)))

        for cat in self.categories:
            self.category_page(cat)

        logger.info("[DBA] Quick sync completed")

    def investigate(self):
        """ Add item history if updates are detected """
        pass
    
    @db_session
    def process_item(self, url):
        item = ItemPage(url)

        if not item.exists():
            try:
                item.fetch()
            except IndexError:
                return False

            item.parse()

            if item.save_to_database():
                commit()
                logger.info("[DBA] Loaded item: {}".format(url))
                new_item_event(Item.get(url=item.url))

    def category_page(self, page):
        logger.info("[DBA] Fetching category page: {}".format(page))
        category_page = CategoryPage(page)
        category_page.fetch()
        listings = category_page.listings()

        # Parallel scraping
        pool = Pool(5)
        pool.map(self.process_item, listings)
        pool.terminate()
        pool.join()

    def category_page_full(self, base_url):
        category = CategoryPage(base_url)
        category.fetch()
        pages = category.all_pages()

        for page in pages:
            self.category_page(page)


class DbaPage:
    def __init__(self, url):
        self.url = url
        self.parsed = None


    def fetch(self):
        headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
            'cache-control': 'max-age=0'
        }

        page = requests.get(self.url + '?fra=privat', headers=headers)

        # Detect redirect
        if len(page.history) > 0:
            raise IndexError("This page does not exist: {}".format(self.url))

        parsed_page = BeautifulSoup(page.content, 'lxml')

        self.parsed = parsed_page


class CategoryPage(DbaPage):
    def next_page(self):
        regex = re.compile('\d{1,4}')
        search = regex.search(self.url)

        if search is None:
            return self.url + 'side-2/'

        else:
            return regex.sub(str(int(search.group()) + 1), self.url)

    def all_pages(self):
        numbers = self.parsed.select('.pagination ul li')
        max_page = 1
        all_pages = []
        base_url = self.url

        if re.search('side-\d{1,4}\/', base_url):
            base_url = base_url.replace(re.search('side-\d{1,4}\/', base_url).group(), '')

        for num in numbers:
            if str.strip(num.text) not in ['1', '2', '3', '...', 'Forrige', 'Næste']:
                max_page = int(str.strip(num.text))

        # Limit max page to 5
        if max_page > 5:
            max_page = 5

        for page in range(0, max_page):
            if page is 0:
                all_pages.append(base_url)
            else:
                all_pages.append(base_url + 'side-{}/'.format(page + 1))

        return all_pages

    def listings(self):
        listings = self.parsed.find_all(class_='dbaListing')
        filtered_listings = []

        for listing in listings:
            date = listing.find_all(class_='simple')[0].text.strip()

            if date in ["I dag", "I går"]:
                filtered_listings.append(listing.find(class_='listingLink').get('href'))

        return filtered_listings


class ItemPage(DbaPage):
    def __init__(self, url):
        super().__init__(url)

        self.item = None

    @db_session
    def exists(self):
        return Item.get(url=self.url) is not None

    def parse(self):
        item = SimpleNamespace(**{
            "dba_id": None,
            "dba_url": self.url,
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

        # Parse basic data
        item.title = self.parsed.find('h1').string
        item.description = self.parsed.find(class_='vip-additional-text').text
        item.dba_id = re.search('\d{10}', self.url).group()
        item.price = int(self.parsed.find(class_='price-tag').text.replace(' kr.', '').replace('.', ''))

        # Find seller information
        item.seller.name = self.parsed.select('.ProfileTitle_profile-title__2rvIX')[0].text

        street = self.parsed.select('.ProfileAddress_profile-address__3WZfH')
        if street:
            item.seller.street = street[0].text
        #item.seller.postal_code = re.search('\d{4}', self.parsed.select('.profile-information .postal-code')[0].text).group()

        # Specific item data
        table_contents = self.parsed.select('.vip-matrix-data table tbody tr')
        item_data = []

        for line in table_contents:

            i = 0

            for data in line.find_all('td'):

                if i in [0, 3] and data.text:
                    try:
                        item_data.append({data.text: data.find_next_sibling().text})
                    except AttributeError:
                        pass

                i = i + 1

        item.item_data = item_data

        # Find images
        image_gallery = self.parsed.select('.vip-picture-gallery a')
        images = []
        for image in image_gallery:
            attrs = image.attrs

            if 'primary' not in attrs['class'] and 'picture-browser-link' not in attrs['class']:
                images.append(attrs['data-src-large'])

        item.images = images

        # Save to class
        self.item = item

        # Return to dict
        item.seller = vars(item.seller)
        item = vars(item)

        return item

    def save_to_database(self):
        return Item(
            provider="DBA",
            provider_id=self.item.dba_id,
            url=self.item.dba_url,
            title=self.item.title,
            description=self.item.description,
            price=self.item.price,
            images=self.item.images,
            item_data=self.item.item_data,
            seller=self.item.seller,
            date_added=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
