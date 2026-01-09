"""
Magellan Data Pipeline - Entry Point
Fetches historical market data using Alpaca Paper API with Market Plus (SIP) subscription.
"""

import os
import requests.exceptions
import pandas as pd
from datetime import datetime, timedelta
from src.data_handler import AlpacaDataClient, FMPDataClient
from src.features import FeatureEngineer
from src.discovery import calculate_ic


def load_env_file() -> None:
    """Manually load .env file into os.environ."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def main() -> None:
    """Main entry point for the Magellan data pipeline."""
    
    # Load environment variables into os.environ
    load_env_file()
    
    # Print System Readiness Report
    print("=" * 60)
    print("MAGELLAN SYSTEM READINESS REPORT")
    print("=" * 60)
    
    apca_key_id = os.getenv('APCA_API_KEY_ID')
    apca_base_url = os.getenv('APCA_API_BASE_URL')
    
    print(f"APCA_API_KEY_ID: {'Found' if apca_key_id else 'Not Found'}")
    if apca_key_id:
        print(f"  → Key Prefix: {apca_key_id[:3]}...")
    print(f"Target Endpoint: {apca_base_url if apca_base_url else 'Not Set'}")
    print(f"Data Feed: SIP (Full Market)")
    print("=" * 60)
    print()
    
    # Initialize clients
    try:
        alpaca_client = AlpacaDataClient()
        fmp_client = FMPDataClient()
        feature_engineer = FeatureEngineer()
    except ValueError as e:
        print(f"[ERROR] Initialization failed: {e}")
        return
    
    # Configuration
    symbol = 'SPY'
    start_date = '2026-01-07'
    end_date = '2026-01-08'
    
    print(f"[PIPELINE] Starting multi-source data fusion for {symbol}")
    print("=" * 60)
    
    try:
        # Step 1: Fetch SPY bars from Alpaca
        print(f"\n[STEP 1] Fetching {symbol} 1-minute bars from Alpaca (SIP feed)...")
        bars = alpaca_client.fetch_historical_bars(
            symbol=symbol,
            timeframe='1Min',
            start=start_date,
            end=end_date,
            feed='sip'
        )
        print(f"[SUCCESS] Fetched {len(bars)} bars")
        
        # Step 2: Fetch FMP fundamental metrics
        print(f"\n[STEP 2] Fetching {symbol} fundamental metrics from FMP...")
        fmp_metrics = fmp_client.fetch_fundamental_metrics(symbol)
        print(f"[SUCCESS] Market Cap: ${fmp_metrics['mktCap']:,.0f}, PE: {fmp_metrics['pe']:.2f}")
        
        # Step 3: Fetch FMP news sentiment
        print(f"\n[STEP 3] Fetching {symbol} news sentiment from FMP...")
        print(f"[FMP CHECK] Attempting to reach Stable endpoint for {symbol}...")
        fmp_sentiment = fmp_client.fetch_news_sentiment(symbol)
        print(f"[SUCCESS] Sentiment Score: {fmp_sentiment['sentiment']:.4f}")
        
        # Step 4: Run feature engineering
        print(f"\n[STEP 4] Running feature engineering...")
        feature_matrix = feature_engineer.merge_all(bars, fmp_metrics, fmp_sentiment)
        
        # Drop first row to remove NaN from log_return
        feature_matrix = feature_matrix.iloc[1:]
        
        print(f"[SUCCESS] Feature matrix created with {len(feature_matrix)} rows")
        
        # Step 5: Output feature matrix
        print("\n" + "=" * 60)
        print("[FEATURE_MATRIX] Last 5 rows:")
        print("=" * 60)
        
        # Select and display key columns
        output_cols = ['close', 'log_return', 'rvol', 'parkinson_vol', 'sentiment', 'mktCap']
        print(feature_matrix[output_cols].tail())
        
        # Step 6: Alpha Discovery - IC Analysis
        print("\n" + "=" * 60)
        print("[SIGNAL STRENGTH REPORT] Information Coefficient Analysis")
        print("=" * 60)
        print(f"Feature: sentiment → Target: log_return")
        print("-" * 60)
        
        horizons = [5, 15, 60]  # 5-min, 15-min, 60-min
        
        for horizon in horizons:
            ic = calculate_ic(feature_matrix, 'sentiment', 'log_return', horizon=horizon)
            if pd.isna(ic):
                ic_str = "N/A (insufficient data)"
            else:
                # Interpret IC strength
                abs_ic = abs(ic)
                if abs_ic < 0.02:
                    strength = "Noise"
                elif abs_ic < 0.05:
                    strength = "Weak"
                elif abs_ic < 0.10:
                    strength = "Moderate"
                else:
                    strength = "Strong"
                ic_str = f"{ic:+.4f} ({strength})"
            
            print(f"  {horizon:>3}-min horizon IC: {ic_str}")
        
        print("-" * 60)
        print("[NOTE] IC > 0.02 suggests exploitable alpha; IC > 0.05 is promising.")
        
        print("\n" + "=" * 60)
        print(f"[COMPLETE] Pipeline finished successfully")
        print("=" * 60)
        
    except requests.exceptions.HTTPError as e:
        print(f"\n[ERROR] HTTP request failed:")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response Text: {e.response.text}")
        else:
            print(str(e))
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {type(e).__name__}: {e}")


if __name__ == '__main__':
    main()
