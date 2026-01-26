#!/usr/bin/env python3
"""
FMP Sentiment Data Cache
Fetches and caches daily sentiment scores for symbols
"""

import os
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import requests
from typing import List, Dict
import json

class SentimentCache:
    def __init__(self, cache_dir: str = "data/cache/sentiment"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = os.getenv('FMP_API_KEY')
        
        if not self.api_key:
            print("⚠️ FMP_API_KEY not found - sentiment will be 0.0")
    
    def get_cache_path(self, symbol: str, start_date: str, end_date: str) -> Path:
        """Generate cache file path"""
        return self.cache_dir / f"{symbol}_sentiment_{start_date}_{end_date}.parquet"
    
    def fetch_news_sentiment(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch news sentiment from FMP and calculate daily scores
        Returns DataFrame with date and sentiment score
        """
        if not self.api_key:
            # Return neutral sentiment
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            return pd.DataFrame({
                'date': dates,
                'sentiment': [0.0] * len(dates)
            })
        
        print(f"📰 Fetching news for {symbol} ({start_date} to {end_date})...")
        
        # FMP stable stock news endpoint with date range
        url = f"https://financialmodelingprep.com/stable/news/stock"
        params = {
            'symbols': symbol,
            'from': start_date,
            'to': end_date,
            'page': 0,
            'limit': 1000,  # Large limit to get all news in range
            'apikey': self.api_key
        }
        
        all_news = []
        
        try:
            # Fetch news for date range (single call with date params)
            response = requests.get(url, params=params, timeout=60)
            
            if response.status_code != 200:
                print(f"⚠️ FMP API error: {response.status_code}")
                dates = pd.date_range(start=start_date, end=end_date, freq='D')
                return pd.DataFrame({
                    'date': dates,
                    'sentiment': [0.0] * len(dates)
                })
            
            all_news = response.json()
                
        except Exception as e:
            print(f"⚠️ Error fetching sentiment: {e}")
            # Return neutral sentiment on error
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            return pd.DataFrame({
                'date': dates,
                'sentiment': [0.0] * len(dates)
            })
        
        # Process news into sentiment scores
        if not all_news:
            print(f"⚠️ No news found for {symbol}")
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            return pd.DataFrame({
                'date': dates,
                'sentiment': [0.0] * len(dates)
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(all_news)
        df['date'] = pd.to_datetime(df['publishedDate']).dt.date
        
        # Filter to date range
        start_dt = pd.to_datetime(start_date).date()
        end_dt = pd.to_datetime(end_date).date()
        df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
        
        # Use news volume as sentiment proxy:
        # More news = higher market attention/momentum
        # Calculate daily news count
        news_count = df.groupby('date').size().reset_index(name='count')
        
        # Normalize news count to sentiment scale using z-score
        # Z-score: (x - mean) / std
        mean_count = news_count['count'].mean()
        std_count = news_count['count'].std()
        
        if std_count > 0:
            news_count['sentiment'] = (news_count['count'] - mean_count) / std_count
            # Clip to [-1, 1] range
            news_count['sentiment'] = news_count['sentiment'].clip(-1.0, 1.0)
        else:
            news_count['sentiment'] = 0.0
        
        # Keep only date and sentiment
        news_count = news_count[['date', 'sentiment']]
        
        # Fill missing dates with neutral sentiment
        all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
        result = pd.DataFrame({'date': all_dates.date})
        result = result.merge(news_count, on='date', how='left')
        result['sentiment'] = result['sentiment'].fillna(0.0)
        
        print(f"✅ Fetched {len(result)} days of sentiment data")
        return result
    
    def get_or_fetch(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Get sentiment from cache or fetch from FMP
        """
        cache_path = self.get_cache_path(symbol, start_date, end_date)
        
        # Check cache
        if cache_path.exists():
            print(f"📂 Loading cached sentiment for {symbol}")
            df = pd.read_parquet(cache_path)
            df['date'] = pd.to_datetime(df['date']).dt.date
            return df
        
        # Fetch from FMP
        df = self.fetch_news_sentiment(symbol, start_date, end_date)
        
        # Save to cache
        df.to_parquet(cache_path, index=False)
        print(f"💾 Cached sentiment to {cache_path}")
        
        return df
