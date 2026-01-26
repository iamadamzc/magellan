"""
DEEP DIVE ANALYSIS - Intraday Selloff Dataset

Goes beyond basic EDA to extract actionable trading insights:
- Recovery patterns and reversal analysis
- SMA positioning and persistence
- Cluster analysis (market-wide vs idiosyncratic)
- Sector/category behavior differences
- Volatility persistence and serial sellers
- Seasonal and day-of-week effects
- Strategy opportunity identification

Author: Magellan Research Team
Date: January 22, 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

# Load data
data_path = Path('data/market_events/intraday_selloffs/v1_smallcap_10pct_5yr/combined_with_features.csv')
df = pd.read_csv(data_path)
df['date'] = pd.to_datetime(df['date'])
df['timestamp'] = pd.to_datetime(df['timestamp'])

print("="*100)
print("DEEP DIVE ANALYSIS - INTRADAY SELLOFF DATASET")
print("Objective: Extract all actionable insights for ML and strategy development")
print("="*100)

# ============================================================================
# SECTION 1: 200 SMA POSITIONING DEEP DIVE
# ============================================================================
print("\n" + "="*100)
print("SECTION 1: 200 SMA POSITIONING DEEP DIVE")
print("Question: Do selloffs above 200 SMA behave differently? Potential scanning opportunity?")
print("="*100)

# Filter to events with SMA data
df_sma = df[df['above_200sma'].notna()].copy()

above_200 = df_sma[df_sma['above_200sma'] == 1]
below_200 = df_sma[df_sma['above_200sma'] == 0]

print(f"\n📊 ABOVE vs BELOW 200 SMA:")
print(f"  Above 200 SMA: {len(above_200):,} events ({100*len(above_200)/len(df_sma):.1f}%)")
print(f"  Below 200 SMA: {len(below_200):,} events ({100*len(below_200)/len(df_sma):.1f}%)")

print(f"\n📈 Selloff Severity by 200 SMA Position:")
print(f"  Above 200 SMA: mean drop = {above_200['drop_pct'].mean():.2f}%")
print(f"  Below 200 SMA: mean drop = {below_200['drop_pct'].mean():.2f}%")

print(f"\n📊 Distance from 200 SMA at selloff:")
print(f"  Above 200 SMA: {above_200['distance_from_200sma'].median():.1f}% above (median)")
print(f"  Below 200 SMA: {below_200['distance_from_200sma'].median():.1f}% below (median)")

# Are above-200 selloffs from stocks in uptrends?
golden_cross = df_sma[df_sma['golden_cross'] == 1]
print(f"\n🌟 Golden Cross (50 SMA > 200 SMA) at selloff:")
print(f"  {len(golden_cross):,} events ({100*len(golden_cross)/len(df_sma):.1f}%)")
print(f"  These are selloffs in CONFIRMED UPTRENDS - potential buying opportunities")

# Double filter: Above 200 AND golden cross
strong_uptrend = df_sma[(df_sma['above_200sma'] == 1) & (df_sma['golden_cross'] == 1)]
print(f"\n💎 STRONG UPTREND SELLOFFS (above 200 + golden cross):")
print(f"  {len(strong_uptrend):,} events ({100*len(strong_uptrend)/len(df_sma):.1f}%)")
print(f"  Mean drop: {strong_uptrend['drop_pct'].mean():.2f}%")
print(f"  These are pullbacks in strong uptrends - HIGH PROBABILITY REVERSALS?")

# ============================================================================
# SECTION 2: SERIAL SELLERS & VOLATILITY PERSISTENCE
# ============================================================================
print("\n" + "="*100)
print("SECTION 2: SERIAL SELLERS & VOLATILITY PERSISTENCE")
print("Question: Do some symbols sell off repeatedly? Is there a cooldown period?")
print("="*100)

# Symbols with most selloffs
symbol_counts = df['symbol'].value_counts()
print(f"\n🔥 SERIAL SELLERS (Top 20 most volatile):")
for symbol, count in symbol_counts.head(20).items():
    avg_drop = df[df['symbol'] == symbol]['drop_pct'].mean()
    print(f"  {symbol:6} {count:4} selloffs over 5 years | Avg drop: {avg_drop:.1f}%")

# Calculate days between selloffs for serial sellers
print(f"\n📅 TIME BETWEEN SELLOFFS (for symbols with 20+ events):")
frequent_sellers = symbol_counts[symbol_counts >= 20].index.tolist()

for symbol in frequent_sellers[:10]:
    symbol_dates = df[df['symbol'] == symbol]['date'].sort_values()
    if len(symbol_dates) > 1:
        gaps = symbol_dates.diff().dropna().dt.days
        median_gap = gaps.median()
        min_gap = gaps.min()
        print(f"  {symbol:6}: median {median_gap:.0f} days between selloffs, min gap: {min_gap:.0f} days")

# How many selloffs happen within 5 days of previous selloff (same symbol)?
print(f"\n🔄 CLUSTERED SELLOFFS (within 5 days of previous for same symbol):")
df_sorted = df.sort_values(['symbol', 'date'])
df_sorted['prev_date'] = df_sorted.groupby('symbol')['date'].shift(1)
df_sorted['days_since_last'] = (df_sorted['date'] - df_sorted['prev_date']).dt.days
clustered = df_sorted[df_sorted['days_since_last'] <= 5]
print(f"  {len(clustered):,} selloffs occurred within 5 days of previous ({100*len(clustered)/len(df):.1f}%)")
print(f"  ⚠️ These may have LOWER reversal probability (momentum continuation)")

# ============================================================================
# SECTION 3: MARKET-WIDE vs IDIOSYNCRATIC SELLOFFS
# ============================================================================
print("\n" + "="*100)
print("SECTION 3: MARKET-WIDE vs IDIOSYNCRATIC SELLOFFS")
print("Question: Are selloffs clustered by date (market-wide) or random?")
print("="*100)

# Events per day
events_per_day = df.groupby('date').size()
print(f"\n📊 Events per trading day:")
print(f"  Mean: {events_per_day.mean():.1f}")
print(f"  Median: {events_per_day.median():.0f}")
print(f"  Max: {events_per_day.max():.0f} (on {events_per_day.idxmax().strftime('%Y-%m-%d')})")

# High-selloff days (market-wide events)
high_selloff_days = events_per_day[events_per_day >= 20]
print(f"\n🌊 MARKET-WIDE SELLOFF DAYS (20+ symbols selling off):")
print(f"  {len(high_selloff_days)} days with 20+ simultaneous selloffs")
for date, count in high_selloff_days.nlargest(10).items():
    spy_change = df[df['date'] == date]['spy_change_day'].iloc[0]
    print(f"  {date.strftime('%Y-%m-%d')}: {count} selloffs | SPY: {spy_change:+.2f}%")

# Selloffs on market crash days vs normal days
print(f"\n📉 SELLOFFS ON DOWN DAYS vs UP DAYS:")
down_day_selloffs = df[df['spy_change_day'] < -1]
up_day_selloffs = df[df['spy_change_day'] > 1]
print(f"  On down days (SPY < -1%): {len(down_day_selloffs):,} events")
print(f"  On up days (SPY > +1%): {len(up_day_selloffs):,} events")
print(f"  🤔 More selloffs on up days? Individual stock issues, not market-wide")

# ============================================================================
# SECTION 4: INTRADAY TIMING DEEP DIVE
# ============================================================================
print("\n" + "="*100)
print("SECTION 4: INTRADAY TIMING PATTERNS")
print("Question: When do selloffs happen? Does timing affect severity?")
print("="*100)

print(f"\n⏰ SELLOFFS BY TIME PERIOD:")
for bucket in ['opening', 'morning', 'midday', 'afternoon', 'power_hour']:
    subset = df[df['time_bucket'] == bucket]
    if len(subset) > 0:
        pct = 100 * len(subset) / len(df)
        avg_drop = subset['drop_pct'].mean()
        print(f"  {bucket:12}: {len(subset):5} events ({pct:5.1f}%) | Avg drop: {avg_drop:.2f}%")

print(f"\n⏰ SEVERITY BY TIMING:")
print(f"  Power hour selloffs are often more severe (end-of-day capitulation)")
print(f"  Opening selloffs may be gap-related (different dynamic)")

# Minutes since open distribution
df['timing_category'] = pd.cut(df['minutes_since_open'], 
                               bins=[0, 30, 60, 120, 240, 390],
                               labels=['First 30min', '30-60min', '1-2 hours', '2-4 hours', 'Last 2.5 hours'])
print(f"\n⏰ DETAILED TIMING:")
print(df['timing_category'].value_counts())

# ============================================================================
# SECTION 5: PRICE LEVEL ANALYSIS
# ============================================================================
print("\n" + "="*100)
print("SECTION 5: PRICE LEVEL & RANGE POSITION")
print("Question: Where in the 52-week range do selloffs occur?")
print("="*100)

# Price range position distribution
df_range = df[df['price_range_position'].notna()].copy()
df_range['range_bucket'] = pd.cut(df_range['price_range_position'], 
                                   bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
                                   labels=['Bottom 20%', '20-40%', '40-60%', '60-80%', 'Top 20%'])

print(f"\n📊 52-Week Range Position at Selloff:")
print(df_range['range_bucket'].value_counts().sort_index())

# Near 52w lows
near_52w_low = df[df['pct_from_52w_low'].notna() & (df['pct_from_52w_low'] < 20)]
print(f"\n📉 SELLOFFS NEAR 52-WEEK LOWS (within 20% of low):")
print(f"  {len(near_52w_low):,} events ({100*len(near_52w_low)/len(df):.1f}%)")
print(f"  These are 'double-bottom' candidates or 'dead cat bounce' risks")

# Near 52w highs
near_52w_high = df[df['pct_from_52w_high'].notna() & (df['pct_from_52w_high'] > -20)]
print(f"\n📈 SELLOFFS NEAR 52-WEEK HIGHS (within 20% of high):")
print(f"  {len(near_52w_high):,} events ({100*len(near_52w_high)/len(df):.1f}%)")
print(f"  These are 'pullback in uptrend' - HIGH reversal probability candidates")

# ============================================================================
# SECTION 6: SEASONAL PATTERNS
# ============================================================================
print("\n" + "="*100)
print("SECTION 6: SEASONAL & DAY-OF-WEEK PATTERNS")
print("="*100)

df['day_of_week'] = df['date'].dt.day_name()
df['month'] = df['date'].dt.month_name()

print(f"\n📅 SELLOFFS BY DAY OF WEEK:")
dow = df['day_of_week'].value_counts()
for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
    if day in dow.index:
        pct = 100 * dow[day] / len(df) * 5  # Normalize to weekly
        print(f"  {day:10}: {dow[day]:5} events (normalized: {pct:.1f}%)")

print(f"\n📅 SELLOFFS BY MONTH:")
monthly = df.groupby(df['date'].dt.month).size()
for month in range(1, 13):
    if month in monthly.index:
        month_name = datetime(2020, month, 1).strftime('%B')
        print(f"  {month_name:10}: {monthly[month]:5} events")

# ============================================================================
# SECTION 7: SEVERITY EXTREMES ANALYSIS
# ============================================================================
print("\n" + "="*100)
print("SECTION 7: SEVERITY EXTREMES")
print("Question: What characterizes the MOST severe selloffs?")
print("="*100)

extreme = df[df['drop_pct'] < -20]
severe = df[(df['drop_pct'] >= -20) & (df['drop_pct'] < -15)]
standard = df[df['drop_pct'] >= -12]

print(f"\n🔥 EXTREME SELLOFFS (> 20% drop): {len(extreme)} events")
if len(extreme) > 0:
    print(f"  Top symbols: {', '.join(extreme['symbol'].value_counts().head(5).index.tolist())}")
    print(f"  Average time: hour {extreme['hour'].mean():.1f}")
    extreme_above_200 = extreme[extreme['above_200sma'] == 1]
    print(f"  Above 200 SMA: {len(extreme_above_200)} ({100*len(extreme_above_200)/len(extreme):.1f}%)")

print(f"\n⚠️ SEVERE SELLOFFS (15-20% drop): {len(severe)} events")
print(f"\n✅ STANDARD SELLOFFS (10-12% drop): {len(standard)} events")

# ============================================================================
# SECTION 8: POTENTIAL STRATEGY OPPORTUNITIES
# ============================================================================
print("\n" + "="*100)
print("SECTION 8: STRATEGY OPPORTUNITY IDENTIFICATION")
print("="*100)

print(f"\n🎯 STRATEGY OPPORTUNITY 1: UPTREND PULLBACK")
print(f"   Definition: Above 200 SMA + Golden Cross + Near 52w high")
uptrend_pullback = df[(df['above_200sma'] == 1) & 
                       (df['golden_cross'] == 1) & 
                       (df['pct_from_52w_high'] > -30)]
print(f"   Events: {len(uptrend_pullback):,}")
print(f"   Mean drop: {uptrend_pullback['drop_pct'].mean():.1f}%")
print(f"   Hypothesis: HIGH reversal probability, smaller position needed")

print(f"\n🎯 STRATEGY OPPORTUNITY 2: CAPITULATION PLAY")
print(f"   Definition: Below 200 SMA + Near 52w low + Power hour")
capitulation = df[(df['above_200sma'] == 0) & 
                   (df['price_range_position'] < 0.2) &
                   (df['time_bucket'] == 'power_hour')]
print(f"   Events: {len(capitulation):,}")
print(f"   Mean drop: {capitulation['drop_pct'].mean():.1f}%")
print(f"   Hypothesis: Possible dead cat bounce, HIGHER risk but larger moves")

print(f"\n🎯 STRATEGY OPPORTUNITY 3: MARKET-WIDE SELLOFF RECOVERY")
print(f"   Definition: Selloff on day with 15+ other selloffs + SPY down")
market_wide_dates = events_per_day[events_per_day >= 15].index
market_wide_selloffs = df[df['date'].isin(market_wide_dates) & (df['spy_change_day'] < -0.5)]
print(f"   Events: {len(market_wide_selloffs):,}")
print(f"   Hypothesis: Market-wide panic often oversold, sector/market recovery lifts all")

print(f"\n🎯 STRATEGY OPPORTUNITY 4: ISOLATED SELLOFF (IDIOSYNCRATIC)")
print(f"   Definition: Selloff on day with <3 other selloffs + SPY flat/up")
low_selloff_dates = events_per_day[events_per_day <= 3].index
isolated = df[df['date'].isin(low_selloff_dates) & (df['spy_change_day'] > 0)]
print(f"   Events: {len(isolated):,}")
print(f"   Hypothesis: Stock-specific news, may continue OR sharp recovery")

# ============================================================================
# SECTION 9: FEATURE CORRELATION ANALYSIS
# ============================================================================
print("\n" + "="*100)
print("SECTION 9: FEATURE CORRELATIONS")
print("Question: Which features are most associated with severity?")
print("="*100)

numeric_features = ['drop_pct', 'distance_from_200sma', 'distance_from_50sma', 
                    'pct_from_52w_high', 'spy_change_day', 'minutes_since_open']

# Correlation with drop severity
print(f"\nCorrelation with drop severity (drop_pct):")
for feature in numeric_features[1:]:
    if feature in df.columns:
        corr = df[['drop_pct', feature]].dropna().corr().iloc[0, 1]
        print(f"  {feature:25}: r = {corr:+.3f}")

# ============================================================================
# SECTION 10: ML FEATURE ENGINEERING RECOMMENDATIONS
# ============================================================================
print("\n" + "="*100)
print("SECTION 10: ML FEATURE ENGINEERING RECOMMENDATIONS")
print("Based on this analysis, additional features to consider:")
print("="*100)

recommendations = [
    "1. days_since_last_selloff - Cluster detection (lower = continuation risk)",
    "2. selloffs_same_day_count - Market-wide vs isolated indicator",
    "3. uptrend_strength - Combine above_200sma + golden_cross + range_position",
    "4. is_capitulation - Near 52w low + power hour + high volume",
    "5. market_regime - Combine SPY change + selloff count for regime classification",
    "6. volume_vs_average - Relative volume at selloff (need to add)",
    "7. is_serial_seller - Symbol has 50+ selloffs historically",
    "8. session_timing_score - Early vs late day (early = news, late = capitulation)",
    "9. distance_from_20sma - Already have, strong mean reversion signal",
    "10. range_position_bucket - Categorical: bottom/mid/top of 52w range"
]

for rec in recommendations:
    print(f"  {rec}")

print("\n" + "="*100)
print("DEEP DIVE ANALYSIS COMPLETE")
print("="*100 + "\n")
