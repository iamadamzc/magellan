"""
Strategy Optimization Framework

Goal: DISCOVER profitable strategies by optimizing parameters, not just testing defaults

Key Insights from Failed Tests:
1. Opening Drive: Lowest frequency (0.6/day) but WORST Sharpe (-162) = Bad signals
2. Micro-Momentum: Low frequency (3.2/day) but 12.5% win rate = Need better filters
3. VWAP: Best Sharpe (-43.76) but 20/day = Too frequent, but signal has potential
4. All strategies: Win rates 7-33% = Need to be MORE SELECTIVE

Optimization Approach:
1. Increase entry thresholds → Reduce frequency, improve signal quality
2. Target larger moves → Overcome friction with bigger edge
3. Add filters → Confluence of signals improves win rate
4. Time-based filtering → Only trade high-volatility periods
5. Hybrid strategies → Combine best elements

Target Parameters:
- Frequency: 1-10 trades/day (not 20-85)
- Win rate: >50% (current: 7-33%)
- Avg profit: >0.15% (current: -0.05% to -0.02%)
- Hold time: 5-30 min (sweet spot between scalping and swing)

Let's find the Goldilocks Zone!
"""

import requests
import os
import pandas as pd
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
import json

load_dotenv()
FMP_API_KEY = os.getenv('FMP_API_KEY')

FRICTION_BPS = 4.1

def fetch_1min_data(symbol, date):
    url = "https://financialmodelingprep.com/stable/historical-chart/1min"
    params = {'symbol': symbol, 'from': date, 'to': date, 'apikey': FMP_API_KEY}
    response = requests.get(url, params=params, timeout=10)
    return response.json() if response.status_code == 200 else []

