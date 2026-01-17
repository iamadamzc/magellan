"""
Data Caching Utility for Magellan
Stores historical price data locally to avoid repeated API calls during backtesting

Cache Structure:
    data/cache/
        equities/
            AAPL_1min_20240101_20251231.parquet
            AAPL_1hour_20240101_20251231.parquet
            AAPL_1day_20220101_20251231.parquet
        futures/
            SIUSD_1hour_20220101_20251231.parquet
        crypto/
            BTCUSD_1day_20220101_20251231.parquet
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import hashlib
from src.logger import LOG
from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame
import requests
import os

class DataCache:
    """Manages local caching of historical price data"""
    
    def __init__(self, cache_dir='data/cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.cache_dir / 'equities').mkdir(exist_ok=True)
        (self.cache_dir / 'futures').mkdir(exist_ok=True)
        (self.cache_dir / 'crypto').mkdir(exist_ok=True)
        (self.cache_dir / 'earnings').mkdir(exist_ok=True)
        (self.cache_dir / 'news').mkdir(exist_ok=True)
    
    def _get_cache_path(self, symbol, timeframe, start, end, asset_type='equity'):
        """Generate cache file path"""
        # Normalize dates
        start_str = start.replace('-', '') if isinstance(start, str) else start.strftime('%Y%m%d')
        end_str = end.replace('-', '') if isinstance(end, str) else end.strftime('%Y%m%d')
        
        # Create filename
        filename = f"{symbol}_{timeframe}_{start_str}_{end_str}.parquet"
        
        return self.cache_dir / asset_type / filename
    
    def get_or_fetch_equity(self, symbol, timeframe, start, end, feed='sip'):
        """Get equity data from cache or fetch from Alpaca"""
        
        cache_path = self._get_cache_path(symbol, timeframe, start, end, 'equities')
        
        # Check cache
        if cache_path.exists():
            LOG.info(f"[CACHE HIT] Loading {symbol} {timeframe} from cache")
            return pd.read_parquet(cache_path)
        
        # Cache miss - fetch from API
        LOG.info(f"[CACHE MISS] Fetching {symbol} {timeframe} from Alpaca")
        client = AlpacaDataClient()
        
        if timeframe == '1min':
            tf = TimeFrame.Minute
        elif timeframe == '1hour':
            tf = TimeFrame.Hour
        elif timeframe == '1day':
            tf = TimeFrame.Day
        else:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        df = client.fetch_historical_bars(
            symbol=symbol,
            timeframe=tf,
            start=start,
            end=end,
            feed=feed
        )
        
        # Resample to ensure correct timeframe
        if timeframe == '1day':
            df = df.resample('1D').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        elif timeframe == '1hour':
            df = df.resample('1H').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        
        # Save to cache
        df.to_parquet(cache_path)
        LOG.success(f"[CACHE SAVED] {cache_path}")
        
        return df
    
    def get_or_fetch_futures(self, symbol, timeframe, start, end):
        """Get futures/commodity data from cache or fetch from FMP"""
        
        cache_path = self._get_cache_path(symbol, timeframe, start, end, 'futures')
        
        # Check cache
        if cache_path.exists():
            LOG.info(f"[CACHE HIT] Loading {symbol} {timeframe} from cache")
            return pd.read_parquet(cache_path)
        
        # Cache miss - fetch from API
        LOG.info(f"[CACHE MISS] Fetching {symbol} {timeframe} from FMP")
        api_key = os.getenv('FMP_API_KEY')
        
        if timeframe == '1hour':
            url = "https://financialmodelingprep.com/stable/historical-chart/1hour"
            params = {'symbol': symbol, 'from': start, 'to': end, 'apikey': api_key}
        elif timeframe == '1day':
            url = f"https://financialmodelingprep.com/stable/historical-price-eod/full/{symbol}"
            params = {'from': start, 'to': end, 'apikey': api_key}
        else:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        df = df[['open', 'high', 'low', 'close', 'volume']]
        
        # Save to cache
        df.to_parquet(cache_path)
        LOG.success(f"[CACHE SAVED] {cache_path}")
        
        return df
    
    def get_or_fetch_earnings_calendar(self, symbol, start, end):
        """Get earnings calendar from cache or fetch from FMP"""
        
        cache_path = self._get_cache_path(symbol, 'earnings', start, end, 'earnings')
        
        # Check cache
        if cache_path.exists():
            LOG.info(f"[CACHE HIT] Loading {symbol} earnings calendar from cache")
            df = pd.read_parquet(cache_path)
            return df['date'].tolist()
        
        # Cache miss - fetch from API
        LOG.info(f"[CACHE MISS] Fetching {symbol} earnings calendar from FMP")
        api_key = os.getenv('FMP_API_KEY')
        
        # Try /stable/ endpoint first
        url = f"https://financialmodelingprep.com/stable/earnings-calendar"
        params = {'symbol': symbol, 'from': start, 'to': end, 'apikey': api_key}
        
        response = requests.get(url, params=params)
        
        if response.status_code == 403:
            # Fallback to /api/v4/ if /stable/ is unavailable
            url = f"https://financialmodelingprep.com/api/v4/earning_calendar"
            params = {'symbol': symbol, 'from': start, 'to': end, 'apikey': api_key}
            response = requests.get(url, params=params)
        
        response.raise_for_status()
        data = response.json()
        
        if not data:
            LOG.warning(f"[EARNINGS] No earnings data for {symbol}")
            return []
        
        # Convert to DataFrame for caching
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Save to cache
        df.to_parquet(cache_path)
        LOG.success(f"[CACHE SAVED] {cache_path}")
        
        return df['date'].tolist()
    
    def get_or_fetch_historical_news(self, symbol, start, end):
        """Get historical news from cache or fetch from FMP"""
        
        cache_path = self._get_cache_path(symbol, 'news', start, end, 'news')
        
        # Check cache
        if cache_path.exists():
            LOG.info(f"[CACHE HIT] Loading {symbol} news from cache")
            df = pd.read_parquet(cache_path)
            # Convert back to list of dicts
            return df.to_dict('records')
        
        # Cache miss - fetch from API
        LOG.info(f"[CACHE MISS] Fetching {symbol} news from FMP")
        
        from src.data_handler import FMPDataClient
        fmp = FMPDataClient()
        news_list = fmp.fetch_historical_news(symbol, start, end)
        
        if not news_list:
            LOG.warning(f"[NEWS] No news data for {symbol}")
            return []
        
        # Save to cache
        df = pd.DataFrame(news_list)
        df.to_parquet(cache_path)
        LOG.success(f"[CACHE SAVED] {cache_path}")
        
        return news_list
    
    def clear_cache(self, asset_type=None):
        """Clear cache for specific asset type or all"""
        if asset_type:
            cache_path = self.cache_dir / asset_type
            for file in cache_path.glob('*.parquet'):
                file.unlink()
            LOG.info(f"[CACHE CLEARED] {asset_type}")
        else:
            for subdir in ['equities', 'futures', 'crypto', 'earnings', 'news']:
                cache_path = self.cache_dir / subdir
                for file in cache_path.glob('*.parquet'):
                    file.unlink()
            LOG.info("[CACHE CLEARED] All")


# Global instance
cache = DataCache()
