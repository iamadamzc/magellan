# Perturbation Testing Framework — Implementation Guide

**Status**: 🟡 Test Protocols Defined — Awaiting Implementation  
**Location**: `research/Perturbations/`  
**Created**: 2026-01-18  

---

## Overview

This directory contains the complete perturbation testing framework for 4 validated trading strategies. Each strategy has **4 focused stress tests** designed to validate robustness against real-world deployment risks.

**Testing Philosophy**: Perturb only what makes sense for each strategy's actual deployment context (no unnecessary over-testing).

---

## Directory Structure

``bash
research/Perturbations/
├── README.md                           # This file
├── daily_trend_hysteresis/             # Tests for Strategy 1
│   ├── test_parameter_robustness.py    # Test 1.1 (66 test runs)
│   ├── test_friction_sensitivity.py    # Test 1.2 (55 test runs)
│   ├── test_regime_shift.py            # Test 1.3 (33 test runs)
│   └── test_correlation_breakdown.py   # Test 1.4 (10,014 test runs)
├── hourly_swing/                       # Tests for Strategy 2
│   ├── test_gap_reversal.py            # Test 2.1 (6 test runs)
│   ├── test_execution_timing.py        # Test 2.2 (12 test runs)
│   ├── test_friction_extreme.py        # Test 2.3 (12 test runs)
│   └── test_single_asset_failure.py    # Test 2.4 (6 test runs)
├── fomc_straddles/                     # Tests for Strategy 3
│   ├── test_timing_window.py           # Test 3.1 (56 test runs)
│   ├── test_bid_ask_spread.py          # Test 3.2 (40 test runs)
│   ├── test_iv_crush.py                # Test 3.3 (32 test runs)
│   └── test_execution_failure.py       # Test 3.4 (Risk scenario analysis)
├── earnings_straddles/                 # Tests for Strategy 4
│   ├── test_ticker_robustness.py       # Test 4.1 (13 test runs)
│   ├── test_entry_timing.py            # Test 4.2 (11 test runs)
│   ├── test_iv_crush_severity.py       # Test 4.3 (12 test runs)
│   └── test_regime_normalization.py    # Test 4.4 (21 test runs)
└── reports/                            # Test documentation and results
    ├── daily_trend_hysteresis_perturbation_report.md   ✅
    ├── hourly_swing_perturbation_report.md             ✅
    ├── fomc_straddles_perturbation_report.md           ✅
    ├── earnings_straddles_perturbation_report.md       ✅
    ├── master_perturbation_summary.md                  ✅
    └── test_results/                   # CSV outputs will go here
        ├── test_1_1_parameter_robustness_results.csv
        ├── test_1_2_friction_sensitivity_results.csv
        └── ... (all test results)
```

---

## Implementation Status

### Reports (Complete ✅)
- [ ] All 5 reports created with detailed test specifications
- [x] Implementation plan and pass criteria documented
- [x] Committed to `perturbation-testing-analysis` branch

### Test Scripts (Pending 🟡)
- [ ] 0/16 test scripts implemented

**Why not implemented?**: Test scripts require integration with Magellan's existing backtest infrastructure. The reports contain complete specifications — you can implement the scripts to match your existing code patterns.

---

## Magellan Code Patterns (For Implementation)

Based on analysis of your existing codebase, here's how to structure the test scripts:

### 1. Imports Pattern
```python
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# Magellan imports
from src.data_cache import cache
from src.data_handler import AlpacaDataClient  # For options
from src.options.features import OptionsFeatureEngineer  # For options greeks
```

### 2. Data Fetching Pattern
```python
# For equities (daily/hourly)
df = cache.get_or_fetch_equity(symbol, '1day', start_date, end_date)
df_hourly = cache.get_or_fetch_equity(symbol, '1hour', start_date, end_date)

# For options pricing (earnings/FOMC)
alpaca = AlpacaDataClient()
price_df = alpaca.fetch_historical_bars('SPY', '1Day', '2020-01-01', '2025-12-31')
```

### 3. Strategy Logic Pattern
```python
def run_backtest(symbol, config, start_date, end_date):
    """Run backtest with given parameters"""
    
    # 1. Fetch data
    df = cache.get_or_fetch_equity(symbol, '1day', start_date, end_date)
    
    # 2. Calculate indicators
    df['rsi'] = calculate_rsi(df['close'], period=config['rsi_period'])
    
    # 3. Generate signals
    df['signal'] = generate_signals(df, config)
    
    # 4. Calculate returns
    df['returns'] = df['close'].pct_change()
    df['strategy_returns'] = df['signal'].shift(1) * df['returns']
    
    # 5. Apply friction
    trades = (df['signal'].diff() != 0).sum()
    friction_cost = trades * config['friction_bps'] / 10000
    
    # 6. Calculate metrics
    total_return = (1 + df['strategy_returns']).prod() - 1 - friction_cost
    sharpe = (df['strategy_returns'].mean() / df['strategy_returns'].std()) * np.sqrt(252)
    
    return {
        'return': total_return * 100,
        'sharpe': sharpe,
        'trades': trades,
        # ... other metrics
    }
