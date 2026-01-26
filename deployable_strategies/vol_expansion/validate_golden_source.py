"""
Golden Source Validation - Isolate Feature Calculation vs Exit Logic

PURPOSE: Determine if the performance gap is due to:
1. Feature Calculation Mismatch (our recalculation doesn't match research)
2. Exit Logic Error (target/stop implementation is broken)

METHOD: Use the PRE-COMPUTED research features directly (SPY_features.parquet)
and apply the exact same entry thresholds and exit logic.

EXPECTED RESULTS:
- If Hit Rate ~57.9%: Feature calculation is the issue, exit logic is correct
- If Hit Rate ~35%: Exit logic is broken, need to investigate target/stop

Author: Magellan Testing Framework
Date: January 25, 2026
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


class GoldenSourceValidator:
    """
    Validate strategy using pre-computed research features (golden source).

    This isolates the exit logic from feature calculation to diagnose
    where the performance gap originates.
    """

    def __init__(self):
        # Load research thresholds
        results_path = (
            project_root
            / "research"
            / "blind_backwards_analysis"
            / "outputs"
            / "FINAL_STRATEGY_RESULTS.json"
        )
        with open(results_path) as f:
            self.research_thresholds = json.load(f)

        print("✓ Loaded research thresholds")

    def load_golden_source(self, symbol: str) -> pd.DataFrame:
        """Load pre-computed research features (the golden source)."""
        features_path = (
            project_root
            / "research"
            / "blind_backwards_analysis"
            / "outputs"
            / f"{symbol}_features.parquet"
        )

        if not features_path.exists():
            raise FileNotFoundError(f"Golden source not found: {features_path}")

        df = pd.read_parquet(features_path)
        print(f"✓ Loaded golden source for {symbol}: {len(df):,} bars")
        print(f"  Columns: {list(df.columns)[:10]}...")

        return df

    def load_price_data(self, symbol: str) -> pd.DataFrame:
        """Load raw OHLCV price data."""
        data_path = project_root / "data" / "cache" / "equities"
        files = sorted(
            data_path.glob(f"{symbol}_1min_202*.parquet"),
            key=lambda x: x.stat().st_size,
            reverse=True,
        )

        if not files:
            raise FileNotFoundError(f"No price data found for {symbol}")

        df = pd.read_parquet(files[0])
        print(f"✓ Loaded price data for {symbol}: {len(df):,} bars")

        return df

    def merge_data(self, features: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
        """Merge golden source features with raw price data."""
        print(f"  Features: {len(features):,} bars")
        print(f"  Prices: {len(prices):,} bars")

        # Simple pandas join (memory efficient)
        merged = features.join(
            prices[["open", "high", "low", "close", "volume"]], how="inner"
        )
        print(f"  Merged: {len(merged):,} bars")

        return merged

    def calculate_atr(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculate proper ATR using True Range."""
        tr1 = df["high"] - df["low"]
        tr2 = (df["high"] - df["close"].shift(1)).abs()
        tr3 = (df["low"] - df["close"].shift(1)).abs()

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(period).mean()

        return atr

    def get_thresholds(self, symbol: str) -> dict:
        """Get entry thresholds from research results."""
        research = self.research_thresholds[symbol]
        thresholds = {}

        for feature_data in research["feature_profile"]:
            feat = feature_data["feature"]
            thresholds[feat] = {
                "value": feature_data["threshold"],
                "direction": feature_data["direction"],
            }

        return thresholds

    def check_entry(self, row: pd.Series, thresholds: dict) -> bool:
        """Check if row meets all entry conditions."""
        for feat_name, threshold_data in thresholds.items():
            value = row.get(feat_name, None)

            if value is None or pd.isna(value):
                return False

            threshold = threshold_data["value"]
            direction = threshold_data["direction"]

            if direction == "<":
                if not (value < threshold):
                    return False
            elif direction == ">":
                if not (value > threshold):
                    return False

        return True

    def run_backtest(self, symbol: str, df: pd.DataFrame) -> list:
        """Run backtest using golden source features."""
        print(f"\n{'='*70}")
        print(f"GOLDEN SOURCE BACKTEST: {symbol}")
        print(f"{'='*70}")

        # Calculate ATR directly (memory efficient - no copy)
        tr1 = df["high"] - df["low"]
        tr2 = (df["high"] - df["close"].shift(1)).abs()
        tr3 = (df["low"] - df["close"].shift(1)).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr_series = true_range.rolling(20).mean()

        # Filter to valid ATR bars
        valid_mask = ~atr_series.isna()
        df = df.loc[valid_mask]
        atr_series = atr_series.loc[valid_mask]
        print(f"Bars after ATR warmup: {len(df):,}")

        # Get thresholds
        thresholds = self.get_thresholds(symbol)
        print(f"Entry thresholds: {thresholds}")

        # Check how many bars pass each condition
        print("\nFeature statistics in golden source:")
        for feat_name, threshold_data in thresholds.items():
            if feat_name in df.columns:
                values = df[feat_name]
                threshold = threshold_data["value"]
                direction = threshold_data["direction"]

                if direction == "<":
                    passing = (values < threshold).sum()
                else:
                    passing = (values > threshold).sum()

                pct = passing / len(df) * 100
                print(
                    f"  {feat_name}: mean={values.mean():.4f}, "
                    f"threshold={threshold:.4f} ({direction}), "
                    f"passing={passing:,} ({pct:.1f}%)"
                )
            else:
                print(f"  {feat_name}: NOT FOUND IN GOLDEN SOURCE!")

        # Run backtest
        position = None
        trades = []
        signals = 0

        # Exit parameters
        target_mult = 2.5
        stop_mult = 1.25
        max_hold_bars = 30

        for idx in range(len(df)):
            row = df.iloc[idx]
            atr = atr_series.iloc[idx]

            if position is None:
                # Check entry
                if self.check_entry(row, thresholds):
                    signals += 1

                    position = {
                        "entry_idx": idx,
                        "entry_time": df.index[idx],
                        "entry_price": row["close"],
                        "target": row["close"] + (target_mult * atr),
                        "stop": row["close"] - (stop_mult * atr),
                        "atr": atr,
                        "highest": row["close"],
                    }
            else:
                # Manage position
                if row["high"] > position["highest"]:
                    position["highest"] = row["high"]

                exit_signal = False
                exit_reason = None
                exit_price = None

                # Check stop loss
                if row["low"] <= position["stop"]:
                    exit_signal = True
                    exit_reason = "STOP_LOSS"
                    exit_price = position["stop"]

                # Check target
                elif row["high"] >= position["target"]:
                    exit_signal = True
                    exit_reason = "TARGET_HIT"
                    exit_price = position["target"]

                # Check time stop
                elif idx - position["entry_idx"] >= max_hold_bars:
                    exit_signal = True
                    exit_reason = "TIME_STOP"
                    exit_price = row["close"]

                if exit_signal:
                    pnl_dollars = exit_price - position["entry_price"]
                    risk = position["entry_price"] - position["stop"]
                    pnl_r = pnl_dollars / risk if risk > 0 else 0

                    trade = {
                        "entry_time": position["entry_time"],
                        "exit_time": df.index[idx],
                        "entry_price": position["entry_price"],
                        "exit_price": exit_price,
                        "pnl_r": pnl_r,
                        "is_win": pnl_dollars > 0,
                        "exit_reason": exit_reason,
                    }
                    trades.append(trade)
                    position = None

        # Close any remaining position
        if position is not None:
            row = df.iloc[-1]
            pnl_dollars = row["close"] - position["entry_price"]
            risk = position["entry_price"] - position["stop"]
            pnl_r = pnl_dollars / risk if risk > 0 else 0

            trades.append(
                {
                    "entry_time": position["entry_time"],
                    "exit_time": df.index[-1],
                    "entry_price": position["entry_price"],
                    "exit_price": row["close"],
                    "pnl_r": pnl_r,
                    "is_win": pnl_dollars > 0,
                    "exit_reason": "END_OF_DATA",
                }
            )

        # Calculate signal frequency
        signal_freq = signals / len(df)
        expected_freq = self.research_thresholds[symbol]["signal_frequency"]
        print(f"\nSignal frequency: {signal_freq:.1%} (Research: {expected_freq:.1%})")

        return trades

    def analyze_results(self, trades: list, symbol: str):
        """Analyze backtest results."""
        if not trades:
            print(f"\n⚠️ WARNING: No trades for {symbol}")
            return None

        df_trades = pd.DataFrame(trades)

        total_trades = len(df_trades)
        wins = df_trades["is_win"].sum()
        hit_rate = wins / total_trades

        avg_win = df_trades[df_trades["is_win"]]["pnl_r"].mean() if wins > 0 else 0
        avg_loss = (
            df_trades[~df_trades["is_win"]]["pnl_r"].mean()
            if (total_trades - wins) > 0
            else 0
        )
        expectancy = (hit_rate * avg_win) + ((1 - hit_rate) * avg_loss)

        print(f"\n{'='*70}")
        print(f"GOLDEN SOURCE RESULTS: {symbol}")
        print(f"{'='*70}")
        print(f"Total Trades:     {total_trades}")
        print(f"Wins:             {wins} ({hit_rate:.1%})")
        print(f"Avg Win:          {avg_win:.3f}R")
        print(f"Avg Loss:         {avg_loss:.3f}R")
        print(f"Expectancy:       {expectancy:.3f}R")

        # Compare to research
        research = self.research_thresholds[symbol]
        expected_hr = research["hit_rate"]
        expected_exp = research["expectancy"]

        hr_diff = (hit_rate - expected_hr) * 100
        exp_diff = expectancy - expected_exp

        print(f"\n{'Research Comparison':-^70}")
        print(f"Expected Hit Rate:   {expected_hr:.1%}")
        print(f"Actual Hit Rate:     {hit_rate:.1%} ({hr_diff:+.1f}pp)")
        print(f"Expected Expectancy: {expected_exp:.3f}R")
        print(f"Actual Expectancy:   {expectancy:.3f}R ({exp_diff:+.3f}R)")

        # Exit reason breakdown
        print(f"\n{'Exit Reasons':-^70}")
        exit_counts = df_trades["exit_reason"].value_counts()
        for reason, count in exit_counts.items():
            pct = (count / total_trades) * 100
            reason_trades = df_trades[df_trades["exit_reason"] == reason]
            reason_hr = reason_trades["is_win"].mean() if len(reason_trades) > 0 else 0
            print(f"{reason:15s}: {count:5d} ({pct:5.1f}%) | Win Rate: {reason_hr:.1%}")

        # Verdict
        print(f"\n{'DIAGNOSIS':-^70}")
        if abs(hr_diff) < 5:
            print("✅ GOLDEN SOURCE VALIDATES!")
            print("   Hit rate matches research → Feature calculation is the problem")
            print("   → Copy feature_engine.py logic exactly to production")
        else:
            print("❌ GOLDEN SOURCE FAILS!")
            print("   Hit rate still off → Exit logic may be broken")
            print("   → Investigate target/stop implementation")

        return {
            "symbol": symbol,
            "total_trades": total_trades,
            "hit_rate": hit_rate,
            "expectancy": expectancy,
            "expected_hr": expected_hr,
            "diff_pp": hr_diff,
        }


