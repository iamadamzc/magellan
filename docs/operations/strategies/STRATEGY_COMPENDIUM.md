# MAGELLAN STRATEGY COMPENDIUM & TUNING GUIDE

**Date**: 2026-01-16  
**Version**: 1.0  
**Scope**: Strategy Logic, Validation Methods, and Refinement Protocols

---

## 1. INTRODUCTION

This document serves as the "Owner's Manual" for the Magellan Strategy Suite. It details the logic behind each validated strategy, how it was tested, and crucially, **how to continue tuning it** as market conditions evolve.

The portfolio is constructed of three distinct "engines," each designed to capture a different type of market alpha.

| Strategy Engine | Alpha Source | Timeframe | Ideal Regime |
| :--- | :--- | :--- | :--- |
| **Daily Trend Hysteresis** | Momentum & Trends | Daily | Bull/Bear Trends |
| **Hourly Swing** | Intraday Volatility | Hourly | High Volatility |
| **Earnings Straddles** | Event Gaps | Event-Based | Earnings Season |

---

## 2. STRATEGY ENGINE: DAILY TREND HYSTERESIS

**Symbol**: `daily_trend_hysteresis`  
**Status**: Core Driver (Steady Growth)

### A. The Logic
This is a trend-following system based on **RSI Hysteresis**.
*   **Entry**: RSI crosses ABOVE 55 (Momentum Confirmed)
*   **Exit**: RSI crosses BELOW 45 (Trend Broken)
*   **The "Dead Zone"**: Between 45-55, the strategy *holds* its current state. This "hysteresis" prevents the strategy from getting chopped up in sideways noise.

### B. Validation Method
*   **Test Period**: 2024-2025 (2 Full Years)
*   **Universe**: MAG7 + Major Indices (SPY, QQQ, IWM, GLD)
*   **Metric**: Sharpe Ratio & Max Drawdown
*   **Key Finding**: Works exceptionally well on steady assets (GOOGL, GLD, META). Fails on parabolic/crash assets (NVDA).

### C. How to Tune & Refine
**When to Tune**:
*   If an asset consistently produces small losses in a sideways market (Whipsaw).
*   If the strategy misses the start of big trends.

**Tuning Levers**:
1.  **RSI Period (Default: 28 for Daily)**
    *   *Increase (e.g., 35)*: Slower, smoother, fewer trades. Good for noisy assets.
    *   *Decrease (e.g., 14)*: Faster, catches earlier entries, more false signals.
2.  **Bands (Default: 55/45)**
    *   *Widen (e.g., 60/40)*: Reduces trade frequency aggressively. Use for highly volatile assets (TSLA).
    *   *Tighten (e.g., 52/48)*: Increases sensitivity. Use for very stable assets (Indices).

**Refinement Protocol**:
1.  Run `backtest_single.py` with the new parameters on the last 6 months.
2.  If Sharpe improves > 0.1 without increasing Max DD > 5%, deploy.

---

## 3. STRATEGY ENGINE: HOURLY SWING

**Symbol**: `hourly_swing`  
**Status**: Tactical Alpha (High Risk/Reward)

### A. The Logic
Scaled-down version of the Hysteresis logic applied to **Hourly Bars** to capture multi-day swings in high-beta assets.
*   **Entry**: Hourly RSI > 60 (Breakout)
*   **Exit**: Hourly RSI < 40 (Breakdown)
*   **Hold Time**: Typically 2-5 days (Overnight holds are key).

### B. Validation Method
*   **Test Period**: 2024-2025
*   **Universe**: High Beta Tech (NVDA, TSLA, PLTR)
*   **Key Finding**: Hourly timeframe captures moves that Daily misses on volatile assets. Requires "High Volatility" band settings (60/40 vs 55/45).

### C. How to Tune & Refine
**When to Tune**:
*   If friction costs (slippage/commissions) are eating > 20% of profits.
*   If the strategy executes > 1 trade per day (Over-trading).

**Tuning Levers**:
1.  **Timeframe**
    *   *Shift to 2-Hour or 4-Hour*: Drastically reduces noise and trade count while keeping trend logic.
2.  **Bands (Default: 60/40)**
    *   *Widen to 65/35*: Only take the most extreme momentum moves. recommended for "Meme Stocks" or Crypto.

**Refinement Protocol**:
1.  Use `tests/tuning/run_new_assets_test.py` to scan candidates.
2.  Target: Sharpe > 0.5 (accounting for 5bps friction).

---

## 4. STRATEGY ENGINE: EARNINGS STRADDLES

**Symbol**: `earnings_straddles`  
**Status**: Super Alpha (Event Driven)

### A. The Logic
Exploits the tendency of high-beta stocks to make massive moves (gaps) on earnings reports that exceed the options market's priced-in move.
*   **Trade**: Buy Straddle (ATM Call + Put) at T-2 days.
*   **Exit**: Sell at T+1 (Market Open).
*   **Filter**: **SPY > 200-Day MA** (Bull Market Regime Only).

