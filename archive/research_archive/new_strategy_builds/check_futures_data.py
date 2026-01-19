"""
Check which futures have valid data and their trading hours
"""
import pandas as pd
from pathlib import Path

data_dir = Path('data/cache/equities')

# All major futures to check
futures_list = [
    # Indices
    'ES', 'NQ', 'YM', 'RTY',
    # Energies
    'CL', 'NG', 'RB', 'HO',
    # Metals
    'GC', 'SI', 'HG', 'PL',
    # Ags
    'ZC', 'ZS', 'ZW', 'ZL', 'KC', 'SB', 'CT',
    # Rates
    'ZN', 'ZB', 'ZF', 'ZT',
    # FX
    '6E', '6J', '6B', '6C',
    # Meats
    'HE', 'LE', 'GF',
]

print("="*80)
print("FUTURES DATA CHECK")
print("="*80)

valid_futures = []
invalid_futures = []

for symbol in futures_list:
    # Check for cached data
    pattern = f"{symbol}_1min_*.parquet"
    files = list(data_dir.glob(pattern))
    
    if files:
        # Load most recent file
        latest = sorted(files)[-1]
        try:
            df = pd.read_parquet(latest)
            
            # Get hour distribution
            hour_counts = df.index.hour.value_counts().sort_index()
            rth_hours = hour_counts[(hour_counts.index >= 9) & (hour_counts.index < 17)]
            total_rth = rth_hours.sum()
            
            # Check if has meaningful RTH data
            if total_rth > 1000:  # At least 1000 RTH bars
                rth_start = rth_hours.index.min()
                rth_end = rth_hours.index.max()
                
                print(f"✅ {symbol:6s} | {len(df):7,d} bars | RTH: {rth_start:02d}:00-{rth_end:02d}:00 ({total_rth:,} bars)")
                valid_futures.append({
                    'symbol': symbol,
                    'total_bars': len(df),
                    'rth_bars': total_rth,
                    'rth_start': rth_start,
                    'rth_end': rth_end
                })
            else:
                print(f"⚠️  {symbol:6s} | {len(df):7,d} bars | Limited RTH data ({total_rth} bars)")
                invalid_futures.append(symbol)
                
        except Exception as e:
            print(f"❌ {symbol:6s} | Error reading: {str(e)[:50]}")
            invalid_futures.append(symbol)
    else:
        print(f"❌ {symbol:6s} | No data file found")
        invalid_futures.append(symbol)

print(f"\n{'='*80}")
print(f"SUMMARY")
print(f"{'='*80}")
print(f"Valid futures with RTH data: {len(valid_futures)}")
print(f"Invalid/missing: {len(invalid_futures)}")

if valid_futures:
    print(f"\n✅ READY TO TEST ({len(valid_futures)} symbols):")
    for f in valid_futures:
        print(f"   {f['symbol']}")
    
    # Save list
    import json
    with open('research/new_strategy_builds/valid_futures_list.json', 'w') as f:
        json.dump([x['symbol'] for x in valid_futures], f)
    print(f"\n📁 Saved to: valid_futures_list.json")

if invalid_futures:
    print(f"\n❌ SKIP THESE ({len(invalid_futures)} symbols):")
    print(f"   {', '.join(invalid_futures)}")
