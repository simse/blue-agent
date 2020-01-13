import os
import datetime

from observable import Observable

from blueagent.logger import logger
from blueagent.models import *
from blueagent.filters import filters


def new_item_event(item):
    # Check all rules from profiles
    monitors = Monitor.select()

    # Iterate through all monitors
    for monitor in monitors:
        passed = False

        # Check all filters
        for f in monitor.filters:
            if item.evaluate_filter(f['filter'], f['args']):
                passed = True
            else:
                passed = False
                break

        if passed:
            item_match(monitor.user, item.item, monitor)


def new_user(profile):
    logger.info("[NEW USER] Sending notification...")

    body = 'Hej, {}!\nVelkommen til Walsingham. Jeg kan hjælpe dig med at finde interessante annoncer på DBA. \
Fra nu af modtager du en besked, når jeg finder noget til dig. \
For at tilføje overvågningsfiltre skal du logge ind på https://walsingham.app.'.format(profile.first_name)

    n = Notification(
        recipient=profile,
        body=body
    )

    profile.welcomed = True


def item_match(profile, item, monitor):
    logger.info("[ITEM MATCH] Notifying profile")

    body = 'Jeg har fundet en annonce til dig!\nTitel: {}\nPris: {}DKK\n{}'.format(item.title, item.price, item.dba_url)

    # Message
    n = Notification(
        recipient=profile,
        body=body
    )

    h = Hit(
        trigger=monitor,
        item=Item.get(url=item.dba_url),
        date_triggered=datetime.now()
    )