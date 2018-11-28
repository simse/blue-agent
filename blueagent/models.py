import os
from datetime import datetime
from urllib.parse import urlparse
from pony.orm import *

db = Database()

if os.environ['HEROKU'] == 'NO':
    db.bind(provider='postgres', host=os.environ['DATABASE_URL'], user="ba",
            database="blueagent", password="hotfla123As")

else:
    # Parse that dumb string
    db_url = urlparse(os.environ['DATABASE_URL'])

    db.bind(provider='postgres', host=db_url.hostname, user=db_url.username,  database=db_url.path[1:],
            password=db_url.password, sslmode='require')


class Item(db.Entity):
    id = PrimaryKey(int, auto=True)
    dba_id = Required(int)
    dba_url = Required(str)
    title = Required(str)
    description = Required(str)
    price = Required(int)
    images = Required(Json)
    item_data = Required(Json)
    seller = Required(Json)
    date_added = Required(datetime)


db.generate_mapping(create_tables=True)
