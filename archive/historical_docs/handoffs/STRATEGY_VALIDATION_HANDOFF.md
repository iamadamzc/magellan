# STRATEGY VALIDATION HANDOFF - Continue Testing & Canonization

**Date**: 2026-01-16  
**From**: Agent Session #412  
**To**: Next Agent  
**Status**: 2 of 4 strategies validated and canonized

---

## 🎯 YOUR MISSION

Continue validating and canonizing the remaining trading strategies using the **exact same process** established in this session.

### Strategies Remaining:
1. ⏳ **FOMC Event Straddles** (Options) - Claims +102.7% annual return
2. ⏳ **Earnings Straddles** (Options) - Claims +79.1% annual return

---

## ✅ WHAT'S BEEN COMPLETED

### Strategy 1: Daily Trend Hysteresis ✅
- **Location**: `docs/operations/strategies/daily_trend_hysteresis/`
- **Tested**: 11 assets (MAG7 + 4 ETFs)
- **Results**: 10/11 profitable (91% success)
- **Best**: GOOGL +118%, GLD +87%
- **Excluded**: NVDA -81% (fails on daily timeframe)
- **Files**:
  - `README.md` - Complete strategy guide
  - `backtest_portfolio.py` - Test all assets
  - `backtest_single.py` - Test GOOGL only
  - `results.csv` - Validated results

### Strategy 2: Hourly Swing Trading ✅
- **Location**: `docs/operations/strategies/hourly_swing/`
- **Tested**: 2 assets (TSLA, NVDA)
- **Results**: 2/2 profitable (100% success)
- **Performance**: TSLA +100.6%, NVDA +124.2%
- **Key Finding**: NVDA fails on Daily but succeeds on Hourly!
- **Files**:
  - `README.md` - Strategy guide
  - `backtest.py` - Validation test
  - `results.csv` - Results

---

## 🔧 CRITICAL BUGS FIXED (DO NOT REVERT!)

### Bug #1: Hardcoded Date Range
- **File**: `main.py` lines 560-575
- **Fix**: Now uses CLI `--start-date` and `--end-date` args
- **Impact**: Was always fetching 2022-2025 regardless of input

### Bug #2: Excessive Warmup Buffer
- **File**: `main.py` line 35
- **Fix**: Reduced from 252 to 50 bars
- **Impact**: 5x faster tests, more relevant data

### Bug #3: Backtester Hardcoded to 1-Minute Bars ⚠️ CRITICAL
- **File**: `src/backtester_pro.py` line 160-195
- **Fix**: Now reads `interval` from `node_config` and resamples correctly
- **Impact**: Daily/Hourly strategies were backtesting on minute bars (WRONG!)
- **Result**: All previous backtest results for Daily/Hourly were INVALID

**Documentation**: See `docs/CRITICAL_BUG_FIXES_2026-01-16.md`

---

## 📋 THE VALIDATION PROCESS (FOLLOW EXACTLY)

### Step 1: Research the Strategy
1. Read `VALIDATED_STRATEGIES_FINAL.md` for claimed performance
2. Identify:
   - Assets to test
   - Timeframe (1Min/1Hour/1Day)
   - Parameters (RSI period, bands, etc.)
   - Claimed returns and metrics

### Step 2: Create Validation Test Script
**Template Location**: Use `docs/operations/strategies/daily_trend_hysteresis/backtest_portfolio.py` as reference

**Key Components**:
```python
# 1. Fetch data at correct timeframe
df = client.fetch_historical_bars(
    symbol=symbol,
    timeframe=TimeFrame.Day,  # or Hour, Minute
    start='2024-01-01',
    end='2025-12-31',
    feed='sip'
)

# 2. CRITICAL: Force resample if needed (Alpaca bug)
if len(df) > expected_bars:
    df = df.resample('1D').agg({  # or '1H' for hourly
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()

# 3. Calculate RSI
delta = df['close'].diff()
gains = delta.where(delta > 0, 0.0)
losses = (-delta).where(delta < 0, 0.0)
avg_gain = gains.ewm(span=rsi_period, adjust=False).mean()
avg_loss = losses.ewm(span=rsi_period, adjust=False).mean()
rs = avg_gain / avg_loss.replace(0, np.inf)
df['rsi'] = 100 - (100 / (1 + rs))

# 4. Run Hysteresis Logic
if position == 'flat' and rsi > upper_band:
    position = 'long'  # Enter
elif position == 'long' and rsi < lower_band:
    position = 'flat'  # Exit

# 5. Calculate metrics
total_return = (final_equity / INITIAL_CAPITAL - 1) * 100
sharpe = (returns.mean() / returns.std()) * np.sqrt(252)
max_dd = drawdown.min() * 100
```

