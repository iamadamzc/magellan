"""Quick comparison: V7 vs V15"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v7 import run_orb_v7
from research.new_strategy_builds.strategies.orb_v15_let_it_run import run_orb_v15_let_it_run

symbol = 'RIOT'
start = '2024-11-01'
end = '2025-01-17'

print("\n" + "="*70)
print("V7 (chop winners) vs V15 (let it run)")
print("="*70)

v7 = run_orb_v7(symbol, start, end)
v15 = run_orb_v15_let_it_run(symbol, start, end)

print(f"\n{'='*70}")
print(f"V7:  {v7['total_pnl']:+.2f}% ({v7['win_rate']:.1f}% win rate)")
print(f"V15: {v15['total_pnl']:+.2f}% ({v15['win_rate']:.1f}% win rate)")
print(f"Delta: {v15['total_pnl']-v7['total_pnl']:+.2f}%")

if v15['total_pnl'] > v7['total_pnl'] * 1.5:
    print("\n🚀 V15 CRUSHES IT!")
elif v15['total_pnl'] > v7['total_pnl']:
    print("\n✅ V15 wins")
else:
    print("\n❌ V15 fails")
