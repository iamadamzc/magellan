"""
Multi-Day Rolling Walk-Forward Backtester
Stress-tests Alpha Score across multiple days to ensure robustness across market regimes.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import os

from src.data_handler import AlpacaDataClient, FMPDataClient
from src.features import FeatureEngineer, add_technical_indicators, merge_news_pit, generate_master_signal
from src.discovery import trim_warmup_period
from src.optimizer import optimize_alpha_weights, calculate_alpha_with_weights, RETRAIN_INTERVAL
from src.pnl_tracker import simulate_portfolio, calculate_max_drawdown
from src.config_loader import EngineConfig

# LIQUIDITY CAP: Maximum trade size to prevent runaway compounding
# Regardless of Virtual Equity, no single trade can exceed this amount
LIQUIDITY_CAP_USD = float(EngineConfig().get('POSITION_CAP', strict=True))



def calculate_wfe(in_sample_hr: float, out_sample_hr: float) -> float:
    """
    Calculate Walk-Forward Efficiency (WFE).
    
    WFE = Out-of-Sample Hit Rate / In-Sample Hit Rate
    Values close to 1.0 indicate good generalization.
    Values > 1.0 indicate out-of-sample outperformed in-sample (rare but possible).
    Values < 0.8 may indicate overfitting.
    
    Args:
        in_sample_hr: In-Sample hit rate (0-1)
        out_sample_hr: Out-of-Sample hit rate (0-1)
    
    Returns:
        WFE ratio (typically 0.5-1.2)
    """
    if in_sample_hr <= 0:
        return 0.0
    return out_sample_hr / in_sample_hr


def calculate_volatility(returns: pd.Series) -> float:
    """
    Calculate annualized volatility from returns.
    
    Assumes 5-min bars: 78 bars/day * 252 trading days/year.
    
    Args:
        returns: Series of period returns (log returns)
    
    Returns:
        Annualized volatility as percentage
    """
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    return returns.std() * np.sqrt(252 * 78) * 100


def get_trading_days(end_date: datetime, num_days: int) -> List[datetime]:
    """
    Get list of trading days (weekdays) going backwards from end_date.
    
    Args:
        end_date: End date (most recent)
        num_days: Number of trading days to retrieve
    
    Returns:
        List of datetime objects representing trading days (oldest first)
    """
    trading_days = []
    current = end_date
    
    while len(trading_days) < num_days:
        # Skip weekends
        if current.weekday() < 5:  # Monday = 0, Friday = 4
            trading_days.append(current)
        current -= timedelta(days=1)
    
    # Reverse to get chronological order (oldest first)
    return list(reversed(trading_days))


def run_rolling_backtest(
    symbol: str,
    days: int = 15,
    in_sample_days: int = 3,
    initial_capital: float = 100000.0,
    end_date: datetime = None,
    start_date: datetime = None,
    report_only: bool = False,
    quiet: bool = False
) -> Dict:
    """
    Run multi-day rolling walk-forward backtest.
    
    Uses a rolling window approach:
    - In-Sample: 3 days of data for weight optimization
    - Out-of-Sample: 1 day for validation
    - Window advances by 1 day each iteration
    
    Args:
        symbol: Stock symbol (e.g., 'SPY')
        days: Total trading days to process (default: 15)
        in_sample_days: Days for in-sample optimization (default: 3)
        initial_capital: Starting capital in dollars (default: 100,000)
        end_date: End date for backtest (default: yesterday)
        report_only: If True, suppress verbose window-by-window logging
    
    Returns:
        Dict with comprehensive backtest results
    """
    if not quiet:
        print("\n" + "=" * 60)
        print(f"[STRESS TEST] Multi-Day Rolling Walk-Forward Backtest")
        print(f"[STRESS TEST] Symbol: {symbol} | Days: {days} | Window: {in_sample_days}+1")
        print(f"[REALITY] Seed: ${initial_capital:,.0f} | Friction: 1.5bps | LiqCap: ${LIQUIDITY_CAP_USD/1000:.0f}k")
        print("=" * 60)
    
    # Initialize clients
    alpaca_client = AlpacaDataClient()
    fmp_client = FMPDataClient()
    feature_engineer = FeatureEngineer()
    
    # Determine date range: explicit dates override days_back calculation
    if start_date is not None and end_date is not None:
        # Explicit temporal range provided
        if not quiet:
            print(f"[TEMPORAL] Syncing Clock to Epoch: {start_date.strftime('%Y-%m-%d')} -> {end_date.strftime('%Y-%m-%d')}")
        
        # Calculate trading days between start and end
        trading_days = []
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:  # Weekday
                trading_days.append(current)
            current += timedelta(days=1)
        
        # Override days count based on actual range
        days = len(trading_days) - in_sample_days
        if days < 1:
            days = 1
    else:
        # Fallback: calculate from days_back
        if end_date is None:
            end_date = datetime.now() - timedelta(days=1)  # Yesterday
        
        # Get trading days (we need days + in_sample_days to have full windows)
        total_days_needed = days + in_sample_days
        trading_days = get_trading_days(end_date, total_days_needed)
    
    if not quiet:
        print(f"[STRESS TEST] Date range: {trading_days[0].strftime('%Y-%m-%d')} to {trading_days[-1].strftime('%Y-%m-%d')}")
        print(f"[STRESS TEST] Total trading days: {len(trading_days)}")
    
    # Fetch all historical data upfront (more efficient than per-day calls)
    if not quiet:
        print(f"\n[STRESS TEST] Fetching {len(trading_days)} days of 1-minute bars...")
    
    start_str = trading_days[0].strftime('%Y-%m-%d')
    end_str = (trading_days[-1] + timedelta(days=1)).strftime('%Y-%m-%d')
    
    try:
        all_bars = alpaca_client.fetch_historical_bars(
            symbol=symbol,
            timeframe='1Min',
            start=start_str,
            end=end_str,
            feed='sip'
        )
        if not quiet:
            print(f"[STRESS TEST] Fetched {len(all_bars)} total bars")
    except Exception as e:
        print(f"[STRESS TEST ERROR] Failed to fetch historical data: {e}")
        return {'error': str(e)}
    
    # Fetch news for sentiment (entire range + 3 days prior for PIT lookback)
    news_start = (trading_days[0] - timedelta(days=3)).strftime('%Y-%m-%d')
    news_end = end_str
    
    if not quiet:
        print(f"[STRESS TEST] Fetching news from {news_start} to {news_end}...")
    try:
        news_list = fmp_client.fetch_historical_news(symbol, news_start, news_end, price_df=all_bars)
    except Exception as e:
        print(f"[STRESS TEST WARNING] News fetch failed: {e}, using neutral sentiment")
        news_list = []
    
    # Process rolling windows
    daily_results = []
    cumulative_equity = initial_capital
    
    # Number of complete out-of-sample days we can test
    num_oos_windows = len(trading_days) - in_sample_days
    
    if not quiet:
        print(f"\n[STRESS TEST] Processing {num_oos_windows} rolling windows...")
        print("-" * 60)
    
    # Initialize Report File
    report_path = f"stress_test_report_{symbol}.txt"
    with open(report_path, 'w') as f:
        f.write(f"STRESS TEST REPORT: {symbol}\n")
        f.write("=" * 60 + "\n")

    def log_msg(msg: str, verbose: bool = False):
        """
        Dual-stream logger:
        - Terminal: Print if not quiet OR if message is critical (WFE-REPORT)
        - File: Write ONLY if not (verbose and report_only)
        """
        if not quiet or "[WFE-REPORT]" in msg:
            print(msg)
        if not (verbose and report_only):
            with open(report_path, 'a') as f:
                f.write(msg + "\n")

    # 20-Day Rigid Lock: Track block-level metrics
    optimal_weights_locked = None  # Weights locked for RETRAIN_INTERVAL days
    block_is_pnl = 0.0
    block_oos_pnl = 0.0
    block_is_dd = 0.0
    block_oos_dd = 0.0
    block_is_sharpe = 0.0
    block_oos_sharpe = 0.0
    block_start_date = None

    for window_idx in range(num_oos_windows):
        # Define window dates
        is_start_idx = window_idx
        is_end_idx = window_idx + in_sample_days
        oos_idx = is_end_idx
        
        is_days = trading_days[is_start_idx:is_end_idx]
        oos_day = trading_days[oos_idx]
        
        is_start = is_days[0]
        is_end = is_days[-1]
        
        if True: # Always execute block, logic handled in log_msg
            log_msg(f"\n[Window {window_idx + 1}/{num_oos_windows}] IS: {is_start.strftime('%m/%d')}-{is_end.strftime('%m/%d')} | OOS: {oos_day.strftime('%m/%d')}", verbose=True)
        
        # Extract bars for this window
        is_start_str = is_start.strftime('%Y-%m-%d')
        is_end_str = (is_end + timedelta(days=1)).strftime('%Y-%m-%d')
        oos_start_str = oos_day.strftime('%Y-%m-%d')
        oos_end_str = (oos_day + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Filter bars for in-sample period
        is_mask = (all_bars.index >= is_start_str) & (all_bars.index < is_end_str)
        is_bars = all_bars.loc[is_mask].copy()
        
        # Filter bars for out-of-sample day
        oos_mask = (all_bars.index >= oos_start_str) & (all_bars.index < oos_end_str)
        oos_bars = all_bars.loc[oos_mask].copy()
        
        if len(is_bars) < 100 or len(oos_bars) < 50:
            log_msg(f"  [SKIP] Insufficient bars: IS={len(is_bars)}, OOS={len(oos_bars)}", verbose=True)
            continue
        
        # Feature engineering for in-sample
        is_df = is_bars.copy()
        is_df['log_return'] = feature_engineer.calculate_log_return(is_df)
        is_features = merge_news_pit(is_df, news_list, lookback_hours=4)
        add_technical_indicators(is_features)
        is_features = trim_warmup_period(is_features, warmup_rows=20)
        
        # Feature engineering for out-of-sample
        oos_df = oos_bars.copy()
        oos_df['log_return'] = feature_engineer.calculate_log_return(oos_df)
        oos_features = merge_news_pit(oos_df, news_list, lookback_hours=4)
        add_technical_indicators(oos_features)
        oos_features = trim_warmup_period(oos_features, warmup_rows=20)
        
        if len(is_features) < 50 or len(oos_features) < 30:
            log_msg(f"  [SKIP] Insufficient features after warmup: IS={len(is_features)}, OOS={len(oos_features)}", verbose=True)
            continue
        
        # 20-Day Rigid Lock: Only optimize weights at start of each block
        if window_idx % RETRAIN_INTERVAL == 0:
            # Telemetry for adaptive metabolism
            log_msg(f"[METABOLISM] Ticker: {symbol} | Retraining Active (3-Day Window)")
            
            # Reset block tracking at start of new block
            block_start_date = oos_day.strftime('%m/%d')
            block_is_pnl = 0.0
            block_oos_pnl = 0.0
            block_is_dd = 0.0
            block_oos_dd = 0.0
            block_is_sharpe = 0.0
            block_oos_sharpe = 0.0
            
            # Optimize weights on in-sample data
            opt_result = optimize_alpha_weights(
                is_features,
                feature_cols=['rsi_14', 'volume_zscore', 'sentiment'],
                target_col='log_return',
                horizon=15,
                metric='hit_rate'
            )
            optimal_weights_locked = opt_result['optimal_weights']
            log_msg(f"  [RIGID-LOCK] New weights locked for {RETRAIN_INTERVAL} days", verbose=True)
        
        # Use locked weights (from Day 1 of this block)
        optimal_weights = optimal_weights_locked.copy() if optimal_weights_locked else None
        
        # SENTIMENT SQUELCH: If news score is 0.5 (neutral), set sentiment weight to 0.0
        if optimal_weights and 'sentiment' in optimal_weights:
            # Check OOS sentiment median (representative of the day)
            if 'sentiment' in oos_features.columns:
                sent_median = oos_features['sentiment'].median()
                if abs(sent_median - 0.5) < 0.000001:  # Exactly 0.5
                     optimal_weights['sentiment'] = 0.0
                     log_msg("[SQUELCH] Sentiment Static Detected | Switching to Pure Physics")
        
        is_hit_rate = opt_result['best_metric'] if optimal_weights_locked else 0.5
        
        # AG: TEMPORAL LEAK PATCH - Backtester Integrity
        # CRITICAL: Alpha Score must ONLY use HISTORICAL features, never forward_return
        # Forward_return is for VALIDATION (truth) only, not SIGNAL (decision)
        
        # Sanitize features before alpha calculation - drop forward_return if present
        is_features_clean = is_features.drop(columns=['forward_return'], errors='ignore')
        oos_features_clean = oos_features.drop(columns=['forward_return'], errors='ignore')
        
        # Calculate alpha on IS and OOS using locked weights (squelched if active)
        # Using cleaned features WITHOUT forward_return
        is_alpha = calculate_alpha_with_weights(is_features_clean, optimal_weights)
        oos_alpha = calculate_alpha_with_weights(oos_features_clean, optimal_weights)
        threshold = is_alpha.median()
        
        # Prepare IS data for simulation (to get IS metrics)
        is_sim = is_features[['close', 'log_return']].copy()
        is_sim['signal'] = np.where(is_alpha > threshold, 1, -1)
        
        # Simulate IS portfolio with Liquidity Cap
        # Apply LIQUIDITY_CAP_USD: no single trade exceeds $100k regardless of equity
        effective_is_cap = min(LIQUIDITY_CAP_USD, cumulative_equity * 0.5)
        is_pnl_metrics = simulate_portfolio(
            is_sim,
            initial_capital=cumulative_equity,
            friction_bps=1.5,
            max_position_dollars=LIQUIDITY_CAP_USD
        )
        
        # Calculate IS metrics for this window
        is_pnl_dollars = is_pnl_metrics['total_return_dollars']
        is_dd = abs(is_pnl_metrics['max_drawdown_pct'])
        is_sharpe = is_pnl_metrics['sharpe_ratio']
        
        # Accumulate block-level IS metrics
        block_is_pnl += is_pnl_dollars
        block_is_dd = max(block_is_dd, is_dd)
        block_is_sharpe += is_sharpe
        
        # Prepare OOS data for simulation
        oos_sim = oos_features[['close', 'log_return']].copy()
        oos_sim['signal'] = np.where(oos_alpha > threshold, 1, -1)
        
        # Calculate OOS hit rate
        oos_sim['forward_return'] = oos_sim['log_return'].shift(-15)
        oos_valid = oos_sim.dropna()
        if len(oos_valid) > 0:
            correct = (oos_valid['signal'] * oos_valid['forward_return']) > 0
            oos_hit_rate = correct.mean()
        else:
            oos_hit_rate = 0.5
        
        # Simulate portfolio on OOS with Liquidity Cap
        # Apply LIQUIDITY_CAP_USD: no single trade exceeds $100k regardless of equity
        effective_oos_cap = min(LIQUIDITY_CAP_USD, cumulative_equity * 0.5)
        pnl_metrics = simulate_portfolio(
            oos_sim, 
            initial_capital=cumulative_equity,
            friction_bps=1.5,
            max_position_dollars=effective_oos_cap
        )
        
        daily_pnl_dollars = pnl_metrics['total_return_dollars']
        daily_pnl_pct = pnl_metrics['total_return_pct']
        oos_dd = abs(pnl_metrics['max_drawdown_pct'])
        oos_sharpe = pnl_metrics['sharpe_ratio']
        cumulative_equity = pnl_metrics['final_equity']
        
        # Accumulate block-level OOS metrics
        block_oos_pnl += daily_pnl_dollars
        block_oos_dd = max(block_oos_dd, oos_dd)
        block_oos_sharpe += oos_sharpe
        
        # Calculate WFE
        wfe = calculate_wfe(is_hit_rate, oos_hit_rate)
        
        # Store result
        day_result = {
            'date': oos_day.strftime('%Y-%m-%d'),
            'optimal_weights': optimal_weights,
            'in_sample_hit_rate': is_hit_rate,
            'out_sample_hit_rate': oos_hit_rate,
            'wfe': wfe,
            'daily_pnl_dollars': daily_pnl_dollars,
            'daily_pnl_pct': daily_pnl_pct,
            'ending_equity': cumulative_equity,
            'equity_curve': pnl_metrics['equity_curve'],
            'is_pnl_dollars': is_pnl_dollars,
            'is_max_dd': is_dd,
            'is_sharpe': is_sharpe,
            'oos_max_dd': oos_dd,
            'oos_sharpe': oos_sharpe
        }
        daily_results.append(day_result)
        
        # Print day summary
        win_loss = "WIN" if daily_pnl_dollars > 0 else "LOSS"
        log_msg(f"  IS HR: {is_hit_rate*100:.1f}% | OOS HR: {oos_hit_rate*100:.1f}% | WFE: {wfe:.2f}", verbose=True)
        log_msg(f"  P&L: ${daily_pnl_dollars:+,.2f} ({daily_pnl_pct:+.2f}%) | [{win_loss}]", verbose=True)
        
        # WFE-REPORT: Print at end of each 20-day block
        if (window_idx + 1) % RETRAIN_INTERVAL == 0:
            block_end_date = oos_day.strftime('%m/%d')
            days_in_block = min(RETRAIN_INTERVAL, window_idx + 1)
            
            # FIX WFE SIGN LOGIC:
            # If OOS_PnL < 0 and IS_PnL > 0, Profit-WFE MUST be negative
            # Formula: Profit-WFE = OOS_PnL / abs(IS_PnL)
            if block_is_pnl != 0:
                profit_wfe = block_oos_pnl / abs(block_is_pnl)
            else:
                profit_wfe = 0.0
            
            dd_wfe = block_oos_dd / block_is_dd if block_is_dd != 0 else 0.0
            avg_is_sharpe = block_is_sharpe / days_in_block
            avg_oos_sharpe = block_oos_sharpe / days_in_block
            sharpe_wfe = avg_oos_sharpe / avg_is_sharpe if avg_is_sharpe != 0 else 0.0
            
            log_msg(f"\n[WFE-REPORT] Ticker: {symbol} | Blocks: {(window_idx + 1) // RETRAIN_INTERVAL}")
            log_msg(f"  Profit-WFE: {profit_wfe:.2f}")
            log_msg(f"  Drawdown-WFE: {dd_wfe:.2f}")
            log_msg(f"  Sharpe-WFE: {sharpe_wfe:.2f}")
    
    # Aggregate results
    if not daily_results:
        print("\n[STRESS TEST] No valid windows processed!")
        return {'error': 'No valid windows'}
    
    # Build master equity curve
    all_equity_curves = [r['equity_curve'] for r in daily_results if len(r['equity_curve']) > 0]
    if all_equity_curves:
        master_equity = pd.concat(all_equity_curves)
    else:
        master_equity = pd.Series(dtype=float)
    
    # Calculate summary statistics
    total_pnl_dollars = cumulative_equity - initial_capital
    total_pnl_pct = (total_pnl_dollars / initial_capital) * 100
    
    winning_days = sum(1 for r in daily_results if r['daily_pnl_dollars'] > 0)
    losing_days = sum(1 for r in daily_results if r['daily_pnl_dollars'] <= 0)
    
    avg_wfe = np.mean([r['wfe'] for r in daily_results])
    avg_is_hr = np.mean([r['in_sample_hit_rate'] for r in daily_results])
    avg_oos_hr = np.mean([r['out_sample_hit_rate'] for r in daily_results])
    
    max_drawdown = calculate_max_drawdown(master_equity) if len(master_equity) > 0 else 0.0
    
    result = {
        'symbol': symbol,
        'total_days': len(daily_results),
        'initial_capital': initial_capital,
        'final_equity': cumulative_equity,
        'cumulative_pnl_dollars': total_pnl_dollars,
        'cumulative_pnl_pct': total_pnl_pct,
        'winning_days': winning_days,
        'losing_days': losing_days,
        'win_rate': winning_days / len(daily_results) if daily_results else 0,
        'avg_in_sample_hr': avg_is_hr,
        'avg_out_sample_hr': avg_oos_hr,
        'avg_wfe': avg_wfe,
        'max_drawdown_pct': max_drawdown,
        'daily_results': daily_results,
        'master_equity_curve': master_equity,
        'report_file_path': report_path
    }
    
    return result


def print_stress_test_summary(result: Dict) -> None:
    """
    Print formatted 15-Day Stress Test Summary.
    
    Args:
        result: Dict returned from run_rolling_backtest()
    """
    print("=" * 60)
    print("[15-DAY STRESS TEST SUMMARY]")
    print("=" * 60)
    
    # helper for dual logging within summary
    report_path = result.get('report_file_path')
    def log_sum(msg):
        print(msg)
        if report_path:
            with open(report_path, 'a') as f:
                f.write(msg + "\n")

    if 'error' in result:
        log_sum(f"[ERROR] Stress test failed: {result['error']}")
        return
    
    # Header
    log_sum(f"Symbol: {result['symbol']}")
    log_sum(f"Days Tested: {result['total_days']}")
    log_sum("-" * 60)
    
    # P&L Summary
    pnl_sign = '+' if result['cumulative_pnl_dollars'] >= 0 else ''
    log_sum(f"\n[P&L SUMMARY]")
    log_sum(f"  Initial Capital:     ${result['initial_capital']:,.2f}")
    log_sum(f"  Final Equity:        ${result['final_equity']:,.2f}")
    log_sum(f"  Cumulative P&L:      ${result['cumulative_pnl_dollars']:+,.2f} ({pnl_sign}{result['cumulative_pnl_pct']:.2f}%)")
    log_sum(f"  Max Drawdown:        {result['max_drawdown_pct']:.2f}%")
    
    # Win/Loss Summary
    log_sum(f"\n[WIN/LOSS BREAKDOWN]")
    log_sum(f"  Winning Days:        {result['winning_days']}")
    log_sum(f"  Losing Days:         {result['losing_days']}")
    log_sum(f"  Win Rate:            {result['win_rate']*100:.1f}%")
    
    # Walk-Forward Efficiency
    log_sum(f"\n[WALK-FORWARD EFFICIENCY]")
    log_sum(f"  Avg In-Sample HR:    {result['avg_in_sample_hr']*100:.2f}%")
    log_sum(f"  Avg Out-Sample HR:   {result['avg_out_sample_hr']*100:.2f}%")
    log_sum(f"  Average WFE:         {result['avg_wfe']:.3f}")
    
    # WFE Interpretation
    wfe = result['avg_wfe']
    if wfe >= 0.95:
        wfe_status = "EXCELLENT - Strong generalization"
    elif wfe >= 0.85:
        wfe_status = "GOOD - Acceptable generalization"
    elif wfe >= 0.75:
        wfe_status = "FAIR - Some overfitting present"
    else:
        wfe_status = "POOR - Significant overfitting detected"
    log_sum(f"  WFE Status:          {wfe_status}")
    
    log_sum("=" * 60)
    
    # Final Verdict
    if result['cumulative_pnl_dollars'] > 0 and wfe >= 0.80 and result['win_rate'] >= 0.5:
        log_sum("[VERDICT] [OK] STRESS TEST PASSED - Strategy shows robustness")
    else:
        log_sum("[VERDICT] [FAIL] STRESS TEST FAILED - Review strategy parameters")
    
    log_sum("=" * 60)
    
    # Daily breakdown table
    if result['daily_results']:
        log_sum("\n[DAILY BREAKDOWN]")
        log_sum(f"{'Date':<12} {'IS HR':<8} {'OOS HR':<8} {'WFE':<6} {'P&L':>12}")
        log_sum("-" * 60)
        for day in result['daily_results']:
            log_sum(f"{day['date']:<12} {day['in_sample_hit_rate']*100:>5.1f}%  {day['out_sample_hit_rate']*100:>5.1f}%  {day['wfe']:>5.2f}  ${day['daily_pnl_dollars']:>+10,.2f}")


def export_stress_test_results(result: Dict, filepath: str = 'stress_test_equity.csv') -> None:
    """
    Export stress test results to CSV.
    
    Args:
        result: Dict returned from run_rolling_backtest()
        filepath: Output file path (default: stress_test_equity.csv)
    """
    if 'error' in result or not result.get('master_equity_curve') is not None:
        print(f"[EXPORT] No data to export")
        return
    
    # Export master equity curve
    equity_df = pd.DataFrame({
        'equity': result['master_equity_curve']
    })
    equity_df.to_csv(filepath)
    print(f"[EXPORT] Master equity curve saved to: {filepath}")
    
    # Also export daily summary
    daily_df = pd.DataFrame([
        {
            'date': d['date'],
            'in_sample_hr': d['in_sample_hit_rate'],
            'out_sample_hr': d['out_sample_hit_rate'],
            'wfe': d['wfe'],
            'daily_pnl_dollars': d['daily_pnl_dollars'],
            'daily_pnl_pct': d['daily_pnl_pct'],
            'ending_equity': d['ending_equity']
        }
        for d in result['daily_results']
    ])
    
    daily_path = filepath.replace('.csv', '_daily.csv')
    daily_df.to_csv(daily_path, index=False)
    print(f"[EXPORT] Daily summary saved to: {daily_path}")
