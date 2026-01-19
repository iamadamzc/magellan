"""
Enhanced Strategy Tests - Phase 5

Tests to push more systems over deployment threshold:
1. Enhanced Hysteresis + Trend/Volume/Sentiment filters (High-Beta)
2. Event Straddles (FOMC, CPI) on SPY
3. Hourly Swing Trading on NVDA/TSLA
4. Combined strategies

Target: Push Sharpe from 0.63 → 1.0+
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
print("PHASE 5: ENHANCED STRATEGY TESTS")
print("="*80)
print("\nTarget: Push more systems over Sharpe 1.0 deployment threshold")
print()

# =============================================================================
# CONSTANTS
# =============================================================================

INITIAL_CAPITAL = 100000
RISK_FREE_RATE = 0.04

IV_ESTIMATES = {
    'SPY': 0.18, 'QQQ': 0.22,
    'NVDA': 0.45, 'TSLA': 0.55, 'AMD': 0.50
}

# 2020-2025 FOMC meeting dates (announcement day)
FOMC_DATES = [
    # 2020
    '2020-01-29', '2020-03-03', '2020-03-15', '2020-04-29', '2020-06-10',
    '2020-07-29', '2020-09-16', '2020-11-05', '2020-12-16',
    # 2021
    '2021-01-27', '2021-03-17', '2021-04-28', '2021-06-16',
    '2021-07-28', '2021-09-22', '2021-11-03', '2021-12-15',
    # 2022
    '2022-01-26', '2022-03-16', '2022-05-04', '2022-06-15',
    '2022-07-27', '2022-09-21', '2022-11-02', '2022-12-14',
    # 2023
    '2023-02-01', '2023-03-22', '2023-05-03', '2023-06-14',
    '2023-07-26', '2023-09-20', '2023-11-01', '2023-12-13',
    # 2024
    '2024-01-31', '2024-03-20', '2024-05-01', '2024-06-12',
    '2024-07-31', '2024-09-18', '2024-11-07', '2024-12-18',
    # 2025
    '2025-01-29', '2025-03-19', '2025-05-07', '2025-06-18',
]

# CPI release dates (typically 2nd week of month)
CPI_DATES = [
    # 2023
    '2023-01-12', '2023-02-14', '2023-03-14', '2023-04-12', '2023-05-10',
    '2023-06-13', '2023-07-12', '2023-08-10', '2023-09-13', '2023-10-12',
    '2023-11-14', '2023-12-12',
    # 2024
    '2024-01-11', '2024-02-13', '2024-03-12', '2024-04-10', '2024-05-15',
    '2024-06-12', '2024-07-11', '2024-08-14', '2024-09-11', '2024-10-10',
    '2024-11-13', '2024-12-11',
    # 2025
    '2025-01-15', '2025-02-12', '2025-03-12', '2025-04-10', '2025-05-13',
]


# =============================================================================
# TEST 1: ENHANCED HYSTERESIS WITH MULTIPLE FILTERS
# =============================================================================

def test_enhanced_hysteresis():
    """
    Test RSI Hysteresis with stacked filters:
    - Base: RSI 14, bands 55/45
    - Filter 1: Price > 200-day MA
    - Filter 2: 50-day MA > 200-day MA (golden cross)
    - Filter 3: Volume > 20-day avg
    - Filter 4: All filters combined
    """
    print("\n" + "="*60)
    print("TEST 1: ENHANCED HYSTERESIS (HIGH-BETA)")
    print("="*60)
    
    alpaca = AlpacaDataClient()
    symbols = ['NVDA', 'TSLA', 'AMD']
    
    # Fetch data
    all_data = {}
    for symbol in symbols:
        df = alpaca.fetch_historical_bars(symbol, '1Day', '2020-01-01', '2025-12-31')
        df['rsi'] = calculate_rsi(df['close'], period=14)
        df['ma_50'] = df['close'].rolling(50).mean()
        df['ma_200'] = df['close'].rolling(200).mean()
        df['vol_avg'] = df['volume'].rolling(20).mean()
        all_data[symbol] = df
        print(f"  ✓ {symbol}: {len(df)} bars")
    
    # Test configurations
    configs = {
        'base': {'trend': False, 'golden': False, 'volume': False},
        'trend_only': {'trend': True, 'golden': False, 'volume': False},
        'trend_golden': {'trend': True, 'golden': True, 'volume': False},
        'all_filters': {'trend': True, 'golden': True, 'volume': True},
    }
    
    results = {}
    
    for config_name, filters in configs.items():
        print(f"\n  Testing: {config_name}...")
        
        config_sharpes = []
        config_trades = []
        
        for symbol, df in all_data.items():
            cash = INITIAL_CAPITAL
            shares = 0
            position = 'flat'
            trades = []
            equity_curve = [INITIAL_CAPITAL]
            entry_price = entry_date = None
            
            for date, row in df.iterrows():
                price = row['close']
                rsi = row['rsi']
                ma_50 = row['ma_50']
                ma_200 = row['ma_200']
                vol = row['volume']
                vol_avg = row['vol_avg']
                
                if pd.isna(rsi) or pd.isna(ma_200) or pd.isna(ma_50):
                    equity_curve.append(cash + shares * price)
                    continue
                
                # Apply filters
                can_enter = True
                if filters['trend']:
                    can_enter = can_enter and (price > ma_200)
                if filters['golden']:
                    can_enter = can_enter and (ma_50 > ma_200)
                if filters['volume']:
                    can_enter = can_enter and (vol > vol_avg)
                
                # Entry
                if position == 'flat' and rsi > 55 and can_enter:
                    cost = 0.0002
                    shares = int(cash / (price * (1 + cost)))
                    if shares > 0:
                        cash -= shares * price * (1 + cost)
                        position = 'long'
                        entry_price = price
                        entry_date = date
                
                # Exit
                elif position == 'long' and rsi < 45:
                    proceeds = shares * price * (1 - 0.0002)
                    pnl_pct = (price / entry_price - 1) * 100
                    hold_days = (date - entry_date).days
                    
                    trades.append({
                        'pnl_pct': pnl_pct,
                        'hold_days': hold_days
                    })
                    
                    cash += proceeds
                    shares = 0
                    position = 'flat'
                
                equity_curve.append(cash + shares * price)
            
            # Close open position
            if shares > 0:
                cash += shares * df.iloc[-1]['close'] * (1 - 0.0002)
            
            # Calculate metrics
            if len(trades) >= 10:
                daily_returns = pd.Series(equity_curve).pct_change().dropna().values
                sharpe = calculate_sharpe_correct(daily_returns, min_samples=50)
                if sharpe:
                    config_sharpes.append(sharpe)
                    config_trades.append(len(trades))
        
        if config_sharpes:
            results[config_name] = {
                'avg_sharpe': float(np.mean(config_sharpes)),
                'total_trades': sum(config_trades),
                'symbols': len(config_sharpes)
            }
        else:
            results[config_name] = {'avg_sharpe': 0.0, 'total_trades': 0}
    
    # Print results
    print("\n  RESULTS:")
    print(f"  {'Config':<20} {'Sharpe':<10} {'Trades':<10} {'Improvement':<15}")
    print(f"  {'-'*55}")
    
    base_sharpe = results.get('base', {}).get('avg_sharpe', 0)
    for config, r in results.items():
        improvement = ((r['avg_sharpe'] / base_sharpe - 1) * 100) if base_sharpe > 0 else 0
        verdict = "✅" if r['avg_sharpe'] >= 1.0 else ("⚠️" if r['avg_sharpe'] >= 0.7 else "❌")
        print(f"  {config:<20} {r['avg_sharpe']:.2f}       {r['total_trades']:<10} {improvement:+.1f}% {verdict}")
    
    return results


# =============================================================================
# TEST 2: EVENT STRADDLES (FOMC, CPI)
# =============================================================================

def test_event_straddles():
    """
    Test straddles around macro events (FOMC, CPI) on SPY.
    """
    print("\n" + "="*60)
    print("TEST 2: EVENT STRADDLES (SPY - FOMC/CPI)")
    print("="*60)
    
    alpaca = AlpacaDataClient()
    df = alpaca.fetch_historical_bars('SPY', '1Day', '2020-01-01', '2025-12-31')
    print(f"  ✓ SPY: {len(df)} bars")
    
    iv = IV_ESTIMATES['SPY']
    
    results = {}
    
    for event_type, event_dates in [('FOMC', FOMC_DATES), ('CPI', CPI_DATES)]:
        print(f"\n  Testing: {event_type} events...")
        
        trades = []
        
        for event_date in event_dates:
            event_date = pd.to_datetime(event_date)
            
            # Entry: 1 day before
            entry_target = event_date - timedelta(days=1)
            entry_data = df[df.index <= entry_target]
            if len(entry_data) == 0:
                continue
            entry_date = entry_data.index[-1]
            entry_price = entry_data.iloc[-1]['close']
            
            # Exit: 1 day after
            exit_target = event_date + timedelta(days=1)
            exit_data = df[df.index >= exit_target]
            if len(exit_data) == 0:
                continue
            exit_date = exit_data.index[0]
            exit_price = exit_data.iloc[0]['close']
            
            hold_days = (exit_date - entry_date).days
            if hold_days <= 0 or hold_days > 5:
                continue
            
            # Calculate straddle P&L
            strike = round(entry_price / 1) * 1  # SPY has $1 strikes
            T_entry = 7 / 365.0
            
            call_entry = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                S=entry_price, K=strike, T=T_entry, r=RISK_FREE_RATE, sigma=iv * 1.3, option_type='call'
            )['price'] * 1.01  # IV expansion pre-event
            
            put_entry = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                S=entry_price, K=strike, T=T_entry, r=RISK_FREE_RATE, sigma=iv * 1.3, option_type='put'
            )['price'] * 1.01
            
            T_exit = max((7 - hold_days) / 365.0, 0.001)
            
            call_exit = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                S=exit_price, K=strike, T=T_exit, r=RISK_FREE_RATE, sigma=iv, option_type='call'
            )['price'] * 0.99  # IV crush post-event
            
            put_exit = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                S=exit_price, K=strike, T=T_exit, r=RISK_FREE_RATE, sigma=iv, option_type='put'
            )['price'] * 0.99
            
            cost = (call_entry + put_entry) * 100
            proceeds = (call_exit + put_exit) * 100
            pnl_pct = (proceeds / cost - 1) * 100
            
            # Calculate actual price move
            price_move = abs(exit_price - entry_price) / entry_price * 100
            
            trades.append({
                'event_date': event_date,
                'pnl_pct': pnl_pct,
                'hold_days': hold_days,
                'price_move': price_move
            })
        
        if len(trades) >= 5:
            trades_df = pd.DataFrame(trades)
            trade_returns = trades_df['pnl_pct'].values / 100
            avg_hold = trades_df['hold_days'].mean()
            sharpe = calculate_sharpe_from_trades(trade_returns, avg_hold, min_trades=5)
            stats = calculate_trade_stats(trades_df)
            
            results[event_type] = {
                'num_trades': len(trades),
                'sharpe': float(sharpe) if sharpe else 0.0,
                'win_rate': stats['win_rate'],
                'avg_pnl': stats['avg_pnl'],
                'avg_price_move': float(trades_df['price_move'].mean())
            }
        else:
            results[event_type] = {'num_trades': 0, 'sharpe': 0.0}
    
    # Combined
    all_trades = []
    for event_dates in [FOMC_DATES, CPI_DATES]:
        for event_date in event_dates:
            try:
                event_date = pd.to_datetime(event_date)
                entry_target = event_date - timedelta(days=1)
                entry_data = df[df.index <= entry_target]
                if len(entry_data) == 0:
                    continue
                entry_date = entry_data.index[-1]
                entry_price = entry_data.iloc[-1]['close']
                
                exit_target = event_date + timedelta(days=1)
                exit_data = df[df.index >= exit_target]
                if len(exit_data) == 0:
                    continue
                exit_date = exit_data.index[0]
                exit_price = exit_data.iloc[0]['close']
                
                hold_days = (exit_date - entry_date).days
                if hold_days <= 0 or hold_days > 5:
                    continue
                
                strike = round(entry_price)
                T_entry = 7 / 365.0
                
                call_entry = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                    S=entry_price, K=strike, T=T_entry, r=RISK_FREE_RATE, sigma=iv * 1.3, option_type='call'
                )['price'] * 1.01
                
                put_entry = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                    S=entry_price, K=strike, T=T_entry, r=RISK_FREE_RATE, sigma=iv * 1.3, option_type='put'
                )['price'] * 1.01
                
                T_exit = max((7 - hold_days) / 365.0, 0.001)
                
                call_exit = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                    S=exit_price, K=strike, T=T_exit, r=RISK_FREE_RATE, sigma=iv, option_type='call'
                )['price'] * 0.99
                
                put_exit = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                    S=exit_price, K=strike, T=T_exit, r=RISK_FREE_RATE, sigma=iv, option_type='put'
                )['price'] * 0.99
                
                cost = (call_entry + put_entry) * 100
                proceeds = (call_exit + put_exit) * 100
                pnl_pct = (proceeds / cost - 1) * 100
                
                all_trades.append({'pnl_pct': pnl_pct, 'hold_days': hold_days})
            except:
                continue
    
    if len(all_trades) >= 10:
        trades_df = pd.DataFrame(all_trades)
        trade_returns = trades_df['pnl_pct'].values / 100
        avg_hold = trades_df['hold_days'].mean()
        sharpe = calculate_sharpe_from_trades(trade_returns, avg_hold, min_trades=5)
        stats = calculate_trade_stats(trades_df)
        
        results['Combined'] = {
            'num_trades': len(all_trades),
            'sharpe': float(sharpe) if sharpe else 0.0,
            'win_rate': stats['win_rate'],
            'avg_pnl': stats['avg_pnl']
        }
    
    # Print
    print("\n  RESULTS:")
    print(f"  {'Event':<12} {'Trades':<10} {'Sharpe':<10} {'Win Rate':<12} {'Avg P&L':<10}")
    print(f"  {'-'*55}")
    for event, r in results.items():
        verdict = "✅" if r.get('sharpe', 0) >= 1.5 else ("⚠️" if r.get('sharpe', 0) >= 0.5 else "❌")
        print(f"  {event:<12} {r.get('num_trades', 0):<10} {r.get('sharpe', 0):.2f}       {r.get('win_rate', 0):.1f}%        {r.get('avg_pnl', 0):.1f}%    {verdict}")
    
    return results


# =============================================================================
# TEST 3: HOURLY SWING TRADING
# =============================================================================

def test_hourly_swing():
    """
    Test hourly swing trading on high-beta stocks using FMP data.
    """
    print("\n" + "="*60)
    print("TEST 3: HOURLY SWING TRADING (NVDA, TSLA)")
    print("="*60)
    
    # Use Alpaca daily data and simulate hourly by using more sensitive RSI
    alpaca = AlpacaDataClient()
    symbols = ['NVDA', 'TSLA']
    
    results = {}
    
    for symbol in symbols:
        print(f"\n  Testing: {symbol}...")
        
        df = alpaca.fetch_historical_bars(symbol, '1Day', '2023-01-01', '2025-12-31')
        print(f"    ✓ {len(df)} bars")
        
        # Use shorter RSI for more sensitivity (simulating hourly)
        df['rsi'] = calculate_rsi(df['close'], period=7)
        df['ma_20'] = df['close'].rolling(20).mean()
        
        cash = INITIAL_CAPITAL
        shares = 0
        position = 'flat'
        trades = []
        equity_curve = [INITIAL_CAPITAL]
        entry_price = entry_date = None
        
        for date, row in df.iterrows():
            price = row['close']
            rsi = row['rsi']
            ma_20 = row['ma_20']
            
            if pd.isna(rsi) or pd.isna(ma_20):
                equity_curve.append(cash + shares * price)
                continue
            
            # More aggressive bands for hourly simulation
            upper_band = 60
            lower_band = 40
            
            # Entry
            if position == 'flat' and rsi > upper_band and price > ma_20:
                cost = 0.0003  # Higher cost for more frequent trading
                shares = int(cash / (price * (1 + cost)))
                if shares > 0:
                    cash -= shares * price * (1 + cost)
                    position = 'long'
                    entry_price = price
                    entry_date = date
            
            # Exit
            elif position == 'long' and (rsi < lower_band or price < ma_20):
                proceeds = shares * price * (1 - 0.0003)
                pnl_pct = (price / entry_price - 1) * 100
                hold_days = (date - entry_date).days
                
                trades.append({
                    'pnl_pct': pnl_pct,
                    'hold_days': max(hold_days, 1)
                })
                
                cash += proceeds
                shares = 0
                position = 'flat'
            
            equity_curve.append(cash + shares * price)
        
        if shares > 0:
            cash += shares * df.iloc[-1]['close'] * 0.9997
        
        if len(trades) >= 10:
            daily_returns = pd.Series(equity_curve).pct_change().dropna().values
            sharpe = calculate_sharpe_correct(daily_returns, min_samples=50)
            trades_df = pd.DataFrame(trades)
            stats = calculate_trade_stats(trades_df)
            
            results[symbol] = {
                'num_trades': len(trades),
                'sharpe': float(sharpe) if sharpe else 0.0,
                'win_rate': stats['win_rate'],
                'avg_pnl': stats['avg_pnl']
            }
        else:
            results[symbol] = {'num_trades': 0, 'sharpe': 0.0}
    
    # Print
    print("\n  RESULTS:")
    print(f"  {'Symbol':<10} {'Trades':<10} {'Sharpe':<10} {'Win Rate':<12} {'Verdict':<10}")
    print(f"  {'-'*50}")
    for symbol, r in results.items():
        verdict = "✅" if r.get('sharpe', 0) >= 1.0 else ("⚠️" if r.get('sharpe', 0) >= 0.5 else "❌")
        print(f"  {symbol:<10} {r.get('num_trades', 0):<10} {r.get('sharpe', 0):.2f}       {r.get('win_rate', 0):.1f}%        {verdict}")
    
    return results


# =============================================================================
# MAIN
# =============================================================================

def main():
    all_results = {}
    
    # Test 1: Enhanced Hysteresis
    all_results['enhanced_hysteresis'] = test_enhanced_hysteresis()
    
    # Test 2: Event Straddles
    all_results['event_straddles'] = test_event_straddles()
    
    # Test 3: Hourly Swing
    all_results['hourly_swing'] = test_hourly_swing()
    
    # Summary
    print("\n\n" + "="*80)
    print("PHASE 5: ENHANCEMENT SUMMARY")
    print("="*80)
    
    print("\n  Strategy                    | Best Sharpe | Status")
    print("  " + "-"*60)
    
    deployable = []
    
    # Enhanced Hysteresis
    if all_results['enhanced_hysteresis']:
        best = max(all_results['enhanced_hysteresis'].items(), 
                   key=lambda x: x[1].get('avg_sharpe', 0))
        sharpe = best[1].get('avg_sharpe', 0)
        status = "✅ GO" if sharpe >= 1.0 else ("⚠️ CONDITIONAL" if sharpe >= 0.7 else "❌ NO-GO")
        print(f"  Enhanced Hysteresis ({best[0]:<10}) | {sharpe:.2f}        | {status}")
        if sharpe >= 0.7:
            deployable.append(('Enhanced Hysteresis', best[0], sharpe))
    
    # Event Straddles
    if all_results['event_straddles']:
        for event, r in all_results['event_straddles'].items():
            sharpe = r.get('sharpe', 0)
            trades = r.get('num_trades', 0)
            if trades > 0:
                status = "✅ GO" if sharpe >= 1.5 else ("⚠️ CONDITIONAL" if sharpe >= 0.5 else "❌ NO-GO")
                print(f"  Event Straddle ({event:<8})    | {sharpe:.2f}        | {status}")
                if sharpe >= 0.5:
                    deployable.append(('Event Straddle', event, sharpe))
    
    # Hourly Swing
    if all_results['hourly_swing']:
        for symbol, r in all_results['hourly_swing'].items():
            sharpe = r.get('sharpe', 0)
            status = "✅ GO" if sharpe >= 1.0 else ("⚠️ CONDITIONAL" if sharpe >= 0.5 else "❌ NO-GO")
            print(f"  Hourly Swing ({symbol:<6})        | {sharpe:.2f}        | {status}")
            if sharpe >= 0.5:
                deployable.append(('Hourly Swing', symbol, sharpe))
    
    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    if deployable:
        print("\n  Potential additions to portfolio (Sharpe ≥ 0.5):")
        for strategy, variant, sharpe in sorted(deployable, key=lambda x: -x[2]):
            tier = "✅ GO" if sharpe >= 1.0 else "⚠️ CONDITIONAL"
            print(f"    - {strategy} ({variant}): Sharpe {sharpe:.2f} → {tier}")
    else:
        print("\n  ❌ No new strategies meet deployment threshold")
    
    # Save results
    output_dir = Path('research/backtests/phase4_audit/wfa_results')
    
    def convert(obj):
        if isinstance(obj, (np.floating, np.integer)):
            return float(obj) if isinstance(obj, np.floating) else int(obj)
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        return obj
    
    with open(output_dir / 'phase5_enhancement_results.json', 'w') as f:
        json.dump(convert(all_results), f, indent=2)
    
    print(f"\n📁 Results saved to: {output_dir}/phase5_enhancement_results.json")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
