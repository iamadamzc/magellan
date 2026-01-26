"""
Debug: Why are futures returning 0 trades?
Check the data and filters step by step
"""
import pandas as pd
from pathlib import Path

# Check the cached futures data
data_dir = Path('data/cache/equities')

futures = ['ES', 'CL', 'NG', 'HG', 'KC']

print("="*80)
print("FUTURES DATA DIAGNOSTIC")
print("="*80)

for symbol in futures:
    cache_file = data_dir / f"{symbol}_1min_20240101_20241231.parquet"
    
    print(f"\n{symbol}:")
    print("-"*40)
    
    if cache_file.exists():
        df = pd.read_parquet(cache_file)
        
        print(f"✅ Total bars: {len(df):,}")
        print(f"   Date range: {df.index.min()} to {df.index.max()}")
        
        # Check RTH hours
        df['hour'] = df.index.hour
        rth_mask = (df['hour'] >= 9) & (df['hour'] < 17)
        rth_bars = df[rth_mask]
        
        print(f"   RTH bars (9-17): {len(rth_bars):,}")
        
        if len(rth_bars) > 0:
            print(f"   RTH date range: {rth_bars.index.min()} to {rth_bars.index.max()}")
            
            # Check for first day of data with enough bars for OR
            df['date'] = df.index.date
            rth_bars['date'] = rth_bars.index.date
            
            for date in sorted(rth_bars['date'].unique())[:5]:
                day_data = rth_bars[rth_bars['date'] == date]
                print(f"   {date}: {len(day_data)} RTH bars, first bar at {day_data.index[0].strftime('%H:%M')}")
                
                # Check if has OR period (first 10 minutes)
                day_data['minutes_since_9am'] = (day_data.index.hour - 9) * 60 + day_data.index.minute
                or_bars = day_data[day_data['minutes_since_9am'] <= 10]
                print(f"      OR period bars: {len(or_bars)}")
        else:
            print(f"   ⚠️  No RTH bars!")
    else:
        print(f"❌ No cache file")

print(f"\n{'='*80}\n")
