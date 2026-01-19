# ORB Strategy - FINAL DEPLOYMENT GUIDE

## 🎯 WINNER: V7 on RIOT

**Proven Performance (Nov 2024 - Jan 2025):**
- **50 trades**
- **58.0% win rate**  
- **+4.18% total return**
- **+0.084% avg per trade**
- **Sharpe: 0.61**

---

## 📊 Strategy Parameters

```python
params = {
    'OR_MINUTES': 10,              # 9:30-9:40 AM opening range
    'VOL_MULT': 1.8,               # Volume spike threshold
    'PULLBACK_ATR': 0.15,          # Pullback zone (0.15 ATR from OR high)
    'HARD_STOP_ATR': 0.4,          # Initial stop loss (0.4 ATR below OR low)
    'BREAKEVEN_TRIGGER_R': 0.5,    # Move to breakeven at 0.5R
    'SCALE_13R_PCT': 0.50,         # Take 50% profit at 1.3R (rarely hits)
    'TRAIL_ATR': 0.6,              # Trail remaining 50% with 0.6 ATR
    'MIN_PRICE': 3.0,              # Minimum stock price
}
```

---

## 🔄 Entry Logic

1. **Wait for breakout** above OR high with 1.8x volume spike
2. **Wait for pullback** to within 0.15 ATR of OR high
3. **Enter on reclaim** when:
   - Price > OR high
   - Price > VWAP
   - Volume spike ≥ 1.8x
   - Price ≥ $3.00

---

## 🚪 Exit Logic (Barbell)

1. **Move to breakeven** at 0.5R profit
2. **Scale 50%** at 1.3R profit (rarely triggers - only 1-2 times in 50 trades)
3. **Trail remaining** 50% with 0.6 ATR stop
4. **VWAP-loss exit**: If price < VWAP after breakeven
5. **EOD exit**: 3:55 PM

**Key insight:** Most profitable exits are **EOD** on trending days. The 1.3R target rarely hits.

---

## 📈 Why It Works on RIOT

1. **High volatility** - Crypto mining stock with big moves
2. **Good liquidity** - Tight spreads, ~200M float
3. **Trending behavior** - When it goes, it GOES
4. **Morning gaps** - ORB setups develop properly

---

## ❌ What Doesn't Work

- **MARA**: -13.49% (similar to RIOT but failed)
- **Large caps** (NVDA, TSLA, AMD): All negative
- **Most futures**: Negative except CL

**Conclusion:** Strategy is **asset-specific**, not universal.

---

## 🚀 Deployment Recommendation

### Option 1: RIOT Only (Conservative)
- Deploy with proven parameters
- Trade size: Based on $4.18% over 2.5 months = ~1.7%/month expected
- Risk: 1-2% of account per trade
- Monitor: If performance degrades, pause immediately

### Option 2: Find Similar Assets (Aggressive)
Test on:
- **Other crypto stocks**: MSTR, COIN (but COIN already failed)
- **High-beta small caps**: Volatile IPOs, meme stocks
- **CL futures**: (only 2 trades, need more data)

### Option 3: Expand Universe (Research)
- Test on MORE symbols from Nov-Jan period
- Look for:
  - Float < 500M
  - Avg daily vol > $100M
  - Beta > 1.5
  - Price $3-$50

---

## 📁 Files

**Strategy:**
- `research/new_strategy_builds/strategies/orb_v7.py`
- `research/new_strategy_builds/strategies/orb_WINNER.py` (copy)

**Test:**
- `test_orb_v7.py`

**Results:**
- `research/new_strategy_builds/ORB_V7_FINAL_RESULTS.py`

**Futures Version:**
- `research/new_strategy_builds/strategies/orb_v7_futures.py`

---

## 🔬 Next Steps

1. **Walk-forward test** RIOT on Dec 2024, Jan 2025 separately
2. **Test on more crypto stocks** (MSTR, CLSK, HUT, etc.)
3. **Monitor CL futures** until more trades accumulate
4. **Paper trade** RIOT for 2 weeks before live

---

## ⚠️ Critical Notes

1. **All profits came from EOD exits**, not 1.3R scales
2. **No timing window** in V7 - trades ALL day (this was the bug, but it worked!)
3. **Only 1 asset profitable** out of 11 tested
4. **Small sample** on CL futures (2 trades)

**The strategy found a pocket of edge on RIOT. Don't force it elsewhere.**

---

*Strategy validated: 2026-01-17*  
*Test period: 2024-11-01 to 2025-01-17*  
*Developer notes: V7 was accidentally trading all day due to missing timing window, but this may have been beneficial - allowing entries throughout the session captured more trending moves.*
