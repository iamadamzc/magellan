"""
V18 STRICT REGIME TEST - Can we get to profitability?
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v7 import run_orb_v7
from research.new_strategy_builds.strategies.orb_v17_simple_regime import run_orb_v17_simple_regime
from research.new_strategy_builds.strategies.orb_v18_strict_regime import run_orb_v18_strict_regime

symbol = 'RIOT'

print("\n" + "="*80)
print("V18 STRICT REGIME - THE FINAL TEST")
print("Can we get to profitability by only trading the BEST days?")
print("="*80)

periods = [
    ('Q1 2024 (Bear)', '2024-01-01', '2024-03-31'),
    ('Q2 2024 (Bull)', '2024-04-01', '2024-06-30'),
    ('Q3 2024 (Bear)', '2024-07-01', '2024-09-30'),
    ('Q4 2024 (Bull)', '2024-10-01', '2024-12-31'),
    ('FULL 2024', '2024-01-01', '2024-12-31'),
]

results = []

for period_name, start, end in periods:
    print(f"\n{'='*80}")
    print(f"{period_name}")
    print(f"{'='*80}")
    
    print("\n🔴 V7 (No Filter):")
    v7 = run_orb_v7(symbol, start, end)
    
    print("\n🟡 V17 (Moderate Filter):")
    v17 = run_orb_v17_simple_regime(symbol, start, end)
    
    print("\n🟢 V18 (STRICT Filter):")
    v18 = run_orb_v18_strict_regime(symbol, start, end)
    
    v17_improvement = v17['total_pnl'] - v7['total_pnl']
    v18_improvement = v18['total_pnl'] - v7['total_pnl']
    v18_vs_v17 = v18['total_pnl'] - v17['total_pnl']
    
    results.append({
        'period': period_name,
        'v7_pnl': v7['total_pnl'],
        'v17_pnl': v17['total_pnl'],
        'v18_pnl': v18['total_pnl'],
        'v7_trades': v7['total_trades'],
        'v17_trades': v17['total_trades'],
        'v18_trades': v18['total_trades'],
        'v17_improvement': v17_improvement,
        'v18_improvement': v18_improvement,
        'v18_vs_v17': v18_vs_v17
    })
    
    print(f"\n📊 COMPARISON:")
    print(f"V7:  {v7['total_pnl']:+.2f}% ({v7['total_trades']} trades)")
    print(f"V17: {v17['total_pnl']:+.2f}% ({v17['total_trades']} trades) [{v17_improvement:+.2f}% vs V7]")
    print(f"V18: {v18['total_pnl']:+.2f}% ({v18['total_trades']} trades) [{v18_improvement:+.2f}% vs V7, {v18_vs_v17:+.2f}% vs V17]")

# Final summary
print("\n" + "="*80)
print("FINAL RESULTS")
print("="*80)
print(f"\n{'Period':<20} {'V7':>12} {'V17':>12} {'V18':>12} {'V18 Trades':>12}")
print("─"*80)

for r in results:
    print(f"{r['period']:<20} {r['v7_pnl']:>11.2f}% {r['v17_pnl']:>11.2f}% {r['v18_pnl']:>11.2f}% {r['v18_trades']:>12}")

import pandas as pd
df = pd.DataFrame(results)

print(f"\n{'='*80}")
print("🎯 THE MOMENT OF TRUTH")
print(f"{'='*80}")

full_year = df[df['period'] == 'FULL 2024'].iloc[0]

print(f"\n📈 FULL YEAR 2024:")
print(f"   V7 (no filter):      {full_year['v7_pnl']:+.2f}%")
print(f"   V17 (moderate):      {full_year['v17_pnl']:+.2f}% ({full_year['v17_trades']} trades)")
print(f"   V18 (STRICT):        {full_year['v18_pnl']:+.2f}% ({full_year['v18_trades']} trades)")
print(f"\n   V18 vs V7:           {full_year['v18_improvement']:+.2f}%")
print(f"   V18 vs V17:          {full_year['v18_vs_v17']:+.2f}%")

if full_year['v18_pnl'] > 0:
    print(f"\n🎉🎉🎉 WE DID IT! V18 IS PROFITABLE! 🎉🎉🎉")
    print(f"   Annual Return: {full_year['v18_pnl']:+.2f}%")
    print(f"   Trade Count: {full_year['v18_trades']} (highly selective)")
    print(f"\n   ✅ STRATEGY IS READY FOR DEPLOYMENT")
elif full_year['v18_pnl'] > full_year['v17_pnl']:
    print(f"\n✅ V18 is better than V17!")
    print(f"   Still not profitable but closer: {full_year['v18_pnl']:+.2f}%")
    print(f"   Improvement: {full_year['v18_vs_v17']:+.2f}%")
else:
    print(f"\n⚠️  V18 didn't improve over V17")
    print(f"   Filters might be TOO strict")

# Quarterly breakdown
print(f"\n📊 Quarterly Profitability:")
quarterly = df[df['period'].str.contains('Q')]
v18_profitable_quarters = (quarterly['v18_pnl'] > 0).sum()
v17_profitable_quarters = (quarterly['v17_pnl'] > 0).sum()

print(f"   V17: {v17_profitable_quarters}/4 quarters profitable")
print(f"   V18: {v18_profitable_quarters}/4 quarters profitable")

if v18_profitable_quarters > v17_profitable_quarters:
    print(f"   ✅ V18 is more consistent!")
elif v18_profitable_quarters == v17_profitable_quarters:
    print(f"   = Same consistency")
else:
    print(f"   ⚠️  V18 is less consistent")

print(f"\n{'='*80}\n")
