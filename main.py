"""
Magellan Data Pipeline - Entry Point
Fetches historical market data using Alpaca Paper API with Market Plus (SIP) subscription.
Supports both simulation and live trading modes.
"""

import os
import json
import argparse
import time
import asyncio
import requests.exceptions
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from src.data_handler import AlpacaDataClient, FMPDataClient, force_resample_ohlcv
from src.features import FeatureEngineer, add_technical_indicators, merge_news_pit, generate_master_signal
from src.discovery import calculate_ic, check_feature_correlation, trim_warmup_period
from src.validation import run_walk_forward_check, print_validation_scorecard, run_optimized_walk_forward_check, print_optimized_scorecard
from src.pnl_tracker import simulate_portfolio, print_virtual_trading_statement
from src.logger import LOG
from src.backtester_pro import run_rolling_backtest, print_stress_test_summary, export_stress_test_results, LIQUIDITY_CAP_USD


# NVDA ISOLATION: Single-ticker focus for Sanity Flight
# Load defaults, but will be overridden by master_config.json if "tickers" key exists
TICKERS = ["NVDA"]

# NVDA ISOLATION ENFORCEMENT: Initial Universe (expanded dynamically)
MAG7_UNIVERSE = frozenset(["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"])

# HOT START PROTOCOL: 252-bar warmup buffer for rolling normalization
# This ensures the 252-bar rolling window in features.py is fully populated at T=0
WARMUP_BUFFER = 252


def validate_mag7_ticker(ticker: str) -> bool:
    """
    Validate that a ticker is within the MAG7 universe.
    
    Args:
        ticker: Stock symbol to validate
        
    Returns:
        True if ticker is in MAG7, False otherwise
    """
    if ticker not in MAG7_UNIVERSE:
        print(f"[WARNING] Ticker {ticker} is NOT in MAG7 universe. Skipping.")
        print(f"[MAG7] Allowed tickers: {', '.join(sorted(MAG7_UNIVERSE))}")
        return False
    return True


TF_MAP = {
    '1Min': TimeFrame.Minute,
    '3Min': TimeFrame(3, TimeFrameUnit.Minute),
    '5Min': TimeFrame(5, TimeFrameUnit.Minute),
    '15Min': TimeFrame(15, TimeFrameUnit.Minute),
    '1Hour': TimeFrame.Hour,
    '1Day': TimeFrame.Day
}


