import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TOKEN_URL = "https://id.twitch.tv/oauth2/token"

class TwitchTokenManager:
    def __init__(self):
        self.client_id = TWITCH_CLIENT_ID
        self.client_secret = TWITCH_CLIENT_SECRET
        self.access_token: str | None = None
        self.expires_at: float = 0.0

    def request_new_token(self):
        if not self.client_id or not self.client_secret:
            raise ValueError("TWITCH_CLIENT_ID or TWITCH_CLIENT_SECRET is missing in .env")

        response = requests.post(
            TOKEN_URL,
            params={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials"
            },
            timeout= 10
        )
        response.raise_for_status()
        data = response.json()

        self.access_token = data["access_token"]
        expires_in = int(data.get("expires_in", 0))
        #We rest 30 seconds to renovate before it expires
        self.expires_at = time.time() + max(expires_in - 30, 0)

    def get_token(self):
        if not self.access_token or time.time() >= self.expires_at:
            self.request_new_token()
        return self.access_token