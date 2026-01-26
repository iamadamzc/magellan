# VOO Workhorse Strategy

**Symbol**: Vanguard S&P 500 ETF  
**Index**: S&P 500  
**Status**: ❌ LOW SAMPLE SIZE  

---

## Performance (2025 OOS)

| Metric | Value |
|--------|-------|
| Return | +28.2% |
| Trades | **18** ⚠️ |
| Win Rate | 61.1% |
| Expectancy | 1.41R |
| Starting Capital | $25,000 |
| Ending Capital | $32,050 |

---

## Parameters

```json
{
  "cluster_id": 4,
  "trend_filter": false,
  "target_atr": 2.0,
  "stop_atr": 0.5,
  "time_stop_bars": 4,
  "risk_per_trade": 0.01
}
```

---

## ⚠️⚠️⚠️ MAJOR WARNING ⚠️⚠️⚠️

### ONLY 18 TRADES

**This is not statistically significant.**

- 61% win rate with 18 trades has a confidence interval of ±20%
- True win rate could be anywhere from 41% to 81%
- The 1.41R expectancy could easily be luck

### Minimum Required for Confidence
- **50+ trades** for basic confidence
- **100+ trades** for deployment
- **18 trades** = DO NOT DEPLOY

---

## Why This Happened

VOO tracks the same index as SPY and IVV (S&P 500), but:
- Lower liquidity than SPY
- Cluster 4 fires less often on VOO's price action
- Different data feed/timing may cause fewer signals

---

## Recommendation

**DO NOT deploy VOO with real capital.**

Instead:
1. **Use IVV** (same index, 237 trades, validated)
2. **Or use SPY** (same index, 338 trades, validated)

VOO adds no value when IVV/SPY are available with proper sample sizes.
