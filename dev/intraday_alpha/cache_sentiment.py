#!/usr/bin/env python3
"""
Pre-cache sentiment data for all symbols
"""

from sentiment_cache import SentimentCache

sc = SentimentCache()

symbols = ['SPY', 'QQQ', 'IWM']
start_date = '2022-01-01'
end_date = '2026-01-10'

print("=" * 80)
print("PRE-CACHING SENTIMENT DATA (2022-2026)")
print("=" * 80)

for symbol in symbols:
    print(f"\n{symbol}:")
    df = sc.get_or_fetch(symbol, start_date, end_date)
    non_zero = (df['sentiment'] != 0).sum()
    print(f"  ✅ Cached {len(df)} days ({non_zero} non-zero)")
    print(f"  Range: [{df['sentiment'].min():.3f}, {df['sentiment'].max():.3f}]")

print("\n" + "=" * 80)
print("✅ ALL SENTIMENT DATA CACHED")
print("=" * 80)
