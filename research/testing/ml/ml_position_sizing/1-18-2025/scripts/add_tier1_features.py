"""
Feature Engineering v2 - Chad's Tier 1 Features

Adds high-signal features NOT part of Bear Trap entry logic:
1. Time of day
2. Speed of reclaim  
3. Distance to VWAP at entry
"""
import pandas as pd
import numpy as np
from pathlib import Path

# Load extracted trades
df = pd.read_csv('research/ml_position_sizing/data/bear_trap_trades_2020_2024.csv')
print(f"Loaded {len(df)} trades")

# Convert entry_date to datetime
df['entry_datetime'] = pd.to_datetime(df['entry_date'])

# Feature 1: Time of Day
df['entry_hour'] = df['entry_datetime'].dt.hour
df['entry_minute'] = df['entry_datetime'].dt.minute

# Create time buckets
df['time_bucket'] = pd.cut(
    df['entry_hour'], 
    bins=[0, 10, 15, 24],
    labels=['early', 'midday', 'late'],
    include_lowest=True
)

# Feature 2: Speed of Reclaim
# This requires bars_to_reclaim which we need to add to extraction
# For now, use a proxy: max_profit as % of entry in first few bars
# (High max_profit early = fast move)
df['early_momentum'] = df['max_profit'] / (df['bars_held'] + 1)  # % profit per bar

# Feature 3: Distance to VWAP
# We don't have VWAP in extracted data yet
# ADD THIS in next extraction run
# For now, mark as TODO
df['vwap_distance_pct'] = np.nan  # TODO: Calculate in extraction

# Feature 4: Day of Week  
df['day_of_week'] = df['entry_datetime'].dt.dayofweek
df['is_monday'] = (df['day_of_week'] == 0).astype(int)
df['is_friday'] = (df['day_of_week'] == 4).astype(int)

print("\nTier 1 Features Added:")
print(f"  - time_bucket: {df['time_bucket'].value_counts().to_dict()}")
print(f"  - early_momentum: mean {df['early_momentum'].mean():.2f}")
print(f"  - day_of_week: {df['day_of_week'].value_counts().sort_index().to_dict()}")

# New labeling based on RISK POSTURE (not outcome)
print("\n" + "="*80)
print("RISK POSTURE LABELING (Chad's Framework)")
print("="*80)

# Risk score components
risk_score = 0

# Time risk (midday = risky)
time_risk = np.where(df['time_bucket'] == 'midday', -2, 0)
time_safe = np.where(df['time_bucket'] == 'early', +1, 0) + np.where(df['time_bucket'] == 'late', +1, 0)

# Momentum risk (fast = safe to scale)
momentum_score = np.where(df['early_momentum'] > df['early_momentum'].median(), +2, -1)

# Volume confirmation (we have this)
volume_score = np.where(df['volume_ratio'] > 2.0, +1, 0)

# Total risk posture score
df['risk_posture_score'] = time_safe + time_risk + momentum_score + volume_score

# Map to labels (risk posture, not outcome)
df['regime_label_v2'] = pd.cut(
    df['risk_posture_score'],
    bins=[-np.inf, 0, 2, np.inf],
    labels=['NO_ADD', 'ADD_NEUTRAL', 'ADD_ALLOWED']
)

print("\nLabel Distribution (v2 - Risk Posture):")
print(df['regime_label_v2'].value_counts())

print("\nValidation by Risk Posture:")
for label in ['ADD_ALLOWED', 'ADD_NEUTRAL', 'NO_ADD']:
    subset = df[df['regime_label_v2'] == label]
    if len(subset) > 0:
        avg_r = subset['r_multiple'].mean()
        std_r = subset['r_multiple'].std()
        worst_10 = subset.nsmallest(10, 'r_multiple')['r_multiple'].mean()
        print(f"\n{label}:")
        print(f"  Count: {len(subset)}")
        print(f"  Avg R: {avg_r:.2f}")
        print(f"  Std R: {std_r:.2f} (variance)")
        print(f"  Worst 10 avg: {worst_10:.2f}")

# Check if variance improved
no_add_var = df[df['regime_label_v2'] == 'NO_ADD']['r_multiple'].std()
add_allowed_var = df[df['regime_label_v2'] == 'ADD_ALLOWED']['r_multiple'].std()

print(f"\n" + "="*80)
print("KEY METRIC: Does NO_ADD have higher variance?")
print("="*80)
print(f"NO_ADD variance: {no_add_var:.2f}")
print(f"ADD_ALLOWED variance: {add_allowed_var:.2f}")

if no_add_var > add_allowed_var:
    print("\n✓ YES! NO_ADD is riskier environment")
    print("  → Suppressing adds during NO_ADD should reduce tail risk")
else:
    print("\n✗ NO: Need to refine features")

# Save
df.to_csv('research/ml_position_sizing/data/labeled_regimes_v2.csv', index=False)
print(f"\nSaved to labeled_regimes_v2.csv")

# Summary stats for Chad's metrics
print(f"\n" + "="*80)
print("CHAD'S SUCCESS METRICS")
print("="*80)

print("\nTime of Day Patterns:")
for bucket in ['early', 'midday', 'late']:
    subset = df[df['time_bucket'] == bucket]
    print(f"  {bucket}: Avg R={subset['r_multiple'].mean():.2f}, Std={subset['r_multiple'].std():.2f}")

print("\nMomentum Patterns:")
fast = df[df['early_momentum'] > df['early_momentum'].median()]
slow = df[df['early_momentum'] <= df['early_momentum'].median()]
print(f"  Fast reclaim: Avg R={fast['r_multiple'].mean():.2f}")
print(f"  Slow reclaim: Avg R={slow['r_multiple'].mean():.2f}")
