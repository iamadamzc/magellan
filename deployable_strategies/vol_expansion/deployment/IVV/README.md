# IVV Workhorse Strategy

**Symbol**: iShares Core S&P 500 ETF  
**Index**: S&P 500  
**Status**: ✅ DEPLOYMENT READY  

---

## Performance (2025 OOS)

| Metric | Value |
|--------|-------|
| Return | **+75.6%** |
| Trades | 237 |
| Win Rate | 38.0% |
| Expectancy | 0.253R |
| Starting Capital | $25,000 |
| Ending Capital | $43,905 |

---

## Parameters

```json
{
  "cluster_id": 0,
  "trend_filter": false,
  "target_atr": 3.0,
  "stop_atr": 1.0,
  "time_stop_bars": 16,
  "risk_per_trade": 0.01
}
```

---

## Trading Rules

### Entry
- Enter LONG at the CLOSE of the bar when Workhorse Cluster 0 fires
- No trend filter required

### Exit
1. **Target**: Entry + (3.0 × ATR20)
2. **Stop**: Entry - (1.0 × ATR20)
3. **Time**: Exit at close after 16 bars (4 hours)

### Position Sizing
```
shares = (account_balance × 0.01) / (1.0 × ATR20)
```

---

## Why IVV Over SPY?

Both track the S&P 500, but IVV shows:
- **Better return**: +75.6% vs +39.4%
- **Different optimal cluster**: Cluster 0 vs Cluster 6
- **Longer optimal time stop**: 16 bars vs 8 bars

This suggests IVV's slightly different liquidity profile creates
different microstructure patterns that Cluster 0 captures better.

---

## Risk Notes

- 16-bar time stop means positions can last up to 4 hours
- 38% win rate means expect 6+ consecutive losses sometimes
- 3:1 R:R requires discipline to let winners run
