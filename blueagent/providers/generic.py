class DbaPage:
    def __init__(self, url):
        self.url = url
        self.parsed = None

    def fetch(self):
        pass


class CategoryPage(DbaPage):
    def next_page(self):
        pass

    def all_pages(self):
        pass

    def listings(self):
        pass


class ItemPage(DbaPage):
    def __init__(self, url):
        super().__init__(url)
        self.item = None

    @db_session
    def exists(self):
        pass

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

        pass

    def evaluate_filter(self, filter_name, filter_args):
        return filters[filter_name](self.item, filter_args)

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
