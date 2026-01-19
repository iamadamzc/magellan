"""
Test NVDA with split-aware logic
NVDA had 10-for-1 stock split on June 10, 2024
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache
import pandas as pd
import numpy as np

# Fetch data
df = cache.get_or_fetch_equity('NVDA', '1day', '2024-06-01', '2026-01-18')

print("NVDA Stock Split Analysis")
print("="*60)

# Check for split (large price drop)
df['price_change_pct'] = df['close'].pct_change() * 100
largest_drops = df.nsmallest(5, 'price_change_pct')[['close', 'price_change_pct']]
print("\nLargest single-day price drops:")
print(largest_drops)

# Find the split date
split_candidates = df[df['price_change_pct'] < -50]
if len(split_candidates) > 0:
    split_date = split_candidates.index[0]
    print(f"\n⚠️  Likely split date: {split_date}")
    print(f"Pre-split close: ${df.loc[df.index < split_date, 'close'].iloc[-1]:.2f}")
    print(f"Post-split close: ${df.loc[split_date, 'close']:.2f}")
    
    # Calculate split ratio
    pre_split_close = df.loc[df.index < split_date, 'close'].iloc[-1]
    post_split_close = df.loc[split_date, 'close']
    split_ratio = pre_split_close / post_split_close
    print(f"Split ratio: ~{split_ratio:.1f}-for-1")
    
    print("\n" + "="*60)
    print("SOLUTION: Need split-adjusted data or use post-split period only")
    print("="*60)
    
    # Test with post-split data only
    post_split_df = df[df.index >= split_date]
    post_split_return = (post_split_df['close'].iloc[-1] / post_split_df['close'].iloc[0] - 1) * 100
    print(f"\nPost-split period return (June 10, 2024 onwards):")
    print(f"  {split_date} to {post_split_df.index[-1]}")
    print(f"  Return: {post_split_return:+.2f}%")
    print(f"  Bars: {len(post_split_df)}")
else:
    print("\nNo obvious split detected")
