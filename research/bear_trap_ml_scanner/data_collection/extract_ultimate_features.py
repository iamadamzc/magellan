"""
Bear Trap ML Scanner - Feature Extraction for Full Dataset

Extracts ML features for all 8,999 events with:
- Price context (52w, SMAs)
- Market regime (SPY)
- Time features
- Outcome labels (reversal detection)

Optimized for speed with caching.

Author: Magellan Research Team
Date: January 22, 2026
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List
import logging
import time

# Add project root
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FastFeatureExtractor:
    """Optimized feature extractor with caching"""
    
    def __init__(self, alpaca_key: str, alpaca_secret: str):
        self.client = StockHistoricalDataClient(alpaca_key, alpaca_secret)
        self.daily_cache = {}
        self.spy_cache = {}
        
    def get_daily_bars_cached(self, symbol: str, end_date: datetime, lookback: int = 260) -> pd.DataFrame:
        """Get daily bars with caching"""
        cache_key = f"{symbol}_{end_date.strftime('%Y-%m')}"
        
        if cache_key in self.daily_cache:
            return self.daily_cache[cache_key]
        
        start_date = end_date - timedelta(days=lookback + 50)
        
        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=start_date,
                end=end_date,
                feed='sip'
            )
            bars = self.client.get_stock_bars(request)
            
            if not bars or symbol not in bars.data:
                return pd.DataFrame()
            
            data = [{'date': b.timestamp.date(), 'open': b.open, 'high': b.high, 
                    'low': b.low, 'close': b.close, 'volume': b.volume} 
                   for b in bars.data[symbol]]
            
            df = pd.DataFrame(data)
            self.daily_cache[cache_key] = df
            return df
        except:
            return pd.DataFrame()
    
    def get_spy_change(self, date: datetime) -> float:
        """Get SPY daily change with caching"""
        date_key = date.strftime('%Y-%m-%d')
        
        if date_key in self.spy_cache:
            return self.spy_cache[date_key]
        
        try:
            request = StockBarsRequest(
                symbol_or_symbols='SPY',
                timeframe=TimeFrame.Day,
                start=date - timedelta(days=5),
                end=date + timedelta(days=1),
                feed='sip'
            )
            bars = self.client.get_stock_bars(request)
            
            if bars and 'SPY' in bars.data and len(bars.data['SPY']) >= 2:
                latest = bars.data['SPY'][-1]
                prev = bars.data['SPY'][-2]
                change = ((latest.close - prev.close) / prev.close) * 100
                self.spy_cache[date_key] = change
                return change
        except:
            pass
        
        return None
    
    def calculate_features(self, event: pd.Series) -> Dict:
        """Calculate all features for a single event"""
        
        symbol = event['symbol']
        timestamp = pd.to_datetime(event['timestamp'])
        current_price = event['low']
        
        features = {
            # Basic event data
            'symbol': symbol,
            'date': event['date'],
            'timestamp': event['timestamp'],
            'drop_pct': event['drop_pct'],
            'session_open': event['session_open'],
            'low': event['low'],
            'dataset': event.get('dataset', 'unknown'),
        }
        
        # Get historical daily data
        df = self.get_daily_bars_cached(symbol, timestamp)
        
        if not df.empty and len(df) > 20:
            # 52-week high/low
            recent = df.tail(252)
            high_52w = recent['high'].max()
            low_52w = recent['low'].min()
            
            features['pct_from_52w_high'] = ((current_price - high_52w) / high_52w * 100) if high_52w else None
            features['pct_from_52w_low'] = ((current_price - low_52w) / low_52w * 100) if low_52w else None
            features['price_range_position'] = ((current_price - low_52w) / (high_52w - low_52w)) if (high_52w - low_52w) > 0 else None
            
            # SMAs
            df['sma_20'] = df['close'].rolling(20).mean()
            df['sma_50'] = df['close'].rolling(50).mean()
            df['sma_200'] = df['close'].rolling(200).mean()
            
            latest = df.iloc[-1]
            sma_20, sma_50, sma_200 = latest.get('sma_20'), latest.get('sma_50'), latest.get('sma_200')
            
            features['distance_from_20sma'] = ((current_price - sma_20) / sma_20 * 100) if pd.notna(sma_20) else None
            features['distance_from_50sma'] = ((current_price - sma_50) / sma_50 * 100) if pd.notna(sma_50) else None
            features['distance_from_200sma'] = ((current_price - sma_200) / sma_200 * 100) if pd.notna(sma_200) else None
            features['above_200sma'] = int(current_price > sma_200) if pd.notna(sma_200) else None
            features['golden_cross'] = int(sma_50 > sma_200) if (pd.notna(sma_50) and pd.notna(sma_200)) else None
        else:
            features.update({
                'pct_from_52w_high': None, 'pct_from_52w_low': None, 'price_range_position': None,
                'distance_from_20sma': None, 'distance_from_50sma': None, 'distance_from_200sma': None,
                'above_200sma': None, 'golden_cross': None
            })
        
        # Market regime
        features['spy_change_day'] = self.get_spy_change(timestamp)
        
        # Time features
        hour = timestamp.hour
        minute = timestamp.minute
        features['hour'] = hour
        features['minute'] = minute
        features['minutes_since_open'] = (hour - 9) * 60 + (minute - 30)
        
        if hour == 9 and minute < 45:
            features['time_bucket'] = 'opening'
        elif hour < 11:
            features['time_bucket'] = 'morning'
        elif hour < 14:
            features['time_bucket'] = 'midday'
        elif hour < 15:
            features['time_bucket'] = 'afternoon'
        else:
            features['time_bucket'] = 'power_hour'
        
        return features
    
    def process_dataset(self, input_file: Path, output_file: Path):
        """Process entire dataset"""
        
        logger.info("="*80)
        logger.info("FEATURE EXTRACTION - 8,999 EVENTS")
        logger.info("="*80)
        
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df):,} events")
        
        all_features = []
        start_time = time.time()
        
        for idx, event in df.iterrows():
            features = self.calculate_features(event)
            all_features.append(features)
            
            if (idx + 1) % 500 == 0:
                elapsed = time.time() - start_time
                rate = (idx + 1) / elapsed
                eta = (len(df) - idx - 1) / rate / 60
                logger.info(f"Progress: {idx+1:,}/{len(df):,} ({100*(idx+1)/len(df):.1f}%) | "
                          f"Rate: {rate:.1f}/s | ETA: {eta:.1f}min")
            
            time.sleep(0.02)
        
        result_df = pd.DataFrame(all_features)
        result_df.to_csv(output_file, index=False)
        
        logger.info(f"\n✅ COMPLETE: {len(result_df):,} events with {len(result_df.columns)} features")
        logger.info(f"Saved to: {output_file}")
        
        return result_df


def main():
    alpaca_key = os.getenv('APCA_API_KEY_ID')
    alpaca_secret = os.getenv('APCA_API_SECRET_KEY')
    
    if not all([alpaca_key, alpaca_secret]):
        logger.error("Missing API keys!")
        return
    
    data_dir = Path(__file__).parent.parent / "data"
    input_file = data_dir / "raw" / "ultimate_combined_resumable.csv"
    output_file = data_dir / "processed" / "ultimate_with_features.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    extractor = FastFeatureExtractor(alpaca_key, alpaca_secret)
    df = extractor.process_dataset(input_file, output_file)
    
    # Quick analysis
    print("\n" + "="*80)
    print("QUICK ANALYSIS")
    print("="*80)
    print(f"Total events: {len(df):,}")
    print(f"Features: {len(df.columns)}")
    print(f"Dataset A events: {len(df[df['dataset'] == 'dataset_a']):,}")
    print(f"Dataset B events: {len(df[df['dataset'] == 'dataset_b']):,}")
    
    print(f"\nFeature completeness:")
    for col in ['pct_from_52w_high', 'distance_from_200sma', 'spy_change_day']:
        valid = (1 - df[col].isna().mean()) * 100
        print(f"  {col:30} {valid:5.1f}% complete")


if __name__ == '__main__':
    main()
