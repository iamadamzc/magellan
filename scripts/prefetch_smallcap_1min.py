"""
Small-Cap 1-Minute Data Prefetch for Scalping Strategies
----------------------------------------------------------
Fetches and caches 1-minute intraday data for small-cap momentum scalping.

This is separate from the main prefetch script because:
1. 1-minute data is MUCH larger (100K+ bars per symbol per year)
2. Only needed for scalping strategies (E, F, G)
3. Different API endpoints and rate limits

Run this AFTER prefetch_all_data.py completes.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache
import time

# Small-cap universe for scalping strategies
# Based on SMALL_CAP_SCALPING_STRATEGIES.md
SMALL_CAPS = [
    'RIOT',  # High volume crypto miner
    'MARA',  # High volume crypto miner
    'PLUG',  # High volume hydrogen play
    'AMC',   # Meme stock (high RVOL)
    'GME',   # Meme stock (high RVOL)
    'SAVA',  # Biotech (high volatility)
    'SOFI',  # Fintech (high volume)
]

# Test periods for scalping (shorter, more recent)
# 1-minute data is HUGE - we only cache recent periods
PERIODS = [
    ('Recent', '2024-11-01', '2025-01-17'),  # Nov 2024 - Jan 2025 (Primary)
    ('Older', '2024-04-01', '2024-06-30'),   # Apr - Jun 2024 (Secondary)
]

def main():
    print("="*80)
    print("SMALL-CAP 1-MINUTE DATA PREFETCH")
    print("="*80)
    print(f"Symbols: {len(SMALL_CAPS)} small-caps")
    print(f"Periods: {len(PERIODS)} periods")
    print(f"Total: {len(SMALL_CAPS) * len(PERIODS)} datasets")
    print("="*80)
    print("\n⚠️  WARNING: 1-minute data is LARGE (100K+ bars per symbol)")
    print("⚠️  This will take 10-30 minutes due to API rate limits")
    print("⚠️  Expected cache size: ~500 MB - 1 GB")
    print("="*80)
    
    response = input("\nProceed with prefetch? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return
    
    total_fetched = 0
    total_bars = 0
    
    print("\n[1/1] FETCHING 1-MINUTE EQUITY DATA")
    print("-"*80)
    
    for symbol in SMALL_CAPS:
        for period_name, start, end in PERIODS:
            try:
                print(f"Fetching {symbol:6} {period_name:10}...", end=" ", flush=True)
                df = cache.get_or_fetch_equity(symbol, '1min', start, end)
                print(f"✓ {len(df):6} bars")
                total_fetched += 1
                total_bars += len(df)
                
                # Rate limit protection (FMP free tier: 250 calls/day, ~5 calls/sec)
                # Sleep 1 second between calls to be safe
                time.sleep(1)
                
            except Exception as e:
                print(f"✗ ERROR: {e}")
    
    print("\n" + "="*80)
    print("PREFETCH COMPLETE")
    print("="*80)
    print(f"Total datasets fetched: {total_fetched}")
    print(f"Total bars cached: {total_bars:,}")
    print(f"All data cached in: data/cache/equities/")
    print("\nYou can now run scalping strategy backtests offline!")
    print("\nNext step: Build Strategy E (VWAP Reclaim)")

if __name__ == "__main__":
    main()
