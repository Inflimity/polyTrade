"""Capture and print raw Kalshi WS messages to see actual payload structure."""
import asyncio
import websockets
import json
import os
import time
import base64
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

PATH = "/trade-api/ws/v2"
def _generate_auth_headers():
    key_id = os.getenv("KALSHI_API_KEY_ID")
    key_path = "kalshi.key"
    with open(key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    ts = str(int(time.time() * 1000))
    msg_bytes = f"{ts}GET{PATH}".encode('utf-8')
    sig = private_key.sign(msg_bytes, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
    return {"KALSHI-ACCESS-KEY": key_id, "KALSHI-ACCESS-SIGNATURE": base64.b64encode(sig).decode('utf-8'), "KALSHI-ACCESS-TIMESTAMP": ts}

async def check():
    url = "wss://api.elections.kalshi.com/trade-api/ws/v2"
    headers = _generate_auth_headers()
    async with websockets.connect(url, additional_headers=headers) as ws:
        await ws.send(json.dumps({"id": 1, "cmd": "subscribe", "params": {"channels": ["ticker", "orderbook_delta"]}}))
        count = 0
        while count < 10:
            raw = await asyncio.wait_for(ws.recv(), timeout=10.0)
            data = json.loads(raw)
            msg_type = data.get("type")
            print(f"\n=== Message {count+1} (type={msg_type}) ===")
            print(json.dumps(data, indent=2)[:500])
            count += 1

asyncio.run(check())
