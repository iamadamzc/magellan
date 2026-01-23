import pandas as pd

df = pd.read_csv('research/bear_trap_ml_scanner/data/processed/selloffs_full_2022_2024_features.csv')

print('\n' + '='*80)
print('ENRICHED DATASET ANALYSIS')
print('='*80)
print(f'Total events: {len(df):,}')
print(f'Total features: {len(df.columns)}')
print(f'Date range: {df["date"].min()} to {df["date"].max()}')

print(f'\n📊 Feature Completeness:')
key_features = ['pct_from_52w_high', 'pct_from_52w_low', 'distance_from_200sma', 
                'distance_from_50sma', 'distance_from_20sma', 'spy_change_day']
for col in key_features:
    if col in df.columns:
        valid_pct = (1 - df[col].isna().mean()) * 100
        print(f'  {col:30} {valid_pct:5.1f}% complete')

print(f'\n📈 Sample Data (first 5 rows):')
sample_cols = ['symbol', 'date', 'drop_pct', 'pct_from_52w_high', 'distance_from_200sma', 'above_200sma', 'time_bucket']
print(df[sample_cols].head(5).to_string())

print(f'\n🎯 Statistics:')
print(df[['drop_pct', 'pct_from_52w_high', 'distance_from_200sma']].describe())

print('\n' + '='*80)
print('✅ DATASET READY FOR ML TRAINING!')
print('='*80 + '\n')
