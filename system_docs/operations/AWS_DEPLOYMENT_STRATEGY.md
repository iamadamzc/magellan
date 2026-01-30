# AWS Deployment Strategy - Alpaca Paper Trading Accounts

**Date:** 2026-01-20  
**Objective:** Deploy Magellan strategies to 3 Alpaca paper trading accounts on AWS  
**Target Launch:** 2026-01-21 (Tomorrow)  
**Total Capital Available:** $100,000

---

## Executive Summary

**RECOMMENDATION: Deploy 4 continuous strategies across 3 accounts, DEFER 2 event-based strategies**

### Account Allocation Strategy

| Account | Name | Strategies | Capital | Rationale |
|---------|------|------------|---------|-----------|
| **Account 1** | `magellan-intraday-momentum` | Bear Trap + Hourly Swing | $35,000 | High-frequency, intraday, complementary timeframes |
| **Account 2** | `magellan-daily-trend` | Daily Trend Hysteresis | $40,000 | End-of-day, low-frequency, largest allocation |
| **Account 3** | `magellan-futures-breakout` | GSB (Gas & Sugar) | $25,000 | Futures-only, commodity session, diversification |

**DEFERRED:** Earnings Straddles, FOMC Straddles (event-based, not optimal for 24/7 deployment)

---

## Strategy Analysis Matrix

### 1. **Bear Trap** (Small-Cap Reversal)
- **Type:** Continuous (Market Hours: 9:30-16:00 ET)
- **Timeframe:** Intraday (1-minute bars)
- **Frequency:** ~77 trades/month
- **Status:** ✅ **READY** (Validated 4-year, +135.6%)
- **Assets:** MULN, ONDS, AMC, NKLA, WKHS (5 symbols)
- **Operational Profile:**
  - Requires real-time 1-minute data
  - Trades concentrated in first 2 hours (9:30-11:30)
  - Fast execution critical (small-cap volatility)
  - Position holds: 5-30 minutes average

**Deployment Readiness:** ⭐⭐⭐⭐⭐ (5/5)
- ✅ Complete validation suite passed (7 pillars)
- ✅ Deployment checklist available
- ✅ Risk gates defined
- ✅ Production code ready

---

### 2. **Daily Trend Hysteresis** (RSI Daily Swing)
- **Type:** Continuous (End-of-Day Signals)
- **Timeframe:** Daily bars
- **Frequency:** ~8 trades/year per asset
- **Status:** ✅ **READY** (Validated 2025, +45.2% avg)
- **Assets:** GOOGL, GLD, META, AAPL, QQQ, SPY, MSFT, TSLA, AMZN, IWM (10 symbols)
- **Operational Profile:**
  - Signal generated at market close (16:00 ET)
  - Execution next day at open (9:30 ET)
  - Low-frequency (1 trade per asset every 6 weeks)
  - Position holds: Days to weeks

**Deployment Readiness:** ⭐⭐⭐⭐⭐ (5/5)
- ✅ 91% success rate (10/11 assets profitable)
- ✅ Simple logic (RSI 55/45 hysteresis)
- ✅ Validated on 2024-2025 data
- ✅ Config files ready

---

### 3. **Hourly Swing** (RSI Hourly)
- **Type:** Continuous (Market Hours)
- **Timeframe:** 1-hour bars
- **Frequency:** ~150 trades/year per asset
- **Status:** ✅ **READY** (Validated 2025, +112% avg)
- **Assets:** TSLA, NVDA (2 symbols)
- **Operational Profile:**
  - Signals every hour during market hours
  - Holds positions overnight (crucial for gaps)
  - Avg hold time: 41-63 hours (1-3 days)
  - Higher friction (5bps vs 1.5bps)

**Deployment Readiness:** ⭐⭐⭐⭐⭐ (5/5)
- ✅ 100% success rate (2/2 assets)
- ✅ Outperformed expectations (2-7x)
- ✅ Gap reversal validated
- ✅ Complementary to Daily Trend

---

