# Quick Start: Testing Your 6 Strategies

**Goal:** Test each strategy with a 1-month simulation  
**Time Required:** 2-4 hours  
**Difficulty:** Moderate

---

## 🎯 30-Second Overview

You have 6 validated strategies. Each has test scripts in `research/Perturbations/[strategy_name]/`. Let's run them systematically.

---

## Step 1: Check Your Data (5 minutes)

```powershell
cd a:\1\Magellan

# Quick check - see what symbols you have
Get-ChildItem data\cache\equities\*.parquet | ForEach-Object { $_.Name.Split('_')[0] } | Sort-Object -Unique | Select-Object -First 30
```

**Look for:**
- SPY, QQQ, IWM, GLD (for Strategy 1)
- TSLA, NVDA (for Strategy 2)
- AMC, MULN, ONDS,NKLA, SENS, ACB, GOEV, BTCS, WKHS (for Strategy 5)

---

## Step 2: Strategy 1 - Daily Trend Hysteresis (15 minutes)

**Easiest to start with!**

```powershell
cd research\Perturbations\daily_trend_hysteresis

# Look at the test file
cat test_friction_sensitivity.py

# Run it
python test_friction_sensitivity.py
```

**What it tests:** How the strategy performs with different friction costs (commissions/slippage)

**Expected output:** CSV file with results for SPY, QQQ, IWM, GLD

**Success criteria:** All 4 symbols should be profitable even with friction

---

## Step 3: Strategy 2 - Hourly Swing (20 minutes)

```powershell
cd ..\hourly_swing

# Check the test
cat test_gap_reversal.py

# Run it
python test_gap_reversal.py
```

**What it tests:** How strategy handles gap-up/gap-down scenarios

**Expected output:** TSLA and NVDA results with gap fade simulations

**Success criteria:** Should remain profitable even when 50% of gaps fade

---

## Step 4: Strategy 5 - Bear Trap (30-60 minutes)

**Most data-intensive!**

```powershell
cd ..\bear_trap

# List available tests
ls test_*.py

# Option A: Run Walk-Forward Analysis (recommended)
python test_bear_trap_wfa.py

# Option B: Run 4-year full validation
python test_bear_trap_4year.py

# Option C: Quick slippage test
python test_slippage_tolerance.py
```

**What it tests:** Small-cap reversal strategy across 9 symbols

**Expected output:** Performance metrics for each of the 9 validated symbols

**Success criteria:** 
- MULN, ONDS should show consistent profits
- At least 7/9 symbols profitable

**⚠️ Note:** This may take 30-60 minutes if it needs to fetch 1-minute data

---

## Step 5: Strategy 6 - GSB (15 minutes)

```powershell
cd ..\GSB

# Check what test files exist
ls *.py

# If there's a test file, run it
# Otherwise, check the main strategy file
cat gsb_strategy.py
```

**What it tests:** Natural Gas and Sugar futures breakout strategy

**Expected output:** NG and SB performance 

**Success criteria:** Both contracts should show positive returns

---

## Step 6: Strategy 3 & 4 - Options Strategies (10 minutes each)

### FOMC Straddles:
```powershell
cd ..\fomc_straddles

# Run slippage test
python test_bid_ask_spread.py
```

### Earnings Straddles:
```powershell
cd ..\earnings_straddles

# Run regime test
python test_regime_normalization.py
```

**What it tests:** Options strategies under stress (slippage, regime change)

**Success criteria:** Should remain profitable even under harsh conditions

---

## 🔥 If You Get Errors

### Error: "No module named 'src'"
**Fix:**
```powershell
# Make sure you're in the project root
cd a:\1\Magellan

# Then run with full path
python research\Perturbations\bear_trap\test_bear_trap_wfa.py
```

### Error: "Data not found"
**Fix:**
```powershell
# Check if you have the data
ls data\cache\equities\*AMC*.parquet

# If missing, fetch it (if you have fetch script)
python scripts\fetch_data.py --symbol AMC --timeframe 1min --start 2024-01-01 --end 2024-12-31
```

### Error: Test script doesn't exist
**Fix:** Some strategies might only have the main strategy file, not separate test scripts. In that case:
1. Read the `parameters_*.md` file to understand the strategy
2. Read the `PERTURBATION_TEST_REPORT.md` to see previous test results
3. Consider the strategy validated based on those reports

---

## 📊 What to Look For in Results

Each test should produce:

1. **CSV file** - Detailed trade-by-trade results
2. **Console output** - Summary statistics
3. **Key metrics:**
   - Total Return (should be positive)
   - Sharpe Ratio (should be > 1.0)
   - Win Rate (varies by strategy)
   - Max Drawdown (should be reasonable)
   - Number of trades (should match expectations)

---

## ✅ Completion Checklist

- [ ] Strategy 1 (Daily Trend): Test ran, results look good
- [ ] Strategy 2 (Hourly Swing): Test ran, TSLA/NVDA profitable
- [ ] Strategy 3 (FOMC): Test ran, slippage tolerance confirmed
- [ ] Strategy 4 (Earnings): Test ran, regime-proof confirmed
- [ ] Strategy 5 (Bear Trap): Test ran, 7+ symbols profitable
- [ ] Strategy 6 (GSB): Test ran, NG & SB both profitable

---

## 🎓 Understanding the Tests

### Perturbation Tests = Stress Tests

The tests in `research/Perturbations/` are **NOT** simple backtests. They are:

- **Adversarial tests** - Deliberately making conditions worse
- **Slippage stress** - Adding extra costs to see if strategy survives
- **Regime tests** - Simulating market condition changes
- **Robustness checks** - Verifying parameters aren't overfitted

**If a strategy passes perturbation tests, it's REALLY validated.**

---

## 🚀 After Testing

1. **Collect all CSV results** from each strategy folder
2. **Create a summary spreadsheet** comparing all 6 strategies
3. **Review against expectations** in `VALIDATED_STRATEGIES_COMPLETE_REFERENCE.md`
4. **Check for anomalies**:
   - Any strategy that lost money?
   - Any with zero trades (might mean data issue)?
   - Any with way too many trades (might mean parameter issue)?

5. **Make deployment decision**:
   - ✅ Green light: Results match validation, proceed to paper trading
   - ⚠️ Yellow light: Results okay but need investigation
   - ❌ Red light: Results contradict validation, DO NOT deploy

---

## 💡 Pro Tips

1. **Start with Strategy 1** (Daily Trend) - it's the simplest and fastest
2. **Run Bear Trap overnight** if it's slow (lots of 1-min data)
3. **Take notes** as you test - document any errors or oddities
4. **Compare results** to the parameter files - they list expected returns
5. **Don't panic if one test fails** - could be a data issue, not strategy issue

---

## 📞 Where to Look for Help

- **Strategy logic:** `research/Perturbations/[strategy]/parameters_*.md`
- **Previous test results:** `research/Perturbations/[strategy]/PERTURBATION_TEST_REPORT.md`
- **Deployment info:** `research/Perturbations/[strategy]/DEPLOYMENT_GUIDE.md` (where it exists)
- **Overall status:** `research/Perturbations/DEPLOYMENT_INDEX.md`

---

**Ready to start?** 

```powershell
cd a:\1\Magellan\research\Perturbations\daily_trend_hysteresis
python test_friction_sensitivity.py
```

Good luck! 🚀
