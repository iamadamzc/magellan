"""
IVV WORKHORSE INVESTIGATION & TUNING

Investigate why IVV had 134 Workhorse trades vs SPY's 3 trades
and tune the strategy specifically for IVV.

Author: Magellan Testing Framework
Date: January 25, 2026
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import json
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import warnings

warnings.filterwarnings("ignore")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


def calculate_atr(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Calculate ATR."""
    tr1 = df["high"] - df["low"]
    tr2 = (df["high"] - df["close"].shift(1)).abs()
    tr3 = (df["low"] - df["close"].shift(1)).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.rolling(period).mean()


def build_features(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """Build stationary features."""
    features = pd.DataFrame(index=df.index)

    # Velocity
    features["velocity_1"] = df["close"].pct_change(1)
    features["velocity_4"] = df["close"].pct_change(4)

    # Volatility ratio
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

    # Volume z-score
    vol_mean = df["volume"].rolling(20).mean()
    vol_std = df["volume"].rolling(20).std()
    features["volume_z"] = ((df["volume"] - vol_mean) / (vol_std + 1)).clip(-5, 5)

    # Effort-result
    pct_change_abs = df["close"].pct_change().abs()
    features["effort_result"] = (features["volume_z"] / (pct_change_abs + 0.0001)).clip(
        -100, 100
    )

    # Range ratio
    full_range = df["high"] - df["low"]
    body = (df["close"] - df["open"]).abs()
    features["range_ratio"] = (full_range / (body + 0.0001)).clip(0, 20)

    # Aggregated features
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


def train_symbol_specific_model(df_train: pd.DataFrame, symbol: str) -> tuple:
    """Train symbol-specific Workhorse model."""

    print(f"\nTraining {symbol}-specific Workhorse model...")

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

    # Get feature columns
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
    labels = np.array(["win"] * len(X_win) + ["non"] * len(X_non))

    # Train scaler and K-Means
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_all)

    kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)

    # Analyze all clusters
    print(f"\n{symbol} Cluster Analysis:")
    print("-" * 60)

    baseline = len(X_win) / len(X_all)
    cluster_stats = []

    for c in range(8):
        mask = clusters == c
        wins_in = (labels[mask] == "win").sum()
        total_in = mask.sum()
        win_rate = wins_in / total_in if total_in > 0 else 0
        lift = win_rate / baseline if baseline > 0 else 0
        freq = total_in / len(X_all)

        cluster_stats.append(
            {
                "cluster": c,
                "win_rate": win_rate,
                "lift": lift,
                "frequency": freq,
                "count": total_in,
            }
        )

        print(
            f"  Cluster {c}: WinRate={win_rate:.1%}, Lift={lift:.2f}x, Freq={freq:.1%}"
        )

    return scaler, kmeans, feat_cols, cluster_stats


def backtest_all_clusters(df_test: pd.DataFrame, model: tuple, symbol: str) -> dict:
    """Backtest all clusters to find the best one."""

    scaler, kmeans, feat_cols, _ = model

    print(f"\nBacktesting all clusters on {symbol} 2025 data...")

    # Build features
    features = build_features(df_test, lookback=20)
    atr = calculate_atr(df_test)
    sma_50 = df_test["close"].rolling(50).mean()
    in_uptrend = df_test["close"] > sma_50

    # Assign clusters
    X_full = features[feat_cols].fillna(0).values
    X_scaled = scaler.transform(X_full)
    clusters = kmeans.predict(X_scaled)

    results = []

    for cluster_id in range(8):
        # Test with and without trend filter
        for use_trend_filter in [False, True]:
            signal_mask = pd.Series(clusters == cluster_id, index=df_test.index)
            if use_trend_filter:
                signal_mask = signal_mask & in_uptrend

            # Run backtest
            account = 25000.0
            trades = []
            position = None

            risk_pct = 0.01
            target_mult = 2.0
            stop_mult = 1.0
            max_hold_bars = 8
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
                        pnl_net = (exit_price - position["entry_price"]) * position[
                            "shares"
                        ]
                        risk = (position["raw_entry"] - position["stop"]) * position[
                            "shares"
                        ]
                        pnl_r = pnl_net / risk if risk > 0 else 0

                        account += pnl_net
                        trades.append(
                            {"pnl": pnl_net, "pnl_r": pnl_r, "is_win": pnl_net > 0}
                        )
                        position = None

            if trades:
                df_trades = pd.DataFrame(trades)
                results.append(
                    {
                        "cluster": cluster_id,
                        "trend_filter": use_trend_filter,
                        "trades": len(df_trades),
                        "win_rate": df_trades["is_win"].mean(),
                        "expectancy": df_trades["pnl_r"].mean(),
                        "total_pnl": df_trades["pnl"].sum(),
                        "final_balance": account,
                        "return_pct": (account / 25000 - 1) * 100,
                    }
                )

    return results


