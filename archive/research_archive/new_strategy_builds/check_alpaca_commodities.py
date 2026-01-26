"""
Check which commodity futures Alpaca has available
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

print("="*80)
print("CHECKING ALPACA COMMODITY AVAILABILITY")
print("="*80)

# Common commodity symbols
test_symbols = [
    # Indices
    'ES', 'NQ', 'YM', 'RTY',
    # Energies
    'CL', 'NG', 'RB', 'HO',
    # Metals
    'GC', 'SI', 'HG', 'PL',
    # Ags
    'ZC', 'ZS', 'ZW', 'ZL', 'KC', 'SB', 'CT', 'CC', 'OJ',
    # Meats
    'HE', 'LE', 'GF',
]

client = AlpacaDataClient()

available = []
missing = []

for symbol in test_symbols:
    try:
        # Try to fetch 1 day of data
        df = client.fetch_historical_bars(
            symbol=symbol,
            timeframe=TimeFrame.Minute,
            start='2024-12-30',
            end='2024-12-31',
            feed='sip'
        )
        
        if df is not None and len(df) > 0:
            available.append(symbol)
            print(f"✅ {symbol:6s} - {len(df):4d} bars")
        else:
            missing.append(symbol)
            print(f"❌ {symbol:6s} - No data")
    except Exception as e:
        missing.append(symbol)
        print(f"❌ {symbol:6s} - Error: {str(e)[:50]}")

print(f"\n{'='*80}")
print("SUMMARY")
print(f"{'='*80}")
print(f"Available: {len(available)} symbols")
print(f"   {', '.join(available)}")
print(f"\nMissing: {len(missing)} symbols")
print(f"   {', '.join(missing)}")
