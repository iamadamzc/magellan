"""Detailed ML stats on clean data"""
import pandas as pd

df = pd.read_csv('research/ml_position_sizing/data/labeled_regimes_v2.csv')

print('='*80)
print('ML POSITION SIZING - DETAILED STATS (CLEAN DATA)')
print('='*80)

print('\nBASELINE (No ML):')
baseline_wr = (df['r_multiple'] > 0).mean() * 100
print(f'  Win Rate: {baseline_wr:.1f}%')
print(f'  Avg R: {df["r_multiple"].mean():+.3f}')
winners = df[df['r_multiple'] > 0]
losers = df[df['r_multiple'] < 0]
print(f'  Avg Winner: {winners["r_multiple"].mean():+.2f}R')
print(f'  Avg Loser: {losers["r_multiple"].mean():+.2f}R')

print('\nML-ENHANCED (by regime):')
print()

for regime in ['ADD_ALLOWED', 'ADD_NEUTRAL', 'NO_ADD']:
    subset = df[df['regime_label_v2'] == regime]
    if len(subset) > 0:
        wr = (subset['r_multiple'] > 0).mean() * 100
        avg_r = subset['r_multiple'].mean()
        winners_r = subset[subset['r_multiple'] > 0]
        losers_r = subset[subset['r_multiple'] < 0]
        avg_win = winners_r['r_multiple'].mean() if len(winners_r) > 0 else 0
        avg_loss = losers_r['r_multiple'].mean() if len(losers_r) > 0 else 0
        
        print(f'{regime} ({len(subset)} trades, {len(subset)/len(df)*100:.0f}%):')
        print(f'  Win Rate: {wr:.1f}%')
        print(f'  Avg R: {avg_r:+.3f}')
        print(f'  Avg Winner: {avg_win:+.2f}R')
        print(f'  Avg Loser: {avg_loss:+.2f}R')
        print()

print('CAPITAL ALLOCATION STRATEGY:')
print(f'  ADD_ALLOWED: 33% of trades → FULL capital (1.0x) + scaling')
print(f'  ADD_NEUTRAL: 26% of trades → NORMAL capital (0.8x)')
print(f'  NO_ADD: 40% of trades → REDUCED capital (0.5x)')
print()

print('EXPECTED PORTFOLIO IMPACT:')
# Weighted average by capital allocation
add_allowed_pct = (df['regime_label_v2'] == 'ADD_ALLOWED').sum() / len(df)
add_neutral_pct = (df['regime_label_v2'] == 'ADD_NEUTRAL').sum() / len(df)
no_add_pct = (df['regime_label_v2'] == 'NO_ADD').sum() / len(df)

add_allowed_r = df[df['regime_label_v2'] == 'ADD_ALLOWED']['r_multiple'].mean()
add_neutral_r = df[df['regime_label_v2'] == 'ADD_NEUTRAL']['r_multiple'].mean()
no_add_r = df[df['regime_label_v2'] == 'NO_ADD']['r_multiple'].mean()

# Capital weights (from templates)
add_allowed_capital = 1.0  # Full position
add_neutral_capital = 0.8
no_add_capital = 0.5

# Weighted contribution
total_capital = (add_allowed_pct * add_allowed_capital + 
                 add_neutral_pct * add_neutral_capital + 
                 no_add_pct * no_add_capital)

weighted_r = ((add_allowed_pct * add_allowed_capital * add_allowed_r +
               add_neutral_pct * add_neutral_capital * add_neutral_r +
               no_add_pct * no_add_capital * no_add_r) / total_capital)

print(f'  Baseline avg R: {df["r_multiple"].mean():+.3f}')
print(f'  ML-weighted avg R: {weighted_r:+.3f}')
print(f'  Improvement: {weighted_r - df["r_multiple"].mean():+.3f}R ({(weighted_r/df["r_multiple"].mean()-1)*100:+.1f}%)')
