"""
Magellan Data Pipeline - Entry Point
Fetches historical market data using Alpaca Paper API with Market Plus (SIP) subscription.
Supports both simulation and live trading modes.
"""

import os
import argparse
import time
import requests.exceptions
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.data_handler import AlpacaDataClient, FMPDataClient
from src.features import FeatureEngineer, add_technical_indicators, merge_news_pit, generate_master_signal
from src.discovery import calculate_ic, check_feature_correlation, trim_warmup_period
from src.validation import run_walk_forward_check, print_validation_scorecard, run_optimized_walk_forward_check, print_optimized_scorecard
from src.pnl_tracker import simulate_portfolio, print_virtual_trading_statement
from src.backtester_pro import run_rolling_backtest, print_stress_test_summary, export_stress_test_results


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


def main() -> None:
    """Main entry point for the Magellan data pipeline."""
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Magellan Trading System - Data Pipeline & Execution Engine'
    )
    parser.add_argument(
        '--mode',
        choices=['simulation', 'live'],
        default='simulation',
        help='Execution mode: simulation (default) or live trading'
    )
    args = parser.parse_args()
    
    # Load environment variables into os.environ
    load_env_file()
    
    # Print Mode Banner
    if args.mode == 'live':
        print("\n" + "!" * 60)
        print("!!! LIVE TRADING MODE - ALPACA PAPER ACCOUNT !!!")
        print("!" * 60)
        print("[WARNING] Real orders will be submitted to your Paper Trading account.")
        print("[WARNING] This affects your paper account balance and positions.")
        print("!" * 60 + "\n")
    
    # Print System Readiness Report
    print("=" * 60)
    print("MAGELLAN SYSTEM READINESS REPORT")
    print("=" * 60)
    
    apca_key_id = os.getenv('APCA_API_KEY_ID')
    apca_base_url = os.getenv('APCA_API_BASE_URL')
    
    print(f"APCA_API_KEY_ID: {'Found' if apca_key_id else 'Not Found'}")
    if apca_key_id:
        print(f"  -> Key Prefix: {apca_key_id[:3]}...")
    print(f"Target Endpoint: {apca_base_url if apca_base_url else 'Not Set'}")
    print(f"Data Feed: SIP (Full Market)")
    print("=" * 60)
    print()
    
    # Initialize clients
    try:
        alpaca_client = AlpacaDataClient()
        fmp_client = FMPDataClient()
        feature_engineer = FeatureEngineer()
    except ValueError as e:
        print(f"[ERROR] Initialization failed: {e}")
        return
    
    # Configuration
    symbol = 'SPY'
    # Bars: 1-day window for analysis
    bar_start_date = '2026-01-07'
    bar_end_date = '2026-01-08'
    # News: 3 days prior to bar_start for PIT lookback coverage
    news_start_date = '2026-01-04'
    news_end_date = '2026-01-08'
    
    print(f"[PIPELINE] Starting multi-source data fusion for {symbol}")
    print("=" * 60)
    
    try:
        # Step 1: Fetch SPY bars from Alpaca
        print(f"\n[STEP 1] Fetching {symbol} 1-minute bars from Alpaca (SIP feed)...")
        bars = alpaca_client.fetch_historical_bars(
            symbol=symbol,
            timeframe='1Min',
            start=bar_start_date,
            end=bar_end_date,
            feed='sip'
        )
        print(f"[SUCCESS] Fetched {len(bars)} bars")
        
        # Step 2: Fetch FMP fundamental metrics
        print(f"\n[STEP 2] Fetching {symbol} fundamental metrics from FMP...")
        fmp_metrics = fmp_client.fetch_fundamental_metrics(symbol)
        print(f"[SUCCESS] Market Cap: ${fmp_metrics['mktCap']:,.0f}, PE: {fmp_metrics['pe']:.2f}")
        
        # Step 3: Fetch 3-day historical news for PIT alignment
        print(f"\n[STEP 3] Fetching {symbol} historical news from FMP (3-day window)...")
        news_list = fmp_client.fetch_historical_news(symbol, news_start_date, news_end_date)
        print(f"[SUCCESS] Retrieved {len(news_list)} news articles for PIT alignment")
        
        # Step 4: Run feature engineering (without legacy sentiment merge)
        print(f"\n[STEP 4] Running feature engineering...")
        
        # Use simplified merge without legacy sentiment (we'll add PIT sentiment separately)
        df = bars.copy()
        df['log_return'] = feature_engineer.calculate_log_return(df)
        df['rvol'] = feature_engineer.calculate_rvol(df, window=20)
        df['parkinson_vol'] = feature_engineer.calculate_parkinson_vol(df)
        
        # Add FMP fundamental metrics as constants (they don't vary per-bar)
        df['mktCap'] = fmp_metrics['mktCap']
        df['pe'] = fmp_metrics['pe']
        df['avgVolume_fmp'] = fmp_metrics['avgVolume']
        
        # Apply Point-in-Time sentiment alignment
        feature_matrix = merge_news_pit(df, news_list, lookback_hours=4)
        
        # Add technical indicators
        add_technical_indicators(feature_matrix)
        
        # Generate master alpha signal
        generate_master_signal(feature_matrix)
        
        # Trim warmup period (20 rows) to remove NaN skew from rolling calculations
        feature_matrix = trim_warmup_period(feature_matrix, warmup_rows=20)
        
        print(f"[SUCCESS] Feature matrix created with {len(feature_matrix)} rows (after warmup trim)")
        
        # Step 5: Output feature matrix
        print("\n" + "=" * 60)
        print("[FEATURE_MATRIX] Last 5 rows:")
        print("=" * 60)
        
        # Select and display key columns including alpha_score
        output_cols = ['close', 'log_return', 'rsi_14', 'volume_zscore', 'sentiment', 'alpha_score']
        print(feature_matrix[output_cols].tail())
        
        # Step 6: Walk-Forward Validation with Dynamic Optimization
        print(f"\n[STEP 6] Running Optimized Walk-Forward Validation...")
        
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
        print_optimized_scorecard(opt_result)
        
        # THE KILL SWITCH: If optimized validation still fails
        if not opt_result['passed']:
            print("\n" + "!" * 60)
            print("[SYSTEM] VALIDATION FAILED - SIGNAL IS UNRELIABLE. TRADING SUSPENDED.")
            print("!" * 60)
            print("[REASON] Optimized Out-of-Sample Hit Rate < 51% indicates persistent model weakness.")
            print("[ACTION] Consider alternative features or longer training window.")
        else:
            print("\n[SYSTEM] VALIDATION PASSED - Trading signals are ACTIVE.")
            
            # Step 6c: 15-Day Rolling Walk-Forward Stress Test (runs ONCE at startup)
            print("\n" + "=" * 60)
            print("[STEP 6c] Running 15-Day Rolling Walk-Forward Stress Test...")
            print("=" * 60)
            print("[NOTE] This is the most rigorous test before live execution.")
            print("[NOTE] It validates the Brain's ability to adapt to shifting market regimes.")
            
            # Run the rolling backtest
            stress_result = run_rolling_backtest(
                symbol=symbol,
                days=15,
                in_sample_days=3,
                initial_capital=100000.0
            )
            
            # Print stress test summary
            print_stress_test_summary(stress_result)
            
            # Export results
            export_stress_test_results(stress_result, 'stress_test_equity.csv')
            
            # MODE: Live Execution or Simulation
            if args.mode == 'live':
                # Live Trading Loop
                print("\n" + "=" * 60)
                print("[LIVE MODE] Entering continuous trading loop...")
                print("=" * 60)
                print("[INFO] Press Ctrl+C to stop the trading loop.")
                
                from src.executor import AlpacaTradingClient, execute_trade
                
                try:
                    # Initialize trading client ONCE
                    trading_client = AlpacaTradingClient()
                    
                    loop_iteration = 0
                    while True:
                        loop_iteration += 1
                        
                        # Sync with next 1-minute bar
                        now = datetime.now()
                        sleep_time = 60 - now.second
                        print(f"\n[LIVE] Iteration #{loop_iteration} | Syncing with next bar... Sleeping {sleep_time}s")
                        time.sleep(sleep_time)
                        
                        # Update date window to current time
                        current_time = datetime.now()
                        bar_end = current_time.strftime('%Y-%m-%d')
                        bar_start = (current_time - timedelta(days=1)).strftime('%Y-%m-%d')
                        news_end = bar_end
                        news_start = (current_time - timedelta(days=4)).strftime('%Y-%m-%d')
                        
                        print(f"\n[LIVE] === Bar Window: {bar_start} to {bar_end} ===")
                        
                        try:
                            # Step 1: Fetch fresh SPY bars
                            print(f"[LIVE STEP 1] Fetching {symbol} 1-minute bars...")
                            bars = alpaca_client.fetch_historical_bars(
                                symbol=symbol,
                                timeframe='1Min',
                                start=bar_start,
                                end=bar_end,
                                feed='sip'
                            )
                            print(f"[SUCCESS] Fetched {len(bars)} bars")
                            
                            # Step 2: Fetch FMP fundamental metrics
                            print(f"[LIVE STEP 2] Fetching {symbol} fundamental metrics...")
                            fmp_metrics = fmp_client.fetch_fundamental_metrics(symbol)
                            
                            # Step 3: Fetch news for PIT alignment
                            print(f"[LIVE STEP 3] Fetching {symbol} news...")
                            news_list = fmp_client.fetch_historical_news(symbol, news_start, news_end)
                            
                            # Step 4: Feature engineering
                            print(f"[LIVE STEP 4] Running feature engineering...")
                            df = bars.copy()
                            df['log_return'] = feature_engineer.calculate_log_return(df)
                            df['rvol'] = feature_engineer.calculate_rvol(df, window=20)
                            df['parkinson_vol'] = feature_engineer.calculate_parkinson_vol(df)
                            df['mktCap'] = fmp_metrics['mktCap']
                            df['pe'] = fmp_metrics['pe']
                            df['avgVolume_fmp'] = fmp_metrics['avgVolume']
                            
                            feature_matrix_live = merge_news_pit(df, news_list, lookback_hours=4)
                            add_technical_indicators(feature_matrix_live)
                            generate_master_signal(feature_matrix_live)
                            feature_matrix_live = trim_warmup_period(feature_matrix_live, warmup_rows=20)
                            
                            # Step 5: Generate signal
                            print(f"[LIVE STEP 5] Generating trading signal...")
                            from src.optimizer import calculate_alpha_with_weights
                            
                            cols_needed = ['rsi_14', 'volume_zscore', 'sentiment', 'log_return', 'close']
                            working_df = feature_matrix_live[cols_needed].copy()
                            working_df['forward_return'] = working_df['log_return'].shift(-15)
                            working_df = working_df.dropna()
                            
                            if len(working_df) < 50:
                                print(f"[LIVE WARNING] Insufficient data ({len(working_df)} rows). Skipping this bar.")
                                continue
                            
                            split_idx = int(len(working_df) * 0.70)
                            out_sample = working_df.iloc[split_idx:].copy()
                            in_sample = working_df.iloc[:split_idx].copy()
                            
                            opt_alpha = calculate_alpha_with_weights(out_sample, opt_result['optimal_weights'])
                            in_alpha = calculate_alpha_with_weights(in_sample, opt_result['optimal_weights'])
                            threshold = in_alpha.median()
                            
                            out_sample['signal'] = np.where(opt_alpha > threshold, 1, -1)
                            latest_signal = int(out_sample['signal'].iloc[-1])
                            
                            # Execute trade
                            print(f"\n[LIVE] Latest signal: {'BUY' if latest_signal == 1 else 'SELL'}")
                            trade_result = execute_trade(trading_client, latest_signal, symbol)
                            
                            if trade_result['executed']:
                                print(f"[LIVE] ✓ Order {trade_result['order_id']} | {trade_result['side'].upper()} {trade_result['qty']} @ ${trade_result['limit_price']:.2f}")
                            else:
                                print(f"[LIVE] ✗ Rejected: {trade_result['rejection_reason']}")
                                
                        except Exception as loop_error:
                            print(f"[LIVE ERROR] Loop iteration failed: {loop_error}")
                            print("[LIVE] Continuing to next bar...")
                            continue
                            
                except KeyboardInterrupt:
                    print("\n\n[LIVE] Trading loop stopped by user (Ctrl+C)")
                    print("[LIVE] Exiting gracefully...")
                except Exception as e:
                    print(f"\n[LIVE ERROR] Fatal error: {e}")
                    print("[FALLBACK] Exiting live mode...")
            
            else:
                # Simulation mode: Run virtual P&L tracker
                print("\n" + "=" * 60)
                print("[STEP 6b] Running Virtual P&L Tracker on Out-of-Sample Data...")
                print("=" * 60)
                
                # Reconstruct out-of-sample DataFrame with signal
                from src.optimizer import calculate_alpha_with_weights
                
                # Get out-of-sample split
                cols_needed = ['rsi_14', 'volume_zscore', 'sentiment', 'log_return', 'close']
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
                pnl_metrics = simulate_portfolio(out_sample, initial_capital=100000)
                
                # Print Virtual Trading Statement
                print_virtual_trading_statement(pnl_metrics)
                
                # Save equity curve to CSV
                equity_curve_path = 'equity_curve.csv'
                pnl_metrics['equity_curve'].to_csv(equity_curve_path, header=['equity'])
                print(f"\n[OUTPUT] Equity curve saved to: {equity_curve_path}")

        
        # Step 7: Alpha Discovery - Multi-Factor IC Analysis
        print("\n" + "=" * 60)
        print("[SIGNAL STRENGTH REPORT] Multi-Factor IC Analysis")
        print("=" * 60)
        
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
            print(f"\nFeature: {feature} → Target: log_return")
            print("-" * 40)
            for horizon in horizons:
                ic = calculate_ic(feature_matrix, feature, 'log_return', horizon=horizon)
                if pd.isna(ic):
                    ic_str = "N/A (insufficient data)"
                else:
                    ic_str = f"{ic:+.4f} ({interpret_ic(ic)})"
                print(f"  {horizon:>3}-min horizon IC: {ic_str}")
        
        print("\n" + "=" * 60)
        print("[NOTE] IC > 0.02 suggests exploitable alpha; IC > 0.05 is promising.")
        
        # Step 8: Feature Independence Check
        print("\n" + "=" * 60)
        print("[FEATURE INDEPENDENCE] Cross-Correlation Analysis")
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
        
        print(f"Sentiment vs RSI Correlation: {corr_str}")
        if independence:
            print(f"  → {independence}")
        print("-" * 60)
        print("[NOTE] |corr| < 0.4 indicates independent signals (desirable for confluence).")
        
        print("\n" + "=" * 60)
        print(f"[COMPLETE] Pipeline finished successfully")
        print("=" * 60)
        
    except requests.exceptions.HTTPError as e:
        print(f"\n[ERROR] HTTP request failed:")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response Text: {e.response.text}")
        else:
            print(str(e))
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {type(e).__name__}: {e}")


if __name__ == '__main__':
    main()
