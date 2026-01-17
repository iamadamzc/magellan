"""
FOMC Event Straddles - Futures Validation Test

Tests FOMC-driven volatility breakout strategy on index futures (2024).

Strategy:
- Entry: At 2:00 PM ET (FOMC announcement)
- Position: Go LONG if futures spike >0.1% in first 2 minutes after announcement
- Exit: 10 minutes after entry (2:10 PM ET)
- Target: Capture FOMC volatility continuation

Expected Output:
- fomc_futures_results.csv with event-by-event results
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
script_path = Path(__file__).resolve()
project_root = script_path.parents[6]  # Magellan folder
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

print("="*80)
print("FOMC EVENT STRADDLES - FUTURES VALIDATION TEST")
print("="*80)
print("Testing FOMC-driven breakout strategy on Index Futures")
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

# Test on index futures only (most FOMC-sensitive)
FUTURES_UNIVERSE = {
    'MES': {'name': 'Micro E-mini S&P 500', 'proxy': 'SPY'},
    'MNQ': {'name': 'Micro E-mini Nasdaq 100', 'proxy': 'QQQ'},
}

INITIAL_CAPITAL = 10000
BREAKOUT_THRESHOLD_PCT = 0.1  # 0.1% move to trigger entry
HOLD_MINUTES = 10
TRANSACTION_COST_BPS = 3.0  # Lower for index futures (tight spreads)

print(f"\n[1/3] Testing {len(FUTURES_UNIVERSE)} futures on {len(FOMC_EVENTS_2024)} FOMC events...\n")

client = AlpacaDataClient()
all_results = []

for symbol, config in FUTURES_UNIVERSE.items():
    print(f"Testing {symbol} ({config['name']}) via {config['proxy']}...")
    print(f"{'='*70}")
    
    event_results = []
    
    for event in FOMC_EVENTS_2024:
        event_date = pd.to_datetime(event['date'])
        event_desc = event['description']
        
        try:
            # Fetch 1-minute data for the FOMC day
            # Need data from 1:50 PM to 2:15 PM ET (25-minute window)
            start_time = event_date.replace(hour=13, minute=50)  # 1:50 PM
            end_time = event_date.replace(hour=14,minute=20)  # 2:20 PM
            
            # Fetch minute data
            df = client.fetch_historical_bars(
                symbol=config['proxy'],
                timeframe=TimeFrame.Minute,
                start=event_date.strftime('%Y-%m-%d'),
                end=(event_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                feed='sip'
            )
            
            if len(df) == 0:
                print(f"  ❌ {event_desc}: No data")
                continue
            
            # Filter to FOMC window (1:50 PM - 2:20 PM)
            df_window = df.between_time('13:50', '14:20')
            
            if len(df_window) < 10:
                print(f"  ❌ {event_desc}: Insufficient intraday data ({len(df_window)} bars)")
                continue
            
            # Get announcement time price (2:00 PM)
            announcement_bars = df_window[df_window.index.hour == 14]
            announcement_bars = announcement_bars[announcement_bars.index.minute == 0]
            
            if len(announcement_bars) == 0:
                print(f"  ⚠️  {event_desc}: No 2:00 PM bar, using closest")
                announcement_price = df_window.iloc[len(df_window)//2]['close']  # Approximate
            else:
                announcement_price = announcement_bars.iloc[0]['close']
            
            # Check for breakout in next 2 minutes (2:00-2:02 PM)
            post_announcement = df_window[df_window.index >= event_date.replace(hour=14, minute=0)]
            post_announcement = post_announcement[post_announcement.index <= event_date.replace(hour=14, minute=2)]
            
            if len(post_announcement) < 2:
                print(f"  ❌ {event_desc}: No post-announcement data")
                continue
            
            # Calculate 2-minute move
            two_min_price = post_announcement.iloc[-1]['close']
            two_min_move_pct = ((two_min_price - announcement_price) / announcement_price) * 100
            
            # BREAKOUT LOGIC: Enter LONG if move > 0.1%
            if abs(two_min_move_pct) > BREAKOUT_THRESHOLD_PCT:
                # Enter at 2:02 PM
                entry_price = two_min_price
                entry_direction = 'LONG' if two_min_move_pct > 0 else 'SKIP'  # Only long on upward breakouts
                
                if entry_direction == 'SKIP':
                    print(f"  ⚠️  {event_desc}: Downward breakout, skipped")
                    continue
                
                # Exit at 2:10 PM (8 minutes later)
                exit_bars = df_window[df_window.index >= event_date.replace(hour=14, minute=10)]
                
                if len(exit_bars) == 0:
                    print(f"  ❌ {event_desc}: No exit data")
                    continue
                
                exit_price = exit_bars.iloc[0]['close']
                
                # Calculate P&L
                cost = TRANSACTION_COST_BPS / 10000
                proceeds = (exit_price - entry_price) / entry_price  # % change
                pnl_pct = (proceeds * 100) - (cost * 10000)  # Account for friction
                
                move_pct = ((exit_price - announcement_price) / announcement_price) * 100
                
                result = {
                    'event_date': event_date.date(),
                    'description': event_desc,
                    'announcement_price': round(announcement_price, 2),
                    'two_min_price': round(two_min_price, 2),
                    'two_min_move_pct': round(two_min_move_pct, 2),
                    'entry_price': round(entry_price, 2),
                    'exit_price': round(exit_price, 2),
                    'move_pct': round(move_pct, 2),
                    'pnl_pct': round(pnl_pct, 2),
                    'win': pnl_pct > 0
                }
                
                event_results.append(result)
                
                win_symbol = "✅" if result['win'] else "❌"
                print(f"  {win_symbol} {event_desc}: Move {move_pct:+.2f}% | P&L {pnl_pct:+.2f}%")
                
            else:
                print(f"  ⚠️  {event_desc}: No breakout (move {two_min_move_pct:+.2f}%)")
                
        except Exception as e:
            print(f"  ❌ {event_desc}: Error - {str(e)[:50]}")
    
    # Analyze results for this contract
    if len(event_results) > 0:
        results_df = pd.DataFrame(event_results)
        win_rate = (results_df['pnl_pct'] > 0).mean() * 100
        avg_pnl = results_df['pnl_pct'].mean()
        total_return = results_df['pnl_pct'].sum()
        
        # Sharpe (annualized for 8 events/year)
        if results_df['pnl_pct'].std() > 0:
            sharpe = (avg_pnl / results_df['pnl_pct'].std()) * np.sqrt(len(event_results))
        else:
            sharpe = 0
        
        summary = {
            'symbol': symbol,
            'name': config['name'],
            'events_traded': len(event_results),
            'win_rate': round(win_rate, 1),
            'avg_pnl_pct': round(avg_pnl, 2),
            'total_return': round(total_return, 2),
            'sharpe': round(sharpe, 2),
            'best_event': results_df.loc[results_df['pnl_pct'].idxmax(), 'description'],
            'best_pnl': round(results_df['pnl_pct'].max(), 2)
        }
        
        all_results.append(summary)
        
        print(f"\n{symbol} Summary:")
        print(f"  Events Traded: {len(event_results)}/8")
        print(f"  Win Rate: {win_rate:.0f}%")
        print(f"  Avg P&L: {avg_pnl:+.2f}%")
        print(f"  Total Return: {total_return:+.2f}%")
        print(f"  Sharpe: {sharpe:.2f}")
        print()
    else:
        print(f"\n{symbol}: No tradeable events (no breakouts detected)\n")

print("="*80)
print("FOMC FUTURES VALIDATION RESULTS")
print("="*80)

if len(all_results) > 0:
    summary_df = pd.DataFrame(all_results)
    
    print("\n📊 Summary by Contract:")
    print(summary_df[['symbol', 'name', 'events_traded', 'win_rate', 'avg_pnl_pct', 'sharpe']].to_string(index=False))
    
    # Save results
    output_file = Path(__file__).parent / 'fomc_futures_results.csv'
    summary_df.to_csv(output_file, index=False)
    print(f"\n📁 Results saved to: {output_file}")
    
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80)
    
    approved = summary_df[summary_df['win_rate'] >= 70]
    
    if len(approved) > 0:
        print(f"\n✅ APPROVED ({len(approved)} contracts with ≥70% win rate):")
        for _, row in approved.iterrows():
            print(f"   {row['symbol']} - {row['win_rate']:.0f}% win rate, {row['avg_pnl_pct']:+.2f}% avg P&L")
    else:
        print("\n❌ NO CONTRACTS APPROVED (Win Rate < 70%)")
        print("   FOMC Event Straddles strategy does not translate well to futures breakout method.")
        print("   Original strategy (options straddle) remains superior for FOMC events.")
else:
    print("\n❌ NO RESULTS - No breakouts detected on any FOMC events")

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)
print("1. Review FOMC_FUTURES_VALIDATION_REPORT.md for detailed analysis")
print("2. If approved, create asset configs")
print("3. Compare to SPY options straddle method (original)")
print("="*80)
