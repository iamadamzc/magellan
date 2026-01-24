import requests
import pandas as pd
import io
import os
from dotenv import load_dotenv

load_dotenv()
FMP_API_KEY = os.getenv("FMP_API_KEY")
BASE_URL = "https://financialmodelingprep.com/api/v3"

def debug_hybrid():
    print("--- 1. YAHOO DISCOVERY ---")
    yahoo_url = "https://finance.yahoo.com/markets/stocks/gainers/?start=0&count=100"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(yahoo_url, headers=headers)
        print(f"Yahoo Status: {response.status_code}")
        
        tables = pd.read_html(io.StringIO(response.text))
        df = tables[0]
        print(f"Yahoo Raw Columns: {df.columns.tolist()}")
        
        # Rename
        rename_map = {
            'Symbol': 'Ticker',
            'Ticker': 'Ticker',
            'Price': 'RawPrice',
            'Price (Intraday)': 'RawPrice',
            'Volume': 'Volume'
        }
        df.rename(columns=rename_map, inplace=True)
        
        # Parse Price
        if 'RawPrice' in df.columns:
            def parse_yahoo_data(row):
                try:
                    text = str(row)
                    parts = text.split()
                    if len(parts) >= 3:
                        price = float(parts[0].replace(',', ''))
                        gap_str = parts[-1].replace('(', '').replace(')', '').replace('%', '').replace('+', '').replace(',', '')
                        gap = float(gap_str)
                        return price, gap
                    return float(text.replace(',', '')), 0.0
                except:
                    return 0.0, 0.0

            parsed = df['RawPrice'].apply(parse_yahoo_data)
            df['Price'] = parsed.apply(lambda x: x[0])
            df['Gap%'] = parsed.apply(lambda x: x[1])
            
        print("\n--- TOP 10 YAHOO CANDIDATES ---")
        print(df[['Ticker', 'Price', 'Gap%', 'Volume']].head(10))
        
        # Check for specific missing tickers
        missing = ['AMBR', 'MNDR', 'INHD']
        print(f"\nChecking for {missing}:")
        for m in missing:
            found = df[df['Ticker'] == m]
            if not found.empty:
                print(f"FOUND {m}: {found[['Ticker', 'Price', 'Gap%']].to_dict('records')}")
            else:
                print(f"MISSING {m}")

    except Exception as e:
        print(f"Yahoo Error: {e}")
        return

    print("\n--- 2. FMP ENRICHMENT ---")
    tickers_list = df['Ticker'].head(5).tolist() # Test with top 5
    print(f"Testing FMP with: {tickers_list}")
    
    tickers_str = ",".join(tickers_list)
    quote_url = f"{BASE_URL}/quote/{tickers_str}?apikey={FMP_API_KEY}"
    
    try:
        resp = requests.get(quote_url)
        print(f"FMP Status: {resp.status_code}")
        data = resp.json()
        print(f"FMP Response Count: {len(data)}")
        if data:
            print("Sample FMP Item:", data[0])
            for item in data:
                print(f"{item.get('symbol')}: Shares={item.get('sharesOutstanding')}")
    except Exception as e:
        print(f"FMP Error: {e}")

if __name__ == "__main__":
    debug_hybrid()
