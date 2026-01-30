"""
=============================================================================
MIDAS PROTOCOL: Decision Tree Rule Induction for MNQ High-Probability Setups
=============================================================================

Role: Expert Quantitative Researcher
Objective: Find sub-conditions within the Golden Window (02:00-06:00 UTC) that
           push Win Rate above 60% using Decision Tree rule extraction.

Author: Magellan Quant Research
Date: 2026-01-30
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

# Data source
MNQ_CSV = Path(r"A:\1\Magellan\data\cache\futures\MNQ\glbx-mdp3-20210129-20260128.ohlcv-1m.csv")
OUTPUT_DIR = Path(r"a:\1\Magellan\research\mnq_buy_low_edge_analysis")

# Golden Window (UTC)
GOLDEN_HOUR_START = 2   # 02:00 UTC
GOLDEN_HOUR_END = 6     # 06:00 UTC (exclusive)

# Target Definition
REWARD_TARGET = 40      # +40 points
RISK_LIMIT = 12         # -12 points max drawdown
FORWARD_WINDOW = 30     # 30 minutes

# Decision Tree parameters
MAX_DEPTH = 3
MIN_SAMPLES_LEAF = 100  # Minimum trades per leaf

# Leaf filtering
MIN_WIN_RATE = 0.55     # 55% minimum
MIN_SAMPLES = 100       # Statistically significant

# =============================================================================
# FEATURE ENGINEERING FUNCTIONS
# =============================================================================

def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    """Calculate Average True Range."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.ewm(span=period, adjust=False).mean()

def count_consecutive_reds(df: pd.DataFrame) -> pd.Series:
    """Count consecutive red candles (negative = red streak)."""
    is_red = df['close'] < df['open']
    
    # Create groups when direction changes
    direction_change = is_red != is_red.shift(1)
    streak_group = direction_change.cumsum()
    
    # Count within each streak
    streak_count = df.groupby(streak_group).cumcount() + 1
    
    # Only count reds (return 0 for green candles)
    result = streak_count.where(is_red, 0)
    return result

# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def load_and_prepare_data() -> pd.DataFrame:
    """Load full MNQ dataset and prepare for analysis."""
    print("="*80)
    print("MIDAS PROTOCOL: Decision Tree Rule Induction")
    print("="*80)
    
    print(f"\n[1/5] Loading data from {MNQ_CSV.name}...")
    df = pd.read_csv(MNQ_CSV)
    print(f"      Raw rows: {len(df):,}")
    
    # Parse timestamps
    df['datetime'] = pd.to_datetime(df['ts_event'].str[:19])
    df = df.set_index('datetime')
    
    # Keep OHLCV
    df = df[['open', 'high', 'low', 'close', 'volume']].copy()
    
    # Aggregate by timestamp (combine multiple contracts)
    df_agg = df.groupby(df.index).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    })
    df_agg = df_agg.sort_index()
    
    print(f"      Aggregated rows: {len(df_agg):,}")
    print(f"      Date range: {df_agg.index.min()} to {df_agg.index.max()}")
    
    return df_agg

