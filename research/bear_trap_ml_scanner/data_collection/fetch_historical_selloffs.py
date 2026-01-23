"""
Bear Trap ML Scanner - Historical Selloff Data Collection

Fetches all instances where small-cap stocks dropped ≥15% intraday
from FMP and Alpaca data sources.

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

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SelloffDataCollector:
    """
    Collects historical selloff data from FMP and Alpaca
    """
    
    def __init__(self, fmp_api_key: str, alpaca_api_key: str, alpaca_secret: str):
        self.fmp_key = fmp_api_key
        self.alpaca_key = alpaca_api_key
        self.alpaca_secret = alpaca_secret
        
        self.fmp_base = "https://financialmodelingprep.com/api/v3"
        self.data_dir = Path(__file__).parent.parent / "data" / "raw"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def get_small_cap_universe(self, min_market_cap: int = 10_000_000, 
                                max_market_cap: int = 5_000_000_000) -> List[str]:
        """
        Get list of small-cap stocks from FMP
        
        Args:
            min_market_cap: Minimum market cap ($10M default)
            max_market_cap: Maximum market cap ($5B default)
            
        Returns:
            List of ticker symbols
        """
        logger.info(f"Fetching small-cap universe (${min_market_cap:,} - ${max_market_cap:,})")
        
        # Use FMP stock screener
        url = f"{self.fmp_base}/stock-screener"
        params = {
            'marketCapMoreThan': min_market_cap,
            'marketCapLowerThan': max_market_cap,
            'limit': 3000,  # Get as many as possible
            'apikey': self.fmp_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            symbols = [stock['symbol'] for stock in data if stock.get('symbol')]
            logger.info(f"Found {len(symbols)} small-cap stocks")
            return symbols
            
        except Exception as e:
            logger.error(f"Error fetching small-cap universe: {e}")
            return []
    
    def scan_daily_losers(self, date: str) -> List[Dict]:
        """
        Scan for biggest losers on a specific date using FMP
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of stocks with significant losses
        """
        logger.info(f"Scanning losers for {date}")
        
        # FMP losers endpoint
        url = f"{self.fmp_base}/stock_market/losers"
        params = {'apikey': self.fmp_key}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            losers = response.json()
            
            # Filter for -15%+ drops
            significant_losers = [
                stock for stock in losers 
                if stock.get('changesPercentage', 0) <= -15.0
            ]
            
            logger.info(f"Found {len(significant_losers)} stocks down ≥15%")
            return significant_losers
            
        except Exception as e:
            logger.error(f"Error scanning daily losers: {e}")
            return []
    
    def get_intraday_data(self, symbol: str, date: str) -> Optional[pd.DataFrame]:
        """
        Fetch 5-minute intraday bars for a symbol on a specific date
        
        Args:
            symbol: Stock ticker
            date: Date in YYYY-MM-DD format
            
        Returns:
            DataFrame with OHLCV data
        """
        # Use FMP intraday endpoint
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
            
            if not data:
                return None
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['date'])
            df = df.sort_values('timestamp')
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching intraday data for {symbol}: {e}")
            return None
    
    def identify_selloffs(self, symbol: str, date: str) -> List[Dict]:
        """
        Identify all -15% selloff events for a symbol on a given date
        
        Args:
            symbol: Stock ticker
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of selloff events with metadata
        """
        df = self.get_intraday_data(symbol, date)
        
        if df is None or len(df) == 0:
            return []
        
        selloffs = []
        
        # Get session open (first bar)
        session_open = df.iloc[0]['open']
        
        # Calculate intraday drop from session open
        df['drop_from_open'] = ((df['low'] - session_open) / session_open) * 100
        
        # Find bars where drop ≥ -15%
        selloff_bars = df[df['drop_from_open'] <= -15.0]
        
        for _, row in selloff_bars.iterrows():
            selloff = {
                'symbol': symbol,
                'date': date,
                'timestamp': row['timestamp'],
                'session_open': session_open,
                'low_price': row['low'],
                'close_price': row['close'],
                'volume': row['volume'],
                'drop_pct': row['drop_from_open'],
            }
            selloffs.append(selloff)
        
        if selloffs:
            logger.info(f"  {symbol}: Found {len(selloffs)} selloff events")
        
        return selloffs
    
    def collect_date_range(self, start_date: str, end_date: str, 
                           test_mode: bool = True) -> pd.DataFrame:
        """
        Collect selloff data for a date range
        
        Args:
            start_date: Start date YYYY-MM-DD
            end_date: End date YYYY-MM-DD
            test_mode: If True, only scan top losers; if False, scan full universe
            
        Returns:
            DataFrame with all selloff events
        """
        logger.info(f"Collecting data from {start_date} to {end_date}")
        logger.info(f"Mode: {'TEST (losers only)' if test_mode else 'FULL (entire universe)'}")
        
        all_selloffs = []
        
        # Generate date range
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        date_range = pd.date_range(start, end, freq='B')  # Business days only
        
        for date in date_range:
            date_str = date.strftime('%Y-%m-%d')
            logger.info(f"\n--- Processing {date_str} ---")
            
            if test_mode:
                # Quick scan: Just check daily losers
                losers = self.scan_daily_losers(date_str)
                symbols_to_check = [stock['symbol'] for stock in losers[:50]]  # Top 50
            else:
                # Full scan: Check entire universe
                symbols_to_check = self.get_small_cap_universe()
            
            # Check each symbol for intraday selloffs
            for symbol in symbols_to_check:
                selloffs = self.identify_selloffs(symbol, date_str)
                all_selloffs.extend(selloffs)
            
            logger.info(f"Total selloffs found so far: {len(all_selloffs)}")
        
        # Convert to DataFrame
        if all_selloffs:
            df = pd.DataFrame(all_selloffs)
            logger.info(f"\n✅ Collection complete: {len(df)} selloff events")
            return df
        else:
            logger.warning("No selloffs found!")
            return pd.DataFrame()
    
    def save_dataset(self, df: pd.DataFrame, filename: str):
        """Save dataset to CSV"""
        filepath = self.data_dir / filename
        df.to_csv(filepath, index=False)
        logger.info(f"💾 Saved dataset to {filepath}")


def main():
    """Test data collection for January 2025"""
    
    # Get API keys (using APCA prefix for Alpaca as in .env)
    fmp_key = os.getenv('FMP_API_KEY')
    alpaca_key = os.getenv('APCA_API_KEY_ID')
    alpaca_secret = os.getenv('APCA_API_SECRET_KEY')
    
    if not all([fmp_key, alpaca_key, alpaca_secret]):
        logger.error("Missing API keys! Set FMP_API_KEY, APCA_API_KEY_ID, APCA_API_SECRET_KEY in .env")
        return
    
    # Initialize collector
    collector = SelloffDataCollector(fmp_key, alpaca_key, alpaca_secret)
    
    # Test collection: Q4 2024 (more market volatility expected)
    logger.info("=" * 80)
    logger.info("BEAR TRAP ML SCANNER - TEST DATA COLLECTION")
    logger.info("Testing with Q4 2024 data (Oct-Dec)")
    logger.info("=" * 80)
    
    df = collector.collect_date_range(
        start_date='2024-10-01',
        end_date='2024-12-31',
        test_mode=True  # Only scan top losers for speed
    )
    
    if not df.empty:
        # Save dataset
        collector.save_dataset(df, 'selloffs_test_q4_2024.csv')
        
        # Print summary stats
        print("\n" + "=" * 80)
        print("DATASET SUMMARY")
        print("=" * 80)
        print(f"Total selloff events: {len(df)}")
        print(f"Unique symbols: {df['symbol'].nunique()}")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"\nDrop % distribution:")
        print(df['drop_pct'].describe())
        print(f"\nTop 10 biggest drops:")
        print(df.nsmallest(10, 'drop_pct')[['symbol', 'date', 'drop_pct', 'low_price']])
    

if __name__ == '__main__':
    main()
