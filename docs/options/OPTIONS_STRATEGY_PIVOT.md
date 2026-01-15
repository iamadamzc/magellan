# OPTIONS STRATEGY PIVOT - COMPREHENSIVE PLAN

**Date**: 2026-01-15  
**Decision**: Abandon momentum buying, pivot to premium selling + event-driven  
**Status**: Implementation ready

---

## 📊 WHAT WE LEARNED (Critical Findings)

### **Momentum Buying Failed** ❌

Tested across 4 systems, 2 assets (SPY, NVDA):
- **Win Rate**: 28-45% (target was >55%)
- **Sharpe**: -0.30 to 0.07 (target was >1.0)
- **Root Cause**: SIGNAL_FLIP exits destroy performance (0% win rate, -60% avg loss)

**BUT**: 80-90% win rate on trades held 45+ days (ROLL exits)!

### **Key Insight**: The entry works! Exit timing kills it.

---

## 🎯 NEW STRATEGY #1: PREMIUM SELLING (THE THETA HARVESTER)

### **Core Thesis**

**Instead of buying options (pay theta), SELL options (collect theta)**

### **Strategy Specification**

```python
# Entry: When RSI indicates mean reversion setup
if RSI < 30:  # Oversold
    SELL PUT (cash-secured)
    # Collect premium as stock bounces back
    
elif RSI > 70:  # Overbought
    SELL CALL (covered, or use spread)
    # Collect premium as stock pulls back

# Exit: 
- Target: Collect 50-70% of premium (don't be greedy)
- Time: Close at 21 DTE (theta accelerates, diminishing returns)
- Stop: Close if stock moves >2σ against position
```

### **Why This Should Work**

| Factor | Buying Options ❌ | Selling Options ✅ |
|--------|------------------|-------------------|
| **Theta** | Enemy (lose $20-40/day) | Friend (earn $20-40/day) |
| **Win Rate** | Need >60% | 70-80% typical |
| **Payoff** | 20:1 on wins, -100% on losses | Small wins, capped loss |
| **Edge** | Predict direction | Predict NO extreme move |

### **Expected Performance**

- **Win Rate**: 70-80% (vs 28% buying)
- **Sharpe**: 1.5-2.5 (vs 0.07 buying)
- **Trades**: 15-25/year
- **Avg Win**: +20-40% premium collected
- **Avg Loss**: -50-80% (get out fast)

### **Implementation Priority: HIGH**

**Timeline**: 2-3 hours to backtest and validate

---

## 🎯 NEW STRATEGY #2: EVENT-DRIVEN OPTIONS (THE CATALYST TRADER)

### **Core Thesis**

**Trade options ONLY around known catalysts with defined exit dates**

### **FMP Ultimate Data Assets**

Based on https://site.financialmodelingprep.com/developer/docs/pricing, we have:

#### **Earnings Data** ⭐
- `earnings_calendar` - Exact earnings dates
- `earnings_surprises` - Historical beat/miss data
- `earnings_confirmed` - Confirmed dates

#### **Economic Calendar** ⭐
- Fed meetings
- CPI, NFP, GDP releases
- Interest rate decisions

#### **Insider Trading** ⭐
- Large purchases before catalysts
- Executive activity signals

#### **Institutional Ownership**
- 13F filings (hedge fund positions)
- Whale movements

#### **Analyst Ratings**
- Upgrades/downgrades (often precede moves)
- Price target changes

### **Strategy #2A: Earnings Straddles**

```python
# Setup
entry_date = earnings_date - 2 days
exit_date = earnings_date + 1 day  # Next trading day

# Position
BUY CALL (ATM, 7 DTE) + BUY PUT (ATM, 7 DTE)
# Straddle = profit from big move either direction

# Exit
- Target: +50% on total premium (stock moves >5%)
- Stop: -50% if stock doesn't move (theta burn)
- Time: Always exit day after earnings (no exceptions!)
```

**Why This Works**:
- ✅ Known catalyst date (no SIGNAL_FLIP problem!)
- ✅ Defined holding period (2-3 days, not 45)
- ✅ High IV before earnings (options are expensive - sell afterwards)
- ✅ Clear exit (no discretion)

### **Strategy #2B: Fed Meeting Straddles**

```python
# Fed meetings = 8x/year predictable volatility

entry_date = fed_meeting - 1 day
exit_date = fed_meeting + 0 days  # Same day

# Position
SPY/QQQ STRADDLE (ATM, 7 DTE)

# Exit
Close position 30 min after Fed announcement
```

### **Strategy #2C: Insider Front-Running** 

```python
# When 10+ insiders buy in same week → bullish signal

if insider_purchases > 10 and total_value > $1M:
    BUY CALL (30 DTE, delta 0.60)
    
# Exit
if stock_move > 5%: Take profit
elif 21 days elapsed: Exit (don't overstay)
```

### **Expected Performance (Event-Driven)**

- **Win Rate**: 55-65% (defined catalysts)
- **Sharpe**: 1.2-1.8
- **Trades**: 20-40/year (earnings + fed meetings)
- **Avg Win**: +60-80%
- **Avg Loss**: -30-40%

### **Implementation Priority: MEDIUM**

**Timeline**: 4-6 hours (need FMP API integration)

---

## 🚀 IMPLEMENTATION PLAN

### **Phase 1: Premium Selling (TODAY)**

**Priority**: HIGH - Quick win, uses existing infrastructure

