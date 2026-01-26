"""
Extended Period Test - RIOT
Avoid holiday bias, test full year
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v7 import run_orb_v7

# Test multiple periods
periods = [
    ('Q4 2023', '2023-10-01', '2023-12-31'),
    ('Q1 2024', '2024-01-01', '2024-03-31'),
    ('Q2 2024', '2024-04-01', '2024-06-30'),
    ('Q3 2024', '2024-07-01', '2024-09-30'),
    ('Q4 2024 (Holiday)', '2024-10-01', '2024-12-31'),
    ('Jan 2025', '2025-01-01', '2025-01-17'),
    ('Full Year 2024', '2024-01-01', '2024-12-31'),
]

symbol = 'RIOT'

print("\n" + "="*80)
print(f"ORB V7 EXTENDED PERIOD ANALYSIS - {symbol}")
print("="*80)

results = []

for period_name, start, end in periods:
    print(f"\n{'─'*80}")
    print(f"Testing: {period_name}")
    print(f"{'─'*80}")
    
    result = run_orb_v7(symbol, start, end)
    if result and result['total_trades'] > 0:
        results.append({
            'period': period_name,
            'trades': result['total_trades'],
            'win_rate': result['win_rate'],
            'total_pnl': result['total_pnl'],
            'avg_pnl': result['avg_pnl']
        })

print("\n" + "="*80)
print("SUMMARY BY PERIOD")
print("="*80)
print(f"{'Period':<20} {'Trades':>8} {'Win%':>8} {'Total P&L':>12} {'Avg/Trade':>12}")
print("─"*80)

for r in results:
    print(f"{r['period']:<20} {r['trades']:>8} {r['win_rate']:>7.1f}% {r['total_pnl']:>11.2f}% {r['avg_pnl']:>11.3f}%")

# Analysis
if results:
    import pandas as pd
    df = pd.DataFrame(results)
    
    print("\n" + "="*80)
    print("INSIGHTS")
    print("="*80)
    
    best = df.loc[df['total_pnl'].idxmax()]
    worst = df.loc[df['total_pnl'].idxmin()]
    
    print(f"Best Period:  {best['period']} ({best['total_pnl']:+.2f}%)")
    print(f"Worst Period: {worst['period']} ({worst['total_pnl']:+.2f}%)")
    print(f"\nAverage across all periods: {df['total_pnl'].mean():+.2f}%")
    print(f"Std Dev: {df['total_pnl'].std():.2f}%")
    
    profitable_periods = (df['total_pnl'] > 0).sum()
    print(f"\nProfitable periods: {profitable_periods}/{len(df)}")
    
    if df['total_pnl'].mean() > 0:
        print("\n✅ Strategy is profitable across extended period!")
    else:
        print("\n❌ Strategy loses money on average")
