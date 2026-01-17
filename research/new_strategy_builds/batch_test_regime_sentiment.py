"""
Batch Test Runner for Regime Sentiment Filter Strategy

Tests across:
- MAG7 Equities (AAPL, MSFT, GOOGL, NVDA, META, AMZN, TSLA)
- Additional Equities (NFLX, AMD, COIN, PLTR)
- Futures (SIUSD, GCUSD, CLUSD, ESUSD, NQUSD)

Outputs results to CSV for analysis
"""

import pandas as pd
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# Import the strategy backtest function
from strategies.regime_sentiment_filter import run_backtest

# Define test universe
EQUITIES = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'META', 'AMZN', 'TSLA', 'NFLX', 'AMD', 'COIN', 'PLTR']
FUTURES = ['SIUSD', 'GCUSD', 'CLUSD', 'ESUSD', 'NQUSD']

PERIODS = [
    ('Primary', '2024-01-01', '2025-12-31'),
    ('Secondary', '2022-01-01', '2023-12-31')
]

def main():
    all_results = []
    
    print("="*80)
    print("REGIME SENTIMENT FILTER - BATCH TEST")
    print("="*80)
    print(f"Testing {len(EQUITIES)} equities + {len(FUTURES)} futures")
    print(f"Across 2 periods (2022-2023 bear, 2024-2025 bull)")
    print("="*80)
    
    # Test equities
    for symbol in EQUITIES:
        for period_name, start, end in PERIODS:
            try:
                result = run_backtest(symbol, period_name, start, end)
                result['asset_class'] = 'equity'
                all_results.append(result)
            except Exception as e:
                print(f"✗ {symbol} {period_name}: ERROR - {e}")
    
    # Test futures (no news for futures, will use sentiment=0)
    print("\n" + "="*80)
    print("TESTING FUTURES (No news sentiment available)")
    print("="*80)
    
    for symbol in FUTURES:
        for period_name, start, end in PERIODS:
            try:
                # Futures use different data source
                from src.data_cache import cache
                import numpy as np
                
                # Load futures data
                df = cache.get_or_fetch_futures(symbol, '1day', start, end)
                
                # Calculate RSI
                from strategies.regime_sentiment_filter import calculate_rsi
                df['rsi_28'] = calculate_rsi(df['close'], period=28)
                
                # No SPY regime for futures - use own 200 MA
                df['ma_200'] = df['close'].rolling(200).mean()
                df['regime'] = (df['close'] > df['ma_200']).astype(int)
                
                # No news for futures
                df['sentiment'] = 0.0
                
                # Simplified entry: RSI > 55 AND above 200 MA
                entry_condition = (df['rsi_28'] > 55) & (df['regime'] == 1)
                exit_condition = (df['rsi_28'] < 45) | (df['regime'] == 0)
                
                # State machine
                position = 0
                signals = []
                
                for i in range(len(df)):
                    if position == 0:
                        if entry_condition.iloc[i]:
                            position = 1
                    elif position == 1:
                        if exit_condition.iloc[i]:
                            position = 0
                    signals.append(position)
                
                df['signal'] = signals
                df['returns'] = df['close'].pct_change()
                df['strategy_returns'] = df['signal'].shift(1) * df['returns']
                
                # Metrics
                total_return = (1 + df['strategy_returns']).prod() - 1
                buy_hold_return = (df['close'].iloc[-1] / df['close'].iloc[0]) - 1
                sharpe = (df['strategy_returns'].mean() / df['strategy_returns'].std()) * np.sqrt(252) if df['strategy_returns'].std() > 0 else 0
                
                cum_returns = (1 + df['strategy_returns']).cumprod()
                running_max = cum_returns.expanding().max()
                drawdown = (cum_returns - running_max) / running_max
                max_dd = drawdown.min()
                
                trades = (df['signal'].diff() != 0).sum()
                winning_days = (df[df['signal'] == 1]['returns'] > 0).sum()
                total_days_in_market = (df['signal'] == 1).sum()
                win_rate = (winning_days / total_days_in_market * 100) if total_days_in_market > 0 else 0
                
                result = {
                    'symbol': symbol,
                    'period': period_name,
                    'strategy_return': total_return * 100,
                    'buy_hold_return': buy_hold_return * 100,
                    'sharpe': sharpe,
                    'max_dd': max_dd * 100,
                    'trades': trades,
                    'win_rate': win_rate,
                    'days_in_market': total_days_in_market,
                    'asset_class': 'futures'
                }
                
                all_results.append(result)
                print(f"✓ {symbol} {period_name}: {total_return*100:+.2f}% | Sharpe: {sharpe:.2f}")
                
            except Exception as e:
                print(f"✗ {symbol} {period_name}: ERROR - {e}")
    
    # Save results
    results_df = pd.DataFrame(all_results)
    output_path = Path('research/new_strategy_builds/results/regime_sentiment_filter_results.csv')
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
        
        avg_return = period_results['strategy_return'].mean()
        avg_sharpe = period_results['sharpe'].mean()
        positive_count = (period_results['strategy_return'] > 0).sum()
        total_count = len(period_results)
        
        print(f"\n{period_name} (2024-2025 bull)" if period_name == 'Primary' else f"\n{period_name} (2022-2023 bear)")
        print(f"  Avg Return: {avg_return:+.2f}%")
        print(f"  Avg Sharpe: {avg_sharpe:.2f}")
        print(f"  Positive: {positive_count}/{total_count} ({positive_count/total_count*100:.1f}%)")
        
        # Top performers
        top_3 = period_results.nlargest(3, 'strategy_return')[['symbol', 'strategy_return', 'sharpe']]
        print(f"\n  Top 3:")
        for _, row in top_3.iterrows():
            print(f"    {row['symbol']:6} {row['strategy_return']:+.2f}% | Sharpe {row['sharpe']:.2f}")

if __name__ == '__main__':
    main()