**Steps**:
1. ✅ Copy `test_system4_fixed_duration.py` → `test_premium_selling.py`
2. ✅ Invert logic: SELL instead of BUY
3. ✅ Use RSI 30/70 (oversold/overbought)
4. ✅ Exit at 50% premium collected or 21 DTE
5. ✅ Run on SPY 2025 data
6. ✅ **Decision**: If Sharpe >1.5 → Production ready!

**Expected Time**: 2 hours

---

### **Phase 2: Event-Driven Setup (NEXT)**

**Priority**: MEDIUM - Higher upside, more complex

**Steps**:
1. ⏳ Integrate FMP earnings calendar API
2. ⏳ Build earnings straddle backtester
3. ⏳ Test on NVDA, TSLA, META (high-IV tech)
4. ⏳ Validate on 2024-2025 earnings (40+ events)
5. ⏳ **Decision**: If Sharpe >1.2 → Add to production

**Expected Time**: 6 hours

---

### **Phase 3: Combined Portfolio (IF BOTH WORK)**

**If premium selling AND event-driven both succeed**:

```python
# Portfolio Allocation
50% Premium Selling (steady theta income)
50% Event-Driven (catalyst profits)

# Expected Combined Performance
Win Rate: 65-75%
Sharpe: 1.8-2.5
Trades: 30-50/year
```

---

## 📋 BACKTEST SPECIFICATIONS

### **Premium Selling Backtest**

```python
# test_premium_selling.py

class PremiumSellingBacktester:
    def calculate_signals(self, df):
        """
        Sell puts when oversold, sell calls when overbought.
        """
        if RSI < 30:
            return 'SELL_PUT'  # Collect premium on mean reversion
        elif RSI > 70:
            return 'SELL_CALL'  # Collect premium on pullback
        else:
            return 'HOLD'
    
    def exit_logic(self, position):
        """
        Exit when profit target hit or theta diminishes.
        """
        if position['unrealized_pnl_pct'] > 50:
            # Collected 50% of premium → close winner
            return 'TAKE_PROFIT'
        
        elif position['dte'] < 21:
            # Theta acceleration slows → exit
            return 'TIME_EXIT'
        
        elif position['unrealized_pnl_pct'] < -80:
            # Stop loss → exit loser fast
            return 'STOP_LOSS'
        
        return 'HOLD'

# Key Differences from Buying:
# 1. SELL options (not buy)
# 2. Profit = premium decay (not intrinsic growth)
# 3. Exit EARLY when profitable (collect 50-70%, not 100%)
```

### **Earnings Straddle Backtest**

```python
# test_earnings_straddles.py

class EarningsStraddleBacktester:
    def fetch_earnings_calendar(self, symbol, year):
        """
        Use FMP earnings calendar API.
        """
        url = f"https://financialmodelingprep.com/api/v3/earning_calendar?symbol={symbol}&year={year}&apikey={FMP_KEY}"
        # Returns: [{'date': '2025-01-15', 'symbol': 'NVDA', ...}, ...]
    
    def calculate_signals(self, earnings_dates):
        """
        Enter 2 days before earnings, exit 1 day after.
        """
        for earnings_date in earnings_dates:
            entry_date = earnings_date - timedelta(days=2)
            exit_date = earnings_date + timedelta(days=1)
            
            yield {
                'entry': entry_date,
                'exit': exit_date,
                'type': 'STRADDLE',  # Buy ATM call + ATM put
                'dte': 7
            }
    
    def backtest_earnings_cycle(self, symbol, year):
        """
        Test all earnings events for a symbol in a year.
        """
        earnings = self.fetch_earnings_calendar(symbol, year)
        
        for event in earnings:
            # Simulate straddle entry 2 days before
            # Track P&L through earnings
            # Exit 1 day after
            pass
```

---

## 🎓 SUCCESS CRITERIA

### **Premium Selling**
- ✅ Sharpe > 1.5
- ✅ Win rate > 70%
- ✅ Max drawdown < 25%
- ✅ Outperform SPY buy-hold

### **Event-Driven**
- ✅ Sharpe > 1.2
- ✅ Win rate > 55%
- ✅ Avg win > 50%
- ✅ Trades = 4x earnings/year per symbol

---

## 🔧 NEXT IMMEDIATE ACTIONS

1. **[RIGHT NOW]** Implement premium selling backtest (2 hours)
2. **[AFTER #1]** Test on SPY 2025 data
3. **[IF #2 WORKS]** Implement earnings straddle backtest
4. **[IF #3 WORKS]** Integrate FMP earnings calendar
5. **[FINAL]** Combined strategy or pick winner

---

## 📊 FMP API ENDPOINTS TO USE

Based on Ultimate plan access:

```python
# Earnings
earnings_calendar = "https://financialmodelingprep.com/api/v3/earning_calendar"
earnings_surprises = "https://financialmodelingprep.com/api/v3/earnings-surprises/{symbol}"

# Economic Calendar
economic_calendar = "https://financialmodelingprep.com/api/v3/economic_calendar"

# Insider Trading
insider_trades = "https://financialmodelingprep.com/api/v4/insider-trading"

# Analyst Ratings
analyst_ratings = "https://financialmodelingprep.com/api/v3/upgrades-downgrades"
```

---

**READY TO IMPLEMENT!** 🚀

Let's start with premium selling - if it works, we have a winner. If not, we pivot to event-driven immediately.
