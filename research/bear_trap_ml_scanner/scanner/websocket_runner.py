#!/usr/bin/env python3
"""
WebSocket Scanner Runner - Real-Time Selloff Detection

Uses Alpaca WebSocket streaming for instant selloff detection.
Zero polling overhead, sub-second latency.
Supports full market coverage (8,000+ symbols).
"""

import os
import sys
import asyncio
import logging
import signal
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent.parent)
sys.path.insert(0, project_root)

from research.bear_trap_ml_scanner.scanner import (
    PriorityScorer,
    AlertManager,
)
from research.bear_trap_ml_scanner.scanner.websocket_scanner import WebSocketScanner
from research.bear_trap_ml_scanner.scanner.dynamic_universe import DynamicUniverseBuilder

# Global shutdown flag
shutdown_flag = False


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global shutdown_flag
    logging.warning(f"Received signal {signum}, shutting down...")
    shutdown_flag = True


def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("research/bear_trap_ml_scanner/scanner/websocket_scanner.log"),
        ],
    )
    return logging.getLogger("scanner.websocket_main")


async def main():
    """Main WebSocket scanner"""
    global shutdown_flag
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Setup
    logger = setup_logging()
    load_dotenv()
    
    logger.info("="*80)
    logger.info("WebSocket Selloff Scanner - Starting")
    logger.info("Real-time streaming with Market Data Plus")
    logger.info("="*80)
    
    # Get API credentials
    api_key = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
    api_secret = os.getenv("ALPACA_API_SECRET") or os.getenv("APCA_API_SECRET_KEY")
    
    if not api_key or not api_secret:
        logger.error("Missing Alpaca API credentials")
        return 1
    
    # Configuration
    THRESHOLD = -10.0
    UNIVERSE_MODE = "full"  # "small_mid" (~500) or "full" (~8,000)
    MIDDAY_ONLY = True  # Set to False to scan all day
    
    logger.info(f"Configuration:")
    logger.info(f"  Threshold: {THRESHOLD}%")
    logger.info(f"  Universe: {UNIVERSE_MODE}")
    logger.info(f"  Midday only: {MIDDAY_ONLY}")
    
    # Build universe
    logger.info(f"\nBuilding symbol universe...")
    universe_builder = DynamicUniverseBuilder(api_key, api_secret)
    symbols = universe_builder.get_recommended_universe(mode=UNIVERSE_MODE)
    
    logger.info(f"✓ Universe built: {len(symbols)} symbols")
    
    # Show sample
    logger.info(f"  Sample: {', '.join(symbols[:20])}...")
    
    # Time filter for midday
    time_filter = (11, 30, 14, 0) if MIDDAY_ONLY else None
    
    # Initialize components
    scorer = PriorityScorer()
    alert_manager = AlertManager()
    
    # Create WebSocket scanner
    scanner = WebSocketScanner(
        api_key=api_key,
        api_secret=api_secret,
        symbols=symbols,
        threshold_pct=THRESHOLD,
        time_filter=time_filter,
        scorer=scorer,
        alert_manager=alert_manager,
    )
    
    logger.info("✓ WebSocket scanner initialized")
    logger.info("="*80)
    
    # Run scanner
    try:
        await scanner.run()
    except KeyboardInterrupt:
        logger.warning("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Scanner error: {e}", exc_info=True)
    finally:
        # Shutdown
        logger.info("\n" + "="*80)
        logger.info("Scanner shutting down...")
        
        summary = alert_manager.get_daily_summary()
        logger.info(f"Daily Summary:")
        logger.info(f"  Total alerts: {summary['total_alerts']}")
        logger.info(f"  By tier: {summary['by_tier']}")
        logger.info(f"  By symbol: {summary['by_symbol']}")
        logger.info("="*80)
        
        scanner.stop()
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
