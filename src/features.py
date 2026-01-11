"""
Feature Engineering Module
Calculates alpha factors and merges multi-source data for quantitative analysis.
"""

import time
from typing import Dict
import pandas as pd
import numpy as np
from textblob import TextBlob
from src.logger import LOG


class FeatureEngineer:
    """Transforms price data into feature-rich DataFrames with alpha factors."""
    
    def __init__(self, node_config: dict = None):
        """
        Initialize FeatureEngineer with optional node configuration.
        
        Args:
            node_config: Ticker-specific configuration dict with keys:
                - rsi_lookback: int (default 14)
                - sentry_gate: float threshold (default 0.0)
                - rsi_wt, vol_wt, sent_wt: alpha weights
        """
        self.node_config = node_config or {}
        self.rsi_lookback = self.node_config.get('rsi_lookback', 14)
    
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
        LOG.warning(f"[VALIDATION] Total NaNs in matrix: {total_nans}")
        if total_nans > 0:
            LOG.warning(f"[FEATURES WARNING] NaN breakdown:")
            for col, count in nan_counts[nan_counts > 0].items():
                LOG.warning(f"  - {col}: {count} NaN values")
        else:
            LOG.info(f"[FEATURES] Feature matrix complete: {len(df_merged)} rows")
        
        return df_merged


def add_technical_indicators(df: pd.DataFrame, node_config: dict = None) -> pd.DataFrame:
    """
    Add technical indicators for multi-factor analysis.
    
    Computes:
    - RSI: Relative Strength Index using Wilder's smoothing (period from node_config)
    - Volatility (14): Rolling standard deviation of log returns
    - Volume Z-Score (20): Standardized volume deviation
    
    Args:
        df: DataFrame with 'close', 'volume', and 'log_return' columns
        node_config: Optional ticker-specific config with 'rsi_lookback' key
    
    Returns:
        DataFrame with new indicator columns added (mutated in-place)
    """
    # Extract RSI lookback from node_config, default to 14
    rsi_lookback = 14
    if node_config:
        rsi_lookback = node_config.get('rsi_lookback', 14)
    
    # RSI using Wilder's smoothing (adjust=False for EWM)
    # V1.0 PRODUCTION: Standard RSI on 'close' only
    source_price = df['close']
        
    delta = source_price.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    
    # Wilder's smoothing: span = 2*period - 1 for adjust=False equivalence
    # OR use alpha = 1/period directly
    avg_gain = gains.ewm(span=rsi_lookback, adjust=False).mean()
    avg_loss = losses.ewm(span=rsi_lookback, adjust=False).mean()
    
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


