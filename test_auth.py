import requests
import jwt
import time
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.example")
key_id = os.getenv("KALSHI_API_KEY_ID")

with open("kalshi.key", "r") as f:
    private_key = f.read()

now = int(time.time())
payload = {
    "iss": key_id,
    "sub": key_id,
    "iat": now,
    "exp": now + 60*60
}
token = jwt.encode(payload, private_key, algorithm="RS256")

headers = {
    "Authorization": f"Bearer {token}"
}
url = "https://api.elections.kalshi.com/trade-api/v2/exchange/status"
res = requests.get(url, headers=headers)
print("Status Code:", res.status_code)
print("Response:", res.text)
