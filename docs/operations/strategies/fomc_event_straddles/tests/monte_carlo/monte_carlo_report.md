# FOMC Event Straddles: Monte Carlo Analysis

**Date**: 2026-01-16
**Iterations**: 10000
**Data Points**: 39 events (2020-2024)

## 1. Bootstrap Analysis (Performance Robustness)
Resampling with replacement to estimate confidence intervals.

- **Win Rate**: 100.0%
- **Mean P&L**: +3.62% (95% CI: [+2.58%, +4.82%])
- **Sharpe Ratio**: 2.84 (95% CI: [2.37, 4.18])
- **Probability of Positive Expectancy**: 100.0%

## 2. Permutation Analysis (Risk/Drawdown)
Shuffling trade order to analyze sequence risk.

- **Actual Max Drawdown**: 0.00%
- **Median Simulated Drawdown**: 0.00%
- **Worst 5% Simulated Drawdown**: 0.00%
- **Risk of Ruin (>20% DD)**: 0.0%

## 3. Verdict
⚠️ **MARGINAL**: Strategy is profitable but confidence intervals are wide or approach zero. Monitor closely.
