"""
Diagnostic: Why is only Coffee generating trades?
Check what's different about KC vs other symbols
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_cache import cache

symbols_to_check = ['ES', 'CL', 'NG', 'HG', 'KC']

print("="*80)
print("WHY ONLY COFFEE? - DIAGNOSTIC")
print("="*80)

for symbol in symbols_to_check:
    print(f"\n{symbol}:")
    print("-"*40)
    
    df = cache.get_or_fetch_equity(symbol, '1min', '2024-01-02', '2024-01-05')
    
    if df is None or len(df) == 0:
        print("❌ No data")
        continue
    
    # Filter RTH
    df['hour'] = df.index.hour
    df['minute'] = df.index.minute
    rth = df[(df['hour'] >= 9) & (df['hour'] < 17)].copy()
    
    print(f"Total bars: {len(df)}, RTH bars: {len(rth)}")
    
    if len(rth) == 0:
        print("❌ No RTH data!")
        continue
    
    # Check by day
    rth['date'] = rth.index.date
    
    for date in sorted(rth['date'].unique())[:2]:  # First 2 days
        day = rth[rth['date'] == date].copy()
        
        print(f"\n  {date}:")
        print(f"    RTH bars: {len(day)}")
        print(f"    First bar: {day.index[0].strftime('%H:%M')}")
        print(f"    Last bar: {day.index[-1].strftime('%H:%M')}")
        
        # Check for OR period (9:00-9:10)
        day['minutes_since_9am'] = (day.index.hour - 9) * 60 + day.index.minute
        or_period = day[(day['minutes_since_9am'] >= 0) & (day['minutes_since_9am'] <= 10)]
        
        print(f"    OR period (9:00-9:10): {len(or_period)} bars")
        
        if len(or_period) >= 5:
            or_high = or_period['high'].max()
            or_low = or_period['low'].min()
            or_range = or_high - or_low
            or_range_pct = (or_range / or_low) * 100
            
            print(f"    OR range: {or_range:.4f} ({or_range_pct:.2f}%)")
            
            # Check for breakout in first hour (9:10-10:00)
            first_hour = day[(day['minutes_since_9am'] > 10) & (day['minutes_since_9am'] <= 60)]
            
            if len(first_hour) > 0:
                breakout_bars = first_hour[first_hour['close'] > or_high]
                print(f"    Breakout bars in first hour: {len(breakout_bars)}")
                
                if len(breakout_bars) > 0:
                    print(f"    ✅ Has breakout opportunity!")
                else:
                    print(f"    ❌ No breakout")
        else:
            print(f"    ❌ Insufficient OR bars")

print(f"\n{'='*80}\n")
