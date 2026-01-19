"""
Parameter Sweep: Test Multiple Delta Values

Runs SPY backtest with different delta targets to find optimal configuration.

Tests:
- Delta 0.50 (ATM): Max leverage, max theta decay
- Delta 0.60 (Slightly ITM): Balanced
- Delta 0.70 (Moderately ITM): Less theta, less leverage
- Delta 0.80 (Deep ITM): Minimal theta, minimal leverage

Run: python research/backtests/options/phase2_validation/parameter_sweep_delta.py

Expected Runtime: 2-3 minutes
"""

import sys
from pathlib import Path
import pandas as pd

# Add project root
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# Import the backtest class
from research.backtests.options.phase2_validation.test_spy_baseline import SPYOptionsBacktester

def run_parameter_sweep():
    """Run backtest with multiple delta values."""
    
    print("=" * 80)
    print("DELTA PARAMETER SWEEP - SPY OPTIONS STRATEGY")
    print("=" * 80)
    print()
    
    # Base configuration
    base_config = {
        'initial_capital': 100000,
        'target_notional': 10000,
        'slippage_pct': 1.0,
        'contract_fee': 0.097,
        'rsi_period': 21,
        'rsi_buy_threshold': 58,
        'rsi_sell_threshold': 42,
        'min_dte': 45,
        'max_dte': 60,
        'roll_threshold_dte': 7
    }
    
    # Delta values to test
    delta_values = [0.50, 0.60, 0.70, 0.80]
    
    # Date range
    start_date = '2024-01-01'
    end_date = '2026-01-15'
    
    # Results storage
    results_summary = []
    
    # Run backtest for each delta
    for delta in delta_values:
        print(f"\n{'='*80}")
        print(f"TESTING DELTA = {delta:.2f}")
        print(f"{'='*80}\n")
        
        # Update config
        config = base_config.copy()
        config['target_delta'] = delta
        
        # Run backtest
        backtester = SPYOptionsBacktester(config)
        df = backtester.fetch_spy_data(start_date, end_date)
        df = backtester.calculate_signals(df)
        results = backtester.simulate_options_trading(df)
        
        # Extract metrics
        metrics = results['metrics']
        
        # Store results
        results_summary.append({
            'delta': delta,
            'total_return_pct': metrics['total_return_pct'],
            'sharpe_ratio': metrics['sharpe_ratio'],
            'max_drawdown_pct': metrics['max_drawdown_pct'],
            'spy_buy_hold_pct': metrics['spy_buy_hold_pct'],
            'outperformance_pct': metrics['outperformance_pct'],
            'num_trades': metrics['num_trades'],
            'win_rate_pct': metrics['win_rate_pct'],
            'avg_win_pct': metrics['avg_win_pct'],
            'avg_loss_pct': metrics['avg_loss_pct'],
            'final_equity': metrics['final_equity']
        })
        
        # Print summary
        print(f"\n📊 Delta {delta:.2f} Results:")
        print(f"  Return: {metrics['total_return_pct']:+.2f}%")
        print(f"  Sharpe: {metrics['sharpe_ratio']:.2f}")
        print(f"  Max DD: {metrics['max_drawdown_pct']:.2f}%")
        print(f"  Outperformance: {metrics['outperformance_pct']:+.2f}%")
        print(f"  Win Rate: {metrics['win_rate_pct']:.1f}%")
        print(f"  Trades: {metrics['num_trades']}")
    
    # Create summary DataFrame
    summary_df = pd.DataFrame(results_summary)
    
    # Print comparison table
    print("\n" + "=" * 80)
    print("PARAMETER SWEEP SUMMARY")
    print("=" * 80)
    print()
    
    print(summary_df.to_string(index=False))
    
    # Find best configuration
    print("\n" + "=" * 80)
    print("OPTIMAL CONFIGURATION")
    print("=" * 80)
    print()
    
    # Best by Sharpe
    best_sharpe_idx = summary_df['sharpe_ratio'].idxmax()
    best_sharpe = summary_df.loc[best_sharpe_idx]
    
    print(f"🏆 Best Sharpe Ratio: Delta {best_sharpe['delta']:.2f}")
    print(f"   Sharpe: {best_sharpe['sharpe_ratio']:.2f}")
    print(f"   Return: {best_sharpe['total_return_pct']:+.2f}%")
    print(f"   Max DD: {best_sharpe['max_drawdown_pct']:.2f}%")
    
    # Best by Return
    best_return_idx = summary_df['total_return_pct'].idxmax()
    best_return = summary_df.loc[best_return_idx]
    
    print(f"\n💰 Best Total Return: Delta {best_return['delta']:.2f}")
    print(f"   Return: {best_return['total_return_pct']:+.2f}%")
    print(f"   Sharpe: {best_return['sharpe_ratio']:.2f}")
    print(f"   Outperformance: {best_return['outperformance_pct']:+.2f}%")
    
    # Best risk-adjusted (Sharpe > 1.0 and highest return)
    qualified = summary_df[summary_df['sharpe_ratio'] > 1.0]
    
    if len(qualified) > 0:
        best_qualified_idx = qualified['total_return_pct'].idxmax()
        best_qualified = qualified.loc[best_qualified_idx]
        
        print(f"\n✅ Best Risk-Adjusted (Sharpe > 1.0): Delta {best_qualified['delta']:.2f}")
        print(f"   Return: {best_qualified['total_return_pct']:+.2f}%")
        print(f"   Sharpe: {best_qualified['sharpe_ratio']:.2f}")
        print(f"   Win Rate: {best_qualified['win_rate_pct']:.1f}%")
        print(f"\n🎯 RECOMMENDATION: Use Delta {best_qualified['delta']:.2f} for production")
    else:
        print(f"\n⚠️  No configuration achieved Sharpe > 1.0")
        print(f"   Best available: Delta {best_sharpe['delta']:.2f} (Sharpe {best_sharpe['sharpe_ratio']:.2f})")
        print(f"\n🔧 RECOMMENDATION: Further optimization needed")
    
    # Save results
    output_dir = Path('results/options')
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(output_dir / 'delta_parameter_sweep.csv', index=False)
    
    print(f"\n📁 Results saved to: {output_dir}/delta_parameter_sweep.csv")
    print("=" * 80)


if __name__ == "__main__":
    run_parameter_sweep()
