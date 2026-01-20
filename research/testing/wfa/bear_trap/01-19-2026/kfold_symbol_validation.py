"""
K-Fold Symbol Validation - Bear Trap Strategy Validation
=========================================================
Cross-validation across symbol universe using leave-one-out and leave-two-out approaches.

Test Suite: Bear Trap ML Validation (01-19-2026)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime
from itertools import combinations

project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from deployable_strategies.bear_trap.bear_trap_strategy import run_bear_trap

# Configuration
CORE_SYMBOLS = ['MULN', 'ONDS', 'NKLA', 'ACB', 'AMC', 'GOEV', 'SENS', 'BTCS', 'WKHS']
NEW_TEST_SYMBOLS = ['RIOT', 'MARA', 'CLSK', 'SNDL', 'PLUG']  # Universe expansion test
TEST_START = '2022-01-01'
TEST_END = '2025-01-01'
INITIAL_CAPITAL = 100000

# Pass/Fail Criteria
CRITERIA = {
    'loocv_positive_folds': 8,            # ≥8 of 9 LOOCV folds positive
    'max_single_symbol_pnl_pct': 40.0,    # No symbol > 40% of total PnL
    'new_symbol_edge_min': 3,             # Edge generalizes to ≥3 of 5 new symbols
}


class KFoldSymbolValidator:
    def __init__(self):
        self.symbol_results = {}
        self.loocv_results = []
        self.ltocv_results = []
        self.expansion_results = []
        
    def run_backtest(self, symbol):
        """Run backtest for a symbol."""
        try:
            result = run_bear_trap(symbol, TEST_START, TEST_END, INITIAL_CAPITAL)
            return result
        except Exception as e:
            print(f"Error: {symbol} - {e}")
            return None
    
    def collect_baseline_results(self, symbols):
        """Collect baseline results for all symbols."""
        print("\n" + "="*60)
        print("Collecting Baseline Results")
        print("="*60)
        
        for symbol in symbols:
            result = self.run_backtest(symbol)
            if result:
                self.symbol_results[symbol] = result
                pnl = result.get('total_pnl_pct', 0)
                trades = result.get('total_trades', 0)
                print(f"  {symbol}: {pnl:+.2f}% ({trades} trades)")
    
    def run_leave_one_out_cv(self):
        """Leave-one-out cross-validation across symbols."""
        print("\n" + "="*60)
        print("Test 1: Leave-One-Out Cross-Validation (9 folds)")
        print("="*60)
        
        total_pnl = sum(r.get('total_pnl_pct', 0) for r in self.symbol_results.values())
        
        for holdout_symbol in CORE_SYMBOLS:
            # Calculate PnL with holdout symbol excluded
            fold_pnl = sum(
                r.get('total_pnl_pct', 0) 
                for s, r in self.symbol_results.items() 
                if s != holdout_symbol
            )
            
            holdout_pnl = self.symbol_results.get(holdout_symbol, {}).get('total_pnl_pct', 0)
            
            fold_result = {
                'holdout': holdout_symbol,
                'fold_pnl': fold_pnl,
                'holdout_pnl': holdout_pnl,
                'positive': fold_pnl > 0
            }
            
            self.loocv_results.append(fold_result)
            
            status = "✅" if fold_pnl > 0 else "❌"
            print(f"  Fold (holdout={holdout_symbol}): {fold_pnl:+.2f}% {status}")
        
        # Summary
        positive_folds = sum(1 for r in self.loocv_results if r['positive'])
        loocv_pass = positive_folds >= CRITERIA['loocv_positive_folds']
        
        print(f"\n  Positive Folds: {positive_folds}/9 {'✅' if loocv_pass else '❌'}")
        
        return loocv_pass
    
    def run_leave_two_out_cv(self, n_iterations=10):
        """Leave-two-out cross-validation with random pairs."""
        print("\n" + "="*60)
        print(f"Test 2: Leave-Two-Out Cross-Validation ({n_iterations} iterations)")
        print("="*60)
        
        # Generate random holdout pairs
        all_pairs = list(combinations(CORE_SYMBOLS, 2))
        np.random.shuffle(all_pairs)
        selected_pairs = all_pairs[:n_iterations]
        
        for pair in selected_pairs:
            fold_pnl = sum(
                r.get('total_pnl_pct', 0)
                for s, r in self.symbol_results.items()
                if s not in pair
            )
            
            holdout_pnl = sum(
                self.symbol_results.get(s, {}).get('total_pnl_pct', 0)
                for s in pair
            )
            
            fold_result = {
                'holdout_pair': pair,
                'fold_pnl': fold_pnl,
                'holdout_pnl': holdout_pnl,
                'positive': fold_pnl > 0
            }
            
            self.ltocv_results.append(fold_result)
            
            status = "✅" if fold_pnl > 0 else "❌"
            print(f"  Holdout ({pair[0]}, {pair[1]}): {fold_pnl:+.2f}% {status}")
        
        positive_folds = sum(1 for r in self.ltocv_results if r['positive'])
        ltocv_pass = positive_folds >= n_iterations * 0.8
        
        print(f"\n  Positive Folds: {positive_folds}/{n_iterations} {'✅' if ltocv_pass else '❌'}")
        
        return ltocv_pass
    
    def analyze_symbol_dependency(self):
        """Analyze if any single symbol drives total performance."""
        print("\n" + "="*60)
        print("Test 3: Symbol Dependency Analysis")
        print("="*60)
        
        total_pnl = sum(r.get('total_pnl_pct', 0) for r in self.symbol_results.values())
        
        symbol_contributions = []
        for symbol, result in self.symbol_results.items():
            pnl = result.get('total_pnl_pct', 0)
            contribution = (pnl / total_pnl * 100) if total_pnl > 0 else 0
            
            symbol_contributions.append({
                'symbol': symbol,
                'pnl': pnl,
                'contribution_pct': contribution
            })
            
            flag = "⚠️" if contribution > CRITERIA['max_single_symbol_pnl_pct'] else ""
            print(f"  {symbol}: {pnl:+.2f}% ({contribution:.1f}% of total) {flag}")
        
        # Check if any symbol dominates
        max_contribution = max(c['contribution_pct'] for c in symbol_contributions)
        no_dominant_symbol = max_contribution <= CRITERIA['max_single_symbol_pnl_pct']
        
        print(f"\n  Max Single Symbol Contribution: {max_contribution:.1f}%")
        print(f"  No Dominant Symbol: {'Yes ✅' if no_dominant_symbol else 'No ⚠️'}")
        
        return no_dominant_symbol, symbol_contributions
    
    def test_universe_expansion(self):
        """Test if strategy edge generalizes to new symbols."""
        print("\n" + "="*60)
        print("Test 4: Universe Expansion (5 new symbols)")
        print("="*60)
        
        profitable_new = 0
        
        for symbol in NEW_TEST_SYMBOLS:
            result = self.run_backtest(symbol)
            
            if result:
                pnl = result.get('total_pnl_pct', 0)
                trades = result.get('total_trades', 0)
                profitable = pnl > 0
                
                if profitable:
                    profitable_new += 1
                
                self.expansion_results.append({
                    'symbol': symbol,
                    'pnl': pnl,
                    'trades': trades,
                    'profitable': profitable
                })
                
                status = "✅" if profitable else "❌"
                print(f"  {symbol}: {pnl:+.2f}% ({trades} trades) {status}")
            else:
                self.expansion_results.append({
                    'symbol': symbol,
                    'pnl': 0,
                    'trades': 0,
                    'profitable': False
                })
                print(f"  {symbol}: No data ⚠️")
        
        expansion_pass = profitable_new >= CRITERIA['new_symbol_edge_min']
        
        print(f"\n  Profitable New Symbols: {profitable_new}/5 {'✅' if expansion_pass else '❌'}")
        
        return expansion_pass
    
    def run_all_tests(self):
        """Run complete cross-validation suite."""
        print("\n" + "="*80)
        print("K-FOLD SYMBOL VALIDATION - BEAR TRAP VALIDATION")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Collect baseline
        self.collect_baseline_results(CORE_SYMBOLS)
        
        # Run tests
        loocv_pass = self.run_leave_one_out_cv()
        ltocv_pass = self.run_leave_two_out_cv()
        no_dominant, contributions = self.analyze_symbol_dependency()
        expansion_pass = self.test_universe_expansion()
        
        return {
            'loocv': loocv_pass,
            'ltocv': ltocv_pass,
            'no_dominant_symbol': no_dominant,
            'expansion': expansion_pass,
            'contributions': contributions
        }
    
    def generate_report(self, output_dir):
        """Generate markdown report."""
        total_tests = 4
        passed = sum([
            len([r for r in self.loocv_results if r['positive']]) >= CRITERIA['loocv_positive_folds'],
            len([r for r in self.ltocv_results if r['positive']]) >= len(self.ltocv_results) * 0.8,
            max(c['contribution_pct'] for symbol, result in self.symbol_results.items() 
                for c in [{'contribution_pct': result.get('total_pnl_pct', 0) / sum(r.get('total_pnl_pct', 0) for r in self.symbol_results.values()) * 100 if sum(r.get('total_pnl_pct', 0) for r in self.symbol_results.values()) > 0 else 0}]) <= CRITERIA['max_single_symbol_pnl_pct'] if self.symbol_results else True,
            sum(1 for r in self.expansion_results if r['profitable']) >= CRITERIA['new_symbol_edge_min']
        ])
        
        report = f"""# K-Fold Cross-Validation Report - Bear Trap Strategy

