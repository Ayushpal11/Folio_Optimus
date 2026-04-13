import os
import requests

API_KEY = os.getenv("UPSTOX_API_KEY")
API_SECRET = os.getenv("UPSTOX_API_SECRET")
REDIRECT_URI = os.getenv("UPSTOX_REDIRECT_URI")

AUTH_URL = "https://api.upstox.com/v2/login/authorization/dialog"
TOKEN_URL = "https://api.upstox.com/v2/login/authorization/token"


def get_login_url() -> str:
    if not API_KEY or not REDIRECT_URI:
        raise EnvironmentError("UPSTOX_API_KEY and UPSTOX_REDIRECT_URI must be set")
    return f"{AUTH_URL}?response_type=code&client_id={API_KEY}&redirect_uri={REDIRECT_URI}"


def exchange_code_for_token(code: str) -> dict:
    if not API_KEY or not API_SECRET or not REDIRECT_URI:
        raise EnvironmentError("UPSTOX_API_KEY, UPSTOX_API_SECRET and UPSTOX_REDIRECT_URI must be set")

    response = requests.post(
        TOKEN_URL,
        headers={"accept": "application/json"},
        data={
            "code": code,
            "client_id": API_KEY,
            "client_secret": API_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        },
    )
    response.raise_for_status()
    return response.json()
