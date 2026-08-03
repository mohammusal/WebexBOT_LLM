"""
Cisco Live 2026 - LABCOL-1007: Building Your First Webex Bot

ChatGPT-powered Webex Bot — every message goes to OpenAI,
with per-user stateful conversation history.
"""

import os
import logging

from dotenv import load_dotenv
from openai import OpenAI

from webex_bot.models.command import Command
from webex_bot.webex_bot import WebexBot

load_dotenv()

log = logging.getLogger(__name__)

bot_token = os.getenv("BOT_TOKEN")
domain = os.getenv("DOMAIN")

SYSTEM_PROMPT = "You are a helpful assistant in a Webex chat. Be concise and clear."
MODEL = "gpt-4o-mini"
MAX_HISTORY = 20
MAX_RESPONSE_LENGTH = 7000

conversations: dict[str, list[dict]] = {}

openai_client = OpenAI()


class ChatGPTCommand(Command):

    def __init__(self):
        super().__init__(
            command_keyword="help",
            help_message="Chat with ChatGPT — just type anything!")

    def pre_execute(self, message, attachment_actions, activity):
        return "🤔 Thinking..."

    def execute(self, message, attachment_actions, activity):
        user_email = activity["actor"]["emailAddress"]

        if not message or not message.strip():
            return "Please type a message and I'll respond using ChatGPT."

        if user_email not in conversations:
            conversations[user_email] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]

        conversations[user_email].append({"role": "user", "content": message.strip()})

        try:
            response = openai_client.chat.completions.create(
                model=MODEL,
                messages=conversations[user_email]
            )
            reply = response.choices[0].message.content
        except Exception:
            log.exception("OpenAI API call failed for user %s", user_email)
            conversations[user_email].pop()
            return "⚠️ Sorry, I couldn't process your request right now. Please try again later."

        conversations[user_email].append({"role": "assistant", "content": reply})

        history = conversations[user_email]
        while len(history) > 1 + MAX_HISTORY * 2:
            history.pop(1)
            history.pop(1)

        if len(reply) > MAX_RESPONSE_LENGTH:
            reply = reply[:MAX_RESPONSE_LENGTH] + "\n\n⚠️ _Response was truncated due to length._"

        return reply


class ResetCommand(Command):

    def __init__(self):
        super().__init__(
            command_keyword="reset",
            help_message="Clear your conversation history",
            exact_command_keyword_match=True)

    def execute(self, message, attachment_actions, activity):
        user_email = activity["actor"]["emailAddress"]
        conversations.pop(user_email, None)
        return "🔄 Conversation history cleared. Start fresh!"


bot = WebexBot(
    teams_bot_token=bot_token,
    bot_name="CiscoLive2026 AI",
    approved_domains=domain,
    include_demo_commands=False,
    help_command=ChatGPTCommand()
)

bot.add_command(ResetCommand())

bot.run()
