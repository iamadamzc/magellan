# New Strategy Builds - Research Directory

**Branch**: `research/new-daily-strategies`  
**Purpose**: Build and test new trading strategies to achieve multi-strategy, multi-asset viability

---

## Strategy Portfolio (7 Total)

### Daily Timeframe Strategies (A-D)
Target: MAG7 equities + ETFs, daily bars, multi-day holds

#### Strategy A: Regime + Sentiment
- **Logic**: RSI(28) > 60 AND SPY > 200 MA AND news > 0
- **Why**: Triple filter prevents bear market catastrophes
- **Exit**: RSI < 40 OR SPY < 200 MA
- **Target Assets**: MAG7, QQQ, SPY

#### Strategy B: Wavelet Multi-Timeframe  
- **Logic**: Multi-timeframe RSI (5min/15min/60min/daily confluence)
- **Why**: Already implemented in system (`features.py`)
- **Exit**: wavelet_alpha < 0.4
- **Target Assets**: MAG7

#### Strategy C: Breakout + Sentiment
- **Logic**: 20-day high breakout AND news > 0
- **Why**: Momentum + catalyst confirmation
- **Exit**: 10-day low break
- **Target Assets**: MAG7, high-beta stocks

#### Strategy D: Moving Average Crossover
- **Logic**: 20 MA > 50 MA (entry), 20 MA < 50 MA (exit)
- **Why**: Classic baseline for comparison
- **Target Assets**: All (benchmark)

---

### Intraday Scalping Strategies (E-G)
Target: Small-cap movers, 1-minute bars, <30min holds

#### Strategy E: VWAP Reclaim / Washout Reversal ✅ PRIORITY
- **Type**: Mean reversion → momentum
- **Entry**: Flush below VWAP with absorption wick + reclaim
- **Exit**: 30% @ VWAP bounce, 30% @ HOD, runner trails
- **Stop**: Flush low - 0.45 ATR
- **Hold**: 30 minutes max
- **Consensus**: Highest across all experts

#### Strategy F: Opening Range / PMH Breakout
- **Type**: Momentum breakout
- **Entry**: Gap >15% + break OR_High/PMH + 2.5x volume
- **Exit**: 45% @ 1R, 30% @ 2R, runner trails
- **Stop**: Breakout level - 0.40 ATR
- **Hold**: 20 minutes max
- **Filters**: 5-min ADX > 25 (Dee_S multi-timeframe)

#### Strategy G: Micro Pullback Continuation
- **Type**: Trend continuation scalp
- **Entry**: Shallow pullback (<0.75 ATR) + volume spike reversal
- **Exit**: 45% @ 1R, 30% @ 2R, runner trails @ EMA
- **Stop**: Pullback low or 0.45 ATR
- **Hold**: 15 minutes max
- **Frequency**: Highest (multiple per day)

---

## Expert Consensus Summary

### Primary Sources
1. **Chad_G**: Most complete parameterization, ATR-normalized risk
2. **Dee_S**: Multi-timeframe filters, regime awareness, missing components analysis
3. **Gem_Ni**: Market structure insights (L2, IMP, wick validation)

### Key Insights Incorporated
- **ATR-normalization** (Chad_G): All stops/targets use ATR, not fixed %
- **Multi-timeframe** (Dee_S): 5-min trend filter for 1-min entries
- **Wick validation** (Gem_Ni): Absorption wick >40% proves institutional buyers
- **Regime filters** (All): Liquidity/spread gates mandatory before ANY entry

---

## Data Requirements

### Daily Strategies (A-D)
✅ **Daily OHLCV**: Cached (MAG7, ETFs, 2022-2025)  
⚠️ **News sentiment**: Needs caching (add to `prefetch_data.py`)  
✅ **SPY 200 MA**: Can calculate from cached SPY daily

### Scalping Strategies (E-G)
❌ **1-minute OHLCV**: NOT cached yet (need to add)  
❌ **Small-cap universe**: RIOT, MARA, PLUG, LCID, NIO, SOFI, etc.  
❌ **Volume profile**: May need Level 2 (Gem_Ni insight)

---

## Testing Plan

### Phase 1: Daily Strategies (This Week)
1. Add news to cache
2. Build Strategy A (regime + sentiment)
3. Test on AAPL (validation)
4. Build B, C, D
5. Run full test matrix (4 × 11 × 2 periods = 88 tests)
6. ~2 minutes runtime with cache

### Phase 2: Scalping Strategies (Next Week)
1. Cache 1-min data for small-cap universe
2. Build Strategy E (VWAP Reclaim - highest priority)
3. Test on RIOT (high vol small-cap)
4. Validate with Nov-Dec 2024 data
5. Build F and G if E validates

---

## Directory Structure

```
research/new_strategy_builds/
├── README.md (this file)
├── SMALL_CAP_SCALPING_STRATEGIES.md (E-G specifications)
├── small_cap_red_team/ (expert analyses)
│   ├── Chad_G.md
│   ├── Dee_S.md
│   ├── Gem_Ni.md
│   ├── Synthesis_Chad_G.md ✅
│   ├── Synthesis_Dee_S.md ✅
│   └── Synthesis_Gem_Ni.md ✅
├── strategies/ (implementations - to be built)
│   ├── strategy_a_regime_sentiment.py
│   ├── strategy_b_wavelet.py
│   ├── strategy_c_breakout_sentiment.py
│   ├── strategy_d_ma_cross.py
│   ├── strategy_e_vwap_reclaim.py ← BUILD FIRST
│   ├── strategy_f_orb_breakout.py
│   └── strategy_g_micro_pullback.py
├── results/ (test outputs)
│   ├── daily_strategies_results.csv
│   └── scalping_strategies_results.csv
└── analysis/
    └── comparison_report.md
```

---

## Success Criteria

### Minimum (Daily)
- 1 strategy beats RSI 55/45 baseline
- 3+ assets viable
- Works in BOTH bull and bear periods

### Target (Daily)
- 2+ strategies viable
- 5+ assets per strategy
- Sharpe > 0.7 in both periods

### Minimum (Scalping)
- 1 strategy shows profit factor > 1.3
- Win rate 45-55%
- R:R > 2:1

### Target (Scalping)
- 2+ strategies profitable
- Sharpe > 0.8
- <30min avg hold time

---

## Next Actions

**Immediate**:
1. ✅ Review small-cap expert analyses (DONE)
2. ✅ Finalize 3 scalping strategies (DONE)
3. Add news caching to `prefetch_data.py`
4. Build Strategy A (daily regime + sentiment)

**This Week**:
- Complete daily strategies (A-D)
- Run test matrix
- Analyze results

**Next Week**:
- Add 1-min data caching
- Build Strategy E (scalping)
- Validate on small-caps

---

**Last Updated**: 2026-01-17  
**Status**: Strategies specified, ready to implement
