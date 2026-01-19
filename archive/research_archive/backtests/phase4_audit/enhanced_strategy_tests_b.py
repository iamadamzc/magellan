"""
Phase 5B: Alternative Strategy Tests

Key learnings from Phase 5A:
1. Filters HURT Hysteresis (reduced Sharpe from 0.51 to 0.06)
2. SPY event straddles DON'T WORK (not enough volatility)
3. TSLA shows promise (0.60 Sharpe) - focus here

New tests:
1. TSLA/NVDA with optimized parameters
2. Mean reversion strategies (opposite of momentum)
3. Breakout strategies
4. News sentiment trading using FMP
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient, FMPDataClient
from src.features import calculate_rsi
from src.options.features import OptionsFeatureEngineer
from research.backtests.phase4_audit.wfa_core import (
    calculate_sharpe_from_trades,
    calculate_sharpe_correct,
    calculate_trade_stats,
)

print("="*80)
print("PHASE 5B: ALTERNATIVE STRATEGY TESTS")
print("="*80)

# =============================================================================
# TEST 1: OPTIMIZED TSLA TRADING (Building on 0.60 Sharpe)
# =============================================================================

def test_optimized_tsla():
    """
    Optimize TSLA strategy parameters to push 0.60 → 1.0+ Sharpe
    """
    print("\n" + "="*60)
    print("TEST 1: OPTIMIZED TSLA STRATEGY")
    print("="*60)
    
    alpaca = AlpacaDataClient()
    df = alpaca.fetch_historical_bars('TSLA', '1Day', '2020-01-01', '2025-12-31')
    print(f"  ✓ TSLA: {len(df)} bars")
    
    # Parameter grid
    param_grid = [
        {'rsi_period': 7, 'upper': 65, 'lower': 35},
        {'rsi_period': 7, 'upper': 60, 'lower': 40},
        {'rsi_period': 14, 'upper': 60, 'lower': 40},
        {'rsi_period': 14, 'upper': 65, 'lower': 35},
        {'rsi_period': 21, 'upper': 55, 'lower': 45},
    ]
    
    results = {}
    
    for params in param_grid:
        config_name = f"RSI{params['rsi_period']}_{params['upper']}/{params['lower']}"
        
        df_test = df.copy()
        df_test['rsi'] = calculate_rsi(df_test['close'], period=params['rsi_period'])
        df_test['ma_50'] = df_test['close'].rolling(50).mean()
        
        cash = 100000
        shares = 0
        position = 'flat'
        trades = []
        equity = [100000]
        entry_price = entry_date = None
        
        for date, row in df_test.iterrows():
            price = row['close']
            rsi = row['rsi']
            ma_50 = row['ma_50']
            
            if pd.isna(rsi) or pd.isna(ma_50):
                equity.append(cash + shares * price)
                continue
            
            # Entry with trend confirmation
            if position == 'flat' and rsi > params['upper'] and price > ma_50:
                shares = int(cash / (price * 1.0003))
                if shares > 0:
                    cash -= shares * price * 1.0003
                    position = 'long'
                    entry_price = price
                    entry_date = date
            
            # Exit
            elif position == 'long' and rsi < params['lower']:
                proceeds = shares * price * 0.9997
                pnl_pct = (price / entry_price - 1) * 100
                trades.append({'pnl_pct': pnl_pct, 'hold_days': max((date - entry_date).days, 1)})
                cash += proceeds
                shares = 0
                position = 'flat'
            
            equity.append(cash + shares * price)
        
        if shares > 0:
            cash += shares * df_test.iloc[-1]['close'] * 0.9997
        
        if len(trades) >= 10:
            returns = pd.Series(equity).pct_change().dropna().values
            sharpe = calculate_sharpe_correct(returns, min_samples=50)
            stats = calculate_trade_stats(pd.DataFrame(trades))
            
            results[config_name] = {
                'sharpe': float(sharpe) if sharpe else 0.0,
                'trades': len(trades),
                'win_rate': stats['win_rate'],
                'avg_pnl': stats['avg_pnl']
            }
    
    print("\n  RESULTS:")
    print(f"  {'Config':<25} {'Sharpe':<10} {'Trades':<10} {'Win Rate':<12}")
    print(f"  {'-'*55}")
    for config, r in sorted(results.items(), key=lambda x: -x[1].get('sharpe', 0)):
        verdict = "✅" if r['sharpe'] >= 1.0 else ("⚠️" if r['sharpe'] >= 0.5 else "❌")
        print(f"  {config:<25} {r['sharpe']:.2f}       {r['trades']:<10} {r['win_rate']:.1f}%       {verdict}")
    
    return results


# =============================================================================
# TEST 2: MEAN REVERSION (Opposite of Momentum)
# =============================================================================

def test_mean_reversion():
    """
    Test mean reversion: buy oversold, sell overbought
    """
    print("\n" + "="*60)
    print("TEST 2: MEAN REVERSION STRATEGY")
    print("="*60)
    
    alpaca = AlpacaDataClient()
    symbols = ['NVDA', 'TSLA', 'AMD', 'META']
    
    results = {}
    
    for symbol in symbols:
        df = alpaca.fetch_historical_bars(symbol, '1Day', '2020-01-01', '2025-12-31')
        df['rsi'] = calculate_rsi(df['close'], period=7)  # Short RSI for mean reversion
        df['bb_middle'] = df['close'].rolling(20).mean()
        df['bb_std'] = df['close'].rolling(20).std()
        df['bb_lower'] = df['bb_middle'] - 2 * df['bb_std']
        df['bb_upper'] = df['bb_middle'] + 2 * df['bb_std']
        
        cash = 100000
        shares = 0
        position = 'flat'
        trades = []
        equity = [100000]
        entry_price = entry_date = None
        
        for date, row in df.iterrows():
            price = row['close']
            rsi = row['rsi']
            bb_lower = row['bb_lower']
            bb_middle = row['bb_middle']
            
            if pd.isna(rsi) or pd.isna(bb_lower):
                equity.append(cash + shares * price)
                continue
            
            # Entry: RSI oversold AND price near lower BB
            if position == 'flat' and rsi < 30 and price < bb_lower * 1.02:
                shares = int(cash / (price * 1.0003))
                if shares > 0:
                    cash -= shares * price * 1.0003
                    position = 'long'
                    entry_price = price
                    entry_date = date
            
            # Exit: RSI neutral OR price reaches middle BB
            elif position == 'long' and (rsi > 50 or price > bb_middle):
                proceeds = shares * price * 0.9997
                pnl_pct = (price / entry_price - 1) * 100
                trades.append({'pnl_pct': pnl_pct, 'hold_days': max((date - entry_date).days, 1)})
                cash += proceeds
                shares = 0
                position = 'flat'
            
            equity.append(cash + shares * price)
        
        if shares > 0:
            cash += shares * df.iloc[-1]['close'] * 0.9997
        
        if len(trades) >= 5:
            returns = pd.Series(equity).pct_change().dropna().values
            sharpe = calculate_sharpe_correct(returns, min_samples=50)
            stats = calculate_trade_stats(pd.DataFrame(trades))
            
            results[symbol] = {
                'sharpe': float(sharpe) if sharpe else 0.0,
                'trades': len(trades),
                'win_rate': stats['win_rate'],
                'avg_pnl': stats['avg_pnl']
            }
        else:
            results[symbol] = {'sharpe': 0.0, 'trades': len(trades)}
    
    print("\n  RESULTS:")
    print(f"  {'Symbol':<10} {'Sharpe':<10} {'Trades':<10} {'Win Rate':<12} {'Avg P&L':<10}")
    print(f"  {'-'*55}")
    for symbol, r in sorted(results.items(), key=lambda x: -x[1].get('sharpe', 0)):
        verdict = "✅" if r['sharpe'] >= 1.0 else ("⚠️" if r['sharpe'] >= 0.5 else "❌")
        print(f"  {symbol:<10} {r['sharpe']:.2f}       {r.get('trades', 0):<10} {r.get('win_rate', 0):.1f}%        {r.get('avg_pnl', 0):.1f}%    {verdict}")
    
    return results


# =============================================================================
# TEST 3: BREAKOUT STRATEGY
# =============================================================================

def test_breakout():
    """
    Test breakout strategy: buy on new highs, sell on trailing stop
    """
    print("\n" + "="*60)
    print("TEST 3: BREAKOUT STRATEGY")
    print("="*60)
    
    alpaca = AlpacaDataClient()
    symbols = ['NVDA', 'TSLA', 'AMD']
    
    results = {}
    
    for symbol in symbols:
        df = alpaca.fetch_historical_bars(symbol, '1Day', '2020-01-01', '2025-12-31')
        df['high_20'] = df['high'].rolling(20).max()
        df['atr'] = (df['high'] - df['low']).rolling(14).mean()
        
        cash = 100000
        shares = 0
        position = 'flat'
        trades = []
        equity = [100000]
        entry_price = entry_date = trailing_stop = None
        
        for date, row in df.iterrows():
            price = row['close']
            high = row['high']
            high_20 = row['high_20']
            atr = row['atr']
            
            if pd.isna(high_20) or pd.isna(atr):
                equity.append(cash + shares * price)
                continue
            
            # Check trailing stop
            if position == 'long':
                # Update trailing stop
                new_stop = price - 2 * atr
                if new_stop > trailing_stop:
                    trailing_stop = new_stop
                
                # Exit if stop hit
                if price < trailing_stop:
                    proceeds = shares * price * 0.9997
                    pnl_pct = (price / entry_price - 1) * 100
                    trades.append({'pnl_pct': pnl_pct, 'hold_days': max((date - entry_date).days, 1)})
                    cash += proceeds
                    shares = 0
                    position = 'flat'
                    trailing_stop = None
            
            # Entry: breakout above 20-day high
            if position == 'flat' and high >= high_20:
                shares = int(cash / (price * 1.0003))
                if shares > 0:
                    cash -= shares * price * 1.0003
                    position = 'long'
                    entry_price = price
                    entry_date = date
                    trailing_stop = price - 2 * atr
            
            equity.append(cash + shares * price)
        
        if shares > 0:
            cash += shares * df.iloc[-1]['close'] * 0.9997
        
        if len(trades) >= 10:
            returns = pd.Series(equity).pct_change().dropna().values
            sharpe = calculate_sharpe_correct(returns, min_samples=50)
            stats = calculate_trade_stats(pd.DataFrame(trades))
            
            results[symbol] = {
                'sharpe': float(sharpe) if sharpe else 0.0,
                'trades': len(trades),
                'win_rate': stats['win_rate'],
                'avg_pnl': stats['avg_pnl']
            }
        else:
            results[symbol] = {'sharpe': 0.0, 'trades': len(trades)}
    
    print("\n  RESULTS:")
    print(f"  {'Symbol':<10} {'Sharpe':<10} {'Trades':<10} {'Win Rate':<12}")
    print(f"  {'-'*45}")
    for symbol, r in sorted(results.items(), key=lambda x: -x[1].get('sharpe', 0)):
        verdict = "✅" if r['sharpe'] >= 1.0 else ("⚠️" if r['sharpe'] >= 0.5 else "❌")
        print(f"  {symbol:<10} {r['sharpe']:.2f}       {r.get('trades', 0):<10} {r.get('win_rate', 0):.1f}%       {verdict}")
    
    return results


# =============================================================================
# TEST 4: EARNINGS STRADDLES ON MORE STOCKS
# =============================================================================

def test_expanded_earnings_straddles():
    """
    Test earnings straddles on high-beta stocks beyond original set
    """
    print("\n" + "="*60)
    print("TEST 4: EXPANDED EARNINGS STRADDLES")
    print("="*60)
    
    alpaca = AlpacaDataClient()
    
    # Earnings dates for additional stocks
    EARNINGS = {
        'AMZN': ['2023-02-02', '2023-04-27', '2023-08-03', '2023-10-26',
                 '2024-02-01', '2024-04-30', '2024-08-01', '2024-10-31',
                 '2025-02-06', '2025-04-29'],
        'META': ['2023-02-01', '2023-04-26', '2023-07-26', '2023-10-25',
                 '2024-02-01', '2024-04-24', '2024-07-31', '2024-10-30',
                 '2025-01-29', '2025-04-30'],
    }
    
    IV_EST = {'AMZN': 0.35, 'META': 0.40}
    
    results = {}
    
    for symbol, dates in EARNINGS.items():
        df = alpaca.fetch_historical_bars(symbol, '1Day', '2023-01-01', '2025-12-31')
        iv = IV_EST.get(symbol, 0.35)
        
        trades = []
        
        for earnings_date in dates:
            try:
                earnings_date = pd.to_datetime(earnings_date)
                
                entry_target = earnings_date - timedelta(days=2)
                entry_data = df[df.index <= entry_target]
                if len(entry_data) == 0:
                    continue
                entry_date = entry_data.index[-1]
                entry_price = entry_data.iloc[-1]['close']
                
                exit_target = earnings_date + timedelta(days=1)
                exit_data = df[df.index >= exit_target]
                if len(exit_data) == 0:
                    continue
                exit_date = exit_data.index[0]
                exit_price = exit_data.iloc[0]['close']
                
                hold_days = (exit_date - entry_date).days
                if hold_days <= 0 or hold_days > 5:
                    continue
                
                strike = round(entry_price / 5) * 5
                T_entry = 7 / 365.0
                
                call_entry = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                    S=entry_price, K=strike, T=T_entry, r=0.04, sigma=iv, option_type='call'
                )['price'] * 1.01
                
                put_entry = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                    S=entry_price, K=strike, T=T_entry, r=0.04, sigma=iv, option_type='put'
                )['price'] * 1.01
                
                T_exit = max((7 - hold_days) / 365.0, 0.001)
                
                call_exit = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                    S=exit_price, K=strike, T=T_exit, r=0.04, sigma=iv, option_type='call'
                )['price'] * 0.99
                
                put_exit = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                    S=exit_price, K=strike, T=T_exit, r=0.04, sigma=iv, option_type='put'
                )['price'] * 0.99
                
                cost = (call_entry + put_entry) * 100
                proceeds = (call_exit + put_exit) * 100
                pnl_pct = (proceeds / cost - 1) * 100
                
                trades.append({'pnl_pct': pnl_pct, 'hold_days': hold_days})
            except:
                continue
        
        if len(trades) >= 3:
            trades_df = pd.DataFrame(trades)
            trade_returns = trades_df['pnl_pct'].values / 100
            avg_hold = trades_df['hold_days'].mean()
            sharpe = calculate_sharpe_from_trades(trade_returns, avg_hold, min_trades=3)
            stats = calculate_trade_stats(trades_df)
            
            results[symbol] = {
                'sharpe': float(sharpe) if sharpe else 0.0,
                'trades': len(trades),
                'win_rate': stats['win_rate'],
                'avg_pnl': stats['avg_pnl']
            }
    
    print("\n  RESULTS:")
    for symbol, r in results.items():
        verdict = "✅" if r['sharpe'] >= 1.5 else ("⚠️" if r['sharpe'] >= 0.5 else "❌")
        print(f"  {symbol}: Sharpe {r['sharpe']:.2f}, {r['trades']} trades, {r['win_rate']:.1f}% win rate {verdict}")
    
    return results


# =============================================================================
# MAIN
# =============================================================================

def main():
    all_results = {}
    
    all_results['optimized_tsla'] = test_optimized_tsla()
    all_results['mean_reversion'] = test_mean_reversion()
    all_results['breakout'] = test_breakout()
    all_results['expanded_earnings'] = test_expanded_earnings_straddles()
    
    # Summary
    print("\n\n" + "="*80)
    print("PHASE 5B: SUMMARY")
    print("="*80)
    
    print("\n  Strategy                    | Best Result      | Sharpe | Status")
    print("  " + "-"*65)
    
    # Best TSLA config
    if all_results.get('optimized_tsla'):
        best = max(all_results['optimized_tsla'].items(), key=lambda x: x[1].get('sharpe', 0))
        status = "✅ GO" if best[1]['sharpe'] >= 1.0 else "⚠️ CONDITIONAL" if best[1]['sharpe'] >= 0.5 else "❌"
        print(f"  TSLA Optimized              | {best[0]:<16} | {best[1]['sharpe']:.2f}   | {status}")
    
    # Best mean reversion
    if all_results.get('mean_reversion'):
        best = max(all_results['mean_reversion'].items(), key=lambda x: x[1].get('sharpe', 0))
        status = "✅ GO" if best[1]['sharpe'] >= 1.0 else "⚠️ CONDITIONAL" if best[1]['sharpe'] >= 0.5 else "❌"
        print(f"  Mean Reversion              | {best[0]:<16} | {best[1]['sharpe']:.2f}   | {status}")
    
    # Best breakout
    if all_results.get('breakout'):
        best = max(all_results['breakout'].items(), key=lambda x: x[1].get('sharpe', 0))
        status = "✅ GO" if best[1]['sharpe'] >= 1.0 else "⚠️" if best[1]['sharpe'] >= 0.5 else "❌"
        print(f"  Breakout                    | {best[0]:<16} | {best[1]['sharpe']:.2f}   | {status}")
    
    # Expanded earnings
    for symbol, r in all_results.get('expanded_earnings', {}).items():
        status = "✅ GO" if r['sharpe'] >= 1.5 else "⚠️" if r['sharpe'] >= 0.5 else "❌"
        print(f"  Earnings Straddle           | {symbol:<16} | {r['sharpe']:.2f}   | {status}")
    
    # Save
    output_dir = Path('research/backtests/phase4_audit/wfa_results')
    
    def convert(obj):
        if isinstance(obj, (np.floating, np.integer)):
            return float(obj) if isinstance(obj, np.floating) else int(obj)
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        return obj
    
    with open(output_dir / 'phase5b_alternative_results.json', 'w') as f:
        json.dump(convert(all_results), f, indent=2)
    
    print(f"\n📁 Results saved")
    print("="*80)


if __name__ == "__main__":
    main()
