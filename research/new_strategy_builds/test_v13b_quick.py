"""Quick test: V7 vs V13b (VWAP exit removal only)"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v7 import run_orb_v7
from research.new_strategy_builds.strategies.orb_v13b_minimal import run_orb_v13b_minimal

symbol = 'RIOT'
start = '2024-11-01'
end = '2025-01-17'

print("\n" + "="*70)
print("QUICK TEST: Does removing VWAP exit alone improve performance?")
print("="*70)

print("\n🔬 V7 (with VWAP exit):")
v7 = run_orb_v7(symbol, start, end)

print("\n💉 V13b (without VWAP exit):")
v13b = run_orb_v13b_minimal(symbol, start, end)

print("\n" + "="*70)
print("COMPARISON:")
print("="*70)
print(f"Total P&L:   V7={v7['total_pnl']:+.2f}%  V13b={v13b['total_pnl']:+.2f}%  Delta={v13b['total_pnl']-v7['total_pnl']:+.2f}%")
print(f"Avg Winner:  V7={0.5:.2f}R  V13b={v13b['avg_winner_r']:+.2f}R  Delta={v13b['avg_winner_r']-0.5:+.2f}R")
print(f"Win Rate:    V7={v7['win_rate']:.1f}%  V13b={v13b['win_rate']:.1f}%  Delta={v13b['win_rate']-v7['win_rate']:+.1f}%")

if v13b['total_pnl'] > v7['total_pnl']:
    print("\n✅ V13b WINS - VWAP exit removal helps!")
else:
    print("\n❌ V13b FAILS - VWAP exit removal doesn't help")
