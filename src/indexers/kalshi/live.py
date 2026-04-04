import asyncio
import json
import logging
import websockets
import time
import os
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)

class KalshiLiveFeed:
    """Connects to the Kalshi WebSocket streaming API for live updates."""
    
    URL = "wss://api.elections.kalshi.com/trade-api/ws/v2"
    PATH = "/trade-api/ws/v2"

    def __init__(self, callback: Callable[[dict], Awaitable[None]]):
        self.callback = callback
        self.running = False
        
    def _generate_auth_headers(self) -> dict:
        """Generate RSA-PSS headers for Kalshi WebSocket Auth."""
        key_id = os.getenv("KALSHI_API_KEY_ID")
        key_path = os.getenv("KALSHI_PRIVATE_KEY_PATH", "kalshi.key")
        
        if not key_id or not os.path.exists(key_path):
            raise ValueError(f"Missing Kalshi credentials. Key ID: {key_id}, Path: {key_path}")
            
        with open(key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
            )
            
        ts = str(int(time.time() * 1000))
        msg = f"{ts}GET{self.PATH}".encode('utf-8')
        
        sig = private_key.sign(
            msg,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH,
            ),
            hashes.SHA256(),
        )
        
        return {
            "KALSHI-ACCESS-KEY": key_id,
            "KALSHI-ACCESS-SIGNATURE": base64.b64encode(sig).decode('utf-8'),
            "KALSHI-ACCESS-TIMESTAMP": ts,
        }
        
    async def connect_and_stream(self, kalshi_tickers: list[str] = None):
        self.running = True
        retry_delay = 1
        
        while self.running:
            try:
                # Generate a fresh token for this connection
                headers = self._generate_auth_headers()
                
                logger.info(f"Connecting to Kalshi WS at {self.URL} with RSA PSS signature auth")
                async with websockets.connect(
                    self.URL, 
                    additional_headers=headers,
                    ping_interval=20,
                    ping_timeout=10
                ) as websocket:
                    logger.info("Connected to Kalshi WS")
                    retry_delay = 1
                    
                    # Subscribe to ticker channel only (orderbook_delta needs separate sub with market_tickers)
                    sub_message = {
                        "id": 1,
                        "cmd": "subscribe",
                        "params": {"channels": ["ticker"]}
                    }
                    if kalshi_tickers:
                        sub_message["params"]["market_tickers"] = kalshi_tickers
                    
                    await websocket.send(json.dumps(sub_message))
                    logger.info(f"Subscribed to Kalshi ticker channel ({len(kalshi_tickers) if kalshi_tickers else 'all'} markets)")
                    
                    while self.running:
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=60)
                            data = json.loads(message)
                            await self.callback({"source": "kalshi", "data": data})
                        except asyncio.TimeoutError:
                            # No data in 60s, connection is still alive (ping handles keepalive)
                            continue
                        except Exception as e:
                            logger.error(f"Error processing Kalshi message: {e}")
                            continue
                        
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"Kalshi WS closed: code={e.code} reason={e.reason}")
            except Exception as e:
                logger.error(f"Error in Kalshi WS stream: {e}")
                
            if self.running:
                logger.info(f"Reconnecting in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)
                
    def stop(self):
        self.running = False

