#!/usr/bin/env python3
"""
Universal Strategy Runner Template
Supports both cached data (local/CI/CD) and live API (production)

USAGE:
1. Copy this file to prod/strategy_name/runner.py
2. Replace {STRATEGY_NAME}, {STRATEGY_DISPLAY_NAME}, {STRATEGY_CLASS}
3. Import the strategy class from strategy.py
4. Customize as needed

ENVIRONMENT DETECTION:
- USE_ARCHIVED_DATA=true  → Uses DataCache (local/CI/CD testing)
- USE_ARCHIVED_DATA=false → Uses live Alpaca API (production)
- No variable set          → Uses live Alpaca API (production default)
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def get_credentials():
    """Get API credentials based on environment"""
    env = os.getenv("ENVIRONMENT", "production")

    if env == "production":
        # Production: AWS SSM Parameter Store
        import boto3

        ssm = boto3.client("ssm", region_name="us-east-2")

        account_id = os.getenv("ALPACA_ACCOUNT_ID")
        if not account_id:
            raise ValueError("ALPACA_ACCOUNT_ID environment variable not set")

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


def get_data_client(api_key, api_secret):
    """Get data client based on environment"""
    use_cache = os.getenv("USE_ARCHIVED_DATA", "false").lower() == "true"

    if use_cache:
        # Testing/CI/CD: Cached data
        from src.data_cache import DataCache

        logging.info("📦 Using cached data (USE_ARCHIVED_DATA=true)")
        return DataCache(api_key, api_secret)
    else:
        # Production: Live API
        from alpaca.data.historical import StockHistoricalDataClient

        logging.info("🔴 Using live Alpaca API (production mode)")
        return StockHistoricalDataClient(api_key, api_secret)


def get_trading_client(api_key, api_secret):
    """Get trading client"""
    from alpaca.trading.client import TradingClient

    # Use paper trading (for now)
    paper = os.getenv("ALPACA_PAPER", "true").lower() == "true"
    return TradingClient(api_key, api_secret, paper=paper)


def load_config():
    """Load strategy configuration"""
    config_path = Path(__file__).parent / "config.json"
    with open(config_path) as f:
        return json.load(f)


def main():
    """Main entry point"""
    setup_logging()
    logger = logging.getLogger("magellan.{STRATEGY_NAME}")

    logger.info("=" * 60)
    logger.info("Starting {STRATEGY_DISPLAY_NAME} Strategy")
    logger.info("=" * 60)
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'production')}")
    logger.info(f"Use cached data: {os.getenv('USE_ARCHIVED_DATA', 'false')}")
    logger.info(f"Paper trading: {os.getenv('ALPACA_PAPER', 'true')}")

    try:
        # Load configuration
        config = load_config()
        logger.info("✓ Configuration loaded")

        # Get credentials
        api_key, api_secret = get_credentials()
        logger.info("✓ Credentials retrieved")

        # Get clients
        data_client = get_data_client(api_key, api_secret)
        trading_client = get_trading_client(api_key, api_secret)
        logger.info("✓ Clients initialized")

        # Import and initialize strategy
        # TODO: Replace with actual strategy import
        # from strategy import {STRATEGY_CLASS}
        #
        # strategy = {STRATEGY_CLASS}(
        #     config=config,
        #     data_client=data_client,
        #     trading_client=trading_client
        # )
        # logger.info("✓ Strategy initialized")
        #
        # # Run strategy
        # logger.info("Starting strategy execution...")
        # strategy.run()

        logger.warning("Strategy import not yet configured - see TODO in runner.py")

    except KeyboardInterrupt:
        logger.info("Received shutdown signal, exiting gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
