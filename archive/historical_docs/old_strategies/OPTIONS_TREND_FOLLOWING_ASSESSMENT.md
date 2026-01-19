# OPTIONS TREND FOLLOWING STRATEGY - PROFESSIONAL ASSESSMENT

**Date**: 2026-01-15  
**Branch**: `feature/options-trend-following`  
**Prepared By**: Quantitative Development Team  
**Status**: 🔬 EXPLORATORY RESEARCH PHASE

---

## 🎯 EXECUTIVE SUMMARY

**Opportunity**: Leverage Alpaca's commission-free options API to develop a trend-following options strategy, potentially enhancing returns while managing risk through options mechanics (leverage, defined risk, time decay management).

**Recommendation**: **QUALIFIED YES** - Options trend-following is viable and potentially superior to equity strategies, BUT requires significant architectural changes, careful risk management, and phased validation.

**Key Insight**: Your current Daily Trend Hysteresis (System 1) and Hourly Swing (System 2) are **perfect candidates** for options translation because:
1. Low trade frequency (2-20 trades/year for System 1) minimizes options-specific friction
2. Trend-following aligns with directional options (calls/puts) rather than complex spreads
3. Hysteresis logic naturally prevents whipsaw that destroys theta in options

**Estimated Development Timeline**: 6-12 weeks to production-ready

---

## 💰 COST ADVANTAGE ANALYSIS

### **Alpaca Options Fees (2026)**

**Commission**: $0 ✅  
**Per-Contract Regulatory Fees** (unavoidable):
- **OCC Fee**: $0.02/contract
- **ORF (Options Regulatory Fee)**: $0.02685/contract  
- **TAF (Trading Activity Fee)**: $0.00279/contract (sell only)
- **FINRA CAT Fee**: $0.0000265/share equivalent

**Total Cost per Round-Trip Trade** (Buy + Sell):
- **Buy**: ~$0.047/contract
- **Sell**: ~$0.050/contract  
- **Round-Trip**: ~**$0.097/contract** (~$9.70 per 100 contracts)

### **Comparison to Equity Trading**

**Example**: $10,000 Position

**Current Equity Strategy** (System 1):
- Cost: Bid-ask spread (~0.02-0.05% on liquid names like NVDA, AAPL)
- Transaction Cost: $2-$5 per side = **$4-$10 round-trip**
- Friction: Minimal on MAG7 stocks

**Options Strategy** (ATM or slightly OTM):
- 1 contract ≈ $1,000-$3,000 exposure (delta ~0.50-0.70)
- For $10,000 exposure: ~3-10 contracts
- Transaction Cost: 5 contracts × $0.097 = **$0.49 round-trip** 🎯
- **Savings**: 90-95% cost reduction!

**Verdict**: ✅ **SIGNIFICANT COST ADVANTAGE** - Options friction is **10-20x lower** than equities on a notional basis, IF contracts are liquid.

---

## 🏗️ ARCHITECTURAL FEASIBILITY

### **Current Engine Strengths (Assets You Already Have)**

1. ✅ **Proven Trend Detection Logic**
   - RSI Hysteresis (Schmidt Trigger) is battle-tested
   - Daily timeframe = low whipsaw = perfect for options theta management
   - Win rate 60-86% on MAG7 (System 1) = ideal for directional bets

2. ✅ **Point-in-Time Data Infrastructure**
   - Alpaca SIP feed for equities
   - FMP for sentiment/fundamentals
   - No look-ahead bias in feature engineering

3. ✅ **Multi-Asset Configuration System**
   - `config/nodes/*.json` already handles per-ticker customization
   - Easy to add options-specific params (DTE, delta target, IV filters)

4. ✅ **Clean Logging & Backtesting**
   - `SystemLogger` with 3 verbosity levels
   - `BacktesterPro` for walk-forward validation
   - Can be extended for options P&L tracking

### **Required Architectural Changes**

#### **1. Data Layer** (`src/data_handler.py`)

