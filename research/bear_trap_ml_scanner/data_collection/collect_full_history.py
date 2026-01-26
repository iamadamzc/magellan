"""
Bear Trap ML Scanner - FULL Historical Data Collection

Collects ALL available selloff events across multiple years
Uses Alpaca API with high throughput

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


class FullDataCollector:
    """Collect maximum historical selloff data"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.client = StockHistoricalDataClient(api_key, api_secret)
        self.data_dir = Path(__file__).parent.parent / "data" / "raw"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def get_daily_bars(self, symbol: str, date: datetime) -> pd.DataFrame:
        """Fetch 1-minute bars for a trading day"""
        start = date.replace(hour=9, minute=30, second=0, microsecond=0)
        end = date.replace(hour=16, minute=0, second=0, microsecond=0)
        
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Minute,
            start=start,
            end=end,
            feed='sip'
        )
        
        try:
            bars = self.client.get_stock_bars(request)
            
            if not bars or symbol not in bars.data:
                return pd.DataFrame()
            
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
        """Find all -15%+ selloffs in a day"""
        df = self.get_daily_bars(symbol, date)
        
        if df.empty:
            return []
        
        events = []
        session_open = df.iloc[0]['open']
        df['drop_from_open_pct'] = ((df['low'] - session_open) / session_open) * 100
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
    
    def collect_year(self, symbols: List[str], year: int) -> pd.DataFrame:
        """
        Collect all selloffs for a full year
        
        Args:
            symbols: List of tickers
            year: Year to collect (e.g., 2024)
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"COLLECTING YEAR {year}")
        logger.info(f"{'='*80}")
        
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        all_events = []
        dates = pd.date_range(start_date, end_date, freq='B')  # Business days
        
        total_iterations = len(symbols) * len(dates)
        current = 0
        
        start_time = time.time()
        
        for symbol in symbols:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing {symbol} ({year})")
            logger.info(f"{'='*60}")
            symbol_events = 0
            
            for date in dates:
                current += 1
                
                # Progress every 25 iterations
                if current % 25 == 0:
                    elapsed = time.time() - start_time
                    rate = current / elapsed if elapsed > 0 else 0
                    eta_seconds = (total_iterations - current) / rate if rate > 0 else 0
                    eta_minutes = eta_seconds / 60
                    
                    pct = 100 * current / total_iterations
                    logger.info(f"  Progress: {current}/{total_iterations} ({pct:.1f}%) | "
                              f"Rate: {rate:.1f} it/s | ETA: {eta_minutes:.1f}m")
                
                events = self.identify_selloffs_in_day(symbol, date)
                
                if events:
                    symbol_events += len(events)
                    all_events.extend(events)
                    logger.info(f"  {date.strftime('%Y-%m-%d')}: Found {len(events)} selloff(s) ⚡")
                
                # Minimal delay (3000 CPM = 50 per second)
                time.sleep(0.02)
            
            logger.info(f"✓ {symbol}: Total {symbol_events} selloffs in {year}")
        
        if all_events:
            df = pd.DataFrame(all_events)
            logger.info(f"\n{'='*80}")
            logger.info(f"✅ Year {year} complete: {len(df)} selloff events")
            logger.info(f"{'='*80}")
            return df
        else:
            logger.warning(f"⚠️  No selloffs found in {year}")
            return pd.DataFrame()
    
    def collect_multi_year(self, symbols: List[str], years: List[int]) -> pd.DataFrame:
        """Collect data across multiple years"""
        
        all_data = []
        
        for year in years:
            year_df = self.collect_year(symbols, year)
            if not year_df.empty:
                all_data.append(year_df)
        
        if all_data:
            combined = pd.concat(all_data, ignore_index=True)
            logger.info(f"\n{'='*80}")
            logger.info(f"🎉 MULTI-YEAR COLLECTION COMPLETE")
            logger.info(f"{'='*80}")
            logger.info(f"Total events: {len(combined):,}")
            logger.info(f"Years: {years}")
            logger.info(f"Symbols: {len(symbols)}")
            logger.info(f"Date range: {combined['date'].min()} to {combined['date'].max()}")
            return combined
        else:
            return pd.DataFrame()
    
    def save_dataset(self, df: pd.DataFrame, filename: str):
        """Save to CSV"""
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
    """Collect MAXIMUM historical data"""
    
    alpaca_key = os.getenv('APCA_API_KEY_ID')
    alpaca_secret = os.getenv('APCA_API_SECRET_KEY')
    
    if not all([alpaca_key, alpaca_secret]):
        logger.error("Missing Alpaca API keys!")
        return
    
    collector = FullDataCollector(alpaca_key, alpaca_secret)
    
    print("\n" + "="*80)
    print("BEAR TRAP ML SCANNER - FULL HISTORICAL COLLECTION")
    print("Data Source: Alpaca Market Data Plus (3000 CPM)")
    print("Resolution: 1-minute bars")
    print("="*80 + "\n")
    
    # Collect 2024, 2023, 2022
    years = [2024, 2023, 2022]
    
    df = collector.collect_multi_year(VALIDATED_SYMBOLS, years)
    
    if not df.empty:
        # Save
        collector.save_dataset(df, 'selloffs_full_2022_2024.csv')
        
        # Summary stats
        print("\n" + "="*80)
        print("DATASET SUMMARY")
        print("="*80)
        print(f"Total events: {len(df):,}")
        print(f"Unique symbols: {df['symbol'].nunique()}")
        print(f"Unique dates: {df['date'].nunique()}")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        
        print(f"\n📊 Drop % Distribution:")
        print(df['drop_pct'].describe())
        
        print(f"\n📈 Events by Symbol:")
        symbol_counts = df['symbol'].value_counts().sort_index()
        for symbol, count in symbol_counts.items():
            pct = 100 * count / len(df)
            print(f"  {symbol:6} {count:5} events ({pct:5.1f}%)")
        
        print(f"\n📅 Events by Year:")
        df['year'] = pd.to_datetime(df['date']).dt.year
        yearly = df.groupby('year').size()
        for year, count in yearly.items():
            print(f"  {year}: {count:5} events")
        
        print("\n" + "="*80)
        print("✅ FULL COLLECTION COMPLETE!")
        print("="*80 + "\n")


if __name__ == '__main__':
    main()
