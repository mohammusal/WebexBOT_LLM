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

from webex_bot.commands.echo import EchoCommand
from webex_bot.webex_bot import WebexBot

# Create a Bot Object
bot = WebexBot(teams_bot_token=bot_token,
               bot_name="CiscoLive2026",
               approved_domains=domain,
               include_demo_commands=True)

# Call `run` for the bot to wait for incoming messages.
bot.run()
