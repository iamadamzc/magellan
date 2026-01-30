"""
Download 4 years of 1-minute Nasdaq-100 futures data from FMP
Saves to data/cache/futures/ directory with yearly partitions

Note: FMP provides NQUSD (E-mini Nasdaq-100), not MNQUSD (Micro E-mini)
      The regular E-mini has 5x the contract size of Micro, but the price action is identical
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
import requests

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

def download_mnq_1min_data():
    """Download 4 years of 1-minute NQ futures data from FMP"""
    
    # Get FMP API key
    api_key = os.getenv('FMP_API_KEY')
    
    if not api_key:
        print("❌ Error: FMP API key not found in .env file")
        print("   Looking for: FMP_API_KEY")
        return
    
    print(f"✅ Found FMP credentials (Key: {api_key[:4]}...)")
    
    # Define symbol and output directory
    # FMP provides NQUSD (E-mini Nasdaq-100), not MNQUSD (Micro)
    # Price action is identical, just 5x contract multiplier difference
    symbol = "NQUSD"
    output_dir = Path("data/cache/futures")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Calculate date range: 4 years back from today
    end_date = datetime.now()
    start_date = end_date - timedelta(days=4*365)  # 4 years
    
    print(f"\n📊 Downloading {symbol} (E-mini Nasdaq-100) 1-minute data from FMP")
    print(f"   Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"   Output: {output_dir}")
    
    # FMP /stable/ 1-minute data endpoint (matching working pattern)
    base_url = "https://financialmodelingprep.com/stable/historical-chart/1min"
    
    # Download data year by year to avoid API limits
    all_data = []
    
    for year in range(start_date.year, end_date.year + 1):
        # Define chunk dates
        chunk_start = f"{year}-01-01"
        chunk_end = f"{year}-12-31"
        
        # Adjust for current year (don't go past today)
        if year == end_date.year:
            chunk_end = end_date.strftime('%Y-%m-%d')
            
        print(f"\n   Fetching {year}: {chunk_start} to {chunk_end}...")
        
        try:
            # FMP /stable/ endpoint: symbol is passed as query parameter, not in path
            params = {
                "symbol": symbol,
                "from": chunk_start,
                "to": chunk_end,
                "apikey": api_key
            }
            
            # Fetch data
            response = requests.get(base_url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            if not data or len(data) == 0:
                print(f"   ⚠️ No data returned for {year}")
                continue
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # FMP returns 'date' column in format: "YYYY-MM-DD HH:MM:SS"
            df['timestamp'] = pd.to_datetime(df['date'])
            df = df.set_index('timestamp')
            
            # Sort ascending (FMP sometimes returns reverse chronological)
            df = df.sort_index(ascending=True)
            
            # Ensure timezone-naive
            if df.index.tz is not None:
                df.index = df.index.tz_convert('UTC').tz_localize(None)
            
            # Normalize column names to lowercase
            df.columns = df.columns.str.lower()
            
            # Select only OHLCV columns
            ohlcv_cols = ['open', 'high', 'low', 'close', 'volume']
            df = df[[col for col in ohlcv_cols if col in df.columns]]
            
            print(f"   ✅ Retrieved {len(df):,} bars for {year}")
            
            # Save immediately as yearly partition
            filename = f"{symbol}_1Min_{year}0101_{year}1231.parquet"
            filepath = output_dir / filename
            df.to_parquet(filepath)
            print(f"   💾 Saved: {filename}")
            
            all_data.append(df)
                
        except requests.exceptions.HTTPError as e:
            print(f"   ❌ HTTP Error for {year}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"      Response: {e.response.text[:200]}")
            continue
        except Exception as e:
            print(f"   ❌ Error fetching {year}: {e}")
            continue
    
    if not all_data:
        print("\n❌ No data retrieved!")
        return
    
    # Combine for summary statistics
    print(f"\n📦 Summary:")
    full_df = pd.concat(all_data)
    full_df.sort_index(inplace=True)
    full_df = full_df[~full_df.index.duplicated(keep='first')]
    
    print(f"   Total bars: {len(full_df):,}")
    print(f"   Date range: {full_df.index.min()} to {full_df.index.max()}")
    print(f"   Years covered: {list(range(start_date.year, end_date.year + 1))}")
    
    print(f"\n✅ Download complete!")
    print(f"   Files saved to: {output_dir.absolute()}")

if __name__ == "__main__":
    download_mnq_1min_data()
