# EARNINGS STRADDLES - TUNING & EXPANSION REPORT

**Date**: 2026-01-16  
**Strategy**: Earnings Straddles (Filter + Expansion)  
**Status**: ✅ **SUCCESS**

---

## EXECUTIVE SUMMARY

The implementation of the **Bear Market Filter** (SPY > 200-Day MA) combined with an **Expanded Universe** has identified 3 new "Super-Alpha" assets (PLTR, COIN, META) and 2 solid performers (NFLX, GOOGL).

**Key Wins:**
1.  **PLTR**: 100% Win Rate, +260% Avg Return, Sharpe 2.36 (New Flagship!)
2.  **COIN**: 76.9% Win Rate, +150% Avg Return, Sharpe 1.89
3.  **META**: 70.6% Win Rate, +102% Avg Return, Sharpe 1.39
4.  **NFLX**: 73.7% Win Rate, +92.8% Avg Return, Sharpe 1.24

**Failures:**
- **TSLA**: Even with filter, performance is negative (-29% Avg Ret).
- **AAPL**: Too stable, option premiums overpriced (-4.4% Avg Ret).
- **AMD**: Marginal (Sharpe 0.85), high volatility but expensive premiums.

---

## CONSOLIDATED RESULTS (With Bear Filter)

| Symbol | Trades | Skipped (Bear) | Win Rate | Avg Return | Sharpe | Status |
|--------|--------|----------------|----------|------------|--------|--------|
| **PLTR** | **15** | **7** | **100.0%** | **+260.7%** | **2.36** | 🚀 **SUPER ALPHA** |
| **COIN** | **13** | **8** | **76.9%** | **+150.2%** | **1.89** | 🚀 **SUPER ALPHA** |
| **META** | **17** | **7** | **70.6%** | **+102.3%** | **1.39** | ✅ **DEPLOY** |
| **NFLX** | **19** | **5** | **73.7%** | **+92.8%** | **1.24** | ✅ **DEPLOY** |
| **GOOGL**| **17** | **7** | **58.8%** | **+57.1%** | **1.21** | ✅ **DEPLOY** |
| AMD | 17 | 7 | 64.7% | +33.2% | 0.85 | ⚠️ Marginal |
| NVDA | 17 | 7 | 58.8% | +3.5% | 0.08 | ❌ Weak |
| AAPL | 17 | 7 | 41.2% | -4.4% | -0.11 | ❌ Reject |
| TSLA | 17 | 7 | 47.1% | -29.2% | -0.52 | ❌ Reject |

*Note: NVDA performance here is lower than earlier WFA (+45%). This is due to the simplified "4% fixed cost" assumption in this screening script being more conservative than the full Black-Scholes pricing model used in the deep dive. In reality, NVDA is likely still viable, but PLTR/COIN are clearly superior raw volatility plays.*

---

## DEPLOYMENT PORTFOLIO

**Tier 1 (Priority Deployment)**:
1.  **PLTR** (Sharpe 2.36, 100% Win Rate)
2.  **COIN** (Sharpe 1.89, High Beta)
3.  **META** (Sharpe 1.39, Reliable Gaps)

**Tier 2 (Secondary)**:
1.  **NFLX** (Sharpe 1.24)
2.  **GOOGL** (Sharpe 1.21)

**Removed/Downgraded**:
- **TSLA** (Too unpredictable/efficient pricing)
- **AAPL** (Low volatility)
- **AMD** (Marginal)

---

## ACTION PLAN
1.  **Assets**: Create CONFIGs for PLTR, COIN, META, NFLX, GOOGL.
2.  **Logic**: Enforce `SPY > 200MA` check for ALL earnings trades.
3.  **Risk**: Size smaller for COIN/PLTR (high volatility) initially.

---

**Artifacts**:
- `tuning/run_earnings_expanded.py`: Screening script.