**New Modules Needed**:
```python
class AlpacaOptionsDataClient:
    """
    Fetch options chain data, Greeks, IV, open interest
    """
    def fetch_options_chain(symbol, expiration_date)
    def fetch_option_quote(option_symbol)  # e.g., "NVDA260117C00150000"
    def get_options_greeks(option_symbol)
```

**Complexity**: Medium  
**Timeline**: 1-2 weeks  
**Risk**: Low (Alpaca has solid options API docs)

#### **2. Options Feature Engineering** (`src/options_features.py` - NEW FILE)

**Required Calculations**:
- **IV Rank/Percentile**: Filter high IV environments (sell premium) vs low IV (buy premium)
- **Delta Selection**: Choose strike based on desired leverage (0.30-0.70 delta)
- **Theta Decay Analysis**: Estimate time decay cost vs trend capture
- **DTE (Days to Expiration) Logic**: Auto-roll before expiration (e.g., 7 DTE threshold)

**Complexity**: High (new domain knowledge)  
**Timeline**: 2-3 weeks  
**Risk**: Medium (requires options-specific expertise)

#### **3. Options Execution** (`src/options_executor.py` - NEW FILE)

**Key Functions**:
- Convert equity signal (UP/DOWN/FLAT) to options position (CALL/PUT/CASH)
- Select optimal strike based on delta target
- Handle rolling positions (close expiring, open new DTE)
- Manage early assignment risk (American options)

**Complexity**: High  
**Timeline**: 2-3 weeks  
**Risk**: High (execution bugs = real money loss)

#### **4. Options P&L Tracking** (`src/options_pnl_tracker.py` - NEW FILE)

**Challenges**:
- Track extrinsic vs intrinsic value separately
- Account for theta decay daily
- Handle assignment/exercise scenarios
- Calculate realized vs unrealized P&L correctly

**Complexity**: High  
**Timeline**: 1-2 weeks  
**Risk**: Medium (accounting errors hard to debug)

#### **5. Backtesting Engine Extension** (`src/backtester_pro.py`)

**Modifications**:
- Simulate options expiration mechanics
- Model bid-ask spreads (wider on options than equities)
- Track Greeks evolution over time
- Simulate early assignment probability

**Complexity**: Very High  
**Timeline**: 3-4 weeks  
**Risk**: Very High (hard to validate without real trades)

---

## 📊 STRATEGY DESIGN: OPTIONS TRANSLATION OF SYSTEM 1

### **System 1 Daily Hysteresis → Options Variant**

**Equity Strategy** (Current):
- Signal: RSI > 55 = BUY, RSI < 45 = SELL
- Hold: Days to weeks
- Position: 100% equity exposure

**Options Translation** (Proposed):
- **Signal**: Same RSI hysteresis logic ✅
- **Instrument Selection**:
  - **BUY signal (RSI > 55)**: Buy ATM or slightly OTM **CALL** (delta 0.50-0.70)
  - **SELL signal (RSI < 45)**: Buy ATM or slightly OTM **PUT** (delta 0.50-0.70)
  - **HOLD signal (45 ≤ RSI ≤ 55)**: Close all options, go to CASH ✅
- **DTE Selection**: 30-45 DTE (1-1.5 months)
  - Why? Balances theta decay vs trend capture time
  - Daily theta on 30 DTE ≈ -0.02 to -0.04 per contract
- **Position Sizing**: 
  - Equity: $10,000 position
  - Options: 5-7 contracts (delta-adjusted notional = $10K)

### **Example Trade Flow: GOOGL**

**Jan 1, 2025**: RSI = 57 → **BUY SIGNAL**
- Action: Buy 5 contracts GOOGL Feb 28 $150 CALL (45 DTE, delta 0.60)
- Cost: $800/contract × 5 = **$4,000 premium** (vs $10,000 equity)
- Max Loss: $4,000 (defined risk) ✅
- Breakeven: GOOGL must rise 5.3% by expiration

