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

## 7. DIRECTORY STRUCTURE & TESTING PROTOCOL

**Purpose**: Maintain a standardized, self-documenting structure for every strategy so that validation, tuning, and deployment are reproducible and traceable.

### A. Standard Folder Layout

```
docs/operations/strategies/<STRATEGY_NAME>/
├── README.md                          # User-facing strategy guide
├── backtest.py                        # Main validation script (run this first)
├── backtest_portfolio.py              # Portfolio-level validation (optional)
├── results.csv                        # Results from validation
│
├── assets/                            # ⭐ NEW: Asset-Level Configs
│   ├── <SYMBOL1>/
│   │   ├── config.json                # Trading parameters (REQUIRED)
│   │   └── VALIDATION_REPORT.md       # Performance proof (optional, for primary assets)
│   └── <SYMBOL2>/
│       └── config.json
│
└── tests/                             # Testing & Validation Artifacts
    ├── FINAL_VALIDATION_REPORT.md     # Overall strategy sign-off
    ├── README.md                      # Test suite guide
    │
    ├── tuning/                        # Tuning experiments & expansions
    │   ├── TUNING_REPORT.md           # Summary of tuning findings
    │   ├── run_<experiment>.py        # Experimental scripts
    │   └── <experiment>_results.csv   # Output data
    │
    ├── regime_analysis/               # Regime-specific testing
    │   └── <regime>_results.csv
    │
    ├── slippage/                      # Slippage stress tests
    │   └── slippage_analysis.csv
    │
    └── wfa*/                          # Walk-Forward Analysis folders
        └── wfa_results.csv
```

### B. What Goes Where (And Why)

#### 1. **`/assets/<SYMBOL>/config.json`** ✅ REQUIRED
**Purpose**: Single source of truth for how to trade this asset.  
**Contents**:
```json
{
    "symbol": "NVDA",
    "strategy_name": "hourly_swing",
    "timeframe": "1Hour",
    "parameters": {
        "rsi_period": 28,
        "rsi_upper": 55,
        "rsi_lower": 45
    },
    "deployment_status": "active",
    "max_position_size_usd": 10000
}
```

**Why**: Enables `scripts/update_master_config.py` to auto-sync all strategy configs to the system's `master_config.json`.

#### 2. **`/assets/<SYMBOL>/VALIDATION_REPORT.md`** (Optional)
**Purpose**: Proof of performance for "flagship" assets.  
**When to Create**: For any asset with Sharpe > 1.0 or notable historical results.  
**Contents**: Summarized metrics (Sharpe, Return, Drawdown) and deployment recommendation.

#### 3. **`/tests/FINAL_VALIDATION_REPORT.md`** ✅ REQUIRED (For Strategy Approval)
**Purpose**: The "Go/No-Go" document for deploying the entire strategy.  
**Contents**:
- Overall performance summary (aggregated across all assets)
- Robustness findings (WFA, regime analysis, slippage tests)
- Deployment checklist
- Risk warnings

**Example**: `earnings_straddles/tests/FINAL_VALIDATION_REPORT.md`

#### 4. **`/tests/tuning/TUNING_REPORT.md`**
**Purpose**: Document parameter optimization and asset expansion results.  
**When to Create**: After running tuning experiments (e.g., testing new assets, adjusting filters).  
**Contents**:
- Baseline vs Tuned performance
- Accept/Reject decisions for each tuning attempt
- Updated portfolio composition

#### 5. **`/tests/tuning/run_<experiment>.py`**
**Purpose**: Experimental validation scripts for one-off tests.  
**Naming Convention**:
- `run_amzn_atr_test.py` (Testing ATR filter on AMZN)
- `run_new_assets_test.py` (Scanning candidate assets)
- `run_crypto_hourly_validation.py` (Timeframe shift experiment)

**Output**: Save results to `<experiment>_results.csv` in the same directory.

### C. Testing Protocol (Step-by-Step)

#### Phase 1: Initial Validation
1. Run `backtest.py` on a 2-year sample (2024-2025).
2. Generate `results.csv` with Sharpe, Return, Max DD for each asset.
3. Create `FINAL_VALIDATION_REPORT.md` if strategy passes (Avg Sharpe > 0.5).

#### Phase 2: Robustness Testing
1. Run **Walk-Forward Analysis** (WFA) to test adaptability.
   - Save to `/tests/wfa/wfa_results.csv`
2. Run **Regime Analysis** (Bull/Bear/Sideways splits).
   - Save to `/tests/regime_analysis/`
3. Run **Slippage Stress Test** (doubling/tripling transaction costs).
   - Save to `/tests/slippage/`

#### Phase 3: Tuning & Expansion
1. Identify weak assets (Sharpe < 0.3).
2. Create tuning experiments in `/tests/tuning/`:
   - Try parameter adjustments
   - Test new candidate assets
3. Document findings in `TUNING_REPORT.md`.
4. Update `/assets/<SYMBOL>/config.json` with optimized parameters.

#### Phase 4: Deployment
1. Run `scripts/update_master_config.py` to sync all asset configs.
2. Deploy to **Paper Trading** for 1-2 weeks.
3. If Paper results match backtest (within 20%), deploy to **Live**.

### D. Best Practices

1. **Never Delete Old Tests**: Archive them in `/tests/archive/` if they become obsolete.
2. **Always Version Reports**: Include date in filename or frontmatter (e.g., `TUNING_REPORT_2026-01-16.md`).
3. **CSVs are Gold**: Save raw data from every test. They're small and enable future re-analysis.
4. **One Experiment = One Script**: Don't create "mega-scripts" that test 10 things. Keep experiments atomic.

---
