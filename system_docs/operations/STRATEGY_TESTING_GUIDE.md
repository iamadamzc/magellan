# Magellan Trading System - Strategy Testing Guide

**Created:** 2026-01-18  
**Purpose:** Step-by-step guide to test all 6 validated strategies  
**Test Period:** 1 month simulation (December 2024)  
**Status:** Ready for Execution

---

## 📋 Overview

You have **6 validated strategies** ready for testing:

| # | Strategy | Assets | Type | Test Location |
|---|----------|--------|------|---------------|
| 1 | **Daily Trend Hysteresis** | 4 indices/ETFs | Daily bars | `research/Perturbations/daily_trend_hysteresis/` |
| 2 | **Hourly Swing** | TSLA, NVDA | 1-hour bars | `research/Perturbations/hourly_swing/` |
| 3 | **FOMC Straddles** | SPY options | Event-driven | `research/Perturbations/fomc_straddles/` |
| 4 | **Earnings Straddles** | 7 tickers | Event-driven | `research/Perturbations/earnings_straddles/` |
| 5 | **Bear Trap** | 9 small-caps | 1-minute bars | `research/Perturbations/bear_trap/` |
| 6 | **GSB (Gas & Sugar)** | NG, SB futures | 1-minute bars | `research/Perturbations/GSB/` |

---

## 🎯 Testing Plan Summary

**Test Period:** December 1-31, 2024 (1 month)  
**Why December?** Recent data, should be in cache, represents normal market conditions

---

## Strategy 1: Daily Trend Hysteresis

### 📊 Assets to Test
- **SPY** (S&P 500 ETF)
- **QQQ** (Nasdaq 100 ETF)
- **IWM** (Russell 2000 ETF)
- **GLD** (Gold ETF)

### 📁 Required Data
```
data/cache/equities/SPY_1day_*.parquet
data/cache/equities/QQQ_1day_*.parquet
data/cache/equities/IWM_1day_*.parquet
data/cache/equities/GLD_1day_*.parquet
```

### 🔍 Verify Data Availability
```powershell
# Check if you have daily data for these symbols
Get-ChildItem data\cache\equities\*_1day_*.parquet | Select-String "SPY|QQQ|IWM|GLD"
```

### ⚙️ Configuration
Location: `research/Perturbations/daily_trend_hysteresis/configs`
- SPY: RSI-21, Bands 58/42
- QQQ: RSI-21, Bands 60/40
- IWM: RSI-28, Bands 65/35
- GLD: RSI-21, Bands 65/35

### 🧪 Test Script
```powershell
# Run the perturbation test
python research/Perturbations/daily_trend_hysteresis/test_friction_sensitivity.py
```

### ✅ Expected Results
- **SPY:** ~2-3% for the month
- **QQQ:** ~2.5-3.5% for the month
- **IWM:** Testing 2 trades/year (might be 0 trades in Dec)
- **GLD:** Testing 2 trades/year (might be 0 trades in Dec)

---

## Strategy 2: Hourly Swing Trading

### 📊 Assets to Test
- **TSLA** (Tesla)
- **NVDA** (Nvidia) - ⚠️ **Note:** Strategy marked marginal for NVDA due to stock split issue

### 📁 Required Data
```
data/cache/equities/TSLA_1hour_*.parquet
data/cache/equities/NVDA_1hour_*.parquet
```

### 🔍 Verify Data Availability
```powershell
# Check if you have hourly data
Get-ChildItem data\cache\equities\*_1hour_*.parquet | Select-String "TSLA|NVDA"
```

### ⚙️ Configuration
Location: `research/Perturbations/hourly_swing/configs`
- TSLA: RSI-14, Bands 60/40, **Swing Mode (overnight holds)**
- NVDA: RSI-28, Bands 55/45, **Swing Mode (overnight holds)**

### 🧪 Test Script
```powershell
# Run the gap reversal perturbation test
python research/Perturbations/hourly_swing/test_gap_reversal.py
```

### ✅ Expected Results
- **TSLA:** ~3-4% for the month (very active, ~8-10 trades)
- **NVDA:** ~1-2% for the month (if working correctly)

