# MAG7 DAILY HYSTERESIS - QUICK REFERENCE CARD

**Print this page and keep it handy!**

---

## 📊 **CURRENT SETTINGS (At-a-Glance)**

```
┌─────────┬────────┬───────┬──────┬──────────┬──────────┬────────┐
│ STOCK   │ RSI    │ ENTRY │ EXIT │ EXPECTED │ MAX DD   │ TRADES │
│         │ PERIOD │ (>)   │ (<)  │ RETURN   │          │ /YEAR  │
├─────────┼────────┼───────┼──────┼──────────┼──────────┼────────┤
│ GOOGL   │   28   │  55   │  45  │  +80%    │  -13%    │   8    │
│ AAPL    │   28   │  65   │  35  │  +30%    │  -20%    │   3    │
│ META    │   28   │  55   │  45  │  +25%    │  -17%    │  11    │
│ NVDA    │   28   │  58   │  42  │  +25%    │  -22%    │   7    │
│ MSFT    │   21   │  58   │  42  │  +14%    │  -12%    │   9    │
│ AMZN    │   21   │  55   │  45  │  +17%    │  -18%    │  19    │
│ TSLA    │   28   │  58   │  42  │ +100%    │  -27%    │   6    │
└─────────┴────────┴───────┴──────┴──────────┴──────────┴────────┘

PORTFOLIO: +23-65% annually | -18% max drawdown | 63 total trades/year
```

---

## 🚦 **REGIME QUICK CHECK**

**Check VIX every month (1st of month):**

```
VIX < 15   →  LOW VOL    →  Tighten bands  (55/45 → 52/48)
VIX 15-25  →  NORMAL     →  Keep current settings
VIX 25-35  →  HIGH VOL   →  Widen bands    (55/45 → 60/40)
VIX > 35   →  EXTREME    →  PAUSE TRADING (go to cash)
```

---

## ⚙️ **REGIME ADJUSTMENT CHEAT SHEET**

### **If VIX Spikes to 30 (High Vol)**

| Stock | Current Bands | → | New Bands |
|-------|---------------|---|-----------|
| GOOGL | 55/45 | → | 60/40 |
| AAPL  | 65/35 | → | 70/30 |
| META  | 55/45 | → | 60/40 |
| NVDA  | 58/42 | → | 65/35 |
| MSFT  | 58/42 | → | 62/38 |
| AMZN  | 55/45 | → | 60/40 |
| TSLA  | 58/42 | → | 65/35 |

### **If VIX Drops to 12 (Low Vol)**

| Stock | Current Bands | → | New Bands |
|-------|---------------|---|-----------|
| GOOGL | 55/45 | → | 52/48 |
| AAPL  | 65/35 | → | 62/38 |
| META  | 55/45 | → | 52/48 |
| NVDA  | 58/42 | → | 55/45 |
| MSFT  | 58/42 | → | 55/45 |
| AMZN  | 55/45 | → | 52/48 |
| TSLA  | 58/42 | → | 55/45 |

---

## 🔴 **EMERGENCY STOP CONDITIONS**

**PAUSE TRADING IMMEDIATELY IF:**
- [ ] VIX > 40
- [ ] Any stock down > 30% from peak
- [ ] Portfolio down > 25% from peak
- [ ] Win rate < 40% for 2 months
- [ ] System generating > 50 trades/month

**To Pause**: Edit all config files, set `"enabled": false`

---

## ✅ **DAILY CHECKLIST (5 min)**

**4:30 PM ET** (After Market Close):
- [ ] Check email summary
- [ ] Verify signals generated
- [ ] Review any trades executed
- [ ] Check for errors in log

---

## 📅 **MONTHLY CHECKLIST (30 min)**

**1st of Every Month**:
- [ ] Check VIX level
- [ ] Run: `python check_regime_change.py`
- [ ] Adjust bands if needed (see table above)
- [ ] Review performance vs expected
- [ ] Rebalance if any stock drifted > 20%

---

## 📞 **QUICK COMMANDS**

```bash
# Start system (auto mode)
python deploy_mag7_daily.py --mode auto

# Check regime
python check_regime_change.py

# Pause all trading
python deploy_mag7_daily.py --pause

# Resume trading
python deploy_mag7_daily.py --resume

# Rebalance portfolio
python rebalance_portfolio.py

# Test signal generation
python test_signal_generation.py --symbol GOOGL
```

---

## 💰 **EXPECTED PERFORMANCE TRACKER**

**After 1 Month**: +2% to +5%  
**After 3 Months**: +5% to +10%  
**After 6 Months**: +10% to +15%  
**After 12 Months**: +20% to +30%

**If you're BELOW these ranges**: Check regime, verify configs loaded correctly

**If you're ABOVE these ranges**: Great! But don't get overconfident, variance is normal

---

## 🎯 **CONFIG FILE LOCATIONS**

All settings in: `config/mag7_daily_hysteresis/`

**To change a setting**:
1. Open `config/mag7_daily_hysteresis/[SYMBOL].json`
2. Edit the value (e.g., `"hysteresis_upper": 55` → `60`)
3. Save file
4. Restart system

**Example** (Widen GOOGL bands):
```json
{
  "hysteresis_upper": 55,  →  "hysteresis_upper": 60,
  "hysteresis_lower": 45,  →  "hysteresis_lower": 40,
}
```

---

## 📊 **PERFORMANCE BENCHMARKS**

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| **Annual Return** | +20-30% | <+15% | <+10% |
| **Win Rate** | 60-80% | <50% | <40% |
| **Max Drawdown** | -15 to -25% | >-30% | >-35% |
| **Trades/Year** | 40-80 | >100 | >150 |
| **Sharpe Ratio** | >0.8 | <0.5 | <0.3 |

---

**Last Updated**: 2026-01-14  
**System Version**: 1.0 (Validated)  
**Next Review**: 2026-02-01

---

**KEEP THIS CARD VISIBLE WHILE TRADING!**
