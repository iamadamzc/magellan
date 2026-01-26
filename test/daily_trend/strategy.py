#!/usr/bin/env python3
"""
Magellan Daily Trend Strategy - AWS Production Runner
Strategy: Daily Trend Hysteresis (RSI 55/45)
"""

import os
import sys
import json
import logging
import time
from datetime import datetime, time as dt_time
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
        "/home/ssm-user/magellan/deployable_strategies/daily_trend_hysteresis/aws_deployment/config.json",
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
    return logging.getLogger("magellan.daily_trend")


def is_signal_time():
    """Check if it's time to generate signals (16:05 ET)"""
    from pytz import timezone

    et = timezone("America/New_York")
    now = datetime.now(et)

    # Must be weekday
    if now.weekday() >= 5:
        return False

    # Check if 16:05
    target_time = dt_time(16, 5)
    current_time = now.time()

    # Window: 16:05:00 - 16:05:59
    return (
        target_time.hour == current_time.hour
        and target_time.minute == current_time.minute
    )


def is_execution_time():
    """Check if it's time to execute orders (09:30 ET)"""
    from pytz import timezone

    et = timezone("America/New_York")
    now = datetime.now(et)

    if now.weekday() >= 5:
        return False

    target_time = dt_time(9, 30)
    current_time = now.time()

    # Window: 09:30:00 - 09:31:00
    return (
        target_time.hour == current_time.hour
        and target_time.minute == current_time.minute
    )


