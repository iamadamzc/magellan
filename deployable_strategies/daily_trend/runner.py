#!/usr/bin/env python3
"""
Magellan Daily Trend Strategy - Universal Runner
Account: PA3A2699UCJM
Strategy: Daily Trend Hysteresis (RSI) v1.0

Supports both cached data (local/CI/CD) and live API (production)
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, project_root)

# Import the strategy module (which contains DailyTrendExecutor)
from deployable_strategies.daily_trend import strategy


def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger("magellan.daily_trend")


def load_config():
    """Load strategy configuration"""
    # Check for CONFIG_PATH env var first
    config_path = os.getenv("CONFIG_PATH")
    if config_path:
        config_path = Path(config_path)
    else:
        # Fallback to local
        config_path = Path(__file__).parent / "config.json"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at: {config_path}")

    with open(config_path, "r") as f:
        return json.load(f)


def get_credentials():
    """Get API credentials based on environment"""
    env = os.getenv("ENVIRONMENT", "production")

    if env == "production":
        # Production: AWS SSM Parameter Store
        import boto3

        ssm = boto3.client("ssm", region_name="us-east-2")
        account_id = os.getenv("ALPACA_ACCOUNT_ID", "PA3A2699UCJM")

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


def main():
    """Main entry point"""
    logger = setup_logging()

    logger.info("=" * 80)
    logger.info("Magellan Daily Trend Strategy - Starting")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'production')}")
    logger.info(f"Use cached data: {os.getenv('USE_ARCHIVED_DATA', 'false')}")
    logger.info("=" * 80)

    try:
        # Load configuration
        config = load_config()
        logger.info("✓ Configuration loaded")

        # Get credentials
        api_key, api_secret = get_credentials()
        logger.info("✓ Credentials retrieved")

        # Run the strategy's main function
        # The strategy module has its own main() that we'll call
        logger.info("Starting strategy execution...")

        # Set environment variables for the strategy to use
        os.environ["ALPACA_API_KEY"] = api_key
        os.environ["ALPACA_API_SECRET"] = api_secret

        # Call the strategy's main function
        return strategy.main()

    except KeyboardInterrupt:
        logger.info("Received shutdown signal, exiting gracefully...")
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