### 4. **GSB (Gas & Sugar Breakout)** (Commodity Futures)
- **Type:** Continuous (Commodity Session: 13:30-21:30 ET)
- **Timeframe:** 1-minute bars (10-min OR)
- **Frequency:** ~126 trades/year (both symbols)
- **Status:** ✅ **READY** (Validated 4-year, +90.67%)
- **Assets:** Natural Gas (NG), Sugar (SB) futures
- **Operational Profile:**
  - Trades during commodity session (NOT equity hours)
  - Opening Range: First 10 minutes after 13:30 ET
  - Entry window: All-day (breakthrough discovery)
  - Requires accurate session time handling

**Deployment Readiness:** ⭐⭐⭐⭐½ (4.5/5)
- ✅ 4-year validation complete
- ✅ 75% profitable years (3/4)
- ⚠️ Requires commodity data feed setup
- ⚠️ Different session times than equities

---

### 5. **Earnings Straddles** (Options - Corporate Catalysts)
- **Type:** ⚠️ **EVENT-BASED** (Quarterly)
- **Timeframe:** T-2 entry, T+1 exit
- **Frequency:** ~28 events/year (7 symbols × 4 quarters)
- **Status:** ✅ VALIDATED (META +3.71%, PLTR +3.21%, AAPL +1.48%)
- **Assets:** META, PLTR, AAPL, NVDA, GOOGL, MSFT, AMZN, NFLX (options)
- **Operational Profile:**
  - Trades only during earnings weeks
  - Requires earnings calendar integration
  - Idle 90% of the time

**Deployment Readiness:** ⭐⭐⭐ (3/5) - **NOT OPTIMAL FOR NOW**
- ❌ Event-based (not continuous)
- ❌ Low frequency (seasonal)
- ❌ Requires options trading setup
- ⚠️ Better suited for Q2 2026 after continuous strategies stabilize

---

### 6. **FOMC Straddles** (Options - Macro Catalysts)
- **Type:** ⚠️ **EVENT-BASED** (8 events/year)
- **Timeframe:** T-5min entry, T+5min exit
- **Frequency:** 8 events/year
- **Status:** ⚠️ CONDITIONAL (QQQ +9.56%, SPY +3.81%)
- **Assets:** QQQ, SPY (options)
- **Operational Profile:**
  - Trades only during FOMC announcements
  - Requires economic calendar integration
  - Idle 99% of the time
  - High-precision timing required (5-minute window)

**Deployment Readiness:** ⭐⭐ (2/5) - **NOT OPTIMAL FOR NOW**
- ❌ Event-based (extreme seasonality)
- ❌ Ultra-low frequency (monthly at best)
- ❌ Requires FOMC calendar
- ⚠️ Consider after continuous strategies proven

---

## Recommended Deployment Plan

### 🎯 **ACCOUNT 1: Intraday Momentum** (PA3DDLQCBJSE - Already Exists)
**Alpaca Account:** PA3DDLQCBJSE  
**Capital:** $35,000  
**Leverage:** 4x available ($140,000 buying power)  
**Strategies:** Bear Trap + Hourly Swing

#### Strategy Mix
| Strategy | Symbols | Allocation | Max Position | Expected Trades/Mo |
|----------|---------|------------|--------------|-------------------|
| **Bear Trap** | MULN, ONDS, AMC, NKLA, WKHS | $25,000 | $12,500 | ~77 |
| **Hourly Swing** | TSLA, NVDA | $10,000 | $5,000 | ~25 |

#### Rationale
- ✅ **Complementary timeframes:** Intraday (5-30 min) + Hourly swing (1-3 days)
- ✅ **Different asset classes:** Small-caps + Large-cap tech
- ✅ **No overlap:** Bear Trap targets different price action than Hourly Swing
- ✅ **Diversified risk:** Small-cap reversals vs tech momentum
- ✅ **Shared infrastructure:** Both need 1-minute data, market hours monitoring

#### Operational Requirements
- **Data:** 1-minute bars for 7 symbols (5 small-caps + TSLA + NVDA)
- **Hours:** 9:30-16:00 ET (US market hours)
- **Monitoring:** Real-time position tracking, stop-loss execution
- **Risk Gates:**
  - Daily loss limit: $3,500 (10% of account)
  - Max position size: $12,500 (Bear Trap), $5,000 (Hourly Swing)

