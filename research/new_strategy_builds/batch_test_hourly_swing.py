"""
Batch Test Runner for Hourly Swing Regime Sentiment Filter Strategy
---------------------------------------------------------------------
Tests the salvaged Hourly Swing strategy with protective filters across MAG7.

Original Hourly Swing (RSI only):
- NVDA: +52% (worked)
- TSLA: -18% (failed)
- Most others: negative

New Hourly Swing Regime Sentiment (RSI + Regime + Sentiment):
- Hypothesis: Protective filters improve success rate
- Target: 70%+ success rate in bear market, Sharpe > 0.5
"""

import pandas as pd
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from strategies.hourly_swing_regime_sentiment import run_backtest
from src.data_cache import cache

# Define test universe (MAG7 + high volatility assets)
EQUITIES = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'META', 'AMZN', 'TSLA', 'NFLX', 'AMD', 'COIN', 'PLTR']

# Test periods
PERIODS = [
    ('Primary', '2024-01-01', '2025-12-31'),    # Bull market
    ('Secondary', '2022-01-01', '2023-12-31'),  # Bear market
]

def main():
    print("="*80)
    print("HOURLY SWING REGIME SENTIMENT FILTER - BATCH TEST")
    print("="*80)
    print(f"Testing {len(EQUITIES)} equities")
    print(f"Across {len(PERIODS)} periods (2022-2025)")
    print("="*80)
    
    # Pre-fetch SPY data once for all tests
    print("\nPre-fetching SPY regime data...")
    for period_name, start, end in PERIODS:
        try:
            # Fetch both hourly and daily for SPY
            cache.get_or_fetch_equity('SPY', '1day', start, end)
            print(f"✓ SPY Daily {period_name}")
        except Exception as e:
            print(f"✗ SPY {period_name}: {e}")
    print()
    
    all_results = []
    
    # Test equities
    for symbol in EQUITIES:
        for period_name, start, end in PERIODS:
            try:
                result = run_backtest(symbol, period_name, start, end)
                all_results.append(result)
            except Exception as e:
                print(f"✗ {symbol} {period_name}: ERROR - {e}")
    
    # Save results
    results_df = pd.DataFrame(all_results)
    output_path = Path('research/new_strategy_builds/results/hourly_swing_regime_sentiment_results.csv')
    output_path.parent.mkdir(exist_ok=True)
    results_df.to_csv(output_path, index=False)
    
    print("\n" + "="*80)
    print("BATCH TEST COMPLETE")
    print("="*80)
    print(f"Total tests: {len(all_results)}")
    print(f"Results saved to: {output_path}")
    
    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY BY PERIOD")
    print("="*80)
    
    for period_name in ['Primary', 'Secondary']:
        period_results = results_df[results_df['period'] == period_name]
        
        if len(period_results) == 0:
            continue
            
        avg_return = period_results['strategy_return'].mean()
        avg_sharpe = period_results['sharpe'].mean()
        positive_count = (period_results['strategy_return'] > 0).sum()
        total_count = len(period_results)
        
        period_label = {
            'Primary': '2024-2025 (bull)',
            'Secondary': '2022-2023 (bear)'
        }.get(period_name, period_name)
        
        print(f"\n{period_name} ({period_label})")
        print(f"  Avg Return: {avg_return:+.2f}%")
        print(f"  Avg Sharpe: {avg_sharpe:.2f}")
        print(f"  Positive: {positive_count}/{total_count} ({positive_count/total_count*100:.1f}%)")
        
        # Top performers
        top_3 = period_results.nlargest(3, 'strategy_return')[['symbol', 'strategy_return', 'sharpe']]
        print(f"\n  Top 3:")
        for _, row in top_3.iterrows():
            print(f"    {row['symbol']:6} {row['strategy_return']:+.2f}% | Sharpe {row['sharpe']:.2f}")
    
    # Comparison with original Hourly Swing
    print("\n" + "="*80)
    print("COMPARISON: Original vs Regime Sentiment")
    print("="*80)
    print("\nOriginal Hourly Swing (RSI only):")
    print("  NVDA: +52% (worked)")
    print("  TSLA: -18% (failed)")
    print("  Most others: negative")
    
    print("\nNew Hourly Swing Regime Sentiment:")
    nvda_results = results_df[results_df['symbol'] == 'NVDA']
    tsla_results = results_df[results_df['symbol'] == 'TSLA']
    
    if len(nvda_results) > 0:
        nvda_primary = nvda_results[nvda_results['period'] == 'Primary']['strategy_return'].values[0]
        nvda_secondary = nvda_results[nvda_results['period'] == 'Secondary']['strategy_return'].values[0]
        print(f"  NVDA: {nvda_primary:+.2f}% (Primary), {nvda_secondary:+.2f}% (Secondary)")
    
    if len(tsla_results) > 0:
        tsla_primary = tsla_results[tsla_results['period'] == 'Primary']['strategy_return'].values[0]
        tsla_secondary = tsla_results[tsla_results['period'] == 'Secondary']['strategy_return'].values[0]
        print(f"  TSLA: {tsla_primary:+.2f}% (Primary), {tsla_secondary:+.2f}% (Secondary)")
    
    # Success criteria check
    print("\n" + "="*80)
    print("SUCCESS CRITERIA CHECK")
    print("="*80)
    
    secondary_results = results_df[results_df['period'] == 'Secondary']
    if len(secondary_results) > 0:
        success_rate = (secondary_results['strategy_return'] > 0).sum() / len(secondary_results) * 100
        avg_sharpe = secondary_results['sharpe'].mean()
        
        print(f"\nBear Market (Secondary) Performance:")
        print(f"  Success Rate: {success_rate:.1f}% (Target: 70%+)")
        print(f"  Avg Sharpe: {avg_sharpe:.2f} (Target: 0.5+)")
        
        if success_rate >= 70 and avg_sharpe >= 0.5:
            print("\n✅ SUCCESS: Strategy meets deployment criteria!")
        elif success_rate >= 70:
            print("\n⚠️ PARTIAL: Success rate met, but Sharpe below target")
        elif avg_sharpe >= 0.5:
            print("\n⚠️ PARTIAL: Sharpe met, but success rate below target")
        else:
            print("\n❌ FAILED: Strategy does not meet deployment criteria")

if __name__ == '__main__':
    main()
