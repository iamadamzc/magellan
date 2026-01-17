"""
Expanded Small-Cap 1-Minute Data Prefetch
------------------------------------------
Fetches missing 1-minute data for expanded universe and Apr-Jun 2025 period.

Based on user's cached daily data, selecting best scalping candidates.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache
import time

# Expanded small-cap universe (best scalping candidates from user's list)
EXPANDED_UNIVERSE = [
    # Original 7 (already have 2 periods)
    'RIOT', 'MARA', 'PLUG', 'AMC', 'GME', 'SAVA', 'SOFI',
    
    # High-priority additions (high volume, good for scalping)
    'HOOD',  # Robinhood - fintech, high volume
    'LCID',  # Lucid - EV, high RVOL
    'CLSK',  # CleanSpark - crypto miner, high volume
    'DKNG',  # DraftKings - sports betting, high volume
    'TLRY',  # Tilray - cannabis, high volatility
    'SNDL',  # Sundial - cannabis, high RVOL
    'BBBY',  # Bed Bath & Beyond - meme stock (if still trading)
    
    # Medium-priority additions
    'PENN',  # Penn Gaming - sports betting
    'CGC',   # Canopy Growth - cannabis
    'WKHS',  # Workhorse - EV
    'FCEL',  # FuelCell - clean energy
    'SPCE',  # Virgin Galactic - space
]

# Periods to fetch
PERIODS = [
    ('Recent', '2024-11-01', '2025-01-17'),   # Already have for original 7
    ('Middle', '2025-04-01', '2025-06-30'),   # NEW - need for all symbols
    ('Older', '2024-04-01', '2024-06-30'),    # Already have for original 7
]

def main():
    print("="*80)
    print("EXPANDED SMALL-CAP 1-MINUTE DATA PREFETCH")
    print("="*80)
    print(f"Symbols: {len(EXPANDED_UNIVERSE)} small-caps")
    print(f"Periods: {len(PERIODS)} periods")
    print("="*80)
    
    # Calculate what we need to fetch
    original_7 = ['RIOT', 'MARA', 'PLUG', 'AMC', 'GME', 'SAVA', 'SOFI']
    new_symbols = [s for s in EXPANDED_UNIVERSE if s not in original_7]
    
    print(f"\nOriginal 7 symbols: {len(original_7)}")
    print(f"New symbols: {len(new_symbols)}")
    print(f"\nNew symbols: {', '.join(new_symbols)}")
    
    print("\n" + "="*80)
    print("FETCHING STRATEGY")
    print("="*80)
    print("1. Fetch Apr-Jun 2025 (Middle) for ALL symbols (original 7 + new)")
    print("2. Fetch Recent + Older periods for NEW symbols only")
    print("="*80)
    
    response = input("\nProceed with prefetch? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return
    
    total_fetched = 0
    total_bars = 0
    errors = []
    
    print("\n[1/2] FETCHING MIDDLE PERIOD (Apr-Jun 2025) FOR ALL SYMBOLS")
    print("-"*80)
    
    # Fetch Middle period for ALL symbols
    for symbol in EXPANDED_UNIVERSE:
        try:
            print(f"Fetching {symbol:6} Middle    ...", end=" ", flush=True)
            df = cache.get_or_fetch_equity(symbol, '1min', '2025-04-01', '2025-06-30')
            print(f"✓ {len(df):6} bars")
            total_fetched += 1
            total_bars += len(df)
            time.sleep(1)  # Rate limit
        except Exception as e:
            print(f"✗ ERROR: {e}")
            errors.append(f"{symbol} Middle: {e}")
    
    print("\n[2/2] FETCHING RECENT + OLDER PERIODS FOR NEW SYMBOLS")
    print("-"*80)
    
    # Fetch Recent and Older for NEW symbols only
    for symbol in new_symbols:
        for period_name, start, end in [PERIODS[0], PERIODS[2]]:  # Recent and Older
            try:
                print(f"Fetching {symbol:6} {period_name:10}...", end=" ", flush=True)
                df = cache.get_or_fetch_equity(symbol, '1min', start, end)
                print(f"✓ {len(df):6} bars")
                total_fetched += 1
                total_bars += len(df)
                time.sleep(1)  # Rate limit
            except Exception as e:
                print(f"✗ ERROR: {e}")
                errors.append(f"{symbol} {period_name}: {e}")
    
    print("\n" + "="*80)
    print("PREFETCH COMPLETE")
    print("="*80)
    print(f"Total datasets fetched: {total_fetched}")
    print(f"Total bars cached: {total_bars:,}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(f"  - {error}")
    
    print(f"\nAll data cached in: data/cache/equities/")
    print("\nExpanded universe ready for testing!")
    
    # Summary
    print("\n" + "="*80)
    print("FINAL UNIVERSE")
    print("="*80)
    print(f"Total symbols: {len(EXPANDED_UNIVERSE)}")
    print(f"Periods: 3 (Recent, Middle, Older)")
    print(f"Expected total datasets: {len(EXPANDED_UNIVERSE) * 3} (if all successful)")

if __name__ == "__main__":
    main()
