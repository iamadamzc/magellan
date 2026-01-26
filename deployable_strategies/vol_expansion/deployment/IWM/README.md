# IWM Workhorse Strategy

**Symbol**: iShares Russell 2000 ETF  
**Index**: Russell 2000 (Small Caps)  
**Status**: ✅ DEPLOYMENT READY  

---

## Performance (2025 OOS)

| Metric | Value |
|--------|-------|
| Return | **+65.8%** |
| Trades | 425 |
| Win Rate | 32.9% |
| Expectancy | 0.137R |
| Starting Capital | $25,000 |
| Ending Capital | $41,443 |

---

## Parameters

```json
{
  "cluster_id": 1,
  "trend_filter": false,
  "target_atr": 2.0,
  "stop_atr": 0.5,
  "time_stop_bars": 8,
  "risk_per_trade": 0.01
}
```

---

## Trading Rules

### Entry
- Enter LONG at the CLOSE of the bar when Workhorse Cluster 1 fires
- No trend filter required

### Exit
1. **Target**: Entry + (2.0 × ATR20)
2. **Stop**: Entry - (0.5 × ATR20) ⚠️ TIGHT STOP
3. **Time**: Exit at close after 8 bars (2 hours)

### Position Sizing
```
shares = (account_balance × 0.01) / (0.5 × ATR20)
```

---

## Why IWM?

- **Small caps**: Russell 2000 is different factor exposure
- **Best diversifier**: ~0.75 correlation with S&P 500
- **Highest trade count**: 425 trades = most active
- **Tight stop strategy**: Lower win rate but higher R:R

---

## ⚠️ IMPORTANT: Tight Stop Strategy

IWM uses a **4:1 R:R ratio** (2.0 target / 0.5 stop):

- **Win rate is LOWER** (33%) because stops are tight
- **Expect 7-10 consecutive losses** occasionally
- **BUT winners are 4x bigger** than losers
- **Requires iron discipline** - don't widen stops!

---

## Risk Notes

- Small caps can have higher volatility
- Tight stops mean more whipsaws
- Lower win rate requires strong psychology
- Best diversification benefit of all symbols
