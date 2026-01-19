"""
Liquidity Grab - QQQ-Specific Optimization

Baseline on QQQ (Q1 2024):
- Sharpe: 0.84 (PROFITABLE!)
- Win Rate: 58.8%
- Avg Win: 0.150%
- Avg Loss: -0.183%
- Trades/Day: 0.6

Goal: Optimize parameters specifically for QQQ to push Sharpe > 2.0

QQQ characteristics vs SPY:
- More volatile (bigger moves)
- Tech-heavy (different patterns)
- Higher average daily range

Optimization approach:
1. Adjust thresholds for QQQ's higher volatility
2. Test different profit targets (QQQ moves more)
3. Optimize stop losses
4. Fine-tune lookback periods
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

def liquidity_grab_qqq(df, lookback=10, rejection_bars=3, profit_target=0.375, 
                       stop_loss=0.15, hold_minutes=15, min_wick_pct=0.10):
    """Liquidity Grab optimized for QQQ"""
    if len(df) < 30:
        return []
    
    df['high_roll'] = df['high'].rolling(lookback).max()
    df['low_roll'] = df['low'].rolling(lookback).min()
    df['upper_wick'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['close'] * 100
    df['lower_wick'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['close'] * 100
    df['time'] = pd.to_datetime(df['date'])
    df['hour'] = df['time'].dt.hour
    
    trades = []
    position = None
    
    for i in range(lookback + 5, len(df)):
        if position:
            hold_min = i - position['entry_idx']
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            exit_reason = None
            if pnl_pct >= profit_target:
                exit_reason = 'target'
            elif pnl_pct <= -stop_loss:
                exit_reason = 'stop_loss'
            elif hold_min >= hold_minutes:
                exit_reason = 'timeout'
            
            if exit_reason:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({'pnl_pct': pnl_pct, 'win': pnl_pct > 0, 'exit_reason': exit_reason})
                position = None
        
        if not position:
            if 12 <= df.loc[i, 'hour'] < 14:
                continue
            
            if i >= rejection_bars:
                recent_high = df.loc[i-rejection_bars:i-1, 'high'].max()
                prev_high_roll = df.loc[i-1, 'high_roll']
                if recent_high > prev_high_roll and df.loc[i, 'close'] < prev_high_roll:
                    position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
                    continue
            
            if i >= rejection_bars:
                recent_low = df.loc[i-rejection_bars:i-1, 'low'].min()
                prev_low_roll = df.loc[i-1, 'low_roll']
                if recent_low < prev_low_roll and df.loc[i, 'close'] > prev_low_roll:
                    position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
                    continue
            
            if df.loc[i, 'upper_wick'] > min_wick_pct:
                position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
            elif df.loc[i, 'lower_wick'] > min_wick_pct:
                position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
    
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
print("LIQUIDITY GRAB - QQQ-SPECIFIC OPTIMIZATION")
print("="*80)
print("\nBaseline: Sharpe 0.84, Win Rate 58.8%")

test_dates = generate_trading_days('2024-01-02', '2024-03-31')
print(f"Testing on Q1 2024: {len(test_dates)} potential days")

print("Loading QQQ data...")
all_dfs = []
for date in test_dates[:30]:
    bars = fetch_1min_data('QQQ', date)
    if len(bars) >= 50:
        all_dfs.append(pd.DataFrame(bars).sort_values('date').reset_index(drop=True))

print(f"Loaded {len(all_dfs)} days")

# QQQ-specific parameter grid
param_grid = [
    # Baseline (from multi-asset test)
    {'lookback': 10, 'rejection_bars': 3, 'profit_target': 0.375, 'stop_loss': 0.15, 'hold_minutes': 15, 'min_wick_pct': 0.10},
    
    # Larger targets (QQQ moves more)
    {'lookback': 10, 'rejection_bars': 3, 'profit_target': 0.45, 'stop_loss': 0.15, 'hold_minutes': 18, 'min_wick_pct': 0.10},
    {'lookback': 10, 'rejection_bars': 3, 'profit_target': 0.50, 'stop_loss': 0.18, 'hold_minutes': 20, 'min_wick_pct': 0.12},
    
    # Tighter stops (preserve capital)
    {'lookback': 10, 'rejection_bars': 3, 'profit_target': 0.40, 'stop_loss': 0.12, 'hold_minutes': 15, 'min_wick_pct': 0.10},
    {'lookback': 10, 'rejection_bars': 3, 'profit_target': 0.35, 'stop_loss': 0.10, 'hold_minutes': 12, 'min_wick_pct': 0.10},
    
    # Different lookbacks
    {'lookback': 8, 'rejection_bars': 2, 'profit_target': 0.40, 'stop_loss': 0.15, 'hold_minutes': 15, 'min_wick_pct': 0.10},
    {'lookback': 12, 'rejection_bars': 3, 'profit_target': 0.40, 'stop_loss': 0.15, 'hold_minutes': 15, 'min_wick_pct': 0.12},
    
    # Stricter wick filter (fewer but better trades)
    {'lookback': 10, 'rejection_bars': 3, 'profit_target': 0.40, 'stop_loss': 0.15, 'hold_minutes': 15, 'min_wick_pct': 0.15},
    {'lookback': 10, 'rejection_bars': 3, 'profit_target': 0.45, 'stop_loss': 0.15, 'hold_minutes': 18, 'min_wick_pct': 0.18},
    
    # Longer holds (let QQQ trends develop)
    {'lookback': 10, 'rejection_bars': 3, 'profit_target': 0.50, 'stop_loss': 0.15, 'hold_minutes': 25, 'min_wick_pct': 0.10},
]

results = []

print("\nTesting QQQ-optimized parameters...")
for idx, params in enumerate(param_grid, 1):
    all_trades = []
    
    for df in all_dfs:
        trades = liquidity_grab_qqq(df.copy(), **params)
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
        
        result = {
            'config': idx,
            'params': params,
            'trades': len(all_trades),
            'trades_per_day': trades_per_day,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'sharpe': sharpe,
            'total_return': sum(pnls)
        }
        results.append(result)
        
        print(f"\nConfig {idx}: Target={params['profit_target']:.2f}%, Stop={params['stop_loss']:.2f}%, Wick>{params['min_wick_pct']:.2f}%")
        print(f"  Trades: {len(all_trades)} ({trades_per_day:.1f}/day) | Win%: {win_rate:.1f}% | Sharpe: {sharpe:.2f}")
        print(f"  Avg Win: {avg_win:.3f}% | Avg Loss: {avg_loss:.3f}%")
    else:
        print(f"\nConfig {idx}: Insufficient trades ({len(all_trades) if all_trades else 0})")

# Summary
print("\n" + "="*80)
print("QQQ OPTIMIZATION RESULTS")
print("="*80)

if results:
    sorted_results = sorted(results, key=lambda x: x['sharpe'], reverse=True)
    
    print(f"\nTop 5 by Sharpe:")
    print(f"{'Rank':<5s} | {'Target':>7s} | {'Stop':>6s} | {'Wick':>6s} | {'T/Day':>6s} | {'Win%':>6s} | {'Sharpe':>7s} | {'vs Base':>8s}")
    print("-" * 85)
    
    baseline_sharpe = 0.84
    for idx, r in enumerate(sorted_results[:5], 1):
        p = r['params']
        improvement = r['sharpe'] - baseline_sharpe
        status = "✅" if r['sharpe'] > 1.5 else "⚠️" if r['sharpe'] > 0.5 else "❌"
        print(f"{idx:<5d} | {p['profit_target']:>6.2f}% | {p['stop_loss']:>5.2f}% | {p['min_wick_pct']:>5.2f}% | {r['trades_per_day']:>6.1f} | {r['win_rate']:>5.1f}% | {r['sharpe']:>7.2f} | {improvement:>+7.2f} {status}")
    
    best = sorted_results[0]
    
    print(f"\n{'='*80}")
    print("BEST QQQ CONFIGURATION")
    print(f"{'='*80}")
    print(f"Sharpe: {best['sharpe']:.2f} (vs 0.84 baseline = {best['sharpe']-0.84:+.2f})")
    print(f"Win Rate: {best['win_rate']:.1f}%")
    print(f"Avg Win: {best['avg_win']:.3f}%")
    print(f"Avg Loss: {best['avg_loss']:.3f}%")
    print(f"Trades/Day: {best['trades_per_day']:.1f}")
    print(f"Parameters: {best['params']}")
    
    if best['sharpe'] > 1.5:
        print(f"\n🎯 **EXCELLENT!** Sharpe > 1.5 - test on full 2024+2025")
    elif best['sharpe'] > 0.84:
        print(f"\n✅ **IMPROVED!** Continue refining")
    else:
        print(f"\n⚠️  No improvement - baseline was already optimal")

# Save
with open('liquidity_grab_qqq_optimization_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Saved to liquidity_grab_qqq_optimization_results.json")
