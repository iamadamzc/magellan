"""
Pull 4 years of 1-minute bars from Alpaca and cache to parquet.
Symbols: SPY, QQQ, IWM
Period: 2022-01-01 to 2026-01-24
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
import time

# Load environment from .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Map env variables
if 'ALPACA_API_KEY' in os.environ and 'APCA_API_KEY_ID' not in os.environ:
    os.environ['APCA_API_KEY_ID'] = os.environ['ALPACA_API_KEY']
if 'ALPACA_SECRET_KEY' in os.environ and 'APCA_API_SECRET_KEY' not in os.environ:
    os.environ['APCA_API_SECRET_KEY'] = os.environ['ALPACA_SECRET_KEY']
if 'APCA_API_BASE_URL' not in os.environ:
    os.environ['APCA_API_BASE_URL'] = 'https://paper-api.alpaca.markets'

from alpaca_trade_api.rest import REST, TimeFrame

# Config
SYMBOLS = ['SPY', 'QQQ', 'IWM']
START_DATE = '2022-01-01'
END_DATE = '2026-01-24'
CACHE_DIR = r'a:\1\Magellan\data\cache\equities'

# Chunk by quarter to avoid API timeouts
def get_quarters(start_date: str, end_date: str) -> list:
    """Generate quarterly date ranges."""
    quarters = []
    current = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    while current < end:
        quarter_end = current + timedelta(days=90)
        if quarter_end > end:
            quarter_end = end
        quarters.append((current.strftime('%Y-%m-%d'), quarter_end.strftime('%Y-%m-%d')))
        current = quarter_end + timedelta(days=1)
    
    return quarters


def fetch_1min_bars(api: REST, symbol: str, start: str, end: str) -> pd.DataFrame:
    """Fetch 1-minute bars for a quarter."""
    try:
        bars = api.get_bars(
            symbol=symbol,
            timeframe=TimeFrame.Minute,
            start=start,
            end=end,
            feed='sip'
        ).df
        
        # Ensure timezone-naive UTC
        if bars.index.tz is not None:
            bars.index = bars.index.tz_convert('UTC').tz_localize(None)
        
        return bars
    except Exception as e:
        print(f"    [ERROR] {e}")
        return pd.DataFrame()


def main():
    print("=" * 70)
    print("PULLING 4-YEAR 1-MINUTE BARS FROM ALPACA")
    print(f"Symbols: {', '.join(SYMBOLS)}")
    print(f"Period: {START_DATE} to {END_DATE}")
    print("=" * 70)
    
    # Initialize API
    api = REST(base_url='https://data.alpaca.markets')
    print("[OK] Connected to Alpaca Data API")
    
    quarters = get_quarters(START_DATE, END_DATE)
    print(f"[INFO] Splitting into {len(quarters)} quarters to avoid timeouts")
    
    for symbol in SYMBOLS:
        print(f"\n{'='*70}")
        print(f"SYMBOL: {symbol}")
        print("=" * 70)
        
        all_bars = []
        
        for i, (q_start, q_end) in enumerate(quarters):
            print(f"  [{i+1}/{len(quarters)}] Fetching {q_start} to {q_end}...", end=" ", flush=True)
            
            bars = fetch_1min_bars(api, symbol, q_start, q_end)
            
            if len(bars) > 0:
                all_bars.append(bars)
                print(f"{len(bars):,} bars")
            else:
                print("0 bars (may be weekend/holiday)")
            
            # Rate limit protection
            time.sleep(0.5)
        
        if all_bars:
            # Concatenate and dedupe
            combined = pd.concat(all_bars)
            combined = combined[~combined.index.duplicated(keep='last')]
            combined = combined.sort_index()
            
            # Save to cache
            filename = f"{symbol}_1min_20220101_20260124.parquet"
            filepath = os.path.join(CACHE_DIR, filename)
            combined.to_parquet(filepath)
            
            print(f"\n[{symbol}] TOTAL: {len(combined):,} bars saved to {filename}")
            print(f"[{symbol}] Date range: {combined.index[0]} to {combined.index[-1]}")
        else:
            print(f"\n[{symbol}] ERROR: No data fetched!")
    
    print("\n" + "=" * 70)
    print("DATA PULL COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    main()
