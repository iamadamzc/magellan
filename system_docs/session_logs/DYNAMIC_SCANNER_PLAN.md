# Bear Trap Dynamic Scanner - Implementation Plan
**Date:** January 26, 2026  
**Goal:** Replace static symbol list with dynamic market scanner  
**Threshold:** -10% (more opportunities than -15%)  
**Environment:** Paper trading (safe to experiment)

---

## 🎯 PERFECT IDEA FOR PAPER TRADING!

You're absolutely right - since this is paper trading, we should:
1. ✅ Lower threshold to -10% (3-5x more opportunities)
2. ✅ Use dynamic scanner (find ANY stock down -10%+)
3. ✅ Experiment freely (no real money at risk)
4. ✅ Prove the order execution works

This will give you WAY more trades and validate the strategy much faster.

---

## 🔧 IMPLEMENTATION APPROACH

### **Hybrid Scanner (Recommended)**

**Base Universe (Always Monitor):**
- 12 validated symbols from backtest
- Ensures we catch known good opportunities

**Dynamic Discovery:**
- Scan market every 5 minutes
- Find ANY stock down -10%+
- Add to watch list if liquid enough

**Combined Watch List:**
- Base universe + dynamically discovered stocks
- Max 50 symbols at once (manageable)
- Prune symbols that recover above -5%

---

## 📋 QUICK IMPLEMENTATION

I can implement this in about 2-3 hours:

1. **Add scanner logic** to `strategy.py`
2. **Lower threshold** from -15% to -10%
3. **Add config settings** for scanner
4. **Test locally** with paper account
5. **Deploy after hours**

**Expected Results:**
- **Current:** 0 trades today (no stocks down -15%)
- **With -10% + scanner:** 15-30 trades/month estimated
- **Proof of concept:** See if order execution actually works!

---

## ✅ SHALL I PROCEED?

**I can start implementing right now:**

1. Update `strategy.py` with scanner
2. Change threshold to -10%
3. Update config
4. Test locally
5. Deploy after market close

**This will give you real trading activity tomorrow and validate the entire system!**

Would you like me to start coding this?
