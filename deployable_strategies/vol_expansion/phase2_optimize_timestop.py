"""
PHASE 2: TIME STOP OPTIMIZATION

Test different time stop durations for each symbol using their
optimized cluster, trend, and R:R settings from Phase 1.

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


# Load Phase 1 results
with open(project_root / "test" / "vol_expansion" / "phase1_rr_results.json") as f:
    PHASE1_RESULTS = json.load(f)

# Time stop configurations to test (in bars @ 15-min = hours)
TIME_STOPS = [
    {"bars": 4, "name": "4 bars (1 hr)"},
    {"bars": 6, "name": "6 bars (1.5 hr)"},
    {"bars": 8, "name": "8 bars (2 hr baseline)"},
    {"bars": 12, "name": "12 bars (3 hr)"},
    {"bars": 16, "name": "16 bars (4 hr)"},
]


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


def train_model(df_train: pd.DataFrame) -> tuple:
    features = build_features(df_train, lookback=20)
    atr = calculate_atr(df_train)

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

    feat_cols = [c for c in features.columns if "_mean" in c or "_std" in c]
    feat_cols = [c for c in feat_cols if not features[c].isna().all()]

    wins_df = features[features["is_winning"]].dropna(subset=feat_cols)
    non_wins_df = features[~features["is_winning"]].dropna(subset=feat_cols)

    n_sample = min(5000, len(wins_df), len(non_wins_df))
    np.random.seed(42)
    wins = wins_df.sample(n=n_sample)
    non_wins = non_wins_df.sample(n=n_sample)

    X_win = wins[feat_cols].values
    X_non = non_wins[feat_cols].values
    X_all = np.vstack([X_win, X_non])

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_all)

    kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
    kmeans.fit(X_scaled)

    return scaler, kmeans, feat_cols


def backtest_timestop(
    df_test: pd.DataFrame,
    model: tuple,
    cluster_id: int,
    use_trend: bool,
    target_mult: float,
    stop_mult: float,
    max_hold_bars: int,
) -> dict:
    scaler, kmeans, feat_cols = model

    features = build_features(df_test, lookback=20)
    atr = calculate_atr(df_test)
    sma_50 = df_test["close"].rolling(50).mean()
    in_uptrend = df_test["close"] > sma_50

    X_full = features[feat_cols].fillna(0).values
    X_scaled = scaler.transform(X_full)
    clusters = kmeans.predict(X_scaled)

    signal_mask = pd.Series(clusters == cluster_id, index=df_test.index)
    if use_trend:
        signal_mask = signal_mask & in_uptrend

    account = 25000.0
    trades = []
    position = None

    risk_pct = 0.01
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
    print("PHASE 2: TIME STOP OPTIMIZATION")
    print("=" * 70)

    all_results = {}

    for symbol, p1_data in PHASE1_RESULTS.items():
        print(f"\n{'='*70}")
        print(f"OPTIMIZING TIME STOP FOR: {symbol}")
        print(f"{'='*70}")

        best_rr = p1_data["best_rr"]
        cluster = p1_data["cluster"]
        trend_filter = p1_data["trend_filter"]

        # Load data
        data_path = project_root / "data" / "cache" / "equities"
        files = list(data_path.glob(f"{symbol}_1min_*.parquet"))

        if not files:
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

        print(f"  Using R:R: {best_rr['target']}:{best_rr['stop']}")
        print(f"  Training model...")
        model = train_model(df_train)

        print(f"  Testing time stops...")
        symbol_results = []

        for ts in TIME_STOPS:
            result = backtest_timestop(
                df_test,
                model,
                cluster,
                trend_filter,
                best_rr["target"],
                best_rr["stop"],
                ts["bars"],
            )
            result["config"] = ts["name"]
            result["bars"] = ts["bars"]
            symbol_results.append(result)
            print(
                f"    {ts['name']}: {result['trades']} trades, {result['return_pct']:.1f}%"
            )

        best = max(symbol_results, key=lambda x: x["return_pct"])
        all_results[symbol] = {
            "best_timestop": best,
            "all_timestops": symbol_results,
            "target": best_rr["target"],
            "stop": best_rr["stop"],
            "cluster": cluster,
            "trend_filter": trend_filter,
        }

        print(f"\n  BEST: {best['config']} → {best['return_pct']:.1f}%")

    # Summary
    print("\n" + "=" * 70)
    print("TIME STOP OPTIMIZATION SUMMARY")
    print("=" * 70)

    print(
        f"\n{'Symbol':<8} {'Best TimeStop':<20} {'Trades':<8} {'Win%':<8} {'Expect':<10} {'Return':<10}"
    )
    print("-" * 70)

    for symbol, data in sorted(
        all_results.items(),
        key=lambda x: x[1]["best_timestop"]["return_pct"],
        reverse=True,
    ):
        best = data["best_timestop"]
        print(
            f"{symbol:<8} {best['config']:<20} {best['trades']:<8} {best['win_rate']:<7.1%} {best['expectancy']:<9.3f}R {best['return_pct']:>8.1f}%"
        )

    # Save
    output_file = (
        project_root / "test" / "vol_expansion" / "phase2_timestop_results.json"
    )
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n*** Results saved to {output_file} ***")

    return all_results


if __name__ == "__main__":
    results = main()
    sys.exit(0)
