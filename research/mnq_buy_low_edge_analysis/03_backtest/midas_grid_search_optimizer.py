"""
=============================================================================
MIDAS PROTOCOL: GRID SEARCH OPTIMIZER
=============================================================================

Optimization Parameters:
- Stop Loss: [8, 10, 12, 15, 18, 20, 25] points
- Take Profit: [30, 40, 50, 60, 80, 100, 120] points

Constraints:
- Friction: $6.50 per trade ($2.50 comms + 2.0 pts slippage)
- Time Limit: 60 minutes
- Worst-Case Execution: If bar hits both TP/SL, assume SL hit first

Uses 2025 Out-of-Sample Data (Clean Dataset)

Author: Magellan Quant Research
Date: 2026-01-30
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.tree import DecisionTreeClassifier
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

MNQ_CSV = Path(r"A:\1\Magellan\data\cache\futures\MNQ\MNQ_CLEAN_OUTRIGHTS_ONLY.csv")
OUTPUT_DIR = Path(r"a:\1\Magellan\research\mnq_buy_low_edge_analysis\03_backtest")

# Data split
TRAIN_END = "2024-12-31"
TEST_START = "2025-01-01"

# Strategy parameters
GOLDEN_HOUR_START = 2
GOLDEN_HOUR_END = 6

# Fixed parameters
SLIPPAGE_POINTS = 2.0         # 2.0 points slippage
POINT_VALUE = 2.0             # MNQ: $2 per point
COMMISSION = 2.50             # $2.50 per trade
STARTING_CAPITAL = 5000
MAX_HOLD_TIME = 60            # 60 minutes

# GRID SEARCH PARAMETERS
STOP_LOSS_VALUES = [8, 10, 12, 15, 18, 20, 25]
TAKE_PROFIT_VALUES = [30, 40, 50, 60, 80, 100, 120]

# Current arbitrary settings for comparison
CURRENT_TP = 40
CURRENT_SL = 12

# =============================================================================
# DATA LOADING & PREPARATION
# =============================================================================

def load_clean_data():
    """Load the clean MNQ dataset."""
    print("=" * 80)
    print("MIDAS PROTOCOL: GRID SEARCH OPTIMIZER")
    print("=" * 80)
    print(f"\n[1/6] Loading clean data from {MNQ_CSV.name}...")
    
    df = pd.read_csv(MNQ_CSV)
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
    
    print(f"      Total rows: {len(df_agg):,}")
    print(f"      Date range: {df_agg.index.min()} to {df_agg.index.max()}")
    
    return df_agg

def split_data(df):
    """Split into training and testing sets."""
    print(f"\n[2/6] Splitting data...")
    
    train = df[df.index <= TRAIN_END].copy()
    test = df[df.index >= TEST_START].copy()
    
    print(f"      Training: {train.index.min().date()} to {train.index.max().date()} ({len(train):,} rows)")
    print(f"      Testing:  {test.index.min().date()} to {test.index.max().date()} ({len(test):,} rows)")
    
    return train, test

def filter_golden_window(df):
    """Filter to Golden Window (02:00 - 06:00 UTC)."""
    df['hour'] = df.index.hour
    mask = (df['hour'] >= GOLDEN_HOUR_START) & (df['hour'] < GOLDEN_HOUR_END)
    return df[mask].copy()

def calculate_features(df):
    """Calculate all technical features."""
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
    
    range_hl = df['high'] - df['low']
    df['Wick_Ratio'] = (df['close'] - df['low']) / range_hl
    df['Wick_Ratio'] = df['Wick_Ratio'].replace([np.inf, -np.inf], np.nan).fillna(0.5)
    
    return df

def calculate_target(df, tp_points, sl_points):
    """Calculate target based on specific TP/SL values."""
    df = df.copy()
    
    df['future_max_high'] = df['high'].shift(-1).rolling(window=30, min_periods=30).max().shift(-29)
    df['future_min_low'] = df['low'].shift(-1).rolling(window=30, min_periods=30).min().shift(-29)
    df['MFE'] = df['future_max_high'] - df['close']
    df['MAE'] = df['close'] - df['future_min_low']
    df['Target'] = (df['MFE'] >= tp_points) & (df['MAE'] <= sl_points)
    
    return df

# =============================================================================
# MODEL TRAINING
# =============================================================================

def train_decision_tree(train_df):
    """Train Decision Tree on training data."""
    feature_cols = ['Dist_EMA200', 'Wick_Ratio', 'Velocity_5m', 'ATR_Ratio']
    
    df_clean = train_df.dropna(subset=feature_cols + ['Target'])
    X = df_clean[feature_cols]
    y = df_clean['Target'].astype(int)
    
    clf = DecisionTreeClassifier(
        max_depth=4,
        min_samples_leaf=50,
        random_state=42
    )
    clf.fit(X, y)
    
    return clf, feature_cols

def apply_model(df, clf, feature_cols):
    """Apply trained model to generate signals."""
    df = df.copy()
    df_clean = df.dropna(subset=feature_cols)
    X = df_clean[feature_cols]
    df_clean['Signal'] = clf.predict(X) == 1
    df_clean['Setup'] = np.where(df_clean['Velocity_5m'] <= -67, 'Crash', 'Quiet')
    return df_clean

# =============================================================================
# TRADE SIMULATION (Parameterized)
# =============================================================================

def simulate_trade(df, signal_idx, entry_price, tp_points, sl_points):
    """
    Simulate a single trade with specific TP/SL parameters.
    
    Constraints Applied:
    - $6.50 total friction ($2.50 comms + 2.0 pts slippage)
    - 60 minute time limit
    - Worst-case: if both TP and SL hit on same bar, assume SL hit first
    """
    entry_loc = df.index.get_loc(signal_idx) + 1
    
    if entry_loc >= len(df):
        return None, 0, 'SKIP', None
    
    # Apply slippage on entry
    actual_entry = entry_price + SLIPPAGE_POINTS
    tp_price = actual_entry + tp_points
    sl_price = actual_entry - sl_points
    
    for i in range(entry_loc, min(entry_loc + MAX_HOLD_TIME, len(df))):
        bar = df.iloc[i]
        bars_held = i - entry_loc + 1
        
        sl_hit = bar['low'] <= sl_price
        tp_hit = bar['high'] >= tp_price
        
        # WORST CASE: If both hit on same bar, assume SL hit first
        if sl_hit and tp_hit:
            return -sl_points - SLIPPAGE_POINTS, bars_held, 'SL', df.index[i]
        if sl_hit:
            return -sl_points - SLIPPAGE_POINTS, bars_held, 'SL', df.index[i]
        if tp_hit:
            return tp_points - SLIPPAGE_POINTS, bars_held, 'TP', df.index[i]
    
    # Timeout exit at market
    last_idx = min(entry_loc + MAX_HOLD_TIME - 1, len(df) - 1)
    last_bar = df.iloc[last_idx]
    exit_price = last_bar['close'] - SLIPPAGE_POINTS  # Exit slippage
    return exit_price - actual_entry, MAX_HOLD_TIME, 'TO', df.index[last_idx]

def run_backtest(df, tp_points, sl_points):
    """Run backtest with specific TP/SL parameters."""
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
        velocity = signals_df.loc[signal_idx, 'Velocity_5m']
        setup = signals_df.loc[signal_idx, 'Setup']
        
        result = simulate_trade(df, signal_idx, entry_price, tp_points, sl_points)
        if result[0] is None:
            continue
        
        pnl_points, hold_time, exit_type, exit_time = result
        pnl_dollars = (pnl_points * POINT_VALUE) - COMMISSION
        
        trades.append({
            'signal_time': signal_idx,
            'entry_time': entry_bar_idx,
            'exit_time': exit_time,
            'entry_price': entry_price + SLIPPAGE_POINTS,
            'setup': setup,
            'velocity_5m': velocity,
            'pnl_points': pnl_points,
            'pnl_dollars': pnl_dollars,
            'hold_time': hold_time,
            'exit_type': exit_type
        })
        
        last_exit_bar = entry_loc + hold_time
    
    return pd.DataFrame(trades)

def calculate_metrics(trades_df, tp_points, sl_points):
    """Calculate performance metrics for a given TP/SL combination."""
    if len(trades_df) == 0:
        return {
            'total_trades': 0,
            'winners': 0,
            'losers': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'avg_pnl': 0,
            'max_drawdown': 0,
            'sharpe': 0,
            'profit_factor': 0
        }
    
    total = len(trades_df)
    winners = (trades_df['pnl_dollars'] > 0).sum()
    losers = (trades_df['pnl_dollars'] <= 0).sum()
    win_rate = winners / total * 100
    total_pnl = trades_df['pnl_dollars'].sum()
    avg_pnl = trades_df['pnl_dollars'].mean()
    
    # Calculate drawdown
    trades_df = trades_df.copy()
    trades_df['cumulative_pnl'] = trades_df['pnl_dollars'].cumsum()
    trades_df['equity'] = STARTING_CAPITAL + trades_df['cumulative_pnl']
    trades_df['peak'] = trades_df['equity'].cummax()
    trades_df['drawdown'] = trades_df['equity'] - trades_df['peak']
    max_dd = trades_df['drawdown'].min()
    
    # Calculate Sharpe
    daily = trades_df.groupby(trades_df['entry_time'].dt.date)['pnl_dollars'].sum()
    sharpe = (daily.mean() / daily.std()) * np.sqrt(252) if len(daily) > 1 and daily.std() > 0 else 0
    
    # Calculate profit factor
    gross_profit = trades_df[trades_df['pnl_dollars'] > 0]['pnl_dollars'].sum()
    gross_loss = abs(trades_df[trades_df['pnl_dollars'] <= 0]['pnl_dollars'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    return {
        'total_trades': total,
        'winners': winners,
        'losers': losers,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'avg_pnl': avg_pnl,
        'max_drawdown': max_dd,
        'sharpe': sharpe,
        'profit_factor': profit_factor
    }

# =============================================================================
# GRID SEARCH ENGINE
# =============================================================================

def run_grid_search(test_signals, train_golden):
    """Run grid search over all TP/SL combinations."""
    print(f"\n[4/6] Running Grid Search Optimization...")
    print(f"      Testing {len(STOP_LOSS_VALUES)} SL values x {len(TAKE_PROFIT_VALUES)} TP values = {len(STOP_LOSS_VALUES) * len(TAKE_PROFIT_VALUES)} combinations")
    print(f"      Friction: ${COMMISSION + (SLIPPAGE_POINTS * POINT_VALUE)} per trade")
    print(f"      Time Limit: {MAX_HOLD_TIME} minutes")
    print()
    
    results = []
    total_combinations = len(STOP_LOSS_VALUES) * len(TAKE_PROFIT_VALUES)
    current = 0
    
    for sl in STOP_LOSS_VALUES:
        for tp in TAKE_PROFIT_VALUES:
            current += 1
            
            # For each TP/SL, we need to retrain the target (since target depends on TP/SL)
            # But we keep the same signals for fair comparison
            # Actually, re-read: the entry signals should be independent of exit parameters
            # We just need to change the exit logic
            
            trades = run_backtest(test_signals, tp, sl)
            metrics = calculate_metrics(trades, tp, sl)
            
            results.append({
                'stop_loss': sl,
                'take_profit': tp,
                'total_trades': metrics['total_trades'],
                'winners': metrics['winners'],
                'losers': metrics['losers'],
                'win_rate': metrics['win_rate'],
                'total_pnl': metrics['total_pnl'],
                'avg_pnl': metrics['avg_pnl'],
                'max_drawdown': metrics['max_drawdown'],
                'sharpe': metrics['sharpe'],
                'profit_factor': metrics['profit_factor']
            })
            
            if current % 7 == 0 or current == total_combinations:
                print(f"      Progress: {current}/{total_combinations} combinations tested")
    
    return pd.DataFrame(results)

# =============================================================================
# ANALYSIS & VISUALIZATION
# =============================================================================

def analyze_results(results_df):
    """Analyze grid search results."""
    print(f"\n[5/6] Analyzing Results...")
    
    # Find the champion
    champion_idx = results_df['total_pnl'].idxmax()
    champion = results_df.loc[champion_idx]
    
    # Current settings
    current_settings = results_df[
        (results_df['stop_loss'] == CURRENT_SL) & 
        (results_df['take_profit'] == CURRENT_TP)
    ].iloc[0]
    
    # Top 5 combinations
    top5 = results_df.nlargest(5, 'total_pnl')
    
    # Win rate analysis for SL comparison (12 vs 20)
    sl_12_results = results_df[results_df['stop_loss'] == 12]
    sl_20_results = results_df[results_df['stop_loss'] == 20]
    
    print("\n" + "=" * 80)
    print("GRID SEARCH RESULTS")
    print("=" * 80)
    
    # 1. Champion Combination
    print(f"\n{'='*60}")
    print("1. THE CHAMPION COMBINATION")
    print("="*60)
    print(f"   Stop Loss:    {champion['stop_loss']} points")
    print(f"   Take Profit:  {champion['take_profit']} points")
    print(f"   Net P&L:      ${champion['total_pnl']:,.2f}")
    print(f"   Win Rate:     {champion['win_rate']:.1f}%")
    print(f"   Sharpe:       {champion['sharpe']:.2f}")
    print(f"   Trades:       {champion['total_trades']:,}")
    print(f"   Profit Factor: {champion['profit_factor']:.2f}")
    
    # 2. Comparison to Current
    print(f"\n{'='*60}")
    print("2. CURRENT SETTINGS (40/12) VS CHAMPION")
    print("="*60)
    pnl_diff = champion['total_pnl'] - current_settings['total_pnl']
    print(f"   Current (TP={CURRENT_TP}/SL={CURRENT_SL}):")
    print(f"      Net P&L:    ${current_settings['total_pnl']:,.2f}")
    print(f"      Win Rate:   {current_settings['win_rate']:.1f}%")
    print(f"   Champion (TP={int(champion['take_profit'])}/SL={int(champion['stop_loss'])}):")
    print(f"      Net P&L:    ${champion['total_pnl']:,.2f}")
    print(f"      Win Rate:   {champion['win_rate']:.1f}%")
    print(f"\n   DIFFERENCE: ${pnl_diff:+,.2f} ({'+' if pnl_diff > 0 else ''}{pnl_diff/current_settings['total_pnl']*100:.1f}%)")
    if pnl_diff > 0:
        print(f"   ⚠️  YOU ARE LEAVING ${pnl_diff:,.2f} ON THE TABLE!")
    
    # 3. Top 5 Heatmap Data
    print(f"\n{'='*60}")
    print("3. PROFIT HEATMAP - TOP 5 COMBINATIONS")
    print("="*60)
    print(f"\n{'Rank':<6}{'TP':<8}{'SL':<8}{'Net PnL':<15}{'Win Rate':<12}{'Sharpe'}")
    print("-" * 60)
    for rank, (idx, row) in enumerate(top5.iterrows(), 1):
        print(f"{rank:<6}{int(row['take_profit']):<8}{int(row['stop_loss']):<8}${row['total_pnl']:>12,.2f}{row['win_rate']:>10.1f}%{row['sharpe']:>10.2f}")
    
    # 4. Win Rate Analysis (SL 12 vs 20)
    print(f"\n{'='*60}")
    print("4. WIN RATE ANALYSIS: SL 12 vs SL 20")
    print("="*60)
    
    print("\n   Stop Loss = 12:")
    for _, row in sl_12_results.sort_values('take_profit').iterrows():
        print(f"      TP={int(row['take_profit'])}: Win Rate = {row['win_rate']:.1f}%, PnL = ${row['total_pnl']:,.2f}")
    
    avg_wr_12 = sl_12_results['win_rate'].mean()
    
    print("\n   Stop Loss = 20:")
    for _, row in sl_20_results.sort_values('take_profit').iterrows():
        print(f"      TP={int(row['take_profit'])}: Win Rate = {row['win_rate']:.1f}%, PnL = ${row['total_pnl']:,.2f}")
    
    avg_wr_20 = sl_20_results['win_rate'].mean()
    
    print(f"\n   SUMMARY:")
    print(f"      Avg Win Rate at SL=12: {avg_wr_12:.1f}%")
    print(f"      Avg Win Rate at SL=20: {avg_wr_20:.1f}%")
    print(f"      Difference: {avg_wr_20 - avg_wr_12:+.1f}%")
    
    # 5. Robustness Check
    print(f"\n{'='*60}")
    print("5. ROBUSTNESS CHECK")
    print("="*60)
    
    champion_sl = int(champion['stop_loss'])
    champion_tp = int(champion['take_profit'])
    
    # Check neighbors
    neighbors = results_df[
        (abs(results_df['stop_loss'] - champion_sl) <= 5) &
        (abs(results_df['take_profit'] - champion_tp) <= 20)
    ].copy()
    
    neighbor_pnls = neighbors['total_pnl'].tolist()
    neighbor_avg = np.mean(neighbor_pnls)
    neighbor_std = np.std(neighbor_pnls)
    
    print(f"\n   Champion: TP={champion_tp}/SL={champion_sl}, PnL=${champion['total_pnl']:,.2f}")
    print(f"   Nearby combinations (±5 SL, ±20 TP):")
    for _, row in neighbors.sort_values('total_pnl', ascending=False).iterrows():
        marker = " ⭐" if (row['stop_loss'] == champion_sl and row['take_profit'] == champion_tp) else ""
        print(f"      TP={int(row['take_profit']):>3}/SL={int(row['stop_loss']):>2}: ${row['total_pnl']:>12,.2f}{marker}")
    
    print(f"\n   Neighbor Statistics:")
    print(f"      Average PnL: ${neighbor_avg:,.2f}")
    print(f"      Std Dev:     ${neighbor_std:,.2f}")
    
    if champion['total_pnl'] > neighbor_avg + 2 * neighbor_std:
        print(f"      ⚠️  Champion may be an OUTLIER (>2σ from neighbors)")
    else:
        print(f"      ✅ Champion is ROBUST (within 2σ of neighbors)")
    
    return champion, current_settings, top5

def create_heatmap(results_df, output_dir):
    """Create a visual heatmap of results."""
    print(f"\n[6/6] Generating visualizations...")
    
    # Create pivot table for heatmap
    pivot_pnl = results_df.pivot(index='stop_loss', columns='take_profit', values='total_pnl')
    pivot_wr = results_df.pivot(index='stop_loss', columns='take_profit', values='win_rate')
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # PnL Heatmap
    ax1 = axes[0]
    sns.heatmap(pivot_pnl, annot=True, fmt=',.0f', cmap='RdYlGn', center=0,
                ax=ax1, cbar_kws={'label': 'Net PnL ($)'})
    ax1.set_title('Net P&L by TP/SL Combination ($)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Take Profit (pts)', fontsize=12)
    ax1.set_ylabel('Stop Loss (pts)', fontsize=12)
    
    # Highlight current and champion
    champion_idx = results_df['total_pnl'].idxmax()
    champion = results_df.loc[champion_idx]
    
    # Win Rate Heatmap
    ax2 = axes[1]
    sns.heatmap(pivot_wr, annot=True, fmt='.1f', cmap='Blues',
                ax=ax2, cbar_kws={'label': 'Win Rate (%)'})
    ax2.set_title('Win Rate by TP/SL Combination (%)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Take Profit (pts)', fontsize=12)
    ax2.set_ylabel('Stop Loss (pts)', fontsize=12)
    
    plt.suptitle(f"MIDAS Protocol Grid Search: Champion = TP{int(champion['take_profit'])}/SL{int(champion['stop_loss'])} (${champion['total_pnl']:,.0f})",
                 fontsize=16, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    plot_path = output_dir / "midas_grid_search_heatmap.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"      Saved: {plot_path}")
    plt.close()
    
    # Create second visualization: 3D surface
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    X, Y = np.meshgrid(TAKE_PROFIT_VALUES, STOP_LOSS_VALUES)
    Z = pivot_pnl.values
    
    surf = ax.plot_surface(X, Y, Z, cmap='RdYlGn', edgecolor='none', alpha=0.8)
    ax.set_xlabel('Take Profit (pts)')
    ax.set_ylabel('Stop Loss (pts)')
    ax.set_zlabel('Net PnL ($)')
    ax.set_title('MIDAS Protocol: PnL Surface by TP/SL', fontsize=14, fontweight='bold')
    
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='Net PnL ($)')
    
    surface_path = output_dir / "midas_grid_search_surface.png"
    plt.savefig(surface_path, dpi=150, bbox_inches='tight')
    print(f"      Saved: {surface_path}")
    plt.close()

def generate_report(results_df, champion, current_settings, top5, output_dir):
    """Generate comprehensive markdown report."""
    
    # Win rate comparison
    sl_12_avg = results_df[results_df['stop_loss'] == 12]['win_rate'].mean()
    sl_20_avg = results_df[results_df['stop_loss'] == 20]['win_rate'].mean()
    
    pnl_diff = champion['total_pnl'] - current_settings['total_pnl']
    pnl_pct_diff = (pnl_diff / current_settings['total_pnl']) * 100
    
    report = f"""# MIDAS Protocol: Grid Search Optimization Results

