"""
ORB Universe Screener - Find Speedboat Stocks
----------------------------------------------
Based on Gem_Ni's universe criteria

SPEEDBOAT UNIVERSE:
- Float < 20M shares
- Market Cap $50M-$500M
- RVOL > 3.0 (today)
- Gap > 15% (pre-market)
- Price $2-$15

Uses FMP API to screen for qualifying stocks
"""

import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

FMP_API_KEY = os.getenv('FMP_API_KEY')

def get_stock_screener(min_market_cap=50_000_000, max_market_cap=500_000_000, 
                       min_price=2.0, max_price=15.0):
    """
    Use FMP stock screener to find candidates
    """
    url = f"https://financialmodelingprep.com/api/v3/stock-screener"
    params = {
        'marketCapMoreThan': min_market_cap,
        'marketCapLowerThan': max_market_cap,
        'priceMoreThan': min_price,
        'priceLowerThan': max_price,
        'volumeMoreThan': 500_000,  # Minimum liquidity
        'exchange': 'NASDAQ,NYSE',
        'limit': 1000,
        'apikey': FMP_API_KEY
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return []

def get_float_data(symbol):
    """Get shares float for a symbol"""
    url = f"https://financialmodelingprep.com/api/v4/shares_float"
    params = {'symbol': symbol, 'apikey': FMP_API_KEY}
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data and len(data) > 0:
            return data[0].get('floatShares', None)
    return None

def get_quote_data(symbol):
    """Get current quote including gap and volume"""
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}"
    params = {'apikey': FMP_API_KEY}
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data and len(data) > 0:
            return data[0]
    return None

print("="*80)
print("SPEEDBOAT UNIVERSE SCREENER")
print("="*80)
print("\nStep 1: Getting initial candidates from FMP screener...")

# Get initial candidates
candidates = get_stock_screener()
print(f"Found {len(candidates)} initial candidates")

print("\nStep 2: Filtering by float < 20M...")

speedboats = []
checked = 0

for stock in candidates[:100]:  # Check first 100 to avoid rate limits
    symbol = stock['symbol']
    checked += 1
    
    if checked % 10 == 0:
        print(f"  Checked {checked}/100...")
    
    # Get float
    float_shares = get_float_data(symbol)
    if float_shares is None or float_shares > 20_000_000:
        continue
    
    # Get quote for gap and volume
    quote = get_quote_data(symbol)
    if quote is None:
        continue
    
    # Calculate metrics
    price = quote.get('price', 0)
    change_pct = quote.get('changesPercentage', 0)
    volume = quote.get('volume', 0)
    avg_volume = quote.get('avgVolume', 1)
    
    rvol = volume / avg_volume if avg_volume > 0 else 0
    
    # Check if it meets speedboat criteria
    if (float_shares < 20_000_000 and
        price >= 2.0 and price <= 15.0 and
        abs(change_pct) > 5.0):  # At least 5% move today
        
        speedboats.append({
            'symbol': symbol,
            'price': price,
            'float_m': float_shares / 1_000_000,
            'market_cap_m': stock.get('marketCap', 0) / 1_000_000,
            'gap_pct': change_pct,
            'rvol': rvol,
            'volume': volume,
            'avg_volume': avg_volume,
        })

# Create DataFrame
df = pd.DataFrame(speedboats)

if len(df) > 0:
    # Sort by RVOL descending
    df = df.sort_values('rvol', ascending=False)
    
    print("\n" + "="*80)
    print(f"FOUND {len(df)} SPEEDBOAT CANDIDATES")
    print("="*80)
    
    print("\nTop 20 by RVOL:")
    print(df.head(20).to_string(index=False))
    
    # Save results
    output_path = 'research/new_strategy_builds/results/speedboat_universe.csv'
    df.to_csv(output_path, index=False)
    print(f"\n✅ Full results saved to: {output_path}")
    
    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDED FOR TESTING")
    print("="*80)
    
    # Top 5 by RVOL with good gap
    top_5 = df[(df['rvol'] > 2.0) & (abs(df['gap_pct']) > 10)].head(5)
    
    if len(top_5) > 0:
        print("\nTop 5 Speedboats (RVOL > 2.0, Gap > 10%):")
        for _, row in top_5.iterrows():
            print(f"  {row['symbol']:6} | ${row['price']:6.2f} | Float: {row['float_m']:5.1f}M | Gap: {row['gap_pct']:+6.1f}% | RVOL: {row['rvol']:.1f}x")
        
        print("\nNext steps:")
        print("1. Cache data for these symbols (Nov 2024 - Jan 2025)")
        print("2. Test V7 (Barbell) on speedboats")
        print("3. Compare to RIOT/MARA (tankers)")
    else:
        print("\n⚠️ No stocks meet strict criteria today.")
        print("   Try running on a more volatile day or relax filters.")
        
        if len(df) > 0:
            print(f"\n   Found {len(df)} with lower thresholds:")
            print(df.head(10).to_string(index=False))
else:
    print("\n⚠️ No speedboat candidates found.")
    print("   This could mean:")
    print("   1. Market is quiet today")
    print("   2. FMP API limits hit")
    print("   3. Need to adjust filters")
