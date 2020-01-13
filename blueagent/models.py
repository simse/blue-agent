import os
from datetime import datetime

from pony.orm import *

db = Database()

db.bind(provider='mysql', host='192.168.0.4', user="root",
        database=os.getenv("DATABASE_NAME"), password="EbYRQzWzTDdbkX2XW5hf")


class Item(db.Entity):
    id = PrimaryKey(int, auto=True)
    provider = Required(str)
    provider_id = Required(str)
    url = Required(str)
    title = Required(str)
    status = Required(str, default='ACTIVE') # ACTIVE, UPDATED, DELETED
    description = Required(str, max_len=5000)
    price = Required(int)
    images = Required(Json)
    item_data = Required(Json)
    seller = Required(Json)
    date_added = Required(datetime)
    hits = Set("Hit")
    history = Set("ItemHistory")


class ItemHistory(db.Entity):
    id = PrimaryKey(int, auto=True)
    provider = Required(str)
    provider_id = Required(str)
    url = Required(str)
    title = Required(str)
    description = Required(str, max_len=5000)
    price = Required(int)
    images = Required(Json)
    item_data = Required(Json)
    seller = Required(Json)
    date_updated = Required(datetime)
    item = Required(Item)


class Profile(db.Entity):
    id = PrimaryKey(int, auto=True)
    first_name = Required(str)
    email = Required(str)
    password = Required(str)
    messenger_id = Required(str)
    welcomed = Required(bool)
    monitors = Set("Monitor")
    session_keys = Set("Session")
    notifications = Set("Notification")


class Monitor(db.Entity):
    id = PrimaryKey(int, auto=True)
    user = Required(Profile)
    name = Required(str)
    filters = Required(Json)
    triggers = Set("Hit")


class Hit(db.Entity):
    id = PrimaryKey(int, auto=True)
    trigger = Required(Monitor)
    item = Required(Item)
    date_triggered = Required(datetime)


class Session(db.Entity):
    id = PrimaryKey(int, auto=True)
    user = Required(Profile)
    session_key = Required(str)
    expires = Required(datetime)


class Notification(db.Entity):
    id = PrimaryKey(int, auto=True)
    recipient = Required(Profile)
    body = Required(str, max_len=5000)


db.generate_mapping(create_tables=True)
