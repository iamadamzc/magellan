"""Test V7 vs V16 on Nov-Jan period (where V7 worked) and full 2024 (where V7 failed)"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v7 import run_orb_v7
from research.new_strategy_builds.strategies.orb_v16_regime_aware import run_orb_v16_regime_aware

symbol = 'RIOT'

print("\n" + "="*80)
print("REGIME FILTER TEST: Does filtering bad days save the strategy?")
print("="*80)

# Test 1: Nov-Jan (known good period)
print("\n" + "─"*80)
print("TEST 1: Nov 2024 - Jan 2025 (Bull Market)")
print("─"*80)
v7_bull = run_orb_v7(symbol, '2024-11-01', '2025-01-17')
v16_bull = run_orb_v16_regime_aware(symbol, '2024-11-01', '2025-01-17')

print(f"\nV7:  {v7_bull['total_pnl']:+.2f}% ({v7_bull['total_trades']} trades)")
print(f"V16: {v16_bull['total_pnl']:+.2f}% ({v16_bull['total_trades']} trades)")

# Test 2: Q1 2024 (known bad period)
print("\n" + "─"*80)
print("TEST 2: Q1 2024 (Bear Market)")
print("─"*80)
v7_bear = run_orb_v7(symbol, '2024-01-01', '2024-03-31')
v16_bear = run_orb_v16_regime_aware(symbol, '2024-01-01', '2024-03-31')

print(f"\nV7:  {v7_bear['total_pnl']:+.2f}% ({v7_bear['total_trades']} trades)")
print(f"V16: {v16_bear['total_pnl']:+.2f}% ({v16_bear['total_trades']} trades)")

# Summary
print("\n" + "="*80)
print("VERDICT")
print("="*80)

bull_improvement = v16_bull['total_pnl'] - v7_bull['total_pnl']
bear_improvement = v16_bear['total_pnl'] - v7_bear['total_pnl']

print(f"\nBull Market (Nov-Jan): V16 vs V7 = {bull_improvement:+.2f}%")
print(f"Bear Market (Q1 2024): V16 vs V7 = {bear_improvement:+.2f}%")

if bear_improvement > 20:
    print("\n🎉 REGIME FILTER WORKS! V16 avoided the bear market disaster!")
elif bear_improvement > 0:
    print("\n✅ V16 helps but not dramatically")
else:
    print("\n❌ Regime filter didn't help")
