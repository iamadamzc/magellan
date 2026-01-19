"""
Fetch all available commodities and forex from FMP and test V19 on them
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v19_futures import run_orb_v19_futures
from dotenv import load_dotenv
load_dotenv()

import requests
import os

FMP_KEY = os.getenv('FMP_API_KEY')

print("\n" + "="*80)
print("FETCHING ALL COMMODITIES & FOREX FROM FMP")
print("="*80)

# Get commodities list
print("\nFetching commodities...")
commodities_url = f"https://financialmodelingprep.com/stable/commodities-list?apikey={FMP_KEY}"
try:
    resp = requests.get(commodities_url)
    commodities = resp.json()
    commodity_symbols = [c['symbol'] for c in commodities if 'symbol' in c]
    print(f"✅ Found {len(commodity_symbols)} commodities")
    print(f"   Examples: {', '.join(commodity_symbols[:10])}")
except Exception as e:
    print(f"❌ Error fetching commodities: {e}")
    commodity_symbols = []

# Get forex list
print("\nFetching forex pairs...")
forex_url = f"https://financialmodelingprep.com/stable/forex-list?apikey={FMP_KEY}"
try:
    resp = requests.get(forex_url)
    forex_pairs = resp.json()
    forex_symbols = [f['symbol'] for f in forex_pairs if 'symbol' in f]
    print(f"✅ Found {len(forex_symbols)} forex pairs")
    print(f"   Examples: {', '.join(forex_symbols[:10])}")
except Exception as e:
    print(f"❌ Error fetching forex: {e}")
    forex_symbols = []

# Combine all
all_symbols = commodity_symbols + forex_symbols

print(f"\n{'='*80}")
print(f"TESTING V19 ON {len(all_symbols)} SYMBOLS")
print(f"{'='*80}")

results = []

for i, symbol in enumerate(all_symbols[:50]):  # Limit to first 50 to avoid rate limits
    if (i + 1) % 10 == 0:
        print(f"\n[{i+1}/{min(50, len(all_symbols))}]")
    
    try:
        result = run_orb_v19_futures(symbol, '2024-01-01', '2024-12-31', rth_open_hour=9, rth_open_min=0)
        
        if result and result['total_trades'] > 0:
            results.append(result)
            status = "🎉" if result['total_pnl'] > 0 else "  "
            print(f"{status} {symbol:12s} {result['total_pnl']:+7.2f}% ({result['total_trades']:3d} trades, {result['win_rate']:4.1f}%)")
    
    except Exception as e:
        # Silent fail, just skip
        pass

# Summary
if results:
    import pandas as pd
    df = pd.DataFrame(results)
    df_sorted = df.sort_values('total_pnl', ascending=False)
    
    print(f"\n{'='*80}")
    print(f"TOP PERFORMERS")
    print(f"{'='*80}")
    
    winners = df[df['total_pnl'] > 0]
    
    if len(winners) > 0:
        print(f"\n🎉 FOUND {len(winners)} PROFITABLE SYMBOLS:")
        for _, row in winners.iterrows():
            print(f"   ✅ {row['symbol']:12s} {row['total_pnl']:+7.2f}% ({row['total_trades']:3d} trades, {row['win_rate']:4.1f}%)")
        
        # Save winners
        winners_path = project_root / 'research' / 'new_strategy_builds' / 'results' / 'ORB_V19_WINNERS.csv'
        winners.to_csv(winners_path, index=False)
        print(f"\n📁 Saved to: {winners_path}")
    else:
        print(f"\n❌ No profitable symbols found in first 50")
else:
    print(f"\n❌ No valid trades across all tested symbols")

print(f"\n{'='*80}\n")