### Step 3: Run Validation
```bash
python test_strategy_name.py
```

**Expected Output**:
- Total return
- Sharpe ratio
- Max drawdown
- Number of trades
- Win rate
- Comparison to Buy & Hold

### Step 4: Analyze Results
**Compare to Claims**:
- Is actual return close to claimed?
- Is Sharpe reasonable (>0.5)?
- Are trades realistic (not thousands)?
- Does it beat Buy & Hold?

**Decision Criteria**:
- ✅ **Profitable**: Return > 0%, Sharpe > 0.5
- ⚠️ **Marginal**: Return > 0% but Sharpe < 0.5
- ❌ **Failed**: Return < 0% or excessive trades

### Step 5: Canonize the Strategy
**Directory Structure**:
```
docs/operations/strategies/
└── strategy_name/
    ├── README.md          (strategy guide)
    ├── backtest.py        (validation test)
    └── results.csv        (validated results)
```

**README.md Template** (see existing strategies for format):
```markdown
# STRATEGY NAME - STRATEGY GUIDE

**Status**: ✅ VALIDATED / ❌ FAILED
**Test Period**: 2024-01-01 to 2025-12-31

## 📊 WHAT IS THIS STRATEGY?
[Brief description]

## 🎯 VALIDATED PERFORMANCE
[Results table]

## 🚀 HOW TO RUN IT
[Command to run backtest]

## ⚙️ CONFIGURATION
[Parameters for each asset]

## 💡 KEY INSIGHTS
[Important findings]

## 📁 FILES
[File locations]

## ✅ DEPLOYMENT CHECKLIST
[Readiness checklist]
```

### Step 6: Commit & Document
```bash
git add docs/operations/strategies/strategy_name/
git commit -m "feat: Add [Strategy Name] - VALIDATED

RESULTS:
- Asset1: +X% (Sharpe Y)
- Asset2: +X% (Sharpe Y)

KEY FINDINGS:
- [Important insight 1]
- [Important insight 2]"
```

---

## 📊 REMAINING STRATEGIES TO TEST

### Strategy 3: FOMC Event Straddles (Options)

**Source**: `VALIDATED_STRATEGIES_FINAL.md` lines 123-160

**Claims**:
- **Return**: +102.7% annual
- **Sharpe**: 1.17
- **Win Rate**: 62.5%
- **Trades**: 8 per year (one per FOMC event)

**Strategy Details**:
- **Type**: Options straddles (buy ATM call + put)
- **Entry**: 2:00 PM ET on FOMC day
- **Exit**: 2:10 PM ET (10-minute hold)
- **Asset**: SPY
- **Capital**: $10K per event

**Testing Challenges**:
⚠️ **This requires OPTIONS data**, not equity bars!
- Need to fetch options chains from Alpaca
- Need to calculate straddle P&L (call + put)
- May need different data source

**Recommendation**:
1. Check if Alpaca provides historical options data
2. If not, may need to use options pricing models (Black-Scholes)
3. Or skip and document as "requires options data"

---

### Strategy 4: Earnings Straddles (Options)

**Source**: `VALIDATED_STRATEGIES_FINAL.md` lines 162-200

**Claims**:
- **Return**: +79.1% annual
- **Sharpe**: 2.25
- **Win Rate**: 58.3%
- **Trades**: 12 per year

**Strategy Details**:
- **Type**: Options straddles on earnings
- **Assets**: GOOGL, META, NVDA, TSLA
- **Entry**: 3:59 PM ET (before earnings)
- **Exit**: Next day 9:31 AM ET
- **Capital**: $5K per event

**Testing Challenges**:
⚠️ **Same as FOMC - requires OPTIONS data**

**Recommendation**:
- Same as Strategy 3
- May need to document and defer to paper trading

---

## 🔍 IMPORTANT CONTEXT

### Why Some Strategies Failed

1. **NVDA on Daily Trend**: -81%
   - Too volatile for daily timeframe
   - Works on hourly (+124%)
   - **Lesson**: Different assets need different timeframes

2. **HFT Strategies**: All failed
   - See `research/high_frequency/HFT_FINAL_RESEARCH_SUMMARY.md`
   - Friction costs too high
   - Sample bias issues
   - **Conclusion**: Abandon HFT, focus on lower-frequency

