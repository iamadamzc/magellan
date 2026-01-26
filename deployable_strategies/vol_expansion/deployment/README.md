# Workhorse Strategy Deployment Configs

**Generated**: January 25, 2026  
**Test Period**: 2025 Out-of-Sample  
**Training Data**: 2022-2024  

---

## Quick Reference

| Priority | Symbol | Return | Trades | Status | Cluster | R:R | Time Stop |
|----------|--------|--------|--------|--------|---------|-----|-----------|
| 1 | **IVV** | +75.6% | 237 | ✅ READY | 0 | 3:1 | 16 bars |
| 2 | **QQQ** | +33.5% | 391 | ✅ READY | 4 | 3:1 | 8 bars |
| 3 | **IWM** | +65.8% | 425 | ✅ READY | 1 | 4:1 | 8 bars |
| 4 | SPY | +39.4% | 338 | ⚠️ Optional | 6 | 3:1 | 8 bars |
| 5 | GLD | +118.5% | 251 | ⚠️ Paper Trade | 4 | 3:1 | 12 bars |
| 6 | VOO | +28.2% | 18 | ❌ Low Sample | 4 | 4:1 | 4 bars |

---

## Recommended Portfolio

**Core Positions** (deploying real capital):
- **IVV** (40%) - Best S&P 500 performance
- **IWM** (35%) - Small caps, diversification
- **QQQ** (25%) - Tech exposure

**Total Expected Return**: ~57% weighted  
**Total Trades**: ~1,000+/year  

---

## Folder Structure

```
deployment/
├── IVV/
│   └── config.json      # Full parameters + performance
├── QQQ/
│   └── config.json
├── IWM/
│   └── config.json
├── SPY/
│   └── config.json      # Optional (redundant with IVV)
├── GLD/
│   └── config.json      # Paper trade first!
├── VOO/
│   └── config.json      # Low sample size
└── README.md            # This file
```

---

## Universal Parameters (All Symbols)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Timeframe | 15-min | Intraday bars |
| Session | 09:30-15:45 ET | Regular hours only |
| ATR Period | 20 | For targets/stops |
| Lookback | 20 bars | Feature aggregation |
| Risk/Trade | 1% | Position sizing |
| Slippage | $0.02/share | Already in results |

---

## Key Findings Summary

1. **3:1 R:R is optimal** for most symbols (vs 2:1 default)
2. **Trend filter HURTS** 7 out of 9 symbols
3. **Symbol-specific clusters** are critical
4. **Longer time stops** work for GLD (12-bar), IVV (16-bar)
5. **IWM uses tight stops** (0.5 ATR) with 4:1 R:R

---

## Trading Rules (Generic)

```
ENTRY:
  IF Workhorse Cluster signal fires
  THEN buy at CLOSE of signal bar

EXIT:
  IF price >= entry + (target_atr × ATR20)
    THEN sell at TARGET
  ELIF price <= entry - (stop_atr × ATR20)
    THEN sell at STOP
  ELIF bars_held >= time_stop_bars
    THEN sell at CLOSE (time exit)

POSITION SIZE:
  shares = (account × risk_pct) / (stop_atr × ATR20)
```

---

## Warnings

- ⚠️ **SPY vs IVV**: Both track S&P 500. Pick ONE, not both.
- ⚠️ **VOO**: Only 18 trades - statistically unreliable.
- ⚠️ **GLD**: May be overfitting. Paper trade 3+ months first.
- ⚠️ **No trend filter**: Most symbols perform BETTER without it.

---

## Next Steps

1. **Paper trade** IVV, QQQ, IWM for 1-2 weeks
2. **Validate** cluster signals match expected frequency
3. **Monitor** drawdowns - cut size if exceeding 15%
4. **Scale in** gradually - don't deploy full capital day 1