---

### 🎯 **ACCOUNT 2: Daily Trend** (NEW - To Be Created)
**Alpaca Account:** `magellan-daily-trend` (NEW)  
**Capital:** $40,000  
**Leverage:** 4x available ($160,000 buying power)  
**Strategy:** Daily Trend Hysteresis ONLY

#### Strategy Configuration
| Strategy | Symbols | Allocation | Max Position | Expected Trades/Mo |
|----------|---------|------------|--------------|-------------------|
| **Daily Trend** | GOOGL, GLD, META, AAPL, QQQ, SPY, MSFT, TSLA, AMZN, IWM | $40,000 | $10,000/asset | ~7 total |

#### Rationale
- ✅ **Largest allocation:** Most stable, lowest frequency, highest Sharpe (1.05 avg)
- ✅ **Isolated strategy:** No conflicts with other strategies
- ✅ **Simple execution:** 1 signal per day, execute at next open
- ✅ **Diversified portfolio:** 10 uncorrelated assets
- ✅ **Low maintenance:** Run once daily after market close

#### Operational Requirements
- **Data:** Daily bars (end-of-day downloads acceptable)
- **Hours:** Signal calculation at 16:05 ET, execution at 9:30 ET next day
- **Monitoring:** Once daily check, minimal real-time monitoring
- **Risk Gates:**
  - Daily loss limit: $4,000 (10% of account)
  - Max position per asset: $10,000

---

### 🎯 **ACCOUNT 3: Futures Breakout** (NEW - To Be Created)
**Alpaca Account:** `magellan-futures-breakout` (NEW)  
**Capital:** $25,000  
**Leverage:** 4x available ($100,000 buying power)  
**Strategy:** GSB (Gas & Sugar Breakout) ONLY

#### Strategy Configuration
| Strategy | Symbols | Allocation | Max Position | Expected Trades/Mo |
|----------|---------|------------|--------------|-------------------|
| **GSB** | Natural Gas (NG), Sugar (SB) | $25,000 | $12,500/contract | ~10 total |

#### Rationale
- ✅ **Futures isolation:** Separate account for futures (different margin, settlement)
- ✅ **Diversification:** Commodities (energy + agriculture)
- ✅ **Different hours:** Commodity session (13:30-21:30 ET) doesn't conflict with equities
- ✅ **Proven edge:** 75% profitable years, +90.67% over 4 years
- ✅ **Uncorrelated returns:** Commodities vs equities

#### Operational Requirements
- **Data:** 1-minute bars for NG, SB futures
- **Hours:** 13:30-21:30 ET (commodity session)
- **Monitoring:** Session-specific (different from equity hours)
- **Risk Gates:**
  - Daily loss limit: $2,500 (10% of account)
  - Max position per contract: $12,500

---

## Capital Allocation Summary

| Account | Strategy | Initial Capital | 4x Margin BP | % of Total |
|---------|----------|----------------|--------------|------------|
| **Account 1** | Bear Trap + Hourly Swing | $35,000 | $140,000 | 35% |
| **Account 2** | Daily Trend | $40,000 | $160,000 | 40% |
| **Account 3** | GSB Futures | $25,000 | $100,000 | 25% |
| **TOTAL** | | **$100,000** | **$400,000** | 100% |

### Allocation Rationale

**Why 40% to Daily Trend?**
- Lowest risk (1.05 Sharpe, -6% to -40% max DD range)
- Most stable returns (+45.2% avg, 91% success rate)
- Largest diversification (10 assets)
- Lowest frequency (fewer execution risks)

**Why 35% to Intraday Momentum?**
- Higher risk/reward (Bear Trap +135.6%, Hourly Swing +112%)
- More execution risk (intraday, fast-moving)
- Smaller opportunity set (7 total assets)

**Why 25% to GSB Futures?**
- Different asset class (commodities)
- Higher volatility (NG/SB can gap significantly)
- Smaller sample size (2 assets, 4-year validation)
- Learning curve (commodity session handling)

---

## Deferred Strategies

### ❌ **Earnings Straddles** - Deferred to Q2 2026
**Reason:** Event-based, seasonal, requires options setup

