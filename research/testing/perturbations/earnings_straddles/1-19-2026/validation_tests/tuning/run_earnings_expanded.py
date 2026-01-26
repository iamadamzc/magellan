"""
Earnings Straddles - Expanded WFA + Regime Filter (WITH CORRECT FMP ENDPOINT)
Tests the strategy across an expanded universe with a Bear Market Filter (SPY 200MA).

Objective: 
1. Validate if filter saves performance in 2022.
2. Identify new candidates (META, NFLX, PLTR, COIN).
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import requests
import os

project_root = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from src.options.features import OptionsFeatureEngineer

print("="*80)
print("EARNINGS STRADDLES - EXPANDED UNIVERSE & REGIME FILTER")
print("="*80)
print("Filter: Pause if SPY < 200-Day MA")
print("Universe: GOOGL, NVDA, TSLA, AAPL, AMD, META, NFLX, PLTR, COIN")
print("Period: 2020-2025")
print("="*80)

# -------------------------------------------------------------------------
# 1. EARNINGS DATES
# -------------------------------------------------------------------------

FMP_API_KEY = os.getenv('FMP_API_KEY')

def fetch_earnings_dates(symbol):
    """Fetch earnings dates from FMP (CORRECT STABLE ENDPOINT)"""
    # Endpoint: https://financialmodelingprep.com/stable/earnings?symbol=AAPL
    url = f"https://financialmodelingprep.com/stable/earnings"
    params = {'apikey': FMP_API_KEY, 'symbol': symbol} 
    
    try:
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        if isinstance(data, list):
            # Keys: date, symbol, eps, epsEstimated, time, revenue, revenueEstimated
            dates = [d['date'] for d in data]
            return sorted(pd.to_datetime(dates)) # Ascending
    except Exception as e:
        print(f"  ❌ FMP Calendar Error for {symbol}: {e}")
    return []

# -------------------------------------------------------------------------
# 2. DATA HANDLER
# -------------------------------------------------------------------------

alpaca = AlpacaDataClient()

def get_spy_ma200():
    print("Fetching SPY 200-Day MA Data...")
    spy = alpaca.fetch_historical_bars('SPY', '1Day', '2019-01-01', '2025-12-31', feed='sip')
    spy['ma200'] = spy['close'].rolling(200).mean()
    return spy[['close', 'ma200']]

spy_data = get_spy_ma200()

def check_regime(date):
    """Return True if Bull (Price > MA200), False if Bear"""
    try:
        # Get last available SPY data on or before date
        idx = spy_data.index.asof(date)
        if pd.isna(idx): return True
        row = spy_data.loc[idx]
        return row['close'] > row['ma200']
    except:
        return True

# -------------------------------------------------------------------------
# 3. BACKTEST ENGINE
# -------------------------------------------------------------------------

def run_backtest(symbol):
    print(f"\nProcessing {symbol}...")
    
    # 1. Earnings Dates
    dates = fetch_earnings_dates(symbol)
    dates = [d for d in dates if '2020-01-01' <= d.strftime('%Y-%m-%d') <= '2025-12-31']
    if not dates:
        print(f"  ❌ No earnings dates found")
        return None
        
    print(f"  Found {len(dates)} earnings events")
    
    # 2. Price Data
    try:
        bars = alpaca.fetch_historical_bars(symbol, '1Day', '2020-01-01', '2025-12-31', feed='sip')
        if bars is None or len(bars) < 100:
            print("  ❌ No price data")
            return None
    except:
        print("  ❌ Data fetch error")
        return None
        
    trades = []
    skipped_bear = 0
    
    for earnings_date in dates:
        entry_date = earnings_date - timedelta(days=2) # T-2
        exit_date = earnings_date + timedelta(days=1)  # T+1
        
        # Check Regime at Entry
        is_bull = check_regime(entry_date)
        if not is_bull:
            skipped_bear += 1
            continue
            
        # Get Prices
        try:
            # Find closest valid dates if exact match missing
            # Entry: last bar ON or BEFORE entry_date
            if entry_date not in bars.index:
                idx_entry = bars.index.asof(entry_date)
                if pd.isna(idx_entry): continue
            else:
                idx_entry = entry_date
                
            entry_price = bars.loc[idx_entry]['close']
            
            # Exit: first bar ON or AFTER exit_date
            # asof goes backward, searchsorted goes forward?
            # Easiest: Slice
            future_bars = bars[bars.index >= exit_date]
            if future_bars.empty: continue
            
            idx_exit = future_bars.index[0]
            exit_price = future_bars.iloc[0]['close']
            
            # Simplified Options Model (Straddle)
            # Assumption: Straddle cost is roughly 4% of spot (valid for high IV events)
            straddle_cost = entry_price * 0.04 
            
            # Payoff
            gross_payoff = abs(exit_price - entry_price)
            
            # Net
            # Assuming 1 contract for simple % calculation
            # PnL = Payoff - Cost
            pnl_val = gross_payoff - straddle_cost
            pnl_pct = (pnl_val / straddle_cost) * 100
            
            trades.append({
                'date': earnings_date,
                'entry': entry_price,
                'exit': exit_price,
                'pnl_pct': pnl_pct,
                'abs_move_pct': abs(exit_price - entry_price) / entry_price * 100
            })
            
        except Exception as e:
            continue
            
    if not trades:
        return None
        
    df = pd.DataFrame(trades)
    
    # Metrics
    win_rate = (df['pnl_pct'] > 0).mean() * 100
    avg_return = df['pnl_pct'].mean()
    sharpe = (df['pnl_pct'].mean() / df['pnl_pct'].std()) * np.sqrt(4) if len(df) > 1 else 0
    
    return {
        'symbol': symbol,
        'trades': len(trades),
        'skipped': skipped_bear,
        'win_rate': win_rate,
        'avg_return': avg_return,
        'sharpe': sharpe,
        'recent_perf': df.tail(4)['pnl_pct'].mean() # Last 4 trades (2025?)
    }

# -------------------------------------------------------------------------
# 4. EXECUTION LOOP
# -------------------------------------------------------------------------

UNIVERSE = ['GOOGL', 'NVDA', 'TSLA', 'AAPL', 'AMD', 'META', 'NFLX', 'PLTR', 'COIN']

results = []
print("\n" + "-"*80)
print(f"{'SYMBOL':<8} {'TRADES':<8} {'SKIPPED':<8} {'WIN RATE':<10} {'AVG RET':<10} {'SHARPE':<8} {'RECENT':<8}")
print("-"*(80))

for sym in UNIVERSE:
    # Need to wait 1s between FMP calls sometimes?
    res = run_backtest(sym)
    if res:
        results.append(res)
        status = "✅" if res['sharpe'] > 1.0 else "❌"
        print(f"{res['symbol']:<8} {res['trades']:<8} {res['skipped']:<8} {res['win_rate']:<9.1f}% {res['avg_return']:<9.1f}% {res['sharpe']:<8.2f} {res['recent_perf']:<8.1f}% {status}")

print("-"*(80))
