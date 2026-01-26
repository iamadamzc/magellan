"""
DAILY REGIME CHECKER

Run this at the start of each session to determine trading regime.

Outputs:
- 90-day regime: SAFE - Full deployment recommended
- 60-day regime: MODERATE - Deploy with monitoring
- 30-day regime: CAUTION - Watch closely, consider reduced size
- NO MATCH: DO NOT TRADE

Author: Magellan Testing Framework
Date: January 25, 2026
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings("ignore")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


def calculate_atr(df: pd.DataFrame, period: int = 20) -> pd.Series:
    tr1 = df["high"] - df["low"]
    tr2 = (df["high"] - df["close"].shift(1)).abs()
    tr3 = (df["low"] - df["close"].shift(1)).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.rolling(period).mean()


def calculate_regime_features(df: pd.DataFrame) -> dict:
    """Calculate current regime characteristics."""

    # Daily aggregation for last 60 trading days
    daily = (
        df.resample("1D")
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )
        .dropna()
        .tail(60)
    )

    if len(daily) < 50:
        return None

    # Calculate features for most recent day
    latest = daily.iloc[-1]

    # 1. Volatility (ATR / Price)
    atr_20 = calculate_atr(daily, period=20).iloc[-1]
    volatility = atr_20 / latest["close"]

    # 2. Trend Strength (20-day slope)
    closes = daily["close"].tail(20).values
    trend = np.polyfit(range(len(closes)), closes, 1)[0]

    # 3. ATR Expansion (current ATR / 50-day ATR)
    atr_50 = calculate_atr(daily, period=50).iloc[-1]
    atr_expansion = atr_20 / atr_50

    # 4. Volume trend (20-day avg / 50-day avg)
    vol_20 = daily["volume"].tail(20).mean()
    vol_50 = daily["volume"].tail(50).mean()
    volume_trend = vol_20 / vol_50

    # 5. Price range (high-low / close)
    price_range = (latest["high"] - latest["low"]) / latest["close"]

    return {
        "volatility": volatility,
        "trend": trend,
        "atr_expansion": atr_expansion,
        "volume_trend": volume_trend,
        "price_range": price_range,
    }


def match_regime(
    current_features: dict, signature: dict, tolerance: float = 0.3
) -> bool:
    """Check if current features match regime signature."""

    matches = 0
    total = 0

    for feature, bounds in signature.items():
        if feature not in current_features:
            continue

        current_val = current_features[feature]
        min_val = bounds["min"]
        max_val = bounds["max"]

        # Expand bounds by tolerance
        range_size = max_val - min_val
        min_expanded = min_val - (range_size * tolerance)
        max_expanded = max_val + (range_size * tolerance)

        total += 1
        if min_expanded <= current_val <= max_expanded:
            matches += 1

    # Require 80% of features to match
    return (matches / total) >= 0.8 if total > 0 else False


def check_regime(symbol: str = "IVV"):
    """Check current regime and output trading recommendation."""

    # Load regime signatures
    sig_file = project_root / "test" / "vol_expansion" / "regime_signatures.json"
    if not sig_file.exists():
        print("❌ Regime signatures not found. Run regime_detection.py first.")
        return None

    with open(sig_file) as f:
        data = json.load(f)

    signatures = data["signatures"]

    # Load recent data
    data_path = project_root / "data" / "cache" / "equities"
    files = list(data_path.glob(f"{symbol}_1min_*.parquet"))
    if not files:
        print(f"❌ No data for {symbol}")
        return None

    file = max(files, key=lambda x: x.stat().st_size)
    df = pd.read_parquet(file)

    # Get last 60 days
    df_recent = df[df.index >= (datetime.now() - timedelta(days=90))]

    # Calculate current regime features
    current = calculate_regime_features(df_recent)

    if not current:
        print("❌ Insufficient data to calculate regime")
        return None

    # Check matches (prioritize 90 > 60 > 30)
    matched_regime = None

    for window in ["90day", "60day", "30day"]:
        if window in signatures:
            if match_regime(current, signatures[window]):
                matched_regime = window
                break

    # Output results
    print("=" * 70)
    print(f"DAILY REGIME CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    print(f"\nSymbol: {symbol}")
    print(f"\nCurrent Market Conditions:")
    print(f"  Volatility: {current['volatility']:.4f}")
    print(f"  Trend: {current['trend']:.4f}")
    print(f"  ATR Expansion: {current['atr_expansion']:.2f}")
    print(f"  Volume Trend: {current['volume_trend']:.2f}")
    print(f"  Price Range: {current['price_range']:.4f}")

    print(f"\n{'-'*70}")

    if matched_regime == "90day":
        print("\n✅ REGIME: 90-DAY FAVORABLE WINDOW")
        print("   STATUS: SAFE")
        print("   RECOMMENDATION: Full deployment with normal risk")
        print("   CONFIDENCE: HIGH")
        status = "SAFE"
    elif matched_regime == "60day":
        print("\n⚠️  REGIME: 60-DAY FAVORABLE WINDOW")
        print("   STATUS: MODERATE")
        print("   RECOMMENDATION: Deploy with monitoring")
        print("   CONFIDENCE: MODERATE")
        status = "MODERATE"
    elif matched_regime == "30day":
        print("\n⚠️⚠️ REGIME: 30-DAY FAVORABLE WINDOW")
        print("   STATUS: CAUTION")
        print("   RECOMMENDATION: Reduced position size, watch closely")
        print("   CONFIDENCE: MARGINAL")
        status = "CAUTION"
    else:
        print("\n❌ REGIME: NO MATCH")
        print("   STATUS: UNFAVORABLE")
        print("   RECOMMENDATION: DO NOT TRADE")
        print("   CONFIDENCE: N/A")
        status = "NO_TRADE"

    print(f"\n{'='*70}")

    return {
        "date": datetime.now().isoformat(),
        "symbol": symbol,
        "regime": matched_regime if matched_regime else "NO_TRADE",
        "status": status,
        "features": current,
    }


if __name__ == "__main__":
    result = check_regime("IVV")

    # Save to log
    if result:
        log_file = project_root / "test" / "vol_expansion" / "regime_log.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(result) + "\n")

    sys.exit(0)
