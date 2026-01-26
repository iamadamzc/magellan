import pandas as pd
from datetime import datetime

# Check Dataset A progress
df = pd.read_csv('research/bear_trap_ml_scanner/data/raw/dataset_a_partial.csv')

print('\n' + '='*80)
print('DATASET A - COLLECTION PROGRESS')
print('='*80)
print(f'Events collected so far: {len(df):,}')
print(f'Unique symbols processed: {df["symbol"].nunique()}')
print(f'Date range: {df["date"].min()} to {df["date"].max()}')

print(f'\nTop 10 Symbols by Event Count:')
for symbol, count in df['symbol'].value_counts().head(10).items():
    print(f'  {symbol:6} {count:4} events')

# Estimate progress
# We're processing 125 symbols for Dataset A
symbols_done = df['symbol'].nunique()
total_symbols_a = 125
pct_complete_a = (symbols_done / total_symbols_a) * 100

print(f'\n📊 Dataset A Progress:')
print(f'  Symbols: {symbols_done}/125 ({pct_complete_a:.1f}%)')
print(f'  Events per symbol avg: {len(df)/symbols_done:.0f}')

# Estimate total for Dataset A
estimated_total_a = (len(df) / symbols_done) * total_symbols_a if symbols_done > 0 else 0
print(f'  Estimated total for Dataset A: ~{estimated_total_a:,.0f} events')

# Time estimate
# Started at 07:07, now it's 12:51 = 5h 44min = 344 minutes
elapsed_minutes = 344
symbols_per_minute = symbols_done / elapsed_minutes if elapsed_minutes > 0 else 0
remaining_symbols_a = total_symbols_a - symbols_done
eta_minutes_a = remaining_symbols_a / symbols_per_minute if symbols_per_minute > 0 else 0
eta_hours_a = eta_minutes_a / 60

print(f'\n⏱️  Time Estimates:')
print(f'  Elapsed: 5h 44min')
print(f'  Rate: {symbols_per_minute:.2f} symbols/minute')
print(f'  Dataset A ETA: {eta_hours_a:.1f} hours')
print(f'  Dataset B ETA: ~{eta_hours_a:.1f} hours (same size)')
print(f'  Total completion ETA: ~{eta_hours_a*2:.1f} hours from now')

current_time = datetime.now()
print(f'\n  Current time: {current_time.strftime("%I:%M %p")}')
print(f'  Estimated completion: ~{(current_time.hour + int(eta_hours_a*2)) % 24:02d}:{current_time.minute:02d}')

print('\n' + '='*80)
