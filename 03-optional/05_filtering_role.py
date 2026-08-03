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
ROLE = "Y2lzY29zcGFyazovL3VzL1JPTEUvaWRfZnVsbF9hZG1pbg"

def list_people_by_role(access_token, role):
    url = f"https://webexapis.com/v1/people?roles={role}"

    headers = {
        'Authorization': f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to obtain people: {response.status_code} - {response.text}")

admins = list_people_by_role(access_token, ROLE)
for admin in admins["items"]:
    print(f"Name: {admin['displayName']}, Email: {admin['emails']}")
