"""
V17 FULL VALIDATION - All of 2024
Test regime filter across bull, bear, and sideways markets
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v7 import run_orb_v7
from research.new_strategy_builds.strategies.orb_v17_simple_regime import run_orb_v17_simple_regime

symbol = 'RIOT'

print("\n" + "="*80)
print("V17 REGIME FILTER - FULL 2024 VALIDATION")
print("="*80)

periods = [
    ('Q1 2024 (Bear)', '2024-01-01', '2024-03-31'),
    ('Q2 2024', '2024-04-01', '2024-06-30'),
    ('Q3 2024', '2024-07-01', '2024-09-30'),
    ('Q4 2024', '2024-10-01', '2024-12-31'),
    ('FULL 2024', '2024-01-01', '2024-12-31'),
]

results = []

for period_name, start, end in periods:
    print(f"\n{'='*80}")
    print(f"{period_name}")
    print(f"{'='*80}")
    
    print("\n🔴 V7 (No Filter):")
    v7 = run_orb_v7(symbol, start, end)
    
    print("\n🟢 V17 (Regime Filter):")
    v17 = run_orb_v17_simple_regime(symbol, start, end)
    
    improvement = v17['total_pnl'] - v7['total_pnl']
    
    results.append({
        'period': period_name,
        'v7_pnl': v7['total_pnl'],
        'v7_trades': v7['total_trades'],
        'v17_pnl': v17['total_pnl'],
        'v17_trades': v17['total_trades'],
        'improvement': improvement
    })
    
    print(f"\n📊 COMPARISON:")
    print(f"V7:  {v7['total_pnl']:+.2f}% ({v7['total_trades']} trades)")
    print(f"V17: {v17['total_pnl']:+.2f}% ({v17['total_trades']} trades)")
    print(f"Improvement: {improvement:+.2f}%")

# Final summary
print("\n" + "="*80)
print("FINAL SUMMARY")
print("="*80)
print(f"\n{'Period':<20} {'V7 P&L':>12} {'V17 P&L':>12} {'Improvement':>12} {'V7 Trades':>10} {'V17 Trades':>10}")
print("─"*80)

for r in results:
    print(f"{r['period']:<20} {r['v7_pnl']:>11.2f}% {r['v17_pnl']:>11.2f}% {r['improvement']:>11.2f}% {r['v7_trades']:>10} {r['v17_trades']:>10}")

# Calculate totals
import pandas as pd
df = pd.DataFrame(results)

print(f"\n{'='*80}")
print("VERDICT")
print(f"{'='*80}")

full_year = df[df['period'] == 'FULL 2024'].iloc[0]

print(f"\n📈 FULL YEAR 2024:")
print(f"   V7 (no filter):  {full_year['v7_pnl']:+.2f}%")
print(f"   V17 (filtered):  {full_year['v17_pnl']:+.2f}%")
print(f"   Improvement:     {full_year['improvement']:+.2f}%")

if full_year['v17_pnl'] > 0:
    print(f"\n🎉 V17 IS PROFITABLE! Strategy is DEPLOYABLE!")
    print(f"   Regime filter turned losing strategy into winner")
elif full_year['v17_pnl'] > full_year['v7_pnl']:
    print(f"\n✅ V17 is better but not yet profitable")
    print(f"   Needs further tuning or different symbols")
else:
    print(f"\n❌ V17 didn't help enough")

# Count profitable quarters
profitable_quarters = (df[df['period'].str.contains('Q')]['v17_pnl'] > 0).sum()
total_quarters = len(df[df['period'].str.contains('Q')])

print(f"\n📊 Quarterly Performance:")
print(f"   V17 profitable in {profitable_quarters}/{total_quarters} quarters")

if profitable_quarters >= 3:
    print(f"   ✅ Strong consistency!")
elif profitable_quarters >= 2:
    print(f"   ⚠️  Moderate consistency")
else:
    print(f"   ❌ Inconsistent")

print(f"\n{'='*80}\n")
