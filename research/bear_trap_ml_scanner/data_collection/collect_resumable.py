"""
Bear Trap ML Scanner - RESUMABLE Data Collection

Checkpoint-based collection that can resume after interruptions.
Saves progress every 1,000 iterations.

Author: Magellan Research Team
Date: January 22, 2026
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
from typing import List, Dict
import logging
import time
import random
import pickle

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


class ResumableCollector:
    """Data collector with checkpoint/resume capability"""
    
    def __init__(self, alpaca_key: str, alpaca_secret: str):
        self.client = StockHistoricalDataClient(alpaca_key, alpaca_secret)
        self.data_dir = Path(__file__).parent.parent / "data" / "raw"
        self.checkpoint_dir = self.data_dir / "checkpoints"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
    def save_checkpoint(self, state: Dict, checkpoint_name: str):
        """Save collection state"""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_name}.pkl"
        with open(checkpoint_file, 'wb') as f:
            pickle.dump(state, f)
        logger.info(f"💾 Checkpoint saved: {checkpoint_file}")
    
    def load_checkpoint(self, checkpoint_name: str) -> Dict:
        """Load collection state"""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_name}.pkl"
        if checkpoint_file.exists():
            with open(checkpoint_file, 'rb') as f:
                state = pickle.load(f)
            logger.info(f"📂 Checkpoint loaded: {checkpoint_file}")
            return state
        return None
    
    def get_symbol_universe(self) -> Dict[str, List[str]]:
        """Get 250 symbols (same as before)"""
        
        # Dataset A symbols (125)
        dataset_a = [
            # Original validated
            'MULN', 'ONDS', 'AMC', 'NKLA', 'WKHS', 'ACB', 'SENS', 'BTCS', 'GOEV',
            'GME', 'PLUG', 'RIOT', 'MARA', 'TLRY',
            # Meme/Retail
            'BBBY', 'DWAC', 'BKKT', 'IRNT', 'WISH', 'CLOV', 'SPCE', 'PLTR',
            'HOOD', 'SOFI', 'DKNG', 'SKLZ', 'BODY', 'EXPR', 'NAKD',
            'KOSS', 'BB', 'NOK', 'SNDL', 'CTRM', 'GNUS', 'BNGO',
            'OCGN', 'SOS', 'MVIS', 'CLNE', 'WKSP', 'SPRT', 'GREE', 'BBIG',
            # EV/Tech
            'LCID', 'RIVN', 'FSR', 'RIDE', 'ARVL', 'INDI', 'ELMS',
            'CHPT', 'BLNK', 'STEM', 'QS', 'HYLN',
            'LAZR', 'VLDR', 'LIDR', 'OUST', 'INVZ', 'AEVA',
            'PSNY', 'FFIE', 'WKHS', 'RIDE',
            # Crypto
            'MSTR', 'COIN', 'RIOT', 'MARA', 'BTBT', 'CAN', 'BITF',
            'HUT', 'ARBK', 'SDIG', 'CLSK', 'CIFR', 'CORZ', 'IREN',
            'WULF', 'BTCS', 'GREE', 'SOS', 'EBON', 'ANY',
            # Biotech
            'SAVA', 'CRIS', 'SRNE', 'VXRT', 'INO', 'OCGN', 'NVAX', 'ATOS',
            'PROG', 'PHUN', 'BIOL', 'ATNF', 'CYDY', 'OBSV', 'ADMP',
            'TNXP', 'ONTX', 'JAGX', 'AKER', 'VERU',
            # Cannabis
            'TLRY', 'CGC', 'SNDL', 'HEXO', 'OGI', 'CRON', 'ACB',
            'APHA', 'CURLF', 'GTBIF', 'TCNNF', 'CRLBF', 'TRSSF',
        ]
        
        # Dataset B symbols (125)
        dataset_b = [
            # Energy
            'TELL', 'FCEL', 'CLNE', 'HYZN', 'PLUG', 'BE', 'BLDP',
            'GP', 'NIO', 'XPEV', 'LI', 'TSLA',
            'ENPH', 'SEDG', 'RUN', 'NOVA', 'CSIQ', 'JKS', 'DQ',
            'MAXN', 'ARRY', 'SPWR', 'FSLR',
            # Fintech
            'SOFI', 'UPST', 'AFRM', 'HOOD', 'LC', 'PYPL', 'SQ',
            'COIN', 'NU', 'OPEN', 'OPFI', 'DAVE', 'BTBT', 'NAVI',
            'STNE', 'PAGS', 'MELI', 'MARA', 'RIOT', 'HUT',
            # Gaming
            'DKNG', 'SKLZ', 'FUBO', 'GENI', 'BETZ', 'RSI', 'PENN',
            'CHDN', 'GMBL', 'DESP', 'NERD', 'ESPO', 'HERO', 'GAMR',
            'RBLX', 'U', 'TTWO', 'EA', 'ATVI', 'ZNGA',
            # Tech
            'PLTR', 'SNOW', 'DDOG', 'CRWD', 'ZS', 'NET', 'OKTA',
            'MDB', 'ESTC', 'CFLT', 'S', 'DOCN', 'GTLB', 'BILL',
            'ZI', 'NCNO', 'FROG', 'PATH', 'AI', 'BBAI',
            'SOUN', 'IONQ', 'RGTI', 'QUBT', 'ARQQ',
            # Consumer
            'WISH', 'BODY', 'PTON', 'BYND', 'OATLY', 'TTCF', 'APPH',
            'CHWY', 'CVNA', 'W', 'SHOP', 'ETSY', 'PINS', 'SNAP',
            'UBER', 'LYFT', 'DASH', 'ABNB', 'EXPE', 'BKNG',
            # Misc
            'NNDM', 'DM', 'MTTR', 'PRNT', 'VELO', 'MKFG', 'SSYS',
            'XONE', 'PRLB', 'FARO', 'KODK', 'EXPR', 'BBBY', 'GME', 'AMC',
        ]
        
        # Dedupe and ensure 250 total
        all_symbols = list(set(dataset_a + dataset_b))
        random.seed(42)  # Reproducible
        random.shuffle(all_symbols)
        
        return {
            'dataset_a': all_symbols[:125],
            'dataset_b': all_symbols[125:250]
        }
    
    def collect_with_resume(self, dataset_name: str, symbols: List[str], 
                           years: List[int], threshold: float = -10.0):
        """
        Collect data with checkpoint/resume capability
        """
        checkpoint_name = f"{dataset_name}_checkpoint"
        
        # Try to load checkpoint
        state = self.load_checkpoint(checkpoint_name)
        
        if state:
            logger.info(f"🔄 Resuming from checkpoint...")
            all_events = state['events']
            completed_symbols = set(state['completed_symbols'])
            start_symbol_idx = state['current_symbol_idx']
            logger.info(f"   Resuming at symbol {start_symbol_idx}/{len(symbols)}")
            logger.info(f"   Events collected so far: {len(all_events)}")
        else:
            logger.info(f"🆕 Starting fresh collection...")
            all_events = []
            completed_symbols = set()
            start_symbol_idx = 0
        
        # Build date range
        all_dates = []
        for year in years:
            year_dates = pd.date_range(f'{year}-01-01', f'{year}-12-31', freq='B')
            all_dates.extend(year_dates)
        
        total_symbols = len(symbols)
        start_time = time.time()
        
        # Process each symbol
        for idx in range(start_symbol_idx, total_symbols):
            symbol = symbols[idx]
            
            if symbol in completed_symbols:
                continue
            
            logger.info(f"\n{'='*60}")
            logger.info(f"[{idx+1}/{total_symbols}] Processing {symbol}")
            logger.info(f"{'='*60}")
            
            symbol_events = 0
            
            for date in all_dates:
                event = self.identify_first_selloff(symbol, date, threshold)
                if event:
                    symbol_events += 1
                    all_events.append(event)
                time.sleep(0.01)
            
            completed_symbols.add(symbol)
            
            if symbol_events > 0:
                logger.info(f"✓ {symbol}: {symbol_events} events | Total: {len(all_events)}")
            
            # Save checkpoint every 5 symbols
            if (idx + 1) % 5 == 0:
                state = {
                    'events': all_events,
                    'completed_symbols': list(completed_symbols),
                    'current_symbol_idx': idx + 1,
                    'timestamp': datetime.now().isoformat()
                }
                self.save_checkpoint(state, checkpoint_name)
                
                # Also save intermediate CSV
                if all_events:
                    df_temp = pd.DataFrame(all_events)
                    df_temp.to_csv(self.data_dir / f"{dataset_name}_partial.csv", index=False)
                    logger.info(f"💾 Partial dataset saved: {len(all_events)} events")
        
        # Final save
        if all_events:
            df = pd.DataFrame(all_events)
            df['dataset'] = dataset_name
            df.to_csv(self.data_dir / f"{dataset_name}_final.csv", index=False)
            logger.info(f"\n✅ {dataset_name.upper()} COMPLETE: {len(df)} events")
            
            # Clean up checkpoint
            checkpoint_file = self.checkpoint_dir / f"{checkpoint_name}.pkl"
            if checkpoint_file.exists():
                checkpoint_file.unlink()
            
            return df
        
        return pd.DataFrame()
    
    def identify_first_selloff(self, symbol: str, date: datetime, threshold: float) -> Dict:
        """Find first selloff (same as before)"""
        try:
            start = date.replace(hour=9, minute=30, second=0, microsecond=0)
            end = date.replace(hour=16, minute=0, second=0, microsecond=0)
            
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Minute,
                start=start,
                end=end,
                feed='sip'
            )
            
            bars = self.client.get_stock_bars(request)
            
            if not bars or symbol not in bars.data:
                return None
            
            data = []
            for bar in bars.data[symbol]:
                data.append({
                    'timestamp': bar.timestamp,
                    'open': bar.open,
                    'low': bar.low,
                    'close': bar.close,
                    'high': bar.high,
                    'volume': bar.volume,
                })
            
            if not data:
                return None
            
            df = pd.DataFrame(data)
            df = df.sort_values('timestamp')
            
            session_open = df.iloc[0]['open']
            df['drop_pct'] = ((df['low'] - session_open) / session_open) * 100
            
            selloff_bars = df[df['drop_pct'] <= threshold]
            
            if selloff_bars.empty:
                return None
            
            first_bar = selloff_bars.iloc[0]
            
            return {
                'symbol': symbol,
                'date': date.strftime('%Y-%m-%d'),
                'timestamp': first_bar['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'session_open': float(session_open),
                'low': float(first_bar['low']),
                'close': float(first_bar['close']),
                'high': float(first_bar['high']),
                'volume': int(first_bar['volume']),
                'drop_pct': float(first_bar['drop_pct']),
                'event_type': 'first_cross',
                'threshold_used': threshold,
            }
        except Exception as e:
            logger.debug(f"Error: {e}")
            return None


def main():
    """Resumable collection"""
    
    alpaca_key = os.getenv('APCA_API_KEY_ID')
    alpaca_secret = os.getenv('APCA_API_SECRET_KEY')
    
    if not all([alpaca_key, alpaca_secret]):
        logger.error("Missing API keys!")
        return
    
    collector = ResumableCollector(alpaca_key, alpaca_secret)
    
    print("\n" + "="*80)
    print("BEAR TRAP ML SCANNER - RESUMABLE COLLECTION")
    print("Features: Checkpoints every 5 symbols, can resume after interruption")
    print("="*80 + "\n")
    
    universe = collector.get_symbol_universe()
    years = [2024, 2023, 2022, 2021, 2020]
    
    # Collect Dataset A
    logger.info("🔵 Dataset A Collection")
    df_a = collector.collect_with_resume('dataset_a', universe['dataset_a'], years, -10.0)
    
    # Collect Dataset B
    logger.info("\n🟢 Dataset B Collection")
    df_b = collector.collect_with_resume('dataset_b', universe['dataset_b'], years, -10.0)
    
    # Combine
    if not df_a.empty and not df_b.empty:
        df_combined = pd.concat([df_a, df_b], ignore_index=True)
        df_combined.to_csv(collector.data_dir / 'ultimate_combined_resumable.csv', index=False)
        
        print("\n" + "="*80)
        print("🎉 COLLECTION COMPLETE!")
        print("="*80)
        print(f"Dataset A: {len(df_a):,} events")
        print(f"Dataset B: {len(df_b):,} events")
        print(f"TOTAL: {len(df_combined):,} events")
        print("="*80 + "\n")


if __name__ == '__main__':
    main()
