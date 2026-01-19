"""
Advanced Strategy Optimization - Maximize Profitability

Current Best: Sharpe 301.84 (0.45% thresh, 0.30% target, 15min hold)

Optimization Opportunities:
1. Fine-tune around best parameters (0.43-0.47% thresholds)
2. Add time-of-day filter (avoid lunch lull 12-2 PM)
3. Add volatility filter (only trade high ATR periods)
4. Dynamic stops (protect winners, cut losers fast)
5. Position sizing (larger size on high-conviction signals)
6. Multi-symbol portfolio (SPY, QQQ, IWM diversification)

Goal: Push Sharpe even higher while maintaining low frequency
"""

import requests
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import json
import os
from datetime import datetime

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

def calculate_atr(df, period=14):
    """Calculate Average True Range (volatility measure)"""
    df['tr'] = df[['high', 'low', 'close']].apply(
        lambda x: max(x['high'] - x['low'], 
                     abs(x['high'] - x.get('prev_close', x['close'])), 
                     abs(x['low'] - x.get('prev_close', x['close']))), axis=1)
    return df['tr'].rolling(period).mean()

def enhanced_vwap_strategy(df, vwap_thresh, profit_target, hold_minutes, 
                          use_time_filter=False, use_vol_filter=False, 
                          use_trailing_stop=False, min_atr_pct=0.25):
    """
    Enhanced VWAP with multiple optimization filters
    """
    df['vwap'] = calculate_vwap(df)
    df['vwap_dev'] = (df['close'] - df['vwap']) / df['vwap'] * 100
    
    # Add time column (hour of day)
    df['time'] = pd.to_datetime(df['date'])
    df['hour'] = df['time'].dt.hour
    df['minute'] = df['time'].dt.minute
    
    # Calculate ATR for volatility filter
    df['prev_close'] = df['close'].shift(1)
    df['atr'] = calculate_atr(df)
    df['atr_pct'] = df['atr'] / df['close'] * 100
    
    trades = []
    position = None
    
    for i in range(20, len(df)):
        if position:
            hold_min = i - position['entry_idx']
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            # Trailing stop logic
            exit_reason = None
            if use_trailing_stop:
                # If profit >0.15%, trail stop at breakeven
                if pnl_pct > 0.15 and pnl_pct < 0.05:
                    exit_reason = 'trailing_stop'
            
            # Standard exits
            if pnl_pct >= profit_target:
                exit_reason = 'target'
            elif abs(df.loc[i, 'vwap_dev']) < 0.03:
                exit_reason = 'vwap_return'
            elif hold_min >= hold_minutes:
                exit_reason = 'timeout'
            
            if exit_reason:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({
                    'pnl_pct': pnl_pct,
                    'win': pnl_pct > 0,
                    'exit_reason': exit_reason,
                    'hold_min': hold_min,
                    'hour': df.loc[i, 'hour']
                })
                position = None
        
        if not position:
            # Time filter: Avoid lunch hour (12-2 PM)
            if use_time_filter:
                hour = df.loc[i, 'hour']
                if 12 <= hour < 14:  # Skip lunch
                    continue
            
            # Volatility filter: Only trade when ATR is high
            if use_vol_filter:
                if pd.notna(df.loc[i, 'atr_pct']) and df.loc[i, 'atr_pct'] < min_atr_pct:
                    continue
            
            # Entry signals
            if df.loc[i, 'vwap_dev'] > vwap_thresh:
                position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
            elif df.loc[i, 'vwap_dev'] < -vwap_thresh:
                position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
    
    return trades

print("="*80)
print("ADVANCED OPTIMIZATION - MAXIMIZE PROFITABILITY")
print("="*80)

test_dates = ['2024-03-15', '2024-05-20', '2024-07-10', '2024-09-18', '2024-11-15']

# Load data
all_dfs = {}
for symbol in ['SPY', 'QQQ', 'IWM']:
    all_dfs[symbol] = []
    for date in test_dates:
        bars = fetch_1min_data(symbol, date)
        if len(bars) >= 50:
            all_dfs[symbol].append(pd.DataFrame(bars).sort_values('date').reset_index(drop=True))

# Optimization 1: Fine-tune threshold
print("\n" + "="*80)
print("OPTIMIZATION 1: FINE-TUNE THRESHOLD")
print("="*80)