def load_env_file() -> None:
    """Manually load .env file into os.environ."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def load_node_config() -> dict:
    """
    Load all node configurations from config/nodes/master_config.json.
    
    Returns:
        Dict mapping ticker symbols to their node config.
        Example: {'SPY': {'rsi_lookback': 14, 'sentry_gate': 0.0, ...}, ...}
    """
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'nodes', 'master_config.json')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            LOG.config(f"[CONFIG] Loaded master_config.json with {len(config)} ticker profiles")
            return config
        except json.JSONDecodeError as e:
            LOG.error(f"[CONFIG] ERROR: Invalid JSON in master_config.json: {e}")
            return {}
    else:
        LOG.warning(f"[CONFIG] WARNING: master_config.json not found at {config_path}")
        return {}


async def process_ticker(
    ticker: str,
    alpaca_client,
    fmp_client,
    feature_engineer,
    trading_client,
    node_config: dict,
    bar_start: str,
    bar_end: str,
    news_start: str,
    news_end: str,
    allocation_pct: float = 0.25,
    max_position_size: float = None
) -> dict:
    """
    Process a single ticker: fetch data, engineer features, generate signal, execute.
    
    This function encapsulates Steps 1-5 of the trading loop for one symbol,
    and runs concurrently with other tickers via asyncio.gather().
    
    Args:
        ticker: Symbol to process (e.g., 'SPY', 'AAPL')
        alpaca_client: AlpacaDataClient instance for market data
        fmp_client: FMPDataClient instance for fundamentals/news
        feature_engineer: FeatureEngineer instance
        trading_client: AlpacaTradingClient instance for execution
        node_config: Ticker-specific configuration dict
        bar_start: Bar window start date (YYYY-MM-DD)
        bar_end: Bar window end date (YYYY-MM-DD)
        news_start: News window start date
        news_end: News window end date
        allocation_pct: Fraction of equity per ticker (default 0.25 = 25%)
        
    Returns:
        Dict with ticker processing results
    """
    from src.executor import async_execute_trade
    from src.optimizer import calculate_alpha_with_weights
    
    result = {
        'ticker': ticker,
        'success': False,
        'signal': None,
        'trade_result': None,
        'error': None
    }
    
    try:
        # NODE TELEMETRY
        rsi_lookback = node_config.get('rsi_lookback', 14)
        sentry_gate = node_config.get('sentry_gate', 'None')
        interval_str = node_config.get('interval', '1Min')
        
        # Map string to Enum (default to Minute if not found)
        interval_enum = TF_MAP.get(interval_str, TimeFrame.Minute)
        
        LOG.config(f"[NODE] Initialized {ticker} | Lookback: {rsi_lookback} | Gate: {sentry_gate}")
        LOG.config(f"[NODE] {ticker} mapping {interval_str} to {type(interval_enum)}")

        # Apply Risk Guard if specified
        if max_position_size is not None:
             node_config['position_cap_usd'] = max_position_size
             LOG.info(f"[RISK GUARD] Capping {ticker} exposure limit to ${max_position_size:,.2f}")

        # Step 1: Fetch bars from Alpaca
        LOG.info(f"\n[STEP 1] Fetching {ticker} {interval_str} bars from Alpaca (SIP feed)...")
        LOG.info(f"[HOT START] Fetching {WARMUP_BUFFER}-bar trailing history for normalization warmup")
        bars = alpaca_client.fetch_historical_bars(
            symbol=ticker,
            timeframe=interval_enum,
            start=bar_start,
            end=bar_end,
            feed='sip',
            lookback_buffer=WARMUP_BUFFER
        )
        LOG.info(f"[{ticker}] Fetched {len(bars)} bars (includes {WARMUP_BUFFER} warmup)")
        
        # FORCE-VERIFY: Resample if fetched data doesn't match requested interval
        bars, was_resampled, actual_secs, expected_secs = force_resample_ohlcv(
            bars, interval_str, ticker=ticker
        )
        if was_resampled:
            LOG.info(f"[{ticker}] Resampled to {len(bars)} bars at {interval_str}")
        else:
            LOG.info(f"[VALIDATION] [OK] Frequency verified: {interval_str} ({int(actual_secs)}s delta)")

        
        LOG.info(f"[LIVE {ticker}] Step 2: Fetching fundamental metrics...")
        fmp_metrics = fmp_client.fetch_fundamental_metrics(ticker)
        
        LOG.info(f"[LIVE {ticker}] Step 3: Fetching news...")
        news_list = fmp_client.fetch_historical_news(ticker, news_start, news_end, price_df=bars)
        
        LOG.info(f"[LIVE {ticker}] Step 4: Feature engineering...")
        df = bars.copy()
        df['log_return'] = feature_engineer.calculate_log_return(df)
        df['rvol'] = feature_engineer.calculate_rvol(df, window=20)
        df['parkinson_vol'] = feature_engineer.calculate_parkinson_vol(df)
        df['mktCap'] = fmp_metrics['mktCap']
        df['pe'] = fmp_metrics['pe']
        df['avgVolume_fmp'] = fmp_metrics['avgVolume']
        
        feature_matrix_live = merge_news_pit(df, news_list, lookback_hours=4, ticker=ticker)
        
        # Add technical indicators (with node_config for RSI lookback)
        add_technical_indicators(feature_matrix_live, node_config=node_config)
        
        # Generate master alpha signal (with node_config for weights and sentry gate)
        generate_master_signal(feature_matrix_live, node_config=node_config, ticker=ticker)
        
        feature_matrix_live = trim_warmup_period(feature_matrix_live, warmup_rows=20)
        
        # HOT START: Strip warmup buffer for live trading
        # Ensure signal generation only uses fully-warmed normalization windows
        if len(feature_matrix_live) > WARMUP_BUFFER:
            LOG.info(f"[HOT START] [{ticker}] Isolating {WARMUP_BUFFER} warmup bars from live trading window")
            feature_matrix_live = feature_matrix_live.iloc[WARMUP_BUFFER:].copy()
            LOG.success(f"[HOT START: ARMED] [{ticker}] Rolling normalization fully populated. Trading bars: {len(feature_matrix_live)}")
        
        LOG.info(f"[LIVE {ticker}] Step 5: Generating signal...")
        # AG: TEMPORAL LEAK PATCH - Feature Isolation
        # CRITICAL: Ensure 'forward_return' is NEVER in feature set for signal generation
        cols_needed = ['rsi_14', 'volume_zscore', 'sentiment', 'log_return', 'close']
        if 'signal' in feature_matrix_live.columns:
            cols_needed.append('signal')
            
        # Safety check: Explicitly exclude forward_return if somehow present
        cols_needed = [col for col in cols_needed if col != 'forward_return']
        working_df = feature_matrix_live[cols_needed].copy()
        working_df['forward_return'] = working_df['log_return'].shift(-15)
        working_df = working_df.dropna()
        
        if len(working_df) < 50:
            result['error'] = f"Insufficient data ({len(working_df)} rows)"
            LOG.warning(f"[{ticker}] WARNING: {result['error']}")
            return result
        
        split_idx = int(len(working_df) * 0.70)
        out_sample = working_df.iloc[split_idx:].copy()
        in_sample = working_df.iloc[:split_idx].copy()
        
        in_sample = working_df.iloc[:split_idx].copy()
        
        # STRATEGY SELECTION: Validated Hysteresis vs Legacy Alpha
        if 'signal' in out_sample.columns and node_config.get('enable_hysteresis', False):
            # VALIDATED STRATEGY: Use the pre-calculated Hysteresis signal
            latest_signal = int(out_sample['signal'].iloc[-1])
            result['signal'] = latest_signal
            LOG.info(f"[{ticker}] Using validated Hysteresis signal: {latest_signal}")
        else:
            # LEGACY STRATEGY: Use alpha weights for adaptive thresholding
            alpha_weights = node_config.get('alpha_weights', {'rsi_14': 0.4, 'volume_zscore': 0.3, 'sentiment': 0.3})
            opt_alpha = calculate_alpha_with_weights(out_sample, alpha_weights)
            in_alpha = calculate_alpha_with_weights(in_sample, alpha_weights)
            threshold = in_alpha.median()
            
            out_sample['signal'] = np.where(opt_alpha > threshold, 1, -1)
            latest_signal = int(out_sample['signal'].iloc[-1])
            result['signal'] = latest_signal
        
        LOG.stats(f"[{ticker}] Signal: {'BUY' if latest_signal == 1 else 'SELL'}")
        
        # Execute trade via async wrapper (runs in thread pool)
        trade_result = await async_execute_trade(
            trading_client, 
            latest_signal, 
            ticker,
            allocation_pct=allocation_pct,
            ticker_config=node_config
        )
        result['trade_result'] = trade_result
        result['success'] = True
        
        if trade_result['executed']:
            LOG.stats(f"[{ticker}] [OK] Order {trade_result['order_id']} | {trade_result['side'].upper()} {trade_result['qty']} @ ${trade_result['limit_price']:.2f}")
        else:
            LOG.stats(f"[{ticker}] [FAIL] Rejected: {trade_result['rejection_reason']}")
            
    except Exception as e:
        result['error'] = str(e)
        LOG.error(f"[{ticker}] ERROR: {e}")
    
    return result


async def live_trading_loop(
    alpaca_client,
    fmp_client,
    feature_engineer,

    node_configs: dict,
    max_position_size: float = None
) -> None:
    """
    Async live trading loop for multi-symbol basket processing.
    
    Uses asyncio.gather() to process all tickers concurrently.
    PDT check runs once per minute before any ticker processing.
    
    Args:
        alpaca_client: AlpacaDataClient for market data
        fmp_client: FMPDataClient for fundamentals
        feature_engineer: FeatureEngineer instance
        opt_weights: Optimized alpha weights
    """
    from src.executor import AlpacaTradingClient
    
    LOG.info("\n" + "=" * 60)
    LOG.info("[LIVE] MAGELLAN V1.0 INITIALIZED. DEPLOYING LAMINAR DNA.")
    LOG.info("=" * 60)
    LOG.info("[LIVE MODE] Entering async multi-symbol trading loop...")
    LOG.info(f"[INFO] Basket: {', '.join(TICKERS)}")
    LOG.info("=" * 60)
    LOG.info("[INFO] Press Ctrl+C to stop the trading loop.")
    
    # Calculate per-ticker allocation
    allocation_pct = 1.0 / len(TICKERS)  # 25% for 4 tickers
    LOG.config(f"[CONFIG] Per-ticker allocation: {allocation_pct*100:.0f}%")
    
    try:
        # Initialize trading client ONCE
        trading_client = AlpacaTradingClient()
        
        loop_iteration = 0
        while True:
            loop_iteration += 1
            
            # Sync with next 1-minute bar
            now = datetime.now()
            sleep_time = 60 - now.second
            LOG.info(f"\n[LIVE] Iteration #{loop_iteration} | Syncing with next bar... Sleeping {sleep_time}s")
            await asyncio.sleep(sleep_time)
            
            # ================================================================
            # PDT_EQUITY_THRESHOLD CHECK (ONCE per minute, BEFORE gather)
            # ================================================================
            pdt_ok, pdt_msg = trading_client.check_pdt_protection()
            LOG.info(f"[LIVE] {pdt_msg}")
            if not pdt_ok:
                LOG.warning(f"[LIVE] [ALERT] PDT PROTECTION ACTIVE - Skipping this bar")
                continue
            
            # Update date window to current time
            current_time = datetime.now()
            bar_end = current_time.strftime('%Y-%m-%d')
            bar_start = (current_time - timedelta(days=1)).strftime('%Y-%m-%d')
            news_end = bar_end
            news_start = (current_time - timedelta(days=4)).strftime('%Y-%m-%d')
            
            if not args.quiet:
                print(f"\n[LIVE] === Bar Window: {bar_start} to {bar_end} ===")
                print(f"[LIVE] Processing {len(TICKERS)} tickers concurrently...")
            
            # ================================================================
            # CONCURRENT TICKER PROCESSING via asyncio.gather
            # ================================================================
            tasks = [
                process_ticker(
                    ticker=ticker,
                    alpaca_client=alpaca_client,
                    fmp_client=fmp_client,
                    feature_engineer=feature_engineer,
                    trading_client=trading_client,
                    node_config=node_configs.get(ticker, node_configs.get('SPY', {})),
                    bar_start=bar_start,
                    bar_end=bar_end,
                    news_start=news_start,
                    news_end=news_end,
                    allocation_pct=allocation_pct,
                    max_position_size=max_position_size
                )
                for ticker in TICKERS
            ]
            
            # return_exceptions=True ensures one ticker failure doesn't stop others
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # ================================================================
            # RESULTS SUMMARY
            # ================================================================
            if not args.quiet:
                print(f"\n[LIVE] === Iteration #{loop_iteration} Summary ===")
            successes = 0
            failures = 0
            for res in results:
                if isinstance(res, Exception):
                    failures += 1
                    LOG.error(f"  [FAIL] Exception: {res}")
                elif isinstance(res, dict):
                    if res.get('success'):
                        successes += 1
                    else:
                        failures += 1
            if not args.quiet:
                print(f"[LIVE] Processed: {successes} success, {failures} failures")
            
    except KeyboardInterrupt:
        print("\n\n[LIVE] Trading loop stopped by user (Ctrl+C)")
        print("[LIVE] Exiting gracefully...")
    except Exception as e:
        print(f"\n[LIVE ERROR] Fatal error: {e}")
        print("[FALLBACK] Exiting live mode...")


def main() -> None:
    global TICKERS, MAG7_UNIVERSE
    """Main entry point for the Magellan data pipeline."""
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Magellan Trading System - Data Pipeline & Execution Engine'
    )
    parser.add_argument(
        '--mode',
        choices=['simulation', 'live', 'observe'],
        default='simulation',
        help='Execution mode: simulation (default), live trading, or observe (ORH analysis)'
    )
    parser.add_argument(
        '--stress-test-days',
        type=int,
        default=0,
        help='Force stress test with N days (bypasses validation). 0=disabled (default)'
    )
    parser.add_argument(
        '--report-only',
        action='store_true',
        default=False,
        help='Minimize output volume (suppress verbose per-window logs)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        default=False,
        help='Research Mode: Compress logs, suppress metrics, redirect debug.'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        default=None,
        help='Start date for temporal range (ISO-8601: YYYY-MM-DD). Overrides days_back.'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        default=None,
        help='End date for temporal range (ISO-8601: YYYY-MM-DD). Overrides days_back.'
    )
    parser.add_argument(
        '--symbols',
        type=str,
        help='Comma-separated list of tickers to override config'
    )
    parser.add_argument(
        '--data-source',
        type=str,
        default='FMP',
        choices=['FMP', 'Alpaca'],
        help='Force a specific data provider')
    parser.add_argument(
        '--config',
        type=str,
        help='Path to JSON config file (default: src/configs/mag7_default.json)')
    parser.add_argument(
        '--max-position-size',
        type=float,
        default=None,
        help='Maximum dollar amount allowed for a single ticker position'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        default=False,
        help='Enable detailed process flow logging (shows step-by-step progress)'
    )
    args = parser.parse_args()
    
    # Load environment variables into os.environ
    load_env_file()
    
    # =========================================================================
    # CONFIG LOADING LOGIC
    # =========================================================================
    # Initialize EngineConfig singleton (global engine configuration)
    from src.config_loader import EngineConfig
    
    if args.config:
        # Custom config specified via CLI
        print(f"[INFO] ENGINE: Loading custom config from {args.config}")
        engine_config = EngineConfig(config_path=args.config)
    else:
        # Fall back to default config
        print("[INFO] ENGINE: Loading default config (mag7_default.json)")
        engine_config = EngineConfig()
    
    # Initialize Logger - New verbosity system
    from src.logger import set_log_level
    set_log_level(quiet=args.quiet, verbose=args.verbose)
    
    # Print Mode Banner
    if args.mode == 'live':
        LOG.warning("\n" + "!" * 60)
        LOG.warning("!!! LIVE TRADING MODE - ALPACA PAPER ACCOUNT !!!")
        LOG.warning("!" * 60)
        LOG.warning("[WARNING] Real orders will be submitted to your Paper Trading account.")
        LOG.warning("[WARNING] This affects your paper account balance and positions.")
        LOG.warning("!" * 60 + "\n")
    
    # Print System Readiness Report
    LOG.system("=" * 60)
    LOG.system("MAGELLAN SYSTEM READINESS REPORT")
    LOG.system("=" * 60)
    
    apca_key_id = os.getenv('APCA_API_KEY_ID')
    apca_base_url = os.getenv('APCA_API_BASE_URL')
    
    LOG.system(f"APCA_API_KEY_ID: {'Found' if apca_key_id else 'Not Found'}")
    if apca_key_id:
        LOG.system(f"  -> Key Prefix: {apca_key_id[:3]}...")
    LOG.system(f"Target Endpoint: {apca_base_url if apca_base_url else 'Not Set'}")
    LOG.system(f"Data Feed: SIP (Full Market)")
    LOG.system("=" * 60)
    print()
    
    # Initialize clients
    try:
        alpaca_client = AlpacaDataClient()
        fmp_client = FMPDataClient()
        feature_engineer = FeatureEngineer()
    except ValueError as e:
        LOG.error(f"[ERROR] Initialization failed: {e}")
        return
    
    # =========================================================================
    # OBSERVE MODE: Hangar Observation Layer (ORH)
    # =========================================================================
    if args.mode == 'observe':
        from src.hangar import run_hangar_observation
        
        print("\n" + "=" * 60)
        print("[HANGAR] OBSERVATION MODE ACTIVATED")
        print("=" * 60)
        print("[SAFETY] Trade execution is DISABLED")
        print("[INFO] Running ORH Kinetic Potential Analysis...")
        print("=" * 60)
        
        # Run hangar observation for all tickers
        hangar_results = run_hangar_observation(
            tickers=TICKERS,
            alpaca_client=alpaca_client,
            lookback_days=7
        )
        
        # Exit after observation (no simulation or live trading)
        return
    # =========================================================================
    
    # Configuration
    # Bars: Modern Era Temporal Lock (2022-2025)
    bar_start_date = '2022-01-01'
    bar_end_date = '2025-12-31'
    # News: 3 days prior to bar_start for PIT lookback coverage
    news_start_date = '2021-12-29' # 3 days prior to 2022-01-01
    news_end_date = '2025-12-31'
    
    # Load node configurations from master_config.json
    node_configs = load_node_config()
    
    # Update TICKERS from config if available (unless overridden by CLI)
    if not args.symbols and 'tickers' in node_configs:
         TICKERS = node_configs['tickers']
         LOG.config(f"[CONFIG] Loaded ticker universe: {TICKERS}")
    
    # Macro Era Telemetry
    if 'VSS' in node_configs and 'IWM' in node_configs:
        LOG.system("[SYSTEM] Macro Era Locked: 2019-2021 | VSS(1H) | IWM(3Min)")
    
    LOG.ensemble("[ENSEMBLE] 5-Node Fleet Synchronized | Telemetry: High-Entropy")
    
    # CLI OVERRIDE: Ticker Selection
    target_tickers = TICKERS
    if args.symbols:
        # Split string into list
        target_tickers = [t.strip() for t in args.symbols.split(',')]
        
        # Expand MAG7 Universe to allow overrides
        global MAG7_UNIVERSE
        MAG7_UNIVERSE = frozenset(list(MAG7_UNIVERSE) + target_tickers)
        LOG.system(f"[OVERRIDE] Target Tickers set to: {target_tickers}")

    # Process each ticker in the basket
    for symbol in target_tickers:
        # MAG7 LOCKDOWN ENFORCEMENT: Skip any ticker not in MAG7 universe
        if not validate_mag7_ticker(symbol):
            continue
        
        LOG.info(f"\n{'='*60}")
        LOG.info(f"[SIMULATION] Processing {symbol}")
        LOG.info(f"{'='*60}")
        
        # Retrieve ticker-specific config (fallback to SPY if missing)
        if symbol in node_configs:
            node_config = node_configs[symbol]
        else:
            node_config = node_configs.get('SPY', {})
            LOG.config(f"[CONFIG] WARNING: No config for {symbol}, using SPY defaults")
        
        # NODE TELEMETRY
        rsi_lookback = node_config.get('rsi_lookback', 14)
        sentry_gate = node_config.get('sentry_gate', 'None')
        interval_str = node_config.get('interval', '1Min')
        
        # Map string to Enum (default to Minute if not found)
        target_tf = TF_MAP.get(interval_str, TimeFrame.Minute)
        
        if not args.quiet:
            print(f"[NODE] Initialized {symbol} | Lookback: {rsi_lookback} | Gate: {sentry_gate}")
            print(f"[NODE] {symbol} mapping {interval_str} to {type(target_tf)}")
        
        try:
            # Step 1: Fetch bars from Alpaca
            LOG.info(f"\n[STEP 1] Fetching {symbol} {interval_str} bars from Alpaca (SIP feed)...")
            LOG.info(f"[HOT START] Fetching {WARMUP_BUFFER}-bar trailing history for normalization warmup")
            bars = alpaca_client.fetch_historical_bars(
                symbol=symbol,
                timeframe=target_tf,
                start=bar_start_date,
                end=bar_end_date,
                feed='sip',
                lookback_buffer=WARMUP_BUFFER
            )
            LOG.success(f"[SUCCESS] Fetched {len(bars)} bars (includes {WARMUP_BUFFER} warmup)")
            
            # FORCE-VERIFY: Resample if fetched data doesn't match requested interval
            bars, was_resampled, actual_secs, expected_secs = force_resample_ohlcv(
                bars, interval_str, ticker=symbol
            )
            if was_resampled:
                LOG.info(f"[{symbol}] Resampled to {len(bars)} bars at {interval_str}")
            else:
                LOG.info(f"[VALIDATION] [OK] Frequency verified: {interval_str} ({int(actual_secs)}s delta)")

            
            # Step 2: Fetch FMP fundamental metrics
            LOG.info(f"\n[STEP 2] Fetching {symbol} fundamental metrics from FMP...")
            fmp_metrics = fmp_client.fetch_fundamental_metrics(symbol)
            LOG.metric(f"[SUCCESS] Market Cap: ${fmp_metrics['mktCap']:,.0f}, PE: {fmp_metrics['pe']:.2f}")
            
            # Step 3: Fetch 3-day historical news for PIT alignment
            LOG.info(f"\n[STEP 3] Fetching {symbol} historical news from FMP (3-day window)...")
            news_list = fmp_client.fetch_historical_news(symbol, news_start_date, news_end_date, price_df=bars)
            LOG.success(f"[SUCCESS] Retrieved {len(news_list)} news articles for PIT alignment")
            
            # Step 4: Run feature engineering
            LOG.info(f"\n[STEP 4] Running feature engineering...")
            
            df = bars.copy()
            df['log_return'] = feature_engineer.calculate_log_return(df)
            df['rvol'] = feature_engineer.calculate_rvol(df, window=20)
            df['parkinson_vol'] = feature_engineer.calculate_parkinson_vol(df)
            
            # Add FMP fundamental metrics as constants (they don't vary per-bar)
            df['mktCap'] = fmp_metrics['mktCap']
            df['pe'] = fmp_metrics['pe']
            df['avgVolume_fmp'] = fmp_metrics['avgVolume']
            
            # Apply Point-in-Time sentiment alignment
            feature_matrix = merge_news_pit(df, news_list, lookback_hours=4, ticker=symbol)
            
            # Add technical indicators (with node_config for RSI lookback)
            add_technical_indicators(feature_matrix, node_config=node_config)
            
            # Generate master alpha signal (with node_config for weights and sentry gate)
            generate_master_signal(feature_matrix, node_config=node_config, ticker=symbol)
            
            # Trim warmup period (20 rows) to remove NaN skew from rolling calculations
            feature_matrix = trim_warmup_period(feature_matrix, warmup_rows=20)
            
            # HOT START: Strip warmup buffer for trading window (252 bars)
            # The warmup buffer was already processed through feature engineering for rolling normalization
            # Now exclude it from validation and backtesting
            warmup_data_size = min(WARMUP_BUFFER, len(feature_matrix))
            if len(feature_matrix) > WARMUP_BUFFER:
                LOG.info(f"[HOT START] Isolating {WARMUP_BUFFER} warmup bars from trading window")
                feature_matrix_warmup = feature_matrix.iloc[:WARMUP_BUFFER].copy()
                feature_matrix = feature_matrix.iloc[WARMUP_BUFFER:].copy()
                LOG.success(f"[HOT START: ARMED] Warmup complete. Rolling normalization fully populated.")
                LOG.info(f"[HOT START] Trading window: {len(feature_matrix)} bars (warmup excluded from P&L)")
                
                # Verify first bar timestamp
                first_bar_time = feature_matrix.index[0]
                LOG.info(f"[HOT START] First trading bar timestamp: {first_bar_time}")
            else:
                LOG.warning(f"[{symbol}] Insufficient data for warmup isolation ({len(feature_matrix)} <= {WARMUP_BUFFER})")
            
            LOG.success(f"[SUCCESS] Feature matrix created with {len(feature_matrix)} rows (after warmup trim)")
            
            # Step 5: Output feature matrix
            LOG.info("\n" + "=" * 60)
            LOG.info(f"[FEATURE_MATRIX] {symbol} - Last 5 rows:")
            LOG.info("=" * 60)
            
            # Select and display key columns including alpha_score
            output_cols = ['close', 'log_return', 'rsi_14', 'volume_zscore', 'sentiment', 'alpha_score']
            if LOG.verbosity >= LOG.VERBOSE:
                print(feature_matrix[output_cols].tail())
            
            # Step 6: Walk-Forward Validation with Dynamic Optimization
            LOG.info(f"\n[STEP 6] Running Optimized Walk-Forward Validation for {symbol}...")
            
            # Define static weights for comparison
            static_weights = {'rsi_14': 0.4, 'volume_zscore': 0.3, 'sentiment': 0.3}
            
            # Run optimized validation
            opt_result = run_optimized_walk_forward_check(
                feature_matrix,
                feature_cols=['rsi_14', 'volume_zscore', 'sentiment'],
                target_col='log_return',
                horizon=15,
                static_weights=static_weights
            )
            
            # Print optimized scorecard
            if not args.quiet:
                print_optimized_scorecard(opt_result)
            
            # THE KILL SWITCH: If optimized validation still fails
            if not opt_result['passed']:
                print("\n" + "!" * 60)
                print(f"[SYSTEM] {symbol} VALIDATION FAILED - SIGNAL IS UNRELIABLE.")
                print("!" * 60)
                print("[REASON] Optimized Out-of-Sample Hit Rate < 51% indicates persistent model weakness.")
                print("[ACTION] Consider alternative features or longer training window.")
            
            # CLI OVERRIDE: Force stress test if --stress-test-days > 0 OR explicit dates provided
            has_explicit_dates = args.start_date is not None and args.end_date is not None
            force_stress_test = args.stress_test_days > 0 or has_explicit_dates
            validation_passed = opt_result['passed']
            
            if force_stress_test or validation_passed:
                # Parse temporal range first to determine mode
                temporal_start = None
                temporal_end = None
                if has_explicit_dates:
                    from datetime import datetime as dt
                    temporal_start = dt.strptime(args.start_date, '%Y-%m-%d')
                    temporal_end = dt.strptime(args.end_date, '%Y-%m-%d')
                    LOG.system(f"[TEMPORAL] Syncing Clock to Epoch: {args.start_date} -> {args.end_date}")
                    # stress_days is ignored when explicit dates are used
                    stress_days = 0  # Placeholder, actual days calculated from date range
                elif args.stress_test_days > 0:
                    LOG.system(f"\n[SYSTEM] Force-Starting Stress Test for {symbol} ({args.stress_test_days} days)...")
                    LOG.system("[OVERRIDE] Bypassing validation check (--stress-test-days specified)")
                    stress_days = args.stress_test_days
                else:
                    LOG.system(f"\n[SYSTEM] {symbol} VALIDATION PASSED - Trading signals are ACTIVE.")
                    stress_days = 15  # Default
                
                # Step 6c: Rolling Walk-Forward Stress Test
                LOG.system("\n" + "=" * 60)
                if has_explicit_dates:
                    LOG.system(f"[STEP 6c] Running Epoch Stress Test for {symbol}...")
                else:
                    LOG.system(f"[STEP 6c] Running {stress_days}-Day Rolling Walk-Forward Stress Test for {symbol}...")
                LOG.system("=" * 60)
                LOG.info("[NOTE] This is the most rigorous test before live execution.")
                LOG.info("[NOTE] It validates the Brain's ability to adapt to shifting market regimes.")
                
                stress_result = run_rolling_backtest(
                    symbol=symbol,
                    days=stress_days,
                    in_sample_days=3,
                    initial_capital=node_config.get('position_cap_usd', 10000.0),
                    start_date=temporal_start,
                    end_date=temporal_end,
                    report_only=args.report_only,
                    quiet=args.quiet,
                    node_config=node_config
                )
                
                # Print stress test summary
                if not args.quiet:
                    print_stress_test_summary(stress_result)
                
                # Export results with symbol-specific filename
                export_stress_test_results(stress_result, f'stress_test_equity_{symbol}.csv')
                
                # MODE: Live Execution or Simulation
                if args.mode == 'live':
                    # Launch async live trading loop (exits after first symbol for live mode)
                    # Launch async live trading loop (exits after first symbol for live mode)
                    asyncio.run(live_trading_loop(
                        alpaca_client=alpaca_client,
                        fmp_client=fmp_client,

                        feature_engineer=feature_engineer,
                        node_configs=node_configs,
                        max_position_size=args.max_position_size
                    ))
                    break  # Exit loop after launching live mode
                
                else:
                    # Simulation mode: Run virtual P&L tracker
                    print("\n" + "=" * 60)
                    print(f"[STEP 6b] Running Virtual P&L Tracker for {symbol} on Out-of-Sample Data...")
                    print("=" * 60)
                    
                    # Reconstruct out-of-sample DataFrame with signal
                    from src.optimizer import calculate_alpha_with_weights
                    
                    # Get out-of-sample split
                    # AG: TEMPORAL LEAK PATCH - Feature Isolation  
                    # CRITICAL: forward_return is TARGET only, never a FEATURE
                    cols_needed = ['rsi_14', 'volume_zscore', 'sentiment', 'log_return', 'close']
                    # Safety check: Explicitly exclude forward_return if somehow present
                    cols_needed = [col for col in cols_needed if col != 'forward_return']
                    working_df = feature_matrix[cols_needed].copy()
                    working_df['forward_return'] = working_df['log_return'].shift(-15)
                    working_df = working_df.dropna()
                    
                    split_idx = int(len(working_df) * 0.70)
                    out_sample = working_df.iloc[split_idx:].copy()
                    
                    # Calculate optimized alpha on out-of-sample
                    opt_alpha = calculate_alpha_with_weights(out_sample, opt_result['optimal_weights'])
                    
                    # Generate signal using in-sample threshold (no look-ahead)
                    in_sample = working_df.iloc[:split_idx].copy()
                    in_alpha = calculate_alpha_with_weights(in_sample, opt_result['optimal_weights'])
                    threshold = in_alpha.median()
                    
                    out_sample['signal'] = np.where(opt_alpha > threshold, 1, -1)
                    
                    # Run portfolio simulation
                    pnl_metrics = simulate_portfolio(
                        out_sample, 
                        initial_capital=100000, 
                        friction_bps=2.5,
                        max_position_dollars=LIQUIDITY_CAP_USD
                    )
                    
                    # Print Virtual Trading Statement
                    if not args.quiet:
                        print_virtual_trading_statement(pnl_metrics)
                    
                    # Save equity curve to CSV with symbol-specific filename
                    equity_curve_path = f'equity_curve_{symbol}.csv'
                    pnl_metrics['equity_curve'].to_csv(equity_curve_path, header=['equity'])
                    print(f"\n[OUTPUT] Equity curve saved to: {equity_curve_path}")

            
            # Step 7: Alpha Discovery - Multi-Factor IC Analysis
            LOG.ic_matrix("\n" + "=" * 60)
            LOG.ic_matrix(f"[SIGNAL STRENGTH REPORT] {symbol} - Multi-Factor IC Analysis")
            LOG.ic_matrix("=" * 60)
            
            features_to_test = ['sentiment', 'rsi_14', 'volatility_14', 'volume_zscore', 'alpha_score']
            horizons = [5, 15, 60]  # 5-min, 15-min, 60-min
            
            def interpret_ic(ic_val):
                """Interpret IC value strength."""
                if pd.isna(ic_val):
                    return "N/A"
                abs_ic = abs(ic_val)
                if abs_ic < 0.02:
                    return "Noise"
                elif abs_ic < 0.05:
                    return "Weak"
                elif abs_ic < 0.10:
                    return "Moderate"
                return "Strong"
            
            for feature in features_to_test:
                LOG.ic_matrix(f"\nFeature: {feature} -> Target: log_return")
                LOG.ic_matrix("-" * 40)
                for horizon in horizons:
                    ic = calculate_ic(feature_matrix, feature, 'log_return', horizon=horizon)
                    if pd.isna(ic):
                        ic_str = "N/A (insufficient data)"
                    else:
                        ic_str = f"{ic:+.4f} ({interpret_ic(ic)})"
                    LOG.ic_matrix(f"  {horizon:>3}-min horizon IC: {ic_str}")
            
            LOG.ic_matrix("\n" + "=" * 60)
            LOG.ic_matrix("[NOTE] IC > 0.02 suggests exploitable alpha; IC > 0.05 is promising.")
            
            # Step 8: Feature Independence Check
            if not args.quiet:
                print("\n" + "=" * 60)
                print(f"[FEATURE INDEPENDENCE] {symbol} - Cross-Correlation Analysis")
                print("=" * 60)
            
            corr_sent_rsi = check_feature_correlation(feature_matrix, 'sentiment', 'rsi_14')
            if pd.isna(corr_sent_rsi):
                corr_str = "N/A (insufficient data)"
                independence = ""
            else:
                abs_corr = abs(corr_sent_rsi)
                if abs_corr > 0.7:
                    independence = "HIGH REDUNDANCY - signals may be redundant"
                elif abs_corr > 0.4:
                    independence = "MODERATE - partial overlap"
                else:
                    independence = "INDEPENDENT - good signal diversity"
                corr_str = f"{corr_sent_rsi:+.4f}"
            
            if not args.quiet:
                print(f"Sentiment vs RSI Correlation: {corr_str}")
                if independence:
                    print(f"  -> {independence}")
                print("-" * 60)
                print("[NOTE] |corr| < 0.4 indicates independent signals (desirable for confluence).")
            
            LOG.info("\n" + "=" * 60)
            LOG.success(f"[COMPLETE] {symbol} pipeline finished successfully")
            LOG.info("=" * 60)
            
        except requests.exceptions.HTTPError as e:
            LOG.error(f"\n[ERROR] {symbol} - HTTP request failed:")
            if hasattr(e, 'response') and e.response is not None:
                LOG.error(f"Status Code: {e.response.status_code}")
                LOG.error(f"Response Text: {e.response.text}")
            else:
                LOG.error(str(e))
            LOG.warning(f"[WARNING] Skipping {symbol} and continuing with next ticker...")
            continue
            
        except Exception as e:
            LOG.error(f"\n[ERROR] {symbol} - Unexpected error: {type(e).__name__}: {e}")
            LOG.warning(f"[WARNING] Skipping {symbol} and continuing with next ticker...")
            continue


if __name__ == '__main__':
    main()