**Deployment Timeline:**
1. **Q1 2026 (Now):** Deploy continuous strategies, validate execution
2. **Q2 2026 (Apr-Jun):** Add earnings straddles if continuous strategies stable
3. **Required Before Deployment:**
   - Options trading enabled on Alpaca
   - Earnings calendar integration
   - Options pricing/Greeks calculation
   - IV spike validation

### ❌ **FOMC Straddles** - Deferred to Q3 2026
**Reason:** Ultra-low frequency (8 events/year), high precision required

**Deployment Timeline:**
1. **Q1-Q2 2026:** Validate continuous strategies
2. **Q3 2026:** Add FOMC if event-based infrastructure exists
3. **Required Before Deployment:**
   - Options trading enabled
   - Economic calendar integration
   - High-precision timing (5-minute window)
   - FOMC announcement schedule tracking

---

## AWS Account Setup Tasks

### ✅ **Account 1: PA3DDLQCBJSE** (Already Exists)
**Status:** Ready  
**Strategies:** Bear Trap + Hourly Swing  
**Capital:** Transfer $35,000

**Setup Tasks:**
- [x] Account created
- [ ] Fund with $35,000
- [ ] Verify 4x margin enabled
- [ ] Create AWS SSM parameters:
  - `/magellan/alpaca/PA3DDLQCBJSE/API_KEY`
  - `/magellan/alpaca/PA3DDLQCBJSE/API_SECRET`
- [ ] Deploy strategy configs to EC2
- [ ] Test data feed connectivity
- [ ] Run paper trading validation (2 weeks)

---

### 🆕 **Account 2: [NEW]** - Daily Trend
**Name Recommendation:** `magellan-daily-trend`  
**Alpaca Account Name:** (You assign after creation)  
**Strategies:** Daily Trend Hysteresis  
**Capital:** $40,000

**Setup Tasks:**
- [ ] Create new Alpaca paper trading account
- [ ] Record account number: `____________`
- [ ] Fund with $40,000
- [ ] Enable 4x margin
- [ ] Create AWS SSM parameters:
  - `/magellan/alpaca/ACCOUNT_ID/API_KEY`
  - `/magellan/alpaca/ACCOUNT_ID/API_SECRET`
- [ ] Deploy strategy config
- [ ] Schedule daily signal generation (16:05 ET cron job)
- [ ] Test execution at next open

---

### 🆕 **Account 3: [NEW]** - Futures Breakout
**Name Recommendation:** `magellan-futures-breakout`  
**Alpaca Account Name:** (You assign after creation)  
**Strategy:** GSB (Gas & Sugar Breakout)  
**Capital:** $25,000

**Setup Tasks:**
- [ ] Create new Alpaca paper trading account
- [ ] Record account number: `____________`
- [ ] Enable **futures trading** on account
- [ ] Fund with $25,000
- [ ] Verify commodity data feed (NG, SB)
- [ ] Create AWS SSM parameters:
  - `/magellan/alpaca/ACCOUNT_ID/API_KEY`
  - `/magellan/alpaca/ACCOUNT_ID/API_SECRET`
- [ ] Deploy GSB strategy
- [ ] Verify session times (NG: 13:29 ET, SB: 13:30 ET)
- [ ] Test opening range calculation

---

## EC2 Deployment Architecture

### Process Architecture (3 Strategies, 3 Processes)

```
EC2 Instance (i-0cd785630b55dd9a2)
├── Process 1: Bear Trap + Hourly Swing (Account PA3DDLQCBJSE)
│   ├── Hours: 9:30-16:00 ET
│   ├── Data: 1-min bars (MULN, ONDS, AMC, NKLA, WKHS, TSLA, NVDA)
│   └── Monitoring: Real-time position/risk tracking
│
├── Process 2: Daily Trend (Account TBD)
│   ├── Hours: 16:05 ET (signal), 9:30 ET (execution)
│   ├── Data: Daily bars (10 symbols)
│   └── Monitoring: Once daily
│
└── Process 3: GSB Futures (Account TBD)
    ├── Hours: 13:30-21:30 ET
    ├── Data: 1-min bars (NG, SB)
    └── Monitoring: Commodity session hours
```