---

## Strategy 3: FOMC Event Straddles

### 📊 Event to Test
December 2024 had **1 FOMC meeting: December 18, 2024**

### 📁 Required Data
```
data/cache/equities/SPY_1min_*.parquet (for Dec 18, 2024)
research/Perturbations/fomc_straddles/economic_events_2024.json
```

### 🔍 Check FOMC Event Data
```powershell
# View the 2024 FOMC calendar
Get-Content research\Perturbations\fomc_straddles\economic_events_2024.json | Select-String "December"
```

### ⚙️ Strategy Parameters
- **Entry:** T-5 minutes (1:55 PM ET)
- **Exit:** T+5 minutes (2:05 PM ET)
- **Hold Time:** 10 minutes
- **Instrument:** SPY ATM straddle (call + put)

### 🧪 Test Script
```powershell
# Run the slippage perturbation test
python research/Perturbations/fomc_straddles/test_bid_ask_spread.py
```

### ✅ Expected Results
- **Dec 18, 2024:** +23.80% (historical result from validation)
- **Test:** Should replicate this result with slippage stress test

---

## Strategy 4: Earnings Straddles

### 📊 Assets to Test (Any with Dec 2024 earnings)
- GOOGL, AAPL, AMD, NVDA, TSLA, MSFT, AMZN

### 📁 Required Data
```
data/cache/equities/*_1day_*.parquet (for any Dec earnings symbols)
```

### 🔍 Find December Earnings
```powershell
# Check if there's an earnings calendar
Get-Content data\cache\earnings\* | Select-String "2024-12"
```

### ⚙️ Strategy Parameters
- **Entry:** T-2 days before earnings
- **Exit:** T+1 day after earnings
- **Hold Time:** 3 days
- **Instrument:** ATM straddle (7-14 DTE)

### 🧪 Test Script
```powershell
# Run the regime normalization test
python research/Perturbations/earnings_straddles/test_regime_normalization.py
```

### ✅ Expected Results
- Depends on which ticker had earnings in December
- Should show ~15-25% return per event

---

## Strategy 5: Bear Trap

### 📊 Assets to Test (9 validated symbols)
1. **MULN** (best performer, 21.5% avg annual)
2. **ONDS** (11.1% avg annual)
3. **NKLA** (10.6% avg annual)
4. **AMC** (9.0% avg annual)
5. **SENS** (8.3% avg annual)
6. **ACB** (6.7% avg annual)
7. **GOEV** (6.4% avg annual)
8. **BTCS** (5.9% avg annual)
9. **WKHS** (5.0% avg annual)

### 📁 Required Data
```
data/cache/equities/*_1min_*.parquet for:
MULN, ONDS, NKLA, AMC, SENS, ACB, GOEV, BTCS, WKHS
```

### 🔍 Verify Data Availability
```powershell
# Check which Bear Trap symbols have 1-minute data
$symbols = @('MULN','ONDS','NKLA','AMC','SENS','ACB','GOEV','BTCS','WKHS')
foreach ($sym in $symbols) {
    $files = Get-ChildItem data\cache\equities\${sym}_1min_*.parquet -ErrorAction SilentlyContinue
    if ($files) {
        Write-Host "✓ $sym has data: $($files.Count) files"
    } else {
        Write-Host "✗ $sym MISSING data" -ForegroundColor Red
    }
}
```

### ⚙️ Strategy Parameters (Same for all 9 symbols)
- **Entry:** Gap down ≥15%, break below session low, then reclaim with volume
- **Stop:** 0.45 ATR below session low
- **Targets:** 3-stage exit (40%/30%/30%)
- **Max Hold:** 30 minutes
- **Timeframe:** 1-minute bars

### 🧪 Test Scripts Available
```powershell
# Option 1: Run 4-year validation (most comprehensive)
python research/Perturbations/bear_trap/test_bear_trap_4year.py

# Option 2: Run slippage tolerance test
python research/Perturbations/bear_trap/test_slippage_tolerance.py

# Option 3: Run Walk-Forward Analysis
python research/Perturbations/bear_trap/test_bear_trap_wfa.py
```

