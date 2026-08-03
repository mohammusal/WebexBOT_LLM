"""
Cisco Live 2026 - LABCOL-1007: Building Your First Webex Bot

- Diego Manuel Jimenez Moreno
"""

import os
from dotenv import load_dotenv
from webexpythonsdk import WebexAPI

# Load environment variables from the .env file.
load_dotenv()

bot_token = os.getenv("BOT_TOKEN")
access_token = os.getenv("ACCESS_TOKEN")
domain = os.getenv("DOMAIN")

from webex_bot.webex_bot import WebexBot
from webex_bot.formatting import quote_info
from webex_bot.models.command import Command
from webex_bot.models.response import Response
import requests
import re

class AutoProvisioning(Command):

    def __init__(self):
        super().__init__(
            command_keyword="provision",
            help_message="Provision your new IP Phone",
            chained_commands=[ProvisionCallback()])

    def execute(self, message, attachment_actions, activity):
        """
        :param message: message with command already stripped
        :param attachment_actions: attachment_actions object
        :param activity: activity object

        :return: a string or Response object (or a list of either). Use Response if you want to return another card.
        """

        card = {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "type": "AdaptiveCard",
                "body": [
                    {
                        "type": "ColumnSet",
                        "columns": [
                            {
                                "type": "Column",
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "weight": "Bolder",
                                        "text": "Welcome to the Auto-Provisioning Bot!\n",
                                        "horizontalAlignment": "Left",
                                        "wrap": True,
                                        "color": "Light",
                                        "size": "Large",
                                        "spacing": "Small"
                                    }
                                ],
                                "width": "stretch"
                            }
                        ]
                    },
                    {
                        "type": "TextBlock",
                        "text": "Please, insert the MAC address of your new phone:",
                        "wrap": True
                    },
                    {
                        "type": "Input.ChoiceSet",
                        "choices": [
                            {
                                "title": "DMS Cisco 8851",
                                "value": "DMS Cisco 8851"
                            },
                            {
                                "title": "DMS Cisco 8861",
                                "value": "DMS Cisco 8861"
                            },
                            {
                                "title": "DMS Cisco 8865",
                                "value": "DMS Cisco 8865"
                            }
                        ],
                        "placeholder": "Phone model",
                        "id": "model",
                        "isRequired": True,
                        "errorMessage": "model is required",
                        "label": "Select mode:"
                    },
                    {
                        "type": "Input.Text",
                        "placeholder": "MAC Address",
                        "id": "mac_address",
                        "isRequired": True,
                        "errorMessage": "MAC is required",
                        "label": "MAC Address:"
                    }
                ],
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "version": "1.3",
                "actions": [
                    {
                        "type": "Action.Submit",
                        "title": "Submit",
                        "data": {
                            "callback_keyword": "provision_callback"
                        }
                    }
                ]
            }
        }

        response = Response()
        response.text = "Text"
        response.attachments = card

        return response

def is_valid_mac_address(mac):
    # Regular expression for a MAC address
    pattern = r'^[0-9A-Fa-f]{12}$'
    return bool(re.match(pattern, mac))

class ProvisionCallback(Command):

    def __init__(self):
        super().__init__(
            card_callback_keyword="provision_callback",
            delete_previous_message=True)

    def execute(self, message, attachment_actions, activity):
        personid = attachment_actions.personId
        mac_address = attachment_actions.inputs.get("mac_address")
        model = attachment_actions.inputs.get("model")

        if not is_valid_mac_address(mac_address):
            return quote_info("MAC Address format is incorrect. Introduce MAC Address like A1B2C3D4E5F6")

        url = "https://webexapis.com/v1/devices"

        payload = {
            "mac": mac_address,
            "model": model,
            "personId": personid
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.request('POST', url, headers=headers, json=payload)
        print(f"{payload} {headers}")

        if response.status_code == 200:
            return quote_info("MAC Address added successfully")
        elif response.status_code == 409:
            return quote_info("MAC Address is duplicated")
        else:
            return quote_info("There was an error")

# Create a Bot Object
bot = WebexBot(teams_bot_token=bot_token,
               bot_name="CiscoLive2026",
               approved_domains=domain,
               )

# Add new commands for the bot to listen out for.
bot.add_command(AutoProvisioning())

# Call `run` for the bot to wait for incoming messages.
bot.run()
