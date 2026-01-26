"""
PHASE 4: SNIPER STRATEGY OPTIMIZATION

Derive symbol-specific Sniper thresholds and test performance.
Sniper uses effort_result, range_ratio, and volatility_ratio thresholds.

Author: Magellan Testing Framework
Date: January 25, 2026
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json
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


def derive_sniper_thresholds(df_train: pd.DataFrame, percentile: float = 10) -> dict:
    """Derive Sniper thresholds from winning trades in training data."""

    features = build_features(df_train, lookback=20)
    atr = calculate_atr(df_train)

    # Find winning bars (same definition as Workhorse)
    target_atr = 2.0
    max_dd_atr = 1.0
    max_bars = 8

    is_winning = []
    for idx in range(len(df_train) - max_bars):
        entry = df_train["close"].iloc[idx]
        current_atr = atr.iloc[idx]

        if pd.isna(current_atr) or current_atr <= 0:
            is_winning.append(False)
            continue

        target = entry + target_atr * current_atr
        max_allowed_dd = max_dd_atr * current_atr

        winner = False
        max_dd = 0

        for j in range(idx + 1, min(idx + max_bars + 1, len(df_train))):
            dd = entry - df_train["low"].iloc[j]
            max_dd = max(max_dd, dd)
            if df_train["high"].iloc[j] >= target and max_dd <= max_allowed_dd:
                winner = True
                break
        is_winning.append(winner)

    is_winning.extend([False] * max_bars)
    features["is_winning"] = is_winning

    # Get feature distributions for winners
    winners = features[features["is_winning"]].dropna()

    # Derive thresholds at specified percentile
    thresholds = {
        "effort_result_mean": float(
            np.percentile(winners["effort_result_mean"].dropna(), percentile)
        ),
        "range_ratio_mean": float(
            np.percentile(winners["range_ratio_mean"].dropna(), 100 - percentile)
        ),
        "volatility_ratio_mean": float(
            np.percentile(winners["volatility_ratio_mean"].dropna(), 100 - percentile)
        ),
    }

    return thresholds


def backtest_sniper(
    df_test: pd.DataFrame,
    thresholds: dict,
    use_trend: bool,
    target_mult: float = 2.0,
    stop_mult: float = 1.0,
    max_hold_bars: int = 8,
) -> dict:
    """Backtest Sniper strategy with given thresholds."""

    features = build_features(df_test, lookback=20)
    atr = calculate_atr(df_test)
    sma_50 = df_test["close"].rolling(50).mean()
    in_uptrend = df_test["close"] > sma_50

    # Sniper signal: extreme values on all three features
    signal_mask = (
        (features["effort_result_mean"] < thresholds["effort_result_mean"])
        & (features["range_ratio_mean"] > thresholds["range_ratio_mean"])
        & (features["volatility_ratio_mean"] > thresholds["volatility_ratio_mean"])
    )

    if use_trend:
        signal_mask = signal_mask & in_uptrend

    account = 25000.0
    trades = []
    position = None

    risk_pct = 0.02  # Sniper uses 2% risk
    slippage = 0.02

    for idx in range(len(df_test)):
        current_atr = atr.iloc[idx]
        if pd.isna(current_atr):
            continue

        if position is None:
            if signal_mask.iloc[idx]:
                risk_dollars = account * risk_pct
                stop_distance = stop_mult * current_atr
                shares = int(risk_dollars / stop_distance)

                if shares > 0:
                    raw_entry = df_test["close"].iloc[idx]
                    position = {
                        "entry_idx": idx,
                        "raw_entry": raw_entry,
                        "entry_price": raw_entry + slippage / 2,
                        "shares": shares,
                        "target": raw_entry + target_mult * current_atr,
                        "stop": raw_entry - stop_mult * current_atr,
                    }
        else:
            high = df_test["high"].iloc[idx]
            low = df_test["low"].iloc[idx]
            close = df_test["close"].iloc[idx]

            exit_signal = False
            raw_exit = None

            if low <= position["stop"]:
                exit_signal = True
                raw_exit = position["stop"]
            elif high >= position["target"]:
                exit_signal = True
                raw_exit = position["target"]
            elif idx - position["entry_idx"] >= max_hold_bars:
                exit_signal = True
                raw_exit = close

            if exit_signal:
                exit_price = raw_exit - slippage / 2
                pnl_net = (exit_price - position["entry_price"]) * position["shares"]
                risk = (position["raw_entry"] - position["stop"]) * position["shares"]
                pnl_r = pnl_net / risk if risk > 0 else 0

                account += pnl_net
                trades.append({"pnl": pnl_net, "pnl_r": pnl_r, "is_win": pnl_net > 0})
                position = None

    if not trades:
        return {"trades": 0, "win_rate": 0, "expectancy": 0, "return_pct": 0}

    df_trades = pd.DataFrame(trades)
    return {
        "trades": len(df_trades),
        "win_rate": df_trades["is_win"].mean(),
        "expectancy": df_trades["pnl_r"].mean(),
        "return_pct": (account / 25000 - 1) * 100,
    }


def main():
    print("=" * 70)
    print("PHASE 4: SNIPER STRATEGY OPTIMIZATION")
    print("=" * 70)

    symbols = ["SPY", "QQQ", "IWM", "IVV", "VOO", "GLD", "SLV", "TQQQ", "SOXL"]
    percentiles = [5, 10, 15]  # Test different selectivity levels

    all_results = {}

    for symbol in symbols:
        print(f"\n{'='*70}")
        print(f"OPTIMIZING SNIPER FOR: {symbol}")
        print(f"{'='*70}")

        # Load data
        data_path = project_root / "data" / "cache" / "equities"
        files = list(data_path.glob(f"{symbol}_1min_*.parquet"))

        if not files:
            print(f"  ⚠️ No data for {symbol}")
            continue

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

        df_train = df_15m[df_15m.index < "2025-01-01"]
        df_test = df_15m[(df_15m.index >= "2025-01-01") & (df_15m.index < "2026-01-01")]

        if len(df_test) < 100:
            continue

        print(f"  Testing Sniper configurations...")
        symbol_results = []

        for pct in percentiles:
            print(f"  Percentile {pct}%:")
            thresholds = derive_sniper_thresholds(df_train, pct)

            for use_trend in [False, True]:
                result = backtest_sniper(df_test, thresholds, use_trend)
                result["percentile"] = pct
                result["trend_filter"] = use_trend
                result["thresholds"] = thresholds
                symbol_results.append(result)
                trend_str = "w/Trend" if use_trend else "No Trend"
                print(
                    f"    {trend_str}: {result['trades']} trades, {result['return_pct']:.1f}%"
                )

        if symbol_results:
            best = max(symbol_results, key=lambda x: x["return_pct"])
            all_results[symbol] = {"best_sniper": best, "all_configs": symbol_results}
            print(
                f"\n  BEST: Pct={best['percentile']}, Trend={best['trend_filter']} → {best['return_pct']:.1f}%"
            )

    # Summary
    print("\n" + "=" * 70)
    print("SNIPER OPTIMIZATION SUMMARY")
    print("=" * 70)

    print(
        f"\n{'Symbol':<8} {'Pct':<6} {'Trend?':<8} {'Trades':<8} {'Win%':<8} {'Expect':<10} {'Return':<10}"
    )
    print("-" * 70)

    for symbol, data in sorted(
        all_results.items(),
        key=lambda x: x[1]["best_sniper"]["return_pct"],
        reverse=True,
    ):
        best = data["best_sniper"]
        trend_str = "Yes" if best["trend_filter"] else "No"
        print(
            f"{symbol:<8} {best['percentile']:<6} {trend_str:<8} {best['trades']:<8} {best['win_rate']:<7.1%} {best['expectancy']:<9.3f}R {best['return_pct']:>8.1f}%"
        )

    # Save
    # Convert numpy types to Python types for JSON serialization
    def convert_types(obj):
        if isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(v) for v in obj]
        elif isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return obj

    output_file = project_root / "test" / "vol_expansion" / "phase4_sniper_results.json"
    with open(output_file, "w") as f:
        json.dump(convert_types(all_results), f, indent=2)

    print(f"\n*** Results saved to {output_file} ***")

    return all_results


if __name__ == "__main__":
    results = main()
    sys.exit(0)
