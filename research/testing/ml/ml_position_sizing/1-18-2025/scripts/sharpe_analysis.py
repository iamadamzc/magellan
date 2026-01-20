"""Sharpe ratio calculation"""
import pandas as pd
import numpy as np

df = pd.read_csv('research/ml_position_sizing/data/labeled_regimes_v2.csv')

print('='*80)
print('SHARPE RATIO ANALYSIS')
print('='*80)

# Calculate returns per trade
df['return_pct'] = df['pnl_pct'] / 100  # Convert to decimal

print('\nBASELINE (No ML):')
baseline_mean = df['return_pct'].mean()
baseline_std = df['return_pct'].std()
baseline_sharpe = (baseline_mean / baseline_std) * np.sqrt(252) if baseline_std > 0 else 0

print(f'  Mean return: {baseline_mean*100:.2f}%')
print(f'  Std dev: {baseline_std*100:.2f}%')
print(f'  Sharpe (annualized): {baseline_sharpe:.2f}')

print('\nBY REGIME:')
for regime in ['ADD_ALLOWED', 'ADD_NEUTRAL', 'NO_ADD']:
    subset = df[df['regime_label_v2'] == regime]
    if len(subset) > 0:
        mean_ret = subset['return_pct'].mean()
        std_ret = subset['return_pct'].std()
        sharpe = (mean_ret / std_ret) * np.sqrt(252) if std_ret > 0 else 0
        
        print(f'\n{regime}:')
        print(f'  Mean return: {mean_ret*100:.2f}%')
        print(f'  Std dev: {std_ret*100:.2f}%')
        print(f'  Sharpe: {sharpe:.2f}')

print('\n' + '='*80)
print('ML-ENHANCED SHARPE:')
print('='*80)

# For ML, we need to weight by capital allocation
add_allowed = df[df['regime_label_v2'] == 'ADD_ALLOWED']
add_neutral = df[df['regime_label_v2'] == 'ADD_NEUTRAL']
no_add = df[df['regime_label_v2'] == 'NO_ADD']

# Create weighted returns
ml_returns = []
for idx, row in df.iterrows():
    regime = row['regime_label_v2']
    ret = row['return_pct']
    
    if regime == 'ADD_ALLOWED':
        weight = 1.0
    elif regime == 'ADD_NEUTRAL':
        weight = 0.8
    else:  # NO_ADD
        weight = 0.5
    
    ml_returns.append(ret * weight)

ml_returns = pd.Series(ml_returns)
ml_mean = ml_returns.mean()
ml_std = ml_returns.std()
ml_sharpe = (ml_mean / ml_std) * np.sqrt(252) if ml_std > 0 else 0

print(f'\n  Baseline Sharpe: {baseline_sharpe:.2f}')
print(f'  ML-Enhanced Sharpe: {ml_sharpe:.2f}')
print(f'  Improvement: {ml_sharpe - baseline_sharpe:+.2f} ({(ml_sharpe/baseline_sharpe-1)*100:+.1f}%)')

print('\n' + '='*80)
print('COMPARISON TO LOOKAHEAD:')
print('='*80)

# From earlier data
lookahead_sharpe = 0.02  # Estimated from old data

print(f'\n  Lookahead (cheating): {lookahead_sharpe:.2f}')
print(f'  Baseline (clean): {baseline_sharpe:.2f}')
print(f'  ML-Enhanced (clean): {ml_sharpe:.2f}')

if ml_sharpe > lookahead_sharpe:
    print(f'\n  ✅ ML BEATS LOOKAHEAD by {ml_sharpe - lookahead_sharpe:.2f}!')
else:
    print(f'\n  ML is {lookahead_sharpe - ml_sharpe:.2f} below lookahead')
