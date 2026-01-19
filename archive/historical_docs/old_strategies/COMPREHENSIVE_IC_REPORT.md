# Comprehensive Regime & IC Analysis Report
**Date**: 2026-01-14
**Objective**: Determine viability of Intraday Alpha Engine across multiple asset classes.

## 1. Executive Summary
The Intraday Alpha Engine (Standardized Linear Combination of RSI/Volume/Sentiment on 1Min-1Hour bars) has been **stress-tested across 3 distinct asset classes** (Tech, Indices, Commodities).

**The Verdict**: 🚨 **SYSTEMIC FAILURE**
The current signal logic is **non-predictive** at intraday frequencies (1m - 60m) net of transaction costs.

| Asset Class | Ticker | Timeframe | Logic | Hit Rate | P&L Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Tech (High Vol)** | NVDA | 5-Min | Momentum | ~50% | **LOSS** |
| **Tech (High Vol)** | NVDA | 15-Min | Reversion | ~48% | **LOSS** |
| **Tech (High Vol)** | NVDA | 1-Hour | Reversion | ~49% | **LOSS** |
| **Index (Liquid)** | SPY | 15-Min | Reversion | ~48% | **LOSS** |
| **Commodity** | GLD | 15-Min | Reversion | ~49% | **LOSS** |

## 2. Quantitative Diagnosis

### A. Information Coefficient (IC) Scan
We performed a deep statistical scan (Spearman Rank Correlation) on **1 Year** of data.

*   **5-Minute Horizon**:
    *   All Assets showed **Negative IC** for RSI (Mean Reversion).
    *   Strength: Weak (-0.01 to -0.07).
    *   Implication: Statistical noise dominates. Signal-to-Noise Ratio (SNR) is too low to trade profitably.
*   **1-Hour Horizon** (NVDA Specific):
    *   RSI IC: **-0.24** (Strong Mean Reversion).
    *   Implication: The signal exists theoretically, but execution friction (spread/slippage) erodes 100% of the alpha in backtesting.

### B. Signal "Inversion" Test
We tested the hypothesis that the strategy was simply "upside down" (Trend Following in a Mean Reverting market).
*   **Action**: We forced `Weight = -1.0` (Short High RSI).
*   **Result**: No improvement in P&L.
*   **Conclusion**: The market is not just mean-reverting; it is **efficiently random** at this scale for these simple indicators.

## 3. Structural Flaws Identified
1.  **Frequency Mismatch**: 5-15 minute candles are dominated by HFT market making (liquidity provision). Simple directional indicators (RSI) are essentially essentially coin flips here.
2.  **Cost Hurdle**: The "Average Profit per Trade" at 15-min frequency is smaller than the "Cost per Trade" (Spread + Slippage + Fees).
3.  **Indicator Simplicity**: RSI and Volume Z-Score are widely known and arbitraged away at high frequencies.


## 4. Strategic Pivot Experiments (Daily Trend)
Following the breakdown of Intraday Alpha, we executed a **365-Day Stress Test** on a **Daily Trend Following** strategy (RSI > 50 = Buy, Long Only).

*   **Hypothesis**: Daily Trends are robust to noise and transaction costs.
*   **Result**: **LOSS**.
*   **Diagnosis**: **Whipsaw**.
    *   The strategy correctly identified the trend but suffered form "Over-Trading" in choppy consolidation periods.
    *   Without a **Hysteresis Buffer** (e.g., Buy > 55, Sell < 45), the system bought/sold repeatedly around the threshold (50.0), accumulating transaction costs that eroded the trend profits.

## 5. Expert Recommendation: "Retooling" Plan

We do not need to discard the infrastructure (Backtester, Data Handler, Executor are solid). We must **Refine the Logic**.

### Option A: The "Daily Trend + Hysteresis" (Recommended)
Stay on Daily Timeframes but implement **Signal Smoothing**.
*   **Logic**: Momentum with **Schmidt Trigger**.
    *   **Buy**: RSI > 55
    *   **Sell**: RSI < 45
    *   **Hold**: 45-55 (Do nothing).
*   **Action**: Set `SENTRY_GATE` to `0.10` (or significant buffer) to stop the churn.

### Option B: The "Basket" Pivot
Trade the entire MAG7 universe simultaneously to reduce idiosyncratic variance.
*   **Logic**: Long/Short Equity (Long strongest, Short weakest).
*   **Complexity**: High.

### Option C: The "Alternative Data" Pivot
Stay intraday but abandon Price/Volume indicators.
*   **Data**: Order Book Imbalance, Real-time Sentiment (Twitter/News), Options Flow.
*   **Complexity**: Very High (Requires new data feeds).

## 6. Next Steps
**Immediate Action**: Deploy **Variant F (Daily Hysteresis)**.
1.  Set `METABOLISM` to `1Day`.
2.  Set `SENTRY_GATE` to `0.1` (to prevent whipsaw).
3.  Run a 1-Year Backtest on NVDA.

This pivot uses the same engine but targets a completely different (and typically more profitable) regime.

