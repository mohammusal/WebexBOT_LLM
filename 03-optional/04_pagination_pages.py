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

def list_people(access_token, url):
    headers = {
        'Authorization': f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response
    else:
        raise Exception(f"Failed to obtain people: {response.status_code} - {response.text}")

response = list_people(access_token, "https://webexapis.com/v1/people?max=2")
people = response.json()["items"]
print("Printing first 2 people:")
for person in people:
    print(f"Name: {person['displayName']}, Email: {person['emails']}")

links = response.links["next"]["url"]
response2 = list_people(access_token, links)
people2 = response2.json()["items"]
print("Printing next 2 people:")
for person in people2:
    print(f"Name: {person['displayName']}, Email: {person['emails']}")