**Date:** {datetime.now().strftime('%Y-%m-%d')}  
**Test Period:** {TEST_START} to {TEST_END}

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Core Symbols** | {len(CORE_SYMBOLS)} |
| **New Test Symbols** | {len(NEW_TEST_SYMBOLS)} |
| **Overall Status** | {'✅ PASS' if passed >= 3 else '⚠️ PARTIAL' if passed >= 2 else '❌ FAIL'} |

---

## Test 1: Leave-One-Out Cross-Validation

**Objective:** Verify strategy remains profitable when each symbol is excluded.

| Holdout Symbol | Fold PnL | Status |
|----------------|----------|--------|
"""
        for r in self.loocv_results:
            status = "✅ PASS" if r['positive'] else "❌ FAIL"
            report += f"| {r['holdout']} | {r['fold_pnl']:+.2f}% | {status} |\n"
        
        positive_loocv = sum(1 for r in self.loocv_results if r['positive'])
        report += f"""
**Positive Folds:** {positive_loocv}/9  
**Status:** {'✅ PASS' if positive_loocv >= CRITERIA['loocv_positive_folds'] else '❌ FAIL'}

---

## Test 2: Leave-Two-Out Cross-Validation

**Objective:** Verify robustness when pairs of symbols are excluded.

| Holdout Pair | Fold PnL | Status |
|--------------|----------|--------|
"""
        for r in self.ltocv_results:
            status = "✅" if r['positive'] else "❌"
            report += f"| {r['holdout_pair'][0]}, {r['holdout_pair'][1]} | {r['fold_pnl']:+.2f}% | {status} |\n"
        
        positive_ltocv = sum(1 for r in self.ltocv_results if r['positive'])
        report += f"""
