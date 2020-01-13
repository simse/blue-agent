from multiprocessing import Pool
from datetime import datetime, timedelta

from blueagent.logger import logger
from blueagent.event import *



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

