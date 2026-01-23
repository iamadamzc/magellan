"""
Selloff Detector - Core Detection Logic

Detects intraday selloff events using 1-minute bar data.
Implements first-cross deduplication and threshold detection.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import pytz

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame


@dataclass
class SelloffEvent:
    """Represents a detected selloff event"""
    symbol: str
    timestamp: datetime
    drop_pct: float
    session_open: float
    current_price: float
    session_low: float
    session_high: float
    volume: int
    time_bucket: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "drop_pct": round(self.drop_pct, 2),
            "session_open": round(self.session_open, 2),
            "current_price": round(self.current_price, 2),
            "session_low": round(self.session_low, 2),
            "session_high": round(self.session_high, 2),
            "volume": self.volume,
            "time_bucket": self.time_bucket,
        }


class SelloffDetector:
    """Detects intraday selloff events"""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        threshold_pct: float = -10.0,
        time_filter: Optional[Tuple[int, int, int, int]] = None,
    ):
        """
        Initialize selloff detector
        
        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            threshold_pct: Selloff threshold (e.g., -10.0 for -10%)
            time_filter: Optional (hour_start, min_start, hour_end, min_end) tuple
                        e.g., (11, 30, 14, 0) for 11:30 AM - 2:00 PM
        """
        self.logger = logging.getLogger("scanner.detector")
        self.data_client = StockHistoricalDataClient(api_key, api_secret)
        self.threshold_pct = threshold_pct
        self.time_filter = time_filter
        
        # Track detected selloffs to avoid duplicates (first-cross only)
        self.detected_today: Dict[str, datetime] = {}
        
        self.logger.info(f"SelloffDetector initialized: threshold={threshold_pct}%")
        if time_filter:
            self.logger.info(f"Time filter: {time_filter[0]}:{time_filter[1]:02d} - {time_filter[2]}:{time_filter[3]:02d}")
    
    def scan_symbol(self, symbol: str) -> Optional[SelloffEvent]:
        """
        Scan a single symbol for selloff
        
        Args:
            symbol: Stock symbol to scan
            
        Returns:
            SelloffEvent if detected, None otherwise
        """
        try:
            # Get today's bars
            et_tz = pytz.timezone('America/New_York')
            now_et = datetime.now(et_tz)
            
            # Market open is 9:30 AM ET
            market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
            
            # Fetch bars from market open to now
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Minute,
                start=market_open,
                end=now_et,
                feed="sip",  # Market Data Plus feed
            )
            
            bars = self.data_client.get_stock_bars(request)
            
            if not bars or not bars.data or symbol not in bars.data:
                return None
            
            bars_list = bars.data[symbol]
            if len(bars_list) < 2:
                return None
            
            # Get session open (first bar)
            session_open = bars_list[0].open
            
            # Check current bar
            current_bar = bars_list[-1]
            current_price = current_bar.close
            drop_pct = ((current_price - session_open) / session_open) * 100
            
            # Check if crosses threshold
            if drop_pct <= self.threshold_pct:
                # Check if already detected today (first-cross only)
                if symbol in self.detected_today:
                    return None
                
                # Check time filter
                if self.time_filter:
                    current_time = current_bar.timestamp.astimezone(et_tz)
                    h_start, m_start, h_end, m_end = self.time_filter
                    
                    start_time = current_time.replace(hour=h_start, minute=m_start)
                    end_time = current_time.replace(hour=h_end, minute=m_end)
                    
                    if not (start_time <= current_time <= end_time):
                        return None
                
                # Calculate session stats
                session_low = min(bar.low for bar in bars_list)
                session_high = max(bar.high for bar in bars_list)
                
                # Determine time bucket
                time_bucket = self._get_time_bucket(current_bar.timestamp.astimezone(et_tz))
                
                # Create event
                event = SelloffEvent(
                    symbol=symbol,
                    timestamp=current_bar.timestamp.astimezone(et_tz),
                    drop_pct=drop_pct,
                    session_open=session_open,
                    current_price=current_price,
                    session_low=session_low,
                    session_high=session_high,
                    volume=current_bar.volume,
                    time_bucket=time_bucket,
                )
                
                # Mark as detected
                self.detected_today[symbol] = current_bar.timestamp
                
                self.logger.info(f"Selloff detected: {symbol} {drop_pct:.1f}% at {current_bar.timestamp}")
                
                return event
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error scanning {symbol}: {e}")
            return None
    
    def scan_universe(self, symbols: List[str]) -> List[SelloffEvent]:
        """
        Scan multiple symbols for selloffs
        
        Args:
            symbols: List of symbols to scan
            
        Returns:
            List of detected selloff events
        """
        events = []
        
        for symbol in symbols:
            event = self.scan_symbol(symbol)
            if event:
                events.append(event)
        
        return events
    
    def reset_daily_tracking(self):
        """Reset daily tracking (call at market open)"""
        self.detected_today.clear()
        self.logger.info("Daily tracking reset")
    
    def _get_time_bucket(self, timestamp: datetime) -> str:
        """Determine time bucket for timestamp"""
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