### Systemd Service Configuration

Each strategy will run as a separate systemd service with auto-restart:

**Service 1:** `magellan-intraday.service`  
**Service 2:** `magellan-daily.service`  
**Service 3:** `magellan-futures.service`

Each service:
- Auto-starts on EC2 boot
- Restarts on failure
- Logs to CloudWatch
- Reads credentials from SSM Parameter Store
- Runs in isolated Python venv

---

## Risk Management Framework

### Account-Level Risk Gates

| Risk Gate | Account 1 | Account 2 | Account 3 |
|-----------|-----------|-----------|-----------|
| **Daily Loss Limit** | $3,500 (10%) | $4,000 (10%) | $2,500 (10%) |
| **Max Position Size** | $12,500 | $10,000 | $12,500 |
| **Max Open Positions** | 5 (Bear) + 2 (Hourly) | 10 | 2 |
| **Stop Trading If:** | 3 losing days | 3 losing days | 3 losing days |

### Portfolio-Level Risk Gates

**HALT ALL TRADING IF:**
- Total portfolio loss exceeds $10,000 in 1 day (10% of total capital)
- Total portfolio drawdown exceeds 20% ($20,000)
- 3 consecutive losing weeks across all accounts
- Data feed issues or system failures

### Emergency Procedures

**Manual Intervention Required:**
- Close all positions at market
- Disable systemd services
- Alert via CloudWatch alarm
- Document incident
- Root cause analysis before restart

---

## Deployment Timeline (7-Day Plan)

### **Day 1 (Tomorrow - Jan 21, 2026): Setup**
- [ ] Create 2 new Alpaca paper accounts
- [ ] Record account numbers
- [ ] Fund all 3 accounts ($35k, $40k, $25k)
- [ ] Store API keys in AWS SSM Parameter Store
- [ ] Verify margin and futures permissions

### **Day 2 (Jan 22): Infrastructure**
- [ ] Deploy strategy code to EC2 (`/home/ec2-user/magellan`)
- [ ] Create 3 systemd service files
- [ ] Configure CloudWatch log groups
- [ ] Test SSM parameter retrieval
- [ ] Verify Python venv and dependencies

### **Day 3 (Jan 23): Data Validation**
- [ ] Test Alpaca data feed for all symbols
- [ ] Verify 1-minute bars (Bear Trap, Hourly Swing, GSB)
- [ ] Verify daily bars (Daily Trend)
- [ ] Test commodity session times (NG: 13:29, SB: 13:30)
- [ ] Cache historical data for RSI warmup

### **Day 4 (Jan 24): Strategy Testing**
- [ ] Test Bear Trap signal generation (dry run)
- [ ] Test Hourly Swing signal generation
- [ ] Test Daily Trend signal at close
- [ ] Test GSB opening range calculation
- [ ] Verify order submission (paper trading)

### **Day 5 (Jan 25): Integration Testing**
- [ ] Run all 3 strategies in parallel
- [ ] Monitor for conflicts or resource issues
- [ ] Test emergency stop procedures
- [ ] Verify CloudWatch logging
- [ ] Check position tracking accuracy

### **Day 6-7 (Jan 26-27): Monitoring & Adjustment**
- [ ] Monitor first weekend data feeds
- [ ] Observe Monday market open (first live signals)
- [ ] Track execution quality vs backtest
- [ ] Measure slippage and friction
- [ ] Document any issues

### **Week 2+ (Jan 28+): Paper Trading Phase**
- [ ] Continue paper trading for 2 weeks minimum
- [ ] Daily P&L review
- [ ] Compare results to backtest expectations
- [ ] Identify and fix any execution gaps
- [ ] Prepare for live deployment decision

---

## Success Metrics (2-Week Paper Trading)

### Bear Trap + Hourly Swing (Account 1)
- **Target:** Win rate > 40% (Bear Trap), > 35% (Hourly Swing)
- **Target:** Positive P&L or small loss acceptable
- **Critical:** Execution slippage < 1% on small-caps
- **Critical:** No data feed gaps or missed signals

