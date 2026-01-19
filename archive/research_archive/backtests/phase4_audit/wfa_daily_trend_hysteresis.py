"""
Phase 4: Walk-Forward Analysis - Daily Trend Hysteresis Strategy

THIS IS THE FIRST WFA FOR THE EQUITY SYSTEM
Previous validation was only parameter sweep on 2024-2025 data.

Tests:
- Rolling 6-month train/test windows (2020-2025)
- MAG7 stocks: NVDA, AAPL, MSFT, GOOGL, AMZN, META, TSLA
- Parameter grid: RSI period, hysteresis bands
- Correct Sharpe calculation

Usage:
    python wfa_daily_trend_hysteresis.py           # Full run
    python wfa_daily_trend_hysteresis.py --quick   # Quick test (2024-2025 only)
"""

import sys
from pathlib import Path
from datetime import datetime
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
from research.backtests.phase4_audit.wfa_core import (
    calculate_sharpe_correct,
    calculate_trade_stats,
    calculate_max_drawdown,
    bootstrap_sharpe_ci,
    generate_rolling_windows
)

print("="*80)
print("PHASE 4: WFA - DAILY TREND HYSTERESIS (EQUITY)")
print("="*80)
print("\nNOTE: This is the FIRST WFA for the equity system")
print("      Previous validation was only parameter sweep on 2024-2025\n")

# =============================================================================
# CONFIGURATION
# =============================================================================

# MAG7 stocks
MAG7 = ['NVDA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA']

# Parameter grid (based on successful Phase 2 findings)
PARAM_GRID = {
    'rsi_period': [14, 21, 28],
    'hysteresis_upper': [55, 58, 65],
    'hysteresis_lower': [45, 42, 35]
}

# Constants
INITIAL_CAPITAL = 100000
TRANSACTION_COST_BPS = 1.5  # 0.015%
MIN_TRADES_PER_WINDOW = 5


def backtest_hysteresis(df, params):
    """
    Run daily trend hysteresis backtest.
    
    Logic:
    - Buy when RSI > upper threshold
    - Sell when RSI < lower threshold  
    - Hold when RSI between thresholds (the "hysteresis" zone)
    """
    rsi_period = params['rsi_period']
    upper = params['hysteresis_upper']
    lower = params['hysteresis_lower']
    
    # Calculate RSI
    df = df.copy()
    df['rsi'] = calculate_rsi(df['close'], period=rsi_period)
    
    # Initialize
    cash = INITIAL_CAPITAL
    shares = 0
    position = 'flat'  # 'long' or 'flat'
    trades = []
    equity_curve = [INITIAL_CAPITAL]
    daily_returns = []
    
    entry_price = None
    entry_date = None
    
    for i, (date, row) in enumerate(df.iterrows()):
        price = row['close']
        rsi = row['rsi']
        
        if pd.isna(rsi):
            equity_curve.append(cash + shares * price)
            continue
        
        # Trading logic with hysteresis
        if position == 'flat' and rsi > upper:
            # Enter long
            cost = TRANSACTION_COST_BPS / 10000
            shares = int(cash / (price * (1 + cost)))
            if shares > 0:
                cash -= shares * price * (1 + cost)
                position = 'long'
                entry_price = price
                entry_date = date
        
        elif position == 'long' and rsi < lower:
            # Exit long
            cost = TRANSACTION_COST_BPS / 10000
            proceeds = shares * price * (1 - cost)
            pnl = proceeds - (shares * entry_price)
            pnl_pct = (price / entry_price - 1) * 100
            hold_days = (date - entry_date).days
            
            trades.append({
                'entry_date': entry_date,
                'exit_date': date,
                'entry_price': entry_price,
                'exit_price': price,
                'hold_days': hold_days,
                'pnl': pnl,
                'pnl_pct': pnl_pct
            })
            
            cash += proceeds
            shares = 0
            position = 'flat'
            entry_price = None
        
        # Track equity
        current_equity = cash + shares * price
        equity_curve.append(current_equity)
        
        if len(equity_curve) >= 2:
            daily_ret = (equity_curve[-1] / equity_curve[-2]) - 1
            daily_returns.append(daily_ret)
    
    # Close any open position
    if position == 'long' and shares > 0:
        price = df.iloc[-1]['close']
        date = df.index[-1]
        cost = TRANSACTION_COST_BPS / 10000
        proceeds = shares * price * (1 - cost)
        pnl = proceeds - (shares * entry_price)
        pnl_pct = (price / entry_price - 1) * 100
        hold_days = (date - entry_date).days
        
        trades.append({
            'entry_date': entry_date,
            'exit_date': date,
            'entry_price': entry_price,
            'exit_price': price,
            'hold_days': hold_days,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        })
        cash += proceeds
        shares = 0
    
    # Calculate metrics
    if len(daily_returns) < 10:
        return trades, None
    
    daily_returns = np.array(daily_returns)
    sharpe = calculate_sharpe_correct(daily_returns, rf=0.04, periods_per_year=252, min_samples=10)
    max_dd = calculate_max_drawdown(np.array(equity_curve))
    
    final_equity = equity_curve[-1]
    total_return = (final_equity / INITIAL_CAPITAL - 1) * 100
    
    # Buy and hold comparison
    buy_hold_return = (df.iloc[-1]['close'] / df.iloc[0]['close'] - 1) * 100
    
    metrics = {
        'total_return': total_return,
        'buy_hold_return': buy_hold_return,
        'outperformance': total_return - buy_hold_return,
        'sharpe': sharpe if sharpe else 0.0,
        'max_drawdown': max_dd * 100,
        'num_trades': len(trades),
        'pct_time_in_market': sum(1 for r in daily_returns if r != 0) / len(daily_returns) * 100
    }
    
    if len(trades) > 0:
        trades_df = pd.DataFrame(trades)
        stats = calculate_trade_stats(trades_df)
        metrics.update(stats)
    
    return trades, metrics


