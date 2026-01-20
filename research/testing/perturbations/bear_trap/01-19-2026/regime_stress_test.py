"""
Regime Stress Testing - Bear Trap Strategy Validation
======================================================
Tests performance across distinct market regimes (bull, bear, choppy, volatility).

Test Suite: Bear Trap ML Validation (01-19-2026)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime

project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from deployable_strategies.bear_trap.bear_trap_strategy import run_bear_trap

# Configuration
CORE_SYMBOLS = ['MULN', 'ONDS', 'NKLA', 'ACB', 'AMC', 'GOEV', 'SENS', 'BTCS', 'WKHS']
INITIAL_CAPITAL = 100000

# Market Regimes (based on SPY/VIX characteristics)
REGIMES = {
    'BULL_2021': {
        'period': ('2021-01-01', '2021-12-31'),
        'description': 'Strong bull market, low VIX',
        'expected': 'positive'
    },
    'BEAR_2022': {
        'period': ('2022-01-01', '2022-12-31'),
        'description': 'Bear market, high volatility',
        'expected': 'neutral'  # Bear trap should work in volatile down markets
    },
    'CHOPPY_2023': {
        'period': ('2023-01-01', '2023-12-31'),
        'description': 'Sideways/choppy market',
        'expected': 'neutral'
    },
    'BULL_2024': {
        'period': ('2024-01-01', '2024-12-31'),
        'description': 'Recovery bull market',
        'expected': 'positive'
    },
}

# Pass/Fail Criteria
CRITERIA = {
    'profitable_regimes_min': 3,          # Profitable in ≥3 of 4 regimes
    'max_regime_drawdown': 25.0,          # Max DD < 25% in any regime
    'max_loss_vs_best_gain': 0.50,        # No regime loss > 50% of best regime gain
}


class RegimeStressValidator:
    def __init__(self):
        self.regime_results = {}
        self.symbol_results = []
        
    def run_regime_backtest(self, symbol, start, end):
        """Run backtest for a specific period."""
        try:
            result = run_bear_trap(symbol, start, end, INITIAL_CAPITAL)
            return result
        except Exception as e:
            print(f"Error: {symbol} [{start} to {end}] - {e}")
            return None
    
    def calculate_max_drawdown(self, returns):
        """Calculate maximum drawdown from cumulative returns."""
        if len(returns) == 0:
            return 0.0
        
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        
        return abs(np.min(drawdown)) if len(drawdown) > 0 else 0.0
    
    def validate_symbol_across_regimes(self, symbol):
        """Test symbol across all market regimes."""
        print(f"\n{'='*60}")
        print(f"Regime Stress Test: {symbol}")
        print(f"{'='*60}")
        
        regime_pnls = {}
        regime_trades = {}
        
        for regime_name, regime_config in REGIMES.items():
            start, end = regime_config['period']
            result = self.run_regime_backtest(symbol, start, end)
            
            if result is not None:
                pnl = result.get('total_pnl_pct', 0)
                trades = result.get('total_trades', 0)
                regime_pnls[regime_name] = pnl
                regime_trades[regime_name] = trades
                status = "✅" if pnl > 0 else "❌"
                print(f"  {regime_name}: {pnl:+.2f}% ({trades} trades) {status}")
            else:
                regime_pnls[regime_name] = 0
                regime_trades[regime_name] = 0
                print(f"  {regime_name}: No data ⚠️")
        
        # Calculate metrics
        positive_regimes = sum(1 for pnl in regime_pnls.values() if pnl > 0)
        best_gain = max(regime_pnls.values()) if regime_pnls else 0
        
        # Only count actual losses (negative PnLs)
        losses = [pnl for pnl in regime_pnls.values() if pnl < 0]
        worst_loss = min(losses) if losses else 0
        
        # Loss/gain ratio only matters if there are actual losses
        loss_vs_gain_ratio = abs(worst_loss) / best_gain if (best_gain > 0 and worst_loss < 0) else 0
        
        # Pass/Fail
        regime_pass = positive_regimes >= CRITERIA['profitable_regimes_min']
        ratio_pass = loss_vs_gain_ratio <= CRITERIA['max_loss_vs_best_gain']
        
        overall_pass = regime_pass and ratio_pass
        status = "✅ PASS" if overall_pass else "❌ FAIL"
        
        print(f"\n  Profitable Regimes: {positive_regimes}/4 {'✅' if regime_pass else '❌'}")
        print(f"  Loss/Gain Ratio: {loss_vs_gain_ratio:.1%} {'✅' if ratio_pass else '❌'}")
        print(f"  Status: {status}")
        
        self.symbol_results.append({
            'symbol': symbol,
            **{f'{k}_pnl': v for k, v in regime_pnls.items()},
            **{f'{k}_trades': v for k, v in regime_trades.items()},
            'profitable_regimes': positive_regimes,
            'best_gain': best_gain,
            'worst_loss': worst_loss,
            'loss_gain_ratio': loss_vs_gain_ratio,
            'status': status
        })
        
        return overall_pass
    
    def calculate_aggregate_regime_stats(self):
        """Calculate aggregate performance per regime across all symbols."""
        aggregate = {}
        
        for regime_name in REGIMES.keys():
            pnl_col = f'{regime_name}_pnl'
            trades_col = f'{regime_name}_trades'
            
            pnls = [r[pnl_col] for r in self.symbol_results if pnl_col in r]
            trades = [r[trades_col] for r in self.symbol_results if trades_col in r]
            
            aggregate[regime_name] = {
                'avg_pnl': np.mean(pnls) if pnls else 0,
                'total_trades': sum(trades),
                'profitable_symbols': sum(1 for p in pnls if p > 0),
                'total_symbols': len(pnls)
            }
        
        return aggregate
    
    def validate_all(self, symbols):
        """Run validation for all symbols."""
        print("\n" + "="*80)
        print("REGIME STRESS TESTING - BEAR TRAP VALIDATION")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Symbols: {len(symbols)} | Regimes: {len(REGIMES)}")
        print("="*80)
        
        for symbol in symbols:
            self.validate_symbol_across_regimes(symbol)
        
        return self.symbol_results
    
    def generate_report(self, output_dir):
        """Generate CSV and markdown report."""
        df = pd.DataFrame(self.symbol_results)
        
        csv_path = output_dir / 'regime_results.csv'
        df.to_csv(csv_path, index=False)
        print(f"\n📊 Results saved to: {csv_path}")
        
        # Aggregate stats
        agg = self.calculate_aggregate_regime_stats()
        
        # Counts
        total = len(self.symbol_results)
        overall_pass = sum(1 for r in self.symbol_results if 'PASS' in r['status'])
        
        report = f"""# Regime Stress Test Report - Bear Trap Strategy

