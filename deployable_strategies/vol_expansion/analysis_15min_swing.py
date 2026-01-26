"""
15-MINUTE TIMEFRAME ELEVATION - BLIND BACKWARDS ANALYSIS

PURPOSE: Discover a robust Intraday Swing Strategy on 15-minute bars
where slippage is statistically negligible relative to profit margins.

PHASES:
0. Data Aggregation (1-min → 15-min)
1. Target Definition (2.0 ATR target, 1.0 ATR max drawdown, 8-bar horizon)
2. Feature Engineering (velocity, volatility, effort_result, range_ratio)
3. Cluster Discovery (K-Means on winning precursors)
4. Strategy Synthesis (Boolean logic extraction)

Author: Magellan Testing Framework
Date: January 25, 2026
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

output_path = Path(__file__).parent / "outputs_15min"
output_path.mkdir(exist_ok=True)


# =============================================================================
# PHASE 0: DATA AGGREGATION
# =============================================================================

def aggregate_to_15min(symbol: str) -> pd.DataFrame:
    """
    Aggregate 1-minute bars to 15-minute bars.
    
    Rules:
    - Open: First bar's open
    - High: Max high
    - Low: Min low  
    - Close: Last bar's close
    - Volume: Sum
    """
    print(f"\n{'='*60}")
    print(f"PHASE 0: DATA AGGREGATION - {symbol}")
    print(f"{'='*60}")
    
    # Load 1-minute data
    data_path = project_root / "data" / "cache" / "equities"
    files = sorted(data_path.glob(f"{symbol}_1min_202*.parquet"),
                   key=lambda x: x.stat().st_size, reverse=True)
    
    if not files:
        raise FileNotFoundError(f"No data for {symbol}")
    
    df = pd.read_parquet(files[0])
    print(f"Loaded 1-min data: {len(df):,} bars")
    print(f"Date range: {df.index.min()} to {df.index.max()}")
    
    # Resample to 15-minute bars
    df_15m = df.resample('15min').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    # Add trade_count if available
    if 'trade_count' in df.columns:
        df_15m['trade_count'] = df['trade_count'].resample('15min').sum()
    
    print(f"Aggregated to 15-min: {len(df_15m):,} bars")
    print(f"Compression ratio: {len(df)/len(df_15m):.1f}x")
    
    # Filter market hours (9:30 AM - 4:00 PM ET)
    df_15m = df_15m.between_time('09:30', '15:45')
    print(f"Market hours only: {len(df_15m):,} bars")
    
    return df_15m


# =============================================================================
# PHASE 1: TARGET DEFINITION
# =============================================================================

def calculate_atr_15m(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Calculate ATR for 15-minute bars."""
    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - df['close'].shift(1)).abs()
    tr3 = (df['low'] - df['close'].shift(1)).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.rolling(period).mean()


