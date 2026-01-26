"""
Opening Range Breakout - Full Year Validation (QQQ & IWM)

Best QQQ config from optimization:
- Range: 10 minutes
- Profit target: 0.30%
- Stop loss: 0.20%
- Hold: 60 minutes
- Trading window: 9:40-11:30 AM
- Sharpe: 0.99 (Q1 2024)

Test on full 2024 + 2025 for:
- QQQ (optimized config)
- IWM (same config to see if it works)
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

def orb_best_config(df):
    """Best config: 10min range, 0.30% target, 0.20% stop"""
    range_minutes = 10
    profit_target = 0.30
    stop_loss = 0.20
    max_hold_minutes = 60
    
    if len(df) < 50:
        return []
    
    df['time'] = pd.to_datetime(df['date'])
    df['hour'] = df['time'].dt.hour
    df['minute'] = df['time'].dt.minute
    
    open_idx = None
    for i in range(len(df)):
        if df.loc[i, 'hour'] == 9 and df.loc[i, 'minute'] >= 30:
            open_idx = i
            break
    
    if open_idx is None or open_idx + range_minutes >= len(df):
        return []
    
    range_end_idx = open_idx + range_minutes
    opening_high = df.loc[open_idx:range_end_idx, 'high'].max()
    opening_low = df.loc[open_idx:range_end_idx, 'low'].min()
    
    trades = []
    position = None
    
    for i in range(range_end_idx + 1, len(df)):
        if df.loc[i, 'hour'] >= 12 or (df.loc[i, 'hour'] == 11 and df.loc[i, 'minute'] >= 30):
            if position:
                pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
                if position['type'] == 'short':
                    pnl_pct = -pnl_pct
                pnl_pct -= FRICTION_BPS / 100
                trades.append({'pnl_pct': pnl_pct, 'win': pnl_pct > 0, 'date': position['date']})
                position = None
            break
        
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
            elif position['type'] == 'long' and df.loc[i, 'close'] < opening_high:
                exit_reason = 'return_to_range'
            elif position['type'] == 'short' and df.loc[i, 'close'] > opening_low:
                exit_reason = 'return_to_range'
            elif hold_min >= max_hold_minutes:
                exit_reason = 'timeout'
            
            if exit_reason:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({'pnl_pct': pnl_pct, 'win': pnl_pct > 0, 'date': position['date']})
                position = None
        
        if not position:
            if df.loc[i, 'close'] > opening_high:
                position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i, 'date': df.loc[i, 'date'][:10]}
            elif df.loc[i, 'close'] < opening_low:
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
print("OPENING RANGE BREAKOUT - FULL YEAR VALIDATION (QQQ & IWM)")
print("="*80)
print("\nConfig: 10min range, 0.30% target, 0.20% stop, 1.0 bps friction")

days_2024 = generate_trading_days('2024-01-02', '2024-12-31')
days_2025 = generate_trading_days('2025-01-02', '2025-12-31')

print(f"\n2024: {len(days_2024)} potential trading days")
print(f"2025: {len(days_2025)} potential trading days")

all_results = {}

for symbol in ['QQQ', 'IWM']:
    print(f"\n{'='*80}")
    print(f"TESTING {symbol}")
    print(f"{'='*80}")
    
    results_by_year = {}
    
    for year, days in [('2024', days_2024), ('2025', days_2025)]:
        print(f"\n{year}:")
        
        all_trades = []
        successful_days = 0
        
        for idx, date in enumerate(days):
            if idx % 50 == 0:
                print(f"  Progress: {idx}/{len(days)} days...", end='\r')
            
            bars = fetch_1min_data(symbol, date)
            if len(bars) < 50:
                continue
            
            successful_days += 1
            df = pd.DataFrame(bars).sort_values('date').reset_index(drop=True)
            trades = orb_best_config(df)
            all_trades.extend(trades)
        
        print(f"  Completed: {successful_days} days with data")
        
        if all_trades:
            pnls = [t['pnl_pct'] for t in all_trades]
            wins = [t for t in all_trades if t['win']]
            
            avg_pnl = np.mean(pnls)
            std_pnl = np.std(pnls)
            sharpe = (avg_pnl / std_pnl * np.sqrt(252 * len(all_trades) / successful_days)) if std_pnl > 0 else 0
            win_rate = len(wins) / len(all_trades) * 100
            trades_per_day = len(all_trades) / successful_days
            
            results_by_year[year] = {
                'trades': len(all_trades),
                'trades_per_day': trades_per_day,
                'win_rate': win_rate,
                'sharpe': sharpe,
                'total_return': sum(pnls)
            }
            
            print(f"  Trades: {len(all_trades)} ({trades_per_day:.1f}/day)")
            print(f"  Win Rate: {win_rate:.1f}%")
            print(f"  Sharpe: {sharpe:.2f}")
            print(f"  Return: {sum(pnls):.2f}%")
    
    all_results[symbol] = results_by_year

# Final summary
print(f"\n{'='*80}")
print("FINAL VERDICT")
print(f"{'='*80}")

for symbol in ['QQQ', 'IWM']:
    if symbol in all_results and '2024' in all_results[symbol] and '2025' in all_results[symbol]:
        r2024 = all_results[symbol]['2024']
        r2025 = all_results[symbol]['2025']
        avg_sharpe = (r2024['sharpe'] + r2025['sharpe']) / 2
        
        print(f"\n{symbol}:")
        print(f"  2024: Sharpe {r2024['sharpe']:.2f}, Return {r2024['total_return']:.2f}%")
        print(f"  2025: Sharpe {r2025['sharpe']:.2f}, Return {r2025['total_return']:.2f}%")
        print(f"  Avg Sharpe: {avg_sharpe:.2f}")
        
        if avg_sharpe > 1.0:
            print(f"  🎯 **VALIDATED!** Profitable and ready for deployment")
        elif avg_sharpe > 0.5:
            print(f"  ✅ **PROFITABLE** but marginal")
        else:
            print(f"  ❌ Failed full-year validation")

with open('orb_full_year_qqq_iwm_results.json', 'w') as f:
    json.dump(all_results, f, indent=2)

print(f"\n✅ Saved to orb_full_year_qqq_iwm_results.json")
