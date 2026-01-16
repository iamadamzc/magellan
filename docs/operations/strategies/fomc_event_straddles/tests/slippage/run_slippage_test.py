"""
FOMC Event Straddles - Slippage Stress Test

Tests the strategy's robustness against higher execution costs and IV Crush.
Since the base model assumes fixed costs, validiting against high slippage is a proxy for IV Crush.

Scenarios:
- Baseline: 0.05% Slippage
- 2x: 0.10%
- 5x: 0.25% (Critical Threshold)
- 10x: 0.50%
- 20x: 1.00% (Simulates major IV Crush)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

script_path = Path(__file__).resolve()
wfa_file = script_path.parents[1] / 'wfa' / 'wfa_results.csv'

print("="*80)
print("FOMC SLIPPAGE STRESS TEST")
print("="*80)

if not wfa_file.exists():
    print("❌ WFA Results not found.")
    sys.exit(1)

df = pd.read_csv(wfa_file)
print(f"Loaded {len(df)} events from WFA.")

# Model Parameters
STRADDLE_COST_PCT = 2.0
THETA_DECAY_PCT = 0.01

slippage_levels = [0.05, 0.10, 0.25, 0.50, 1.00, 1.50, 2.00]
results = []

print("\nTesting Slippage Levels:")

for s in slippage_levels:
    # Recalculate P&L
    # profit = (spy_move / cost * 100) - theta - slippage
    pnl_pcts = (df['spy_move_pct'] / STRADDLE_COST_PCT * 100) - THETA_DECAY_PCT - s
    
    win_rate = (pnl_pcts > 0).mean() * 100
    avg_pnl = pnl_pcts.mean()
    sharpe = (pnl_pcts.mean() / pnl_pcts.std() * np.sqrt(8)) if pnl_pcts.std() > 0 else 0
    total_ret = pnl_pcts.sum()
    
    status = "✅"
    if avg_pnl < 0: status = "❌"
    elif avg_pnl < 1.0: status = "⚠️"
    
    print(f"  Slippage {s:.2f}%: WR {win_rate:.1f}% | Avg P&L {avg_pnl:+.2f}% | Sharpe {sharpe:.2f} {status}")
    
    results.append({
        'slippage': s,
        'win_rate': win_rate,
        'avg_pnl': avg_pnl,
        'sharpe': sharpe
    })

# Save Report
report_path = Path(__file__).parent / 'slippage_report.md'
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("# FOMC Slippage Stress Test\n\n")
    f.write("| Slippage | Win Rate | Avg P&L | Sharpe | Verdict |\n")
    f.write("|----------|----------|---------|--------|---------|\n")
    for r in results:
        verdict = "PASS" if r['avg_pnl'] > 0 else "FAIL"
        f.write(f"| {r['slippage']:.2f}% | {r['win_rate']:.1f}% | {r['avg_pnl']:+.2f}% | {r['sharpe']:.2f} | {verdict} |\n")
        
    f.write("\n## Conclusion\n")
    fail_level = next((r['slippage'] for r in results if r['avg_pnl'] < 0), None)
    if fail_level:
        f.write(f"Strategy becomes unprofitable at **{fail_level:.2f}%** slippage.\n")
    else:
        f.write("Strategy survives all tested slippage levels.\n")

print(f"\nReport saved to {report_path}")
