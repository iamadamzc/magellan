import requests
import pandas as pd
import io

def debug_yahoo():
    print("Scanning Yahoo Finance for Gainers...")
    yahoo_url = "https://finance.yahoo.com/markets/stocks/gainers/?start=0&count=100"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(yahoo_url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML tables
        tables = pd.read_html(io.StringIO(response.text))
        if not tables:
            print("No tables found.")
            return
            
        df = tables[0]
        print("Columns found:", df.columns.tolist())
        print("First 5 rows:")
        print(df.head())
        
        # Check specific column content
        if 'Price' in df.columns:
            print("\nPrice column sample:")
            print(df['Price'].head())
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_yahoo()
