"""
BATCH TEST: Strategy 2 (Hourly Swing) - Futures
Testing ES, NQ, CL, GC (via FMP)
RSI(28) 60/40 bands, Hourly timeframe
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
import requests
import os

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))
print(f"Project root: {project_root}")

from dotenv import load_dotenv
load_dotenv()

# Configuration
SYMBOLS = {
    'ES': 'ESUSD',
    'NQ': 'NQUSD',
    'CL': 'CLUSD',
    'GC': 'GCUSD'
}
RSI_PERIOD = 28
ENTRY_THRESHOLD = 60
EXIT_THRESHOLD = 40
CONTRACT_SIZE = 1
FRICTION_BASELINE_BPS = 10
FRICTION_DEGRADED_BPS = 20

TEST_PERIODS = [
    {'name': 'Primary', 'start': '2024-01-01', 'end': '2025-12-31'},
    {'name': 'Secondary', 'start': '2022-01-01', 'end': '2023-12-31'}
]

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.replace([np.inf, -np.inf], np.nan).fillna(50)
    return rsi

def fetch_futures_hourly(symbol, start, end):
    api_key = os.getenv('FMP_API_KEY')
    endpoint = f"https://financialmodelingprep.com/stable/historical-chart/1hour"
    params = {'symbol': symbol, 'apikey': api_key, 'from': start, 'to': end}
    
    response = requests.get(endpoint, params=params)
    response.raise_for_status()
    
    data = response.json()
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()
    
    return df[['open', 'high', 'low', 'close', 'volume']]

def run_backtest(df, friction_bps):
    df['rsi'] = calculate_rsi(df['close'], period=RSI_PERIOD)
    df['rsi_prev'] = df['rsi'].shift(1)
    
    position = 'flat'
    entry_price = None
    trades = []
    equity_curve = []
    initial_capital = 100000
    cash = initial_capital
    
    for idx in range(1, len(df)):
        current_price = df.iloc[idx]['close']
        current_rsi = df.iloc[idx]['rsi']
        prev_rsi = df.iloc[idx]['rsi_prev']
        
        if pd.isna(current_rsi) or pd.isna(prev_rsi):
            equity_curve.append(cash)
            continue
        
        if position == 'flat':
            if prev_rsi <= ENTRY_THRESHOLD and current_rsi > ENTRY_THRESHOLD:
                friction_cost = (friction_bps / 10000) * current_price * CONTRACT_SIZE
                entry_price = current_price
                position = 'long'
                cash -= friction_cost
        
        elif position == 'long':
            if prev_rsi >= EXIT_THRESHOLD and current_rsi < EXIT_THRESHOLD:
                friction_cost = (friction_bps / 10000) * current_price * CONTRACT_SIZE
                pnl_points = (current_price - entry_price) * CONTRACT_SIZE
                pnl_dollars = pnl_points - (friction_bps / 10000) * (entry_price + current_price) * CONTRACT_SIZE
                
                trades.append({'pnl_dollars': pnl_dollars})
                cash += pnl_dollars
                position = 'flat'
                entry_price = None
        
        if position == 'long':
            unrealized_pnl = (current_price - entry_price) * CONTRACT_SIZE
            equity_curve.append(cash + unrealized_pnl)
        else:
            equity_curve.append(cash)
    
    if position == 'long':
        current_price = df.iloc[-1]['close']
        friction_cost = (friction_bps / 10000) * current_price * CONTRACT_SIZE
        pnl_points = (current_price - entry_price) * CONTRACT_SIZE
        pnl_dollars = pnl_points - (friction_bps / 10000) * (entry_price + current_price) * CONTRACT_SIZE
        cash += pnl_dollars
    
    final_equity = equity_curve[-1] if equity_curve else initial_capital
    total_return = ((final_equity / initial_capital) - 1) * 100
    
    equity_series = pd.Series(equity_curve)
    running_max = equity_series.expanding().max()
    drawdown = (equity_series - running_max) / running_max
    max_dd = drawdown.min() * 100
    
    returns = equity_series.pct_change().dropna()
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252 * 6.5) if returns.std() > 0 else 0
    
    if trades:
        trades_df = pd.DataFrame(trades)
        winning_trades = trades_df[trades_df['pnl_dollars'] > 0]
        win_rate = (len(winning_trades) / len(trades)) * 100
        profit_factor = abs(winning_trades['pnl_dollars'].sum() / trades_df[trades_df['pnl_dollars'] <= 0]['pnl_dollars'].sum()) if len(trades_df[trades_df['pnl_dollars'] <= 0]) > 0 else np.inf
    else:
        win_rate = 0
        profit_factor = 0
    
    return {
        'total_return': total_return,
        'max_dd': max_dd,
        'sharpe': sharpe,
        'total_trades': len(trades),
        'win_rate': win_rate,
        'profit_factor': profit_factor
    }

print("=" * 80)
print("BATCH TEST: Strategy 2 (Hourly Swing) - Futures")
print("=" * 80)

all_results = []

for symbol_name, fmp_symbol in SYMBOLS.items():
    print(f"\n{'#' * 80}")
    print(f"TESTING: {symbol_name} ({fmp_symbol})")
    print(f"{'#' * 80}")
    
    for period in TEST_PERIODS:
        print(f"\n  Period: {period['name']} ({period['start']} to {period['end']})")
        
        try:
            df = fetch_futures_hourly(fmp_symbol, period['start'], period['end'])
            print(f"  ✓ Fetched {len(df)} hourly bars")
            
            result_baseline = run_backtest(df.copy(), FRICTION_BASELINE_BPS)
            print(f"  Baseline: {result_baseline['total_return']:+.2f}% | Sharpe: {result_baseline['sharpe']:.2f} | Trades: {result_baseline['total_trades']}")
            
            result_degraded = run_backtest(df.copy(), FRICTION_DEGRADED_BPS)
            print(f"  Degraded: {result_degraded['total_return']:+.2f}% | Sharpe: {result_degraded['sharpe']:.2f} | Trades: {result_degraded['total_trades']}")
            
            for result, friction_name in [(result_baseline, 'Baseline'), (result_degraded, 'Degraded')]:
                all_results.append({
                    'Symbol': symbol_name,
                    'Period': period['name'],
                    'Friction': friction_name,
                    'Return (%)': f"{result['total_return']:+.2f}",
                    'Sharpe': f"{result['sharpe']:.2f}",
                    'Max DD (%)': f"{result['max_dd']:.2f}",
                    'Trades': result['total_trades'],
                    'Win Rate (%)': f"{result['win_rate']:.1f}",
                    'PF': f"{result['profit_factor']:.2f}"
                })
            
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

output_dir = Path(__file__).parent / 'batch_results'
output_dir.mkdir(exist_ok=True)

summary_df = pd.DataFrame(all_results)
summary_df.to_csv(output_dir / 'strategy2_hourly_futures_summary.csv', index=False)

print(f"\n\n{'=' * 80}")
print("SUMMARY - Strategy 2 (Hourly Swing) - Futures")
print(f"{'=' * 80}\n")
print(summary_df.to_string(index=False))
print(f"\n✓ Results saved to: {output_dir / 'strategy2_hourly_futures_summary.csv'}")
