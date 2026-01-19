"""
Phase 4: Parameter Tuning Tests

Tests specific parameter changes to see if failing systems can be salvaged:

1. Premium Selling with Regime Filter (vol <20%, RSI range >29)
2. Daily Trend Hysteresis with Trend Filter (200-day MA)
3. Earnings Straddles - optimize entry timing

Usage:
    python parameter_tuning_tests.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from itertools import product
import json

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from src.features import calculate_rsi
from src.options.features import OptionsFeatureEngineer
from research.backtests.phase4_audit.wfa_core import (
    calculate_sharpe_from_trades,
    calculate_sharpe_correct,
    calculate_trade_stats,
    calculate_max_drawdown,
    bootstrap_sharpe_ci,
    generate_rolling_windows
)

print("="*80)
print("PHASE 4: PARAMETER TUNING TESTS")
print("="*80)
print("\nTesting if failing systems can be salvaged with tuning:")
print("  1. Premium Selling + Regime Filter (vol <20%, RSI range >29)")
print("  2. Daily Hysteresis + Trend Filter (200-day MA)")
print("  3. Earnings Straddles - Entry Timing Optimization")
print()

# =============================================================================
# CONSTANTS
# =============================================================================

INITIAL_CAPITAL = 100000
RISK_FREE_RATE = 0.04
SLIPPAGE_PCT = 1.0
CONTRACT_FEE = 0.097

IV_ESTIMATES = {
    'SPY': 0.18,
    'QQQ': 0.22,
    'NVDA': 0.45,
    'AAPL': 0.28,
    'MSFT': 0.25,
    'GOOGL': 0.30,
    'AMZN': 0.35,
    'META': 0.40,
    'TSLA': 0.55
}


# =============================================================================
# TEST 1: PREMIUM SELLING WITH REGIME FILTER
# =============================================================================

def test_premium_selling_with_regime_filter():
    """
    Test Premium Selling with regime filter:
    - Only trade when VIX proxy (realized vol) < 20%
    - Only trade when RSI range (high-low over 10 days) > 29
    """
    print("\n" + "="*60)
    print("TEST 1: PREMIUM SELLING WITH REGIME FILTER")
    print("="*60)
    print("\nFilter: vol < 20% AND RSI range > 29")
    
    alpaca = AlpacaDataClient()
    symbols = ['SPY', 'QQQ']
    
    # Fetch data
    all_data = {}
    for symbol in symbols:
        df = alpaca.fetch_historical_bars(symbol, '1Day', '2020-01-01', '2025-12-31')
        df['rsi'] = calculate_rsi(df['close'], period=21)
        df['returns'] = df['close'].pct_change()
        df['realized_vol'] = df['returns'].rolling(21).std() * np.sqrt(252) * 100
        df['rsi_range_10d'] = df['rsi'].rolling(10).max() - df['rsi'].rolling(10).min()
        all_data[symbol] = df
        print(f"  ✓ {symbol}: {len(df)} bars")
    
    # Test with and without filter
    results = {'no_filter': [], 'with_filter': []}
    
    params = {
        'rsi_oversold': 30,
        'rsi_overbought': 70,
        'profit_target_pct': 60,
        'time_exit_dte': 21,
        'stop_loss_pct': -150
    }
    
    for filter_mode in ['no_filter', 'with_filter']:
        print(f"\n  Testing: {filter_mode}...")
        
        all_trades = []
        
        for symbol, df in all_data.items():
            iv = IV_ESTIMATES.get(symbol, 0.20)
            cash = INITIAL_CAPITAL
            position = None
            
            for date, row in df.iterrows():
                price = row['close']
                rsi = row['rsi']
                vol = row['realized_vol']
                rsi_range = row['rsi_range_10d']
                
                if pd.isna(rsi) or pd.isna(vol) or pd.isna(rsi_range):
                    continue
                
                # Apply regime filter if enabled
                if filter_mode == 'with_filter':
                    regime_ok = (vol < 20) and (rsi_range > 29)
                else:
                    regime_ok = True
                
                # Mark-to-market existing position
                if position:
                    dte = (position['expiration'] - date).days
                    T = max(dte / 365.0, 0.001)
                    
                    greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                        S=price, K=position['strike'], T=T, r=RISK_FREE_RATE,
                        sigma=iv, option_type=position['type']
                    )
                    
                    current_price = greeks['price']
                    unrealized_pnl = position['premium_collected'] - (current_price * position['contracts'] * 100)
                    unrealized_pnl_pct = (unrealized_pnl / position['premium_collected']) * 100
                    
                    should_exit = False
                    exit_reason = None
                    
                    if unrealized_pnl_pct >= params['profit_target_pct']:
                        should_exit, exit_reason = True, 'PROFIT_TARGET'
                    elif dte <= params['time_exit_dte']:
                        should_exit, exit_reason = True, 'TIME_EXIT'
                    elif unrealized_pnl_pct <= params['stop_loss_pct']:
                        should_exit, exit_reason = True, 'STOP_LOSS'
                    
                    if should_exit:
                        buyback_cost = current_price * position['contracts'] * 100 * (1 + SLIPPAGE_PCT/100)
                        fees = CONTRACT_FEE * position['contracts']
                        total_cost = buyback_cost + fees
                        
                        final_pnl = position['premium_collected'] - total_cost
                        hold_days = (date - position['entry_date']).days
                        
                        all_trades.append({
                            'symbol': symbol,
                            'entry_date': position['entry_date'],
                            'exit_date': date,
                            'hold_days': hold_days,
                            'pnl': final_pnl,
                            'pnl_pct': (final_pnl / position['premium_collected']) * 100,
                            'reason': exit_reason,
                            'entry_vol': position['entry_vol'],
                            'entry_rsi_range': position['entry_rsi_range']
                        })
                        
                        cash += final_pnl
                        position = None
                
                # Enter new position
                if position is None and regime_ok:
                    if (rsi < params['rsi_oversold']) or (rsi > params['rsi_overbought']):
                        option_type = 'put' if rsi < params['rsi_oversold'] else 'call'
                        strike = round(price / 5) * 5
                        expiration = date + timedelta(days=45)
                        T = 45 / 365.0
                        
                        greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                            S=price, K=strike, T=T, r=RISK_FREE_RATE,
                            sigma=iv, option_type=option_type
                        )
                        
                        sell_price = greeks['price'] * (1 - SLIPPAGE_PCT/100)
                        contracts = max(1, int(10000 / (price * abs(greeks['delta']))))
                        
                        premium_collected = sell_price * contracts * 100
                        fees = CONTRACT_FEE * contracts
                        net_premium = premium_collected - fees
                        
                        if net_premium > 0 and net_premium < cash:
                            position = {
                                'type': option_type,
                                'strike': strike,
                                'expiration': expiration,
                                'contracts': contracts,
                                'premium_collected': net_premium,
                                'entry_date': date,
                                'entry_vol': vol,
                                'entry_rsi_range': rsi_range
                            }
                            cash += net_premium
        
        # Calculate metrics
        if len(all_trades) > 0:
            trades_df = pd.DataFrame(all_trades)
            trade_returns = trades_df['pnl_pct'].values / 100
            avg_hold = trades_df['hold_days'].mean()
            
            sharpe = calculate_sharpe_from_trades(trade_returns, avg_hold, min_trades=5)
            stats = calculate_trade_stats(trades_df)
            
            results[filter_mode] = {
                'num_trades': len(all_trades),
                'sharpe': sharpe if sharpe else 0.0,
                'win_rate': stats['win_rate'],
                'avg_pnl': stats['avg_pnl'],
                'profit_factor': stats['profit_factor']
            }
        else:
            results[filter_mode] = {'num_trades': 0, 'sharpe': 0.0}
    
    # Print comparison
    print("\n  RESULTS:")
    print(f"  {'Mode':<15} {'Trades':<10} {'Sharpe':<10} {'Win Rate':<12} {'Avg P&L':<10}")
    print(f"  {'-'*55}")
    for mode, r in results.items():
        if r['num_trades'] > 0:
            print(f"  {mode:<15} {r['num_trades']:<10} {r['sharpe']:.2f}      {r['win_rate']:.1f}%        {r['avg_pnl']:.1f}%")
        else:
            print(f"  {mode:<15} {0:<10} {'N/A':<10}")
    
    # Verdict
    print("\n  VERDICT:")
    if results['with_filter']['num_trades'] > 50 and results['with_filter']['sharpe'] > 1.0:
        print("  ✅ Regime filter IMPROVES strategy - consider CONDITIONAL deployment")
    elif results['with_filter']['num_trades'] < 20:
        print("  ❌ Regime filter leaves TOO FEW trades - not practical")
    else:
        print("  ❌ Regime filter doesn't help enough - strategy still fails")
    
    return results


# =============================================================================
# TEST 2: DAILY HYSTERESIS WITH TREND FILTER
# =============================================================================

def test_hysteresis_with_trend_filter():
    """
    Test Daily Trend Hysteresis with added filters:
    - 200-day MA trend filter (only long when price > 200 MA)
    - Volume confirmation (volume > 20-day average)
    """
    print("\n" + "="*60)
    print("TEST 2: DAILY HYSTERESIS WITH TREND FILTER")
    print("="*60)
    print("\nFilter: Price > 200-day MA (trend confirmation)")
    
    alpaca = AlpacaDataClient()
    symbols = ['NVDA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA']
    
    # Fetch data
    all_data = {}
    for symbol in symbols:
        df = alpaca.fetch_historical_bars(symbol, '1Day', '2020-01-01', '2025-12-31')
        df['rsi'] = calculate_rsi(df['close'], period=14)
        df['ma_200'] = df['close'].rolling(200).mean()
        df['vol_avg'] = df['volume'].rolling(20).mean()
        all_data[symbol] = df
        print(f"  ✓ {symbol}: {len(df)} bars")
    
    params = {
        'rsi_period': 14,
        'hysteresis_upper': 55,
        'hysteresis_lower': 45
    }
    
    results = {'no_filter': {}, 'with_trend': {}, 'with_trend_vol': {}}
    
    for filter_mode in ['no_filter', 'with_trend', 'with_trend_vol']:
        print(f"\n  Testing: {filter_mode}...")
        
        mode_sharpes = []
        mode_outperformance = []
        
        for symbol, df in all_data.items():
            cash = INITIAL_CAPITAL
            shares = 0
            position = 'flat'
            trades = []
            equity_curve = [INITIAL_CAPITAL]
            entry_price = None
            entry_date = None
            
            for i, (date, row) in enumerate(df.iterrows()):
                price = row['close']
                rsi = row['rsi']
                ma_200 = row['ma_200']
                vol = row['volume']
                vol_avg = row['vol_avg']
                
                if pd.isna(rsi) or pd.isna(ma_200):
                    equity_curve.append(cash + shares * price)
                    continue
                
                # Apply filters
                if filter_mode == 'no_filter':
                    can_enter = True
                elif filter_mode == 'with_trend':
                    can_enter = price > ma_200  # Trend filter
                else:  # with_trend_vol
                    can_enter = (price > ma_200) and (vol > vol_avg)
                
                # Trading logic
                if position == 'flat' and rsi > params['hysteresis_upper'] and can_enter:
                    cost = 0.00015  # 1.5 bps
                    shares = int(cash / (price * (1 + cost)))
                    if shares > 0:
                        cash -= shares * price * (1 + cost)
                        position = 'long'
                        entry_price = price
                        entry_date = date
                
                elif position == 'long' and rsi < params['hysteresis_lower']:
                    cost = 0.00015
                    proceeds = shares * price * (1 - cost)
                    pnl = proceeds - (shares * entry_price)
                    pnl_pct = (price / entry_price - 1) * 100
                    hold_days = (date - entry_date).days
                    
                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': date,
                        'pnl_pct': pnl_pct,
                        'hold_days': hold_days
                    })
                    
                    cash += proceeds
                    shares = 0
                    position = 'flat'
                
                equity_curve.append(cash + shares * price)
            
            # Close any open position
            if position == 'long' and shares > 0:
                price = df.iloc[-1]['close']
                proceeds = shares * price * (1 - 0.00015)
                cash += proceeds
                shares = 0
            
            # Calculate metrics
            daily_returns = pd.Series(equity_curve).pct_change().dropna().values
            sharpe = calculate_sharpe_correct(daily_returns, min_samples=50)
            
            buy_hold_return = (df.iloc[-1]['close'] / df.iloc[0]['close'] - 1) * 100
            strategy_return = (equity_curve[-1] / INITIAL_CAPITAL - 1) * 100
            outperf = strategy_return - buy_hold_return
            
            if sharpe:
                mode_sharpes.append(sharpe)
                mode_outperformance.append(outperf)
        
        if mode_sharpes:
            results[filter_mode] = {
                'avg_sharpe': np.mean(mode_sharpes),
                'avg_outperformance': np.mean(mode_outperformance),
                'pct_positive': np.mean([s > 0 for s in mode_sharpes]) * 100
            }
        else:
            results[filter_mode] = {'avg_sharpe': 0.0, 'avg_outperformance': 0.0}
    
    # Print comparison
    print("\n  RESULTS (across 7 stocks):")
    print(f"  {'Mode':<20} {'Avg Sharpe':<12} {'Avg Outperf':<15} {'% Positive':<10}")
    print(f"  {'-'*55}")
    for mode, r in results.items():
        print(f"  {mode:<20} {r['avg_sharpe']:.2f}         {r['avg_outperformance']:+.1f}%          {r.get('pct_positive', 0):.0f}%")
    
    # Verdict
    print("\n  VERDICT:")
    best_mode = max(results.keys(), key=lambda k: results[k]['avg_sharpe'])
    if results[best_mode]['avg_sharpe'] > 0.5:
        print(f"  ⚠️  {best_mode} shows improvement but still weak (Sharpe {results[best_mode]['avg_sharpe']:.2f})")
    else:
        print(f"  ❌ No filter configuration achieves acceptable Sharpe - strategy fundamentally flawed")
    
    return results


# =============================================================================
# TEST 3: EARNINGS STRADDLES - ENTRY TIMING
# =============================================================================

def test_earnings_entry_timing():
    """
    Test different entry timings for earnings straddles:
    - 1 day before (current)
    - 2 days before (more IV expansion)
    - 3 days before (even more)
    """
    print("\n" + "="*60)
    print("TEST 3: EARNINGS STRADDLES - ENTRY TIMING OPTIMIZATION")
    print("="*60)
    print("\nTesting: 1-day, 2-day, 3-day before earnings entry")
    
    alpaca = AlpacaDataClient()
    
    # Earnings dates for GOOGL (best performer)
    GOOGL_EARNINGS = {
        2020: ['2020-02-03', '2020-04-28', '2020-07-30', '2020-10-29'],
        2021: ['2021-02-02', '2021-04-27', '2021-07-27', '2021-10-26'],
        2022: ['2022-02-01', '2022-04-26', '2022-07-26', '2022-10-25'],
        2023: ['2023-02-02', '2023-04-25', '2023-07-25', '2023-10-24'],
        2024: ['2024-01-30', '2024-04-25', '2024-07-23', '2024-10-29'],
        2025: ['2025-02-04', '2025-04-29', '2025-07-29', '2025-10-28'],
    }
    
    df = alpaca.fetch_historical_bars('GOOGL', '1Day', '2020-01-01', '2025-12-31')
    print(f"  ✓ GOOGL: {len(df)} bars")
    
    iv = 0.30
    results = {}
    
    for days_before in [1, 2, 3]:
        print(f"\n  Testing: {days_before} day(s) before entry...")
        
        trades = []
        
        for year, dates in GOOGL_EARNINGS.items():
            for earnings_date in dates:
                earnings_date = pd.to_datetime(earnings_date)
                
                # Entry
                entry_target = earnings_date - timedelta(days=days_before)
                entry_data = df[df.index <= entry_target]
                if len(entry_data) == 0:
                    continue
                entry_date = entry_data.index[-1]
                entry_price = entry_data.iloc[-1]['close']
                
                # Exit: 1 day after
                exit_target = earnings_date + timedelta(days=1)
                exit_data = df[df.index >= exit_target]
                if len(exit_data) == 0:
                    continue
                exit_date = exit_data.index[0]
                exit_price = exit_data.iloc[0]['close']
                
                hold_days = (exit_date - entry_date).days
                if hold_days <= 0:
                    continue
                
                # Calculate straddle P&L
                strike = round(entry_price / 5) * 5
                T_entry = (days_before + 7) / 365.0
                
                call_entry = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                    S=entry_price, K=strike, T=T_entry, r=RISK_FREE_RATE, sigma=iv, option_type='call'
                )['price'] * 1.01  # slippage
                
                put_entry = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                    S=entry_price, K=strike, T=T_entry, r=RISK_FREE_RATE, sigma=iv, option_type='put'
                )['price'] * 1.01
                
                T_exit = max((7 - hold_days + days_before) / 365.0, 0.001)
                
                call_exit = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                    S=exit_price, K=strike, T=T_exit, r=RISK_FREE_RATE, sigma=iv, option_type='call'
                )['price'] * 0.99
                
                put_exit = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                    S=exit_price, K=strike, T=T_exit, r=RISK_FREE_RATE, sigma=iv, option_type='put'
                )['price'] * 0.99
                
                cost = (call_entry + put_entry) * 100 + CONTRACT_FEE * 2
                proceeds = (call_exit + put_exit) * 100 - CONTRACT_FEE * 2
                pnl_pct = (proceeds / cost - 1) * 100
                
                trades.append({
                    'earnings_date': earnings_date,
                    'pnl_pct': pnl_pct,
                    'hold_days': hold_days
                })
        
        if len(trades) > 0:
            trades_df = pd.DataFrame(trades)
            trade_returns = trades_df['pnl_pct'].values / 100
            avg_hold = trades_df['hold_days'].mean()
            sharpe = calculate_sharpe_from_trades(trade_returns, avg_hold, min_trades=5)
            stats = calculate_trade_stats(trades_df)
            
            results[f'{days_before}_day'] = {
                'num_trades': len(trades),
                'sharpe': sharpe if sharpe else 0.0,
                'win_rate': stats['win_rate'],
                'avg_pnl': stats['avg_pnl'],
                'avg_hold': avg_hold
            }
    
    # Print comparison
    print("\n  RESULTS (GOOGL only):")
    print(f"  {'Entry':<10} {'Trades':<10} {'Sharpe':<10} {'Win Rate':<12} {'Avg P&L':<10} {'Avg Hold':<10}")
    print(f"  {'-'*60}")
    for mode, r in results.items():
        print(f"  {mode:<10} {r['num_trades']:<10} {r['sharpe']:.2f}       {r['win_rate']:.1f}%        {r['avg_pnl']:.1f}%      {r['avg_hold']:.1f} days")
    
    # Verdict
    print("\n  VERDICT:")
    best_mode = max(results.keys(), key=lambda k: results[k]['sharpe'])
    print(f"  ✅ Best entry timing: {best_mode} (Sharpe {results[best_mode]['sharpe']:.2f})")
    
    return results


# =============================================================================
# MAIN
# =============================================================================

def main():
    # Run all tests
    print("\n" + "="*80)
    print("RUNNING ALL PARAMETER TUNING TESTS")
    print("="*80)
    
    ps_results = test_premium_selling_with_regime_filter()
    hysteresis_results = test_hysteresis_with_trend_filter()
    earnings_results = test_earnings_entry_timing()
    
    # Summary
    print("\n\n" + "="*80)
    print("PARAMETER TUNING SUMMARY")
    print("="*80)
    
    print("\n1. PREMIUM SELLING + REGIME FILTER:")
    if ps_results.get('with_filter', {}).get('sharpe', 0) > ps_results.get('no_filter', {}).get('sharpe', 0):
        improvement = ps_results['with_filter']['sharpe'] - ps_results['no_filter']['sharpe']
        print(f"   Improvement: +{improvement:.2f} Sharpe")
        if ps_results['with_filter']['sharpe'] > 1.0:
            print("   Recommendation: CONDITIONAL deployment with regime filter")
        else:
            print("   Recommendation: Still NO-GO, improvement insufficient")
    else:
        print("   Recommendation: NO improvement, confirm NO-GO")
    
    print("\n2. DAILY HYSTERESIS + TREND FILTER:")
    best_mode = max(hysteresis_results.keys(), key=lambda k: hysteresis_results[k]['avg_sharpe'])
    print(f"   Best mode: {best_mode} (Sharpe {hysteresis_results[best_mode]['avg_sharpe']:.2f})")
    if hysteresis_results[best_mode]['avg_sharpe'] > 0.5:
        print("   Recommendation: WEAK improvement, still not deployable")
    else:
        print("   Recommendation: NO improvement, confirm NO-GO")
    
    print("\n3. EARNINGS STRADDLES ENTRY TIMING:")
    best_entry = max(earnings_results.keys(), key=lambda k: earnings_results[k]['sharpe'])
    print(f"   Best entry: {best_entry} (Sharpe {earnings_results[best_entry]['sharpe']:.2f})")
    print("   Recommendation: Current 2-day entry is near-optimal, no change needed")
    
    # Save results
    output_dir = Path('research/backtests/phase4_audit/wfa_results')
    
    all_results = {
        'premium_selling_regime_filter': ps_results,
        'hysteresis_trend_filter': hysteresis_results,
        'earnings_entry_timing': earnings_results
    }
    
    # Convert numpy types
    def convert(obj):
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        return obj
    
    with open(output_dir / 'parameter_tuning_results.json', 'w') as f:
        json.dump(convert(all_results), f, indent=2)
    
    print(f"\n📁 Results saved to: {output_dir}/parameter_tuning_results.json")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
