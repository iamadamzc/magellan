# OPTIONS STRATEGY - QUICK START GUIDE

**Created**: 2026-01-15  
**Branch**: `feature/options-trend-following`  
**For**: Getting started with options exploration

---

## 🎯 TL;DR - THE OPPORTUNITY

**What**: Build a trend-following options strategy using your validated Daily Hysteresis system (System 1)

**Why**: 
- ✅ **90-95% lower friction** than equities on Alpaca
- ✅ **2-3x leverage** with defined risk
- ✅ **$0 commissions** on Alpaca options
- ✅ **Reuse proven RSI logic** (no new signal development needed)

**Timeline**: 12 weeks to production (6 weeks to first backtest)

**Risk Level**: Medium (options are more complex than equities, but strategy is conservative)

---

## 📊 HIGH-LEVEL STRATEGY

### **Current System 1 (Equity)**

```
RSI > 55  →  BUY equity  →  Hold until RSI < 45  →  SELL equity
```

**Performance** (GOOGL, 19 months):
- Return: +108%
- Sharpe: 2.05
- Trades: 8 (low frequency = low friction)

### **Proposed System 1 Options**

```
RSI > 55  →  BUY CALL (60 DTE, delta 0.60)  →  Hold/Roll  →  RSI < 45  →  Close CALL, BUY PUT
RSI < 45  →  BUY PUT (60 DTE, delta 0.60)   →  Hold/Roll  →  RSI > 55  →  Close PUT, BUY CALL
45 ≤ RSI ≤ 55  →  CLOSE ALL (Hold cash in quiet zone)
```

**Expected Performance** (Estimated):
- Return: +150-250% (2-3x equity due to leverage)
- Sharpe: 1.5-1.8 (lower due to theta decay)
- Max Loss per Trade: -100% of premium paid (vs -10-20% equity drawdown)
- Trades: 8 entries + 0-3 rolls = 8-24 transactions

---

## 💰 COST COMPARISON

### **Equity Trade Example: $10,000 GOOGL Position**

- Friction: 0.02-0.05% bid-ask spread
- Cost: **$2-$5 per side** = $4-$10 round-trip
- Capital Required: **$10,000**

### **Options Trade Example: $10,000 GOOGL Exposure**

- 5 contracts × $800 premium = **$4,000 capital**
- Delta 0.60 × 500 shares = 300 delta-adjusted shares × $200 = $6,000 exposure
- Friction: $0.097/contract × 5 contracts × 2 (round-trip) = **$0.97**
- **Savings**: $9/trade × 16 trades/year = $144/year (minimal, but capital efficiency is huge)

**Key Advantage**: Not the fee savings (small), but the **capital efficiency** (2.5x leverage with defined risk)

---

## 🚦 DECISION TREE

### **Should You Pursue This?**

**✅ YES, if**:
- You want to maximize returns with your proven System 1 logic
- You're comfortable with higher volatility (100% premium loss possible)
- You have 12 weeks for development + validation
- You're excited to learn options mechanics

**⚠️  MAYBE, if**:
- You want to deploy System 1 equity first, then add options later
- You prefer stable, predictable returns over explosive but volatile gains
- You're unsure about options complexity

**❌ NO, if**:
- You want to deploy trading capital immediately (use System 1 equity instead)
- You're not comfortable with 100% loss potential per trade
- You don't have time for 3-6 month development cycle

---

## 🛠️ IMMEDIATE NEXT STEPS

### **Step 1: Verify Alpaca Options Access** (15 minutes)

1. **Check if options are enabled**:
   - Log into Alpaca dashboard
   - Go to Account → Settings → Options Trading
   - Verify "Options Approved Level" ≥ 1

2. **Test API access**:
   ```bash
   # Run the connection test (create this file from Implementation Roadmap)
   python research/options_api_test.py
   ```

   **Expected Output**:
   ```
   ✅ Account Status: ACTIVE
   ✅ Options Trading Approved: 2
   ✅ Found 127 SPY call contracts
   ✅ ALL TESTS PASSED!
   ```

