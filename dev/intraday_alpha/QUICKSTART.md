# 🚀 Quick Start: Running Phase 1.1 Baseline Backtest

## Current Status

✅ **Testing regimen designed** (6 phases, 19 tests, 14 deployment gates)  
✅ **Phase 1.1 smoke test script ready** (`run_phase1_baseline_backtest.py`)  
⚠️ **Waiting for API credentials** to fetch historical data

---

## What's Needed to Run the Test

The backtest script needs **Alpaca API credentials** to fetch historical market data for SPY/QQQ/IWM (2024-2025). Based on the Magellan testing infrastructure patterns, here are your options:

### **Option 1: Create `.env` File** (Recommended - Matches Magellan Pattern)

Create a `.env` file in the project root (`a:\1\Magellan\.env`) with:

```bash
# Alpaca API Credentials (Paper Trading)
APCA_API_KEY_ID=your_alpaca_api_key
APCA_API_SECRET_KEY=your_alpaca_secret_key
APCA_API_BASE_URL=https://paper-api.alpaca.markets

# FMP API Credentials (for sentiment data - optional for now)
FMP_API_KEY=your_fmp_api_key
```

**Where to get credentials:**
- **Alpaca**: Sign up at https://alpaca.markets (free paper trading account)
- **FMP**: Sign up at https://financialmodelingprep.com (Ultimate plan for `/stable/` endpoints)

Once `.env` is created, run:
```bash
cd a:\1\Magellan\test\intraday_alpha
python run_phase1_baseline_backtest.py
```

---

### **Option 2: Set Environment Variables Directly**

If you prefer not to create a `.env` file, set variables in PowerShell:

```powershell
$env:APCA_API_KEY_ID = "your_alpaca_api_key"
$env:APCA_API_SECRET_KEY = "your_alpaca_secret_key"
$env:APCA_API_BASE_URL = "https://paper-api.alpaca.markets"

cd a:\1\Magellan\test\intraday_alpha
python run_phase1_baseline_backtest.py
```

---

### **Option 3: Use Pre-Cached Data** (If Available)

If you've already run other Magellan backtests and have cached data for SPY/QQQ/IWM:

1. Check if cache exists: `a:\1\Magellan\data\cache\equities\`
2. Look for files like: `SPY_1min_20240101_20260110.parquet`
3. If present, the DataCache will use them automatically (no new API calls)

**Note**: You still need credentials set (even if cached), as the DataCache initialization requires them.

---

## What the Test Will Do

Once credentials are set, the Phase 1.1 smoke test will:

1. **Fetch data** for SPY/QQQ/IWM (1-minute bars, 2024-2025) via DataCache
2. **Resample** to 3-minute (IWM) and 5-minute (SPY/QQQ) bars
3. **Calculate** RSI + Volume signals per the V1.0 strategy logic
4. **Simulate** trades with +1 bar lag and 5 bps slippage
5. **Generate** comprehensive metrics (Sharpe, Win Rate, PnL, etc.)
6. **Check** 5 deployment gates (Sharpe >1.0, Win Rate >45%, etc.)
7. **Output** recommendation: PASS / CONDITIONAL / FAIL

**Expected Runtime**: 5-15 minutes (depending on data fetch speed)

---

## Expected Output

```
================================================================================
🚀 PHASE 1.1: BASELINE BACKTEST (2024-2025)
================================================================================
Period: 2024-01-01 → 2026-01-10
Symbols: SPY, QQQ, IWM
Initial Capital: $25,000.00
Slippage: 5 bps per trade
================================================================================

📥 Fetching data for SPY (5Min)...
✅ Fetched 12,450 bars for SPY
...

📊 BACKTEST RESULTS
================================================================================

💰 FINANCIAL PERFORMANCE
  Initial Capital:    $   25,000.00
  Final Equity:       $   XX,XXX.XX
  Total P&L:          $   +X,XXX.XX
  Total Return:           +XX.XX%
  Sharpe Ratio:              X.XX
  Max Drawdown:            -XX.XX%

📈 TRADE STATISTICS
  Total Trades:              XXX
  Winning Trades:            XXX
  Losing Trades:             XXX
  Win Rate:                XX.XX%
  Profit Factor:             X.XX

🚦 PHASE 1.1 ASSESSMENT
================================================================================

Gate Checks:
  ✅/❌ Sharpe Ratio > 1.0
  ✅/❌ Win Rate > 45%
  ✅/❌ Profit Factor > 1.3
  ✅/❌ Max Drawdown < 20%
  ✅/❌ Trade Count > 100

Gates Passed: X/5 (XX%)

✅ RECOMMENDATION: PASS - Proceed to full Phase 1-2 testing
  OR
⚠️ RECOMMENDATION: CONDITIONAL - Review results before proceeding
  OR
❌ RECOMMENDATION: FAIL - Consider early kill or strategy modification
```

Results will be saved to:
- `a:\1\Magellan\test\intraday_alpha\results\phase1_baseline_trades.csv`
- `a:\1\Magellan\test\intraday_alpha\results\phase1_baseline_equity.csv`

---

## After the Smoke Test

Based on the results:

### If PASS (≥4/5 gates):
→ Proceed with full **Phase 1-2 testing** (Week 1 of regimen)
- Multi-regime stress test (2022-2025)
- Friction escalation ladder
- Parameter stability audit
- Timing shift stress

### If CONDITIONAL (3/5 gates):
→ Discuss findings and decide:
- Continue with modified expectations?
- Adjust parameters and retest?
- Skip to Phase 2.4 (sentiment dependency test)?

### If FAIL (<3/5 gates):
→ Strategy likely not viable for deployment
- Document findings
- Recommend archiving or fundamental redesign

---

## Questions?

- **"I don't have Alpaca API keys"**: Sign up for free paper trading at alpaca.markets
- **"I don't want to use my real keys"**: Paper trading keys are separate from live trading
- **"Can I skip fetching data?"**: Not for this test - we need 2024-2025 data that may not be cached
- **"What if FMP sentiment is unavailable?"**: The test will still run; sentiment is weighted 0-10% only

---

## Ready to Proceed?

Once you have: ations set up
- Run: `python run_phase1_baseline_backtest.py`
- Review results (5-10 min)
- We'll discuss next steps based on the gates passed

**Status**: ⏸️ AWAITING API CREDENTIALS  
**Next Action**: Set up `.env` file or environment variables, then run test
