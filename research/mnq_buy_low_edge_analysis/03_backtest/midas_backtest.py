"""
=============================================================================
MIDAS PROTOCOL: Final Backtest - Equity Curve Simulation
=============================================================================

Strategy Logic:
- Time Window: 02:00 - 06:00 UTC
- Setup #1 (Crash): Velocity_5m <= -67 AND Dist_EMA200 <= 220 AND ATR_Ratio > 0.5
- Setup #2 (Quiet): Velocity_5m <= 10 AND Dist_EMA200 <= 220 AND 0.06 < ATR_Ratio <= 0.50

Execution Rules:
- Take Profit: +40 points ($80 per contract)
- Stop Loss: -12 points ($24 per contract)
- Commission: $1.00 per trade
- Position Size: 1 Contract (MNQ)
- Starting Capital: $5,000

Author: Magellan Quant Research
Date: 2026-01-30
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

MNQ_CSV = Path(r"A:\1\Magellan\data\cache\futures\MNQ\glbx-mdp3-20210129-20260128.ohlcv-1m.csv")
OUTPUT_DIR = Path(r"a:\1\Magellan\research\mnq_buy_low_edge_analysis\03_backtest")

# Strategy parameters
GOLDEN_HOUR_START = 2
GOLDEN_HOUR_END = 6

# Trade parameters
TAKE_PROFIT_POINTS = 40
STOP_LOSS_POINTS = 12
POINT_VALUE = 2.0  # MNQ: $2 per point
COMMISSION = 1.0   # $1 per trade

# Capital
STARTING_CAPITAL = 5000
POSITION_SIZE = 1  # 1 contract

# Forward window for simulating trade outcomes
MAX_HOLD_TIME = 60  # Max minutes to hold if neither TP nor SL hit

# =============================================================================
# DATA LOADING AND PREPARATION
# =============================================================================

def load_data():
    """Load and prepare MNQ data."""
    print("="*80)
    print("MIDAS PROTOCOL: Final Backtest")
    print("="*80)
    
    print(f"\n[1/6] Loading data from {MNQ_CSV.name}...")
    df = pd.read_csv(MNQ_CSV)
    print(f"      Raw rows: {len(df):,}")
    
    # Parse timestamps
    df['datetime'] = pd.to_datetime(df['ts_event'].str[:19])
    df = df.set_index('datetime')
    df = df[['open', 'high', 'low', 'close', 'volume']].copy()
    
    # Aggregate by timestamp
    df_agg = df.groupby(df.index).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).sort_index()
    
    print(f"      Aggregated rows: {len(df_agg):,}")
    print(f"      Date range: {df_agg.index.min()} to {df_agg.index.max()}")
    
    return df_agg

def filter_golden_window(df):
    """Filter to Golden Window (02:00-06:00 UTC)."""
    print(f"\n[2/6] Filtering to Golden Window ({GOLDEN_HOUR_START:02d}:00 - {GOLDEN_HOUR_END:02d}:00 UTC)...")
    
    df['hour'] = df.index.hour
    mask = (df['hour'] >= GOLDEN_HOUR_START) & (df['hour'] < GOLDEN_HOUR_END)
    df_golden = df[mask].copy()
    
    print(f"      Rows in Golden Window: {len(df_golden):,}")
    
    return df_golden

def calculate_features(df):
    """Calculate all features needed for the strategy."""
    print("\n[3/6] Calculating features...")
    
    df = df.copy()
    
    # EMA200 and distance
    df['EMA200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['Dist_EMA200'] = df['close'] - df['EMA200']
    
    # 5-minute velocity
    df['Velocity_5m'] = df['close'] - df['close'].shift(5)
    
    # ATR and ratio
    prev_close = df['close'].shift(1)
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - prev_close).abs(),
        (df['low'] - prev_close).abs()
    ], axis=1).max(axis=1)
    df['ATR'] = tr.ewm(span=14, adjust=False).mean()
    df['ATR_Avg'] = df['ATR'].rolling(50).mean()
    df['ATR_Ratio'] = df['ATR'] / df['ATR_Avg']
    df['ATR_Ratio'] = df['ATR_Ratio'].replace([np.inf, -np.inf], np.nan).fillna(1.0)
    
    print("      Features calculated: Dist_EMA200, Velocity_5m, ATR_Ratio")
    
    return df

def identify_signals(df):
    """Identify entry signals based on MIDAS rules."""
    print("\n[4/6] Identifying entry signals...")
    
    df = df.copy()
    
    # Setup #1: Crash Reversal
    df['Setup1'] = (
        (df['Velocity_5m'] <= -67) &
        (df['Dist_EMA200'] <= 220) &
        (df['ATR_Ratio'] > 0.50)
    )
    
    # Setup #2: Quiet Mean Reversion
    df['Setup2'] = (
        (df['Velocity_5m'] <= 10) &
        (df['Dist_EMA200'] <= 220) &
        (df['ATR_Ratio'] > 0.06) &
        (df['ATR_Ratio'] <= 0.50)
    )
    
    # Combined signal
    df['Signal'] = df['Setup1'] | df['Setup2']
    
    setup1_count = df['Setup1'].sum()
    setup2_count = df['Setup2'].sum()
    total_signals = df['Signal'].sum()
    
    print(f"      Setup #1 signals (Crash): {setup1_count:,}")
    print(f"      Setup #2 signals (Quiet): {setup2_count:,}")
    print(f"      Total unique signals: {total_signals:,}")
    
    return df

def simulate_trade(df, entry_idx, entry_price):
    """
    Simulate a single trade from entry point.
    Returns: (pnl_points, hold_time, exit_type)
    """
    entry_loc = df.index.get_loc(entry_idx)
    
    # Look forward up to MAX_HOLD_TIME bars
    for i in range(1, min(MAX_HOLD_TIME + 1, len(df) - entry_loc)):
        future_idx = df.index[entry_loc + i]
        future_bar = df.loc[future_idx]
        
        # Check stop loss first (worst case)
        if future_bar['low'] <= entry_price - STOP_LOSS_POINTS:
            return -STOP_LOSS_POINTS, i, 'SL'
        
        # Check take profit
        if future_bar['high'] >= entry_price + TAKE_PROFIT_POINTS:
            return TAKE_PROFIT_POINTS, i, 'TP'
    
    # Timeout - exit at last close
    last_idx = df.index[min(entry_loc + MAX_HOLD_TIME, len(df) - 1)]
    exit_price = df.loc[last_idx, 'close']
    pnl = exit_price - entry_price
    return pnl, MAX_HOLD_TIME, 'TO'

def run_backtest(df):
    """Run the full backtest simulation."""
    print("\n[5/6] Running backtest simulation...")
    
    # Get signal rows
    signals_df = df[df['Signal'] == True].copy()
    
    trades = []
    last_exit_idx = None
    
    # Process signals chronologically (no overlapping trades)
    for entry_idx in signals_df.index:
        # Skip if we're still in a trade
        if last_exit_idx is not None and entry_idx <= last_exit_idx:
            continue
        
        entry_price = df.loc[entry_idx, 'close']
        
        # Simulate trade
        pnl_points, hold_time, exit_type = simulate_trade(df, entry_idx, entry_price)
        
        # Calculate P&L in dollars
        pnl_dollars = (pnl_points * POINT_VALUE * POSITION_SIZE) - COMMISSION
        
        # Record trade
        trades.append({
            'entry_time': entry_idx,
            'entry_price': entry_price,
            'pnl_points': pnl_points,
            'pnl_dollars': pnl_dollars,
            'hold_time': hold_time,
            'exit_type': exit_type,
            'setup': 'Crash' if df.loc[entry_idx, 'Setup1'] else 'Quiet'
        })
        
        # Update last exit index
        entry_loc = df.index.get_loc(entry_idx)
        last_exit_idx = df.index[min(entry_loc + hold_time, len(df) - 1)]
    
    trades_df = pd.DataFrame(trades)
    print(f"      Total trades executed: {len(trades_df):,}")
    
    return trades_df

def calculate_metrics(trades_df):
    """Calculate backtest metrics."""
    print("\n[6/6] Calculating metrics...")
    
    # Basic metrics
    total_trades = len(trades_df)
    winners = (trades_df['pnl_dollars'] > 0).sum()
    losers = (trades_df['pnl_dollars'] <= 0).sum()
    win_rate = winners / total_trades * 100
    
    # P&L metrics
    total_pnl = trades_df['pnl_dollars'].sum()
    avg_pnl = trades_df['pnl_dollars'].mean()
    avg_winner = trades_df[trades_df['pnl_dollars'] > 0]['pnl_dollars'].mean()
    avg_loser = trades_df[trades_df['pnl_dollars'] <= 0]['pnl_dollars'].mean()
    
    # Equity curve
    trades_df['cumulative_pnl'] = trades_df['pnl_dollars'].cumsum()
    trades_df['equity'] = STARTING_CAPITAL + trades_df['cumulative_pnl']
    
    # Max drawdown
    trades_df['peak'] = trades_df['equity'].cummax()
    trades_df['drawdown'] = trades_df['equity'] - trades_df['peak']
    max_drawdown = trades_df['drawdown'].min()
    max_drawdown_pct = (max_drawdown / trades_df['peak'].max()) * 100
    
    # Sharpe Ratio (annualized)
    # Assuming ~250 trading days, trades per day
    trades_per_day = total_trades / ((trades_df['entry_time'].max() - trades_df['entry_time'].min()).days + 1)
    daily_returns = trades_df.groupby(trades_df['entry_time'].dt.date)['pnl_dollars'].sum()
    if len(daily_returns) > 1:
        sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
    else:
        sharpe = 0
    
    # By setup
    setup_stats = trades_df.groupby('setup').agg({
        'pnl_dollars': ['count', 'sum', 'mean'],
    }).round(2)
    
    metrics = {
        'total_trades': total_trades,
        'winners': winners,
        'losers': losers,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'avg_pnl': avg_pnl,
        'avg_winner': avg_winner,
        'avg_loser': avg_loser,
        'max_drawdown': max_drawdown,
        'max_drawdown_pct': max_drawdown_pct,
        'sharpe': sharpe,
        'final_equity': trades_df['equity'].iloc[-1],
        'trades_per_day': trades_per_day,
        'setup_stats': setup_stats
    }
    
    return metrics, trades_df

def print_results(metrics, trades_df):
    """Print backtest results."""
    print("\n" + "="*80)
    print("BACKTEST RESULTS")
    print("="*80)
    
    print(f"\n{'PERFORMANCE SUMMARY':^60}")
    print("-"*60)
    print(f"Starting Capital:        ${STARTING_CAPITAL:,.2f}")
    print(f"Final Equity:            ${metrics['final_equity']:,.2f}")
    print(f"Total P&L:               ${metrics['total_pnl']:,.2f}")
    print(f"Total Return:            {(metrics['final_equity']/STARTING_CAPITAL - 1)*100:.1f}%")
    print(f"Max Drawdown:            ${metrics['max_drawdown']:,.2f} ({metrics['max_drawdown_pct']:.1f}%)")
    print(f"Sharpe Ratio:            {metrics['sharpe']:.2f}")
    
    print(f"\n{'TRADE STATISTICS':^60}")
    print("-"*60)
    print(f"Total Trades:            {metrics['total_trades']:,}")
    print(f"Winners:                 {metrics['winners']:,}")
    print(f"Losers:                  {metrics['losers']:,}")
    print(f"Win Rate:                {metrics['win_rate']:.1f}%")
    print(f"Avg P&L per Trade:       ${metrics['avg_pnl']:.2f}")
    print(f"Avg Winner:              ${metrics['avg_winner']:.2f}")
    print(f"Avg Loser:               ${metrics['avg_loser']:.2f}")
    print(f"Trades per Day:          {metrics['trades_per_day']:.1f}")
    
    print(f"\n{'BY SETUP':^60}")
    print("-"*60)
    print(metrics['setup_stats'])
    
    # Exit type breakdown
    print(f"\n{'EXIT TYPE BREAKDOWN':^60}")
    print("-"*60)
    exit_counts = trades_df['exit_type'].value_counts()
    for exit_type, count in exit_counts.items():
        label = {'TP': 'Take Profit', 'SL': 'Stop Loss', 'TO': 'Timeout'}[exit_type]
        print(f"{label:20}: {count:,} ({100*count/len(trades_df):.1f}%)")

def plot_equity_curve(trades_df, metrics):
    """Generate and save equity curve plot."""
    print("\n[PLOT] Generating equity curve...")
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
    
    # Equity curve
    ax1 = axes[0]
    ax1.plot(trades_df['entry_time'], trades_df['equity'], 'b-', linewidth=1, label='Equity')
    ax1.axhline(y=STARTING_CAPITAL, color='gray', linestyle='--', alpha=0.5, label='Starting Capital')
    ax1.fill_between(trades_df['entry_time'], STARTING_CAPITAL, trades_df['equity'], 
                     where=trades_df['equity'] >= STARTING_CAPITAL, color='green', alpha=0.3)
    ax1.fill_between(trades_df['entry_time'], STARTING_CAPITAL, trades_df['equity'], 
                     where=trades_df['equity'] < STARTING_CAPITAL, color='red', alpha=0.3)
    
    ax1.set_title('MIDAS Protocol Backtest: Equity Curve (2021-2026)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Equity ($)', fontsize=12)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # Add key metrics as text box
    textstr = f"Total P&L: ${metrics['total_pnl']:,.0f}\n"
    textstr += f"Win Rate: {metrics['win_rate']:.1f}%\n"
    textstr += f"Sharpe: {metrics['sharpe']:.2f}\n"
    textstr += f"Max DD: ${metrics['max_drawdown']:,.0f}"
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax1.text(0.02, 0.98, textstr, transform=ax1.transAxes, fontsize=10,
             verticalalignment='top', bbox=props)
    
    # Drawdown
    ax2 = axes[1]
    ax2.fill_between(trades_df['entry_time'], 0, trades_df['drawdown'], color='red', alpha=0.5)
    ax2.set_title('Drawdown', fontsize=12)
    ax2.set_ylabel('Drawdown ($)', fontsize=10)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    
    # Save
    plot_path = OUTPUT_DIR / "midas_equity_curve.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"      Saved to: {plot_path}")
    
    plt.close()
    
    return plot_path

def generate_report(metrics, trades_df):
    """Generate markdown report."""
    
    report = f"""# MIDAS Protocol: Final Backtest Results

