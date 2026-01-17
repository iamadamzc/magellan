"""
Speedboat Universe - Manual Curation
-------------------------------------
Based on Gem's criteria, manually curated list of known low-float momentum stocks

SPEEDBOAT CRITERIA:
- Float < 20M
- Price $2-$15
- Known for momentum/volatility

CURATED LIST (Known Speedboats):
- SAVA (Cassava Sciences) - ~50M float, biotech
- BBIG (Vinco Ventures) - ~15M float, meme
- MULN (Mullen Automotive) - ~10M float, EV
- GREE (Greenidge Generation) - ~5M float, crypto mining
- SPRC (SciSparc) - ~3M float, biotech

MID-CAP (Test Twilight Zone):
- HOOD (Robinhood) - ~85M float
- SOFI (SoFi) - ~95M float  
- DKNG (DraftKings) - ~80M float
- PLTR (Palantir) - ~200M float (tanker)

We'll cache data for these and test V7
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache

# Define universe
speedboats = [
    # Low float momentum (if data available)
    'SAVA', 'BBIG', 'MULN', 'GREE', 'SPRC',
]

mid_cap = [
    # Mid-cap (Twilight Zone)
    'HOOD', 'SOFI', 'DKNG',
]

tankers = [
    # Already cached
    'RIOT', 'MARA', 'AMC'
]

# Test period
start = '2024-11-01'
end = '2025-01-17'

print("="*80)
print("CACHING SPEEDBOAT & MID-CAP UNIVERSE")
print("="*80)

all_symbols = speedboats + mid_cap
cached = []
failed = []

for symbol in all_symbols:
    print(f"\nCaching {symbol}...")
    try:
        df = cache.get_or_fetch_equity(symbol, '1min', start, end)
        if df is not None and len(df) > 0:
            print(f"  ✅ {symbol}: {len(df):,} bars cached")
            cached.append(symbol)
        else:
            print(f"  ⚠️ {symbol}: No data")
            failed.append(symbol)
    except Exception as e:
        print(f"  ✗ {symbol}: {e}")
        failed.append(symbol)

print("\n" + "="*80)
print("CACHE SUMMARY")
print("="*80)
print(f"Successfully cached: {len(cached)}")
print(f"Failed: {len(failed)}")

if cached:
    print(f"\n✅ Ready to test: {', '.join(cached)}")

if failed:
    print(f"\n⚠️ Failed to cache: {', '.join(failed)}")

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)
print("1. Test V7 (Barbell) on cached symbols")
print("2. Compare Speedboats vs Mid-Cap vs Tankers")
print("3. Identify which universe works best for ORB")
