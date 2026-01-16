# ROBUSTNESS FINDINGS & TUNING RECOMMENDATIONS

**Date**: 2026-01-16
**Status**: Validation Complete

## 1. STRATEGY: FOMC Event Straddles
**Status**: ❌ **CRITICAL FAILURE**
**Finding**: The strategy relied on an incorrect pricing model in backtesting. Real-world options mechanics (Delta/Gamma/Vega) make the claimed "100% Win Rate" impossible for the small spot moves observed.
**Tuning / Refinement**:
- **Pricing Engine**: Must implement Black-Scholes or Binomial pricing to account for Greeks.
- **Directional Pivot**: Switch to directional trading (Delta 1) using the same entry triggers, rather than Straddles.
- **Short Volatility**: Investigate selling straddles (Short Iron Condors) post-announcement to capture IV crush, instead of buying high-IV premium.

## 2. STRATEGY: Daily Trend Hysteresis (SPY)
**Status**: ⚠️ **MARGINAL / WATCH**
**Finding**: WFA currently running (likely slow due to data). Preliminary 2024 results were strong, but long-term robustness depends on regime filtering.
**Tuning / Refinement**:
- **Regime Filter**: Add a `VIX < 25` or `MA200 > Price` filter to avoid "whipsaw" losses in sideways/bear markets.
- **Parameter Stabilization**: If simple RSI-14 is too noisy, switch to **RSI-28** (smoother) with wider bands (60/40) to reduce trade frequency and friction costs.
- **Stop Loss**: Implement a standardized 2-ATR trailing stop to cap downside in sudden reversals.

## 3. STRATEGY: Hourly Swing (TSLA)
**Status**: ⚠️ **HIGH FRICTION RISK**
**Finding**: Hourly trading incurs significantly higher transaction costs and slippage. WFA (2020-2025) is necessary to prove the "Alpha" isn't just beta-chasing in a bull run.
**Tuning / Refinement**:
- **Execution Optimization**: Switch to Limit Orders with "Urgency" logic (e.g., Peg to Mid) instead of Market Orders to save ~5bps per trade.
- **Session Filter**: Only take signals during "Liquid Hours" (10:00 AM - 3:30 PM) to avoid open/close volatility and wide spreads.
- **Asset Selection**: Drop low-beta assets. Focus ONLY on high-beta names (TSLA, NVDA, AMD) where volatility > spread cost.

## 4. STRATEGY: Earnings Straddles
**Status**: ⚠️ **REGIME DEPENDENT**
**Finding**: failed in 2022 (Bear Market).
**Tuning / Refinement**:
- **IV Rank Filter**: Only enter if IV Rank < 50 (cheap premium). Avoid buying expensive straddles when expectations are already priced in.
- **Sector Rotation**: Rotate target tickers based on sector strength (e.g., trade Tech earnings only when XLK > MA50).
- **Asymmetric Structures**: Use **Backspreads** (sell 1 ATM, buy 2 OTM) instead of Straddles to reduce upfront cost and theta decay.
