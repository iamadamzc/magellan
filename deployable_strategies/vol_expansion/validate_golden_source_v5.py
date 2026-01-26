"""
Golden Source Validation V5 - "SNIPER" Stress Test

PURPOSE:
1. Compare "Sniper" (0.5 ATR stop) vs "Balanced" (1.0 ATR stop) configurations
2. Apply realistic slippage to test fragility
3. Calculate max drawdown and consecutive losses for psychological viability
4. Determine if the edge survives transaction costs

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
from typing import List, Dict, Tuple

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class BacktestConfig:
    """Configuration for a backtest run."""

    name: str
    stop_atr: float
    target_atr: float
    slippage_per_share: float  # Total round-trip slippage
    max_hold_bars: int = 30


@dataclass
class TradeResult:
    """Result of a single trade."""

    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    atr: float
    pnl_gross: float
    pnl_net: float  # After slippage
    pnl_r: float  # In risk units
    is_win: bool
    exit_reason: str
    slippage_cost: float


class SniperStressTest:
    """
    Stress test comparing aggressive vs balanced stop configurations.
    """

    def __init__(self):
        results_path = (
            project_root
            / "research"
            / "blind_backwards_analysis"
            / "outputs"
            / "FINAL_STRATEGY_RESULTS.json"
        )
        with open(results_path) as f:
            self.research_thresholds = json.load(f)
        print("=" * 70)
        print("V5 'SNIPER' STRESS TEST")
        print("Comparing Aggressive vs Balanced Stop Configurations")
        print("=" * 70)
        print("\nLoaded research thresholds")

    def load_data(self, symbol: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load golden source and price data."""
        features_path = (
            project_root
            / "research"
            / "blind_backwards_analysis"
            / "outputs"
            / f"{symbol}_features.parquet"
        )
        features = pd.read_parquet(features_path)

        data_path = project_root / "data" / "cache" / "equities"
        files = sorted(
            data_path.glob(f"{symbol}_1min_202*.parquet"),
            key=lambda x: x.stat().st_size,
            reverse=True,
        )
        prices = pd.read_parquet(files[0])

        print(f"Loaded {symbol}: {len(features):,} bars")
        return features, prices

    def setup_clustering(self, features: pd.DataFrame, symbol: str) -> Tuple:
        """Replicate research clustering."""
        feat_cols = [c for c in features.columns if "_mean" in c][:15]

        strict_path = (
            project_root
            / "research"
            / "blind_backwards_analysis"
            / "outputs"
            / f"{symbol}_winning_events_strict.parquet"
        )
        strict = pd.read_parquet(strict_path)
        strict_ts = pd.to_datetime(strict["timestamp"])
        features["is_strict_win"] = features.index.isin(strict_ts[strict["is_winning"]])

        np.random.seed(42)
        wins_df = features[features["is_strict_win"]].dropna(subset=feat_cols)
        non_wins_df = features[~features["is_strict_win"]].dropna(subset=feat_cols)

        n_sample = min(30000, len(wins_df), len(non_wins_df))
        wins = wins_df.sample(n=n_sample)
        non_wins = non_wins_df.sample(n=n_sample)

        X_win = wins[feat_cols].values
        X_non = non_wins[feat_cols].values
        X_all = np.vstack([X_win, X_non])
        labels = np.array(["win"] * len(X_win) + ["non"] * len(X_non))

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_all)

        kmeans = KMeans(n_clusters=6, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)

        best_cluster = None
        best_lift = 0

        for c in range(6):
            mask = clusters == c
            wins_in = (labels[mask] == "win").sum()
            total_in = mask.sum()
            prev_win = (clusters[labels == "win"] == c).mean()
            prev_non = (clusters[labels == "non"] == c).mean()
            lift = prev_win / (prev_non + 0.001)
            if lift > best_lift:
                best_lift = lift
                best_cluster = c

        print(f"Best cluster: {best_cluster} (Lift: {best_lift:.2f}x)")
        return scaler, kmeans, feat_cols, best_cluster

    def prepare_data(
        self,
        features: pd.DataFrame,
        prices: pd.DataFrame,
        scaler,
        kmeans,
        feat_cols,
        best_cluster,
    ) -> pd.DataFrame:
        """Prepare merged data with signals."""
        merged = features.join(
            prices[["open", "high", "low", "close", "volume"]], how="inner"
        )

        X_full = merged[feat_cols].fillna(0).values
        valid_mask = ~np.isnan(X_full).any(axis=1)
        X_valid = X_full[valid_mask]

        X_scaled = scaler.transform(X_valid)
        cluster_labels = kmeans.predict(X_scaled)

        signal_mask = np.zeros(len(merged), dtype=bool)
        signal_mask[valid_mask] = cluster_labels == best_cluster

        merged_valid = merged.loc[valid_mask].copy()
        merged_valid["signal"] = cluster_labels == best_cluster

        # Calculate ATR
        tr1 = merged_valid["high"] - merged_valid["low"]
        tr2 = (merged_valid["high"] - merged_valid["close"].shift(1)).abs()
        tr3 = (merged_valid["low"] - merged_valid["close"].shift(1)).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        merged_valid["atr"] = true_range.rolling(20).mean()

        # Filter valid
        merged_valid = merged_valid.dropna(subset=["atr"])

        signal_count = merged_valid["signal"].sum()
        print(f"Signals: {signal_count:,} ({merged_valid['signal'].mean():.1%})")

        return merged_valid

    def run_backtest(
        self, merged: pd.DataFrame, config: BacktestConfig
    ) -> List[TradeResult]:
        """Run backtest with given configuration."""

        position = None
        trades = []

        price_array = merged[["open", "high", "low", "close"]].values
        atr_array = merged["atr"].values
        signal_array = merged["signal"].values
        index_array = merged.index

        for idx in range(len(merged)):
            if position is None:
                if signal_array[idx]:
                    atr = atr_array[idx]
                    # Entry at close with slippage (worse fill)
                    raw_entry = price_array[idx, 3]
                    entry_slippage = config.slippage_per_share / 2
                    entry_price = raw_entry + entry_slippage  # Buying higher

                    position = {
                        "entry_idx": idx,
                        "entry_time": index_array[idx],
                        "raw_entry": raw_entry,
                        "entry_price": entry_price,
                        "target": raw_entry + (config.target_atr * atr),
                        "stop": raw_entry - (config.stop_atr * atr),
                        "atr": atr,
                    }
            else:
                high = price_array[idx, 1]
                low = price_array[idx, 2]
                close = price_array[idx, 3]

                exit_signal = False
                exit_reason = None
                raw_exit = None

                # Check stop (uses raw price levels, not slippage-adjusted)
                if low <= position["stop"]:
                    exit_signal = True
                    exit_reason = "STOP_LOSS"
                    raw_exit = position["stop"]

                # Check target
                elif high >= position["target"]:
                    exit_signal = True
                    exit_reason = "TARGET_HIT"
                    raw_exit = position["target"]

                # Time stop
                elif idx - position["entry_idx"] >= config.max_hold_bars:
                    exit_signal = True
                    exit_reason = "TIME_STOP"
                    raw_exit = close

                if exit_signal:
                    # Apply exit slippage (worse fill)
                    exit_slippage = config.slippage_per_share / 2
                    exit_price = raw_exit - exit_slippage  # Selling lower

                    # Calculate P&L
                    pnl_gross = raw_exit - position["raw_entry"]
                    pnl_net = exit_price - position["entry_price"]
                    slippage_cost = config.slippage_per_share

                    # P&L in R units (risk = stop distance)
                    risk = position["raw_entry"] - position["stop"]
                    pnl_r = pnl_net / risk if risk > 0 else 0

                    trade = TradeResult(
                        entry_time=position["entry_time"],
                        exit_time=index_array[idx],
                        entry_price=position["entry_price"],
                        exit_price=exit_price,
                        atr=position["atr"],
                        pnl_gross=pnl_gross,
                        pnl_net=pnl_net,
                        pnl_r=pnl_r,
                        is_win=pnl_net > 0,
                        exit_reason=exit_reason,
                        slippage_cost=slippage_cost,
                    )
                    trades.append(trade)
                    position = None

        return trades

    def calculate_metrics(
        self, trades: List[TradeResult], config: BacktestConfig
    ) -> Dict:
        """Calculate comprehensive metrics including drawdown and losing streaks."""

        if not trades:
            return {"error": "No trades"}

        df = pd.DataFrame(
            [
                {
                    "entry_time": t.entry_time,
                    "pnl_net": t.pnl_net,
                    "pnl_r": t.pnl_r,
                    "is_win": t.is_win,
                    "exit_reason": t.exit_reason,
                    "slippage_cost": t.slippage_cost,
                    "atr": t.atr,
                }
                for t in trades
            ]
        )

        total_trades = len(df)
        wins = df["is_win"].sum()
        losses = total_trades - wins
        hit_rate = wins / total_trades

        avg_win_r = df[df["is_win"]]["pnl_r"].mean() if wins > 0 else 0
        avg_loss_r = df[~df["is_win"]]["pnl_r"].mean() if losses > 0 else 0

        # Net expectancy (after slippage)
        expectancy_r = df["pnl_r"].mean()

        # Total P&L
        total_pnl = df["pnl_net"].sum()
        total_slippage = df["slippage_cost"].sum()

        # Equity curve for drawdown
        df["cumulative_pnl"] = df["pnl_net"].cumsum()
        df["running_max"] = df["cumulative_pnl"].cummax()
        df["drawdown"] = df["cumulative_pnl"] - df["running_max"]
        max_drawdown = df["drawdown"].min()

        # Max consecutive losses
        df["loss_streak"] = 0
        current_streak = 0
        max_streak = 0
        streaks = []

        for i, row in df.iterrows():
            if not row["is_win"]:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                if current_streak > 0:
                    streaks.append(current_streak)
                current_streak = 0

        if current_streak > 0:
            streaks.append(current_streak)

        # Sharpe-like ratio (simplified)
        if df["pnl_r"].std() > 0:
            sharpe_proxy = (df["pnl_r"].mean() / df["pnl_r"].std()) * np.sqrt(
                252 * 6.5 * 60 / 30
            )  # Annualized
        else:
            sharpe_proxy = 0

        # Exit reason breakdown
        exit_breakdown = {}
        for reason in ["TARGET_HIT", "STOP_LOSS", "TIME_STOP"]:
            count = (df["exit_reason"] == reason).sum()
            reason_df = df[df["exit_reason"] == reason]
            reason_hr = reason_df["is_win"].mean() if len(reason_df) > 0 else 0
            exit_breakdown[reason] = {
                "count": count,
                "pct": count / total_trades * 100,
                "win_rate": reason_hr,
            }

        # P&L per trade stats
        avg_pnl_dollars = df["pnl_net"].mean()
        avg_slippage = df["slippage_cost"].mean()
        slippage_pct_of_pnl = (
            abs(avg_slippage / avg_pnl_dollars * 100)
            if avg_pnl_dollars != 0
            else float("inf")
        )

        return {
            "config_name": config.name,
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "hit_rate": hit_rate,
            "avg_win_r": avg_win_r,
            "avg_loss_r": avg_loss_r,
            "expectancy_r": expectancy_r,
            "total_pnl": total_pnl,
            "total_slippage": total_slippage,
            "max_drawdown": max_drawdown,
            "max_consecutive_losses": max_streak,
            "avg_losing_streak": np.mean(streaks) if streaks else 0,
            "sharpe_proxy": sharpe_proxy,
            "exit_breakdown": exit_breakdown,
            "avg_pnl_dollars": avg_pnl_dollars,
            "avg_slippage": avg_slippage,
            "slippage_pct_of_pnl": slippage_pct_of_pnl,
        }

    def print_results(self, metrics: Dict, config: BacktestConfig):
        """Print detailed results for a configuration."""

        print(f"\n{'='*70}")
        print(f"CONFIGURATION: {config.name}")
        print(
            f"Stop: {config.stop_atr} ATR | Target: {config.target_atr} ATR | R:R = 1:{config.target_atr/config.stop_atr:.1f}"
        )
        print(f"Slippage: ${config.slippage_per_share:.2f} round-trip")
        print(f"{'='*70}")

        print(f"\n--- CORE METRICS ---")
        print(f"Total Trades:        {metrics['total_trades']:,}")
        print(f"Wins/Losses:         {metrics['wins']:,} / {metrics['losses']:,}")
        print(f"Hit Rate:            {metrics['hit_rate']:.1%}")
        print(f"Avg Win:             {metrics['avg_win_r']:.3f}R")
        print(f"Avg Loss:            {metrics['avg_loss_r']:.3f}R")
        print(f"NET EXPECTANCY:      {metrics['expectancy_r']:.3f}R per trade")

        print(f"\n--- P&L ANALYSIS ---")
        print(f"Total P&L:           ${metrics['total_pnl']:,.2f}")
        print(f"Total Slippage Cost: ${metrics['total_slippage']:,.2f}")
        print(f"Avg P&L/Trade:       ${metrics['avg_pnl_dollars']:.4f}")
        print(f"Slippage % of P&L:   {metrics['slippage_pct_of_pnl']:.1f}%")

        print(f"\n--- RISK METRICS ---")
        print(f"Max Drawdown:        ${metrics['max_drawdown']:,.2f}")
        print(f"Max Consec. Losses:  {metrics['max_consecutive_losses']}")
        print(f"Avg Losing Streak:   {metrics['avg_losing_streak']:.1f}")
        print(f"Sharpe Proxy:        {metrics['sharpe_proxy']:.2f}")

        print(f"\n--- EXIT BREAKDOWN ---")
        for reason, data in metrics["exit_breakdown"].items():
            print(
                f"  {reason:12s}: {data['count']:5d} ({data['pct']:5.1f}%) | Win Rate: {data['win_rate']:.1%}"
            )

        # Psychological viability assessment
        print(f"\n--- PSYCHOLOGICAL VIABILITY ---")
        if metrics["max_consecutive_losses"] <= 10:
            print(
                f"  Losing Streak: MANAGEABLE ({metrics['max_consecutive_losses']} max)"
            )
        elif metrics["max_consecutive_losses"] <= 15:
            print(
                f"  Losing Streak: CHALLENGING ({metrics['max_consecutive_losses']} max)"
            )
        else:
            print(
                f"  Losing Streak: EXTREME ({metrics['max_consecutive_losses']} max) - May cause abandonment!"
            )

        if metrics["slippage_pct_of_pnl"] < 20:
            print(
                f"  Slippage Impact: LOW ({metrics['slippage_pct_of_pnl']:.1f}% of profits)"
            )
        elif metrics["slippage_pct_of_pnl"] < 50:
            print(
                f"  Slippage Impact: MODERATE ({metrics['slippage_pct_of_pnl']:.1f}% of profits)"
            )
        else:
            print(
                f"  Slippage Impact: SEVERE ({metrics['slippage_pct_of_pnl']:.1f}% of profits) - Strategy may be fragile!"
            )