def identify_winning_events(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Identify "Swing" winning events on 15-minute bars.
    
    Winning Event Criteria:
    - Magnitude: >= 2.0 ATR move
    - Timeframe: Within 8 bars (2 hours)
    - Efficiency: Max drawdown < 1.0 ATR
    """
    print(f"\n{'='*60}")
    print(f"PHASE 1: TARGET DEFINITION - {symbol}")
    print(f"{'='*60}")
    
    df = df.copy()
    df['atr'] = calculate_atr_15m(df, period=20)
    df = df.dropna(subset=['atr'])
    
    target_atr = 2.0
    max_dd_atr = 1.0
    max_bars = 8  # 2 hours at 15-min
    
    events = []
    
    print(f"Scanning {len(df):,} bars for winning events...")
    print(f"Criteria: +{target_atr} ATR within {max_bars} bars, max DD {max_dd_atr} ATR")
    
    for idx in range(len(df) - max_bars):
        entry_bar = df.iloc[idx]
        entry_price = entry_bar['close']
        atr = entry_bar['atr']
        
        if atr <= 0 or np.isnan(atr):
            continue
        
        target_price = entry_price + (target_atr * atr)
        max_allowed_dd = max_dd_atr * atr
        
        # Look ahead
        max_drawdown = 0
        target_hit = False
        bars_to_target = 0
        exit_price = None
        
        for future_idx in range(idx + 1, min(idx + max_bars + 1, len(df))):
            future_bar = df.iloc[future_idx]
            
            # Track drawdown
            dd = entry_price - future_bar['low']
            if dd > max_drawdown:
                max_drawdown = dd
            
            # Check if target hit with acceptable drawdown
            if future_bar['high'] >= target_price and max_drawdown <= max_allowed_dd:
                target_hit = True
                bars_to_target = future_idx - idx
                exit_price = target_price
                break
        
        events.append({
            'timestamp': df.index[idx],
            'entry_price': entry_price,
            'atr': atr,
            'is_winning': target_hit,
            'bars_to_target': bars_to_target if target_hit else None,
            'max_drawdown': max_drawdown,
            'dd_in_atr': max_drawdown / atr,
            'exit_price': exit_price
        })
    
    events_df = pd.DataFrame(events)
    
    win_count = events_df['is_winning'].sum()
    win_rate = win_count / len(events_df)
    
    print(f"\nResults:")
    print(f"  Total bars analyzed: {len(events_df):,}")
    print(f"  Winning events: {win_count:,} ({win_rate:.1%})")
    
    if win_count > 0:
        avg_bars = events_df[events_df['is_winning']]['bars_to_target'].mean()
        print(f"  Avg bars to target: {avg_bars:.1f}")
    
    # Save events
    events_df.to_parquet(output_path / f"{symbol}_15m_winning_events.parquet")
    print(f"Saved to {output_path / f'{symbol}_15m_winning_events.parquet'}")
    
    return events_df


# =============================================================================
# PHASE 2: FEATURE ENGINEERING
# =============================================================================

def build_features_15m(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Build stationary feature vector for 15-minute bars.
    
    Features:
    - velocity_15m: 1-bar momentum
    - velocity_60m: 4-bar momentum
    - volatility_ratio: ATR5 / ATR20
    - effort_result: Volume efficiency
    - range_ratio: Bar structure
    - body_position: Close location in range
    """
    print(f"\n{'='*60}")
    print(f"PHASE 2: FEATURE ENGINEERING - {symbol}")
    print(f"{'='*60}")
    
    df = df.copy()
    features = pd.DataFrame(index=df.index)
    
    # Velocity (momentum)
    features['velocity_1'] = df['close'].pct_change(1)
    features['velocity_4'] = df['close'].pct_change(4)  # 1-hour momentum
    features['velocity_8'] = df['close'].pct_change(8)  # 2-hour momentum
    
    # Acceleration
    features['acceleration'] = features['velocity_1'].diff()
    
    # Volatility ratio (expansion/compression)
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - df['close'].shift(1)).abs(),
        (df['low'] - df['close'].shift(1)).abs()
    ], axis=1).max(axis=1)
    
    atr_5 = tr.rolling(5).mean()
    atr_20 = tr.rolling(20).mean()
    features['volatility_ratio'] = atr_5 / (atr_20 + 0.0001)
    features['volatility_ratio'] = features['volatility_ratio'].clip(0, 5)
    
    # Volume z-score
    vol_mean = df['volume'].rolling(20).mean()
    vol_std = df['volume'].rolling(20).std()
    features['volume_z'] = (df['volume'] - vol_mean) / (vol_std + 1)
    features['volume_z'] = features['volume_z'].clip(-5, 5)
    
    # Effort-result (volume efficiency)
    pct_change_abs = df['close'].pct_change().abs()
    features['effort_result'] = features['volume_z'] / (pct_change_abs + 0.0001)
    features['effort_result'] = features['effort_result'].clip(-100, 100)
    
    # Range ratio (bar structure)
    full_range = df['high'] - df['low']
    body = (df['close'] - df['open']).abs()
    features['range_ratio'] = full_range / (body + 0.0001)
    features['range_ratio'] = features['range_ratio'].clip(0, 20)
    
    # Body position
    features['body_position'] = (df['close'] - df['low']) / (full_range + 0.0001)
    features['body_position'] = features['body_position'].clip(0, 1)
    
    # Trade intensity (if available)
    if 'trade_count' in df.columns:
        tc_mean = df['trade_count'].rolling(20).mean()
        features['trade_intensity'] = df['trade_count'] / (tc_mean + 1)
        features['trade_intensity'] = features['trade_intensity'].clip(0, 5)
    
    # Aggregate over lookback window (50 bars = ~12.5 hours)
    lookback = 20  # 5 hours lookback for 15-min bars
    
    for col in ['velocity_1', 'velocity_4', 'volatility_ratio', 'effort_result', 
                'range_ratio', 'body_position', 'volume_z']:
        features[f'{col}_mean'] = features[col].rolling(lookback).mean()
        features[f'{col}_std'] = features[col].rolling(lookback).std()
    
    print(f"Created {len(features.columns)} features")
    
    # Save features
    features.to_parquet(output_path / f"{symbol}_15m_features.parquet")
    print(f"Saved to {output_path / f'{symbol}_15m_features.parquet'}")
    
    return features


# =============================================================================
# PHASE 3: CLUSTER DISCOVERY
# =============================================================================

