# SPY Workhorse Strategy

**Symbol**: SPDR S&P 500 ETF Trust  
**Index**: S&P 500  
**Status**: ⚠️ OPTIONAL (Redundant with IVV)  

---

## Performance (2025 OOS)

| Metric | Value |
|--------|-------|
| Return | **+39.4%** |
| Trades | 338 |
| Win Rate | 38.8% |
| Expectancy | 0.109R |
| Starting Capital | $25,000 |
| Ending Capital | $34,850 |

---

## Parameters

```json
{
  "cluster_id": 6,
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
- Enter LONG at the CLOSE of the bar when Workhorse Cluster 6 fires
- No trend filter required

### Exit
1. **Target**: Entry + (3.0 × ATR20)
2. **Stop**: Entry - (1.0 × ATR20)
3. **Time**: Exit at close after 8 bars (2 hours)

---

## ⚠️ Why This is OPTIONAL

**SPY and IVV both track the S&P 500.**

| Metric | SPY | IVV |
|--------|-----|-----|
| Return | +39.4% | +75.6% |
| Cluster | 6 | 0 |
| Time Stop | 8 bars | 16 bars |

**IVV outperforms SPY by +36%** with the optimized configs.

### Reasons to Choose SPY Anyway:
1. **Best liquidity** - tightest spreads in the market
2. **Most familiar** - you may prefer it psychologically
3. **Options chain** - deepest options market if hedging

### Recommendation:
- **Use IVV** unless you have specific reason for SPY
- **Never run both** - same exposure, wasted capital
