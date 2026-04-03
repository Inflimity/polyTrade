import asyncio
import json
import logging
import websockets
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)

class KalshiLiveFeed:
    """Connects to the Kalshi WebSocket streaming API for live updates."""
    
    # Kalshi WebSocket URIs usually require authentication,
    # but for public data they might have a public feed depending on the API environment.
    URL = "wss://trading-api.kalshi.com/trade-api/ws/v2"

    def __init__(self, callback: Callable[[dict], Awaitable[None]]):
        self.callback = callback
        self.running = False
        
    async def connect_and_stream(self):
        self.running = True
        retry_delay = 1
        
        while self.running:
            try:
                logger.info(f"Connecting to Kalshi WS at {self.URL}")
                async with websockets.connect(self.URL) as websocket:
                    logger.info("Connected to Kalshi WS")
                    retry_delay = 1
                    
                    # Since Kalshi WS requires an initial payload (often with subscriptions),
                    # we stub out the subscription mechanics.
                    sub_message = {
                        "id": 1,
                        "cmd": "subscribe",
                        "params": {"channels": ["orderbook_delta"]}
                    }
                    await websocket.send(json.dumps(sub_message))
                    
                    while self.running:
                        message = await websocket.recv()
                        data = json.loads(message)
                        await self.callback({"source": "kalshi", "data": data})
                        
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Kalshi WS connection closed")
            except Exception as e:
                logger.error(f"Error in Kalshi WS stream: {e}")
                
            if self.running:
                logger.info(f"Reconnecting in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)
                
    def stop(self):
        self.running = False
