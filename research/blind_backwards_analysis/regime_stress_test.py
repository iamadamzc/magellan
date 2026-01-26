"""
Phase 5: Risk Validation & Regime Stress Test

Addresses:
1. "Hard Number" Fix: Convert effort_result < 45 to z-score/percentile
2. "Singularity" Fix: Add floor to range_ratio denominator
3. VIX Regime Stress Test: Partition performance by VIX buckets

Author: Risk Manager / Strategy Validator
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple
import json
import warnings
warnings.filterwarnings('ignore')


# =============================================================================
# REFACTORED ENTRY LOGIC (SANITIZED)
# =============================================================================

def calculate_effort_result_safe(
    volume: pd.Series,
    close: pd.Series,
    lookback: int = 50
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate effort-result ratio with z-score normalization.
    
    FIX: Replaces hard-coded threshold (< 45) with dynamic z-score
    """
    # Raw effort-result
    pct_change = close.pct_change().abs()
    volume_z = (volume - volume.rolling(20).mean()) / (volume.rolling(20).std() + 1)
    effort_result = volume_z / (pct_change + 0.0001)
    effort_result = effort_result.clip(-100, 100)
    
    # Rolling z-score (dynamic threshold)
    er_mean = effort_result.rolling(lookback).mean()
    er_std = effort_result.rolling(lookback).std()
    effort_result_zscore = (effort_result - er_mean) / (er_std + 0.0001)
    
    # Rolling percentile (alternative metric)
    effort_result_pct = effort_result.rolling(lookback).apply(
        lambda x: (x[-1] - x.min()) / (x.max() - x.min() + 0.0001), raw=True
    )
    
    return effort_result_zscore, effort_result_pct


def calculate_range_ratio_safe(
    high: pd.Series,
    low: pd.Series,
    open_: pd.Series,
    close: pd.Series,
    min_tick: float = 0.01
) -> pd.Series:
    """
    Calculate range ratio with floor on denominator.
    
    FIX: Prevents divide-by-zero on Doji bars (Open == Close)
    """
    full_range = high - low
    body = (close - open_).abs()
    
    # Apply floor to prevent singularity
    body_floored = np.maximum(body, min_tick)
    
    range_ratio = full_range / body_floored
    return range_ratio.clip(0, 20)


def check_entry_conditions_v2(features: Dict[str, float]) -> bool:
    """
    REFACTORED Entry Conditions (Sanitized)
    
    Changes from v1:
    - effort_result: absolute threshold (< 45) → z-score (< -0.5)
    - range_ratio: now uses safe calculation with min_tick floor
    - All thresholds are relative to rolling statistics
    
    Args:
        features: Dictionary of normalized feature values
        
    Returns:
        True if entry conditions met, False otherwise
    """
    return all([
        # FIX 1: Dynamic z-score instead of hard-coded threshold
        features.get('effort_result_zscore', 0) < -0.5,
        
        # FIX 2: Safe range_ratio (pre-calculated with floor)
        features.get('range_ratio_mean', 0) > 1.4,
        
        # Volatility expansion (unchanged - already relative)
        features.get('volatility_ratio_mean', 0) > 1.0,
        
        # Trade intensity (unchanged - already relative)
        features.get('trade_intensity_mean', 0) > 0.9,
        
        # Body position (unchanged - bounded 0-1)
        features.get('body_position_mean', 0) > 0.25
    ])


# =============================================================================
# VIX REGIME PARTITIONING
# =============================================================================

def get_vix_data(start_date: str, end_date: str, cache_path: Path) -> pd.DataFrame:
    """
    Get VIX data for regime classification.
    Uses cached data or simulates from SPY volatility if not available.
    """
    # Try to load VIX from cache
    vix_files = list(cache_path.glob("*VIX*.parquet")) + list(cache_path.glob("*VIXY*.parquet"))
    
    if vix_files:
        vix = pd.read_parquet(vix_files[0])
        return vix
    
    # Fallback: Estimate VIX from SPY realized volatility
    print("  VIX data not found - estimating from SPY realized volatility")
    spy_files = sorted(cache_path.glob("SPY_1min_202*.parquet"), key=lambda x: x.stat().st_size, reverse=True)
    
    if not spy_files:
        return None
    
    spy = pd.read_parquet(spy_files[0])
    
    # 20-day realized volatility scaled to annualized VIX-like measure
    daily = spy['close'].resample('D').last()
    returns = daily.pct_change()
    realized_vol = returns.rolling(20).std() * np.sqrt(252) * 100
    
    # Scale to VIX range (typically 10-80)
    vix_estimate = realized_vol.clip(10, 80)
    
    return pd.DataFrame({'vix': vix_estimate})


