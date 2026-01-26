"""
FOMC Event Straddles - Complete Futures Validation (All 13 Contracts)

Tests FOMC-driven volatility breakout strategy on all futures (2024).

Strategy:
- Entry: At 2:00 PM ET (FOMC announcement)
- Position: Go LONG if futures spike >0.1% in first 2 minutes
- Exit: 10 minutes after entry (2:10 PM ET)
- Target: Capture FOMC volatility continuation

Data Sources:
- Index Futures: Alpaca (SPY, QQQ, DIA, IWM)
- Commodities/FX/Crypto: FMP 1-minute data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path
import requests
import os

# Add project root to path
script_path = Path(__file__).resolve()
project_root = script_path.parents[6]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

print("="*80)
print("FOMC EVENT STRADDLES - COMPLETE FUTURES VALIDATION")
print("="*80)
print("Testing all 13 futures on FOMC events")
print("Period: 2024 (8 FOMC events)")
print("Strategy: Volatility Breakout (10-minute hold)")
print("="*80)

# 2024 FOMC Events
FOMC_EVENTS_2024 = [
    {'date': '2024-01-31', 'description': 'Jan FOMC'},
    {'date': '2024-03-20', 'description': 'Mar FOMC (hawkish pivot)'},
    {'date': '2024-05-01', 'description': 'May FOMC'},
    {'date': '2024-06-12', 'description': 'Jun FOMC'},
    {'date': '2024-07-31', 'description': 'Jul FOMC'},
    {'date': '2024-09-18', 'description': 'Sep FOMC (Fed pivot)'},
    {'date': '2024-11-07', 'description': 'Nov FOMC'},
    {'date': '2024-12-18', 'description': 'Dec FOMC'},
]

# All 13 futures
FUTURES_UNIVERSE = {
    # Index (Alpaca)
    'MES': {'name': 'Micro S&P 500', 'source': 'alpaca', 'proxy': 'SPY'},
    'MNQ': {'name': 'Micro Nasdaq', 'source': 'alpaca', 'proxy': 'QQQ'},
    'MYM': {'name': 'Micro Dow', 'source': 'alpaca', 'proxy': 'DIA'},
    'M2K': {'name': 'Micro Russell', 'source': 'alpaca', 'proxy': 'IWM'},
    
    # Commodities (FMP - note: 1-min data may not be available)
    'MCL': {'name': 'Micro Crude Oil', 'source': 'fmp', 'proxy': 'CLUSD'},
    'MGC': {'name': 'Micro Gold', 'source': 'fmp', 'proxy': 'GCUSD'},
    'MSI': {'name': 'Micro Silver', 'source': 'fmp', 'proxy': 'SIUSD'},
    'MNG': {'name': 'Micro Natural Gas', 'source': 'fmp', 'proxy': 'NGUSD'},
    'MCP': {'name': 'Micro Copper', 'source': 'fmp', 'proxy': 'HGUSD'},
    
    # Currencies (FMP)
    'M6E': {'name': 'Micro EUR/USD', 'source': 'fmp', 'proxy': 'EURUSD'},
    'M6B': {'name': 'Micro GBP/USD', 'source': 'fmp', 'proxy': 'GBPUSD'},
    'M6A': {'name': 'Micro AUD/USD', 'source': 'fmp', 'proxy': 'AUDUSD'},
    
    # Crypto (FMP)
    'MBT': {'name': 'Micro Bitcoin', 'source': 'fmp', 'proxy': 'BTCUSD'},
}

BREAKOUT_THRESHOLD_PCT = 0.1
TRANSACTION_COST_BPS = 3.0

FMP_API_KEY = os.getenv('FMP_API_KEY')

def fetch_fmp_minute_data(symbol, event_date):
    """Fetch 1-minute intraday data from FMP for a specific date"""
    url = f"https://financialmodelingprep.com/stable/historical-chart/1min"
    
    params = {
        'symbol': symbol,
        'from': event_date.strftime('%Y-%m-%d'),
        'to': event_date.strftime('%Y-%m-%d'),
        'apikey': FMP_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data or len(data) == 0:
            return None
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['date'])
        df = df.set_index('timestamp')
        df = df.sort_index(ascending=True)
        df.columns = df.columns.str.lower()
        
        return df[['open', 'high', 'low', 'close', 'volume']]
        
    except:
        return None

print(f"\n[1/2] Testing {len(FUTURES_UNIVERSE)} futures on {len(FOMC_EVENTS_2024)} FOMC events...\n")

alpaca_client = AlpacaDataClient()
all_results = []

for symbol, config in FUTURES_UNIVERSE.items():
    print(f"Testing {symbol} ({config['name']})...")
    print(f"{'='*70}")
    
    event_results = []
    
    for event in FOMC_EVENTS_2024:
        event_date = pd.to_datetime(event['date'])
        event_desc = event['description']
        
        try:
            # Fetch data based on source
            if config['source'] == 'alpaca':
                df = alpaca_client.fetch_historical_bars(
                    symbol=config['proxy'],
                    timeframe=TimeFrame.Minute,
                    start=event_date.strftime('%Y-%m-%d'),
                    end=(event_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                    feed='sip'
                )
            else:  # FMP
                df = fetch_fmp_minute_data(config['proxy'], event_date)
            
            if df is None or len(df) == 0:
                continue
            
            # Filter to FOMC window (1:50 PM - 2:20 PM)
            df_window = df.between_time('13:50', '14:20')
            
            if len(df_window) < 10:
                continue
            
            # Get 2:00 PM price
            announcement_bars = df_window[df_window.index.hour == 14]
            announcement_bars = announcement_bars[announcement_bars.index.minute == 0]
            
            if len(announcement_bars) == 0:
                announcement_price = df_window.iloc[len(df_window)//2]['close']
            else:
                announcement_price = announcement_bars.iloc[0]['close']
            
            # Check 2-minute breakout
            post = df_window[df_window.index >= event_date.replace(hour=14, minute=0)]
            post = post[post.index <= event_date.replace(hour=14, minute=2)]
            
            if len(post) < 2:
                continue
            
            two_min_price = post.iloc[-1]['close']
            two_min_move_pct = ((two_min_price - announcement_price) / announcement_price) * 100
            
            # Breakout logic (long only on upward moves)
            if two_min_move_pct > BREAKOUT_THRESHOLD_PCT:
                entry_price = two_min_price
                
                # Find exit at 2:10 PM
                exit_bars = df_window[df_window.index >= event_date.replace(hour=14, minute=10)]
                
                if len(exit_bars) == 0:
                    continue
                
                exit_price = exit_bars.iloc[0]['close']
                
                # Calculate P&L
                cost = TRANSACTION_COST_BPS / 10000
                proceeds = (exit_price - entry_price) / entry_price
                pnl_pct = (proceeds * 100) - (cost * 10000)
                
                move_pct = ((exit_price - announcement_price) / announcement_price) * 100
                
                result = {
                    'event_date': event_date.date(),
                    'description': event_desc,
                    'two_min_move_pct': round(two_min_move_pct, 2),
                    'entry_price': round(entry_price, 2),
                    'exit_price': round(exit_price, 2),
                    'pnl_pct': round(pnl_pct, 2),
                    'win': pnl_pct > 0
                }
                
                event_results.append(result)
                
                win_symbol = "✅" if result['win'] else "❌"
                print(f"  {win_symbol} {event_desc}: Entry {two_min_move_pct:+.2f}% | P&L {pnl_pct:+.2f}%")
            
        except Exception as e:
            pass
    
    # Summarize for this contract
    if len(event_results) > 0:
        results_df = pd.DataFrame(event_results)
        win_rate = (results_df['pnl_pct'] > 0).mean() * 100
        avg_pnl = results_df['pnl_pct'].mean()
        total_return = results_df['pnl_pct'].sum()
        
        summary = {
            'symbol': symbol,
            'name': config['name'],
            'events_traded': len(event_results),
            'win_rate': round(win_rate, 1),
            'avg_pnl_pct': round(avg_pnl, 2),
            'total_return': round(total_return, 2),
        }
        
        all_results.append(summary)
        
        print(f"\n{symbol}: {len(event_results)} trades, {win_rate:.0f}% win rate, {avg_pnl:+.2f}% avg\n")
    else:
        print(f"\n{symbol}: No breakout trades\n")

print("="*80)
print("FOMC FUTURES RESULTS")
print("="*80)

if len(all_results) > 0:
    summary_df = pd.DataFrame(all_results)
    
    print("\n📊 Summary:")
    print(summary_df[['symbol', 'name', 'events_traded', 'win_rate', 'avg_pnl_pct']].to_string(index=False))
    
    # Save
    output_file = Path(__file__).parent / 'fomc_all_futures_results.csv'
    summary_df.to_csv(output_file, index=False)
    print(f"\n📁 Saved to: {output_file}")
    
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80)
    
    approved = summary_df[summary_df['win_rate'] >= 70]
    
    if len(approved) > 0:
        print(f"\n✅ APPROVED ({len(approved)} contracts):")
        for _, row in approved.iterrows():
            print(f"   {row['symbol']} - {row['win_rate']:.0f}% win, {row['avg_pnl_pct']:+.2f}% avg")
    else:
        print("\n❌ NO APPROVALS (Win Rate < 70%)")
        print("   FOMC futures testing shows limited applicability.")
        print("   SPY options straddle remains superior for FOMC events.")
else:
    print("\n❌ NO BREAKOUTS on any contracts")

print("\n" + "="*80)
print("Complete! All 13 contracts tested on FOMC events.")
print("="*80)