**Positive Folds:** {positive_ltocv}/{len(self.ltocv_results)}

---

## Test 3: Symbol Dependency

**Objective:** No single symbol should drive > {CRITERIA['max_single_symbol_pnl_pct']:.0f}% of total PnL.

| Symbol | PnL | Contribution |
|--------|-----|--------------|
"""
        total_pnl = sum(r.get('total_pnl_pct', 0) for r in self.symbol_results.values())
        for symbol, result in sorted(self.symbol_results.items(), key=lambda x: x[1].get('total_pnl_pct', 0), reverse=True):
            pnl = result.get('total_pnl_pct', 0)
            contribution = (pnl / total_pnl * 100) if total_pnl > 0 else 0
            flag = "⚠️" if contribution > CRITERIA['max_single_symbol_pnl_pct'] else ""
            report += f"| {symbol} | {pnl:+.2f}% | {contribution:.1f}% {flag} |\n"

        report += f"""
---

## Test 4: Universe Expansion

**Objective:** Edge should generalize to ≥{CRITERIA['new_symbol_edge_min']} of 5 new similar symbols.

| Symbol | PnL | Trades | Status |
|--------|-----|--------|--------|
"""
        for r in self.expansion_results:
            status = "✅ Profitable" if r['profitable'] else "❌ Unprofitable"
            report += f"| {r['symbol']} | {r['pnl']:+.2f}% | {r['trades']} | {status} |\n"
        
        profitable_new = sum(1 for r in self.expansion_results if r['profitable'])
        report += f"""
**Profitable New Symbols:** {profitable_new}/5  
**Status:** {'✅ PASS' if profitable_new >= CRITERIA['new_symbol_edge_min'] else '❌ FAIL'}

---

## Conclusion

{'The Bear Trap strategy shows robust cross-validated performance across the symbol universe.' if passed >= 3 else 'The strategy shows some concentration risk or limited generalization.'}

**Recommendation:** {'✅ Symbol universe validated' if passed >= 3 else '⚠️ Consider diversification adjustments'}
"""
        
        # Save results CSV
        df_loocv = pd.DataFrame(self.loocv_results)
        csv_path = output_dir / 'kfold_results.csv'
        df_loocv.to_csv(csv_path, index=False)
        
        report_path = output_dir / 'CROSS_VALIDATION_REPORT.md'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📝 Report saved to: {report_path}")


def main():
    """Run K-fold validation suite."""
    output_dir = Path(__file__).parent
    
    validator = KFoldSymbolValidator()
    results = validator.run_all_tests()
    validator.generate_report(output_dir)
    
    print("\n" + "="*80)
    print("K-FOLD VALIDATION COMPLETE")
    print("="*80)
    
    passed = sum([
        results['loocv'],
        results['ltocv'],
        results['no_dominant_symbol'],
        results['expansion']
    ])
    
    print(f"\nTests Passed: {passed}/4")
    print(f"\nOverall Status: {'✅ PASS' if passed >= 3 else '❌ FAIL'}")
    
    return passed >= 3


if __name__ == '__main__':
    main()
