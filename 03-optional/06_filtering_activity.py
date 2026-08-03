"""
Cisco Live 2026 - LABCOL-1007: Building Your First Webex Bot

- Diego Manuel Jimenez Moreno
"""

import os
from dotenv import load_dotenv
from webexpythonsdk import WebexAPI
from datetime import date

# Load environment variables from the .env file.
load_dotenv()

access_token = os.getenv("ACCESS_TOKEN")

webex = WebexAPI(access_token=access_token)

try:
    all_people = webex.people.list()
    for person in all_people:
        if str(person.lastActivity).startswith(date.today().isoformat()):
            print(f"Name: {person.displayName}, Email: {person.emails}")
except Exception as e:
    print(f"An error occurred: {e}")
