"""
ES ORB (Opening Range Breakout) Strategy
High-return leveraged futures strategy targeting $200-500/day on $20k capital

Adapted from GSB commodity strategy (90%+ 4yr returns on NG/SB)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
from datetime import datetime, time

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()


def load_config():
    """Load strategy configuration"""
    config_path = Path(__file__).parent / "config.json"
    with open(config_path) as f:
        return json.load(f)


def load_es_data(start_date: str, end_date: str, data_dir: str = None) -> pd.DataFrame:
    """
    Load ES futures data from cache.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        data_dir: Optional data directory override
    
    Returns:
        DataFrame with OHLCV data
    """
    # Search multiple directories for ES 1-min data
    search_dirs = []
    
    if data_dir is not None:
        search_dirs.append(Path(data_dir))
    else:
        # Check equities first (where ES_1min data is located)
        search_dirs.append(project_root / "data" / "cache" / "equities")
        search_dirs.append(project_root / "data" / "cache" / "futures")
    
    es_files = []
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        
        # Use SPY_1min as ES proxy (ES file has incorrect data, SPY is documented proxy)
        # Per FUTURES_QUICK_START_FMP.md: "SPY - S&P 500 (proxy for MES)"
        found = list(search_dir.glob("SPY_1min_*.parquet"))
        if found:
            es_files.extend(found)
            print("Using SPY as MES proxy (per FUTURES_QUICK_START_FMP.md)")
            break
    
    if not es_files:
        # Fallback to ESUSD daily format
        for search_dir in search_dirs:
            if search_dir.exists():
                found = list(search_dir.glob("ESUSD_1day_*.parquet"))
                if found:
                    es_files.extend(found)
                    print(f"WARNING: Using daily data, not 1-minute (ORB strategy may not work correctly)")
                    break
    
    if not es_files:
        raise FileNotFoundError(f"No ES data files found in {search_dirs}")
    
    print(f"Loading: {[f.name for f in es_files]}")
    
    # Load and concatenate all matching files
    dfs = []
    for f in es_files:
        df = pd.read_parquet(f)
        dfs.append(df)
    
    if not dfs:
        raise ValueError("No data loaded")
    
    df = pd.concat(dfs)
    df = df.sort_index()
    
    # Convert to Eastern Time if needed (data may be in UTC)
    if df.index.tz is None:
        df.index = pd.to_datetime(df.index).tz_localize('UTC').tz_convert('US/Eastern')
    elif 'UTC' in str(df.index.tz):
        df.index = df.index.tz_convert('US/Eastern')
    
    # Filter to date range
    df = df[start_date:end_date]
    
    return df


def run_es_orb_backtest(
    start_date: str,
    end_date: str,
    initial_capital: float = 20000,
    leverage: float = 5,
    use_mes: bool = True,
    verbose: bool = True
) -> dict:
    """
    Run ES ORB backtest.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD) 
        initial_capital: Starting capital in USD
        leverage: Leverage multiplier
        use_mes: If True, use MES (micro) contracts
        verbose: Print progress
    
    Returns:
        Dict with backtest results
    """
    config = load_config()
    
    if verbose:
        print("\n" + "=" * 60)
        print("ES ORB STRATEGY BACKTEST")
        print(f"Period: {start_date} to {end_date}")
        print(f"Capital: ${initial_capital:,.0f} | Leverage: {leverage}x")
        print(f"Contract: {'MES (Micro)' if use_mes else 'ES (Full)'}")
        print("=" * 60)
    
    # Load data
    try:
        df = load_es_data(start_date, end_date)
        if verbose:
            print(f"Loaded {len(df)} bars")
    except Exception as e:
        print(f"ERROR loading data: {e}")
        return {"error": str(e)}
    
    if len(df) == 0:
        return {"error": "No data in range"}
    
    # Strategy parameters
    params = {
        "OR_MINUTES": config["session"]["or_minutes"],
        "VOL_MULT": config["entry"]["vol_mult"],
        "PULLBACK_ATR": config["entry"]["pullback_atr"],
        "HARD_STOP_ATR": config["exit"]["hard_stop_atr"],
        "BREAKEVEN_TRIGGER_R": config["exit"]["breakeven_trigger_r"],
        "PROFIT_TARGET_R": config["exit"]["profit_target_r"],
        "TRAIL_ATR": config["exit"]["trail_atr"],
        "SESSION_HOUR": 9,
        "SESSION_MIN": 30,
        "MIN_OR_RANGE": config["entry"]["min_or_range_pts"],
    }
    
    # Contract specs
    point_value = config["contract"]["point_value_mes"] if use_mes else config["contract"]["point_value_es"]
    tick_value = config["contract"]["tick_value_mes"] if use_mes else config["contract"]["tick_value_es"]
    commission = config["friction"]["commission_per_contract"]
    slippage_ticks = config["friction"]["slippage_ticks"]
    
    # Position sizing: how many contracts can we trade?
    effective_capital = initial_capital * leverage
    # Rough margin per MES: ~$1,500
    margin_per_contract = 1500 if use_mes else 15000
    max_contracts = int(effective_capital / margin_per_contract)
    target_contracts = min(max_contracts, config["position_sizing"]["max_contracts_mes"])
    
    if verbose:
        print(f"Position Size: {target_contracts} contracts (max: {max_contracts})")
    
    # Data prep
    df = df.copy()
    df["date"] = df.index.date
    df["hour"] = df.index.hour
    df["minute"] = df.index.minute
    df["minutes_since_session"] = (df["hour"] - params["SESSION_HOUR"]) * 60 + (
        df["minute"] - params["SESSION_MIN"]
    )
    
    # Filter to RTH only
    df = df[
        (df["minutes_since_session"] >= 0) & 
        (df["minutes_since_session"] <= 390)  # 6.5 hours = 390 mins
    ].copy()
    
    if len(df) == 0:
        return {"error": "No RTH data"}
    
    # Technical indicators
    df["h_l"] = df["high"] - df["low"]
    df["h_pc"] = abs(df["high"] - df["close"].shift(1))
    df["l_pc"] = abs(df["low"] - df["close"].shift(1))
    df["tr"] = df[["h_l", "h_pc", "l_pc"]].max(axis=1)
    df["atr"] = df["tr"].rolling(14).mean()
    
    # VWAP
    df["typical_price"] = (df["high"] + df["low"] + df["close"]) / 3
    df["tp_volume"] = df["typical_price"] * df["volume"]
    df["cumulative_tp_volume"] = df.groupby("date")["tp_volume"].cumsum()
    df["cumulative_volume"] = df.groupby("date")["volume"].cumsum()
    df["vwap"] = df["cumulative_tp_volume"] / df["cumulative_volume"].replace(0, np.inf)
    
    # Volume spike
    df["avg_volume_20"] = df["volume"].rolling(20).mean()
    df["volume_spike"] = df["volume"] / df["avg_volume_20"].replace(0, np.inf)
    
    # Opening Range calculation
    or_mask = df["minutes_since_session"] <= params["OR_MINUTES"]
    df["or_high"] = np.nan
    df["or_low"] = np.nan
    df["or_range"] = np.nan
    
    for date in df["date"].unique():
        date_mask = df["date"] == date
        or_data = df[date_mask & or_mask]
        if len(or_data) >= 5:
            or_high = or_data["high"].max()
            or_low = or_data["low"].min()
            df.loc[date_mask, "or_high"] = or_high
            df.loc[date_mask, "or_low"] = or_low
            df.loc[date_mask, "or_range"] = or_high - or_low
    
    # Breakout detection
    df["breakout"] = (df["close"] > df["or_high"]) & (df["volume_spike"] >= params["VOL_MULT"])
    df["above_vwap"] = df["close"] > df["vwap"]
    
    # Trading simulation
    trades = []
    position = None
    entry_price = None
    entry_time = None
    stop_loss = None
    highest_price = 0
    breakout_seen = False
    moved_to_be = False
    contracts = target_contracts
    
    equity = initial_capital
    equity_curve = []
    
    for i in range(len(df)):
        row = df.iloc[i]
        
        if pd.isna(row["atr"]) or pd.isna(row["or_high"]):
            continue
        
        current_price = row["close"]
        current_low = row["low"]
        current_high = row["high"]
        current_atr = row["atr"]
        current_or_high = row["or_high"]
        current_or_low = row["or_low"]
        current_or_range = row["or_range"]
        current_vwap = row["vwap"]
        minutes_since_session = row["minutes_since_session"]
        
        # Skip OR period
        if minutes_since_session <= params["OR_MINUTES"]:
            continue
        
        # Skip if OR range too small
        if current_or_range < params["MIN_OR_RANGE"]:
            continue
        
        # ENTRY LOGIC - Simple breakout entry (no pullback required)
        if position is None:
            # Enter on first close above OR high, above VWAP
            if (
                current_price > current_or_high
                and current_price > current_vwap
                and not breakout_seen  # Only one trade per day
            ):
                # ENTER LONG
                position = contracts
                entry_price = current_price + (slippage_ticks * 0.25)  # Slippage
                entry_time = df.index[i]
                stop_loss = current_or_low - (params["HARD_STOP_ATR"] * current_atr)
                highest_price = current_price
                breakout_seen = True  # Mark breakout seen for this day
                moved_to_be = False
        
        # POSITION MANAGEMENT
        elif position is not None and position > 0:
            risk_pts = entry_price - stop_loss
            current_r = (current_price - entry_price) / risk_pts if risk_pts > 0 else 0
            
            if current_high > highest_price:
                highest_price = current_high
            
            exit_price = None
            exit_reason = None
            
            # Stop loss hit
            if current_low <= stop_loss:
                exit_price = stop_loss - (slippage_ticks * 0.25)
                exit_reason = "stop"
            
            # Profit target hit
            elif current_r >= params["PROFIT_TARGET_R"]:
                exit_price = entry_price + (risk_pts * params["PROFIT_TARGET_R"])
                exit_reason = "target"
            
            # EOD exit
            elif minutes_since_session >= 385:  # 15 mins before close
                exit_price = current_price - (slippage_ticks * 0.25)
                exit_reason = "eod"
            
            # Breakeven move
            if current_r >= params["BREAKEVEN_TRIGGER_R"] and not moved_to_be:
                stop_loss = entry_price
                moved_to_be = True
            
            # Trailing stop
            if moved_to_be:
                trail_stop = highest_price - (params["TRAIL_ATR"] * current_atr)
                stop_loss = max(stop_loss, trail_stop)
                
                if current_low <= stop_loss:
                    exit_price = stop_loss - (slippage_ticks * 0.25)
                    exit_reason = "trail"
            
            # Execute exit
            if exit_price is not None:
                pnl_pts = exit_price - entry_price
                pnl_dollars = pnl_pts * point_value * contracts
                
                # Subtract commission
                pnl_dollars -= (commission * contracts * 2)  # Round trip
                
                equity += pnl_dollars
                
                trades.append({
                    "entry_time": entry_time,
                    "exit_time": df.index[i],
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "pnl_pts": pnl_pts,
                    "pnl_dollars": pnl_dollars,
                    "r_multiple": current_r,
                    "exit_reason": exit_reason,
                    "contracts": contracts,
                })
                
                position = None
                breakout_seen = False
        
        equity_curve.append({"time": df.index[i], "equity": equity})
    
    # Close any open position at end
    if position is not None:
        last_row = df.iloc[-1]
        pnl_pts = last_row["close"] - entry_price
        pnl_dollars = pnl_pts * point_value * contracts - (commission * contracts * 2)
        equity += pnl_dollars
        trades.append({
            "entry_time": entry_time,
            "exit_time": df.index[-1],
            "entry_price": entry_price,
            "exit_price": last_row["close"],
            "pnl_pts": pnl_pts,
            "pnl_dollars": pnl_dollars,
            "r_multiple": 0,
            "exit_reason": "final",
            "contracts": contracts,
        })
    
    # Calculate metrics
    if len(trades) == 0:
        if verbose:
            print("NO TRADES GENERATED")
        return {
            "total_trades": 0,
            "error": "No trades generated"
        }
    
    trades_df = pd.DataFrame(trades)
    equity_df = pd.DataFrame(equity_curve)
    
    total_trades = len(trades_df)
    winning_trades = (trades_df["pnl_dollars"] > 0).sum()
    losing_trades = (trades_df["pnl_dollars"] <= 0).sum()
    win_rate = winning_trades / total_trades * 100
    
    total_pnl = trades_df["pnl_dollars"].sum()
    avg_trade_pnl = trades_df["pnl_dollars"].mean()
    avg_winner = trades_df[trades_df["pnl_dollars"] > 0]["pnl_dollars"].mean() if winning_trades > 0 else 0
    avg_loser = trades_df[trades_df["pnl_dollars"] <= 0]["pnl_dollars"].mean() if losing_trades > 0 else 0
    
    # Calculate trading days and daily P&L
    trading_days = trades_df["entry_time"].dt.date.nunique()
    avg_daily_pnl = total_pnl / trading_days if trading_days > 0 else 0
    
    # Max drawdown
    equity_df["peak"] = equity_df["equity"].cummax()
    equity_df["drawdown"] = (equity_df["equity"] - equity_df["peak"]) / equity_df["peak"] * 100
    max_drawdown = equity_df["drawdown"].min()
    
    # Final return
    total_return_pct = (equity - initial_capital) / initial_capital * 100
    
    results = {
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
        "total_return_pct": total_return_pct,
        "final_equity": equity,
        "initial_capital": initial_capital,
        "trades_df": trades_df,
        "equity_df": equity_df,
        "contracts_per_trade": contracts,
    }
    
    if verbose:
        print("\n" + "=" * 60)
        print("BACKTEST RESULTS")
        print("=" * 60)
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
        print(f"Max Drawdown:       {max_drawdown:.1f}%")
        print(f"Total Return:       {total_return_pct:+.1f}%")
        print("-" * 40)
        print(f"Initial Capital:    ${initial_capital:,.0f}")
        print(f"Final Equity:       ${equity:,.2f}")
        print("=" * 60)
        
        # Reality check vs target
        print("\n[REALITY CHECK vs $200-500/day TARGET]")
        if avg_daily_pnl >= 200:
            print(f"✅ Strategy meets minimum target: ${avg_daily_pnl:.2f}/day >= $200")
        else:
            print(f"❌ Strategy BELOW target: ${avg_daily_pnl:.2f}/day < $200")
            shortfall = 200 - avg_daily_pnl
            print(f"   Shortfall: ${shortfall:.2f}/day")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ES ORB Strategy Backtest")
    parser.add_argument("--start", default="2024-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default="2024-12-31", help="End date (YYYY-MM-DD)")
    parser.add_argument("--capital", type=float, default=20000, help="Initial capital")
    parser.add_argument("--leverage", type=float, default=5, help="Leverage multiplier")
    parser.add_argument("--mes", action="store_true", default=True, help="Use MES (micro) contracts")
    
    args = parser.parse_args()
    
    results = run_es_orb_backtest(
        start_date=args.start,
        end_date=args.end,
        initial_capital=args.capital,
        leverage=args.leverage,
        use_mes=args.mes,
    )
