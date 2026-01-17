"""
Batch Test Runner for VWAP Reclaim Strategy
--------------------------------------------
Tests VWAP Reclaim across expanded small-cap universe with relaxed parameters.

Initial test showed 0 trades with strict parameters. This version uses:
- MIN_DAY_CHANGE_PCT: 8% (down from 15%)
- FLUSH_DEV_ATR: 0.6 (down from 0.8)
- WICK_RATIO_MIN: 0.30 (down from 0.40)
- HOLD_BARS: 1 (down from 2)

Goal: Get baseline trade frequency and identify which parameters matter most.
"""

import pandas as pd
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from strategies.vwap_reclaim import run_backtest

# Test universe (start with highest volume)
TEST_SYMBOLS = [
    'RIOT',  # Crypto miner - high volume
    'MARA',  # Crypto miner - high volume
    'AMC',   # Meme stock - high RVOL
]

# Test periods
PERIODS = [
    ('Recent', '2024-11-01', '2025-01-17'),
    ('Middle', '2025-04-01', '2025-06-30'),
]

# Relaxed parameters
RELAXED_PARAMS = {
    'MIN_DAY_CHANGE_PCT': 8.0,      # Down from 15%
    'FLUSH_DEV_ATR': 0.6,            # Down from 0.8
    'WICK_RATIO_MIN': 0.30,          # Down from 0.40
    'FLUSH_VOL_MULT': 1.4,           # Down from 1.6
    'STOP_LOSS_ATR': 0.45,
    'HOLD_BARS': 1,                  # Down from 2
    'MAX_HOLD_MINUTES': 30,
    'SCALE_TP1_PCT': 0.40,
    'SCALE_TP2_PCT': 0.30,
    'MIN_DOLLAR_VOLUME': 200000,     # Down from 250K
    'MAX_SPREAD_BPS': 40,            # Up from 35
}

def main():
    print("="*80)
    print("VWAP RECLAIM STRATEGY - BATCH TEST (RELAXED PARAMETERS)")
    print("="*80)
    print(f"Testing {len(TEST_SYMBOLS)} symbols")
    print(f"Across {len(PERIODS)} periods")
    print("="*80)
    print("\nRelaxed Parameters:")
    print(f"  MIN_DAY_CHANGE_PCT: {RELAXED_PARAMS['MIN_DAY_CHANGE_PCT']}% (was 15%)")
    print(f"  FLUSH_DEV_ATR: {RELAXED_PARAMS['FLUSH_DEV_ATR']} (was 0.8)")
    print(f"  WICK_RATIO_MIN: {RELAXED_PARAMS['WICK_RATIO_MIN']} (was 0.40)")
    print(f"  HOLD_BARS: {RELAXED_PARAMS['HOLD_BARS']} (was 2)")
    print("="*80)
    
    all_results = []
    
    for symbol in TEST_SYMBOLS:
        for period_name, start, end in PERIODS:
            try:
                result = run_backtest(symbol, start, end, params=RELAXED_PARAMS)
                result['period'] = period_name
                all_results.append(result)
            except Exception as e:
                print(f"✗ {symbol} {period_name}: ERROR - {e}")
    
    # Save results
    results_df = pd.DataFrame(all_results)
    output_path = Path('research/new_strategy_builds/results/vwap_reclaim_results.csv')
    output_path.parent.mkdir(exist_ok=True)
    results_df.to_csv(output_path, index=False)
    
    print("\n" + "="*80)
    print("BATCH TEST COMPLETE")
    print("="*80)
    print(f"Total tests: {len(all_results)}")
    print(f"Results saved to: {output_path}")
    
    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if len(results_df) > 0:
        total_trades = results_df['total_trades'].sum()
        avg_trades = results_df['total_trades'].mean()
        
        print(f"\nTotal trades across all tests: {total_trades}")
        print(f"Average trades per test: {avg_trades:.1f}")
        
        # Filter tests with trades
        with_trades = results_df[results_df['total_trades'] > 0]
        
        if len(with_trades) > 0:
            print(f"\nTests with trades: {len(with_trades)}/{len(results_df)}")
            print(f"\nPerformance (tests with trades only):")
            print(f"  Avg Win Rate: {with_trades['win_rate'].mean():.1f}%")
            print(f"  Avg P&L per trade: {with_trades['avg_pnl_pct'].mean():+.2f}%")
            print(f"  Avg Sharpe: {with_trades['sharpe'].mean():.2f}")
            print(f"  Avg Hold Time: {with_trades['avg_hold_minutes'].mean():.1f} minutes")
            
            print(f"\nBest performers:")
            best = with_trades.nlargest(3, 'total_pnl_pct')[['symbol', 'period', 'total_trades', 'win_rate', 'total_pnl_pct', 'sharpe']]
            print(best.to_string(index=False))
        else:
            print("\n⚠️ NO TRADES GENERATED")
            print("Strategy is still too restrictive. Need to relax parameters further.")
    
    # Detailed results
    print("\n" + "="*80)
    print("DETAILED RESULTS")
    print("="*80)
    print(results_df[['symbol', 'period', 'total_trades', 'win_rate', 'avg_pnl_pct', 'sharpe']].to_string(index=False))

if __name__ == '__main__':
    main()
