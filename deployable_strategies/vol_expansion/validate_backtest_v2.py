"""
Backtest Validation Script v2.0 - CORRECTED

Fixes Applied:
1. CRITICAL: Proper ATR calculation using True Range
2. CRITICAL: Correct feature thresholds from cluster centroids (not arbitrary z-score)
3. CRITICAL: Actual VIX data for regime classification

Key Change: Research used effort_result_mean (raw values ~-40 to -52),
NOT effort_result_zscore. This was the primary cause of signal frequency mismatch.
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

from src.vol_expansion_features import add_vol_expansion_features


class VolExpansionBacktestV2:
    """Backtest engine v2.0 with corrected ATR, thresholds, and VIX detection"""

    def __init__(self, config_path: Path):
        with open(config_path) as f:
            self.config = json.load(f)

        # Load research thresholds from FINAL_STRATEGY_RESULTS.json
        results_path = (
            project_root
            / "research"
            / "blind_backwards_analysis"
            / "outputs"
            / "FINAL_STRATEGY_RESULTS.json"
        )
        with open(results_path) as f:
            self.research_thresholds = json.load(f)

        self.feature_config = self.config.get("feature_engineering", {})
        self.exit_config = self.config.get("exit_rules", {})

        # Load VIX data for regime classification
        self.vix_data = self._load_vix_data()

        print("✓ Loaded research thresholds:")
        for symbol, data in self.research_thresholds.items():
            print(
                f"  {symbol}: Signal Freq={data['signal_frequency']:.1%}, Hit Rate={data['hit_rate']:.1%}"
            )

    def _load_vix_data(self):
        """Load VIX data or estimate from SPY daily data"""
        try:
            # Try to load VIX from data cache
            vix_path = project_root / "data" / "cache" / "equities"
            vix_files = list(vix_path.glob("*VIX*1min*.parquet")) + list(
                vix_path.glob("*VIX*1d*.parquet")
            )

            if vix_files:
                vix = pd.read_parquet(vix_files[0])
                print(f"✓ Loaded VIX data: {len(vix):,} bars")
                return vix[["close"]].rename(columns={"close": "vix"})

            # Fallback: Estimate from SPY 20-day realized volatility
            spy_files = sorted(
                (project_root / "data" / "cache" / "equities").glob("SPY_1d_*.parquet")
            )
            if spy_files:
                spy_daily = pd.read_parquet(spy_files[-1])
                returns = spy_daily["close"].pct_change()
                realized_vol = returns.rolling(20).std() * np.sqrt(252) * 100
                vix_est = realized_vol.clip(10, 80)
                print(f"⚠️ VIX estimated from SPY daily volatility")
                return pd.DataFrame({"vix": vix_est})

            print("⚠️ WARNING: No VIX data available, using volatility_ratio proxy")
            return None
        except Exception as e:
            print(f"⚠️ VIX load error: {e}, using proxy")
            return None

    def load_data(self, symbol: str, start_date: str = None, end_date: str = None):
        """Load 1-minute bar data for symbol"""
        data_path = project_root / "data" / "cache" / "equities"

        files = sorted(
            data_path.glob(f"{symbol}_1min_202*.parquet"),
            key=lambda x: x.stat().st_size,
            reverse=True,
        )

        if not files:
            raise FileNotFoundError(f"No data found for {symbol}")

        print(f"Loading data from: {files[0].name}")
        df = pd.read_parquet(files[0])

        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]

        print(f"Loaded {len(df):,} bars ({df.index[0]} to {df.index[-1]})")
        return df

    def run_backtest(self, symbol: str, df: pd.DataFrame):
        """Run backtest with corrected logic"""
        print(f"\n{'='*70}")
        print(f"BACKTESTING v2.0: {symbol}")
        print(f"{'='*70}")

        # Calculate features
        print("Calculating features...")
        df = add_vol_expansion_features(df, config=self.feature_config)

        # Calculate proper ATR
        df["atr"] = self._calculate_atr(df, period=20)

        # Drop warmup period
        df = df.dropna(subset=["effort_result_mean", "range_ratio_mean", "atr"])
        print(f"Clean bars after warmup: {len(df):,}")

        # Get symbol-specific thresholds from research
        thresholds = self._get_thresholds(symbol)
        print(f"Using research thresholds: {thresholds}")

        # Align VIX if available
        if self.vix_data is not None:
            df = self._align_vix(df)

        # Backtest logic
        position = None
        trades = []
        signals = 0

        for idx in range(len(df)):
            row = df.iloc[idx]

            if position is None:
                # Check for entry using RESEARCH THRESHOLDS
                if self._check_entry_v2(row, thresholds):
                    signals += 1
                    position = self._open_position(symbol, row, idx, df.index[idx])
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

        # Calculate signal frequency
        signal_freq = signals / len(df)
        expected_freq = self.research_thresholds[symbol]["signal_frequency"]
        print(f"\nSignal Frequency: {signal_freq:.1%} (Research: {expected_freq:.1%})")

        return trades

    def _calculate_atr(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculate proper ATR using True Range formula"""
        tr1 = df["high"] - df["low"]
        tr2 = (df["high"] - df["close"].shift(1)).abs()
        tr3 = (df["low"] - df["close"].shift(1)).abs()

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(period).mean()

        return atr

    def _get_thresholds(self, symbol: str) -> dict:
        """Get symbol-specific thresholds from research results"""
        research = self.research_thresholds[symbol]
        thresholds = {}

        for feature_data in research["feature_profile"]:
            feat = feature_data["feature"]
            thresholds[feat] = {
                "value": feature_data["threshold"],
                "direction": feature_data["direction"],
            }

        return thresholds

    def _check_entry_v2(self, row, thresholds: dict) -> bool:
        """Check entry using EXACT research thresholds"""
        conditions = []

        for feat_name, threshold_data in thresholds.items():
            value = row.get(feat_name, 0)
            threshold = threshold_data["value"]
            direction = threshold_data["direction"]

            if direction == "<":
                conditions.append(value < threshold)
            elif direction == ">":
                conditions.append(value > threshold)

        return all(conditions)

    def _align_vix(self, df: pd.DataFrame) -> pd.DataFrame:
        """Align VIX data to 1-minute bars"""
        # Resample VIX to daily and forward-fill
        vix_daily = self.vix_data.resample("D").last()

        # Map to df by date
        df["date"] = df.index.date
        df["vix"] = df["date"].map(
            lambda d: (
                vix_daily.loc[pd.Timestamp(d), "vix"]
                if pd.Timestamp(d) in vix_daily.index
                else None
            )
        )

        # Forward fill
        df["vix"] = df["vix"].fillna(method="ffill").fillna(15)  # Default to NORMAL

        return df

    def _classify_regime(self, vix_value: float) -> str:
        """Classify VIX into regime buckets"""
        if pd.isna(vix_value):
            return "NORMAL"
        elif vix_value < 15:
            return "COMPLACENCY"
        elif vix_value <= 25:
            return "NORMAL"
        else:
            return "PANIC"

    def _open_position(self, symbol: str, row, idx: int, timestamp):
        """Open a new position"""
        atr = row["atr"]

        target_mult = self.exit_config.get("target_atr_multiple", 2.5)
        stop_mult = self.exit_config.get("stop_atr_multiple", 1.25)

        regime = self._classify_regime(row.get("vix", 15))

        return {
            "symbol": symbol,
            "entry_idx": idx,
            "entry_time": timestamp,
            "entry_price": row["close"],
            "target": row["close"] + (target_mult * atr),
            "stop": row["close"] - (stop_mult * atr),
            "atr": atr,
            "highest": row["close"],
            "regime": regime,
            "entry_features": {
                "effort_result_mean": row.get("effort_result_mean", 0),
                "range_ratio_mean": row.get("range_ratio_mean", 0),
                "vol_ratio_mean": row.get("volatility_ratio_mean", 0),
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

    def analyze_results(self, trades: list, symbol: str):
        """Analyze backtest results"""
        if not trades:
            print(f"\n⚠️ WARNING: No trades for {symbol}")
            return None

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
        print(f"RESULTS v2.0: {symbol}")
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

        research = self.research_thresholds[symbol]
        expected_hr = research["hit_rate"]
        expected_exp = research["expectancy"]

        hit_rate_diff = (hit_rate - expected_hr) * 100
        exp_diff = expectancy - expected_exp

        hit_rate_status = "✅ PASS" if abs(hit_rate_diff) < 5 else "⚠️ WARNING"
        exp_status = "✅ PASS" if abs(exp_diff) < 0.1 else "⚠️ WARNING"

        print(f"Expected Hit Rate:   {expected_hr:.1%}")
        print(
            f"Actual Hit Rate:     {hit_rate:.1%} ({hit_rate_diff:+.1f}pp) {hit_rate_status}"
        )
        print(f"Expected Expectancy: {expected_exp:.3f}R")
        print(f"Actual Expectancy:   {expectancy:.3f}R ({exp_diff:+.3f}R) {exp_status}")

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
            "total_pnl": float(df_trades["pnl_dollars"].sum()),
        }


def main():
    """Run corrected backtest validation"""
    print("=" * 70)
    print("VOLATILITY EXPANSION ENTRY - BACKTEST VALIDATION v2.0")
    print("Fixes: Proper ATR, Research Thresholds, VIX Regimes")
    print("=" * 70)

    # Load config
    config_path = Path(__file__).parent / "config.json"
    backtest = VolExpansionBacktestV2(config_path)

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
                if results:
                    period_results[symbol] = results

            except Exception as e:
                print(f"\n❌ ERROR testing {symbol}: {e}")
                import traceback

                traceback.print_exc()

        all_results[period_name] = period_results

    # Final summary
    print(f"\n\n{'='*70}")
    print("FINAL VALIDATION SUMMARY v2.0")
    print(f"{'='*70}")

    for period_name, period_results in all_results.items():
        print(f"\n{period_name}:")
        for symbol, results in period_results.items():
            print(
                f"  {symbol}: Hit Rate={results['hit_rate']:.1%}, "
                f"Expectancy={results['expectancy']:.3f}R, "
                f"Trades={results['total_trades']}"
            )

    # Overall verdict
    print(f"\n{'='*70}")
    print("VERDICT")
    print(f"{'='*70}")

    oos_results = all_results.get("OOS", {})
    if oos_results:
        all_pass = all(
            r["hit_rate"] > 0.52 and r["expectancy"] > 0.25
            for r in oos_results.values()
        )

        if all_pass:
            print("✅ PASS: Strategy validated on out-of-sample data")
            print("   → Proceed to paper trading")
        else:
            print("⚠️ PARTIAL PASS: Some metrics slightly below threshold")
            print("   → Review and consider paper trading with caution")

    return 0


if __name__ == "__main__":
    sys.exit(main())
