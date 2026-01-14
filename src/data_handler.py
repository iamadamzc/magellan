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
        feed: str = 'sip',
        lookback_buffer: int = 0
    ) -> pd.DataFrame:
        """
        Fetch historical bar data for a given symbol and timeframe.
        
        Args:
            symbol: Stock symbol (e.g., 'SPY')
            timeframe: Bar timeframe (e.g., '1Min', '1Hour', '1Day')
            start: Start date in ISO format (e.g., '2026-01-08')
            end: End date in ISO format (e.g., '2026-01-09')
            feed: Data feed to use ('sip' for Market Plus, 'iex' for free tier)
            lookback_buffer: Number of additional bars to fetch before start (default 0)
        
        Returns:
            DataFrame with OHLCV data, timezone-naive UTC timestamps as index
        """
        from datetime import datetime, timedelta
        
        # HOT START: Adjust start date if lookback_buffer is specified
        adjusted_start = start
        if lookback_buffer > 0:
            # Calculate buffer period based on timeframe
            start_dt = datetime.fromisoformat(start)
            
            # Map timeframe to minutes for buffer calculation
            timeframe_minutes = {
                '1Min': 1,
                '5Min': 5,
                '15Min': 15,
                '1Hour': 60,
                '1Day': 1440
            }
            
            interval_str = timeframe if isinstance(timeframe, str) else '1Min'
            minutes_per_bar = timeframe_minutes.get(interval_str, 1)
            buffer_minutes = lookback_buffer * minutes_per_bar
            
            # Subtract buffer (add extra 20% for market closures)
            adjusted_start_dt = start_dt - timedelta(minutes=int(buffer_minutes * 1.2))
            adjusted_start = adjusted_start_dt.strftime('%Y-%m-%d')
            
            print(f"[HOT START] Fetching {lookback_buffer} warmup bars before {start}")
            print(f"[HOT START] Adjusted start: {adjusted_start}")
        
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
                start=adjusted_start,
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
    
    def __init__(self) -> None:
        """
        Initialize the FMP Data Client.
        
        Credentials are loaded from environment variable:
        - FMP_API_KEY: Financial Modeling Prep API key
        """
        self.api_key = os.getenv('FMP_API_KEY')
        if not self.api_key:
            raise ValueError("FMP_API_KEY environment variable must be set")
        
        self.base_url_stable = "https://financialmodelingprep.com/stable"
        self.base_url_v3 = "https://financialmodelingprep.com/api/v3"
    
    @staticmethod
    def _parse_fmp_sentiment(raw_sent) -> float:
        """
        Convert FMP sentiment string or float to numeric value.
        
        Standardizes sentiment parsing across all FMP endpoints.
        
        Args:
            raw_sent: Sentiment from FMP API (string or float)
        
        Returns:
            Float: 0.5 (positive), 0.0 (neutral), -0.5 (negative)
        """
        if isinstance(raw_sent, str):
            mapping = {'positive': 0.5, 'neutral': 0.0, 'negative': -0.5}
            return mapping.get(raw_sent.lower(), 0.0)
        return float(raw_sent)
    
    def fetch_historical_bars(
        self, 
        symbol: str, 
        timeframe: str, 
        start: str, 
        end: str,
        lookback_buffer: int = 0
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV bars from FMP v3 API using 1-minute data,
        then resample to target timeframe with fill-forward.
        
        Args:
            symbol: Stock symbol (e.g., 'SPY')
            timeframe: Target timeframe (e.g., '1Hour') - auto-resampled from 1min
            start: Start date in ISO format (e.g., '2026-01-08')
            end: End date in ISO format (e.g., '2026-01-09')
            lookback_buffer: Number of additional bars to fetch before start (default 0)
        
        Returns:
            DataFrame with lowercase OHLCV columns ['open', 'high', 'low', 'close', 'volume']
            and DatetimeIndex (timezone-naive UTC)
        """
        import requests
        from datetime import datetime, timedelta
        
        # HOT START: Adjust start date if lookback_buffer is specified
        adjusted_start = start
        if lookback_buffer > 0:
            start_dt = datetime.fromisoformat(start)
            
            # Map timeframe to minutes for buffer calculation
            timeframe_minutes = {
                '1Min': 1,
                '5Min': 5,
                '15Min': 15,
                '1Hour': 60,
                '1Day': 1440
            }
            
            interval_str = timeframe if isinstance(timeframe, str) else '1Hour'
            minutes_per_bar = timeframe_minutes.get(interval_str, 60)
            buffer_minutes = lookback_buffer * minutes_per_bar
            
            # Subtract buffer (add extra 20% for market closures)
            adjusted_start_dt = start_dt - timedelta(minutes=int(buffer_minutes * 1.2))
            adjusted_start = adjusted_start_dt.strftime('%Y-%m-%d')
            
            print(f"[HOT START] [FMP] Fetching {lookback_buffer} warmup bars before {start}")
            print(f"[HOT START] [FMP] Adjusted start: {adjusted_start}")
        
        # FORCE 1-minute resolution for maximum granularity
        url = f"{self.base_url_v3}/historical-chart/1min/{symbol}"
        
        params = {
            'from': adjusted_start,
            'to': end,
            'apikey': self.api_key
        }
        
        masked_url = f"{url}?from={adjusted_start}&to={end}&apikey={self.api_key[:4]}..."
        print(f"[FMP] Fetching 1min bars: {masked_url}")
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Check for empty data
            if not data or len(data) == 0:
                print(f"[CRITICAL] FMP Ultimate 1min stream empty for {symbol}")
                return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
            
            # Convert JSON to DataFrame
            df = pd.DataFrame(data)
            
            # FMP returns 'date' column in format: "YYYY-MM-DD HH:MM:SS"
            df['timestamp'] = pd.to_datetime(df['date'])
            df = df.set_index('timestamp')
            
            # Sort ascending (FMP sometimes returns reverse chronological)
            df = df.sort_index(ascending=True)
            
            # Ensure timezone-naive UTC
            if df.index.tz is not None:
                df.index = df.index.tz_convert('UTC').tz_localize(None)
            
            # Normalize column names to lowercase
            df.columns = df.columns.str.lower()
            
            # Select only OHLCV columns
            ohlcv_cols = ['open', 'high', 'low', 'close', 'volume']
            df = df[[col for col in ohlcv_cols if col in df.columns]]
            
            print(f"[FMP] Fetched {len(df)} 1min bars for {symbol}")
            
            # RESAMPLE TO 1-HOUR with standard OHLCV aggregation
            print(f"[FMP] Resampling to 1H resolution...")
            
            agg_rules = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }
            
            # Resample with label='left' (bar labeled by start time)
            df_resampled = df.resample('1h', label='left', closed='left').agg(agg_rules)
            
            # IMPLEMENT FILL-FORWARD to eliminate blackout gaps
            # Forward-fill price columns only (not volume)
            price_cols = ['open', 'high', 'low', 'close']
            df_resampled[price_cols] = df_resampled[price_cols].ffill()
            
            # Fill volume NaN with 0 (no trading = zero volume)
            df_resampled['volume'] = df_resampled['volume'].fillna(0)
            
            # Drop any remaining NaN rows (start of series edge case)
            df_resampled = df_resampled.dropna()
            
            print(f"[FMP] Resampled to {len(df_resampled)} 1H bars (fill-forward applied)")
            
            return df_resampled
            
        except requests.exceptions.HTTPError as e:
            print(f"[FMP ERROR] HTTP error fetching historical bars: {e}")
            if e.response is not None:
                print(f"[FMP ERROR] Response: {e.response.text[:200]}")
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
        except Exception as e:
            print(f"[FMP ERROR] Unexpected error: {e}")
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
    
    def fetch_news_sentiment(self, symbol: str) -> dict:
        """
        Fetch rolling news sentiment for a given symbol using FMP Stable stock-latest API.
        
        HARDWIRED: https://financialmodelingprep.com/stable/news/stock-latest
        LIMIT: 250 articles for maximum bandwidth.
        
        Args:
            symbol: Stock symbol (e.g., 'SPY')
        
        Returns:
            Dictionary with keys: 'symbol', 'sentiment', 'publishedDate'
            Returns sentiment=0.0 if no news is available
        """
        import requests
        from datetime import datetime
        
        # HARDWIRED: Stable news/stock-latest endpoint
        url = "https://financialmodelingprep.com/stable/news/stock-latest"
        params = {
            'symbol': symbol,
            'limit': 250,
            'apikey': self.api_key
        }
            
        masked_url = f"{url}?symbol={symbol}&limit=250&apikey={self.api_key[:4]}..."
        
        try:
            print(f"[FMP] Attempting News Upgrade endpoint: {masked_url}")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check if response is empty
            if not data or len(data) == 0:
                print(f"[FMP] Empty response from News Upgrade endpoint")
                return {
                    'symbol': symbol,
                    'sentiment': 0.0,
                    'publishedDate': datetime.utcnow()
                }
            
            # Success - process the data
            print(f"[FMP] Successfully fetched {len(data)} articles")
            
            # Calculate proxy sentiment from news articles
            sentiments = []
            for article in data:
                if 'sentiment' in article and article['sentiment'] is not None:
                    sent_val = self._parse_fmp_sentiment(article['sentiment'])
                    sentiments.append(sent_val)
            
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
                print(f"[FMP] 403 Forbidden on News Upgrade endpoint")
            else:
                print(f"[FMP ERROR] HTTP error: {e}")
        except requests.exceptions.RequestException as e:
            print(f"[FMP ERROR] Network error: {e}")
        
        # Default return on failure
        print(f"[FMP] News fetch failed for {symbol}, defaulting to sentiment=0")
        return {
            'symbol': symbol,
            'sentiment': 0.0,
            'publishedDate': datetime.utcnow()
        }
    
    def fetch_historical_news(self, symbol: str, start_date: str, end_date: str, price_df: Optional[pd.DataFrame] = None, use_cache: bool = True) -> list:
        """
        Fetch historical news articles for Point-in-Time sentiment alignment.
        
        Uses FMP Ultimate's full-range capability (no chunking needed).
        Implements 24-hour caching to avoid redundant API calls.
        
        Args:
            symbol: Stock symbol (e.g., 'SPY')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            price_df: Optional DataFrame (kept for backwards compatibility, unused)
            use_cache: Enable 24-hour disk cache (default: True)
        
        Returns:
            List of dicts with keys: 'publishedDate' (datetime), 'sentiment' (float),
            'title', 'text', 'summary', 'url'
        """
        import requests
        from datetime import datetime
        import hashlib
        import pickle
        from pathlib import Path
        
        # Caching layer
        if use_cache:
            cache_dir = Path('.cache/fmp_news')
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            cache_key = hashlib.md5(
                f"{symbol}_{start_date}_{end_date}".encode()
            ).hexdigest()
            cache_file = cache_dir / f"{cache_key}.pkl"
            
            if cache_file.exists():
                import time
                age = time.time() - cache_file.stat().st_mtime
                if age < 86400:  # 24-hour cache
                    try:
                        cached_news = pickle.load(cache_file.open('rb'))
                        print(f"[FMP] Using cached news for {symbol} ({start_date} to {end_date})")
                        return cached_news
                    except Exception as e:
                        print(f"[FMP] Cache read failed: {e}, fetching fresh data")
        
        # Single API call for full date range (FMP Ultimate capability)
        url = f"{self.base_url_stable}/news/stock"
        params = {
            'symbols': symbol,
            'from': start_date,
            'to': end_date,
            'apikey': self.api_key
        }
        
        print(f"[FMP] Fetching news: {start_date} -> {end_date}")
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
            # Fail loudly on 402 Payment Required
            if response.status_code == 402:
                raise RuntimeError(
                    f"[CRITICAL] FMP API returned 402 Payment Required for {symbol}. "
                    f"Check your Ultimate plan status and billing. "
                    f"Date range: {start_date} to {end_date}"
                )
            
            response.raise_for_status()
            data = response.json()
            
            if not data:
                print(f"[FMP] No news found for {symbol}")
                return []
            
            # Parse articles
            all_news = []
            for article in data:
                pub_date = None
                if 'publishedDate' in article:
                    try:
                        pub_date = pd.to_datetime(article['publishedDate'])
                        if pub_date.tzinfo is not None:
                            pub_date = pub_date.tz_convert('UTC').tz_localize(None)
                    except Exception:
                        continue
                
                if pub_date is None:
                    continue
                
                # Use helper for sentiment parsing
                sent_val = 0.0
                if 'sentiment' in article and article['sentiment'] is not None:
                    sent_val = self._parse_fmp_sentiment(article['sentiment'])
                
                all_news.append({
                    'publishedDate': pub_date,
                    'sentiment': sent_val,
                    'title': article.get('title', ''),
                    'text': article.get('text', ''),
                    'summary': article.get('summary', ''),
                    'url': article.get('url', '')
                })
            
            all_news.sort(key=lambda x: x['publishedDate'])
            print(f"[FMP] Fetched {len(all_news)} articles")
            
            # Save to cache
            if use_cache and all_news:
                try:
                    pickle.dump(all_news, cache_file.open('wb'))
                except Exception as e:
                    print(f"[FMP] Cache write failed: {e}")
            
            return all_news
            
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 402:
                # Re-raise 402 errors (already handled above)
                raise
            else:
                print(f"[FMP ERROR] HTTP error fetching news: {e}")
                return []
        
        except requests.exceptions.RequestException as e:
            print(f"[FMP ERROR] Network error: {e}")
            return []
    
    def fetch_fundamental_metrics(self, symbol: str) -> dict:
        """
        Fetch fundamental metrics for a given symbol using FMP Stable API.
        
        Uses stable quote endpoint.
        
        Args:
            symbol: Stock symbol (e.g., 'SPY')
        
        Returns:
            Dictionary with keys: 'symbol', 'mktCap', 'pe', 'avgVolume', 'timestamp'
        """
        import requests
        from datetime import datetime
        
        # Hardwired: Stable Quote
        url = f"{self.base_url_stable}/quote"
        params = {'symbol': symbol, 'apikey': self.api_key}
        
        try:
            print(f"[FMP] Attempting Stable Quote endpoint for {symbol}")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check if response is empty
            if not data or len(data) == 0:
                print(f"[FMP] Empty response from Quote endpoint")
                raise ValueError(f"No Data for {symbol}")
            
            # Success - process the data
            # FMP returns a list with one item
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
                print(f"[FMP] 403 Forbidden on Quote endpoint")
            else:
                print(f"[FMP ERROR] HTTP error: {e}")
            raise ValueError(f"Failed to fetch fundamental data for {symbol}")
        except (KeyError, IndexError, ValueError) as e:
            print(f"[FMP ERROR] Parse error: {e}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"[FMP ERROR] Network error: {e}")
            raise