def discover_clusters(features: pd.DataFrame, events: pd.DataFrame, 
                      symbol: str) -> dict:
    """
    Run K-Means clustering on winning event precursors.
    Goal: Find hidden state with Lift > 1.3x over baseline.
    """
    print(f"\n{'='*60}")
    print(f"PHASE 3: CLUSTER DISCOVERY - {symbol}")
    print(f"{'='*60}")
    
    # Merge features with events
    events_ts = pd.to_datetime(events['timestamp'])
    features['is_winning'] = features.index.isin(events_ts[events['is_winning']])
    
    # Select feature columns
    feat_cols = [c for c in features.columns if '_mean' in c or '_std' in c]
    feat_cols = [c for c in feat_cols if not features[c].isna().all()]
    
    print(f"Using {len(feat_cols)} aggregated features")
    
    # Prepare data
    wins_df = features[features['is_winning']].dropna(subset=feat_cols)
    non_wins_df = features[~features['is_winning']].dropna(subset=feat_cols)
    
    print(f"Winning samples: {len(wins_df):,}")
    print(f"Non-winning samples: {len(non_wins_df):,}")
    
    # Balanced sampling
    np.random.seed(42)
    n_sample = min(5000, len(wins_df), len(non_wins_df))  # Smaller for 15-min
    
    wins = wins_df.sample(n=n_sample)
    non_wins = non_wins_df.sample(n=n_sample)
    
    X_win = wins[feat_cols].values
    X_non = non_wins[feat_cols].values
    X_all = np.vstack([X_win, X_non])
    labels = np.array(['win']*len(X_win) + ['non']*len(X_non))
    
    # Scale
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_all)
    
    # Find optimal k
    print("\nFinding optimal cluster count...")
    best_k = 6
    best_score = -1
    
    for k in range(4, 10):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, cluster_labels)
        print(f"  k={k}: silhouette={score:.4f}")
        if score > best_score:
            best_score = score
            best_k = k
    
    print(f"\nOptimal k: {best_k}")
    
    # Cluster with optimal k
    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    
    # Analyze clusters
    print(f"\nCluster Analysis:")
    print("-"*70)
    print(f"{'Cluster':>8} {'Win Count':>10} {'Non Count':>10} {'Win Rate':>10} {'Lift':>10}")
    print("-"*70)
    
    hidden_states = []
    baseline_win_rate = len(X_win) / len(X_all)
    
    for c in range(best_k):
        mask = clusters == c
        wins_in = (labels[mask] == 'win').sum()
        non_in = (labels[mask] == 'non').sum()
        total_in = mask.sum()
        
        win_rate = wins_in / total_in if total_in > 0 else 0
        lift = win_rate / baseline_win_rate if baseline_win_rate > 0 else 0
        
        print(f"{c:>8} {wins_in:>10} {non_in:>10} {win_rate:>10.1%} {lift:>10.2f}x")
        
        if lift > 1.3:
            hidden_states.append({
                'cluster_id': c,
                'win_rate': win_rate,
                'lift': lift,
                'size': total_in,
                'centroid': kmeans.cluster_centers_[c],
                'centroid_raw': scaler.inverse_transform([kmeans.cluster_centers_[c]])[0]
            })
    
    print("-"*70)
    
    if hidden_states:
        print(f"\n*** Found {len(hidden_states)} Hidden State(s) with Lift > 1.3x ***")
    else:
        print("\n*** No Hidden States found with Lift > 1.3x ***")
        # Take best cluster anyway
        best_c = None
        best_lift = 0
        for c in range(best_k):
            mask = clusters == c
            wins_in = (labels[mask] == 'win').sum()
            total_in = mask.sum()
            win_rate = wins_in / total_in if total_in > 0 else 0
            lift = win_rate / baseline_win_rate if baseline_win_rate > 0 else 0
            if lift > best_lift:
                best_lift = lift
                best_c = c
        
        if best_c is not None:
            mask = clusters == best_c
            wins_in = (labels[mask] == 'win').sum()
            total_in = mask.sum()
            win_rate = wins_in / total_in if total_in > 0 else 0
            hidden_states.append({
                'cluster_id': best_c,
                'win_rate': win_rate,
                'lift': best_lift,
                'size': total_in,
                'centroid': kmeans.cluster_centers_[best_c],
                'centroid_raw': scaler.inverse_transform([kmeans.cluster_centers_[best_c]])[0]
            })
            print(f"Using best available cluster: {best_c} (Lift: {best_lift:.2f}x)")
    
    return {
        'hidden_states': hidden_states,
        'scaler': scaler,
        'kmeans': kmeans,
        'feat_cols': feat_cols,
        'baseline_win_rate': baseline_win_rate
    }


# =============================================================================
# PHASE 4: STRATEGY SYNTHESIS
# =============================================================================

