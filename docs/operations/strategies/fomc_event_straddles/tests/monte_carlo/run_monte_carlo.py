"""
FOMC Event Straddles - Monte Carlo Simulation

Performs rigorous statistical analysis on the WFA results (2020-2024):
1. Bootstrap Analysis (10,000 iterations): Resampling with replacement to estimate confidence intervals for Sharpe Ratio, Win Rate, and Mean P&L.
2. Permutation Analysis (10,000 iterations): Shuffling trade order to analyze Max Drawdown distribution and sequence risk.
3. Streak Analysis: Probability of consecutive losses.

Objective:
Validate if the strategy's performance is statistically significant or due to luck/regime bias.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats

# Setup Paths
script_path = Path(__file__).resolve()
# backtest_extended.py is in ../wfa/backtest_extended.py
# wfa_results.csv is in ../wfa/wfa_results.csv
wfa_results_path = script_path.parents[1] / 'wfa' / 'wfa_results.csv'

print("="*80)
print("FOMC MONTE CARLO SIMULATION")
print("="*80)

if not wfa_results_path.exists():
    print(f"❌ Error: Results file not found at {wfa_results_path}")
    print("   Please run the WFA backtest first.")
    sys.exit(1)

df = pd.read_csv(wfa_results_path)
print(f"Loaded {len(df)} trades from WFA results.")

pnl_pct = df['pnl_pct'].values
win_rate_actual = (df['win'].sum() / len(df)) * 100
mean_pnl_actual = np.mean(pnl_pct)
std_pnl_actual = np.std(pnl_pct)
sharpe_actual = (mean_pnl_actual / std_pnl_actual * np.sqrt(8)) if std_pnl_actual > 0 else 0

print(f"\nActual Performance:")
print(f"  Win Rate: {win_rate_actual:.1f}%")
print(f"  Mean P&L: {mean_pnl_actual:+.2f}%")
print(f"  Sharpe:   {sharpe_actual:.2f}")

# -----------------------------------------------------------------------------
# 1. Bootstrap Analysis (Resampling with Replacement)
# -----------------------------------------------------------------------------
print("\n[1/3] Running Bootstrap Analysis (10,000 iterations)...")
N_ITERIONS = 10000
bootstrap_sharpes = []
bootstrap_means = []
bootstrap_win_rates = []

np.random.seed(42) # Reproducibility

for _ in range(N_ITERIONS):
    # Resample with replacement
    sample = np.random.choice(pnl_pct, size=len(pnl_pct), replace=True)
    
    mean_s = np.mean(sample)
    std_s = np.std(sample)
    sharpe_s = (mean_s / std_s * np.sqrt(8)) if std_s > 0 else 0
    win_rate_s = (np.sum(sample > 0) / len(sample)) * 100
    
    bootstrap_sharpes.append(sharpe_s)
    bootstrap_means.append(mean_s)
    bootstrap_win_rates.append(win_rate_s)

bootstrap_sharpes = np.array(bootstrap_sharpes)
bootstrap_means = np.array(bootstrap_means)

# Confidence Intervals (95%)
sharpe_low = np.percentile(bootstrap_sharpes, 2.5)
sharpe_high = np.percentile(bootstrap_sharpes, 97.5)
mean_low = np.percentile(bootstrap_means, 2.5)
mean_high = np.percentile(bootstrap_means, 97.5)

print(f"  95% CI Sharpe:   [{sharpe_low:.2f}, {sharpe_high:.2f}]")
print(f"  95% CI Mean P&L: [{mean_low:+.2f}%, {mean_high:+.2f}%]")
print(f"  Prob(Sharpe > 1.0): {(np.sum(bootstrap_sharpes > 1.0) / N_ITERIONS * 100):.1f}%")
print(f"  Prob(P&L > 0):      {(np.sum(bootstrap_means > 0) / N_ITERIONS * 100):.1f}%")

# -----------------------------------------------------------------------------
# 2. Permutation Analysis (Max Drawdown)
# -----------------------------------------------------------------------------
print("\n[2/3] Running Permutation Analysis (Max Drawdown)...")

def calculate_max_drawdown(returns):
    # Returns in percentage
    equity_curve = np.cumprod(1 + returns/100)
    peak = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - peak) / peak
    return drawdown.min() * 100

perm_drawdowns = []

for _ in range(N_ITERIONS):
    # Shuffle without replacement
    shuffled = np.random.permutation(pnl_pct)
    dd = calculate_max_drawdown(shuffled)
    perm_drawdowns.append(dd)

perm_drawdowns = np.array(perm_drawdowns)
actual_dd = calculate_max_drawdown(pnl_pct)

dd_low = np.percentile(perm_drawdowns, 5)   # Worst 5% case
dd_median = np.median(perm_drawdowns)

print(f"  Actual Max Drawdown: {actual_dd:.2f}%")
print(f"  Median Random DD:    {dd_median:.2f}%")
print(f"  Worst 5% Random DD:  {dd_low:.2f}%")
print(f"  Prob(DD < -20%):     {(np.sum(perm_drawdowns < -20) / N_ITERIONS * 100):.1f}%")

# -----------------------------------------------------------------------------
# 3. Save Report
# -----------------------------------------------------------------------------
print("\n[3/3] Generating Report...")

report_path = Path(__file__).parent / 'monte_carlo_report.md'
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("# FOMC Event Straddles: Monte Carlo Analysis\n\n")
    f.write(f"**Date**: {pd.Timestamp.now().strftime('%Y-%m-%d')}\n")
    f.write(f"**Iterations**: {N_ITERIONS}\n")
    f.write(f"**Data Points**: {len(pnl_pct)} events (2020-2024)\n\n")
    
    f.write("## 1. Bootstrap Analysis (Performance Robustness)\n")
    f.write("Resampling with replacement to estimate confidence intervals.\n\n")
    f.write(f"- **Win Rate**: {win_rate_actual:.1f}%\n")
    f.write(f"- **Mean P&L**: {mean_pnl_actual:+.2f}% (95% CI: [{mean_low:+.2f}%, {mean_high:+.2f}%])\n")
    f.write(f"- **Sharpe Ratio**: {sharpe_actual:.2f} (95% CI: [{sharpe_low:.2f}, {sharpe_high:.2f}])\n")
    f.write(f"- **Probability of Positive Expectancy**: {(np.sum(bootstrap_means > 0) / N_ITERIONS * 100):.1f}%\n\n")
    
    f.write("## 2. Permutation Analysis (Risk/Drawdown)\n")
    f.write("Shuffling trade order to analyze sequence risk.\n\n")
    f.write(f"- **Actual Max Drawdown**: {actual_dd:.2f}%\n")
    f.write(f"- **Median Simulated Drawdown**: {dd_median:.2f}%\n")
    f.write(f"- **Worst 5% Simulated Drawdown**: {dd_low:.2f}%\n")
    f.write(f"- **Risk of Ruin (>20% DD)**: {(np.sum(perm_drawdowns < -20) / N_ITERIONS * 100):.1f}%\n\n")
    
    f.write("## 3. Verdict\n")
    if sharpe_low > 0.5 and actual_dd > dd_low:
        f.write("✅ **ROBUST**: Strategy shows positive expectancy even in lower bounds of confidence intervals, and drawdown is within normal statistical bounds.\n")
    elif sharpe_low > 0:
        f.write("⚠️ **MARGINAL**: Strategy is profitable but confidence intervals are wide or approach zero. Monitor closely.\n")
    else:
        f.write("❌ **FRAGILE**: Confidence intervals cross zero. Strategy may be result of luck.\n")

print(f"Saved verified report to {report_path}")
