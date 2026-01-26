#!/usr/bin/env python3
"""
Quick credential check for Intraday Alpha backtest
Tests if .env file is properly configured
"""

from pathlib import Path
from dotenv import load_dotenv
import os

print("=" * 80)
print("CREDENTIAL CHECK")
print("=" * 80)

# Try loading from different locations
env_paths = [
    Path(__file__).parent / '.env',
    Path(__file__).parent.parent / '.env',
    Path(__file__).parent.parent.parent / '.env',
]

print("\nSearching for .env file...")
for env_path in env_paths:
    print(f"  Checking: {env_path}")
    if env_path.exists():
        print(f"  ✅ Found .env at: {env_path}")
        load_dotenv(env_path)
        break
    else:
        print(f"  ❌ Not found")
else:
    print("\n⚠️ No .env file found in expected locations")
    print("\nExpected location: a:\\1\\Magellan\\test\\.env")
    print("\nPlease create .env file with:")
    print("  APCA_API_KEY_ID=your_key")
    print("  APCA_API_SECRET_KEY=your_secret")
    print("  APCA_API_BASE_URL=https://paper-api.alpaca.markets")
    exit(1)

# Check if credentials are set
print("\n" + "=" * 80)
print("CREDENTIAL STATUS")
print("=" * 80)

credentials = {
    'APCA_API_KEY_ID': os.getenv('APCA_API_KEY_ID'),
    'APCA_API_SECRET_KEY': os.getenv('APCA_API_SECRET_KEY'),
    'APCA_API_BASE_URL': os.getenv('APCA_API_BASE_URL'),
    'FMP_API_KEY': os.getenv('FMP_API_KEY'),  # Optional
}

all_set = True
for key, value in credentials.items():
    if value:
        masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
        print(f"  ✅ {key}: {masked}")
    else:
        if key == 'FMP_API_KEY':
            print(f"  ⚠️ {key}: Not set (optional - sentiment data)")
        else:
            print(f"  ❌ {key}: NOT SET (required)")
            all_set = False

print("\n" + "=" * 80)
if all_set or (credentials['APCA_API_KEY_ID'] and credentials['APCA_API_SECRET_KEY'] and credentials['APCA_API_BASE_URL']):
    print("✅ ALL REQUIRED CREDENTIALS SET")
    print("\nYou can now run:")
    print("  python run_phase1_baseline_backtest.py")
else:
    print("❌ MISSING REQUIRED CREDENTIALS")
    print("\nPlease update your .env file with the missing values")
print("=" * 80)
