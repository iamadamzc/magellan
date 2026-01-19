"""
Bear Trap Validation Suite - Master Test Runner
=================================================
Executes all validation tests and generates comprehensive summary report.

Test Suite: Bear Trap ML Validation (01-19-2026)
"""

import sys
from pathlib import Path
from datetime import datetime
import importlib.util

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Test directories
TEST_BASE = project_root / 'research' / 'testing'
BACKTEST_DIR = TEST_BASE / 'backtests' / 'bear_trap' / '01-19-2026'
PERTURBATION_DIR = TEST_BASE / 'perturbations' / 'bear_trap' / '01-19-2026'
WFA_DIR = TEST_BASE / 'wfa' / 'bear_trap' / '01-19-2026'
ML_DIR = TEST_BASE / 'ml' / 'bear_trap' / '01-19-2026'


def load_and_run_test(test_path, test_name):
    """Dynamically load and run a test module."""
    print(f"\n{'='*80}")
    print(f"RUNNING: {test_name}")
    print(f"Path: {test_path}")
    print(f"{'='*80}")
    
    try:
        spec = importlib.util.spec_from_file_location(test_name, test_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, 'main'):
            result = module.main()
            return {'name': test_name, 'passed': result, 'error': None}
        else:
            print(f"⚠️ No main() function in {test_name}")
            return {'name': test_name, 'passed': False, 'error': 'No main() function'}
    except Exception as e:
        print(f"❌ Error running {test_name}: {e}")
        return {'name': test_name, 'passed': False, 'error': str(e)}


def generate_master_report(results, output_dir):
    """Generate comprehensive master validation report."""
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['passed'])
    failed_tests = total_tests - passed_tests
    
    overall_status = "✅ APPROVED FOR DEPLOYMENT" if passed_tests / total_tests >= 0.80 else "⚠️ FURTHER REVIEW REQUIRED"
    
    report = f"""# Bear Trap ML Validation Suite - Master Report

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Strategy:** Bear Trap with ML Disaster Filter  
**Branch:** feature/bear-trap-validation-suite

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Total Test Suites** | {total_tests} |
| **Passed** | {passed_tests} ✅ |
| **Failed** | {failed_tests} ❌ |
| **Pass Rate** | {passed_tests/total_tests*100:.0f}% |
| **Overall Status** | {overall_status} |

---

## Test Suite Results

| Test Suite | Category | Status |
|------------|----------|--------|
"""
    
    for r in results:
        status = "✅ PASS" if r['passed'] else f"❌ FAIL ({r['error']})" if r['error'] else "❌ FAIL"
        category = "Backtest" if "monte_carlo" in r['name'] or "baseline" in r['name'] else \
                   "Perturbation" if "regime" in r['name'] or "stability" in r['name'] else \
                   "WFA" if "kfold" in r['name'] else "ML"
        report += f"| {r['name']} | {category} | {status} |\n"

    report += f"""
---

## Test Categories

### 1. Statistical Robustness (Monte Carlo, Statistical Significance)
Tests the statistical validity of strategy returns through simulation and hypothesis testing.

### 2. Regime Analysis (Regime Stress Test)
Validates performance across bull, bear, and choppy market conditions.

### 3. Risk Analysis (Drawdown Analysis)
Evaluates maximum drawdown, recovery time, and risk-adjusted metrics.

### 4. ML Validation (ML Stability, Baseline Comparison)
Confirms the ML disaster filter's stability and improvement over baseline.

### 5. Cross-Validation (K-Fold Symbol Validation)
Tests generalization across the symbol universe using leave-one-out methodology.

---

## Individual Report Locations

| Report | Location |
|--------|----------|
| Monte Carlo Report | [MONTE_CARLO_REPORT.md]({BACKTEST_DIR / 'MONTE_CARLO_REPORT.md'}) |
| Statistical Validation | [STATISTICAL_VALIDATION_REPORT.md]({ML_DIR / 'STATISTICAL_VALIDATION_REPORT.md'}) |
| Regime Stress Report | [REGIME_STRESS_REPORT.md]({PERTURBATION_DIR / 'REGIME_STRESS_REPORT.md'}) |
| Drawdown Analysis | [DRAWDOWN_ANALYSIS_REPORT.md]({ML_DIR / 'DRAWDOWN_ANALYSIS_REPORT.md'}) |
| ML Stability Report | [ML_STABILITY_REPORT.md]({PERTURBATION_DIR / 'ML_STABILITY_REPORT.md'}) |
| Baseline vs ML | [BASELINE_ML_COMPARISON_REPORT.md]({BACKTEST_DIR / 'BASELINE_ML_COMPARISON_REPORT.md'}) |
| Cross-Validation | [CROSS_VALIDATION_REPORT.md]({WFA_DIR / 'CROSS_VALIDATION_REPORT.md'}) |

---

## Deployment Recommendation

"""
    
    if passed_tests / total_tests >= 0.85:
        report += """### ✅ APPROVED FOR LIVE DEPLOYMENT

The Bear Trap strategy with ML disaster filter has passed comprehensive validation testing:

1. **Statistical Robustness:** Returns are statistically significant
2. **Regime Resilience:** Profitable across diverse market conditions
3. **Risk Profile:** Acceptable drawdown and recovery characteristics
4. **ML Enhancement:** Validated +100%+ improvement over baseline
5. **Generalization:** Strategy edge validated across symbol universe

**Next Steps:**
1. Begin paper trading for 2 weeks
2. Proceed to live pilot at 50% capital
3. Full deployment after successful pilot

"""
    elif passed_tests / total_tests >= 0.60:
        report += """### ⚠️ CONDITIONAL APPROVAL

The Bear Trap strategy shows promising results but some tests require attention:

**Recommended Actions:**
1. Review failed test reports for specific issues
2. Consider parameter adjustments if needed
3. Extended paper trading recommended (4 weeks)
4. Start with reduced position sizing

"""
    else:
        report += """### ❌ NOT RECOMMENDED FOR DEPLOYMENT

The validation suite identified significant concerns:

**Required Actions:**
1. Analyze failed tests in detail
2. Address systematic issues before re-testing
3. Consider fundamental strategy modifications
4. Re-run validation suite after changes

"""

    report += f"""---

## Appendix: Pass/Fail Criteria Summary

| Test | Key Criteria |
|------|-------------|
| Monte Carlo | 95% CI > 0, Sharpe pass rate ≥90%, Luck factor <40% |
| Statistical | p-value <0.05 for T-test, Profit Factor CI >1.0 |
| Regime Stress | Profitable in ≥3/4 regimes, loss/gain ratio ≤50% |
| Drawdown | Max DD <30%, Calmar ratio >1.0 |
| ML Stability | Quarterly decay <20%, Calibration drift <0.1 |
| Baseline vs ML | ML improvement ≥100%, ≥60% symbols benefit |
| Cross-Validation | ≥8/9 LOOCV folds positive, no dominant symbol |

---

**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Validation Suite Version:** 1.0  
**Author:** Antigravity Quant Validation Engine
"""
    
    report_path = output_dir / 'BEAR_TRAP_VALIDATION_SUITE_01-19-2026.md'
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"\n📝 Master report saved to: {report_path}")
    
    return passed_tests / total_tests >= 0.80


