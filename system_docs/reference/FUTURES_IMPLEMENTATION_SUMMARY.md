# Futures Testing Suite - Implementation Summary

**Created**: 2026-01-16  
**Status**: Ready for Data Infrastructure Phase

---

## WHAT WAS CREATED

### 📁 Documentation (5 files)

1. **`FUTURES_TESTING_MASTER_PLAN.md`** (Master)
   - Complete 5-week roadmap
   - All strategies, all 13 futures contracts
   - Expected outcomes and risk management

2. **`daily_trend_hysteresis/tests/futures/README.md`**
   - Daily RSI hysteresis on futures
   - 13 contracts, 2-year test (2024-2025)

3. **`hourly_swing/tests/futures/README.md`**
   - Hourly RSI hysteresis on high-volatility futures
   - Focus on MBT (Bitcoin), MNG (NatGas), MCL (Crude)

4. **`fomc_event_straddles/tests/futures/README.md`**
   - Event-driven FOMC strategy adapted for futures
   - Two methods: Volatility Breakout, Mean Reversion
   - 8 FOMC events × 13 contracts

5. **`STRATEGY_COMPENDIUM.md`** (EXISTING - review Section 7 for /tests/ structure)

---

### 🐍 Python Scripts (1 template)

1. **`daily_trend_hysteresis/tests/futures/run_futures_baseline.py`**
   - Baseline test for all 13 futures
   - **NOTE**: Currently has placeholder logic
   - **BLOCKER**: Needs Polygon.io client implementation

---

### ⚙️ Configuration Templates (2 examples)

1. **`daily_trend_hysteresis/assets/MES/config.json`**
   - Template for Micro E-mini S&P 500
   - Includes contract specs, backtest placeholders

2. **`hourly_swing/assets/MBT/config.json`**
   - Template for Micro Bitcoin futures
   - Wider bands (65/35) for extreme volatility

---

## DIRECTORY STRUCTURE CREATED

```
docs/operations/strategies/
├── FUTURES_TESTING_MASTER_PLAN.md              ⭐ NEW
│
├── daily_trend_hysteresis/
│   ├── assets/
│   │   └── MES/
│   │       └── config.json                     ⭐ NEW (template)
│   └── tests/
│       └── futures/
│           ├── README.md                       ⭐ NEW
│           └── run_futures_baseline.py         ⭐ NEW
│
├── hourly_swing/
│   ├── assets/
│   │   └── MBT/
│   │       └── config.json                     ⭐ NEW (template)
│   └── tests/
│       └── futures/
│           └── README.md                       ⭐ NEW
│
└── fomc_event_straddles/
    └── tests/
        └── futures/
            └── README.md                       ⭐ NEW
```

---

## FUTURES UNIVERSE (13 CONTRACTS)

### ✅ All CME Micro Futures

| Symbol | Name | Category | Expected Fit |
|--------|------|----------|-------------|
| **MES** | Micro E-mini S&P 500 | Equity Index | ✅ High |
| **MNQ** | Micro E-mini Nasdaq 100 | Equity Index | ✅ High |
| **MYM** | Micro E-mini Dow | Equity Index | ✅ Medium |
| **M2K** | Micro E-mini Russell 2000 | Equity Index | ⚠️ Medium |
| **MCL** | Micro Crude Oil | Commodity | ✅ High (hourly) |
| **MGC** | Micro Gold | Commodity | ✅ High (daily) |
| **MSI** | Micro Silver | Commodity | ⚠️ Medium |
| **MNG** | Micro Natural Gas | Commodity | ✅ High (hourly - extreme vol) |
| **MCP** | Micro Copper | Commodity | ⚠️ Low |
| **M6E** | Micro EUR/USD | Currency | ⚠️ Medium (FOMC events) |
| **M6B** | Micro GBP/USD | Currency | ⚠️ Low |
| **M6A** | Micro AUD/USD | Currency | ⚠️ Low |
| **MBT** | Micro Bitcoin | Crypto | ✅ Very High (hourly) |

**Expected Approvals**: 9-15 contracts across all strategies

---

## NEXT STEPS (IMMEDIATE)

### Step 1: Data Infrastructure ⏰ REQUIRED FIRST

**BLOCKER**: Alpaca doesn't support futures data

**Option A (Recommended): Polygon.io**
```bash
# Sign up at polygon.io (Starter plan: $99/month)
# Then implement in code:
```

```python
# src/data_handler.py (ADD THIS)
import requests

class PolygonFuturesClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io/v2"
    
    def fetch_historical_bars(self, symbol, timeframe, start, end):
        # Implementation here
        pass
```

**Option B (Free): Interactive Brokers**
```bash
pip install ib_insync
# Requires IB account (paper trading is free)
```

---

