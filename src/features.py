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
    # RSI 0-100 (raw, no centering)
    # VARIANT F: Keep raw RSI for intuitive hysteresis thresholds (55/45)
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
    DEPRECATED: LAM damping replaced with volatility targeting.
    
    This function now returns a passthrough (scaling_factor = 1.0) for
    backwards compatibility. Position sizing is handled by volatility
    targeting in src/risk_manager.py.
    
    Args:
        df: DataFrame (unused, kept for backwards compatibility)
        ticker: Ticker symbol (unused)
        node_config: Node configuration (unused)
    
    Returns:
        Dict with default values (no damping applied)
    """
    # Passthrough: No damping applied
    # Real position sizing handled by volatility targeting
    return {
        'scaling_factor': 1.0,
        'atr_damping': 0.0,
        'carrier_damping': 0.0,
        'metabolism_pct': 100,
        'carrier_alignment': 0.5
    }


def add_wavelet_signals(
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
    
    # Local NLP Fallback: If API sentiment is MISSING, calculate via TextBlob
    nlp_start = time.perf_counter()
    nlp_engaged = False
    
    for idx, row in news_df.iterrows():
        # Only run NLP if sentiment field is truly missing
        if 'sentiment' not in row or row['sentiment'] is None or pd.isna(row['sentiment']):
            nlp_engaged = True
            # Concatenate title and text/summary for full context
            title = str(row.get('title', ''))
            text = str(row.get('text', row.get('summary', '')))
            full_text = f"{title} {text}".strip()
            
            if full_text:
                # TextBlob polarity returns -1.0 to 1.0
                news_df.at[idx, 'sentiment'] = TextBlob(full_text).sentiment.polarity
            else:
                news_df.at[idx, 'sentiment'] = 0.0  # Fallback for empty text
    
    nlp_end = time.perf_counter()
    calc_time = nlp_end - nlp_start
    
    if nlp_engaged:
        LOG.warning(f"[PIT] API sentiment missing. Local NLP engaged for {len(news_df)} articles. Latency: {calc_time:.4f}s")
    
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
    # AG: TEMPORAL LEAK PATCH - Signal Generation Sanitization
    # CRITICAL: Ensure forward_return is NEVER used in signal generation
    # Drop it entirely if somehow present in the input DataFrame
    if 'forward_return' in df.columns:
        LOG.warning(f"[LEAK-PATCH] WARNING: forward_return found in signal input for {ticker}, dropping it!")
        df = df.drop(columns=['forward_return'])
    
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
    
    # Normalize RSI (0-100 -> 0-1) - no change needed, RSI is already bounded
    rsi_norm = df['rsi_14'] / 100.0
    
    # P1 REMEDIATION: Rolling normalization (look-back only, no future data)
    NORM_WINDOW = 252  # ~1 trading day of 1-minute bars
    
    # Normalize Volume Z-Score (rolling min-max to 0-1)
    vol_rolling_min = df['volume_zscore'].rolling(window=NORM_WINDOW, min_periods=20).min()
    vol_rolling_max = df['volume_zscore'].rolling(window=NORM_WINDOW, min_periods=20).max()
    vol_range = vol_rolling_max - vol_rolling_min
    vol_norm = (df['volume_zscore'] - vol_rolling_min) / vol_range.replace(0, np.inf)
    vol_norm = vol_norm.fillna(0.5)  # Warmup period fallback
    
    # Normalize Sentiment (rolling min-max to 0-1)
    sent_rolling_min = df['sentiment'].rolling(window=NORM_WINDOW, min_periods=20).min()
    sent_rolling_max = df['sentiment'].rolling(window=NORM_WINDOW, min_periods=20).max()
    sent_range = sent_rolling_max - sent_rolling_min
    sent_norm = (df['sentiment'] - sent_rolling_min) / sent_range.replace(0, np.inf)
    sent_norm = sent_norm.fillna(0.5)  # Warmup period fallback
    
    # Calculate weighted alpha score
    df['alpha_score'] = (rsi_wt * rsi_norm) + (vol_wt * vol_norm) + (sent_wt * sent_norm)
    
    # -------------------------------------------------------------------------
    # VARIANT F: HYSTERESIS (Schmidt Trigger) for Daily Trend Following
    # Solves whipsaw over-trading by creating a "quiet zone" (45-55 RSI)
    # -------------------------------------------------------------------------
    # DEBUG: Log node_config to diagnose activation
    LOG.info(f"[DEBUG] generate_master_signal called for {ticker}")
    LOG.info(f"[DEBUG] node_config type: {type(node_config)}")
    LOG.info(f"[DEBUG] node_config content: {node_config}")
    LOG.info(f"[DEBUG] enable_hysteresis value: {node_config.get('enable_hysteresis', 'KEY_MISSING') if node_config else 'NODE_CONFIG_IS_NONE'}")
    
    if node_config and node_config.get('enable_hysteresis', False):
        LOG.info(f"[HYSTERESIS] Schmidt Trigger enabled for {ticker}")
        
        upper_threshold = node_config.get('hysteresis_upper_rsi', 55)  # Buy threshold (raw RSI)
        lower_threshold = node_config.get('hysteresis_lower_rsi', 45)  # Sell threshold (raw RSI)
        
        LOG.info(f"[HYSTERESIS] Thresholds: Long Entry RSI > {upper_threshold}, Flat Exit RSI < {lower_threshold}")
        
        # Initialize state tracking
        # State: 0 = FLAT, 1 = LONG, -1 = SHORT (but config may force long-only)
        allow_shorts = node_config.get('allow_shorts', False)
        
        position_state = np.zeros(len(df))  # State column
        hysteresis_signal = np.zeros(len(df))  # Signal column (0 = flat, 1 = long, -1 = short)
        
        current_state = 0  # Start FLAT
        
        # Schmidt Trigger State Machine (forward iteration, no lookahead)
        for i, (idx, row) in enumerate(df.iterrows()):
            rsi_value = row['rsi_14']
            
            # State transitions
            if current_state == 0:  # Currently FLAT
                if rsi_value > upper_threshold:
                    current_state = 1  # Enter LONG
                elif allow_shorts and rsi_value < lower_threshold:
                    current_state = -1  # Enter SHORT (if allowed)
                # else: stay FLAT
            
            elif current_state == 1:  # Currently LONG
                if rsi_value < lower_threshold:
                    current_state = 0  # Exit to FLAT
                # else: hold LONG (quiet zone 45-55 does nothing)
            
            elif current_state == -1:  # Currently SHORT
                if rsi_value > upper_threshold:
                    current_state = 0  # Exit to FLAT
                # else: hold SHORT (quiet zone 45-55 does nothing)
            
            # Record state
            position_state[i] = current_state
            hysteresis_signal[i] = current_state
        
        # Store in DataFrame
        df['position_state'] = position_state
        df['hysteresis_signal'] = hysteresis_signal
        
        # MAPPING: Validated strategy writes directly to 'signal'
        df['signal'] = hysteresis_signal
        
        # Telemetry
        state_changes = pd.Series(position_state).diff().fillna(0)
        num_transitions = (state_changes != 0).sum()
        long_periods = (position_state == 1).sum()
        flat_periods = (position_state == 0).sum()
        short_periods = (position_state == -1).sum()
        
        LOG.info(f"[HYSTERESIS] State transitions: {num_transitions}")
        LOG.info(f"[HYSTERESIS] Distribution - Long: {long_periods}, Flat: {flat_periods}, Short: {short_periods}")
        LOG.success(f"[HYSTERESIS] Schmidt Trigger complete - Whipsaw filter active")
        
        # CRITICAL: Early return to skip legacy Fermi/Carrier logic
        return df
    # -------------------------------------------------------------------------
    
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
            # LOG.cryogen(f"[CRYOGEN] VSS Cooling ACTIVE: {cryo_count} bars exceed 1.5x baseline temp")
    # -------------------------------------------------------------------------
    
    # Calculate rolling statistics for dynamic threshold (Fermi_Gate)
    alpha_mean = df['alpha_score'].mean()
    alpha_std = df['alpha_score'].std()
    fermi_gate = alpha_mean + (sigma_multiplier * alpha_std)
    
    # -------------------------------------------------------------------------
    # HYSTERESIS DEADBAND: Anti-Chatter Logic (0.05 threshold)
    # Prevents rapid state oscillations at threshold boundaries
    # -------------------------------------------------------------------------
    HYSTERESIS_DEADBAND = 0.05
    
    # Apply High-Pass Gate with directional signals
    fire_buy_count = 0
    fire_sell_count = 0
    filter_count = 0
    phase_lock_silence = 0
    cryo_silence_count = 0
    
    # Create signal column and state tracking
    df['signal'] = 0
    df['prev_state'] = 'FILTER'  # Initialize state tracking
    
    # Track previous state for hysteresis
    prev_state = 'FILTER'
    
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
            # LOG.cryogen(f"[CRYOGEN] VSS Temp: {temp_val:.4f} | Status: {action} | Metabolism: {cryo_metabolism}%")
            LOG.info(f"[LAM] Damping Active | Metabolism: {cryo_metabolism}%")
            prev_state = 'FILTER'
            df.loc[idx, 'prev_state'] = prev_state
            continue
        
        # CARRIER DAMPING: Apply proportional reduction instead of hard veto
        # WITH HYSTERESIS DEADBAND
        if is_vetoed:
            # Calculate carrier damping based on misalignment severity
            carrier_gate = 0.5
            carrier_shortfall = abs(c_score - carrier_gate)
            carrier_damping_val = min(carrier_shortfall * 2.0, 0.80)  # Scale shortfall to damping
            carrier_scaling = 1.0 - carrier_damping_val
            carrier_metabolism = int(carrier_scaling * 100)
            
            # HYSTERESIS LOGIC: Apply deadband to prevent chatter
            # If prev_state is FILTER, need Carrier > (Gate + 0.02) to flip to BUY
            # If prev_state is BUY, need Carrier < (Gate - 0.02) to flip to FILTER
            if prev_state == 'FILTER':
                # Require extra margin to enter BUY state
                if c_score > (carrier_gate + HYSTERESIS_DEADBAND):
                    if score > fermi_gate:
                        damped_signal = 1
                        action = "DAMP-BUY"
                        prev_state = 'BUY'
                    else:
                        damped_signal = 0
                        action = "DAMP-HOLD"
                else:
                    damped_signal = 0
                    action = "FILTER"
            elif prev_state == 'BUY':
                # Require extra margin to exit BUY state
                if c_score < (carrier_gate - HYSTERESIS_DEADBAND):
                    damped_signal = 0
                    action = "FILTER"
                    prev_state = 'FILTER'
                else:
                    # Stay in BUY state
                    damped_signal = 1
                    action = "BUY"
            else:
                # Default fallback
                if score > fermi_gate:
                    damped_signal = 1
                    action = "DAMP-BUY"
                elif score < -fermi_gate:
                    damped_signal = -1
                    action = "DAMP-SELL"
                else:
                    damped_signal = 0
                    action = "DAMP-HOLD"
            
            df.loc[idx, 'signal'] = damped_signal
            df.loc[idx, 'damping_factor'] = carrier_scaling
            df.loc[idx, 'prev_state'] = prev_state
            phase_lock_silence += 1
            # LOG.phase_lock(f"[PHASE-LOCK] Ticker: {ticker} | Carrier: {c_score:.4f} | Gate: {carrier_gate:.2f} | Status: {action}")
            LOG.info(f"[LAM] Damping Active | Metabolism: {carrier_metabolism}%")
            continue
        
        # FERMI LOGIC: directional threshold applies WITH HYSTERESIS
        # If prev_state is FILTER, need score > (fermi_gate + DEADBAND) to flip to BUY
        # If prev_state is BUY, need score < (fermi_gate - DEADBAND) to flip to FILTER
        if prev_state == 'FILTER':
            if score > (fermi_gate + HYSTERESIS_DEADBAND):
                df.loc[idx, 'signal'] = 1
                action = "BUY"
                prev_state = 'BUY'
                fire_buy_count += 1
            elif score < -(fermi_gate + HYSTERESIS_DEADBAND):
                df.loc[idx, 'signal'] = -1
                action = "SELL"
                prev_state = 'SELL'
                fire_sell_count += 1
            else:
                df.loc[idx, 'signal'] = 0
                action = "FILTER"
                filter_count += 1
        elif prev_state == 'BUY':
            if score < (fermi_gate - HYSTERESIS_DEADBAND):
                df.loc[idx, 'signal'] = 0
                action = "FILTER"
                prev_state = 'FILTER'
                filter_count += 1
            else:
                df.loc[idx, 'signal'] = 1
                action = "BUY"
                fire_buy_count += 1
        elif prev_state == 'SELL':
            if score > -(fermi_gate - HYSTERESIS_DEADBAND):
                df.loc[idx, 'signal'] = 0
                action = "FILTER"
                prev_state = 'FILTER'
                filter_count += 1
            else:
                df.loc[idx, 'signal'] = -1
                action = "SELL"
                fire_sell_count += 1
        else:
            # Default fallback for first iteration
            if score > (fermi_gate + HYSTERESIS_DEADBAND):
                df.loc[idx, 'signal'] = 1
                action = "BUY"
                prev_state = 'BUY'
                fire_buy_count += 1
            elif score < -(fermi_gate + HYSTERESIS_DEADBAND):
                df.loc[idx, 'signal'] = -1
                action = "SELL"
                prev_state = 'SELL'
                fire_sell_count += 1
            else:
                df.loc[idx, 'signal'] = 0
                action = "FILTER"
                filter_count += 1
        
        df.loc[idx, 'prev_state'] = prev_state
        
        # PHASE-LOCK TELEMETRY: Report per-bar decision for observability
        if ticker == 'VSS':
            pass # LOG.cryogen(f"[CRYOGEN] VSS Temp: {temp_val:.4f} | Status: {action}")
        else:
            pass # LOG.phase_lock(f"[PHASE-LOCK] Ticker: {ticker} | Carrier: {c_score:.4f} | Status: {action}")
    
    # Summary Telemetry
    LOG.stats(f"[SIGNAL] Fermi Gate: {fermi_gate:.4f} (Mean={alpha_mean:.4f} + {sigma_multiplier}*StdDev={alpha_std:.4f})")
    LOG.stats(f"[SIGNAL] Hysteresis Deadband: {HYSTERESIS_DEADBAND} (Anti-Chatter Active)")
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


