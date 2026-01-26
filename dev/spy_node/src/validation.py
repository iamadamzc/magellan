"""
Walk-Forward Validation Engine
Validates alpha signals on unseen data before allowing live trading.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict


def run_walk_forward_check(
    df: pd.DataFrame,
    alpha_col: str,
    target_col: str = 'log_return',
    in_sample_pct: float = 0.70,
    horizon: int = 15
) -> Dict:
    """
    Run walk-forward validation to test alpha signal on unseen data.
    
    Split Logic:
    - First 70% of data: "In-Sample" for observing signal behavior
    - Last 30%: "Out-of-Sample" for validation
    
    Metrics:
    - Hit Rate: Percentage of times signal direction matches return direction
    - Expected Profitability: Simulated P&L assuming signal-based trades
    
    Args:
        df: DataFrame with alpha signal and target columns
        alpha_col: Name of the alpha signal column (e.g., 'alpha_score')
        target_col: Name of the target return column (e.g., 'log_return')
        in_sample_pct: Percentage of data for in-sample (default: 0.70)
        horizon: Forward return horizon in bars (default: 15)
    
    Returns:
        Dict with validation metrics and pass/fail status
    """
    # Create working copy
    working_df = df[[alpha_col, target_col]].copy()
    
    # Create forward returns
    working_df['forward_return'] = working_df[target_col].shift(-horizon)
    
    # Drop NaN values
    working_df = working_df.dropna()
    
    if len(working_df) < 100:
        print("[VALIDATION] Insufficient data for walk-forward check")
        return {
            'passed': False,
            'reason': 'INSUFFICIENT_DATA',
            'in_sample_hit_rate': None,
            'out_sample_hit_rate': None,
            'expected_pnl': None
        }
    
    # Split data
    split_idx = int(len(working_df) * in_sample_pct)
    in_sample = working_df.iloc[:split_idx].copy()
    out_sample = working_df.iloc[split_idx:].copy()
    
    print(f"[VALIDATION] In-Sample: {len(in_sample)} bars | Out-of-Sample: {len(out_sample)} bars")
    
    # Calculate signal direction
    # Alpha score > median = bullish signal (expect positive return)
    # Alpha score < median = bearish signal (expect negative return)
    
    # In-Sample metrics
    is_median = in_sample[alpha_col].median()
    in_sample.loc[:, 'signal'] = np.where(in_sample[alpha_col] > is_median, 1, -1)
    in_sample.loc[:, 'correct'] = (in_sample['signal'] * in_sample['forward_return']) > 0
    is_hit_rate = in_sample['correct'].mean()
    is_pnl = (in_sample['signal'] * in_sample['forward_return']).sum()
    
    # Out-of-Sample metrics (using in-sample median as threshold - no look-ahead)
    out_sample.loc[:, 'signal'] = np.where(out_sample[alpha_col] > is_median, 1, -1)
    out_sample.loc[:, 'correct'] = (out_sample['signal'] * out_sample['forward_return']) > 0
    os_hit_rate = out_sample['correct'].mean()
    os_pnl = (out_sample['signal'] * out_sample['forward_return']).sum()
    
    # Calculate expected profitability (annualized estimate)
    # Assuming 1-minute bars, 390 bars per trading day
    avg_trade_return = os_pnl / len(out_sample) if len(out_sample) > 0 else 0
    expected_daily_pnl = avg_trade_return * 390
    
    # Validation pass criteria: Out-of-Sample Hit Rate >= 51%
    passed = os_hit_rate >= 0.51
    
    result = {
        'passed': passed,
        'reason': 'VALIDATION_PASSED' if passed else 'HIT_RATE_BELOW_THRESHOLD',
        'in_sample_bars': len(in_sample),
        'out_sample_bars': len(out_sample),
        'in_sample_hit_rate': is_hit_rate,
        'out_sample_hit_rate': os_hit_rate,
        'in_sample_pnl': is_pnl,
        'out_sample_pnl': os_pnl,
        'expected_daily_pnl': expected_daily_pnl,
        'signal_threshold': is_median
    }
    
    return result


def print_validation_scorecard(result: Dict) -> None:
    """
    Print a formatted Validation Scorecard.
    
    Args:
        result: Dict returned from run_walk_forward_check()
    """
    print("\n" + "=" * 60)
    print("[VALIDATION SCORECARD] Walk-Forward Analysis")
    print("=" * 60)
    
    if result.get('reason') == 'INSUFFICIENT_DATA':
        print("[ERROR] Insufficient data for validation")
        return
    
    # Header
    print(f"{'Metric':<30} {'In-Sample':<15} {'Out-of-Sample':<15}")
    print("-" * 60)
    
    # Bar counts
    print(f"{'Bars Analyzed':<30} {result['in_sample_bars']:<15} {result['out_sample_bars']:<15}")
    
    # Hit rates
    is_hr = f"{result['in_sample_hit_rate']*100:.2f}%"
    os_hr = f"{result['out_sample_hit_rate']*100:.2f}%"
    print(f"{'Hit Rate':<30} {is_hr:<15} {os_hr:<15}")
    
    # P&L
    is_pnl = f"{result['in_sample_pnl']*10000:.2f} bps"
    os_pnl = f"{result['out_sample_pnl']*10000:.2f} bps"
    print(f"{'Cumulative P&L':<30} {is_pnl:<15} {os_pnl:<15}")
    
    print("-" * 60)
    
    # Expected profitability
    print(f"{'Expected Daily P&L':<30} {result['expected_daily_pnl']*10000:.2f} bps")
    print(f"{'Signal Threshold':<30} {result['signal_threshold']:.4f}")
    
    # Decay detection
    hr_decay = result['in_sample_hit_rate'] - result['out_sample_hit_rate']
    if hr_decay > 0.05:
        print(f"\n[WARNING] Hit Rate Decay: {hr_decay*100:.2f}% (potential overfitting)")
    
    print("=" * 60)
    
    # Final verdict
    if result['passed']:
        print("[VERDICT] VALIDATION PASSED - Signal is reliable for trading")
    else:
        print("[VERDICT] VALIDATION FAILED - Signal is NOT reliable")
    
    print("=" * 60)


def run_optimized_walk_forward_check(
    df: pd.DataFrame,
    feature_cols: list = None,
    target_col: str = 'log_return',
    in_sample_pct: float = 0.70,
    horizon: int = 15,
    static_weights: Dict[str, float] = None
) -> Dict:
    """
    Run walk-forward validation with dynamic weight optimization.
    
    Process:
    1. Split data into In-Sample (70%) and Out-of-Sample (30%)
    2. Optimize weights on In-Sample data (no look-ahead bias)
    3. Test optimized weights on Out-of-Sample data
    4. Compare against static weights performance
    
    Args:
        df: DataFrame with feature and target columns
        feature_cols: List of feature columns to weight
        target_col: Name of target return column
        in_sample_pct: Percentage for in-sample (default: 0.70)
        horizon: Forward return horizon in bars
        static_weights: Dict of static weights for comparison
    
    Returns:
        Dict with validation metrics, optimal weights, and comparison
    """
    from src.optimizer import optimize_alpha_weights, calculate_alpha_with_weights
    
    if feature_cols is None:
        feature_cols = ['rsi_14', 'volume_zscore']
    
    if static_weights is None:
        static_weights = {'rsi_14': 0.6, 'volume_zscore': 0.4}
    
    # Create working copy with forward returns
    cols_needed = feature_cols + [target_col]
    working_df = df[cols_needed].copy()
    working_df['forward_return'] = working_df[target_col].shift(-horizon)
    working_df = working_df.dropna()
    
    if len(working_df) < 100:
        print("[OPTIMIZER] Insufficient data for optimized walk-forward check")
        return {
            'passed': False,
            'reason': 'INSUFFICIENT_DATA',
            'optimal_weights': static_weights,
            'static_hit_rate': None,
            'optimized_hit_rate': None
        }
    
    # Split data
    split_idx = int(len(working_df) * in_sample_pct)
    in_sample = working_df.iloc[:split_idx].copy()
    out_sample = working_df.iloc[split_idx:].copy()
    
    print(f"[OPTIMIZER] In-Sample: {len(in_sample)} bars | Out-of-Sample: {len(out_sample)} bars")
    
    # Step 1: Optimize weights on In-Sample data
    print("[OPTIMIZER] Finding optimal weights on In-Sample data...")
    opt_result = optimize_alpha_weights(
        in_sample,
        feature_cols=feature_cols,
        target_col=target_col,
        horizon=0,  # Already shifted
        metric='hit_rate'
    )
    optimal_weights = opt_result['optimal_weights']
    
    # Step 2: Calculate alpha scores for both weight sets
    # Static weights
    static_alpha_is = calculate_alpha_with_weights(in_sample, static_weights)
    static_alpha_os = calculate_alpha_with_weights(out_sample, static_weights)
    
    # Optimized weights
    opt_alpha_is = calculate_alpha_with_weights(in_sample, optimal_weights)
    opt_alpha_os = calculate_alpha_with_weights(out_sample, optimal_weights)
    
    # Step 3: Calculate hit rates for both
    def calc_hit_rate(alpha_series, returns, threshold=None):
        if threshold is None:
            threshold = alpha_series.median()
        signal = np.where(alpha_series > threshold, 1, -1)
        correct = (signal * returns.values) > 0
        return correct.mean(), threshold
    
    # Static weights performance
    static_is_hr, static_is_thresh = calc_hit_rate(static_alpha_is, in_sample['forward_return'])
    static_os_hr, _ = calc_hit_rate(static_alpha_os, out_sample['forward_return'], static_is_thresh)
    
    # Optimized weights performance
    opt_is_hr, opt_is_thresh = calc_hit_rate(opt_alpha_is, in_sample['forward_return'])
    opt_os_hr, _ = calc_hit_rate(opt_alpha_os, out_sample['forward_return'], opt_is_thresh)
    
    # Step 4: Calculate P&L
    static_signal_os = np.where(static_alpha_os > static_is_thresh, 1, -1)
    static_pnl = (static_signal_os * out_sample['forward_return'].values).sum()
    
    opt_signal_os = np.where(opt_alpha_os > opt_is_thresh, 1, -1)
    opt_pnl = (opt_signal_os * out_sample['forward_return'].values).sum()
    
    # Validation pass criteria
    passed = opt_os_hr >= 0.51
    
    result = {
        'passed': passed,
        'reason': 'VALIDATION_PASSED' if passed else 'HIT_RATE_BELOW_THRESHOLD',
        'optimal_weights': optimal_weights,
        'static_weights': static_weights,
        'weights_tested': opt_result['weights_tested'],
        'in_sample_bars': len(in_sample),
        'out_sample_bars': len(out_sample),
        # Static performance
        'static_is_hit_rate': static_is_hr,
        'static_os_hit_rate': static_os_hr,
        'static_pnl': static_pnl,
        # Optimized performance
        'optimized_is_hit_rate': opt_is_hr,
        'optimized_os_hit_rate': opt_os_hr,
        'optimized_pnl': opt_pnl,
        # Improvement
        'hr_improvement': opt_os_hr - static_os_hr,
        'pnl_improvement': opt_pnl - static_pnl
    }
    
    return result


def print_optimized_scorecard(result: Dict) -> None:
    """
    Print formatted scorecard comparing static vs optimized weights.
    
    Args:
        result: Dict from run_optimized_walk_forward_check()
    """
    print("\n" + "=" * 60)
    print("[OPTIMIZER] Dynamic Weight Optimization Results")
    print("=" * 60)
    
    if result.get('reason') == 'INSUFFICIENT_DATA':
        print("[ERROR] Insufficient data for optimization")
        return
    
    # Display optimal weights found
    print("\n[OPTIMIZER] Best Weights Found:")
    for feature, weight in result['optimal_weights'].items():
        display = feature.replace('rsi_14', 'RSI').replace('volume_zscore', 'Vol').replace('sentiment', 'Sent')
        print(f"  {display}: {weight*100:.0f}%")
    
    print(f"\nWeights tested: {result['weights_tested']} combinations")
    print("-" * 60)
    
    # Comparison table
    print(f"\n{'Metric':<25} {'Static (40/30/30)':<20} {'Optimized':<20}")
    print("-" * 60)
    
    # In-Sample Hit Rate
    static_is = f"{result['static_is_hit_rate']*100:.2f}%"
    opt_is = f"{result['optimized_is_hit_rate']*100:.2f}%"
    print(f"{'In-Sample Hit Rate':<25} {static_is:<20} {opt_is:<20}")
    
    # Out-of-Sample Hit Rate (THE KEY METRIC)
    static_os = f"{result['static_os_hit_rate']*100:.2f}%"
    opt_os = f"{result['optimized_os_hit_rate']*100:.2f}%"
    delta = result['hr_improvement'] * 100
    delta_str = f"({'+' if delta >= 0 else ''}{delta:.2f}%)"
    print(f"{'Out-of-Sample Hit Rate':<25} {static_os:<20} {opt_os:<17} {delta_str}")
    
    # P&L
    static_pnl = f"{result['static_pnl']*10000:.2f} bps"
    opt_pnl = f"{result['optimized_pnl']*10000:.2f} bps"
    print(f"{'Out-of-Sample P&L':<25} {static_pnl:<20} {opt_pnl:<20}")
    
    print("=" * 60)
    
    # Verdict
    if result['passed']:
        print("[VERDICT] VALIDATION PASSED - Optimized signal is reliable")
    else:
        print("[VERDICT] VALIDATION FAILED - Signal remains unreliable")
    
    print("=" * 60)