def calculate_vwap(df):
    return (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()

# OPTIMIZED Strategy 1: Strict VWAP + Volatility Filter
def optimized_vwap_strategy(df, vwap_threshold=0.5, min_volatility=0.3, hold_minutes=10):
    """
    Optimization:
    - Increase VWAP deviation threshold (0.3% → 0.5%)
    - Add volatility filter (only trade when ATR > threshold)
    - Longer hold time (3 min → 10 min) to catch bigger moves
    - Target larger profit (0.15% → 0.30%)
    """
    df['vwap'] = calculate_vwap(df)
    df['vwap_dev'] = (df['close'] - df['vwap']) / df['vwap'] * 100
    
    # Calculate ATR (volatility filter)
    df['tr'] = df[['high', 'low', 'close']].apply(
        lambda x: max(x['high'] - x['low'], abs(x['high'] - x['close']), abs(x['low'] - x['close'])), axis=1)
    df['atr'] = df['tr'].rolling(14).mean()
    df['atr_pct'] = df['atr'] / df['close'] * 100
    
    trades = []
    position = None
    
    for i in range(20, len(df)):
        if position:
            hold_min = i - position['entry_idx']
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            # Exit: Target hit (0.30%) OR back to VWAP OR timeout
            if pnl_pct >= 0.30 or abs(df.loc[i, 'vwap_dev']) < 0.05 or hold_min >= hold_minutes:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({
                    'strategy': 'Optimized VWAP',
                    'pnl_pct': pnl_pct,
                    'hold_min': hold_min,
                    'win': pnl_pct > 0,
                    'exit_reason': 'target' if pnl_pct >= 0.30 else 'vwap' if abs(df.loc[i, 'vwap_dev']) < 0.05 else 'timeout'
                })
                position = None
        
        if not position:
            # STRICT filter: Higher threshold + volatility
            if df.loc[i, 'atr_pct'] > min_volatility:  # Only in volatile periods
                if df.loc[i, 'vwap_dev'] > vwap_threshold:
                    position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
                elif df.loc[i, 'vwap_dev'] < -vwap_threshold:
                    position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
    
    return trades

# OPTIMIZED Strategy 2: High-Conviction Momentum
def optimized_momentum_strategy(df, momentum_threshold=0.20, volume_multiplier=3.0):
    """
    Optimization:
    - Much higher momentum threshold (0.05% → 0.20%)
    - Higher volume requirement (2x → 3x)
    - Larger profit target (0.10% → 0.25%)
    - Goal: Fewer trades, better quality
    """
    df['vol_sma'] = df['volume'].rolling(20).mean()
    df['vol_spike'] = df['volume'] > volume_multiplier * df['vol_sma']
    df['price_change_5'] = (df['close'] - df['close'].shift(5)) / df['close'].shift(5) * 100
    
    trades = []
    position = None
    
    for i in range(30, len(df)):
        if position:
            hold_min = i - position['entry_idx']
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            # Exit: Target (0.25%) or stop (-0.15%) or timeout (5 min)
            if pnl_pct >= 0.25 or pnl_pct <= -0.15 or hold_min >= 5:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({
                    'strategy': 'Optimized Momentum',
                    'pnl_pct': pnl_pct,
                    'hold_min': hold_min,
                    'win': pnl_pct > 0
                })
                position = None
        
        if not position and df.loc[i, 'vol_spike']:
            mom = df.loc[i, 'price_change_5']
            if mom > momentum_threshold:
                position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
            elif mom < -momentum_threshold:
                position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
    
    return trades

# OPTIMIZED Strategy 3: Confluence Breakout (Multiple Filters)
def optimized_confluence_breakout(df):
    """
    Optimization:
    - Require MULTIPLE signals to align (confluence)
    - Opening range break + volume spike + momentum
    - Much larger target (0.50%)
    - Longer hold (20 min)
    """
    if len(df) < 40:
        return []
    
    or_high = df.loc[:29, 'high'].max()
    or_low = df.loc[:29, 'low'].min()
    
    df['vol_sma'] = df['volume'].rolling(20).mean()
    df['momentum_10'] = (df['close'] - df['close'].shift(10)) / df['close'].shift(10) * 100
    
    trades = []
    position = None
    
    for i in range(40, len(df)):
        if position:
            hold_min = i - position['entry_idx']
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            # Target 0.50% or timeout 20 min
            if abs(pnl_pct) >= 0.50 or hold_min >= 20:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({
                    'strategy': 'Confluence Breakout',
                    'pnl_pct': pnl_pct,
                    'hold_min': hold_min,
                    'win': pnl_pct > 0
                })
                position = None
        
        if not position:
            # CONFLUENCE: All 3 must align
            volume_spike = df.loc[i, 'volume'] > 2.5 * df.loc[i, 'vol_sma']
            strong_momentum = abs(df.loc[i, 'momentum_10']) > 0.15
            
            if volume_spike and strong_momentum:
                if df.loc[i, 'high'] > or_high and df.loc[i, 'momentum_10'] > 0:
                    position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
                elif df.loc[i, 'low'] < or_low and df.loc[i, 'momentum_10'] < 0:
                    position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
    
    return trades

# OPTIMIZED Strategy 4: First Hour Only (Time Filter)
def optimized_first_hour_strategy(df):
    """
    Optimization:
    - Trade ONLY in first 60 minutes (highest volatility)
    - Strict momentum filter (>0.25%)
    - Large target (0.40%)
    - Max 2-3 trades/day
    """
    if len(df) < 60:
        return []
    
    df['momentum_10'] = (df['close'] - df['close'].shift(10)) / df['close'].shift(10) * 100
    df['vol_sma'] = df['volume'].rolling(20).mean()
    
    trades = []
    
    # Only first 60 minutes
    for i in range(20, min(60, len(df))):
        mom = df.loc[i, 'momentum_10']
        vol_spike = df.loc[i, 'volume'] > 2.0 * df.loc[i, 'vol_sma']
        
        # Very strict: Large momentum + volume
        if abs(mom) > 0.25 and vol_spike and len(trades) < 3:  # Max 3 trades
            entry_price = df.loc[i, 'close']
            entry_type = 'long' if mom > 0 else 'short'
            
            # Hold for 10 minutes
            for j in range(i+1, min(i+11, len(df))):
                pnl_pct = (df.loc[j, 'close'] - entry_price) / entry_price * 100
                if entry_type == 'short':
                    pnl_pct = -pnl_pct
                
                if abs(pnl_pct) >= 0.40 or j == i+10:
                    pnl_pct -= FRICTION_BPS / 100
                    trades.append({
                        'strategy': 'First Hour Only',
                        'pnl_pct': pnl_pct,
                        'hold_min': j-i,
                        'win': pnl_pct > 0
                    })
                    break
            
            # Skip ahead to avoid overlapping trades
            i = j + 5
    
    return trades

# Run optimization tests
print("="*80)
print("STRATEGY OPTIMIZATION FRAMEWORK")
print("="*80)
print("\nGoal: Find profitable parameters through systematic optimization")

test_dates = ['2024-03-15', '2024-05-20', '2024-07-10', '2024-09-18', '2024-11-15']

optimized_strategies = [
    ('Optimized VWAP (0.5% thresh, vol filter)', lambda df: optimized_vwap_strategy(df, 0.5, 0.3, 10)),
    ('Optimized VWAP (0.7% thresh)', lambda df: optimized_vwap_strategy(df, 0.7, 0.4, 15)),
    ('High-Conviction Momentum', lambda df: optimized_momentum_strategy(df, 0.20, 3.0)),
    ('Ultra-Strict Momentum', lambda df: optimized_momentum_strategy(df, 0.30, 4.0)),
    ('Confluence Breakout', optimized_confluence_breakout),
    ('First Hour Only', optimized_first_hour_strategy),
]

results = []

for strategy_name, strategy_func in optimized_strategies:
    print(f"\n{'='*80}")
    print(f"{strategy_name}")
    print(f"{'='*80}")
    
    all_trades = []
    
    for date in test_dates:
        bars = fetch_1min_data('SPY', date)
        if len(bars) < 50:
            continue
        
        df = pd.DataFrame(bars).sort_values('date').reset_index(drop=True)
        trades = strategy_func(df)
        all_trades.extend(trades)
    
    if all_trades:
        pnls = [t['pnl_pct'] for t in all_trades]
        wins = [t for t in all_trades if t['win']]
        
        avg_pnl = np.mean(pnls)
        std_pnl = np.std(pnls) if len(pnls) > 1 else 0
        sharpe = (avg_pnl / std_pnl * np.sqrt(252 * 78)) if std_pnl > 0 else 0
        win_rate = len(wins) / len(all_trades) * 100
        
        trades_per_day = len(all_trades) / 5
        annual_trades = trades_per_day * 252
        annual_friction = annual_trades * (FRICTION_BPS / 100)
        
        print(f"Trades (5 days):   {len(all_trades)}")
        print(f"Trades/day:        {trades_per_day:.1f}")
        print(f"Win Rate:          {win_rate:.1f}%")
        print(f"Avg P&L:           {avg_pnl:.3f}%")
        print(f"**Sharpe:          {sharpe:.2f}**")
        print(f"Annual Friction:   {annual_friction:.1f}%")
        
        results.append({
            'strategy': strategy_name,
            'sharpe': sharpe,
            'trades_per_day': trades_per_day,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'annual_friction': annual_friction
        })
        
        if sharpe >= 1.0:
            print(f"\n🎯 **BREAKTHROUGH!** - Sharpe {sharpe:.2f}")
        elif sharpe >= 0.5:
            print(f"\n⚠️  **PROMISING** - Sharpe {sharpe:.2f}, needs more tuning")
        elif sharpe >= 0.0:
            print(f"\n📈 **IMPROVING** - Sharpe {sharpe:.2f}, getting closer")
        else:
            print(f"\n❌ Still negative - try more aggressive filters")
    else:
        print("No trades (filters too strict - need to relax slightly)")

# Summary
print("\n" + "="*80)
print("OPTIMIZATION RESULTS")
print("="*80)

if results:
    sorted_results = sorted(results, key=lambda x: x['sharpe'], reverse=True)
    
    print(f"\n{'Strategy':<45s} | {'Sharpe':>7s} | {'Trades/Day':>11s} | {'Win%':>6s}")
    print("-" * 80)
    
    for r in sorted_results:
        print(f"{r['strategy']:<45s} | {r['sharpe']:>7.2f} | {r['trades_per_day']:>11.1f} | {r['win_rate']:>5.1f}%")
    
    best = sorted_results[0]
    print(f"\n🏆 BEST: {best['strategy']}")
    print(f"   Sharpe: {best['sharpe']:.2f} | Trades/Day: {best['trades_per_day']:.1f} | Win Rate: {best['win_rate']:.1f}%")
    
    if best['sharpe'] >= 1.0:
        print(f"\n✅ **PROFITABLE STRATEGY DISCOVERED!**")
    elif best['sharpe'] >= 0:
        print(f"\n📈 **PROGRESS!** Improved from -43.76 to {best['sharpe']:.2f}")
        print("   Next: Continue parameter optimization in this direction")

with open('optimized_strategy_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Saved to optimized_strategy_results.json")