### Daily Trend (Account 2)
- **Target:** Signal parity with backtest (same entries/exits)
- **Target:** Execution within 0.5% of target price
- **Critical:** Daily signal generation at 16:05 ET without fail
- **Critical:** Correct position tracking (especially overnight holds)

### GSB Futures (Account 3)
- **Target:** Correct opening range calculation every day
- **Target:** Entry signals match backtest logic
- **Critical:** Session times accurate (13:29/13:30 ET)
- **Critical:** Futures data feed reliable

### Portfolio-Level
- **Target:** No system failures or crashes
- **Target:** All 3 processes running 24/7 (auto-restart working)
- **Target:** CloudWatch logs capturing all trades
- **Critical:** Risk gates triggering correctly

---

## Decision Points

### After 2 Weeks (Feb 4, 2026)
**Review Results and Decide:**
1. ✅ **Green Light:** If all metrics met → Scale to live trading
2. ⚠️ **Yellow Light:** If minor issues → Extend paper trading, fix issues
3. 🛑 **Red Light:** If major discrepancies → Halt, root cause analysis

### After 1 Month (Feb 21, 2026)
**Portfolio Review:**
- Compare live results to 4-year backtest expectations
- Assess capital allocation (rebalance if needed)
- Consider adding Tier 2 symbols (Bear Trap: ACB, BTCS, SENS)
- Evaluate readiness for event-based strategies (Earnings, FOMC)

### After 3 Months (Apr 21, 2026)
**Strategic Assessment:**
- Full performance analysis across all strategies
- Decide on Earnings Straddles deployment
- Assess need for additional accounts or capital
- Review AWS infrastructure costs and optimization

---

## Questions to Resolve Before Proceeding

### Immediate (Answer Now)
1. ✅ **Alpaca Account Creation:** Shall I proceed with creating 2 new paper accounts, or will you create them manually?
2. ✅ **Account Naming:** Confirm account names: `magellan-daily-trend` and `magellan-futures-breakout`?
3. ✅ **Capital Allocation:** Agree with $35k/$40k/$25k split, or prefer different allocation?
4. ✅ **Futures Trading:** Is futures trading enabled on Alpaca for paper accounts?

### Pre-Deployment (This Week)
5. **Data Feed:** Confirm Alpaca provides 1-minute historical data for all symbols (including NG, SB futures)?
6. **Options:** Defer earnings/FOMC strategies, or set them up now (inactive)?
7. **Monitoring:** Do you want SMS/email alerts for trades, or CloudWatch only?
8. **Backup:** Should we set up a backup EC2 instance for failover?

---

## Implementation Files Needed

I can create the following deployment files once you confirm the strategy:

### Configuration Files
1. `deployment_configs/account_1_intraday.json` - Bear Trap + Hourly Swing config
2. `deployment_configs/account_2_daily.json` - Daily Trend config
3. `deployment_configs/account_3_futures.json` - GSB config

### Systemd Services
4. `magellan-intraday.service` - Account 1 service
5. `magellan-daily.service` - Account 2 service
6. `magellan-futures.service` - Account 3 service

### Deployment Scripts
7. `scripts/deploy_to_ec2.sh` - Automated deployment script
8. `scripts/setup_systemd.sh` - Service installation script
9. `scripts/verify_deployment.py` - Health check script

### Monitoring
10. `scripts/monitor_accounts.py` - Real-time P&L tracking
11. `scripts/daily_report.py` - End-of-day summary generator

---

## Next Steps

**Immediate Action Items:**
1. **Review this document** and confirm strategy allocation
2. **Create 2 new Alpaca paper accounts** (or confirm you'll do it)
3. **Provide account numbers** for Account 2 and Account 3
4. **Confirm capital allocation** ($35k/$40k/$25k)
5. **Verify futures trading** is available on Alpaca paper accounts

**Once Confirmed:**
- I'll create all configuration files
- I'll write deployment scripts for EC2
- I'll create systemd service files
- I'll prepare the 7-day deployment timeline with exact commands

---

**Ready to proceed?** Let me know your decisions on the questions above, and I'll start building the deployment infrastructure.
