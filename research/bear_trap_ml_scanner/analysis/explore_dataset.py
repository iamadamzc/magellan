"""
Quick EDA: Exploring the Q4 2024 selloff dataset
"""
import pandas as pd
import numpy as np
from pathlib import Path

# Load dataset
data_path = Path(__file__).parent.parent / "data" / "raw" / "selloffs_alpaca_q4_2024.csv"
df = pd.read_csv(data_path)

print("="*80)
print("BEAR TRAP ML SCANNER - DATASET EXPLORATION")
print("="*80)
print(f"\n📊 Dataset Overview")
print(f"   Total events: {len(df):,}")
print(f"   Unique symbols: {df['symbol'].nunique()}")
print(f"   Unique dates: {df['date'].nunique()}")
print(f"   Date range: {df['date'].min()} to {df['date'].max()}")

print(f"\n🔥 Drop Magnitude Statistics")
print(df['drop_pct'].describe())

print(f"\n📈 Events by Symbol")
symbol_counts = df['symbol'].value_counts()
for symbol, count in symbol_counts.items():
    pct = 100 * count / len(df)
    avg_drop = df[df['symbol'] == symbol]['drop_pct'].mean()
    max_drop = df[df['symbol'] == symbol]['drop_pct'].min()
    print(f"   {symbol:6} {count:4} events ({pct:5.1f}%)  Avg: {avg_drop:6.2f}%  Max: {max_drop:6.2f}%")

print(f"\n📅 Events by Month")
df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
monthly = df.groupby('month').size()
for month, count in monthly.items():
    print(f"   {month}: {count:4} events")

print(f"\n⏰ Time of Day Distribution")
df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
hourly = df.groupby('hour').size().sort_index()
for hour, count in hourly.items():
    bar = '█' * (count // 10)
    print(f"   {hour:02d}:00  {count:4} {bar}")

print(f"\n🏆 Top 20 Biggest Drops")
top20 = df.nsmallest(20, 'drop_pct')[['symbol', 'date', 'timestamp', 'drop_pct', 'low', 'session_open']]
print(top20.to_string(index=False))

print(f"\n💡 Key Insights:")
print(f"   - MULN dominates with {symbol_counts.iloc[0]} events ({100*symbol_counts.iloc[0]/len(df):.1f}%)")
print(f"   - Average drop: {df['drop_pct'].mean():.2f}%")
print(f"   - Biggest drop: {df['drop_pct'].min():.2f}%")
print(f"   - Most active month: {monthly.idxmax()} with {monthly.max()} events")

print("\n" + "="*80)
print("✅ Dataset is ready for feature engineering!")
print("="*80 + "\n")
