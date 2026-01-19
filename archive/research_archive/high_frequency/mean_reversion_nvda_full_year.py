"""
Mean Reversion NVDA - Full Year Validation (2024 + 2025)

Baseline config on NVDA (Q1 2024):
- Sharpe: 2.04 (PROFITABLE!)
- Win Rate: 60.0%
- Avg Win: 0.171%
- Avg Loss: -0.228%
- Trades/Day: 6.0

Config:
- Lookback: 20
- Z-threshold: 2.0
- Profit target: 0.20%
- Stop loss: 0.20%
- Hold: 20 minutes
- RSI confirmation: <30 or >70
- Friction: 1.0 bps

Goal: Validate on full 2024 (252 days) and 2025 (252 days)
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

def mean_reversion_nvda(df):
    """Best config from Q1 testing"""
    lookback = 20
    z_threshold = 2.0
    profit_target = 0.20
    stop_loss = 0.20
    hold_minutes = 20
    
    if len(df) < 30:
        return []
    
    df['sma'] = df['close'].rolling(lookback).mean()
    df['std'] = df['close'].rolling(lookback).std()
    df['z_score'] = (df['close'] - df['sma']) / df['std']
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    df['time'] = pd.to_datetime(df['date'])
    df['hour'] = df['time'].dt.hour
    
    trades = []
    position = None
    
    for i in range(lookback + 15, len(df)):
        if position:
            hold_min = i - position['entry_idx']
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            exit_reason = None
            
            if position['type'] == 'long' and df.loc[i, 'z_score'] > -0.5:
                exit_reason = 'mean_revert'
            elif position['type'] == 'short' and df.loc[i, 'z_score'] < 0.5:
                exit_reason = 'mean_revert'
            elif pnl_pct >= profit_target:
                exit_reason = 'target'
            elif pnl_pct <= -stop_loss:
                exit_reason = 'stop_loss'
            elif hold_min >= hold_minutes:
                exit_reason = 'timeout'
            
            if exit_reason:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({'pnl_pct': pnl_pct, 'win': pnl_pct > 0, 'date': position['date']})
                position = None
        
        if not position:
            if 12 <= df.loc[i, 'hour'] < 14:
                continue
            
            if pd.isna(df.loc[i, 'z_score']) or pd.isna(df.loc[i, 'rsi']):
                continue
            
            if df.loc[i, 'z_score'] < -z_threshold and df.loc[i, 'rsi'] < 30:
                position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i, 'date': df.loc[i, 'date'][:10]}
            elif df.loc[i, 'z_score'] > z_threshold and df.loc[i, 'rsi'] > 70:
                position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i, 'date': df.loc[i, 'date'][:10]}
    
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
print("MEAN REVERSION NVDA - FULL YEAR VALIDATION")
print("="*80)
print("\nConfig: Z-score 2.0, 0.20% target/stop, RSI confirm, 1.0 bps friction")

days_2024 = generate_trading_days('2024-01-02', '2024-12-31')
days_2025 = generate_trading_days('2025-01-02', '2025-12-31')

print(f"\n2024: {len(days_2024)} potential trading days")
print(f"2025: {len(days_2025)} potential trading days")

results_by_year = {}

for year, days in [('2024', days_2024), ('2025', days_2025)]:
    print(f"\n{'='*80}")
    print(f"TESTING {year}")
    print(f"{'='*80}")
    
    all_trades = []
    successful_days = 0
    
    for idx, date in enumerate(days):
        if idx % 50 == 0:
            print(f"Progress: {idx}/{len(days)} days...", end='\r')
        
        bars = fetch_1min_data('NVDA', date)
        if len(bars) < 50:
            continue
        
        successful_days += 1
        df = pd.DataFrame(bars).sort_values('date').reset_index(drop=True)
        trades = mean_reversion_nvda(df)
        all_trades.extend(trades)
    
    print(f"\nCompleted: {successful_days} days with data")
    
    if all_trades:
        pnls = [t['pnl_pct'] for t in all_trades]
        wins = [t for t in all_trades if t['win']]
        losses = [t for t in all_trades if not t['win']]
        
        avg_pnl = np.mean(pnls)
        std_pnl = np.std(pnls)
        sharpe = (avg_pnl / std_pnl * np.sqrt(252 * len(all_trades) / successful_days)) if std_pnl > 0 else 0
        win_rate = len(wins) / len(all_trades) * 100
        trades_per_day = len(all_trades) / successful_days
        
        avg_win = np.mean([t['pnl_pct'] for t in wins]) if wins else 0
        avg_loss = np.mean([t['pnl_pct'] for t in losses]) if losses else 0
        
        # Monthly breakdown
        monthly_trades = {}
        for trade in all_trades:
            month = trade['date'][:7]
            if month not in monthly_trades:
                monthly_trades[month] = []
            monthly_trades[month].append(trade)
        
        results_by_year[year] = {
            'total_trades': len(all_trades),
            'successful_days': successful_days,
            'trades_per_day': trades_per_day,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'sharpe': sharpe,
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
        
        print(f"\n{year} RESULTS:")
        print(f"{'='*80}")
        print(f"Total Trades:        {len(all_trades)}")
        print(f"Trades/Day:          {trades_per_day:.2f}")
        print(f"Win Rate:            {win_rate:.1f}%")
        print(f"Avg P&L:             {avg_pnl:.3f}%")
        print(f"Avg Win:             {avg_win:.3f}%")
        print(f"Avg Loss:            {avg_loss:.3f}%")
        print(f"**Sharpe Ratio:      {sharpe:.2f}**")
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

# Final summary
print(f"\n{'='*80}")
print("FINAL VERDICT")
print(f"{'='*80}")

if '2024' in results_by_year and '2025' in results_by_year:
    r2024 = results_by_year['2024']
    r2025 = results_by_year['2025']
    
    print(f"\n2024: Sharpe {r2024['sharpe']:.2f}, Return {r2024['total_return']:.2f}%")
    print(f"2025: Sharpe {r2025['sharpe']:.2f}, Return {r2025['total_return']:.2f}%")
    
    avg_sharpe = (r2024['sharpe'] + r2025['sharpe']) / 2
    
    if avg_sharpe > 1.0:
        print(f"\n🎯 **VALIDATED!** Avg Sharpe {avg_sharpe:.2f} > 1.0")
        print(f"   Mean Reversion on NVDA is profitable and ready for deployment")
    elif avg_sharpe > 0.5:
        print(f"\n✅ **PROFITABLE** Avg Sharpe {avg_sharpe:.2f}")
        print(f"   Consider deployment with caution")
    else:
        print(f"\n❌ Avg Sharpe {avg_sharpe:.2f} - failed full-year validation")

# Save
with open('mean_reversion_nvda_full_year_results.json', 'w') as f:
    json.dump(results_by_year, f, indent=2)

print(f"\n✅ Saved to mean_reversion_nvda_full_year_results.json")