### **Step 2: Review Full Documents** (30 minutes)

- **Assessment**: `OPTIONS_TREND_FOLLOWING_ASSESSMENT.md` (5000 words, comprehensive)
- **Roadmap**: `OPTIONS_IMPLEMENTATION_ROADMAP.md` (detailed code examples)
- **This Guide**: Quick decision-making reference

### **Step 3: Make Go/No-Go Decision**

**Option A: Full Build-Out** (Recommended if excited)
- Commit to 12-week timeline
- Start with Phase 1 (API POC) this week
- Target: Paper trading by March, live by May

**Option B: POC Only** (Conservative approach)
- Commit to 3 weeks for Phase 1 only
- Build API connection and basic data fetch
- Reassess after seeing real options data

**Option C: Defer** (Focus on equity first)
- Deploy System 1 equity to start earning
- Revisit options in 3-6 months after equity is proven live
- Lower risk, slower growth

---

## 📚 RECOMMENDED LEARNING PATH

### **If New to Options** (1-2 weeks study before coding)

1. **Understand Basics** (2-3 hours):
   - Calls vs Puts
   - Strike price, expiration, premium
   - Intrinsic vs extrinsic value

2. **Learn Greeks** (2-3 hours):
   - Delta: Directional exposure
   - Theta: Time decay (your enemy as a buyer)
   - IV: Volatility pricing

3. **Practice on Paper** (1 week):
   - Manual options trades on Alpaca paper account
   - Experience expiration mechanics
   - See theta decay in action

4. **Then Start Coding** (Week 4+)

### **If Experienced with Options** (Start immediately)

- Review assessment for strategy specifics
- Proceed to Phase 1 (API POC)
- Validate Alpaca's options data quality

---

## 🎯 SUCCESS METRICS

### **Phase 1 Success (Week 3)**
- [ ] Connected to Alpaca Options API
- [ ] Fetched SPY options chain (30-60 DTE)
- [ ] Retrieved bid/ask quotes for 5 contracts
- [ ] Verified spreads are reasonable (<5% of mid price)

### **Phase 2 Success (Week 7)**
- [ ] Built strike selection logic (delta-based)
- [ ] Implemented auto-roll logic (DTE < 7)
- [ ] Created options feature engineering (IV, Greeks)
- [ ] First backtest runs without errors

### **Phase 3 Success (Week 10)**
- [ ] SPY backtest: Sharpe > 1.0, Return > +30% (2-year period)
- [ ] Win rate > 55%
- [ ] Max premium loss < 50% (vs 100% total wipeout)
- [ ] Code passes temporal leak audit

### **Phase 4 Success (Week 16)**
- [ ] 4 weeks of error-free paper trading
- [ ] Paper P&L matches backtest within 30%
- [ ] No critical bugs (wrong strikes, missed rolls)

---

## 🚨 RED FLAGS (Stop if you see these)

### **Phase 1 Red Flags**
- ❌ Alpaca options API is unreliable (frequent errors)
- ❌ Options spreads are >10% (illiquid market)
- ❌ Cannot fetch Greeks or IV data

### **Phase 2 Red Flags**
- ❌ Backtest code is taking >4 weeks (too complex)
- ❌ Cannot model theta decay accurately
- ❌ Strike selection logic yields nonsensical results

### **Phase 3 Red Flags**
- ❌ SPY backtest shows negative returns (strategy broken)
- ❌ Sharpe < 0.5 (worse than bonds)
- ❌ Friction costs are >5% per trade (model is wrong)

