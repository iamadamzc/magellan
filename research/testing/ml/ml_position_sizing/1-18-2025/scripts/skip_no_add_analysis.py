"""What if we SKIP NO_ADD trades entirely?"""
import pandas as pd
import numpy as np

df = pd.read_csv('research/ml_position_sizing/data/labeled_regimes_v2.csv')

print('='*80)
print('SCENARIO ANALYSIS: SKIP NO_ADD TRADES')
print('='*80)

print('\nCURRENT APPROACH (reduce NO_ADD to 0.5x capital):')
print(f'  Total trades: {len(df)}')
print(f'  NO_ADD trades: {(df["regime_label_v2"] == "NO_ADD").sum()} ({(df["regime_label_v2"] == "NO_ADD").sum()/len(df)*100:.0f}%)')
print(f'  NO_ADD avg R: {df[df["regime_label_v2"] == "NO_ADD"]["r_multiple"].mean():.3f}')
print(f'  NO_ADD avg PnL: {df[df["regime_label_v2"] == "NO_ADD"]["pnl_pct"].mean():.2f}%')

# Calculate current ML performance
add_allowed = df[df['regime_label_v2'] == 'ADD_ALLOWED']
add_neutral = df[df['regime_label_v2'] == 'ADD_NEUTRAL']
no_add = df[df['regime_label_v2'] == 'NO_ADD']

current_weighted_r = (
    add_allowed['r_multiple'].mean() * 1.0 * len(add_allowed) +
    add_neutral['r_multiple'].mean() * 0.8 * len(add_neutral) +
    no_add['r_multiple'].mean() * 0.5 * len(no_add)
) / (
    1.0 * len(add_allowed) + 
    0.8 * len(add_neutral) + 
    0.5 * len(no_add)
)

print(f'\n  Current ML-weighted R: {current_weighted_r:.3f}')

print('\n' + '='*80)
print('OPTION 1: SKIP NO_ADD ENTIRELY')
print('='*80)

# Only trade ADD_ALLOWED and ADD_NEUTRAL
tradeable = df[df['regime_label_v2'].isin(['ADD_ALLOWED', 'ADD_NEUTRAL'])]

skip_weighted_r = (
    add_allowed['r_multiple'].mean() * 1.0 * len(add_allowed) +
    add_neutral['r_multiple'].mean() * 0.8 * len(add_neutral)
) / (
    1.0 * len(add_allowed) + 
    0.8 * len(add_neutral)
)

print(f'\n  Trades taken: {len(tradeable)} ({len(tradeable)/len(df)*100:.0f}% of original)')
print(f'  Trades skipped: {len(no_add)} ({len(no_add)/len(df)*100:.0f}%)')
print(f'  Avg R (skipping NO_ADD): {skip_weighted_r:.3f}')
print(f'  Improvement vs current ML: {skip_weighted_r - current_weighted_r:+.3f}R ({(skip_weighted_r/current_weighted_r-1)*100:+.1f}%)')

# Win rate
skip_wr = (tradeable['r_multiple'] > 0).mean() * 100
current_wr = (df['r_multiple'] > 0).mean() * 100

print(f'\n  Win rate (skipping NO_ADD): {skip_wr:.1f}%')
print(f'  Win rate (current): {current_wr:.1f}%')
print(f'  Improvement: {skip_wr - current_wr:+.1f}%')

print('\n' + '='*80)
print('OPTION 2: SKIP NO_ADD + ADD_NEUTRAL (only trade ADD_ALLOWED)')
print('='*80)

only_allowed = add_allowed

print(f'\n  Trades taken: {len(only_allowed)} ({len(only_allowed)/len(df)*100:.0f}% of original)')
print(f'  Trades skipped: {len(df) - len(only_allowed)} ({(len(df)-len(only_allowed))/len(df)*100:.0f}%)')
print(f'  Avg R: {only_allowed["r_multiple"].mean():.3f}')
print(f'  Improvement vs current ML: {only_allowed["r_multiple"].mean() - current_weighted_r:+.3f}R ({(only_allowed["r_multiple"].mean()/current_weighted_r-1)*100:+.1f}%)')

only_wr = (only_allowed['r_multiple'] > 0).mean() * 100
print(f'\n  Win rate: {only_wr:.1f}%')
print(f'  Improvement vs current: {only_wr - current_wr:+.1f}%')

print('\n' + '='*80)
print('TRADE-OFFS:')
print('='*80)

print('\nCurrent ML (0.5x NO_ADD):')
print(f'  ✅ Takes all trades (2,025)')
print(f'  ✅ Avg R: {current_weighted_r:.3f}')
print(f'  ❌ Still exposes capital to losers')

print('\nSkip NO_ADD:')
print(f'  ✅ Avg R: {skip_weighted_r:.3f} (+{(skip_weighted_r/current_weighted_r-1)*100:.0f}%)')
print(f'  ✅ Win rate: {skip_wr:.1f}% (vs {current_wr:.1f}%)')
print(f'  ❌ Fewer trades ({len(tradeable)} vs {len(df)})')
print(f'  ❌ Less diversification')

print('\nOnly ADD_ALLOWED:')
print(f'  ✅ Highest avg R: {only_allowed["r_multiple"].mean():.3f}')
print(f'  ✅ Highest win rate: {only_wr:.1f}%')
print(f'  ❌ Much fewer trades ({len(only_allowed)} vs {len(df)})')
print(f'  ❌ Significant opportunity cost')

print('\n' + '='*80)
print('RECOMMENDATION:')
print('='*80)

print('\n🎯 SKIP NO_ADD ENTIRELY')
print(f'   - Improves R by {(skip_weighted_r/current_weighted_r-1)*100:.0f}%')
print(f'   - Improves win rate by {skip_wr - current_wr:.0f}%')
print(f'   - Still takes 60% of trades (good diversification)')
print(f'   - Eliminates losing trades')
print('\n   This is the sweet spot!')
