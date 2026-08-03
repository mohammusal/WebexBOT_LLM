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

card = {
    "contentType": "application/vnd.microsoft.card.adaptive",
    "content": {
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
                                "url": "https://securitydocs.cisco.com/Site%20images%20for%20Docs%20portal/Initial%20site%20images/Temp_Cisco-logo.png",
                                "size": "Medium",
                                "height": "50px"
                            }
                        ],
                        "width": "auto"
                    },
                    {
                        "type": "Column",
                        "items": [
                            {
                                "type": "TextBlock",
                                "weight": "Bolder",
                                "text": "Cisco Live!",
                                "horizontalAlignment": "Left",
                                "wrap": True,
                                "color": "Light",
                                "size": "Large",
                                "spacing": "Small"
                            }
                        ],
                         "width": "stretch"
                    }
                ]
            },
            {
                "type": "TextBlock",
                "text": "This is my first Adaptive Card!",
                "wrap": True
            }
        ],
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.3"
    }
}

webex = WebexAPI(bot_token)
webex.messages.create(toPersonEmail=person_email, text="", attachments=[card])