### B. Validation Method
*   **Test Period**: 2020-2025 (6 Years)
*   **Key Finding**: Fails in Bear Markets (2022). "Super Alpha" in Bull Markets for PLTR, COIN, META.

### C. How to Tune & Refine
**When to Tune**:
*   If Win Rate drops below 50% for 2 consecutive quarters.
*   If Option Premiums become too expensive (IV Rank > 90 consistently).

**Tuning Levers**:
1.  **Regime Filter**
    *   *Current*: SPY > 200MA.
    *   *Refinement*: Add VIX < 25 filter if volatility is too high across the board.
2.  **Entry Timing**
    *   *Current*: T-2 Days.
    *   *Refinement*: T-1 Day (Closer to event, less theta decay, but potentially higher IV).

**Refinement Protocol**:
1.  Run `tests/tuning/run_earnings_expanded.py` to re-validate the basket.
2.  Add/Remove tickers based on recent "Earnings Reaction Magnitude" (ERM).

---

## 5. CONTINUOUS IMPROVEMENT LOOP

To keep Magellan healthy, perform this **Quarterly Maintenance Ritual**:

1.  **The Purge**: Run `backtest_portfolio.py` for all strategies on the *last 3 months*.
    *   Any asset with Sharpe < 0 is put on "Watchlist".
    *   Any asset with Sharpe < 0 for 2 quarters is **Removed**.

2.  **The Scout**: Run `run_new_assets_test.py` on a watchlist of 10-20 new tickers.
    *   Any asset with Sharpe > 1.0 is a candidate for **Incubation** (Paper Trading).

3.  **The Audit**: Check `config/nodes/master_config.json`.
    *   Ensure all parameters match the latest validation reports.
    *   Standardize position sizing based on recent volatility.

---

**Artifacts Reference**:
*   Logic: `src/features.py`
*   Configs: `docs/operations/strategies/*/assets/*/config.json`
*   Validation: `docs/operations/strategies/*/tests/`

---

## 6. FMP API REFERENCE (CRITICAL!)

**⚠️ IMPORTANT**: FMP has deprecated many legacy endpoints. Use the correct `/stable/` endpoints to avoid 403/404 errors.

### A. Crypto Historical Data

**CORRECT Endpoint** (1-Hour Interval):
```
https://financialmodelingprep.com/stable/historical-chart/1hour?symbol=BTCUSD&apikey=YOUR_KEY
```

**Response Format**: 
```json
[
  {"date": "2024-01-01 00:00:00", "open": 42000, "high": 42100, "low": 41900, "close": 42050, "volume": 1234},
  ...
]
```

**Key Notes**:
- ✅ Returns a **LIST** directly (NOT `{"historical": [...]}`).
- ✅ Symbol uses **no hyphen**: `BTCUSD` (not `BTC-USD`).
- ✅ Query parameters: `symbol`, `from` (optional), `to` (optional), `apikey`.

**Other Intervals**:
- `/stable/historical-chart/1min?symbol=BTCUSD` (1-Minute)
- `/stable/historical-chart/1day?symbol=BTCUSD` (Daily)
- `/stable/historical-price-eod/full?symbol=BTCUSD` (Full Daily History)

### B. Earnings Calendar

**CORRECT Endpoint** (Company Earnings):
```
https://financialmodelingprep.com/stable/earnings?symbol=AAPL&apikey=YOUR_KEY
```

**Response Format**:
```json
[
  {"date": "2024-02-01", "symbol": "AAPL", "eps": 2.18, "epsEstimated": 2.10, "time": "amc", "revenue": 123.9, "revenueEstimated": 121.0},
  ...
]
```

**DEPRECATED** (Do NOT Use):
- ❌ `/api/v3/historical/earning_calendar/AAPL` (Returns 403 Forbidden)

### C. Stock Price Data (Equities)

**Daily Bars** (SIP Feed via Alpaca Recommended):
```python
alpaca_client.fetch_historical_bars('NVDA', TimeFrame.Day, '2024-01-01', '2025-12-31', feed='sip')
```

**If using FMP** (NOT recommended for equities backtesting):
```
https://financialmodelingprep.com/api/v3/historical-price-full/NVDA?apikey=YOUR_KEY
```

### D. Common Pitfalls

1. **Crypto vs Equity Endpoints**: 
   - Crypto uses `/stable/` 
   - Equities use `/api/v3/`
   
2. **Response Structure**:
   - Crypto endpoints return `LIST` directly.
   - Equity endpoints return `{"historical": [...]}`
   
3. **Rate Limits**: 
   - Free tier: 250 requests/day
   - Starter: 750 requests/day
   - Use chunked fetching (90-day windows) for large date ranges.

### E. Debugging Script

If you encounter FMP issues, run:
```bash
python docs/operations/strategies/daily_trend_hysteresis/tests/crypto_validation/debug_fmp_api.py
```

This will probe all major endpoints and report which are working.

---
