"""
REGIME DETECTION SYSTEM

Identifies favorable trading regimes by:
1. Finding best 90/60/30-day rolling windows historically
2. Extracting regime characteristics (VIX, ATR, trend, volatility)
3. Matching current market to these favorable regimes
4. Outputting confidence level (90-day = safest, 30-day = caution)

Author: Magellan Testing Framework
Date: January 25, 2026
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
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


def build_features(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    features = pd.DataFrame(index=df.index)
    features["velocity_1"] = df["close"].pct_change(1)
    features["velocity_4"] = df["close"].pct_change(4)

    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - df["close"].shift(1)).abs(),
            (df["low"] - df["close"].shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr_5 = tr.rolling(5).mean()
    atr_20 = tr.rolling(20).mean()
    features["volatility_ratio"] = (atr_5 / (atr_20 + 0.0001)).clip(0, 5)

    vol_mean = df["volume"].rolling(20).mean()
    vol_std = df["volume"].rolling(20).std()
    features["volume_z"] = ((df["volume"] - vol_mean) / (vol_std + 1)).clip(-5, 5)

    pct_change_abs = df["close"].pct_change().abs()
    features["effort_result"] = (features["volume_z"] / (pct_change_abs + 0.0001)).clip(
        -100, 100
    )

    full_range = df["high"] - df["low"]
    body = (df["close"] - df["open"]).abs()
    features["range_ratio"] = (full_range / (body + 0.0001)).clip(0, 20)

    for col in [
        "velocity_1",
        "volatility_ratio",
        "effort_result",
        "range_ratio",
        "volume_z",
    ]:
        features[f"{col}_mean"] = features[col].rolling(lookback).mean()
        features[f"{col}_std"] = features[col].rolling(lookback).std()

    return features


def calculate_regime_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate regime characteristics for each day."""

    # Daily aggregation
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
    )

    regime = pd.DataFrame(index=daily.index)

    # 1. Volatility (ATR / Price)
    atr_daily = calculate_atr(daily, period=20)
    regime["volatility"] = atr_daily / daily["close"]

    # 2. Trend Strength (20-day slope)
    regime["trend"] = (
        daily["close"]
        .rolling(20)
        .apply(lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 20 else 0)
    )

    # 3. ATR Expansion (current ATR / 50-day ATR)
    atr_50 = calculate_atr(daily, period=50)
    regime["atr_expansion"] = atr_daily / (atr_50 + 0.0001)

    # 4. Volume trend
    regime["volume_trend"] = (
        daily["volume"].rolling(20).mean() / daily["volume"].rolling(50).mean()
    )

    # 5. Price range (high-low / close)
    regime["price_range"] = (daily["high"] - daily["low"]) / daily["close"]

    return regime.dropna()


def find_best_windows(
    df_intraday: pd.DataFrame, symbol: str, window_days: int, top_pct: float = 0.2
):
    """Find best performing windows of specified length."""

    # Get daily data
    daily = df_intraday.resample("1D").agg({"close": "last"}).dropna()

    # Calculate rolling returns
    rolling_returns = daily["close"].pct_change(window_days).shift(-window_days)

    # Find top percentile
    threshold = rolling_returns.quantile(1 - top_pct)
    best_windows = rolling_returns[rolling_returns >= threshold]

    print(
        f"  {window_days}-day windows: Found {len(best_windows)} in top {top_pct*100}%"
    )
    print(f"    Return threshold: {threshold:.1%}")
    print(f"    Best window return: {best_windows.max():.1%}")

    return best_windows.index.tolist()


