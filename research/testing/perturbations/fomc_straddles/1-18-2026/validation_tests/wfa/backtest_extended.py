"""
FOMC Event Straddles - Extended WFA Backtest (2020-2024)

Tests the FOMC Event Straddles strategy across multiple market regimes:
- 2020: COVID Crash & Recovery (High Volatility)
- 2021: Bull Market / Meme Mania (High/Mixed Volatility)
- 2022: Bear Market / Fed Tightening (High Volatility)
- 2023: AI Boom / Recovery (Mixed Volatility)
- 2024: Bull Market (Low Volatility)

Objective:
Determine if the strategy's edge is robust across regimes or if the 2024 "100% win rate" was a low-volatility anomaly.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import os

# Add project root to path
script_path = Path(__file__).resolve()
# Navigate up: backtest_extended.py -> wfa -> tests -> fomc_event_straddles -> strategies -> operations -> docs -> Magellan
project_root = script_path.parents[6]
sys.path.insert(0, str(project_root))

# Change to project root directory for .env loading
os.chdir(project_root)

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient

print("="*80)
print("FOMC EVENT STRADDLES - EXTENDED WFA (2020-2024)")
print("="*80)

# FOMC Events Config (Date of Announcement)
# Time is standard 14:00 ET unless noted
FOMC_EVENTS = [
    # 2020 (COVID)
    {'date': '2020-01-29', 'time': '14:00'},
    {'date': '2020-04-29', 'time': '14:00'},
    {'date': '2020-06-10', 'time': '14:00'},
    {'date': '2020-07-29', 'time': '14:00'},
    {'date': '2020-09-16', 'time': '14:00'},
    {'date': '2020-11-05', 'time': '14:00'},
    {'date': '2020-12-16', 'time': '14:00'},
    
    # 2021 (Inflation starts)
    {'date': '2021-01-27', 'time': '14:00'},
    {'date': '2021-03-17', 'time': '14:00'},
    {'date': '2021-04-28', 'time': '14:00'},
    {'date': '2021-06-16', 'time': '14:00'},
    {'date': '2021-07-28', 'time': '14:00'},
    {'date': '2021-09-22', 'time': '14:00'},
    {'date': '2021-11-03', 'time': '14:00'},
    {'date': '2021-12-15', 'time': '14:00'},

    # 2022 (Aggressive Hiking)
    {'date': '2022-01-26', 'time': '14:00'},
    {'date': '2022-03-16', 'time': '14:00'},
    {'date': '2022-05-04', 'time': '14:00'},
    {'date': '2022-06-15', 'time': '14:00'},
    {'date': '2022-07-27', 'time': '14:00'},
    {'date': '2022-09-21', 'time': '14:00'},
    {'date': '2022-11-02', 'time': '14:00'},
    {'date': '2022-12-14', 'time': '14:00'},

    # 2023 (Peak Rates)
    {'date': '2023-02-01', 'time': '14:00'},
    {'date': '2023-03-22', 'time': '14:00'},
    {'date': '2023-05-03', 'time': '14:00'},
    {'date': '2023-06-14', 'time': '14:00'},
    {'date': '2023-07-26', 'time': '14:00'},
    {'date': '2023-09-20', 'time': '14:00'},
    {'date': '2023-11-01', 'time': '14:00'},
    {'date': '2023-12-13', 'time': '14:00'},

    # 2024 (Pivot Anticipation)
    {'date': '2024-01-31', 'time': '14:00'},
    {'date': '2024-03-20', 'time': '14:00'},
    {'date': '2024-05-01', 'time': '14:00'},
    {'date': '2024-06-12', 'time': '14:00'},
    {'date': '2024-07-31', 'time': '14:00'},
    {'date': '2024-09-18', 'time': '14:00'},
    {'date': '2024-11-07', 'time': '14:00'},
    {'date': '2024-12-18', 'time': '14:00'},
]

print(f"Testing {len(FOMC_EVENTS)} FOMC events from 2020-2024\n")

# Parameters
INITIAL_CAPITAL = 10000
STRADDLE_COST_PCT = 2.0  # Assumed cost of ATM straddle
THETA_DECAY_PCT = 0.01
SLIPPAGE_PCT = 0.05

# Setup Data Client
alpaca = AlpacaDataClient()

# Helper to categorize year
def get_regime(year):
    if year == 2020: return "COVID/Volatile"
    if year == 2022: return "Bear/Hiking"
    if year == 2024: return "Bull/Stable"
    return "Mixed"

all_trades = []

# Fetch Data in Chunks (Yearly) to manage memory/request limits
years = [2020, 2021, 2022, 2023, 2024]
price_cache = {}

for year in years:
    print(f"Fetching data for {year}...")
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    # Fetch 1Min bars
    df = alpaca.fetch_historical_bars('SPY', '1Min', start_date, end_date, feed='sip')
    if df is not None and not df.empty:
        price_cache[year] = df
        print(f"  ✓ Fetched {len(df)} bars")
    else:
        print(f"  ❌ Failed to fetch data for {year}")

print("\nSimulating Trades...\n")

for event in FOMC_EVENTS:
    event_date = pd.to_datetime(event['date'])
    year = event_date.year
    
    if year not in price_cache:
        print(f"Skipping {event_date.date()} (No Data)")
        continue
        
    price_df = price_cache[year]
    
    # Entry: 13:55, Exit: 14:05
    entry_dt = event_date.replace(hour=13, minute=55)
    exit_dt = event_date.replace(hour=14, minute=5)
    
    # Locate bars
    entry_bars = price_df[price_df.index <= entry_dt]
    if len(entry_bars) == 0:
        continue
    entry_price = entry_bars.iloc[-1]['close']
    
    exit_bars = price_df[price_df.index >= exit_dt]
    if len(exit_bars) == 0:
        continue
    exit_price = exit_bars.iloc[0]['close']
    
    # Calculate Logic
    spy_move_pct = abs((exit_price - entry_price) / entry_price) * 100
    profit_pct = (spy_move_pct / STRADDLE_COST_PCT * 100) - THETA_DECAY_PCT - SLIPPAGE_PCT
    dollar_pnl = INITIAL_CAPITAL * (profit_pct / 100)
    
    trade = {
        'date': event_date.date(),
        'year': year,
        'regime': get_regime(year),
        'entry_price': entry_price,
        'exit_price': exit_price,
        'spy_move_pct': spy_move_pct,
        'pnl_pct': profit_pct,
        'pnl_dollars': dollar_pnl,
        'win': profit_pct > 0
    }
    all_trades.append(trade)
    
    icon = "✅" if trade['win'] else "❌"
    print(f"{event_date.date()} | Move: {spy_move_pct:.2f}% | P&L: {profit_pct:+.2f}% {icon}")

# Analysis
trades_df = pd.DataFrame(all_trades)
if trades_df.empty:
    print("No trades generated.")
    sys.exit()

print("\n" + "="*80)
print("WFA RESULTS SUMMARY")
print("="*80)

print(f"Total Trades: {len(trades_df)}")
global_win_rate = trades_df['win'].mean() * 100
global_sharpe = 0
if trades_df['pnl_pct'].std() > 0:
    global_sharpe = trades_df['pnl_pct'].mean() / trades_df['pnl_pct'].std() * np.sqrt(8) # approx 8 events/yr

print(f"Global Win Rate: {global_win_rate:.1f}%")
print(f"Global Sharpe (Annualized est): {global_sharpe:.2f}")

print("\nBy Year:")
for year in years:
    ydf = trades_df[trades_df['year'] == year]
    if ydf.empty: continue
    wr = ydf['win'].mean() * 100
    avg_ret = ydf['pnl_pct'].mean()
    print(f"  {year}: WR {wr:.1f}% | Avg P&L {avg_ret:+.2f}% | Trades: {len(ydf)}")

# Save
output_path = Path(__file__).parent / 'wfa_results.csv'
trades_df.to_csv(output_path, index=False)
print(f"\nSaved detailed results to {output_path}")
