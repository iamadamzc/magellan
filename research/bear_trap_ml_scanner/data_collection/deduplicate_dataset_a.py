"""
Deduplicate Dataset A - Apply First-Cross Logic

Takes the raw 9,278 events and keeps only FIRST occurrence per symbol per day.
This matches the Dataset B collection logic.

Author: Magellan Research Team
Date: January 22, 2026
"""

import pandas as pd
from pathlib import Path

# Paths
data_dir = Path('research/bear_trap_ml_scanner/data/raw')
input_file = data_dir / 'selloffs_full_2022_2024.csv'
output_file = data_dir / 'dataset_a_validated_deduped.csv'

print("\n" + "="*80)
print("DATASET A DEDUPLICATION")
print("="*80)

# Load raw data
df = pd.read_csv(input_file)
print(f"\nOriginal events: {len(df):,}")
print(f"Unique symbol-date pairs: {df.groupby(['symbol', 'date']).ngroups:,}")

# Sort by timestamp to ensure we get the FIRST occurrence
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values(['symbol', 'date', 'timestamp'])

# Keep only first occurrence per symbol per day
df_deduped = df.groupby(['symbol', 'date']).first().reset_index()

# Add metadata
df_deduped['event_type'] = 'first_cross'
df_deduped['dataset'] = 'A'

# Convert timestamp back to string for consistency
df_deduped['timestamp'] = df_deduped['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

print(f"\nAfter deduplication: {len(df_deduped):,}")
print(f"Reduction: {len(df) - len(df_deduped):,} events removed ({100*(len(df)-len(df_deduped))/len(df):.1f}%)")

# Save
df_deduped.to_csv(output_file, index=False)
print(f"\n💾 Saved to: {output_file}")

# Summary stats
print(f"\n📊 Dataset A Summary:")
print(f"  Events: {len(df_deduped):,}")
print(f"  Symbols: {df_deduped['symbol'].nunique()}")
print(f"  Date range: {df_deduped['date'].min()} to {df_deduped['date'].max()}")

print(f"\n📈 Events by Year:")
df_deduped['year'] = pd.to_datetime(df_deduped['date']).dt.year
yearly = df_deduped.groupby('year').size()
for year, count in yearly.items():
    print(f"  {year}: {count:4} events")

print(f"\n📈 Events by Symbol:")
symbol_counts = df_deduped['symbol'].value_counts()
for symbol, count in symbol_counts.items():
    pct = 100 * count / len(df_deduped)
    print(f"  {symbol:6} {count:4} events ({pct:5.1f}%)")

print(f"\n📉 Drop % Statistics:")
print(df_deduped['drop_pct'].describe())

print("\n" + "="*80)
print("✅ DATASET A DEDUPLICATION COMPLETE!")
print("="*80 + "\n")
