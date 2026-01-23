"""
WebSocket Streaming Scanner - Real-Time Selloff Detection

Uses Alpaca WebSocket to receive real-time 1-minute bar updates.
Detects selloffs instantly as they cross the -10% threshold.
Zero polling overhead, sub-second latency.
"""

import logging
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional, Callable
import pytz
from collections import defaultdict

from alpaca.data.live import StockDataStream
from alpaca.data.models import Bar

from .selloff_detector import SelloffEvent
from .priority_scorer import PriorityScorer
from .alert_manager import AlertManager


class WebSocketScanner:
    """Real-time selloff scanner using WebSocket streaming"""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        symbols: List[str],
        threshold_pct: float = -10.0,
        time_filter: Optional[tuple] = None,
        scorer: Optional[PriorityScorer] = None,
        alert_manager: Optional[AlertManager] = None,
    ):
        """
        Initialize WebSocket scanner
        
        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            symbols: List of symbols to monitor
            threshold_pct: Selloff threshold (e.g., -10.0)
            time_filter: Optional (hour_start, min_start, hour_end, min_end)
            scorer: Optional PriorityScorer instance
            alert_manager: Optional AlertManager instance
        """
        self.logger = logging.getLogger("scanner.websocket")
        self.symbols = symbols
        self.threshold_pct = threshold_pct
        self.time_filter = time_filter
        
        # Components
        self.scorer = scorer or PriorityScorer()
        self.alert_manager = alert_manager or AlertManager()
        
        # WebSocket stream
        self.stream = StockDataStream(api_key, api_secret)
        
        # Track session data for each symbol
        self.session_data: Dict[str, Dict] = defaultdict(lambda: {
            'session_open': None,
            'session_high': None,
            'session_low': None,
            'bars': [],
            'selloff_detected': False,
        })
        
        # Track market hours
        self.et_tz = pytz.timezone('America/New_York')
        
        self.logger.info(f"WebSocketScanner initialized for {len(symbols)} symbols")
        self.logger.info(f"Threshold: {threshold_pct}%")
        if time_filter:
            self.logger.info(f"Time filter: {time_filter[0]}:{time_filter[1]:02d} - {time_filter[2]}:{time_filter[3]:02d}")
    
    async def _handle_bar(self, bar: Bar):
        """
        Handle incoming 1-minute bar
        
        Args:
            bar: Bar object from WebSocket
        """
        symbol = bar.symbol
        data = self.session_data[symbol]
        
        # Initialize session open on first bar
        if data['session_open'] is None:
            data['session_open'] = bar.open
            data['session_high'] = bar.high
            data['session_low'] = bar.low
            self.logger.debug(f"{symbol}: Session open = ${bar.open:.2f}")
        
        # Update session stats
        data['session_high'] = max(data['session_high'], bar.high)
        data['session_low'] = min(data['session_low'], bar.low)
        data['bars'].append(bar)
        
        # Check if already detected selloff today
        if data['selloff_detected']:
            return
        
        # Calculate drop from session open
        drop_pct = ((bar.close - data['session_open']) / data['session_open']) * 100
        
        # Check threshold
        if drop_pct <= self.threshold_pct:
            # Check time filter
            if self.time_filter:
                bar_time = bar.timestamp.astimezone(self.et_tz)
                h_start, m_start, h_end, m_end = self.time_filter
                
                start_time = bar_time.replace(hour=h_start, minute=m_start)
                end_time = bar_time.replace(hour=h_end, minute=m_end)
                
                if not (start_time <= bar_time <= end_time):
                    return
            
            # Selloff detected!
            self._handle_selloff(symbol, bar, drop_pct, data)
    
    def _handle_selloff(self, symbol: str, bar: Bar, drop_pct: float, data: Dict):
        """Handle detected selloff"""
        # Mark as detected (first-cross only)
        data['selloff_detected'] = True
        
        # Determine time bucket
        time_bucket = self._get_time_bucket(bar.timestamp.astimezone(self.et_tz))
        
        # Create event
        event = SelloffEvent(
            symbol=symbol,
            timestamp=bar.timestamp.astimezone(self.et_tz),
            drop_pct=drop_pct,
            session_open=data['session_open'],
            current_price=bar.close,
            session_low=data['session_low'],
            session_high=data['session_high'],
            volume=bar.volume,
            time_bucket=time_bucket,
        )
        
        # Score event
        score_data = self.scorer.score_event(event)
        
        # Send alert
        self.alert_manager.send_alert(event, score_data)
        
        self.logger.info(
            f"🔥 SELLOFF: {symbol} {drop_pct:.1f}% | "
            f"Score: {score_data['total_score']} ({score_data['tier']})"
        )
    
    def _get_time_bucket(self, timestamp: datetime) -> str:
        """Determine time bucket"""
        hour = timestamp.hour
        minute = timestamp.minute
        
        if hour == 9 and minute < 45:
            return "opening"
        elif hour < 11 or (hour == 11 and minute < 30):
            return "morning"
        elif hour < 14:
            return "midday"
        elif hour < 15:
            return "afternoon"
        else:
            return "power_hour"
    
    def reset_daily_tracking(self):
        """Reset session data (call at market open)"""
        self.session_data.clear()
        self.alert_manager.reset_daily()
        self.logger.info("Daily tracking reset")
    
    async def run(self):
        """Start WebSocket streaming"""
        self.logger.info("="*80)
        self.logger.info("Starting WebSocket Scanner")
        self.logger.info(f"Monitoring {len(self.symbols)} symbols")
        self.logger.info("="*80)
        
        # Subscribe to 1-minute bars
        self.stream.subscribe_bars(self._handle_bar, *self.symbols)
        
        # Run stream
        self.logger.info("WebSocket connected - listening for selloffs...")
        await self.stream._run_forever()
    
    def stop(self):
        """Stop WebSocket streaming"""
        self.logger.info("Stopping WebSocket scanner...")
        self.stream.stop()
