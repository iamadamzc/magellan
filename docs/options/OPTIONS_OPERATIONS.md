# OPTIONS TRADING OPERATIONS GUIDE

**Version**: 1.0  
**Last Updated**: 2026-01-15  
**Status**: 🚧 Under Development (Phase 1 in progress)

---

## 📋 **TABLE OF CONTENTS**

1. [Quick Start Commands](#quick-start-commands)
2. [Configuration Files](#configuration-files)
3. [Daily Operations Workflow](#daily-operations-workflow)
4. [Parameter Tuning](#parameter-tuning)
5. [Monitoring & Alerts](#monitoring--alerts)
6. [Troubleshooting](#troubleshooting)

---

## 🚀 **QUICK START COMMANDS**

### **Phase 1: API Testing (Development Only)**

```bash
# Test Alpaca options API connection
python research/options_api_test.py

# Expected output:
# ✅ Account Status: ACTIVE
# ✅ Options Trading Approved: 2
# ✅ Found 127 SPY call contracts
# ✅ ALL TESTS PASSED!
```

### **Phase 2-3: Backtesting**

```bash
# Run options backtest on SPY (2024-2026)
python research/test_options_system1.py --symbol SPY --start-date 2024-01-01 --end-date 2026-01-15

# Run exhaustive parameter sweep (delta, DTE, IV filters)
python research/options_parameter_sweep.py --symbol SPY --config config/options/SPY.json

# Compare options vs equity performance
python research/compare_options_vs_equity.py --symbols SPY,QQQ,IWM
```

### **Phase 4: Paper Trading**

```bash
# Deploy paper trading bot (market hours only)
python main_options.py --mode paper --symbols SPY --config config/options/SPY.json

# Monitor paper trading performance
python research/monitor_options_paper.py

# Generate daily P&L report
python research/generate_options_pnl_report.py --date 2026-01-15
```

### **Phase 5: Live Trading** (After Paper Validation)

```bash
# Deploy live (REQUIRES CONFIRMATION)
python main_options.py --mode live --symbols SPY --config config/options/SPY.json --confirm-live

# Daily monitoring
python research/monitor_options_live.py --alert-on-loss-pct 10
```

---

## 📁 **CONFIGURATION FILES**

### **Directory Structure**

```
config/options/
├── master_options_config.json    # Global options settings
├── SPY.json                       # SPY-specific config
├── QQQ.json                       # QQQ-specific config
├── IWM.json                       # IWM-specific config
├── AAPL.json                      # AAPL-specific (Tier 2)
└── GOOGL.json                     # GOOGL-specific (Tier 2)
```

### **Configuration Parameters Explained**

**File**: `config/options/SPY.json`

```json
{
  "symbol": "SPY",
  "strategy": "System1_Daily_Hysteresis",
  
  // ========== SIGNAL GENERATION ==========
  // (REUSED FROM EQUITY - DO NOT MODIFY HERE)
  "rsi_period": 21,
  "rsi_buy_threshold": 58,
  "rsi_sell_threshold": 42,
  
  // ========== OPTIONS-SPECIFIC PARAMETERS ==========
  
  // Strike Selection
  "target_delta": 0.60,          // Delta for strike selection (0.50-0.70)
                                 // 0.50 = ATM (max premium)
                                 // 0.60 = Slightly ITM (recommended)
                                 // 0.70 = Deeper ITM (less leverage)
  
  // Expiration Management
  "min_dte": 45,                 // Minimum days to expiration for new positions
  "max_dte": 60,                 // Maximum days to expiration for new positions
  "roll_threshold_dte": 7,       // Roll position when DTE falls below this
  
  // Risk Management
  "max_iv_rank": 70,             // Don't enter if IV rank > 70 (expensive)
  "earnings_blackout_days": 7,   // Close positions X days before earnings
  "max_position_size_contracts": 5, // Max contracts per position
  "target_notional_exposure": 10000, // Target $ exposure (delta-adjusted)
  
  // Position Sizing
  "position_sizing_method": "delta_adjusted", // or "fixed"
  "contracts_per_signal": 3,     // If using "fixed" method
  
  // Friction Model (for backtesting)
  "slippage_pct": 1.0,           // 1% slippage on options (bid-ask spread)
  "contract_fee": 0.097,         // Alpaca regulatory fees per contract
  
  // Monitoring
  "alert_on_loss_pct": 20,       // Alert if position down >20%
  "alert_on_theta_decay_pct": 50 // Alert if theta eaten >50% of premium
}
```

### **When to Modify Configuration**

| Parameter | Modify When | Impact |
|-----------|-------------|--------|
| `target_delta` | Want more/less leverage | Higher delta = more directional exposure, less leverage |
| `min_dte` / `max_dte` | Adjust theta decay tolerance | Longer DTE = less daily theta, more capital tied up |
| `roll_threshold_dte` | Manage roll frequency | Lower threshold = fewer rolls, more expiration risk |
| `max_iv_rank` | Filter expensive options | Lower threshold = fewer trades, better option prices |
| `target_notional_exposure` | Adjust position size | Scales with account size |
| **DO NOT MODIFY** | `rsi_period`, `rsi_buy_threshold` | These are **equity signal params** - modify in equity config only |

---

## 📅 **DAILY OPERATIONS WORKFLOW**

### **Pre-Market (8:30 AM - 9:25 AM ET)**

1. **Check System Health**
   ```bash
   python research/options_health_check.py
   ```
   - Verifies API connectivity
   - Checks for upcoming earnings (closes positions if needed)
   - Validates current positions vs expected

2. **Review Open Positions**
   ```bash
   python research/list_options_positions.py
   ```
   Output:
   ```
   [SPY] Position: 3 contracts SPY260221C00590000
         Entry: $1.45 | Current: $1.62 | P&L: +$51 (+11.7%)
         DTE: 37 days | Delta: 0.62 | Theta: -$0.32/day
         Status: ✅ HEALTHY
   ```

3. **Calculate Today's Signals** (9:25 AM)
   ```bash
   python research/calculate_options_signals.py --symbols SPY,QQQ,IWM
   ```
   - Runs RSI calculation on latest daily close
   - Determines BUY/SELL/HOLD for each asset
   - Checks IV rank filter
   - Outputs recommended actions

### **Market Open (9:30 AM - 9:45 AM ET)**

4. **Execute Signals** (if any)
   ```bash
   # Paper trading (auto-executes)
   python main_options.py --mode paper --execute-morning-signals
   
   # Live trading (shows preview, requires confirmation)
   python main_options.py --mode live --execute-morning-signals --preview
   # Review output, then:
   python main_options.py --mode live --execute-morning-signals --confirm
   ```

5. **Monitor Execution**
   ```bash
   python research/verify_options_fills.py
   ```
   - Confirms orders filled
   - Checks fill price vs expected
   - Alerts if slippage >2%

### **Intraday (10:00 AM - 3:00 PM ET)**

6. **Passive Monitoring** (automated)
   - System logs position P&L every hour
   - Alerts sent if:
     - Position down >20% (check if need to close)
     - DTE < 7 (roll reminder)
     - Earnings announcement detected

### **Market Close (4:00 PM - 4:30 PM ET)**

7. **End-of-Day P&L Report**
   ```bash
   python research/generate_options_eod_report.py
   ```
   Output:
   ```
   ===== OPTIONS P&L REPORT (2026-01-15) =====
   
   Equity Balance: $95,432 (+$1,234 today)
   
   Open Positions:
   - SPY: 3 contracts | P&L: +$51 | Theta: -$0.96/day
   - QQQ: 2 contracts | P&L: -$14 | Theta: -$0.64/day
   
   Today's Trades: 0
   
   Week-to-Date: +$342 (+0.36%)
   Month-to-Date: +$1,892 (+2.01%)
   
   Status: ✅ All systems normal
   ```

8. **Check for Roll Requirements**
   ```bash
   python research/check_options_roll_needed.py
   ```
   - Lists positions with DTE < 7
   - Recommends roll parameters (new strike, new expiration)

### **Weekly Tasks (Friday 4:30 PM)**

9. **Weekly Performance Review**
   ```bash
   python research/generate_weekly_options_summary.py
   ```
   - Week's trades and P&L
   - Options vs equity performance comparison
   - Theta decay analysis
   - Recommendation: Continue/pause/adjust

10. **Regime Check**
    ```bash
    python research/check_market_regime.py
    ```
    - VIX level (if >30, reduce position sizes)
    - IV rank trending up/down
    - Upcoming earnings calendar for next week

---

## 🎛️ **PARAMETER TUNING**

### **When to Adjust Parameters**

| Scenario | Parameter to Adjust | New Value | Reason |
|----------|---------------------|-----------|--------|
| **Options consistently losing to equity** | `target_delta` | Increase to 0.70 | More ITM = less theta decay |
| **Frequent rolls eating profits** | `min_dte` | Increase to 60 | Longer DTE = fewer rolls |
| **Missing trades due to IV filter** | `max_iv_rank` | Increase to 80 | Accept slightly higher IV |
| **High VIX environment (>30)** | `max_position_size_contracts` | Reduce by 50% | Risk management |
| **Post-earnings success** | `earnings_blackout_days` | Reduce to 3 | Capture more opportunities |
| **Excessive slippage (>3%)** | `slippage_pct` | Increase to 2.0 | Model more conservative |

### **Parameter Optimization Workflow**

```bash
# 1. Run parameter sweep on historical data
python research/options_parameter_sweep.py \
    --symbol SPY \
    --delta-range 0.50,0.55,0.60,0.65,0.70 \
    --dte-range 30,45,60 \
    --iv-rank-max 60,70,80 \
    --output results/param_sweep_SPY_$(date +%Y%m%d).csv

# 2. Analyze results
python research/analyze_param_sweep.py \
    --input results/param_sweep_SPY_20260115.csv \
    --optimize-for sharpe_ratio

# 3. Update config with optimal params
# (Manual step: edit config/options/SPY.json)

# 4. Validate new params with out-of-sample backtest
python research/validate_new_params.py \
    --symbol SPY \
    --config config/options/SPY.json \
    --start-date 2025-01-01
```

---

## 📊 **MONITORING & ALERTS**

### **Key Metrics to Track**

**Daily**:
- Position P&L ($ and %)
- Theta decay ($/day)
- DTE for each position
- IV rank for underlying

**Weekly**:
- Options return vs equity return (should be 1.5-2x)
- Win rate (target: >55%)
- Average win vs average loss (target: >1.2:1)
- Sharpe ratio (target: >1.0)

**Monthly**:
- Total theta paid (should be <30% of gross gains)
- Roll frequency (target: <0.5 rolls per position)
- Slippage vs model (should be within 20%)

### **Alert Thresholds**

**Critical** (immediate action):
- 🔴 Position down >50% → Close immediately
- 🔴 DTE = 0 → Emergency roll or let expire ITM
- 🔴 API error on signal execution → Manual intervention

**Warning** (review within 1 day):
- 🟡 Position down 20-50% → Evaluate if thesis changed
- 🟡 Theta eaten >50% of initial premium → Consider closing
- 🟡 IV rank spike >80 → Don't enter new positions

**Info** (monitor):
- 🟢 DTE < 7 → Prepare to roll
- 🟢 Earnings in 7 days → Schedule position close
- 🟢 Win rate drops below 50% → Review strategy

### **Alert Delivery**

```bash
# Configure alerts (one-time setup)
python research/setup_options_alerts.py \
    --email your.email@example.com \
    --telegram-bot-token YOUR_TOKEN \
    --alert-level WARNING

# Test alert system
python research/test_options_alerts.py
```

---

## 🔧 **TROUBLESHOOTING**

### **Problem: "Options Trading Not Enabled"**

**Symptom**:
```
❌ ERROR: Options trading not enabled on this account!
   Options Approved Level: 0
```

**Solution**:
1. Log into Alpaca dashboard
2. Navigate to Account → Settings → Options Trading
3. Apply for options approval (Level 2 required)
4. Wait 1-2 business days for approval
5. Re-run `python research/options_api_test.py`

---

### **Problem: "No Options Contracts Found"**

**Symptom**:
```
❌ ERROR: No options contracts found for SPY (30-60 DTE)
```

**Solution**:
1. Check if requesting during market hours (9:30 AM - 4:00 PM ET)
2. Verify symbol is correct (`SPY`, not `$SPY` or `spy`)
3. Check DTE range is reasonable (30-60 days from today)
4. Try wider DTE range: `--min-dte 7 --max-dte 90`

---

### **Problem: "Excessive Slippage"**

**Symptom**:
```
⚠️  Filled at $1.55, expected $1.45 (slippage: 6.9%)
```

**Root Causes**:
- Illiquid strike (open interest <1000)
- Wide bid-ask spread (>5% of mid)
- Market volatility spike
- After-hours trading attempt

**Solutions**:
1. Stick to liquid strikes (within 5% of current price)
2. Use limit orders, not market orders
3. Only trade during market hours (avoid first/last 15 min)
4. Check open interest: `python research/check_option_liquidity.py --symbol SPY260221C00590000`

---

### **Problem: "Position Not Rolled"**

**Symptom**:
```
❌ ERROR: DTE = 0, position expired worthless
```

**Prevention**:
1. Enable auto-roll: `"auto_roll_enabled": true` in config
2. Set roll threshold >7 days for safety margin
3. Monitor DTE daily: `python research/check_options_roll_needed.py`
4. Set calendar reminders for expiration dates

**Recovery** (if too late):
- If ITM at expiration: Alpaca auto-exercises (you'll own shares)
- Sell shares immediately if don't want to hold
- If OTM at expiration: Position expires worthless (max loss = premium)

---

### **Problem: "Theta Decay Destroying Returns"**

**Symptom**:
```
Position down 40% despite SPY up 2% (theta ate all gains)
```

**Analysis**:
```bash
python research/analyze_theta_impact.py --position SPY260221C00590000
```

Output:
```
Theta Analysis:
- Days held: 15
- Theta decay: -$30/day × 15 = -$450 total
- Intrinsic gain: SPY up 2% = +$200
- Net P&L: -$250 ❌

Diagnosis: DTE too short (30 days), trend not strong enough
```

**Solutions**:
1. Increase min_dte to 60 (lower theta per day)
2. Increase target_delta to 0.70 (more intrinsic, less extrinsic)
3. Only trade when RSI momentum is very strong (>65 for calls)
4. Consider switching back to equity for this asset

---

## 📖 **ADDITIONAL RESOURCES**

**Internal Docs**:
- [Options Overview](OPTIONS_OVERVIEW.md) - What, why, how
- [Greeks Guide](GREEKS_GUIDE.md) - Delta, theta, IV explained
- [Risk Management](RISK_MANAGEMENT.md) - Position sizing, stops

**External Resources**:
- [Alpaca Options Docs](https://alpaca.markets/docs/trading/options/)
- [CBOE Options Institute](https://www.cboe.com/education/)
- [Options Playbook](https://www.optionsplaybook.com/)

---

## ✅ **PRE-FLIGHT CHECKLIST** (Before Going Live)

**Phase 4: Paper Trading**
- [ ] 4 weeks of error-free paper trading
- [ ] Options P&L matches backtest within 30%
- [ ] No missed rolls or expirations
- [ ] Alert system tested and working
- [ ] User comfortable with daily workflow

**Phase 5: Live Deployment**
- [ ] Start with $5K-$10K (10-20% of capital)
- [ ] SPY only for first month
- [ ] Max 1-2 contracts per trade
- [ ] Hard stop if lose >$500 in single trade
- [ ] Daily monitoring commitment confirmed

---

**STATUS**: 🚧 Document will be updated as system is built  
**NEXT UPDATE**: After Phase 1 completion (API testing)

---

**QUESTIONS? See [OPTIONS_OVERVIEW.md](OPTIONS_OVERVIEW.md) or [TROUBLESHOOTING.md](../operations/TROUBLESHOOTING.md)**