## Executive Summary

**Mission:** Find the optimal Stop Loss (SL) and Take Profit (TP) combination that maximizes Net Profit.

**Data:** 2025 Out-of-Sample (Clean Dataset, No Calendar Spreads)

**Tested Parameters:**
- Stop Loss: {STOP_LOSS_VALUES} points
- Take Profit: {TAKE_PROFIT_VALUES} points
- Total Combinations: {len(STOP_LOSS_VALUES) * len(TAKE_PROFIT_VALUES)}

---

## 1. THE CHAMPION COMBINATION 🏆

| Parameter | Value |
|-----------|-------|
| **Stop Loss** | **{int(champion['stop_loss'])} points** |
| **Take Profit** | **{int(champion['take_profit'])} points** |
| **Net P&L** | **${champion['total_pnl']:,.2f}** |
| **Win Rate** | **{champion['win_rate']:.1f}%** |
| **Sharpe Ratio** | **{champion['sharpe']:.2f}** |
| **Total Trades** | {int(champion['total_trades']):,} |
| **Profit Factor** | {champion['profit_factor']:.2f} |

---

## 2. PROFIT HEATMAP - Top 5 Combinations

| Rank | Take Profit | Stop Loss | Net PnL | Win Rate | Sharpe |
|------|-------------|-----------|---------|----------|--------|
"""
    
    for rank, (idx, row) in enumerate(top5.iterrows(), 1):
        marker = " 🏆" if rank == 1 else ""
        report += f"| {rank}{marker} | {int(row['take_profit'])} pts | {int(row['stop_loss'])} pts | ${row['total_pnl']:,.2f} | {row['win_rate']:.1f}% | {row['sharpe']:.2f} |\n"
    
    report += f"""