## Executive Summary

| Metric | Value |
|--------|-------|
| **Starting Capital** | ${STARTING_CAPITAL:,.2f} |
| **Final Equity** | ${metrics['final_equity']:,.2f} |
| **Total P&L** | **${metrics['total_pnl']:,.2f}** |
| **Total Return** | **{(metrics['final_equity']/STARTING_CAPITAL - 1)*100:.1f}%** |
| **Max Drawdown** | ${metrics['max_drawdown']:,.2f} ({metrics['max_drawdown_pct']:.1f}%) |
| **Sharpe Ratio** | **{metrics['sharpe']:.2f}** |

---

## Configuration

| Parameter | Value |
|-----------|-------|
| Time Window | 02:00 - 06:00 UTC |
| Take Profit | +{TAKE_PROFIT_POINTS} points (${TAKE_PROFIT_POINTS * POINT_VALUE}) |
| Stop Loss | -{STOP_LOSS_POINTS} points (${STOP_LOSS_POINTS * POINT_VALUE}) |
| Commission | ${COMMISSION} per trade |
| Position Size | {POSITION_SIZE} contract |
| Point Value | ${POINT_VALUE} (MNQ) |

---

## Trade Statistics

| Metric | Value |
|--------|-------|
| Total Trades | {metrics['total_trades']:,} |
| Winners | {metrics['winners']:,} |
| Losers | {metrics['losers']:,} |
| Win Rate | {metrics['win_rate']:.1f}% |
| Avg P&L per Trade | ${metrics['avg_pnl']:.2f} |
| Avg Winner | ${metrics['avg_winner']:.2f} |
| Avg Loser | ${metrics['avg_loser']:.2f} |
| Trades per Day | {metrics['trades_per_day']:.1f} |

