"""
V2 Strategy Backtest - Stricter Filters

Based on 2024 analysis, implementing:
✅ VWAP Threshold: 0.60% (vs 0.45%)
✅ Profit Target: 0.40% (vs 0.30%)
✅ Stop Loss: 0.20% (NEW)
✅ Hold Time: 20 min (vs 15 min)
✅ Time Filter: 12-2 PM (keep)
✅ Volatility Filter: ATR > 0.5% (NEW)
✅ Volume Filter: >2x avg (NEW)

Hypothesis: Reduce trades 361 → 100-150/year, improve win rate 36% → 45%+
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

def calculate_vwap(df):
    return (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()

def calculate_atr(df, period=14):
    """Calculate Average True Range"""
    df['prev_close'] = df['close'].shift(1)
    df['tr'] = df[['high', 'low', 'close', 'prev_close']].apply(
        lambda x: max(x['high'] - x['low'], 
                     abs(x['high'] - x['prev_close']) if pd.notna(x['prev_close']) else 0,
                     abs(x['low'] - x['prev_close']) if pd.notna(x['prev_close']) else 0), axis=1)
    return df['tr'].rolling(period).mean()

def v2_strategy(df, vwap_thresh=0.60, profit_target=0.40, stop_loss=0.20, 
                hold_minutes=20, min_atr_pct=0.5, vol_multiplier=2.0):
    """
    V2 Strategy with strict filters
    """
    if len(df) < 30:
        return []
    
    # Calculate indicators
    df['vwap'] = calculate_vwap(df)
    df['vwap_dev'] = (df['close'] - df['vwap']) / df['vwap'] * 100
    df['time'] = pd.to_datetime(df['date'])
    df['hour'] = df['time'].dt.hour
    
    # ATR for volatility filter
    df['atr'] = calculate_atr(df)
    df['atr_pct'] = df['atr'] / df['close'] * 100
    
    # Volume filter
    df['vol_sma'] = df['volume'].rolling(20).mean()
    df['vol_spike'] = df['volume'] > vol_multiplier * df['vol_sma']
    
    trades = []
    position = None
    
    for i in range(30, len(df)):
        if position:
            hold_min = i - position['entry_idx']
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            # Exit conditions
            exit_reason = None
            if pnl_pct >= profit_target:
                exit_reason = 'target'
            elif pnl_pct <= -stop_loss:
                exit_reason = 'stop_loss'
            elif abs(df.loc[i, 'vwap_dev']) < 0.03:
                exit_reason = 'vwap_return'
            elif hold_min >= hold_minutes:
                exit_reason = 'timeout'
            
            if exit_reason:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({
                    'entry_time': position['entry_time'],
                    'exit_time': df.loc[i, 'time'],
                    'type': position['type'],
                    'pnl_pct': pnl_pct,
                    'win': pnl_pct > 0,
                    'hold_min': hold_min,
                    'exit_reason': exit_reason
                })
                position = None
        
        if not position:
            # ALL filters must pass
            
            # Time filter
            if 12 <= df.loc[i, 'hour'] < 14:
                continue
            
            # Volatility filter
            if pd.notna(df.loc[i, 'atr_pct']) and df.loc[i, 'atr_pct'] < min_atr_pct:
                continue
            
            # Volume filter
            if not df.loc[i, 'vol_spike']:
                continue
            
            # Entry signals (stricter threshold)
            if df.loc[i, 'vwap_dev'] > vwap_thresh:
                position = {
                    'type': 'short',
                    'entry_price': df.loc[i, 'close'],
                    'entry_idx': i,
                    'entry_time': df.loc[i, 'time']
                }
            elif df.loc[i, 'vwap_dev'] < -vwap_thresh:
                position = {
                    'type': 'long',
                    'entry_price': df.loc[i, 'close'],
                    'entry_idx': i,
                    'entry_time': df.loc[i, 'time']
                }
    
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
print("V2 STRATEGY BACKTEST - 2024 & 2025 (FULL YEARS)")
print("="*80)
print("\nConfiguration V2:")
print("  VWAP Threshold: 0.60% (vs 0.45% V1)")
print("  Profit Target: 0.40% (vs 0.30% V1)")
print("  Stop Loss: 0.20% (NEW)")
print("  Hold Time: 20 min (vs 15 min V1)")
print("  Volatility Filter: ATR > 0.5% (NEW)")
print("  Volume Filter: >2x average (NEW)")

# Generate trading days for FULL years
days_2024 = generate_trading_days('2024-01-02', '2024-12-31')
days_2025 = generate_trading_days('2025-01-02', '2025-12-31')  # FULL 2025

print(f"\n2024: {len(days_2024)} potential trading days")
print(f"2025: {len(days_2025)} potential trading days (FULL YEAR)")

results_v2 = {}

for year, days in [('2024', days_2024), ('2025', days_2025)]:
    print(f"\n{'='*80}")
    print(f"BACKTESTING {year}")
    print(f"{'='*80}")
    
    all_trades = []
    successful_days = 0
    failed_days = 0
    
    for idx, date in enumerate(days):
        if idx % 50 == 0:
            print(f"Progress: {idx}/{len(days)} days...", end='\r')
        
        bars = fetch_1min_data('SPY', date)
        
        if len(bars) < 50:
            failed_days += 1
            continue
        
        successful_days += 1
        df = pd.DataFrame(bars).sort_values('date').reset_index(drop=True)
        trades = v2_strategy(df)
        
        for trade in trades:
            trade['date'] = date
            all_trades.append(trade)
    
    print(f"\nCompleted: {successful_days} days, {failed_days} failed/holidays")
    
    if all_trades:
        pnls = [t['pnl_pct'] for t in all_trades]
        wins = [t for t in all_trades if t['win']]
        losses = [t for t in all_trades if not t['win']]
        
        avg_pnl = np.mean(pnls)
        std_pnl = np.std(pnls)
        sharpe = (avg_pnl / std_pnl * np.sqrt(252 * len(all_trades) / successful_days)) if std_pnl > 0 and successful_days > 0 else 0
        win_rate = len(wins) / len(all_trades) * 100
        
        avg_win = np.mean([t['pnl_pct'] for t in wins]) if wins else 0
        avg_loss = np.mean([t['pnl_pct'] for t in losses]) if losses else 0
        
        trades_per_day = len(all_trades) / successful_days if successful_days > 0 else 0
        
        # Monthly
        monthly_trades = {}
        for trade in all_trades:
            month = trade['date'][:7]
            if month not in monthly_trades:
                monthly_trades[month] = []
            monthly_trades[month].append(trade)
        
        results_v2[year] = {
            'total_trades': len(all_trades),
            'successful_days': successful_days,
            'trades_per_day': trades_per_day,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'std_pnl': std_pnl,
            'sharpe': sharpe,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'best_trade': max(pnls),
            'worst_trade': min(pnls),
            'total_return': sum(pnls),
            'monthly_breakdown': {
                month: {
                    'trades': len(trades),
                    'return': sum(t['pnl_pct'] for t in trades),
                    'win_rate': sum(1 for t in trades if t['win']) / len(trades) * 100
                }
                for month, trades in sorted(monthly_trades.items())
            }
        }
        
        print(f"\n{year} RESULTS (V2):")
        print(f"{'='*80}")
        print(f"Total Trades:        {len(all_trades)}")
        print(f"Trades/Day:          {trades_per_day:.2f}")
        print(f"Win Rate:            {win_rate:.1f}%")
        print(f"Avg P&L:             {avg_pnl:.3f}%")
        print(f"Avg Win:             {avg_win:.3f}%")
        print(f"Avg Loss:            {avg_loss:.3f}%")
        print(f"**Sharpe Ratio:      {sharpe:.2f}**")
        print(f"Best Trade:          {max(pnls):.3f}%")
        print(f"Worst Trade:         {min(pnls):.3f}%")
        print(f"**Total Return:      {sum(pnls):.2f}%**")
        
        print(f"\nMonthly Breakdown:")
        print(f"{'Month':<10s} | {'Trades':>7s} | {'Return':>8s} | {'Win %':>6s}")
        print("-" * 45)
        for month in sorted(monthly_trades.keys()):
            m_data = monthly_trades[month]
            m_return = sum(t['pnl_pct'] for t in m_data)
            m_wins = sum(1 for t in m_data if t['win'])
            m_win_rate = m_wins / len(m_data) * 100
            print(f"{month:<10s} | {len(m_data):>7d} | {m_return:>7.2f}% | {m_win_rate:>5.1f}%")
    else:
        print(f"\n⚠️  No trades in {year}")
        results_v2[year] = None

# Comparison V1 vs V2
print(f"\n{'='*80}")
print("V1 vs V2 COMPARISON")
print(f"{'='*80}")

# Load V1 results
with open('full_year_backtest_results.json', 'r') as f:
    results_v1 = json.load(f)

print(f"\n2024 Comparison:")
print(f"{'Metric':<20s} | {'V1 (0.45%)':>15s} | {'V2 (0.60%)':>15s} | {'Change':>12s}")
print("-" * 70)

for metric, label in [
    ('total_trades', 'Trades'),
    ('trades_per_day', 'Trades/Day'),
    ('win_rate', 'Win Rate (%)'),
    ('sharpe', 'Sharpe'),
    ('total_return', 'Return (%)')
]:
    v1_val = results_v1['2024'].get(metric, 0)
    v2_val = results_v2['2024'].get(metric, 0) if results_v2.get('2024') else 0
    change = v2_val - v1_val
    
    if metric == 'total_trades':
        print(f"{label:<20s} | {v1_val:>15.0f} | {v2_val:>15.0f} | {change:>+12.0f}")
    else:
        print(f"{label:<20s} | {v1_val:>15.2f} | {v2_val:>15.2f} | {change:>+12.2f}")

# Save
with open('v2_backtest_results.json', 'w') as f:
    json.dump(results_v2, f, indent=2, default=str)

print(f"\n{'='*80}")
print("✅ Saved V2 results to v2_backtest_results.json")
print(f"{'='*80}")
