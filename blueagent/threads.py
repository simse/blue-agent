import threading
from datetime import datetime, timedelta
from functools import wraps
import binascii
import hashlib
import random
import string
import time
import json
import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from fbchat import Client
from fbchat.models import *

from blueagent.providers.dba import Dba
from blueagent.providers.guloggratis import GulOgGratis
from blueagent.logger import logger
from blueagent.models import *
from blueagent.run import welcome_users, investigate

# HTTP server
app = Flask(__name__)
CORS(app)



# Password hashing
def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), 
                                salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)

    return (salt + pwdhash).decode('ascii')

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', 
                                  provided_password.encode('utf-8'), 
                                  salt.encode('ascii'), 
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')

    return pwdhash == stored_password


# Authentication decorator
def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verify existence of session key
        if(request.args.get('session_key')):
            pass
        else:
            try:
                request.get_json()['session_key']
            except KeyError:
                return jsonify({"error":"NO_SESSION_KEY","error_msg":"You must supply a session key to access this route."})

        return f(*args, **kwargs)

    return decorated_function


class WebThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, name='WebThread')

    def run(self):
        app.run(host='0.0.0.0', port=os.getenv("WEB_PORT"))


@app.route('/')
def index():
    return 'Hello world!'


@app.route('/auth', methods=['POST'])
@db_session
def auth():
    email = ''
    password = ''

    # Verify existence of email
    try:
        email = request.get_json()['email']
    except(KeyError):
        return jsonify({"error":"NO_EMAIL","error_msg":"You must supply an email to authenticate."})

    # Verify existence of password
    try:
        password = request.get_json()['password']
    except(KeyError):
        return jsonify({"error":"NO_PASSWORD","error_msg":"You must supply a password to authenticate."})

    # Fetch user
    user = Profile.get(email=email)

    if not verify_password(user.password, password):
        return jsonify({"error":"INCORRECT_CREDENTIALS","error_msg":"The supplied credentials are incorrect."})

    # Create session key (TODO: Actually authenticate)
    session = Session(
        user=user,
        session_key=''.join(random.choice(string.ascii_lowercase) for i in range(12)),
        expires=datetime.now() + timedelta(days=3)
    )

    return jsonify({"msg":"Welcome.", "session_key": session.session_key})


@app.route('/ping')
@auth_required
def ping():
    return jsonify({"status":"OK"})


@app.route('/user', methods=['GET'])
@auth_required
@db_session
def get_user():
    session_key = request.args.get('session_key')

    # Get user associated with session key
    user = Session.get(session_key=session_key).user.to_dict()

    # Delete hashed password
    del user['password']

    return jsonify(user)


@app.route('/monitor', methods=['GET'])
@auth_required
@db_session
def get_monitors():
    session_key = request.args.get('session_key')

    # Get user associated with session key
    user = Session.get(session_key=session_key).user

    monitors = []
    for monitor in user.monitors:
        monitor_dictionary = monitor.to_dict()
        monitor_dictionary['hits'] = []

        for hit in monitor.triggers:
            monitor_dictionary['hits'].append(hit.to_dict())

        monitors.append(monitor_dictionary)

    return jsonify(monitors)


@app.route('/monitor/<id>', methods=['GET'])
@auth_required
@db_session
def get_monitor(id):
    session_key = request.args.get('session_key')

    # Get user associated with session key
    user = Session.get(session_key=session_key).user

    m = Monitor.get(id=id)

    return jsonify(m.to_dict())


@app.route('/monitor', methods=['POST'])
@auth_required
@db_session
def post_monitor():
    session_key = request.get_json()['session_key']

    # Get user associated with session key
    user = Session.get(session_key=session_key).user

    # Create new monitor if no ID is found
    try:
        m = Monitor.get(id=request.get_json()['id'])
        m.name = request.get_json()['name']
        m.filters = request.get_json()['filters']
    except KeyError:
        m = Monitor(
            name=request.get_json()['name'],
            user=user,
            filters=request.get_json()['filters']
        )

    return jsonify(m.to_dict())


@app.route('/monitor', methods=['DELETE'])
@auth_required
@db_session
def delete_monitor():
    session_key = request.args.get('session_key')

    # Get user associated with session key
    user = Session.get(session_key=session_key).user

    m = Monitor.get(id=request.args.get('id'))
    m.delete()

    return jsonify({})


# Blue Agent
class BlueAgentThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, name='BlueAgentThread')

    def run(self):
        cycle = 0
        dba = Dba()
        gg = GulOgGratis()

        while True:
            try:
                # Run certain tasks
                if cycle is 0:
                    #investigate()
                    dba.sync()
                    # gg.sync()

                if cycle % 10 is 0:
                    dba.quick_sync()
                    # gg.quick_sync()
                    welcome_users()

                if cycle % 60 is 0:
                    # clean_items()
                    pass

                cycle += 1

                # Reset cycle counter
                if cycle > 600:
                    cycle = 0
            except Exception as error:
                logger.error("[WALINGHAM] Exception occurred: \n{}".format(error))

            time.sleep(1)


# Notification thread
class NotificationThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, name='NotificationThread')
        logger.info("[NOTIFICATIONS] Connecting to Facebook Messenger")

        self.client = Client('walsingham@simse.io', 'FZu5tEfmMFNGp8wQbArh')

    def run(self):
        while True:
            self.send_notifications()

            time.sleep(1)

    @db_session
    def send_notifications(self):
        # Fetch pending notifications
        notifications = Notification.select()

        if(len(notifications) > 0):
            for notification in notifications:
                recipient = notification.recipient.messenger_id
                body = notification.body

                self.client.send(Message(text=body), thread_id=recipient, thread_type=ThreadType.USER)
                notification.delete()