"""
=============================================================================
MIDAS PROTOCOL: Walk-Forward Validation (Out-of-Sample Test)
=============================================================================

WALK-FORWARD PROTOCOL:
- TRAINING SET: Jan 2021 - Dec 2024 (Learn rules)
- TESTING SET:  Jan 2025 - Present (Validate on unseen data)
- CRUCIAL: Algorithm cannot see 2025 data while learning rules

Author: Magellan Quant Research (Validation Mode)
Date: 2026-01-30
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.tree import DecisionTreeClassifier, export_text
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

# Trade parameters (STRICT)
TAKE_PROFIT_POINTS = 40
STOP_LOSS_POINTS = 12
SLIPPAGE_POINTS = 0.5
POINT_VALUE = 2.0
COMMISSION = 1.0
STARTING_CAPITAL = 5000
MAX_HOLD_TIME = 60

# =============================================================================
# DATA LOADING
# =============================================================================

def load_data():
    """Load full MNQ dataset."""
    print("="*80)
    print("MIDAS PROTOCOL: Walk-Forward Validation")
    print("="*80)
    print(f"\nTRAINING: Jan 2021 - Dec 2024")
    print(f"TESTING:  Jan 2025 - Present (OUT-OF-SAMPLE)")
    
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
    
    print(f"      Total rows: {len(df_agg):,}")
    print(f"      Date range: {df_agg.index.min()} to {df_agg.index.max()}")
    
    return df_agg

def split_data(df):
    """Split into training and testing sets."""
    print(f"\n[2/8] Splitting data...")
    
    train = df[df.index <= TRAIN_END].copy()
    test = df[df.index >= TEST_START].copy()
    
    print(f"      Training: {train.index.min()} to {train.index.max()} ({len(train):,} rows)")
    print(f"      Testing:  {test.index.min()} to {test.index.max()} ({len(test):,} rows)")
    
    return train, test

def filter_golden_window(df):
    """Filter to Golden Window."""
    df['hour'] = df.index.hour
    mask = (df['hour'] >= GOLDEN_HOUR_START) & (df['hour'] < GOLDEN_HOUR_END)
    return df[mask].copy()

def calculate_features(df):
    """Calculate all features."""
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
    
    # Wick ratio
    range_hl = df['high'] - df['low']
    df['Wick_Ratio'] = (df['close'] - df['low']) / range_hl
    df['Wick_Ratio'] = df['Wick_Ratio'].replace([np.inf, -np.inf], np.nan).fillna(0.5)
    
    return df

def calculate_target(df):
    """Calculate Golden Target with 30-min forward window."""
    df = df.copy()
    
    df['future_max_high'] = df['high'].shift(-1).rolling(window=30, min_periods=30).max().shift(-29)
    df['future_min_low'] = df['low'].shift(-1).rolling(window=30, min_periods=30).min().shift(-29)
    df['MFE'] = df['future_max_high'] - df['close']
    df['MAE'] = df['close'] - df['future_min_low']
    df['Target'] = (df['MFE'] >= 40) & (df['MAE'] <= 12)
    
    return df

# =============================================================================
# DECISION TREE TRAINING (ON TRAINING DATA ONLY)
# =============================================================================

def train_decision_tree(train_df):
    """Train Decision Tree on training data ONLY."""
    print(f"\n[4/8] Training Decision Tree on 2021-2024 data ONLY...")
    
    feature_cols = ['Dist_EMA200', 'Wick_Ratio', 'Velocity_5m', 'ATR_Ratio']
    
    df_clean = train_df.dropna(subset=feature_cols + ['Target'])
    X = df_clean[feature_cols]
    y = df_clean['Target'].astype(int)
    
    print(f"      Training samples: {len(X):,}")
    print(f"      Base win rate: {y.mean()*100:.2f}%")
    
    clf = DecisionTreeClassifier(
        max_depth=4,
        min_samples_leaf=50,
        random_state=42
    )
    clf.fit(X, y)
    
    # Print tree
    print(f"\n      LEARNED DECISION TREE:")
    print("-"*60)
    tree_text = export_text(clf, feature_names=feature_cols)
    print(tree_text)
    
    # Find best leaves
    leaf_ids = clf.apply(X)
    best_leaves = []
    
    for leaf_id in np.unique(leaf_ids):
        mask = leaf_ids == leaf_id
        samples = mask.sum()
        wins = y[mask].sum()
        rate = wins / samples if samples > 0 else 0
        
        if rate >= 0.50 and samples >= 50:
            best_leaves.append({
                'leaf_id': leaf_id,
                'samples': samples,
                'win_rate': rate
            })
    
    best_leaves = sorted(best_leaves, key=lambda x: x['win_rate'], reverse=True)
    
    print(f"\n      HIGH-PROBABILITY LEAVES (from training):")
    print("-"*60)
    for leaf in best_leaves[:5]:
        print(f"      Leaf {leaf['leaf_id']}: {leaf['win_rate']:.1%} win rate ({leaf['samples']} samples)")
    
    return clf, feature_cols, best_leaves

def extract_rules_from_tree(clf, feature_cols):
    """Extract the specific rules learned from training."""
    tree = clf.tree_
    
    # Find the thresholds at the first few splits
    rules = {}
    
    def traverse(node, path=[]):
        if tree.feature[node] == -2:  # Leaf
            return
        
        feature_idx = tree.feature[node]
        threshold = tree.threshold[node]
        feature_name = feature_cols[feature_idx]
        
        if feature_name not in rules:
            rules[feature_name] = []
        rules[feature_name].append(threshold)
        
        traverse(tree.children_left[node], path + [(feature_name, '<=', threshold)])
        traverse(tree.children_right[node], path + [(feature_name, '>', threshold)])
    
    traverse(0)
    
    # Summarize
    print(f"\n      LEARNED THRESHOLDS:")
    print("-"*60)
    for feat, thresholds in rules.items():
        print(f"      {feat}: {[round(t, 2) for t in sorted(set(thresholds))]}")
    
    return rules

def apply_learned_rules(df, clf, feature_cols):
    """Apply the learned rules to identify signals."""
    df = df.copy()
    df_clean = df.dropna(subset=feature_cols)
    
    X = df_clean[feature_cols]
    
    # Get leaf predictions
    predictions = clf.predict(X)
    leaf_ids = clf.apply(X)
    
    # Mark signals where tree predicts class 1
    df_clean['Signal'] = predictions == 1
    
    # Also mark which setup based on features (for reporting)
    df_clean['Setup'] = 'Tree'
    
    return df_clean

# =============================================================================
# STRICT BACKTEST
# =============================================================================

def simulate_trade_strict(df, signal_idx, entry_price):
    """Strict trade simulation."""
    entry_loc = df.index.get_loc(signal_idx) + 1
    
    if entry_loc >= len(df):
        return None, 0, 'SKIP'
    
    actual_entry_price = entry_price + SLIPPAGE_POINTS
    tp_price = actual_entry_price + TAKE_PROFIT_POINTS
    sl_price = actual_entry_price - STOP_LOSS_POINTS
    
    for i in range(entry_loc, min(entry_loc + MAX_HOLD_TIME, len(df))):
        bar = df.iloc[i]
        bars_held = i - entry_loc + 1
        
        sl_hit = bar['low'] <= sl_price
        tp_hit = bar['high'] >= tp_price
        
        if sl_hit and tp_hit:
            return -STOP_LOSS_POINTS - SLIPPAGE_POINTS, bars_held, 'SL'
        if sl_hit:
            return -STOP_LOSS_POINTS - SLIPPAGE_POINTS, bars_held, 'SL'
        if tp_hit:
            return TAKE_PROFIT_POINTS - SLIPPAGE_POINTS, bars_held, 'TP'
    
    last_bar = df.iloc[min(entry_loc + MAX_HOLD_TIME - 1, len(df) - 1)]
    exit_price = last_bar['close'] - SLIPPAGE_POINTS
    return exit_price - actual_entry_price, MAX_HOLD_TIME, 'TO'

def run_backtest(df, label=""):
    """Run strict backtest."""
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
        
        result = simulate_trade_strict(df, signal_idx, entry_price)
        if result[0] is None:
            continue
        
        pnl_points, hold_time, exit_type = result
        pnl_dollars = (pnl_points * POINT_VALUE) - COMMISSION
        
        trades.append({
            'entry_time': entry_bar_idx,
            'entry_price': entry_price + SLIPPAGE_POINTS,
            'pnl_points': pnl_points,
            'pnl_dollars': pnl_dollars,
            'hold_time': hold_time,
            'exit_type': exit_type
        })
        
        last_exit_bar = entry_loc + hold_time
    
    if len(trades) == 0:
        return pd.DataFrame()
    
    trades_df = pd.DataFrame(trades)
    return trades_df

def calculate_metrics(trades_df, label=""):
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
    
    return {
        'total_trades': total_trades,
        'winners': winners,
        'losers': total_trades - winners,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'max_drawdown': max_drawdown,
        'sharpe': sharpe,
        'final_equity': trades_df['equity'].iloc[-1]
    }

# =============================================================================
# MAIN WALK-FORWARD
# =============================================================================

def main():
    """Execute Walk-Forward Validation."""
    
    # Load full data
    df = load_data()
    
    # Split into train/test
    train_raw, test_raw = split_data(df)
    
    # =========================================================================
    # PHASE 1: TRAIN ON 2021-2024
    # =========================================================================
    print("\n" + "="*80)
    print("PHASE 1: TRAINING (2021-2024)")
    print("="*80)
    
    print(f"\n[3/8] Preparing training data...")
    train_golden = filter_golden_window(train_raw)
    train_golden = calculate_features(train_golden)
    train_golden = calculate_target(train_golden)
    print(f"      Training rows (Golden Window): {len(train_golden):,}")
    
    # Train Decision Tree
    clf, feature_cols, best_leaves = train_decision_tree(train_golden)
    rules = extract_rules_from_tree(clf, feature_cols)
    
    # =========================================================================
    # PHASE 2: TEST ON 2025+ (OUT-OF-SAMPLE)
    # =========================================================================
    print("\n" + "="*80)
    print("PHASE 2: OUT-OF-SAMPLE TESTING (2025+)")
    print("="*80)
    
    print(f"\n[5/8] Preparing test data...")
    test_golden = filter_golden_window(test_raw)
    test_golden = calculate_features(test_golden)
    print(f"      Test rows (Golden Window): {len(test_golden):,}")
    
    print(f"\n[6/8] Applying LEARNED rules to 2025 data...")
    test_with_signals = apply_learned_rules(test_golden, clf, feature_cols)
    signal_count = test_with_signals['Signal'].sum()
    print(f"      Signals in 2025: {signal_count:,}")
    
    print(f"\n[7/8] Running STRICT backtest on 2025...")
    test_trades = run_backtest(test_with_signals, "2025 OOS")
    
    if len(test_trades) == 0:
        print("ERROR: No trades in test period!")
        return
    
    test_metrics = calculate_metrics(test_trades, "2025 OOS")
    
    # =========================================================================
    # PHASE 3: RESULTS
    # =========================================================================
    print("\n" + "="*80)
    print("WALK-FORWARD RESULTS")
    print("="*80)
    
    print(f"\n{'2025 OUT-OF-SAMPLE PERFORMANCE':^60}")
    print("-"*60)
    print(f"Starting Capital:        ${STARTING_CAPITAL:,.2f}")
    print(f"Final Equity:            ${test_metrics['final_equity']:,.2f}")
    print(f"Total P&L:               ${test_metrics['total_pnl']:,.2f}")
    print(f"Total Return:            {(test_metrics['final_equity']/STARTING_CAPITAL - 1)*100:.1f}%")
    print(f"Max Drawdown:            ${test_metrics['max_drawdown']:,.2f}")
    print(f"Sharpe Ratio:            {test_metrics['sharpe']:.2f}")
    
    print(f"\n{'TRADE STATISTICS (2025)':^60}")
    print("-"*60)
    print(f"Total Trades:            {test_metrics['total_trades']:,}")
    print(f"Winners:                 {test_metrics['winners']:,}")
    print(f"Losers:                  {test_metrics['losers']:,}")
    print(f"Win Rate:                {test_metrics['win_rate']:.1f}%")
    
    # Validation threshold
    print("\n" + "-"*60)
    if test_metrics['win_rate'] >= 55:
        print(f"VALIDATION: PASSED (Win Rate {test_metrics['win_rate']:.1f}% >= 55%)")
    else:
        print(f"VALIDATION: FAILED (Win Rate {test_metrics['win_rate']:.1f}% < 55%)")
    
    if test_metrics['total_pnl'] > 0:
        print(f"           PASSED (Profit ${test_metrics['total_pnl']:,.2f} > $0)")
    else:
        print(f"           FAILED (Loss ${test_metrics['total_pnl']:,.2f})")
    
    # Plot 2025 equity curve
    print(f"\n[8/8] Generating 2025 equity curve...")
    
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(test_trades['entry_time'], test_trades['equity'], 'b-', linewidth=1.5, label='Equity (2025 OOS)')
    ax.axhline(y=STARTING_CAPITAL, color='gray', linestyle='--', alpha=0.5, label='Starting Capital')
    ax.fill_between(test_trades['entry_time'], STARTING_CAPITAL, test_trades['equity'],
                    where=test_trades['equity'] >= STARTING_CAPITAL, color='green', alpha=0.3)
    ax.fill_between(test_trades['entry_time'], STARTING_CAPITAL, test_trades['equity'],
                    where=test_trades['equity'] < STARTING_CAPITAL, color='red', alpha=0.3)
    
    ax.set_title('MIDAS Walk-Forward: 2025 Out-of-Sample Equity Curve', fontsize=14, fontweight='bold')
    ax.set_ylabel('Equity ($)', fontsize=12)
    ax.set_xlabel('Date', fontsize=12)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    textstr = f"2025 OOS Results:\n"
    textstr += f"P&L: ${test_metrics['total_pnl']:,.0f}\n"
    textstr += f"Win Rate: {test_metrics['win_rate']:.1f}%\n"
    textstr += f"Trades: {test_metrics['total_trades']}"
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    plot_path = OUTPUT_DIR / "midas_equity_curve_2025_OOS.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"      Saved: {plot_path}")
    plt.close()
    
    # Generate report
    report = f"""# MIDAS Walk-Forward Validation: Out-of-Sample Results

