"""
Phase 2: Feature Engineering - Stationary Feature Vector Construction

Creates stationary features from raw OHLCV data:
- Velocity & Acceleration (price derivatives)
- Volume Force (effort vs. result analysis)
- Bar Topology (compression/expansion detection)
- Autocorrelation (market regime)

All features use differencing and ratios for stationarity.
NO classic patterns or standard indicators used.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple
import warnings
warnings.filterwarnings('ignore')


def calculate_velocity(close: pd.Series, periods: list = [1, 5, 10]) -> pd.DataFrame:
    """
    Calculate price velocity (1st derivative) over multiple periods.
    Returns percentage changes for stationarity.
    """
    result = pd.DataFrame(index=close.index)
    for p in periods:
        result[f'velocity_{p}'] = close.pct_change(periods=p)
    return result


def calculate_acceleration(velocity: pd.Series) -> pd.Series:
    """Calculate acceleration (2nd derivative of price)."""
    return velocity.diff()


def calculate_volume_force(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """
    Calculate volume-based features.
    
    Features:
    - vwap_position: Close relative to VWAP, normalized by range
    - volume_z: Volume z-score vs rolling mean
    - effort_result: Volume / price change ratio (absorption detection)
    """
    result = pd.DataFrame(index=df.index)
    
    # VWAP position (normalized)
    bar_range = df['high'] - df['low']
    result['vwap_position'] = (df['close'] - df['vwap']) / (bar_range + 0.0001)
    result['vwap_position'] = result['vwap_position'].clip(-3, 3)  # Cap outliers
    
    # Volume z-score
    vol_mean = df['volume'].rolling(lookback).mean()
    vol_std = df['volume'].rolling(lookback).std()
    result['volume_z'] = (df['volume'] - vol_mean) / (vol_std + 1)
    result['volume_z'] = result['volume_z'].clip(-5, 5)
    
    # Effort vs Result (high volume + low price change = absorption)
    pct_change = df['close'].pct_change().abs()
    result['effort_result'] = result['volume_z'] / (pct_change + 0.0001)
    result['effort_result'] = result['effort_result'].clip(-100, 100)
    
    return result


def calculate_bar_topology(df: pd.DataFrame, atr_short: int = 5, atr_long: int = 20) -> pd.DataFrame:
    """
    Calculate bar structure features.
    
    Features:
    - range_ratio: (High-Low) / |Open-Close| - high = indecision
    - volatility_ratio: ATR5 / ATR20 - low = compression
    - body_position: Where close is within the bar range
    """
    result = pd.DataFrame(index=df.index)
    
    # Range ratio (high value = long wicks, indecision)
    full_range = df['high'] - df['low']
    body = (df['close'] - df['open']).abs()
    result['range_ratio'] = full_range / (body + 0.0001)
    result['range_ratio'] = result['range_ratio'].clip(0, 20)
    
    # True Range for ATR
    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - df['close'].shift(1)).abs()
    tr3 = (df['low'] - df['close'].shift(1)).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Volatility ratio (ATR compression)
    atr_s = true_range.rolling(atr_short).mean()
    atr_l = true_range.rolling(atr_long).mean()
    result['volatility_ratio'] = atr_s / (atr_l + 0.0001)
    result['volatility_ratio'] = result['volatility_ratio'].clip(0, 5)
    
    # Body position within range (0 = close at low, 1 = close at high)
    result['body_position'] = (df['close'] - df['low']) / (full_range + 0.0001)
    result['body_position'] = result['body_position'].clip(0, 1)
    
    return result


def calculate_autocorrelation(returns: pd.Series, window: int = 10) -> pd.Series:
    """
    Calculate rolling autocorrelation of returns.
    Positive = trending, Negative = mean-reverting
    """
    def autocorr_1(x):
        if len(x) < 2:
            return np.nan
        return np.corrcoef(x[:-1], x[1:])[0, 1]
    
    return returns.rolling(window).apply(autocorr_1, raw=True)


def calculate_momentum_divergence(df: pd.DataFrame, period: int = 10) -> pd.DataFrame:
    """
    Detect divergences between price and volume trends.
    """
    result = pd.DataFrame(index=df.index)
    
    # Price trend (slope of last N bars)
    price_change = df['close'].pct_change(periods=period)
    
    # Volume trend
    vol_change = df['volume'].pct_change(periods=period)
    
    # Divergence: price up but volume down, or vice versa
    result['pv_divergence'] = np.sign(price_change) * np.sign(vol_change) * -1
    
    # Trade count intensity (if available)
    if 'trade_count' in df.columns:
        tc_mean = df['trade_count'].rolling(20).mean()
        result['trade_intensity'] = df['trade_count'] / (tc_mean + 1)
        result['trade_intensity'] = result['trade_intensity'].clip(0, 5)
    
    return result


def build_feature_vector(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construct the complete stationary feature vector for each bar.
    
    Features (9 core + extras):
    1. velocity_1: 1-bar price % change
    2. velocity_5: 5-bar price % change
    3. velocity_10: 10-bar price % change
    4. acceleration: Change in 1-bar velocity
    5. vwap_position: Close vs VWAP, normalized
    6. volume_z: Volume z-score vs 20-bar mean
    7. effort_result: Volume / price change ratio
    8. range_ratio: Bar range / body size
    9. volatility_ratio: ATR5 / ATR20 (compression)
    10. body_position: Close position in bar range
    11. autocorr_10: 10-bar return autocorrelation
    12. pv_divergence: Price-volume divergence
    """
    features = pd.DataFrame(index=df.index)
    
    # 1. Velocity features
    velocity_df = calculate_velocity(df['close'], periods=[1, 5, 10])
    features = pd.concat([features, velocity_df], axis=1)
    
    # 2. Acceleration
    features['acceleration'] = calculate_acceleration(features['velocity_1'])
    
    # 3. Volume force features
    volume_df = calculate_volume_force(df)
    features = pd.concat([features, volume_df], axis=1)
    
    # 4. Bar topology features
    topology_df = calculate_bar_topology(df)
    features = pd.concat([features, topology_df], axis=1)
    
    # 5. Autocorrelation
    returns = df['close'].pct_change()
    features['autocorr_10'] = calculate_autocorrelation(returns, window=10)
    
    # 6. Momentum divergence
    divergence_df = calculate_momentum_divergence(df)
    features = pd.concat([features, divergence_df], axis=1)
    
    return features


