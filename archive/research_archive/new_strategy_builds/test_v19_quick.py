"""Quick test: V7 vs V19 (first hour only) on RIOT"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v7 import run_orb_v7
from research.new_strategy_builds.strategies.orb_v19_first_hour import run_orb_v19_first_hour

symbol = 'RIOT'

print("\n" + "="*80)
print("V19 TEST: Does limiting to first hour fix everything?")
print("="*80)

# Test Q4 2024 (known profitable period for V7)
print("\nQ4 2024 (Bull Market):")
v7 = run_orb_v7(symbol, '2024-10-01', '2024-12-31')
v19 = run_orb_v19_first_hour(symbol, '2024-10-01', '2024-12-31')

print(f"\nV7 (all day):     {v7['total_pnl']:+.2f}% ({v7['total_trades']} trades)")
print(f"V19 (first hour): {v19['total_pnl']:+.2f}% ({v19['total_trades']} trades)")
print(f"Improvement:      {v19['total_pnl']-v7['total_pnl']:+.2f}%")

# Test full 2024
print("\n" + "="*80)
print("FULL 2024:")
v7_full = run_orb_v7(symbol, '2024-01-01', '2024-12-31')
v19_full = run_orb_v19_first_hour(symbol, '2024-01-01', '2024-12-31')

print(f"\nV7 (all day):     {v7_full['total_pnl']:+.2f}% ({v7_full['total_trades']} trades)")
print(f"V19 (first hour): {v19_full['total_pnl']:+.2f}% ({v19_full['total_trades']} trades)")
print(f"Improvement:      {v19_full['total_pnl']-v7_full['total_pnl']:+.2f}%")

if v19_full['total_pnl'] > 0:
    print("\n🎉 V19 IS PROFITABLE! Entry window was the missing piece!")
elif v19_full['total_pnl'] > v7_full['total_pnl']:
    print("\n✅ V19 is better but not yet profitable")
else:
    print("\n❌ Entry window didn't help enough")