## Protocol

| Phase | Period | Purpose |
|-------|--------|---------|
| **Training** | Jan 2021 - Dec 2024 | Learn rules from Decision Tree |
| **Testing** | Jan 2025 - Present | Validate on UNSEEN data |

**CRUCIAL:** The algorithm could NOT see 2025 data while learning rules.

---

## 2025 Out-of-Sample Results

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| **Win Rate** | **{test_metrics['win_rate']:.1f}%** | >= 55% | {'PASS' if test_metrics['win_rate'] >= 55 else 'FAIL'} |
| **Total P&L** | **${test_metrics['total_pnl']:,.2f}** | > $0 | {'PASS' if test_metrics['total_pnl'] > 0 else 'FAIL'} |
| **Sharpe Ratio** | {test_metrics['sharpe']:.2f} | > 1.0 | {'PASS' if test_metrics['sharpe'] > 1 else 'FAIL'} |

---

## Performance Summary

| Metric | Value |
|--------|-------|
| Starting Capital | ${STARTING_CAPITAL:,.2f} |
| Final Equity | ${test_metrics['final_equity']:,.2f} |
| Total P&L | ${test_metrics['total_pnl']:,.2f} |
| Total Return | {(test_metrics['final_equity']/STARTING_CAPITAL - 1)*100:.1f}% |
| Max Drawdown | ${test_metrics['max_drawdown']:,.2f} |

