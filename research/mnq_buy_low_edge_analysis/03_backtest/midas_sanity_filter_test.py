"""
=============================================================================
MIDAS PROTOCOL: Sanity Filter Test with Rejected Trade Log
=============================================================================

OBJECTIVE: Test the Sanity Filter and record every blocked signal

THE FILTER:
- IF Velocity_5m < -150: REJECT (Log to Rejected_Ledger)
- IF Velocity_5m >= -150: ACCEPT (Execute trade)

Author: Magellan Quant Research (Forensic Auditor)
Date: 2026-01-30
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.tree import DecisionTreeClassifier
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

# Data split
TRAIN_END = "2024-12-31"
TEST_START = "2025-01-01"

# Strategy parameters
GOLDEN_HOUR_START = 2
GOLDEN_HOUR_END = 6

# SANITY FILTER THRESHOLD
VELOCITY_REJECT_THRESHOLD = -150  # Reject if velocity < this

# Trade parameters (TORTURE MODE)
TAKE_PROFIT_POINTS = 40
STOP_LOSS_POINTS = 12
SLIPPAGE_SPREAD_POINTS = 2.0
POINT_VALUE = 2.0
COMMISSION = 2.50
TOTAL_COST_PER_TRADE = (SLIPPAGE_SPREAD_POINTS * POINT_VALUE) + COMMISSION

STARTING_CAPITAL = 5000
MAX_HOLD_TIME = 60

# =============================================================================
# DATA FUNCTIONS
# =============================================================================

def load_data():
    """Load full dataset."""
    print("="*80)
    print("MIDAS PROTOCOL: Sanity Filter Test with Rejected Trade Log")
    print("="*80)
    print(f"\nSANITY FILTER: Reject trades where Velocity_5m < {VELOCITY_REJECT_THRESHOLD}")
    
    print(f"\n[1/8] Loading data...")
    df = pd.read_csv(MNQ_CSV)
    
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
    
    return df_agg

def split_data(df):
    """Split into train/test."""
    print(f"\n[2/8] Splitting data...")
    train = df[df.index <= TRAIN_END].copy()
    test = df[df.index >= TEST_START].copy()
    print(f"      Training: {len(train):,} rows")
    print(f"      Testing:  {len(test):,} rows (2025+)")
    return train, test

def filter_golden_window(df):
    """Filter to Golden Window."""
    df['hour'] = df.index.hour
    return df[(df['hour'] >= GOLDEN_HOUR_START) & (df['hour'] < GOLDEN_HOUR_END)].copy()

def calculate_features(df):
    """Calculate features."""
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
    df['ATR_Ratio'] = (df['ATR'] / df['ATR_Avg']).replace([np.inf, -np.inf], np.nan).fillna(1.0)
    
    range_hl = df['high'] - df['low']
    df['Wick_Ratio'] = ((df['close'] - df['low']) / range_hl).replace([np.inf, -np.inf], np.nan).fillna(0.5)
    
    return df

def calculate_target(df):
    """Calculate target for training."""
    df = df.copy()
    df['future_max_high'] = df['high'].shift(-1).rolling(window=30, min_periods=30).max().shift(-29)
    df['future_min_low'] = df['low'].shift(-1).rolling(window=30, min_periods=30).min().shift(-29)
    df['MFE'] = df['future_max_high'] - df['close']
    df['MAE'] = df['close'] - df['future_min_low']
    df['Target'] = (df['MFE'] >= 40) & (df['MAE'] <= 12)
    return df

def train_model(train_df):
    """Train on 2021-2024 data."""
    print(f"\n[3/8] Training model on 2021-2024...")
    
    feature_cols = ['Dist_EMA200', 'Wick_Ratio', 'Velocity_5m', 'ATR_Ratio']
    df_clean = train_df.dropna(subset=feature_cols + ['Target'])
    
    X = df_clean[feature_cols]
    y = df_clean['Target'].astype(int)
    
    clf = DecisionTreeClassifier(max_depth=4, min_samples_leaf=50, random_state=42)
    clf.fit(X, y)
    
    print(f"      Training samples: {len(X):,}")
    return clf, feature_cols

def apply_model_with_filter(df, clf, feature_cols):
    """Apply model and separate accepted vs rejected signals."""
    print(f"\n[5/8] Applying model with SANITY FILTER...")
    
    df = df.copy()
    df_clean = df.dropna(subset=feature_cols)
    X = df_clean[feature_cols]
    
    # Get all potential signals (where tree predicts positive)
    predictions = clf.predict(X) == 1
    df_clean['RawSignal'] = predictions
    
    # All potential signals
    all_signals = df_clean[df_clean['RawSignal'] == True].copy()
    
    # Apply sanity filter
    all_signals['Rejected'] = all_signals['Velocity_5m'] < VELOCITY_REJECT_THRESHOLD
    all_signals['RejectReason'] = np.where(
        all_signals['Velocity_5m'] < VELOCITY_REJECT_THRESHOLD,
        f'Velocity < {VELOCITY_REJECT_THRESHOLD}',
        ''
    )
    
    # Split into accepted and rejected
    rejected = all_signals[all_signals['Rejected'] == True].copy()
    accepted = all_signals[all_signals['Rejected'] == False].copy()
    accepted['Signal'] = True
    
    print(f"      Total Signals Detected: {len(all_signals):,}")
    print(f"      Signals REJECTED:       {len(rejected):,}")
    print(f"      Signals ACCEPTED:       {len(accepted):,}")
    print(f"      Rejection Rate:         {len(rejected)/len(all_signals)*100:.1f}%")
    
    return accepted, rejected, len(all_signals)

def simulate_trade_torture(df, signal_idx, entry_price):
    """Torture mode trade simulation."""
    entry_loc = df.index.get_loc(signal_idx) + 1
    
    if entry_loc >= len(df):
        return None, 0, 'SKIP', None
    
    actual_entry = entry_price + SLIPPAGE_SPREAD_POINTS
    tp_price = actual_entry + TAKE_PROFIT_POINTS
    sl_price = actual_entry - STOP_LOSS_POINTS
    
    for i in range(entry_loc, min(entry_loc + MAX_HOLD_TIME, len(df))):
        bar = df.iloc[i]
        bars_held = i - entry_loc + 1
        
        sl_hit = bar['low'] <= sl_price
        tp_hit = bar['high'] >= tp_price
        
        if sl_hit and tp_hit:
            return -STOP_LOSS_POINTS - SLIPPAGE_SPREAD_POINTS, bars_held, 'SL', df.index[i]
        if sl_hit:
            return -STOP_LOSS_POINTS - SLIPPAGE_SPREAD_POINTS, bars_held, 'SL', df.index[i]
        if tp_hit:
            return TAKE_PROFIT_POINTS - SLIPPAGE_SPREAD_POINTS, bars_held, 'TP', df.index[i]
    
    last_idx = min(entry_loc + MAX_HOLD_TIME - 1, len(df) - 1)
    last_bar = df.iloc[last_idx]
    exit_price = last_bar['close'] - SLIPPAGE_SPREAD_POINTS
    return exit_price - actual_entry, MAX_HOLD_TIME, 'TO', df.index[last_idx]

def run_backtest_on_accepted(df, accepted_df):
    """Run backtest only on accepted signals."""
    print(f"\n[6/8] Running backtest on ACCEPTED signals only...")
    
    trades = []
    last_exit_bar = -1
    
    for signal_idx in accepted_df.index:
        if signal_idx not in df.index:
            continue
            
        signal_loc = df.index.get_loc(signal_idx)
        
        if signal_loc <= last_exit_bar:
            continue
        
        entry_loc = signal_loc + 1
        if entry_loc >= len(df):
            continue
        
        entry_bar_idx = df.index[entry_loc]
        entry_price = df.iloc[entry_loc]['open']
        velocity = accepted_df.loc[signal_idx, 'Velocity_5m']
        
        result = simulate_trade_torture(df, signal_idx, entry_price)
        if result[0] is None:
            continue
        
        pnl_points, hold_time, exit_type, exit_time = result
        pnl_dollars = (pnl_points * POINT_VALUE) - COMMISSION
        
        trades.append({
            'signal_time': signal_idx,
            'entry_time': entry_bar_idx,
            'exit_time': exit_time,
            'entry_price': entry_price,
            'velocity_5m': velocity,
            'pnl_points': pnl_points,
            'pnl_dollars': pnl_dollars,
            'hold_time': hold_time,
            'exit_type': exit_type
        })
        
        last_exit_bar = entry_loc + hold_time
    
    trades_df = pd.DataFrame(trades)
    print(f"      Trades executed: {len(trades_df):,}")
    
    return trades_df

def calculate_metrics(trades_df):
    """Calculate metrics."""
    if len(trades_df) == 0:
        return None
    
    total_trades = len(trades_df)
    winners = (trades_df['pnl_dollars'] > 0).sum()
    win_rate = winners / total_trades * 100
    total_pnl = trades_df['pnl_dollars'].sum()
    
    trades_df['cumulative_pnl'] = trades_df['pnl_dollars'].cumsum()
    trades_df['equity'] = STARTING_CAPITAL + trades_df['cumulative_pnl']
    
    trades_df['peak'] = trades_df['equity'].cummax()
    trades_df['drawdown'] = trades_df['equity'] - trades_df['peak']
    max_drawdown = trades_df['drawdown'].min()
    
    daily_returns = trades_df.groupby(trades_df['entry_time'].dt.date)['pnl_dollars'].sum()
    if len(daily_returns) > 1 and daily_returns.std() > 0:
        sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
    else:
        sharpe = 0
    
    # Breakeven analysis
    tp_value = (TAKE_PROFIT_POINTS - SLIPPAGE_SPREAD_POINTS) * POINT_VALUE - COMMISSION
    sl_value = (-STOP_LOSS_POINTS - SLIPPAGE_SPREAD_POINTS) * POINT_VALUE - COMMISSION
    breakeven_wr = abs(sl_value) / (tp_value + abs(sl_value)) * 100
    
    return {
        'total_trades': total_trades,
        'winners': winners,
        'losers': total_trades - winners,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'max_drawdown': max_drawdown,
        'sharpe': sharpe,
        'final_equity': trades_df['equity'].iloc[-1],
        'breakeven_wr': breakeven_wr
    }

def print_kill_list(rejected_df, top_n=10):
    """Print the Kill List (top rejected trades)."""
    print("\n" + "="*80)
    print("KILL LIST: Top 10 Rejected Trades (Most Extreme Velocity)")
    print("="*80)
    
    # Sort by velocity (most negative first)
    sorted_rejected = rejected_df.sort_values('Velocity_5m', ascending=True).head(top_n)
    
    print(f"\n{'Date':<12} | {'Time (UTC)':<10} | {'Price':>12} | {'Velocity':>12} | {'Reason':<25}")
    print("-"*80)
    
    for idx, row in sorted_rejected.iterrows():
        date_str = idx.strftime('%Y-%m-%d')
        time_str = idx.strftime('%H:%M:%S')
        print(f"{date_str:<12} | {time_str:<10} | {row['close']:>12.2f} | {row['Velocity_5m']:>12.2f} | {row['RejectReason']:<25}")
    
    return sorted_rejected

def main():
    """Execute sanity filter test."""
    
    # Load and split data
    df = load_data()
    train_raw, test_raw = split_data(df)
    
    # Prepare training data
    print(f"\n[4/8] Preparing data...")
    train_golden = filter_golden_window(train_raw)
    train_golden = calculate_features(train_golden)
    train_golden = calculate_target(train_golden)
    clf, feature_cols = train_model(train_golden)
    
    # Prepare test data
    test_golden = filter_golden_window(test_raw)
    test_golden = calculate_features(test_golden)
    print(f"      2025 Golden Window rows: {len(test_golden):,}")
    
    # Apply model with sanity filter
    accepted_df, rejected_df, total_signals = apply_model_with_filter(test_golden, clf, feature_cols)
    
    # Run backtest on accepted only
    trades_df = run_backtest_on_accepted(test_golden, accepted_df)
    
    if len(trades_df) == 0:
        print("ERROR: No trades!")
        return
    
    # Calculate metrics
    print(f"\n[7/8] Calculating metrics...")
    metrics = calculate_metrics(trades_df)
    
    # Print results
    print("\n" + "="*80)
    print("SANITY FILTER TEST RESULTS")
    print("="*80)
    
    print(f"\n{'VOLUME STATISTICS':^60}")
    print("-"*60)
    print(f"Total Signals Detected:  {total_signals:,}")
    print(f"Total Signals REJECTED:  {len(rejected_df):,}")
    print(f"Total Signals TRADED:    {len(accepted_df):,}")
    print(f"Rejection Rate:          {len(rejected_df)/total_signals*100:.1f}%")
    
    print(f"\n{'PERFORMANCE (Accepted Trades Only)':^60}")
    print("-"*60)
    print(f"Starting Capital:        ${STARTING_CAPITAL:,.2f}")
    print(f"Final Equity:            ${metrics['final_equity']:,.2f}")
    print(f"Total P&L:               ${metrics['total_pnl']:,.2f}")
    print(f"Total Return:            {(metrics['final_equity']/STARTING_CAPITAL - 1)*100:.1f}%")
    print(f"Max Drawdown:            ${metrics['max_drawdown']:,.2f}")
    print(f"Sharpe Ratio:            {metrics['sharpe']:.2f}")
    
    print(f"\n{'TRADE STATISTICS':^60}")
    print("-"*60)
    print(f"Total Trades:            {metrics['total_trades']:,}")
    print(f"Winners:                 {metrics['winners']:,}")
    print(f"Losers:                  {metrics['losers']:,}")
    print(f"Win Rate:                {metrics['win_rate']:.1f}%")
    print(f"Breakeven Required:      {metrics['breakeven_wr']:.1f}%")
    
    edge_above_breakeven = metrics['win_rate'] - metrics['breakeven_wr']
    print(f"Edge Above Breakeven:    {'+' if edge_above_breakeven > 0 else ''}{edge_above_breakeven:.1f}%")
    
    # Print Kill List
    kill_list = print_kill_list(rejected_df, top_n=10)
    
    # Plot equity curve
    print(f"\n[8/8] Generating equity curve...")
    
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(trades_df['entry_time'], trades_df['equity'], 'b-', linewidth=1.5)
    ax.axhline(y=STARTING_CAPITAL, color='gray', linestyle='--', alpha=0.5)
    ax.fill_between(trades_df['entry_time'], STARTING_CAPITAL, trades_df['equity'],
                    where=trades_df['equity'] >= STARTING_CAPITAL, color='green', alpha=0.3)
    ax.fill_between(trades_df['entry_time'], STARTING_CAPITAL, trades_df['equity'],
                    where=trades_df['equity'] < STARTING_CAPITAL, color='red', alpha=0.3)
    
    ax.set_title(f'MIDAS Sanity Filter Test: 2025 Equity (Velocity > {VELOCITY_REJECT_THRESHOLD} only)', 
                 fontsize=14, fontweight='bold')
    ax.set_ylabel('Equity ($)', fontsize=12)
    ax.set_xlabel('Date', fontsize=12)
    ax.grid(True, alpha=0.3)
    
    textstr = f"Sanity Filter:\n"
    textstr += f"Rejected: {len(rejected_df):,}\n"
    textstr += f"Traded: {metrics['total_trades']:,}\n"
    textstr += f"P&L: ${metrics['total_pnl']:,.0f}\n"
    textstr += f"Win Rate: {metrics['win_rate']:.1f}%"
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    plot_path = OUTPUT_DIR / "midas_equity_curve_SANITY_FILTER.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"      Saved: {plot_path}")
    plt.close()
    
    # Generate report
    report = f"""# MIDAS Sanity Filter Test: Rejected Trade Audit

