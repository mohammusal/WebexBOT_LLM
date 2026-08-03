"""
Cisco Live 2026 - LABCOL-1007: Building Your First Webex Bot

- Diego Manuel Jimenez Moreno
"""

import os
from dotenv import load_dotenv
import requests

# Load environment variables from the .env file.
load_dotenv()

clientid = os.getenv("CLIENTID")
secretid = os.getenv("SECRETID")
refreshtoken = os.getenv("REFRESH_TOKEN")

def refresh_token(client_id, client_secret, refresh_token):
    url = "https://webexapis.com/v1/access_token"

    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret,
    }

    headers = {
        'Content-type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(url, headers=headers, data=payload)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to refresh token: {response.status_code} - {response.text}")

token = refresh_token(clientid, secretid, refreshtoken)

print(f"Access Token: {token['access_token']}")
print(f"Expires in: {token['expires_in']}")
print(f"Refresh Token: {token['refresh_token']}")
print(f"Refresh Token Expires in: {token['refresh_token_expires_in']}")
print(f"Token Type: {token['token_type']}")
