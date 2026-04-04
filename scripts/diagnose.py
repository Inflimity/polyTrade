"""Quick diagnostic to test the REST APIs and market matching pipeline."""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.indexers.kalshi.client import KalshiClient
from src.indexers.polymarket.client import PolymarketClient
from src.analysis.common.market_matcher import MarketMatcher

print("=" * 60)
print("STEP 1: Fetch Kalshi markets (status=open, binary only)")
print("=" * 60)
try:
    with KalshiClient() as kc:
        k_markets = kc.list_markets(limit=200, status="open")
    k_markets = [m for m in k_markets if m.market_type == "binary"]
    print(f"✅ Got {len(k_markets)} binary Kalshi markets")
    for m in k_markets[:5]:
        print(f"   - {m.ticker}: {m.title[:60]} (type={m.market_type})")
except Exception as e:
    print(f"❌ Kalshi REST failed: {e}")
    k_markets = []

print()
print("=" * 60)
print("STEP 2: Fetch Polymarket markets (active, not closed, by volume)")
print("=" * 60)
try:
    with PolymarketClient() as pc:
        p_markets = pc.get_markets(limit=100, active=True, closed=False, order="volume", ascending=False)
    p_markets = [m for m in p_markets if m.clob_token_ids and m.clob_token_ids != "[]"]
    print(f"✅ Got {len(p_markets)} active Polymarket markets")
    for m in p_markets[:5]:
        print(f"   - {m.question[:60]}...")
        print(f"     volume={m.volume}, clob_ids={m.clob_token_ids[:40]}...")
except Exception as e:
    print(f"❌ Polymarket REST failed: {e}")
    p_markets = []

print()
print("=" * 60)
print("STEP 3: Run MarketMatcher (threshold=70)")
print("=" * 60)
if k_markets and p_markets:
    matcher = MarketMatcher(similarity_threshold=70.0)
    matches = matcher.find_all_matches(k_markets, p_markets)
    matches.sort(key=lambda x: x.similarity_score, reverse=True)
    print(f"✅ Found {len(matches)} matches")
    for m in matches[:10]:
        print(f"   [{m.similarity_score}%] {m.kalshi_ticker}")
        print(f"     K: {m.kalshi_title[:50]}")
        print(f"     P: {m.polymarket_question[:50]}")
        print(f"     asset_ids: {m.polymarket_asset_ids[:2]}")
    
    if not matches:
        print("⚠️  ZERO matches at 70%. Trying lower...")
        matcher2 = MarketMatcher(similarity_threshold=40.0)
        matches2 = matcher2.find_all_matches(k_markets, p_markets)
        matches2.sort(key=lambda x: x.similarity_score, reverse=True)
        print(f"   With 40% threshold: {len(matches2)} matches")
        for m in matches2[:5]:
            print(f"   [{m.similarity_score}%] K:'{m.kalshi_title[:40]}' <-> P:'{m.polymarket_question[:40]}'")
else:
    print("⚠️ Cannot match — one or both market lists are empty")

print()
print("=" * 60)
print("DONE")
print("=" * 60)
