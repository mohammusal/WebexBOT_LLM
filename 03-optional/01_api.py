"""
Cisco Live 2026 - LABCOL-1007: Building Your First Webex Bot

- Diego Manuel Jimenez Moreno
"""

import os
from dotenv import load_dotenv
import requests

# Load environment variables from the .env file.
load_dotenv()

bot_token = os.getenv("BOT_TOKEN")
person_email = os.getenv("PERSON_EMAIL")

URL = 'https://api.ciscospark.com/v1/messages'
MESSAGE_TEXT = "Hello! I am testing my new bot."

headers = {'Authorization': 'Bearer ' + bot_token,
           'Content-type': 'application/json;charset=utf-8'}
post_data = {'toPersonEmail': person_email,
             'text': MESSAGE_TEXT}

response = requests.post(URL, json=post_data, headers=headers)

if response.status_code == 200:
    print("Message sent")
else:
    print(response.status_code, response.text)
