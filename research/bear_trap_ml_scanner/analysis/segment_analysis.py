"""
Segment Analysis - Find the strongest reversal edge

Compare reversal rates across different market contexts
to identify the highest-probability trades.
"""

import pandas as pd
from pathlib import Path

# Load full dataset with outcomes
df = pd.read_csv('data/market_events/intraday_selloffs/v1_smallcap_10pct_5yr/combined_with_outcomes.csv')

print("="*80)
print("SEGMENT ANALYSIS - FINDING THE STRONGEST EDGE")
print("="*80)

print(f"\nTotal events: {len(df):,}")
print(f"Overall 60-min reversal rate: {df['reversed_60min'].mean()*100:.1f}%")
print(f"Overall EOD reversal rate: {df['reversed_eod'].mean()*100:.1f}%")

# ============================================================================
# SEGMENT 1: Uptrend Pullback (strongest edge hypothesis)
# ============================================================================
print("\n" + "="*80)
print("SEGMENT 1: UPTREND PULLBACK")
print("Definition: Above 200 SMA + Golden Cross Active")
print("="*80)

uptrend = df[(df['above_200sma'] == 1) & (df['golden_cross'] == 1)]
print(f"\nEvents: {len(uptrend):,} ({100*len(uptrend)/len(df):.1f}%)")
print(f"60-min reversal: {uptrend['reversed_60min'].mean()*100:.1f}%")
print(f"EOD reversal: {uptrend['reversed_eod'].mean()*100:.1f}%")
print(f"Avg recovery (60min): {uptrend['recovery_pct_60min'].mean():.2f}%")

# Even stronger: Uptrend + near 52w high
uptrend_near_high = uptrend[uptrend['pct_from_52w_high'] > -30]
print(f"\n  Uptrend + Near 52w High: {len(uptrend_near_high):,} events")
print(f"  60-min reversal: {uptrend_near_high['reversed_60min'].mean()*100:.1f}%")
print(f"  EOD reversal: {uptrend_near_high['reversed_eod'].mean()*100:.1f}%")

# ============================================================================
# SEGMENT 2: Falling Knife (high risk)
# ============================================================================
print("\n" + "="*80)
print("SEGMENT 2: FALLING KNIFE (High Risk)")
print("Definition: Below 200 SMA + Near 52w Low")
print("="*80)

falling_knife = df[(df['above_200sma'] == 0) & (df['price_range_position'] < 0.2)]
print(f"\nEvents: {len(falling_knife):,} ({100*len(falling_knife)/len(df):.1f}%)")
print(f"60-min reversal: {falling_knife['reversed_60min'].mean()*100:.1f}%")
print(f"EOD reversal: {falling_knife['reversed_eod'].mean()*100:.1f}%")
print(f"Max additional drop (avg): {falling_knife['max_additional_drop'].mean():.2f}%")

# ============================================================================
# SEGMENT 3: Clustered (momentum continuation)
# ============================================================================
print("\n" + "="*80)
print("SEGMENT 3: CLUSTERED SELLOFFS (Momentum Continuation)")
print("Definition: Previous selloff within 5 days")
print("="*80)

# Need to calculate this
df_sorted = df.sort_values(['symbol', 'date'])
df_sorted['prev_date'] = pd.to_datetime(df_sorted.groupby('symbol')['date'].shift(1))
df_sorted['date'] = pd.to_datetime(df_sorted['date'])
df_sorted['days_since_last'] = (df_sorted['date'] - df_sorted['prev_date']).dt.days
clustered = df_sorted[df_sorted['days_since_last'] <= 5]
isolated = df_sorted[(df_sorted['days_since_last'] > 5) | (df_sorted['days_since_last'].isna())]

print(f"\nClustered: {len(clustered):,} events")
print(f"60-min reversal: {clustered['reversed_60min'].mean()*100:.1f}%")
print(f"EOD reversal: {clustered['reversed_eod'].mean()*100:.1f}%")

print(f"\nIsolated: {len(isolated):,} events")
print(f"60-min reversal: {isolated['reversed_60min'].mean()*100:.1f}%")
print(f"EOD reversal: {isolated['reversed_eod'].mean()*100:.1f}%")

# ============================================================================
# SEGMENT 4: Market-Wide vs Isolated
# ============================================================================
print("\n" + "="*80)
print("SEGMENT 4: MARKET CONTEXT")
print("="*80)

# By SPY change
spy_up = df[df['spy_change_day'] > 0.5]
spy_down = df[df['spy_change_day'] < -0.5]
spy_flat = df[(df['spy_change_day'] >= -0.5) & (df['spy_change_day'] <= 0.5)]

print(f"\nSPY Up (>0.5%): {len(spy_up):,} events")
print(f"  60-min reversal: {spy_up['reversed_60min'].mean()*100:.1f}%")

print(f"\nSPY Down (<-0.5%): {len(spy_down):,} events")
print(f"  60-min reversal: {spy_down['reversed_60min'].mean()*100:.1f}%")

print(f"\nSPY Flat: {len(spy_flat):,} events")
print(f"  60-min reversal: {spy_flat['reversed_60min'].mean()*100:.1f}%")

# ============================================================================
# SEGMENT 5: Time of Day
# ============================================================================
print("\n" + "="*80)
print("SEGMENT 5: TIME OF DAY")
print("="*80)

for bucket in ['opening', 'morning', 'midday', 'afternoon', 'power_hour']:
    subset = df[df['time_bucket'] == bucket]
    if len(subset) > 10:
        print(f"\n{bucket.upper()}: {len(subset):,} events")
        print(f"  60-min reversal: {subset['reversed_60min'].mean()*100:.1f}%")
        print(f"  EOD reversal: {subset['reversed_eod'].mean()*100:.1f}%")

# ============================================================================
# THE GOLDEN FILTER: Combine best conditions
# ============================================================================
print("\n" + "="*80)
print("THE GOLDEN FILTER: Combining Best Conditions")
print("="*80)

# Uptrend + Isolated + Not near 52w low
best = df[(df['above_200sma'] == 1) & 
          (df['price_range_position'] > 0.3) &  # Not near 52w low
          (df['time_bucket'].isin(['midday', 'afternoon']))]

print(f"\nGOLDEN: Uptrend + Not Near Lows + Midday/Afternoon")
print(f"Events: {len(best):,}")
print(f"60-min reversal: {best['reversed_60min'].mean()*100:.1f}%")
print(f"EOD reversal: {best['reversed_eod'].mean()*100:.1f}%")
print(f"Avg recovery (60min): {best['recovery_pct_60min'].mean():.2f}%")

# Ultra-strict
ultra = df[(df['above_200sma'] == 1) & 
           (df['golden_cross'] == 1) &
           (df['pct_from_52w_high'] > -40) &
           (df['time_bucket'].isin(['midday', 'afternoon', 'power_hour']))]

print(f"\nULTRA: Uptrend + Golden + Near Highs + Good Timing")
print(f"Events: {len(ultra):,}")
if len(ultra) > 0:
    print(f"60-min reversal: {ultra['reversed_60min'].mean()*100:.1f}%")
    print(f"EOD reversal: {ultra['reversed_eod'].mean()*100:.1f}%")
    print(f"Avg recovery (60min): {ultra['recovery_pct_60min'].mean():.2f}%")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