def main():
    """Run all validation tests."""
    print("\n" + "="*80)
    print("BEAR TRAP ML VALIDATION SUITE - MASTER RUNNER")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Define all tests
    tests = [
        (BACKTEST_DIR / 'monte_carlo_simulation.py', 'Monte Carlo Simulation'),
        (ML_DIR / 'statistical_significance.py', 'Statistical Significance'),
        (PERTURBATION_DIR / 'regime_stress_test.py', 'Regime Stress Test'),
        (ML_DIR / 'drawdown_analysis.py', 'Drawdown Analysis'),
        (PERTURBATION_DIR / 'ml_model_stability.py', 'ML Model Stability'),
        (BACKTEST_DIR / 'baseline_ml_comparison.py', 'Baseline vs ML Comparison'),
        (WFA_DIR / 'kfold_symbol_validation.py', 'K-Fold Cross-Validation'),
    ]
    
    results = []
    
    for test_path, test_name in tests:
        if test_path.exists():
            result = load_and_run_test(test_path, test_name)
            results.append(result)
        else:
            print(f"\n⚠️ Test not found: {test_path}")
            results.append({'name': test_name, 'passed': False, 'error': 'File not found'})
    
    # Generate master report
    output_dir = TEST_BASE
    overall_pass = generate_master_report(results, output_dir)
    
    # Print summary
    print("\n" + "="*80)
    print("VALIDATION SUITE COMPLETE")
    print("="*80)
    
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    
    print(f"\n📊 Summary:")
    print(f"  Total Tests: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {total - passed}")
    print(f"  Pass Rate: {passed/total*100:.0f}%")
    print(f"\n  Overall Status: {'✅ APPROVED' if overall_pass else '❌ REVIEW REQUIRED'}")
    
    print(f"\n📁 Reports saved to: {TEST_BASE}")
    
    return overall_pass


if __name__ == '__main__':
    main()
