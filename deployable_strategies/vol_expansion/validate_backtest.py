"""
Backtest Validation Script - Volatility Expansion Entry Strategy

Validates strategy implementation against research results:
- Expected hit rate: 55-58%
- Expected expectancy: 0.3-0.4R
- Signal frequency: 20-26%

Tests on full dataset (2022-2026) and OOS period (2025-2026)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.vol_expansion_features import (
    add_vol_expansion_features,
    check_vol_expansion_entry,
)


class VolExpansionBacktest:
    """Backtest engine for Volatility Expansion Entry strategy"""

    def __init__(self, config_path: Path):
        with open(config_path) as f:
            self.config = json.load(f)

        self.entry_config = self.config.get("entry_conditions", {})
        self.exit_config = self.config.get("exit_rules", {})
        self.feature_config = self.config.get("feature_engineering", {})

        self.results = {
            "trades": [],
            "daily_stats": [],
            "regime_stats": {"COMPLACENCY": [], "NORMAL": [], "PANIC": []},
        }

    def load_data(self, symbol: str, start_date: str = None, end_date: str = None):
        """Load 1-minute bar data for symbol"""
        data_path = project_root / "data" / "cache" / "equities"

        # Find the most recent data file
        files = sorted(
            data_path.glob(f"{symbol}_1min_202*.parquet"),
            key=lambda x: x.stat().st_size,
            reverse=True,
        )

        if not files:
            raise FileNotFoundError(f"No data found for {symbol}")

        print(f"Loading data from: {files[0].name}")
        df = pd.read_parquet(files[0])

        # Filter by date range
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]

        print(f"Loaded {len(df):,} bars for {symbol} ({df.index[0]} to {df.index[-1]})")
        return df

    def run_backtest(self, symbol: str, df: pd.DataFrame):
        """Run backtest on dataframe"""
        print(f"\n{'='*70}")
        print(f"BACKTESTING: {symbol}")
        print(f"{'='*70}")

        # Calculate features
        print("Calculating features...")
        df = add_vol_expansion_features(df, config=self.feature_config)

        # Drop warmup period (NaN features)
        df = df.dropna(subset=["effort_result_zscore", "range_ratio_mean"])
        print(f"Clean bars after warmup: {len(df):,}")

        # Backtest logic
        position = None
        trades = []

        for idx in range(len(df)):
            row = df.iloc[idx]

            if position is None:
                # Check for entry
                if check_vol_expansion_entry(row, config=self.entry_config):
                    position = self._open_position(symbol, row, idx)
            else:
                # Manage position
                exit_signal, exit_reason = self._check_exit(position, row, idx)
                if exit_signal:
                    trade = self._close_position(position, row, exit_reason)
                    trades.append(trade)
                    position = None

        # Close any remaining position
        if position is not None:
            trade = self._close_position(position, df.iloc[-1], "END_OF_DATA")
            trades.append(trade)

        return trades

    def _open_position(self, symbol: str, row, idx: int):
        """Open a new position"""
        # Calculate ATR
        atr = row.get("volatility_ratio", 1.0) * 0.5  # Approximate ATR from data

        target_mult = self.exit_config.get("target_atr_multiple", 2.5)
        stop_mult = self.exit_config.get("stop_atr_multiple", 1.25)

        return {
            "symbol": symbol,
            "entry_idx": idx,
            "entry_time": row.name,
            "entry_price": row["close"],
            "target": row["close"] + (target_mult * atr),
            "stop": row["close"] - (stop_mult * atr),
            "highest": row["close"],
            "regime": self._estimate_regime(row.get("volatility_ratio_mean", 1.0)),
            "entry_features": {
                "er_zscore": row.get("effort_result_zscore", 0),
                "range_ratio": row.get("range_ratio_mean", 0),
                "vol_ratio": row.get("volatility_ratio_mean", 0),
            },
        }

    def _check_exit(self, position, row, idx: int):
        """Check if position should be exited"""
        # Update highest
        if row["high"] > position["highest"]:
            position["highest"] = row["high"]

        # Stop loss
        if row["low"] <= position["stop"]:
            return True, "STOP_LOSS"

        # Target hit
        if row["high"] >= position["target"]:
            return True, "TARGET_HIT"

        # Time exit (30 bars)
        max_bars = self.exit_config.get("max_hold_bars", 30)
        if idx - position["entry_idx"] >= max_bars:
            return True, "TIME_STOP"

        return False, None

    def _close_position(self, position, row, reason: str):
        """Close position and record trade"""
        if reason == "STOP_LOSS":
            exit_price = position["stop"]
        elif reason == "TARGET_HIT":
            exit_price = position["target"]
        else:
            exit_price = row["close"]

        pnl_dollars = exit_price - position["entry_price"]
        pnl_percent = (pnl_dollars / position["entry_price"]) * 100
        risk = position["entry_price"] - position["stop"]
        pnl_r = pnl_dollars / risk if risk > 0 else 0

        is_win = pnl_dollars > 0

        trade = {
            "symbol": position["symbol"],
            "entry_time": position["entry_time"],
            "exit_time": row.name,
            "entry_price": position["entry_price"],
            "exit_price": exit_price,
            "pnl_dollars": pnl_dollars,
            "pnl_percent": pnl_percent,
            "pnl_r": pnl_r,
            "is_win": is_win,
            "exit_reason": reason,
            "regime": position["regime"],
            "mfe": position["highest"] - position["entry_price"],
            "entry_features": position["entry_features"],
        }

        return trade

    def _estimate_regime(self, vol_ratio: float) -> str:
        """Estimate VIX regime from volatility ratio"""
        if vol_ratio > 1.3:
            return "PANIC"
        elif vol_ratio > 0.9:
            return "NORMAL"
        else:
            return "COMPLACENCY"

    def analyze_results(self, trades: list, symbol: str):
        """Analyze backtest results"""
        if not trades:
            print(f"\n⚠️ WARNING: No trades for {symbol}")
            return

        df_trades = pd.DataFrame(trades)

        # Overall statistics
        total_trades = len(df_trades)
        wins = df_trades["is_win"].sum()
        losses = total_trades - wins
        hit_rate = wins / total_trades if total_trades > 0 else 0

        avg_win = df_trades[df_trades["is_win"]]["pnl_r"].mean() if wins > 0 else 0
        avg_loss = df_trades[~df_trades["is_win"]]["pnl_r"].mean() if losses > 0 else 0
        expectancy = (hit_rate * avg_win) + ((1 - hit_rate) * avg_loss)

        print(f"\n{'='*70}")
        print(f"RESULTS: {symbol}")
        print(f"{'='*70}")
        print(f"Total Trades:     {total_trades}")
        print(f"Wins:             {wins} ({hit_rate:.1%})")
        print(f"Losses:           {losses} ({(1-hit_rate):.1%})")
        print(f"Avg Win:          {avg_win:.3f}R")
        print(f"Avg Loss:         {avg_loss:.3f}R")
        print(f"Expectancy:       {expectancy:.3f}R")
        print(f"Total P&L:        ${df_trades['pnl_dollars'].sum():.2f}")

        # Regime breakdown
        print(f"\n{'Regime Performance':-^70}")
        for regime in ["COMPLACENCY", "NORMAL", "PANIC"]:
            regime_trades = df_trades[df_trades["regime"] == regime]
            if len(regime_trades) > 0:
                regime_wins = regime_trades["is_win"].sum()
                regime_hit_rate = regime_wins / len(regime_trades)
                regime_exp = regime_trades["pnl_r"].mean()
                print(
                    f"{regime:15s}: {len(regime_trades):3d} trades | "
                    f"Hit Rate: {regime_hit_rate:.1%} | Expectancy: {regime_exp:.3f}R"
                )

        # Validation against research
        print(f"\n{'Research Validation':-^70}")

        research_metrics = {
            "SPY": {"hit_rate": 0.579, "expectancy": 0.368},
            "QQQ": {"hit_rate": 0.570, "expectancy": 0.355},
            "IWM": {"hit_rate": 0.550, "expectancy": 0.326},
        }

        if symbol in research_metrics:
            expected = research_metrics[symbol]
            hit_rate_diff = (hit_rate - expected["hit_rate"]) * 100
            exp_diff = expectancy - expected["expectancy"]

            hit_rate_status = "✅ PASS" if abs(hit_rate_diff) < 5 else "⚠️ WARNING"
            exp_status = "✅ PASS" if abs(exp_diff) < 0.1 else "⚠️ WARNING"

            print(f"Expected Hit Rate:   {expected['hit_rate']:.1%}")
            print(
                f"Actual Hit Rate:     {hit_rate:.1%} ({hit_rate_diff:+.1f}pp) {hit_rate_status}"
            )
            print(f"Expected Expectancy: {expected['expectancy']:.3f}R")
            print(
                f"Actual Expectancy:   {expectancy:.3f}R ({exp_diff:+.3f}R) {exp_status}"
            )

        # Exit reason breakdown
        print(f"\n{'Exit Reasons':-^70}")
        exit_counts = df_trades["exit_reason"].value_counts()
        for reason, count in exit_counts.items():
            pct = (count / total_trades) * 100
            print(f"{reason:15s}: {count:3d} ({pct:5.1f}%)")

        return {
            "symbol": symbol,
            "total_trades": total_trades,
            "hit_rate": hit_rate,
            "expectancy": expectancy,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "total_pnl": df_trades["pnl_dollars"].sum(),
            "regime_breakdown": df_trades.groupby("regime")
            .agg({"is_win": ["count", "sum", "mean"], "pnl_r": "mean"})
            .to_dict(),
        }


def main():
    """Run backtest validation"""
    print("=" * 70)
    print("VOLATILITY EXPANSION ENTRY - BACKTEST VALIDATION")
    print("=" * 70)

    # Load config
    config_path = Path(__file__).parent / "config.json"
    backtest = VolExpansionBacktest(config_path)

    # Test periods
    test_periods = {
        "FULL": {
            "start": "2022-01-01",
            "end": "2026-01-24",
            "description": "Full Dataset (In-Sample)",
        },
        "OOS": {
            "start": "2025-01-01",
            "end": "2026-01-24",
            "description": "Out-of-Sample (Walk-Forward)",
        },
    }

    all_results = {}

    for period_name, period_config in test_periods.items():
        print(f"\n\n{'#'*70}")
        print(f"# TEST PERIOD: {period_config['description']}")
        print(f"# {period_config['start']} to {period_config['end']}")
        print(f"{'#'*70}")

        period_results = {}

        for symbol in ["SPY", "QQQ", "IWM"]:
            try:
                # Load data
                df = backtest.load_data(
                    symbol,
                    start_date=period_config["start"],
                    end_date=period_config["end"],
                )

                # Run backtest
                trades = backtest.run_backtest(symbol, df)

                # Analyze
                results = backtest.analyze_results(trades, symbol)
                period_results[symbol] = results

            except Exception as e:
                print(f"\n❌ ERROR testing {symbol}: {e}")
                import traceback

                traceback.print_exc()

        all_results[period_name] = period_results

    # Final summary
    print(f"\n\n{'='*70}")
    print("FINAL VALIDATION SUMMARY")
    print(f"{'='*70}")

    for period_name, period_results in all_results.items():
        print(f"\n{period_name}:")
        for symbol, results in period_results.items():
            print(
                f"  {symbol}: Hit Rate={results['hit_rate']:.1%}, "
                f"Expectancy={results['expectancy']:.3f}R, "
                f"Trades={results['total_trades']}"
            )

    # Save results
    results_file = Path(__file__).parent / "backtest_results.json"
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\n✓ Results saved to: {results_file}")

    # Overall verdict
    print(f"\n{'='*70}")
    print("VERDICT")
    print(f"{'='*70}")

    oos_results = all_results.get("OOS", {})
    if oos_results:
        all_pass = all(
            r["hit_rate"] > 0.50 and r["expectancy"] > 0.20
            for r in oos_results.values()
        )

        if all_pass:
            print("✅ PASS: Strategy validated on out-of-sample data")
            print("   → Proceed to paper trading")
        else:
            print("⚠️ WARNING: Some metrics below threshold")
            print("   → Review feature calculations and parameters")

    return 0


if __name__ == "__main__":
    sys.exit(main())
