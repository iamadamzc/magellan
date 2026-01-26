"""
Extract features for FULL historical dataset (9,278 events)

This will take ~45-60 minutes but will give us a production-ready ML dataset
"""

import os
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# Import the extractor
from research.bear_trap_ml_scanner.data_collection.extract_features import FeatureExtractor
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    alpaca_key = os.getenv('APCA_API_KEY_ID')
    alpaca_secret = os.getenv('APCA_API_SECRET_KEY')
    fmp_key = os.getenv('FMP_API_KEY')
    
    if not all([alpaca_key, alpaca_secret, fmp_key]):
        logger.error("Missing API keys!")
        return
    
    data_dir = Path(__file__).parent.parent / "data"
    input_file = data_dir / "raw" / "selloffs_full_2022_2024.csv"
    output_file = data_dir / "processed" / "selloffs_full_2022_2024_features.csv"
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*80)
    print("BEAR TRAP ML SCANNER - FULL FEATURE EXTRACTION")
    print("Processing 9,278 selloff events (2022-2024)")
    print("Expected time: ~45-60 minutes")
    print("="*80 + "\n")
    
    extractor = FeatureExtractor(alpaca_key, alpaca_secret, fmp_key)
    
    # Process with outcome calculation disabled for speed
    # We'll calculate outcomes in a separate pass if needed
    extractor.process_dataset(input_file, output_file, calculate_outcomes=False)
    
    # Quick summary
    import pandas as pd
    df = pd.read_csv(output_file)
    
    print("\n" + "="*80)
    print("📊 FINAL ENRICHED DATASET")
    print("="*80)
    print(f"Total events: {len(df):,}")
    print(f"Features: {len(df.columns)}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    
    print(f"\nFeature completeness:")
    for col in ['pct_from_52w_high', 'distance_from_200sma', 'spy_change_day']:
        valid_pct = (1 - df[col].isna().mean()) * 100
        print(f"  {col:30} {valid_pct:5.1f}% complete")
    
    print("\n" + "="*80)
    print("✅ PRODUCTION DATASET READY!")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
