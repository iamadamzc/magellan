# Bear Trap ML Scanner - Session 1 Status Report

**Date**: January 21, 2026  
**Branch**: `research/bear-trap-ml-scanner`  
**Status**: Foundation complete, API endpoint issue identified

---

## ✅ Completed

### 1. Project Planning
- Comprehensive implementation plan created
- 35-feature ML architecture designed
- 4-tier framework specified (Tier 2: classifier, Tier 4: risk allocator)
- 6-week timeline established

### 2. Repository Setup
- Created `research/bear-trap-ml-scanner` branch
- Established project structure (6 directories)
- Committed initial setup

### 3. Data Collection Scripts
- Built `collect_validated_symbols.py` - modular data collector
- Configured for 14 validated Bear Trap symbols
- Includes progress tracking and error handling

---

## 🚧 Current Blocker

### **FMP API Legacy Endpoint Issue**

**Problem**: FMP intraday endpoints are marked as "legacy" and require higher tier:
- `/historical-chart/5min/{symbol}` → Legacy Endpoint error
- `/stock_market/losers` → Legacy Endpoint error

**Impact**: Cannot collect historical intraday data with current approach

**Solutions**:

#### Option 1: Use Alpaca Historical Data (Recommended)
- Alpaca Market Data Plus includes historical intraday bars
- Available back to Feb 2024 (23 months)
- We already have the subscription
- Better for our use case (real-time compatible)

```python
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

client = StockHistoricalDataClient(api_key, api_secret)
request = StockBarsRequest(
    symbol_or_symbols='MULN',
    timeframe=TimeFrame.Minute,  # 1-min or 5-min
    start=datetime(2024, 10, 1),
    end=datetime(2024, 12, 31)
)
bars = client.get_stock_bars(request)
```

#### Option 2: Upgrade FMP Plan
- Move from current tier to higher tier with intraday access
- More expensive, may not be necessary

#### Option 3: Use FMP Current API Structure
- Research modern FMP endpoints for intraday data
- May exist under different path structure

---

## 📋 Next Session Tasks

1. **Immediate Priority**: Switch to Alpaca historical data API
   - Update `collect_validated_symbols.py` to use Alpaca
   - Test data collection for Q4 2024
   - Validate we can retrieve -15% selloff events

2. **Data Collection**: Once API fixed
   - Collect Q4 2024 test dataset
   - Expand to 2024 full year if successful
   - Target: 50-200 selloff events for initial analysis

3. **EDA Phase**: After data collected
   - Analyze selloff frequency and distribution
   - Validate "30-minute hold time" hypothesis
   - Calculate feature importance heuristics

4. **Feature Engineering**: Pipeline setup
   - Build extraction framework for 35 features
   - Test on sample dataset

---

## 📊 Current Codebase

```
research/bear_trap_ml_scanner/
├── README.md                                    ✅
├── data_collection/
│   ├── fetch_historical_selloffs.py           ⚠️ (Legacy endpoint issue)
│   ├── collect_validated_symbols.py            ⚠️ (Needs Alpaca integration)
│   └── test_fmp.py                            ✅ (Diagnostic tool)
├── analysis/                                    📝 (Ready for EDA)
├── models/                                      📝 (Ready for ML)
├── scanner/                                     📝 (Future)
├── backtesting/                                 📝 (Future)
└── data/
    └── raw/                                     ⏳ (Empty, awaiting first collection)
```

---

## 💡 Key Insights

1. **Market Calm in Q4 2024**: Zero -15% selloffs found suggests bull market conditions
   - May need to test with more volatile periods (2022 crash, 2023 volatility)
   - Or expand threshold to -10% for testing

2. **Data Source Strategy**: Alpaca is better for our long-term needs
   - Integrates with existing infrastructure
   - Real-time + historical unified API
   - Already paying for it

3. **Validated Symbols Approach**: Smart starting point
   - 14 symbols × 252 trading days × 4 years = ~14,000 symbol-days
   - Even if only 1% have selloffs = 140 events (sufficient for initial ML)

---

## 🎯 Success Criteria (Unchanged)

- ML model achieves >65% accuracy predicting reversals
- Out-of-sample backtest shows >10% improvement vs baseline
- Scanner discovers 3-10 tradeable candidates per day
- False positive rate <35%

---

**Session handoff ready**. Primary blocker identified and solutions proposed. Recommend starting next session with Alpaca API integration.
