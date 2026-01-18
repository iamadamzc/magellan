"""Test V9 Confirmed Breakout"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from research.new_strategy_builds.strategies.orb_v9_confirmed import run_orb_v9

# Test on key symbols: RIOT + top 3 paradox
test_symbols = ['RIOT', 'PLTR', 'NVDA', 'MSTR']

print("="*80)
print("V9 TEST - CONFIRMED BREAKOUT (2-bar OR 0.4% momentum)")
print("="*80)

# Load V7 and V8 for comparison
v7_results = {
    'RIOT': 4.18,
    'PLTR': -6.15,
    'NVDA': -8.19,
    'MSTR': -28.01,
}

v8_results = {
    'RIOT': -14.50,
    'PLTR': -13.86,
    'NVDA': -31.70,
    'MSTR': -14.62,
}

v9_results = []
for symbol in test_symbols:
    try:
        result = run_orb_v9(symbol, '2024-11-01', '2025-01-17')
        v9_results.append(result)
    except Exception as e:
        print(f"✗ {symbol}: {e}")

# Comparison table
print("\n" + "="*80)
print("V7 vs V8 vs V9 COMPARISON")
print("="*80)
print(f"{'Symbol':<8} {'V7 P&L':>10} {'V8 P&L':>10} {'V9 P&L':>10} {'V9 Trades':>10} {'Best':>8}")
print("-"*80)

for result in v9_results:
    symbol = result['symbol']
    v7 = v7_results.get(symbol, 0)
    v8 = v8_results.get(symbol, 0)
    v9 = result['total_pnl']
    trades = result['total_trades']
    
    # Find best
    best = max(v7, v8, v9)
    if best == v7:
        best_str = "V7"
    elif best == v8:
        best_str = "V8"
    else:
        best_str = "✅ V9"
    
    print(f"{symbol:<8} {v7:>+9.2f}% {v8:>+9.2f}% {v9:>+9.2f}% {trades:>10} {best_str:>8}")

# Summary
v9_df = pd.DataFrame(v9_results)
print("\n" + "="*80)
print("V9 SUMMARY")
print("="*80)
print(f"Symbols tested: {len(v9_df)}")
print(f"Avg trades: {v9_df['total_trades'].mean():.1f}")
print(f"Avg win rate: {v9_df['win_rate'].mean():.1f}%")
print(f"Avg P&L: {v9_df['total_pnl'].mean():+.2f}%")

# Check RIOT specifically
riot = v9_df[v9_df['symbol'] == 'RIOT'].iloc[0]
print(f"\n🎯 RIOT CHECK:")
print(f"  V7: +4.18%")
print(f"  V8: -14.50%")
print(f"  V9: {riot['total_pnl']:+.2f}%")
print(f"  Trades: {riot['total_trades']}")
print(f"  Win rate: {riot['win_rate']:.1f}%")

if riot['total_pnl'] > 0:
    print(f"  ✅ V9 PROFITABLE on RIOT!")
elif riot['total_pnl'] > -2:
    print(f"  ⚠️ V9 Near breakeven on RIOT")
else:
    print(f"  ❌ V9 Still losing on RIOT")

# Save
v9_df.to_csv('research/new_strategy_builds/results/v9_confirmed_test.csv', index=False)
print(f"\n✅ Saved to: v9_confirmed_test.csv")