### **Phase 4 Red Flags**
- ❌ Paper trading P&L deviates >50% from backtest (overfitting)
- ❌ Multiple execution errors per week (buggy code)
- ❌ Theta decay is eating all gains (strategy doesn't work)

**Action**: If you hit 2+ red flags in any phase, **STOP** and reassess. Don't throw good money after bad.

---

## 💡 PRO TIPS FROM YOUR QUANT

### **Tip 1: Start with SPY, not individual stocks**

**Rationale**:
- SPY options are the most liquid in the world (millions of contracts daily)
- Tightest spreads (0.01-0.05 vs 0.10-0.30 on stocks)
- No earnings surprises (index doesn't have earnings)
- Your System 1 SPY: +25% return, 1.37 Sharpe (validated)

**Don't**: Jump straight to NVDA or TSLA (high IV, wider spreads, earnings risk)

### **Tip 2: Use 60 DTE, not 30 DTE**

**Rationale**:
- System 1 average hold time: 30-60 days
- 60 DTE gives you breathing room (less rolling)
- Theta decay: -$20/day (60 DTE) vs -$40/day (30 DTE)
- Costs: Fewer rolls = lower transaction fees

### **Tip 3: Target delta 0.60, not 0.50**

**Rationale**:
- Delta 0.50 (ATM): Max extrinsic value = max theta bleed
- Delta 0.60 (slightly ITM): More intrinsic, less theta
- Still 40% extrinsic for leverage, but more stable
- Better aligns with trend-following (you want directional exposure)

### **Tip 4: Avoid earnings weeks**

**Rationale**:
- IV spikes 50-100% before earnings (expensive options)
- IV crushes 30-50% after earnings (instant loss)
- Gap moves can negate signals

**Rule**: If earnings in <7 days, close options, wait in cash

### **Tip 5: Use hybrid allocation (60% equity / 40% options)**

**Rationale**:
- Equity provides stable base (System 1 is proven)
- Options provide explosive upside (2-3x leverage)
- If options fail, you still have equity core
- Psychologically easier to stomach 100% premium losses on smaller allocation

**Example Portfolio** ($100K):
- $60K: System 1 Daily Equity (11 assets)
- $40K: System 1 Options (SPY + QQQ only)

---

## 🎓 RECOMMENDED RESOURCES

### **Options Basics**
- [Investopedia Options Guide](https://www.investopedia.com/options-basics-tutorial-4583012)
- [CBOE Options Institute](https://www.cboe.com/education/)

### **Alpaca Options Documentation**
- [Alpaca Options Trading Docs](https://alpaca.markets/docs/trading/options/)
- [Alpaca API Reference](https://alpaca.markets/docs/api-references/)

### **Greeks \& Pricing**
- [Option Greeks Explained](https://www.optionsplaybook.com/options-introduction/option-greeks/)
- [Black-Scholes Calculator](https://www.investopedia.com/terms/b/blackscholes.asp)

---

## 🚀 FINAL WORDS

**This is a HIGH-POTENTIAL opportunity**. Your System 1 is perfect for options:
1. ✅ Low trade frequency (2-20/year) → Minimal rolling costs
2. ✅ Trend-following → Aligns with directional options (not spreads)
3. ✅ High win rate (60-86%) → Options perform best with conviction
4. ✅ Proven logic → No need to develop new signal generation

**But it's NOT a shortcut**. Options are complex:
- More moving parts (Greeks, IV, expiration)
- Higher volatility (100% loss possible per trade)
- Steeper learning curve

**My Recommendation**: 
- If you're excited → **Go for it!** (Option A: Full build-out)
- If you're cautious → **POC first** (Option B: 3-week test)
- If you're focused on equity → **Defer** (Option C: System 1 equity first)

**I'm here to guide you through whichever path you choose.** 🎯

---

**Good luck, and let's have some fun!** 🚀

---

**Quick Reference**:
- **Assessment**: `OPTIONS_TREND_FOLLOWING_ASSESSMENT.md` (Why + What)
- **Roadmap**: `OPTIONS_IMPLEMENTATION_ROADMAP.md` (How + Code)
- **This Guide**: Decision-making + Getting started

**Next Step**: Review assessment, make go/no-go decision, then ping me to proceed! 👍