def synthesize_strategy(cluster_results: dict, symbol: str) -> dict:
    """
    Extract Boolean logic for the best performing cluster.
    """
    print(f"\n{'='*60}")
    print(f"PHASE 4: STRATEGY SYNTHESIS - {symbol}")
    print(f"{'='*60}")
    
    if not cluster_results['hidden_states']:
        print("No hidden states to synthesize!")
        return None
    
    # Use best hidden state
    best_hs = max(cluster_results['hidden_states'], key=lambda x: x['lift'])
    
    print(f"\nBest Hidden State: Cluster {best_hs['cluster_id']}")
    print(f"  Win Rate: {best_hs['win_rate']:.1%}")
    print(f"  Lift: {best_hs['lift']:.2f}x")
    print(f"  Size: {best_hs['size']:,} samples")
    
    # Extract thresholds from centroid
    feat_cols = cluster_results['feat_cols']
    centroid_raw = best_hs['centroid_raw']
    
    print(f"\nDefining Feature Profile:")
    feature_profile = []
    
    for feat, val in sorted(zip(feat_cols, centroid_raw), 
                            key=lambda x: abs(x[1]), reverse=True)[:5]:
        direction = '>' if val > 0 else '<'
        print(f"  {feat} {direction} {val:.4f}")
        feature_profile.append({
            'feature': feat,
            'threshold': float(val),
            'direction': direction
        })
    
    # Calculate expected metrics
    hit_rate = best_hs['win_rate']
    target_atr = 2.0
    stop_atr = 1.0
    
    # With 2:1 R:R
    avg_win = target_atr  # 2.0 ATR
    avg_loss = stop_atr   # 1.0 ATR
    expectancy = (hit_rate * avg_win) - ((1 - hit_rate) * avg_loss)
    
    print(f"\nEXPECTED PERFORMANCE:")
    print(f"  Hit Rate: {hit_rate:.1%}")
    print(f"  Target: {target_atr} ATR")
    print(f"  Stop: {stop_atr} ATR (R:R = 2:1)")
    print(f"  Expectancy: {expectancy:.3f} ATR per trade")
    
    # Signal frequency (on balanced sample, not full data)
    signal_freq = best_hs['size'] / (cluster_results['baseline_win_rate'] * 2 * 5000)
    
    strategy = {
        'timeframe': '15min',
        'hit_rate': hit_rate,
        'lift': best_hs['lift'],
        'target_atr': target_atr,
        'stop_atr': stop_atr,
        'expectancy': expectancy,
        'signal_frequency': signal_freq,
        'feature_profile': feature_profile
    }
    
    return strategy


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def run_full_analysis():
    """Run complete Blind Backwards Analysis on 15-minute data."""
    
    print("="*70)
    print("15-MINUTE TIMEFRAME ELEVATION")
    print("BLIND BACKWARDS ANALYSIS - INTRADAY SWING STRATEGY")
    print("="*70)
    
    symbols = ['SPY', 'QQQ', 'IWM']
    all_results = {}
    
    for symbol in symbols:
        try:
            # Phase 0: Aggregate
            df_15m = aggregate_to_15min(symbol)
            
            # Phase 1: Identify targets
            events = identify_winning_events(df_15m, symbol)
            
            # Phase 2: Build features
            features = build_features_15m(df_15m, symbol)
            
            # Phase 3: Cluster discovery
            cluster_results = discover_clusters(features, events, symbol)
            
            # Phase 4: Synthesize strategy
            strategy = synthesize_strategy(cluster_results, symbol)
            
            if strategy:
                all_results[symbol] = strategy
        
        except Exception as e:
            print(f"\nERROR processing {symbol}: {e}")
            import traceback
            traceback.print_exc()
    
    # Final summary
    print("\n" + "="*70)
    print("FINAL SUMMARY: 15-MINUTE SWING STRATEGIES")
    print("="*70)
    
    for symbol, strat in all_results.items():
        print(f"\n{symbol}:")
        print(f"  Hit Rate: {strat['hit_rate']:.1%}")
        print(f"  Lift: {strat['lift']:.2f}x")
        print(f"  Expectancy: {strat['expectancy']:.3f} ATR/trade")
        print(f"  Signal Freq: {strat['signal_frequency']:.1%}")
    
    # Save results
    results_file = output_path / "15MIN_STRATEGY_RESULTS.json"
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n*** Results saved to {results_file} ***")
    
    # Trading frequency estimate
    print("\n" + "="*70)
    print("TRADING FREQUENCY ESTIMATE")
    print("="*70)
    
    for symbol, strat in all_results.items():
        # 15-min bars per day = 26 (9:30-16:00)
        # Trading days per month = 21
        bars_per_month = 26 * 21
        trades_per_month = bars_per_month * strat['signal_frequency']
        trades_per_week = trades_per_month / 4
        
        print(f"\n{symbol}:")
        print(f"  Trades/Week: ~{trades_per_week:.0f}")
        print(f"  Trades/Month: ~{trades_per_month:.0f}")
    
    return all_results


if __name__ == "__main__":
    results = run_full_analysis()
    sys.exit(0 if results else 1)