```

### 4. Results Saving Pattern
```python
# Save to CSV
results_df = pd.DataFrame(all_results)
output_path = Path('research/Perturbations/reports/test_results/test_1_1_results.csv')
output_path.parent.mkdir(parents=True, exist_ok=True)
results_df.to_csv(output_path, index=False)
```

---

## Quick Start Guide

### Option 1: Implement All Tests Systematically

1. **Read the detailed report** for each strategy:
   - `reports/daily_trend_hysteresis_perturbation_report.md`
   - `reports/hourly_swing_perturbation_report.md`
   - `reports/fomc_straddles_perturbation_report.md`
   - `reports/earnings_straddles_perturbation_report.md`

2. **Start with one test** (recommended: Test 1.2 - Friction Sensitivity, simplest):
   - Create `daily_trend_hysteresis/test_friction_sensitivity.py`
   - Use the Magellan code patterns above
   - Follow the test specification in the report
   - Run and verify output

3. **Iterate** through remaining 15 tests

### Option 2: Implement Critical Tests Only

Focus on the **4 critical tests** (one per strategy) that are mandatory for deployment:

1. **Test 1.2**: Daily Trend Friction Sensitivity (MUST survive 15 bps)
2. **Test 2.1**: Hourly Swing Gap Reversal (MUST be profitable with 50% gap fading)
3. **Test 3.2**: FOMC Bid-Ask Spread Stress (MUST survive 1.0% slippage)
4. **Test 4.4**: Earnings Regime Normalization (MUST survive AI boom reversal)

### Option 3: Create a Unified Test Harness

Instead of 16 separate scripts, create a single framework:

```python
# research/Perturbations/run_all_tests.py

class PerturbationTestFramework:
    def __init__(self, strategy_name):
        self.strategy = strategy_name
        self.results = []
    
    def test_parameter_robustness(self, configs):
        """Generic parameter robustness test"""
        for config in configs:
            result = self.run_backtest_with_config(config)
            self.results.append(result)
    
    def test_friction_sensitivity(self, friction_levels):
        """Generic friction sensitivity test"""
        for friction_bps in friction_levels:
            result = self.run_backtest_with_friction(friction_bps)
            self.results.append(result)
    
    # ... other generic test methods

# Usage
framework = PerturbationTestFramework('daily_trend_hysteresis')
framework.test_friction_sensitivity([2, 5, 10, 15, 20])
framework.generate_report()
```

---

## Test Execution Commands

Once implemented, run tests with:

```bash
# Individual tests
python research/Perturbations/daily_trend_hysteresis/test_friction_sensitivity.py
python research/Perturbations/hourly_swing/test_gap_reversal.py

# Batch execution (if you create a harness)
python research/Perturbations/run_all_tests.py --strategy daily_trend_hysteresis
python research/Perturbations/run_all_tests.py --all

# Fast-track critical tests only
python research/Perturbations/run_critical_tests.py
```

---

## Expected Runtime

| Strategy | Total Tests | Est. Runtime | Bottleneck |
|----------|-------------|--------------|------------|
| Daily Trend | 10,168 runs | 2-4 hours | Test 1.4 Monte Carlo (10,014 sims) |
| Hourly Swing | 36 runs | 15-30 min | 1-hour bar processing |
| FOMC Straddles | 128 runs | 30-60 min | Options pricing calculations |
| Earnings Straddles | 57 runs | 30-45 min | Historical options data |

**Total**: 4-6 hours if run sequentially; 2-3 hours if parallelized

---

## Pass/Fail Criteria Summary

Each test has specific pass criteria documented in the reports. Here's the high-level summary:

### Daily Trend Hysteresis
- **1.1 Parameter**: ≥70% neighboring configs profitable
- **1.2 Friction** ✅ CRITICAL: All assets profitable at 10 bps
- **1.3 Regime**: Max DD ≤35% in bear market simulation
- **1.4 Correlation**: No asset >40% of returns

### Hourly Swing
- **2.1 Gap Reversal** ✅ CRITICAL: Profitable with 50% gap fading
- **2.2 Timing**: <15% degradation at 30-min lag
- **2.3 Friction**: Both assets profitable at 20 bps
- **2.4 Concentration**: Combined Sharpe ≥1.0

### FOMC Straddles
- **3.1 Timing**: ≥75% win rate with ±3 min window
- **3.2 Slippage** ✅ CRITICAL: ≥75% win rate at 1.0% slippage
- **3.3 IV Crush**: ≥50% win rate with -60% IV drop
- **3.4 Execution**: Expected loss <5% per event

### Earnings Straddles
- **4.1 Ticker**: No-GOOGL Sharpe ≥1.5
- **4.2 Entry Timing**: T-1 entry degradation ≤20%
- **4.3 IV Crush**: Win rate ≥40% in severe crush
- **4.4 Regime** ✅ CRITICAL: Sharpe ≥1.0 with -50% normalization

---

## Next Steps

1. **Review**: Read this README and the 5 reports in `reports/`
2. **Decide**: Choose implementation approach (Option 1, 2, or 3 above)
3. **Implement**: Create test scripts matching Magellan code patterns
4. **Execute**: Run tests and save results to `reports/test_results/`
5. **Analyze**: Review results against pass criteria
6. **Deploy**: Make go/no-go decisions per strategy

---

## Questions?

Refer to:
- **Implementation details**: Individual strategy reports in `reports/`
- **Deployment scenarios**: `reports/master_perturbation_summary.md`
- **Code patterns**: Existing Magellan scripts in `research/new_strategy_builds/`

---

**Created**: 2026-01-18  
**Owner**: Quantitative Research Team  
**Status**: ✅ Ready for Implementation  
**Next**: Implement test scripts using Magellan patterns
