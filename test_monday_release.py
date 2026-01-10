"""
Test script for Monday Release Protocol
Demonstrates the kinetic gap execution logic.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_handler import AlpacaDataClient
from src.monday_release import monday_release_logic


def load_env_file():
    """Manually load .env file into os.environ."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def main():
    """Test Monday Release Protocol."""
    print("=" * 70)
    print("MONDAY RELEASE PROTOCOL - TEST")
    print("=" * 70)
    
    # Load environment
    load_env_file()
    
    # Initialize Alpaca client
    try:
        alpaca_client = AlpacaDataClient()
    except Exception as e:
        print(f"[ERROR] Failed to initialize Alpaca client: {e}")
        return
    
    # Test tickers
    tickers = ['SPY', 'QQQ', 'IWM']
    
    for ticker in tickers:
        print(f"\n{'='*70}")
        print(f"Testing {ticker}")
        print('='*70)
        
        # Run Monday Release Logic
        result = monday_release_logic(
            alpaca_client=alpaca_client,
            symbol=ticker
        )
        
        # Display results
        print(f"\n[RESULT] Status: {result['status']}")
        print(f"[RESULT] Recommendation: {result['recommendation']}")
        
        if result['status'] not in ['ERROR', 'NOT_MONDAY', 'NO_DATA']:
            print(f"[RESULT] Gap: {result['gap_pct']:+.2f}%")
            print(f"[RESULT] Volume Z-Score: {result['impulse_volume_zscore']:.2f}")
            print(f"[RESULT] Volume Ratio: {result['volume_ratio']:.2f}x")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    main()