class DailyTrendExecutor:
    """Executes Daily Trend Hysteresis strategy"""

    def __init__(self, api_key, api_secret, base_url, symbols, config):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.symbols = symbols
        self.config = config
        self.signals = {}
        self.positions = {}

        # Initialize Alpaca data client - use cache if USE_ARCHIVED_DATA is true
        use_cache = os.getenv('USE_ARCHIVED_DATA', 'false').lower() == 'true'
        if use_cache:
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from src.data_cache import DataCache
            self.data_client = DataCache(api_key, api_secret)
            logging.info("📦 Using DataCache for historical data")
        else:
            self.data_client = StockHistoricalDataClient(api_key, api_secret)
            logging.info("🔴 Using live Alpaca API for historical data")

        # Initialize Alpaca trading client for order execution
        self.trading_client = TradingClient(api_key, api_secret, paper=True)

    def generate_signals(self):
        """Generate entry/exit signals based on RSI"""
        logger = logging.getLogger("magellan.daily_trend")
        logger.info("Generating daily signals...")

        from datetime import timedelta

        for symbol in self.symbols:
            try:
                # Get symbol-specific parameters
                symbol_params = self.config["symbol_parameters"].get(symbol, {})
                rsi_period = symbol_params.get("rsi_period", 28)
                upper_band = symbol_params.get("hysteresis_upper", 55)
                lower_band = symbol_params.get("hysteresis_lower", 45)

                # Fetch daily data via direct API call - NO CACHE
                start_date = datetime.now() - timedelta(days=150)
                end_date = datetime.now()

                request = StockBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=TimeFrame.Day,
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
                    logger.warning(f"No data for {symbol}")
                    continue

                # Calculate RSI
                rsi = calculate_rsi(data["close"], period=rsi_period)
                current_rsi = rsi.iloc[-1]

                # Determine signal based on hysteresis
                if current_rsi > upper_band:
                    self.signals[symbol] = "BUY"
                    logger.info(f"{symbol}: RSI={current_rsi:.2f} > {upper_band} → BUY")
                elif current_rsi < lower_band:
                    self.signals[symbol] = "SELL"
                    logger.info(
                        f"{symbol}: RSI={current_rsi:.2f} < {lower_band} → SELL"
                    )
                else:
                    self.signals[symbol] = "HOLD"
                    logger.info(f"{symbol}: RSI={current_rsi:.2f} → HOLD")

            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")

        # Save signals to file for execution tomorrow
        signal_file = "/home/ssm-user/magellan/deployable_strategies/daily_trend_hysteresis/aws_deployment/signals.json"
        with open(signal_file, "w") as f:
            json.dump(
                {"date": datetime.now().strftime("%Y-%m-%d"), "signals": self.signals},
                f,
                indent=2,
            )

        logger.info(f"Signals saved to {signal_file}")

    def execute_signals(self):
        """Execute pending signals at market open"""
        logger = logging.getLogger("magellan.daily_trend")
        logger.info("Executing signals...")

        # Load signals from file
        signal_file = "/home/ssm-user/magellan/deployable_strategies/daily_trend_hysteresis/aws_deployment/signals.json"
        try:
            with open(signal_file, "r") as f:
                signal_data = json.load(f)
                signals = signal_data["signals"]
        except FileNotFoundError:
            logger.warning("No signal file found, skipping execution")
            return

        # Execute each signal
        for symbol, signal in signals.items():
            try:
                if signal == "BUY":
                    self._place_buy_order(symbol)
                elif signal == "SELL":
                    self._place_sell_order(symbol)
                else:
                    logger.info(f"{symbol}: HOLD - no action")
            except Exception as e:
                logger.error(f"Error executing signal for {symbol}: {e}")

        logger.info("Signal execution complete")

    def _place_buy_order(self, symbol):
        """Place buy order via Alpaca API"""
        logger = logging.getLogger("magellan.daily_trend")

        try:
            # Check if already have position (prevent double-entry)
            try:
                position = self.trading_client.get_open_position(symbol)
                logger.warning(f"Already have position in {symbol}, skipping buy")
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
                logger.warning(
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
            logger.info(
                f"✅ BUY order placed for {symbol}: {qty} shares @ ${current_price:.2f} (Order ID: {order.id})"
            )

            # Log trade to CSV
            self._log_trade(symbol, "BUY", qty, current_price, order.id)

        except Exception as e:
            logger.error(f"❌ Error placing BUY order for {symbol}: {e}", exc_info=True)

    def _place_sell_order(self, symbol):
        """Place sell order via Alpaca API"""
        logger = logging.getLogger("magellan.daily_trend")

        try:
            # Check if have position to sell
            try:
                position = self.trading_client.get_open_position(symbol)
                qty = int(float(position.qty))
            except Exception:
                logger.info(f"No position in {symbol} to sell, skipping")
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
            logger.info(
                f"✅ SELL order placed for {symbol}: {qty} shares @ ${current_price:.2f} (Order ID: {order.id})"
            )

            # Log trade to CSV
            self._log_trade(symbol, "SELL", qty, current_price, order.id)

        except Exception as e:
            logger.error(
                f"❌ Error placing SELL order for {symbol}: {e}", exc_info=True
            )

    def _log_trade(self, symbol, action, qty, price, order_id):
        """Log trade to CSV file"""
        log_dir = self.config["monitoring"]["log_directory"]
        Path(log_dir).mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime("%Y%m%d")
        log_file = Path(log_dir) / f"daily_trend_trades_{date_str}.csv"

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


def main():
    """Main execution loop - runs 24/7, triggers at specific times"""
    global shutdown_flag

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    config = load_config()
    logger = setup_logging(config)

    logger.info("=" * 80)
    logger.info("Magellan Daily Trend Strategy - Starting")
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

    executor = DailyTrendExecutor(
        api_key=api_key,
        api_secret=api_secret,
        base_url=config["ssm_parameters"]["base_url"],
        symbols=config["symbols"],
        config=config,
    )

    logger.info("✓ Executor initialized")
    logger.info(
        "Waiting for signal generation time (16:05 ET) or execution time (09:30 ET)..."
    )

    signal_generated_today = False
    execution_done_today = False

    try:
        while not shutdown_flag:
            current_date = datetime.now().strftime("%Y-%m-%d")

            # Reset flags on new day
            if datetime.now().hour == 0 and datetime.now().minute == 0:
                signal_generated_today = False
                execution_done_today = False
                logger.info(f"New trading day: {current_date}")

            # Generate signals at 16:05
            if is_signal_time() and not signal_generated_today:
                executor.generate_signals()
                signal_generated_today = True

            # Execute signals at 09:30
            if is_execution_time() and not execution_done_today:
                executor.execute_signals()
                execution_done_today = True

            # Sleep for 30 seconds
            time.sleep(30)

    except KeyboardInterrupt:
        logger.warning("Received keyboard interrupt")

    finally:
        logger.info("Strategy shutdown complete")

    return 0


if __name__ == "__main__":
    sys.exit(main())
