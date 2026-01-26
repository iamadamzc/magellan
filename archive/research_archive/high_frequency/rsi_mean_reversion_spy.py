"""
RSI Mean Reversion Strategy - SPY Intraday

Strategy:
- Buy when RSI(14) < 30 (oversold)
- Sell when RSI(14) > 70 (overbought)
- Or: Exit after 15 minutes (time stop)
- Target: 0.15% profit
- Stop: 0.15% loss

Holding period: 5-15 minutes (scalping/intraday)
Expected trades: 10-30 per day

Latency scenarios:
1. 67ms actual: 1 bps slippage
2. 500ms legacy: 3 bps slippage

Test on SPY 2024 data to validate if 67ms edge makes strategy profitable
"""

import requests
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json

load_dotenv()
FMP_API_KEY = os.getenv('FMP_API_KEY')

def fetch_1min_data(symbol, date):
    """Fetch 1-minute OHLCV data for a specific date"""
    url = "https://financialmodelingprep.com/stable/historical-chart/1min"
    params = {
        'symbol': symbol,
        'from': date,
        'to': date,
        'apikey': FMP_API_KEY
    }
    
    response = requests.get(url, params=params, timeout=10)
    if response.status_code == 200:
        return response.json()
    return []

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.convolve(gains, np.ones(period)/period, mode='valid')
    avg_loss = np.convolve(losses, np.ones(period)/period, mode='valid')
    
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    
    # Pad to match original length
    return np.concatenate([np.full(period, np.nan), rsi])

def backtest_rsi_strategy(bars, slippage_bps=1.0, max_hold_minutes=15):
    """
    Backtest RSI mean reversion on 1-minute bars
    
    Entry: RSI < 30 (buy) or RSI > 70 (sell short)
    Exit: Opposite signal, profit target (0.15%), stop loss (0.15%), or time (15 min)
    """
    if len(bars) < 20:
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(bars)
    df['time'] = pd.to_datetime(df['date'])
    df = df.sort_values('time').reset_index(drop=True)
    
    # Calculate RSI
    closes = df['close'].values
    df['rsi'] = calculate_rsi(closes, period=14)
    
    # Backtest
    trades = []
    position = None  # {type: 'long'/'short', entry_price, entry_time, entry_idx}
    
    for i in range(20, len(df)):  # Start after RSI warm-up
        current_row = df.iloc[i]
        rsi = current_row['rsi']
        price = current_row['close']
        time = current_row['time']
        
        # Check exit conditions first
        if position:
            entry_price = position['entry_price']
            entry_time = position['entry_time']
            hold_minutes = (time - entry_time).total_seconds() / 60
            
            pnl_pct = 0
            exit_reason = None
            
            if position['type'] == 'long':
                pnl_pct = (price - entry_price) / entry_price * 100
                
                # Exit conditions
                if rsi > 70:
                    exit_reason = 'rsi_signal'
                elif pnl_pct >= 0.15:
                    exit_reason = 'profit_target'
                elif pnl_pct <= -0.15:
                    exit_reason = 'stop_loss'
                elif hold_minutes >= max_hold_minutes:
                    exit_reason = 'time_stop'
            
            elif position['type'] == 'short':
                pnl_pct = (entry_price - price) / entry_price * 100
                
                # Exit conditions
                if rsi < 30:
                    exit_reason = 'rsi_signal'
                elif pnl_pct >= 0.15:
                    exit_reason = 'profit_target'
                elif pnl_pct <= -0.15:
                    exit_reason = 'stop_loss'
                elif hold_minutes >= max_hold_minutes:
                    exit_reason = 'time_stop'
            
            if exit_reason:
                # Apply slippage
                pnl_pct -= slippage_bps / 100  # Entry slippage
                pnl_pct -= slippage_bps / 100  # Exit slippage
                
                trades.append({
                    'type': position['type'],
                    'entry_time': entry_time,
                    'entry_price': entry_price,
                    'exit_time': time,
                    'exit_price': price,
                    'hold_minutes': hold_minutes,
                    'pnl_pct': pnl_pct,
                    'exit_reason': exit_reason,
                    'win': pnl_pct > 0
                })
                
                position = None
        
        # Entry signals (only if no position)
        if not position:
            if rsi < 30:  # Oversold - buy
                position = {
                    'type': 'long',
                    'entry_price': price,
                    'entry_time': time,
                    'entry_idx': i
                }
            elif rsi > 70:  # Overbought - sell short
                position = {
                    'type': 'short',
                    'entry_price': price,
                    'entry_time': time,
                    'entry_idx': i
                }
    
    return trades

# Backtest on sample of 2024 trading days
print("="*80)
print("RSI MEAN REVERSION BACKTEST - SPY")
print("="*80)

