"""ORB V7 - Win Rate Paradox Analysis"""
import pandas as pd

df = pd.read_csv('research/new_strategy_builds/results/ORB_V7_FULL_UNIVERSE.csv')

print("="*80)
print("WIN RATE PARADOX ANALYSIS")
print("="*80)

# The Paradox: >50% win rate but LOSING money
paradox = df[(df['win_rate'] > 50) & (df['total_pnl'] < 0) & (df['total_trades'] >= 10)].copy()
paradox = paradox.sort_values('win_rate', ascending=False)

print(f"\nPARADOX CASES: {len(paradox)} symbols with >50% win but LOSING")
print("="*80)
print(paradox[['symbol', 'asset_class', 'total_trades', 'win_rate', 'avg_pnl', 'total_pnl']].to_string(index=False))

# Small loss cases
small_loss = df[(df['total_pnl'] > -5) & (df['total_pnl'] < 0) & (df['total_trades'] >= 10)].copy()
small_loss = small_loss.sort_values('total_pnl', ascending=False)

print(f"\n{'='*80}")
print(f"SMALL LOSS CASES: {len(small_loss)} symbols with <-5% total (good stops)")
print("="*80)
print(small_loss[['symbol', 'asset_class', 'total_trades', 'win_rate', 'avg_pnl', 'total_pnl']].to_string(index=False))

# Stats comparison
print(f"\n{'='*80}")
print("STATS COMPARISON")
print("="*80)

winners = df[df['total_pnl'] > 0]

print("\nParadox Group (High win, negative P&L):")
print(f"  Count: {len(paradox)}")
print(f"  Avg win rate: {paradox['win_rate'].mean():.1f}%")
print(f"  Avg trades: {paradox['total_trades'].mean():.1f}")
print(f"  Avg P&L/trade: {paradox['avg_pnl'].mean():+.4f}%")

print("\nWinners Group:")
print(f"  Count: {len(winners)}")
print(f"  Avg win rate: {winners['win_rate'].mean():.1f}%")
print(f"  Avg trades: {winners['total_trades'].mean():.1f}")
print(f"  Avg P&L/trade: {winners['avg_pnl'].mean():+.4f}%")

print("\nLosers Group (controls):")
losers_normal = df[(df['total_pnl'] < 0) & (df['win_rate'] <= 50)]
print(f"  Count: {len(losers_normal)}")
print(f"  Avg win rate: {losers_normal['win_rate'].mean():.1f}%")
print(f"  Avg P&L/trade: {losers_normal['avg_pnl'].mean():+.4f}%")

# The math
print(f"\n{'='*80}")
print("THE MATH REVEALS THE PROBLEM")
print("="*80)

print("\nFor 55% win rate to be profitable, need:")
print("  Avg Winner / Avg Loser ratio > (1-0.55)/0.55 = 0.82")
print("  So: Avg winner must be > 82% of abs(avg loser)")

print("\nParadox group has NEGATIVE avg P&L, which means:")
print(f"  Avg Winner < 82% of Avg Loser")
print("  Winners are TOO SMALL relative to losers!")

print("\n" + "="*80)
print("HYPOTHESIS & FIXES")
print("="*80)

print("\nThe Problem:")
print("  - Stops work well (limiting losses)")
print("  - But winners exit too early (scaling at 1.3R rarely hit)")
print("  - Most exits are 'stop' or 'eod', FEW reach targets")

print("\nPossible Causes:")
print("  1. 1.3R target too far (unrealistic)")
print("  2. Entries too late (not enough room)")
print("  3. Breakeven + VWAP loss cutting winners early")
print("  4. Pullback entry timing misses the momentum")

print("\nProposed Fixes:")
print("  A. CLOSER TARGETS: Scale at 0.5R/0.7R instead of 1.3R")
print("  B. NO SCALING: Pure trail from entry (no premature exits)")
print("  C. NO VWAP FILTER: May be cutting winning moves")
print("  D. EARLIER ENTRY: On breakout, not pullback")
print("  E. WIDER TRAILING: Let winners breathe")

# Save analysis
paradox.to_csv('research/new_strategy_builds/results/paradox_symbols.csv', index=False)
small_loss.to_csv('research/new_strategy_builds/results/small_loss_symbols.csv', index=False)

print(f"\n{'='*80}")
print("SAVED:")
print("  - paradox_symbols.csv")
print("  - small_loss_symbols.csv")
print("="*80)