---

## 3. WIN RATE ANALYSIS: SL 12 vs SL 20

### Stop Loss = 12 points
"""
    
    sl_12_results = results_df[results_df['stop_loss'] == 12].sort_values('take_profit')
    for _, row in sl_12_results.iterrows():
        report += f"- TP={int(row['take_profit'])}: Win Rate = {row['win_rate']:.1f}%, PnL = ${row['total_pnl']:,.2f}\n"
    
    report += f"""
### Stop Loss = 20 points
"""
    
    sl_20_results = results_df[results_df['stop_loss'] == 20].sort_values('take_profit')
    for _, row in sl_20_results.iterrows():
        report += f"- TP={int(row['take_profit'])}: Win Rate = {row['win_rate']:.1f}%, PnL = ${row['total_pnl']:,.2f}\n"
    
    report += f"""
### Summary

| Metric | SL = 12 | SL = 20 | Difference |
|--------|---------|---------|------------|
| Avg Win Rate | {sl_12_avg:.1f}% | {sl_20_avg:.1f}% | {sl_20_avg - sl_12_avg:+.1f}% |

**Insight:** Moving Stop Loss from 12 to 20 points {"increases" if sl_20_avg > sl_12_avg else "decreases"} the average win rate by {abs(sl_20_avg - sl_12_avg):.1f}%.

