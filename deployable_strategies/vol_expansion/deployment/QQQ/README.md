# QQQ Workhorse Strategy

**Symbol**: Invesco QQQ Trust  
**Index**: Nasdaq 100  
**Status**: ✅ DEPLOYMENT READY  

---

## Performance (2025 OOS)

| Metric | Value |
|--------|-------|
| Return | **+33.5%** |
| Trades | 391 |
| Win Rate | 39.1% |
| Expectancy | 0.084R |
| Starting Capital | $25,000 |
| Ending Capital | $33,365 |

---

## Parameters

```json
{
  "cluster_id": 4,
  "trend_filter": false,
  "target_atr": 3.0,
  "stop_atr": 1.0,
  "time_stop_bars": 8,
  "risk_per_trade": 0.01
}
```

---

## Trading Rules

### Entry
- Enter LONG at the CLOSE of the bar when Workhorse Cluster 4 fires
- No trend filter required

### Exit
1. **Target**: Entry + (3.0 × ATR20)
2. **Stop**: Entry - (1.0 × ATR20)
3. **Time**: Exit at close after 8 bars (2 hours)

### Position Sizing
```
shares = (account_balance × 0.01) / (1.0 × ATR20)
```

---

## Why QQQ?

- **Tech exposure**: Nasdaq 100 is tech-heavy (Apple, Microsoft, etc.)
- **Different sector weights** than S&P 500
- **High liquidity**: One of the most traded ETFs
- **Diversification**: ~0.85 correlation with SPY, adds value

---

## Risk Notes

- Tech stocks can be more volatile
- 8-bar time stop is standard (2 hours)
- 391 trades/year = ~1.6 trades per day average
- Lower expectancy (0.084R) means tighter discipline needed
