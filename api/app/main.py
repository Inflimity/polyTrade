from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
import os
from dotenv import load_dotenv

# Load the environment configurations
load_dotenv(dotenv_path=".env")

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
    key = os.getenv("POLYMARKET_API_KEY")
    key_status = "Loaded" if key else "Missing"
    return {"status": "ok", "message": f"Alpha Engine Backend Live. API Key: {key_status}"}

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
from src.indexers.polymarket.client import PolymarketClient
from src.indexers.kalshi.client import KalshiClient
from src.analysis.common.arbitrage_scanner import ArbitrageScanner
from src.analysis.common.market_matcher import MarketMatcher, MatchedMarket

# Initialize our scanner instances
matcher = MarketMatcher(similarity_threshold=75.0)
scanner = ArbitrageScanner(target_profit_margin=0.5) # Lowered for testing

# Store live latest data
# Structure: live_books["kalshi"]["ticker"] = {"yes_ask": X, "no_ask": Y}
# Structure: live_books["polymarket"]["asset_id"] = {"price": X}
live_books = {
    "kalshi": {},
    "polymarket": {}
}

# The active dynamically matched markets
ACTIVE_MATCHES: list[MatchedMarket] = []

async def handle_market_update(payload: dict):
    """Processes incoming data from either exchange and scans for arbitrage."""
    source = payload.get("source")
    data = payload.get("data", {})
    
    # 1. Format human-readable ticker stream & Update local caches
    message_str = "Received heartbeat or empty payload"
    
    if source == "kalshi":
        msg_type = data.get("type")
        msg_payload = data.get("msg", {}) # Kalshi V2 wraps data in 'msg'
        
        if msg_type == "orderbook_delta" or msg_type == "ticker":
            ticker = msg_payload.get("market_ticker") or data.get("market_ticker", "Unknown")
            
            # Extract prices (v2 sometimes uses yes_ask in top-level, sometimes in 'msg')
            yes_ask = msg_payload.get("yes_ask") or data.get("yes_ask")
            no_ask = msg_payload.get("no_ask") or data.get("no_ask")
            
            if msg_type == "orderbook_delta":
                delta = msg_payload.get("delta", {}) or data.get("delta", {})
                try:
                    p_list = delta.get("yes", [])
                    if p_list and not yes_ask: yes_ask = p_list[0][0]
                except (IndexError, TypeError): pass
                try:
                    p_list = delta.get("no", [])
                    if p_list and not no_ask: no_ask = p_list[0][0]
                except (IndexError, TypeError): pass
                
            if ticker and ticker != "Unknown":
                if ticker not in live_books["kalshi"]:
                    live_books["kalshi"][ticker] = {}
                if yes_ask is not None: live_books["kalshi"][ticker]["yes_ask"] = float(yes_ask)
                if no_ask is not None: live_books["kalshi"][ticker]["no_ask"] = float(no_ask)
                message_str = f"Kalshi {msg_type}: {ticker} Y:{yes_ask}¢ N:{no_ask}¢"
            else:
                message_str = f"Kalshi tick: {msg_type} (ignored)"
        else:
            message_str = f"Kalshi event: {msg_type}"
            
    elif source == "polymarket":
        events = data if isinstance(data, list) else [data]
        for event in events:
            e_type = event.get("event_type")
            asset_id = event.get("asset_id")
            
            # Polymarket price can be top-level or nested in bids/asks
            price = event.get("price") or event.get("ask")
            if not price and e_type == "book":
                asks = event.get("asks", [])
                if asks: price = asks[0].get("price")
            
            if asset_id and price is not None:
                try:
                    p_cents = float(price) * 100
                    live_books["polymarket"][asset_id] = {"price": p_cents}
                    message_str = f"Poly {e_type}: {asset_id[:8]}.. @ {p_cents:.1f}¢"
                except (ValueError, TypeError):
                    pass
            elif e_type == "ping":
                message_str = "Poly heartbeat"
            
    # Broadcast raw data to dashboard 'live feed' tab
    await manager.broadcast({
        "type": "raw_feed",
        "source": source,
        "message": message_str
    })
    
    # Broadcast current system status periodically or on every update
    await manager.broadcast({
        "type": "system_status",
        "total_matched": len(ACTIVE_MATCHES)
    })
    
    # 2. Feed the Arbitrage Engine to make Predictions
    for match in ACTIVE_MATCHES:
        k_data = live_books["kalshi"].get(match.kalshi_ticker, {})
        
        # Need to find YES and NO prices from Polymarket assets
        # Polymarket typically has 2 outcome tokens. Let's assume asset_ids[0] is YES, [1] is NO
        p_yes, p_no = None, None
        if len(match.polymarket_asset_ids) >= 2:
            p_yes_id = match.polymarket_asset_ids[0]
            p_no_id = match.polymarket_asset_ids[1]
            p_yes = live_books["polymarket"].get(p_yes_id, {}).get("price")
            p_no = live_books["polymarket"].get(p_no_id, {}).get("price")
            
        p_data = {"yes_ask": p_yes, "no_ask": p_no}
        
        opportunity = scanner.scan(match, k_data, p_data)
        if opportunity:
            await manager.broadcast({
                "type": "prediction_flag",
                "ticker": match.kalshi_ticker,
                "direction": opportunity.direction,
                "profit_margin": round(opportunity.spread_pct, 2),
                "k_yes": opportunity.kalshi_yes_price_cents,
                "p_yes": opportunity.polymarket_yes_price_cents
            })
    
