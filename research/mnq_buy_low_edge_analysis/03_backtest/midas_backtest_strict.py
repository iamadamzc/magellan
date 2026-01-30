"""
=============================================================================
MIDAS PROTOCOL: STRICT BACKTEST (Bias-Free Execution)
=============================================================================

AUDIT FIXES APPLIED:
1. EXECUTION DELAY: Signal on Close of bar i -> Execute on OPEN of bar i+1
2. WORST CASE INTRA-BAR: If both TP and SL hit same bar, assume SL hit FIRST
3. SLIPPAGE: Add 0.5 points slippage per trade

Author: Magellan Quant Research (Audit Mode)
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

# Trade parameters (STRICT)
TAKE_PROFIT_POINTS = 40
STOP_LOSS_POINTS = 12
SLIPPAGE_POINTS = 0.5  # NEW: Slippage per trade
POINT_VALUE = 2.0      # MNQ: $2 per point
COMMISSION = 1.0       # $1 per trade

# Capital
STARTING_CAPITAL = 5000
POSITION_SIZE = 1

# Max hold time
MAX_HOLD_TIME = 60

# =============================================================================
# DATA LOADING
# =============================================================================

def load_data():
    """Load and prepare MNQ data."""
    print("="*80)
    print("MIDAS PROTOCOL: STRICT BACKTEST (Bias-Free)")
    print("="*80)
    print("\nAUDIT FIXES APPLIED:")
    print("  1. Execution Delay: Signal on Close[i] -> Execute on Open[i+1]")
    print("  2. Worst Case Intra-Bar: If TP & SL both hit, assume SL first")
    print(f"  3. Slippage: {SLIPPAGE_POINTS} points per trade")
    
    print(f"\n[1/6] Loading data...")
    df = pd.read_csv(MNQ_CSV)
    print(f"      Raw rows: {len(df):,}")
    
    df['datetime'] = pd.to_datetime(df['ts_event'].str[:19])
    df = df.set_index('datetime')
    df = df[['open', 'high', 'low', 'close', 'volume']].copy()
    
    df_agg = df.groupby(df.index).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).sort_index()
    
    print(f"      Aggregated rows: {len(df_agg):,}")
    
    return df_agg

def filter_golden_window(df):
    """Filter to Golden Window."""
    print(f"\n[2/6] Filtering to Golden Window...")
    
    df['hour'] = df.index.hour
    mask = (df['hour'] >= GOLDEN_HOUR_START) & (df['hour'] < GOLDEN_HOUR_END)
    df_golden = df[mask].copy()
    
    print(f"      Rows in Golden Window: {len(df_golden):,}")
    
    return df_golden

def calculate_features(df):
    """Calculate features."""
    print("\n[3/6] Calculating features...")
    
    df = df.copy()
    
    df['EMA200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['Dist_EMA200'] = df['close'] - df['EMA200']
    df['Velocity_5m'] = df['close'] - df['close'].shift(5)
    
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
    
    return df

def identify_signals(df):
    """Identify entry signals."""
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
    
    df['Signal'] = df['Setup1'] | df['Setup2']
    
    print(f"      Total signals: {df['Signal'].sum():,}")
    
    return df

def simulate_trade_strict(df, signal_idx, entry_price):
    """
    STRICT trade simulation with worst-case assumptions.
    
    Key fixes:
    - Entry is on OPEN of bar AFTER signal (already passed in)
    - If both TP and SL hit in same bar, assume SL hit FIRST
    - Apply slippage to entry price
    """
    entry_loc = df.index.get_loc(signal_idx) + 1  # +1 for next bar
    
    if entry_loc >= len(df):
        return None, 0, 'SKIP'
    
    # Entry is on OPEN of next bar, with slippage
    actual_entry_price = entry_price + SLIPPAGE_POINTS  # Slippage hurts longs
    
    tp_price = actual_entry_price + TAKE_PROFIT_POINTS
    sl_price = actual_entry_price - STOP_LOSS_POINTS
    
    # Simulate forward
    for i in range(entry_loc, min(entry_loc + MAX_HOLD_TIME, len(df))):
        bar = df.iloc[i]
        bars_held = i - entry_loc + 1
        
        # WORST CASE: Check if BOTH levels hit in same bar
        sl_hit = bar['low'] <= sl_price
        tp_hit = bar['high'] >= tp_price
        
        if sl_hit and tp_hit:
            # BOTH hit - assume STOP LOSS hit FIRST (worst case)
            pnl = -STOP_LOSS_POINTS - SLIPPAGE_POINTS
            return pnl, bars_held, 'SL'
        
        if sl_hit:
            # Stop loss hit
            pnl = -STOP_LOSS_POINTS - SLIPPAGE_POINTS
            return pnl, bars_held, 'SL'
        
        if tp_hit:
            # Take profit hit   
            pnl = TAKE_PROFIT_POINTS - SLIPPAGE_POINTS
            return pnl, bars_held, 'TP'
    
    # Timeout - exit at last close
    last_bar = df.iloc[min(entry_loc + MAX_HOLD_TIME - 1, len(df) - 1)]
    exit_price = last_bar['close'] - SLIPPAGE_POINTS  # Exit slippage hurts too
    pnl = exit_price - actual_entry_price
    return pnl, MAX_HOLD_TIME, 'TO'

def run_backtest_strict(df):
    """Run strict backtest with execution delay."""
    print("\n[5/6] Running STRICT backtest...")
    print("      (Execution on Open[i+1], worst-case intra-bar, slippage applied)")
    
    signals_df = df[df['Signal'] == True].copy()
    
    trades = []
    last_exit_bar = -1
    
    for signal_idx in signals_df.index:
        signal_loc = df.index.get_loc(signal_idx)
        
        # Skip if we're still in a trade
        if signal_loc <= last_exit_bar:
            continue
        
        # EXECUTION DELAY: Entry price is OPEN of NEXT bar
        entry_loc = signal_loc + 1
        if entry_loc >= len(df):
            continue
        
        entry_bar_idx = df.index[entry_loc]
        entry_price = df.iloc[entry_loc]['open']  # OPEN of next bar
        
        # Simulate trade
        result = simulate_trade_strict(df, signal_idx, entry_price)
        if result[0] is None:
            continue
        
        pnl_points, hold_time, exit_type = result
        
        # Calculate P&L in dollars
        pnl_dollars = (pnl_points * POINT_VALUE * POSITION_SIZE) - COMMISSION
        
        trades.append({
            'signal_time': signal_idx,
            'entry_time': entry_bar_idx,
            'entry_price': entry_price + SLIPPAGE_POINTS,  # Actual entry after slippage
            'pnl_points': pnl_points,
            'pnl_dollars': pnl_dollars,
            'hold_time': hold_time,
            'exit_type': exit_type,
            'setup': 'Crash' if df.loc[signal_idx, 'Setup1'] else 'Quiet'
        })
        
        # Update last exit
        last_exit_bar = entry_loc + hold_time
    
    trades_df = pd.DataFrame(trades)
    print(f"      Total trades executed: {len(trades_df):,}")
    
    return trades_df

def calculate_metrics(trades_df):
    """Calculate backtest metrics."""
    print("\n[6/6] Calculating metrics...")
    
    total_trades = len(trades_df)
    winners = (trades_df['pnl_dollars'] > 0).sum()
    losers = (trades_df['pnl_dollars'] <= 0).sum()
    win_rate = winners / total_trades * 100
    
    total_pnl = trades_df['pnl_dollars'].sum()
    avg_pnl = trades_df['pnl_dollars'].mean()
    avg_winner = trades_df[trades_df['pnl_dollars'] > 0]['pnl_dollars'].mean()
    avg_loser = trades_df[trades_df['pnl_dollars'] <= 0]['pnl_dollars'].mean()
    
    trades_df['cumulative_pnl'] = trades_df['pnl_dollars'].cumsum()
    trades_df['equity'] = STARTING_CAPITAL + trades_df['cumulative_pnl']
    
    trades_df['peak'] = trades_df['equity'].cummax()
    trades_df['drawdown'] = trades_df['equity'] - trades_df['peak']
    max_drawdown = trades_df['drawdown'].min()
    max_drawdown_pct = (max_drawdown / trades_df['peak'].max()) * 100 if trades_df['peak'].max() > 0 else 0
    
    daily_returns = trades_df.groupby(trades_df['entry_time'].dt.date)['pnl_dollars'].sum()
    if len(daily_returns) > 1 and daily_returns.std() > 0:
        sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
    else:
        sharpe = 0
    
    trades_per_day = total_trades / ((trades_df['entry_time'].max() - trades_df['entry_time'].min()).days + 1)
    
    return {
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
        'final_equity': trades_df['equity'].iloc[-1] if len(trades_df) > 0 else STARTING_CAPITAL,
        'trades_per_day': trades_per_day
    }, trades_df

def print_results(metrics, trades_df):
    """Print results with comparison."""
    print("\n" + "="*80)
    print("STRICT BACKTEST RESULTS (Bias-Free)")
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
    
    print(f"\n{'EXIT TYPE BREAKDOWN':^60}")
    print("-"*60)
    exit_counts = trades_df['exit_type'].value_counts()
    for exit_type in ['TP', 'SL', 'TO']:
        if exit_type in exit_counts:
            count = exit_counts[exit_type]
            label = {'TP': 'Take Profit', 'SL': 'Stop Loss', 'TO': 'Timeout'}[exit_type]
            print(f"{label:20}: {count:,} ({100*count/len(trades_df):.1f}%)")
    
    print("\n" + "="*80)
    print("COMPARISON: Original vs Strict")
    print("="*80)
    print(f"{'Metric':<25} {'Original':>15} {'Strict':>15} {'Delta':>15}")
    print("-"*70)
    print(f"{'Win Rate':<25} {'90.2%':>15} {metrics['win_rate']:.1f}%{' ':>10} {metrics['win_rate']-90.2:+.1f}%")
    print(f"{'Total P&L':<25} {'$1,674,065':>15} ${metrics['total_pnl']:>13,.0f} ${metrics['total_pnl']-1674065:>+12,.0f}")
    print(f"{'Sharpe Ratio':<25} {'19.98':>15} {metrics['sharpe']:>15.2f} {metrics['sharpe']-19.98:>+15.2f}")

def plot_equity_curve(trades_df, metrics):
    """Generate equity curve plot."""
    print("\n[PLOT] Generating equity curve...")
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
    
    ax1 = axes[0]
    ax1.plot(trades_df['entry_time'], trades_df['equity'], 'b-', linewidth=1, label='Equity (Strict)')
    ax1.axhline(y=STARTING_CAPITAL, color='gray', linestyle='--', alpha=0.5, label='Starting Capital')
    ax1.fill_between(trades_df['entry_time'], STARTING_CAPITAL, trades_df['equity'], 
                     where=trades_df['equity'] >= STARTING_CAPITAL, color='green', alpha=0.3)
    ax1.fill_between(trades_df['entry_time'], STARTING_CAPITAL, trades_df['equity'], 
                     where=trades_df['equity'] < STARTING_CAPITAL, color='red', alpha=0.3)
    
    ax1.set_title('MIDAS Protocol STRICT Backtest: Equity Curve (Bias-Free)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Equity ($)', fontsize=12)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    textstr = f"Total P&L: ${metrics['total_pnl']:,.0f}\n"
    textstr += f"Win Rate: {metrics['win_rate']:.1f}%\n"
    textstr += f"Sharpe: {metrics['sharpe']:.2f}\n"
    textstr += f"Max DD: ${metrics['max_drawdown']:,.0f}"
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax1.text(0.02, 0.98, textstr, transform=ax1.transAxes, fontsize=10,
             verticalalignment='top', bbox=props)
    
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
    
    plot_path = OUTPUT_DIR / "midas_equity_curve_STRICT.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"      Saved to: {plot_path}")
    
    plt.close()

def generate_report(metrics, trades_df):
    """Generate markdown report."""
    
    report = f"""# MIDAS Protocol: STRICT Backtest Results (Bias-Free)

