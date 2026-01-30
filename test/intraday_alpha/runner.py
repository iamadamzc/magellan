#!/usr/bin/env python3
"""
Simple runner for Intraday Alpha Strategy (V1.0 Archive)
For testing purposes only - uses archived data by default
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from test.intraday_alpha.strategy import IntradayAlphaStrategy


def load_config():
    """Load strategy configuration"""
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, "r") as f:
        return json.load(f)


def setup_logging():
    """Setup logging"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger("magellan.intraday_alpha")


def main():
    """Main runner - single execution for testing"""
    logger = setup_logging()

    logger.info("=" * 80)
    logger.info("Magellan Intraday Alpha Strategy (V1.0 Archive) - Test Run")
    logger.info("=" * 80)

    # Load configuration
    config = load_config()
    logger.info(f"Strategy: {config['strategy_name']}")
    logger.info(f"Version: {config['version']}")
    logger.info(f"Symbols: {', '.join(config['symbols'])}")
    logger.info(f"Status: {config['status']}")

    # Check for API credentials
    api_key = os.getenv("ALPACA_API_KEY")
    api_secret = os.getenv("ALPACA_API_SECRET")

    if not api_key or not api_secret:
        logger.error("❌ Missing Alpaca API credentials")
        logger.error("Set ALPACA_API_KEY and ALPACA_API_SECRET environment variables")
        return 1

    # Force use of archived data for testing
    os.environ["USE_ARCHIVED_DATA"] = "true"
    logger.info("📦 Using archived data for testing")

    # Initialize strategy
    strategy = IntradayAlphaStrategy(
        api_key=api_key, api_secret=api_secret, symbols=config["symbols"], config=config
    )

    logger.info("✓ Strategy initialized")
    logger.info("")

    # Process signals once
    logger.info("Processing signals...")
    strategy.process_signals()

    logger.info("")
    logger.info("=" * 80)
    logger.info("Test run complete")
    logger.info("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
