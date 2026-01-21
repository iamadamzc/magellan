"""
Bear Trap ML Scanner - Feature Extraction Pipeline

Enriches raw selloff events with ML features:
- Price context (52w high/low, SMAs)
- Volume analysis
- Market regime indicators
- Time-of-day features
- Outcome labels (reversal detection)

Author: Magellan Research Team
Date: January 21, 2026
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
import time

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Extract ML features for each selloff event"""
    
    def __init__(self, alpaca_key: str, alpaca_secret: str, fmp_key: str):
        self.alpaca_client = StockHistoricalDataClient(alpaca_key, alpaca_secret)
        self.fmp_key = fmp_key
        self.fmp_base = "https://financialmodelingprep.com/api/v3"
        
        # Cache to avoid repeated API calls
        self.sma_cache = {}
        self.market_data_cache = {}
        
    def get_historical_daily_data(self, symbol: str, end_date: datetime, 
                                  lookback_days: int = 300) -> pd.DataFrame:
        """
        Get daily bars for SMA and 52-week calculations
        
        Args:
            symbol: Stock ticker
            end_date: End date (the selloff date)
            lookback_days: How many days to fetch (300 = ~1 year)
        """
        cache_key = f"{symbol}_{end_date.date()}"
        
        if cache_key in self.sma_cache:
            return self.sma_cache[cache_key]
        
        start_date = end_date - timedelta(days=lookback_days)
        
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=start_date,
            end=end_date,
            feed='sip'
        )
        
        try:
            bars = self.alpaca_client.get_stock_bars(request)
            
            if not bars or symbol not in bars.data:
                return pd.DataFrame()
            
            data = []
            for bar in bars.data[symbol]:
                data.append({
                    'date': bar.timestamp.date(),
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume,
                })
            
            df = pd.DataFrame(data)
            self.sma_cache[cache_key] = df
            return df
            
        except Exception as e:
            logger.debug(f"Error fetching daily data for {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_price_context(self, symbol: str, current_price: float, 
                                date: datetime) -> Dict:
        """Calculate price context features"""
        
        df = self.get_historical_daily_data(symbol, date)
        
        if df.empty:
            return {
                'pct_from_52w_high': None,
                'pct_from_52w_low': None,
                'price_range_position': None,
                'distance_from_200sma': None,
                'distance_from_50sma': None,
                'distance_from_20sma': None,
                'above_200sma': None,
                'golden_cross': None,
            }
        
        # 52-week high/low (use last 252 trading days)
        recent_df = df.tail(252)
        high_52w = recent_df['high'].max()
        low_52w = recent_df['low'].min()
        
        # SMAs
        df['sma_20'] = df['close'].rolling(20).mean()
        df['sma_50'] = df['close'].rolling(50).mean()
        df['sma_200'] = df['close'].rolling(200).mean()
        
        latest = df.iloc[-1]
        sma_20 = latest['sma_20']
        sma_50 = latest['sma_50']
        sma_200 = latest['sma_200']
        
        features = {
            'pct_from_52w_high': ((current_price - high_52w) / high_52w * 100) if high_52w else None,
            'pct_from_52w_low': ((current_price - low_52w) / low_52w * 100) if low_52w else None,
            'price_range_position': ((current_price - low_52w) / (high_52w - low_52w)) if (high_52w - low_52w) > 0 else None,
            'distance_from_200sma': ((current_price - sma_200) / sma_200 * 100) if pd.notna(sma_200) else None,
            'distance_from_50sma': ((current_price - sma_50) / sma_50 * 100) if pd.notna(sma_50) else None,
            'distance_from_20sma': ((current_price - sma_20) / sma_20 * 100) if pd.notna(sma_20) else None,
            'above_200sma': (current_price > sma_200) if pd.notna(sma_200) else None,
            'golden_cross': (sma_50 > sma_200) if (pd.notna(sma_50) and pd.notna(sma_200)) else None,
        }
        
        return features
    
    def get_market_data(self, date: datetime) -> Dict:
        """Get market regime data for a specific date (SPY, VIX)"""
        
        date_key = date.date()
        
        if date_key in self.market_data_cache:
            return self.market_data_cache[date_key]
        
        # Use Alpaca to get SPY data
        start = date.replace(hour=9, minute=30)
        end = date.replace(hour=16, minute=0)
        
        try:
            request = StockBarsRequest(
                symbol_or_symbols='SPY',
                timeframe=TimeFrame.Day,
                start=date - timedelta(days=2),
                end=date,
                feed='sip'
            )
            
            bars = self.alpaca_client.get_stock_bars(request)
            
            if bars and 'SPY' in bars.data and len(bars.data['SPY']) >= 2:
                latest = bars.data['SPY'][-1]
                prev = bars.data['SPY'][-2]
                
                spy_change = ((latest.close - prev.close) / prev.close) * 100
            else:
                spy_change = None
            
            # VIX would need a separate source or FMP
            # For now, we'll use simple heuristics
            vix_level = None  # TODO: Add VIX data if available
            
            result = {
                'spy_change_day': spy_change,
                'vix_level': vix_level,
            }
            
            self.market_data_cache[date_key] = result
            return result
            
        except Exception as e:
            logger.debug(f"Error fetching market data for {date.date()}: {e}")
            return {'spy_change_day': None, 'vix_level': None}
    
    def calculate_time_features(self, timestamp: datetime) -> Dict:
        """Extract time-of-day features"""
        
        hour = timestamp.hour
        minute = timestamp.minute
        
        # Categorize time of day
        if hour == 9 and minute < 45:
            time_bucket = 'opening'
        elif hour < 11:
            time_bucket = 'morning'
        elif hour < 14:
            time_bucket = 'midday'
        elif hour < 15:
            time_bucket = 'afternoon'
        else:
            time_bucket = 'power_hour'
        
        minutes_since_open = (hour - 9) * 60 + (minute - 30)
        
        return {
            'hour': hour,
            'minute': minute,
            'time_bucket': time_bucket,
            'minutes_since_open': minutes_since_open,
        }
    
    def calculate_reversal_outcome(self, symbol: str, selloff_time: datetime,
                                   selloff_low: float, session_open: float) -> Dict:
        """
        Determine if the selloff reversed and calculate outcome metrics
        
        Args:
            symbol: Stock ticker
            selloff_time: When the -15% breach occurred
            selloff_low: The low price during selloff
            session_open: Session open price
        
        Returns:
            Dict with reversal metrics
        """
        # Get intraday bars for 4 hours after selloff
        end_time = selloff_time + timedelta(hours=4)
        
        # Don't go past market close
        market_close = selloff_time.replace(hour=16, minute=0, second=0)
        if end_time > market_close:
            end_time = market_close
        
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Minute,
            start=selloff_time,
            end=end_time,
            feed='sip'
        )
        
        try:
            bars = self.alpaca_client.get_stock_bars(request)
            
            if not bars or symbol not in bars.data:
                return self._empty_outcome()
            
            # Get all bars after selloff
            data = []
            for bar in bars.data[symbol]:
                data.append({
                    'timestamp': bar.timestamp,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                })
            
            if not data:
                return self._empty_outcome()
            
            df = pd.DataFrame(data)
            
            # Find peak price reached
            peak_price = df['high'].max()
            peak_time = df.loc[df['high'].idxmax(), 'timestamp']
            
            # Calculate recovery metrics
            drop_amount = session_open - selloff_low
            recovery_amount = peak_price - selloff_low
            recovery_pct = (recovery_amount / drop_amount) * 100 if drop_amount > 0 else 0
            
            # Reversal = recovered at least 50% of the drop
            reversed = recovery_pct >= 50.0
            
            # Time to peak
            time_to_peak_minutes = (peak_time - selloff_time).total_seconds() / 60
            
            # Categorize hold time
            if time_to_peak_minutes <= 15:
                hold_time_category = 'fast'
            elif time_to_peak_minutes <= 35:
                hold_time_category = 'standard'
            else:
                hold_time_category = 'slow'
            
            # R-multiple (using selloff_low as entry, session_open - selloff_low * 0.45 as stop)
            entry_price = selloff_low
            stop_distance = drop_amount * 0.45  # Bear Trap uses 0.45 ATR
            profit = peak_price - entry_price
            r_multiple = (profit / stop_distance) if stop_distance > 0 else 0
            
            return {
                'reversed': reversed,
                'recovery_pct': recovery_pct,
                'peak_price': peak_price,
                'time_to_peak_minutes': time_to_peak_minutes,
                'hold_time_category': hold_time_category,
                'r_multiple': r_multiple,
            }
            
        except Exception as e:
            logger.debug(f"Error calculating outcome for {symbol} at {selloff_time}: {e}")
            return self._empty_outcome()
    
    def _empty_outcome(self) -> Dict:
        """Return empty outcome dict"""
        return {
            'reversed': None,
            'recovery_pct': None,
            'peak_price': None,
            'time_to_peak_minutes': None,
            'hold_time_category': None,
            'r_multiple': None,
        }
    
    def extract_features_for_event(self, event: pd.Series, 
                                   calculate_outcomes: bool = True) -> Dict:
        """
        Extract all features for a single selloff event
        
        Args:
            event: Row from selloffs DataFrame
            calculate_outcomes: If True, look forward to determine reversal
        
        Returns:
            Dict of all features
        """
        symbol = event['symbol']
        timestamp = pd.to_datetime(event['timestamp'])
        current_price = event['low']  # Use the low as "current" price at selloff
        
        features = {}
        
        # Basic event data
        features['symbol'] = symbol
        features['date'] = event['date']
        features['timestamp'] = event['timestamp']
        features['drop_pct'] = event['drop_pct']
        features['session_open'] = event['session_open']
        features['low'] = event['low']
        
        # Price context
        logger.debug(f"  Extracting price context for {symbol}")
        price_features = self.calculate_price_context(symbol, current_price, timestamp)
        features.update(price_features)
        
        # Market data
        logger.debug(f"  Extracting market data")
        market_features = self.get_market_data(timestamp)
        features.update(market_features)
        
        # Time features
        logger.debug(f"  Extracting time features")
        time_features = self.calculate_time_features(timestamp)
        features.update(time_features)
        
        # Outcome labels (if requested)
        if calculate_outcomes:
            logger.debug(f"  Calculating reversal outcome")
            outcome_features = self.calculate_reversal_outcome(
                symbol, timestamp, event['low'], event['session_open']
            )
            features.update(outcome_features)
        
        return features
    
    def process_dataset(self, input_csv: Path, output_csv: Path,
                       calculate_outcomes: bool = True):
        """
        Process entire selloff dataset and add features
        
        Args:
            input_csv: Path to raw selloffs CSV
            output_csv: Path to save enriched CSV
            calculate_outcomes: Whether to calculate reversal outcomes
        """
        logger.info("="*80)
        logger.info("FEATURE EXTRACTION PIPELINE")
        logger.info("="*80)
        
        # Load raw data
        df = pd.read_csv(input_csv)
        logger.info(f"Loaded {len(df)} selloff events")
        
        # Extract features for each event
        enriched_events = []
        
        for idx, event in df.iterrows():
            logger.info(f"\nProcessing event {idx+1}/{len(df)}: {event['symbol']} on {event['date']}")
            
            try:
                features = self.extract_features_for_event(event, calculate_outcomes)
                enriched_events.append(features)
                
                # Progress indicator
                if (idx + 1) % 50 == 0:
                    logger.info(f"✓ Progress: {idx+1}/{len(df)} ({100*(idx+1)/len(df):.1f}%)")
                
                # Rate limiting
                time.sleep(0.05)
                
            except Exception as e:
                logger.error(f"Error processing event {idx}: {e}")
                # Add event with None features
                features = event.to_dict()
                enriched_events.append(features)
        
        # Convert to DataFrame
        enriched_df = pd.DataFrame(enriched_events)
        
        # Save
        enriched_df.to_csv(output_csv, index=False)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ Feature extraction complete!")
        logger.info(f"   Input:  {len(df)} events")
        logger.info(f"   Output: {len(enriched_df)} events")
        logger.info(f"   Features: {len(enriched_df.columns)} columns")
        logger.info(f"   Saved to: {output_csv}")
        logger.info(f"{'='*80}\n")


