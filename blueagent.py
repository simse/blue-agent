# Python dependencies
import time

# Third-party dependencies

# Blue Agent
from rq import Queue
from worker import conn
from blueagent.run import *


if __name__ == '__main__':
    while True:
        sync()