def run_wfa(symbols=MAG7, start_date='2020-01-01', end_date='2025-12-31'):
    """Run walk-forward analysis on equity hysteresis strategy."""
    
    print(f"[1/4] Fetching data for {len(symbols)} symbols...")
    alpaca = AlpacaDataClient()
    
    all_data = {}
    for symbol in symbols:
        try:
            df = alpaca.fetch_historical_bars(symbol, '1Day', start_date, end_date)
            all_data[symbol] = df
            print(f"  ✓ {symbol}: {len(df)} bars")
        except Exception as e:
            print(f"  ✗ {symbol}: Error - {e}")
    
    # Generate windows
    windows = generate_rolling_windows(start_date, end_date, train_months=6, test_months=6, step_months=6)
    print(f"\n[2/4] Running WFA with {len(windows)} windows...")
    print(f"      Symbols: {len(all_data)}")
    print(f"      Parameter combinations: {len(list(product(*PARAM_GRID.values())))}")
    
    all_results = []
    symbol_results = {s: [] for s in all_data.keys()}
    
    for window in windows:
        print(f"\n{'='*60}")
        print(f"Window {window.name}: Train {window.train_start} to {window.train_end}")
        print(f"           Test  {window.test_start} to {window.test_end}")
        print(f"{'='*60}")
        
        window_oos_sharpes = []
        
        for symbol, df in all_data.items():
            train_df = df[(df.index >= window.train_start) & (df.index <= window.train_end)]
            test_df = df[(df.index >= window.test_start) & (df.index <= window.test_end)]
            
            if len(train_df) < 50 or len(test_df) < 50:
                continue
            
            # Optimize on training data
            best_sharpe = -999
            best_params = None
            
            for combo in product(*PARAM_GRID.values()):
                params = {
                    'rsi_period': combo[0],
                    'hysteresis_upper': combo[1],
                    'hysteresis_lower': combo[2]
                }
                
                # Skip invalid combinations (upper must be > lower)
                if params['hysteresis_upper'] <= params['hysteresis_lower']:
                    continue
                
                _, metrics = backtest_hysteresis(train_df, params)
                
                if metrics and metrics['sharpe'] and metrics['sharpe'] > best_sharpe:
                    best_sharpe = metrics['sharpe']
                    best_params = params.copy()
            
            if best_params is None:
                continue
            
            # Test on OOS data
            oos_trades, oos_metrics = backtest_hysteresis(test_df, best_params)
            
            if oos_metrics and oos_metrics['sharpe']:
                window_oos_sharpes.append(oos_metrics['sharpe'])
                
                result = {
                    'window': window.name,
                    'symbol': symbol,
                    'train_start': window.train_start,
                    'train_end': window.train_end,
                    'test_start': window.test_start,
                    'test_end': window.test_end,
                    'is_sharpe': best_sharpe,
                    'oos_sharpe': oos_metrics['sharpe'],
                    'oos_return': oos_metrics['total_return'],
                    'oos_buy_hold': oos_metrics['buy_hold_return'],
                    'oos_outperformance': oos_metrics['outperformance'],
                    'oos_max_dd': oos_metrics['max_drawdown'],
                    'oos_trades': oos_metrics['num_trades'],
                    'oos_win_rate': oos_metrics.get('win_rate', 0),
                    **{f'param_{k}': v for k, v in best_params.items()}
                }
                
                all_results.append(result)
                symbol_results[symbol].append(result)
        
        if window_oos_sharpes:
            avg_sharpe = np.mean(window_oos_sharpes)
            print(f"  Window avg OOS Sharpe: {avg_sharpe:.2f} ({len(window_oos_sharpes)} symbols)")
    
    return all_results, symbol_results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--quick', action='store_true', help='Quick test (2024-2025 only)')
    parser.add_argument('--symbols', type=str, default=None, help='Comma-separated symbols')
    args = parser.parse_args()
    
    if args.quick:
        start_date = '2024-01-01'
        end_date = '2025-12-31'
        print("🚀 QUICK TEST MODE: 2024-2025 only\n")
    else:
        start_date = '2020-01-01'
        end_date = '2025-12-31'
    
    if args.symbols:
        symbols = args.symbols.split(',')
    else:
        symbols = MAG7
    
    # Run WFA
    results, symbol_results = run_wfa(symbols, start_date, end_date)
    
    if len(results) == 0:
        print("\n❌ No valid results generated")
        return
    
    results_df = pd.DataFrame(results)
    
    # Analysis
    print(f"\n\n{'='*80}")
    print("[3/4] WALK-FORWARD ANALYSIS RESULTS")
    print(f"{'='*80}\n")
    
    print("📊 Overall Performance:")
    print(f"  Total Symbol-Windows: {len(results_df)}")
    print(f"  Average OOS Sharpe: {results_df['oos_sharpe'].mean():.2f}")
    print(f"  Sharpe Std Dev: {results_df['oos_sharpe'].std():.2f}")
    print(f"  Min OOS Sharpe: {results_df['oos_sharpe'].min():.2f}")
    print(f"  Max OOS Sharpe: {results_df['oos_sharpe'].max():.2f}")
    print(f"  Average OOS Return: {results_df['oos_return'].mean():.1f}%")
    print(f"  Average Outperformance: {results_df['oos_outperformance'].mean():.1f}%")
    
    # By symbol
    print(f"\n📈 Performance by Symbol:")
    for symbol in symbols:
        sym_results = results_df[results_df['symbol'] == symbol]
        if len(sym_results) > 0:
            avg_sharpe = sym_results['oos_sharpe'].mean()
            avg_return = sym_results['oos_return'].mean()
            avg_outperf = sym_results['oos_outperformance'].mean()
            pct_positive = (sym_results['oos_sharpe'] > 0).mean() * 100
            print(f"  {symbol}: Sharpe {avg_sharpe:.2f}, Return {avg_return:+.1f}%, Outperf {avg_outperf:+.1f}%, {pct_positive:.0f}% positive")
    
    # Parameter stability
    print(f"\n🔧 Parameter Stability:")
    for param in ['rsi_period', 'hysteresis_upper', 'hysteresis_lower']:
        col = f'param_{param}'
        if col in results_df.columns:
            mode = results_df[col].mode()[0] if len(results_df[col].mode()) > 0 else 'N/A'
            unique = results_df[col].nunique()
            print(f"  {param}: Most common = {mode}, Unique values used = {unique}")
    
    # Save results
    output_dir = Path('research/backtests/phase4_audit/wfa_results')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results_df.to_csv(output_dir / 'daily_trend_hysteresis_wfa.csv', index=False)
    
    # Summary JSON
    summary = {
        'strategy': 'Daily Trend Hysteresis',
        'symbols': symbols,
        'period': f"{start_date} to {end_date}",
        'total_observations': len(results_df),
        'avg_oos_sharpe': float(results_df['oos_sharpe'].mean()),
        'sharpe_std': float(results_df['oos_sharpe'].std()),
        'avg_oos_return': float(results_df['oos_return'].mean()),
        'avg_outperformance': float(results_df['oos_outperformance'].mean()),
        'pct_positive_sharpe': float((results_df['oos_sharpe'] > 0).mean() * 100),
        'pct_outperform_buyhold': float((results_df['oos_outperformance'] > 0).mean() * 100)
    }
    
    with open(output_dir / 'daily_trend_hysteresis_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📁 Results saved to: {output_dir}/")
    
    # GO/NO-GO
    print(f"\n{'='*80}")
    print("[4/4] PRELIMINARY GO/NO-GO ASSESSMENT")
    print(f"{'='*80}\n")
    
    avg_sharpe = results_df['oos_sharpe'].mean()
    sharpe_std = results_df['oos_sharpe'].std()
    pct_positive = (results_df['oos_sharpe'] > 0).mean() * 100
    pct_outperform = (results_df['oos_outperformance'] > 0).mean() * 100
    
    if avg_sharpe >= 1.5 and pct_positive >= 80:
        print("✅ PRELIMINARY: GO")
        print("   Strategy shows robust performance across windows and symbols")
    elif avg_sharpe >= 1.0 and pct_positive >= 60:
        print("⚠️  PRELIMINARY: CONDITIONAL")
        print("   Strategy shows moderate performance")
        print(f"   Consider limiting to symbols with Sharpe > 1.0")
    elif avg_sharpe >= 0.5 and pct_outperform >= 50:
        print("⚠️  PRELIMINARY: CONDITIONAL (WEAK)")
        print("   Strategy beats buy-hold but has low absolute Sharpe")
    else:
        print("❌ PRELIMINARY: NO-GO")
        print(f"   Avg Sharpe {avg_sharpe:.2f}, only {pct_positive:.0f}% positive")
    
    print(f"\n📝 Key Metrics:")
    print(f"   Avg Sharpe: {avg_sharpe:.2f} (threshold: ≥1.0)")
    print(f"   % Positive Sharpe: {pct_positive:.0f}% (threshold: ≥60%)")
    print(f"   % Beat Buy-Hold: {pct_outperform:.0f}%")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