---

## Trade Statistics (2025)

| Metric | Value |
|--------|-------|
| Total Trades | {test_metrics['total_trades']:,} |
| Winners | {test_metrics['winners']:,} |
| Losers | {test_metrics['losers']:,} |
| Win Rate | {test_metrics['win_rate']:.1f}% |

---

## 2025 Equity Curve

![2025 OOS Equity Curve](midas_equity_curve_2025_OOS.png)

---

## Conclusion

{"**VALIDATED:** The strategy maintains edge on unseen data." if test_metrics['win_rate'] >= 55 and test_metrics['total_pnl'] > 0 else "**NEEDS REVIEW:** Performance degraded on out-of-sample data."}

---

*Generated by Magellan Quant Research - Walk-Forward Validation*  
*Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    report_path = OUTPUT_DIR / "MIDAS_WALK_FORWARD_RESULTS.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n[SAVED] Report: {report_path}")
    
    # Save trades
    trades_path = OUTPUT_DIR / "midas_trades_2025_OOS.csv"
    test_trades.to_csv(trades_path, index=False)
    print(f"[SAVED] Trades: {trades_path}")
    
    print("\n" + "="*80)
    print("WALK-FORWARD VALIDATION COMPLETE")
    print("="*80)
    
    return test_metrics, test_trades

if __name__ == "__main__":
    metrics, trades = main()
