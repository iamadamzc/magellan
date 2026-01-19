"""
Check cached parquet files directly to see what data we have
"""
import pandas as pd
from pathlib import Path

cache_dir = Path('data/cache/equities')

symbols = ['ES', 'CL', 'NG', 'HG', 'KC']

print("="*80)
print("CACHED DATA ANALYSIS")
print("="*80)

for symbol in symbols:
    files = list(cache_dir.glob(f"{symbol}_1min_*.parquet"))
    
    if not files:
        print(f"\n{symbol}: No cache files")
        continue
    
    # Load most recent
    latest = sorted(files)[-1]
    df = pd.read_parquet(latest)
    
    print(f"\n{symbol}:")
    print(f"  File: {latest.name}")
    print(f"  Total bars: {len(df):,}")
    print(f"  Date range: {df.index.min()} to {df.index.max()}")
    
    # Check RTH
    df['hour'] = df.index.hour
    rth = df[(df['hour'] >= 9) & (df['hour'] < 17)]
    print(f"  RTH bars (9-17): {len(rth):,}")
    
    if len(rth) > 0:
        print(f"  RTH range: {rth.index.min()} to {rth.index.max()}")
        
        # Check first few days
        rth['date'] = rth.index.date
        unique_dates = sorted(rth['date'].unique())
        
        print(f"  Trading days with RTH data: {len(unique_dates)}")
        print(f"  First RTH day: {unique_dates[0]} ({len(rth[rth['date']==unique_dates[0]])} bars)")
        
        # Check for 9:00-9:10 period on first day
        first_day = rth[rth['date'] == unique_dates[0]]
        morning_bars = first_day[(first_day.index.hour == 9) & (first_day.index.minute <= 10)]
        
        print(f"  9:00-9:10 bars on first day: {len(morning_bars)}")
        if len(morning_bars) > 0:
            print(f"    ✅ Has OR period data")
        else:
            first_bar_time = first_day.index[0].strftime('%H:%M') if len(first_day) > 0 else 'N/A'
            print(f"    ❌ No OR period! First bar at {first_bar_time}")
    else:
        print(f"  ❌ No RTH data!")

print(f"\n{'='*80}\n")
