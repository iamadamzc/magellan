"""
Priority Scorer - Opportunity Ranking

Scores selloff opportunities based on research findings:
- Time of day (midday = highest)
- Market context (SPY direction)
- Trend positioning (above 200 SMA)
- 52-week range position
"""

from typing import Dict, Optional
from datetime import datetime
import logging

from .selloff_detector import SelloffEvent


class PriorityScorer:
    """Scores and prioritizes selloff opportunities"""
    
    # Time bucket scores (based on research)
    TIME_SCORES = {
        "opening": 30,      # 71% win rate but small sample
        "morning": 28,      # 66% win rate
        "midday": 30,       # 60% win rate, largest sample
        "afternoon": 15,    # 38% win rate
        "power_hour": 5,    # 15% 60-min, 71% EOD
    }
    
    def __init__(self, spy_client=None):
        """
        Initialize priority scorer
        
        Args:
            spy_client: Optional Alpaca client for SPY data
        """
        self.logger = logging.getLogger("scanner.scorer")
        self.spy_client = spy_client
        self.spy_change = None  # Cache SPY change
    
    def score_event(
        self,
        event: SelloffEvent,
        spy_change: Optional[float] = None,
        above_200sma: Optional[bool] = None,
        range_position: Optional[float] = None,
    ) -> Dict:
        """
        Score a selloff event
        
        Args:
            event: SelloffEvent to score
            spy_change: Optional SPY daily change %
            above_200sma: Optional whether price is above 200 SMA
            range_position: Optional 52-week range position (0-1)
            
        Returns:
            Dict with score and breakdown
        """
        score = 0
        breakdown = {}
        
        # Time bucket score (30 points max)
        time_score = self.TIME_SCORES.get(event.time_bucket, 0)
        score += time_score
        breakdown["time_bucket"] = {
            "bucket": event.time_bucket,
            "score": time_score,
        }
        
        # Market context (15 points max)
        if spy_change is not None:
            if spy_change > 0.5:
                market_score = 15
                market_label = "strong_up"
            elif spy_change > 0:
                market_score = 10
                market_label = "up"
            elif spy_change > -0.5:
                market_score = 5
                market_label = "flat"
            else:
                market_score = 0
                market_label = "down"
            
            score += market_score
            breakdown["market_context"] = {
                "spy_change": spy_change,
                "label": market_label,
                "score": market_score,
            }
        
        # Trend positioning (10 points max)
        if above_200sma is not None:
            trend_score = 10 if above_200sma else 0
            score += trend_score
            breakdown["trend"] = {
                "above_200sma": above_200sma,
                "score": trend_score,
            }
        
        # Range position (10 points max)
        # Avoid falling knives (near 52w low)
        if range_position is not None:
            if range_position > 0.5:
                range_score = 10  # Upper half of range
            elif range_position > 0.3:
                range_score = 5   # Middle
            else:
                range_score = 0   # Lower third (risky)
            
            score += range_score
            breakdown["range_position"] = {
                "position": range_position,
                "score": range_score,
            }
        
        # Severity bonus (deeper selloffs may have more bounce)
        if event.drop_pct <= -15:
            severity_score = 5
        elif event.drop_pct <= -12:
            severity_score = 3
        else:
            severity_score = 0
        
        score += severity_score
        breakdown["severity"] = {
            "drop_pct": event.drop_pct,
            "score": severity_score,
        }
        
        # Determine priority tier
        if score >= 50:
            tier = "HIGH"
            action = "TRADE"
        elif score >= 30:
            tier = "MEDIUM"
            action = "CONSIDER"
        else:
            tier = "LOW"
            action = "SKIP"
        
        return {
            "total_score": score,
            "tier": tier,
            "action": action,
            "breakdown": breakdown,
        }
    
    def get_spy_change(self) -> Optional[float]:
        """
        Get current SPY daily change
        
        Returns:
            SPY change % or None if unavailable
        """
        if not self.spy_client:
            return None
        
        try:
            # Fetch SPY bars for today
            # (Implementation would go here)
            # For now, return None
            return self.spy_change
        except Exception as e:
            self.logger.error(f"Error fetching SPY: {e}")
            return None
    
    def set_spy_change(self, change: float):
        """Manually set SPY change (for testing or external data)"""
        self.spy_change = change
