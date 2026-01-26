"""
Earnings Straddles - Slippage Stress Testing
Tests strategy profitability under various slippage scenarios

Current assumption: 1% entry + 1% exit slippage
Test scenarios: 2x, 5x, 10x slippage
"""

import pandas as pd
import numpy as np
from pathlib import Path

print("="*80)
print("EARNINGS STRADDLES - SLIPPAGE STRESS TESTING")
print("="*80)

# Load WFA results
results_file = Path('research/backtests/options/phase3_walk_forward/wfa_results/earnings_straddles_wfa.csv')
trades_df = pd.read_csv(results_file)

print(f"\nLoaded {len(trades_df)} trades from WFA (2020-2025)")

# Current slippage: 1% entry + 1% exit = 2% total
# This is embedded in the pnl_pct calculation
BASE_SLIPPAGE = 2.0  # 2% total (1% entry + 1% exit)

# Test scenarios
SLIPPAGE_SCENARIOS = {
    'Baseline (1% + 1%)': 1.0,
    '2x Slippage (2% + 2%)': 2.0,
    '5x Slippage (5% + 5%)': 5.0,
    '10x Slippage (10% + 10%)': 10.0,
}

print("\n" + "="*80)
print("SLIPPAGE STRESS TEST RESULTS")
print("="*80)

results = []

for scenario_name, multiplier in SLIPPAGE_SCENARIOS.items():
    # Adjust P&L for additional slippage
    # Original pnl_pct already includes 2% slippage
    # Additional slippage = (multiplier - 1) * BASE_SLIPPAGE
    additional_slippage = (multiplier - 1) * BASE_SLIPPAGE
    
    # Subtract additional slippage from each trade
    adjusted_pnl = trades_df['pnl_pct'] - additional_slippage
    
    # Calculate metrics
    win_rate = (adjusted_pnl > 0).mean() * 100
    avg_pnl = adjusted_pnl.mean()
    sharpe = (adjusted_pnl.mean() / adjusted_pnl.std() * np.sqrt(len(adjusted_pnl))) if adjusted_pnl.std() > 0 else 0
    
    # Determine status
    if sharpe > 1.5:
        status = "✅ EXCELLENT"
    elif sharpe > 1.0:
        status = "✅ GOOD"
    elif sharpe > 0.5:
        status = "⚠️ MARGINAL"
    elif sharpe > 0:
        status = "⚠️ WEAK"
    else:
        status = "❌ UNPROFITABLE"
    
    results.append({
        'scenario': scenario_name,
        'multiplier': multiplier,
        'total_slippage_pct': multiplier * BASE_SLIPPAGE,
        'win_rate': win_rate,
        'avg_pnl': avg_pnl,
        'sharpe': sharpe,
        'status': status
    })
    
    print(f"\n{scenario_name} {status}")
    print(f"  Total Slippage: {multiplier * BASE_SLIPPAGE:.1f}%")
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  Avg P&L: {avg_pnl:+.2f}%")
    print(f"  Sharpe: {sharpe:.2f}")

# Save results
results_df = pd.DataFrame(results)
out_file = Path('docs/operations/strategies/earnings_straddles/tests/slippage/slippage_stress_results.csv')
out_file.parent.mkdir(parents=True, exist_ok=True)
results_df.to_csv(out_file, index=False)

# Recommendation
print("\n" + "="*80)
print("SLIPPAGE ROBUSTNESS ASSESSMENT")
print("="*80)

baseline_sharpe = results_df[results_df['multiplier'] == 1.0]['sharpe'].values[0]
stress_5x_sharpe = results_df[results_df['multiplier'] == 5.0]['sharpe'].values[0]
stress_10x_sharpe = results_df[results_df['multiplier'] == 10.0]['sharpe'].values[0]

print(f"\nBaseline Sharpe: {baseline_sharpe:.2f}")
print(f"5x Slippage Sharpe: {stress_5x_sharpe:.2f}")
print(f"10x Slippage Sharpe: {stress_10x_sharpe:.2f}")

if stress_5x_sharpe > 1.0:
    print("\n✅ STRATEGY IS ROBUST TO SLIPPAGE")
    print("   Remains profitable even with 5x worse slippage (10% total)")
    print("   Safe to deploy with confidence")
elif stress_5x_sharpe > 0:
    print("\n⚠️ STRATEGY IS MODERATELY ROBUST")
    print("   Profitable with 5x slippage but reduced edge")
    print("   Deploy with caution, focus on liquid tickers (GOOGL, AAPL)")
else:
    print("\n❌ STRATEGY IS NOT ROBUST TO SLIPPAGE")
    print("   Unprofitable with realistic slippage")
    print("   Do NOT deploy - slippage assumptions too optimistic")

print(f"\n✓ Saved to {out_file}")
print("\n" + "="*80)
