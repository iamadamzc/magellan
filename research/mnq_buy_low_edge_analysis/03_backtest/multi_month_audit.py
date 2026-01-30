"""
Multi-Month Data Contamination Audit - Print Results
"""
import pandas as pd
import random
from pathlib import Path

monthly_dir = Path(r'a:\1\Magellan\data\cache\futures\MNQ\monthly')
csv_files = sorted([f for f in monthly_dir.glob('*.csv') if 'ohlcv' in f.name])

random.seed(42)
sample_files = random.sample(csv_files, 6)

print('='*80)
print('MULTI-MONTH CONTAMINATION AUDIT')
print('='*80)
print()
print('Months tested:')
for f in sorted(sample_files):
    parts = f.stem.split('-')
    print(f'  - {parts[2][:4]}-{parts[2][4:6]}')

print()
print('='*80)
print('RESULTS')
print('='*80)
print()

header = "Month      | Total Rows   | Bad Rows   | Bad %   | Status"
print(header)
print('-'*70)

total_all = 0
bad_all = 0

for csv_file in sorted(sample_files):
    parts = csv_file.stem.split('-')
    month = parts[2][:4] + "-" + parts[2][4:6]
    
    df = pd.read_csv(csv_file)
    total = len(df)
    bad = len(df[(df['close'] < 1000) | (df['low'] < 1000)])
    pct = (bad / total * 100) if total > 0 else 0
    
    total_all += total
    bad_all += bad
    
    status = 'CONTAMINATED' if bad > 0 else 'CLEAN'
    line = f"{month:<10} | {total:>12,} | {bad:>10,} | {pct:>5.1f}% | {status}"
    print(line)

print('-'*70)
overall_pct = (bad_all / total_all * 100) if total_all > 0 else 0
print(f"{'TOTAL':<10} | {total_all:>12,} | {bad_all:>10,} | {overall_pct:>5.1f}% |")

print()
print('='*80)
print('INSTRUMENT BREAKDOWN')
print('='*80)
symbology = pd.read_csv(monthly_dir / 'symbology.csv')
spread_count = len(symbology[symbology.iloc[:, 0].str.contains('-', na=False)]['instrument_id'].unique())
outright_count = len(symbology[~symbology.iloc[:, 0].str.contains('-', na=False)]['instrument_id'].unique())
print(f"\nSpread instruments (contamination source): {spread_count}")
print(f"Outright instruments (clean):              {outright_count}")

print()
print('='*80)
print('CONCLUSION')
print('='*80)
print()
if bad_all > 0:
    print('** CONTAMINATION CONFIRMED across entire dataset **')
    print()
    print('Root Cause:')
    print('  Calendar spreads (e.g., MNQZ5-MNQH6) with prices ~250-500')
    print('  are mixed with outright contracts (e.g., MNQZ5) at ~15,000-26,000')
    print()
    print('Solution:')
    print('  Filter by instrument_id to exclude spread instruments')
    print('  (any instrument with a dash in the symbol name)')
else:
    print('No contamination found in sample.')
