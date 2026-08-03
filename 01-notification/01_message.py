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
person_email = os.getenv("PERSON_EMAIL")

def send_teams_message(bot_token: str, message: str, person_email: str):
    """
    Sends a direct message to a specified person via Webex Teams.

    Args:
        bot_token (str): The authentication token for the Webex bot.
        message (str): The content of the message to send (supports Markdown).
        person_email (str): The email address of the recipient.
    """
    # Initialize the main WebexAPI client with the bot token.
    webex = WebexAPI(bot_token)
    # Create a direct message to the specified person's email with the given markdown content.
    webex.messages.create(toPersonEmail=person_email, markdown=message)

MESSAGE_TEXT = "Hello! I am testing my new bot."
send_teams_message(bot_token, MESSAGE_TEXT, person_email)