def main():
    """Extract features for Q4 2024 dataset"""
    
    # Get API credentials
    alpaca_key = os.getenv('APCA_API_KEY_ID')
    alpaca_secret = os.getenv('APCA_API_SECRET_KEY')
    fmp_key = os.getenv('FMP_API_KEY')
    
    if not all([alpaca_key, alpaca_secret, fmp_key]):
        logger.error("Missing API keys!")
        return
    
    # Paths
    data_dir = Path(__file__).parent.parent / "data"
    input_file = data_dir / "raw" / "selloffs_alpaca_q4_2024.csv"
    output_file = data_dir / "processed" / "selloffs_with_features_q4_2024.csv"
    
    # Create processed dir
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize extractor
    extractor = FeatureExtractor(alpaca_key, alpaca_secret, fmp_key)
    
    # Process dataset
    extractor.process_dataset(input_file, output_file, calculate_outcomes=True)
    
    # Quick summary
    df = pd.read_csv(output_file)
    print("\n📊 ENRICHED DATASET SUMMARY")
    print("="*80)
    print(f"Total events: {len(df)}")
    print(f"Features: {len(df.columns)}")
    print(f"\nColumn names:")
    for col in df.columns:
        print(f"  - {col}")
    
    if 'reversed' in df.columns:
        # Filter out None values for proper boolean calculation
        valid_reversals = df['reversed'].dropna()
        if len(valid_reversals) > 0:
            reversal_rate = valid_reversals.mean() * 100
            reversed_count = valid_reversals.sum()
            failed_count = len(valid_reversals) - reversed_count
            print(f"\n💡 Reversal rate: {reversal_rate:.1f}%")
            print(f"   Events that reversed: {int(reversed_count)}")
            print(f"   Events that failed: {int(failed_count)}")
            print(f"   Events with no data: {df['reversed'].isna().sum()}")


if __name__ == '__main__':
    main()
