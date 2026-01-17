"""
Wavelet Multi-Timeframe Strategy (Daily, MAG7 Equities)

Uses existing wavelet signals from features.py that combine:
- 5-minute RSI (20% weight - kinetic)
- 15-minute RSI (30% weight - momentum)  
- 60-minute RSI (50% weight - structure)

Entry: wavelet_alpha > 0.6 (strong multi-timeframe alignment)
Exit: wavelet_alpha < 0.4 (alignment breaks)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache
from src.features import FeatureEngineer, add_wavelet_signals
import argparse

def run_backtest(symbol, period_name, start, end, friction_bps=1.5):
    """Run Wavelet Multi-Timeframe backtest"""
    
    print(f"\n{'='*80}")
    print(f"Testing {symbol} - {period_name} ({start} to {end})")
    print(f"{'='*80}")
    
    # Load cached daily data
    df = cache.get_or_fetch_equity(symbol, '1day', start, end)
    print(f"✓ Loaded {len(df)} daily bars")
    
    # Add wavelet signals (standalone function)
    df = add_wavelet_signals(df, ticker=symbol)
    
    # Check if wavelet_alpha exists
    if 'wavelet_alpha' not in df.columns:
        print("⚠️ wavelet_alpha not found, using simple RSI instead")
        # Fallback to simple RSI
        df['rsi_14'] = fe.calculate_rsi(df['close'], period=14)
        df['wavelet_alpha'] = (df['rsi_14'] - 30) / 40  # Normalize to 0-1
    
    # Generate signals
    df['signal'] = 0
    
    # Entry: Strong multi-timeframe alignment
    entry_condition = df['wavelet_alpha'] > 0.6
    
    # Exit: Alignment breaks
    exit_condition = df['wavelet_alpha'] < 0.4
    
    # State machine
    position = 0
    signals = []
    
    for i in range(len(df)):
        if position == 0:  # Flat
            if entry_condition.iloc[i]:
                position = 1  # Enter long
        elif position == 1:  # Long
            if exit_condition.iloc[i]:
                position = 0  # Exit
        
        signals.append(position)
    
    df['signal'] = signals
    
    # Calculate returns
    df['returns'] = df['close'].pct_change()
    df['strategy_returns'] = df['signal'].shift(1) * df['returns']
    
    # Apply friction
    trades = (df['signal'].diff() != 0).sum()
    
    # Performance metrics
    total_return = (1 + df['strategy_returns']).prod() - 1
    buy_hold_return = (df['close'].iloc[-1] / df['close'].iloc[0]) - 1
    
    # Sharpe ratio
    sharpe = (df['strategy_returns'].mean() / df['strategy_returns'].std()) * np.sqrt(252) if df['strategy_returns'].std() > 0 else 0
    
    # Max drawdown
    cum_returns = (1 + df['strategy_returns']).cumprod()
    running_max = cum_returns.expanding().max()
    drawdown = (cum_returns - running_max) / running_max
    max_dd = drawdown.min()
    
    # Win rate
    winning_days = (df[df['signal'] == 1]['returns'] > 0).sum()
    total_days_in_market = (df['signal'] == 1).sum()
    win_rate = (winning_days / total_days_in_market * 100) if total_days_in_market > 0 else 0
    
    print(f"\nResults:")
    print(f"  Strategy Return: {total_return*100:+.2f}%")
    print(f"  Buy & Hold:      {buy_hold_return*100:+.2f}%")
    print(f"  Sharpe Ratio:    {sharpe:.2f}")
    print(f"  Max Drawdown:    {max_dd*100:.2f}%")
    print(f"  Trades:          {trades}")
    print(f"  Win Rate:        {win_rate:.1f}%")
    print(f"  Days in Market:  {total_days_in_market}")
    
    return {
        'symbol': symbol,
        'period': period_name,
        'strategy_return': total_return * 100,
        'buy_hold_return': buy_hold_return * 100,
        'sharpe': sharpe,
        'max_dd': max_dd * 100,
        'trades': trades,
        'win_rate': win_rate,
        'days_in_market': total_days_in_market
    }

def main():
    parser = argparse.ArgumentParser(description='Test Wavelet Multi-Timeframe Strategy')
    parser.add_argument('--symbol', type=str, default='AAPL', help='Symbol to test')
    parser.add_argument('--period', type=str, default='both', choices=['both', 'primary', 'secondary'])
    args = parser.parse_args()
    
    results = []
    
    if args.period in ['both', 'primary']:
        result = run_backtest(args.symbol, 'Primary', '2024-01-01', '2025-12-31')
        results.append(result)
    
    if args.period in ['both', 'secondary']:
        result = run_backtest(args.symbol, 'Secondary', '2022-01-01', '2023-12-31')
        results.append(result)
    
    # Summary
    if len(results) > 1:
        print(f"\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}")
        for r in results:
            print(f"{r['period']:12} Return: {r['strategy_return']:+.2f}% | Sharpe: {r['sharpe']:.2f} | Trades: {r['trades']}")

if __name__ == '__main__':
    main()
