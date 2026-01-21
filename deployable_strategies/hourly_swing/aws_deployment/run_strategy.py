#!/usr/bin/env python3
"""
Magellan Hourly Swing Strategy - AWS Production Runner
Strategy: Hourly Swing (RSI Hysteresis on 1H bars)
"""

import os
import sys
import json
import logging
import time
from datetime import datetime, time as dt_time, timedelta
import signal

sys.path.insert(0, "/home/ssm-user/magellan")

# Direct Alpaca API imports - NO CACHE for production
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from src.features import calculate_rsi
import boto3
import pandas as pd
import csv
from pathlib import Path

shutdown_flag = False


def signal_handler(signum, frame):
    global shutdown_flag
    logging.warning(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_flag = True


def load_config():
    config_path = os.getenv(
        "CONFIG_PATH",
        "/home/ssm-user/magellan/deployable_strategies/hourly_swing/aws_deployment/config.json",
    )
    with open(config_path, "r") as f:
        return json.load(f)


def get_alpaca_credentials(account_id):
    ssm = boto3.client("ssm", region_name="us-east-2")
    api_key_path = f"/magellan/alpaca/{account_id}/API_KEY"
    api_secret_path = f"/magellan/alpaca/{account_id}/API_SECRET"

    api_key = ssm.get_parameter(Name=api_key_path, WithDecryption=True)["Parameter"][
        "Value"
    ]
    api_secret = ssm.get_parameter(Name=api_secret_path, WithDecryption=True)[
        "Parameter"
    ]["Value"]

    return api_key, api_secret


def setup_logging(config):
    log_level = config["monitoring"].get("log_level", "INFO")
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger("magellan.hourly_swing")


def is_market_hours():
    """Check if currently in market hours (9:30-16:00 ET)"""
    from pytz import timezone

    et = timezone("America/New_York")
    now = datetime.now(et)

    if now.weekday() >= 5:  # Weekend
        return False

    market_open = dt_time(9, 30)
    market_close = dt_time(16, 0)
    current_time = now.time()

    return market_open <= current_time <= market_close


class HourlySwingExecutor:
    """Executes Hourly Swing strategy for TSLA and NVDA"""

    def __init__(self, api_key, api_secret, base_url, symbols, config):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.symbols = symbols
        self.config = config
        self.positions = {}
        self.logger = logging.getLogger("magellan.hourly_swing")

        # Initialize Alpaca data client for live market data
        self.data_client = StockHistoricalDataClient(api_key, api_secret)

        # Initialize Alpaca trading client for order execution
        self.trading_client = TradingClient(api_key, api_secret, paper=True)

        # Symbol-specific parameters
        self.params = config["strategy_parameters"]

    def process_hourly_signals(self):
        """Check RSI on hourly bars and generate signals"""

        for symbol in self.symbols:
            try:
                # Get symbol-specific parameters
                symbol_params = self.params[symbol]

                # Fetch hourly data via direct API call - NO CACHE
                # Need ~84 bars for RSI warmup
                start_date = datetime.now() - timedelta(days=30)
                end_date = datetime.now()

                request = StockBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=TimeFrame.Hour,
                    start=start_date,
                    end=end_date,
                    feed="sip",  # Market Data Plus (paid plan)
                )

                bars = self.data_client.get_stock_bars(request)

                # Convert BarSet to DataFrame (correct BarSet.data access)
                if bars and bars.data and symbol in bars.data:
                    bar_list = bars.data[symbol]
                    data = pd.DataFrame(
                        [
                            {
                                "timestamp": bar.timestamp,
                                "open": bar.open,
                                "high": bar.high,
                                "low": bar.low,
                                "close": bar.close,
                                "volume": bar.volume,
                            }
                            for bar in bar_list
                        ]
                    )
                    data.set_index("timestamp", inplace=True)
                else:
                    self.logger.warning(f"No data for {symbol}")
                    continue

                # Calculate RSI
                rsi = calculate_rsi(data["close"], period=symbol_params["rsi_period"])
                current_rsi = rsi.iloc[-1]

                # Get current position state
                current_position = self.positions.get(symbol, "flat")

                # Hysteresis logic
                if (
                    current_position == "flat"
                    and current_rsi > symbol_params["hysteresis_upper"]
                ):
                    self.logger.info(
                        f"{symbol}: RSI={current_rsi:.2f} > {symbol_params['hysteresis_upper']} → ENTER LONG"
                    )
                    self._enter_long(symbol)
                    self.positions[symbol] = "long"

                elif (
                    current_position == "long"
                    and current_rsi < symbol_params["hysteresis_lower"]
                ):
                    self.logger.info(
                        f"{symbol}: RSI={current_rsi:.2f} < {symbol_params['hysteresis_lower']} → EXIT"
                    )
                    self._exit_position(symbol)
                    self.positions[symbol] = "flat"

                else:
                    self.logger.debug(
                        f"{symbol}: RSI={current_rsi:.2f} → HOLD ({current_position})"
                    )

            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {e}", exc_info=True)

    def _enter_long(self, symbol):
        """Place buy order via Alpaca API"""
        try:
            # Check if already have position (prevent double-entry)
            try:
                position = self.trading_client.get_open_position(symbol)
                self.logger.warning(
                    f"Already have position in {symbol}, skipping entry"
                )
                return
            except Exception:
                pass  # No position exists, proceed with order

            # Get account equity for position sizing
            account = self.trading_client.get_account()
            equity = float(account.equity)
            position_size = equity * 0.10  # 10% per position

            # Get current price via latest quote
            quote_request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quote = self.data_client.get_stock_latest_quote(quote_request)
            current_price = float(quote[symbol].ask_price)

            # Calculate quantity
            qty = int(position_size / current_price)

            if qty < 1:
                self.logger.warning(
                    f"Position size too small for {symbol} (${position_size:.2f} @ ${current_price:.2f}), skipping"
                )
                return

            # Place market order
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY,
            )

            order = self.trading_client.submit_order(order_request)
            self.logger.info(
                f"✅ LONG entry for {symbol}: {qty} shares @ ${current_price:.2f} (Order ID: {order.id})"
            )

            # Log trade to CSV
            self._log_trade(symbol, "ENTRY", qty, current_price, order.id)

        except Exception as e:
            self.logger.error(
                f"❌ Error entering LONG for {symbol}: {e}", exc_info=True
            )

    def _exit_position(self, symbol):
        """Close position via Alpaca API"""
        try:
            # Check if have position to exit
            try:
                position = self.trading_client.get_open_position(symbol)
                qty = int(float(position.qty))
            except Exception:
                self.logger.info(f"No position in {symbol} to exit, skipping")
                return

            # Get current price via latest quote
            quote_request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quote = self.data_client.get_stock_latest_quote(quote_request)
            current_price = float(quote[symbol].bid_price)

            # Place market sell order
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )

            order = self.trading_client.submit_order(order_request)
            self.logger.info(
                f"✅ EXIT position for {symbol}: {qty} shares @ ${current_price:.2f} (Order ID: {order.id})"
            )

            # Log trade to CSV
            self._log_trade(symbol, "EXIT", qty, current_price, order.id)

        except Exception as e:
            self.logger.error(
                f"❌ Error exiting position for {symbol}: {e}", exc_info=True
            )

    def _log_trade(self, symbol, action, qty, price, order_id):
        """Log trade to CSV file"""
        log_dir = self.config["monitoring"]["log_directory"]
        Path(log_dir).mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime("%Y%m%d")
        log_file = Path(log_dir) / f"hourly_swing_trades_{date_str}.csv"

        file_exists = log_file.is_file()

        with open(log_file, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(
                    ["timestamp", "symbol", "action", "qty", "price", "order_id"]
                )

            writer.writerow(
                [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    symbol,
                    action,
                    qty,
                    f"{price:.2f}",
                    order_id,
                ]
            )

    def manage_positions(self):
        """Monitor and manage existing positions"""
        # TODO: Implement position management (stops, trailing, etc.)
        pass

    def check_risk_gates(self):
        """Check if any risk limits are breached"""
        # TODO: Implement risk gate checks
        pass

    def get_status(self):
        """Return current strategy status"""
        return {
            "positions": self.positions,
            "open_positions": len([p for p in self.positions.values() if p == "long"]),
            "pnl_today": 0.0,  # TODO: Calculate from Alpaca
            "trades_today": 0,
        }


def main():
    """Main execution loop - checks every hour during market hours"""
    global shutdown_flag

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    config = load_config()
    logger = setup_logging(config)

    logger.info("=" * 80)
    logger.info("Magellan Hourly Swing Strategy - Starting")
    logger.info(f"Account: {config['account_info']['account_id']}")
    logger.info(f"Capital: ${config['account_info']['initial_capital']:,}")
    logger.info(f"Symbols: {', '.join(config['symbols'])}")
    logger.info("=" * 80)

    account_id = config["account_info"]["account_id"]
    try:
        api_key, api_secret = get_alpaca_credentials(account_id)
        logger.info("✓ Retrieved Alpaca API credentials from SSM")
    except Exception as e:
        logger.error(f"✗ Failed to retrieve credentials: {e}")
        return 1

    executor = HourlySwingExecutor(
        api_key=api_key,
        api_secret=api_secret,
        base_url=config["ssm_parameters"]["base_url"],
        symbols=config["symbols"],
        config=config,
    )

    logger.info("✓ Executor initialized")
    logger.info("Monitoring hourly signals during market hours...")

    last_check_hour = None

    try:
        while not shutdown_flag:
            # Only process during market hours
            if not is_market_hours():
                logger.debug("Outside market hours, sleeping...")
                time.sleep(300)  # 5 minutes
                continue

            # Check signals once per hour
            current_hour = datetime.now().hour
            if current_hour != last_check_hour:
                logger.info(f"Hourly check at {datetime.now().strftime('%H:%M')}")
                executor.process_hourly_signals()
                executor.manage_positions()
                executor.check_risk_gates()
                last_check_hour = current_hour

            # Sleep for 5 minutes before next check
            time.sleep(300)

    except KeyboardInterrupt:
        logger.warning("Received keyboard interrupt")

    finally:
        logger.info("Shutting down strategy...")
        # Close any open positions
        logger.info("Strategy shutdown complete")

    return 0


if __name__ == "__main__":
    sys.exit(main())