## Objective

Test the Sanity Filter and record every blocked signal to inspect data quality.

---

## Filter Logic

```
IF Velocity_5m < {VELOCITY_REJECT_THRESHOLD}: REJECT (Ghost Trade)
IF Velocity_5m >= {VELOCITY_REJECT_THRESHOLD}: ACCEPT (Execute)
```

---

## Volume Statistics

| Metric | Value |
|--------|-------|
| **Total Signals Detected** | {total_signals:,} |
| **Signals REJECTED** | {len(rejected_df):,} |
| **Signals TRADED** | {len(accepted_df):,} |
| Rejection Rate | {len(rejected_df)/total_signals*100:.1f}% |

---

## Performance (Accepted Trades Only)

| Metric | Value |
|--------|-------|
| Starting Capital | ${STARTING_CAPITAL:,.2f} |
| **Final Equity** | **${metrics['final_equity']:,.2f}** |
| **Total P&L** | **${metrics['total_pnl']:,.2f}** |
| Total Return | {(metrics['final_equity']/STARTING_CAPITAL - 1)*100:.1f}% |
| Max Drawdown | ${metrics['max_drawdown']:,.2f} |
| Sharpe Ratio | {metrics['sharpe']:.2f} |

---

## Trade Statistics

| Metric | Value |
|--------|-------|
| Total Trades | {metrics['total_trades']:,} |
| Winners | {metrics['winners']:,} |
| Losers | {metrics['losers']:,} |
| **Win Rate** | **{metrics['win_rate']:.1f}%** |
| Breakeven Required | {metrics['breakeven_wr']:.1f}% |
| **Edge** | **{'+' if edge_above_breakeven > 0 else ''}{edge_above_breakeven:.1f}%** |

