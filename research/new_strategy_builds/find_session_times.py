"""
Find the actual session start time for each commodity
Then test V19 with correct times
"""
import pandas as pd
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

cache_dir = Path('data/cache/equities')

symbols = ['ES', 'CL', 'NG', 'HG', 'PL', 'ZS', 'KC', 'SB', 'CC', 'HE', 'LE', 'GF']

print("="*80)
print("FINDING ACTUAL SESSION TIMES FOR EACH COMMODITY")
print("="*80)

session_times = {}

for symbol in symbols:
    files = list(cache_dir.glob(f"{symbol}_1min_*.parquet"))
    
    if not files:
        print(f"{symbol}: No cache - will fetch")
        continue
    
    df = pd.read_parquet(sorted(files)[-1])
    
    # Find earliest hour across all days
    df['date'] = df.index.date
    df['hour'] = df.index.hour
    df['minute'] = df.index.minute
    
    # Get first bar time for each day
    first_bars = df.groupby('date').first()
    
    # Find most common opening hour (mode)
    earliest_hour = first_bars['hour'].mode()[0] if len(first_bars) > 0 else None
    
    # For that hour, find median opening minute
    bars_at_earliest = df[df['hour'] == earliest_hour]
    earliest_minute = bars_at_earliest.groupby('date')['minute'].min().median() if len(bars_at_earliest) > 0 else 0
    
    session_times[symbol] = {
        'hour': int(earliest_hour),
        'minute': int(earliest_minute),
        'typical_open': f"{int(earliest_hour):02d}:{int(earliest_minute):02d}"
    }
    
    print(f"{symbol:4s}: Session typically starts at {session_times[symbol]['typical_open']}")

# Save to JSON for use in testing
import json
with open('research/new_strategy_builds/commodity_session_times.json', 'w') as f:
    json.dump(session_times, f, indent=2)

print(f"\n✅ Session times saved to commodity_session_times.json")
print(f"\n{'='*80}\n")
