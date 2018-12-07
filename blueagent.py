# Python dependencies
import time

# Third-party dependencies

# Blue Agent
from blueagent.threads import *
from blueagent.logger import *


def run():
    logger.info("[BLUE-AGENT] Starting main loop. Welcome.")

    web = WebThread()
    blueagent = BlueAgentThread()
    web.start()
    blueagent.start()


run()
