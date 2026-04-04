import asyncio
import json
import logging
import websockets
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)

class PolymarketLiveFeed:
    """Connects to the Polymarket Gamma WebSocket API for live market data."""
    
    URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

    def __init__(self, callback: Callable[[dict], Awaitable[None]]):
        self.callback = callback
        self.running = False
        
    async def connect_and_stream(self, asset_ids: list[str]):
        self.running = True
        retry_delay = 1
        
        if not asset_ids:
            logger.warning("No Polymarket asset IDs provided for WS subscription.")
            return

        while self.running:
            try:
                logger.info(f"Connecting to Polymarket WS at {self.URL}")
                async with websockets.connect(self.URL) as websocket:
                    logger.info("Connected to Polymarket WS")
                    retry_delay = 1 # reset delay on successful connection
                    
                    # Subscribe to specific asset IDs to avoid overloading the feed
                    # Polymarket CLOB accepts chunks, we can send all in one list
                    sub_message = {
                        "assets_ids": asset_ids,
                        "type": "market"
                    }
                    await websocket.send(json.dumps(sub_message))
                    logger.info(f"Subscribed to {len(asset_ids)} Polymarket assets.")
                    
                    while self.running:
                        message = await websocket.recv()
                        data = json.loads(message)
                        await self.callback({"source": "polymarket", "data": data})
                        
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Polymarket WS connection closed")
            except Exception as e:
                logger.error(f"Error in Polymarket WS stream: {e}")
                
            if self.running:
                logger.info(f"Reconnecting in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)
                
    def stop(self):
        self.running = False
