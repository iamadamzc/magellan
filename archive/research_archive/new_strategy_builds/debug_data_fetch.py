"""
Debug: Check what's happening with data fetches
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache

# Test a few specific symbols we know should work
test_symbols = [
    'GCUSD',   # Gold (commodity)
    'NGUSD',   # Natural Gas (commodity)
    'CLUSD',   # Crude Oil (commodity)
    'KCUSX',   # Coffee (commodity)
    'EURUSD',  # EUR/USD (forex)
    'ESUSD',   # S&P 500 futures
]

print("="*80)
print("DATA FETCH DEBUG")
print("="*80)

for symbol in test_symbols:
    print(f"\n{symbol}:")
    print("-" * 40)
    
    try:
        df = cache.get_or_fetch_equity(symbol, '1min', '2024-01-01', '2024-12-31')
        
        if df is None:
            print(f"❌ Returned None")
        elif len(df) == 0:
            print(f"❌ Empty dataframe")
        else:
            print(f"✅ {len(df):,} bars")
            print(f"   Date range: {df.index.min()} to {df.index.max()}")
            print(f"   Columns: {list(df.columns)}")
            
            # Check RTH hours
            hour_dist = df.index.hour.value_counts().sort_index()
            rth_hours = hour_dist[(hour_dist.index >= 9) & (hour_dist.index < 17)]
            if len(rth_hours) > 0:
                print(f"   RTH bars (9-5): {rth_hours.sum():,}")
            else:
                print(f"   ⚠️  No RTH data (9-5)")
            
            # Check for first 10 bars
            first_day = df[df.index.date == df.index.date[0]]
            if len(first_day) >= 10:
                print(f"   First day: {len(first_day)} bars starting at {first_day.index[0].strftime('%H:%M')}")
            else:
                print(f"   ⚠️  First day only has {len(first_day)} bars")
    
    except Exception as e:
        print(f"❌ Exception: {str(e)[:100]}")

print(f"\n{'='*80}\n")