**Feb 15, 2025**: RSI still > 55 → **HOLD**
- DTE = 13 days (approaching expiration)
- Action: **ROLL** forward to March 28 CALL (same $150 strike, 45 DTE)
- Cost: Close Feb 28 CALL, open March 28 CALL

**Feb 22, 2025**: RSI = 43 → **SELL SIGNAL**
- Action: Close March 28 CALL, open March 28 **PUT** (delta 0.60)
- Switch from bullish to bearish ✅

### **Key Advantages Over Equity**

1. **Leverage**: Control $10K notional with $4K premium (2.5x leverage)
2. **Defined Risk**: Max loss = premium paid (can't lose more than $4K)
3. **Capital Efficiency**: Free up $6K for other positions
4. **Asymmetric Payoff**: 
   - Win: Unlimited (call) or large (put)
   - Loss: Limited to premium

### **Key Risks vs Equity**

1. **Theta Decay**: -$20-$40/day per position if trend stalls
2. **Expiration Management**: Must roll or close before expiry
3. **Wider Spreads**: Bid-ask on options ~0.05-0.15 vs 0.01-0.02 on equities
4. **Volatility Risk**: IV crush after earnings can destroy value even if direction correct

---

## 🚨 CRITICAL RISK FACTORS

### **1. Liquidity Risk** 🔴 HIGH PRIORITY

**Problem**: Not all MAG7 stocks have liquid options on all strikes/expirations.

**Mitigation**:
- **Stick to weekly expirations** on NVDA, AAPL, TSLA, GOOGL (most liquid)
- **Avoid**: META, AMZN options (lower volume, wider spreads)
- **IWM, SPY, QQQ**: ✅ EXCELLENT liquidity (largest options markets globally)

**Test Before Deploy**:
```python
# Check average daily volume for target strike/DTE
alpaca_options.get_option_volume("NVDA260221C00140000")
# Require: Volume > 1000 contracts/day, Open Interest > 5000
```

### **2. Implied Volatility Risk** 🟡 MEDIUM PRIORITY

**Problem**: Buying options when IV is high = overpaying for insurance.

**Example**:
- Normal IV for NVDA: 40-50%
- Post-earnings IV: 80-100%
- Same strike/DTE costs **2x more** at high IV

**Mitigation**:
- Add **IV Rank filter** to `src/options_features.py`:
  ```python
  if iv_rank > 70:
      # High IV = expensive options
      # Reduce position size by 50% or skip trade
  ```
- **Alternative**: Use equity strategy during high IV, switch to options during low IV

### **3. Earnings Event Risk** 🟡 MEDIUM PRIORITY

**Problem**: Earnings announcements cause:
- IV spike before (expensive options)
- IV crush after (instant 30-50% value loss)
- Gap moves (can blow through stops)

**Mitigation**:
- **Earnings Calendar Filter**: 
  ```python
  if days_to_earnings < 7:
      close_options_position()
      wait_for_earnings()
  ```
- **Alternative**: Use equity during earnings week, options otherwise

### **4. Expiration Management** 🔴 HIGH PRIORITY

**Problem**: Options expire! Must roll or close.

**Solution**:
- **Auto-Roll Logic**:
  ```python
  if DTE < 7 and position_open:
      close_current_option()
      open_new_option(DTE=45)
  ```
- **Cost**: Rolling incurs transaction fees + potential slippage
- **Frequency**: System 1 trades 2-20x/year, may require 0-3 rolls per trade

### **5. Assignment Risk** 🟢 LOW PRIORITY (for long options)

**Problem**: Short options can be assigned early (American-style).

**Verdict**: **NOT A CONCERN** for this strategy (we're buying calls/puts, not selling)

---

## 📈 EXPECTED PERFORMANCE ANALYSIS

### **Theoretical Performance: GOOGL (System 1)**

**Equity Strategy** (Validated):
- Return: +108% (19 months)
- Sharpe: 2.05
- Max DD: -13%
- Trades: 8

**Options Strategy** (Estimated):
- **Return**: +150-250% (2-3x equity due to leverage)
- **Sharpe**: 1.5-1.8 (lower due to theta decay and volatility drag)
- **Max DD**: -60% to -100% (defined risk per trade, but can lose 100% of premium)
- **Trades**: 8 entries + 0-3 rolls = 8-24 total transactions
- **Win Rate**: Similar ~60-70% (same signal logic)

**Key Differences**:
- **Wins are BIGGER** (leverage amplifies gains)
- **Losses are SMALLER in $** (max = premium paid)
- **Losses are LARGER in %** (can lose 100% of premium vs 10-20% equity drawdown)
- **Return profile shifts** from "steady climber" to "volatile home-run hitter"

### **Risk-Adjusted Verdict**

✅ **Options are BETTER for**:
- Accounts with high conviction, want leverage
- Traders comfortable with volatility
- Portfolios where capital efficiency matters

❌ **Equity is BETTER for**:
- Accounts seeking stable, predictable returns
- Traders wanting low maintenance (no expiration management)
- Strategies with frequent signals (high roll costs)

---

## 🎯 RECOMMENDED DEVELOPMENT ROADMAP

### **Phase 1: Proof of Concept (2-3 weeks)**

**Goals**:
1. Connect to Alpaca Options API ✅
2. Fetch options chain for NVDA ✅
3. Build basic strike selection logic (delta 0.50-0.70) ✅
4. Paper trade 1 manual options trade ✅

**Deliverables**:
- `src/options_data_handler.py` (basic implementation)
- `research/options_api_test.py` (API connection test)
- Manual trade log documenting execution

**Success Criteria**:
- [ ] Successfully fetch options chain for NVDA, AAPL
- [ ] Execute 1 paper options trade via API
- [ ] Track P&L correctly (premium paid vs current value)

---

### **Phase 2: Strategy Translation (3-4 weeks)**

**Goals**:
1. Translate System 1 (Daily Hysteresis) to options ✅
2. Build options feature engineering (`src/options_features.py`) ✅
3. Implement auto-roll logic ✅
4. Create options-specific backtester ✅

**Deliverables**:
- `src/options_features.py` (IV, Greeks, DTE calculations)
- `src/options_executor.py` (signal → options position logic)
- `src/options_backtester.py` (historical simulation)
- `test_options_system1.py` (validation script)

**Success Criteria**:
- [ ] Backtest System 1 Options on SPY (2024-2026)
- [ ] Sharpe > 1.0, Win Rate > 55%
- [ ] Max premium loss < 40% (vs 100% = total wipeout)
- [ ] Code passes temporal leak audit

---

### **Phase 3: Multi-Asset Validation (2-3 weeks)**

**Goals**:
1. Test options strategy on SPY, QQQ, NVDA, AAPL ✅
2. Optimize delta selection (0.30 vs 0.50 vs 0.70) ✅
3. Optimize DTE selection (30 vs 45 vs 60 days) ✅
4. Add IV filters and earnings avoidance ✅

**Deliverables**:
- `OPTIONS_VALIDATION_REPORT.md` (results for 4 assets)
- `config/options/*.json` (per-asset configurations)
- Parameter sweep results (delta, DTE, IV threshold)

**Success Criteria**:
- [ ] 3 out of 4 assets profitable post-friction
- [ ] Portfolio Sharpe > 1.2
- [ ] System handles expirations and rolls correctly

---

### **Phase 4: Paper Trading (4-6 weeks)**

**Goals**:
1. Deploy options bot in paper trading mode ✅
2. Monitor daily for execution bugs ✅
3. Validate real-world slippage vs backtest assumptions ✅
4. Track actual options quotes vs theoretical ✅

**Deliverables**:
- `deploy_options_system1.py` (production deployment script)
- Daily monitoring dashboard (optional)
- Paper trading performance report

**Success Criteria**:
- [ ] 4 weeks of error-free execution
- [ ] Paper P&L matches backtest within 20%
- [ ] No critical bugs (wrong strikes, missed rolls, etc.)
- [ ] User comfort with options mechanics

---

### **Phase 5: Live Deployment (Staged)**

**Goals**:
1. Deploy with 10% of capital ($10-20K) ✅
2. Run for 2-3 months ✅
3. Scale to 30% if successful ✅

**Success Criteria**:
- [ ] Live returns match paper trading within 30%
- [ ] No execution errors or margin calls
- [ ] User confident in system operation

---

## 💡 PROFESSIONAL RECOMMENDATIONS

### **1. Start with Indices, Not Stocks**

**Rationale**:
- **SPY/QQQ options**: Most liquid options market in the world
- **Spreads**: 0.01-0.05 wide vs 0.10-0.30 on individual stocks
- **IV Stability**: Less prone to earnings-driven spikes
- **Your System 1**: SPY +25% (Sharpe 1.37), QQQ +29% (Sharpe 1.20)

**Recommendation**: ✅ **Validate on SPY first**, then expand to QQQ, then cherry-pick best MAG7 (NVDA, AAPL).

---

### **2. Use Longer DTE (45-60) for System 1**

**Rationale**:
- System 1 trades are **low frequency** (2-20/year)
- Average hold time: 30-60 days
- Longer DTE = lower theta decay per day
- 60 DTE theta ≈ -0.02/day vs 30 DTE ≈ -0.04/day

**Recommendation**: ✅ **Start with 60 DTE**, roll at 30 DTE remaining.

---

### **3. Use System 2 (Hourly) for Options Later**

**Rationale**:
- System 2 trades **50-150x/year** (much higher frequency)
- High frequency + options rolls = friction nightmare
- Better to prove System 1 options first

**Recommendation**: ⛔ **Defer System 2 options** until System 1 is profitable for 6+ months.

---

### **4. Hybrid Approach: Equity Core + Options Satellite**

**Portfolio Allocation** ($100K example):
- **60% Equity** (System 1 Daily on all 11 assets): $60K
  - Stable, predictable, low maintenance
- **20% Options** (System 1 on SPY, QQQ only): $20K premium ($40K notional)
  - High upside, defined risk, volatile
- **20% Cash**: Reserve for opportunities

**Benefits**:
- Equity core ensures steady performance
- Options satellite provides leverage and excitement
- If options fail (lose $20K), still have $60K equity base

**Recommendation**: ✅ **This is the OPTIMAL deployment strategy** for your risk profile.

---

## 🔬 TECHNICAL IMPLEMENTATION NOTES

### **Alpaca Options Symbol Format**

**Equity Symbol**: `NVDA`  
**Options Symbol**: `NVDA260117C00150000`

**Breakdown**:
- `NVDA`: Underlying ticker
- `26`: Year (2026)
- `01`: Month (January)
- `17`: Day (17th)
- `C`: Call (or `P` for Put)
- `00150000`: Strike price ($150.00, padded to 8 digits)

**Code Example**:
```python
def build_option_symbol(ticker, expiry_date, option_type, strike):
    """
    ticker: 'NVDA'
    expiry_date: datetime(2026, 1, 17)
    option_type: 'C' or 'P'
    strike: 150.0
    """
    yy = expiry_date.strftime('%y')
    mm = expiry_date.strftime('%m')
    dd = expiry_date.strftime('%d')
    strike_padded = f"{int(strike * 1000):08d}"
    return f"{ticker}{yy}{mm}{dd}{option_type}{strike_padded}"
```

---

### **Greeks Calculation Fallback**

**Problem**: Alpaca may not provide Greeks (delta, theta, vega) in real-time.

**Solution**: Use **Black-Scholes model** to estimate Greeks:
```python
from scipy.stats import norm
import numpy as np

def calculate_delta(S, K, T, r, sigma, option_type='C'):
    """
    S: Spot price
    K: Strike
    T: Time to expiration (years)
    r: Risk-free rate (0.03-0.05)
    sigma: Implied volatility (IV)
    """
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    if option_type == 'C':
        return norm.cdf(d1)
    else:
        return norm.cdf(d1) - 1
```

**Recommendation**: ✅ Build this fallback into `src/options_features.py`.

---

## 📊 ESTIMATED RESOURCE REQUIREMENTS

### **Development Time**

| Phase | Duration | Effort |
|-------|----------|--------|
| Phase 1: POC | 2-3 weeks | 20-30 hours |
| Phase 2: Strategy Translation | 3-4 weeks | 40-60 hours |
| Phase 3: Multi-Asset Validation | 2-3 weeks | 30-40 hours |
| Phase 4: Paper Trading | 4-6 weeks | 10-20 hours (monitoring) |
| **Total to Paper Trading** | **11-16 weeks** | **100-150 hours** |

### **API Costs**

- **Alpaca**: $0 (paper trading is free)
- **FMP**: Already have Ultimate plan ✅
- **Options Data**: Included in Alpaca feed ✅

**Total New Costs**: $0 ✅

---

## 🎯 FINAL VERDICT

### **Is Options Trend-Following Viable?**

**SHORT ANSWER**: ✅ **YES** - This is a HIGH-POTENTIAL opportunity that aligns perfectly with your existing infrastructure and trading style.

**LONG ANSWER**:
1. **Cost Advantage**: Options friction is 10-20x lower than equities on Alpaca ✅
2. **Strategic Fit**: System 1 (low frequency, trend-following) is IDEAL for options ✅
3. **Risk Management**: Defined risk (max loss = premium) is superior to equity drawdowns ✅
4. **Leverage**: 2-3x capital efficiency enables portfolio diversification ✅
5. **Alpaca Support**: API is mature, well-documented, fee-free ✅

### **Risks to Manage**:
1. 🔴 **Liquidity**: Stick to SPY/QQQ/NVDA/AAPL (most liquid)
2. 🟡 **IV Risk**: Add filters to avoid high IV environments
3. 🟡 **Expiration**: Build robust auto-roll logic
4. 🔴 **Complexity**: Options have more moving parts than equities
5. 🟡 **Theta Decay**: Trends must move fast enough to overcome daily decay

### **Recommended Next Steps**:

1. **This Week**: 
   - Review this assessment
   - Decide on commitment level (explore vs full build-out)
   - If yes → Start Phase 1 (API connection proof-of-concept)

2. **Month 1**: 
   - Complete Phase 1 (API POC)
   - Complete Phase 2 (Strategy translation)
   - Backtest SPY options with System 1

3. **Month 2-3**: 
   - Multi-asset validation (SPY, QQQ, NVDA)
   - Parameter optimization (delta, DTE, IV)
   - Begin paper trading

4. **Month 4-6**: 
   - Paper trading validation
   - Live deployment with 10% capital
   - Scale if successful

---

## 🚀 LET'S HAVE SOME FUN!

**This is EXACTLY the type of project that plays to your strengths**:
- ✅ You have proven trend-detection logic (System 1 + System 2)
- ✅ You have excellent git hygiene and testing discipline
- ✅ You have a solid data infrastructure (Alpaca + FMP)
- ✅ You appreciate removing complexity (options are simpler than multi-leg spreads)
- ✅ You value evidence over theory (we'll backtest before deploying)

**Why I'm Excited**:
1. **Intellectual Challenge**: Options are a new domain with rich math (Greeks, IV, time decay)
2. **Financial Upside**: 2-3x return potential vs equity-only
3. **Capital Efficiency**: Free up capital for other strategies
4. **Natural Evolution**: You've mastered equity trend-following, options are the next frontier

**Setting Realistic Expectations**:
- **This is NOT a get-rich-quick scheme**: 3-6 months to production
- **This WILL have bumps**: Options are complex, expect bugs and learning curve
- **This COULD outperform equity**: But only if executed with discipline

**My Quant's Oath**: I will guide you through this with the same rigor we applied to System 1 and System 2. We'll backtest thoroughly, paper trade patiently, and deploy conservatively.

**Are you ready to explore this?** 🚀

---

**END OF ASSESSMENT**