---

## By Setup Performance

| Setup | Trades | Total P&L | Avg P&L |
|-------|--------|-----------|---------|
"""
    
    for setup in ['Crash', 'Quiet']:
        if setup in trades_df['setup'].values:
            setup_trades = trades_df[trades_df['setup'] == setup]
            count = len(setup_trades)
            total = setup_trades['pnl_dollars'].sum()
            avg = setup_trades['pnl_dollars'].mean()
            report += f"| {setup} | {count:,} | ${total:,.2f} | ${avg:.2f} |\n"
    
    report += f"""
---

## Exit Type Breakdown

| Exit Type | Count | Percentage |
|-----------|-------|------------|
"""
    
    exit_counts = trades_df['exit_type'].value_counts()
    for exit_type in ['TP', 'SL', 'TO']:
        if exit_type in exit_counts:
            count = exit_counts[exit_type]
            label = {'TP': 'Take Profit', 'SL': 'Stop Loss', 'TO': 'Timeout'}[exit_type]
            report += f"| {label} | {count:,} | {100*count/len(trades_df):.1f}% |\n"
    
    report += f"""
---

## Equity Curve

![Equity Curve](midas_equity_curve.png)

---

## Strategy Rules

**Setup #1: Crash Reversal**
- `Velocity_5m <= -67`
- `Dist_EMA200 <= 220`
- `ATR_Ratio > 0.50`

