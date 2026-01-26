"""
COMBINED PORTFOLIO BACKTEST
Sniper (Dip Buyer) + Workhorse (Cluster 7)

Each strategy starts with $25,000
- Sniper: 2% risk per trade (low frequency, high quality)
- Workhorse: 1% risk per trade (high frequency, volume)

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
from dataclasses import dataclass
from typing import List, Dict
import warnings

warnings.filterwarnings("ignore")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class Trade:
    """Trade record."""

    strategy: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    shares: int
    pnl_dollars: float
    pnl_r: float
    is_win: bool
    exit_reason: str


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


def train_workhorse_model(features: pd.DataFrame, df: pd.DataFrame) -> tuple:
    """Train K-Means model for Workhorse strategy."""

    print("\nTraining Workhorse (Cluster 7) model...")

    # Calculate ATR and identify winning events
    atr = calculate_atr(df)

    target_atr = 2.0
    max_dd_atr = 1.0
    max_bars = 8

    is_winning = []
    for idx in range(len(df) - max_bars):
        entry = df["close"].iloc[idx]
        current_atr = atr.iloc[idx]

        if pd.isna(current_atr) or current_atr <= 0:
            is_winning.append(False)
            continue

        target = entry + target_atr * current_atr
        max_allowed_dd = max_dd_atr * current_atr

        winner = False
        max_dd = 0

        for j in range(idx + 1, min(idx + max_bars + 1, len(df))):
            dd = entry - df["low"].iloc[j]
            max_dd = max(max_dd, dd)

            if df["high"].iloc[j] >= target and max_dd <= max_allowed_dd:
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

    # Train scaler and K-Means
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_all)

    kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
    kmeans.fit(X_scaled)

    print(
        f"  Trained on {len(X_all):,} samples ({n_sample:,} wins + {n_sample:,} non-wins)"
    )

    return scaler, kmeans, feat_cols


def run_portfolio_backtest(
    df: pd.DataFrame, features: pd.DataFrame, workhorse_model: tuple
) -> Dict:
    """Run combined backtest for both strategies."""

    print("\n" + "=" * 70)
    print("RUNNING COMBINED PORTFOLIO BACKTEST")
    print("=" * 70)

    scaler, kmeans, feat_cols = workhorse_model

    # Calculate ATR and SMA
    atr = calculate_atr(df)
    sma_50 = df["close"].rolling(50).mean()
    in_uptrend = df["close"] > sma_50

    # Assign clusters for Workhorse
    X_full = features[feat_cols].fillna(0).values
    X_scaled = scaler.transform(X_full)
    clusters = kmeans.predict(X_scaled)
    is_cluster_7 = clusters == 7

    # Sniper thresholds (from original analysis)
    sniper_effort_threshold = -61.0
    sniper_range_threshold = 3.88
    sniper_volatility_threshold = 0.88

    # Check Sniper signals
    is_sniper = (
        (features.get("effort_result_mean", 0) < sniper_effort_threshold)
        & (features.get("range_ratio_mean", 0) > sniper_range_threshold)
        & (features.get("volatility_ratio_mean", 0) > sniper_volatility_threshold)
    )

    # Account tracking
    sniper_account = 25000.0
    workhorse_account = 25000.0

    sniper_trades = []
    workhorse_trades = []

    sniper_position = None
    workhorse_position = None

    # Risk parameters
    sniper_risk_pct = 0.02  # 2% risk
    workhorse_risk_pct = 0.01  # 1% risk

    target_mult = 2.0
    stop_mult = 1.0
    max_hold_bars = 8
    slippage = 0.02

    # Daily tracking
    daily_pnl = []
    current_date = None
    daily_sniper_pnl = 0
    daily_workhorse_pnl = 0

    print(f"\nStarting capital: $25,000 each")
    print(f"Sniper risk: 2% per trade")
    print(f"Workhorse risk: 1% per trade")
    print(f"\nBacktesting {len(df):,} bars...")

    for idx in range(len(df)):
        bar_time = df.index[idx]
        current_price = df["close"].iloc[idx]

        # Track daily P&L
        bar_date = bar_time.date()
        if current_date != bar_date:
            if current_date is not None:
                daily_pnl.append(
                    {
                        "date": current_date,
                        "sniper_pnl": daily_sniper_pnl,
                        "workhorse_pnl": daily_workhorse_pnl,
                        "sniper_balance": sniper_account,
                        "workhorse_balance": workhorse_account,
                    }
                )
            current_date = bar_date
            daily_sniper_pnl = 0
            daily_workhorse_pnl = 0

        current_atr = atr.iloc[idx]
        if pd.isna(current_atr) or pd.isna(sma_50.iloc[idx]):
            continue

        # ===== SNIPER STRATEGY =====
        if sniper_position is None:
            # Check entry
            if is_sniper.iloc[idx] and in_uptrend.iloc[idx]:
                # Calculate position size
                risk_dollars = sniper_account * sniper_risk_pct
                stop_distance = stop_mult * current_atr
                shares = int(risk_dollars / stop_distance)

                if shares > 0:
                    raw_entry = current_price
                    entry_price = raw_entry + slippage / 2

                    sniper_position = {
                        "entry_idx": idx,
                        "entry_time": bar_time,
                        "raw_entry": raw_entry,
                        "entry_price": entry_price,
                        "shares": shares,
                        "target": raw_entry + target_mult * current_atr,
                        "stop": raw_entry - stop_mult * current_atr,
                        "atr": current_atr,
                    }
        else:
            # Manage Sniper position
            high = df["high"].iloc[idx]
            low = df["low"].iloc[idx]
            close = df["close"].iloc[idx]

            exit_signal = False
            raw_exit = None
            exit_reason = None

            if low <= sniper_position["stop"]:
                exit_signal = True
                raw_exit = sniper_position["stop"]
                exit_reason = "STOP"
            elif high >= sniper_position["target"]:
                exit_signal = True
                raw_exit = sniper_position["target"]
                exit_reason = "TARGET"
            elif idx - sniper_position["entry_idx"] >= max_hold_bars:
                exit_signal = True
                raw_exit = close
                exit_reason = "TIME"

            if exit_signal:
                exit_price = raw_exit - slippage / 2
                pnl_gross = (raw_exit - sniper_position["raw_entry"]) * sniper_position[
                    "shares"
                ]
                pnl_net = (
                    exit_price - sniper_position["entry_price"]
                ) * sniper_position["shares"]

                risk = (
                    sniper_position["raw_entry"] - sniper_position["stop"]
                ) * sniper_position["shares"]
                pnl_r = pnl_net / risk if risk > 0 else 0

                sniper_account += pnl_net
                daily_sniper_pnl += pnl_net

                sniper_trades.append(
                    Trade(
                        strategy="SNIPER",
                        entry_time=sniper_position["entry_time"],
                        exit_time=bar_time,
                        entry_price=sniper_position["entry_price"],
                        exit_price=exit_price,
                        shares=sniper_position["shares"],
                        pnl_dollars=pnl_net,
                        pnl_r=pnl_r,
                        is_win=pnl_net > 0,
                        exit_reason=exit_reason,
                    )
                )
                sniper_position = None

        # ===== WORKHORSE STRATEGY =====
        if workhorse_position is None:
            # Check entry
            if is_cluster_7[idx] and in_uptrend.iloc[idx]:
                # Calculate position size
                risk_dollars = workhorse_account * workhorse_risk_pct
                stop_distance = stop_mult * current_atr
                shares = int(risk_dollars / stop_distance)

                if shares > 0:
                    raw_entry = current_price
                    entry_price = raw_entry + slippage / 2

                    workhorse_position = {
                        "entry_idx": idx,
                        "entry_time": bar_time,
                        "raw_entry": raw_entry,
                        "entry_price": entry_price,
                        "shares": shares,
                        "target": raw_entry + target_mult * current_atr,
                        "stop": raw_entry - stop_mult * current_atr,
                        "atr": current_atr,
                    }
        else:
            # Manage Workhorse position
            high = df["high"].iloc[idx]
            low = df["low"].iloc[idx]
            close = df["close"].iloc[idx]

            exit_signal = False
            raw_exit = None
            exit_reason = None

            if low <= workhorse_position["stop"]:
                exit_signal = True
                raw_exit = workhorse_position["stop"]
                exit_reason = "STOP"
            elif high >= workhorse_position["target"]:
                exit_signal = True
                raw_exit = workhorse_position["target"]
                exit_reason = "TARGET"
            elif idx - workhorse_position["entry_idx"] >= max_hold_bars:
                exit_signal = True
                raw_exit = close
                exit_reason = "TIME"

            if exit_signal:
                exit_price = raw_exit - slippage / 2
                pnl_gross = (
                    raw_exit - workhorse_position["raw_entry"]
                ) * workhorse_position["shares"]
                pnl_net = (
                    exit_price - workhorse_position["entry_price"]
                ) * workhorse_position["shares"]

                risk = (
                    workhorse_position["raw_entry"] - workhorse_position["stop"]
                ) * workhorse_position["shares"]
                pnl_r = pnl_net / risk if risk > 0 else 0

                workhorse_account += pnl_net
                daily_workhorse_pnl += pnl_net

                workhorse_trades.append(
                    Trade(
                        strategy="WORKHORSE",
                        entry_time=workhorse_position["entry_time"],
                        exit_time=bar_time,
                        entry_price=workhorse_position["entry_price"],
                        exit_price=exit_price,
                        shares=workhorse_position["shares"],
                        pnl_dollars=pnl_net,
                        pnl_r=pnl_r,
                        is_win=pnl_net > 0,
                        exit_reason=exit_reason,
                    )
                )
                workhorse_position = None

    # Add final day
    if current_date is not None:
        daily_pnl.append(
            {
                "date": current_date,
                "sniper_pnl": daily_sniper_pnl,
                "workhorse_pnl": daily_workhorse_pnl,
                "sniper_balance": sniper_account,
                "workhorse_balance": workhorse_account,
            }
        )

    return {
        "sniper_trades": sniper_trades,
        "workhorse_trades": workhorse_trades,
        "sniper_final": sniper_account,
        "workhorse_final": workhorse_account,
        "daily_pnl": pd.DataFrame(daily_pnl),
    }


def analyze_results(results: Dict):
    """Analyze and print portfolio results."""

    sniper_trades = results["sniper_trades"]
    workhorse_trades = results["workhorse_trades"]
    daily_pnl = results["daily_pnl"]

    print("\n" + "=" * 70)
    print("PORTFOLIO PERFORMANCE SUMMARY")
    print("=" * 70)

    # Sniper analysis
    if sniper_trades:
        df_sniper = pd.DataFrame(
            [
                {
                    "pnl_dollars": t.pnl_dollars,
                    "pnl_r": t.pnl_r,
                    "is_win": t.is_win,
                    "exit_reason": t.exit_reason,
                }
                for t in sniper_trades
            ]
        )

        sniper_total = len(df_sniper)
        sniper_wins = df_sniper["is_win"].sum()
        sniper_hr = sniper_wins / sniper_total
        sniper_total_pnl = df_sniper["pnl_dollars"].sum()
        sniper_avg_pnl = df_sniper["pnl_dollars"].mean()
        sniper_expect = df_sniper["pnl_r"].mean()
    else:
        sniper_total = sniper_wins = sniper_hr = sniper_total_pnl = sniper_avg_pnl = (
            sniper_expect
        ) = 0

    # Workhorse analysis
    if workhorse_trades:
        df_workhorse = pd.DataFrame(
            [
                {
                    "pnl_dollars": t.pnl_dollars,
                    "pnl_r": t.pnl_r,
                    "is_win": t.is_win,
                    "exit_reason": t.exit_reason,
                }
                for t in workhorse_trades
            ]
        )

        workhorse_total = len(df_workhorse)
        workhorse_wins = df_workhorse["is_win"].sum()
        workhorse_hr = workhorse_wins / workhorse_total
        workhorse_total_pnl = df_workhorse["pnl_dollars"].sum()
        workhorse_avg_pnl = df_workhorse["pnl_dollars"].mean()
        workhorse_expect = df_workhorse["pnl_r"].mean()
    else:
        workhorse_total = workhorse_wins = workhorse_hr = workhorse_total_pnl = (
            workhorse_avg_pnl
        ) = workhorse_expect = 0

    # Print results
    print(f"\n{'SNIPER (Dip Buyer)':^35} {'WORKHORSE (Cluster 7)':^35}")
    print("-" * 70)
    print(f"{'Starting Capital:':<25} $25,000 {'':>10} $25,000")
    print(
        f"{'Final Balance:':<25} ${results['sniper_final']:>8,.2f} {'':>8} ${results['workhorse_final']:>8,.2f}"
    )
    print(
        f"{'Total P&L:':<25} ${sniper_total_pnl:>8,.2f} {'':>8} ${workhorse_total_pnl:>8,.2f}"
    )
    print(
        f"{'Return:':<25} {(results['sniper_final']/25000-1)*100:>7.2f}% {'':>8} {(results['workhorse_final']/25000-1)*100:>7.2f}%"
    )
    print()
    print(f"{'Total Trades:':<25} {sniper_total:>10} {'':>10} {workhorse_total:>10}")
    print(f"{'Win Rate:':<25} {sniper_hr:>9.1%} {'':>10} {workhorse_hr:>9.1%}")
    print(
        f"{'Avg P&L/Trade:':<25} ${sniper_avg_pnl:>8.2f} {'':>8} ${workhorse_avg_pnl:>8.2f}"
    )
    print(
        f"{'Expectancy (R):':<25} {sniper_expect:>9.3f}R {'':>7} {workhorse_expect:>9.3f}R"
    )

    # Combined portfolio
    combined_final = results["sniper_final"] + results["workhorse_final"]
    combined_pnl = combined_final - 50000
    combined_return = (combined_final / 50000 - 1) * 100

    print("\n" + "-" * 70)
    print(f"{'COMBINED PORTFOLIO':^70}")
    print("-" * 70)
    print(f"Starting Capital:     $50,000")
    print(f"Final Balance:        ${combined_final:,.2f}")
    print(f"Total P&L:            ${combined_pnl:,.2f}")
    print(f"Return:               {combined_return:.2f}%")
    print(f"Total Trades:         {sniper_total + workhorse_total}")

    # Daily/Weekly P&L
    print("\n" + "=" * 70)
    print("DAILY P&L SUMMARY (Last 10 Days)")
    print("=" * 70)

    if len(daily_pnl) > 0:
        print(
            f"\n{'Date':<12} {'Sniper P&L':>12} {'Workhorse P&L':>15} {'Combined':>12} {'Total Balance':>15}"
        )
        print("-" * 70)

        for _, row in daily_pnl.tail(10).iterrows():
            combined_day = row["sniper_pnl"] + row["workhorse_pnl"]
            total_balance = row["sniper_balance"] + row["workhorse_balance"]
            print(
                f"{str(row['date']):<12} ${row['sniper_pnl']:>11,.2f} ${row['workhorse_pnl']:>14,.2f} ${combined_day:>11,.2f} ${total_balance:>14,.2f}"
            )

        # Weekly summary for Sniper
        print("\n" + "=" * 70)
        print("WEEKLY P&L SUMMARY (Last 8 Weeks)")
        print("=" * 70)

        daily_pnl["week"] = pd.to_datetime(daily_pnl["date"]).dt.to_period("W")
        weekly = daily_pnl.groupby("week").agg(
            {
                "sniper_pnl": "sum",
                "workhorse_pnl": "sum",
                "sniper_balance": "last",
                "workhorse_balance": "last",
            }
        )

        print(
            f"\n{'Week Ending':<15} {'Sniper P&L':>12} {'Workhorse P&L':>15} {'Combined':>12}"
        )
        print("-" * 60)

        for week, row in weekly.tail(8).iterrows():
            combined_week = row["sniper_pnl"] + row["workhorse_pnl"]
            print(
                f"{str(week):<15} ${row['sniper_pnl']:>11,.2f} ${row['workhorse_pnl']:>14,.2f} ${combined_week:>11,.2f}"
            )


def main():
    print("=" * 70)
    print("COMBINED PORTFOLIO BACKTEST")
    print("Sniper (Dip Buyer) + Workhorse (Cluster 7)")
    print("=" * 70)

    # Load data
    data_path = project_root / "data" / "cache" / "equities"
    files = sorted(
        data_path.glob("SPY_1min_202*.parquet"),
        key=lambda x: x.stat().st_size,
        reverse=True,
    )
    df_1m = pd.read_parquet(files[0])

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
    print(f"\nLoaded 15-min data: {len(df_15m):,} bars")
    print(f"Date range: {df_15m.index.min()} to {df_15m.index.max()}")

    # Build features
    features = build_features(df_15m, lookback=20)

    # Train Workhorse model
    workhorse_model = train_workhorse_model(features, df_15m)

    # Run backtest
    results = run_portfolio_backtest(df_15m, features, workhorse_model)

    # Analyze
    analyze_results(results)

    # Save results
    output_file = (
        project_root / "test" / "vol_expansion" / "portfolio_backtest_results.json"
    )

    results_summary = {
        "start_date": str(df_15m.index.min()),
        "end_date": str(df_15m.index.max()),
        "sniper": {
            "starting_capital": 25000,
            "final_balance": results["sniper_final"],
            "total_pnl": results["sniper_final"] - 25000,
            "return_pct": (results["sniper_final"] / 25000 - 1) * 100,
            "total_trades": len(results["sniper_trades"]),
        },
        "workhorse": {
            "starting_capital": 25000,
            "final_balance": results["workhorse_final"],
            "total_pnl": results["workhorse_final"] - 25000,
            "return_pct": (results["workhorse_final"] / 25000 - 1) * 100,
            "total_trades": len(results["workhorse_trades"]),
        },
        "combined": {
            "starting_capital": 50000,
            "final_balance": results["sniper_final"] + results["workhorse_final"],
            "total_pnl": (results["sniper_final"] + results["workhorse_final"]) - 50000,
            "return_pct": (
                (results["sniper_final"] + results["workhorse_final"]) / 50000 - 1
            )
            * 100,
            "total_trades": len(results["sniper_trades"])
            + len(results["workhorse_trades"]),
        },
    }

    with open(output_file, "w") as f:
        json.dump(results_summary, f, indent=2)

    print(f"\n*** Results saved to {output_file} ***")

    return results


if __name__ == "__main__":
    results = main()
    sys.exit(0)
