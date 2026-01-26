"""
Full Year Backtest - 2024 & 2025

Strategy: Optimized VWAP Mean Reversion
Parameters:
- VWAP threshold: 0.45%
- Profit target: 0.30%
- Hold time: 15 minutes
- Time filter: Avoid 12-2 PM (lunch hour)

Goal: Generate annual performance reports for 2024 and 2025
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
    """Fetch 1-minute OHLCV data"""
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
    """Calculate VWAP"""
    return (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()

def optimized_vwap_strategy(df, vwap_thresh=0.45, profit_target=0.30, hold_minutes=15, use_time_filter=True):
    """
    Optimized VWAP strategy with time filter
    """
    if len(df) < 20:
        return []
    
    df['vwap'] = calculate_vwap(df)
    df['vwap_dev'] = (df['close'] - df['vwap']) / df['vwap'] * 100
    df['time'] = pd.to_datetime(df['date'])
    df['hour'] = df['time'].dt.hour
    
    trades = []
    position = None
    
    for i in range(10, len(df)):
        if position:
            hold_min = i - position['entry_idx']
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            # Exit conditions
            if pnl_pct >= profit_target or abs(df.loc[i, 'vwap_dev']) < 0.03 or hold_min >= hold_minutes:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({
                    'entry_time': position['entry_time'],
                    'exit_time': df.loc[i, 'time'],
                    'type': position['type'],
                    'pnl_pct': pnl_pct,
                    'win': pnl_pct > 0,
                    'hold_min': hold_min
                })
                position = None
        
        if not position:
            # Time filter
            if use_time_filter and 12 <= df.loc[i, 'hour'] < 14:
                continue
            
            # Entry signals
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
    """Generate list of potential trading days (weekdays)"""
    current = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    trading_days = []
    while current <= end:
        # Skip weekends
        if current.weekday() < 5:  # Monday=0, Friday=4
            trading_days.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    return trading_days

print("="*80)
print("FULL YEAR BACKTEST - 2024 & 2025")
print("="*80)
print("\nStrategy: Optimized VWAP Mean Reversion")
print("Parameters: 0.45% threshold, 0.30% target, 15min hold, time filter ON")

# Generate trading days
days_2024 = generate_trading_days('2024-01-02', '2024-12-31')
days_2025 = generate_trading_days('2025-01-02', '2025-01-16')  # Up to today

print(f"\n2024: {len(days_2024)} potential trading days")
print(f"2025: {len(days_2025)} potential trading days (YTD)")

# Run backtest for each year
results_by_year = {}

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
        trades = optimized_vwap_strategy(df)
        
        for trade in trades:
            trade['date'] = date
            all_trades.append(trade)
    
    print(f"\nCompleted: {successful_days} days with data, {failed_days} days failed/holidays")
    
    if all_trades:
        # Calculate metrics
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
        
        # Monthly breakdown
        monthly_trades = {}
        for trade in all_trades:
            month = trade['date'][:7]  # YYYY-MM
            if month not in monthly_trades:
                monthly_trades[month] = []
            monthly_trades[month].append(trade)
        
        # Store results
        results_by_year[year] = {
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
            },
            'trades': all_trades[:100]  # Save first 100 for analysis
        }
        
        # Print summary
        print(f"\n{year} RESULTS:")
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
        
        # Monthly performance
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
        results_by_year[year] = None

# Comparison
if '2024' in results_by_year and '2025' in results_by_year:
    print(f"\n{'='*80}")
    print("YEAR-OVER-YEAR COMPARISON")
    print(f"{'='*80}")
    
    print(f"\n{'Metric':<20s} | {'2024':>12s} | {'2025':>12s} | {'Change':>12s}")
    print("-" * 65)
    
    for metric, label in [
        ('total_trades', 'Total Trades'),
        ('trades_per_day', 'Trades/Day'),
        ('win_rate', 'Win Rate (%)'),
        ('sharpe', 'Sharpe Ratio'),
        ('total_return', 'Total Return (%)')
    ]:
        val_2024 = results_by_year['2024'].get(metric, 0)
        val_2025 = results_by_year['2025'].get(metric, 0)
        
        if metric == 'total_trades':
            change = val_2025 - val_2024
            print(f"{label:<20s} | {val_2024:>12.0f} | {val_2025:>12.0f} | {change:>+12.0f}")
        else:
            change = val_2025 - val_2024
            print(f"{label:<20s} | {val_2024:>12.2f} | {val_2025:>12.2f} | {change:>+12.2f}")

# Save results
with open('full_year_backtest_results.json', 'w') as f:
    json.dump(results_by_year, f, indent=2, default=str)

print(f"\n{'='*80}")
print("✅ Saved detailed results to full_year_backtest_results.json")
print(f"{'='*80}")