fine_tune_params = [
    {'vwap_thresh': 0.43, 'profit_target': 0.30, 'hold_minutes': 15},
    {'vwap_thresh': 0.44, 'profit_target': 0.30, 'hold_minutes': 15},
    {'vwap_thresh': 0.45, 'profit_target': 0.30, 'hold_minutes': 15},  # Best so far
    {'vwap_thresh': 0.46, 'profit_target': 0.30, 'hold_minutes': 15},
    {'vwap_thresh': 0.47, 'profit_target': 0.30, 'hold_minutes': 15},
]

results_finetune = []
for params in fine_tune_params:
    all_trades = []
    for df in all_dfs['SPY']:
        trades = enhanced_vwap_strategy(df.copy(), **params, use_time_filter=False, use_vol_filter=False)
        all_trades.extend(trades)
    
    if all_trades and len(all_trades) >= 2:
        pnls = [t['pnl_pct'] for t in all_trades]
        avg_pnl = np.mean(pnls)
        std_pnl = np.std(pnls)
        sharpe = (avg_pnl / std_pnl * np.sqrt(252 * 78)) if std_pnl > 0 else 0
        win_rate = sum(1 for t in all_trades if t['win']) / len(all_trades) * 100
        
        results_finetune.append({
            'params': params,
            'sharpe': sharpe,
            'trades': len(all_trades),
            'win_rate': win_rate,
            'avg_pnl': avg_pnl
        })
        
        print(f"Threshold {params['vwap_thresh']:.2f}%: Sharpe {sharpe:>7.2f} | Trades {len(all_trades):>2d} | Win% {win_rate:>5.1f}%")

# Optimization 2: Add filters
print("\n" + "="*80)
print("OPTIMIZATION 2: ADD FILTERS")
print("="*80)

best_base = {'vwap_thresh': 0.45, 'profit_target': 0.30, 'hold_minutes': 15}

filter_configs = [
    {'name': 'Baseline', 'time_filter': False, 'vol_filter': False},
    {'name': 'Time Filter (no lunch)', 'time_filter': True, 'vol_filter': False},
    {'name': 'Volatility Filter', 'time_filter': False, 'vol_filter': True},
    {'name': 'Both Filters', 'time_filter': True, 'vol_filter': True},
]

results_filters = []
for config in filter_configs:
    all_trades = []
    for df in all_dfs['SPY']:
        trades = enhanced_vwap_strategy(df.copy(), **best_base, 
                                       use_time_filter=config['time_filter'],
                                       use_vol_filter=config['vol_filter'])
        all_trades.extend(trades)
    
    if all_trades and len(all_trades) >= 2:
        pnls = [t['pnl_pct'] for t in all_trades]
        avg_pnl = np.mean(pnls)
        std_pnl = np.std(pnls)
        sharpe = (avg_pnl / std_pnl * np.sqrt(252 * 78)) if std_pnl > 0 else 0
        win_rate = sum(1 for t in all_trades if t['win']) / len(all_trades) * 100
        
        results_filters.append({
            'config': config['name'],
            'sharpe': sharpe,
            'trades': len(all_trades),
            'win_rate': win_rate,
            'avg_pnl': avg_pnl
        })
        
        print(f"{config['name']:<25s}: Sharpe {sharpe:>7.2f} | Trades {len(all_trades):>2d} | Win% {win_rate:>5.1f}%")

# Optimization 3: Multi-symbol portfolio
print("\n" + "="*80)
print("OPTIMIZATION 3: MULTI-SYMBOL PORTFOLIO")
print("="*80)

for symbol in ['SPY', 'QQQ', 'IWM']:
    all_trades = []
    for df in all_dfs[symbol]:
        trades = enhanced_vwap_strategy(df.copy(), **best_base, 
                                       use_time_filter=False, use_vol_filter=False)
        all_trades.extend(trades)
    
    if all_trades and len(all_trades) >= 2:
        pnls = [t['pnl_pct'] for t in all_trades]
        avg_pnl = np.mean(pnls)
        std_pnl = np.std(pnls)
        sharpe = (avg_pnl / std_pnl * np.sqrt(252 * 78)) if std_pnl > 0 else 0
        win_rate = sum(1 for t in all_trades if t['win']) / len(all_trades) * 100
        
        print(f"{symbol:<6s}: Sharpe {sharpe:>7.2f} | Trades {len(all_trades):>2d} | Win% {win_rate:>5.1f}% | Avg P&L {avg_pnl:>6.3f}%")

