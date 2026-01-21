"""
Bear Trap ML Scanner - Data Collection via Alpaca API

Collects historical intraday bar data using Alpaca Market Data Plus
to identify all -15%+ selloff events for Bear Trap candidates.

Author: Magellan Research Team
Date: January 21, 2026
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict
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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Validated Bear Trap symbols
VALIDATED_SYMBOLS = [
    'MULN', 'ONDS', 'AMC', 'NKLA', 'WKHS',  # Tier 1
    'ACB', 'SENS', 'BTCS', 'GOEV',           # Extended
    'GME', 'PLUG', 'RIOT', 'MARA', 'TLRY',   # Additional volatiles
]


class AlpacaSelloffCollector:
    """Collect selloff data using Alpaca historical API"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.client = StockHistoricalDataClient(api_key, api_secret)
        self.data_dir = Path(__file__).parent.parent / "data" / "raw"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def get_daily_bars(self, symbol: str, date: datetime) -> pd.DataFrame:
        """
        Fetch 5-minute bars for a symbol on a specific date
        
        Args:
            symbol: Stock ticker
            date: datetime object for the trading day
            
        Returns:
            DataFrame with OHLCV data
        """
        # Set time range for the trading day (9:30 AM - 4:00 PM ET)
        start = date.replace(hour=9, minute=30, second=0, microsecond=0)
        end = date.replace(hour=16, minute=0, second=0, microsecond=0)
        
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Minute,  # Use 1-min for precision
            start=start,
            end=end,
            feed='sip'  # Market Data Plus feed
        )
        
        try:
            bars = self.client.get_stock_bars(request)
            
            if not bars or symbol not in bars.data:
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for bar in bars.data[symbol]:
                data.append({
                    'timestamp': bar.timestamp,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume,
                })
            
            df = pd.DataFrame(data)
            if not df.empty:
                df = df.sort_values('timestamp').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            logger.debug(f"Error fetching {symbol} on {date.date()}: {e}")
            return pd.DataFrame()
    
    def identify_selloffs_in_day(self, symbol: str, date: datetime) -> List[Dict]:
        """
        Find all -15%+ selloff events in a trading day
        
        Args:
            symbol: Stock ticker
            date: datetime object
            
        Returns:
            List of selloff event dictionaries
        """
        df = self.get_daily_bars(symbol, date)
        
        if df.empty:
            return []
        
        events = []
        
        # Get session open (first bar)
        session_open = df.iloc[0]['open']
        
        # Calculate drop from session open
        df['drop_from_open_pct'] = ((df['low'] - session_open) / session_open) * 100
        
        # Find bars with -15%+ drops
        selloff_bars = df[df['drop_from_open_pct'] <= -15.0]
        
        for idx, row in selloff_bars.iterrows():
            event = {
                'symbol': symbol,
                'date': date.strftime('%Y-%m-%d'),
                'timestamp': row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'session_open': float(session_open),
                'low': float(row['low']),
                'close': float(row['close']),
                'high': float(row['high']),
                'volume': int(row['volume']),
                'drop_pct': float(row['drop_from_open_pct']),
            }
            events.append(event)
        
        return events
    
    def collect_date_range(self, symbols: List[str], 
                          start_date: str, end_date: str) -> pd.DataFrame:
        """
        Collect selloff events for symbols over a date range
        
        Args:
            symbols: List of tickers
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD
            
        Returns:
            DataFrame of all selloff events
        """
        logger.info(f"Collecting data for {len(symbols)} symbols")
        logger.info(f"Period: {start_date} to {end_date}")
        logger.info(f"Using Alpaca Market Data Plus (1-min bars)")
        
        all_events = []
        
        # Generate business day range (market trading days)
        dates = pd.date_range(start_date, end_date, freq='B')
        
        total_iterations = len(symbols) * len(dates)
        current = 0
        
        for symbol in symbols:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing {symbol}")
            logger.info(f"{'='*60}")
            symbol_events = 0
            
            for date in dates:
                current += 1
                
                # Progress indicator every 10 iterations
                if current % 10 == 0:
                    pct = 100 * current / total_iterations
                    logger.info(f"  Progress: {current}/{total_iterations} ({pct:.1f}%)")
                
                events = self.identify_selloffs_in_day(symbol, date)
                
                if events:
                    symbol_events += len(events)
                    all_events.extend(events)
                    logger.info(f"  {date.strftime('%Y-%m-%d')}: Found {len(events)} selloff(s) ⚡")
                
                # Small delay to be respectful to API
                time.sleep(0.1)
            
            logger.info(f"✓ {symbol}: Total {symbol_events} selloff events")
        
        # Convert to DataFrame
        if all_events:
            df = pd.DataFrame(all_events)
            logger.info(f"\n{'='*80}")
            logger.info(f"✅ Collection complete: {len(df)} total selloff events")
            logger.info(f"{'='*80}")
            return df
        else:
            logger.warning(f"\n{'='*80}")
            logger.warning("⚠️  No selloffs found in period")
            logger.warning(f"{'='*80}")
            return pd.DataFrame()
    
    def save_dataset(self, df: pd.DataFrame, filename: str):
        """Save dataset to CSV"""
        if df.empty:
            logger.warning("Empty dataset, not saving")
            return
        
        filepath = self.data_dir / filename
        df.to_csv(filepath, index=False)
        
        size_kb = df.memory_usage(deep=True).sum() / 1024
        logger.info(f"\n💾 Dataset saved:")
        logger.info(f"   File: {filepath}")
        logger.info(f"   Rows: {len(df):,}")
        logger.info(f"   Size: {size_kb:.1f} KB")


