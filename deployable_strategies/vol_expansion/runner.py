#!/usr/bin/env python3
"""
Magellan Volatility Expansion Entry Strategy - Universal Runner
Account: PA3DDLQCBJSE
Strategy: Vol Expansion (v2.0 Sanitized)

Supports both cached data (local/CI/CD) and live API (production)
"""

import os
import sys
import json
import logging
import time
import signal
from datetime import datetime, time as dt_time
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, project_root)

# Import strategy
from test.vol_expansion.strategy import VolatilityExpansionStrategy

# Global flag for graceful shutdown
shutdown_flag = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_flag
    logging.warning(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_flag = True


def setup_logging(config):
    """Configure logging"""
    log_level = config.get("monitoring", {}).get("log_level", "INFO")

    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    return logging.getLogger("magellan.vol_expansion")


def load_config():
    """Load strategy configuration"""
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, "r") as f:
        return json.load(f)


def get_credentials():
    """Get API credentials based on environment"""
    env = os.getenv("ENVIRONMENT", "production")

    if env == "production":
        # Production: AWS SSM Parameter Store
        import boto3

        ssm = boto3.client("ssm", region_name="us-east-2")

        account_id = os.getenv("ALPACA_ACCOUNT_ID", "PA3DDLQCBJSE")

        api_key = ssm.get_parameter(
            Name=f"/magellan/alpaca/{account_id}/API_KEY", WithDecryption=True
        )["Parameter"]["Value"]

        api_secret = ssm.get_parameter(
            Name=f"/magellan/alpaca/{account_id}/API_SECRET", WithDecryption=True
        )["Parameter"]["Value"]

        return api_key, api_secret
    else:
        # Local/Testing: Environment variables
        from dotenv import load_dotenv

        load_dotenv()

        api_key = os.getenv("ALPACA_API_KEY")
        api_secret = os.getenv("ALPACA_API_SECRET")

        if not api_key or not api_secret:
            raise ValueError("ALPACA_API_KEY and ALPACA_API_SECRET must be set")

        return api_key, api_secret


def is_market_hours():
    """Check if currently in market hours (9:30-16:00 ET)"""
    from pytz import timezone

    et = timezone("America/New_York")
    now = datetime.now(et)

    # Check if weekday
    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        return False

    # Check if in trading hours
    market_open = dt_time(9, 30)
    market_close = dt_time(16, 0)
    current_time = now.time()

    return market_open <= current_time <= market_close


def main():
    """Main execution loop"""
    global shutdown_flag

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Load configuration
    config = load_config()
    logger = setup_logging(config)

    logger.info("=" * 80)
    logger.info("Magellan Volatility Expansion Entry Strategy - Starting")
    logger.info(f"Version: {config['strategy']['version']}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'production')}")
    logger.info(f"Use cached data: {os.getenv('USE_ARCHIVED_DATA', 'false')}")
    logger.info(f"Account: {config['account_info']['account_id']}")
    logger.info(f"Capital: ${config['account_info']['initial_capital']:,}")
    logger.info(f"Symbols: {', '.join(config['symbols'])}")
    logger.info(f"Data Resolution: {config['data_requirements']['timeframe']}")
    logger.info("=" * 80)

    # Get Alpaca credentials
    try:
        api_key, api_secret = get_credentials()
        logger.info("✓ Retrieved Alpaca API credentials")
    except Exception as e:
        logger.error(f"✗ Failed to retrieve credentials: {e}")
        return 1

    # Initialize strategy
    strategy = VolatilityExpansionStrategy(
        api_key=api_key,
        api_secret=api_secret,
        base_url=config["ssm_parameters"]["base_url"],
        symbols=config["symbols"],
        config=config,
    )

    logger.info("✓ Strategy initialized")
    logger.info(
        f"  Entry: ER_zscore < {config['entry_conditions']['effort_result_zscore_max']}, "
        f"RR > {config['entry_conditions']['range_ratio_mean_min']}, "
        f"VR > {config['entry_conditions']['volatility_ratio_min']}"
    )
    logger.info(
        f"  Exit: Target={config['exit_rules']['target_atr_multiple']}×ATR, "
        f"Stop={config['exit_rules']['stop_atr_multiple']}×ATR, "
        f"Time={config['exit_rules']['time_exit_minutes']}min"
    )

    # Main execution loop
    last_health_check = time.time()
    health_check_interval = config["monitoring"]["health_check_interval_seconds"]

    try:
        while not shutdown_flag:
            # Check if market hours
            if not is_market_hours():
                logger.debug("Outside market hours, sleeping...")
                time.sleep(60)
                continue

            # Run strategy logic
            try:
                strategy.process_market_data()

            except Exception as e:
                logger.error(f"Error in strategy execution: {e}", exc_info=True)

            # Health check
            if time.time() - last_health_check > health_check_interval:
                status = strategy.get_status()
                logger.info(
                    f"Health Check - Positions: {status['open_positions']}, "
                    f"P&L Today: ${status['pnl_today']:.2f}, "
                    f"Trades Today: {status['trades_today']}"
                )

                # Regime stats
                for regime, stats in status.get("regime_stats", {}).items():
                    if stats["trades"] > 0:
                        hit_rate = stats["wins"] / stats["trades"]
                        logger.info(
                            f"  {regime}: {stats['trades']} trades, {hit_rate:.1%} win rate"
                        )

                last_health_check = time.time()

            # Strategy checks every 30 seconds (1-min bars, check 2x per bar)
            time.sleep(30)

    except KeyboardInterrupt:
        logger.warning("Received keyboard interrupt")

    finally:
        # Graceful shutdown
        logger.info("Shutting down strategy...")
        strategy.close_all_positions("System shutdown")
        strategy.generate_end_of_day_report()
        logger.info("Strategy shutdown complete")

    return 0


if __name__ == "__main__":
    sys.exit(main())
