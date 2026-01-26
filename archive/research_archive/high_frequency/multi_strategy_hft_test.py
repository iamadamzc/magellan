"""
Multi-Strategy HFT Testing Suite

After RSI mean reversion failed, test 3 more strategies quickly:
1. VWAP Reversion (price deviation from VWAP)
2. Opening Range Breakout (first 30-min range)
3. Momentum Scalping (5-min momentum bursts)

Goal: Find if ANY high-frequency strategy is profitable with 67ms latency
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

def fetch_1min_data(symbol, date):
    """Fetch 1-minute data"""
    url = "https://financialmodelingprep.com/stable/historical-chart/1min"
    params = {'symbol': symbol, 'from': date, 'to': date, 'apikey': FMP_API_KEY}
    response = requests.get(url, params=params, timeout=10)
    return response.json() if response.status_code == 200 else []

def vwap_reversion_strategy(bars, slippage_bps=1.0):
    """
    VWAP Reversion: Buy when price < 0.995 * VWAP, sell when price > 1.005 * VWAP
    Exit: Opposite signal or 10-minute time stop
    """
    if len(bars) < 50:
        return []
    
    df = pd.DataFrame(bars).sort_values('date').reset_index(drop=True)
    
    # Calculate VWAP
    df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
    
    trades = []
    position = None
    
    for i in range(20, len(df)):
        price = df.loc[i, 'close']
        vwap = df.loc[i, 'vwap']
        time = pd.to_datetime(df.loc[i, 'date'])
        
        # Exit logic
        if position:
            entry_price = position['entry_price']
            entry_time = position['entry_time']
            hold_min = (time - entry_time).total_seconds() / 60
            
            pnl_pct = (price - entry_price) / entry_price * 100 if position['type'] == 'long' else (entry_price - price) / entry_price * 100
            
            exit_cond = False
            if position['type'] == 'long' and price > 1.005 * vwap:
                exit_cond = True
            elif position['type'] == 'short' and price < 0.995 * vwap:
                exit_cond = True
            elif hold_min >= 10:
                exit_cond = True
            
            if exit_cond:
                pnl_pct -= 2 * slippage_bps / 100
                trades.append({'pnl_pct': pnl_pct, 'hold_min': hold_min, 'win': pnl_pct > 0})
                position = None
        
        # Entry logic
        if not position:
            if price < 0.995 * vwap:
                position = {'type': 'long', 'entry_price': price, 'entry_time': time}
            elif price > 1.005 * vwap:
                position = {'type': 'short', 'entry_price': price, 'entry_time': time}
    
    return trades

def opening_range_breakout(bars, slippage_bps=1.0):
    """
    Opening Range Breakout: First 30 min = range, breakout = signal
    Exit: 60-min time stop or 0.3% profit/loss
    """
    if len(bars) < 100:
        return []
    
    df = pd.DataFrame(bars).sort_values('date').reset_index(drop=True)
    
    # First 30 minutes (bars 0-29)
    or_high = df.loc[:29, 'high'].max()
    or_low = df.loc[:29, 'low'].min()
    
    trades = []
    position = None
    
    for i in range(30, len(df)):
        price = df.loc[i, 'close']
        time = pd.to_datetime(df.loc[i, 'date'])
        
        # Exit logic
        if position:
            entry_price = position['entry_price']
            entry_time = position['entry_time']
            hold_min = (time - entry_time).total_seconds() / 60
            
            pnl_pct = (price - entry_price) / entry_price * 100 if position['type'] == 'long' else (entry_price - price) / entry_price * 100
            
            exit_cond = False
            if abs(pnl_pct) >= 0.3 or hold_min >= 60:
                exit_cond = True
            
            if exit_cond:
                pnl_pct -= 2 * slippage_bps / 100
                trades.append({'pnl_pct': pnl_pct, 'hold_min': hold_min, 'win': pnl_pct > 0})
                position = None
        
        # Entry logic
        if not position:
            if price > or_high:
                position = {'type': 'long', 'entry_price': price, 'entry_time': time}
            elif price < or_low:
                position = {'type': 'short', 'entry_price': price, 'entry_time': time}
    
    return trades

def momentum_scalping(bars, slippage_bps=1.0):
    """
    Momentum Scalping: Large 5-bar moves = momentum
    Enter in direction of move, exit after 5 minutes
    """
    if len(bars) < 50:
        return []
    
    df = pd.DataFrame(bars).sort_values('date').reset_index(drop=True)
    
    trades = []
    position = None
    
    for i in range(20, len(df)):
        # Calculate 5-bar momentum
        if i >= 5:
            momentum = (df.loc[i, 'close'] - df.loc[i-5, 'close']) / df.loc[i-5, 'close'] * 100
        else:
            continue
        
        price = df.loc[i, 'close']
        time = pd.to_datetime(df.loc[i, 'date'])
        
        # Exit logic
        if position:
            entry_price = position['entry_price']
            entry_time = position['entry_time']
            hold_min = (time - entry_time).total_seconds() / 60
            
            pnl_pct = (price - entry_price) / entry_price * 100 if position['type'] == 'long' else (entry_price - price) / entry_price * 100
            
            if hold_min >= 5 or abs(pnl_pct) >= 0.2:
                pnl_pct -= 2 * slippage_bps / 100
                trades.append({'pnl_pct': pnl_pct, 'hold_min': hold_min, 'win': pnl_pct > 0})
                position = None
        
        # Entry logic
        if not position:
            if momentum > 0.15:  # Strong up move
                position = {'type': 'long', 'entry_price': price, 'entry_time': time}
            elif momentum < -0.15:  # Strong down move
                position = {'type': 'short', 'entry_price': price, 'entry_time': time}
    
    return trades

# Quick multi-strategy test
print("="*80)
print("MULTI-STRATEGY HFT TESTING SUITE")
print("="*80)

test_dates = ['2024-03-15', '2024-05-20', '2024-07-10', '2024-09-18', '2024-11-15']

results_summary = []

for strategy_name, strategy_func in [
    ('VWAP Reversion', vwap_reversion_strategy),
    ('Opening Range Breakout', opening_range_breakout),
    ('Momentum Scalping', momentum_scalping)
]:
    print(f"\n{'='*80}")
    print(f"{strategy_name}")
    print(f"{'='*80}")
    
    all_trades = []
    
    for date in test_dates:
        bars = fetch_1min_data('SPY', date)
        if len(bars) < 50:
            continue
        
        trades = strategy_func(bars, slippage_bps=1.0)
        all_trades.extend(trades)
    
    if all_trades:
        pnls = [t['pnl_pct'] for t in all_trades]
        wins = [t for t in all_trades if t['win']]
        
        avg_pnl = np.mean(pnls)
        std_pnl = np.std(pnls)
        sharpe = (avg_pnl / std_pnl * np.sqrt(252 * 78)) if std_pnl > 0 else 0
        win_rate = len(wins) / len(all_trades) * 100
        
        print(f"Trades:      {len(all_trades)}")
        print(f"Win Rate:    {win_rate:.1f}%")
        print(f"Avg P&L:     {avg_pnl:.3f}%")
        print(f"Sharpe:      {sharpe:.2f}")
        print(f"Total Return: {sum(pnls):.2f}%")
        
        results_summary.append({
            'strategy': strategy_name,
            'sharpe': sharpe,
            'trades': len(all_trades),
            'win_rate': win_rate
        })
        
        if sharpe >= 1.0:
            print(f"\n✅ **GO** - Profitable strategy!")
        elif sharpe >= 0.5:
            print(f"\n⚠️  **MARGINAL** - Needs optimization")
        else:
            print(f"\n❌ **NO-GO** - Unprofitable")
    else:
        print("❌ No trades generated")

# Final summary
print("\n" + "="*80)
print("FINAL SUMMARY - ALL HFT STRATEGIES")
print("="*80)

if results_summary:
    sorted_results = sorted(results_summary, key=lambda x: x['sharpe'], reverse=True)
    
    print(f"\n{'Strategy':<25s} | {'Sharpe':>8s} | {'Trades':>7s} | {'Win%':>6s} | {'Status':>10s}")
    print("-" * 80)
    
    for result in sorted_results:
        status = "✅ GO" if result['sharpe'] >= 1.0 else "⚠️  COND" if result['sharpe'] >= 0.5 else "❌ NO-GO"
        print(f"{result['strategy']:<25s} | {result['sharpe']:>8.2f} | {result['trades']:>7d} | {result['win_rate']:>5.1f}% | {status:>10s}")
    
    best = sorted_results[0]
    if best['sharpe'] >= 1.0:
        print(f"\n🎯 WINNER: {best['strategy']} (Sharpe {best['sharpe']:.2f})")
    else:
        print(f"\n❌ NO PROFITABLE HFT STRATEGIES FOUND")
        print("   Even with 67ms latency, intraday/scalping faces too much friction")
        print("   Recommendation: Stick with event-driven strategies (FOMC validated)")

# Save results
with open('hft_multi_strategy_results.json', 'w') as f:
    json.dump(results_summary, f, indent=2)

print(f"\n✅ Saved to hft_multi_strategy_results.json")