**Setup #2: Quiet Mean Reversion**
- `Velocity_5m <= 10`
- `Dist_EMA200 <= 220`
- `0.06 < ATR_Ratio <= 0.50`

---

*Generated by Magellan Quant Research*  
*Backtest Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    report_path = OUTPUT_DIR / "MIDAS_BACKTEST_RESULTS.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n[SAVED] Report: {report_path}")
    
    return report

def main():
    """Run the full backtest."""
    
    # Load and prepare data
    df = load_data()
    df = filter_golden_window(df)
    df = calculate_features(df)
    df = identify_signals(df)
    
    # Run backtest
    trades_df = run_backtest(df)
    
    # Calculate metrics
    metrics, trades_df = calculate_metrics(trades_df)
    
    # Print results
    print_results(metrics, trades_df)
    
    # Generate plots and report
    plot_equity_curve(trades_df, metrics)
    generate_report(metrics, trades_df)
    
    # Save trades
    trades_path = OUTPUT_DIR / "midas_trades.csv"
    trades_df.to_csv(trades_path, index=False)
    print(f"[SAVED] Trades: {trades_path}")
    
    print("\n" + "="*80)
    print("MIDAS PROTOCOL BACKTEST COMPLETE")
    print("="*80)
    
    return metrics, trades_df

if __name__ == "__main__":
    metrics, trades_df = main()