def main():
    """Run golden source validation."""
    print("=" * 70)
    print("GOLDEN SOURCE VALIDATION")
    print("Purpose: Isolate Feature Calculation vs Exit Logic")
    print("=" * 70)

    validator = GoldenSourceValidator()
    results = {}

    # Only test SPY first (simplest case, no autocorr requirement)
    for symbol in ["SPY"]:
        try:
            # Load golden source features
            features = validator.load_golden_source(symbol)

            # Load price data
            prices = validator.load_price_data(symbol)

            # Merge
            merged = validator.merge_data(features, prices)

            # Run backtest
            trades = validator.run_backtest(symbol, merged)

            # Analyze
            result = validator.analyze_results(trades, symbol)
            if result:
                results[symbol] = result

        except Exception as e:
            print(f"\n❌ ERROR testing {symbol}: {e}")
            import traceback

            traceback.print_exc()

    # Final summary
    print(f"\n\n{'='*70}")
    print("FINAL VERDICT")
    print(f"{'='*70}")

    for symbol, result in results.items():
        if abs(result["diff_pp"]) < 5:
            print(
                f"✅ {symbol}: Hit rate {result['hit_rate']:.1%} matches research ({result['expected_hr']:.1%})"
            )
            print(f"   → FEATURE CALCULATION is the root cause")
        else:
            print(
                f"❌ {symbol}: Hit rate {result['hit_rate']:.1%} ≠ research ({result['expected_hr']:.1%})"
            )
            print(f"   → EXIT LOGIC may be broken")

    return 0


if __name__ == "__main__":
    sys.exit(main())
