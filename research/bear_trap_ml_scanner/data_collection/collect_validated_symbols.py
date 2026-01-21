"""
Bear Trap ML Scanner - Simplified Data Collection for Testing

Instead of scanning the entire market, start with the validated Bear Trap symbols
to build and test the feature extraction pipeline.

Author: Magellan Research Team  
Date: January 21, 2026
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import requests
from typing import List, Dict, Optional
import logging
import time

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Use validated Bear Trap symbols as starting point
VALIDATED_SYMBOLS = [
    'MULN', 'ONDS', 'AMC', 'NKLA', 'WKHS',  # Tier 1
    'ACB', 'SENS', 'BTCS', 'GOEV',           # Extended
    'GME', 'PLUG', 'RIOT', 'MARA', 'TLRY',   # Additional volatiles
]


class SimplifiedDataCollector:
    """Collect intraday data for validated symbols"""
    
    def __init__(self, fmp_api_key: str):
        self.fmp_key = fmp_api_key
        self.fmp_base = "https://financialmodelingprep.com/api/v3"
        self.data_dir = Path(__file__).parent.parent / "data" / "raw"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def get_intraday_bars(self, symbol: str, date: str) -> Optional[pd.DataFrame]:
        """
        Fetch 5-minute bars for a symbol on a specific date
        
        Args:
            symbol: Stock ticker
            date: Date in YYYY-MM-DD format
            
        Returns:
            DataFrame with OHLCV data or None
        """
        url = f"{self.fmp_base}/historical-chart/5min/{symbol}"
        params = {
            'from': date,
            'to': date,
            'apikey': self.fmp_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, list):
                return None
            
            df = pd.DataFrame(data)
            if 'date' in df.columns:
                df['timestamp'] = pd.to_datetime(df['date'])
                df = df.sort_values('timestamp')
                return df
            return None
            
        except Exception as e:
            logger.debug(f"Error fetching {symbol} on {date}: {e}")
            return None
    
    def identify_selloffs_in_day(self, symbol: str, date: str) -> List[Dict]:
        """
        Find all -15%+ selloff events in a trading day
        
        Args:
            symbol: Stock ticker
            date: Date string YYYY-MM-DD
            
        Returns:
            List of selloff event dictionaries
        """
        df = self.get_intraday_bars(symbol, date)
        
        if df is None or len(df) == 0:
            return []
        
        events = []
        
        # Get session open
        if 'open' not in df.columns:
            return []
            
        session_open = df.iloc[0]['open']
        
        # Calculate drop from session open for each bar
        df['drop_from_open_pct'] = ((df['low'] - session_open) / session_open) * 100
        
        # Find bars with -15%+ drops
        selloff_bars = df[df['drop_from_open_pct'] <= -15.0]
        
        for idx, row in selloff_bars.iterrows():
            event = {
                'symbol': symbol,
                'date': date,
                'timestamp': row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'session_open': session_open,
                'low': row['low'],
                'close': row['close'],
                'high': row['high'],
                'volume': row['volume'],
                'drop_pct': row['drop_from_open_pct'],
            }
            events.append(event)
        
        return events
    
    def collect_symbols_over_period(self, symbols: List[str], 
                                    start_date: str, end_date: str) -> pd.DataFrame:
        """
        Collect selloff events for specific symbols over a date range
        
        Args:
            symbols: List of tickers
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD
            
        Returns:
            DataFrame of all selloff events
        """
        logger.info(f"Collecting data for {len(symbols)} symbols")
        logger.info(f"Period: {start_date} to {end_date}")
        
        all_events = []
        
        # Generate business day range
        dates = pd.date_range(start_date, end_date, freq='B')
        
        total_iterations = len(symbols) * len(dates)
        current = 0
        
        for symbol in symbols:
            logger.info(f"\nProcessing {symbol}...")
            symbol_events = 0
            
            for date in dates:
                current += 1
                date_str = date.strftime('%Y-%m-%d')
                
                # Progress indicator
                if current % 10 == 0:
                    logger.info(f"  Progress: {current}/{total_iterations} ({100*current/total_iterations:.1f}%)")
                
                events = self.identify_selloffs_in_day(symbol, date_str)
                
                if events:
                    symbol_events += len(events)
                    all_events.extend(events)
                    logger.info(f"  {date_str}: Found {len(events)} selloff(s)")
                
                # Rate limiting (FMP allows high throughput but be respectful)
                time.sleep(0.02)  # 50 requests/second
            
            logger.info(f"✓ {symbol}: Total {symbol_events} selloffs")
        
        # Convert to DataFrame
        if all_events:
            df = pd.DataFrame(all_events)
            logger.info(f"\n{'='*80}")
            logger.info(f"Collection complete: {len(df)} total selloff events")
            logger.info(f"{'='*80}")
            return df
        else:
            logger.warning("No selloffs found in period")
            return pd.DataFrame()
    
    def save_dataset(self, df: pd.DataFrame, filename: str):
        """Save to CSV"""
        if df.empty:
            logger.warning("Empty dataset, not saving")
            return
            
        filepath = self.data_dir / filename
        df.to_csv(filepath, index=False)
        logger.info(f"💾 Saved to {filepath}")
        logger.info(f"   Size: {len(df)} rows, {df.memory_usage(deep=True).sum() / 1024:.1f} KB")


def main():
    """Test collection with validated symbols"""
    
    fmp_key = os.getenv('FMP_API_KEY')
    
    if not fmp_key:
        logger.error("Missing FMP_API_KEY in .env")
        return
    
    collector = SimplifiedDataCollector(fmp_key)
    
    print("="*80)
    print("BEAR TRAP ML SCANNER - TEST DATA COLLECTION")
    print("Mode: Validated Symbols Only")
    print("="*80)
    
    # Test with 3 months of recent data
    df = collector.collect_symbols_over_period(
        symbols=VALIDATED_SYMBOLS,
        start_date='2024-10-01',
        end_date='2024-12-31'
    )
    
    if not df.empty:
        # Save
        collector.save_dataset(df, 'selloffs_validated_q4_2024.csv')
        
        # Summary
        print("\n" + "="*80)
        print("DATASET SUMMARY")
        print("="*80)
        print(f"Total events: {len(df)}")
        print(f"Unique symbols: {df['symbol'].nunique()}")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"\nDrop % statistics:")
        print(df['drop_pct'].describe())
        print(f"\nTop 10 biggest drops:")
        top10 = df.nsmallest(10, 'drop_pct')[['symbol', 'date', 'timestamp', 'drop_pct', 'low']]
        print(top10.to_string(index=False))
        
        print(f"\nEvents by symbol:")
        symbol_counts = df['symbol'].value_counts()
        print(symbol_counts.to_string())


if __name__ == '__main__':
    main()
