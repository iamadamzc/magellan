"""
Liquidity Grab V4 - Let Winners Run!

Key insight: Avg win (0.042%) is 6x smaller than avg loss (-0.249%)
Even with 60% win rate, this loses money.

Solution: REMOVE profit targets, let winners run until:
1. Price reverses (trailing stop)
2. Momentum fades
3. Much longer timeout (30+ minutes)

Use REALISTIC friction: 1.0 bps (not 4.1 bps)
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
FRICTION_BPS = 1.0  # REALISTIC friction

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

def liquidity_grab_v4_let_winners_run(df, lookback=10, rejection_bars=3,
                                      stop_loss=0.20, trail_distance=0.08,
                                      hold_minutes=45, momentum_exit_threshold=-0.05):
    """
    V4: NO profit targets - let winners run!
    
    Exit only when:
    - Trailing stop hit (price reverses by trail_distance from peak)
    - Momentum turns against us
    - Long timeout (45 min)
    - Hard stop loss
    """
    if len(df) < 30:
        return []
    
    df['high_roll'] = df['high'].rolling(lookback).max()
    df['low_roll'] = df['low'].rolling(lookback).min()
    df['upper_wick'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['close'] * 100
    df['lower_wick'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['close'] * 100
    df['time'] = pd.to_datetime(df['date'])
    df['hour'] = df['time'].dt.hour
    df['momentum_3'] = (df['close'] - df['close'].shift(3)) / df['close'].shift(3) * 100
    
    trades = []
    position = None
    
    for i in range(lookback + 5, len(df)):
        if position:
            hold_min = i - position['entry_idx']
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            # Update peak
            if pnl_pct > position['peak_pnl']:
                position['peak_pnl'] = pnl_pct
            
            exit_reason = None
            
            # Trailing stop from peak
            if pnl_pct < position['peak_pnl'] - trail_distance:
                exit_reason = 'trailing_stop'
            
            # Momentum reversal
            elif pd.notna(df.loc[i, 'momentum_3']):
                if position['type'] == 'long' and df.loc[i, 'momentum_3'] < momentum_exit_threshold:
                    exit_reason = 'momentum_reversal'
                elif position['type'] == 'short' and df.loc[i, 'momentum_3'] > -momentum_exit_threshold:
                    exit_reason = 'momentum_reversal'
            
            # Hard stop
            if pnl_pct <= -stop_loss:
                exit_reason = 'stop_loss'
            
            # Timeout
            elif hold_min >= hold_minutes:
                exit_reason = 'timeout'
            
            if exit_reason:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({
                    'pnl_pct': pnl_pct,
                    'win': pnl_pct > 0,
                    'hold_min': hold_min,
                    'exit_reason': exit_reason,
                    'peak_pnl': position['peak_pnl']
                })
                position = None
        
        if not position:
            if 12 <= df.loc[i, 'hour'] < 14:
                continue
            
            # Pattern 1: Break high then reject
            if i >= rejection_bars:
                recent_high = df.loc[i-rejection_bars:i-1, 'high'].max()
                prev_high_roll = df.loc[i-1, 'high_roll']
                
                if recent_high > prev_high_roll and df.loc[i, 'close'] < prev_high_roll:
                    position = {
                        'type': 'short',
                        'entry_price': df.loc[i, 'close'],
                        'entry_idx': i,
                        'peak_pnl': 0
                    }
                    continue
            
            # Pattern 2: Break low then reclaim
            if i >= rejection_bars:
                recent_low = df.loc[i-rejection_bars:i-1, 'low'].min()
                prev_low_roll = df.loc[i-1, 'low_roll']
                
                if recent_low < prev_low_roll and df.loc[i, 'close'] > prev_low_roll:
                    position = {
                        'type': 'long',
                        'entry_price': df.loc[i, 'close'],
                        'entry_idx': i,
                        'peak_pnl': 0
                    }
                    continue
            
            # Pattern 3: Large wick
            if df.loc[i, 'upper_wick'] > 0.10:
                position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i, 'peak_pnl': 0}
            elif df.loc[i, 'lower_wick'] > 0.10:
                position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i, 'peak_pnl': 0}
    
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
print("LIQUIDITY GRAB V4 - LET WINNERS RUN (1.0 BPS FRICTION)")
print("="*80)

test_dates = generate_trading_days('2024-01-02', '2024-03-31')
print(f"\nTesting on Q1 2024: {len(test_dates)} potential days")
print(f"Friction: {FRICTION_BPS} bps (REALISTIC)")

print("Loading data...")
all_dfs = []
for date in test_dates[:30]:
    bars = fetch_1min_data('SPY', date)
    if len(bars) >= 50:
        all_dfs.append(pd.DataFrame(bars).sort_values('date').reset_index(drop=True))

print(f"Loaded {len(all_dfs)} days of data")

# Parameter grid - focus on letting winners run
param_grid = [
    # Tight trailing, long hold
    {'lookback': 10, 'rejection_bars': 3, 'stop_loss': 0.20, 'trail_distance': 0.06, 'hold_minutes': 45, 'momentum_exit_threshold': -0.08},
    {'lookback': 10, 'rejection_bars': 3, 'stop_loss': 0.20, 'trail_distance': 0.08, 'hold_minutes': 60, 'momentum_exit_threshold': -0.10},
    
    # Loose trailing, very long hold
    {'lookback': 10, 'rejection_bars': 3, 'stop_loss': 0.25, 'trail_distance': 0.10, 'hold_minutes': 60, 'momentum_exit_threshold': -0.12},
    {'lookback': 10, 'rejection_bars': 3, 'stop_loss': 0.25, 'trail_distance': 0.12, 'hold_minutes': 90, 'momentum_exit_threshold': -0.15},
    
    # Moderate
    {'lookback': 10, 'rejection_bars': 3, 'stop_loss': 0.22, 'trail_distance': 0.08, 'hold_minutes': 50, 'momentum_exit_threshold': -0.10},
]

results = []

print("\nTesting 'let winners run' configurations...")
for idx, params in enumerate(param_grid, 1):
    all_trades = []
    
    for df in all_dfs:
        trades = liquidity_grab_v4_let_winners_run(df.copy(), **params)
        all_trades.extend(trades)
    
    if all_trades and len(all_trades) >= 5:
        pnls = [t['pnl_pct'] for t in all_trades]
        wins = [t for t in all_trades if t['win']]
        losses = [t for t in all_trades if not t['win']]
        
        avg_pnl = np.mean(pnls)
        std_pnl = np.std(pnls)
        sharpe = (avg_pnl / std_pnl * np.sqrt(252 * len(all_trades) / len(all_dfs))) if std_pnl > 0 else 0
        win_rate = len(wins) / len(all_trades) * 100
        trades_per_day = len(all_trades) / len(all_dfs)
        
        avg_win = np.mean([t['pnl_pct'] for t in wins]) if wins else 0
        avg_loss = np.mean([t['pnl_pct'] for t in losses]) if losses else 0
        avg_peak = np.mean([t['peak_pnl'] for t in all_trades])
        
        result = {
            'config': idx,
            'params': params,
            'trades': len(all_trades),
            'trades_per_day': trades_per_day,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_peak': avg_peak,
            'sharpe': sharpe,
            'total_return': sum(pnls)
        }
        results.append(result)
        
        print(f"\nConfig {idx}: Trail={params['trail_distance']:.2f}%, Hold={params['hold_minutes']}min")
        print(f"  Trades: {len(all_trades)} ({trades_per_day:.1f}/day) | Win%: {win_rate:.1f}% | Sharpe: {sharpe:.2f}")
        print(f"  Avg Win: {avg_win:.3f}% | Avg Loss: {avg_loss:.3f}% | Avg Peak: {avg_peak:.3f}%")
    else:
        print(f"\nConfig {idx}: Insufficient trades ({len(all_trades) if all_trades else 0})")

# Summary
print("\n" + "="*80)
print("V4 'LET WINNERS RUN' RESULTS")
print("="*80)

if results:
    sorted_results = sorted(results, key=lambda x: x['sharpe'], reverse=True)
    
    print(f"\nTop 3 by Sharpe:")
    print(f"{'Rank':<5s} | {'Trail':>7s} | {'Hold':>7s} | {'Trades/Day':>11s} | {'Win%':>6s} | {'Avg Win':>8s} | {'Sharpe':>7s}")
    print("-" * 85)
    
    for idx, r in enumerate(sorted_results[:3], 1):
        p = r['params']
        status = "✅" if r['sharpe'] > 0 else "⚠️" if r['sharpe'] > -1 else "❌"
        print(f"{idx:<5d} | {p['trail_distance']:>6.2f}% | {p['hold_minutes']:>6d}m | {r['trades_per_day']:>11.1f} | {r['win_rate']:>5.1f}% | {r['avg_win']:>7.3f}% | {r['sharpe']:>7.2f} {status}")
    
    best = sorted_results[0]
    
    print(f"\n{'='*80}")
    print("BEST V4 CONFIGURATION")
    print(f"{'='*80}")
    print(f"Sharpe: {best['sharpe']:.2f}")
    print(f"Win Rate: {best['win_rate']:.1f}%")
    print(f"Avg Win: {best['avg_win']:.3f}% (vs 0.042% in V2!)")
    print(f"Avg Loss: {best['avg_loss']:.3f}%")
    print(f"Avg Peak: {best['avg_peak']:.3f}%")
    print(f"Trades/Day: {best['trades_per_day']:.1f}")
    
    # Calculate if profitable
    expected_pnl = (best['win_rate']/100 * best['avg_win']) + ((100-best['win_rate'])/100 * best['avg_loss'])
    print(f"\nExpected P&L per trade: {expected_pnl:.3f}%")
    
    if best['sharpe'] > 0:
        print(f"\n🎯 **PROFITABLE!** Test on full 2024+2025")
    elif expected_pnl > 0:
        print(f"\n⚠️  **POSITIVE EXPECTANCY!** Test on full year")
    else:
        print(f"\n❌ Still negative expectancy")

# Save
with open('liquidity_grab_v4_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Saved to liquidity_grab_v4_results.json")
