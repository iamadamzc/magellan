import pandas as pd

df = pd.read_csv('research/bear_trap_ml_scanner/data/raw/dataset_b_out_of_sample.csv')

print('\n' + '='*80)
print('DATASET B - OUT-OF-SAMPLE TEST SET')
print('='*80)
print(f'Total events: {len(df):,}')
print(f'Unique symbols: {df["symbol"].nunique()}')
print(f'Date range: {df["date"].min()} to {df["date"].max()}')

print(f'\n📊 Events by Year:')
yearly = pd.to_datetime(df['date']).dt.year.value_counts().sort_index()
for year, count in yearly.items():
    print(f'  {year}: {count:4} events')

print(f'\n📈 Top 15 Symbols by Event Count:')
symbol_counts = df['symbol'].value_counts().head(15)
for symbol, count in symbol_counts.items():
    pct = 100 * count / len(df)
    print(f'  {symbol:6} {count:4} events ({pct:5.1f}%)')

print(f'\n📉 Drop % Statistics:')
print(df['drop_pct'].describe())

print('\n' + '='*80)
print('✅ DATASET B COLLECTION COMPLETE!')
print('='*80 + '\n')