def main():
    """Collect test dataset using Alpaca API"""
    
    # Get API credentials
    api_key = os.getenv('APCA_API_KEY_ID')
    api_secret = os.getenv('APCA_API_SECRET_KEY')
    
    if not all([api_key, api_secret]):
        logger.error("Missing Alpaca API keys! Set APCA_API_KEY_ID and APCA_API_SECRET_KEY in .env")
        return
    
    # Initialize collector
    collector = AlpacaSelloffCollector(api_key, api_secret)
    
    print("\n" + "="*80)
    print("BEAR TRAP ML SCANNER - DATA COLLECTION")
    print("Data Source: Alpaca Market Data Plus")
    print("Resolution: 1-minute bars")
    print("="*80 + "\n")
    
    # Collect Q4 2024 data  
    df = collector.collect_date_range(
        symbols=VALIDATED_SYMBOLS,
        start_date='2024-10-01',
        end_date='2024-12-31'
    )
    
    if not df.empty:
        # Save dataset
        collector.save_dataset(df, 'selloffs_alpaca_q4_2024.csv')
        
        # Print summary statistics
        print("\n" + "="*80)
        print("DATASET SUMMARY")
        print("="*80)
        print(f"Total selloff events: {len(df):,}")
        print(f"Unique symbols: {df['symbol'].nunique()}")
        print(f"Unique dates: {df['date'].nunique()}")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        
        print(f"\n📊 Drop % Distribution:")
        print(df['drop_pct'].describe())
        
        print(f"\n🔥 Top 10 Biggest Drops:")
        top10 = df.nsmallest(10, 'drop_pct')[['symbol', 'date', 'timestamp', 'drop_pct', 'low']]
        print(top10.to_string(index=False))
        
        print(f"\n📈 Events by Symbol:")
        symbol_counts = df['symbol'].value_counts().sort_index()
        for symbol, count in symbol_counts.items():
            pct = 100 * count / len(df)
            print(f"  {symbol:6} {count:4} events ({pct:5.1f}%)")
        
        print("\n" + "="*80)
        print("✅ Data collection successful!")
        print("="*80 + "\n")
    else:
        print("\n" + "="*80)
        print("⚠️  RESULT: No -15% selloffs found in Q4 2024")
        print("="*80)
        print("\nPossible reasons:")
        print("1. Q4 2024 was a strong bull market (low volatility)")
        print("2. These specific symbols didn't experience extreme selloffs")
        print("\nRecommendations:")
        print("- Try earlier periods: 2022 (bear market), 2023 (choppy)")
        print("- Lower threshold temporarily to -10% for testing")
        print("- Expand symbol universe")
        print("="*80 + "\n")


if __name__ == '__main__':
    main()
