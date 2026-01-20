"""Compare ML results to baseline extraction"""
import pandas as pd

df = pd.read_csv('research/ml_position_sizing/data/bear_trap_trades_2020_2024.csv')
df_2024 = df[df['entry_date'].str.startswith('2024')]

print('='*80)
print('2024 COMPARISON: ML vs BASELINE')
print('='*80)

print('\nBASELINE (from extraction, all trades):')
print(f'  Total trades: {len(df_2024)}')
print(f'  Win rate: {(df_2024["r_multiple"] > 0).mean()*100:.1f}%')
print(f'  Avg R: {df_2024["r_multiple"].mean():.2f}')
print(f'  Avg PnL: {df_2024["pnl_pct"].mean():.2f}%')

print('\nML-ENHANCED (live test):')
print(f'  Total trades: 247')
print(f'  Win rate: 38.0%')
print(f'  Avg R: +0.02')
print(f'  Avg PnL: -5.46%')

print('\n' + '='*80)
print('BY SYMBOL:')
print('='*80)

for sym in ['AMC', 'MULN', 'NKLA']:
    subset = df_2024[df_2024['symbol'] == sym]
    if len(subset) > 0:
        print(f'\n{sym}:')
        print(f'  Baseline: {len(subset)} trades, WR={((subset["r_multiple"]>0).mean()*100):.0f}%, R={subset["r_multiple"].mean():.2f}')

print('\n  ML (AMC): 46 trades, WR=46%, R=-0.02')
print('  ML (MULN): 131 trades, WR=41%, R=+0.24')
print('  ML (NKLA): 70 trades, WR=27%, R=-0.15')

print('\n' + '='*80)
print('DIAGNOSIS:')
print('='*80)
print('\nThe ML classifier is NOT matching the training data.')
print('The simple decision tree in the live code is too different from')
print('the pandas-based labeling we did on the extracted trades.')
print('\nWe need to either:')
print('1. Train an actual ML model (sklearn) and save it')
print('2. Use the exact same pandas logic from labeling')
print('3. Simplify to just use the extracted labels directly')
