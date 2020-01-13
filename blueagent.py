# Python dependencies
import time

# Third-party dependencies
from dotenv import load_dotenv
# Load enviroment variables
load_dotenv()

# Blue Agent
from blueagent.threads import *
from blueagent.logger import *


def run():
    logger.info("[WALSINGHAM] Starting Walsingham threads")

    web = WebThread()
    web.start()
    logger.info("[WALSINGHAM] Web thread started")

    blueagent = BlueAgentThread()
    blueagent.start()
    logger.info("[WALSINGHAM] Scraping and item matching thread started")

    notifications = NotificationThread()
    notifications.start()
    logger.info("[WALSINGHAM] Notification thread started")

run()
