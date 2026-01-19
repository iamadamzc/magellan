"""
Grid Search Optimization - Find the Goldilocks Zone

Results so far:
- Default VWAP (0.3% thresh): Sharpe -43.76,  20 trades/day
- Strict VWAP (0.5-0.7%): 0 trades (too strict)
- Momentum (0.20%): Sharpe 0.00, 0.2 trades/day ← PROGRESS!

Strategy: Test parameter grid to find sweet spot
- Too loose → Many trades, negative Sharpe
- Too strict → No trades
- Goldilocks → 1-5 trades/day, positive Sharpe

Testing:
1. VWAP thresholds: 0.35%, 0.40%, 0.45%
2. Momentum thresholds: 0.15%, 0.18%, 0.22%
3. Profit targets: 0.20%, 0.25%, 0.35%
4. Hold times: 8, 12, 15 minutes
"""

import requests
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import json
import os

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

def grid_search_vwap(df, vwap_thresh, profit_target, hold_minutes):
    """VWAP strategy with tunable parameters"""
    df['vwap'] = calculate_vwap(df)
    df['vwap_dev'] = (df['close'] - df['vwap']) / df['vwap'] * 100
    
    trades = []
    position = None
    
    for i in range(10, len(df)):
        if position:
            hold_min = i - position['entry_idx']
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            if pnl_pct >= profit_target or abs(df.loc[i, 'vwap_dev']) < 0.03 or hold_min >= hold_minutes:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({'pnl_pct': pnl_pct, 'win': pnl_pct > 0})
                position = None
        
        if not position:
            if df.loc[i, 'vwap_dev'] > vwap_thresh:
                position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
            elif df.loc[i, 'vwap_dev'] < -vwap_thresh:
                position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
    
    return trades

def grid_search_momentum(df, mom_thresh, profit_target, hold_minutes):
    """Momentum strategy with tunable parameters"""
    df['vol_sma'] = df['volume'].rolling(20).mean()
    df['mom_5'] = (df['close'] - df['close'].shift(5)) / df['close'].shift(5) * 100
    
    trades = []
    position = None
    
    for i in range(25, len(df)):
        if position:
            hold_min = i - position['entry_idx']
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            if abs(pnl_pct) >= profit_target or hold_min >= hold_minutes:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({'pnl_pct': pnl_pct, 'win': pnl_pct > 0})
                position = None
        
        if not position:
            vol_spike = df.loc[i, 'volume'] > 2.5 * df.loc[i, 'vol_sma']
            if vol_spike:
                if df.loc[i, 'mom_5'] > mom_thresh:
                    position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
                elif df.loc[i, 'mom_5'] < -mom_thresh:
                    position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
    
    return trades

print("="*80)
print("GRID SEARCH OPTIMIZATION")
print("="*80)

test_dates = ['2024-03-15', '2024-05-20', '2024-07-10', '2024-09-18', '2024-11-15']

# Load data once
all_dfs = []
for date in test_dates:
    bars = fetch_1min_data('SPY', date)
    if len(bars) >= 50:
        all_dfs.append(pd.DataFrame(bars).sort_values('date').reset_index(drop=True))

# Parameter grids
vwap_params = [
    {'vwap_thresh': 0.35, 'profit_target': 0.20, 'hold_minutes': 8},
    {'vwap_thresh': 0.35, 'profit_target': 0.25, 'hold_minutes': 10},
    {'vwap_thresh': 0.40, 'profit_target': 0.20, 'hold_minutes': 10},
    {'vwap_thresh': 0.40, 'profit_target': 0.25, 'hold_minutes': 12},
    {'vwap_thresh': 0.45, 'profit_target': 0.25, 'hold_minutes': 12},
    {'vwap_thresh': 0.45, 'profit_target': 0.30, 'hold_minutes': 15},
]

momentum_params = [
    {'mom_thresh': 0.12, 'profit_target': 0.15, 'hold_minutes': 5},
    {'mom_thresh': 0.15, 'profit_target': 0.20, 'hold_minutes': 8},
    {'mom_thresh': 0.18, 'profit_target': 0.25, 'hold_minutes': 10},
    {'mom_thresh': 0.20, 'profit_target': 0.25, 'hold_minutes': 10},
    {'mom_thresh': 0.22, 'profit_target': 0.30, 'hold_minutes': 12},
]

all_results = []

# Test VWAP grid
print("\n" + "="*80)
print("VWAP PARAMETER GRID")
print("="*80)

