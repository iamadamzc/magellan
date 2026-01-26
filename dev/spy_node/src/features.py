"""
Feature Engineering Module
Calculates alpha factors and merges multi-source data for quantitative analysis.
"""

from typing import Dict
import pandas as pd
import numpy as np


class FeatureEngineer:
    """Transforms price data into feature-rich DataFrames with alpha factors."""
    
    @staticmethod
    def calculate_log_return(df: pd.DataFrame) -> pd.Series:
        """
        Calculate logarithmic returns.
        
        Args:
            df: DataFrame with 'close' column
        
        Returns:
            Series of log returns (first value will be NaN)
        """
        return np.log(df['close'] / df['close'].shift(1))
    
    @staticmethod
    def calculate_rvol(df: pd.DataFrame, window: int = 20) -> pd.Series:
        """
        Calculate Relative Volume (RVOL).
        
        Args:
            df: DataFrame with 'volume' column
            window: Moving average window (default 20)
        
        Returns:
            Series of relative volume values
        """
        avg_volume = df['volume'].rolling(window=window).mean()
        # Handle division by zero
        rvol = df['volume'] / avg_volume
        return rvol
    
    @staticmethod
    def calculate_parkinson_vol(df: pd.DataFrame) -> pd.Series:
        """
        Calculate Parkinson High-Low Volatility.
        
        Formula: sqrt(1 / (4 * ln(2)) * (ln(High/Low))^2)
        
        Args:
            df: DataFrame with 'high' and 'low' columns
        
        Returns:
            Series of Parkinson volatility estimates
        """
        # Handle High == Low edge case: set floor to 1e-9
        high_low_ratio = df['high'] / df['low']
        high_low_ratio = high_low_ratio.clip(lower=1.0)  # Ensure >= 1
        
        log_hl = np.log(high_low_ratio)
        
        # Parkinson constant: 1 / (4 * ln(2))
        parkinson_const = 1.0 / (4.0 * np.log(2.0))
        
        parkinson = np.sqrt(parkinson_const * (log_hl ** 2))
        
        # Apply floor of 1e-9 for stability
        return parkinson.clip(lower=1e-9)
    
    @staticmethod
    def merge_all(
        price_df: pd.DataFrame,
        fmp_metrics: Dict[str, any],
        fmp_sentiment: Dict[str, any]
    ) -> pd.DataFrame:
        """
        Merge price data with FMP fundamentals and sentiment, then calculate alpha factors.
        
        Uses backward merge_asof to prevent look-ahead bias, then forward-fills sparse FMP data.
        
        Args:
            price_df: DataFrame from Alpaca with OHLCV columns (timezone-naive UTC index)
            fmp_metrics: Dict with 'mktCap', 'pe', 'avgVolume', 'timestamp'
            fmp_sentiment: Dict with 'sentiment', 'timestamp'
        
        Returns:
            Complete feature matrix with all alpha factors and FMP data
        """
        # Create working copy
        df = price_df.copy()
        
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # Calculate alpha factors
        df['log_return'] = FeatureEngineer.calculate_log_return(df)
        df['rvol'] = FeatureEngineer.calculate_rvol(df, window=20)
        df['parkinson_vol'] = FeatureEngineer.calculate_parkinson_vol(df)
        
        # Create FMP data as single-row DataFrames for merging
        fmp_metrics_df = pd.DataFrame([{
            'timestamp': pd.to_datetime(fmp_metrics['timestamp']).tz_localize(None),
            'mktCap': fmp_metrics['mktCap'],
            'pe': fmp_metrics['pe'],
            'avgVolume_fmp': fmp_metrics['avgVolume']
        }])
        
        # Handle both 'timestamp' (legacy) and 'publishedDate' (Stable API) keys
        sentiment_timestamp_key = 'publishedDate' if 'publishedDate' in fmp_sentiment else 'timestamp'
        fmp_sentiment_df = pd.DataFrame([{
            'timestamp': pd.to_datetime(fmp_sentiment[sentiment_timestamp_key]).tz_localize(None),
            'sentiment': fmp_sentiment['sentiment']
        }])
        
        # Reset index to use timestamp column for merge
        df_reset = df.reset_index()
        df_reset.rename(columns={'timestamp': 'timestamp'}, inplace=True)
        
        # Merge FMP metrics using merge_asof with direction='backward' to prevent look-ahead
        df_merged = pd.merge_asof(
            df_reset.sort_values('timestamp'),
            fmp_metrics_df.sort_values('timestamp'),
            on='timestamp',
            direction='backward'
        )
        
        # Merge FMP sentiment
        df_merged = pd.merge_asof(
            df_merged.sort_values('timestamp'),
            fmp_sentiment_df.sort_values('timestamp'),
            on='timestamp',
            direction='backward'
        )
        
        # Handle case where FMP timestamp is after all price data:
        # If all values are NaN after merge_asof, broadcast the FMP value across all rows
        fmp_columns = ['mktCap', 'pe', 'avgVolume_fmp', 'sentiment']
        fmp_source_values = {
            'mktCap': fmp_metrics['mktCap'],
            'pe': fmp_metrics['pe'],
            'avgVolume_fmp': fmp_metrics['avgVolume'],
            'sentiment': fmp_sentiment['sentiment']
        }
        
        for col in fmp_columns:
            if df_merged[col].isna().all():
                # All NaN means FMP timestamp was after all price data - broadcast the value
                df_merged[col] = fmp_source_values[col]
            else:
                # Normal case: forward-fill to propagate across 1-minute bars
                df_merged[col] = df_merged[col].ffill()
        
        # Backward-fill any remaining leading NaNs (for rows before first FMP timestamp)
        for col in fmp_columns:
            df_merged[col] = df_merged[col].bfill()
        
        # Set timestamp back as index
        df_merged.set_index('timestamp', inplace=True)
        
        # Validation: Count remaining NaN values and warn if any exist
        nan_counts = df_merged.isna().sum()
        total_nans = nan_counts.sum()
        print(f"[VALIDATION] Total NaNs in matrix: {total_nans}")
        if total_nans > 0:
            print(f"[FEATURES WARNING] NaN breakdown:")
            for col, count in nan_counts[nan_counts > 0].items():
                print(f"  - {col}: {count} NaN values")
        else:
            print(f"[FEATURES] Feature matrix complete: {len(df_merged)} rows")
        
        return df_merged


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add technical indicators for multi-factor analysis.
    
    Computes:
    - RSI (14): Relative Strength Index using Wilder's smoothing
    - Volatility (14): Rolling standard deviation of log returns
    - Volume Z-Score (20): Standardized volume deviation
    
    Args:
        df: DataFrame with 'close', 'volume', and 'log_return' columns
    
    Returns:
        DataFrame with new indicator columns added (mutated in-place)
    """
    # RSI (14) using Wilder's smoothing (adjust=False for EWM)
    delta = df['close'].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    
    # Wilder's smoothing: span = 2*period - 1 for adjust=False equivalence
    # OR use alpha = 1/period directly
    avg_gain = gains.ewm(span=14, adjust=False).mean()
    avg_loss = losses.ewm(span=14, adjust=False).mean()
    
    # Avoid division by zero
    rs = avg_gain / avg_loss.replace(0, np.inf)
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    # Handle edge case where avg_loss is 0 (RSI = 100)
    df.loc[avg_loss == 0, 'rsi_14'] = 100.0
    # Handle edge case where avg_gain is 0 (RSI = 0)
    df.loc[avg_gain == 0, 'rsi_14'] = 0.0
    
    # Volatility (14): Rolling standard deviation of log returns
    df['volatility_14'] = df['log_return'].rolling(window=14).std()
    
    # Volume Z-Score (20): Standardized volume
    vol_mean = df['volume'].rolling(window=20).mean()
    vol_std = df['volume'].rolling(window=20).std()
    df['volume_zscore'] = (df['volume'] - vol_mean) / vol_std.replace(0, np.inf)
    
    # Handle division by zero (constant volume)
    df.loc[vol_std == 0, 'volume_zscore'] = 0.0
    
    return df


def merge_news_pit(price_df: pd.DataFrame, news_list: list, lookback_hours: int = 4) -> pd.DataFrame:
    """
    Point-in-Time sentiment alignment - only uses news available at each bar timestamp.
    
    For each 1-minute bar, calculates sentiment from news published within the lookback
    window *before* the bar's timestamp. If raw sentiment values are constant/zero,
    uses news frequency as a proxy (more news = higher activity sentiment).
    
    Args:
        price_df: DataFrame with datetime index (timezone-naive UTC)
        news_list: List of dicts with 'publishedDate' and 'sentiment' keys
        lookback_hours: Hours to look back for recent news (default: 4)
    
    Returns:
        DataFrame with 'sentiment' column added
    """
    from datetime import timedelta
    
    df = price_df.copy()
    
    if not news_list:
        # No news available - set neutral sentiment
        df['sentiment'] = 0.0
        print("[PIT] No news articles available, using neutral sentiment")
        return df
    
    # Convert news_list to DataFrame for efficient lookups
    news_df = pd.DataFrame(news_list)
    news_df = news_df.sort_values('publishedDate').reset_index(drop=True)
    
    # Check if all sentiment values are constant (API data quality issue)
    unique_sentiments = news_df['sentiment'].nunique()
    use_frequency_proxy = unique_sentiments <= 1
    
    if use_frequency_proxy:
        print("[PIT] All news sentiment values are constant - using news frequency as proxy")
    
    lookback_delta = timedelta(hours=lookback_hours)
    sentiments = []
    news_counts = []
    
    for bar_time in df.index:
        # Find news published before this bar, within lookback window
        window_start = bar_time - lookback_delta
        
        # Filter news: window_start <= publishedDate < bar_time (strict PIT)
        mask = (news_df['publishedDate'] >= window_start) & (news_df['publishedDate'] < bar_time)
        recent_news = news_df.loc[mask]
        
        news_count = len(recent_news)
        news_counts.append(news_count)
        
        if news_count > 0:
            avg_sent = recent_news['sentiment'].mean()
        else:
            avg_sent = np.nan  # Will forward-fill later
        
        sentiments.append(avg_sent)
    
    if use_frequency_proxy:
        # Use news count as sentiment proxy: normalize to roughly -0.5 to +0.5 range
        # Based on news count per 4-hour window (expected range 0-10)
        news_count_series = pd.Series(news_counts, index=df.index)
        # Z-score normalize then clip to reasonable range
        nc_mean = news_count_series.mean()
        nc_std = news_count_series.std()
        if nc_std > 0:
            df['sentiment'] = ((news_count_series - nc_mean) / nc_std).clip(-2, 2) * 0.25
        else:
            df['sentiment'] = 0.0
    else:
        df['sentiment'] = sentiments
        # Forward-fill NaN values (bars with no recent news inherit last known sentiment)
        df['sentiment'] = df['sentiment'].ffill()
        # Backward-fill any remaining NaNs at the start
        df['sentiment'] = df['sentiment'].bfill()
        # Final fallback: if still NaN (no news at all), use 0
        df['sentiment'] = df['sentiment'].fillna(0.0)
    
    # Report variance for IC validation
    sent_std = df['sentiment'].std()
    sent_unique = df['sentiment'].nunique()
    print(f"[PIT] Sentiment aligned: std={sent_std:.4f}, unique_values={sent_unique}")
    
    return df


def generate_master_signal(
    df: pd.DataFrame,
    rsi_wt: float = 0.6,
    vol_wt: float = 0.4
) -> pd.DataFrame:
    """
    Combine multiple factors into a weighted alpha_score.
    
    Normalizes each component to 0-1 range before combining:
    - RSI: Already 0-100, scaled to 0-1
    - Volume Z-Score: Min-max normalized
    
    Note: Sentiment factor was removed after analysis showed FMP API
    does not provide actual sentiment data (only article count proxy).
    
    Args:
        df: DataFrame with 'rsi_14', 'volume_zscore' columns
        rsi_wt: Weight for RSI component (default: 0.6)
        vol_wt: Weight for volume z-score (default: 0.4)
    
    Returns:
        DataFrame with 'alpha_score' column added (mutates in-place)
    """
    # Normalize RSI (0-100 -> 0-1)
    rsi_norm = df['rsi_14'] / 100.0
    
    # Normalize Volume Z-Score (min-max to 0-1)
    vol_min = df['volume_zscore'].min()
    vol_max = df['volume_zscore'].max()
    vol_range = vol_max - vol_min
    if vol_range > 0:
        vol_norm = (df['volume_zscore'] - vol_min) / vol_range
    else:
        vol_norm = pd.Series(0.5, index=df.index)  # Constant volume
    
    # Weighted combination (no sentiment)
    df['alpha_score'] = (rsi_wt * rsi_norm) + (vol_wt * vol_norm)
    
    print(f"[ALPHA] Master signal generated: mean={df['alpha_score'].mean():.4f}, std={df['alpha_score'].std():.4f}")
    
    return df

