

# =============================================================================
# VOLATILITY EXPANSION ENTRY - Feature Engineering
# Discovered via blind backwards analysis on 2.46M 1-minute bars
# =============================================================================

import pandas as pd
import numpy as np
from src.logger import LOG


def calculate_effort_result(
    df: pd.DataFrame,
    volume_period: int = 20
) -> pd.Series:
    """
    Calculate raw effort-result ratio.
    
    Effort-Result = Volume Z-Score / |Price Change|
    Higher values indicate absorption (volume without price movement)
    
    Args:
        df: DataFrame with 'volume' and 'close' columns
        volume_period: Period for volume z-score calculation (default 20)
    
    Returns:
        Series of effort_result values (clipped -100 to 100)
    """
    # Calculate volume z-score
    vol_mean = df['volume'].rolling(volume_period).mean()
    vol_std = df['volume'].rolling(volume_period).std()
    volume_z = (df['volume'] - vol_mean) / (vol_std + 1)
    volume_z = volume_z.clip(-5, 5)
    
    # Calculate effort-result ratio
    pct_change = df['close'].pct_change().abs()
    effort_result = volume_z / (pct_change + 0.0001)
    effort_result = effort_result.clip(-100, 100)
    
    return effort_result


def calculate_effort_result_zscore(
    df: pd.DataFrame,
    volume_period: int = 20,
    zscore_window: int = 50
) -> pd.Series:
    """
    Calculate effort-result ratio with z-score normalization.
    
    Effort-Result = Volume Z-Score / |Price Change|
    Higher values indicate absorption (volume without price movement)
    Lower z-scores (< -0.5) indicate efficient price movement
    
    Args:
        df: DataFrame with 'volume' and 'close' columns
        volume_period: Period for volume z-score calculation (default 20)
        zscore_window: Rolling window for z-score normalization (default 50)
    
    Returns:
        Series of effort_result z-scores
    """
    # Get raw effort result
    effort_result = calculate_effort_result(df, volume_period=volume_period)
    
    # Apply rolling z-score normalization
    er_mean = effort_result.rolling(zscore_window).mean()
    er_std = effort_result.rolling(zscore_window).std()
    effort_result_zscore = (effort_result - er_mean) / (er_std + 0.0001)
    
    return effort_result_zscore


def calculate_range_ratio_safe(
    df: pd.DataFrame,
    min_tick: float = 0.01
) -> pd.Series:
    """
    Calculate range ratio with singularity protection.
    
    Range Ratio = (High - Low) / max(|Open - Close|, min_tick)
    
    Protection prevents divide-by-zero on Doji bars (Open == Close)
    
    Args:
        df: DataFrame with 'high', 'low', 'open', 'close' columns
        min_tick: Minimum value for denominator (default 0.01)
    
    Returns:
        Series of safe range ratios
    """
    full_range = df['high'] - df['low']
    body = (df['close'] - df['open']).abs()
    
    # Apply floor to prevent divide-by-zero
    body_safe = np.maximum(body, min_tick)
    
    range_ratio = full_range / body_safe
    return range_ratio.clip(0, 20)


def calculate_volatility_ratio(
    df: pd.DataFrame,
    short_period: int = 5,
    long_period: int = 20
) -> pd.Series:
    """
    Calculate volatility ratio (ATR short / ATR long).
    
    Values > 1.0 indicate volatility expansion
    Values < 1.0 indicate volatility compression
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        short_period: Short ATR period (default 5)
        long_period: Long ATR period (default 20)
    
    Returns:
        Series of volatility ratios
    """
    # Calculate True Range
    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - df['close'].shift(1)).abs()
    tr3 = (df['low'] - df['close'].shift(1)).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Calculate ATR for both periods
    atr_short = true_range.rolling(short_period).mean()
    atr_long = true_range.rolling(long_period).mean()
    
    # Calculate ratio
    volatility_ratio = atr_short / (atr_long + 0.0001)
    return volatility_ratio.clip(0, 5)


def calculate_trade_intensity(
    df: pd.DataFrame,
    period: int = 20
) -> pd.Series:
    """
    Calculate trade intensity relative to rolling average.
    
    Trade Intensity = Trade Count / Rolling Mean(Trade Count)
    
    Args:
        df: DataFrame with 'trade_count' column
        period: Rolling average period (default 20)
    
    Returns:
        Series of trade intensity ratios
    """
    if 'trade_count' not in df.columns:
        # Fallback: Use volume as proxy if trade_count unavailable
        tc_mean = df['volume'].rolling(period).mean()
        trade_intensity = df['volume'] / (tc_mean + 1)
    else:
        tc_mean = df['trade_count'].rolling(period).mean()
        trade_intensity = df['trade_count'] / (tc_mean + 1)
    
    return trade_intensity.clip(0, 5)


