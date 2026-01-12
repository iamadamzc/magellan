"""
Dynamic Weight Optimizer
Finds optimal alpha factor weights for current market conditions using grid search.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from scipy.stats import spearmanr

from src.config_loader import EngineConfig

# Retrain interval for weight optimization (trading days) - loaded from config
RETRAIN_INTERVAL = EngineConfig().get('RETRAIN_INTERVAL', strict=True)


def optimize_alpha_weights(
    df: pd.DataFrame,
    feature_cols: List[str] = None,
    target_col: str = 'log_return',
    horizon: int = 15,
    metric: str = 'hit_rate',
    weight_step: float = 0.1
) -> Dict:
    """
    Find optimal weights for alpha factors using grid search.
    
    Searches weight combinations that sum to 1.0 and maximizes the target metric.
    
    Args:
        df: DataFrame with feature and target columns
        feature_cols: List of feature column names (default: ['rsi_14', 'volume_zscore', 'sentiment'])
        target_col: Name of target return column
        horizon: Forward return horizon in bars
        metric: Optimization target - 'hit_rate' or 'ic' (Information Coefficient)
        weight_step: Step size for grid search (default: 0.1 = 10% increments)
    
    Returns:
        Dict with optimal weights and performance metrics
    """
    if feature_cols is None:
        feature_cols = ['rsi_14', 'volume_zscore', 'sentiment']
    
    # Create working copy with forward returns
    working_df = df[feature_cols + [target_col]].copy()
    working_df['forward_return'] = working_df[target_col].shift(-horizon)
    working_df = working_df.dropna()
    
    if len(working_df) < 50:
        # print("[OPTIMIZER] Insufficient data for optimization")
        return {
            'optimal_weights': {col: 1.0/len(feature_cols) for col in feature_cols},
            'best_metric': 0.0,
            'weights_tested': 0
        }
    
    # Normalize features to 0-1 range for fair weighting
    normalized = {}
    for col in feature_cols:
        col_min = working_df[col].min()
        col_max = working_df[col].max()
        col_range = col_max - col_min
        if col_range > 0:
            normalized[col] = (working_df[col] - col_min) / col_range
        else:
            normalized[col] = pd.Series(0.5, index=working_df.index)
    
    # Generate weight combinations that sum to 1.0
    weight_options = np.arange(0.0, 1.0 + weight_step, weight_step)
    weight_combos = []
    
    for w1 in weight_options:
        for w2 in weight_options:
            w3 = 1.0 - w1 - w2
            if 0.0 <= w3 <= 1.0:
                # Round to avoid floating point issues
                w3 = round(w3, 2)
                weight_combos.append((round(w1, 2), round(w2, 2), w3))
    
    # Remove duplicates
    weight_combos = list(set(weight_combos))
    
    best_metric = -999
    best_weights = None
    results_log = []
    
    for weights in weight_combos:
        # Calculate weighted alpha score
        alpha_score = sum(
            weights[i] * normalized[feature_cols[i]] 
            for i in range(len(feature_cols))
        )
        
        # Calculate metric
        if metric == 'hit_rate':
            # Signal direction based on median
            median_alpha = alpha_score.median()
            signal = np.where(alpha_score > median_alpha, 1, -1)
            correct = (signal * working_df['forward_return'].values) > 0
            score = correct.mean()
        else:  # 'ic'
            # Spearman correlation
            score, _ = spearmanr(alpha_score, working_df['forward_return'])
            if pd.isna(score):
                score = 0.0
        
        results_log.append({
            'weights': weights,
            'score': score
        })
        
        if score > best_metric:
            best_metric = score
            best_weights = weights
    
    # Build result
    optimal_weights = {
        feature_cols[i]: best_weights[i] 
        for i in range(len(feature_cols))
    }
    
    return {
        'optimal_weights': optimal_weights,
        'best_metric': best_metric,
        'metric_type': metric,
        'weights_tested': len(weight_combos),
        'feature_cols': feature_cols
    }


def calculate_alpha_with_weights(
    df: pd.DataFrame,
    weights: Dict[str, float]
) -> pd.Series:
    """
    Calculate alpha score using specified weights.
    
    Args:
        df: DataFrame with feature columns
        weights: Dict mapping feature names to weights
    
    Returns:
        Series with weighted alpha scores
    """
    feature_cols = list(weights.keys())
    
    # Normalize features to 0-1 range
    normalized = {}
    for col in feature_cols:
        col_min = df[col].min()
        col_max = df[col].max()
        col_range = col_max - col_min
        if col_range > 0:
            normalized[col] = (df[col] - col_min) / col_range
        else:
            normalized[col] = pd.Series(0.5, index=df.index)
    
    # Calculate weighted sum
    alpha_score = sum(
        weights[col] * normalized[col] 
        for col in feature_cols
    )
    
    return alpha_score


def print_optimizer_result(result: Dict, static_weights: Dict[str, float] = None) -> None:
    """
    Print optimizer results with comparison to static weights.
    
    Args:
        result: Dict from optimize_alpha_weights()
        static_weights: Optional dict of static weights for comparison
    """
    """
    print("\n" + "=" * 60)
    print("[OPTIMIZER] Weight Optimization Results")
    print("=" * 60)
    
    print(f"Weights tested: {result['weights_tested']} combinations")
    print(f"Target metric: {result['metric_type'].upper()}")
    print("-" * 60)
    
    # Display optimal weights
    print("\n[OPTIMIZER] Best Weights Found:")
    for feature, weight in result['optimal_weights'].items():
        # Clean feature name for display
        display_name = feature.replace('_', ' ').title()
        if feature == 'rsi_14':
            display_name = 'RSI'
        elif feature == 'volume_zscore':
            display_name = 'Vol'
        elif feature == 'sentiment':
            display_name = 'Sent'
        print(f"  {display_name}: {weight*100:.0f}%")
    
    print(f"\nBest In-Sample {result['metric_type'].upper()}: {result['best_metric']:.4f}")
    
    # Compare to static if provided
    if static_weights:
        print("\n[COMPARISON] Static vs Optimized Weights:")
        print(f"  {'Feature':<15} {'Static':<10} {'Optimized':<10}")
        print("  " + "-" * 35)
        for feature in result['optimal_weights']:
            static = static_weights.get(feature, 0)
            optimal = result['optimal_weights'][feature]
            display = feature.replace('_14', '').replace('_zscore', '').title()
            print(f"  {display:<15} {static*100:>6.0f}%    {optimal*100:>6.0f}%")
    
    print("=" * 60)
    """
    pass
