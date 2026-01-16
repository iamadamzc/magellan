"""
Liquidity Grab - Deep Refinement Round 2

Analysis of Round 1:
- Config 4 & 6: 45.5% win rate (BEST so far across all strategies!)
- But Sharpe still -3.10 (losing)
- Only 0.4 trades/day (very selective)

Key insight: Win rate is good, but we're losing on:
1. Profit target too small vs stop loss
2. Not enough edge per trade to overcome friction

Refinement approach:
1. LARGER profit targets (0.30% to 0.50%) - capture bigger moves
2. TIGHTER stops (0.15% to 0.20%) - cut losses faster
3. Better risk/reward ratios (2:1 or 3:1)
4. Add volume confirmation
5. Test different lookback periods more granularly
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
FRICTION_BPS = 4.1

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

def liquidity_grab_v2(df, lookback=10, rejection_bars=3, profit_target=0.35, 
                     stop_loss=0.15, hold_minutes=12, min_wick_pct=0.10,
                     require_volume=True, vol_multiplier=1.5):
    """
    Liquidity Grab V2 - Refined with better risk/reward
    """
    if len(df) < 30:
        return []
    
    df['high_roll'] = df['high'].rolling(lookback).max()
    df['low_roll'] = df['low'].rolling(lookback).min()
    df['upper_wick'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['close'] * 100
    df['lower_wick'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['close'] * 100
    df['time'] = pd.to_datetime(df['date'])
    df['hour'] = df['time'].dt.hour
    
    # Volume filter
    if require_volume:
        df['vol_sma'] = df['volume'].rolling(20).mean()
        df['vol_spike'] = df['volume'] > vol_multiplier * df['vol_sma']
    
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
                trades.append({
                    'pnl_pct': pnl_pct,
                    'win': pnl_pct > 0,
                    'hold_min': hold_min,
                    'exit_reason': exit_reason
                })
                position = None
        
        if not position:
            if 12 <= df.loc[i, 'hour'] < 14:
                continue
            
            # Volume filter
            if require_volume and not df.loc[i, 'vol_spike']:
                continue
            
            # Pattern 1: Break high then reject
            if i >= rejection_bars:
                recent_high = df.loc[i-rejection_bars:i-1, 'high'].max()
                prev_high_roll = df.loc[i-1, 'high_roll']
                
                if recent_high > prev_high_roll and df.loc[i, 'close'] < prev_high_roll:
                    position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
                    continue
            
            # Pattern 2: Break low then reclaim
            if i >= rejection_bars:
                recent_low = df.loc[i-rejection_bars:i-1, 'low'].min()
                prev_low_roll = df.loc[i-1, 'low_roll']
                
                if recent_low < prev_low_roll and df.loc[i, 'close'] > prev_low_roll:
                    position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
                    continue
            
            # Pattern 3: Large wick
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
print("LIQUIDITY GRAB V2 - REFINED PARAMETER OPTIMIZATION")
print("="*80)
print("\nFocus: Better risk/reward ratios to overcome friction")

test_dates = generate_trading_days('2024-01-02', '2024-03-31')
print(f"Testing on Q1 2024: {len(test_dates)} potential days")

print("Loading data...")
all_dfs = []
for date in test_dates[:30]:
    bars = fetch_1min_data('SPY', date)
    if len(bars) >= 50:
        all_dfs.append(pd.DataFrame(bars).sort_values('date').reset_index(drop=True))

print(f"Loaded {len(all_dfs)} days of data")

# Refined parameter grid - focus on better R/R ratios
param_grid = [
    # 2:1 Risk/Reward
    {'lookback': 10, 'rejection_bars': 3, 'profit_target': 0.30, 'stop_loss': 0.15, 'hold_minutes': 12, 'min_wick_pct': 0.10, 'require_volume': True, 'vol_multiplier': 1.5},
    {'lookback': 12, 'rejection_bars': 3, 'profit_target': 0.32, 'stop_loss': 0.16, 'hold_minutes': 12, 'min_wick_pct': 0.12, 'require_volume': True, 'vol_multiplier': 1.8},
    
    # 2.5:1 Risk/Reward
    {'lookback': 10, 'rejection_bars': 3, 'profit_target': 0.375, 'stop_loss': 0.15, 'hold_minutes': 15, 'min_wick_pct': 0.10, 'require_volume': True, 'vol_multiplier': 1.5},
    {'lookback': 8, 'rejection_bars': 2, 'profit_target': 0.35, 'stop_loss': 0.14, 'hold_minutes': 12, 'min_wick_pct': 0.08, 'require_volume': True, 'vol_multiplier': 1.5},
    
    # 3:1 Risk/Reward (aggressive targets)
    {'lookback': 10, 'rejection_bars': 3, 'profit_target': 0.45, 'stop_loss': 0.15, 'hold_minutes': 15, 'min_wick_pct': 0.10, 'require_volume': True, 'vol_multiplier': 2.0},
    {'lookback': 12, 'rejection_bars': 3, 'profit_target': 0.50, 'stop_loss': 0.17, 'hold_minutes': 18, 'min_wick_pct': 0.12, 'require_volume': True, 'vol_multiplier': 2.0},
    
    # No volume filter (more trades)
    {'lookback': 10, 'rejection_bars': 3, 'profit_target': 0.35, 'stop_loss': 0.15, 'hold_minutes': 12, 'min_wick_pct': 0.10, 'require_volume': False, 'vol_multiplier': 0},
    
    # Shorter lookback (more signals)
    {'lookback': 7, 'rejection_bars': 2, 'profit_target': 0.35, 'stop_loss': 0.15, 'hold_minutes': 10, 'min_wick_pct': 0.08, 'require_volume': True, 'vol_multiplier': 1.5},
]

results = []

print("\nTesting refined parameter combinations...")
for idx, params in enumerate(param_grid, 1):
    all_trades = []
    
    for df in all_dfs:
        trades = liquidity_grab_v2(df.copy(), **params)
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
        rr_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        result = {
            'config': idx,
            'params': params,
            'trades': len(all_trades),
            'trades_per_day': trades_per_day,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'rr_ratio': rr_ratio,
            'sharpe': sharpe,
            'total_return': sum(pnls)
        }
        results.append(result)
        
        rr_str = f"{params['profit_target']/params['stop_loss']:.1f}:1" if params['stop_loss'] > 0 else "N/A"
        print(f"\nConfig {idx}: Target={params['profit_target']:.2f}%, Stop={params['stop_loss']:.2f}% (R/R {rr_str})")
        print(f"  Trades: {len(all_trades)} ({trades_per_day:.1f}/day) | Win%: {win_rate:.1f}% | Sharpe: {sharpe:.2f}")
        print(f"  Avg Win: {avg_win:.3f}% | Avg Loss: {avg_loss:.3f}% | Actual R/R: {rr_ratio:.2f}:1")
    else:
        print(f"\nConfig {idx}: Insufficient trades ({len(all_trades) if all_trades else 0})")

# Summary
print("\n" + "="*80)
print("REFINED OPTIMIZATION RESULTS")
print("="*80)

if results:
    sorted_results = sorted(results, key=lambda x: x['sharpe'], reverse=True)
    
    print(f"\nTop 5 by Sharpe:")
    print(f"{'Rank':<5s} | {'Target':>7s} | {'Stop':>6s} | {'Trades/Day':>11s} | {'Win%':>6s} | {'R/R':>6s} | {'Sharpe':>7s}")
    print("-" * 80)
    
    for idx, r in enumerate(sorted_results[:5], 1):
        p = r['params']
        status = "✅" if r['sharpe'] > 0 else "⚠️" if r['sharpe'] > -2 else "❌"
        print(f"{idx:<5d} | {p['profit_target']:>6.2f}% | {p['stop_loss']:>5.2f}% | {r['trades_per_day']:>11.1f} | {r['win_rate']:>5.1f}% | {r['rr_ratio']:>5.2f}:1 | {r['sharpe']:>7.2f} {status}")
    
    best = sorted_results[0]
    
    print(f"\n{'='*80}")
    print("BEST CONFIGURATION ANALYSIS")
    print(f"{'='*80}")
    print(f"Sharpe: {best['sharpe']:.2f}")
    print(f"Win Rate: {best['win_rate']:.1f}%")
    print(f"Avg Win: {best['avg_win']:.3f}%")
    print(f"Avg Loss: {best['avg_loss']:.3f}%")
    print(f"Risk/Reward: {best['rr_ratio']:.2f}:1")
    print(f"Trades/Day: {best['trades_per_day']:.1f}")
    
    if best['sharpe'] > 0:
        print(f"\n🎯 **PROFITABLE!** Test on full 2024+2025")
    elif best['sharpe'] > -2:
        print(f"\n⚠️  **CLOSE!** Sharpe {best['sharpe']:.2f} - try more refinement or test full year")
    else:
        print(f"\n❌ Still unprofitable - try next strategy")

# Save
with open('liquidity_grab_v2_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Saved to liquidity_grab_v2_results.json")
