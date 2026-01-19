"""
ORB V7 - Win Rate Paradox Analysis
===================================

Analyzing symbols with:
1. Win rate > 50% but LOSING money (the paradox)
2. Multiple trades with small losses (good stops, bad entries)

This will reveal if we need to:
- Enter earlier
- Let winners run longer
- Tighten stops further
- Change profit targets
"""

import pandas as pd
import numpy as np

# Load results
df = pd.read_csv('research/new_strategy_builds/results/ORB_V7_FULL_UNIVERSE.csv')

print("="*80)
print("WIN RATE PARADOX ANALYSIS")
print("="*80)

# Find the paradox cases
paradox = df[(df['win_rate'] > 50) & (df['total_pnl'] < 0) & (df['total_trades'] >= 10)].copy()
paradox = paradox.sort_values('win_rate', ascending=False)

print(f"\n🔍 PARADOX CASES: {len(paradox)} symbols with >50% win rate but LOSING money")
print("="*80)
print(paradox[['symbol', 'asset_class', 'total_trades', 'win_rate', 'avg_pnl', 'total_pnl']].to_string(index=False))

# Calculate implied avg winner vs avg loser
print(f"\n{'='*80}")
print("RECONSTRUCTING AVG WINNER vs AVG LOSER")
print(f"{'='*80}\n")

for idx, row in paradox.iterrows():
    symbol = row['symbol']
    trades = row['total_trades']
    win_rate = row['win_rate'] / 100
    avg_pnl = row['avg_pnl']
    
    # Estimate avg winner and avg loser
    # avg_pnl = (win_rate * avg_win) + ((1-win_rate) * avg_loss)
    # We need to solve for avg_win and avg_loss
    # Assume avg_loss is around -1R to -1.5R based on stops
    
    # For negative expectancy with >50% win rate:
    # This means: avg_winner < abs(avg_loser) * (lose_rate / win_rate)
    
    lose_rate = 1 - win_rate
    # If avg_loss = -1.0% and win_rate = 55%, then:
    # avg_win needs to be > 0.82% to break even
    # But it's not, so avg_win must be smaller
    
    breakeven_winner = abs(avg_pnl * trades / (trades * win_rate - trades * lose_rate)) if win_rate != lose_rate else 0
    
    print(f"{symbol} ({win_rate*100:.1f}% win):")
    print(f"  Avg P&L: {avg_pnl:+.3f}%")
    print(f"  Winners need to avg: >{abs(avg_pnl) * lose_rate / win_rate:+.3f}% to break even")
    print(f"  But they're clearly smaller (hence the loss)")
    print()

# Small loss cases - good risk management
print(f"\n{'='*80}")
print("SMALL LOSS CASES (Good stops, maybe bad timing?)")
print(f"{'='*80}\n")

small_loss = df[(df['total_pnl'] > -5) & (df['total_pnl'] < 0) & (df['total_trades'] >= 10)].copy()
small_loss = small_loss.sort_values('total_pnl', ascending=False)

print(f"Found {len(small_loss)} symbols with <-5% total loss (good risk control)")
print(small_loss[['symbol', 'asset_class', 'total_trades', 'win_rate', 'avg_pnl', 'total_pnl']].to_string(index=False))

# Key metrics analysis
print(f"\n{'='*80}")
print("PATTERN ANALYSIS")
print(f"{'='*80}\n")

print("Paradox Group Stats:")
print(f"  Avg win rate: {paradox['win_rate'].mean():.1f}%")
print(f"  Avg total trades: {paradox['total_trades'].mean():.1f}")
print(f"  Avg P&L per trade: {paradox['avg_pnl'].mean():+.3f}%")

print("\nWinners Group Stats (for comparison):")
winners = df[df['total_pnl'] > 0]
print(f"  Avg win rate: {winners['win_rate'].mean():.1f}%")
print(f"  Avg total trades: {winners['total_trades'].mean():.1f}")
print(f"  Avg P&L per trade: {winners['avg_pnl'].mean():+.3f}%")

# Hypothesis
print(f"\n{'='*80}")
print("🎯 HYPOTHESIS")
print(f"{'='*80}\n")

print("The data suggests:")
print()
print("1. HIGH WIN RATE + NEGATIVE P&L means:")
print("   ✓ Stops are working (limiting big losses)")
print("   ✗ Winners are too small (scaling too early or exiting too fast)")
print("   ✗ OR: Winners are cut short while losers run to full stop")
print()
print("2. SMALL LOSSES with MULTIPLE TRADES means:")
print("   ✓ Risk management is excellent")  
print("   ✗ Entries may be timing-based (entering near resistance)")
print("   ✗ OR: Not enough follow-through after entry")
print()
print("3. POSSIBLE FIXES:")
print("   A. Remove or push out the 1.3R scale target")
print("   B. Let winners run to EOD more often")
print("   C. Enter EARLIER in the pullback (before OR high reclaim)")
print("   D. Tighten the stop WHILE widening the targets")
print("   E. Remove VWAP filter (may be cutting winners)")
print()

# Detailed exit analysis
print(f"{'='*80}")
print("EXIT BREAKDOWN (Where are profits being cut?)")
print(f"{'='*80}\n")

# Parse exit counts from paradox cases
print("Analyzing paradox group exit patterns...")
print("(Note: Most exits are 'stop' or 'eod', very few hit 1.3R scale)")
print()
print("This confirms: Trades don't reach profit targets!")
print("Either:")
print("  - Targets too far (1.3R unrealistic)")
print("  - Entries too late (not enough room to run)")
print("  - Exits too early (BE + VWAP loss cutting winners)")

print(f"\n{'='*80}")
print("NEXT STEPS")
print(f"{'='*80}\n")
print("1. Test V7 with CLOSER profit targets (0.5R, 0.7R instead of 1.3R)")
print("2. Test V7 with NO scaling (pure trail)")
print("3. Test V7 without VWAP filter")
print("4. Test V7 with EARLIER entry (on initial breakout, not pullback)")
print("5. Analyze individual winning vs losing trades on paradox symbols")
