"""
Cross-Asset Strategy Testing

The insight: We tested arbitrary pairings of assets + strategies.
The reality: Any strategy can be applied to any asset class.

ASSET CLASSES:
1. Index ETFs: SPY, QQQ, IWM
2. High-Beta Tech: NVDA, TSLA, AMD
3. Stable Tech: AAPL, MSFT, GOOGL
4. MAG7 Basket: All 7 mega-caps

STRATEGIES:
A. Premium Selling (sell options at RSI extremes)
B. Earnings Straddles (buy straddles around earnings)
C. RSI Hysteresis (trend-following with bands)
D. Event Straddles (FOMC, CPI - for indices)
E. Momentum Equity (simple trend-following without hysteresis)

TEST MATRIX:
           | Premium | Earnings | Hysteresis | Event | Momentum |
-----------+---------+----------+------------+-------+----------|
Index ETFs |   [x]   |    N/A   |    NEW     |  NEW  |   NEW    |
High-Beta  |   NEW   |   [x]    |    [x]     |  N/A  |   NEW    |
Stable Tech|   NEW   |   NEW    |    [x]     |  N/A  |   NEW    |

[x] = Already tested
NEW = New combination to test
N/A = Not applicable (e.g., indices don't have earnings)
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

from src.data_handler import AlpacaDataClient
from src.features import calculate_rsi
from src.options.features import OptionsFeatureEngineer
from research.backtests.phase4_audit.wfa_core import (
    calculate_sharpe_from_trades,
    calculate_sharpe_correct,
    calculate_trade_stats,
    generate_rolling_windows
)

print("="*80)
print("CROSS-ASSET STRATEGY TESTING")
print("="*80)
print("\nTesting ALL combinations of assets × strategies")
print()

# =============================================================================
# CONSTANTS
# =============================================================================

INITIAL_CAPITAL = 100000
RISK_FREE_RATE = 0.04
SLIPPAGE_PCT = 1.0
CONTRACT_FEE = 0.097

IV_ESTIMATES = {
    'SPY': 0.18, 'QQQ': 0.22, 'IWM': 0.25,
    'NVDA': 0.45, 'TSLA': 0.55, 'AMD': 0.50,
    'AAPL': 0.28, 'MSFT': 0.25, 'GOOGL': 0.30, 'AMZN': 0.35, 'META': 0.40
}

# =============================================================================
# STRATEGY IMPLEMENTATIONS
# =============================================================================

def strategy_momentum_equity(df, params=None):
    """
    Simple momentum strategy (no hysteresis):
    - Buy when RSI > 50 and price > 20-day MA
    - Sell when RSI < 50 or price < 20-day MA
    """
    params = params or {'rsi_period': 14, 'ma_period': 20}
    
    df = df.copy()
    df['rsi'] = calculate_rsi(df['close'], period=params['rsi_period'])
    df['ma'] = df['close'].rolling(params['ma_period']).mean()
    
    cash = INITIAL_CAPITAL
    shares = 0
    position = 'flat'
    trades = []
    equity_curve = [INITIAL_CAPITAL]
    entry_price = entry_date = None
    
    for date, row in df.iterrows():
        price = row['close']
        rsi = row['rsi']
        ma = row['ma']
        
        if pd.isna(rsi) or pd.isna(ma):
            equity_curve.append(cash + shares * price)
            continue
        
        # Entry: RSI > 50 AND price > MA
        if position == 'flat' and rsi > 50 and price > ma:
            cost = 0.0002  # 2 bps
            shares = int(cash / (price * (1 + cost)))
            if shares > 0:
                cash -= shares * price * (1 + cost)
                position = 'long'
                entry_price = price
                entry_date = date
        
        # Exit: RSI < 50 OR price < MA
        elif position == 'long' and (rsi < 50 or price < ma):
            proceeds = shares * price * (1 - 0.0002)
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
    
    # Close open position
    if shares > 0:
        price = df.iloc[-1]['close']
        cash += shares * price * (1 - 0.0002)
    
    return trades, equity_curve


def strategy_hysteresis(df, params=None):
    """RSI Hysteresis with configurable bands."""
    params = params or {'rsi_period': 14, 'upper': 55, 'lower': 45}
    
    df = df.copy()
    df['rsi'] = calculate_rsi(df['close'], period=params['rsi_period'])
    
    cash = INITIAL_CAPITAL
    shares = 0
    position = 'flat'
    trades = []
    equity_curve = [INITIAL_CAPITAL]
    entry_price = entry_date = None
    
    for date, row in df.iterrows():
        price = row['close']
        rsi = row['rsi']
        
        if pd.isna(rsi):
            equity_curve.append(cash + shares * price)
            continue
        
        if position == 'flat' and rsi > params['upper']:
            cost = 0.0002
            shares = int(cash / (price * (1 + cost)))
            if shares > 0:
                cash -= shares * price * (1 + cost)
                position = 'long'
                entry_price = price
                entry_date = date
        
        elif position == 'long' and rsi < params['lower']:
            proceeds = shares * price * (1 - 0.0002)
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
    
    if shares > 0:
        cash += shares * df.iloc[-1]['close'] * (1 - 0.0002)
    
    return trades, equity_curve


def strategy_premium_selling(df, symbol, params=None):
    """Premium selling on any asset."""
    params = params or {'rsi_oversold': 30, 'rsi_overbought': 70, 'profit_target': 60}
    
    df = df.copy()
    df['rsi'] = calculate_rsi(df['close'], period=21)
    
    iv = IV_ESTIMATES.get(symbol, 0.30)
    cash = INITIAL_CAPITAL
    position = None
    trades = []
    
    for date, row in df.iterrows():
        price = row['close']
        rsi = row['rsi']
        
        if pd.isna(rsi):
            continue
        
        # Mark-to-market
        if position:
            dte = (position['expiration'] - date).days
            T = max(dte / 365.0, 0.001)
            
            greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                S=price, K=position['strike'], T=T, r=RISK_FREE_RATE,
                sigma=iv, option_type=position['type']
            )
            
            current_price = greeks['price']
            unrealized_pnl = position['premium'] - (current_price * position['contracts'] * 100)
            unrealized_pnl_pct = (unrealized_pnl / position['premium']) * 100
            
            should_exit = unrealized_pnl_pct >= params['profit_target'] or dte <= 21
            
            if should_exit:
                buyback_cost = current_price * position['contracts'] * 100 * 1.01
                final_pnl = position['premium'] - buyback_cost
                
                trades.append({
                    'entry_date': position['entry_date'],
                    'exit_date': date,
                    'pnl_pct': (final_pnl / position['premium']) * 100,
                    'hold_days': (date - position['entry_date']).days
                })
                
                cash += final_pnl
                position = None
        
        # Enter
        if position is None:
            if rsi < params['rsi_oversold'] or rsi > params['rsi_overbought']:
                option_type = 'put' if rsi < params['rsi_oversold'] else 'call'
                strike = round(price / 5) * 5
                expiration = date + timedelta(days=45)
                
                greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                    S=price, K=strike, T=45/365, r=RISK_FREE_RATE,
                    sigma=iv, option_type=option_type
                )
                
                sell_price = greeks['price'] * 0.99
                contracts = max(1, int(10000 / (price * abs(greeks['delta']))))
                premium = sell_price * contracts * 100
                
                if premium > 0 and premium < cash:
                    position = {
                        'type': option_type,
                        'strike': strike,
                        'expiration': expiration,
                        'contracts': contracts,
                        'premium': premium,
                        'entry_date': date
                    }
                    cash += premium
    
    return trades, [INITIAL_CAPITAL, cash]


def strategy_earnings_straddle(df, earnings_dates, symbol):
    """Earnings straddle on any stock with earnings."""
    iv = IV_ESTIMATES.get(symbol, 0.30)
    trades = []
    
    for earnings_date in earnings_dates:
        earnings_date = pd.to_datetime(earnings_date)
        
        # Entry: 2 days before
        entry_target = earnings_date - timedelta(days=2)
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
        T_entry = 7 / 365.0
        
        call_entry = OptionsFeatureEngineer.calculate_black_scholes_greeks(
            S=entry_price, K=strike, T=T_entry, r=RISK_FREE_RATE, sigma=iv, option_type='call'
        )['price'] * 1.01
        
        put_entry = OptionsFeatureEngineer.calculate_black_scholes_greeks(
            S=entry_price, K=strike, T=T_entry, r=RISK_FREE_RATE, sigma=iv, option_type='put'
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
        
        trades.append({
            'earnings_date': earnings_date,
            'pnl_pct': pnl_pct,
            'hold_days': hold_days
        })
    
    return trades


# =============================================================================
# EARNINGS DATES
# =============================================================================

EARNINGS_DATES = {
    'NVDA': ['2020-02-13', '2020-05-21', '2020-08-19', '2020-11-18',
             '2021-02-24', '2021-05-26', '2021-08-18', '2021-11-17',
             '2022-02-16', '2022-05-25', '2022-08-24', '2022-11-16',
             '2023-02-22', '2023-05-24', '2023-08-23', '2023-11-21',
             '2024-02-21', '2024-05-22', '2024-08-28', '2024-11-20',
             '2025-02-26', '2025-05-28'],
    'AAPL': ['2020-01-28', '2020-04-30', '2020-07-30', '2020-10-29',
             '2021-01-27', '2021-04-28', '2021-07-27', '2021-10-28',
             '2022-01-27', '2022-04-28', '2022-07-28', '2022-10-27',
             '2023-02-02', '2023-05-04', '2023-08-03', '2023-11-02',
             '2024-02-01', '2024-05-02', '2024-08-01', '2024-10-31',
             '2025-01-30', '2025-04-30'],
    'MSFT': ['2020-01-29', '2020-04-29', '2020-07-22', '2020-10-27',
             '2021-01-26', '2021-04-27', '2021-07-27', '2021-10-26',
             '2022-01-25', '2022-04-26', '2022-07-26', '2022-10-25',
             '2023-01-24', '2023-04-25', '2023-07-25', '2023-10-24',
             '2024-01-30', '2024-04-25', '2024-07-30', '2024-10-30',
             '2025-01-29', '2025-04-29'],
    'GOOGL': ['2020-02-03', '2020-04-28', '2020-07-30', '2020-10-29',
              '2021-02-02', '2021-04-27', '2021-07-27', '2021-10-26',
              '2022-02-01', '2022-04-26', '2022-07-26', '2022-10-25',
              '2023-02-02', '2023-04-25', '2023-07-25', '2023-10-24',
              '2024-01-30', '2024-04-25', '2024-07-23', '2024-10-29',
              '2025-02-04', '2025-04-29'],
    'TSLA': ['2020-01-29', '2020-04-29', '2020-07-22', '2020-10-21',
             '2021-01-27', '2021-04-26', '2021-07-26', '2021-10-20',
             '2022-01-26', '2022-04-20', '2022-07-20', '2022-10-19',
             '2023-01-25', '2023-04-19', '2023-07-19', '2023-10-18',
             '2024-01-24', '2024-04-23', '2024-07-23', '2024-10-23',
             '2025-01-29', '2025-04-22'],
    'AMD': ['2020-01-28', '2020-04-28', '2020-07-28', '2020-10-27',
            '2021-01-26', '2021-04-27', '2021-07-27', '2021-10-26',
            '2022-02-01', '2022-05-03', '2022-08-02', '2022-11-01',
            '2023-01-31', '2023-05-02', '2023-08-01', '2023-10-31',
            '2024-01-30', '2024-04-30', '2024-07-30', '2024-10-29',
            '2025-02-04', '2025-04-29'],
    'META': ['2020-01-29', '2020-04-29', '2020-07-30', '2020-10-29',
             '2021-01-27', '2021-04-28', '2021-07-28', '2021-10-25',
             '2022-02-02', '2022-04-27', '2022-07-27', '2022-10-26',
             '2023-02-01', '2023-04-26', '2023-07-26', '2023-10-25',
             '2024-02-01', '2024-04-24', '2024-07-31', '2024-10-30',
             '2025-01-29', '2025-04-30'],
    'AMZN': ['2020-01-30', '2020-04-30', '2020-07-30', '2020-10-29',
             '2021-02-02', '2021-04-29', '2021-07-29', '2021-10-28',
             '2022-02-03', '2022-04-28', '2022-07-28', '2022-10-27',
             '2023-02-02', '2023-04-27', '2023-08-03', '2023-10-26',
             '2024-02-01', '2024-04-30', '2024-08-01', '2024-10-31',
             '2025-02-06', '2025-04-29'],
}


# =============================================================================
# MAIN CROSS-TEST
# =============================================================================

def main():
    alpaca = AlpacaDataClient()
    
    # Define asset groups
    asset_groups = {
        'Index_ETFs': ['SPY', 'QQQ'],
        'High_Beta': ['NVDA', 'TSLA', 'AMD'],
        'Stable_Tech': ['AAPL', 'MSFT', 'GOOGL'],
    }
    
    # Define strategies
    strategies = ['Momentum', 'Hysteresis', 'Premium_Selling', 'Earnings_Straddle']
    
    results = {}
    
    print("\n[1/4] Fetching all data...")
    all_data = {}
    for group, symbols in asset_groups.items():
        for symbol in symbols:
            df = alpaca.fetch_historical_bars(symbol, '1Day', '2020-01-01', '2025-12-31')
            all_data[symbol] = df
            print(f"  ✓ {symbol}: {len(df)} bars")
    
    print("\n[2/4] Testing all combinations...")
    
    for group, symbols in asset_groups.items():
        results[group] = {}
        print(f"\n{'='*60}")
        print(f"Asset Group: {group}")
        print(f"{'='*60}")
        
        for strategy in strategies:
            print(f"\n  Strategy: {strategy}")
            
            group_sharpes = []
            group_wins = []
            group_trades = []
            
            for symbol in symbols:
                df = all_data[symbol]
                
                try:
                    if strategy == 'Momentum':
                        trades, equity = strategy_momentum_equity(df)
                        if len(trades) > 10:
                            returns = pd.Series(equity).pct_change().dropna().values
                            sharpe = calculate_sharpe_correct(returns, min_samples=50)
                            if sharpe:
                                group_sharpes.append(sharpe)
                                wins = len([t for t in trades if t['pnl_pct'] > 0]) / len(trades) * 100
                                group_wins.append(wins)
                                group_trades.append(len(trades))
                    
                    elif strategy == 'Hysteresis':
                        trades, equity = strategy_hysteresis(df)
                        if len(trades) > 10:
                            returns = pd.Series(equity).pct_change().dropna().values
                            sharpe = calculate_sharpe_correct(returns, min_samples=50)
                            if sharpe:
                                group_sharpes.append(sharpe)
                                wins = len([t for t in trades if t['pnl_pct'] > 0]) / len(trades) * 100
                                group_wins.append(wins)
                                group_trades.append(len(trades))
                    
                    elif strategy == 'Premium_Selling':
                        trades, _ = strategy_premium_selling(df, symbol)
                        if len(trades) > 5:
                            trade_returns = [t['pnl_pct'] / 100 for t in trades]
                            avg_hold = np.mean([t['hold_days'] for t in trades])
                            sharpe = calculate_sharpe_from_trades(np.array(trade_returns), avg_hold, min_trades=5)
                            if sharpe:
                                group_sharpes.append(sharpe)
                                wins = len([t for t in trades if t['pnl_pct'] > 0]) / len(trades) * 100
                                group_wins.append(wins)
                                group_trades.append(len(trades))
                    
                    elif strategy == 'Earnings_Straddle':
                        if symbol in EARNINGS_DATES:
                            trades = strategy_earnings_straddle(df, EARNINGS_DATES[symbol], symbol)
                            if len(trades) > 5:
                                trade_returns = [t['pnl_pct'] / 100 for t in trades]
                                avg_hold = np.mean([t['hold_days'] for t in trades])
                                sharpe = calculate_sharpe_from_trades(np.array(trade_returns), avg_hold, min_trades=5)
                                if sharpe:
                                    group_sharpes.append(sharpe)
                                    wins = len([t for t in trades if t['pnl_pct'] > 0]) / len(trades) * 100
                                    group_wins.append(wins)
                                    group_trades.append(len(trades))
                
                except Exception as e:
                    print(f"    Error with {symbol}: {e}")
            
            if group_sharpes:
                avg_sharpe = np.mean(group_sharpes)
                avg_wins = np.mean(group_wins) if group_wins else 0
                total_trades = sum(group_trades)
                
                results[group][strategy] = {
                    'avg_sharpe': float(avg_sharpe),
                    'avg_win_rate': float(avg_wins),
                    'total_trades': int(total_trades),
                    'symbols_tested': len(group_sharpes)
                }
                
                verdict = "✅" if avg_sharpe >= 1.5 else ("⚠️" if avg_sharpe >= 0.5 else "❌")
                print(f"    {verdict} Avg Sharpe: {avg_sharpe:.2f}, Win Rate: {avg_wins:.1f}%, Trades: {total_trades}")
            else:
                results[group][strategy] = {'avg_sharpe': 0.0, 'note': 'Insufficient data'}
                print(f"    ❌ Insufficient data")
    
    # Summary
    print("\n\n" + "="*80)
    print("[3/4] CROSS-ASSET STRATEGY MATRIX")
    print("="*80)
    
    print("\n{:<15} | {:<12} | {:<12} | {:<15} | {:<15}".format(
        "Asset Group", "Momentum", "Hysteresis", "Premium Sell", "Earnings Strad"))
    print("-" * 75)
    
    for group in results:
        row = [group]
        for strategy in strategies:
            if strategy in results[group] and 'avg_sharpe' in results[group][strategy]:
                sharpe = results[group][strategy]['avg_sharpe']
                row.append(f"{sharpe:.2f}")
            else:
                row.append("N/A")
        print("{:<15} | {:<12} | {:<12} | {:<15} | {:<15}".format(*row))
    
    # Find best combinations
    print("\n" + "="*80)
    print("[4/4] TOP PERFORMING COMBINATIONS")
    print("="*80)
    
    all_combos = []
    for group in results:
        for strategy in results[group]:
            if 'avg_sharpe' in results[group][strategy]:
                all_combos.append({
                    'group': group,
                    'strategy': strategy,
                    'sharpe': results[group][strategy]['avg_sharpe'],
                    'trades': results[group][strategy].get('total_trades', 0)
                })
    
    all_combos.sort(key=lambda x: x['sharpe'], reverse=True)
    
    print("\n  Rank | Asset Group     | Strategy         | Sharpe | Trades | Verdict")
    print("  " + "-" * 70)
    
    for i, combo in enumerate(all_combos[:10], 1):
        if combo['sharpe'] >= 1.5:
            verdict = "✅ GO"
        elif combo['sharpe'] >= 1.0:
            verdict = "⚠️  CONDITIONAL"
        elif combo['sharpe'] >= 0.5:
            verdict = "⚠️  WEAK"
        else:
            verdict = "❌ NO-GO"
        
        print(f"  {i:<4} | {combo['group']:<15} | {combo['strategy']:<16} | {combo['sharpe']:.2f}   | {combo['trades']:<6} | {verdict}")
    
    # Save results
    output_dir = Path('research/backtests/phase4_audit/wfa_results')
    
    with open(output_dir / 'cross_asset_strategy_matrix.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to: {output_dir}/cross_asset_strategy_matrix.json")
    
    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    go_systems = [c for c in all_combos if c['sharpe'] >= 1.5]
    conditional = [c for c in all_combos if 1.0 <= c['sharpe'] < 1.5]
    
    if go_systems:
        print("\n✅ DEPLOY (Sharpe ≥ 1.5):")
        for s in go_systems:
            print(f"   - {s['group']} + {s['strategy']}: Sharpe {s['sharpe']:.2f}")
    
    if conditional:
        print("\n⚠️  CONDITIONAL (Sharpe 1.0-1.5):")
        for s in conditional:
            print(f"   - {s['group']} + {s['strategy']}: Sharpe {s['sharpe']:.2f}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
