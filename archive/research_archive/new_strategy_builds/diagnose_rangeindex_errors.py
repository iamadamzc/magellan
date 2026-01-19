"""
Diagnose which symbols have RangeIndex error vs no trades
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_cache import cache

# All symbols that had issues
test_symbols = [
    'BBBY', 'PROG', 'TELL', 'BKKT', 'RIDE', 
    'BBIG', 'CLOV', 'WISH', 'LCID', 'HYLN',
    'MATX', 'SBLK', 'GOGL', 'NMCI', 'HEXO',
    'SKLZ', 'DKNG'
]

print("="*80)
print("DIAGNOSING DATA FETCH ERRORS")
print("="*80)

errors = []
success = []

for symbol in test_symbols:
    try:
        df = cache.get_or_fetch_equity(symbol, '1min', '2024-01-01', '2024-01-05')
        if df is not None and len(df) > 0:
            success.append(symbol)
            print(f"✅ {symbol}: {len(df)} bars")
        else:
            print(f"⚠️  {symbol}: No data returned")
    except Exception as e:
        error_msg = str(e)
        if 'RangeIndex' in error_msg:
            errors.append(symbol)
            print(f"❌ {symbol}: RangeIndex error")
        else:
            print(f"❌ {symbol}: {error_msg[:60]}")

print(f"\n{'='*80}")
print("SUMMARY")
print(f"{'='*80}")
print(f"RangeIndex errors: {len(errors)}")
if errors:
    print(f"  Symbols: {', '.join(errors)}")
print(f"\nSuccessful: {len(success)}")
if success:
    print(f"  Symbols: {', '.join(success)}")