# Test on 5 random trading days from 2024
test_dates = [
    '2024-03-15',  # Mid-March
    '2024-05-20',  # May
    '2024-07-10',  # Summer
    '2024-09-18',  # September (FOMC day - volatile!)
    '2024-11-15',  # Fall
]

all_trades_67ms = []
all_trades_500ms = []

print("\nFetching data and backtesting...")

for date in test_dates:
    print(f"\n{date}...", end='')
    
    bars = fetch_1min_data('SPY', date)
    
    if not bars or len(bars) < 50:
        print(" ❌ Insufficient data")
        continue
    
    print(f" ✅ {len(bars)} bars")
    
    # Test with 67ms latency (1 bps slippage)
    trades_67 = backtest_rsi_strategy(bars, slippage_bps=1.0)
    if trades_67:
        all_trades_67ms.extend(trades_67)
        print(f"  67ms scenario:  {len(trades_67):2d} trades")
    
    # Test with 500ms latency (3 bps slippage)
    trades_500 = backtest_rsi_strategy(bars, slippage_bps=3.0)
    if trades_500:
        all_trades_500ms.extend(trades_500)
        print(f"  500ms scenario: {len(trades_500):2d} trades")

# Calculate metrics
def calculate_metrics(trades, scenario_name):
    if not trades:
        return None
    
    pnls = [t['pnl_pct'] for t in trades]
    wins = [t for t in trades if t['win']]
    
    avg_pnl = np.mean(pnls)
    std_pnl = np.std(pnls)
    sharpe = (avg_pnl / std_pnl * np.sqrt(252 * 78)) if std_pnl > 0 else 0  # Annualized (78 bars/day avg)
    win_rate = len(wins) / len(trades) * 100
    
    return {
        'scenario': scenario_name,
        'trades': len(trades),
        'win_rate': win_rate,
        'avg_pnl': avg_pnl,
        'std_pnl': std_pnl,
        'sharpe': sharpe,
        'best_trade': max(pnls),
        'worst_trade': min(pnls),
        'total_return': sum(pnls)
    }

# Results
print("\n" + "="*80)
print("RESULTS COMPARISON")
print("="*80)

metrics_67 = calculate_metrics(all_trades_67ms, "67ms (actual latency)")
metrics_500 = calculate_metrics(all_trades_500ms, "500ms (legacy assumption)")

print(f"\n{'Metric':<20s} | {'67ms (Actual)':>15s} | {'500ms (Legacy)':>15s} | {'Difference':>12s}")
print("-" * 80)

if metrics_67 and metrics_500:
    for key in ['trades', 'win_rate', 'avg_pnl', 'sharpe', 'total_return']:
        val_67 = metrics_67[key]
        val_500 = metrics_500[key]
        diff = val_67 - val_500
        
        if key == 'trades':
            print(f"{key:<20s} | {val_67:>15.0f} | {val_500:>15.0f} | {diff:>12.0f}")
        elif key in ['win_rate', 'total_return']:
            print(f"{key:<20s} | {val_67:>14.1f}% | {val_500:>14.1f}% | {diff:>11.1f}%")
        else:
            print(f"{key:<20s} | {val_67:>15.2f} | {val_500:>15.2f} | {diff:>12.2f}")

# GO/NO-GO Decision
print("\n" + "="*80)
print("GO/NO-GO DECISION")
print("="*80)

if metrics_67:
    sharpe_67 = metrics_67['sharpe']
    
    if sharpe_67 >= 1.0:
        print(f"\n✅ **GO** - Sharpe {sharpe_67:.2f} with 67ms latency")
        print("   67ms latency makes RSI mean reversion profitable!")
    elif sharpe_67 >= 0.5:
        print(f"\n⚠️  **CONDITIONAL** - Sharpe {sharpe_67:.2f} is marginal")
        print("   Needs more testing or parameter optimization")
    else:
        print(f"\n❌ **NO-GO** - Sharpe {sharpe_67:.2f} below threshold")
        print("   Even with 67ms, strategy is not profitable")
        
    if metrics_500:
        sharpe_500 = metrics_500['sharpe']
        improvement = sharpe_67 - sharpe_500
        print(f"\n💡 Latency Impact: Sharpe improved by {improvement:.2f} ({improvement/sharpe_500*100 if sharpe_500 > 0 else 0:.1f}%)")

# Save results
results = {
    'strategy': 'RSI Mean Reversion',
    'symbol': 'SPY',
    'test_dates': test_dates,
    'scenarios': {
        '67ms': metrics_67,
        '500ms': metrics_500
    },
    'trades_67ms': all_trades_67ms[:20],  # Sample
    'trades_500ms': all_trades_500ms[:20]
}

with open('rsi_mean_reversion_results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

print(f"\n✅ Saved results to rsi_mean_reversion_results.json")
