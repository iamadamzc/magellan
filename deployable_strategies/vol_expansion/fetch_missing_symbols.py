"""
Fetch missing symbol data for multi-symbol validation

Missing symbols: IVV, GLD, SLV, TQQQ, SOXL

Author: Magellan Testing Framework
Date: January 25, 2026
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"Loaded environment variables from {env_file}")

from src.data_handler import AlpacaDataClient


def fetch_missing_symbols():
    """Fetch 1-minute data for missing symbols."""

    # Symbols we need
    missing_symbols = ["IVV", "GLD", "SLV", "TQQQ", "SOXL"]

    # We need data from 2022-2026 for training and testing
    start_date = "2022-01-01"
    end_date = "2026-01-24"

    print("=" * 70)
    print("FETCHING MISSING SYMBOL DATA FROM ALPACA")
    print("=" * 70)
    print(f"\nSymbols: {', '.join(missing_symbols)}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Timeframe: 1-minute bars")

    # Initialize Alpaca client
    client = AlpacaDataClient()

    # Output directory
    output_dir = project_root / "data" / "cache" / "equities"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for symbol in missing_symbols:
        print(f"\n{'-'*70}")
        print(f"Fetching {symbol}...")
        print(f"{'-'*70}")

        try:
            # Fetch data
            df = client.fetch_historical_bars(
                symbol=symbol,
                timeframe="1Min",
                start=start_date,
                end=end_date,
                feed="sip",  # Use SIP feed for better data quality
            )

            if df is None or len(df) == 0:
                print(f"  ❌ No data returned for {symbol}")
                results[symbol] = {"status": "failed", "reason": "no data"}
                continue

            print(f"  ✅ Fetched {len(df):,} bars")
            print(f"  Date range: {df.index.min()} to {df.index.max()}")

            # Save to parquet
            output_file = output_dir / f"{symbol}_1min_20220101_20260124.parquet"
            df.to_parquet(output_file)

            print(f"  💾 Saved to: {output_file.name}")

            results[symbol] = {
                "status": "success",
                "bars": len(df),
                "start": str(df.index.min()),
                "end": str(df.index.max()),
                "file": str(output_file),
            }

        except Exception as e:
            print(f"  ❌ Error fetching {symbol}: {e}")
            results[symbol] = {"status": "error", "reason": str(e)}

    # Summary
    print("\n" + "=" * 70)
    print("FETCH SUMMARY")
    print("=" * 70)

    successful = [s for s, r in results.items() if r["status"] == "success"]
    failed = [s for s, r in results.items() if r["status"] != "success"]

    print(f"\n✅ Successful: {len(successful)}/{len(missing_symbols)}")
    for symbol in successful:
        print(f"  {symbol}: {results[symbol]['bars']:,} bars")

    if failed:
        print(f"\n❌ Failed: {len(failed)}/{len(missing_symbols)}")
        for symbol in failed:
            print(f"  {symbol}: {results[symbol].get('reason', 'unknown error')}")

    return results


if __name__ == "__main__":
    results = fetch_missing_symbols()
    sys.exit(0)
