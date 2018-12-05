# Python dependencies
import time

# Third-party dependencies

# Blue Agent
from blueagent.run import *
from blueagent.logger import *

if __name__ == '__main__':
    logger.info("[BLUE-AGENT] Starting main loop. Welcome.")

    cycle = 0

    while True:
        # Run certain tasks
        if cycle is 0:
            logger.info("[BLUE-AGENT] Running full sync.")
            sync()

        if cycle % 10 is 0:
            logger.info("[BLUE-AGENT] Performing quick sync.")
            quick_sync()
            welcome_users()

        if cycle % 60 is 0:
            logger.info("[BLUE-AGENT] Cleaning database.")
            clean_items()

        cycle += 1

        # Reset cycle counter
        if cycle > 600:
            cycle = 0

        time.sleep(1)
