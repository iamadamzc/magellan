"""PNL comparison"""
import pandas as pd

df = pd.read_csv('research/ml_position_sizing/data/labeled_regimes_v2.csv')

print('='*80)
print('PNL COMPARISON - CLEAN DATA')
print('='*80)

print('\nBASELINE (No ML):')
print(f'  Avg PnL: {df["pnl_pct"].mean():+.2f}%')
print(f'  Total PnL (sum): {df["pnl_pct"].sum():+.2f}%')
print(f'  Win Rate: {(df["pnl_pct"] > 0).mean()*100:.1f}%')

print('\nBY REGIME:')
for regime in ['ADD_ALLOWED', 'ADD_NEUTRAL', 'NO_ADD']:
    subset = df[df['regime_label_v2'] == regime]
    print(f'\n{regime} ({len(subset)} trades):')
    print(f'  Avg PnL: {subset["pnl_pct"].mean():+.2f}%')
    print(f'  Total PnL: {subset["pnl_pct"].sum():+.2f}%')
    print(f'  Win Rate: {(subset["pnl_pct"] > 0).mean()*100:.1f}%')

print('\n' + '='*80)
print('ML-WEIGHTED PNL (capital allocation):')
print('='*80)

add_allowed = df[df['regime_label_v2'] == 'ADD_ALLOWED']
add_neutral = df[df['regime_label_v2'] == 'ADD_NEUTRAL']
no_add = df[df['regime_label_v2'] == 'NO_ADD']

# Weighted by capital allocation
weighted_pnl = (
    add_allowed['pnl_pct'].mean() * 1.0 * len(add_allowed) +
    add_neutral['pnl_pct'].mean() * 0.8 * len(add_neutral) +
    no_add['pnl_pct'].mean() * 0.5 * len(no_add)
) / (
    1.0 * len(add_allowed) + 
    0.8 * len(add_neutral) + 
    0.5 * len(no_add)
)

print(f'\n  Baseline avg: {df["pnl_pct"].mean():+.2f}%')
print(f'  ML-weighted avg: {weighted_pnl:+.2f}%')
print(f'  Improvement: {weighted_pnl - df["pnl_pct"].mean():+.2f}% ({(weighted_pnl/df["pnl_pct"].mean()-1)*100:+.1f}%)')

print('\n' + '='*80)
print('COMPARISON TO LOOKAHEAD:')
print('='*80)

# From earlier comparison
lookahead_pnl = 2.45
baseline_pnl = df["pnl_pct"].mean()

print(f'\n  Lookahead (cheating): +{lookahead_pnl:.2f}%')
print(f'  Baseline (clean): {baseline_pnl:+.2f}%')
print(f'  ML-Enhanced (clean): {weighted_pnl:+.2f}%')
print(f'\n  ML vs Lookahead: {weighted_pnl - lookahead_pnl:+.2f}% ({(weighted_pnl/lookahead_pnl-1)*100:+.1f}%)')
