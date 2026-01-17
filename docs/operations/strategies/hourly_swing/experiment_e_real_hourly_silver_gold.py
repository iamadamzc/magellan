"""
EXPERIMENT E: Silver + Gold Hourly Swing with REAL Data
Test hourly RSI strategy with actual 1-hour bars (not simulated)

Based on TESTING_ASSESSMENT findings:
- MSI (Silver) hourly showed Sharpe 2.67 (exceptional)
- MGC (Gold) hourly showed Sharpe 1.84 (excellent)
- COMPREHENSIVE used SIMULATED hourly (resampled from daily)

This experiment uses REAL hourly data from FMP
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path
import requests
import os

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

print("=" * 80)
print("EXPERIMENT E: Silver + Gold Hourly with REAL Data")
print("=" * 80)
print("Assets: SIUSD (Silver), GCUSD (Gold)")
print("Data: Real 1-hour bars from FMP")
print("Strategy: RSI 60/40 hysteresis")
print("=" * 80)

# Configuration
ASSETS = {
    'SIUSD': 'Silver',
    'GCUSD': 'Gold'
}

RSI_PERIOD = 28
ENTRY_THRESHOLD = 60
EXIT_THRESHOLD = 40
FRICTION_BASELINE_BPS = 10
FRICTION_DEGRADED_BPS = 20

TEST_PERIODS = [
    {'name': 'Primary', 'start': '2024-01-01', 'end': '2025-12-31'},
    {'name': 'Secondary', 'start': '2022-01-01', 'end': '2023-12-31'}
]

def fetch_real_hourly_data(symbol, start, end):
    """Fetch REAL hourly data from FMP"""
    api_key = os.getenv('FMP_API_KEY')
    
    url = "https://financialmodelingprep.com/stable/historical-chart/1hour"
    
    params = {
        'symbol': symbol,
        'from': start,
        'to': end,
        'apikey': api_key
    }
    
    print(f"  Fetching from: {url}")
    print(f"  Symbol: {symbol}, Period: {start} to {end}")
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    data = response.json()
    
    if not data or len(data) == 0:
        raise ValueError(f"No data returned for {symbol}")
    
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    df = df.sort_index()
    
    # Select OHLCV columns
    df = df[['open', 'high', 'low', 'close', 'volume']]
    
    return df

def calculate_rsi(prices, period=14):
    """Calculate RSI using Wilder's smoothing"""
    delta = prices.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    
    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    
    rsi = rsi.replace([np.inf, -np.inf], np.nan)
    rsi = rsi.fillna(50)
    
    return rsi

