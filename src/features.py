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