## Audit Fixes Applied

| Fix | Description |
|-----|-------------|
| **Execution Delay** | Signal on Close[i] -> Execute on Open[i+1] |
| **Worst Case Intra-Bar** | If both TP & SL hit same bar, assume SL hit FIRST |
| **Slippage** | {SLIPPAGE_POINTS} points per trade (${SLIPPAGE_POINTS * POINT_VALUE} per contract) |

---

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

## Comparison: Original vs Strict

| Metric | Original (Biased) | Strict (Bias-Free) | Delta |
|--------|-------------------|---------------------|-------|
| Win Rate | 90.2% | {metrics['win_rate']:.1f}% | {metrics['win_rate']-90.2:+.1f}% |
| Total P&L | $1,674,065 | ${metrics['total_pnl']:,.0f} | ${metrics['total_pnl']-1674065:+,.0f} |
| Sharpe | 19.98 | {metrics['sharpe']:.2f} | {metrics['sharpe']-19.98:+.2f} |
| Total Trades | 24,436 | {metrics['total_trades']:,} | {metrics['total_trades']-24436:+,} |

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

![Equity Curve (Strict)](midas_equity_curve_STRICT.png)

---

*Generated by Magellan Quant Research - AUDIT MODE*  
*Backtest Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    report_path = OUTPUT_DIR / "MIDAS_BACKTEST_RESULTS_STRICT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n[SAVED] Report: {report_path}")

def main():
    """Run strict backtest."""
    
    df = load_data()
    df = filter_golden_window(df)
    df = calculate_features(df)
    df = identify_signals(df)
    
    trades_df = run_backtest_strict(df)
    
    if len(trades_df) == 0:
        print("ERROR: No trades executed!")
        return None, None
    
    metrics, trades_df = calculate_metrics(trades_df)
    
    print_results(metrics, trades_df)
    plot_equity_curve(trades_df, metrics)
    generate_report(metrics, trades_df)
    
    trades_path = OUTPUT_DIR / "midas_trades_STRICT.csv"
    trades_df.to_csv(trades_path, index=False)
    print(f"[SAVED] Trades: {trades_path}")
    
    print("\n" + "="*80)
    print("STRICT BACKTEST COMPLETE")
    print("="*80)
    
    return metrics, trades_df

if __name__ == "__main__":
    metrics, trades_df = main()
