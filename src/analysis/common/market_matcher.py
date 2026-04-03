from typing import Dict, List, Optional, Tuple
import json
import logging
from dataclasses import dataclass
from thefuzz import fuzz

logger = logging.getLogger(__name__)

@dataclass
class MatchedMarket:
    kalshi_ticker: str
    kalshi_title: str
    polymarket_id: str
    polymarket_question: str
    similarity_score: float

class MarketMatcher:
    """Matches Kalshi markets to Polymarket markets using fuzzy NLP matching."""
    
    def __init__(self, similarity_threshold: float = 85.0):
        self.similarity_threshold = similarity_threshold
        
    def preprocess_text(self, text: str) -> str:
        """Clean and normalize text for better matching."""
        if not text:
            return ""
        text = text.lower()
        # Remove common stop words or framing phrases that differs between platforms
        phrases_to_remove = [
            "will ", "?", "to be ", "by ", "in ", "at ",
            "happen ", "occur ", "reach "
        ]
        for phrase in phrases_to_remove:
            text = text.replace(phrase, " ")
        
        # Replace multiple spaces
        return " ".join(text.split())

    def match_market(self, kalshi_market: Dict, polymarket_markets: List[Dict]) -> Optional[MatchedMarket]:
        """Find the best match for a Kalshi market among active Polymarket markets."""
        kalshi_title = f"{kalshi_market.get('title', '')} {kalshi_market.get('yes_sub_title', '')}"
        cleaned_k_title = self.preprocess_text(kalshi_title)
        
        if not cleaned_k_title:
            return None
            
        best_match = None
        highest_score = 0
        
        for p_market in polymarket_markets:
            p_question = p_market.get("question", "")
            cleaned_p_title = self.preprocess_text(p_question)
            
            if not cleaned_p_title:
                continue
                
            # Token set ratio handles varying word order better
            score = fuzz.token_set_ratio(cleaned_k_title, cleaned_p_title)
            
            if score > highest_score:
                highest_score = score
                best_match = p_market
                
        if highest_score >= self.similarity_threshold and best_match:
            return MatchedMarket(
                kalshi_ticker=kalshi_market["ticker"],
                kalshi_title=kalshi_title.strip(),
                polymarket_id=best_match["id"],
                polymarket_question=best_match["question"],
                similarity_score=highest_score
            )
            
        return None

    def find_all_matches(self, kalshi_markets: List[Dict], polymarket_markets: List[Dict]) -> List[MatchedMarket]:
        """Find matches for all provided markets."""
        matches = []
        for k_market in kalshi_markets:
            match = self.match_market(k_market, polymarket_markets)
            if match:
                matches.append(match)
        return matches