for params in vwap_params:
    all_trades = []
    for df in all_dfs:
        trades = grid_search_vwap(df.copy(), **params)
        all_trades.extend(trades)
    
    if all_trades and len(all_trades) >= 3:
        pnls = [t['pnl_pct'] for t in all_trades]
        wins = [t for t in all_trades if t['win']]
        
        avg_pnl = np.mean(pnls)
        std_pnl = np.std(pnls)
        sharpe = (avg_pnl / std_pnl * np.sqrt(252 * 78)) if std_pnl > 0 else 0
        win_rate = len(wins) / len(all_trades) * 100
        trades_per_day = len(all_trades) / 5
        
        result = {
            'strategy': f"VWAP_{params['vwap_thresh']}_{params['profit_target']}_{params['hold_minutes']}",
            'params': params,
            'sharpe': sharpe,
            'trades_per_day': trades_per_day,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'trades': len(all_trades)
        }
        all_results.append(result)
        
        print(f"Thresh:{params['vwap_thresh']:.2f}% Target:{params['profit_target']:.2f}% Hold:{params['hold_minutes']}min | " +
              f"Sharpe:{sharpe:>7.2f} | Trades/Day:{trades_per_day:>4.1f} | Win%:{win_rate:>5.1f}%")

# Test Momentum grid
print("\n" + "="*80)
print("MOMENTUM PARAMETER GRID")
print("="*80)

for params in momentum_params:
    all_trades = []
    for df in all_dfs:
        trades = grid_search_momentum(df.copy(), **params)
        all_trades.extend(trades)
    
    if all_trades and len(all_trades) >= 3:
        pnls = [t['pnl_pct'] for t in all_trades]
        wins = [t for t in all_trades if t['win']]
        
        avg_pnl = np.mean(pnls)
        std_pnl = np.std(pnls)
        sharpe = (avg_pnl / std_pnl * np.sqrt(252 * 78)) if std_pnl > 0 else 0
        win_rate = len(wins) / len(all_trades) * 100
        trades_per_day = len(all_trades) / 5
        
        result = {
            'strategy': f"Mom_{params['mom_thresh']}_{params['profit_target']}_{params['hold_minutes']}",
            'params': params,
            'sharpe': sharpe,
            'trades_per_day': trades_per_day,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'trades': len(all_trades)
        }
        all_results.append(result)
        
        print(f"Thresh:{params['mom_thresh']:.2f}% Target:{params['profit_target']:.2f}% Hold:{params['hold_minutes']}min | " +
              f"Sharpe:{sharpe:>7.2f} | Trades/Day:{trades_per_day:>4.1f} | Win%:{win_rate:>5.1f}%")

# Final results
print("\n" + "="*80)
print("BEST PARAMETERS FOUND")
print("="*80)

if all_results:
    sorted_results = sorted(all_results, key=lambda x: x['sharpe'], reverse=True)
    
    print(f"\nTop 5 by Sharpe:")
    print(f"{'Strategy':<30s} | {'Sharpe':>7s} | {'Trades/Day':>11s} | {'Win%':>6s} | {'Avg P&L':>8s}")
    print("-" * 85)
    
    for r in sorted_results[:5]:
        status = "✅" if r['sharpe'] >= 1.0 else "📈" if r['sharpe'] >= 0.5 else "⚠️" if r['sharpe'] >= 0 else "❌"
        print(f"{r['strategy']:<30s} | {r['sharpe']:>7.2f} | {r['trades_per_day']:>11.1f} | {r['win_rate']:>5.1f}% | {r['avg_pnl']:>7.3f}% {status}")
    
    best = sorted_results[0]
    
    if best['sharpe'] >= 1.0:
        print(f"\n🎯 **PROFITABLE STRATEGY DISCOVERED!**")
        print(f"   Strategy: {best['strategy']}")
        print(f"   Sharpe: {best['sharpe']:.2f}")
        print(f"   Parameters: {best['params']}")
    elif best['sharpe'] >= 0.5:
        print(f"\n📈 **PROMISING!** Close to profitability")
        print(f"   Best Sharpe: {best['sharpe']:.2f}")
        print(f"   Continue optimization with finer grid around these parameters")
    elif best['sharpe'] >= 0:
        print(f"\n⚠️  **PROGRESS** - Positive Sharpe achieved!")
        print(f"   From -43.76 → {best['sharpe']:.2f}")
        print(f"   Try: Longer holds, stricter filters, or different symbols (NVDA, TSLA)")
    else:
        print(f"\n❌ Still negative - need different approach")
    
    with open('grid_search_results.json', 'w') as f:
        json.dump(sorted_results, f, indent=2)
    
    print(f"\n✅ Saved to grid_search_results.json")
