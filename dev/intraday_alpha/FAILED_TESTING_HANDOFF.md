# 💀 POST-MORTEM: Intraday Alpha (RSI Momentum)
**Status:** ❌ PERMANENTLY ARCHIVED (FAILED)
**Date:** 2026-01-24
**Final Verdict:** Structural Incompatibility

## 1. The Experiment
We tested the hypothesis that **Intraday Momentum** on Index ETFs (QQQ, SPY, IWM) could be captured using a standard RSI(14) trigger on short timeframes.

## 2. The Tests & Failures
We ran 6 distinct variations spanning the 2022-2026 market cycle:

| Test Configuration | Timeframe | Logic | Result | Cause of Death |
| :--- | :--- | :--- | :--- | :--- |
| **Baseline V1.0** | 5-Min | RSI > 75 (Hold to Crash) | **-12% to -24%** | **Frequency Friction:** 1,500+ trades/year ate 100% of alpha. |
| **Momentum Repair** | 5-Min | RSI > 60 (Fast Exit) | **Capital Depletion** | **Noise:** Triggered on every minor fluctuation. Death by 1000 cuts. |
| **Reversion Pivot** | 5-Min | Buy RSI < 30 (Dip) | **-4% to -20%** | **Knife Catching:** Bought failing trends during 2022 crash. |
| **Trend Filter** | 15-Min | SMA200 Filter | **-26%** | **Lag:** SMA on 15m is too fast to filter true Bear Regimes. |
| **Pure Swing** | 1-Hour | RSI > 60 (Hold) | **-7.5%** | **Giveback:** Held winners until they turned into losers (Lack of TP). |
| **Sniper** | 1-Hour | TP +2% / SL -1% | **-6.3%** | **Poor Signal:** RSI > 55 is not predictive enough to hit 2% target before 1% stop. |

## 3. The Structural Flaws
1.  **The "Square Peg" Problem:** RSI is a Mean Reversion oscillator. Using it to chase break-outs (Momentum) on Intraday charts means **buying the top** of the 5-minute candle 70% of the time.
2.  **Friction vs. Expectancy:** The "Edge" per trade (< 0.2%) is smaller than the "Cost" per trade (Slippage + Spread + Commissions).
3.  **Regime Sensitivity:** The strategy performs reasonably well in 2024 (Bull) but suffers **Catastrophic Drawdowns** (-25%) in 2022 (Bear). It lacks a robust biological immune system against downtrends.

## 4. RECOMMENDATION: STRATEGIC PIVOT
**DO NOT** continue optimizing RSI parameters. The well is dry.

**Next Steps (The "Gap Hunter"):**
Pivot to **Structural Imbalance** strategies rather than Indicator strategies.
*   **Logic:** Opening Range Breakout (ORB) on Gaps.
*   **Why:** A Gap Up > 2% represents a real-world change in value (Earnings, News). It creates a sustained imbalance that outweighs friction.
*   **Action:** Build `strategy_gap_orb.py` targeting specific stocks (NVDA, TSLA, AAPL) rather than broad indices.