def filter_golden_window(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to Golden Window (02:00-06:00 UTC)."""
    print(f"\n[2/5] Filtering to Golden Window ({GOLDEN_HOUR_START:02d}:00 - {GOLDEN_HOUR_END:02d}:00 UTC)...")
    
    df['hour'] = df.index.hour
    mask = (df['hour'] >= GOLDEN_HOUR_START) & (df['hour'] < GOLDEN_HOUR_END)
    df_golden = df[mask].copy()
    
    print(f"      Rows in Golden Window: {len(df_golden):,} ({100*len(df_golden)/len(df):.1f}%)")
    
    return df_golden

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create physics-based features."""
    print("\n[3/5] Engineering features...")
    
    df = df.copy()
    
    # 1. Dist_EMA200: How stretched is the rubber band?
    df['EMA200'] = calculate_ema(df['close'], 200)
    df['Dist_EMA200'] = df['close'] - df['EMA200']
    print("      [+] Dist_EMA200 (rubber band stretch)")
    
    # 2. Wick_Ratio: Did buyers step in? (1.0 = Hammer)
    range_hl = df['high'] - df['low']
    df['Wick_Ratio'] = (df['close'] - df['low']) / range_hl
    df['Wick_Ratio'] = df['Wick_Ratio'].replace([np.inf, -np.inf], np.nan).fillna(0.5)
    print("      [+] Wick_Ratio (buyer absorption)")
    
    # 3. Velocity_5m: How fast is it crashing?
    df['Velocity_5m'] = df['close'] - df['close'].shift(5)
    print("      [+] Velocity_5m (momentum speed)")
    
    # 4. Consecutive_Reds: Rolling count of red candles
    df['Consecutive_Reds'] = count_consecutive_reds(df)
    print("      [+] Consecutive_Reds (selling exhaustion)")
    
    # 5. ATR_Ratio: Is it quiet or violent?
    df['ATR'] = calculate_atr(df['high'], df['low'], df['close'], 14)
    df['ATR_Avg'] = df['ATR'].rolling(50).mean()
    df['ATR_Ratio'] = df['ATR'] / df['ATR_Avg']
    df['ATR_Ratio'] = df['ATR_Ratio'].replace([np.inf, -np.inf], np.nan).fillna(1.0)
    print("      [+] ATR_Ratio (volatility regime)")
    
    # 6. Bonus: Range as percentage
    df['Range_Pct'] = (df['high'] - df['low']) / df['close'] * 100
    print("      [+] Range_Pct (bar size)")
    
    return df

def calculate_target(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Golden Target with 30-min forward window."""
    print(f"\n[4/5] Calculating Target (+{REWARD_TARGET}pts / -{RISK_LIMIT}pts in {FORWARD_WINDOW} mins)...")
    
    df = df.copy()
    
    # Forward-looking max high and min low
    df['future_max_high'] = df['high'].shift(-1).rolling(window=FORWARD_WINDOW, min_periods=FORWARD_WINDOW).max().shift(-(FORWARD_WINDOW-1))
    df['future_min_low'] = df['low'].shift(-1).rolling(window=FORWARD_WINDOW, min_periods=FORWARD_WINDOW).min().shift(-(FORWARD_WINDOW-1))
    
    # MFE and MAE
    df['MFE'] = df['future_max_high'] - df['close']
    df['MAE'] = df['close'] - df['future_min_low']
    
    # Target: Reward achieved AND risk not exceeded
    df['Target'] = (df['MFE'] >= REWARD_TARGET) & (df['MAE'] <= RISK_LIMIT)
    
    # Stats
    valid = df['Target'].notna()
    total_valid = valid.sum()
    target_count = df.loc[valid, 'Target'].sum()
    
    print(f"      Valid rows: {total_valid:,}")
    print(f"      Golden Targets: {target_count:,} ({100*target_count/total_valid:.2f}%)")
    
    return df

def train_decision_tree(df: pd.DataFrame):
    """Train Decision Tree and extract rules."""
    print("\n[5/5] Training Decision Tree Classifier...")
    
    # Feature columns
    feature_cols = ['Dist_EMA200', 'Wick_Ratio', 'Velocity_5m', 'Consecutive_Reds', 'ATR_Ratio']
    
    # Clean data
    df_clean = df.dropna(subset=feature_cols + ['Target'])
    
    X = df_clean[feature_cols]
    y = df_clean['Target'].astype(int)
    
    print(f"      Training samples: {len(X):,}")
    print(f"      Features: {feature_cols}")
    
    # Train Decision Tree
    clf = DecisionTreeClassifier(
        max_depth=MAX_DEPTH,
        min_samples_leaf=MIN_SAMPLES_LEAF,
        random_state=42
    )
    clf.fit(X, y)
    
    # Print tree structure
    print("\n" + "="*80)
    print("DECISION TREE STRUCTURE")
    print("="*80)
    tree_rules = export_text(clf, feature_names=feature_cols)
    print(tree_rules)
    
    return clf, X, y, feature_cols, df_clean

def extract_high_probability_leaves(clf, X, y, feature_cols, df_clean):
    """Find the purest leaf nodes with high win rates."""
    print("\n" + "="*80)
    print("HIGH-PROBABILITY LEAF ANALYSIS")
    print("="*80)
    
    # Get leaf assignments for each sample
    leaf_ids = clf.apply(X)
    
    # Analyze each leaf
    leaf_stats = []
    unique_leaves = np.unique(leaf_ids)
    
    for leaf_id in unique_leaves:
        mask = leaf_ids == leaf_id
        leaf_samples = mask.sum()
        leaf_wins = y[mask].sum()
        leaf_win_rate = leaf_wins / leaf_samples if leaf_samples > 0 else 0
        
        leaf_stats.append({
            'leaf_id': leaf_id,
            'samples': leaf_samples,
            'wins': leaf_wins,
            'win_rate': leaf_win_rate
        })
    
    # Convert to DataFrame and sort
    leaf_df = pd.DataFrame(leaf_stats)
    leaf_df = leaf_df.sort_values('win_rate', ascending=False)
    
    print(f"\nAll Leaf Nodes ({len(leaf_df)} total):")
    print("-"*60)
    print(f"{'Leaf ID':>10} | {'Samples':>10} | {'Wins':>10} | {'Win Rate':>10}")
    print("-"*60)
    for _, row in leaf_df.iterrows():
        marker = " ***" if row['win_rate'] >= MIN_WIN_RATE and row['samples'] >= MIN_SAMPLES else ""
        print(f"{row['leaf_id']:>10} | {row['samples']:>10,} | {row['wins']:>10,} | {row['win_rate']:>9.1%}{marker}")
    
    # Filter to high-probability leaves
    high_prob = leaf_df[(leaf_df['win_rate'] >= MIN_WIN_RATE) & (leaf_df['samples'] >= MIN_SAMPLES)]
    
    print(f"\n" + "="*80)
    print(f"TOP HIGH-PROBABILITY SETUPS (Win Rate >= {MIN_WIN_RATE:.0%}, Samples >= {MIN_SAMPLES})")
    print("="*80)
    
    if len(high_prob) == 0:
        print("\nNo leaves meet the criteria. Showing top 3 by win rate:")
        high_prob = leaf_df[leaf_df['samples'] >= MIN_SAMPLES].head(3)
    
    # Extract rules for each high-probability leaf
    tree = clf.tree_
    feature_names = feature_cols
    
    results = []
    
    for rank, (_, row) in enumerate(high_prob.head(5).iterrows(), 1):
        leaf_id = row['leaf_id']
        
        # Find path to this leaf
        path = get_path_to_leaf(tree, leaf_id, feature_names)
        
        results.append({
            'rank': rank,
            'leaf_id': leaf_id,
            'samples': row['samples'],
            'wins': row['wins'],
            'win_rate': row['win_rate'],
            'rules': path
        })
        
        print(f"\n{'='*60}")
        print(f"SETUP #{rank}: Win Rate = {row['win_rate']:.1%}")
        print(f"{'='*60}")
        print(f"Samples: {row['samples']:,} | Wins: {row['wins']:,}")
        print(f"\nRULES (If/Then Logic):")
        for rule in path:
            print(f"  - {rule}")
        
        # Plain English summary
        print(f"\nPLAIN ENGLISH:")
        print(f"  \"If {' AND '.join(path)}, then Win Rate = {row['win_rate']:.1%}\"")
    
    return results

def get_path_to_leaf(tree, leaf_id, feature_names):
    """Extract the decision path to a specific leaf node."""
    # Build path by traversing from root
    path = []
    node_id = 0  # Start at root
    
    # Find path to leaf using BFS/recursion
    def find_path(node, target_leaf, current_path):
        if node == target_leaf:
            return current_path
        
        left_child = tree.children_left[node]
        right_child = tree.children_right[node]
        
        if left_child == -1:  # Leaf node
            return None
        
        feature = feature_names[tree.feature[node]]
        threshold = tree.threshold[node]
        
        # Try left (<=)
        left_path = find_path(left_child, target_leaf, 
                              current_path + [f"{feature} <= {threshold:.2f}"])
        if left_path is not None:
            return left_path
        
        # Try right (>)
        right_path = find_path(right_child, target_leaf,
                               current_path + [f"{feature} > {threshold:.2f}"])
        if right_path is not None:
            return right_path
        
        return None
    
    path = find_path(0, leaf_id, [])
    return path if path else ["(Root node)"]

def generate_report(results, df_golden):
    """Generate markdown report."""
    
    base_win_rate = df_golden['Target'].mean() * 100
    
    report = f"""# MIDAS Protocol: Decision Tree Rule Extraction

## Executive Summary

**Objective:** Find sub-conditions within the Golden Window that push Win Rate above 60%.

**Base Win Rate (02:00-06:00 UTC):** {base_win_rate:.2f}%

---

## Configuration

| Parameter | Value |
|-----------|-------|
| Golden Window | 02:00 - 06:00 UTC |
| Reward Target | +{REWARD_TARGET} points |
| Risk Limit | {RISK_LIMIT} points |
| Forward Window | {FORWARD_WINDOW} minutes |
| Decision Tree Depth | {MAX_DEPTH} |
| Min Samples per Leaf | {MIN_SAMPLES_LEAF} |

---

## Features Used (Physics)

| Feature | Description |
|---------|-------------|
| Dist_EMA200 | Close - EMA(200). Rubber band stretch |
| Wick_Ratio | (Close - Low) / (High - Low). Buyer absorption (1.0 = Hammer) |
| Velocity_5m | Close - Close(5 bars ago). Momentum speed |
| Consecutive_Reds | Count of consecutive red candles |
| ATR_Ratio | ATR / Avg_ATR(50). Volatility regime |

---

## High-Probability Setups Discovered

"""
    
    for r in results:
        improvement = r['win_rate'] * 100 - base_win_rate
        report += f"""
### Setup #{r['rank']}: Win Rate = {r['win_rate']:.1%}

**Improvement over baseline:** +{improvement:.1f}%

| Metric | Value |
|--------|-------|
| Samples | {r['samples']:,} |
| Wins | {r['wins']:,} |
| Win Rate | {r['win_rate']:.1%} |

**Rules (If/Then Logic):**
"""
        for rule in r['rules']:
            report += f"- `{rule}`\n"
        
        report += f"\n**Plain English:**\n> \"If {' AND '.join(r['rules'])}, then Win Rate = {r['win_rate']:.1%}\"\n"
    
    report += """
---

## Trading Implementation

To implement these rules in a trading bot:

```python
def check_midas_entry(bar):
    # Setup conditions extracted from Decision Tree
    # [INSERT CONDITIONS FROM TOP SETUPS]
    pass
```

---

## Notes

1. These rules are derived from Decision Tree analysis of 5 years of data
2. All times are in UTC
3. The 02:00-06:00 UTC window corresponds to ~9pm-1am US Eastern
4. Validate these rules with out-of-sample testing before deployment

---

*Generated by Magellan Quant Research - Midas Protocol*
"""
    
    report_path = OUTPUT_DIR / "MIDAS_PROTOCOL_RESULTS.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n[SAVED] Report saved to: {report_path}")
    
    return report

def main():
    """Execute the Midas Protocol."""
    
    # Load data
    df = load_and_prepare_data()
    
    # Filter to Golden Window
    df_golden = filter_golden_window(df)
    
    # Engineer features
    df_golden = engineer_features(df_golden)
    
    # Calculate target
    df_golden = calculate_target(df_golden)
    
    # Train Decision Tree
    clf, X, y, feature_cols, df_clean = train_decision_tree(df_golden)
    
    # Extract high-probability leaves
    results = extract_high_probability_leaves(clf, X, y, feature_cols, df_clean)
    
    # Generate report
    report = generate_report(results, df_clean)
    
    print("\n" + "="*80)
    print("MIDAS PROTOCOL COMPLETE")
    print("="*80)
    
    return clf, results

if __name__ == "__main__":
    clf, results = main()
