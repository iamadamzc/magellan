"""
Fetch ES Futures Data from FMP
Downloads S&P 500 1-minute data using SPY as proxy for MES/ES futures
Per FUTURES_QUICK_START_FMP.md: "SPY - S&P 500 (proxy for MES)"
"""

import sys
from pathlib import Path
import pandas as pd
import requests
from datetime import datetime

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import os
# Load .env from project root
load_dotenv(project_root / ".env")

FMP_API_KEY = os.getenv("FMP_API_KEY")


def fetch_fmp_1min_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch 1-minute data from FMP Ultimate.
    
    Args:
        symbol: Stock/ETF symbol (e.g., 'SPY')
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        DataFrame with OHLCV data
    """
    # FMP Ultimate uses /stable/ base URL (not /api/v3/)
    # Per FMP_ULTIMATE_COMPLETE.md: "Legacy endpoints deprecated: Must use /stable/ base URL"
    # Format: ?symbol= as query param (per intraday_analysis.py)
    base_url = "https://financialmodelingprep.com/stable"
    url = f"{base_url}/historical-chart/1min"
    
    params = {
        "symbol": symbol,
        "from": start_date,
        "to": end_date,
        "apikey": FMP_API_KEY
    }
    
    print(f"Fetching {symbol} 1-min data from FMP: {start_date} to {end_date}")
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if not data or len(data) == 0:
            print(f"ERROR: No data returned for {symbol}")
            return pd.DataFrame()
        
        print(f"Received {len(data)} bars")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["date"])
        df = df.set_index("timestamp")
        df = df.sort_index(ascending=True)
        
        # Normalize columns
        df.columns = df.columns.str.lower()
        
        # Select OHLCV
        ohlcv_cols = ["open", "high", "low", "close", "volume"]
        df = df[[col for col in ohlcv_cols if col in df.columns]]
        
        # Validate prices
        print(f"Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
        
        return df
        
    except Exception as e:
        print(f"ERROR: {e}")
        return pd.DataFrame()


def fetch_es_proxy_data(start_date: str, end_date: str, save_path: str = None):
    """
    Fetch ES futures proxy data (SPY) from FMP.
    
    Per FMP documentation, SPY is used as proxy for MES (Micro E-mini S&P 500).
    """
    print("\n" + "="*60)
    print("FETCHING S&P 500 DATA FOR ES/MES STRATEGY")
    print("Using SPY as proxy (per FUTURES_QUICK_START_FMP.md)")
    print("="*60)
    
    if not FMP_API_KEY:
        print("ERROR: FMP_API_KEY not found in environment!")
        return None
    
    # Fetch SPY as ES proxy
    df = fetch_fmp_1min_data("SPY", start_date, end_date)
    
    if len(df) == 0:
        print("\nNo data retrieved. Check FMP API key and symbol.")
        return None
    
    print(f"\n✓ Successfully fetched {len(df)} 1-min bars")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    
    if save_path:
        df.to_parquet(save_path)
        print(f"✓ Saved to: {save_path}")
    
    return df


if __name__ == "__main__":
    # Fetch 2024 SPY data as ES proxy
    save_path = project_root / "data" / "cache" / "equities" / "SPY_1min_FMP_2024.parquet"
    
    df = fetch_es_proxy_data(
        start_date="2024-01-01",
        end_date="2024-12-31", 
        save_path=str(save_path)
    )
    
    if df is not None:
        print(f"\nSample data:")
        print(df.head())
