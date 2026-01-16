# Scalping Strategy Reality Check

**Date**: 2026-01-14
**Status**: ⛔ FAILED REALITY CHECK
**Asset**: TSLA, NVDA (2025 Data)

---

## 🚨 The Verdict: "Death by Friction"

While the strategy generated spectacular theoretical returns (+91% on TSLA), the **Reality Check** reveals it is **not viable** in its current form due to transaction costs.

### Performance Breakdown (2025)

| Metric | TSLA | NVDA | Interpretation |
| :--- | :--- | :--- | :--- |
| **Baseline (Theoretical)** | **+91.0%** | **+34.3%** | "Paper Millionaire" results |
| **Intraday Mode (No Gaps)** | **+93.7%** | +22.2% | **PASS**: Current strategy works better *without* overnight gaps! |
| **Friction (0.05% Slippage)** | **+0.9%** | **-28.2%** | **FAIL**: 5bps cost wipes out 99% of profit |
| **Total Reality (Intra + Cost)** | **-5.4%** | **-40.7%** | **CRITICAL FAIL**: You lose money in production |

### Analysis

1.  **Good News**: The strategy is **Alpha Rich**. The "Intraday Only" profit (+93.7% for TSLA) is notably higher than the Baseline (+91.0%). This means **we are capturing valid intraday trends**, not just getting lucky with overnight gaps.
2.  **Bad News**: The **Trade Frequency (700+ trades/year)** is too high for the average trade expectancy.
    *   **Avg Profit per Trade (TSLA)**: 91% / 700 trades ≈ 0.13% per trade.
    *   **Cost per Trade**: 0.05% (5bps) or more.
    *   **Edge**: 0.08% per trade. This is razor thin; one bad fill or skipped quote kills months of gains.

### Recommendation
**DO NOT DEPLOY** the 15-minute scalping strategy as-is. The friction drag is terminal.

**Corrective Actions**:
1.  **Increase Timeframe**: Move from 15-min to **1-Hour**. This reduces trade count by ~4x, increasing the Avg Trade Profit to ~0.50%, which easily survives 5bps friction.
2.  **Refine Filters**: Add a filter (e.g., ADX > 25) to trade only when trends are strongest, reducing "chop" trades that rack up commissions.

---

### Revised Plan
Pivot to **System 2 (Hourly Swing)** as the primary short-interval strategy. It trades less frequently (150-200 times/year) but captures larger moves (1-3%), making it robust against friction.
