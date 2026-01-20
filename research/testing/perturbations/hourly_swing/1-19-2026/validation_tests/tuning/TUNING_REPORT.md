# HOURLY SWING - TUNING REPORT

**Date**: 2026-01-16  
**Strategy**: Hourly Swing Trading  
**Status**: ✅ **SUCCESS (TUNING COMPLETED)**

---

## EXECUTIVE SUMMARY

Tuning efforts focused on optimizing **AMZN** (via ATR filters) and identifying **New Assets** (AMD, META, COIN, PLTR).

**Key Outcomes:**
1.  **AMZN Failed**: Adding an ATR filter **worsened** performance (Sharpe -0.45). AMZN should be **dropped**.
2.  **PLTR Validated**: **PLTR** emerged as a powerful new asset (Sharpe 0.68, +114.6% Return), comparable to TSLA/NVDA performance.
3.  **Others Rejected**: AMD, META, and COIN failed to meet the Sharpe > 0.5 threshold.

---

## DETAILED FINDINGS

### 1. AMZN Tuning (ATR Filter) ❌
- **Baseline**: Weak performance (Sharpe ~0.36 historically).
- **Tuned (ATR > 2%)**: **FAILED** (Sharpe -0.45).
- **Insight**: AMZN's hourly moves are too noisy or efficient for this logic. Volatility filtering reduced opportunity count without improving signal quality.
- **Decision**: **REMOVE from portfolio**.

### 2. New Asset Expansion
Tested on 2024-2025 Hourly Data (Alpaca SIP):

| Asset | Sharpe | Return | Status |
|-------|--------|--------|--------|
| **PLTR** | **0.68** | **+114.6%** | ✅ **DEPLOY** |
| META | 0.23 | +12.2% | ❌ Reject |
| AMD | 0.16 | +5.1% | ❌ Reject |
| COIN | 0.14 | -6.0% | ❌ Reject |

**PLTR Insight**: Palantir (PLTR) exhibits high-momentum characteristics similar to NVDA/TSLA, making it an ideal candidate for this strategy.

---

## UPDATED PORTFOLIO

The Hourly Swing portfolio has been rebalanced:

**IN (Active):**
1.  **NVDA**: Sharpe 0.90, Return +124%
2.  **TSLA**: Sharpe 0.68, Return +100%
3.  **PLTR**: Sharpe 0.68, Return +115% (NEW)
4.  **GLD**: Sharpe 0.52 (Defensive Hedge)

**OUT (Removed):**
- **AMZN**: Performance degraded.
- **Indices (SPY/QQQ)**: Rejected previously.

---

## DEPLOYMENT ACTIONS
1.  Create `assets/PLTR` folder + config.
2.  Remove `AMZN` references from active configurations.
3.  Deploy PLTR with standard "High Vol" settings (RSI-14, 60/40).

---

**Artifacts**:
- `tuning/run_amzn_atr_test.py`
- `tuning/run_new_assets_test.py`