def extract_regime_signatures(df_intraday: pd.DataFrame, best_dates: list) -> dict:
    """Extract regime characteristics for best periods."""

    regime_features = calculate_regime_features(df_intraday)

    # Get features for best dates
    signatures = []
    for date in best_dates:
        if date in regime_features.index:
            signatures.append(regime_features.loc[date].to_dict())

    if not signatures:
        return None

    # Calculate signature statistics
    df_sigs = pd.DataFrame(signatures)

    signature = {
        "volatility": {
            "min": float(df_sigs["volatility"].quantile(0.1)),
            "max": float(df_sigs["volatility"].quantile(0.9)),
            "mean": float(df_sigs["volatility"].mean()),
        },
        "trend": {
            "min": float(df_sigs["trend"].quantile(0.1)),
            "max": float(df_sigs["trend"].quantile(0.9)),
            "mean": float(df_sigs["trend"].mean()),
        },
        "atr_expansion": {
            "min": float(df_sigs["atr_expansion"].quantile(0.1)),
            "max": float(df_sigs["atr_expansion"].quantile(0.9)),
            "mean": float(df_sigs["atr_expansion"].mean()),
        },
        "volume_trend": {
            "min": float(df_sigs["volume_trend"].quantile(0.1)),
            "max": float(df_sigs["volume_trend"].quantile(0.9)),
            "mean": float(df_sigs["volume_trend"].mean()),
        },
        "price_range": {
            "min": float(df_sigs["price_range"].quantile(0.1)),
            "max": float(df_sigs["price_range"].quantile(0.9)),
            "mean": float(df_sigs["price_range"].mean()),
        },
    }

    return signature


def match_current_regime(
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


def main():
    print("=" * 70)
    print("REGIME DETECTION SYSTEM")
    print("=" * 70)

    symbol = "IVV"  # Test on IVV (best performer)

    # Load data
    data_path = project_root / "data" / "cache" / "equities"
    files = list(data_path.glob(f"{symbol}_1min_*.parquet"))
    if not files:
        print(f"No data for {symbol}")
        return

    file = max(files, key=lambda x: x.stat().st_size)
    df_1m = pd.read_parquet(file)

    df_15m = (
        df_1m.resample("15min")
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
    )
    df_15m = df_15m.between_time("09:30", "15:45")

    # Use 2022-2024 to build regime signatures
    df_train = df_15m[df_15m.index < "2025-01-01"]

    print(
        f"\nBuilding regime signatures from {df_train.index[0].date()} to {df_train.index[-1].date()}"
    )

    # Find best windows
    regime_signatures = {}

    for window_days in [90, 60, 30]:
        print(f"\n{'-'*70}")
        print(f"Analyzing {window_days}-day windows...")

        best_dates = find_best_windows(df_train, symbol, window_days, top_pct=0.2)
        signature = extract_regime_signatures(df_train, best_dates)

        if signature:
            regime_signatures[f"{window_days}day"] = signature
            print(f"  Signature created:")
            print(f"    Volatility: {signature['volatility']['mean']:.4f}")
            print(f"    Trend: {signature['trend']['mean']:.4f}")
            print(f"    ATR Expansion: {signature['atr_expansion']['mean']:.2f}")

    # Test regime detection on 2025
    print(f"\n{'='*70}")
    print("TESTING REGIME DETECTION ON 2025")
    print(f"{'='*70}")

    df_test = df_15m[df_15m.index >= "2025-01-01"]
    regime_features = calculate_regime_features(df_test)

    regime_matches = []

    for date in regime_features.index:
        current = regime_features.loc[date].to_dict()

        matched_window = None
        for window, signature in regime_signatures.items():
            if match_current_regime(current, signature):
                matched_window = window
                break  # Match most conservative (90 > 60 > 30)

        regime_matches.append(
            {"date": date, "regime": matched_window if matched_window else "NO_TRADE"}
        )

    df_regime = pd.DataFrame(regime_matches)

    # Summary
    regime_counts = df_regime["regime"].value_counts()
    print(f"\n2025 Regime Distribution:")
    for regime, count in regime_counts.items():
        pct = count / len(df_regime) * 100
        print(f"  {regime}: {count} days ({pct:.1f}%)")

    # Save signatures
    output = {
        "symbol": symbol,
        "signatures": regime_signatures,
        "2025_regime_distribution": regime_counts.to_dict(),
    }

    output_file = project_root / "test" / "vol_expansion" / "regime_signatures.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n*** Regime signatures saved to {output_file} ***")

    return regime_signatures


if __name__ == "__main__":
    signatures = main()
    sys.exit(0)
