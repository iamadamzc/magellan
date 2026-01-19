# Bear Trap ML Simulation Walkthrough
**Date:** 2026-01-19
**Status:** 🔴 ML VALIDATION FAILED

## Executive Summary
A "True Simulation" backtest (Engine Replay) was conducted on the 2024 Bear Trap cohort (GOEV, MULN, NKLA) to validate the proposed XGBoost ML improvements. 

**Result:** The ML Filter **destroyed 98% of the strategy's profitability** in a realistic simulation, contradicting previous CSV-based findings.
- **Baseline PnL:** +$15,258 (+15.2%)
- **ML Enhanced PnL:** +$352 (+0.3%)
- **Validation Verdict:** **REJECT ML ENHANCEMENT**. Deploy Baseline.

## The Discrepancy
Previous analysis (`verify_handoff_claims.py`) claimed the ML model improved average R-multiple from +0.15R to +0.34R. This summary validation was based on pre-extracted CSV data properly matching training features.
When running a *True Simulation* (re-calculating features from raw price data tick-by-tick):
- The model consistently predicted `0.00` probability for the strategy's biggest winning trades (specifically in MULN).
- These winners were characterized by **Extreme Volatility (ATR Percentile 1.0)** and **High Volume (Ratio > 2.0)**.
- The model appears to have learned that "Extreme Setup = Trap" based on 2020-2023 data, and thus filtered out the "Black Swan" winners of 2024 that defied the historical odds.

## Technical Findings
1. **Feature Engineering Drift:** Found and patched a discrepancy where Training Data used a truncated 7-period ATR lookback vs 20-period in Simulation. Patching this did NOT resolve the failure.
2. **Probability Collapse:** The calibrated model outputs extremely polarized probabilities (`0.00` or `0.99`). It output `0.00` for all major 2024 winners.
3. **Baseline Robustness:** The Baseline strategy (without ML) proved robust, generating +$15k profit on the top 3 tickers alone, confirming the underlying mechanical edge exists without ML complexity.

## Artifacts Created
- `scripts/run_simulation_backtest.py`: The "Source of Truth" simulation engine that revealed the failure.
- `models/bear_trap_enhanced_xgb.pkl`: The failed model (archived for research, do not deploy).

## Recommendation
**IMMEDIATE:**
1. **Discard** the ML enhancement for the current deployment cycle.
2. **Deploy** the `bear_trap_strategy.py` in its Baseline configuration (Lookahead fixed).
3. **Archive** the ML research as a "Negative Result" to prevent re-treading this path without fundamental changes to labeling logic.

**FUTURE RESEARCH:**
- Investigate "Outcome Labeling" leakage (`early_momentum`) in the training pipeline.
- Retrain model essentially targeting *only* "Average R > 0" without complex "Risk Posture" scoring, which may have biased the model against high-volatility winners.
