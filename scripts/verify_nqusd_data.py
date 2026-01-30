"""
Verify downloaded NQUSD 1-minute data
"""

import pandas as pd
from pathlib import Path

futures_dir = Path("data/cache/futures")

print("=" * 80)
print("NQUSD 1-MINUTE DATA VERIFICATION")
print("=" * 80)

files = sorted(futures_dir.glob("NQUSD_1Min*.parquet"))

total_bars = 0
for file in files:
    df = pd.read_parquet(file)
    total_bars += len(df)
    
    print(f"\n{file.name}:")
    print(f"  Bars: {len(df):,}")
    print(f"  Date Range: {df.index.min()} to {df.index.max()}")
    print(f"  Columns: {list(df.columns)}")
    print(f"  Sample data:")
    print(df.head(3).to_string())

print(f"\n" + "=" * 80)
print(f"TOTAL: {total_bars:,} bars across {len(files)} files")
print("=" * 80)

# Show the most recent data
if len(files) > 0:
    latest_df = pd.read_parquet(files[-1])
    print(f"\nMost recent bars:")
    print(latest_df.tail(5).to_string())