### Step 2: Run First Baseline Test

Once data is available:
```bash
cd a:\1\Magellan
python docs/operations/strategies/daily_trend_hysteresis/tests/futures/run_futures_baseline.py
```

**Expected Output**:
- `futures_baseline_results.csv` with Sharpe, Return, Max DD for each contract

---

### Step 3: Analyze and Tune

Review results:
1. Identify contracts with Sharpe > 0.7
2. For Sharpe 0.3-0.7, try wider bands (60/40)
3. For Sharpe < 0.3, reject

---

### Step 4: Create Asset Configs

For each approved contract:
```bash
# Example: MES passed with Sharpe 1.2
# Edit: daily_trend_hysteresis/assets/MES/config.json
# Update backtest_results section with actual values
# Set deployment_status: "approved"
```

---

### Step 5: Repeat for Hourly and FOMC

Follow same process:
- Hourly Swing → Focus on MBT, MNG, MCL
- FOMC Events → Focus on MES, M6E

---

## KEY DECISION POINTS

### After Daily Trend Results:
- **If 6+ contracts pass**: CONTINUE to Hourly Swing
- **If 3-5 contracts pass**: Acceptable, but tune more
- **If <3 contracts pass**: Futures may not fit this strategy

### After Hourly Swing Results:
- **If 4+ high-vol contracts pass**: CONTINUE to FOMC
- **If 2-3 contracts pass**: Acceptable (smaller universe)
- **If <2 contracts pass**: Skip FOMC, deploy what works

### After FOMC Results:
- **If 2+ contracts pass**: Build futures portfolio
- **If 0-1 contracts pass**: Skip FOMC for futures

---

## TESTING CHECKLIST

### Daily Trend Hysteresis (Futures)
- [ ] Data source implemented
- [ ] `run_futures_baseline.py` executes successfully
- [ ] `futures_baseline_results.csv` generated
- [ ] ≥4 contracts with Sharpe >0.7
- [ ] Asset configs created for approved contracts
- [ ] `FUTURES_VALIDATION_REPORT.md` written

### Hourly Swing (Futures)
- [ ] Hourly data fetching confirmed
- [ ] `run_futures_hourly.py` created and executed
- [ ] MBT, MNG, MCL tested with wider bands
- [ ] ≥3 contracts with Sharpe >1.0
- [ ] Asset configs created
- [ ] `FUTURES_HOURLY_VALIDATION.md` written

### FOMC Event Straddles (Futures)
- [ ] 1-minute data available for FOMC dates
- [ ] Both methods (Breakout + Reversion) tested
- [ ] ≥2 contracts with Win Rate ≥70%
- [ ] Method winner identified per contract
- [ ] `FOMC_FUTURES_VALIDATION.md` written

### Portfolio Integration
- [ ] All approved contracts added to `master_config.json`
- [ ] Position sizing rules defined
- [ ] Correlation analysis complete
- [ ] `FUTURES_PORTFOLIO_ALLOCATION.md` created

---

## ESTIMATED TIMELINE

| Phase | Duration | Owner | Blocker |
|-------|----------|-------|---------|
| **Data Setup** | 1-2 days | Dev | Polygon.io sign-up |
| **Daily Trend** | 3-5 days | Quant | Data setup |
| **Hourly Swing** | 3-5 days | Quant | Data setup |
| **FOMC Events** | 3-5 days | Quant | Data setup |
| **Portfolio** | 2-3 days | Quant | All tests complete |
| **TOTAL** | **12-20 days** | — | — |

---

## RISK WARNINGS

1. **Futures = Leverage**: 10-20x leverage means 5% price move = 50-100% account move
2. **24-Hour Trading**: Overnight gaps can bypass stops
3. **Margin Calls**: Insufficient margin can force liquidation
4. **Rollover Risk**: Must roll contracts quarterly (cost: 2-5 bps)

**Mitigation**:
- Start with 1 contract per symbol (micro contracts are small)
- Use max 50% futures allocation (diversify with equities)
- Monitor margin 2x daily
- Implement automated rollover logic

---

## QUESTIONS TO RESOLVE

1. **Data Source**: Polygon.io or Interactive Brokers? (Decision: Polygon recommended)
2. **Rolling Contracts**: Use continuous contracts or manual rollover? (Decision: Continuous if available, else automate)
3. **Overnight Holds**: Keep positions 24hrs or close before Asia open? (Decision: Keep for now, monitor risk)
4. **Futures vs Equity Split**: 50/50 or 30/70? (Decision: Start 30% futures, scale to 50%)

---

**STATUS**: 🟡 Awaiting Data Infrastructure  
**NEXT ACTION**: Sign up for Polygon.io and implement `PolygonFuturesClient`  
**COMPLETION**: 5 weeks from data infrastructure completion
