"""
Cisco Live 2026 - LABCOL-1007: Building Your First Webex Bot

- Diego Manuel Jimenez Moreno
"""

import os
from dotenv import load_dotenv

# Load environment variables from the .env file.
load_dotenv()

bot_token = os.getenv("BOT_TOKEN")
domain = os.getenv("DOMAIN")

from webex_bot.formatting import quote_info
from webex_bot.models.command import Command
from webex_bot.models.response import Response

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
    "type": "AdaptiveCard",
    "body": [
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "items": [
                        {
                            "type": "Image",
                            "style": "Person",
                            "url": "https://developer.webex.com/images/webex-logo-icon-non-contained.svg",
                            "size": "Medium",
                            "height": "50px"
                        }
                    ],
                    "width": "auto"
                }
            ]
        },
        {
            "type": "TextBlock",
            "text": "This is my First Designed Card",
            "wrap": True,
            "id": "Hello"
        },
        {
            "type": "ActionSet",
            "spacing": "Small",
            "horizontalAlignment": "Right",
            "$when": "Submit",
            "id": "Submit",
            "$data": "Submit",
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Action.Submit"
                }
            ]
        }
    ],
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "version": "1.3"
}

        response = Response()
        response.text = "Text is needed when sending a card."
        response.attachments = card

        return response

class ProvisionCallback(Command):

    def __init__(self):
        super().__init__(
            card_callback_keyword="provision_callback",
            delete_previous_message=True)

    def execute(self, message, attachment_actions, activity):
        return quote_info(attachment_actions.inputs.get("mac_address"))


from webex_bot.commands.echo import EchoCommand
from webex_bot.webex_bot import WebexBot

# Create a Bot Object
bot = WebexBot(teams_bot_token=bot_token,
               bot_name="CiscoLive2026",
               approved_domains=domain,
               include_demo_commands=False)

# Add new commands for the bot to listen out for.
bot.add_command(AutoProvisioning())

# Call `run` for the bot to wait for incoming messages.
bot.run()