def calculate_body_position(df: pd.DataFrame) -> pd.Series:
    """
    Calculate where the close price sits within the bar's range.
    
    Body Position = (Close - Low) / (High - Low)
    
    0.0 = Close at low (bearish)
    0.5 = Close at midpoint
    1.0 = Close at high (bullish)
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
    
    Returns:
        Series of body positions (0-1)
    """
    full_range = df['high'] - df['low']
    body_position = (df['close'] - df['low']) / (full_range + 0.0001)
    return body_position.clip(0, 1)


def add_vol_expansion_features(
    df: pd.DataFrame,
    config: dict = None
) -> pd.DataFrame:
    """
    Add all Volatility Expansion Entry features to a DataFrame.
    
    Calculates all features needed for the vol expansion strategy:
    - effort_result_zscore: Volume absorption metric (z-score normalized)
    - range_ratio: Bar topology metric (with singularity protection)
    - volatility_ratio: ATR expansion/compression indicator
    - trade_intensity: Trade activity relative to average
    - body_position: Close location within bar range
    
    Additionally calculates aggregated features (mean/std/trend) over lookback window.
    
    Args:
        df: DataFrame with OHLCV data
        config: Optional configuration dict with parameters:
            - volume_zscore_period: int (default 20)
            - rolling_zscore_window: int (default 50)
            - min_tick_floor: float (default 0.01)
            - atr_short_period: int (default 5)
            - atr_long_period: int (default 20)
            - trade_intensity_period: int (default 20)
            - feature_lookback: int (default 50)
    
    Returns:
        DataFrame with new feature columns added (mutates in-place)
    """
    # Extract config parameters
    if config is None:
        config = {}
    
    volume_period = config.get('volume_zscore_period', 20)
    zscore_window = config.get('rolling_zscore_window', 50)
    min_tick = config.get('min_tick_floor', 0.01)
    atr_short = config.get('atr_short_period', 5)
    atr_long = config.get('atr_long_period', 20)
    ti_period = config.get('trade_intensity_period', 20)
    lookback = config.get('feature_lookback', 50)
    
    # Calculate core features
    # CRITICAL: Calculate BOTH raw effort_result AND zscore version
    # Research used effort_result_mean (raw), not zscore!
    df['effort_result'] = calculate_effort_result(
        df, volume_period=volume_period
    )
    
    df['effort_result_zscore'] = calculate_effort_result_zscore(
        df, volume_period=volume_period, zscore_window=zscore_window
    )
    
    df['range_ratio'] = calculate_range_ratio_safe(df, min_tick=min_tick)
    
    df['volatility_ratio'] = calculate_volatility_ratio(
        df, short_period=atr_short, long_period=atr_long
    )
    
    df['trade_intensity'] = calculate_trade_intensity(df, period=ti_period)
    
    df['body_position'] = calculate_body_position(df)
    
    # Calculate aggregated features over lookback window
    core_features = [
        'effort_result',  # Raw version for research thresholds
        'effort_result_zscore',  # Z-score version for v2.0 logic
        'range_ratio',
        'volatility_ratio',
        'trade_intensity',
        'body_position'
    ]
    
    for feat in core_features:
        # Rolling mean
        df[f'{feat}_mean'] = df[feat].rolling(lookback).mean()
        
        # Rolling std
        df[f'{feat}_std'] = df[feat].rolling(lookback).std()
        
        # Trend (end - start over window)
        df[f'{feat}_trend'] = df[feat].diff(lookback)
    
    LOG.info(f"[VOL_EXPANSION] Added {len(core_features)} core + {len(core_features)*3} aggregated features")
    
    return df


def check_vol_expansion_entry(row: pd.Series, config: dict = None) -> bool:
    """
    Check if current bar meets Volatility Expansion Entry conditions v2.0.
    
    Entry Conditions (ALL must be true):
    1. effort_result_zscore < -0.5 (low absorption, efficient movement)
    2. range_ratio_mean > 1.4 (wide bars indicating momentum)
    3. volatility_ratio_mean > 1.0 (volatility expanding)
    4. trade_intensity_mean > 0.9 (normal liquidity)
    5. body_position_mean > 0.25 (bullish bar structure)
    
    Args:
        row: DataFrame row with feature columns
        config: Optional config dict with threshold overrides
    
    Returns:
        True if entry conditions met, False otherwise
    """
    if config is None:
        config = {}
    
    # Extract thresholds from config
    effort_max = config.get('effort_result_zscore_max', -0.5)
    range_min = config.get('range_ratio_mean_min', 1.4)
    vol_min = config.get('volatility_ratio_min', 1.0)
    ti_min = config.get('trade_intensity_min', 0.9)
    bp_min = config.get('body_position_min', 0.25)
    
    # Check all conditions
    return all([
        row.get('effort_result_zscore', 0) < effort_max,
        row.get('range_ratio_mean', 0) > range_min,
        row.get('volatility_ratio_mean', 0) > vol_min,
        row.get('trade_intensity_mean', 0) > ti_min,
        row.get('body_position_mean', 0) > bp_min
    ])
