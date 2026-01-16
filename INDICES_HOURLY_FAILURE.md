# Indices (SPY/IWM) Short-Interval Analysis

**Date**: 2026-01-15
**Verdict**: ⛔ DO NOT TRADE INDICES INTRA-DAY/HOURLY.

---

## 💥 The Failure

We conducted a "Deep Dive" stress test on SPY and IWM across Hourly and 15-Minute timeframes for the last 12 months (2025-2026). Even with a reduced friction model (3bps), the results were catastrophic.

| Asset | Timeframe | Best Result | Worst Result | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **SPY** | Hourly | +4.8% (RSI-28) | -22.5% | **Avoid** (Buy-Hold was +25%) |
| **SPY** | 15-Min | -8.0% | -31.8% | **Burn Incinerator** |
| **IWM** | Hourly | -9.9% | -21.8% | **Avoid** |
| **IWM** | 15-Min | -7.7% | -34.1% | **Burn Incinerator** |

## 🧠 Why indices fail at short intervals?

1.  **Mean Reversion Noise**: Indices are composed of 500+ (SPY) or 2000+ (IWM) stocks. The aggregate noise effectively cancels out the clean "momentum bursts" seen in individual stocks like NVDA/TSLA.
2.  **Efficiency**: The SPY is the most efficient market in the world. Hourly alpha is near zero.
3.  **HFT Dominance**: Short-interval index trading is dominated by High Frequency Traders (micros/nanoseconds). Retail logic (RSI) cannot compete here.

## 🚀 Strategic Decision

**DO NOT** dilute your edge by forcing System 2 (Hourly) on Indices.

*   **Indices (SPY, IWM, QQQ)**: Stick to **System 1 (Daily Trend)**. It is robust, profitable (+25-50%), and tax-efficient.
*   **Stocks (NVDA, TSLA)**: Use **System 2 (Hourly Swing)**. They have the inefficiencies and volatility required to overcome friction.

**Action**: No hourly config files will be created for SPY/IWM.