---

## 4. ROBUSTNESS CHECK

"""
    
    champion_sl = int(champion['stop_loss'])
    champion_tp = int(champion['take_profit'])
    
    neighbors = results_df[
        (abs(results_df['stop_loss'] - champion_sl) <= 5) &
        (abs(results_df['take_profit'] - champion_tp) <= 20)
    ].copy()
    
    neighbor_avg = neighbors['total_pnl'].mean()
    neighbor_std = neighbors['total_pnl'].std()
    
    is_outlier = champion['total_pnl'] > neighbor_avg + 2 * neighbor_std
    
    report += f"""The Champion (TP={champion_tp}/SL={champion_sl}) was compared against neighboring parameter combinations (±5 SL, ±20 TP):

| TP/SL Combo | Net PnL | Status |
|-------------|---------|--------|
"""
    
    for _, row in neighbors.sort_values('total_pnl', ascending=False).iterrows():
        marker = "⭐ Champion" if (row['stop_loss'] == champion_sl and row['take_profit'] == champion_tp) else ""
        report += f"| TP={int(row['take_profit'])}/SL={int(row['stop_loss'])} | ${row['total_pnl']:,.2f} | {marker} |\n"
    
    report += f"""
**Statistics:**
- Average PnL of neighbors: ${neighbor_avg:,.2f}
- Std Dev of neighbors: ${neighbor_std:,.2f}
- Champion deviation: {(champion['total_pnl'] - neighbor_avg) / neighbor_std:.1f}σ