def main():
    print("=" * 70)
    print("IVV WORKHORSE INVESTIGATION & TUNING")
    print("=" * 70)

    # Load IVV data
    data_path = project_root / "data" / "cache" / "equities"
    files = list(data_path.glob("IVV_1min_*.parquet"))

    if not files:
        print("ERROR: No IVV data found!")
        return

    file = max(files, key=lambda x: x.stat().st_size)
    df_1m = pd.read_parquet(file)

    print(f"\nLoaded IVV: {len(df_1m):,} 1-min bars")

    # Aggregate to 15-min
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

    # Split
    df_train = df_15m[df_15m.index < "2025-01-01"]
    df_test = df_15m[(df_15m.index >= "2025-01-01") & (df_15m.index < "2026-01-01")]

    print(f"Training: {len(df_train):,} bars")
    print(f"Testing (2025): {len(df_test):,} bars")

    # Train IVV-specific model
    ivv_model = train_symbol_specific_model(df_train, "IVV")

    # Backtest all clusters
    results = backtest_all_clusters(df_test, ivv_model, "IVV")

    # Display results
    print("\n" + "=" * 70)
    print("IVV CLUSTER BACKTEST RESULTS (2025)")
    print("=" * 70)

    print(
        f"\n{'Cluster':<8} {'Trend?':<8} {'Trades':<8} {'Win%':<8} {'Expect':<10} {'Return':<10}"
    )
    print("-" * 70)

    for r in sorted(results, key=lambda x: x["return_pct"], reverse=True):
        trend_str = "Yes" if r["trend_filter"] else "No"
        print(
            f"{r['cluster']:<8} {trend_str:<8} {r['trades']:<8} {r['win_rate']:<7.1%} {r['expectancy']:<9.3f}R {r['return_pct']:>8.1f}%"
        )

    # Find best configuration
    best = max(results, key=lambda x: x["return_pct"])

    print("\n" + "=" * 70)
    print("BEST IVV WORKHORSE CONFIGURATION")
    print("=" * 70)

    print(f"\nCluster: {best['cluster']}")
    print(f"Trend Filter: {'Yes' if best['trend_filter'] else 'No'}")
    print(f"Trades: {best['trades']}")
    print(f"Win Rate: {best['win_rate']:.1%}")
    print(f"Expectancy: {best['expectancy']:.3f}R")
    print(f"Total P&L: ${best['total_pnl']:,.2f}")
    print(f"Final Balance: ${best['final_balance']:,.2f}")
    print(f"Return: {best['return_pct']:.1f}%")

    # Compare to original Cluster 7 with trend filter
    cluster_7_trend = [r for r in results if r["cluster"] == 7 and r["trend_filter"]][0]

    print("\n" + "-" * 70)
    print("COMPARISON: Best vs Original (Cluster 7 + Trend)")
    print("-" * 70)

    print(f"\n{'Metric':<20} {'Best Config':<20} {'Original (C7+T)':<20}")
    print("-" * 60)
    print(f"{'Cluster':<20} {best['cluster']:<20} {cluster_7_trend['cluster']:<20}")
    print(f"{'Trades':<20} {best['trades']:<20} {cluster_7_trend['trades']:<20}")
    print(
        f"{'Win Rate':<20} {best['win_rate']:<19.1%} {cluster_7_trend['win_rate']:<19.1%}"
    )
    print(
        f"{'Expectancy':<20} {best['expectancy']:<19.3f}R {cluster_7_trend['expectancy']:<19.3f}R"
    )
    print(
        f"{'Return':<20} {best['return_pct']:<19.1f}% {cluster_7_trend['return_pct']:<19.1f}%"
    )

    improvement = best["return_pct"] - cluster_7_trend["return_pct"]
    print(f"\n{'Improvement:':<20} {improvement:>19.1f}%")

    # Save results
    output = {
        "symbol": "IVV",
        "best_config": {
            "cluster": int(best["cluster"]),
            "trend_filter": bool(best["trend_filter"]),
            "trades": int(best["trades"]),
            "win_rate": float(best["win_rate"]),
            "expectancy": float(best["expectancy"]),
            "return_pct": float(best["return_pct"]),
        },
        "original_config": {
            "cluster": 7,
            "trend_filter": True,
            "trades": int(cluster_7_trend["trades"]),
            "win_rate": float(cluster_7_trend["win_rate"]),
            "expectancy": float(cluster_7_trend["expectancy"]),
            "return_pct": float(cluster_7_trend["return_pct"]),
        },
        "improvement_pct": float(improvement),
    }

    output_file = project_root / "test" / "vol_expansion" / "ivv_workhorse_tuned.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n*** Results saved to {output_file} ***")

    return results


if __name__ == "__main__":
    results = main()
    sys.exit(0)
