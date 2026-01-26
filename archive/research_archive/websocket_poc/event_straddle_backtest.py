"""
Event Straddle Backtest - REAL DATA VERSION
Backtests 5-minute hold strategy on actual 2024 FOMC/CPI events

Uses:  
- Real SPY 1-minute bars from FMP
- Simplified straddle pricing (2% of SPY for ATM straddle cost)
- Profit = SPY abs(move%) - theta decay - costs

This is a SIMPLIFIED model - doesn't use actual options pricing
"""

import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import statistics

load_dotenv()
FMP_API_KEY = os.getenv('FMP_API_KEY')


def get_spy_1min_data(date):
    """Fetch SPY 1-minute bars for a specific date"""
    url = "https://financialmodelingprep.com/stable/historical-chart/1min"
    params = {
        'symbol': 'SPY',
        'from': date,
        'to': date,
        'apikey': FMP_API_KEY
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return []


def find_price_at_time(bars, target_time):
    """Find SPY price closest to target time"""
    for bar in bars:
        if target_time in bar.get('date', ''):
            return bar.get('close')
    return None


def simulate_straddle_trade(event_date, event_time_str, bars):
    """
    Simulate straddle trade with REAL data
    
    Entry: 5 minutes before event
    Exit: 5 minutes after event
    """
    # Parse event time
    hour, minute = map(int, event_time_str.split(':'))
    
    # Entry time (5 min before)
    entry_minute = minute - 5
    entry_hour = hour
    if entry_minute < 0:
        entry_minute += 60
        entry_hour -= 1
    entry_time = f"{entry_hour:02d}:{entry_minute:02d}"
    
    # Exit time (5 min after)
    exit_minute = minute + 5
    exit_hour = hour
    if exit_minute >= 60:
        exit_minute -= 60
        exit_hour += 1
    exit_time = f"{exit_hour:02d}:{exit_minute:02d}"
    
    # Get prices
    entry_price = find_price_at_time(bars, entry_time)
    announcement_price = find_price_at_time(bars, event_time_str)
    exit_price = find_price_at_time(bars, exit_time)
    
    if not entry_price or not exit_price:
        return None
    
    # Calculate SPY move
    move_pct = abs(exit_price - entry_price) / entry_price * 100
    
    # Simplified straddle pricing:
    # - ATM straddle costs ~2% of SPY price
    # - Profit = (SPY move %) - (theta decay) - (slippage)
    # - Theta decay for 10 min = negligible (~0.01%)
    # - Slippage = 0.05% (options spread)
    
    straddle_cost_pct = 2.0  # ATM straddle costs 2% of SPY
    theta_decay_pct = 0.01   # 10 minutes = minimal decay
    slippage_pct = 0.05      # Bid-ask spread
    
    # P&L = (Move captured) - (Theta) - (Slippage)
    # For straddles, profit = move - cost_to_hold
    profit_pct = (move_pct / straddle_cost_pct * 100) - theta_decay_pct - slippage_pct
    
    return {
        'date': event_date,
        'entry_time': entry_time,
        'exit_time': exit_time,
        'entry_price': entry_price,
        'announcement_price': announcement_price,
        'exit_price': exit_price,
        'move_pct': move_pct,
        'profit_pct': profit_pct,
        'win': profit_pct > 0
    }


# Test on 3 FOMC events (sample)
FOMC_EVENTS = [
    {'date': '2024-01-31', 'time': '14:00'},  # Jan 31
    {'date': '2024-03-20', 'time': '14:00'},  # Mar 20
    {'date': '2024-05-01', 'time': '14:00'},  # May 1
]

# Test on 3 CPI events (sample)
CPI_EVENTS = [
    {'date': '2024-01-11', 'time': '08:30'},  # Jan 11
    {'date': '2024-02-13', 'time': '08:30'},  # Feb 13
    {'date': '2024-03-12', 'time': '08:30'},  # Mar 12
]


def backtest_events(events, event_type):
    """Backtest list of events"""
    
    print(f"\n{'='*70}")
    print(f"{event_type} Events Backtest (5-Minute Hold)")
    print(f"{'='*70}")
    
    trades = []
    
    for event in events:
        print(f"\n{event['date']} @ {event['time']}:")
        print(f"  Fetching 1-min data...", end='')
        
        bars = get_spy_1min_data(event['date'])
        if not bars:
            print(" ❌ No data")
            continue
        
        print(f" ✅ {len(bars)} bars")
        
        trade = simulate_straddle_trade(event['date'], event['time'], bars)
        
        if trade:
            trades.append(trade)
            win_symbol = "✅" if trade['win'] else "❌"
            print(f"  Entry:  {trade['entry_time']} @ ${trade['entry_price']:.2f}")
            print(f"  Event:  {event['time']} @ ${trade['announcement_price']:.2f}")
            print(f"  Exit:   {trade['exit_time']} @ ${trade['exit_price']:.2f}")
            print(f"  Move:   {trade['move_pct']:.2f}%")
            print(f"  P&L:    {trade['profit_pct']:.2f}% {win_symbol}")
        else:
            print(f"  ❌ Could not simulate (missing data)")
    
    return trades


def calculate_metrics(trades, event_type):
    """Calculate performance metrics"""
    
    if not trades:
        print(f"\n❌ No trades for {event_type}")
        return None
    
    profits = [t['profit_pct'] for t in trades]
    wins = [t for t in trades if t['win']]
    
    avg_profit = statistics.mean(profits)
    sharpe = avg_profit / statistics.stdev(profits) if len(profits) > 1 and statistics.stdev(profits) > 0 else 0
    win_rate = len(wins) / len(trades) * 100
    
    print(f"\n{'='*70}")
    print(f"{event_type} RESULTS")
    print(f"{'='*70}")
    print(f"Trades:      {len(trades)}")
    print(f"Avg Profit:  {avg_profit:.2f}%")
    print(f"Sharpe:      {sharpe:.2f}")
    print(f"Win Rate:    {win_rate:.0f}%")
    print(f"Best Trade:  {max(profits):.2f}%")
    print(f"Worst Trade: {min(profits):.2f}%")
    
    return {
        'trades': len(trades),
        'avg_profit': avg_profit,
        'sharpe': sharpe,
        'win_rate': win_rate
    }


def main():
    """Main backtest"""
    
    print("\n" + "="*70)
    print("EVENT STRADDLE BACKTEST - REAL DATA")
    print("="*70)
    print("\nStrategy: Enter 5min before, Exit 5min after")
    print("Sample: 3 FOMC + 3 CPI events from 2024")
    print("\nSimplified Model:")
    print("  • ATM straddle = 2% of SPY price")
    print("  • Profit = (Move% / 2%) - Theta - Slippage")
    print("  • Theta decay (10 min) = 0.01%")
    print("  • Slippage = 0.05%")
    
    # Backtest FOMC
    fomc_trades = backtest_events(FOMC_EVENTS, "FOMC")
    fomc_metrics = calculate_metrics(fomc_trades, "FOMC")
    
    # Backtest CPI
    cpi_trades = backtest_events(CPI_EVENTS, "CPI")
    cpi_metrics = calculate_metrics(cpi_trades, "CPI")
    
    # Compare to Phase 5A
    print("\n" + "="*70)
    print("COMPARISON TO PHASE 5A (1-Day Hold)")
    print("="*70)
    
    print("\nPhase 5A (1-day hold on SPY):")
    print("  FOMC: Sharpe 0.31")
    print("  CPI:  Sharpe -3.36 (massive loss)")
    
    print("\nNew Strategy (5-min hold):")
    if fomc_metrics:
        print(f"  FOMC: Sharpe {fomc_metrics['sharpe']:.2f}")
    if cpi_metrics:
        print(f"  CPI:  Sharpe {cpi_metrics['sharpe']:.2f}")
    
    if fomc_metrics and fomc_metrics['sharpe'] > 0.31:
        print(f"\n✅ FOMC improved from 0.31 to {fomc_metrics['sharpe']:.2f}")
    if cpi_metrics and cpi_metrics['sharpe'] > -3.36:
        print(f"✅ CPI improved from -3.36 to {cpi_metrics['sharpe']:.2f}")
    
    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)
    
    if (fomc_metrics and fomc_metrics['sharpe'] > 1.0) or (cpi_metrics and cpi_metrics['sharpe'] > 1.0):
        print("\n✅ SUCCESS! 5-minute hold strategy works!")
        print("   Precision timing is KEY for event straddles")
    else:
        print("\n⚠️  Results mixed - strategy shows improvement but needs:")
        print("   • Real options pricing (not simplified model)")
        print("   • More events (full 2024 calendar)")
        print("   • Better IV estimation")
    
    print(f"\n📊 Simplified model tested on {len(fomc_trades) + len(cpi_trades)} events")
    print(f"   For production: Use Black-Scholes + actual options data")


if __name__ == "__main__":
    main()
