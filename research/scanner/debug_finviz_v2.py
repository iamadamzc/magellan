import requests
import pandas as pd
import io

def debug_finviz_v2():
    print("Scanning Finviz for Gainers...")
    finviz_url = "https://finviz.com/screener.ashx?v=111&s=ta_topgainers&f=sh_price_u20"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(finviz_url, headers=headers)
        print(f"Status: {response.status_code}")
        
        tables = pd.read_html(io.StringIO(response.text))
        print(f"Tables found: {len(tables)}")
        
        for i, df in enumerate(tables):
            print(f"\n--- Table {i} ---")
            print(f"Shape: {df.shape}")
            print(f"Columns: {df.columns.tolist()}")
            print(df.head(10))
            
            # Check for the target columns
            if {'Ticker', 'Change', 'Volume', 'Price'}.issubset(df.columns):
                print(">>> POTENTIAL MATCH <<<")
            
            # Check for the garbage row content
            mask = df.apply(lambda x: x.astype(str).str.contains('Reset Filters').any(), axis=1)
            if mask.any():
                print(">>> CONTAINS GARBAGE ROW <<<")
                print(df[mask])

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_finviz_v2()
