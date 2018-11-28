import os
from pony.orm import *

db = Database()

if os.environ['HEROKU']:
    db.bind(provider='postgres', host=os.environ['DATABASE_URL'], user="ba",
            database="blueagent", password="hotfla123As")

else:
    db.bind(provider='postgres', host=os.environ['DATABASE_URL'], sslmode='require')


class Item(db.Entity):
    id = PrimaryKey(int, auto=True)
    dba_id = Required(int)
    dba_url = Required(str)
    title = Required(str)
    description = Required(str)
    images = Required(Json)
    item_data = Required(Json)
    seller = Required(Json)


db.generate_mapping(create_tables=True)
