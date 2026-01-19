"""
Opening Range Breakout - Multi-Asset Class Testing

Strategy Concept:
- First 15-30 minutes define the "opening range"
- Buy breakout above range high
- Sell breakout below range low
- Momentum continuation play

Entry signals:
1. Price breaks above opening range high → Long
2. Price breaks below opening range low → Short

Exit signals:
1. Profit target (0.20-0.40%)
2. Stop loss (0.15-0.25%)
3. End of day or timeout (30-60 min)
4. Return to opening range

Test on: SPY, QQQ, IWM, NVDA, TSLA, ES, NQ
Friction: 1.0 bps (realistic)
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import os

load_dotenv()
FMP_API_KEY = os.getenv('FMP_API_KEY')
FRICTION_BPS = 1.0

def fetch_1min_data(symbol, date):
    url = "https://financialmodelingprep.com/stable/historical-chart/1min"
    params = {'symbol': symbol, 'from': date, 'to': date, 'apikey': FMP_API_KEY}
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

def opening_range_breakout(df, range_minutes=15, profit_target=0.30, 
                           stop_loss=0.20, hold_minutes=60):
    """
    Opening Range Breakout Strategy
    
    Define range in first 15-30 minutes
    Trade breakouts with momentum
    """
    if len(df) < 50:
        return []
    
    df['time'] = pd.to_datetime(df['date'])
    df['hour'] = df['time'].dt.hour
    df['minute'] = df['time'].dt.minute
    
    # Find market open (9:30 AM)
    open_idx = None
    for i in range(len(df)):
        if df.loc[i, 'hour'] == 9 and df.loc[i, 'minute'] >= 30:
            open_idx = i
            break
    
    if open_idx is None or open_idx + range_minutes >= len(df):
        return []
    
    # Calculate opening range
    range_end_idx = open_idx + range_minutes
    opening_high = df.loc[open_idx:range_end_idx, 'high'].max()
    opening_low = df.loc[open_idx:range_end_idx, 'low'].min()
    
    trades = []
    position = None
    
    for i in range(range_end_idx + 1, len(df)):
        if position:
            hold_min = i - position['entry_idx']
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            exit_reason = None
            
            # Profit target
            if pnl_pct >= profit_target:
                exit_reason = 'target'
            # Stop loss
            elif pnl_pct <= -stop_loss:
                exit_reason = 'stop_loss'
            # Return to range (failed breakout)
            elif position['type'] == 'long' and df.loc[i, 'close'] < opening_high:
                exit_reason = 'return_to_range'
            elif position['type'] == 'short' and df.loc[i, 'close'] > opening_low:
                exit_reason = 'return_to_range'
            # Timeout
            elif hold_min >= hold_minutes:
                exit_reason = 'timeout'
            # End of day (3:30 PM)
            elif df.loc[i, 'hour'] >= 15 and df.loc[i, 'minute'] >= 30:
                exit_reason = 'eod'
            
            if exit_reason:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({'pnl_pct': pnl_pct, 'win': pnl_pct > 0})
                position = None
        
        if not position:
            # Long breakout above opening range
            if df.loc[i, 'close'] > opening_high:
                position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
            
            # Short breakout below opening range
            elif df.loc[i, 'close'] < opening_low:
                position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
    
    return trades

def generate_trading_days(start_date, end_date):
    current = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    trading_days = []
    while current <= end:
        if current.weekday() < 5:
            trading_days.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    return trading_days

print("="*80)
print("OPENING RANGE BREAKOUT - MULTI-ASSET CLASS TESTING")
print("="*80)

test_dates = generate_trading_days('2024-01-02', '2024-03-31')
symbols = ['SPY', 'QQQ', 'IWM', 'NVDA', 'TSLA', 'ES', 'NQ']

print(f"\nTesting on Q1 2024: {len(test_dates)} potential days")
print(f"Assets: {', '.join(symbols)}")
print(f"Friction: {FRICTION_BPS} bps")

all_results = {}

for symbol in symbols:
    print(f"\n{'='*80}")
    print(f"TESTING {symbol}")
    print(f"{'='*80}")
    
    print(f"Loading {symbol} data...")
    symbol_dfs = []
    loaded = 0
    
    for date in test_dates[:30]:
        bars = fetch_1min_data(symbol, date)
        if len(bars) >= 50:
            symbol_dfs.append(pd.DataFrame(bars).sort_values('date').reset_index(drop=True))
            loaded += 1
    
    print(f"Loaded {loaded} days")
    
    if loaded < 10:
        print(f"⚠️  Insufficient data for {symbol}")
        continue
    
    # Run strategy
    all_trades = []
    for df in symbol_dfs:
        trades = opening_range_breakout(df.copy())
        all_trades.extend(trades)
    
    if all_trades and len(all_trades) >= 5:
        pnls = [t['pnl_pct'] for t in all_trades]
        wins = [t for t in all_trades if t['win']]
        losses = [t for t in all_trades if not t['win']]
        
        avg_pnl = np.mean(pnls)
        std_pnl = np.std(pnls)
        sharpe = (avg_pnl / std_pnl * np.sqrt(252 * len(all_trades) / loaded)) if std_pnl > 0 else 0
        win_rate = len(wins) / len(all_trades) * 100
        trades_per_day = len(all_trades) / loaded
        
        avg_win = np.mean([t['pnl_pct'] for t in wins]) if wins else 0
        avg_loss = np.mean([t['pnl_pct'] for t in losses]) if losses else 0
        
        all_results[symbol] = {
            'trades': len(all_trades),
            'trades_per_day': trades_per_day,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'sharpe': sharpe,
            'total_return': sum(pnls)
        }
        
        print(f"\nResults:")
        print(f"  Trades: {len(all_trades)} ({trades_per_day:.1f}/day)")
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  Avg Win: {avg_win:.3f}%")
        print(f"  Avg Loss: {avg_loss:.3f}%")
        print(f"  Sharpe: {sharpe:.2f}")
        print(f"  Total Return: {sum(pnls):.2f}%")
    else:
        print(f"⚠️  Insufficient trades: {len(all_trades) if all_trades else 0}")

# Summary
print(f"\n{'='*80}")
print("MULTI-ASSET COMPARISON")
print(f"{'='*80}")

if all_results:
    print(f"\n{'Symbol':<8s} | {'Trades':>7s} | {'T/Day':>6s} | {'Win%':>6s} | {'Avg Win':>8s} | {'Avg Loss':>9s} | {'Sharpe':>7s}")
    print("-" * 80)
    
    sorted_symbols = sorted(all_results.items(), key=lambda x: x[1]['sharpe'], reverse=True)
    
    for symbol, r in sorted_symbols:
        status = "✅" if r['sharpe'] > 0 else "⚠️" if r['sharpe'] > -2 else "❌"
        print(f"{symbol:<8s} | {r['trades']:>7d} | {r['trades_per_day']:>6.1f} | {r['win_rate']:>5.1f}% | {r['avg_win']:>7.3f}% | {r['avg_loss']:>8.3f}% | {r['sharpe']:>7.2f} {status}")
    
    best_symbol, best_result = sorted_symbols[0]
    
    print(f"\n{'='*80}")
    print(f"BEST ASSET: {best_symbol}")
    print(f"{'='*80}")
    print(f"Sharpe: {best_result['sharpe']:.2f}")
    print(f"Win Rate: {best_result['win_rate']:.1f}%")
    print(f"Avg Win: {best_result['avg_win']:.3f}%")
    print(f"Avg Loss: {best_result['avg_loss']:.3f}%")
    
    if best_result['sharpe'] > 0:
        print(f"\n🎯 **PROFITABLE on {best_symbol}!** Test on full 2024+2025")
    else:
        print(f"\n❌ No profitable assets - Opening Range Breakout doesn't work")

# Save
with open('opening_range_breakout_multi_asset_results.json', 'w') as f:
    json.dump(all_results, f, indent=2)

print(f"\n✅ Saved to opening_range_breakout_multi_asset_results.json")
