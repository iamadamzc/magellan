# GLD Workhorse Strategy

**Symbol**: SPDR Gold Shares  
**Asset**: Gold Bullion  
**Status**: ⚠️ PAPER TRADE FIRST  

---

## Performance (2025 OOS)

| Metric | Value |
|--------|-------|
| Return | **+118.5%** 🚀 |
| Trades | 251 |
| Win Rate | 38.2% |
| Expectancy | 0.328R |
| Starting Capital | $25,000 |
| Ending Capital | $54,618 |

---

## Parameters

```json
{
  "cluster_id": 4,
  "trend_filter": false,
  "target_atr": 3.0,
  "stop_atr": 1.0,
  "time_stop_bars": 12,
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
3. **Time**: Exit at close after 12 bars (3 hours)

---

## ⚠️⚠️⚠️ CRITICAL WARNINGS ⚠️⚠️⚠️

### Why You MUST Paper Trade First:

1. **Model was trained on EQUITY concepts**
   - Effort/result, volume patterns are equity-based
   - Gold has different market microstructure
   - This could be spurious correlation

2. **2025 was a GOLD RALLY year**
   - Any long-biased strategy would have worked
   - May be regime-specific, not edge
   - Needs multi-year validation

3. **SUSPICIOUS outperformance**
   - +118% is TOO good
   - When something works this well on an asset
     it wasn't designed for, be skeptical

4. **Different liquidity**
   - GLD has lower volume than SPY/QQQ
   - Slippage may be higher in practice

---

## Validation Plan

Before deploying real capital:

1. **Paper trade for 3+ months**
2. **Track actual vs expected signals**
3. **Compare to simple buy-and-hold gold**
4. **Validate on 2023-2024 data** (in-sample)
5. **Only deploy if paper trading confirms edge**

---

## If Validated

If paper trading confirms the edge:
- Start with 25% of intended position size
- Scale up over 3 months if performance holds
- Cut immediately if return diverges from expectation