### ✅ Expected Results (December 2024)
- Intraday strategy: Expect 5-15 trades across all 9 symbols
- Monthly return: ~1-3% (varies with volatility)

---

## Strategy 6: GSB (Gas & Sugar Breakout)

### 📊 Assets to Test
- **NG** (Natural Gas futures)
- **SB** (Sugar futures)

### 📁 Required Data
```
data/cache/futures/NG_1min_*.parquet or NGUSD_1hour_*.parquet
data/cache/futures/SB_1min_*.parquet
```

### 🔍 Verify Futures Data
```powershell
# Check what futures data is available
Get-ChildItem data\cache\futures\NG*.parquet
Get-ChildItem data\cache\futures\SB*.parquet
```

### ⚙️ Strategy Parameters
- **OR Period:** First 10 minutes after session start
- **NG Session:** 13:29 ET
- **SB Session:** 13:30 ET
- **Entry:** Breakout above OR high with volume, then pullback & reclaim
- **Stop:** 0.4 ATR below OR low
- **Target:** 2R (risk:reward)
- **Timeframe:** 1-minute bars

### 🧪 Test Script
Look for or create:
```powershell
# If there's a test file:
python research/Perturbations/GSB/test_*.py

# Otherwise, check the main strategy file:
python research/Perturbations/GSB/gsb_strategy.py
```

### ✅ Expected Results (December 2024)
- **NG:** Variable (depends on energy market volatility)
- **SB:** Variable (agricultural commodity)
- Combined: Should show 1-2% for the month

---

## 🚀 Quick Start: Test All Strategies

### Step 1: Verify Data Availability

Run this comprehensive check:

```powershell
# Create a data availability report
Write-Host "`n=== STRATEGY DATA AVAILABILITY REPORT ===" -ForegroundColor Cyan

# Strategy 1: Daily Trend
Write-Host "`n[Strategy 1] Daily Trend Hysteresis:" -ForegroundColor Yellow
$etfs = @('SPY','QQQ','IWM','GLD')
foreach ($sym in $etfs) {
    $files = Get-ChildItem "data\cache\equities\${sym}_1day_*.parquet" -ErrorAction SilentlyContinue
    if ($files) { Write-Host "  ✓ $sym" -ForegroundColor Green } 
    else { Write-Host "  ✗ $sym MISSING" -ForegroundColor Red }
}

# Strategy 2: Hourly Swing
Write-Host "`n[Strategy 2] Hourly Swing:" -ForegroundColor Yellow
$hourly = @('TSLA','NVDA')
foreach ($sym in $hourly) {
    $files = Get-ChildItem "data\cache\equities\${sym}_1hour_*.parquet" -ErrorAction SilentlyContinue
    if ($files) { Write-Host "  ✓ $sym" -ForegroundColor Green } 
    else { Write-Host "  ✗ $sym MISSING" -ForegroundColor Red }
}

# Strategy 5: Bear Trap
Write-Host "`n[Strategy 5] Bear Trap:" -ForegroundColor Yellow
$beartrap = @('MULN','ONDS','NKLA','AMC','SENS','ACB','GOEV','BTCS','WKHS')
foreach ($sym in $beartrap) {
    $files = Get-ChildItem "data\cache\equities\${sym}_1min_*.parquet" -ErrorAction SilentlyContinue
    if ($files) { Write-Host "  ✓ $sym" -ForegroundColor Green } 
    else { Write-Host "  ✗ $sym MISSING" -ForegroundColor Red }
}

# Strategy 6: GSB
Write-Host "`n[Strategy 6] GSB (Gas & Sugar):" -ForegroundColor Yellow
$futures = @('NG','SB','NGUSD','SBUSD')
foreach ($sym in $futures) {
    $files = Get-ChildItem "data\cache\futures\${sym}*.parquet" -ErrorAction SilentlyContinue
    if ($files) { Write-Host "  ✓ $sym" -ForegroundColor Green }
}

