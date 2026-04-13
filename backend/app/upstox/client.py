import os
import requests
from datetime import datetime

BASE_URL = "https://api.upstox.com/v2"


class UpstoxClient:
    def __init__(self, access_token: str):
        if not access_token:
            raise ValueError("Upstox access token is required")
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

    def get_ltp(self, instrument_key: str) -> dict:
        if not instrument_key:
            raise ValueError("Instrument key is required")
        url = f"{BASE_URL}/market-quote/ltp"
        params = {"instrument_key": instrument_key}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_historical(self, instrument_key: str, interval: str = "day", from_date: str = None, to_date: str = None) -> dict:
        if not instrument_key:
            raise ValueError("Instrument key is required")
        if not from_date:
            from_date = "2024-01-01"
        if not to_date:
            to_date = datetime.utcnow().strftime("%Y-%m-%d")
        url = f"{BASE_URL}/historical-candle/{instrument_key}/{interval}/{from_date}/{to_date}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
