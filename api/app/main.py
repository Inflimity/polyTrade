from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging

app = FastAPI(title="Prediction Market Alpha Engine API")

# Setup CORS for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active websocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        # Fire and forget messages to all connected clients
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Alpha Engine Backend Live"}

@app.websocket("/api/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect messages from client, but keep the loop alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

import sys
from pathlib import Path
# Add project root to python path to allow importing from src
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.indexers.polymarket.live import PolymarketLiveFeed
from src.indexers.kalshi.live import KalshiLiveFeed
from src.analysis.common.arbitrage_scanner import ArbitrageScanner
from src.analysis.common.market_matcher import MarketMatcher, MatchedMarket

# Initialize our scanner instances
matcher = MarketMatcher()
scanner = ArbitrageScanner(target_profit_margin=1.0) # 1% profit margin minimum

# Store live latest data
live_books = {
    "kalshi": {},
    "polymarket": {}
}

# A mock list of matched markets just for the MVP
# In a real scenario, this would be periodically computed by hitting the REST APIs of both
DEMO_MATCHES = [
    MatchedMarket(
        kalshi_ticker="KXVS-24",
        kalshi_title="Will Trump win?",
        polymarket_id="0xdeadbeef",
        polymarket_question="Will Trump win the 2024 Presidential Election?",
        similarity_score=95.0
    )
]

async def handle_market_update(payload: dict):
    """Processes incoming data from either exchange and scans for arbitrage."""
    source = payload.get("source")
    data = payload.get("data")
    
    # Broadcast raw data to dashboard 'live feed' tab
    await manager.broadcast({
        "type": "raw_feed",
        "source": source,
        "data": data
    })
    
    # Normally we would update our local order book copy:
    # live_books[source][market_id] = parsed_prices
    # Then we run the scanner
    
    # Simulate an arbitrage result format
    # In full production we would do scanner.scan(match, live_books["kalshi"], live_books["polymarket"])
    
async def orchestrate_data_feeds():
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    
    polymarket_feed = PolymarketLiveFeed(handle_market_update)
    kalshi_feed = KalshiLiveFeed(handle_market_update)
    
    # Start tasks without blocking the main event loop
    asyncio.create_task(polymarket_feed.connect_and_stream())
    asyncio.create_task(kalshi_feed.connect_and_stream())
    
    while True:
        # We can implement a periodic manual scan or cleanup here
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(orchestrate_data_feeds())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
