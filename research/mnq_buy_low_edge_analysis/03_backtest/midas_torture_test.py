"""
=============================================================================
MIDAS PROTOCOL: TORTURE TEST (Maximum Friction)
=============================================================================

OBJECTIVE: DESTROY THE STRATEGY. Apply maximum friction to see if edge survives.

CONSTRAINTS:
- Data: 2025 ONLY (Out-of-Sample)
- Commission: $2.50 per trade (round trip)
- Slippage + Spread: 2.0 points ($4.00) per trade
- Total Cost: Every trade starts -$6.50 in the hole
- Worst-Case Intra-Bar: Both TP & SL hit = SL

Author: Magellan Quant Research (Pessimist Mode)
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
# CONFIGURATION (TORTURE MODE)
# =============================================================================

MNQ_CSV = Path(r"A:\1\Magellan\data\cache\futures\MNQ\glbx-mdp3-20210129-20260128.ohlcv-1m.csv")
OUTPUT_DIR = Path(r"a:\1\Magellan\research\mnq_buy_low_edge_analysis\03_backtest")

# Data split
TRAIN_END = "2024-12-31"
TEST_START = "2025-01-01"

# Strategy parameters
GOLDEN_HOUR_START = 2
GOLDEN_HOUR_END = 6

# Trade parameters (TORTURE MODE - MAXIMUM FRICTION)
TAKE_PROFIT_POINTS = 40
STOP_LOSS_POINTS = 12
SLIPPAGE_SPREAD_POINTS = 2.0  # 2.0 points = $4.00 per trade
POINT_VALUE = 2.0             # MNQ: $2 per point
COMMISSION = 2.50             # $2.50 per trade (round trip)

# Total cost per trade: Slippage ($4) + Commission ($2.50) = $6.50
TOTAL_COST_PER_TRADE = (SLIPPAGE_SPREAD_POINTS * POINT_VALUE) + COMMISSION

STARTING_CAPITAL = 5000
MAX_HOLD_TIME = 60

# =============================================================================
# DATA FUNCTIONS
# =============================================================================

def load_data():
    """Load full dataset."""
    print("="*80)
    print("MIDAS PROTOCOL: TORTURE TEST (Maximum Friction)")
    print("="*80)
    print("\nFRICTION SETTINGS:")
    print(f"  - Commission:        ${COMMISSION} per trade")
    print(f"  - Slippage + Spread: {SLIPPAGE_SPREAD_POINTS} points (${SLIPPAGE_SPREAD_POINTS * POINT_VALUE})")
    print(f"  - TOTAL COST:        ${TOTAL_COST_PER_TRADE} per trade")
    print(f"  - Every trade starts ${TOTAL_COST_PER_TRADE} IN THE HOLE")
    
    print(f"\n[1/7] Loading data...")
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
    print(f"\n[2/7] Splitting data...")
    train = df[df.index <= TRAIN_END].copy()
    test = df[df.index >= TEST_START].copy()
    print(f"      Training: {train.index.min()} to {train.index.max()}")
    print(f"      Testing:  {test.index.min()} to {test.index.max()} ({len(test):,} rows)")
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
    """Train on 2021-2024 data ONLY."""
    print(f"\n[3/7] Training model on 2021-2024 (BLIND to 2025)...")
    
    feature_cols = ['Dist_EMA200', 'Wick_Ratio', 'Velocity_5m', 'ATR_Ratio']
    df_clean = train_df.dropna(subset=feature_cols + ['Target'])
    
    X = df_clean[feature_cols]
    y = df_clean['Target'].astype(int)
    
    clf = DecisionTreeClassifier(max_depth=4, min_samples_leaf=50, random_state=42)
    clf.fit(X, y)
    
    print(f"      Training samples: {len(X):,}")
    return clf, feature_cols

def apply_model(df, clf, feature_cols):
    """Apply trained model to identify signals."""
    df = df.copy()
    df_clean = df.dropna(subset=feature_cols)
    X = df_clean[feature_cols]
    df_clean['Signal'] = clf.predict(X) == 1
    
    # Determine setup type based on velocity
    df_clean['Setup'] = np.where(df_clean['Velocity_5m'] <= -67, 'Crash', 'Quiet')
    
    return df_clean

# =============================================================================
# TORTURE TEST EXECUTION
# =============================================================================

def simulate_trade_torture(df, signal_idx, entry_price, velocity):
    """
    TORTURE MODE trade simulation.
    - Entry suffers 2.0 points slippage
    - If both TP and SL hit, assume SL FIRST
    """
    entry_loc = df.index.get_loc(signal_idx) + 1
    
    if entry_loc >= len(df):
        return None, 0, 'SKIP', None
    
    # Entry price after slippage (hurts longs)
    actual_entry = entry_price + SLIPPAGE_SPREAD_POINTS
    tp_price = actual_entry + TAKE_PROFIT_POINTS
    sl_price = actual_entry - STOP_LOSS_POINTS
    
    for i in range(entry_loc, min(entry_loc + MAX_HOLD_TIME, len(df))):
        bar = df.iloc[i]
        bars_held = i - entry_loc + 1
        
        sl_hit = bar['low'] <= sl_price
        tp_hit = bar['high'] >= tp_price
        
        # WORST CASE: Both hit = SL FIRST
        if sl_hit and tp_hit:
            pnl_points = -STOP_LOSS_POINTS - SLIPPAGE_SPREAD_POINTS
            return pnl_points, bars_held, 'SL', df.index[i]
        
        if sl_hit:
            pnl_points = -STOP_LOSS_POINTS - SLIPPAGE_SPREAD_POINTS
            return pnl_points, bars_held, 'SL', df.index[i]
        
        if tp_hit:
            pnl_points = TAKE_PROFIT_POINTS - SLIPPAGE_SPREAD_POINTS
            return pnl_points, bars_held, 'TP', df.index[i]
    
    # Timeout
    last_idx = min(entry_loc + MAX_HOLD_TIME - 1, len(df) - 1)
    last_bar = df.iloc[last_idx]
    exit_price = last_bar['close'] - SLIPPAGE_SPREAD_POINTS
    pnl_points = exit_price - actual_entry
    return pnl_points, MAX_HOLD_TIME, 'TO', df.index[last_idx]

def run_torture_test(df):
    """Run the torture test backtest."""
    print(f"\n[5/7] Running TORTURE TEST on 2025 data...")
    print(f"      (Every trade starts ${TOTAL_COST_PER_TRADE} in the hole)")
    
    signals_df = df[df['Signal'] == True].copy()
    
    trades = []
    last_exit_bar = -1
    
    for signal_idx in signals_df.index:
        signal_loc = df.index.get_loc(signal_idx)
        
        if signal_loc <= last_exit_bar:
            continue
        
        entry_loc = signal_loc + 1
        if entry_loc >= len(df):
            continue
        
        entry_bar_idx = df.index[entry_loc]
        entry_price = df.iloc[entry_loc]['open']
        velocity = df.loc[signal_idx, 'Velocity_5m']
        setup = df.loc[signal_idx, 'Setup']
        
        result = simulate_trade_torture(df, signal_idx, entry_price, velocity)
        if result[0] is None:
            continue
        
        pnl_points, hold_time, exit_type, exit_time = result
        
        # PnL in dollars (subtract commission)
        pnl_dollars = (pnl_points * POINT_VALUE) - COMMISSION
        
        trades.append({
            'signal_time': signal_idx,
            'entry_time': entry_bar_idx,
            'exit_time': exit_time,
            'entry_price': entry_price,
            'actual_entry': entry_price + SLIPPAGE_SPREAD_POINTS,
            'setup': setup,
            'velocity_5m': velocity,
            'pnl_points': pnl_points,
            'pnl_dollars': pnl_dollars,
            'hold_time': hold_time,
            'exit_type': exit_type
        })
        
        last_exit_bar = entry_loc + hold_time
    
    trades_df = pd.DataFrame(trades)
    print(f"      Total trades: {len(trades_df):,}")
    
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
    
    avg_pnl = trades_df['pnl_dollars'].mean()
    avg_winner = trades_df[trades_df['pnl_dollars'] > 0]['pnl_dollars'].mean() if winners > 0 else 0
    avg_loser = trades_df[trades_df['pnl_dollars'] <= 0]['pnl_dollars'].mean() if (total_trades - winners) > 0 else 0
    
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
        'avg_pnl': avg_pnl,
        'avg_winner': avg_winner,
        'avg_loser': avg_loser,
        'max_drawdown': max_drawdown,
        'sharpe': sharpe,
        'final_equity': trades_df['equity'].iloc[-1],
        'tp_value': tp_value,
        'sl_value': sl_value,
        'breakeven_wr': breakeven_wr
    }

def print_phantom_validator(trades_df):
    """Print first 3 and last 3 trades for cross-reference."""
    print("\n" + "="*80)
    print("PHANTOM VALIDATOR: Trade Calibration Check")
    print("="*80)
    print("\nCross-reference these with your TradingView chart to validate timestamps.")
    print("\nFIRST 3 TRADES:")
    print("-"*100)
    print(f"{'Date':<12} | {'Time (UTC)':<10} | {'Entry Price':>12} | {'Setup':<8} | {'Velocity_5m':>12} | {'Result':<6}")
    print("-"*100)
    
    for i, row in trades_df.head(3).iterrows():
        date_str = row['entry_time'].strftime('%Y-%m-%d')
        time_str = row['entry_time'].strftime('%H:%M:%S')
        print(f"{date_str:<12} | {time_str:<10} | {row['entry_price']:>12.2f} | {row['setup']:<8} | {row['velocity_5m']:>12.2f} | {row['exit_type']:<6}")
    
    print("\nLAST 3 TRADES:")
    print("-"*100)
    print(f"{'Date':<12} | {'Time (UTC)':<10} | {'Entry Price':>12} | {'Setup':<8} | {'Velocity_5m':>12} | {'Result':<6}")
    print("-"*100)
    
    for i, row in trades_df.tail(3).iterrows():
        date_str = row['entry_time'].strftime('%Y-%m-%d')
        time_str = row['entry_time'].strftime('%H:%M:%S')
        print(f"{date_str:<12} | {time_str:<10} | {row['entry_price']:>12.2f} | {row['setup']:<8} | {row['velocity_5m']:>12.2f} | {row['exit_type']:<6}")

def main():
    """Execute Torture Test."""
    
    # Load and split data
    df = load_data()
    train_raw, test_raw = split_data(df)
    
    # Prepare training data
    print(f"\n[3/7] Training model on 2021-2024 (BLIND to 2025)...")
    train_golden = filter_golden_window(train_raw)
    train_golden = calculate_features(train_golden)
    train_golden = calculate_target(train_golden)
    clf, feature_cols = train_model(train_golden)
    
    # Prepare 2025 test data
    print(f"\n[4/7] Preparing 2025 test data...")
    test_golden = filter_golden_window(test_raw)
    test_golden = calculate_features(test_golden)
    print(f"      2025 Golden Window rows: {len(test_golden):,}")
    
    # Apply model
    test_with_signals = apply_model(test_golden, clf, feature_cols)
    print(f"      Signals found: {test_with_signals['Signal'].sum():,}")
    
    # Run torture test
    trades_df = run_torture_test(test_with_signals)
    
    if len(trades_df) == 0:
        print("ERROR: No trades!")
        return
    
    # Calculate metrics
    print(f"\n[6/7] Calculating metrics...")
    metrics = calculate_metrics(trades_df)
    
    # Print results
    print("\n" + "="*80)
    print("TORTURE TEST RESULTS")
    print("="*80)
    
    print(f"\n{'FRICTION APPLIED':^60}")
    print("-"*60)
    print(f"Commission per trade:    ${COMMISSION}")
    print(f"Slippage + Spread:       {SLIPPAGE_SPREAD_POINTS} pts (${SLIPPAGE_SPREAD_POINTS * POINT_VALUE})")
    print(f"TOTAL COST per trade:    ${TOTAL_COST_PER_TRADE}")
    print(f"Breakeven Win Rate:      {metrics['breakeven_wr']:.1f}%")
    
    print(f"\n{'2025 TORTURE TEST PERFORMANCE':^60}")
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
    print(f"Avg P&L per Trade:       ${metrics['avg_pnl']:.2f}")
    print(f"Avg Winner:              ${metrics['avg_winner']:.2f}")
    print(f"Avg Loser:               ${metrics['avg_loser']:.2f}")
    
    # Edge Survival Analysis
    print(f"\n{'EDGE SURVIVAL ANALYSIS':^60}")
    print("-"*60)
    edge_above_breakeven = metrics['win_rate'] - metrics['breakeven_wr']
    if edge_above_breakeven > 0:
        print(f"Win Rate:                {metrics['win_rate']:.1f}%")
        print(f"Breakeven Required:      {metrics['breakeven_wr']:.1f}%")
        print(f"EDGE ABOVE BREAKEVEN:    +{edge_above_breakeven:.1f}%")
        print(f"STATUS:                  EDGE SURVIVES")
    else:
        print(f"Win Rate:                {metrics['win_rate']:.1f}%")
        print(f"Breakeven Required:      {metrics['breakeven_wr']:.1f}%")
        print(f"SHORTFALL:               {edge_above_breakeven:.1f}%")
        print(f"STATUS:                  EDGE DESTROYED")
    
    # Phantom Validator
    print_phantom_validator(trades_df)
    
    # Plot equity curve
    print(f"\n[7/7] Generating equity curve...")
    
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(trades_df['entry_time'], trades_df['equity'], 'b-', linewidth=1.5)
    ax.axhline(y=STARTING_CAPITAL, color='gray', linestyle='--', alpha=0.5)
    ax.fill_between(trades_df['entry_time'], STARTING_CAPITAL, trades_df['equity'],
                    where=trades_df['equity'] >= STARTING_CAPITAL, color='green', alpha=0.3)
    ax.fill_between(trades_df['entry_time'], STARTING_CAPITAL, trades_df['equity'],
                    where=trades_df['equity'] < STARTING_CAPITAL, color='red', alpha=0.3)
    
    ax.set_title(f'MIDAS TORTURE TEST: 2025 Equity Curve (${TOTAL_COST_PER_TRADE}/trade friction)', 
                 fontsize=14, fontweight='bold')
    ax.set_ylabel('Equity ($)', fontsize=12)
    ax.set_xlabel('Date', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    textstr = f"TORTURE TEST:\n"
    textstr += f"Friction: ${TOTAL_COST_PER_TRADE}/trade\n"
    textstr += f"P&L: ${metrics['total_pnl']:,.0f}\n"
    textstr += f"Win Rate: {metrics['win_rate']:.1f}%\n"
    textstr += f"Edge: +{edge_above_breakeven:.1f}%"
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    plot_path = OUTPUT_DIR / "midas_equity_curve_TORTURE.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"      Saved: {plot_path}")
    plt.close()
    
    # Generate report
    report = f"""# MIDAS TORTURE TEST: Maximum Friction Backtest

