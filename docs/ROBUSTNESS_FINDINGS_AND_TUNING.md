# ROBUSTNESS FINDINGS & TUNING RECOMMENDATIONS

**Date**: 2026-01-16
**Status**: Validation Complete

## 1. STRATEGY: FOMC Event Straddles
**Status**: ❌ **CRITICAL FAILURE**
**Finding**: 
- Backtest relied on an invalid linear pricing model.
- A 0.10% spot move generated +5% simulated profit, which is mathematically impossible for an ATM straddle (requires ~2% move to break even at expiry, or massive IV spike).
- **Stress Test**: Model showed profit even at 2.0% slippage, confirming it is a "hallucination engine" disconnected from real options mechanics.
**Recommendation**: **DO NOT DEPLOY**. Redesign using a verified Options Pricing Engine (Black-Scholes).

## 2. STRATEGY: Daily Trend Hysteresis
**Status**: ⚠️ **ASSET DEPENDENT (SPY FAILED)**
**Finding**: 
- **SPY Walk-Forward**: FAILED. Sharpes ~0.0 to -0.1 across 2020-2025. OOS Returns consistently flat or negative (e.g., -14% in mid-2022).
- **Asset Specificity**: The strategy (RSI > 55 = Buy) depends entirely on **Strong Momentum** (e.g., NVDA, BTC). It fails on mean-reverting indices like SPY.
**Tuning / Refinement**:
- **Universe Restriction**: whitelist ONLY high-momentum assets (e.g., Top 10% RS Rating). Do not trade on Indices.
- **Regime Filter**: Add `VIX < 25` to filter out chopped markets where the strategy bleeds 15-20%.
- **Parameter Adjustment**: RSI-21 with 65/35 bands performed slightly better than RSI-14.

## 3. STRATEGY: Hourly Swing (TSLA)
**Status**: ⚠️ **HIGH VOLATILITY / BEAR MARKET RISK**
**Finding**: 
- **2020/2023/2024**: Exceptional Performance. Win rates > 60%, OOS Returns +30-60% per window (e.g., +67% in Sep 2024).
- **2022 (Bear Market)**: **CATASTROPHIC FAILURE**. Window 8 (Jun 2022) lost **-63%** with a Sharpe of -1.07. The strategy kept buying the dip in a crashing market.
**Tuning / Refinement**:
- **Trend Filter**: **MANDATORY**. Do not take Long signals if Price < 200-Hour MA or Daily MA50. This would have prevented the 2022 wipeout.
- **Stop Loss**: Implement a hard stop (e.g., 3-5%) or Time Stop (exit if no profit in 24 hours) to prevent "bag holding" during crashes.
- **Execution**: Use Limit Orders pegged to Mid. Market orders will eat 5-10% of annual alpha.

## 4. STRATEGY: Earnings Straddles
**Status**: ⚠️ **REGIME DEPENDENT**
**Findings**:
- Validated profitable in 2023-2024 (AI Boom).
- Failed in 2022 (-17% Sharpe).
**Tuning / Refinement**:
- **IV Rank Filter**: Only buy straddles when IV Rank < 50.
- **Sector Rotation**: Only trade earnings in sectors above their 50-day MA.
- **Structure**: Consider Debit Spreads instead of pure Long Straddles to reduce Theta risk.

## SUMMARY VERDICT
- **FOMC**: 🛑 **REJECT** (Redesign needed).
- **Daily Trend**: ⚠️ **CONDITIONAL** (High-Momentum Assets ONLY).
- **Hourly Swing**: ⚠️ **CONDITIONAL** (Must have Trend Filter & Stops).
- **Earnings**: ⚠️ **CONDITIONAL** (Bull Market Only).

*Deployment is NOT recommended without these Refinements.*