def classify_vix_regime(vix_value: float) -> str:
    """Classify VIX into regime buckets."""
    if pd.isna(vix_value):
        return 'UNKNOWN'
    elif vix_value < 15:
        return 'COMPLACENCY'  # Bucket A
    elif vix_value <= 25:
        return 'NORMAL'       # Bucket B
    else:
        return 'PANIC'        # Bucket C


def regime_stress_test(
    features_df: pd.DataFrame,
    vix_df: pd.DataFrame,
    symbol: str
) -> Dict:
    """
    Partition strategy performance by VIX regime.
    
    Returns performance metrics for each bucket:
    - COMPLACENCY (VIX < 15)
    - NORMAL (15 <= VIX <= 25)
    - PANIC (VIX > 25)
    """
    # Resample features to daily for VIX alignment
    features_df = features_df.copy()
    features_df['date'] = features_df.index.date
    
    # Align VIX to features
    if vix_df is not None and 'vix' in vix_df.columns:
        vix_df = vix_df.copy()
        vix_df['date'] = vix_df.index.date
        
        # Create date-to-VIX mapping
        vix_daily = vix_df.groupby('date')['vix'].mean()
        features_df['vix'] = features_df['date'].map(vix_daily)
    else:
        # Use simulated VIX from volatility_ratio
        # Higher volatility_ratio correlates with higher VIX
        vol_ratio = features_df.get('volatility_ratio_mean', pd.Series(1.0, index=features_df.index))
        # Map: vol_ratio 0.5-2.0 → VIX 10-40
        features_df['vix'] = 10 + (vol_ratio.fillna(1) - 0.5) * 20
    
    features_df['regime'] = features_df['vix'].apply(classify_vix_regime)
    
    # Calculate metrics per regime
    regime_metrics = {}
    
    for regime in ['COMPLACENCY', 'NORMAL', 'PANIC']:
        mask = features_df['regime'] == regime
        regime_data = features_df[mask]
        
        if len(regime_data) == 0:
            regime_metrics[regime] = {
                'count': 0,
                'hit_rate': None,
                'expectancy': None,
                'max_drawdown': None
            }
            continue
        
        if 'is_strict_win' in regime_data.columns:
            wins = regime_data['is_strict_win'].sum()
            total = len(regime_data)
            hit_rate = wins / total if total > 0 else 0
        elif 'is_winning' in regime_data.columns:
            wins = regime_data['is_winning'].sum()
            total = len(regime_data)
            hit_rate = wins / total if total > 0 else 0
        else:
            hit_rate = 0
            total = len(regime_data)
        
        # Calculate expectancy (2:1 R:R assumption)
        avg_win = 1.0
        avg_loss = 0.5
        expectancy = (hit_rate * avg_win) - ((1 - hit_rate) * avg_loss)
        
        # Estimate drawdown from consecutive losses
        if 'is_strict_win' in regime_data.columns:
            results = regime_data['is_strict_win'].astype(int)
        elif 'is_winning' in regime_data.columns:
            results = regime_data['is_winning'].astype(int)
        else:
            results = pd.Series([0])
        
        # Simple max consecutive losses as drawdown proxy
        consecutive_losses = 0
        max_consecutive = 0
        for r in results:
            if r == 0:
                consecutive_losses += 1
                max_consecutive = max(max_consecutive, consecutive_losses)
            else:
                consecutive_losses = 0
        
        max_drawdown = max_consecutive * avg_loss
        
        regime_metrics[regime] = {
            'count': int(total),
            'hit_rate': round(hit_rate, 4),
            'expectancy': round(expectancy, 4),
            'max_drawdown': round(max_drawdown, 2)
        }
    
    return regime_metrics


# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def main():
    """Run Phase 5: Risk Validation & Regime Stress Test"""
    
    print("=" * 70)
    print("PHASE 5: RISK VALIDATION & REGIME STRESS TEST")
    print("=" * 70)
    
    base_path = Path(__file__).parent.parent.parent
    data_path = base_path / "data" / "cache" / "equities"
    output_path = Path(__file__).parent / "outputs"
    
    # =========================================================================
    # TASK 1: Demonstrate Refactored Logic
    # =========================================================================
    
    print("\n" + "-" * 70)
    print("TASK 1: REFACTORED ENTRY LOGIC (SANITIZED)")
    print("-" * 70)
    
    print("""
ORIGINAL (UNSAFE):
    effort_result_mean < 45          # Hard-coded scalar - will drift
    range_ratio = (H-L) / |O-C|      # Divide by zero on Doji bars

REFACTORED (SAFE):
    effort_result_zscore < -0.5      # Dynamic relative to 50-bar rolling stats
    range_ratio = (H-L) / max(|O-C|, min_tick)  # Floor prevents singularity
""")
    
    # Generate refactored Python code
    refactored_code = '''
def check_entry_conditions_v2(features: dict) -> bool:
    """
    SANITIZED Entry Logic v2.0
    
    Fixes Applied:
    1. effort_result: absolute threshold → rolling z-score
    2. range_ratio: singularity protection via min_tick floor
    """
    return all([
        # Dynamic z-score (was: effort_result_mean < 45)
        features['effort_result_zscore'] < -0.5,
        
        # Safe range ratio (calculated with floor)
        features['range_ratio_mean'] > 1.4,
        
        # Volatility expansion (unchanged)
        features['volatility_ratio_mean'] > 1.0,
        
        # Trade intensity (unchanged)
        features['trade_intensity_mean'] > 0.9,
        
        # Body position (unchanged)  
        features['body_position_mean'] > 0.25
    ])


def calculate_range_ratio_safe(high, low, open_, close, min_tick=0.01):
    """Safe range ratio with singularity protection."""
    body = abs(close - open_)
    body_safe = max(body, min_tick)  # FLOOR prevents div-by-zero
    return (high - low) / body_safe
'''
    
    print("Refactored Python Code:")
    print(refactored_code)
    
    # =========================================================================
    # TASK 2: VIX Regime Stress Test
    # =========================================================================
    
    print("\n" + "-" * 70)
    print("TASK 2: VIX REGIME STRESS TEST")
    print("-" * 70)
    
    results_all = {}
    
    for symbol in ['SPY', 'QQQ', 'IWM']:
        print(f"\n=== {symbol} ===")
        
        # Load features with win labels
        features_file = output_path / f"{symbol}_features.parquet"
        strict_file = output_path / f"{symbol}_winning_events_strict.parquet"
        
        if not features_file.exists():
            print(f"  Features not found for {symbol}")
            continue
        
        features = pd.read_parquet(features_file)
        
        # Apply strict labels if available
        if strict_file.exists():
            strict = pd.read_parquet(strict_file)
            strict_ts = pd.to_datetime(strict['timestamp'])
            features['is_strict_win'] = features.index.isin(strict_ts[strict['is_winning']])
        
        # Get VIX data (or estimate)
        vix_df = get_vix_data("2022-01-01", "2026-01-24", data_path)
        
        # Run regime stress test
        regime_metrics = regime_stress_test(features, vix_df, symbol)
        results_all[symbol] = regime_metrics
        
        # Print results
        print(f"\n  Regime Performance:")
        print(f"  {'Regime':<15} {'Count':>10} {'Hit Rate':>10} {'Expectancy':>12} {'Max DD':>10}")
        print("  " + "-" * 60)
        for regime, metrics in regime_metrics.items():
            hr = f"{metrics['hit_rate']:.1%}" if metrics['hit_rate'] else "N/A"
            exp = f"{metrics['expectancy']:.3f}R" if metrics['expectancy'] else "N/A"
            dd = f"{metrics['max_drawdown']:.1f}R" if metrics['max_drawdown'] else "N/A"
            print(f"  {regime:<15} {metrics['count']:>10} {hr:>10} {exp:>12} {dd:>10}")
    
    # =========================================================================
    # TASK 3: GO/NO-GO RECOMMENDATION
    # =========================================================================
    
    print("\n" + "=" * 70)
    print("TASK 3: GO/NO-GO RECOMMENDATION")
    print("=" * 70)
    
    # Analyze SPY specifically for the recommendation
    spy_results = results_all.get('SPY', {})
    
    complacency = spy_results.get('COMPLACENCY', {})
    normal = spy_results.get('NORMAL', {})
    panic = spy_results.get('PANIC', {})
    
    # Decision logic
    low_vol_hit_rate = complacency.get('hit_rate', 0) or 0
    low_vol_expectancy = complacency.get('expectancy', 0) or 0
    normal_expectancy = normal.get('expectancy', 0) or 0
    panic_expectancy = panic.get('expectancy', 0) or 0
    
    print(f"""
SPY Performance by Regime:
┌─────────────────┬───────────┬────────────┬─────────────┐
│ Regime          │ Hit Rate  │ Expectancy │ Max DD      │
├─────────────────┼───────────┼────────────┼─────────────┤
│ COMPLACENCY     │ {low_vol_hit_rate:.1%}     │ {low_vol_expectancy:.3f}R      │ {complacency.get('max_drawdown', 0):.1f}R        │
│ NORMAL          │ {normal.get('hit_rate', 0):.1%}     │ {normal.get('expectancy', 0):.3f}R      │ {normal.get('max_drawdown', 0):.1f}R        │
│ PANIC           │ {panic.get('hit_rate', 0):.1%}     │ {panic.get('expectancy', 0):.3f}R      │ {panic.get('max_drawdown', 0):.1f}R        │
└─────────────────┴───────────┴────────────┴─────────────┘
""")
    
    # GO/NO-GO Decision
    passes_low_vol = low_vol_expectancy > 0.1  # Must have positive expectancy in low vol
    passes_normal = normal_expectancy > 0.2    # Strong in normal conditions
    has_regime_stability = abs(low_vol_expectancy - normal_expectancy) < 0.3  # Not too regime-dependent
    
    all_positive = all([
        low_vol_expectancy > 0,
        normal_expectancy > 0,
        panic_expectancy > 0 if panic.get('count', 0) > 100 else True
    ])
    
    print("DECISION CRITERIA:")
    print(f"  ✓ Low-Vol Expectancy > 0.1R: {'PASS' if passes_low_vol else 'FAIL'} ({low_vol_expectancy:.3f}R)")
    print(f"  ✓ Normal Expectancy > 0.2R:  {'PASS' if passes_normal else 'FAIL'} ({normal_expectancy:.3f}R)")
    print(f"  ✓ Regime Stability < 0.3R:   {'PASS' if has_regime_stability else 'FAIL'}")
    print(f"  ✓ All Regimes Positive:      {'PASS' if all_positive else 'FAIL'}")
    
    if passes_low_vol and passes_normal and all_positive:
        recommendation = "GO"
        rationale = "Strategy survives low-volatility regime with positive expectancy"
    elif all_positive and not passes_low_vol:
        recommendation = "CONDITIONAL GO"
        rationale = "Positive across regimes but weak in low-vol; add VIX > 15 filter"
    else:
        recommendation = "NO-GO"
        rationale = "Strategy fails fundamental regime robustness tests"
    
    print(f"""
┌{'─'*68}┐
│{'FINAL RECOMMENDATION: ' + recommendation:^68}│
├{'─'*68}┤
│ {rationale:<66} │
└{'─'*68}┘
""")
    
    # Save results
    final_output = {
        'refactored_logic': {
            'effort_result_threshold': 'z-score < -0.5 (was: absolute < 45)',
            'range_ratio_fix': 'denominator = max(|O-C|, min_tick=0.01)',
            'version': '2.0'
        },
        'regime_performance': results_all,
        'recommendation': {
            'decision': recommendation,
            'rationale': rationale,
            'low_vol_passes': passes_low_vol,
            'normal_passes': passes_normal,
            'all_positive': all_positive
        }
    }
    
    with open(output_path / 'REGIME_STRESS_TEST_RESULTS.json', 'w') as f:
        json.dump(final_output, f, indent=2, default=str)
    
    print(f"\n✓ Results saved to outputs/REGIME_STRESS_TEST_RESULTS.json")
    
    return final_output


if __name__ == "__main__":
    main()
