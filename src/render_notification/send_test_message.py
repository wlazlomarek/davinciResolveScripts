''' 
Sends test message to slack user
'''

import os

from slack import WebClient
from slack.errors import SlackApiError

from dotenv import load_dotenv

load_dotenv('.env')


def send(message: str):
    sc = WebClient(token=os.getenv('S_TOKEN'))
    try:
        msg = sc.chat_postMessage(
            text=message,
            channel=os.getenv('S_USER_ID'),
            as_user=True)
    except SlackApiError as e:
        print(f"Slack error: {e.response['error']}")


if __name__ == '__main__':
    send('test message')
