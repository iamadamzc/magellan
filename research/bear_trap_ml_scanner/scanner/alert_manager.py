"""
Alert Manager - Output and Notifications

Manages alert output for detected selloff opportunities.
Supports console, JSON file, and future notification channels.
"""

import json
import logging
from datetime import datetime
from typing import List, Dict
from pathlib import Path

from .selloff_detector import SelloffEvent


class AlertManager:
    """Manages selloff alerts and notifications"""
    
    def __init__(self, output_dir: str = "research/bear_trap_ml_scanner/scanner/alerts"):
        """
        Initialize alert manager
        
        Args:
            output_dir: Directory for alert output files
        """
        self.logger = logging.getLogger("scanner.alerts")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.alerts_today: List[Dict] = []
    
    def send_alert(
        self,
        event: SelloffEvent,
        score_data: Dict,
    ):
        """
        Send alert for selloff event
        
        Args:
            event: SelloffEvent that triggered alert
            score_data: Scoring data from PriorityScorer
        """
        alert = {
            "timestamp": datetime.now().isoformat(),
            "event": event.to_dict(),
            "score": score_data,
        }
        
        self.alerts_today.append(alert)
        
        # Console output
        self._print_console_alert(event, score_data)
        
        # JSON file output
        self._write_json_alert(alert)
    
    def _print_console_alert(self, event: SelloffEvent, score_data: Dict):
        """Print formatted alert to console"""
        tier = score_data["tier"]
        action = score_data["action"]
        score = score_data["total_score"]
        
        # Color codes
        colors = {
            "HIGH": "\033[92m",    # Green
            "MEDIUM": "\033[93m",  # Yellow
            "LOW": "\033[90m",     # Gray
            "RESET": "\033[0m",
        }
        
        color = colors.get(tier, colors["RESET"])
        reset = colors["RESET"]
        
        print(f"\n{color}{'='*80}{reset}")
        print(f"{color}[{tier}] SELLOFF DETECTED - {action}{reset}")
        print(f"{color}{'='*80}{reset}")
        print(f"Symbol:       {event.symbol}")
        print(f"Drop:         {event.drop_pct:.1f}%")
        print(f"Price:        ${event.current_price:.2f} (Open: ${event.session_open:.2f})")
        print(f"Time:         {event.timestamp.strftime('%H:%M:%S')} ({event.time_bucket})")
        print(f"Priority:     {score}/70")
        
        # Score breakdown
        breakdown = score_data["breakdown"]
        print(f"\nScore Breakdown:")
        
        if "time_bucket" in breakdown:
            tb = breakdown["time_bucket"]
            print(f"  Time ({tb['bucket']}): {tb['score']}")
        
        if "market_context" in breakdown:
            mc = breakdown["market_context"]
            print(f"  Market ({mc['label']}, SPY {mc['spy_change']:+.1f}%): {mc['score']}")
        
        if "trend" in breakdown:
            tr = breakdown["trend"]
            print(f"  Trend (above 200 SMA: {tr['above_200sma']}): {tr['score']}")
        
        if "range_position" in breakdown:
            rp = breakdown["range_position"]
            print(f"  Range (position: {rp['position']:.1%}): {rp['score']}")
        
        if "severity" in breakdown:
            sv = breakdown["severity"]
            print(f"  Severity ({sv['drop_pct']:.1f}%): {sv['score']}")
        
        print(f"{color}{'='*80}{reset}\n")
    
    def _write_json_alert(self, alert: Dict):
        """Write alert to JSON file"""
        today = datetime.now().strftime("%Y-%m-%d")
        filepath = self.output_dir / f"alerts_{today}.json"
        
        # Append to daily file
        alerts = []
        if filepath.exists():
            with open(filepath) as f:
                alerts = json.load(f)
        
        alerts.append(alert)
        
        with open(filepath, 'w') as f:
            json.dump(alerts, f, indent=2)
    
    def get_daily_summary(self) -> Dict:
        """Get summary of today's alerts"""
        if not self.alerts_today:
            return {
                "total_alerts": 0,
                "by_tier": {},
                "by_symbol": {},
            }
        
        by_tier = {}
        by_symbol = {}
        
        for alert in self.alerts_today:
            tier = alert["score"]["tier"]
            symbol = alert["event"]["symbol"]
            
            by_tier[tier] = by_tier.get(tier, 0) + 1
            by_symbol[symbol] = by_symbol.get(symbol, 0) + 1
        
        return {
            "total_alerts": len(self.alerts_today),
            "by_tier": by_tier,
            "by_symbol": by_symbol,
        }
    
    def reset_daily(self):
        """Reset daily alerts (call at market open)"""
        self.alerts_today.clear()
        self.logger.info("Daily alerts reset")
