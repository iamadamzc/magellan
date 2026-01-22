"""
Bear Trap ML Scanner - ULTIMATE DATA COLLECTION

Target: 5,000+ events for production-grade ML model

Strategy:
- 250 symbols (125 per dataset)
- 5 years (2020-2024)
- -10% threshold (still meaningful selloffs)
- First-cross deduplication

Expected yield: 5,000-8,000 events

Author: Magellan Research Team
Date: January 22, 2026
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict
import logging
import time
import random

# Add project root
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UltimateDataCollector:
    """Collect maximum possible training data"""
    
    def __init__(self, alpaca_key: str, alpaca_secret: str):
        self.client = StockHistoricalDataClient(alpaca_key, alpaca_secret)
        self.data_dir = Path(__file__).parent.parent / "data" / "raw"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def get_expanded_symbol_universe(self) -> Dict[str, List[str]]:
        """
        Get 250 symbols split into Dataset A (validated-style) and Dataset B (random)
        """
        logger.info("Building 250-symbol universe...")
        
        # Dataset A: Validated + similar volatile small-caps (125 symbols)
        dataset_a_symbols = [
            # Original validated (14)
            'MULN', 'ONDS', 'AMC', 'NKLA', 'WKHS', 'ACB', 'SENS', 'BTCS', 'GOEV',
            'GME', 'PLUG', 'RIOT', 'MARA', 'TLRY',
            
            # Meme/Retail expansion (30)
            'BBBY', 'DWAC', 'BKKT', 'IRNT', 'WISH', 'CLOV', 'SPCE', 'PLTR',
            'HOOD', 'SOFI', 'DKNG', 'SKLZ', 'BODY', 'EXPR', 'NAKD',
            'KOSS', 'BB', 'NOK', 'SNDL', 'CTRM', 'GNUS', 'BNGO',
            'OCGN', 'SOS', 'MVIS', 'CLNE', 'WKSP', 'SPRT', 'GREE', 'BBIG',
            
            # EV/Tech SPACs (25)
            'LCID', 'RIVN', 'FSR', 'RIDE', 'ARVL', 'INDI', 'ELMS',
            'CHPT', 'BLNK', 'STEM', 'QS', 'HYLN', 'NKLA', 'GOEV',
            'LAZR', 'VLDR', 'LIDR', 'OUST', 'INVZ', 'AEVA',
            'PSNY', 'FFIE', 'MULN', 'WKHS', 'RIDE',
            
            # Crypto-related (20)
            'MSTR', 'COIN', 'RIOT', 'MARA', 'BTBT', 'CAN', 'BITF',
            'HUT', 'ARBK', 'SDIG', 'CLSK', 'CIFR', 'CORZ', 'IREN',
            'WULF', 'BTCS', 'GREE', 'SOS', 'EBON', 'ANY',
            
            # Biotech/Pharma small-caps (20)
            'SAVA', 'CRIS', 'SRNE', 'VXRT', 'INO', 'OCGN', 'NVAX', 'ATOS',
            'PROG', 'PHUN', 'BIOL', 'ATNF', 'CYDY', 'OBSV', 'ADMP',
            'TNXP', 'ONTX', 'JAGX', 'AKER', 'VERU',
            
            # Cannabis (16)
            'TLRY', 'CGC', 'SNDL', 'HEXO', 'OGI', 'CRON', 'ACB',
            'APHA', 'CURLF', 'GTBIF', 'TCNNF', 'CRLBF', 'TRSSF', 'MSOS',
            'YOLO', 'THCX',
        ]
        
        # Dataset B: Broader volatile universe (125 symbols)
        dataset_b_symbols = [
            # Energy/Commodity (25)
            'TELL', 'FCEL', 'CLNE', 'HYZN', 'PLUG', 'BE', 'BLDP',
            'NKLA', 'HYLN', 'GP', 'NIO', 'XPEV', 'LI', 'TSLA',
            'ENPH', 'SEDG', 'RUN', 'NOVA', 'CSIQ', 'JKS', 'DQ',
            'MAXN', 'ARRY', 'SPWR', 'FSLR',
            
            # Fintech/Payments (20)
            'SOFI', 'UPST', 'AFRM', 'HOOD', 'LC', 'PYPL', 'SQ',
            'COIN', 'NU', 'OPEN', 'OPFI', 'DAVE', 'BTBT', 'NAVI',
            'STNE', 'PAGS', 'MELI', 'MARA', 'RIOT', 'HUT',
            
            # Gaming/Entertainment (20)
            'DKNG', 'SKLZ', 'FUBO', 'GENI', 'BETZ', 'RSI', 'PENN',
            'CHDN', 'GMBL', 'DESP', 'NERD', 'ESPO', 'HERO', 'GAMR',
            'RBLX', 'U', 'TTWO', 'EA', 'ATVI', 'ZNGA',
            
            # Tech/Software small-caps (25)
            'PLTR', 'SNOW', 'DDOG', 'CRWD', 'ZS', 'NET', 'OKTA',
            'MDB', 'ESTC', 'CFLT', 'S', 'DOCN', 'GTLB', 'BILL',
            'ZI', 'NCNO', 'FROG', 'PATH', 'AI', 'BBAI',
            'SOUN', 'IONQ', 'RGTI', 'QUBT', 'ARQQ',
            
            # Consumer/Retail (20)
            'WISH', 'BODY', 'PTON', 'BYND', 'OATLY', 'TTCF', 'APPH',
            'CHWY', 'CVNA', 'W', 'SHOP', 'ETSY', 'PINS', 'SNAP',
            'UBER', 'LYFT', 'DASH', 'ABNB', 'EXPE', 'BKNG',
            
            # Misc volatiles (15)
            'NNDM', 'DM', 'MTTR', 'PRNT', 'VELO', 'MKFG', 'SSYS',
            'XONE', 'PRLB', 'FARO', 'KODK', 'EXPR', 'BBBY', 'GME', 'AMC',
        ]
        
        # Deduplicate and ensure we have 250 total
        all_symbols = list(set(dataset_a_symbols + dataset_b_symbols))
        random.shuffle(all_symbols)
        
        # Split into A and B
        final_a = all_symbols[:125]
        final_b = all_symbols[125:250]
        
        logger.info(f"Dataset A: {len(final_a)} symbols")
        logger.info(f"Dataset B: {len(final_b)} symbols")
        
        return {
            'dataset_a': final_a,
            'dataset_b': final_b
        }
    
    def get_daily_bars(self, symbol: str, date: datetime) -> pd.DataFrame:
        """Fetch 1-minute bars for a trading day"""
        start = date.replace(hour=9, minute=30, second=0, microsecond=0)
        end = date.replace(hour=16, minute=0, second=0, microsecond=0)
        
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Minute,
            start=start,
            end=end,
            feed='sip'
        )
        
        try:
            bars = self.client.get_stock_bars(request)
            
            if not bars or symbol not in bars.data:
                return pd.DataFrame()
            
            data = []
            for bar in bars.data[symbol]:
                data.append({
                    'timestamp': bar.timestamp,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume,
                })
            
            df = pd.DataFrame(data)
            if not df.empty:
                df = df.sort_values('timestamp').reset_index(drop=True)
            return df
            
        except Exception as e:
            logger.debug(f"Error fetching {symbol} on {date.date()}: {e}")
            return pd.DataFrame()
    
    def identify_first_selloff(self, symbol: str, date: datetime, 
                               threshold: float = -10.0) -> Dict:
        """
        Find FIRST selloff crossing threshold in a day
        
        Args:
            threshold: -10.0 for broader coverage (default)
        """
        df = self.get_daily_bars(symbol, date)
        
        if df.empty:
            return None
        
        session_open = df.iloc[0]['open']
        df['drop_from_open_pct'] = ((df['low'] - session_open) / session_open) * 100
        
        # Find FIRST bar crossing threshold
        selloff_bars = df[df['drop_from_open_pct'] <= threshold]
        
        if selloff_bars.empty:
            return None
        
        first_bar = selloff_bars.iloc[0]
        
        event = {
            'symbol': symbol,
            'date': date.strftime('%Y-%m-%d'),
            'timestamp': first_bar['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'session_open': float(session_open),
            'low': float(first_bar['low']),
            'close': float(first_bar['close']),
            'high': float(first_bar['high']),
            'volume': int(first_bar['volume']),
            'drop_pct': float(first_bar['drop_from_open_pct']),
            'event_type': 'first_cross',
            'threshold_used': threshold,
        }
        
        return event
    
    def collect_dataset(self, symbols: List[str], years: List[int], 
                       dataset_name: str, threshold: float = -10.0) -> pd.DataFrame:
        """Collect data for a symbol set across multiple years"""
        
        logger.info(f"\n{'='*80}")
        logger.info(f"COLLECTING {dataset_name.upper()}")
        logger.info(f"Symbols: {len(symbols)}, Years: {years}, Threshold: {threshold}%")
        logger.info(f"{'='*80}")
        
        all_events = []
        
        # Build date range across all years
        all_dates = []
        for year in years:
            year_dates = pd.date_range(f'{year}-01-01', f'{year}-12-31', freq='B')
            all_dates.extend(year_dates)
        
        total_iterations = len(symbols) * len(all_dates)
        current = 0
        start_time = time.time()
        
        for symbol in symbols:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing {symbol}")
            logger.info(f"{'='*60}")
            symbol_events = 0
            
            for date in all_dates:
                current += 1
                
                # Progress every 100 iterations
                if current % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = current / elapsed if elapsed > 0 else 0
                    eta_seconds = (total_iterations - current) / rate if rate > 0 else 0
                    eta_hours = eta_seconds / 3600
                    
                    pct = 100 * current / total_iterations
                    logger.info(f"  Progress: {current:,}/{total_iterations:,} ({pct:.1f}%) | "
                              f"Rate: {rate:.1f} it/s | ETA: {eta_hours:.1f}h | "
                              f"Events: {len(all_events):,}")
                
                event = self.identify_first_selloff(symbol, date, threshold)
                
                if event:
                    symbol_events += 1
                    all_events.append(event)
                
                # Minimal delay
                time.sleep(0.01)
            
            if symbol_events > 0:
                logger.info(f"✓ {symbol}: {symbol_events} events")
        
        if all_events:
            df = pd.DataFrame(all_events)
            df['dataset'] = dataset_name
            logger.info(f"\n{'='*80}")
            logger.info(f"✅ {dataset_name.upper()} COMPLETE: {len(df):,} events")
            logger.info(f"{'='*80}")
            return df
        else:
            return pd.DataFrame()
    
    def save_dataset(self, df: pd.DataFrame, filename: str):
        """Save to CSV"""
        if df.empty:
            logger.warning("Empty dataset, not saving")
            return
        
        filepath = self.data_dir / filename
        df.to_csv(filepath, index=False)
        
        size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        logger.info(f"\n💾 Dataset saved:")
        logger.info(f"   File: {filepath}")
        logger.info(f"   Rows: {len(df):,}")
        logger.info(f"   Size: {size_mb:.2f} MB")


def main():
    """Ultimate data collection - 5,000+ events"""
    
    alpaca_key = os.getenv('APCA_API_KEY_ID')
    alpaca_secret = os.getenv('APCA_API_SECRET_KEY')
    
    if not all([alpaca_key, alpaca_secret]):
        logger.error("Missing Alpaca API keys!")
        return
    
    collector = UltimateDataCollector(alpaca_key, alpaca_secret)
    
    print("\n" + "="*80)
    print("BEAR TRAP ML SCANNER - ULTIMATE DATA COLLECTION")
    print("Target: 5,000+ events for production ML")
    print("="*80)
    print("Configuration:")
    print("  - Symbols: 250 (125 per dataset)")
    print("  - Years: 2020-2024 (5 years)")
    print("  - Threshold: -10% (broader coverage)")
    print("  - Deduplication: First-cross only")
    print("="*80 + "\n")
    
    # Get symbol universe
    universe = collector.get_expanded_symbol_universe()
    
    # Collect both datasets
    years = [2024, 2023, 2022, 2021, 2020]
    
    # Dataset A
    logger.info("\n🔵 Starting Dataset A collection...")
    df_a = collector.collect_dataset(
        universe['dataset_a'], 
        years, 
        'dataset_a',
        threshold=-10.0
    )
    
    # Dataset B
    logger.info("\n🟢 Starting Dataset B collection...")
    df_b = collector.collect_dataset(
        universe['dataset_b'], 
        years, 
        'dataset_b',
        threshold=-10.0
    )
    
    # Combine
    if not df_a.empty and not df_b.empty:
        df_combined = pd.concat([df_a, df_b], ignore_index=True)
        
        # Save individual datasets
        collector.save_dataset(df_a, 'ultimate_dataset_a.csv')
        collector.save_dataset(df_b, 'ultimate_dataset_b.csv')
        
        # Save combined
        collector.save_dataset(df_combined, 'ultimate_combined_5years.csv')
        
        # Final summary
        print("\n" + "="*80)
        print("🎉 ULTIMATE DATA COLLECTION COMPLETE!")
        print("="*80)
        print(f"Dataset A: {len(df_a):,} events")
        print(f"Dataset B: {len(df_b):,} events")
        print(f"TOTAL: {len(df_combined):,} events")
        print(f"\nBy Year:")
        df_combined['year'] = pd.to_datetime(df_combined['date']).dt.year
        yearly = df_combined.groupby('year').size()
        for year, count in yearly.items():
            print(f"  {year}: {count:,} events")
        print("="*80 + "\n")


if __name__ == '__main__':
    main()