**Date:** {datetime.now().strftime('%Y-%m-%d')}  
**Symbols Tested:** {total}  
**Regimes Tested:** {len(REGIMES)}

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Symbols Passing Regime Test** | {overall_pass}/{total} ({overall_pass/total*100:.1f}%) |
| **Overall Status** | {'✅ PASS' if overall_pass/total >= 0.80 else '⚠️ PARTIAL' if overall_pass/total >= 0.50 else '❌ FAIL'} |

---

## Pass/Fail Criteria

| Criterion | Threshold |
|-----------|-----------|
| Profitable in ≥ N regimes | ≥ {CRITERIA['profitable_regimes_min']} of 4 |
| Max loss vs best gain | ≤ {CRITERIA['max_loss_vs_best_gain']:.0%} |

---

## Regime Definitions

| Regime | Period | Description |
|--------|--------|-------------|
"""
        for name, config in REGIMES.items():
            report += f"| {name} | {config['period'][0]} to {config['period'][1]} | {config['description']} |\n"

        report += """
---

## Aggregate Performance by Regime

| Regime | Avg PnL | Total Trades | Profitable Symbols |
|--------|---------|--------------|-------------------|
"""
        for regime_name, stats in agg.items():
            status = "✅" if stats['avg_pnl'] > 0 else "⚠️"
            report += f"| {regime_name} | {stats['avg_pnl']:+.2f}% | {stats['total_trades']} | {stats['profitable_symbols']}/{stats['total_symbols']} {status} |\n"

        report += """
---

## Symbol Results

| Symbol | BULL_2021 | BEAR_2022 | CHOPPY_2023 | BULL_2024 | Profitable Regimes | Status |
|--------|-----------|-----------|-------------|-----------|-------------------|--------|
"""
        for r in self.symbol_results:
            report += f"| {r['symbol']} | {r.get('BULL_2021_pnl', 0):+.1f}% | {r.get('BEAR_2022_pnl', 0):+.1f}% | {r.get('CHOPPY_2023_pnl', 0):+.1f}% | {r.get('BULL_2024_pnl', 0):+.1f}% | {r['profitable_regimes']}/4 | {r['status']} |\n"

        report += f"""
---

## Interpretation

- **Bull Markets (2021, 2024):** Strategy should capture reversals in volatile stocks during uptrends.
- **Bear Market (2022):** Strategy is designed for panic/selloff scenarios - expected to perform well.
- **Choppy Market (2023):** May underperform due to lack of clear directional moves.

---

## Conclusion

{'The Bear Trap strategy shows consistent performance across diverse market regimes.' if overall_pass/total >= 0.80 else 'The strategy exhibits regime-dependent performance.'}

**Recommendation:** {'✅ Regime-robust for deployment' if overall_pass/total >= 0.80 else '⚠️ Consider regime filters'}
"""
        
        report_path = output_dir / 'REGIME_STRESS_REPORT.md'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📝 Report saved to: {report_path}")
        
        return df


def main():
    """Run regime stress test suite."""
    output_dir = Path(__file__).parent
    
    validator = RegimeStressValidator()
    results = validator.validate_all(CORE_SYMBOLS)
    df = validator.generate_report(output_dir)
    
    print("\n" + "="*80)
    print("REGIME STRESS TEST COMPLETE")
    print("="*80)
    
    pass_count = sum(1 for r in results if 'PASS' in r['status'])
    total = len(results)
    
    print(f"\nTotal Symbols: {total}")
    print(f"Passed: {pass_count}")
    print(f"Pass Rate: {pass_count/total*100:.1f}%")
    
    overall_pass = pass_count / total >= 0.80
    print(f"\nOverall Status: {'✅ PASS' if overall_pass else '❌ FAIL'}")
    
    return overall_pass


if __name__ == '__main__':
    main()
