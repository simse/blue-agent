import os
import datetime

from slackclient import SlackClient
from twilio.rest import Client

from blueagent.logger import logger
from blueagent.models import *

twilio_client = Client(os.environ['TWILIO_SID'], os.environ['TWILIO_TOKEN'])


def new_item_event(item):
    # logger.info("New item, processing....")
    # sc = SlackClient(os.environ['SLACK_API_KEY'])

    # Temp send to Slack
    #sc.api_call(
    #    "chat.postMessage",
    #    channel="CEEC4PCSW",
    #    text="[{}] New item: {}".format(datetime.datetime.now(), item.dba_url)
    #)

    # Check all rules from profiles
    with db_session:
        profiles = Profile.select()

        for profile in profiles:
            rules = profile.rules

            for rule in rules:

                rule_pass = True

                for part in rule:

                    if not item.filter(part, rule[part]):
                        rule_pass = False

                if rule_pass:
                    item_match(profile, item.item)


def new_user(profile):
    logger.info("[NEW USER] Sending SMS...")

    body = 'Hej, {}!\nVelkommen til Den Blå Agent. Jeg kan hjælpe dig med at finde interessante annoncer på DBA. \
Fra nu af modtager du en SMS, når jeg finder noget. \
I øjeblikket leder jeg after {} ting til dig.'.format(profile.first_name, len(profile.rules))

    message = twilio_client.messages.create(
        to='+45' + str(profile.phone_number),
        messaging_service_sid='MG7d683a3611bf5c55cd59297e4a023795',
        body=body
    )

    if message:
        profile.welcomed = True


def item_match(profile, item):
    logger.info("[ITEM MATCH] Notifying profile")

    phone_number = '+45' + str(profile.phone_number)
    body = 'Jeg har fundet en annonce til dig!\nTitel: {}\nPris: {}DKK\n{}'.format(item.title, item.price, item.dba_url)

    # Message
    #message = twilio_client.messages.create(
    #    to=phone_number,
    #    messaging_service_sid='MG7d683a3611bf5c55cd59297e4a023795',
    #    body=body
    #)