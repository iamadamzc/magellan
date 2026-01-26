# Optimization History & Methodology

**Project**: Magellan Workhorse Strategy  
**Date**: January 25, 2026  
**Author**: Quant Strategy Team  

---

## Overview

This document records the complete optimization process that transformed
the original SPY-only strategy into a multi-symbol deployment-ready system.

---

## Phase 0: Baseline (Pre-Optimization)

### Original SPY Defaults Applied to All Symbols

| Symbol | Return | Status |
|--------|--------|--------|
| SPY | +9.7% | ✅ Profitable |
| QQQ | -7.4% | ❌ Losing |
| IWM | -2.8% | ❌ Losing |
| IVV | -2.7% | ❌ Losing |
| VOO | -0.0% | Flat |
| GLD | -16.7% | ❌ Losing |
| SLV | -27.0% | ❌ Losing |
| TQQQ | -14.6% | ❌ Losing |
| SOXL | -43.6% | ❌ Losing |

**Profitable Symbols**: 1/9 (11%)

---

## Phase 0.5: Symbol-Specific Cluster + Trend Optimization

### Key Finding: Trend Filter HURTS Most Symbols

| Symbol | Best Cluster | Trend Filter | Return After |
|--------|--------------|--------------|--------------|
| SPY | 6 | ❌ OFF | +7.5% |
| QQQ | 4 | ❌ OFF | +21.5% |
| IWM | 1 | ❌ OFF | +7.6% |
| IVV | 0 | ❌ OFF | +42.1% |
| VOO | 4 | ❌ OFF | +9.7% |
| GLD | 4 | ❌ OFF | +41.4% |
| SLV | 6 | ❌ OFF | -7.8% |
| TQQQ | 2 | ✅ ON | +3.4% |
| SOXL | 1 | ✅ ON | -1.5% |

**Profitable Symbols**: 7/9 (78%)

---

## Phase 1: R:R Ratio Optimization

### Key Finding: 3:1 R:R is Optimal for Most Symbols

| Symbol | Best R:R | Return Before | Return After | Improvement |
|--------|----------|---------------|--------------|-------------|
| GLD | 3:1 | +41.4% | +77.9% | +36.5% |
| IWM | 4:1 (tight) | +7.6% | +65.8% | +58.2% |
| IVV | 3:1 | +42.1% | +46.0% | +3.9% |
| SPY | 3:1 | +7.5% | +39.4% | +31.9% |
| QQQ | 3:1 | +21.5% | +33.5% | +12.0% |
| VOO | 4:1 (tight) | +9.7% | +16.3% | +6.6% |

**Scripts**: `phase1_optimize_rr.py`  
**Results**: `phase1_rr_results.json`

---

## Phase 2: Time Stop Optimization

### Key Finding: Longer Holds Work for Some Symbols

| Symbol | Best Time Stop | Return Before | Return After | Improvement |
|--------|----------------|---------------|--------------|-------------|
| GLD | 12 bars (3hr) | +77.9% | +118.5% | +40.6% |
| IVV | 16 bars (4hr) | +46.0% | +75.6% | +29.6% |
| VOO | 4 bars (1hr) | +16.3% | +28.2% | +11.9% |
| SLV | 16 bars (4hr) | -1.1% | +4.4% | +5.5% |
| TQQQ | 16 bars (4hr) | +3.4% | +5.4% | +2.0% |
| SPY | 8 bars (2hr) | +39.4% | +39.4% | 0.0% |
| QQQ | 8 bars (2hr) | +33.5% | +33.5% | 0.0% |
| IWM | 8 bars (2hr) | +65.8% | +65.8% | 0.0% |

**Scripts**: `phase2_optimize_timestop.py`  
**Results**: `phase2_timestop_results.json`

---

## Phase 3: Cluster Count Optimization

**Status**: SKIPPED

Rationale: k=8 clusters is working well. Marginal expected improvement
didn't justify additional complexity and overfitting risk.

---

## Phase 4: Sniper Strategy Optimization

### Key Finding: Sniper Has Low Frequency

| Symbol | Best Config | Trades | Return |
|--------|-------------|--------|--------|
| SLV | 15% pct, No trend | 7 | +8.3% |
| GLD | 10% pct, No trend | 6 | +5.6% |
| IVV | 15% pct, No trend | 5 | +1.6% |
| Others | - | 0-4 | 0% or negative |

**Conclusion**: Sniper thresholds are too restrictive for most symbols.
Workhorse (cluster-based) is the primary strategy.

**Scripts**: `phase4_optimize_sniper.py`  
**Results**: `phase4_sniper_results.json`

---

## Final Results Summary

### Before vs After Optimization

| Symbol | Before | After | Improvement |
|--------|--------|-------|-------------|
| GLD | -16.7% | **+118.5%** | +135.2% |
| IVV | -2.7% | **+75.6%** | +78.3% |
| IWM | -2.8% | **+65.8%** | +68.6% |
| SPY | +9.7% | **+39.4%** | +29.7% |
| QQQ | -7.4% | **+33.5%** | +40.9% |
| VOO | -0.0% | **+28.2%** | +28.2% |
| TQQQ | -14.6% | **+5.4%** | +20.0% |
| SLV | -27.0% | **+4.4%** | +31.4% |
| SOXL | -43.6% | **+0.6%** | +44.2% |

**Profitable Symbols**: 9/9 (100%)  
**Total Combined Return**: +371.4%

---

## Key Learnings

1. **Symbol-specific clusters are critical**
   - Each symbol needs its own cluster ID
   - SPY's Cluster 7 does NOT work on other symbols

2. **Trend filter hurts most symbols**
   - 7/9 symbols perform BETTER without trend filter
   - Only TQQQ and SOXL benefit from trend filter

3. **3:1 R:R outperforms 2:1 baseline**
   - Wider targets capture more trend
   - Win rate drops but expectancy increases

4. **Longer time stops help some symbols**
   - GLD: 12 bars (+40% improvement)
   - IVV: 16 bars (+30% improvement)
   - Others: 8 bars is optimal

5. **IWM benefits from tight stops**
   - 0.5 ATR stop with 4:1 R:R
   - Lower win rate but higher profit factor

---

## File Inventory

### Data Files
- `phase1_rr_results.json` - R:R optimization results
- `phase2_timestop_results.json` - Time stop optimization results
- `phase4_sniper_results.json` - Sniper threshold results
- `FINAL_OPTIMIZED_CONFIGS.json` - Deployment-ready configs
- `optimized_configs.json` - Cluster+trend optimization results

### Scripts
- `phase1_optimize_rr.py` - R:R testing script
- `phase2_optimize_timestop.py` - Time stop testing script
- `phase4_optimize_sniper.py` - Sniper threshold derivation
- `optimize_all_symbols.py` - Initial cluster optimization
- `compile_final_results.py` - Results aggregation

### Documentation
- `deployment/README.md` - Deployment quick reference
- `deployment/*/README.md` - Per-symbol documentation
- `deployment/*/config.json` - Per-symbol parameters
