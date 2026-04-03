from typing import Dict, List, Optional
from dataclasses import dataclass
from .market_matcher import MatchedMarket

@dataclass
class ArbitrageOpportunity:
    kalshi_ticker: str
    polymarket_id: str
    kalshi_yes_price_cents: float
    polymarket_yes_price_cents: float
    polymarket_no_price_cents: float
    kalshi_no_price_cents: float
    spread_pct: float
    capital_required: float
    direction: str  # e.g., "BUY_KALSHI_YES_POLY_NO"
    timestamp: float

class ArbitrageScanner:
    """Calculates spread and highlights profitable arbitrages between Kalshi and Polymarket."""
    
    def __init__(self, target_profit_margin: float = 2.0, polymarket_fee_pct: float = 2.0, kalshi_fee_pct: float = 2.0):
        self.target_profit_margin = target_profit_margin
        self.polymarket_fee_pct = polymarket_fee_pct
        self.kalshi_fee_pct = kalshi_fee_pct
        
    def calculate_spread(self, 
                         k_yes: float, k_no: float, 
                         p_yes: float, p_no: float) -> tuple[float, str]:
        """
        Calculate if there is an arbitrage opportunity.
        Prices should be in cents (0 - 100).
        """
        if not all([k_yes, k_no, p_yes, p_no]):
            return 0.0, ""
            
        # Strategy 1: Buy YES on Kalshi, Buy NO on Polymarket
        # Ensure total cost < 100 representing risk-free profit
        # Include estimated fees
        cost_1 = (k_yes * (1 + self.kalshi_fee_pct / 100.0)) + (p_no * (1 + self.polymarket_fee_pct / 100.0))
        
        # Strategy 2: Buy NO on Kalshi, Buy YES on Polymarket
        cost_2 = (k_no * (1 + self.kalshi_fee_pct / 100.0)) + (p_yes * (1 + self.polymarket_fee_pct / 100.0))
        
        if cost_1 < cost_2 and cost_1 < (100.0 - self.target_profit_margin):
            return 100.0 - cost_1, "BUY_KALSHI_YES_POLY_NO"
        elif cost_2 < cost_1 and cost_2 < (100.0 - self.target_profit_margin):
            return 100.0 - cost_2, "BUY_KALSHI_NO_POLY_YES"
            
        return 0.0, ""

    def scan(self, match: MatchedMarket, live_kalshi: Dict, live_polymarket: Dict) -> Optional[ArbitrageOpportunity]:
        """Scan a matched pair for arbitrage given live market data."""
        
        # Expecting live data dicts to contain current best ask prices in cents
        k_yes = live_kalshi.get("yes_ask")
        k_no = live_kalshi.get("no_ask")
        
        # Polymarket typically represents prices as [0.0, 1.0]. Convert to cents
        p_yes = live_polymarket.get("yes_ask")
        p_no = live_polymarket.get("no_ask")
        
        if k_yes and k_no and p_yes and p_no:
            spread, direction = self.calculate_spread(k_yes, k_no, p_yes, p_no)
            
            if spread > 0:
                import time
                return ArbitrageOpportunity(
                    kalshi_ticker=match.kalshi_ticker,
                    polymarket_id=match.polymarket_id,
                    kalshi_yes_price_cents=k_yes,
                    kalshi_no_price_cents=k_no,
                    polymarket_yes_price_cents=p_yes,
                    polymarket_no_price_cents=p_no,
                    spread_pct=spread,
                    capital_required=(k_yes + p_no) if "KALSHI_YES" in direction else (k_no + p_yes),
                    direction=direction,
                    timestamp=time.time()
                )
                
        return None