---

## KILL LIST: Top 10 Rejected Trades (Ghost Trades)

These trades were blocked by the sanity filter due to extreme velocity values.

| Date | Time (UTC) | Price | Velocity | Reason |
|------|------------|-------|----------|--------|
"""
    
    for idx, row in kill_list.iterrows():
        date_str = idx.strftime('%Y-%m-%d')
        time_str = idx.strftime('%H:%M:%S')
        report += f"| {date_str} | {time_str} | {row['close']:.2f} | {row['Velocity_5m']:.2f} | {row['RejectReason']} |\n"
    
    report += f"""
---

## Velocity Distribution of Rejected Trades

| Velocity Range | Count |
|----------------|-------|
| < -200 | {(rejected_df['Velocity_5m'] < -200).sum():,} |
| -200 to -180 | {((rejected_df['Velocity_5m'] >= -200) & (rejected_df['Velocity_5m'] < -180)).sum():,} |
| -180 to -160 | {((rejected_df['Velocity_5m'] >= -180) & (rejected_df['Velocity_5m'] < -160)).sum():,} |
| -160 to -150 | {((rejected_df['Velocity_5m'] >= -160) & (rejected_df['Velocity_5m'] < -150)).sum():,} |

---

## Equity Curve

![Sanity Filter Equity Curve](midas_equity_curve_SANITY_FILTER.png)

---

## Conclusion

{"The sanity filter successfully identifies and blocks ghost trades with extreme velocity values. Even after removing these suspicious signals, the strategy remains profitable." if metrics['total_pnl'] > 0 else "The strategy underperforms after applying the sanity filter."}

---

*Generated by Magellan Quant Research - Forensic Auditor*  
*Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    report_path = OUTPUT_DIR / "MIDAS_SANITY_FILTER_RESULTS.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n[SAVED] Report: {report_path}")
    
    # Save rejected trades
    rejected_path = OUTPUT_DIR / "rejected_trades_kill_list.csv"
    rejected_df.to_csv(rejected_path)
    print(f"[SAVED] Kill List: {rejected_path}")
    
    # Save accepted trades
    trades_path = OUTPUT_DIR / "midas_trades_SANITY_FILTER.csv"
    trades_df.to_csv(trades_path, index=False)
    print(f"[SAVED] Trades: {trades_path}")
    
    print("\n" + "="*80)
    print("SANITY FILTER TEST COMPLETE")
    print("="*80)
    
    return metrics, trades_df, rejected_df

if __name__ == "__main__":
    metrics, trades, rejected = main()
