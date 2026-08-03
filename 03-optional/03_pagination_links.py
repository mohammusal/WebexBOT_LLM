"""
Cisco Live 2026 - LABCOL-1007: Building Your First Webex Bot

- Diego Manuel Jimenez Moreno
"""

import os
from dotenv import load_dotenv
import requests

# Load environment variables from the .env file.
load_dotenv()

access_token = os.getenv("ACCESS_TOKEN")

def list_people(access_token, limit):
    url = f"https://webexapis.com/v1/people?max={limit}"

    headers = {
        'Authorization': f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.links
    else:
        raise Exception(f"Failed to obtain people: {response.status_code} - {response.text}")

links = list_people(access_token, 2)
print(f"{links}")
