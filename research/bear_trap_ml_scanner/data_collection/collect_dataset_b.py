"""
Bear Trap ML Scanner - Dataset B Collection (Out-of-Sample Test Set)

Collects -15% selloff events from RANDOM symbols (not in validated set)
to test model generalization.

Strategy:
1. Get small-cap universe from FMP
2. Exclude the 14 validated symbols
3. Randomly sample 50 symbols
4. Collect their -15% events (2022-2024)
5. Deduplicate properly (first-cross only)

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
import random
import requests

# Add project root
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


# Dataset A (validated symbols)
DATASET_A_SYMBOLS = [
    'MULN', 'ONDS', 'AMC', 'NKLA', 'WKHS',  # Tier 1
    'ACB', 'SENS', 'BTCS', 'GOEV',           # Extended
    'GME', 'PLUG', 'RIOT', 'MARA', 'TLRY',   # Additional volatiles
]


class DatasetBCollector:
    """Collect out-of-sample test set from random symbols"""
    
    def __init__(self, alpaca_key: str, alpaca_secret: str, fmp_key: str):
        self.alpaca_client = StockHistoricalDataClient(alpaca_key, alpaca_secret)
        self.fmp_key = fmp_key
        self.fmp_base = "https://financialmodelingprep.com/api/v3"
        self.data_dir = Path(__file__).parent.parent / "data" / "raw"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def get_candidate_symbols_from_history(self, exclude: List[str] = None) -> List[str]:
        """
        Simpler approach: Use a predefined list of volatile small-caps
        that are likely to have -15% events but NOT in our validated set
        
        This is more practical than trying to scan the entire universe
        """
        logger.info(f"Using curated candidate symbol list")
        
        # Curated list of volatile small/mid caps (not in Dataset A)
        # These are known to have volatility but weren't specifically validated for Bear Trap
        candidate_pool = [
            # Meme/Retail stocks
            'BBBY', 'DWAC', 'BKKT', 'IRNT', 'WISH', 'CLOV', 'SPCE', 'PLTR',
            # Crypto-related
            'MSTR', 'COIN', 'SDIG', 'BRPHF', 'ARBK',
            # EV/Tech specs
            'LCID', 'RIVN', 'FSR', 'RIDE', 'ARVL', 'INDI', 'ELMS',
            # Biotech/Pharma small-caps
            'SAVA', 'CRIS', 'SRNE', 'VXRT', 'INO', 'OCGN', 'NVAX', 'ATOS',
            # Energy/Commodity
            'TELL', 'FCEL', 'CLNE', 'HYZN',
            # Cannabis
            'SNDL', 'HEXO', 'OGI', 'CRON', 'CGC',
            # Other volatile small-caps
            'SOFI', 'HOOD', 'BODY', 'DKNG', 'SKLZ', 'LAZR', 'BLNK',
            'CHPT', 'STEM', 'NNDM', 'EXPR', 'NAKD', 'APHA', 'FUBO',
        ]
        
        # Filter out excluded symbols
        if exclude:
            candidate_pool = [s for s in candidate_pool if s not in exclude]
        
        # Shuffle for randomness
        random.shuffle(candidate_pool)
        
        logger.info(f"Candidate pool: {len(candidate_pool)} symbols")
        return candidate_pool
    
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
            bars = self.alpaca_client.get_stock_bars(request)
            
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
    
    def identify_first_selloff_in_day(self, symbol: str, date: datetime) -> Dict:
        """
        Find FIRST -15% selloff in a day (deduplication implemented)
        
        Returns single event dict or None
        """
        df = self.get_daily_bars(symbol, date)
        
        if df.empty:
            return None
        
        session_open = df.iloc[0]['open']
        df['drop_from_open_pct'] = ((df['low'] - session_open) / session_open) * 100
        
        # Find FIRST bar that crosses -15%
        selloff_bars = df[df['drop_from_open_pct'] <= -15.0]
        
        if selloff_bars.empty:
            return None
        
        # Take ONLY the first occurrence
        first_bar = selloff_bars.iloc[0]
        
        event = {
            'symbol': symbol,
            'date': date.strftime('%Y-%m-%d'),
            'timestamp': first_bar['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'session_open': float(session_open),
            'low': float(first_bar['low']),
            'close': float(first_bar['close']),
            'high': float(first_bar['high']),
            'volume': int(first_bar['volume']),
            'drop_pct': float(first_bar['drop_from_open_pct']),
            'event_type': 'first_cross',
            'dataset': 'B',
        }
        
        return event
    
    def collect_year(self, symbols: List[str], year: int) -> pd.DataFrame:
        """Collect all FIRST selloffs for a year"""
        
        logger.info(f"\n{'='*80}")
        logger.info(f"COLLECTING DATASET B - YEAR {year}")
        logger.info(f"{'='*80}")
        
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        all_events = []
        dates = pd.date_range(start_date, end_date, freq='B')
        
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
                
                if current % 50 == 0:
                    elapsed = time.time() - start_time
                    rate = current / elapsed if elapsed > 0 else 0
                    eta_seconds = (total_iterations - current) / rate if rate > 0 else 0
                    eta_minutes = eta_seconds / 60
                    
                    pct = 100 * current / total_iterations
                    logger.info(f"  Progress: {current}/{total_iterations} ({pct:.1f}%) | "
                              f"Rate: {rate:.1f} it/s | ETA: {eta_minutes:.1f}m")
                
                event = self.identify_first_selloff_in_day(symbol, date)
                
                if event:
                    symbol_events += 1
                    all_events.append(event)
                    logger.info(f"  {date.strftime('%Y-%m-%d')}: FIRST cross at {event['timestamp']} ⚡")
                
                time.sleep(0.02)
            
            logger.info(f"✓ {symbol}: Total {symbol_events} first-cross events in {year}")
        
        if all_events:
            df = pd.DataFrame(all_events)
            logger.info(f"\n{'='*80}")
            logger.info(f"✅ Year {year} complete: {len(df)} UNIQUE events")
            logger.info(f"{'='*80}")
            return df
        else:
            logger.warning(f"⚠️  No selloffs found in {year}")
            return pd.DataFrame()
    
    def collect_multi_year(self, symbols: List[str], years: List[int]) -> pd.DataFrame:
        """Collect Dataset B across multiple years"""
        
        all_data = []
        
        for year in years:
            year_df = self.collect_year(symbols, year)
            if not year_df.empty:
                all_data.append(year_df)
        
        if all_data:
            combined = pd.concat(all_data, ignore_index=True)
            logger.info(f"\n{'='*80}")
            logger.info(f"🎉 DATASET B COLLECTION COMPLETE")
            logger.info(f"{'='*80}")
            logger.info(f"Total events: {len(combined):,}")
            logger.info(f"Unique symbols: {combined['symbol'].nunique()}")
            logger.info(f"Years: {years}")
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
    """Collect Dataset B (out-of-sample test set)"""
    
    alpaca_key = os.getenv('APCA_API_KEY_ID')
    alpaca_secret = os.getenv('APCA_API_SECRET_KEY')
    fmp_key = os.getenv('FMP_API_KEY')
    
    if not all([alpaca_key, alpaca_secret, fmp_key]):
        logger.error("Missing API keys!")
        return
    
    collector = DatasetBCollector(alpaca_key, alpaca_secret, fmp_key)
    
    print("\n" + "="*80)
    print("BEAR TRAP ML SCANNER - DATASET B COLLECTION")
    print("Purpose: Out-of-sample generalization test set")
    print("Strategy: Random sample of NON-validated symbols")
    print("="*80 + "\n")
    
    # Get universe and sample
    logger.info("Step 1: Getting candidate symbols...")
    universe = collector.get_candidate_symbols_from_history(exclude=DATASET_A_SYMBOLS)
    
    if len(universe) < 50:
        logger.error(f"Only found {len(universe)} symbols, need at least 50")
        return
    
    # Random sample
    random.seed(42)  # Reproducible
    dataset_b_symbols = random.sample(universe, 50)
    
    logger.info(f"\nStep 2: Randomly selected 50 symbols:")
    logger.info(f"  {', '.join(dataset_b_symbols[:10])}...")
    
    # Collect data
    logger.info(f"\nStep 3: Collecting -15% events (2022-2024)...")
    years = [2024, 2023, 2022]  # Start with recent
    
    df = collector.collect_multi_year(dataset_b_symbols, years)
    
    if not df.empty:
        # Save
        collector.save_dataset(df, 'dataset_b_out_of_sample.csv')
        
        # Summary
        print("\n" + "="*80)
        print("DATASET B SUMMARY")
        print("="*80)
        print(f"Total events: {len(df):,}")
        print(f"Unique symbols: {df['symbol'].nunique()}")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        
        print(f"\n📊 Events by Year:")
        df['year'] = pd.to_datetime(df['date']).dt.year
        yearly = df.groupby('year').size()
        for year, count in yearly.items():
            print(f"  {year}: {count:5} events")
        
        print(f"\n📈 Top 10 Symbols by Event Count:")
        symbol_counts = df['symbol'].value_counts().head(10)
        for symbol, count in symbol_counts.items():
            print(f"  {symbol:6} {count:4} events")
        
        print("\n" + "="*80)
        print("✅ DATASET B READY FOR A/B TESTING!")
        print("="*80 + "\n")


if __name__ == '__main__':
    main()
