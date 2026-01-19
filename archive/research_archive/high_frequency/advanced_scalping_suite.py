"""
Advanced Scalping Strategy Suite - Comprehensive Testing

Goal: Test 7 professional scalping strategies to find viable approaches

Strategies:
1. Micro-Momentum (volume spikes, tape acceleration)
2. Mean Reversion (sigma deviation from VWAP)
3. VWAP Scalping (bounce/reclaim/rejection)
4. Liquidity Grab (stop hunts, wick plays)
5. Breakout Scalping (tight ranges, key levels)
6. Range Scalping (support/resistance in balanced markets)
7. Opening Drive (first 5-30 min volatility)

Key: Find strategies with:
- Lower natural frequency (<100 trades/day)
- Larger edge per trade (>0.1% to overcome 4.1 bps friction)
- Higher win rates (>55%)
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

FRICTION_BPS = 4.1  # Our proven friction cost

def fetch_1min_data(symbol, date):
    """Fetch 1-minute data"""
    url = "https://financialmodelingprep.com/stable/historical-chart/1min"
    params = {'symbol': symbol, 'from': date, 'to': date, 'apikey': FMP_API_KEY}
    response = requests.get(url, params=params, timeout=10)
    return response.json() if response.status_code == 200 else []

def calculate_vwap(df):
    """Calculate VWAP"""
    return (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()

def calculate_bollinger_bands(prices, period=20, std=2):
    """Calculate Bollinger Bands"""
    rolling_mean = pd.Series(prices).rolling(period).mean()
    rolling_std = pd.Series(prices).rolling(period).std()
    upper = rolling_mean + (std * rolling_std)
    lower = rolling_mean - (std * rolling_std)
    return upper.values, lower.values, rolling_mean.values

# Strategy 1: Micro-Momentum (Volume Spikes)
def micro_momentum_strategy(df):
    """
    Entry: Volume spike (>2x avg) + price move >0.05%
    Exit: 2 minutes or 0.10% profit/loss
    """
    df['vol_sma'] = df['volume'].rolling(20).mean()
    df['vol_spike'] = df['volume'] > 2 * df['vol_sma']
    df['price_change'] = df['close'].pct_change() * 100
    
    trades = []
    position = None
    
    for i in range(30, len(df)):
        if position:
            hold_min = i - position['entry_idx']
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            if hold_min >= 2 or abs(pnl_pct) >= 0.10:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({'strategy': 'Micro-Momentum', 'pnl_pct': pnl_pct, 'hold_min': hold_min, 'win': pnl_pct > 0})
                position = None
        
        if not position and df.loc[i, 'vol_spike']:
            if df.loc[i, 'price_change'] > 0.05:
                position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
            elif df.loc[i, 'price_change'] < -0.05:
                position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
    
    return trades

# Strategy 2: Mean Reversion (Sigma Deviation)
def mean_reversion_strategy(df):
    """
    Entry: Price >2σ from 20-period mean
    Exit: Return to mean or 5 min timeout
    """
    df['sma20'] = df['close'].rolling(20).mean()
    df['std20'] = df['close'].rolling(20).std()
    df['zscore'] = (df['close'] - df['sma20']) / df['std20']
    
    trades = []
    position = None
    
    for i in range(25, len(df)):
        if position:
            hold_min = i - position['entry_idx']
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            # Exit if price returns to mean or timeout
            if abs(df.loc[i, 'zscore']) < 0.5 or hold_min >= 5:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({'strategy': 'Mean Reversion', 'pnl_pct': pnl_pct, 'hold_min': hold_min, 'win': pnl_pct > 0})
                position = None
        
        if not position:
            if df.loc[i, 'zscore'] > 2.0:  # Overbought
                position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
            elif df.loc[i, 'zscore'] < -2.0:  # Oversold
                position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
    
    return trades

# Strategy 3: VWAP Scalping
def vwap_scalping_strategy(df):
    """
    Entry: Price deviates >0.3% from VWAP
    Exit: Snapback to VWAP or 3 min timeout
    """
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
            
            # Exit if back to VWAP or timeout
            if abs(df.loc[i, 'vwap_dev']) < 0.05 or hold_min >= 3:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({'strategy': 'VWAP Scalping', 'pnl_pct': pnl_pct, 'hold_min': hold_min, 'win': pnl_pct > 0})
                position = None
        
        if not position:
            if df.loc[i, 'vwap_dev'] > 0.3:  # Above VWAP
                position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
            elif df.loc[i, 'vwap_dev'] < -0.3:  # Below VWAP
                position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
    
    return trades

# Strategy 4: Liquidity Grab / Stop Run
def liquidity_grab_strategy(df):
    """
    Entry: Price breaks recent high/low then quickly reverses
    Exit: 0.15% profit or 5 min timeout
    """
    df['high_5'] = df['high'].rolling(5).max()
    df['low_5'] = df['low'].rolling(5).min()
    
    trades = []
    position = None
    
    for i in range(10, len(df)):
        if position:
            hold_min = i - position['entry_idx']
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            if abs(pnl_pct) >= 0.15 or hold_min >= 5:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({'strategy': 'Liquidity Grab', 'pnl_pct': pnl_pct, 'hold_min': hold_min, 'win': pnl_pct > 0})
                position = None
        
        if not position and i > 5:
            # Detect stop hunt: break high then reject
            prev_high = df.loc[i-1, 'high_5']
            if df.loc[i, 'high'] > prev_high and df.loc[i, 'close'] < prev_high:
                position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
            
            # Break low then reclaim
            prev_low = df.loc[i-1, 'low_5']
            if df.loc[i, 'low'] < prev_low and df.loc[i, 'close'] > prev_low:
                position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
    
    return trades

# Strategy 5: Breakout Scalping
def breakout_scalping_strategy(df):
    """
    Entry: Break of 30-min range with volume
    Exit: 0.20% profit or 10 min timeout
    """
    if len(df) < 40:
        return []
    
    # First 30 minutes = opening range
    or_high = df.loc[:29, 'high'].max()
    or_low = df.loc[:29, 'low'].min()
    
    trades = []
    position = None
    
    for i in range(30, len(df)):
        if position:
            hold_min = i - position['entry_idx']
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            if abs(pnl_pct) >= 0.20 or hold_min >= 10:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({'strategy': 'Breakout Scalping', 'pnl_pct': pnl_pct, 'hold_min': hold_min, 'win': pnl_pct > 0})
                position = None
        
        if not position:
            if df.loc[i, 'high'] > or_high:
                position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
            elif df.loc[i, 'low'] < or_low:
                position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
    
    return trades

# Strategy 6: Range Scalping
def range_scalping_strategy(df):
    """
    Entry: Buy support, sell resistance in tight range
    Exit: Opposite side of range or breakout
    """
    if len(df) < 60:
        return []
    
    # Define range from first hour
    range_high = df.loc[:59, 'high'].max()
    range_low = df.loc[:59, 'low'].min()
    range_mid = (range_high + range_low) / 2
    
    # Only trade if tight range (<0.5%)
    if (range_high - range_low) / range_mid > 0.005:
        return []
    
    trades = []
    position = None
    
    for i in range(60, len(df)):
        if position:
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            # Exit at opposite side or breakout
            if (position['type'] == 'long' and df.loc[i, 'close'] >= range_high) or \
               (position['type'] == 'short' and df.loc[i, 'close'] <= range_low) or \
               df.loc[i, 'close'] > range_high or df.loc[i, 'close'] < range_low:
                pnl_pct -= FRICTION_BPS / 100
                hold_min = i - position['entry_idx']
                trades.append({'strategy': 'Range Scalping', 'pnl_pct': pnl_pct, 'hold_min': hold_min, 'win': pnl_pct > 0})
                position = None
        
        if not position:
            if df.loc[i, 'close'] <= range_low * 1.001:
                position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
            elif df.loc[i, 'close'] >= range_high * 0.999:
                position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
    
    return trades

# Strategy 7: Opening Drive
def opening_drive_strategy(df):
    """
    Entry: First 30 min - trade with momentum
    Exit: After 30 min or 0.15% profit/loss
    """
    if len(df) < 30:
        return []
    
    trades = []
    
    # Only trade in first 30 minutes
    for i in range(5, 30):
        # Calculate 5-bar momentum
        momentum = (df.loc[i, 'close'] - df.loc[i-5, 'close']) / df.loc[i-5, 'close'] * 100
        
        if abs(momentum) > 0.10:  # Significant move
            entry_price = df.loc[i, 'close']
            entry_type = 'long' if momentum > 0 else 'short'
            
            # Hold for 5 minutes max
            for j in range(i+1, min(i+6, len(df))):
                pnl_pct = (df.loc[j, 'close'] - entry_price) / entry_price * 100
                if entry_type == 'short':
                    pnl_pct = -pnl_pct
                
                if abs(pnl_pct) >= 0.15 or j == i+5:
                    pnl_pct -= FRICTION_BPS / 100
                    trades.append({'strategy': 'Opening Drive', 'pnl_pct': pnl_pct, 'hold_min': j-i, 'win': pnl_pct > 0})
                    break
    
    return trades[:1]  # Max 1 trade per day

# Run all strategies
print("="*80)
print("ADVANCED SCALPING STRATEGY SUITE")
print("="*80)
print(f"\nFriction cost: {FRICTION_BPS} bps ({FRICTION_BPS/100:.3f}%) per round-trip")

test_dates = ['2024-03-15', '2024-05-20', '2024-07-10', '2024-09-18', '2024-11-15']

strategies = [
    ('Micro-Momentum', micro_momentum_strategy),
    ('Mean Reversion', mean_reversion_strategy),
    ('VWAP Scalping', vwap_scalping_strategy),
    ('Liquidity Grab', liquidity_grab_strategy),
    ('Breakout Scalping', breakout_scalping_strategy),
    ('Range Scalping', range_scalping_strategy),
    ('Opening Drive', opening_drive_strategy),
]

all_results = []

for strategy_name, strategy_func in strategies:
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
        std_pnl = np.std(pnls)
        sharpe = (avg_pnl / std_pnl * np.sqrt(252 * 78)) if std_pnl > 0 else 0
        win_rate = len(wins) / len(all_trades) * 100
        avg_hold = np.mean([t['hold_min'] for t in all_trades])
        
        # Estimate annual trades
        trades_per_day = len(all_trades) / 5
        annual_trades = trades_per_day * 252
        annual_friction = annual_trades * (FRICTION_BPS / 100)
        
        print(f"Trades (5 days):   {len(all_trades)}")
        print(f"Trades/day:        {trades_per_day:.1f}")
        print(f"Annual trades:     {annual_trades:.0f}")
        print(f"Win Rate:          {win_rate:.1f}%")
        print(f"Avg P&L:           {avg_pnl:.3f}%")
        print(f"Avg Hold:          {avg_hold:.1f} min")
        print(f"Sharpe:            {sharpe:.2f}")
        print(f"Annual Friction:   {annual_friction:.1f}%")
        
        result = {
            'strategy': strategy_name,
            'trades': len(all_trades),
            'trades_per_day': trades_per_day,
            'annual_trades': annual_trades,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'sharpe': sharpe,
            'annual_friction': annual_friction
        }
        
        all_results.append(result)
        
        if sharpe >= 1.0:
            print(f"\n✅ **GO** - Profitable!")
        elif sharpe >= 0.5:
            print(f"\n⚠️  **MARGINAL** - Close to viable")
        else:
            print(f"\n❌ **NO-GO** - Unprofitable")
    else:
        print("❌ No trades generated")

# Final ranking
print("\n" + "="*80)
print("FINAL RANKING - ALL SCALPING STRATEGIES")
print("="*80)

if all_results:
    sorted_results = sorted(all_results, key=lambda x: x['sharpe'], reverse=True)
    
    print(f"\n{'Strategy':<20s} | {'Sharpe':>7s} | {'Trades/Day':>11s} | {'Annual Frict':>13s} | {'Status':>10s}")
    print("-" * 80)
    
    for r in sorted_results:
        status = "✅ GO" if r['sharpe'] >= 1.0 else "⚠️  MARG" if r['sharpe'] >= 0.5 else "❌ NO-GO"
        print(f"{r['strategy']:<20s} | {r['sharpe']:>7.2f} | {r['trades_per_day']:>11.1f} | {r['annual_friction']:>12.1f}% | {status:>10s}")
    
    best = sorted_results[0]
    if best['sharpe'] >= 1.0:
        print(f"\n🎯 WINNER: {best['strategy']} (Sharpe {best['sharpe']:.2f})")
        print(f"   Trades: {best['trades_per_day']:.1f}/day | Friction: {best['annual_friction']:.1f}%/year")
    else:
        print(f"\n⚠️  BEST: {best['strategy']} (Sharpe {best['sharpe']:.2f}) - Still marginal/unprofitable")

# Save
with open('advanced_scalping_results.json', 'w') as f:
    json.dump(all_results, f, indent=2)

print(f"\n✅ Saved to advanced_scalping_results.json")
