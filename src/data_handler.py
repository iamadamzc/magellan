"""
Alpaca Data Client Module
Handles fetching and cleaning historical market data from Alpaca API.
"""

from typing import Optional
import os
import pandas as pd
from alpaca_trade_api.rest import REST, TimeFrame
from datetime import datetime


class AlpacaDataClient:
    """Client for fetching and processing historical market data from Alpaca."""
    
    def __init__(self):
        """
        Initialize the Alpaca Data Client.
        
        Credentials are automatically loaded from environment variables:
        - APCA_API_KEY_ID: Alpaca API key
        - APCA_API_SECRET_KEY: Alpaca secret key
        - APCA_API_BASE_URL: Alpaca API base URL
        """
        base_url = os.getenv('APCA_API_BASE_URL')
        if not base_url:
            raise ValueError("APCA_API_BASE_URL environment variable must be set")
        
        # SDK will automatically pick up APCA_API_KEY_ID and APCA_API_SECRET_KEY
        self.api = REST(base_url=base_url)
    
    def fetch_historical_bars(
        self, 
        symbol: str, 
        timeframe: str, 
        start: str, 
        end: str,
        feed: str = 'sip'
    ) -> pd.DataFrame:
        """
        Fetch historical bar data for a given symbol and timeframe.
        
        Args:
            symbol: Stock symbol (e.g., 'SPY')
            timeframe: Bar timeframe (e.g., '1Min', '1Hour', '1Day')
            start: Start date in ISO format (e.g., '2026-01-08')
            end: End date in ISO format (e.g., '2026-01-09')
            feed: Data feed to use ('sip' for Market Plus, 'iex' for free tier)
        
        Returns:
            DataFrame with OHLCV data, timezone-naive UTC timestamps as index
        """
        # Map string timeframe to Alpaca TimeFrame enum
        timeframe_map = {
            '1Min': TimeFrame.Minute,
            '5Min': TimeFrame(5, 'Min'),
            '15Min': TimeFrame(15, 'Min'),
            '1Hour': TimeFrame.Hour,
            '1Day': TimeFrame.Day,
        }
        
        if isinstance(timeframe, TimeFrame):
            tf = timeframe
        else:
            tf = timeframe_map.get(timeframe, TimeFrame.Minute)
        
        print(f"[DEBUG] Fetching {symbol} via {feed.upper()} feed...")
        
        # Fetch bars from Alpaca with error handling
        try:
            bars = self.api.get_bars(
                symbol=symbol,
                timeframe=tf,
                start=start,
                end=end,
                feed=feed
            ).df
        except Exception as error:
            # Capture 401 errors and print the detailed response
            if hasattr(error, 'response') and error.response is not None:
                if hasattr(error.response, 'status_code') and error.response.status_code == 401:
                    print(f"[ERROR] 401 Unauthorized: {error.response.text}")
            raise
        
        # Ensure timezone-aware to UTC, then make timezone-naive
        if bars.index.tz is None:
            # If not timezone-aware, assume UTC
            bars.index = pd.to_datetime(bars.index, utc=True)
        else:
            # Convert to UTC
            bars.index = bars.index.tz_convert('UTC')
        
        # Remove timezone information to make it timezone-naive
        bars.index = bars.index.tz_localize(None)
        
        return bars
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean market data by forward-filling missing values.
        Prints transparency information about NaN values filled.
        
        Args:
            df: DataFrame with potential missing values
        
        Returns:
            Cleaned DataFrame with forward-filled values
        """
        # Count NaN values before cleaning
        nan_count = df.isna().sum().sum()
        
        if nan_count > 0:
            print(f"[DATA_CLEAN] Forward-filling {nan_count} NaN values")
        else:
            print("[DATA_CLEAN] No NaN values detected")
        
        # Forward-fill missing values
        df_cleaned = df.ffill()
        
        # Check if any NaN values remain (e.g., at the start of the series)
        remaining_nan = df_cleaned.isna().sum().sum()
        if remaining_nan > 0:
            print(f"[DATA_CLEAN] Warning: {remaining_nan} NaN values remain after forward-fill")
        
        return df_cleaned


def force_resample_ohlcv(
    df: pd.DataFrame, 
    target_interval: str, 
    ticker: str = 'UNKNOWN'
) -> tuple:
    """
    Force-resample OHLCV data if bar frequency doesn't match target interval.
    
    This is a defensive mechanism to ensure data integrity when the Alpaca API
    returns bars at a different frequency than requested (e.g., 1-minute bars
    when 5-minute was requested due to SDK version or API quirks).
    
    Args:
        df: DataFrame with OHLCV columns and DatetimeIndex
        target_interval: Target interval string ('1Min', '3Min', '5Min', '15Min', '1Hour', '1Day')
        ticker: Symbol for telemetry logging
    
    Returns:
        Tuple of (resampled_df, was_resampled, actual_seconds, expected_seconds)
    """
    # Map interval strings to expected seconds
    interval_seconds = {
        '1Min': 60,
        '3Min': 180,
        '5Min': 300,
        '15Min': 900,
        '30Min': 1800,
        '1Hour': 3600,
        '1Day': 86400
    }
    
    # Map interval strings to pandas resample rules
    resample_rules = {
        '1Min': '1min',
        '3Min': '3min',
        '5Min': '5min',
        '15Min': '15min',
        '30Min': '30min',
        '1Hour': '1h',
        '1Day': '1D'
    }
    
    expected_seconds = interval_seconds.get(target_interval, 60)
    resample_rule = resample_rules.get(target_interval, '1min')
    
    # Check if we have enough bars to determine actual frequency
    if len(df) < 2:
        return (df, False, 0, expected_seconds)
    
    # Calculate actual bar delta from first two bars
    actual_seconds = (df.index[1] - df.index[0]).total_seconds()
    
    # Allow 1 second tolerance for floating-point rounding
    if abs(actual_seconds - expected_seconds) <= 1:
        # Frequency matches, no resample needed
        return (df, False, actual_seconds, expected_seconds)
    
    # Frequency mismatch detected - perform resample
    print(f"[DATA] Force-Resampled {ticker} from {int(actual_seconds)}s to {int(expected_seconds)}s")
    
    # Define OHLCV aggregation rules
    agg_dict = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }
    
    # Add optional columns if present
    if 'trade_count' in df.columns:
        agg_dict['trade_count'] = 'sum'
    if 'vwap' in df.columns:
        agg_dict['vwap'] = 'mean'
    
    # Filter agg_dict to only include columns present in df
    agg_dict = {k: v for k, v in agg_dict.items() if k in df.columns}
    
    # Perform resample with label='left' to match Alpaca's bar labeling convention
    resampled_df = df.resample(resample_rule, label='left', closed='left').agg(agg_dict)
    
    # Drop any rows with NaN (incomplete bars at edges)
    resampled_df = resampled_df.dropna()
    
    return (resampled_df, True, actual_seconds, expected_seconds)


class FMPDataClient:
    """Client for fetching fundamental and sentiment data from Financial Modeling Prep API."""
    
    def __init__(self, use_legacy_fallback: bool = False) -> None:
        """
        Initialize the FMP Data Client.
        
        Credentials are loaded from environment variable:
        - FMP_API_KEY: Financial Modeling Prep API key
        
        Args:
            use_legacy_fallback: If True, attempt legacy v3 endpoint after stable fails.
                                 Only enable if your account has legacy access.
        """
        self.api_key = os.getenv('FMP_API_KEY')
        if not self.api_key:
            raise ValueError("FMP_API_KEY environment variable must be set")
        
        self.base_url_stable = "https://financialmodelingprep.com/stable"
        self.base_url_v3 = "https://financialmodelingprep.com/api/v3"
        self.use_legacy_fallback = use_legacy_fallback
    
    def fetch_news_sentiment(self, symbol: str) -> dict:
        """
        Fetch rolling news sentiment for a given symbol using FMP Stable API.
        
        Uses stable endpoint first. Legacy v3 fallback only if enabled in constructor.
        
        Args:
            symbol: Stock symbol (e.g., 'SPY')
        
        Returns:
            Dictionary with keys: 'symbol', 'sentiment', 'publishedDate'
            Returns sentiment=0.0 if no news is available
        """
        import requests
        from datetime import datetime
        
        # Build endpoint list: stable first, then legacy v3 only if enabled
        endpoints = [
            ('stable', f"{self.base_url_stable}/news/stock", {'symbols': symbol, 'limit': 50, 'apikey': self.api_key}),
        ]
        if self.use_legacy_fallback:
            endpoints.append(
                ('v3-legacy', f"{self.base_url_v3}/stock_news", {'tickers': symbol, 'limit': 50, 'apikey': self.api_key})
            )
        
        for api_version, url, params in endpoints:
            # Create masked URL for debugging
            param_key = 'symbols' if api_version == 'stable' else 'tickers'
            masked_url = f"{url}?{param_key}={symbol}&limit=50&apikey={self.api_key[:4]}..."
            
            try:
                print(f"[FMP] Attempting {api_version.upper()} news endpoint: {masked_url}")
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Check if response is empty - try next endpoint
                if not data or len(data) == 0:
                    print(f"[FMP] Empty response from {api_version.upper()}, trying next endpoint...")
                    continue
                
                # Success - process the data
                print(f"[FMP] Successfully fetched from {api_version.upper()}")
                
                # Calculate proxy sentiment from news articles
                sentiments = []
                for article in data:
                    if 'sentiment' in article and article['sentiment'] is not None:
                        # Convert sentiment string to numeric if needed
                        sent_val = article['sentiment']
                        if isinstance(sent_val, str):
                            # Map common sentiment strings to values
                            sentiment_map = {'positive': 0.5, 'neutral': 0.0, 'negative': -0.5}
                            sent_val = sentiment_map.get(sent_val.lower(), 0.0)
                        sentiments.append(float(sent_val))
                
                # Check for 0.5 baseline saturation (STALE_DATA signature)
                if sentiments and all(abs(s - 0.5) < 0.001 for s in sentiments):
                     print("[FMP] STALE_DATA Detected (All 0.5) - Squelch candidate")
                
                # If no sentiment fields, use news frequency as proxy (normalized)
                if sentiments:
                    avg_sentiment = sum(sentiments) / len(sentiments)
                else:
                    # Proxy: More news = higher engagement, normalize by expected baseline
                    news_count = len(data)
                    avg_sentiment = min((news_count - 10) / 40.0, 1.0) if news_count > 10 else 0.0
                
                # Extract most recent publishedDate
                published_date = datetime.utcnow()
                if data and 'publishedDate' in data[0]:
                    try:
                        published_date = pd.to_datetime(data[0]['publishedDate'])
                    except:
                        pass
                
                print(f"[FMP] Processed {len(data)} articles, proxy sentiment: {avg_sentiment:.4f}")
                
                return {
                    'symbol': symbol,
                    'sentiment': float(avg_sentiment),
                    'publishedDate': published_date
                }
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    print(f"[FMP] 403 Forbidden on {api_version.upper()}, trying next endpoint...")
                    continue
                print(f"[FMP ERROR] HTTP error on {api_version.upper()}: {e}")
                continue
            except requests.exceptions.RequestException as e:
                print(f"[FMP ERROR] Network error on {api_version.upper()}: {e}")
                continue
        
        # All endpoints failed - return default
        print(f"[FMP] All endpoints failed for {symbol}, defaulting to sentiment=0")
        return {
            'symbol': symbol,
            'sentiment': 0.0,
            'publishedDate': datetime.utcnow()
        }
    
    def fetch_historical_news(self, symbol: str, start_date: str, end_date: str, price_df: Optional[pd.DataFrame] = None) -> list:
        """
        Fetch historical news articles for Point-in-Time sentiment alignment.
        
        Uses FMP Stable API with 'from' and 'to' parameters to fetch date-ranged news.
        Implements chunked fetching (30-day blocks) to bypass bulk request limits.
        Falls back to Price-Volume proxy if 402 Payment Required error occurs.
        
        Args:
            symbol: Stock symbol (e.g., 'SPY')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            price_df: Optional DataFrame with OHLCV data for proxy calculation on 402 error
        
        Returns:
            List of dicts with keys: 'publishedDate' (datetime), 'sentiment' (float)
        """
        import requests
        from datetime import datetime, timedelta
        import math
        
        # Helper to generate chunks
        def generate_chunks(start, end, chunk_size_days=30):
            current = datetime.strptime(start, '%Y-%m-%d')
            end_dt = datetime.strptime(end, '%Y-%m-%d')
            while current <= end_dt:
                chunk_end = min(current + timedelta(days=chunk_size_days), end_dt)
                yield current.strftime('%Y-%m-%d'), chunk_end.strftime('%Y-%m-%d')
                current = chunk_end + timedelta(days=1)

        all_news = []
        
        # Iterate through 30-day chunks
        for chunk_start, chunk_end in generate_chunks(start_date, end_date):
            url = f"{self.base_url_stable}/news/stock"
            params = {
                'symbols': symbol,
                'from': chunk_start,
                'to': chunk_end,
                'apikey': self.api_key
            }
            
            masked_url = f"{url}?symbols={symbol}&from={chunk_start}&to={chunk_end}&apikey={self.api_key[:4]}..."
            print(f"[FMP] Fetching chunk: {chunk_start} -> {chunk_end}")
            
            try:
                response = requests.get(url, params=params, timeout=15)
                
                # Check for 402 specifically
                if response.status_code == 402:
                    raise requests.exceptions.HTTPError("402 Payment Required", response=response)
                    
                response.raise_for_status()
                data = response.json()
                
                if not data:
                    print(f"[FMP] No news found for chunk {chunk_start} to {chunk_end}")
                    continue
                
                # Parse articles using existing logic
                chunk_news = []
                for article in data:
                    pub_date = None
                    if 'publishedDate' in article:
                        try:
                            # Parse directly to naive UTC
                            pub_date = pd.to_datetime(article['publishedDate'])
                            if pub_date.tzinfo is not None:
                                pub_date = pub_date.tz_convert('UTC').tz_localize(None)
                        except Exception:
                            continue
                    
                    if pub_date is None:
                        continue
                    
                    sent_val = 0.0
                    if 'sentiment' in article and article['sentiment'] is not None:
                        raw_sent = article['sentiment']
                        if isinstance(raw_sent, str):
                            sentiment_map = {'positive': 0.5, 'neutral': 0.0, 'negative': -0.5}
                            sent_val = sentiment_map.get(raw_sent.lower(), 0.0)
                        else:
                            sent_val = float(raw_sent)
                    
                    chunk_news.append({
                        'publishedDate': pub_date,
                        'sentiment': sent_val,
                        'title': article.get('title', ''),
                        'text': article.get('text', ''),
                        'summary': article.get('summary', ''),
                        'url': article.get('url', '')
                    })
                
                all_news.extend(chunk_news)
                print(f"[FMP] Chunk success: {len(chunk_news)} articles")

            except requests.exceptions.HTTPError as e:
                is_402 = (e.response is not None and e.response.status_code == 402)
                if is_402:
                    print(f"[SENTIMENT] API Paywall: Using Neutral Baseline (0.5)")
                    
                    # Generate Neutral Baseline (0.5) for the entire chunk
                    # Create one synthetic entry per day to ensure coverage
                    try:
                        c_start = datetime.strptime(chunk_start, '%Y-%m-%d')
                        c_end = datetime.strptime(chunk_end, '%Y-%m-%d')
                        curr = c_start
                        synthetic_news = []
                        
                        while curr <= c_end:
                            synthetic_news.append({
                                'publishedDate': curr + timedelta(hours=12), # Mid-day
                                'sentiment': 0.5,
                                'title': 'PAYWALL_NEUTRAL_BASELINE',
                                'text': 'Synthetic neutral sentiment due to API 402 limit',
                                'summary': '',
                                'url': ''
                            })
                            curr += timedelta(days=1)
                            
                        all_news.extend(synthetic_news)
                        print(f"[FMP] Injected {len(synthetic_news)} neutral baseline articles")
                        print(f"[FMP] Tagging as STALE_DATA (0.5) for Backtester Squelch")
                        
                    except Exception as err:
                        print(f"[FMP ERROR] Failed to generate baseline: {err}")
                        
                else:
                     print(f"[FMP ERROR] HTTP error fetching historical news: {e}")
            
            except requests.exceptions.RequestException as e:
                print(f"[FMP ERROR] Network error fetching historical news: {e}")
                
        # Sort combined results
        all_news.sort(key=lambda x: x['publishedDate'])
        print(f"[FMP] Parsed {len(all_news)} total articles with valid timestamps")
        
        return all_news
    
    def fetch_fundamental_metrics(self, symbol: str) -> dict:
        """
        Fetch fundamental metrics for a given symbol using FMP Stable API.
        
        Uses stable endpoint first. Legacy v3 fallback only if enabled in constructor.
        
        Args:
            symbol: Stock symbol (e.g., 'SPY')
        
        Returns:
            Dictionary with keys: 'symbol', 'mktCap', 'pe', 'avgVolume', 'timestamp'
        """
        import requests
        from datetime import datetime
        
        # Build endpoint list: stable first, then legacy v3 only if enabled
        # Stable uses query param: /stable/quote?symbol=SPY
        # Legacy v3 uses path param: /api/v3/quote/SPY
        endpoints = [
            ('stable', f"{self.base_url_stable}/quote", {'symbol': symbol, 'apikey': self.api_key}),
        ]
        if self.use_legacy_fallback:
            endpoints.append(
                ('v3-legacy', f"{self.base_url_v3}/quote/{symbol}", {'apikey': self.api_key})
            )
        
        for api_version, url, params in endpoints:
            try:
                print(f"[FMP] Attempting {api_version.upper()} quote endpoint for {symbol}")
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Check if response is empty - try next endpoint
                if not data or len(data) == 0:
                    print(f"[FMP] Empty response from {api_version.upper()}, trying next endpoint...")
                    continue
                
                # Success - process the data
                # FMP returns a list with one item for both stable and legacy
                quote = data[0] if isinstance(data, list) else data
                
                return {
                    'symbol': symbol,
                    'mktCap': float(quote.get('marketCap', 0.0)),
                    'pe': float(quote.get('pe', 0.0)),
                    'avgVolume': float(quote.get('avgVolume', 0.0)),
                    'timestamp': datetime.utcnow()
                }
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    print(f"[FMP] 403 Forbidden on {api_version.upper()}, trying next endpoint...")
                    continue
                print(f"[FMP ERROR] HTTP error on {api_version.upper()}: {e}")
                continue
            except (KeyError, IndexError, ValueError) as e:
                print(f"[FMP ERROR] Parse error on {api_version.upper()}: {e}")
                continue
            except requests.exceptions.RequestException as e:
                print(f"[FMP ERROR] Network error on {api_version.upper()}: {e}")
                continue
        
        # All endpoints failed
        print(f"[FMP ERROR] All endpoints failed for {symbol}")
        raise ValueError(f"Failed to fetch fundamental data for {symbol} from all API versions")
