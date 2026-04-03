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
        
    async def connect_and_stream(self):
        self.running = True
        retry_delay = 1
        
        while self.running:
            try:
                logger.info(f"Connecting to Polymarket WS at {self.URL}")
                async with websockets.connect(self.URL) as websocket:
                    logger.info("Connected to Polymarket WS")
                    retry_delay = 1 # reset delay on successful connection
                    
                    # Standard subscription payload for specific markets
                    # We might need to listen to all or specific asset IDs.
                    # Since polymarket doesn't have a single stream for "all trades" without filtering,
                    # we would typically subscribe by token IDs here. For the skeleton, we listen.
                    
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
