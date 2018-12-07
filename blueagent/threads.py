import threading
import time
from flask import Flask, jsonify
from blueagent.run import *
from blueagent.logger import logger

# HTTP server
app = Flask(__name__)


class WebThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self, name='WebThread')

    def run(self):
        app.run(host='0.0.0.0', port=80)


@app.route('/')
def index():
    return 'Hello world!'


# Blue Agent
class BlueAgentThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self, name='BlueAgentThread')

    def run(self):
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