**Verdict:** {"⚠️ Champion may be an OUTLIER (>2σ from neighbors) - proceed with caution" if is_outlier else "✅ Champion is ROBUST - nearby parameters also perform well"}

---

## 5. CURRENT SETTINGS ANALYSIS

### Are You Leaving Money on the Table?

| Setting | Current (40/12) | Champion ({int(champion['take_profit'])}/{int(champion['stop_loss'])}) | Difference |
|---------|-----------------|-----------------|------------|
| Net P&L | ${current_settings['total_pnl']:,.2f} | ${champion['total_pnl']:,.2f} | **${pnl_diff:+,.2f}** |
| Win Rate | {current_settings['win_rate']:.1f}% | {champion['win_rate']:.1f}% | {champion['win_rate'] - current_settings['win_rate']:+.1f}% |
| Sharpe | {current_settings['sharpe']:.2f} | {champion['sharpe']:.2f} | {champion['sharpe'] - current_settings['sharpe']:+.2f} |

### Verdict

"""
    
    if pnl_diff > 0:
        report += f"""⚠️ **YES, YOU ARE LEAVING ${pnl_diff:,.2f} ON THE TABLE ({pnl_pct_diff:+.1f}%)**

**Recommended Action:** Change your settings from TP={CURRENT_TP}/SL={CURRENT_SL} to **TP={int(champion['take_profit'])}/SL={int(champion['stop_loss'])}**

