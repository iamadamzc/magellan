"""
Quick summary generator - outputs key numbers only
"""
import pandas as pd
from pathlib import Path
from datetime import datetime

data_path = Path('data/market_events/intraday_selloffs/v1_smallcap_10pct_5yr/combined_with_features.csv')
df = pd.read_csv(data_path)
df['date'] = pd.to_datetime(df['date'])

print("="*80)
print("DEEP DIVE - KEY NUMBERS SUMMARY")
print("="*80)

# 200 SMA Analysis
df_sma = df[df['above_200sma'].notna()]
above_200 = df_sma[df_sma['above_200sma'] == 1]
below_200 = df_sma[df_sma['above_200sma'] == 0]

print(f"\n1. 200 SMA POSITIONING:")
print(f"   Above 200 SMA: {len(above_200):,} events ({100*len(above_200)/len(df_sma):.1f}%)")
print(f"   Below 200 SMA: {len(below_200):,} events ({100*len(below_200)/len(df_sma):.1f}%)")
print(f"   Above 200 avg drop: {above_200['drop_pct'].mean():.2f}%")
print(f"   Below 200 avg drop: {below_200['drop_pct'].mean():.2f}%")

# Golden cross
golden = df_sma[df_sma['golden_cross'] == 1]
print(f"\n   Golden Cross active: {len(golden):,} ({100*len(golden)/len(df_sma):.1f}%)")

# Strong uptrend
strong = df_sma[(df_sma['above_200sma'] == 1) & (df_sma['golden_cross'] == 1)]
print(f"   STRONG UPTREND (above200 + golden): {len(strong):,} ({100*len(strong)/len(df_sma):.1f}%)")

# Clustered selloffs
print(f"\n2. SERIAL SELLERS & CLUSTERING:")
df_sorted = df.sort_values(['symbol', 'date'])
df_sorted['prev_date'] = df_sorted.groupby('symbol')['date'].shift(1)
df_sorted['days_since'] = (df_sorted['date'] - df_sorted['prev_date']).dt.days
clustered = df_sorted[df_sorted['days_since'] <= 5]
print(f"   Within 5 days of last: {len(clustered):,} ({100*len(clustered)/len(df):.1f}%)")

# Market-wide
print(f"\n3. MARKET-WIDE vs ISOLATED:")
events_per_day = df.groupby('date').size()
print(f"   Days with 20+ selloffs: {len(events_per_day[events_per_day >= 20])}")
print(f"   Days with 1-3 selloffs: {len(events_per_day[events_per_day <= 3])}")

# Timing
print(f"\n4. TIMING:")
for bucket in ['opening', 'morning', 'midday', 'afternoon', 'power_hour']:
    count = len(df[df['time_bucket'] == bucket])
    pct = 100 * count / len(df)
    print(f"   {bucket:12}: {count:5} ({pct:.1f}%)")

# Range position
print(f"\n5. 52-WEEK RANGE POSITION:")
near_high = df[df['pct_from_52w_high'] > -20]
near_low = df[df['pct_from_52w_low'] < 20]
print(f"   Near 52w high (within 20%): {len(near_high):,} ({100*len(near_high)/len(df):.1f}%)")
print(f"   Near 52w low (within 20%): {len(near_low):,} ({100*len(near_low)/len(df):.1f}%)")

# Strategy opportunities
print(f"\n6. STRATEGY OPPORTUNITY COUNTS:")

# Uptrend pullback
uptrend = df[(df['above_200sma'] == 1) & (df['golden_cross'] == 1) & (df['pct_from_52w_high'] > -30)]
print(f"   Uptrend Pullback (above200+golden+near52wh): {len(uptrend):,}")

# Capitulation
cap = df[(df['above_200sma'] == 0) & (df['price_range_position'] < 0.2) & (df['time_bucket'] == 'power_hour')]
print(f"   Capitulation (below200+nearlow+powerhour): {len(cap):,}")

# Market-wide recovery
mw_dates = events_per_day[events_per_day >= 15].index
mw = df[df['date'].isin(mw_dates) & (df['spy_change_day'] < -0.5)]
print(f"   Market-wide recovery (15+selloffs+SPYdown): {len(mw):,}")

# Isolated
iso_dates = events_per_day[events_per_day <= 3].index
iso = df[df['date'].isin(iso_dates) & (df['spy_change_day'] > 0)]
print(f"   Isolated selloff (<3 selloffs+SPYup): {len(iso):,}")

# Correlations
print(f"\n7. CORRELATIONS WITH SEVERITY (drop_pct):")
for feat in ['distance_from_200sma', 'pct_from_52w_high', 'spy_change_day', 'minutes_since_open']:
    if feat in df.columns:
        corr = df[['drop_pct', feat]].dropna().corr().iloc[0,1]
        print(f"   {feat:25} r = {corr:+.3f}")

print("\n" + "="*80)
print("SUMMARY COMPLETE")
print("="*80)
