"""
Bear Trap Strategy - Production Implementation with Comprehensive Logging
Intraday reversal strategy for small-cap stocks
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.trade_logger import TradeLogger
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame


class BearTrapStrategy:
    """
    Production Bear Trap Strategy

    Entry Criteria:
    - Stock down ≥15% on the day
    - Breaks session low
    - Reclaims above session low with quality candle (wick ratio, volume, body)

    Exit Strategy:
    - 40% at mid-range (halfway to session high)
    - 30% at session high
    - 30% trailing stop
    - Max hold time: 30 minutes
    - Stop loss: Session low - (0.45 * ATR)
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str,
        symbols: List[str],
        config: Dict,
    ):
        self.logger = logging.getLogger("magellan.bear_trap")
        self.trade_logger = TradeLogger(strategy_name="bear_trap")

        # Alpaca clients
        self.trading_client = TradingClient(api_key, api_secret, paper=True)

        # Use DataCache if USE_ARCHIVED_DATA is true, otherwise live API
        use_cache = os.getenv("USE_ARCHIVED_DATA", "false").lower() == "true"
        if use_cache:
            from src.data_cache import DataCache

            self.data_client = DataCache(api_key, api_secret)
            self.logger.info(
                "📦 Using DataCache for historical data (USE_ARCHIVED_DATA=true)"
            )
        else:
            self.data_client = StockHistoricalDataClient(api_key, api_secret)
            self.logger.info("🔴 Using live Alpaca API for historical data")

        self.symbols = symbols
        self.config = config
        self.params = config.get("risk_management", {})

        # Strategy state
        self.positions = {}  # {symbol: position_data}
        self.daily_pnl = 0
        self.daily_trades = 0
        self.daily_loss_limit = self.params.get("max_daily_loss_dollars", 10000)
        self.max_trades_per_day = self.params.get("max_trades_per_day", 10)

        self.logger.info(f"✓ BearTrapStrategy initialized for {len(symbols)} symbols")

    def process_market_data(self):
        """Fetch and process 1-minute bars for all symbols"""
        for symbol in self.symbols:
            try:
                # Fetch recent 1-min bars
                request = StockBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=TimeFrame.Minute,
                    start=datetime.now() - timedelta(minutes=45),
                    feed="sip",  # Market Data Plus (paid plan) feed
                )
                bars = self.data_client.get_stock_bars(request)

                if bars and bars.data and symbol in bars.data:
                    self._evaluate_symbol(symbol, bars.data[symbol])
                else:
                    self.logger.warning(f"No data for {symbol}")

            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {e}", exc_info=True)

    def _evaluate_symbol(self, symbol: str, bars):
        """Evaluate entry/exit for a single symbol"""
        # Convert to DataFrame for analysis
        import pandas as pd

        df = pd.DataFrame(
            [
                {
                    "timestamp": bar.timestamp,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                }
                for bar in bars
            ]
        )

        if len(df) < 20:
            return

        # Calculate indicators
        df["session_low"] = df["low"].cummin()
        df["session_high"] = df["high"].cummax()
        df["session_open"] = df["open"].iloc[0]
        df["day_change_pct"] = (
            (df["close"] - df["session_open"]) / df["session_open"]
        ) * 100

        # ATR calculation
        df["h_l"] = df["high"] - df["low"]
        df["h_pc"] = abs(df["high"] - df["close"].shift(1))
        df["l_pc"] = abs(df["low"] - df["close"].shift(1))
        df["tr"] = df[["h_l", "h_pc", "l_pc"]].max(axis=1)
        df["atr"] = df["tr"].rolling(14).mean()

        # Candle metrics
        df["candle_range"] = df["high"] - df["low"]
        df["candle_body"] = abs(df["close"] - df["open"])
        df["lower_wick"] = df[["open", "close"]].min(axis=1) - df["low"]
        df["wick_ratio"] = df["lower_wick"] / df["candle_range"].replace(0, 1)
        df["body_ratio"] = df["candle_body"] / df["candle_range"].replace(0, 1)

        # Volume
        df["avg_volume"] = df["volume"].rolling(20).mean()
        df["volume_ratio"] = df["volume"] / df["avg_volume"].replace(0, 1)

        current = df.iloc[-1]

        # Check if we have a position
        if symbol in self.positions:
            self._manage_position(symbol, current, df)
        else:
            self._evaluate_entry(symbol, current, df)

    def _evaluate_entry(self, symbol: str, current, df):
        """Evaluate entry criteria"""
        # Check risk gates first
        if not self._check_risk_gates(symbol):
            return

        # Entry criteria
        day_change = current["day_change_pct"]
        is_down_enough = day_change <= -15.0

        if not is_down_enough:
            self.trade_logger.log_decision(
                symbol=symbol,
                decision_type="SKIP_ENTRY",
                reason=f"Not down enough: {day_change:.1f}%",
                details=f"Required: -15%, Current: {day_change:.1f}%",
                current_price=current["close"],
                indicator_values={"day_change_pct": day_change},
            )
            return

        # Check for reclaim candle
        is_reclaim = (
            current["close"] > current["session_low"]
            and current["wick_ratio"] >= 0.15
            and current["body_ratio"] >= 0.20
            and current["volume_ratio"] >= 1.20
        )

        if is_reclaim:
            # Calculate position size
            stop_loss = current["session_low"] - (0.45 * current["atr"])
            risk_per_share = current["close"] - stop_loss

            if risk_per_share <= 0:
                self.trade_logger.log_decision(
                    symbol=symbol,
                    decision_type="SKIP_ENTRY",
                    reason="Invalid stop loss (negative risk)",
                    details=f"Price: {current['close']}, Stop: {stop_loss}",
                    current_price=current["close"],
                )
                return

            # 2% risk per trade
            account = self.trading_client.get_account()
            risk_dollars = float(account.equity) * 0.02
            shares = int(risk_dollars / risk_per_share)
            position_dollars = shares * current["close"]

            # Cap at max position size
            max_position = self.params.get("max_position_dollars", 50000)
            if position_dollars > max_position:
                shares = int(max_position / current["close"])
                position_dollars = shares * current["close"]

            if shares > 0:
                self._enter_position(symbol, shares, current, stop_loss, df)
        else:
            self.trade_logger.log_signal(
                symbol=symbol,
                signal_type="BUY",
                signal_strength=0,
                indicator_values={
                    "day_change_pct": day_change,
                    "wick_ratio": current["wick_ratio"],
                    "body_ratio": current["body_ratio"],
                    "volume_ratio": current["volume_ratio"],
                },
                entry_criteria_met=False,
                risk_gates_passed=True,
                action_taken="SKIPPED",
                skip_reason=f"Reclaim criteria not met: wick={current['wick_ratio']:.2f}, body={current['body_ratio']:.2f}, vol={current['volume_ratio']:.2f}",
            )

    def _enter_position(self, symbol: str, shares: int, current, stop_loss: float, df):
        """Execute entry order"""
        try:
            # Place market order
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=shares,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY,
            )

            order = self.trading_client.submit_order(order_request)

            # Store position data
            self.positions[symbol] = {
                "entry_time": datetime.now(),
                "entry_price": current["close"],
                "shares": shares,
                "stop_loss": stop_loss,
                "session_low": current["session_low"],
                "session_high": current["session_high"],
                "highest_price": current["close"],
                "order_id": order.id,
            }

            # Log trade
            self.trade_logger.log_trade(
                symbol=symbol,
                action="ENTRY",
                side="BUY",
                quantity=shares,
                price=current["close"],
                order_id=order.id,
                position_size_before=0,
                position_size_after=shares,
                entry_reason=f"Bear trap reclaim: Down {current['day_change_pct']:.1f}%, wick={current['wick_ratio']:.2f}, vol={current['volume_ratio']:.2f}",
                market_conditions={
                    "session_low": current["session_low"],
                    "session_high": current["session_high"],
                    "day_change_pct": current["day_change_pct"],
                },
                indicators={
                    "atr": current["atr"],
                    "wick_ratio": current["wick_ratio"],
                    "body_ratio": current["body_ratio"],
                    "volume_ratio": current["volume_ratio"],
                },
                risk_metrics={
                    "stop_loss": stop_loss,
                    "risk_per_share": current["close"] - stop_loss,
                    "position_dollars": shares * current["close"],
                },
            )

            self.daily_trades += 1
            self.logger.info(
                f"✓ ENTRY {symbol}: {shares} shares @ ${current['close']:.2f}"
            )

        except Exception as e:
            self.logger.error(f"Error entering {symbol}: {e}", exc_info=True)
            self.trade_logger.log_decision(
                symbol=symbol,
                decision_type="ENTRY_FAILED",
                reason=f"Order execution error: {str(e)}",
                current_price=current["close"],
            )

    def _manage_position(self, symbol: str, current, df):
        """Manage existing position"""
        pos = self.positions[symbol]

        # Update highest price
        if current["high"] > pos["highest_price"]:
            pos["highest_price"] = current["high"]

        # Check stop loss
        if current["low"] <= pos["stop_loss"]:
            self._exit_position(symbol, pos["stop_loss"], "STOP_LOSS", current)
            return

        # Check time stop (30 minutes)
        hold_time = (datetime.now() - pos["entry_time"]).total_seconds() / 60
        if hold_time >= 30:
            self._exit_position(symbol, current["close"], "TIME_STOP", current)
            return

        # EOD exit
        now = datetime.now()
        if now.hour >= 15 and now.minute >= 55:
            self._exit_position(symbol, current["close"], "EOD", current)
            return

        # Scale out logic (simplified for now - can be enhanced)
        # This would check mid-range and HOD targets

    def _exit_position(self, symbol: str, exit_price: float, reason: str, current):
        """Execute exit order"""
        try:
            pos = self.positions[symbol]

            # Place market sell order
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=pos["shares"],
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )

            order = self.trading_client.submit_order(order_request)

            # Calculate P&L
            pnl_dollars = (exit_price - pos["entry_price"]) * pos["shares"]
            pnl_percent = (pnl_dollars / (pos["entry_price"] * pos["shares"])) * 100
            hold_time = (datetime.now() - pos["entry_time"]).total_seconds() / 60

            # Log trade
            self.trade_logger.log_trade(
                symbol=symbol,
                action="EXIT",
                side="SELL",
                quantity=pos["shares"],
                price=exit_price,
                order_id=order.id,
                position_size_before=pos["shares"],
                position_size_after=0,
                exit_reason=reason,
                pnl_dollars=pnl_dollars,
                pnl_percent=pnl_percent,
                hold_time_minutes=hold_time,
                market_conditions={
                    "exit_price": exit_price,
                    "highest_reached": pos["highest_price"],
                },
            )

            self.daily_pnl += pnl_dollars
            self.logger.info(
                f"✓ EXIT {symbol}: {reason} | P&L: ${pnl_dollars:+.2f} ({pnl_percent:+.1f}%)"
            )

            # Remove position
            del self.positions[symbol]

        except Exception as e:
            self.logger.error(f"Error exiting {symbol}: {e}", exc_info=True)

    def _check_risk_gates(self, symbol: str) -> bool:
        """Check if risk gates allow trading"""
        # Check daily loss limit
        if self.daily_pnl <= -self.daily_loss_limit:
            self.trade_logger.log_risk_gate_failure(
                symbol=symbol,
                gate_name="MAX_DAILY_LOSS",
                gate_details={
                    "current_loss": self.daily_pnl,
                    "max_allowed": -self.daily_loss_limit,
                },
            )
            return False

        # Check max trades per day
        if self.daily_trades >= self.max_trades_per_day:
            self.trade_logger.log_risk_gate_failure(
                symbol=symbol,
                gate_name="MAX_TRADES_PER_DAY",
                gate_details={
                    "current_trades": self.daily_trades,
                    "max_allowed": self.max_trades_per_day,
                },
            )
            return False

        return True

    def get_status(self) -> Dict:
        """Return current strategy status"""
        return {
            "open_positions": len(self.positions),
            "pnl_today": self.daily_pnl,
            "trades_today": self.daily_trades,
            "positions": list(self.positions.keys()),
        }

    def close_all_positions(self, reason: str):
        """Emergency close all positions"""
        self.logger.warning(f"Closing all positions: {reason}")
        for symbol in list(self.positions.keys()):
            try:
                current_price = self._get_current_price(symbol)
                self._exit_position(symbol, current_price, f"EMERGENCY_{reason}", {})
            except Exception as e:
                self.logger.error(f"Error closing {symbol}: {e}")

    def _get_current_price(self, symbol: str) -> float:
        """Get current market price"""
        try:
            quote = self.trading_client.get_latest_quote(symbol)
            return (quote.ask_price + quote.bid_price) / 2
        except:
            return 0

    def generate_end_of_day_report(self):
        """Generate EOD summary"""
        summary = self.trade_logger.create_daily_summary()
        self.logger.info(
            f"EOD Summary: {summary['total_trades']} trades, P&L: ${summary['total_pnl']:.2f}"
        )

        # Reset daily counters
        self.daily_pnl = 0
        self.daily_trades = 0