async def orchestrate_data_feeds():
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    logger.info("Initializing REST clients to find cross-exchange matching markets...")
    
    # 1. Fetch Active Markets
    try:
        with KalshiClient() as kc:
            k_markets = kc.list_markets(limit=200, status="active")
    except Exception as e:
        logger.error(f"Failed to fetch Kalshi markets: {e}")
        k_markets = []
        
    try:
        with PolymarketClient() as pc:
            p_markets = pc.get_markets(limit=200, active=True)
    except Exception as e:
        logger.error(f"Failed to fetch Polymarket markets: {e}")
        p_markets = []
        
    logger.info(f"Loaded {len(k_markets)} Kalshi markets and {len(p_markets)} Polymarket markets.")
    
    # 2. Match the markets using NLP
    global ACTIVE_MATCHES
    ACTIVE_MATCHES = matcher.find_all_matches(k_markets, p_markets)
    # Sort by highest score and take top 50 to avoid overloading limits
    ACTIVE_MATCHES.sort(key=lambda x: x.similarity_score, reverse=True)
    ACTIVE_MATCHES = ACTIVE_MATCHES[:50]
    
    logger.info(f"Successfully matched {len(ACTIVE_MATCHES)} overlapping markets!")
    for i, m in enumerate(ACTIVE_MATCHES[:5]):
        logger.info(f"Match #{i+1} ({m.similarity_score}%): {m.kalshi_ticker} <-> {m.polymarket_question[:40]}..")
    
    # 3. Extract the exact identifiers we need for WebSocket Subscriptions
    kalshi_tickers = [m.kalshi_ticker for m in ACTIVE_MATCHES]
    polymarket_asset_ids = []
    for m in ACTIVE_MATCHES:
        polymarket_asset_ids.extend(m.polymarket_asset_ids)

    # 4. Start the WebSockets with the precise tracking targets
    polymarket_feed = PolymarketLiveFeed(handle_market_update)
    kalshi_feed = KalshiLiveFeed(handle_market_update)
    
    asyncio.create_task(polymarket_feed.connect_and_stream(asset_ids=polymarket_asset_ids))
    asyncio.create_task(kalshi_feed.connect_and_stream(kalshi_tickers=kalshi_tickers))
    
    while True:
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(orchestrate_data_feeds())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
