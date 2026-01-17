"""
BATCH TEST: Strategy 1 (Daily Trend) - ETFs & Crypto
Testing SPY, QQQ, BTC-USD, ETH-USD
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path
import requests
import os

# Fix project root path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))
print(f"Project root: {project_root}")

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

# Configuration
EQUITY_SYMBOLS = ['SPY', 'QQQ']
CRYPTO_SYMBOLS = ['BTCUSD', 'ETHUSD']  # FMP format
RSI_PERIOD = 28
ENTRY_THRESHOLD = 55
EXIT_THRESHOLD = 45
SHARES_PER_TRADE = 100
FRICTION_BASELINE_BPS = 1.5
FRICTION_DEGRADED_BPS = 5.0

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

def resample_to_daily(df):
    daily = df.resample('1D').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    return daily

def fetch_crypto_data(symbol, start, end):
    """Fetch crypto data from FMP"""
    api_key = os.getenv('FMP_API_KEY')
    endpoint = f"https://financialmodelingprep.com/stable/historical-price-eod/full/{symbol}"
    params = {'apikey': api_key, 'from': start, 'to': end}
    
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
    entry_date = None
    trades = []
    equity_curve = []
    initial_capital = 100000
    cash = initial_capital
    
    for idx in range(1, len(df)):
        current_date = df.index[idx]
        current_price = df.iloc[idx]['close']
        current_rsi = df.iloc[idx]['rsi']
        prev_rsi = df.iloc[idx]['rsi_prev']
        
        if pd.isna(current_rsi) or pd.isna(prev_rsi):
            equity_curve.append(cash)
            continue
        
        if position == 'flat':
            if prev_rsi <= ENTRY_THRESHOLD and current_rsi > ENTRY_THRESHOLD:
                friction_cost = (friction_bps / 10000) * current_price * SHARES_PER_TRADE
                entry_price = current_price
                entry_date = current_date
                position = 'long'
                cash -= (current_price * SHARES_PER_TRADE + friction_cost)
        
        elif position == 'long':
            if prev_rsi >= EXIT_THRESHOLD and current_rsi < EXIT_THRESHOLD:
                friction_cost = (friction_bps / 10000) * current_price * SHARES_PER_TRADE
                proceeds = current_price * SHARES_PER_TRADE - friction_cost
                pnl_dollars = proceeds - (entry_price * SHARES_PER_TRADE)
                pnl_pct = ((current_price / entry_price) - 1) * 100
                
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': current_date,
                    'pnl_pct': pnl_pct,
                    'pnl_dollars': pnl_dollars
                })
                
                cash += proceeds
                position = 'flat'
                entry_price = None
        
        if position == 'long':
            unrealized_pnl = (current_price - entry_price) * SHARES_PER_TRADE
            equity_curve.append(cash + unrealized_pnl)
        else:
            equity_curve.append(cash)
    
    if position == 'long':
        current_price = df.iloc[-1]['close']
        friction_cost = (friction_bps / 10000) * current_price * SHARES_PER_TRADE
        proceeds = current_price * SHARES_PER_TRADE - friction_cost
        pnl_dollars = proceeds - (entry_price * SHARES_PER_TRADE)
        cash += proceeds
    
    final_equity = equity_curve[-1] if equity_curve else initial_capital
    total_return = ((final_equity / initial_capital) - 1) * 100
    bh_return = ((df.iloc[-1]['close'] / df.iloc[0]['close']) - 1) * 100
    
    equity_series = pd.Series(equity_curve)
    running_max = equity_series.expanding().max()
    drawdown = (equity_series - running_max) / running_max
    max_dd = drawdown.min() * 100
    
    returns = equity_series.pct_change().dropna()
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
    
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
        'bh_return': bh_return,
        'max_dd': max_dd,
        'sharpe': sharpe,
        'total_trades': len(trades),
        'win_rate': win_rate,
        'profit_factor': profit_factor
    }

# Main execution
print("=" * 80)
print("BATCH TEST: Strategy 1 (Daily Trend) - ETFs & Crypto")
print("=" * 80)

all_results = []
client = AlpacaDataClient()

# Test ETFs
for symbol in EQUITY_SYMBOLS:
    print(f"\n{'#' * 80}")
    print(f"TESTING: {symbol} (ETF)")
    print(f"{'#' * 80}")
    
    for period in TEST_PERIODS:
        print(f"\n  Period: {period['name']} ({period['start']} to {period['end']})")
        
        try:
            raw_df = client.fetch_historical_bars(
                symbol=symbol,
                timeframe=TimeFrame.Day,
                start=period['start'],
                end=period['end'],
                feed='sip'
            )
            df = resample_to_daily(raw_df)
            print(f"  ✓ Fetched {len(df)} daily bars")
            
            # Baseline
            result_baseline = run_backtest(df.copy(), FRICTION_BASELINE_BPS)
            print(f"  Baseline: {result_baseline['total_return']:+.2f}% | Sharpe: {result_baseline['sharpe']:.2f} | Trades: {result_baseline['total_trades']}")
            
            # Degraded
            result_degraded = run_backtest(df.copy(), FRICTION_DEGRADED_BPS)
            print(f"  Degraded: {result_degraded['total_return']:+.2f}% | Sharpe: {result_degraded['sharpe']:.2f} | Trades: {result_degraded['total_trades']}")
            
            all_results.append({
                'Symbol': symbol,
                'Type': 'ETF',
                'Period': period['name'],
                'Friction': 'Baseline',
                'Return (%)': f"{result_baseline['total_return']:+.2f}",
                'B&H (%)': f"{result_baseline['bh_return']:+.2f}",
                'Sharpe': f"{result_baseline['sharpe']:.2f}",
                'Max DD (%)': f"{result_baseline['max_dd']:.2f}",
                'Trades': result_baseline['total_trades'],
                'Win Rate (%)': f"{result_baseline['win_rate']:.1f}",
                'PF': f"{result_baseline['profit_factor']:.2f}"
            })
            
            all_results.append({
                'Symbol': symbol,
                'Type': 'ETF',
                'Period': period['name'],
                'Friction': 'Degraded',
                'Return (%)': f"{result_degraded['total_return']:+.2f}",
                'B&H (%)': f"{result_degraded['bh_return']:+.2f}",
                'Sharpe': f"{result_degraded['sharpe']:.2f}",
                'Max DD (%)': f"{result_degraded['max_dd']:.2f}",
                'Trades': result_degraded['total_trades'],
                'Win Rate (%)': f"{result_degraded['win_rate']:.1f}",
                'PF': f"{result_degraded['profit_factor']:.2f}"
            })
            
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")

# Test Crypto
for symbol in CRYPTO_SYMBOLS:
    print(f"\n{'#' * 80}")
    print(f"TESTING: {symbol} (Crypto)")
    print(f"{'#' * 80}")
    
    for period in TEST_PERIODS:
        print(f"\n  Period: {period['name']} ({period['start']} to {period['end']})")
        
        try:
            df = fetch_crypto_data(symbol, period['start'], period['end'])
            print(f"  ✓ Fetched {len(df)} daily bars")
            
            # Baseline
            result_baseline = run_backtest(df.copy(), FRICTION_BASELINE_BPS)
            print(f"  Baseline: {result_baseline['total_return']:+.2f}% | Sharpe: {result_baseline['sharpe']:.2f} | Trades: {result_baseline['total_trades']}")
            
            # Degraded
            result_degraded = run_backtest(df.copy(), FRICTION_DEGRADED_BPS)
            print(f"  Degraded: {result_degraded['total_return']:+.2f}% | Sharpe: {result_degraded['sharpe']:.2f} | Trades: {result_degraded['total_trades']}")
            
            all_results.append({
                'Symbol': symbol,
                'Type': 'Crypto',
                'Period': period['name'],
                'Friction': 'Baseline',
                'Return (%)': f"{result_baseline['total_return']:+.2f}",
                'B&H (%)': f"{result_baseline['bh_return']:+.2f}",
                'Sharpe': f"{result_baseline['sharpe']:.2f}",
                'Max DD (%)': f"{result_baseline['max_dd']:.2f}",
                'Trades': result_baseline['total_trades'],
                'Win Rate (%)': f"{result_baseline['win_rate']:.1f}",
                'PF': f"{result_baseline['profit_factor']:.2f}"
            })
            
            all_results.append({
                'Symbol': symbol,
                'Type': 'Crypto',
                'Period': period['name'],
                'Friction': 'Degraded',
                'Return (%)': f"{result_degraded['total_return']:+.2f}",
                'B&H (%)': f"{result_degraded['bh_return']:+.2f}",
                'Sharpe': f"{result_degraded['sharpe']:.2f}",
                'Max DD (%)': f"{result_degraded['max_dd']:.2f}",
                'Trades': result_degraded['total_trades'],
                'Win Rate (%)': f"{result_degraded['win_rate']:.1f}",
                'PF': f"{result_degraded['profit_factor']:.2f}"
            })
            
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

# Save results
output_dir = Path(__file__).parent / 'batch_results'
output_dir.mkdir(exist_ok=True)

summary_df = pd.DataFrame(all_results)
summary_df.to_csv(output_dir / 'strategy1_etf_crypto_summary.csv', index=False)

print(f"\n\n{'=' * 80}")
print("SUMMARY - Strategy 1 (Daily Trend) - ETFs & Crypto")
print(f"{'=' * 80}\n")
print(summary_df.to_string(index=False))
print(f"\n✓ Results saved to: {output_dir / 'strategy1_etf_crypto_summary.csv'}")
