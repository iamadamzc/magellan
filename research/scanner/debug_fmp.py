import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("FMP_API_KEY")
base_url = "https://financialmodelingprep.com/api/v3"

def test_endpoint(name, url):
    print(f"Testing {name}...")
    try:
        resp = requests.get(url)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("Success!")
            data = resp.json()
            print(f"Sample: {str(data)[:100]}")
        else:
            print(f"Error: {resp.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")
    print("-" * 20)

if __name__ == "__main__":
    print(f"Using Key: {api_key}")
    
    # 1. Test Basic Quote (Usually Free)
    test_endpoint("Basic Quote (AAPL)", f"{base_url}/quote/AAPL?apikey={api_key}")
    
    # 2. Test Gainers (The one failing)
    test_endpoint("Gainers", f"{base_url}/stock_market/gainers?apikey={api_key}")
    
    # 3. Test Pre-Market Gainers
    test_endpoint("Pre-Market Gainers", f"{base_url}/stock_market/pre-market-gainers?apikey={api_key}")