# Optimization 4: Profit target variation
print("\n" + "="*80)
print("OPTIMIZATION 4: PROFIT TARGET OPTIMIZATION")
print("="*80)

target_params = [
    {'vwap_thresh': 0.45, 'profit_target': 0.25, 'hold_minutes': 12},
    {'vwap_thresh': 0.45, 'profit_target': 0.28, 'hold_minutes': 13},
    {'vwap_thresh': 0.45, 'profit_target': 0.30, 'hold_minutes': 15},  # Current best
    {'vwap_thresh': 0.45, 'profit_target': 0.32, 'hold_minutes': 16},
    {'vwap_thresh': 0.45, 'profit_target': 0.35, 'hold_minutes': 18},
]

results_targets = []
for params in target_params:
    all_trades = []
    for df in all_dfs['SPY']:
        trades = enhanced_vwap_strategy(df.copy(), **params, use_time_filter=False, use_vol_filter=False)
        all_trades.extend(trades)
    
    if all_trades and len(all_trades) >= 2:
        pnls = [t['pnl_pct'] for t in all_trades]
        avg_pnl = np.mean(pnls)
        std_pnl = np.std(pnls)
        sharpe = (avg_pnl / std_pnl * np.sqrt(252 * 78)) if std_pnl > 0 else 0
        win_rate = sum(1 for t in all_trades if t['win']) / len(all_trades) * 100
        
        results_targets.append({
            'params': params,
            'sharpe': sharpe,
            'trades': len(all_trades),
            'win_rate': win_rate,
            'avg_pnl': avg_pnl
        })
        
        print(f"Target {params['profit_target']:.2f}% / Hold {params['hold_minutes']}min: " +
              f"Sharpe {sharpe:>7.2f} | Trades {len(all_trades):>2d} | Win% {win_rate:>5.1f}%")

# Summary
print("\n" + "="*80)
print("OPTIMIZATION SUMMARY")
print("="*80)

# Find absolute best across all optimizations
all_results = []

if results_finetune:
    best_finetune = max(results_finetune, key=lambda x: x['sharpe'])
    all_results.append(('Fine-tune Threshold', best_finetune['sharpe'], best_finetune['params']))

if results_filters:
    best_filter = max(results_filters, key=lambda x: x['sharpe'])
    all_results.append(('Filter Optimization', best_filter['sharpe'], best_filter['config']))

if results_targets:
    best_target = max(results_targets, key=lambda x: x['sharpe'])
    all_results.append(('Target Optimization', best_target['sharpe'], best_target['params']))

if all_results:
    print("\nBest configuration from each optimization:")
    for name, sharpe, config in sorted(all_results, key=lambda x: x[1], reverse=True):
        print(f"\n{name}:")
        print(f"  Sharpe: {sharpe:.2f}")
        print(f"  Config: {config}")
    
    best_overall = max(all_results, key=lambda x: x[1])
    
    print(f"\n{'='*80}")
    print("🏆 BEST OVERALL CONFIGURATION")
    print(f"{'='*80}")
    print(f"Optimization: {best_overall[0]}")
    print(f"Sharpe: {best_overall[1]:.2f}")
    print(f"Parameters: {best_overall[2]}")
    
    if best_overall[1] > 301.84:
        improvement = best_overall[1] - 301.84
        print(f"\n✅ **IMPROVED!** Sharpe increased by {improvement:.2f} ({improvement/301.84*100:.1f}%)")
    elif best_overall[1] == 301.84:
        print(f"\n⚠️  No improvement - current parameters are optimal")
    else:
        print(f"\n⚠️  Slightly worse - original parameters (301.84) remain best")

# Save results
with open('advanced_optimization_results.json', 'w') as f:
    json.dump({
        'fine_tune': results_finetune,
        'filters': results_filters,
        'targets': results_targets,
        'best_overall': {
            'name': best_overall[0],
            'sharpe': best_overall[1],
            'config': str(best_overall[2])
        }
    }, f, indent=2)

print(f"\n✅ Saved to advanced_optimization_results.json")
