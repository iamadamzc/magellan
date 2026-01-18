"""Test V7 vs V14 on RIOT"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v7 import run_orb_v7
from research.new_strategy_builds.strategies.orb_v14_closer_targets import run_orb_v14_closer_targets

symbol = 'RIOT'
start = '2024-11-01'
end = '2025-01-17'

print("\n" + "="*70)
print("TEST: V7 vs V14 (Closer Profit Targets)")
print("="*70)

v7 = run_orb_v7(symbol, start, end)
v14 = run_orb_v14_closer_targets(symbol, start, end)

delta = v14['total_pnl'] - v7['total_pnl']
improvement = (delta / abs(v7['total_pnl']) * 100) if v7['total_pnl'] != 0 else 0

print(f"\n{'='*70}")
print(f"V7:  {v7['total_pnl']:+.2f}%")
print(f"V14: {v14['total_pnl']:+.2f}%")
print(f"Delta: {delta:+.2f}% ({improvement:+.0f}% improvement)")

if v14['total_pnl'] > v7['total_pnl'] * 1.3:
    print("\n🎉 V14 WINS BIG (+30%+)")
elif v14['total_pnl'] > v7['total_pnl']:
    print("\n✅ V14 wins (modest improvement)")
else:
    print("\n❌ V14 doesn't improve")
