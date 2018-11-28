import os
import datetime

from slackclient import SlackClient

from blueagent.logger import logger


def new_item_event(item):
    # logger.info("New item, processing....")
    sc = SlackClient(os.environ['SLACK_API_KEY'])

    # Temp send to Slack
    sc.api_call(
        "chat.postMessage",
        channel="CEEC4PCSW",
        text="[{}] New item: {}".format(datetime.datetime, item.dba_url)
    )

