"""
Deep Trade-by-Trade Analysis
Analyzes patterns in winning vs losing trades to identify refinement opportunities.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

OUTPUT_DIR = r"a:\1\Magellan\test\spy_node"

print("=" * 80)
print("DEEP TRADE-BY-TRADE ANALYSIS")
print("=" * 80)

# Load the LONG-only trade data (best performing configuration)
trades = pd.read_csv(os.path.join(OUTPUT_DIR, "long_only_trades.csv"))
trades['entry_time'] = pd.to_datetime(trades['entry_time'])
trades['exit_time'] = pd.to_datetime(trades['exit_time'])

# Add derived columns
trades['entry_hour'] = trades['entry_time'].dt.hour
trades['entry_minute'] = trades['entry_time'].dt.minute
trades['entry_dow'] = trades['entry_time'].dt.dayofweek  # 0=Monday
trades['entry_date'] = trades['entry_time'].dt.date

# ============================================================================
# ANALYSIS 1: TIME OF DAY
# ============================================================================
print("\n" + "=" * 80)
print("ANALYSIS 1: TIME OF DAY PERFORMANCE")
print("=" * 80)

for symbol in ['SPY', 'QQQ']:
    sym_df = trades[trades['symbol'] == symbol]
    
    print(f"\n{symbol}:")
    print("-" * 50)
    
    # Group by hour
    hourly = sym_df.groupby('entry_hour').agg({
        'correct': 'mean',
        'pnl_dollars': ['sum', 'mean', 'count']
    }).round(4)
    hourly.columns = ['hit_rate', 'total_pnl', 'avg_pnl', 'trades']
    hourly['hit_rate'] = (hourly['hit_rate'] * 100).round(1)
    
    print("\nBy Hour:")
    print(hourly.to_string())
    
    # Best and worst hours
    best_hour = hourly['total_pnl'].idxmax()
    worst_hour = hourly['total_pnl'].idxmin()
    print(f"\nBest hour: {best_hour}:00 (P&L: ${hourly.loc[best_hour, 'total_pnl']:,.2f})")
    print(f"Worst hour: {worst_hour}:00 (P&L: ${hourly.loc[worst_hour, 'total_pnl']:,.2f})")

# ============================================================================
# ANALYSIS 2: DAY OF WEEK
# ============================================================================
print("\n" + "=" * 80)
print("ANALYSIS 2: DAY OF WEEK PERFORMANCE")
print("=" * 80)

dow_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

for symbol in ['SPY', 'QQQ']:
    sym_df = trades[trades['symbol'] == symbol]
    
    print(f"\n{symbol}:")
    print("-" * 50)
    
    daily = sym_df.groupby('entry_dow').agg({
        'correct': 'mean',
        'pnl_dollars': ['sum', 'mean', 'count']
    }).round(4)
    daily.columns = ['hit_rate', 'total_pnl', 'avg_pnl', 'trades']
    daily['hit_rate'] = (daily['hit_rate'] * 100).round(1)
    dow_map = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
    daily.index = [dow_map.get(i, f'Day{i}') for i in daily.index]
    
    print(daily.to_string())
    
    best_day = daily['total_pnl'].idxmax()
    worst_day = daily['total_pnl'].idxmin()
    print(f"\nBest day: {best_day} (P&L: ${daily.loc[best_day, 'total_pnl']:,.2f})")
    print(f"Worst day: {worst_day} (P&L: ${daily.loc[worst_day, 'total_pnl']:,.2f})")

# ============================================================================
# ANALYSIS 3: TRADE SIZE DISTRIBUTION
# ============================================================================
print("\n" + "=" * 80)
print("ANALYSIS 3: P&L DISTRIBUTION")
print("=" * 80)

for symbol in ['SPY', 'QQQ']:
    sym_df = trades[trades['symbol'] == symbol]
    
    wins = sym_df[sym_df['pnl_dollars'] > 0]['pnl_dollars']
    losses = sym_df[sym_df['pnl_dollars'] <= 0]['pnl_dollars']
    
    print(f"\n{symbol}:")
    print("-" * 50)
    print(f"Win count: {len(wins)} | Loss count: {len(losses)}")
    print(f"Win rate: {100*len(wins)/(len(wins)+len(losses)):.1f}%")
    print(f"\nWinning trades:")
    print(f"  Mean: ${wins.mean():.2f}")
    print(f"  Median: ${wins.median():.2f}")
    print(f"  Max: ${wins.max():.2f}")
    print(f"  Std: ${wins.std():.2f}")
    print(f"\nLosing trades:")
    print(f"  Mean: ${losses.mean():.2f}")
    print(f"  Median: ${losses.median():.2f}")
    print(f"  Max (worst): ${losses.min():.2f}")
    print(f"  Std: ${losses.std():.2f}")
    
    # Win/Loss ratio
    avg_win = wins.mean()
    avg_loss = abs(losses.mean())
    print(f"\nWin/Loss Ratio: {avg_win/avg_loss:.3f}")
    
    # Expectancy per trade
    win_rate = len(wins) / len(sym_df)
    expectancy = (win_rate * avg_win) - ((1-win_rate) * avg_loss)
    print(f"Expectancy per trade: ${expectancy:.4f}")

# ============================================================================
# ANALYSIS 4: FIRST VS LAST HOUR
# ============================================================================
print("\n" + "=" * 80)
print("ANALYSIS 4: FIRST HOUR vs LAST HOUR")
print("=" * 80)

for symbol in ['SPY', 'QQQ']:
    sym_df = trades[trades['symbol'] == symbol]
    
    first_hour = sym_df[sym_df['entry_hour'] == 9]  # 9:30-10:00
    last_hour = sym_df[sym_df['entry_hour'] >= 15]  # 3:00-4:00
    middle = sym_df[(sym_df['entry_hour'] >= 10) & (sym_df['entry_hour'] < 15)]
    
    print(f"\n{symbol}:")
    print("-" * 50)
    print(f"First Hour (9:xx): {len(first_hour)} trades, HR={100*first_hour['correct'].mean():.1f}%, P&L=${first_hour['pnl_dollars'].sum():,.2f}")
    print(f"Middle (10-14):    {len(middle)} trades, HR={100*middle['correct'].mean():.1f}%, P&L=${middle['pnl_dollars'].sum():,.2f}")
    print(f"Last Hour (15:xx): {len(last_hour)} trades, HR={100*last_hour['correct'].mean():.1f}%, P&L=${last_hour['pnl_dollars'].sum():,.2f}")

# ============================================================================
# ANALYSIS 5: STREAK ANALYSIS
# ============================================================================
print("\n" + "=" * 80)
print("ANALYSIS 5: STREAK ANALYSIS")
print("=" * 80)

for symbol in ['SPY', 'QQQ']:
    sym_df = trades[trades['symbol'] == symbol].sort_values('entry_time').reset_index(drop=True)
    
    # Find streaks
    streaks = []
    current_streak = 1
    current_type = sym_df.iloc[0]['correct']
    
    for i in range(1, len(sym_df)):
        if sym_df.iloc[i]['correct'] == current_type:
            current_streak += 1
        else:
            streaks.append((current_type, current_streak))
            current_streak = 1
            current_type = sym_df.iloc[i]['correct']
    streaks.append((current_type, current_streak))
    
    win_streaks = [s[1] for s in streaks if s[0] == 1]
    loss_streaks = [s[1] for s in streaks if s[0] == 0]
    
    print(f"\n{symbol}:")
    print("-" * 50)
    print(f"Max winning streak: {max(win_streaks)}")
    print(f"Max losing streak: {max(loss_streaks)}")
    print(f"Avg winning streak: {np.mean(win_streaks):.1f}")
    print(f"Avg losing streak: {np.mean(loss_streaks):.1f}")

# ============================================================================
# ANALYSIS 6: MONTHLY PERFORMANCE
# ============================================================================
print("\n" + "=" * 80)
print("ANALYSIS 6: MONTHLY PERFORMANCE")
print("=" * 80)

trades['month'] = trades['entry_time'].dt.to_period('M')

for symbol in ['SPY', 'QQQ']:
    sym_df = trades[trades['symbol'] == symbol]
    
    print(f"\n{symbol}:")
    print("-" * 50)
    
    monthly = sym_df.groupby('month').agg({
        'pnl_dollars': 'sum',
        'correct': 'mean'
    }).round(2)
    monthly.columns = ['pnl', 'hit_rate']
    monthly['hit_rate'] = (monthly['hit_rate'] * 100).round(1)
    
    # Show best and worst months
    best_months = monthly.nlargest(3, 'pnl')
    worst_months = monthly.nsmallest(3, 'pnl')
    
    print("\nBest 3 Months:")
    for idx, row in best_months.iterrows():
        print(f"  {idx}: ${row['pnl']:,.2f} (HR: {row['hit_rate']}%)")
    
    print("\nWorst 3 Months:")
    for idx, row in worst_months.iterrows():
        print(f"  {idx}: ${row['pnl']:,.2f} (HR: {row['hit_rate']}%)")
    
    # Profitable months ratio
    profitable = (monthly['pnl'] > 0).sum()
    print(f"\nProfitable months: {profitable}/{len(monthly)} ({100*profitable/len(monthly):.0f}%)")

# ============================================================================
# ANALYSIS 7: RECOMMENDATIONS BASED ON FINDINGS
# ============================================================================
print("\n" + "=" * 80)
print("ANALYSIS SUMMARY & RECOMMENDATIONS")
print("=" * 80)

print("""
Based on the analysis above, identify:

1. BEST TRADING HOURS - Exclude hours with consistent losses
2. BEST TRADING DAYS - Consider skipping worst performing days
3. ENTRY TIMING - First hour vs last hour performance
4. STREAK PATTERNS - Maximum drawdown exposure

Next steps for refinement:
- Filter trades to only include profitable hours/days
- Test with filtered universe
- Compare results
""")

print("=" * 80)