def main():
    tester = SniperStressTest()

    # Load and prepare data
    features, prices = tester.load_data("SPY")
    scaler, kmeans, feat_cols, best_cluster = tester.setup_clustering(features, "SPY")
    merged = tester.prepare_data(
        features, prices, scaler, kmeans, feat_cols, best_cluster
    )

    # Define configurations
    configs = [
        BacktestConfig(
            name="CONFIG A: AGGRESSIVE SNIPER",
            stop_atr=0.5,
            target_atr=2.5,
            slippage_per_share=0.02,  # $0.01 entry + $0.01 exit
            max_hold_bars=30,
        ),
        BacktestConfig(
            name="CONFIG B: BALANCED APPROACH",
            stop_atr=1.0,
            target_atr=2.5,
            slippage_per_share=0.02,
            max_hold_bars=30,
        ),
    ]

    all_metrics = []

    for config in configs:
        trades = tester.run_backtest(merged, config)
        metrics = tester.calculate_metrics(trades, config)
        tester.print_results(metrics, config)
        all_metrics.append(metrics)

    # Final comparison
    print("\n" + "=" * 70)
    print("FINAL VERDICT: CONFIGURATION COMPARISON")
    print("=" * 70)

    print(f"\n{'Metric':<25} {'SNIPER (0.5 ATR)':<20} {'BALANCED (1.0 ATR)':<20}")
    print("-" * 65)

    m_a, m_b = all_metrics

    hr_a = f"{m_a['hit_rate']:.1%}"
    hr_b = f"{m_b['hit_rate']:.1%}"
    print(f"{'Hit Rate':<25} {hr_a:<20} {hr_b:<20}")

    exp_a = f"{m_a['expectancy_r']:.3f}R"
    exp_b = f"{m_b['expectancy_r']:.3f}R"
    print(f"{'Net Expectancy (R)':<25} {exp_a:<20} {exp_b:<20}")

    pnl_a = f"${m_a['total_pnl']:,.0f}"
    pnl_b = f"${m_b['total_pnl']:,.0f}"
    print(f"{'Total P&L':<25} {pnl_a:<20} {pnl_b:<20}")

    dd_a = f"${m_a['max_drawdown']:,.0f}"
    dd_b = f"${m_b['max_drawdown']:,.0f}"
    print(f"{'Max Drawdown':<25} {dd_a:<20} {dd_b:<20}")

    print(
        f"{'Max Consec. Losses':<25} {m_a['max_consecutive_losses']:<20} {m_b['max_consecutive_losses']:<20}"
    )

    sharpe_a = f"{m_a['sharpe_proxy']:.2f}"
    sharpe_b = f"{m_b['sharpe_proxy']:.2f}"
    print(f"{'Sharpe Proxy':<25} {sharpe_a:<20} {sharpe_b:<20}")

    slip_a = f"{m_a['slippage_pct_of_pnl']:.1f}%"
    slip_b = f"{m_b['slippage_pct_of_pnl']:.1f}%"
    print(f"{'Slippage % of P&L':<25} {slip_a:<20} {slip_b:<20}")

    print("\n" + "-" * 65)

    # Determine winner
    if m_a["expectancy_r"] > m_b["expectancy_r"] and m_a["expectancy_r"] > 0:
        if m_a["max_consecutive_losses"] <= 15 and m_a["slippage_pct_of_pnl"] < 50:
            winner = "CONFIG A: AGGRESSIVE SNIPER"
            reason = "Higher expectancy with manageable risk"
        else:
            winner = "CONFIG B: BALANCED APPROACH"
            reason = "Sniper has too much psychological/slippage risk"
    elif m_b["expectancy_r"] > 0:
        winner = "CONFIG B: BALANCED APPROACH"
        reason = "More stable expectancy"
    else:
        winner = "NEITHER"
        reason = "Both configurations unprofitable after slippage"

    print(f"\nRECOMMENDED: {winner}")
    print(f"REASON: {reason}")

    print("\n" + "=" * 70)
    print("DEPLOYMENT GUIDANCE")
    print("=" * 70)

    if m_a["expectancy_r"] > 0 or m_b["expectancy_r"] > 0:
        best = m_a if m_a["expectancy_r"] > m_b["expectancy_r"] else m_b
        print(f"\n1. Use {best['config_name'].split(':')[1].strip()} configuration")
        print(f"2. Expect {best['hit_rate']:.0%} win rate - NORMAL to lose often")
        print(
            f"3. Prepare for up to {best['max_consecutive_losses']} consecutive losses"
        )
        print(f"4. Net expectancy: {best['expectancy_r']:.3f}R per trade")
        print(f"5. Slippage costs {best['slippage_pct_of_pnl']:.1f}% of your edge")
    else:
        print("\nWARNING: Strategy not profitable after slippage costs!")
        print("Consider: Reducing trade frequency or finding lower-cost execution")

    return 0


if __name__ == "__main__":
    sys.exit(main())