def aggregate_lookback_features(
    features: pd.DataFrame,
    lookback: int = 50
) -> pd.DataFrame:
    """
    For each bar, aggregate features from the lookback window.
    Creates summary statistics for cluster analysis.
    """
    result = pd.DataFrame(index=features.index)
    
    for col in features.columns:
        if col in ['timestamp']:
            continue
        
        # Rolling mean and std
        result[f'{col}_mean'] = features[col].rolling(lookback).mean()
        result[f'{col}_std'] = features[col].rolling(lookback).std()
        
        # Trend over window (end - start)
        result[f'{col}_trend'] = features[col].diff(lookback)
    
    return result


def process_symbol(
    symbol: str,
    data_path: Path,
    events_path: Path,
    output_path: Path
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Process a symbol: build features and merge with events."""
    
    # Load raw data
    pattern = f"{symbol}_1min_*20260124.parquet"
    files = list(data_path.glob(pattern))
    if not files:
        pattern = f"{symbol}_1min_202*.parquet"
        files = sorted(data_path.glob(pattern), key=lambda x: x.stat().st_size, reverse=True)
    
    if not files:
        print(f"No data file found for {symbol}")
        return None, None
    
    print(f"\n{'='*60}")
    print(f"Building features for {symbol}")
    print(f"{'='*60}")
    
    df = pd.read_parquet(files[0])
    print(f"Loaded {len(df):,} bars")
    
    # Build feature vector
    print("Calculating features...")
    features = build_feature_vector(df)
    print(f"  Created {len(features.columns)} features")
    
    # Aggregate over lookback window
    print("Aggregating lookback features...")
    lookback_features = aggregate_lookback_features(features, lookback=50)
    print(f"  Created {len(lookback_features.columns)} aggregated features")
    
    # Combine
    all_features = pd.concat([features, lookback_features], axis=1)
    
    # Load events if available
    events_file = events_path / f"{symbol}_winning_events.parquet"
    if events_file.exists():
        print(f"Merging with events from {events_file.name}...")
        events = pd.read_parquet(events_file)
        
        # Align by index
        all_features['is_winning'] = False
        all_features['direction'] = ''
        all_features['magnitude'] = 0.0
        
        # Map events
        event_idx = pd.to_datetime(events[events['is_winning']]['timestamp'])
        all_features.loc[all_features.index.isin(event_idx), 'is_winning'] = True
        
        win_count = all_features['is_winning'].sum()
        print(f"  Mapped {win_count:,} winning events to features")
    
    # Save
    output_file = output_path / f"{symbol}_features.parquet"
    all_features.to_parquet(output_file)
    print(f"Saved to {output_file}")
    
    return all_features, features


def main():
    """Run Phase 2 feature engineering."""
    
    base_path = Path(__file__).parent.parent.parent
    data_path = base_path / "data" / "cache" / "equities"
    events_path = Path(__file__).parent / "outputs"
    output_path = Path(__file__).parent / "outputs"
    output_path.mkdir(exist_ok=True)
    
    symbols = ['SPY', 'QQQ', 'IWM']
    
    print("=" * 60)
    print("PHASE 2: FEATURE ENGINEERING - STATIONARY VOCABULARY")
    print("=" * 60)
    
    all_features = {}
    
    for symbol in symbols:
        features, raw = process_symbol(
            symbol=symbol,
            data_path=data_path,
            events_path=events_path,
            output_path=output_path
        )
        if features is not None:
            all_features[symbol] = features
    
    # Summary
    print("\n" + "=" * 60)
    print("FEATURE SUMMARY")
    print("=" * 60)
    
    if all_features:
        sample = list(all_features.values())[0]
        feature_cols = [c for c in sample.columns if c not in ['is_winning', 'direction', 'magnitude']]
        print(f"\nTotal features: {len(feature_cols)}")
        print("\nCore features:")
        core_features = [c for c in feature_cols if not any(s in c for s in ['_mean', '_std', '_trend'])]
        for f in core_features[:15]:
            print(f"  - {f}")
        
        print(f"\nAggregated features: {len(feature_cols) - len(core_features)}")
    
    print("\n✓ Phase 2 complete. Feature files saved to outputs/")
    return all_features


if __name__ == "__main__":
    main()
