"""
Precious Metals Bull Market Strategy
Trend-following strategy for Gold (GCUSD) and Silver (SIUSD)

Uses RSI Hysteresis (proven on equities) adapted for commodities in bull market.
Optimized for capturing large trend moves with pyramiding.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv(project_root / ".env")


def load_precious_metal_data(
    symbol: str, interval: str = "1day", start_date: str = None, end_date: str = None
) -> pd.DataFrame:
    """
    Load precious metal data from cache.

    Args:
        symbol: 'GCUSD' (gold) or 'SIUSD' (silver)
        interval: '1day' or '1hour'
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        DataFrame with OHLCV data
    """
    cache_dir = project_root / "data" / "cache" / "futures"

    # Find matching files
    pattern = f"{symbol}_{interval}_*.parquet"
    files = list(cache_dir.glob(pattern))

    if not files:
        raise FileNotFoundError(f"No {symbol} {interval} data found in {cache_dir}")

    print(f"Loading {symbol} {interval} data from {len(files)} files")

    dfs = []
    for f in files:
        df = pd.read_parquet(f)
        dfs.append(df)

    df = pd.concat(dfs)
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="last")]

    # Filter date range
    if start_date:
        df = df[start_date:]
    if end_date:
        df = df[:end_date]

    print(f"Loaded {len(df)} bars ({df.index[0]} to {df.index[-1]})")

    return df


def calculate_rsi(prices: pd.Series, period: int = 28) -> pd.Series:
    """Calculate RSI indicator"""
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


def run_trend_backtest(
    symbol: str,
    start_date: str,
    end_date: str,
    initial_capital: float = 20000,
    leverage: float = 3,
    rsi_period: int = 28,
    entry_band: float = 55,
    exit_band: float = 45,
    transaction_cost_bps: float = 5.0,
    verbose: bool = True,
) -> dict:
    """
    Run trend-following backtest on precious metals.

    Args:
        symbol: 'GCUSD' or 'SIUSD'
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        initial_capital: Starting capital in USD
        leverage: Position size multiplier
        rsi_period: RSI calculation period
        entry_band: RSI level to enter long
        exit_band: RSI level to exit
        transaction_cost_bps: Transaction costs in basis points
        verbose: Print progress

    Returns:
        Dict with backtest results
    """
    if verbose:
        print("\n" + "=" * 60)
        print(f"PRECIOUS METALS TREND-FOLLOWING BACKTEST")
        print(f"Symbol: {symbol}")
        print(f"Period: {start_date} to {end_date}")
        print(f"Capital: ${initial_capital:,.0f} | Leverage: {leverage}x")
        print(f"RSI: {rsi_period} | Entry: >{entry_band} | Exit: <{exit_band}")
        print("=" * 60)

    # Load data
    df = load_precious_metal_data(symbol, "1day", start_date, end_date)

    if len(df) < rsi_period + 10:
        return {"error": "Insufficient data"}

    # Calculate RSI
    df["rsi"] = calculate_rsi(df["close"], rsi_period)

    # Contract specs for micro futures
    if symbol == "GCUSD":
        # Micro Gold: 10 oz per contract
        contract_multiplier = 10
        contract_name = "MGC"
    elif symbol == "SIUSD":
        # Micro Silver: 1000 oz per contract
        contract_multiplier = 1000
        contract_name = "MSI"
    else:
        contract_multiplier = 1
        contract_name = symbol

    # Position sizing
    effective_capital = initial_capital * leverage

    # Trading simulation
    cash = initial_capital
    position_value = 0
    position = "flat"  # 'flat' or 'long'
    trades = []
    equity_curve = []

    entry_price = None
    entry_date = None

    for i in range(len(df)):
        row = df.iloc[i]
        date = df.index[i]
        price = row["close"]
        rsi = row["rsi"]

        if pd.isna(rsi):
            equity_curve.append(
                {"date": date, "equity": cash + position_value, "position": position}
            )
            continue

        # Mark-to-market if in position
        if position == "long":
            position_value = effective_capital * (price / entry_price)

        # Entry: RSI crosses above entry band
        if position == "flat" and rsi > entry_band:
            # Enter long
            cost = transaction_cost_bps / 10000
            effective_capital = cash * leverage * (1 - cost)
            entry_price = price
            entry_date = date
            position = "long"
            position_value = effective_capital

            if verbose:
                print(
                    f"  {date.strftime('%Y-%m-%d')} ENTER LONG @ ${price:.2f} (RSI: {rsi:.1f})"
                )

        # Exit: RSI crosses below exit band
        elif position == "long" and rsi < exit_band:
            # Exit position
            cost = transaction_cost_bps / 10000
            exit_value = position_value * (1 - cost)
            pnl = exit_value - (cash * leverage)
            pnl_pct = (price / entry_price - 1) * 100 * leverage
            hold_days = (date - entry_date).days

            trades.append(
                {
                    "entry_date": entry_date,
                    "exit_date": date,
                    "entry_price": entry_price,
                    "exit_price": price,
                    "hold_days": hold_days,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "leverage": leverage,
                }
            )

            cash = cash + pnl
            position = "flat"
            position_value = 0
            effective_capital = cash * leverage

            if verbose:
                win_loss = "✅" if pnl > 0 else "❌"
                print(
                    f"  {date.strftime('%Y-%m-%d')} EXIT @ ${price:.2f} | P&L: ${pnl:+,.2f} ({pnl_pct:+.1f}%) {win_loss}"
                )

        current_equity = cash + (position_value if position == "long" else 0)
        equity_curve.append(
            {"date": date, "equity": current_equity, "position": position}
        )

    # Close any open position at end
    if position == "long":
        final_price = df.iloc[-1]["close"]
        final_date = df.index[-1]
        cost = transaction_cost_bps / 10000
        exit_value = position_value * (1 - cost)
        pnl = exit_value - (cash * leverage)
        pnl_pct = (final_price / entry_price - 1) * 100 * leverage
        hold_days = (final_date - entry_date).days

        trades.append(
            {
                "entry_date": entry_date,
                "exit_date": final_date,
                "entry_price": entry_price,
                "exit_price": final_price,
                "hold_days": hold_days,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "leverage": leverage,
            }
        )

        cash = cash + pnl

        if verbose:
            win_loss = "✅" if pnl > 0 else "❌"
            print(
                f"  {final_date.strftime('%Y-%m-%d')} FINAL EXIT @ ${final_price:.2f} | P&L: ${pnl:+,.2f} ({pnl_pct:+.1f}%) {win_loss}"
            )

    # Calculate metrics
    if len(trades) == 0:
        if verbose:
            print("\nNO TRADES GENERATED")
        return {"total_trades": 0, "error": "No trades"}

    trades_df = pd.DataFrame(trades)
    equity_df = pd.DataFrame(equity_curve)

    total_trades = len(trades_df)
    winning_trades = (trades_df["pnl"] > 0).sum()
    losing_trades = (trades_df["pnl"] <= 0).sum()
    win_rate = winning_trades / total_trades * 100

    total_pnl = trades_df["pnl"].sum()
    avg_trade_pnl = trades_df["pnl"].mean()
    avg_winner = (
        trades_df[trades_df["pnl"] > 0]["pnl"].mean() if winning_trades > 0 else 0
    )
    avg_loser = (
        trades_df[trades_df["pnl"] <= 0]["pnl"].mean() if losing_trades > 0 else 0
    )

    # Trading days
    trading_days = len(df)
    avg_daily_pnl = total_pnl / trading_days

    # Max drawdown
    equity_df["peak"] = equity_df["equity"].cummax()
    equity_df["drawdown"] = (
        (equity_df["equity"] - equity_df["peak"]) / equity_df["peak"] * 100
    )
    max_drawdown = equity_df["drawdown"].min()

    # Sharpe ratio (annualized)
    daily_returns = equity_df["equity"].pct_change().dropna()
    if len(daily_returns) > 0 and daily_returns.std() > 0:
        sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
    else:
        sharpe = 0

    final_equity = cash
    total_return_pct = (final_equity - initial_capital) / initial_capital * 100

    results = {
        "symbol": symbol,
        "contract": contract_name,
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": win_rate,
        "total_pnl": total_pnl,
        "avg_trade_pnl": avg_trade_pnl,
        "avg_winner": avg_winner,
        "avg_loser": avg_loser,
        "trading_days": trading_days,
        "avg_daily_pnl": avg_daily_pnl,
        "max_drawdown_pct": max_drawdown,
        "sharpe_ratio": sharpe,
        "total_return_pct": total_return_pct,
        "final_equity": final_equity,
        "initial_capital": initial_capital,
        "leverage": leverage,
        "trades_df": trades_df,
        "equity_df": equity_df,
    }

    if verbose:
        print("\n" + "=" * 60)
        print("BACKTEST RESULTS")
        print("=" * 60)
        print(f"Symbol:             {symbol} ({contract_name})")
        print(f"Total Trades:       {total_trades}")
        print(f"Win Rate:           {win_rate:.1f}%")
        print(f"Trading Days:       {trading_days}")
        print("-" * 40)
        print(f"Total P&L:          ${total_pnl:+,.2f}")
        print(f"Avg Trade P&L:      ${avg_trade_pnl:+,.2f}")
        print(f"Avg Winner:         ${avg_winner:+,.2f}")
        print(f"Avg Loser:          ${avg_loser:+,.2f}")
        print("-" * 40)
        print(f"AVG DAILY P&L:      ${avg_daily_pnl:+,.2f}")
        print(f"Sharpe Ratio:       {sharpe:.2f}")
        print(f"Max Drawdown:       {max_drawdown:.1f}%")
        print(f"Total Return:       {total_return_pct:+.1f}%")
        print("-" * 40)
        print(f"Initial Capital:    ${initial_capital:,.0f}")
        print(f"Final Equity:       ${final_equity:,.2f}")
        print("=" * 60)

        # Target assessment
        print("\n[TARGET ASSESSMENT: $200+/day]")
        if avg_daily_pnl >= 200:
            print(f"✅ MEETS TARGET: ${avg_daily_pnl:.2f}/day >= $200")
        elif avg_daily_pnl >= 100:
            print(f"⚠️ CLOSE: ${avg_daily_pnl:.2f}/day (increase leverage?)")
        else:
            print(f"❌ BELOW TARGET: ${avg_daily_pnl:.2f}/day < $200")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Precious Metals Trend Strategy Backtest"
    )
    parser.add_argument(
        "--symbol", default="GCUSD", choices=["GCUSD", "SIUSD"], help="Symbol to test"
    )
    parser.add_argument("--start", default="2024-01-01", help="Start date")
    parser.add_argument("--end", default="2025-01-24", help="End date")
    parser.add_argument("--capital", type=float, default=20000, help="Initial capital")
    parser.add_argument("--leverage", type=float, default=3, help="Leverage multiplier")

    args = parser.parse_args()

    results = run_trend_backtest(
        symbol=args.symbol,
        start_date=args.start,
        end_date=args.end,
        initial_capital=args.capital,
        leverage=args.leverage,
    )
