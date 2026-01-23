"""
Outcome Extraction - Add Recovery/Reversal Data to Selloff Events

Adds post-selloff outcome metrics to existing 8,999 events:
- Same-day recovery metrics
- End-of-day outcomes
- Next-day outcomes (where available)

Author: Magellan Research Team
Date: January 22, 2026
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
import time
import pickle

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OutcomeExtractor:
    """Extract post-selloff outcomes for all events"""
    
    def __init__(self, alpaca_key: str, alpaca_secret: str):
        self.client = StockHistoricalDataClient(alpaca_key, alpaca_secret)
        self.data_dir = Path('data/market_events/intraday_selloffs/v1_smallcap_10pct_5yr')
        self.checkpoint_file = self.data_dir / 'outcome_checkpoint.pkl'
        
    def get_intraday_bars(self, symbol: str, date: datetime) -> pd.DataFrame:
        """Fetch 1-minute bars for a trading day"""
        start = date.replace(hour=9, minute=30, second=0, microsecond=0)
        end = date.replace(hour=16, minute=0, second=0, microsecond=0)
        
        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Minute,
                start=start,
                end=end,
                feed='sip'
            )
            bars = self.client.get_stock_bars(request)
            
            if not bars or symbol not in bars.data:
                return pd.DataFrame()
            
            data = [{'timestamp': b.timestamp, 'open': b.open, 'high': b.high,
                    'low': b.low, 'close': b.close, 'volume': b.volume}
                   for b in bars.data[symbol]]
            
            return pd.DataFrame(data).sort_values('timestamp').reset_index(drop=True)
        except Exception as e:
            logger.debug(f"Error fetching {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_outcomes(self, event: pd.Series, bars_df: pd.DataFrame) -> dict:
        """Calculate all outcome metrics for a single event"""
        
        outcomes = {
            # Recovery metrics (% from selloff low)
            'recovery_pct_30min': None,
            'recovery_pct_60min': None,
            'recovery_pct_120min': None,
            'recovery_pct_eod': None,
            
            # Binary outcomes
            'reversed_30min': None,  # Recovered > 50% of drop in 30 min?
            'reversed_60min': None,
            'reversed_eod': None,    # Closed above selloff low
            
            # Session metrics
            'eod_close': None,
            'eod_high': None,
            'eod_low': None,
            'selloff_was_day_low': None,  # Was the selloff low the day's low?
            
            # Risk metrics
            'max_additional_drop': None,  # Max drawdown AFTER selloff
            'time_to_recovery': None,     # Minutes to recover above low
        }
        
        if bars_df.empty:
            return outcomes
        
        selloff_time = pd.to_datetime(event['timestamp'])
        selloff_low = float(event['low'])
        session_open = float(event['session_open'])
        drop_pct = float(event['drop_pct'])
        
        # Filter to bars AFTER the selloff
        bars_df['timestamp'] = pd.to_datetime(bars_df['timestamp']).dt.tz_localize(None)
        selloff_time = selloff_time.tz_localize(None) if selloff_time.tzinfo else selloff_time
        post_selloff = bars_df[bars_df['timestamp'] > selloff_time].copy()
        
        if post_selloff.empty:
            return outcomes
        
        # Calculate minutes since selloff
        post_selloff['minutes_since_selloff'] = (
            post_selloff['timestamp'] - selloff_time
        ).dt.total_seconds() / 60
        
        # End of day metrics
        eod_bar = bars_df.iloc[-1]
        outcomes['eod_close'] = float(eod_bar['close'])
        outcomes['eod_high'] = float(bars_df['high'].max())
        outcomes['eod_low'] = float(bars_df['low'].min())
        
        # Was selloff the day's low?
        day_low = bars_df['low'].min()
        outcomes['selloff_was_day_low'] = int(selloff_low <= day_low * 1.001)  # 0.1% tolerance
        
        # Recovery percentages at different time windows
        for window, col in [(30, 'recovery_pct_30min'), (60, 'recovery_pct_60min'), 
                            (120, 'recovery_pct_120min')]:
            window_bars = post_selloff[post_selloff['minutes_since_selloff'] <= window]
            if not window_bars.empty:
                max_high = window_bars['high'].max()
                recovery_pct = ((max_high - selloff_low) / selloff_low) * 100
                outcomes[col] = float(recovery_pct)
        
        # EOD recovery
        eod_close = float(eod_bar['close'])
        outcomes['recovery_pct_eod'] = ((eod_close - selloff_low) / selloff_low) * 100
        
        # Binary reversed flags
        # Reversed = recovered more than 50% of the drop
        half_drop = abs(drop_pct) / 2
        
        for window, pct_col, reversed_col in [
            (30, 'recovery_pct_30min', 'reversed_30min'),
            (60, 'recovery_pct_60min', 'reversed_60min')
        ]:
            if outcomes[pct_col] is not None:
                outcomes[reversed_col] = int(outcomes[pct_col] >= half_drop)
        
        # EOD reversed = closed above selloff low
        outcomes['reversed_eod'] = int(eod_close > selloff_low)
        
        # Max additional drop after selloff
        if not post_selloff.empty:
            min_low_after = post_selloff['low'].min()
            additional_drop = ((min_low_after - selloff_low) / selloff_low) * 100
            outcomes['max_additional_drop'] = min(0, float(additional_drop))  # Negative or 0
        
        # Time to recovery (first bar that trades above selloff low)
        recovered_bars = post_selloff[post_selloff['high'] > selloff_low]
        if not recovered_bars.empty:
            first_recovery = recovered_bars.iloc[0]
            outcomes['time_to_recovery'] = float(first_recovery['minutes_since_selloff'])
        
        return outcomes
    
    def process_all_events(self):
        """Process all events and add outcome columns"""
        
        # Load existing data
        input_file = self.data_dir / 'combined_with_features.csv'
        df = pd.read_csv(input_file)
        
        logger.info("="*80)
        logger.info("OUTCOME EXTRACTION - Adding Recovery Data")
        logger.info(f"Processing {len(df):,} events")
        logger.info("="*80)
        
        # Load checkpoint if exists
        start_idx = 0
        outcome_data = {}
        
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'rb') as f:
                checkpoint = pickle.load(f)
                outcome_data = checkpoint.get('outcomes', {})
                start_idx = checkpoint.get('last_idx', 0) + 1
                logger.info(f"Resuming from checkpoint at index {start_idx}")
        
        start_time = time.time()
        
        for idx in range(start_idx, len(df)):
            event = df.iloc[idx]
            
            # Get intraday bars
            event_date = pd.to_datetime(event['date'])
            bars = self.get_intraday_bars(event['symbol'], event_date)
            
            # Calculate outcomes
            outcomes = self.calculate_outcomes(event, bars)
            outcome_data[idx] = outcomes
            
            # Progress logging
            if (idx + 1) % 200 == 0:
                elapsed = time.time() - start_time
                rate = (idx - start_idx + 1) / elapsed if elapsed > 0 else 0
                remaining = len(df) - idx - 1
                eta = remaining / rate / 60 if rate > 0 else 0
                
                logger.info(f"Progress: {idx+1:,}/{len(df):,} ({100*(idx+1)/len(df):.1f}%) | "
                          f"Rate: {rate:.1f}/s | ETA: {eta:.1f}min")
            
            # Save checkpoint every 500 events
            if (idx + 1) % 500 == 0:
                checkpoint = {'outcomes': outcome_data, 'last_idx': idx}
                with open(self.checkpoint_file, 'wb') as f:
                    pickle.dump(checkpoint, f)
                logger.info(f"Checkpoint saved at index {idx}")
            
            time.sleep(0.02)  # Rate limiting
        
        # Convert outcomes to DataFrame and merge
        logger.info("Merging outcomes with original data...")
        outcome_df = pd.DataFrame.from_dict(outcome_data, orient='index')
        
        # Merge on index
        for col in outcome_df.columns:
            df[col] = outcome_df[col]
        
        # Save updated dataset
        output_file = self.data_dir / 'combined_with_outcomes.csv'
        df.to_csv(output_file, index=False)
        
        # Clean up checkpoint
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("OUTCOME EXTRACTION COMPLETE")
        logger.info("="*80)
        logger.info(f"Total events: {len(df):,}")
        logger.info(f"Output: {output_file}")
        
        # Quick stats
        logger.info("\nOutcome Statistics:")
        for col in ['reversed_30min', 'reversed_60min', 'reversed_eod']:
            if col in df.columns:
                rate = df[col].mean() * 100
                logger.info(f"  {col}: {rate:.1f}% reversed")
        
        return df


def main():
    alpaca_key = os.getenv('APCA_API_KEY_ID')
    alpaca_secret = os.getenv('APCA_API_SECRET_KEY')
    
    if not all([alpaca_key, alpaca_secret]):
        logger.error("Missing API keys!")
        return
    
    extractor = OutcomeExtractor(alpaca_key, alpaca_secret)
    df = extractor.process_all_events()
    
    # Final summary
    print("\n" + "="*80)
    print("OUTCOME COLUMNS ADDED:")
    print("="*80)
    outcome_cols = [c for c in df.columns if 'recovery' in c or 'reversed' in c or 'eod' in c or 'max_' in c]
    for col in outcome_cols:
        non_null = df[col].notna().sum()
        print(f"  {col}: {non_null:,} values ({100*non_null/len(df):.1f}%)")


if __name__ == '__main__':
    main()