### Data Resolution Bug (CRITICAL)

**The Problem**:
Alpaca API returns minute bars even when you request daily/hourly bars.

**The Fix**:
Always check bar count and resample:
```python
if len(df) > 1000:  # Too many bars for daily
    df = df.resample('1D').agg({...}).dropna()
```

**Verification**:
Look for this in output:
```
⚠️  Got 343060 bars, resampling to daily...
✓ 541 daily bars
```

---

## 📁 KEY FILES & LOCATIONS

### Configuration:
- `config/nodes/master_config.json` - Strategy parameters

### Core Code:
- `src/features.py` line 693 - Hysteresis logic
- `src/backtester_pro.py` - Backtester (now uses correct intervals)
- `src/data_handler.py` - Data fetching & resampling

### Documentation:
- `VALIDATED_STRATEGIES_FINAL.md` - Strategy claims
- `docs/CRITICAL_BUG_FIXES_2026-01-16.md` - Bug fixes
- `README.md` - Project overview

### Validated Strategies:
- `docs/operations/strategies/daily_trend_hysteresis/`
- `docs/operations/strategies/hourly_swing/`

---

## 🎯 SUCCESS CRITERIA

For each strategy, you should:

1. ✅ **Create validation test script**
2. ✅ **Run on 2024-2025 data** (2 full years minimum)
3. ✅ **Compare to claimed performance**
4. ✅ **Analyze results** (profitable? realistic?)
5. ✅ **Canonize** (create README, organize files)
6. ✅ **Commit** (with clear commit message)
7. ✅ **Document findings** (update this handoff if needed)

---

## ⚠️ POTENTIAL BLOCKERS

### Options Data Availability
- **Issue**: Strategies 3 & 4 require options data
- **Check**: Does Alpaca provide historical options chains?
- **Fallback**: Document as "requires options data" and defer to paper trading

### API Rate Limits
- **Issue**: Fetching lots of historical data
- **Solution**: Add delays between requests if needed

### Timeframe Confusion
- **Issue**: Different strategies use different timeframes
- **Solution**: Always verify bar count matches expected
  - Daily: ~500 bars for 2 years
  - Hourly: ~3000-8000 bars for 2 years
  - Minute: ~100,000+ bars (usually wrong!)

---

## 📞 QUESTIONS TO ASK USER

If you encounter issues:

1. **Options data unavailable**: "Should I skip options strategies or use pricing models?"
2. **Strategy fails validation**: "Strategy X shows -Y% return. Should I document as failed or investigate further?"
3. **Unclear parameters**: "Strategy X documentation is unclear on [parameter]. Should I test multiple configurations?"

---

## 🚀 GETTING STARTED

### Immediate Next Steps:

1. **Read this entire document** - Understand the process
2. **Review completed strategies** - See the pattern
3. **Check options data availability**:
   ```python
   from alpaca.data import OptionsDataClient
   # Test if historical options data is available
   ```
4. **Start with Strategy 3** (FOMC Event Straddles)
5. **Follow the validation process exactly**

### Expected Timeline:
- Strategy 3: 1-2 hours (if options data available)
- Strategy 4: 1-2 hours (similar to Strategy 3)
- Total: 2-4 hours

---

## 📚 REFERENCE EXAMPLES

### Example: Daily Trend Hysteresis
**See**: `docs/operations/strategies/daily_trend_hysteresis/backtest_portfolio.py`
- Shows how to test multiple assets
- Proper resampling logic
- Clean output format

### Example: Hourly Swing
**See**: `docs/operations/strategies/hourly_swing/backtest.py`
- Shows hourly timeframe handling
- Simpler (only 2 assets)
- Good for reference

---

## ✅ FINAL CHECKLIST

Before completing your session:

- [ ] All remaining strategies tested
- [ ] Results documented in strategy READMEs
- [ ] Files organized in `docs/operations/strategies/`
- [ ] All changes committed with clear messages
- [ ] Update main `README.md` if needed
- [ ] Create handoff for next agent (if work remains)

---

## 🎉 COMPLETION CRITERIA

Your work is done when:

1. ✅ All 4 strategies have been tested
2. ✅ Each has a dedicated directory with README, test script, results
3. ✅ Main README updated with links to all strategies
4. ✅ All findings documented
5. ✅ Code committed and pushed

---

**Good luck! Follow the process, and you'll do great.** 🚀

**Questions?** Check the completed strategies for examples.
