"""Compare lookahead bias impact"""
import pandas as pd
import numpy as np

old = pd.read_csv('research/ml_position_sizing/data/labeled_regimes_v2.csv')
new = pd.read_csv('research/ml_position_sizing/data/bear_trap_trades_2020_2024.csv')

print('='*80)
print('LOOKAHEAD BIAS IMPACT - FULL COMPARISON')
print('='*80)

print('\nTRADE COUNT:')
print(f'  OLD (lookahead): {len(old):,} trades')
print(f'  NEW (fixed):     {len(new):,} trades')
print(f'  Difference:      {len(new)-len(old):+,} trades ({(len(new)-len(old))/len(old)*100:+.1f}%)')

print('\nAVERAGE R-MULTIPLE:')
print(f'  OLD: {old["r_multiple"].mean():+.3f}R')
print(f'  NEW: {new["r_multiple"].mean():+.3f}R')
print(f'  Difference: {new["r_multiple"].mean() - old["r_multiple"].mean():.3f}R ({(new["r_multiple"].mean()/old["r_multiple"].mean()-1)*100:+.1f}%)')

print('\nWIN RATE:')
old_wr = (old['r_multiple'] > 0).mean() * 100
new_wr = (new['r_multiple'] > 0).mean() * 100
print(f'  OLD: {old_wr:.1f}%')
print(f'  NEW: {new_wr:.1f}%')
print(f'  Difference: {new_wr - old_wr:+.1f}%')

print('\nPNL %:')
print(f'  OLD avg: {old["pnl_pct"].mean():+.2f}%')
print(f'  NEW avg: {new["pnl_pct"].mean():+.2f}%')
print(f'  Difference: {new["pnl_pct"].mean() - old["pnl_pct"].mean():+.2f}%')

print('\nMAX PROFIT (Favorable Excursion):')
print(f'  OLD avg: {old["max_profit"].mean():.2f}%')
print(f'  NEW avg: {new["max_profit"].mean():.2f}%')
print(f'  Difference: {new["max_profit"].mean() - old["max_profit"].mean():+.2f}%')

print('\nMAX LOSS (Adverse Excursion):')
print(f'  OLD avg: {old["max_loss"].mean():.2f}%')
print(f'  NEW avg: {new["max_loss"].mean():.2f}%')
print(f'  Difference: {new["max_loss"].mean() - old["max_loss"].mean():+.2f}%')

print('\nWORST TRADES:')
print(f'  OLD worst 10: {old.nsmallest(10, "r_multiple")["r_multiple"].mean():.2f}R')
print(f'  NEW worst 10: {new.nsmallest(10, "r_multiple")["r_multiple"].mean():.2f}R')

print('\nBEST TRADES:')
print(f'  OLD best 10: {old.nlargest(10, "r_multiple")["r_multiple"].mean():.2f}R')
print(f'  NEW best 10: {new.nlargest(10, "r_multiple")["r_multiple"].mean():.2f}R')

print('\n' + '='*80)
