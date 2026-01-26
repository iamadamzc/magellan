"""
Phase 4: Corrected Walk-Forward Analysis - Premium Selling Strategy

CORRECTIONS FROM PHASE 3:
1. Correct Sharpe formula: sqrt(252) annualization instead of sqrt(n_trades)
2. Minimum 10 trades per window required
3. Combines SPY + QQQ for more trades
4. Reduced parameter grid (27 vs 243 combinations)
5. Shorter windows (4 months) for more trades per window

Usage:
    python wfa_premium_selling_v2.py           # Full run (2020-2025)
    python wfa_premium_selling_v2.py --quick   # Quick test (2024-2025 only)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from itertools import product
import json
import argparse

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from src.features import calculate_rsi
from src.options.features import OptionsFeatureEngineer
from research.backtests.phase4_audit.wfa_core import (
    calculate_sharpe_from_trades,
    calculate_trade_stats,
    calculate_max_drawdown,
    bootstrap_sharpe_ci,
    generate_rolling_windows
)

print("="*80)
print("PHASE 4: CORRECTED WFA - PREMIUM SELLING STRATEGY")
print("="*80)
print("\nCORRECTIONS APPLIED:")
print("  ✓ Correct Sharpe annualization (sqrt(252))")
print("  ✓ Minimum 10 trades per window")
print("  ✓ SPY + QQQ combined for more trades")
print("  ✓ Reduced parameter grid (27 combinations)")
print()

# =============================================================================
# CONFIGURATION
# =============================================================================

# Reduced parameter grid (key parameters only)
PARAM_GRID = {
    'rsi_oversold': [25, 30, 35],
    'rsi_overbought': [65, 70, 75],
    'profit_target_pct': [50, 60, 70],
    # Fixed parameters (based on Phase 2 findings)
    'time_exit_dte': [21],  # Fixed at 21 DTE
    'stop_loss_pct': [-150]  # Fixed at -150%
}

# Constants
INITIAL_CAPITAL = 100000
TARGET_NOTIONAL = 10000
SLIPPAGE_PCT = 1.0
CONTRACT_FEE = 0.097
RISK_FREE_RATE = 0.04
MIN_TRADES_PER_WINDOW = 10

# IV estimates by symbol
IV_ESTIMATES = {
    'SPY': 0.18,
    'QQQ': 0.22
}

def backtest_premium_selling(df, params, symbol='SPY'):
    """
    Run premium selling backtest with given parameters.
    Returns trades list and metrics dict.
    """
    iv = IV_ESTIMATES.get(symbol, 0.20)
    
    cash = INITIAL_CAPITAL
    position = None
    trades = []
    equity_curve = [INITIAL_CAPITAL]
    
    for date, row in df.iterrows():
        price = row['close']
        rsi = row['rsi']
        
        if pd.isna(rsi):
            continue
        
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
            
            # Exit conditions
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
                
                trades.append({
                    'symbol': symbol,
                    'entry_date': position['entry_date'],
                    'exit_date': date,
                    'hold_days': hold_days,
                    'pnl': final_pnl,
                    'pnl_pct': (final_pnl / position['premium_collected']) * 100,
                    'reason': exit_reason
                })
                
                cash += final_pnl
                position = None
        
        # Enter new position
        if position is None and ((rsi < params['rsi_oversold']) or (rsi > params['rsi_overbought'])):
            option_type = 'put' if rsi < params['rsi_oversold'] else 'call'
            strike = round(price / 5) * 5
            expiration = date + timedelta(days=45)
            T = 45 / 365.0
            
            greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                S=price, K=strike, T=T, r=RISK_FREE_RATE,
                sigma=iv, option_type=option_type
            )
            
            sell_price = greeks['price'] * (1 - SLIPPAGE_PCT/100)
            contracts = max(1, int(TARGET_NOTIONAL / (price * abs(greeks['delta']))))
            
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
                    'entry_date': date
                }
                cash += net_premium
        
        equity_curve.append(cash)
    
    # Calculate metrics
    if len(trades) == 0:
        return [], None
    
    trades_df = pd.DataFrame(trades)
    trade_returns = trades_df['pnl_pct'].values / 100
    avg_hold = trades_df['hold_days'].mean()
    
    # Correct Sharpe calculation
    sharpe = calculate_sharpe_from_trades(trade_returns, avg_holding_days=avg_hold, min_trades=5)
    
    stats = calculate_trade_stats(trades_df)
    max_dd = calculate_max_drawdown(np.array(equity_curve))
    
    metrics = {
        'total_return': (cash / INITIAL_CAPITAL - 1) * 100,
        'sharpe': sharpe if sharpe else 0.0,
        'max_drawdown': max_dd * 100,
        'avg_holding_days': avg_hold,
        **stats
    }
    
    return trades, metrics


def run_wfa(symbols=['SPY', 'QQQ'], start_date='2020-01-01', end_date='2025-12-31'):
    """Run full walk-forward analysis."""
    
    print(f"[1/4] Fetching data for {symbols}...")
    alpaca = AlpacaDataClient()
    
    all_data = {}
    for symbol in symbols:
        df = alpaca.fetch_historical_bars(symbol, '1Day', start_date, end_date)
        df['rsi'] = calculate_rsi(df['close'], period=21)
        df['symbol'] = symbol
        all_data[symbol] = df
        print(f"  ✓ {symbol}: {len(df)} bars")
    
    # Generate windows (4-month train, 4-month test for more trades)
    windows = generate_rolling_windows(start_date, end_date, train_months=4, test_months=4, step_months=4)
    print(f"\n[2/4] Running WFA with {len(windows)} windows...")
    print(f"      Parameter combinations: {len(list(product(*PARAM_GRID.values())))}")
    
    all_results = []
    window_best_params = []
    
    for window in windows:
        print(f"\n{'='*60}")
        print(f"Window {window.name}: Train {window.train_start} to {window.train_end}")
        print(f"           Test  {window.test_start} to {window.test_end}")
        print(f"{'='*60}")
        
        # Combine symbols for training
        train_trades = []
        for symbol, df in all_data.items():
            train_df = df[(df.index >= window.train_start) & (df.index <= window.train_end)]
            train_trades.append((symbol, train_df))
        
        # Optimize on training data
        best_sharpe = -999
        best_params = None
        
        for combo in product(*PARAM_GRID.values()):
            params = {
                'rsi_oversold': combo[0],
                'rsi_overbought': combo[1],
                'profit_target_pct': combo[2],
                'time_exit_dte': combo[3],
                'stop_loss_pct': combo[4]
            }
            
            all_trades = []
            for symbol, train_df in train_trades:
                trades, _ = backtest_premium_selling(train_df, params, symbol)
                all_trades.extend(trades)
            
            if len(all_trades) >= 5:
                trade_returns = [t['pnl_pct'] / 100 for t in all_trades]
                avg_hold = np.mean([t['hold_days'] for t in all_trades])
                sharpe = calculate_sharpe_from_trades(np.array(trade_returns), avg_hold, min_trades=3)
                
                if sharpe and sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_params = params.copy()
        
        if best_params is None:
            print(f"  ⚠️  No valid parameters found in training")
            continue
        
        print(f"  ✓ Best in-sample Sharpe: {best_sharpe:.2f}")
        print(f"    Params: RSI {best_params['rsi_oversold']}/{best_params['rsi_overbought']}, Target {best_params['profit_target_pct']}%")
        
        # Test on out-of-sample data
        oos_trades = []
        for symbol, df in all_data.items():
            test_df = df[(df.index >= window.test_start) & (df.index <= window.test_end)]
            trades, _ = backtest_premium_selling(test_df, best_params, symbol)
            oos_trades.extend(trades)
        
        if len(oos_trades) < MIN_TRADES_PER_WINDOW:
            print(f"  ⚠️  Only {len(oos_trades)} OOS trades (min: {MIN_TRADES_PER_WINDOW})")
            # Still record but flag as insufficient
            
        if len(oos_trades) > 0:
            oos_trades_df = pd.DataFrame(oos_trades)
            trade_returns = oos_trades_df['pnl_pct'].values / 100
            avg_hold = oos_trades_df['hold_days'].mean()
            
            oos_sharpe = calculate_sharpe_from_trades(trade_returns, avg_hold, min_trades=5)
            oos_stats = calculate_trade_stats(oos_trades_df)
            
            # Bootstrap CI
            point, lower, upper = bootstrap_sharpe_ci(trade_returns, periods_per_year=int(252/avg_hold))
            
            oos_sharpe_str = f"{oos_sharpe:.2f}" if oos_sharpe is not None else "N/A"
            print(f"  ✓ Out-of-sample: {len(oos_trades)} trades, Sharpe: {oos_sharpe_str}")
            if lower is not None and upper is not None:
                print(f"    95% CI: [{lower:.2f}, {upper:.2f}]")
            
            all_results.append({
                'window': window.name,
                'train_start': window.train_start,
                'train_end': window.train_end,
                'test_start': window.test_start,
                'test_end': window.test_end,
                'oos_sharpe': oos_sharpe if oos_sharpe else 0.0,
                'oos_sharpe_ci_lower': lower if lower else None,
                'oos_sharpe_ci_upper': upper if upper else None,
                'oos_num_trades': len(oos_trades),
                'oos_win_rate': oos_stats['win_rate'],
                'oos_avg_pnl': oos_stats['avg_pnl'],
                'oos_profit_factor': oos_stats['profit_factor'],
                'sufficient_trades': len(oos_trades) >= MIN_TRADES_PER_WINDOW,
                **{f'param_{k}': v for k, v in best_params.items()}
            })
            
            window_best_params.append(best_params)
    
    return all_results, window_best_params


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--quick', action='store_true', help='Quick test (2024-2025 only)')
    args = parser.parse_args()
    
    if args.quick:
        start_date = '2024-01-01'
        end_date = '2025-12-31'
        print("🚀 QUICK TEST MODE: 2024-2025 only\n")
    else:
        start_date = '2020-01-01'
        end_date = '2025-12-31'
    
    # Run WFA
    results, best_params = run_wfa(['SPY', 'QQQ'], start_date, end_date)
    
    if len(results) == 0:
        print("\n❌ No valid results generated")
        return
    
    # Analysis
    print(f"\n\n{'='*80}")
    print("[3/4] WALK-FORWARD ANALYSIS RESULTS")
    print(f"{'='*80}\n")
    
    results_df = pd.DataFrame(results)
    
    # Filter to windows with sufficient trades
    valid_results = results_df[results_df['sufficient_trades'] == True]
    
    print(f"📊 Summary:")
    print(f"  Total Windows: {len(results_df)}")
    print(f"  Valid Windows (≥{MIN_TRADES_PER_WINDOW} trades): {len(valid_results)}")
    
    if len(valid_results) > 0:
        print(f"\n📈 Valid Windows Performance:")
        print(f"  Average OOS Sharpe: {valid_results['oos_sharpe'].mean():.2f}")
        print(f"  Sharpe Std Dev: {valid_results['oos_sharpe'].std():.2f}")
        print(f"  Min OOS Sharpe: {valid_results['oos_sharpe'].min():.2f}")
        print(f"  Max OOS Sharpe: {valid_results['oos_sharpe'].max():.2f}")
        print(f"  Average Win Rate: {valid_results['oos_win_rate'].mean():.1f}%")
        print(f"  Average Trades/Window: {valid_results['oos_num_trades'].mean():.1f}")
    
    # Compare to Phase 3
    print(f"\n🎯 Comparison to Phase 3:")
    print(f"  Phase 3 Avg Sharpe: 0.35 (INCORRECT FORMULA!)")
    print(f"  Phase 4 Avg Sharpe: {results_df['oos_sharpe'].mean():.2f} (CORRECTED)")
    
    # Save results
    output_dir = Path('research/backtests/phase4_audit/wfa_results')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results_df.to_csv(output_dir / 'premium_selling_wfa_v2.csv', index=False)
    
    # Summary JSON
    summary = {
        'strategy': 'Premium Selling',
        'symbols': ['SPY', 'QQQ'],
        'period': f"{start_date} to {end_date}",
        'total_windows': len(results_df),
        'valid_windows': len(valid_results),
        'avg_oos_sharpe': float(results_df['oos_sharpe'].mean()),
        'sharpe_std': float(results_df['oos_sharpe'].std()),
        'avg_trades_per_window': float(results_df['oos_num_trades'].mean()),
        'methodology': 'Phase 4 Corrected (sqrt(252) annualization)',
        'min_trades_required': MIN_TRADES_PER_WINDOW
    }
    
    with open(output_dir / 'premium_selling_summary_v2.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📁 Results saved to: {output_dir}/")
    
    # GO/NO-GO recommendation
    print(f"\n{'='*80}")
    print("[4/4] PRELIMINARY GO/NO-GO ASSESSMENT")
    print(f"{'='*80}\n")
    
    avg_sharpe = results_df['oos_sharpe'].mean() if len(results_df) > 0 else 0
    sharpe_std = results_df['oos_sharpe'].std() if len(results_df) > 0 else 999
    pct_valid = len(valid_results) / len(results_df) * 100 if len(results_df) > 0 else 0
    
    if avg_sharpe >= 1.5 and sharpe_std < 0.5 and pct_valid >= 80:
        print("✅ PRELIMINARY: GO")
        print("   Strategy shows robust performance across windows")
    elif avg_sharpe >= 1.0 and pct_valid >= 60:
        print("⚠️  PRELIMINARY: CONDITIONAL")
        print("   Strategy shows moderate performance, may need regime filter")
    else:
        print("❌ PRELIMINARY: NO-GO")
        print(f"   Avg Sharpe {avg_sharpe:.2f} < 1.0 threshold")
        print(f"   {pct_valid:.0f}% windows have sufficient trades")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
