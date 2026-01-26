"""Quick test V17 regime filter"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v7 import run_orb_v7
from research.new_strategy_builds.strategies.orb_v17_simple_regime import run_orb_v17_simple_regime

symbol = 'RIOT'

print("\n" + "="*80)
print("V17 REGIME FILTER TEST")
print("="*80)

# Q1 2024 (bear market - should filter most days)
print("\nQ1 2024 (Bear Market):")
print("─"*80)
v7 = run_orb_v7(symbol, '2024-01-01', '2024-03-31')
v17 = run_orb_v17_simple_regime(symbol, '2024-01-01', '2024-03-31')

print(f"\nV7 (no filter):  {v7['total_pnl']:+.2f}% ({v7['total_trades']} trades)")
print(f"V17 (filtered):  {v17['total_pnl']:+.2f}% ({v17['total_trades']} trades)")
print(f"Improvement:     {v17['total_pnl']-v7['total_pnl']:+.2f}%")

if v17['total_pnl'] > v7['total_pnl'] + 20:
    print("\n🎉 REGIME FILTER WORKS!")
elif v17['total_pnl'] > v7['total_pnl']:
    print("\n✅ Modest improvement")
else:
    print("\n❌ Didn't help")