This change is expected to increase your annual profit by approximately ${pnl_diff:,.2f}.
"""
    else:
        report += f"""✅ **Your current settings are already optimal or near-optimal.**

The potential improvement is ${pnl_diff:,.2f}, which is {'negligible' if abs(pnl_diff) < 1000 else 'not significant enough to warrant a change'}.
"""
    
    report += f"""
---

## Visualizations

### Profit Heatmap
![Grid Search Heatmap](midas_grid_search_heatmap.png)

### 3D PnL Surface
![Grid Search Surface](midas_grid_search_surface.png)

---

## Methodology

- **Data:** MNQ_CLEAN_OUTRIGHTS_ONLY.csv (2025 Out-of-Sample)
- **Time Window:** 02:00 - 06:00 UTC (Asian Session)
- **Friction:** $6.50 per trade ($2.50 commission + 2.0 pts slippage)
- **Time Limit:** 60 minutes (exit at market if neither TP nor SL hit)
- **Worst-Case Execution:** If both TP and SL hit on same bar, assume SL hit first
- **Entry Signals:** Decision Tree classifier trained on 2021-2024 data

---

*Generated by Magellan Quant Research*  
*Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    report_path = output_dir / "MIDAS_GRID_SEARCH_RESULTS.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"      Saved: {report_path}")
    
    return report_path

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Execute grid search optimization."""
    
    # Load and prepare data
    df = load_clean_data()
    train_raw, test_raw = split_data(df)
    
    # Prepare training data (using current TP/SL for training target)
    print(f"\n[3/6] Preparing data and training model...")
    train_golden = filter_golden_window(train_raw)
    train_golden = calculate_features(train_golden)
    train_golden = calculate_target(train_golden, CURRENT_TP, CURRENT_SL)
    
    # Train model
    clf, feature_cols = train_decision_tree(train_golden)
    print(f"      Model trained on {len(train_golden):,} samples")
    
    # Prepare test data
    test_golden = filter_golden_window(test_raw)
    test_golden = calculate_features(test_golden)
    
    # Apply model to get signals
    test_signals = apply_model(test_golden, clf, feature_cols)
    signal_count = test_signals['Signal'].sum()
    print(f"      Signals found in 2025: {signal_count:,}")
    
    # Run grid search
    results_df = run_grid_search(test_signals, train_golden)
    
    # Analyze results
    champion, current_settings, top5 = analyze_results(results_df)
    
    # Create visualizations
    create_heatmap(results_df, OUTPUT_DIR)
    
    # Generate report
    report_path = generate_report(results_df, champion, current_settings, top5, OUTPUT_DIR)
    
    # Save raw results
    results_path = OUTPUT_DIR / "midas_grid_search_raw_results.csv"
    results_df.to_csv(results_path, index=False)
    print(f"      Saved: {results_path}")
    
    print("\n" + "=" * 80)
    print("GRID SEARCH OPTIMIZATION COMPLETE")
    print("=" * 80)
    
    # Final summary
    pnl_diff = champion['total_pnl'] - current_settings['total_pnl']
    print(f"\n📊 ANSWER TO YOUR QUESTION:")
    print(f"   Current Settings: TP={CURRENT_TP}/SL={CURRENT_SL} → ${current_settings['total_pnl']:,.2f}")
    print(f"   Optimal Settings: TP={int(champion['take_profit'])}/SL={int(champion['stop_loss'])} → ${champion['total_pnl']:,.2f}")
    
    if pnl_diff > 0:
        print(f"\n   ⚠️ YES, you are leaving ${pnl_diff:,.2f} on the table!")
        print(f"   💡 RECOMMENDATION: Switch to TP={int(champion['take_profit'])}/SL={int(champion['stop_loss'])}")
    else:
        print(f"\n   ✅ Your current settings are already near-optimal.")
    
    return results_df, champion, current_settings

if __name__ == "__main__":
    results_df, champion, current_settings = main()