def run_backtest(df, friction_bps, test_name):
    """Run hourly swing backtest"""
    
    print(f"\n  Running: {test_name} ({friction_bps} bps)")
    
    # Calculate RSI
    df['rsi'] = calculate_rsi(df['close'], period=RSI_PERIOD)
    df['rsi_prev'] = df['rsi'].shift(1)
    
    # Initialize tracking
    position = 'flat'
    entry_price = None
    entry_date = None
    trades = []
    equity_curve = []
    initial_capital = 100000
    cash = initial_capital
    contract_size = 1
    
    # Backtest loop
    for idx in range(1, len(df)):
        current_date = df.index[idx]
        current_price = df.iloc[idx]['close']
        current_rsi = df.iloc[idx]['rsi']
        prev_rsi = df.iloc[idx]['rsi_prev']
        
        if pd.isna(current_rsi) or pd.isna(prev_rsi):
            equity_curve.append(cash)
            continue
        
        # ENTRY: Strict crossover above 60
        if position == 'flat':
            if prev_rsi <= ENTRY_THRESHOLD and current_rsi > ENTRY_THRESHOLD:
                friction_cost = (friction_bps / 10000) * current_price * contract_size
                entry_price = current_price
                entry_date = current_date
                position = 'long'
                cash -= friction_cost
        
        # EXIT: Strict crossover below 40
        elif position == 'long':
            if prev_rsi >= EXIT_THRESHOLD and current_rsi < EXIT_THRESHOLD:
                friction_cost = (friction_bps / 10000) * current_price * contract_size
                pnl_points = (current_price - entry_price) * contract_size
                pnl_dollars = pnl_points - (friction_bps / 10000) * (entry_price + current_price) * contract_size
                pnl_pct = ((current_price / entry_price) - 1) * 100
                hold_hours = (current_date - entry_date).total_seconds() / 3600
                
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': current_date,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'pnl_dollars': pnl_dollars,
                    'pnl_pct': pnl_pct,
                    'hold_hours': hold_hours
                })
                
                cash += pnl_dollars
                position = 'flat'
                entry_price = None
                entry_date = None
        
        # Track equity
        if position == 'long':
            unrealized_pnl = (current_price - entry_price) * contract_size
            equity_curve.append(cash + unrealized_pnl)
        else:
            equity_curve.append(cash)
    
    # Close any open position
    if position == 'long':
        current_price = df.iloc[-1]['close']
        current_date = df.index[-1]
        friction_cost = (friction_bps / 10000) * current_price * contract_size
        pnl_points = (current_price - entry_price) * contract_size
        pnl_dollars = pnl_points - (friction_bps / 10000) * (entry_price + current_price) * contract_size
        pnl_pct = ((current_price / entry_price) - 1) * 100
        hold_hours = (current_date - entry_date).total_seconds() / 3600
        
        trades.append({
            'entry_date': entry_date,
            'exit_date': current_date,
            'entry_price': entry_price,
            'exit_price': current_price,
            'pnl_dollars': pnl_dollars,
            'pnl_pct': pnl_pct,
            'hold_hours': hold_hours
        })
        
        cash += pnl_dollars
    
    # Calculate metrics
    final_equity = equity_curve[-1] if equity_curve else initial_capital
    total_return = ((final_equity / initial_capital) - 1) * 100
    
    # Max Drawdown
    equity_series = pd.Series(equity_curve)
    running_max = equity_series.expanding().max()
    drawdown = (equity_series - running_max) / running_max
    max_dd = drawdown.min() * 100
    
    # Sharpe Ratio (annualize for hourly: sqrt(252 * 6.5))
    if len(equity_curve) > 1:
        returns = equity_series.pct_change().dropna()
        sharpe = (returns.mean() / returns.std()) * np.sqrt(1638) if returns.std() > 0 else 0
    else:
        sharpe = 0
    
    # Trade statistics
    if trades:
        trades_df = pd.DataFrame(trades)
        winning_trades = trades_df[trades_df['pnl_dollars'] > 0]
        win_rate = (len(winning_trades) / len(trades)) * 100
        avg_hold = trades_df['hold_hours'].mean()
    else:
        win_rate = 0
        avg_hold = 0
    
    print(f"    Return: {total_return:+.2f}% | Sharpe: {sharpe:.2f} | Trades: {len(trades)} | Win Rate: {win_rate:.1f}%")
    
    return {
        'total_return': total_return,
        'max_dd': max_dd,
        'sharpe': sharpe,
        'total_trades': len(trades),
        'win_rate': win_rate,
        'avg_hold_hours': avg_hold
    }

# Run tests
all_results = []

for symbol, name in ASSETS.items():
    print(f"\n{'#' * 80}")
    print(f"TESTING: {name} ({symbol})")
    print(f"{'#' * 80}")
    
    for period in TEST_PERIODS:
        print(f"\n  Period: {period['name']} ({period['start']} to {period['end']})")
        
        try:
            # Fetch REAL hourly data
            df = fetch_real_hourly_data(symbol, period['start'], period['end'])
            print(f"  ✓ Fetched {len(df)} REAL hourly bars")
            
            # Run baseline test
            baseline_result = run_backtest(df.copy(), FRICTION_BASELINE_BPS, 'Baseline')
            baseline_result['symbol'] = symbol
            baseline_result['name'] = name
            baseline_result['period'] = period['name']
            baseline_result['friction'] = 'baseline'
            all_results.append(baseline_result)
            
            # Run degraded test
            degraded_result = run_backtest(df.copy(), FRICTION_DEGRADED_BPS, 'Degraded')
            degraded_result['symbol'] = symbol
            degraded_result['name'] = name
            degraded_result['period'] = period['name']
            degraded_result['friction'] = 'degraded'
            all_results.append(degraded_result)
        
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

# Summary
print(f"\n\n{'#' * 80}")
print("EXPERIMENT E SUMMARY - REAL HOURLY DATA")
print(f"{'#' * 80}")

summary_df = pd.DataFrame([{
    'Asset': r['name'],
    'Period': r['period'],
    'Friction': r['friction'],
    'Return (%)': f"{r['total_return']:+.2f}",
    'Sharpe': f"{r['sharpe']:.2f}",
    'Max DD (%)': f"{r['max_dd']:.2f}",
    'Trades': r['total_trades'],
    'Win Rate (%)': f"{r['win_rate']:.1f}",
    'Avg Hold (hrs)': f"{r['avg_hold_hours']:.1f}"
} for r in all_results])

print("\n" + summary_df.to_string(index=False))

# Save results
output_dir = Path(__file__).parent
summary_df.to_csv(output_dir / 'experiment_e_results.csv', index=False)

print(f"\n✓ Results saved to: {output_dir / 'experiment_e_results.csv'}")
print("\nDone!")