Write-Host "`n"
```

### Step 2: Download Missing Data (if needed)

If any data is missing, you'll need to fetch it using the Magellan data scripts:

```powershell
# Example: Fetch missing equity data for December 2024
python scripts/fetch_data.py --symbol SPY --timeframe 1day --start 2024-12-01 --end 2024-12-31

# Example: Fetch 1-minute data for Bear Trap symbols
python scripts/fetch_data.py --symbol AMC --timeframe 1min --start 2024-12-01 --end 2024-12-31
```

### Step 3: Run Tests In Order

**Priority 1: Simplest Tests (Daily Trend)**
```powershell
cd research\Perturbations\daily_trend_hysteresis
python test_friction_sensitivity.py
```

**Priority 2: Hourly Swing**
```powershell
cd ..\hourly_swing
python test_gap_reversal.py
```

**Priority 3: Bear Trap (Most Complex)**
```powershell
cd ..\bear_trap
# Start with WFA test (most comprehensive)
python test_bear_trap_wfa.py
```

**Priority 4: FOMC & Earnings (Event-Driven)**
```powershell
cd ..\fomc_straddles
python test_bid_ask_spread.py

cd ..\earnings_straddles
python test_regime_normalization.py
```

**Priority 5: GSB (Futures)**
```powershell
cd ..\GSB
# Check what test files exist
ls test_*.py
```

---

## 📊 Create Custom Month-Long Test

If the existing test scripts don't do exactly a 1-month test, you can create a simple custom test. Here's a template:

```python
# test_december_2024.py
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache

# Test parameters
START_DATE = '2024-12-01'
END_DATE = '2024-12-31'
SYMBOL = 'SPY'
TIMEFRAME = '1day'

print(f"\n=== Testing {SYMBOL} for December 2024 ===\n")

# Fetch data
df = cache.get_or_fetch_equity(SYMBOL, TIMEFRAME, START_DATE, END_DATE)

print(f"Data points: {len(df)}")
print(f"Date range: {df.index[0]} to {df.index[-1]}")
print(f"\nFirst few rows:")
print(df.head())

# Calculate simple buy-and-hold return
bh_return = ((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100
print(f"\nBuy-and-hold return for December: {bh_return:.2f}%")
```

---

## 🔧 Troubleshooting

### Issue: "Module not found" errors
**Solution:** Make sure you're running from the project root or the script's directory

### Issue: "No data found in cache"
**Solution:** Run the data fetch scripts in `/scripts` folder

### Issue: "Perturbation test taking too long"
**Solution:** Some tests run 4-year validations. Use December-only custom tests for speed

### Issue: "Test script doesn't accept date parameters"
**Solution:** Most perturbation tests use hardcoded date ranges. Edit the script or create a custom test

---

## ✅ Success Criteria

For each strategy, verify:

1. **✓ Test completes without errors**
2. **✓ Results CSV file is generated** (in `reports/test_results/`)
3. **✓ Returns are positive** (for December 2024)
4. **✓ Trade count is reasonable** (not zero, not excessive)
5. **✓ Metrics align with expectations** (see Expected Results sections above)

---

## 📈 Next Steps After Testing

1. **Review all test results** in `research/Perturbations/reports/test_results/`
2. **Compare to historical validation** in each strategy's `PERTURBATION_TEST_REPORT.md`
3. **Note any anomalies** (missing data, unexpected losses, etc.)
4. **Create summary report** consolidating all findings
5. **Make go/no-go decision** for each strategy based on December results

---

## 📞 Support References

- **Architecture:** `ARCHIVE_INDEX.md`
- **Strategy Specs:** `research/Perturbations/*/parameters_*.md`
- **Validation History:** `research/Perturbations/*/PERTURBATION_TEST_REPORT.md`
- **Deployment Guide:** `DEPLOYMENT_GUIDE.md`
- **Complete Reference:** `VALIDATED_STRATEGIES_COMPLETE_REFERENCE.md`

---

**Last Updated:** 2026-01-18  
**Status:** Ready for Testing  
**Estimated Time:** 2-4 hours (all strategies)
