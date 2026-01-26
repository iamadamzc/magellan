"""
DUAL-TRACK FREQUENCY OPTIMIZATION

Track A: 5-Minute "Goldilocks" Discovery
- Aggregate to 5-min bars
- Find hidden state that survives slippage
- Target: 1-3 trades/day

Track B: 15-Minute "Secondary Cluster" Audit
- Re-examine ALL clusters (not just best)
- Find workhorse with >5% signal frequency
- Target: Complement to sniper strategy

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


# =============================================================================
# COMMON UTILITIES
# =============================================================================


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

    # Body position
    features["body_position"] = (
        (df["close"] - df["low"]) / (full_range + 0.0001)
    ).clip(0, 1)

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


def run_backtest(
    df: pd.DataFrame,
    signal_mask: pd.Series,
    target_atr: float,
    stop_atr: float,
    max_bars: int,
    slippage: float,
) -> dict:
    """Run backtest on signals."""

    position = None
    trades = []

    atr = calculate_atr(df)

    for idx in range(len(df)):
        if pd.isna(atr.iloc[idx]):
            continue

        if position is None:
            if signal_mask.iloc[idx]:
                raw_entry = df["close"].iloc[idx]
                position = {
                    "entry_idx": idx,
                    "raw_entry": raw_entry,
                    "entry_price": raw_entry + slippage / 2,
                    "target": raw_entry + target_atr * atr.iloc[idx],
                    "stop": raw_entry - stop_atr * atr.iloc[idx],
                    "atr": atr.iloc[idx],
                }
        else:
            high = df["high"].iloc[idx]
            low = df["low"].iloc[idx]
            close = df["close"].iloc[idx]

            exit_signal = False
            raw_exit = None
            exit_reason = None

            if low <= position["stop"]:
                exit_signal = True
                raw_exit = position["stop"]
                exit_reason = "STOP"
            elif high >= position["target"]:
                exit_signal = True
                raw_exit = position["target"]
                exit_reason = "TARGET"
            elif idx - position["entry_idx"] >= max_bars:
                exit_signal = True
                raw_exit = close
                exit_reason = "TIME"

            if exit_signal:
                exit_price = raw_exit - slippage / 2
                pnl_net = exit_price - position["entry_price"]
                risk = position["raw_entry"] - position["stop"]
                pnl_r = pnl_net / risk if risk > 0 else 0

                trades.append(
                    {
                        "pnl_net": pnl_net,
                        "pnl_r": pnl_r,
                        "is_win": pnl_net > 0,
                        "exit_reason": exit_reason,
                    }
                )
                position = None

    if not trades:
        return {"trades": 0, "expectancy": 0, "hit_rate": 0}

    df_trades = pd.DataFrame(trades)

    return {
        "trades": len(df_trades),
        "expectancy": df_trades["pnl_r"].mean(),
        "hit_rate": df_trades["is_win"].mean(),
        "total_pnl": df_trades["pnl_net"].sum(),
        "target_pct": (df_trades["exit_reason"] == "TARGET").mean(),
        "stop_pct": (df_trades["exit_reason"] == "STOP").mean(),
    }


# =============================================================================
# TRACK A: 5-MINUTE GOLDILOCKS
# =============================================================================


def run_track_a():
    """5-Minute Goldilocks Discovery."""

    print("\n" + "=" * 70)
    print("TRACK A: 5-MINUTE 'GOLDILOCKS' DISCOVERY")
    print("=" * 70)

    # Load 1-min data
    data_path = project_root / "data" / "cache" / "equities"
    files = sorted(
        data_path.glob("SPY_1min_202*.parquet"),
        key=lambda x: x.stat().st_size,
        reverse=True,
    )
    df_1m = pd.read_parquet(files[0])
    print(f"Loaded 1-min data: {len(df_1m):,} bars")

    # Aggregate to 5-min
    df_5m = (
        df_1m.resample("5min")
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

    df_5m = df_5m.between_time("09:30", "15:55")
    print(f"Aggregated to 5-min: {len(df_5m):,} bars")

    # Calculate features (shorter lookback for 5-min)
    features = build_features(df_5m, lookback=12)  # 1 hour lookback

    # Calculate ATR
    atr = calculate_atr(df_5m)

    # Identify winning events (2.0 ATR target, 1.0 ATR max DD, 12 bars = 1 hour)
    print("\nIdentifying winning events...")
    target_atr = 2.0
    max_dd_atr = 1.0
    max_bars = 12

    is_winning = []
    for idx in range(len(df_5m) - max_bars):
        entry = df_5m["close"].iloc[idx]
        current_atr = atr.iloc[idx]

        if pd.isna(current_atr) or current_atr <= 0:
            is_winning.append(False)
            continue

        target = entry + target_atr * current_atr
        max_allowed_dd = max_dd_atr * current_atr

        winner = False
        max_dd = 0

        for j in range(idx + 1, min(idx + max_bars + 1, len(df_5m))):
            dd = entry - df_5m["low"].iloc[j]
            max_dd = max(max_dd, dd)

            if df_5m["high"].iloc[j] >= target and max_dd <= max_allowed_dd:
                winner = True
                break

        is_winning.append(winner)

    # Pad to match length
    is_winning.extend([False] * max_bars)
    features["is_winning"] = is_winning

    win_rate = sum(is_winning) / len(is_winning)
    print(f"Baseline win rate: {win_rate:.1%}")

    # Cluster analysis
    feat_cols = [c for c in features.columns if "_mean" in c or "_std" in c]
    feat_cols = [c for c in feat_cols if not features[c].isna().all()]

    wins_df = features[features["is_winning"]].dropna(subset=feat_cols)
    non_wins_df = features[~features["is_winning"]].dropna(subset=feat_cols)

    print(f"Winning samples: {len(wins_df):,}")
    print(f"Non-winning samples: {len(non_wins_df):,}")

    n_sample = min(10000, len(wins_df), len(non_wins_df))
    np.random.seed(42)
    wins = wins_df.sample(n=n_sample)
    non_wins = non_wins_df.sample(n=n_sample)

    X_win = wins[feat_cols].values
    X_non = non_wins[feat_cols].values
    X_all = np.vstack([X_win, X_non])
    labels = np.array(["win"] * len(X_win) + ["non"] * len(X_non))

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_all)

    # Cluster with k=6
    kmeans = KMeans(n_clusters=6, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)

    print("\n5-Minute Cluster Analysis:")
    print("-" * 60)

    results = []
    baseline = len(X_win) / len(X_all)

    for c in range(6):
        mask = clusters == c
        wins_in = (labels[mask] == "win").sum()
        total_in = mask.sum()
        win_rate_c = wins_in / total_in if total_in > 0 else 0
        lift = win_rate_c / baseline if baseline > 0 else 0
        signal_freq = total_in / len(X_all)

        # Estimate trades per day (78 5-min bars per day)
        bars_per_day = 78
        trades_per_day = signal_freq * bars_per_day

        print(
            f"  Cluster {c}: WinRate={win_rate_c:.1%}, Lift={lift:.2f}x, Freq={signal_freq:.1%}, ~{trades_per_day:.1f} trades/day"
        )

        # Get cluster membership for full dataset
        X_full = features[feat_cols].fillna(0).values
        X_full_scaled = scaler.transform(X_full)
        full_clusters = kmeans.predict(X_full_scaled)
        signal_mask = pd.Series(full_clusters == c, index=features.index)

        # Backtest this cluster
        backtest = run_backtest(
            df_5m, signal_mask, target_atr=2.0, stop_atr=1.0, max_bars=12, slippage=0.02
        )

        results.append(
            {
                "cluster": c,
                "win_rate": win_rate_c,
                "lift": lift,
                "signal_freq": signal_freq,
                "trades_per_day": trades_per_day,
                "expectancy": backtest["expectancy"],
                "backtest_trades": backtest["trades"],
                "hit_rate": backtest.get("hit_rate", 0),
                "target_pct": backtest.get("target_pct", 0),
            }
        )

    # Find best candidate
    print("\n5-Minute Backtest Results:")
    print("-" * 60)

    viable = []
    for r in results:
        print(
            f"  Cluster {r['cluster']}: Trades={r['backtest_trades']:,}, HitRate={r['hit_rate']:.1%}, Expect={r['expectancy']:.3f}R, Target%={r['target_pct']:.1%}"
        )
        if r["expectancy"] > 0.05 and r["trades_per_day"] >= 1:
            viable.append(r)

    if viable:
        best = max(viable, key=lambda x: x["expectancy"])
        print(f"\n*** BEST 5-MIN CANDIDATE: Cluster {best['cluster']} ***")
        print(f"    Expectancy: {best['expectancy']:.3f}R")
        print(f"    Trades/Day: {best['trades_per_day']:.1f}")
        print(f"    Hit Rate: {best['hit_rate']:.1%}")
    else:
        print(
            "\n*** NO VIABLE 5-MIN CANDIDATE (Expectancy > 0.05R and 1+ trades/day) ***"
        )
        best = max(results, key=lambda x: x["expectancy"])
        print(
            f"    Best available: Cluster {best['cluster']} with {best['expectancy']:.3f}R"
        )

    return best


# =============================================================================
# TRACK B: 15-MINUTE SECONDARY CLUSTER AUDIT
# =============================================================================


def run_track_b():
    """15-Minute Secondary Cluster Audit."""

    print("\n" + "=" * 70)
    print("TRACK B: 15-MINUTE 'SECONDARY CLUSTER' AUDIT")
    print("=" * 70)

    # Load 1-min data and aggregate to 15-min
    data_path = project_root / "data" / "cache" / "equities"
    files = sorted(
        data_path.glob("SPY_1min_202*.parquet"),
        key=lambda x: x.stat().st_size,
        reverse=True,
    )
    df_1m = pd.read_parquet(files[0])

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
    print(f"Loaded 15-min data: {len(df_15m):,} bars")

    # Calculate features
    features = build_features(df_15m, lookback=20)

    # Calculate ATR and add trend filter
    atr = calculate_atr(df_15m)
    features["sma_50"] = df_15m["close"].rolling(50).mean()
    features["in_uptrend"] = df_15m["close"] > features["sma_50"]

    # Identify winning events (2.0 ATR, 1.0 max DD, 8 bars)
    print("\nIdentifying winning events...")
    target_atr = 2.0
    max_dd_atr = 1.0
    max_bars = 8

    is_winning = []
    for idx in range(len(df_15m) - max_bars):
        entry = df_15m["close"].iloc[idx]
        current_atr = atr.iloc[idx]

        if pd.isna(current_atr) or current_atr <= 0:
            is_winning.append(False)
            continue

        target = entry + target_atr * current_atr
        max_allowed_dd = max_dd_atr * current_atr

        winner = False
        max_dd = 0

        for j in range(idx + 1, min(idx + max_bars + 1, len(df_15m))):
            dd = entry - df_15m["low"].iloc[j]
            max_dd = max(max_dd, dd)

            if df_15m["high"].iloc[j] >= target and max_dd <= max_allowed_dd:
                winner = True
                break

        is_winning.append(winner)

    is_winning.extend([False] * max_bars)
    features["is_winning"] = is_winning

    win_rate = sum(is_winning) / len(is_winning)
    print(f"Baseline win rate: {win_rate:.1%}")

    # Cluster analysis with MORE clusters (k=8) to find secondary opportunities
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

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_all)

    # Try k=8 for more granular clusters
    kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)

    print("\n15-Minute All-Cluster Analysis:")
    print("-" * 60)

    results = []
    baseline = len(X_win) / len(X_all)

    for c in range(8):
        mask = clusters == c
        wins_in = (labels[mask] == "win").sum()
        total_in = mask.sum()
        win_rate_c = wins_in / total_in if total_in > 0 else 0
        lift = win_rate_c / baseline if baseline > 0 else 0
        signal_freq = total_in / len(X_all)

        # Estimate trades per day (26 15-min bars per day)
        bars_per_day = 26
        trades_per_day = signal_freq * bars_per_day

        print(
            f"  Cluster {c}: WinRate={win_rate_c:.1%}, Lift={lift:.2f}x, Freq={signal_freq:.1%}, ~{trades_per_day:.1f} trades/day"
        )

        # Get cluster membership for full dataset
        X_full = features[feat_cols].fillna(0).values
        X_full_scaled = scaler.transform(X_full)
        full_clusters = kmeans.predict(X_full_scaled)

        # Test with and without trend filter
        signal_mask_raw = pd.Series(full_clusters == c, index=features.index)
        signal_mask_trend = signal_mask_raw & features["in_uptrend"]

        # Backtest raw
        backtest_raw = run_backtest(
            df_15m,
            signal_mask_raw,
            target_atr=2.0,
            stop_atr=1.0,
            max_bars=8,
            slippage=0.02,
        )

        # Backtest with trend filter
        backtest_trend = run_backtest(
            df_15m,
            signal_mask_trend,
            target_atr=2.0,
            stop_atr=1.0,
            max_bars=8,
            slippage=0.02,
        )

        results.append(
            {
                "cluster": c,
                "win_rate": win_rate_c,
                "lift": lift,
                "signal_freq": signal_freq,
                "trades_per_day": trades_per_day,
                "raw_expectancy": backtest_raw["expectancy"],
                "raw_trades": backtest_raw["trades"],
                "raw_hit_rate": backtest_raw.get("hit_rate", 0),
                "trend_expectancy": backtest_trend["expectancy"],
                "trend_trades": backtest_trend["trades"],
                "trend_hit_rate": backtest_trend.get("hit_rate", 0),
            }
        )

    # Find secondary candidates (not just the best)
    print("\n15-Minute Backtest Results (All Clusters):")
    print("-" * 70)
    print(
        f"{'Cluster':<8} {'Raw Trades':<12} {'Raw Exp.':<10} {'Trend Trades':<14} {'Trend Exp.':<12}"
    )
    print("-" * 70)

    workhorse_candidates = []

    for r in results:
        print(
            f"{r['cluster']:<8} {r['raw_trades']:<12} {r['raw_expectancy']:.3f}R{'':3} {r['trend_trades']:<14} {r['trend_expectancy']:.3f}R"
        )

        # Workhorse criteria: >5% signal freq AND positive expectancy
        if r["signal_freq"] > 0.05 and r["trend_expectancy"] > 0.05:
            workhorse_candidates.append(r)

    print("-" * 70)

    if workhorse_candidates:
        # Sort by expectancy
        workhorse_candidates.sort(key=lambda x: x["trend_expectancy"], reverse=True)
        best = workhorse_candidates[0]

        print(f"\n*** WORKHORSE CANDIDATES (Freq > 5%, Expect > 0.05R): ***")
        for r in workhorse_candidates:
            print(
                f"    Cluster {r['cluster']}: Expect={r['trend_expectancy']:.3f}R, Freq={r['signal_freq']:.1%}, ~{r['trades_per_day']:.1f}/day"
            )

        print(f"\n*** BEST 15-MIN WORKHORSE: Cluster {best['cluster']} ***")
        print(f"    Expectancy: {best['trend_expectancy']:.3f}R (with trend filter)")
        print(f"    Trades/Day: {best['trades_per_day']:.1f}")
        print(f"    Signal Freq: {best['signal_freq']:.1%}")
    else:
        print("\n*** NO WORKHORSE CANDIDATES (need Freq > 5% AND Expect > 0.05R) ***")
        # Find best available with higher frequency
        high_freq = [r for r in results if r["signal_freq"] > 0.05]
        if high_freq:
            best = max(high_freq, key=lambda x: x["trend_expectancy"])
            print(
                f"    Best high-freq: Cluster {best['cluster']} with {best['trend_expectancy']:.3f}R at {best['signal_freq']:.1%} freq"
            )
        else:
            best = max(results, key=lambda x: x["trend_expectancy"])

    return best


# =============================================================================
# MAIN
# =============================================================================


def main():
    print("=" * 70)
    print("DUAL-TRACK FREQUENCY OPTIMIZATION")
    print("Goal: Find 1-3 trades/day with positive expectancy")
    print("=" * 70)

    # Track A: 5-Minute
    best_5m = run_track_a()

    # Track B: 15-Minute Secondary
    best_15m = run_track_b()

    # Final comparison
    print("\n" + "=" * 70)
    print("FINAL COMPARISON: BEST CANDIDATES")
    print("=" * 70)

    print(f"\n{'Track A: 5-Minute Goldilocks':}")
    print(f"  Cluster: {best_5m['cluster']}")
    print(f"  Expectancy: {best_5m['expectancy']:.3f}R")
    print(f"  Trades/Day: {best_5m['trades_per_day']:.1f}")
    print(f"  Hit Rate: {best_5m['hit_rate']:.1%}")

    print(f"\n{'Track B: 15-Minute Workhorse':}")
    print(f"  Cluster: {best_15m['cluster']}")
    print(f"  Expectancy: {best_15m['trend_expectancy']:.3f}R (with trend filter)")
    print(f"  Trades/Day: {best_15m['trades_per_day']:.1f}")
    print(f"  Signal Freq: {best_15m['signal_freq']:.1%}")

    # Verdict
    print("\n" + "-" * 70)

    candidates_viable = []

    if best_5m["expectancy"] > 0.05 and best_5m["trades_per_day"] >= 1:
        candidates_viable.append(
            ("5-MIN", best_5m["expectancy"], best_5m["trades_per_day"])
        )

    if best_15m["trend_expectancy"] > 0.05 and best_15m["trades_per_day"] >= 1:
        candidates_viable.append(
            ("15-MIN", best_15m["trend_expectancy"], best_15m["trades_per_day"])
        )

    if candidates_viable:
        print("\n*** VIABLE DAILY TRADING CANDIDATES: ***")
        for name, exp, tpd in candidates_viable:
            print(f"  {name}: {exp:.3f}R expectancy, {tpd:.1f} trades/day")

        best_name, best_exp, best_tpd = max(candidates_viable, key=lambda x: x[1])
        print(f"\n*** RECOMMENDED: {best_name} ***")
    else:
        print("\n*** NO VIABLE DAILY TRADING CANDIDATE ***")
        print("Consider: Lower frequency 'sniper' approach may be more appropriate")

    return {"5m": best_5m, "15m": best_15m}


if __name__ == "__main__":
    results = main()
    sys.exit(0)
