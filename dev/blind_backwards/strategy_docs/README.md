# Volatility Expansion Entry Strategy - Documentation Index

**Location**: `/test/blind_backwards/strategy_docs/`  
**Created**: January 25, 2026  
**Strategy Version**: 2.0 (Sanitized)

---

## Strategy Documents

### 1. [FINAL_REPORT.md](FINAL_REPORT.md)
**Comprehensive analysis report covering all 5 phases**

Contents:
- Executive Summary
- Phase-by-phase methodology and results
- VIX regime stress test results
- Refactored entry logic (v2.0)
- Mathematical formulation
- Implementation roadmap

### 2. [RESULTS.md](RESULTS.md)
**Strategy specification and performance metrics**

Contents:
- Boolean entry logic
- Exit rules (target/stop/time)
- Performance metrics by symbol
- Feature engineering details
- Cluster analysis summary

### 3. [regime_stress_test.py](regime_stress_test.py)
**Phase 5 validation script**

Features:
- Refactored entry conditions (v2.0)
- VIX regime partitioning
- Statistical validation
- Go/No-Go recommendation logic

### 4. [FINAL_STRATEGY_RESULTS.json](FINAL_STRATEGY_RESULTS.json)
**Performance metrics in JSON format**

Data:
- Hit rates by symbol
- Edge ratios
- Expectancy calculations
- Feature profiles for each hidden state

### 5. [REGIME_STRESS_TEST_RESULTS.json](REGIME_STRESS_TEST_RESULTS.json)
**VIX regime analysis results**

Data:
- Performance by regime (Complacency/Normal/Panic)
- Refactored logic specifications
- Final recommendation with rationale

---

## Quick Reference

### Strategy Summary

| Metric | SPY | QQQ | IWM |
|--------|-----|-----|-----|
| **Hit Rate** | 57.9% | 57.0% | 55.0% |
| **Expectancy** | 0.368R | 0.355R | 0.326R |
| **Edge Ratio** | 2.00 | 2.00 | 2.00 |

### Entry Conditions (v2.0)

```python
entry_signal = all([
    effort_result_zscore < -0.5,      # Dynamic z-score
    range_ratio_mean > 1.4,           # Safe calculation
    volatility_ratio_mean > 1.0,      # Vol expansion
    trade_intensity_mean > 0.9,       # Normal liquidity
    body_position_mean > 0.25         # Bullish structure
])
```

### VIX Regime Performance (SPY)

| Regime | Hit Rate | Expectancy |
|--------|----------|------------|
| COMPLACENCY (< 15) | 60.9% | 0.413R |
| NORMAL (15-25) | 56.9% | 0.353R |
| PANIC (> 25) | 46.0% | 0.190R |

---

## Recommendation

✅ **GO** - Strategy approved for paper trading validation

**Rationale**: Positive expectancy across all VIX regimes with best performance in low-volatility environments.

---

## Next Steps

1. Deploy v2.0 logic in paper trading
2. 30-day validation period
3. Walk-forward test on 2025 data
4. Monitor regime-specific performance

---

**Data Coverage**: 2.46M 1-minute bars (2022-2026)  
**Symbols**: SPY, QQQ, IWM  
**Methodology**: 5-Phase Blind Backwards Analysis
