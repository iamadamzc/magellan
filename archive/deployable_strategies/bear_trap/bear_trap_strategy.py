"""
Bear Trap Strategy - Small-Cap Reversal Hunter
Catches violent reversals on heavily sold-off small-cap stocks
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

from src.data_cache import cache


def run_bear_trap(symbol, start, end, initial_capital=100000):
    """
    Bear Trap Strategy

    Entry: Stock down ≥15%, breaks session low, then reclaims with quality candle
    Exit: Multi-stage (40% at mid, 30% at HOD, 30% trail)
    """

    params = {
        # Entry Filters
        "RECLAIM_WICK_RATIO_MIN": 0.15,
        "RECLAIM_VOL_MULT": 0.2,
        "RECLAIM_BODY_RATIO_MIN": 0.2,
        "MIN_DAY_CHANGE_PCT": 15.0,
        # Support
        "SUPPORT_MODE": "session_low",
        # Exit
        "STOP_ATR_MULTIPLIER": 0.45,
        "ATR_PERIOD": 14,
        "SCALE_TP1_PCT": 40,  # 40% at mid-range
        "SCALE_TP2_PCT": 30,  # 30% at HOD
        "RUNNER_PCT": 30,  # 30% trail
        "MAX_HOLD_MINUTES": 30,
        # Position Sizing
        "PER_TRADE_RISK_PCT": 0.02,
        "MAX_POSITION_DOLLARS": 50000,
        # Risk Gates
        "MAX_DAILY_LOSS_PCT": 0.10,
        "MAX_TRADES_PER_DAY": 10,
        "MAX_SPREAD_PCT": 0.02,
        "MIN_BID_ASK_SIZE": 50,
    }

    print(f"\nTesting {symbol} - Bear Trap [{start} to {end}]")

    # Fetch 1-minute data
    df = cache.get_or_fetch_equity(symbol, "1min", start, end)
    if df is None or len(df) == 0:
        print(f"0 trades (no data)")
        return {"symbol": symbol, "total_trades": 0, "total_pnl_pct": 0, "win_rate": 0}

    # Add time features
    df["date"] = df.index.date
    df["time"] = df.index.time
    df["hour"] = df.index.hour
    df["minute"] = df.index.minute

    # Calculate ATR
    df["h_l"] = df["high"] - df["low"]
    df["h_pc"] = abs(df["high"] - df["close"].shift(1))
    df["l_pc"] = abs(df["low"] - df["close"].shift(1))
    df["tr"] = df[["h_l", "h_pc", "l_pc"]].max(axis=1)
    df["atr"] = df["tr"].rolling(params["ATR_PERIOD"]).mean()

    # Volume metrics
    df["avg_volume_20"] = df["volume"].rolling(20).mean()
    df["volume_ratio"] = df["volume"] / df["avg_volume_20"].replace(0, np.inf)

    # Calculate session metrics (NO LOOKAHEAD - use cumulative)
    df["session_low"] = df.groupby("date")[
        "low"
    ].cummin()  # Running minimum (only knows past)
    df["session_high"] = df.groupby("date")[
        "high"
    ].cummax()  # Running maximum (only knows past)
    df["session_open"] = df.groupby("date")["open"].transform(
        "first"
    )  # First is OK (known at start)

    # Day change from open
    df["day_change_pct"] = (
        (df["close"] - df["session_open"]) / df["session_open"]
    ) * 100

    # Candle metrics
    df["candle_range"] = df["high"] - df["low"]
    df["candle_body"] = abs(df["close"] - df["open"])
    df["lower_wick"] = df[["open", "close"]].min(axis=1) - df["low"]
    df["upper_wick"] = df["high"] - df[["open", "close"]].max(axis=1)

    df["wick_ratio"] = df["lower_wick"] / df["candle_range"].replace(0, np.inf)
    df["body_ratio"] = df["candle_body"] / df["candle_range"].replace(0, np.inf)

    trades = []
    capital = initial_capital
    daily_pnl = {}
    daily_trades = {}

    position = None
    entry_price = None
    stop_loss = None
    position_size = 0
    highest_price = 0
    entry_time = None
    support_level = None

    for i in range(len(df)):
        if pd.isna(df.iloc[i]["atr"]):
            continue

        current_date = df.iloc[i]["date"]
        current_price = df.iloc[i]["close"]
        current_low = df.iloc[i]["low"]
        current_high = df.iloc[i]["high"]
        current_time = df.iloc[i].name
        current_atr = df.iloc[i]["atr"]
        session_low = df.iloc[i]["session_low"]
        session_high = df.iloc[i]["session_high"]
        day_change = df.iloc[i]["day_change_pct"]

        # Initialize daily tracking
        if current_date not in daily_pnl:
            daily_pnl[current_date] = 0
            daily_trades[current_date] = 0

        # Check daily loss limit
        if daily_pnl[current_date] <= -params["MAX_DAILY_LOSS_PCT"] * capital:
            continue

        # Check daily trade limit
        if daily_trades[current_date] >= params["MAX_TRADES_PER_DAY"]:
            continue

        # Entry Logic
        if position is None:
            # Must be down ≥15% on day
            if day_change >= -params["MIN_DAY_CHANGE_PCT"]:
                continue

            # Check for reclaim candle
            is_reclaim = (
                df.iloc[i]["close"] > session_low  # Reclaimed above session low
                and df.iloc[i]["wick_ratio"] >= params["RECLAIM_WICK_RATIO_MIN"]
                and df.iloc[i]["body_ratio"] >= params["RECLAIM_BODY_RATIO_MIN"]
                and df.iloc[i]["volume_ratio"] >= (1 + params["RECLAIM_VOL_MULT"])
            )

            if is_reclaim:
                # Calculate position size
                support_level = session_low
                stop_distance = support_level - (
                    params["STOP_ATR_MULTIPLIER"] * current_atr
                )
                risk_per_share = current_price - stop_distance

                if risk_per_share <= 0:
                    continue

                # Position size based on 2% risk
                risk_dollars = capital * params["PER_TRADE_RISK_PCT"]
                shares = int(risk_dollars / risk_per_share)
                position_dollars = shares * current_price

                # Cap at max position size
                if position_dollars > params["MAX_POSITION_DOLLARS"]:
                    shares = int(params["MAX_POSITION_DOLLARS"] / current_price)
                    position_dollars = shares * current_price

                if shares > 0:
                    position = 1.0  # Full position initially
                    position_size = shares
                    entry_price = current_price
                    stop_loss = stop_distance
                    highest_price = current_price
                    entry_time = current_time

        # Position Management
        elif position is not None and position > 0:
            # Update highest price
            if current_high > highest_price:
                highest_price = current_high

            # Check stop loss
            if current_low <= stop_loss:
                pnl_dollars = (stop_loss - entry_price) * position_size * position
                pnl_pct = (pnl_dollars / capital) * 100

                trades.append(
                    {
                        "pnl_pct": pnl_pct,
                        "pnl_dollars": pnl_dollars,
                        "type": "stop",
                        "exit_price": stop_loss,
                    }
                )

                capital += pnl_dollars
                daily_pnl[current_date] += pnl_dollars
                daily_trades[current_date] += 1

                position = None
                continue

            # Scale TP1: 40% at mid-range (halfway to session high)
            mid_range = entry_price + ((session_high - entry_price) * 0.5)
            if current_high >= mid_range and position == 1.0:
                scale_pct = params["SCALE_TP1_PCT"] / 100
                pnl_dollars = (mid_range - entry_price) * position_size * scale_pct
                pnl_pct = (pnl_dollars / capital) * 100

                trades.append(
                    {
                        "pnl_pct": pnl_pct,
                        "pnl_dollars": pnl_dollars,
                        "type": "tp1_mid",
                        "exit_price": mid_range,
                    }
                )

                capital += pnl_dollars
                position -= scale_pct

            # Scale TP2: 30% at HOD
            if current_high >= session_high and position >= (
                params["SCALE_TP2_PCT"] / 100
            ):
                scale_pct = params["SCALE_TP2_PCT"] / 100
                pnl_dollars = (session_high - entry_price) * position_size * scale_pct
                pnl_pct = (pnl_dollars / capital) * 100

                trades.append(
                    {
                        "pnl_pct": pnl_pct,
                        "pnl_dollars": pnl_dollars,
                        "type": "tp2_hod",
                        "exit_price": session_high,
                    }
                )

                capital += pnl_dollars
                position -= scale_pct

                # Move stop to support for runner
                stop_loss = support_level

            # Time stop: 30 minutes
            if (current_time - entry_time).total_seconds() / 60 >= params[
                "MAX_HOLD_MINUTES"
            ]:
                pnl_dollars = (current_price - entry_price) * position_size * position
                pnl_pct = (pnl_dollars / capital) * 100

                trades.append(
                    {
                        "pnl_pct": pnl_pct,
                        "pnl_dollars": pnl_dollars,
                        "type": "time_stop",
                        "exit_price": current_price,
                    }
                )

                capital += pnl_dollars
                daily_pnl[current_date] += pnl_dollars
                daily_trades[current_date] += 1

                position = None
                continue

            # EOD exit
            if df.iloc[i]["hour"] >= 15 and df.iloc[i]["minute"] >= 55:
                pnl_dollars = (current_price - entry_price) * position_size * position
                pnl_pct = (pnl_dollars / capital) * 100

                trades.append(
                    {
                        "pnl_pct": pnl_pct,
                        "pnl_dollars": pnl_dollars,
                        "type": "eod",
                        "exit_price": current_price,
                    }
                )

                capital += pnl_dollars
                daily_pnl[current_date] += pnl_dollars
                daily_trades[current_date] += 1

                position = None

    if len(trades) == 0:
        print(f"0 trades")
        return {"symbol": symbol, "total_trades": 0, "total_pnl_pct": 0, "win_rate": 0}

    trades_df = pd.DataFrame(trades)

    total_trades = len(trades_df)
    win_rate = (trades_df["pnl_pct"] > 0).sum() / total_trades * 100
    total_pnl_pct = trades_df["pnl_pct"].sum()
    total_pnl_dollars = trades_df["pnl_dollars"].sum()

    print(
        f"✓ {total_trades} trades | {win_rate:.1f}% win | {total_pnl_pct:+.2f}% | ${total_pnl_dollars:+,.0f}"
    )

    return {
        "symbol": symbol,
        "total_trades": total_trades,
        "win_rate": win_rate,
        "total_pnl_pct": total_pnl_pct,
        "total_pnl_dollars": total_pnl_dollars,
        "final_capital": capital,
    }
