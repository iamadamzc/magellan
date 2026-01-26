# System 3: Options Momentum Breakout Strategy

**Created**: 2026-01-15  
**Strategy Type**: Options-Only, High-Conviction Momentum  
**Status**: Design Phase  

---

## 📋 EXECUTIVE SUMMARY

**System 3** is a **high-conviction options momentum breakout strategy** designed to address the critical failures discovered in System 1 (equity signals applied to options).

### **The Problem**
System 1 (Daily Trend Hysteresis, RSI 58/42) works brilliantly for equity trading:
- ✅ Sharpe: 1.4-2.4
- ✅ Win Rate: 60-86%
- ✅ Trades: 8-12/year

**But fails spectacularly for options:**
- ❌ Sharpe: 0.27-0.55
- ❌ Win Rate: 28-30%
- ❌ Trades: 57/2 years (too many!)
- ❌ Total Return: -5% to -10% (vs SPY +46%)

### **Root Cause Analysis**

| Issue | System 1 (Equity) | System 1 (Options) | Impact |
|-------|------------------|-------------------|--------|
| **Signal Sensitivity** | RSI 58/42 (early detection) | RSI 58/42 (too loose) | ❌ 57 trades, whipsaw in quiet zone |
| **Theta Decay** | N/A (stocks don't expire) | -$20-40/day constant drain | ❌ Losing positions never recover |
| **Win Rate Requirement** | 60% acceptable | **Need >55%** for profitability | ❌ 28% = death spiral |
| **Trade Frequency** | More = better (no friction) | Fewer = better (lower decay cost) | ❌ Each trade pays premium |

### **The Solution: System 3**

Trade options **ONLY** on extreme momentum breakouts, not early trends.

**Core Thesis**: Options need **proof** the trend exists, not **anticipation** the trend is forming.

---

## 🎯 STRATEGY SPECIFICATION

### **Signal Criteria**

#### **Entry Rules**
```python
# BULLISH BREAKOUT → Buy CALL
if RSI > 65:
    action = 'BUY_CALL'
    # Rationale: RSI >65 = strong confirmed uptrend
    # Historical: Only 15-20% of days (high conviction)

# BEARISH BREAKDOWN → Buy PUT  
elif RSI < 35:
    action = 'BUY_PUT'
    # Rationale: RSI <35 = strong confirmed downtrend
    # Historical: Only 10-15% of days (rare, high conviction)

# NEUTRAL → Cash (avoid theta decay)
else:
    action = 'HOLD_CASH'
```

#### **Exit Rules**
```python
# MEAN REVERSION EXIT
if position_open and (45 <= RSI <= 55):
    action = 'CLOSE_POSITION'
    # Rationale: RSI crossing 50 = momentum exhausted
    # Take profit before theta decay erodes gains

# STOP LOSS (optional, evaluate in backtest)
if position_open and (
    (position_type == 'CALL' and RSI < 40) or
    (position_type == 'PUT' and RSI > 60)
):
    action = 'CLOSE_POSITION'  
    # Rationale: Signal invalidation = cut losses fast
```

### **Position Management**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Target Delta** | 0.70 | Deep ITM for lower theta decay, proven optimal from sweep |
| **DTE Range** | 45-60 days | Balance theta vs roll frequency |
| **Roll Threshold** | DTE < 7 | Avoid explosive theta in final week |
| **Position Size** | $10,000 notional | ~10% of $100K capital (proper risk mgmt) |
| **Max Positions** | 1 (long only) | Simplicity, no hedging complexity |

### **Comparison: System 1 vs System 3**

| Dimension | System 1 (Equity Signals) | System 3 (Momentum Breakout) | Change |
|-----------|--------------------------|----------------------------|--------|
| **RSI Buy Threshold** | 58 (early) | **65** (high conviction) | +7 points tighter |
| **RSI Sell Threshold** | 42 (early) | **35** (high conviction) | -7 points tighter |
| **Exit Logic** | Hold in 42-58 zone | **Close at RSI 50** | Active mean reversion exit |
| **Expected Trades** | 57/2 years (28/year) | **10-15/year** | 2.8x reduction |
| **Expected Win Rate** | 28% ❌ | **50-60%** ✅ | 2x improvement target |
| **Expected Sharpe** | 0.27-0.55 ❌ | **>1.0** ✅ | 3x improvement target |

---

## 📊 SUCCESS CRITERIA

### **Minimum Viable Product (MVP)**

System 3 must achieve **ALL** of the following to proceed to multi-asset validation:

- [ ] **Sharpe Ratio > 1.0** (vs 0.55 for System 1 baseline)
- [ ] **Win Rate > 50%** (vs 28% for System 1 baseline)
- [ ] **Total Return > 0%** (beat cash, even if not beat buy-hold)
- [ ] **Max Drawdown < 40%** (acceptable risk)
- [ ] **Trades: 10-20/year** (low frequency, high conviction)

### **Production-Ready**

System 3 must achieve the following for live deployment:

- [ ] **Sharpe Ratio > 1.5** (institutional grade)
- [ ] **Win Rate > 55%** (professional standard)
- [ ] **Outperform SPY Buy-Hold** (justify existence vs passive index)
- [ ] **Max Drawdown < 30%** (acceptable volatility)
- [ ] **Validated on 3+ assets** (SPY, QQQ, IWM)
- [ ] **4 weeks successful paper trading** (live validation)

### **Stretch Goals** (Nice to Have)

- [ ] Sharpe Ratio > 2.0 (elite performance)
- [ ] Win Rate > 60% (match System 1 equity)
- [ ] Outperform System 1 on risk-adjusted basis

---

## 🔬 HYPOTHESIS \& EXPECTED BEHAVIOR

### **Why System 3 Should Work**

| Mechanism | How It Helps | Expected Impact |
|-----------|-------------|----------------|
| **Tighter Entry Criteria** | RSI 65/35 only triggers on PROVEN trends | Win rate ↑ from 28% to 50-60% |
| **Fewer Trades** | 10-15/year vs 57/year | Theta decay cost ↓ by 70% |
| **Active Exit at RSI 50** | Close when momentum exhausted (instead of holding through decay) | Capture gains before reversal |
| **Longer Holds** | 30-60 days average (vs 10-15 days) | Intrinsic value has time to grow |
| **Delta 0.70** | Deep ITM = lower theta, higher probability of profit | Theta decay ↓, win rate ↑ |

### **Expected Trade Profile**

**Winning Trade Example**:
1. SPY at $500, RSI crosses 65 → Buy CALL ($425 strike, 52 DTE, delta 0.70)
2. Hold for 30-45 days as trend continues
3. RSI crosses 50 → Exit at profit (intrinsic value grew $20-30)
4. **Win**: 20-40% return

**Losing Trade Example**:
1. SPY at $500, RSI crosses 65 → Buy CALL ($425 strike, 52 DTE)
2. False breakout, RSI drops to 55 within 5 days
3. Exit at RSI 50 to cut losses
4. **Loss**: -5% to -10% (theta + extrinsic decay)

**Key**: With 50-60% win rate and 2:1 win/loss ratio, system is profitable.

---

## 🚧 RISK FACTORS \& MITIGATION

### **Known Risks**

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| **Too few trades** | Medium | Returns too low | If <5 trades/year, loosen to RSI 63/37 |
| **Win rate still <50%** | Medium | System unprofitable | Tighten further to RSI 70/30 |
| **Whipsaw at RSI 50 exit** | Low | Premature exits | Add confirmation (2-day RSI below 50) |
| **Theta decay still dominant** | Low | Negative returns | Shift to delta 0.80 (more ITM) |

### **Contingency Plans**

**If System 3 fails MVP criteria**:

1. **Plan A**: Tighten to RSI 70/30 (even higher conviction)
2. **Plan B**: Add trend confirmation (ADX >25, price >20-day MA)
3. **Plan C**: Use Bollinger Bands breakout (price >2σ) instead of RSI
4. **Plan D**: Pivot to different timeframe (weekly instead of daily)

**Abandon Threshold**: If 3 major iterations fail to achieve Sharpe >1.0, **options momentum strategy is not viable** with current market conditions.

---

## 🧪 BACKTEST DESIGN

### **Test Plan**

#### **Phase 2A: SPY Validation** (THIS PHASE)
- **Asset**: SPY only
- **Period**: 2024-2026 (2 years, 511 trading days)
- **Goal**: Prove System 3 > System 1 baseline

#### **Phase 2B: Multi-Asset Validation**
- **Assets**: QQQ (tech-heavy), IWM (small cap)
- **Period**: Same 2024-2026
- **Goal**: Confirm strategy generalizes

#### **Phase 2C: Parameter Sensitivity**
- **Variables**: RSI thresholds (63/37, 65/35, 67/33, 70/30), delta (0.60, 0.70, 0.80)
- **Goal**: Find optimal configuration

### **Expected Results**

| Scenario | Sharpe | Win Rate | Trades/Year | Verdict |
|----------|--------|---------|-------------|---------|
| **Best Case** | 1.8 | 65% | 12 | ✅ Production-ready immediately |
| **Base Case** | 1.2 | 55% | 15 | ✅ Proceed to multi-asset test |
| **Marginal** | 0.9 | 48% | 18 | ⚠️ Iterate (tighten to 70/30) |
| **Failure** | 0.5 | 35% | 25 | ❌ Pivot strategy |

---

## 💻 IMPLEMENTATION PLAN

### **Code Changes Required**

**File**: `research/backtests/options/phase2_validation/test_system3_momentum.py`

**Changes**:
1. Copy from `test_spy_baseline.py`
2. Modify signal thresholds (lines 126-136):
   ```python
   # OLD
   if rsi > 58:  # System 1
       current_position = 'BUY'
   elif rsi < 42:
       current_position = 'SELL'
   elif 42 <= rsi <= 58:
       current_position = 'HOLD'
   
   # NEW (System 3)
   if rsi > 65:  # High conviction
       current_position = 'BUY'
   elif rsi < 35:  # High conviction
       current_position = 'SELL'
   elif current_position in ['BUY', 'SELL'] and 45 <= rsi <= 55:
       # Exit when RSI crosses 50 (mean reversion)
       current_position = 'HOLD'
   ```

3. Update config (lines 542-543):
   ```python
   'rsi_buy_threshold': 65,  # Was 58
   'rsi_sell_threshold': 35,  # Was 42
   ```

**No other files need modification** - infrastructure is complete!

### **Verification Plan**

1. **Run System 3 Backtest**:
   ```bash
   python research/backtests/options/phase2_validation/test_system3_momentum.py
   ```

2. **Compare Results**:
   - System 1: `results/options/spy_baseline_trades.csv`
   - System 3: `results/options/spy_system3_trades.csv`

3. **Expected Improvements**:
   - ✅ Sharpe: 0.55 → >1.0 (2x improvement)
   - ✅ Win Rate: 28% → >50% (2x improvement)
   - ✅ Trades: 57 → 10-15 (4x reduction)

---

## 📅 TIMELINE

| Phase | Duration | Deliverable |
|-------|----------|------------|
| **Design** ✅ | 1 hour | This document |
| **Implementation** | 1 hour | `test_system3_momentum.py` |
| **SPY Backtest** | 30 min | Results + analysis |
| **Decision Point** | 15 min | GO/NO-GO for multi-asset |
| **Multi-Asset Test** (if GO) | 2 hours | QQQ, IWM validation |
| **Parameter Sweep** (if GO) | 2 hours | Optimization |
| **Total** | **1-2 days** | Production-ready strategy |

---

## ✅ NEXT STEPS

1. ✅ **Design Complete** (you are here!)
2. Create `test_system3_momentum.py` (copy + modify baseline)
3. Run backtest on SPY (2024-2026)
4. Compare to System 1 baseline
5. **Decision**:
   - ✅ If Sharpe >1.0 → Multi-asset validation
   - ❌ If Sharpe <1.0 → Iterate (RSI 70/30) or pivot

---

## 📚 REFERENCES

- **System 1 Baseline**: `results/options/spy_baseline_trades.csv`
- **Infrastructure**: `src/options/` (complete, no changes needed)
- **Handoff Doc**: `OPTIONS_HANDOFF.md` (detailed findings)
- **Assessment**: `OPTIONS_TREND_FOLLOWING_ASSESSMENT.md` (strategic context)

---

**CONFIDENCE LEVEL**: High (8/10)

**RATIONALE**:
- ✅ Clear hypothesis (tighter signals = higher win rate)
- ✅ Mathematical backing (fewer trades = less theta decay)
- ✅ Infrastructure proven (Black-Scholes, backtester works)
- ⚠️ Unknown: Will RSI 65/35 provide enough trades? (validate in backtest)

**STATUS**: Ready to implement! 🚀
