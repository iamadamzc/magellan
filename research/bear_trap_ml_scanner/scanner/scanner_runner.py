#!/usr/bin/env python3
"""
Selloff Scanner - Main Runner

Real-time scanner for intraday selloff opportunities.
Polls every minute for -10% selloffs during market hours.
"""

import os
import sys
import time
import logging
import signal
from datetime import datetime, time as dt_time
from pathlib import Path
from dotenv import load_dotenv
import pytz

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent.parent)
sys.path.insert(0, project_root)

from research.bear_trap_ml_scanner.scanner import (
    SelloffDetector,
    UniverseManager,
    PriorityScorer,
    AlertManager,
)

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
            logging.FileHandler("research/bear_trap_ml_scanner/scanner/scanner.log"),
        ],
    )
    return logging.getLogger("scanner.main")


def is_market_hours() -> bool:
    """Check if currently in market hours (9:30-16:00 ET)"""
    et = pytz.timezone("America/New_York")
    now = datetime.now(et)
    
    # Check if weekday
    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    
    # Check if in trading hours
    market_open = dt_time(9, 30)
    market_close = dt_time(16, 0)
    current_time = now.time()
    
    return market_open <= current_time <= market_close


def is_midday() -> bool:
    """Check if currently in midday window (11:30-14:00 ET)"""
    et = pytz.timezone("America/New_York")
    now = datetime.now(et)
    
    midday_start = dt_time(11, 30)
    midday_end = dt_time(14, 0)
    current_time = now.time()
    
    return midday_start <= current_time <= midday_end


def main():
    """Main scanner loop"""
    global shutdown_flag
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Setup
    logger = setup_logging()
    load_dotenv()
    
    logger.info("="*80)
    logger.info("Selloff Scanner - Starting")
    logger.info("="*80)
    
    # Get API credentials
    api_key = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
    api_secret = os.getenv("ALPACA_API_SECRET") or os.getenv("APCA_API_SECRET_KEY")
    
    if not api_key or not api_secret:
        logger.error("Missing Alpaca API credentials")
        return 1
    
    # Configuration
    THRESHOLD = -10.0
    UNIVERSE_MODE = "static_50"  # or "static_250"
    MIDDAY_ONLY = True  # Set to False to scan all day
    SCAN_INTERVAL = 60  # seconds
    
    # Initialize components
    logger.info(f"Initializing scanner...")
    logger.info(f"  Threshold: {THRESHOLD}%")
    logger.info(f"  Universe: {UNIVERSE_MODE}")
    logger.info(f"  Midday only: {MIDDAY_ONLY}")
    
    universe = UniverseManager(mode=UNIVERSE_MODE)
    symbols = universe.get_symbols()
    logger.info(f"  Symbols: {len(symbols)}")
    
    # Time filter for midday
    time_filter = (11, 30, 14, 0) if MIDDAY_ONLY else None
    
    detector = SelloffDetector(
        api_key=api_key,
        api_secret=api_secret,
        threshold_pct=THRESHOLD,
        time_filter=time_filter,
    )
    
    scorer = PriorityScorer()
    alert_manager = AlertManager()
    
    logger.info("✓ Scanner initialized")
    logger.info("="*80)
    
    # Main loop
    last_scan = None
    scan_count = 0
    
    try:
        while not shutdown_flag:
            # Check if market hours
            if not is_market_hours():
                logger.debug("Outside market hours, sleeping...")
                time.sleep(60)
                continue
            
            # Check if midday (if filter enabled)
            if MIDDAY_ONLY and not is_midday():
                logger.debug("Outside midday window, sleeping...")
                time.sleep(60)
                continue
            
            # Scan universe
            scan_count += 1
            logger.info(f"\n[Scan #{scan_count}] Scanning {len(symbols)} symbols...")
            
            events = detector.scan_universe(symbols)
            
            if events:
                logger.info(f"Found {len(events)} selloff(s)")
                
                for event in events:
                    # Score event
                    score_data = scorer.score_event(event)
                    
                    # Send alert
                    alert_manager.send_alert(event, score_data)
            else:
                logger.info("No selloffs detected")
            
            last_scan = datetime.now()
            
            # Summary every 10 scans
            if scan_count % 10 == 0:
                summary = alert_manager.get_daily_summary()
                logger.info(f"\n{'='*80}")
                logger.info(f"Daily Summary (after {scan_count} scans):")
                logger.info(f"  Total alerts: {summary['total_alerts']}")
                logger.info(f"  By tier: {summary['by_tier']}")
                logger.info(f"  By symbol: {summary['by_symbol']}")
                logger.info(f"{'='*80}\n")
            
            # Sleep until next scan
            time.sleep(SCAN_INTERVAL)
    
    except KeyboardInterrupt:
        logger.warning("Received keyboard interrupt")
    
    finally:
        # Shutdown
        logger.info("\n" + "="*80)
        logger.info("Scanner shutting down...")
        
        summary = alert_manager.get_daily_summary()
        logger.info(f"Final Summary:")
        logger.info(f"  Total scans: {scan_count}")
        logger.info(f"  Total alerts: {summary['total_alerts']}")
        logger.info(f"  By tier: {summary['by_tier']}")
        logger.info(f"  By symbol: {summary['by_symbol']}")
        logger.info("="*80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
