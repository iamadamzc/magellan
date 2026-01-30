"""
December 2025 Data Contamination Audit
"""
import pandas as pd
pd.set_option('display.max_columns', 10)
pd.set_option('display.width', 200)

# Load December 2025 data
df = pd.read_csv(r'a:\1\Magellan\data\cache\futures\MNQ\monthly\glbx-mdp3-20251201-20251231.ohlcv-1m.csv')

print('='*80)
print('DECEMBER 2025 DATA CONTAMINATION AUDIT')
print('='*80)

print(f'\nTotal rows: {len(df):,}')

# Find rows with suspiciously low prices
bad_rows = df[(df['close'] < 1000) | (df['low'] < 1000)]
print(f'Contaminated rows (close or low < 1000): {len(bad_rows):,}')

# Show only the contaminated rows
if len(bad_rows) > 0:
    print('\n' + '='*80)
    print('CONTAMINATED ENTRIES (Prices ~250 instead of ~25000)')
    print('='*80)
    print()
    for idx, row in bad_rows.head(15).iterrows():
        ts = row['ts_event'][:19]
        o = row['open']
        h = row['high']
        l = row['low']
        c = row['close']
        v = row['volume']
        print(f"Row {idx}: {ts} | O: {o:>10.2f} | H: {h:>10.2f} | L: {l:>10.2f} | C: {c:>10.2f} | Vol: {v}")
    
    if len(bad_rows) > 15:
        print(f'\n... and {len(bad_rows) - 15} more')
    
    # Unique instruments
    print('\n' + '='*80)
    print('INSTRUMENTS WITH BAD DATA')
    print('='*80)
    print(bad_rows['instrument_id'].value_counts())
    
    # Check specific dates
    print('\n' + '='*80)
    print('DATES FROM KILL LIST')
    print('='*80)
    for target_date in ['2025-12-11', '2025-12-12', '2025-12-15']:
        mask = bad_rows['ts_event'].str.startswith(target_date)
        if mask.any():
            subset = bad_rows[mask]
            print(f'\n{target_date}: {len(subset)} bad rows')
            for idx, row in subset.head(3).iterrows():
                ts = row['ts_event'][:19]
                c = row['close']
                inst = row.get('instrument_id', 'N/A')
                print(f"  {ts} | Close: {c:.2f} | Instrument: {inst}")