## Objective

**DESTROY THE STRATEGY.** Apply maximum friction to see if edge survives.

---

## Friction Applied

| Parameter | Value |
|-----------|-------|
| Commission | ${COMMISSION} per trade |
| Slippage + Spread | {SLIPPAGE_SPREAD_POINTS} points (${SLIPPAGE_SPREAD_POINTS * POINT_VALUE}) |
| **TOTAL COST** | **${TOTAL_COST_PER_TRADE} per trade** |
| Breakeven Win Rate | {metrics['breakeven_wr']:.1f}% |

Every trade starts **${TOTAL_COST_PER_TRADE} in the hole**.

---

## 2025 Torture Test Results

| Metric | Value |
|--------|-------|
| Starting Capital | ${STARTING_CAPITAL:,.2f} |
| Final Equity | ${metrics['final_equity']:,.2f} |
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
| Avg P&L per Trade | ${metrics['avg_pnl']:.2f} |

---

## Edge Survival Analysis

| Metric | Value |
|--------|-------|
| Win Rate | {metrics['win_rate']:.1f}% |
| Breakeven Required | {metrics['breakeven_wr']:.1f}% |
| **Edge Above Breakeven** | **{'+' if edge_above_breakeven > 0 else ''}{edge_above_breakeven:.1f}%** |
| **Status** | **{'EDGE SURVIVES' if edge_above_breakeven > 0 else 'EDGE DESTROYED'}** |

