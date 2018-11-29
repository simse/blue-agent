import re
from types import SimpleNamespace
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from blueagent.models import *
from blueagent.logger import logger
from blueagent.filters import *


class DbaPage:

    def __init__(self, url):
        self.url = url
        self.parsed = None

    def fetch(self):
        headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        }

        proxies = {
            'https': 'socks5://194.182.80.21:3029'
        }

        page = requests.get(self.url + '?fra=privat', headers=headers, proxies=proxies)

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
        return Item.get(dba_url=self.url) is not None

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
        item.seller.name = self.parsed.select('.profile-information h2.fn a')[0].text

        street = self.parsed.select('.profile-information .street-address')
        if street:
            item.seller.street = street[0].text
        item.seller.postal_code = re.search('\d{4}', self.parsed.select('.profile-information .postal-code')[0].text).group()

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

    def filter(self, filter_name, filter_args):
        return filters[filter_name](self.item, filter_args)

    def save_to_database(self):
        return Item(
            dba_id=self.item.dba_id,
            dba_url=self.item.dba_url,
            title=self.item.title,
            description=self.item.description,
            price=self.item.price,
            images=self.item.images,
            item_data=self.item.item_data,
            seller=self.item.seller,
            date_added=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
