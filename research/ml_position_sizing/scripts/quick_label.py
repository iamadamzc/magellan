"""Quick regime labeling"""
import pandas as pd
import numpy as np

# Load trades
df = pd.read_csv('research/ml_position_sizing/data/bear_trap_trades_2020_2024.csv')
print(f"Loaded {len(df)} trades")

# Get features with defaults
trend = df.get('trend_strength', pd.Series([0.5]*len(df))).fillna(0.5)
atr = df.get('atr_percentile', pd.Series([0.5]*len(df))).fillna(0.5)
vol = df.get('volume_ratio', pd.Series([1.0]*len(df))).fillna(1.0)
drop = abs(df.get('day_change_pct', pd.Series([-15]*len(df))).fillna(-15))

# Calculate scores
trend_score = np.where(trend > 0.7, 3, np.where(trend > 0.4, 2, np.where(trend > 0.2, 1, 0)))
vol_score = np.where(atr < 0.3, 3, np.where(atr < 0.6, 2, np.where(atr < 0.8, 1, 0)))
volume_score = np.where(vol > 2.0, 3, np.where(vol > 1.5, 2, np.where(vol > 1.2, 1, 0)))
drop_score = np.where(drop > 25, 3, np.where(drop > 20, 2, np.where(drop > 15, 1, 0)))

total = trend_score + vol_score + volume_score + drop_score
df['total_score'] = total
df['regime_label'] = np.where(total >= 9, 'ADD_ALLOWED', np.where(total >= 5, 'ADD_NEUTRAL', 'NO_ADD'))

print("\nLABEL DISTRIBUTION:")
print(df['regime_label'].value_counts())

print("\nVALIDATION:")
for label in ['ADD_ALLOWED', 'ADD_NEUTRAL', 'NO_ADD']:
    subset = df[df['regime_label'] == label]
    if len(subset) > 0:
        avg_r = subset['r_multiple'].mean()
        wr = (subset['r_multiple'] > 0).mean() * 100
        print(f"  {label}: {len(subset)} trades, Avg R={avg_r:.2f}, Win Rate={wr:.0f}%")

# Check if makes sense
add_r = df[df['regime_label'] == 'ADD_ALLOWED']['r_multiple'].mean()
no_r = df[df['regime_label'] == 'NO_ADD']['r_multiple'].mean()
print(f"\nQuality Check: ADD_ALLOWED R ({add_r:.2f}) vs NO_ADD R ({no_r:.2f})")
if add_r > no_r:
    print("PASS: Structural features identify favorable conditions")
else:
    print("WARNING: Features may need revision")

# Save
df.to_csv('research/ml_position_sizing/data/labeled_regimes.csv', index=False)
print(f"\nSaved to labeled_regimes.csv")
