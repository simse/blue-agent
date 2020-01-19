import json
from multiprocessing import Pool
from datetime import datetime, timedelta

from blueagent.logger import logger
from blueagent.event import *
from blueagent.providers.dba import ItemPage
from blueagent.providers.guloggratis import GGItem



@db_session
def investigate():
    """items = Item.select().where(status='ACTIVE')
    logger.info("[WALSINGHAM] Running listing investigation on {} listings".format(len(items)))

    for item in items:
        result = compare_to_db(item)"""
    pass


@db_session
def compare_to_db(item):
    identical = True

    logger.info("[WALSINGHAM] Comparing database with listing: {}".format(item.url))
    online_item = None

    try:
        if item.provider == 'DBA':
            item_page = ItemPage(item.url)
            item_page.fetch()
            online_item = item_page.parse()
        elif item.provider == 'GULOGGRATIS':
            online_item = GGItem(item.url).parse()
    except(IndexError):
        logger.info("[WALSINGHAM] Deletion detected: {}".format(item.url))
        return (
            'DELETED',
            item
        )


    # Detect change
    if item.title != online_item['title']:
        identical = False

    if item.description != online_item['description']:
        identical = False

    if item.price != online_item['price']:
        identical = False

    if item.images != online_item['images']:
        identical = False

    if identical:
        logger.info("[WALSINGHAM] No change detected: {}".format(item.url))
    else:
        logger.info("[WALSINGHAM] Change detected: {}".format(item.url))

        ItemHistory(
            provider=item.provider,
            provider_id=item.provider_id,
            url=item.url,
            title=item.title,
            description=item.description,
            price=item.price,
            date_updated=datetime.now(),
            item=item
        )
        
        return (
            'UPDATED',
            online_item
        )


@db_session
def welcome_users():
    profiles = Profile.select(lambda p: not p.welcomed)

    for profile in profiles:
        new_user(profile)




@db_session
def clean_items():
    # items = select(
    #     i for i in Item if i.date_added + timedelta(days=3) <= datetime.now()
    # ).delete()
    pass