---

## Phantom Validator (Calibration Check)

Cross-reference these trades with TradingView to validate timestamps.

### First 3 Trades

| Date | Time (UTC) | Entry Price | Setup | Velocity_5m | Result |
|------|------------|-------------|-------|-------------|--------|
"""
    
    for i, row in trades_df.head(3).iterrows():
        date_str = row['entry_time'].strftime('%Y-%m-%d')
        time_str = row['entry_time'].strftime('%H:%M:%S')
        report += f"| {date_str} | {time_str} | {row['entry_price']:.2f} | {row['setup']} | {row['velocity_5m']:.2f} | {row['exit_type']} |\n"
    
    report += f"""
### Last 3 Trades

| Date | Time (UTC) | Entry Price | Setup | Velocity_5m | Result |
|------|------------|-------------|-------|-------------|--------|
"""
    
    for i, row in trades_df.tail(3).iterrows():
        date_str = row['entry_time'].strftime('%Y-%m-%d')
        time_str = row['entry_time'].strftime('%H:%M:%S')
        report += f"| {date_str} | {time_str} | {row['entry_price']:.2f} | {row['setup']} | {row['velocity_5m']:.2f} | {row['exit_type']} |\n"
    
    report += f"""
---

## Equity Curve

![Torture Test Equity Curve](midas_equity_curve_TORTURE.png)

---

## Conclusion

{"**THE EDGE SURVIVES.** Even with maximum friction ($6.50/trade), the strategy remains profitable." if edge_above_breakeven > 0 and metrics['total_pnl'] > 0 else "**THE EDGE IS DESTROYED.** Friction costs eliminate profitability."}

---

*Generated by Magellan Quant Research - Pessimist Mode*  
*Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    report_path = OUTPUT_DIR / "MIDAS_TORTURE_TEST_RESULTS.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n[SAVED] Report: {report_path}")
    
    # Save trades
    trades_path = OUTPUT_DIR / "midas_trades_TORTURE.csv"
    trades_df.to_csv(trades_path, index=False)
    print(f"[SAVED] Trades: {trades_path}")
    
    print("\n" + "="*80)
    print("TORTURE TEST COMPLETE")
    print("="*80)
    
    return metrics, trades_df

if __name__ == "__main__":
    metrics, trades = main()
