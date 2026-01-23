import requests
import pandas as pd
import io
import os
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()
FMP_API_KEY = os.getenv("FMP_API_KEY")

def debug_finviz_and_fmp():
    # 1. Test FMP Single Ticker (Final Check)
    print("--- 1. FMP CHECK (AAPL) ---")
    url = f"https://financialmodelingprep.com/api/v3/quote/AAPL?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url)
        print(f"FMP Status: {r.status_code}")
        print(f"FMP Response: {r.text[:100]}")
    except Exception as e:
        print(f"FMP Error: {e}")

    # 2. Test Finviz Scraping
    print("\n--- 2. FINVIZ CHECK ---")
    # Top Gainers, Price < $20
    finviz_url = "https://finviz.com/screener.ashx?v=111&s=ta_topgainers&f=sh_price_u20"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        r = requests.get(finviz_url, headers=headers)
        print(f"Finviz Status: {r.status_code}")
        
        if r.status_code == 200:
            tables = pd.read_html(io.StringIO(r.text))
            # Finviz usually has the main table at index 1 or so
            print(f"Tables found: {len(tables)}")
            for i, df in enumerate(tables):
                print(f"Table {i} Columns: {df.columns.tolist()[:5]}")
                if 'Ticker' in df.columns or 'No.' in df.columns:
                    print(df.head())
                    # Check for AMBR
                    if 'Ticker' in df.columns:
                        print("Checking for AMBR:", not df[df['Ticker'] == 'AMBR'].empty)
    except Exception as e:
        print(f"Finviz Error: {e}")

    # 3. Test yfinance Float
    print("\n--- 3. YFINANCE FLOAT CHECK (AMBR) ---")
    try:
        ticker = yf.Ticker("AMBR")
        info = ticker.info
        print(f"Float Shares: {info.get('floatShares')}")
        print(f"Shares Outstanding: {info.get('sharesOutstanding')}")
    except Exception as e:
        print(f"yfinance Error: {e}")

if __name__ == "__main__":
    debug_finviz_and_fmp()