def calculate_rsi(close_series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate RSI for a given close price series.
    
    Args:
        close_series: Series of close prices
        period: RSI lookback period (default 14)
    
    Returns:
        Series of RSI values (0-100)
    """
    delta = close_series.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    
    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    
    # Handle edge cases
    rsi = rsi.copy()
    rsi.loc[avg_loss == 0] = 100.0
    rsi.loc[avg_gain == 0] = 0.0
    
    return rsi


def get_damping_factor(
    df: pd.DataFrame,
    ticker: str = None,
    node_config: dict = None
) -> dict:
    """
    Proportional Damping (PID Scaling) System.
    
    Replaces binary veto logic with a 'Variable Metabolism' that scales
    position size based on signal purity conditions.
    
    Damping Rules:
    - ATR Thermal Damping: If current ATR is X% above baseline, reduce size by X%
      (e.g., ATR 10% above baseline = 10% position reduction)
    - Carrier-Wave Damping: If carrier alignment is below 0.5 gate, apply
      proportional reduction (e.g., alignment 0.4 = 20% reduction)
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns and datetime index
        ticker: Ticker symbol for telemetry
        node_config: Optional node configuration
    
    Returns:
        Dict with keys:
        - 'scaling_factor': Float 0.0-1.0 (1.0 = full size, 0.5 = half size)
        - 'atr_damping': Float damping contribution from ATR
        - 'carrier_damping': Float damping contribution from carrier alignment
        - 'metabolism_pct': Integer percentage of metabolism (scaling_factor * 100)
    """
    # Initialize damping components
    atr_damping = 0.0
    carrier_damping = 0.0
    
    # -------------------------------------------------------------------------
    # ATR THERMAL DAMPING: Scale down position when volatility exceeds baseline
    # Formula: If ATR is X% above baseline, reduce size by X%
    # -------------------------------------------------------------------------
    if 'high' in df.columns and 'low' in df.columns and 'close' in df.columns:
        # Calculate True Range
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift(1)).abs()
        low_close = (df['low'] - df['close'].shift(1)).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # Current ATR (20-period)
        current_atr = true_range.rolling(window=20).mean()
        
        # Baseline ATR (200-period median for stability)
        baseline_atr = current_atr.rolling(window=200).median()
        
        # Get latest values (most recent bar)
        latest_atr = current_atr.iloc[-1] if len(current_atr) > 0 else 0.0
        latest_baseline = baseline_atr.iloc[-1] if len(baseline_atr) > 0 else latest_atr
        
        # Calculate ATR excess ratio
        if latest_baseline > 0 and pd.notna(latest_baseline):
            atr_ratio = latest_atr / latest_baseline
            
            # If ATR is X% above baseline, damping = X% (capped at 50%)
            if atr_ratio > 1.0:
                atr_excess_pct = (atr_ratio - 1.0)  # e.g., 1.10 -> 0.10 (10%)
                atr_damping = min(atr_excess_pct, 0.50)  # Cap at 50% damping
    
    # -------------------------------------------------------------------------
    # CARRIER-WAVE DAMPING: Scale down when carrier alignment is weak
    # Formula: If alignment < 0.5, damping = (0.5 - alignment) * 0.4
    # Example: Alignment 0.4 -> (0.5 - 0.4) * 0.4 = 0.04 (but scaled by 2x = 20%)
    # -------------------------------------------------------------------------
    if 'close' in df.columns and len(df) >= 14:
        # Calculate 60-minute Alpha (The Carrier)
        df_60min = df['close'].resample('60Min').last().dropna()
        if len(df_60min) >= 14:
            rsi_60_raw = calculate_rsi(df_60min, period=14)
            # Get latest carrier alignment (0-1 scale)
            carrier_alignment = (rsi_60_raw.iloc[-1] / 100.0) if len(rsi_60_raw) > 0 else 0.5
        else:
            carrier_alignment = 0.5  # Neutral fallback
        
        # Gate threshold = 0.5 (neutral)
        # If carrier below 0.5, apply proportional damping
        carrier_gate = 0.5
        if carrier_alignment < carrier_gate:
            # Shortfall from gate, scaled to damping
            # Alignment 0.4 means 0.1 shortfall, damping = 0.1 * 2.0 = 20%
            shortfall = carrier_gate - carrier_alignment
            carrier_damping = min(shortfall * 2.0, 0.50)  # Cap at 50% damping
    else:
        carrier_alignment = 0.5
    
    # -------------------------------------------------------------------------
    # COMBINE DAMPING FACTORS (Additive, capped at 80% max damping)
    # This ensures we never fully zero out, preserving minimum exposure
    # -------------------------------------------------------------------------
    total_damping = atr_damping + carrier_damping
    total_damping = min(total_damping, 0.80)  # Never more than 80% reduction
    
    # Scaling factor = 1.0 - total_damping
    scaling_factor = 1.0 - total_damping
    metabolism_pct = int(scaling_factor * 100)
    
    # -------------------------------------------------------------------------
    # TELEMETRY: Report damping state (ASCII ONLY)
    # -------------------------------------------------------------------------
    if total_damping > 0.0:
        LOG.info(f"[LAM] Damping Active | Metabolism: {metabolism_pct}%")
        LOG.info(f"[LAM] ATR Damping: {atr_damping*100:.1f}% | Carrier Damping: {carrier_damping*100:.1f}%")
    else:
        LOG.info(f"[LAM] Full Metabolism | Scaling: 100%")
    
    return {
        'scaling_factor': scaling_factor,
        'atr_damping': atr_damping,
        'carrier_damping': carrier_damping,
        'metabolism_pct': metabolism_pct,
        'carrier_alignment': carrier_alignment if 'carrier_alignment' in dir() else 0.5
    }


def scale_confluence_filter(
    df: pd.DataFrame,
    ticker: str = None,
    node_config: dict = None
) -> pd.DataFrame:
    """
    Multi-Resolution Wavelet Decomposition using RSI across three timescales.
    
    Calculates 14-period RSI at 5Min, 15Min, and 60Min resolutions,
    then combines them with a weighted formula to filter for structural permission.
    
    Formula: NEW_ALPHA = (RSI_5 * 0.2) + (RSI_15 * 0.3) + (RSI_60 * 0.5)
    
    This captures high-frequency kinetic energy (5Min) ONLY when the macro trend
    (60Min) provides Structural Permission.
    
    Args:
        df: DataFrame with 'close' column and datetime index (5Min resolution)
        ticker: Ticker symbol for telemetry
        node_config: Optional node configuration
    
    Returns:
        DataFrame with 'wavelet_alpha' column added (mutates in-place)
    """
    # Ensure we have enough data
    if len(df) < 14:
        df['wavelet_alpha'] = 0.5
        LOG.warning(f"[WAVELET] {ticker} Insufficient data for wavelet decomposition")
        return df
    
    # RSI at 5-minute scale (native resolution)
    rsi_5 = calculate_rsi(df['close'], period=14)
    
    # RSI at 15-minute scale (resample 5Min -> 15Min)
    df_15min = df['close'].resample('15Min').last().dropna()
    if len(df_15min) >= 14:
        rsi_15_raw = calculate_rsi(df_15min, period=14)
        # Upsample back to 5Min resolution for alignment
        rsi_15 = rsi_15_raw.reindex(df.index, method='ffill')
    else:
        rsi_15 = pd.Series(50.0, index=df.index)  # Neutral fallback
    
    # RSI at 60-minute scale (resample 5Min -> 60Min)
    df_60min = df['close'].resample('60Min').last().dropna()
    if len(df_60min) >= 14:
        rsi_60_raw = calculate_rsi(df_60min, period=14)
        # Upsample back to 5Min resolution for alignment
        rsi_60 = rsi_60_raw.reindex(df.index, method='ffill')
    else:
        rsi_60 = pd.Series(50.0, index=df.index)  # Neutral fallback
    
    # Fill NaN values with neutral 50
    rsi_5 = rsi_5.fillna(50.0)
    rsi_15 = rsi_15.fillna(50.0)
    rsi_60 = rsi_60.fillna(50.0)
    
    # Weighted confluence:
    # 5Min (kinetic) = 20%, 15Min (momentum) = 30%, 60Min (structure) = 50%
    wavelet_alpha = (rsi_5 * 0.2) + (rsi_15 * 0.3) + (rsi_60 * 0.5)
    
    # Normalize to 0-1 range (from 0-100)
    wavelet_alpha_norm = wavelet_alpha / 100.0
    
    # Store in dataframe
    df['wavelet_alpha'] = wavelet_alpha_norm
    
    # Calculate multiplier effect (how much macro structure amplifies/dampens)
    macro_score = rsi_60.mean() / 100.0
    if macro_score > 0.6:
        multiplier = 1.0 + ((macro_score - 0.6) * 2.5)  # Bullish structural permission
    elif macro_score < 0.4:
        multiplier = 1.0 - ((0.4 - macro_score) * 2.5)  # Bearish structural drag
    else:
        multiplier = 1.0  # Neutral zone
    
    # Apply structural multiplier
    df['wavelet_alpha'] = (df['wavelet_alpha'] * multiplier).clip(0.0, 1.0)
    
    # Telemetry (ASCII only)
    mean_alpha = df['wavelet_alpha'].mean()
    LOG.info(f"[WAVELET] VSS Confluence: {mean_alpha:.2f} | Multiplier: {multiplier:.2f}x")
    
    return df


def carrier_wave_confluence(
    df: pd.DataFrame,
    ticker: str = None,
    node_config: dict = None
) -> pd.DataFrame:
    """
    Carrier-Wave Alpha Filter for signal smoothing.
    
    Compares 60-minute Alpha_Score (Carrier) with 5-minute Alpha_Score (Signal).
    If they have opposite polarities (signs), forces Final_Signal to 0 (Silence).
    
    This ensures 5-minute 'Jitter' is only traded when it aligns with the
    powerful 60-minute structural trend.
    
    Polarity Rules:
    - Carrier > 0.5 = Bullish (positive polarity)
    - Carrier < 0.5 = Bearish (negative polarity)
    - Signal > 0.5 = Bullish (positive polarity)
    - Signal < 0.5 = Bearish (negative polarity)
    - If polarities match: PASS signal through
    - If polarities conflict: SILENCE (force to 0)
    
    Args:
        df: DataFrame with 'close' column and datetime index (5Min resolution)
        ticker: Ticker symbol for telemetry
        node_config: Optional node configuration
    
    Returns:
        DataFrame with 'carrier_signal' column added (mutates in-place)
    """
    # Ensure we have enough data
    if len(df) < 14:
        df['carrier_signal'] = 0
        LOG.warning(f"[SIGNAL] {ticker} Insufficient data for carrier wave analysis")
        return df
    
    # Calculate 5-minute Alpha (The Signal) using RSI
    rsi_5 = calculate_rsi(df['close'], period=14)
    signal_alpha = rsi_5 / 100.0  # Normalize to 0-1
    signal_alpha = signal_alpha.fillna(0.5)
    
    # Calculate 60-minute Alpha (The Carrier) using resampled RSI
    df_60min = df['close'].resample('60Min').last().dropna()
    if len(df_60min) >= 14:
        rsi_60_raw = calculate_rsi(df_60min, period=14)
        # Upsample back to 5Min resolution for alignment
        carrier_alpha = rsi_60_raw.reindex(df.index, method='ffill') / 100.0
    else:
        carrier_alpha = pd.Series(0.5, index=df.index)  # Neutral fallback
    
    carrier_alpha = carrier_alpha.fillna(0.5)
    
    # Determine polarities (centered at 0.5)
    # Polarity: +1 if > 0.5 (bullish), -1 if < 0.5 (bearish), 0 if exactly 0.5
    signal_polarity = np.sign(signal_alpha - 0.5)
    carrier_polarity = np.sign(carrier_alpha - 0.5)
    
    # Initialize carrier_signal column
    df['carrier_signal'] = 0
    
    # Counters for telemetry
    pass_count = 0
    silence_count = 0
    
    # Apply carrier wave filter
    for idx in df.index:
        sig_pol = signal_polarity.loc[idx]
        car_pol = carrier_polarity.loc[idx]
        sig_val = signal_alpha.loc[idx]
        car_val = carrier_alpha.loc[idx]
        
        # Check polarity alignment
        # Both positive, both negative, or either is neutral (0) = PASS
        # Opposite signs = SILENCE
        polarities_conflict = (sig_pol * car_pol) < 0
        
        if polarities_conflict:
            # Opposite polarities - SILENCE
            df.loc[idx, 'carrier_signal'] = 0
            action = "SILENCE"
            silence_count += 1
        else:
            # Aligned or neutral - PASS through signal
            # Convert alpha to directional signal: > 0.6 = BUY, < 0.4 = SELL, else HOLD
            if sig_val > 0.6:
                df.loc[idx, 'carrier_signal'] = 1
                action = "BUY"
            elif sig_val < 0.4:
                df.loc[idx, 'carrier_signal'] = -1
                action = "SELL"
            else:
                df.loc[idx, 'carrier_signal'] = 0
                action = "HOLD"
            pass_count += 1
        
        # Per-bar telemetry (ASCII only)
        LOG.info(f"[SIGNAL] Carrier Alignment: {car_val:.4f} | Signal: {sig_val:.4f} | Result: {action}")
    
    # Summary telemetry
    LOG.info(f"[SIGNAL] Carrier Wave Summary: {pass_count} PASS, {silence_count} SILENCE")
    
    return df


def merge_news_pit(price_df: pd.DataFrame, news_list: list, lookback_hours: int = 4, ticker: str = None) -> pd.DataFrame:
    """
    Point-in-Time sentiment alignment - only uses news available at each bar timestamp.
    
    For each 1-minute bar, calculates sentiment from news published within the lookback
    window *before* the bar's timestamp. If raw sentiment values are constant/zero,
    uses news frequency as a proxy (more news = higher activity sentiment).
    
    Args:
        price_df: DataFrame with datetime index (timezone-naive UTC)
        news_list: List of dicts with 'publishedDate' and 'sentiment' keys
        lookback_hours: Hours to look back for recent news (default: 4)
        ticker: Symbol being processed (optional, used for control tests like SPY bypass)
    
    Returns:
        DataFrame with 'sentiment' column added
    """
    from datetime import timedelta
    
    df = price_df.copy()
    
    if not news_list:
        # No news available - set neutral sentiment
        df['sentiment'] = 0.0
        LOG.info("[PIT] No news articles available, using neutral sentiment")
        return df
    
    # Convert news_list to DataFrame for efficient lookups
    news_df = pd.DataFrame(news_list)
    if 'sentiment' in news_df.columns:
        news_df['sentiment'] = news_df['sentiment'].astype(float)
    news_df = news_df.sort_values('publishedDate').reset_index(drop=True)
    
    # Local NLP Fallback: If API sentiment is 0.0, calculate via TextBlob
    nlp_start = time.perf_counter()
    nlp_engaged = False
    
    for idx, row in news_df.iterrows():
        if row['sentiment'] == 0.0:
            nlp_engaged = True
            # Concatenate title and text/summary for full context
            title = str(row.get('title', ''))
            text = str(row.get('text', row.get('summary', '')))
            full_text = f"{title} {text}".strip()
            
            if full_text:
                # TextBlob polarity returns -1.0 to 1.0
                news_df.at[idx, 'sentiment'] = TextBlob(full_text).sentiment.polarity
    nlp_end = time.perf_counter()
    calc_time = nlp_end - nlp_start
    
    if nlp_engaged:
        LOG.warning(f"[PIT] API Blackout Detected. Local NLP engaged for {len(news_df)} articles. Latency: {calc_time:.4f}s")
    
    # Check if all sentiment values are constant (API data quality issue)
    unique_sentiments = news_df['sentiment'].nunique()
    use_frequency_proxy = unique_sentiments <= 1
    
    if use_frequency_proxy:
        LOG.info("[PIT] All news sentiment values are constant after NLP - using news frequency as proxy")
    
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
    LOG.info(f"[PIT] Sentiment aligned: std={sent_std:.4f}, unique_values={sent_unique}")
    
    return df


def generate_master_signal(
    df: pd.DataFrame,
    node_config: dict = None,
    ticker: str = None
) -> pd.DataFrame:
    """
    Combine multiple factors into a weighted alpha_score with Phase-Lock filtering.
    
    Normalizes each component to 0-1 range before combining:
    - RSI: Already 0-100, scaled to 0-1
    - Volume Z-Score: Min-max normalized
    - Sentiment: Min-max normalized
    
    Phase-Lock Features:
    - Carrier Veto: Silences signal if 5M and 60M alpha polarities conflict
    - HAW Damping (IWM only): Widens Fermi Gate 1.5x during volatility spikes
    
    Args:
        df: DataFrame with 'rsi_14', 'volume_zscore', 'sentiment' columns
        node_config: Ticker-specific config dict with keys:
            - rsi_wt, vol_wt, sent_wt: Alpha weights
            - sentry_gate: Sentiment threshold (float) - KILL alpha if sentiment below this
            - high_pass_sigma: Sigma multiplier for Fermi Gate
        ticker: Ticker symbol for telemetry logging
    
    Returns:
        DataFrame with 'alpha_score' column added (mutates in-place)
    """
    # Shootout telemetry for phase-locked comparison
    if ticker in ['IWM', 'VSS']:
        LOG.info("[SHOOTOUT] Normalizing Reference Frames: IWM vs VSS @ 5Min")
    
    # Default weights
    rsi_wt = 0.4
    vol_wt = 0.3
    sent_wt = 0.3
    sentry_gate = None  # No gate by default
    high_pass_sigma = None
    
    # Override with node_config if provided
    if node_config:
        rsi_wt = node_config.get('rsi_wt', rsi_wt)
        vol_wt = node_config.get('vol_wt', vol_wt)
        sent_wt = node_config.get('sent_wt', sent_wt)
        sentry_gate = node_config.get('sentry_gate', None)
        high_pass_sigma = node_config.get('high_pass_sigma', None)
    
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
    
    # Normalize Sentiment (min-max to 0-1)
    sent_min = df['sentiment'].min()
    sent_max = df['sentiment'].max()
    sent_range = sent_max - sent_min
    if sent_range > 0:
        sent_norm = (df['sentiment'] - sent_min) / sent_range
    else:
        sent_norm = pd.Series(0.5, index=df.index)  # Constant sentiment
    
    # Calculate weighted alpha score
    df['alpha_score'] = (rsi_wt * rsi_norm) + (vol_wt * vol_norm) + (sent_wt * sent_norm)
    
    # -------------------------------------------------------------------------
    # CARRIER VETO: Phase-Lock Filter (5M vs 60M polarity alignment)
    # Eliminates Destructive Interference by silencing conflicting signals
    # -------------------------------------------------------------------------
    # Calculate Alpha_5M (current resolution RSI normalized to -0.5 to +0.5 scale)
    alpha_5m = rsi_norm - 0.5  # Centered: >0 = bullish, <0 = bearish
    
    # Calculate Alpha_60M (60-minute resampled RSI)
    df_60min = df['close'].resample('60Min').last().dropna()
    if len(df_60min) >= 14:
        rsi_60_raw = calculate_rsi(df_60min, period=14)
        rsi_60_aligned = rsi_60_raw.reindex(df.index, method='ffill') / 100.0
        alpha_60m = rsi_60_aligned.fillna(0.5) - 0.5  # Centered
    else:
        alpha_60m = pd.Series(0.0, index=df.index)  # Neutral fallback
    
    # Carrier Veto: If polarities conflict, silence the signal
    # Conflict = (Alpha_5M > 0 AND Alpha_60M < 0) OR (Alpha_5M < 0 AND Alpha_60M > 0)
    carrier_conflict = ((alpha_5m > 0) & (alpha_60m < 0)) | ((alpha_5m < 0) & (alpha_60m > 0))
    veto_count = carrier_conflict.sum()
    
    # Store carrier score for telemetry
    df['carrier_score'] = alpha_60m + 0.5  # Back to 0-1 scale for display
    # -------------------------------------------------------------------------
    
    # -------------------------------------------------------------------------
    # SENTRY GATE: Apply sentiment threshold kill from node_config
    # V1.0 PRODUCTION: Jitter filters and RSI tuning gates REMOVED
    # -------------------------------------------------------------------------
    if sentry_gate is not None:
        mask_toxic = df['sentiment'] < sentry_gate
        kill_count = mask_toxic.sum()
        df.loc[mask_toxic, 'alpha_score'] = 0.0
        LOG.info(f"[SENTRY] Gate applied: Killed {kill_count} bars where sentiment < {sentry_gate}")
    # -------------------------------------------------------------------------
    
    # -------------------------------------------------------------------------
    # FERMI BIAS ADJUSTMENT: Ticker-specific sigma gates for noise filtering
    # Use high_pass_sigma from config if available, else fall back to defaults
    # -------------------------------------------------------------------------
    
    # Determine sigma multiplier from config or ticker defaults
    if high_pass_sigma is not None:
        sigma_multiplier = high_pass_sigma
    elif ticker == 'SPY':
        sigma_multiplier = 2.25  # FERMI GATE: Doped node, low conductivity
    elif ticker == 'QQQ':
        sigma_multiplier = 1.25  # Moderate turbulence filter
    elif ticker == 'IWM':
        sigma_multiplier = 0.75  # Open aperture for small-cap dynamics
    else:
        sigma_multiplier = 0.5   # Default fallback
    
    # -------------------------------------------------------------------------
    # HAW DAMPING (IWM ONLY): Widen Fermi Gate during volatility spikes
    # If Rolling_Volatility_1H > 2.0 * Baseline, increase gate by 1.5x
    # -------------------------------------------------------------------------
    haw_active = False
    if ticker == 'IWM' and 'log_return' in df.columns:
        # Rolling 1H volatility = 12 bars of 5Min data
        rolling_vol_1h = df['log_return'].rolling(window=12).std()
        vol_baseline = rolling_vol_1h.mean()
        
        # Check if current volatility exceeds 2x baseline
        if vol_baseline > 0:
            vol_spike_mask = rolling_vol_1h > (2.0 * vol_baseline)
            haw_spike_count = vol_spike_mask.sum()
            if haw_spike_count > 0:
                haw_active = True
                sigma_multiplier = sigma_multiplier * 1.5  # Widen gate during spike
                LOG.info(f"[HAW] IWM Damping ACTIVE: {haw_spike_count} bars exceed 2x baseline vol")
                LOG.info(f"[HAW] Fermi Gate widened to {sigma_multiplier:.2f} sigma")
    # -------------------------------------------------------------------------
    
    # -------------------------------------------------------------------------
    # CRYOGENIC COOLING (VSS ONLY): Silence signals during thermal noise spikes
    # If Vol_Temp > 1.5 * Baseline_Temp, system is "Too Hot" for clear signals
    # -------------------------------------------------------------------------
    cryo_active = False
    cryo_mask = pd.Series(False, index=df.index)
    
    if ticker == 'VSS' and 'high' in df.columns and 'low' in df.columns:
        # Calculate ATR (Average True Range) for volatility temperature
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift(1)).abs()
        low_close = (df['low'] - df['close'].shift(1)).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # Vol_Temp = Rolling 20-period ATR
        vol_temp = true_range.rolling(window=20).mean()
        
        # Baseline_Temp = 200-period Rolling Median of ATR
        baseline_temp = vol_temp.rolling(window=200).median()
        
        # Store for telemetry
        df['vol_temp'] = vol_temp
        
        # RULE: If Vol_Temp > 1.5 * Baseline_Temp, signal = 0 (Too Hot)
        cryo_mask = vol_temp > (1.5 * baseline_temp)
        cryo_count = cryo_mask.sum()
        
        if cryo_count > 0:
            cryo_active = True
            LOG.cryogen(f"[CRYOGEN] VSS Cooling ACTIVE: {cryo_count} bars exceed 1.5x baseline temp")
    # -------------------------------------------------------------------------
    
    # Calculate rolling statistics for dynamic threshold (Fermi_Gate)
    alpha_mean = df['alpha_score'].mean()
    alpha_std = df['alpha_score'].std()
    fermi_gate = alpha_mean + (sigma_multiplier * alpha_std)
    
    # Apply High-Pass Gate with directional signals
    fire_buy_count = 0
    fire_sell_count = 0
    filter_count = 0
    phase_lock_silence = 0
    cryo_silence_count = 0
    
    # Create signal column
    df['signal'] = 0
    
    for idx in df.index:
        score = df.loc[idx, 'alpha_score']
        c_score = df.loc[idx, 'carrier_score']
        is_vetoed = carrier_conflict.loc[idx] if idx in carrier_conflict.index else False
        is_cryo_hot = cryo_mask.loc[idx] if idx in cryo_mask.index else False
        
        # Get vol_temp for telemetry (VSS only)
        temp_val = df.loc[idx, 'vol_temp'] if 'vol_temp' in df.columns else 0.0
        
        # CRYOGENIC COOLING (VSS): Apply proportional damping instead of hard veto
        # Damping scaled by temperature excess ratio
        if ticker == 'VSS' and is_cryo_hot:
            # Calculate damping factor from temperature excess
            temp_baseline = df['vol_temp'].rolling(window=200).median().loc[idx] if 'vol_temp' in df.columns else temp_val
            if temp_baseline > 0 and pd.notna(temp_baseline):
                temp_ratio = temp_val / temp_baseline
                cryo_damping = min((temp_ratio - 1.0), 0.80) if temp_ratio > 1.0 else 0.0
            else:
                cryo_damping = 0.50  # Default 50% damping if baseline unavailable
            
            cryo_scaling = 1.0 - cryo_damping
            cryo_metabolism = int(cryo_scaling * 100)
            
            # Store damped score instead of zeroing
            df.loc[idx, 'signal'] = 0  # Signal still 0 but with damping metadata
            df.loc[idx, 'damping_factor'] = cryo_scaling
            action = "DAMP"
            cryo_silence_count += 1
            LOG.cryogen(f"[CRYOGEN] VSS Temp: {temp_val:.4f} | Status: {action} | Metabolism: {cryo_metabolism}%")
            LOG.info(f"[LAM] Damping Active | Metabolism: {cryo_metabolism}%")
            continue
        
        # CARRIER DAMPING: Apply proportional reduction instead of hard veto
        if is_vetoed:
            # Calculate carrier damping based on misalignment severity
            carrier_gate = 0.5
            carrier_shortfall = abs(c_score - carrier_gate)
            carrier_damping_val = min(carrier_shortfall * 2.0, 0.80)  # Scale shortfall to damping
            carrier_scaling = 1.0 - carrier_damping_val
            carrier_metabolism = int(carrier_scaling * 100)
            
            # Apply damped signal - direction preserved, size scaled by damping factor
            if score > fermi_gate:
                damped_signal = 1  # Direction preserved, size scaled externally
                action = "DAMP-BUY"
            elif score < -fermi_gate:
                damped_signal = -1
                action = "DAMP-SELL"
            else:
                damped_signal = 0
                action = "DAMP-HOLD"
            
            df.loc[idx, 'signal'] = damped_signal
            df.loc[idx, 'damping_factor'] = carrier_scaling
            phase_lock_silence += 1
            LOG.phase_lock(f"[PHASE-LOCK] Ticker: {ticker} | Carrier: {c_score:.4f} | Status: {action}")
            LOG.info(f"[LAM] Damping Active | Metabolism: {carrier_metabolism}%")
            continue
        
        # FERMI LOGIC: directional threshold applies
        if score > fermi_gate:
            df.loc[idx, 'signal'] = 1
            action = "BUY"
            fire_buy_count += 1
        elif score < -fermi_gate:
            df.loc[idx, 'signal'] = -1
            action = "SELL"
            fire_sell_count += 1
        else:
            df.loc[idx, 'signal'] = 0
            action = "FILTER"
            filter_count += 1
        
        # PHASE-LOCK TELEMETRY: Report per-bar decision for observability
        if ticker == 'VSS':
            LOG.cryogen(f"[CRYOGEN] VSS Temp: {temp_val:.4f} | Status: {action}")
        else:
            LOG.phase_lock(f"[PHASE-LOCK] Ticker: {ticker} | Carrier: {c_score:.4f} | Status: {action}")
    
    # Summary Telemetry
    LOG.stats(f"[SIGNAL] Fermi Gate: {fermi_gate:.4f} (Mean={alpha_mean:.4f} + {sigma_multiplier}*StdDev={alpha_std:.4f})")
    LOG.stats(f"[SIGNAL] Fermi Results: {fire_buy_count} BUY, {fire_sell_count} SELL, {filter_count} FILTER")
    LOG.stats(f"[SIGNAL] Phase-Lock Vetoed: {phase_lock_silence} bars (destructive interference)")
    if cryo_active:
        LOG.stats(f"[CRYOGEN] VSS Cryo-Cooled: {cryo_silence_count} bars (thermal noise suppressed)")
    LOG.stats(f"[SIGNAL] Ticker: {ticker} | Sigma Multiplier: {sigma_multiplier}")
    if haw_active:
        LOG.stats(f"[HAW] IWM HAW Damping was applied this session")
    LOG.stats(f"[ALPHA] Master signal generated: mean={df['alpha_score'].mean():.4f}, std={df['alpha_score'].std():.4f}")
    # -------------------------------------------------------------------------
    
    return df

