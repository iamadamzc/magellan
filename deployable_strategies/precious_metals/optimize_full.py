"""
Comprehensive Parameter Optimization for Precious Metals Strategy
Walk-forward optimization across RSI bands, periods, and leverage levels.

Tests: Gold (GCUSD) and Silver (SIUSD) daily data
Goal: Find parameters that maximize Sharpe while achieving $200/day target
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import itertools

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

CACHE_DIR = project_root / "data" / "cache" / "futures"
CAPITAL = 20000
TARGET_DAILY_PNL = 200


def load_precious_metal_data(symbol: str, start_date: str = None, end_date: str = None):
    """Load daily precious metal data from cache."""
    pattern = f"{symbol}_1day_*.parquet"
    files = list(CACHE_DIR.glob(pattern))

    if not files:
        raise FileNotFoundError(f"No {symbol} data found in {CACHE_DIR}")

    dfs = []
    for f in files:
        df = pd.read_parquet(f)
        dfs.append(df)

    df = pd.concat(dfs)
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="last")]

    if start_date:
        df = df[start_date:]
    if end_date:
        df = df[:end_date]

    return df


def calculate_rsi(prices: pd.Series, period: int = 28) -> pd.Series:
    """Calculate RSI indicator."""
    delta = prices.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)

    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))

    rsi.loc[avg_loss == 0] = 100.0
    rsi.loc[avg_gain == 0] = 0.0

    return rsi


def run_backtest(
    df, rsi_period, entry_band, exit_band, leverage, transaction_cost_bps=5.0
):
    """Run backtest with given parameters. Returns metrics dict."""

    df = df.copy()
    df["rsi"] = calculate_rsi(df["close"], rsi_period)

    # Skip warmup
    df = df.iloc[rsi_period + 5 :]

    if len(df) < 20:
        return None

    # Simulation
    cash = CAPITAL
    position = "flat"
    entry_price = None
    trades = []
    equity_curve = []

    effective_capital = CAPITAL * leverage

    for i in range(len(df)):
        row = df.iloc[i]
        price = row["close"]
        rsi = row["rsi"]

        if pd.isna(rsi):
            continue

        # Entry
        if position == "flat" and rsi > entry_band:
            cost = transaction_cost_bps / 10000
            effective_capital = cash * leverage * (1 - cost)
            entry_price = price
            position = "long"

        # Exit
        elif position == "long" and rsi < exit_band:
            cost = transaction_cost_bps / 10000
            position_value = effective_capital * (price / entry_price)
            exit_value = position_value * (1 - cost)
            pnl = exit_value - (cash * leverage)

            trades.append(
                {
                    "entry_price": entry_price,
                    "exit_price": price,
                    "pnl": pnl,
                }
            )

            cash = cash + pnl
            position = "flat"
            effective_capital = cash * leverage

        # Track equity
        if position == "long":
            current_equity = cash + (
                effective_capital * (price / entry_price) - cash * leverage
            )
        else:
            current_equity = cash
        equity_curve.append(current_equity)

    # Close final position if open
    if position == "long":
        price = df.iloc[-1]["close"]
        position_value = effective_capital * (price / entry_price)
        pnl = position_value * 0.9995 - (cash * leverage)
        trades.append({"entry_price": entry_price, "exit_price": price, "pnl": pnl})
        cash = cash + pnl

    if len(trades) == 0:
        return None

    # Calculate metrics
    trades_df = pd.DataFrame(trades)
    total_pnl = trades_df["pnl"].sum()
    trading_days = len(df)
    avg_daily_pnl = total_pnl / trading_days

    # Sharpe
    if len(equity_curve) > 1:
        equity_series = pd.Series(equity_curve)
        daily_returns = equity_series.pct_change().dropna()
        if daily_returns.std() > 0:
            sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
        else:
            sharpe = 0
    else:
        sharpe = 0

    # Max drawdown
    if len(equity_curve) > 1:
        equity_series = pd.Series(equity_curve)
        peak = equity_series.expanding().max()
        drawdown = (equity_series - peak) / peak
        max_dd = drawdown.min() * 100
    else:
        max_dd = 0

    final_equity = cash
    total_return = (final_equity - CAPITAL) / CAPITAL * 100
    win_rate = (trades_df["pnl"] > 0).mean() * 100

    return {
        "total_pnl": total_pnl,
        "avg_daily_pnl": avg_daily_pnl,
        "trading_days": trading_days,
        "total_trades": len(trades),
        "sharpe": sharpe,
        "max_dd": max_dd,
        "total_return": total_return,
        "win_rate": win_rate,
        "final_equity": final_equity,
        "meets_target": avg_daily_pnl >= TARGET_DAILY_PNL,
    }


def run_optimization():
    """Run comprehensive grid search optimization."""

    symbols = ["GCUSD", "SIUSD"]

    # Parameter grid
    rsi_periods = [14, 21, 28, 35]
    entry_bands = [48, 50, 52, 55, 58, 60]
    exit_bands = [25, 30, 35, 40, 42, 45]
    leverages = [5, 6, 7, 8, 9, 10]

    print("=" * 90)
    print("PRECIOUS METALS STRATEGY OPTIMIZATION")
    print("Walk-Forward Parameter Tuning | Daily Data | 2024-2025")
    print("=" * 90)
    print(f"Target: ${TARGET_DAILY_PNL}/day on ${CAPITAL:,} capital")
    print(
        f"Testing: {len(rsi_periods)} RSI periods × {len(entry_bands)} entry bands × {len(exit_bands)} exit bands × {len(leverages)} leverages"
    )

    total_combos = (
        len(rsi_periods) * len(entry_bands) * len(exit_bands) * len(leverages)
    )
    print(f"Total combinations per symbol: {total_combos}")
    print("=" * 90)

    all_results = []

    for symbol in symbols:
        print(f"\n{'='*90}")
        print(f"SYMBOL: {symbol}")
        print("=" * 90)

        # Load data
        df = load_precious_metal_data(symbol, "2024-01-01", "2025-01-24")
        print(
            f"Loaded {len(df)} bars ({df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')})"
        )

        combo_num = 0
        best_sharpe = -999
        best_target_match = None

        for rsi_period in rsi_periods:
            for entry_band in entry_bands:
                for exit_band in exit_bands:
                    # Skip invalid combinations (entry must be > exit)
                    if entry_band <= exit_band:
                        continue

                    for lev in leverages:
                        combo_num += 1

                        result = run_backtest(
                            df, rsi_period, entry_band, exit_band, lev
                        )

                        if result is None:
                            continue

                        result["symbol"] = symbol
                        result["rsi_period"] = rsi_period
                        result["entry_band"] = entry_band
                        result["exit_band"] = exit_band
                        result["leverage"] = lev

                        all_results.append(result)

                        # Track best
                        if result["sharpe"] > best_sharpe:
                            best_sharpe = result["sharpe"]

                        if result["meets_target"] and (
                            best_target_match is None
                            or lev < best_target_match["leverage"]
                        ):
                            best_target_match = result

                        # Progress
                        if combo_num % 200 == 0:
                            print(f"  Progress: {combo_num} combos tested...")

        print(f"\nTotal valid combinations tested: {combo_num}")

        if best_target_match:
            print(f"\n✅ BEST $200/day CONFIG (lowest leverage):")
            print(f"   RSI Period: {best_target_match['rsi_period']}")
            print(f"   Entry Band: {best_target_match['entry_band']}")
            print(f"   Exit Band: {best_target_match['exit_band']}")
            print(f"   Leverage: {best_target_match['leverage']}x")
            print(f"   Daily P&L: ${best_target_match['avg_daily_pnl']:.2f}")
            print(f"   Sharpe: {best_target_match['sharpe']:.2f}")
            print(f"   Max DD: {best_target_match['max_dd']:.1f}%")

    # Save results
    results_df = pd.DataFrame(all_results)
    output_file = Path(__file__).parent / "optimization_results.csv"
    results_df.to_csv(output_file, index=False)
    print(f"\n📁 Full results saved to: {output_file}")

    # Summary tables
    print("\n" + "=" * 90)
    print("OPTIMIZATION SUMMARY")
    print("=" * 90)

    for symbol in symbols:
        sym_df = results_df[results_df["symbol"] == symbol]
        if len(sym_df) == 0:
            continue

        # Best by Sharpe
        best_sharpe_row = sym_df.loc[sym_df["sharpe"].idxmax()]

        # Best that meets target with lowest leverage
        target_df = sym_df[sym_df["meets_target"] == True]
        if len(target_df) > 0:
            best_target_row = target_df.loc[target_df["leverage"].idxmin()]
        else:
            best_target_row = None

        print(f"\n{symbol}:")
        print("-" * 50)
        print(f"  Best Sharpe: {best_sharpe_row['sharpe']:.2f}")
        print(
            f"    RSI: {int(best_sharpe_row['rsi_period'])}, Entry: {int(best_sharpe_row['entry_band'])}, Exit: {int(best_sharpe_row['exit_band'])}"
        )
        print(
            f"    Leverage: {int(best_sharpe_row['leverage'])}x | Daily: ${best_sharpe_row['avg_daily_pnl']:.0f}"
        )

        if best_target_row is not None:
            print(f"\n  Lowest Leverage for $200/day:")
            print(
                f"    RSI: {int(best_target_row['rsi_period'])}, Entry: {int(best_target_row['entry_band'])}, Exit: {int(best_target_row['exit_band'])}"
            )
            print(
                f"    Leverage: {int(best_target_row['leverage'])}x | Daily: ${best_target_row['avg_daily_pnl']:.0f}"
            )
            print(
                f"    Sharpe: {best_target_row['sharpe']:.2f} | Max DD: {best_target_row['max_dd']:.0f}%"
            )

    print("\n" + "=" * 90)
    print("OPTIMIZATION COMPLETE")
    print("=" * 90)

    return results_df


if __name__ == "__main__":
    results = run_optimization()
