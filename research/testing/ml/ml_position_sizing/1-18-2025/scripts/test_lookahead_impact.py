"""
Quick test to measure lookahead bias impact

Compares Bear Trap performance with and without the lookahead fix
"""
import pandas as pd
import numpy as np
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache

# Test on AMC (one of the better ones) for December 2024
symbol = 'AMC'
start = '2024-12-01'
end = '2024-12-31'

print("="*80)
print("LOOKAHEAD BIAS IMPACT TEST")
print("="*80)
print(f"Symbol: {symbol}")
print(f"Period: {start} to {end}\n")

# Fetch data
df = cache.get_or_fetch_equity(symbol, '1min', start, end)

if df is None or len(df) == 0:
    print("No data!")
    exit()

# Add date column
df['date'] = df.index.date

print(f"Total bars: {len(df)}")
print(f"Total days: {df['date'].nunique()}\n")

# Calculate BOTH ways
print("="*80)
print("CALCULATING SESSION LOWS")
print("="*80)

# WRONG WAY (lookahead)
df['session_low_lookahead'] = df.groupby('date')['low'].transform('min')

# CORRECT WAY (no lookahead)
df['session_low_correct'] = df.groupby('date')['low'].cummin()

# Check differences
df['difference'] = df['session_low_lookahead'] - df['session_low_correct']
df['has_lookahead'] = df['difference'] < -0.01  # Session low will go lower later

# Stats
total_bars_with_lookahead = df['has_lookahead'].sum()
pct_bars_with_lookahead = (total_bars_with_lookahead / len(df)) * 100

print(f"\nBars with lookahead advantage: {total_bars_with_lookahead} ({pct_bars_with_lookahead:.1f}%)")
print(f"  (These bars 'know' the low will go lower later)")

# Show example
print(f"\n{'='*80}")
print("EXAMPLE DAY")
print(f"{'='*80}")

# Pick a day with differences
example_day = df[df['has_lookahead']].iloc[0]['date']
example_df = df[df['date'] == example_day][['session_low_lookahead', 'session_low_correct', 'low', 'close', 'difference']].head(20)

print(f"\nDate: {example_day}")
print(f"First 20 bars of the day:\n")
print(example_df.to_string())

print(f"\n{'='*80}")
print("IMPACT ON STRATEGY")
print(f"{'='*80}")

# Simulate simplified Bear Trap logic
# Entry: price > session_low (reclaim)

# With lookahead
df['reclaim_lookahead'] = df['close'] > df['session_low_lookahead']

# Without lookahead  
df['reclaim_correct'] = df['close'] > df['session_low_correct']

# False signals (lookahead says yes, correct says no)
df['false_signal'] = df['reclaim_lookahead'] & ~df['reclaim_correct']

false_signals = df['false_signal'].sum()
pct_false = (false_signals / len(df)) * 100

print(f"\nFalse 'reclaim' signals from lookahead: {false_signals} ({pct_false:.1f}%)")
print(f"  (Strategy thought it reclaimed, but it actually hadn't yet)")

print(f"\n{'='*80}")
print("CONCLUSION")
print(f"{'='*80}")

if pct_bars_with_lookahead > 20:
    print("\n⚠️  HIGH IMPACT: Lookahead affected >20% of bars")
    print("   → Strategy performance is likely SIGNIFICANTLY inflated")
    print("   → Need to re-run ALL Bear Trap backtests with fix")
elif pct_bars_with_lookahead > 5:
    print("\n⚠️  MODERATE IMPACT: Lookahead affected 5-20% of bars")
    print("   → Strategy performance is inflated")
    print("   → Should re-run backtests with fix")
else:
    print("\n✓ LOW IMPACT: Lookahead affected <5% of bars")
    print("   → Minor effect on results")

print(f"\n{'='*80}")
