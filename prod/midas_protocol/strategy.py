"""
MIDAS Protocol - Asian Session Mean Reversion Strategy
Instrument: Micro Nasdaq-100 Futures (MNQ)
Timeframe: 1-Minute Candles
Session: 02:00:00 to 06:00:00 UTC

Entry Logic:
- Setup A (Crash Reversal): Velocity -150 to -67, EMA distance <=220, ATR Ratio >0.50
- Setup B (Quiet Drift): Velocity <=10, EMA distance <=220, ATR Ratio 0.06-0.50

Exit Logic:
- OCO Bracket: Stop Loss 20 points, Take Profit 120 points, Time-based 60 bars
- Max Daily Loss: $300
"""

import logging
from datetime import datetime, timedelta, time as dt_time
from typing import Dict, List, Optional
import sys
from pathlib import Path

import pandas as pd
import numpy as np
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame


class MIDASProtocolStrategy:
    """
    MIDAS Protocol - Asian Session Mean Reversion for MNQ Futures

    Indicators:
    - EMA 200: Exponential Moving Average (Length 200)
    - Velocity (5m): Close[0] - Close[5]
    - ATR Ratio: ATR(14) / ATR_Avg(50)

    Risk Management:
    - Long-only positions
    - Max 1 position at a time
    - Max daily loss: $300
    - Fixed SL: 20 points ($40), TP: 120 points ($240)
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str,
        symbols: List[str],
        config: Dict,
    ):
        """Initialize MIDAS Protocol strategy"""
        self.logger = logging.getLogger("magellan.midas_protocol")

        # API clients
        self.trading_client = TradingClient(api_key, api_secret, paper=True)
        self.data_client = StockHistoricalDataClient(api_key, api_secret)

        # Configuration
        self.config = config
        self.symbols = symbols
        self.symbol = symbols[0]  # MNQ only

        # Indicator parameters
        self.ema_period = config["indicators"]["ema_period"]
        self.velocity_lookback = config["indicators"]["velocity_lookback"]
        self.atr_period = config["indicators"]["atr_period"]
        self.atr_avg_period = config["indicators"]["atr_avg_period"]

        # Entry parameters
        self.glitch_velocity = config["entry_logic"]["glitch_guard"][
            "velocity_threshold"
        ]

        # Setup A (Crash Reversal)
        self.setup_a_vel_min = config["entry_logic"]["setup_a_crash_reversal"][
            "velocity_min"
        ]
        self.setup_a_vel_max = config["entry_logic"]["setup_a_crash_reversal"][
            "velocity_max"
        ]
        self.setup_a_ema_dist = config["entry_logic"]["setup_a_crash_reversal"][
            "ema_distance_max"
        ]
        self.setup_a_atr_min = config["entry_logic"]["setup_a_crash_reversal"][
            "atr_ratio_min"
        ]

        # Setup B (Quiet Drift)
        self.setup_b_vel_max = config["entry_logic"]["setup_b_quiet_drift"][
            "velocity_max"
        ]
        self.setup_b_ema_dist = config["entry_logic"]["setup_b_quiet_drift"][
            "ema_distance_max"
        ]
        self.setup_b_atr_min = config["entry_logic"]["setup_b_quiet_drift"][
            "atr_ratio_min"
        ]
        self.setup_b_atr_max = config["entry_logic"]["setup_b_quiet_drift"][
            "atr_ratio_max"
        ]

        # Exit parameters
        self.stop_loss_points = config["exit_logic"]["stop_loss_points"]
        self.take_profit_points = config["exit_logic"]["take_profit_points"]
        self.time_exit_bars = config["exit_logic"]["time_based_exit_bars"]

        # Risk management
        self.max_daily_loss = config["risk_management"]["max_daily_loss_dollars"]
        self.max_positions = config["risk_management"]["max_position_size"]
        self.point_value = config["symbol_parameters"]["MNQ"]["point_value"]

        # State tracking
        self.positions = {}  # {symbol: {entry_price, entry_time, entry_bar_count}}
        self.daily_pnl = 0.0
        self.trades_today = 0
        self.session_halted = False

        # Market data cache
        self.current_bars = {}

        self.logger.info("✓ MIDAS Protocol Strategy initialized")
        self.logger.info(f"  Symbol: {self.symbol}")
        self.logger.info(f"  Max Daily Loss: ${self.max_daily_loss}")
        self.logger.info(f"  Session: 02:00-06:00 UTC")

    def calculate_ema(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return series.ewm(span=period, adjust=False).mean()

    def calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """
        Calculate Average True Range (ATR)

        True Range = max(high - low, |high - prev_close|, |low - prev_close|)
        ATR = Exponential Moving Average of True Range
        """
        high = df["high"]
        low = df["low"]
        close = df["close"]
        prev_close = close.shift(1)

        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.ewm(span=period, adjust=False).mean()

        return atr

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all required indicators:
        - EMA 200
        - Velocity (5 bars)
        - ATR(14)
        - ATR_Avg(50)
        - ATR Ratio
        """
        df = df.copy()

        # EMA 200
        df["ema_200"] = self.calculate_ema(df["close"], self.ema_period)

        # Velocity: Close[0] - Close[5]
        df["velocity"] = df["close"] - df["close"].shift(self.velocity_lookback)

        # ATR(14)
        df["atr_14"] = self.calculate_atr(df, self.atr_period)

        # ATR_Avg(50): Simple Moving Average of ATR(14)
        df["atr_avg_50"] = df["atr_14"].rolling(window=self.atr_avg_period).mean()

        # ATR Ratio: ATR(14) / ATR_Avg(50)
        df["atr_ratio"] = df["atr_14"] / df["atr_avg_50"]

        # Distance to EMA 200 (absolute points)
        df["ema_distance"] = (df["close"] - df["ema_200"]).abs()

        return df

    def is_in_session(self) -> bool:
        """
        Check if current time is within Asian session (02:00-06:00 UTC)
        """
        from pytz import timezone

        utc = timezone("UTC")
        now = datetime.now(utc)

        # Check if weekday (0=Monday, 6=Sunday)
        if now.weekday() >= 5:
            return False

        # Check if in session hours (02:00-06:00 UTC)
        session_start = dt_time(2, 0, 0)
        session_end = dt_time(6, 0, 0)
        current_time = now.time()

        return session_start <= current_time <= session_end

    def process_market_data(self):
        """Fetch and process 1-minute bars for MNQ"""
        try:
            # Fetch recent bars (need enough for warmup)
            request = StockBarsRequest(
                symbol_or_symbols=self.symbol,
                timeframe=TimeFrame.Minute,
                start=datetime.now() - timedelta(minutes=300),  # 5 hours of data
                end=datetime.now(),
            )

            bars = self.data_client.get_stock_bars(request)

            if bars and self.symbol in bars:
                df = bars[self.symbol].df
                df = self.calculate_indicators(df)
                self.current_bars[self.symbol] = df

                self.logger.debug(f"Fetched {len(df)} bars for {self.symbol}")

        except Exception as e:
            self.logger.error(f"Error fetching market data: {e}", exc_info=True)

    def evaluate_entry(self, symbol: str) -> Optional[str]:
        """
        Evaluate entry criteria for MIDAS Protocol

        Returns:
            'setup_a' for Crash Reversal
            'setup_b' for Quiet Drift
            None if no entry signal
        """
        if symbol not in self.current_bars:
            return None

        df = self.current_bars[symbol]

        if len(df) < max(self.ema_period, self.atr_avg_period):
            self.logger.debug(f"Insufficient data for {symbol}")
            return None

        # Get current bar
        current = df.iloc[-1]

        velocity = current["velocity"]
        ema_distance = current["ema_distance"]
        atr_ratio = current["atr_ratio"]

        # Check for NaN values
        if pd.isna(velocity) or pd.isna(ema_distance) or pd.isna(atr_ratio):
            return None

        # GLITCH GUARD: Block trading if velocity < -150
        if velocity < self.glitch_velocity:
            self.logger.warning(
                f"GLITCH GUARD TRIGGERED: Velocity={velocity:.2f} < {self.glitch_velocity}"
            )
            return None

        # SETUP A: Crash Reversal
        # Velocity between -150 and -67
        # EMA distance <= 220 points
        # ATR Ratio > 0.50
        if (
            self.setup_a_vel_min <= velocity <= self.setup_a_vel_max
            and ema_distance <= self.setup_a_ema_dist
            and atr_ratio > self.setup_a_atr_min
        ):

            self.logger.info(f"SETUP A (Crash Reversal) TRIGGERED:")
            self.logger.info(
                f"  Velocity: {velocity:.2f} (range: {self.setup_a_vel_min} to {self.setup_a_vel_max})"
            )
            self.logger.info(
                f"  EMA Distance: {ema_distance:.2f} (<= {self.setup_a_ema_dist})"
            )
            self.logger.info(f"  ATR Ratio: {atr_ratio:.4f} (> {self.setup_a_atr_min})")
            return "setup_a"

        # SETUP B: Quiet Drift
        # Velocity <= 10
        # EMA distance <= 220 points
        # ATR Ratio between 0.06 and 0.50
        if (
            velocity <= self.setup_b_vel_max
            and ema_distance <= self.setup_b_ema_dist
            and self.setup_b_atr_min <= atr_ratio <= self.setup_b_atr_max
        ):

            self.logger.info(f"SETUP B (Quiet Drift) TRIGGERED:")
            self.logger.info(f"  Velocity: {velocity:.2f} (<= {self.setup_b_vel_max})")
            self.logger.info(
                f"  EMA Distance: {ema_distance:.2f} (<= {self.setup_b_ema_dist})"
            )
            self.logger.info(
                f"  ATR Ratio: {atr_ratio:.4f} (range: {self.setup_b_atr_min} to {self.setup_b_atr_max})"
            )
            return "setup_b"

        return None

    def enter_position(self, symbol: str, setup: str):
        """Execute entry order for MIDAS Protocol"""
        try:
            df = self.current_bars[symbol]
            current = df.iloc[-1]
            entry_price = current["close"]

            # Calculate stop loss and take profit
            stop_loss = entry_price - self.stop_loss_points
            take_profit = entry_price + self.take_profit_points

            # Place market order (1 contract)
            order = MarketOrderRequest(
                symbol=symbol, qty=1, side=OrderSide.BUY, time_in_force=TimeInForce.DAY
            )

            result = self.trading_client.submit_order(order)

            # Track position
            self.positions[symbol] = {
                "entry_price": entry_price,
                "entry_time": datetime.now(),
                "entry_bar_count": 0,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "setup": setup,
            }

            self.trades_today += 1

            self.logger.info("=" * 80)
            self.logger.info(f"📈 LONG ENTRY - {symbol} ({setup})")
            self.logger.info(f"  Entry Price: {entry_price:.2f}")
            self.logger.info(
                f"  Stop Loss: {stop_loss:.2f} (-{self.stop_loss_points} pts / $40)"
            )
            self.logger.info(
                f"  Take Profit: {take_profit:.2f} (+{self.take_profit_points} pts / $240)"
            )
            self.logger.info(f"  Time Exit: {self.time_exit_bars} bars (60 minutes)")
            self.logger.info(f"  Order ID: {result.id}")
            self.logger.info("=" * 80)

        except Exception as e:
            self.logger.error(f"Error entering position: {e}", exc_info=True)

    def manage_position(self, symbol: str):
        """Manage existing position with OCO bracket logic"""
        if symbol not in self.positions:
            return

        position = self.positions[symbol]
        df = self.current_bars[symbol]
        current = df.iloc[-1]
        current_price = current["close"]

        # Increment bar count
        position["entry_bar_count"] += 1

        # Check Stop Loss
        if current_price <= position["stop_loss"]:
            self.exit_position(symbol, position["stop_loss"], "Stop Loss Hit")
            return

        # Check Take Profit
        if current_price >= position["take_profit"]:
            self.exit_position(symbol, position["take_profit"], "Take Profit Hit")
            return

        # Check Time-Based Exit (60 bars)
        if position["entry_bar_count"] >= self.time_exit_bars:
            self.exit_position(symbol, current_price, "Time-Based Exit (60 bars)")
            return

    def exit_position(self, symbol: str, exit_price: float, reason: str):
        """Execute exit order"""
        try:
            position = self.positions[symbol]
            entry_price = position["entry_price"]

            # Calculate P&L
            pnl_points = exit_price - entry_price
            pnl_dollars = pnl_points * self.point_value

            # Update daily P&L
            self.daily_pnl += pnl_dollars

            # Place market sell order
            order = MarketOrderRequest(
                symbol=symbol, qty=1, side=OrderSide.SELL, time_in_force=TimeInForce.DAY
            )

            result = self.trading_client.submit_order(order)

            self.logger.info("=" * 80)
            self.logger.info(f"📉 LONG EXIT - {symbol}")
            self.logger.info(f"  Reason: {reason}")
            self.logger.info(f"  Entry: {entry_price:.2f}")
            self.logger.info(f"  Exit: {exit_price:.2f}")
            self.logger.info(f"  P&L: {pnl_points:+.2f} points / ${pnl_dollars:+.2f}")
            self.logger.info(f"  Setup: {position['setup']}")
            self.logger.info(f"  Bars Held: {position['entry_bar_count']}")
            self.logger.info(f"  Daily P&L: ${self.daily_pnl:+.2f}")
            self.logger.info(f"  Order ID: {result.id}")
            self.logger.info("=" * 80)

            # Remove from positions
            del self.positions[symbol]

            # Check daily loss limit
            if self.daily_pnl <= -self.max_daily_loss:
                self.logger.warning("=" * 80)
                self.logger.warning(f"🛑 MAX DAILY LOSS HIT: ${self.daily_pnl:.2f}")
                self.logger.warning(f"   HALTING ALL TRADING UNTIL NEXT SESSION")
                self.logger.warning("=" * 80)
                self.session_halted = True

        except Exception as e:
            self.logger.error(f"Error exiting position: {e}", exc_info=True)

    def check_risk_gates(self) -> bool:
        """
        Check if trading is allowed based on risk gates

        Returns:
            True if trading allowed, False otherwise
        """
        # Check session halt
        if self.session_halted:
            return False

        # Check max positions
        if len(self.positions) >= self.max_positions:
            return False

        # Check daily loss
        if self.daily_pnl <= -self.max_daily_loss:
            return False

        # Check if in Asian session
        if not self.is_in_session():
            return False

        return True

    def get_status(self) -> Dict:
        """Return current strategy status"""
        return {
            "open_positions": len(self.positions),
            "pnl_today": self.daily_pnl,
            "trades_today": self.trades_today,
            "session_halted": self.session_halted,
            "in_session": self.is_in_session(),
        }

    def close_all_positions(self, reason: str):
        """Emergency close all positions"""
        for symbol in list(self.positions.keys()):
            df = self.current_bars.get(symbol)
            if df is not None and len(df) > 0:
                current_price = df.iloc[-1]["close"]
                self.exit_position(symbol, current_price, reason)

    def reset_daily_state(self):
        """Reset daily tracking at session start"""
        self.daily_pnl = 0.0
        self.trades_today = 0
        self.session_halted = False
        self.logger.info("Daily state reset for new session")

    def generate_end_of_day_report(self):
        """Generate EOD summary"""
        self.logger.info("=" * 80)
        self.logger.info("📊 MIDAS PROTOCOL - END OF SESSION REPORT")
        self.logger.info(f"  Total P&L: ${self.daily_pnl:+.2f}")
        self.logger.info(f"  Trades Executed: {self.trades_today}")
        self.logger.info(f"  Open Positions: {len(self.positions)}")
        self.logger.info("=" * 80)
