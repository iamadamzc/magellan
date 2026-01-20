"""
Analyze disaster concentration by time of day.
Test combined time + ML filtering strategies.
"""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
import matplotlib.pyplot as plt

# Load disaster model and training data
model_path = Path('research/ml_position_sizing/models/bear_trap_disaster_filter.pkl')
with open(model_path, 'rb') as f:
    model_data = pickle.load(f)

data_path = Path('research/ml_position_sizing/data/labeled_regimes_v2.csv')
df = pd.read_csv(data_path)

# Add disaster label
df['is_disaster'] = (df['r_multiple'] < -0.5).astype(int)

# Parse entry time
df['entry_datetime'] = pd.to_datetime(df['entry_date'])
df['entry_hour'] = df['entry_datetime'].dt.hour
df['entry_minute'] = df['entry_datetime'].dt.minute

print("="*70)
print("DISASTER CONCENTRATION BY TIME OF DAY")
print("="*70)

# Hourly analysis
hourly = df.groupby('entry_hour').agg({
    'is_disaster': ['sum', 'mean', 'count'],
    'r_multiple': 'mean'
}).round(3)

hourly.columns = ['Disasters', 'Disaster_Rate', 'Total_Trades', 'Avg_R']

print("\nHourly Breakdown:")
print(hourly)

# Morning vs Afternoon
morning = df[df['entry_hour'] < 12]
midday = df[(df['entry_hour'] >= 12) & (df['entry_hour'] < 14)]
afternoon = df[df['entry_hour'] >= 14]

print(f"\n{'='*70}")
print("TIME PERIOD ANALYSIS")
print(f"{'='*70}")

for name, subset in [('Morning (9:30-12)', morning), 
                      ('Midday (12-2pm)', midday),
                      ('Afternoon (2pm+)', afternoon)]:
    disaster_rate = subset['is_disaster'].mean() * 100
    avg_r = subset['r_multiple'].mean()
    count = len(subset)
    print(f"\n{name}:")
    print(f"  Trades: {count}")
    print(f"  Disaster Rate: {disaster_rate:.1f}%")
    print(f"  Avg R: {avg_r:+.2f}")

# Test simple time rules
print(f"\n{'='*70}")
print("SIMPLE TIME FILTER BACKTEST (Training Data)")
print(f"{'='*70}")

strategies = {
    'Baseline (All Trades)': df,
    'Skip After 2pm': df[df['entry_hour'] < 14],
    'Skip After 3pm': df[df['entry_hour'] < 15],
    'Skip 12-2pm (Lunch)': df[(df['entry_hour'] < 12) | (df['entry_hour'] >= 14)],
}

for name, subset in strategies.items():
    avg_r = subset['r_multiple'].mean()
    disaster_rate = subset['is_disaster'].mean() * 100
    count = len(subset)
    
    print(f"\n{name}:")
    print(f"  Trades: {count}")
    print(f"  Avg R: {avg_r:+.2f}")
    print(f"  Disaster Rate: {disaster_rate:.1f}%")
    print(f"  Total R: {avg_r * count:+.1f}R")

# Combined strategy simulation
print(f"\n{'='*70}")
print("COMBINED TIME + ML STRATEGIES")
print(f"{'='*70}")

# Strategy 1: Skip after 2pm
strat1 = df[df['entry_hour'] < 14]
print(f"\nStrategy 1: Skip After 2pm (Simple)")
print(f"  Trades: {len(strat1)}")
print(f"  Avg R: {strat1['r_multiple'].mean():+.2f}")
print(f"  Total R: {strat1['r_multiple'].sum():+.1f}R")

# Strategy 2: ML filter 0.5 + Skip after 2pm
# (This would require re-running simulation, just showing concept)
print(f"\nStrategy 2: ML (0.5) + Skip After 2pm (Theoretical)")
print(f"  Would combine 27 ML rejections + {len(df[df['entry_hour'] >= 14])} time rejections")
print(f"  Expected: Further 5-10% improvement if filters are orthogonal")

# Strategy 3: Adaptive threshold by time
# Morning: 0.6 (less strict), Afternoon: 0.4 (more strict)
print(f"\nStrategy 3: Adaptive Threshold by Time (Concept)")
print(f"  Morning (< 2pm): Use threshold 0.6 (allow more risk)")
print(f"  Afternoon (>= 2pm): Use threshold 0.4 (very strict)")
print(f"  Rationale: Afternoon disasters are cheaper to avoid")

# Best hour identification
best_hours = hourly.nsmallest(3, 'Disaster_Rate')
worst_hours = hourly.nlargest(3, 'Disaster_Rate')

print(f"\n{'='*70}")
print("OPTIMAL TRADING WINDOWS")
print(f"{'='*70}")
print(f"\nBest Hours (Lowest Disaster Rate):")
for hour in best_hours.index:
    rate = best_hours.loc[hour, 'Disaster_Rate'] * 100
    avg_r = best_hours.loc[hour, 'Avg_R']
    print(f"  {hour:02d}:00 - {rate:.1f}% disasters, {avg_r:+.2f}R avg")

print(f"\nWorst Hours (Highest Disaster Rate):")
for hour in worst_hours.index:
    rate = worst_hours.loc[hour, 'Disaster_Rate'] * 100
    avg_r = worst_hours.loc[hour, 'Avg_R']
    print(f"  {hour:02d}:00 - {rate:.1f}% disasters, {avg_r:+.2f}R avg")
