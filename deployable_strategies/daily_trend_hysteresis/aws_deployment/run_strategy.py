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

sys.path.insert(0, '/home/ec2-user/magellan')

from src.data_cache.cache import get_cached_data
from src.features import calculate_rsi
from src.backtester_pro import BacktesterPro
import boto3

shutdown_flag = False

def signal_handler(signum, frame):
    global shutdown_flag
    logging.warning(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_flag = True

def load_config():
    config_path = os.getenv('CONFIG_PATH', '/home/ec2-user/magellan/deployable_strategies/daily_trend_hysteresis/aws_deployment/config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def get_alpaca_credentials(account_id):
    ssm = boto3.client('ssm', region_name='us-east-2')
    api_key_path = f'/magellan/alpaca/{account_id}/API_KEY'
    api_secret_path = f'/magellan/alpaca/{account_id}/API_SECRET'
    
    api_key = ssm.get_parameter(Name=api_key_path, WithDecryption=True)['Parameter']['Value']
    api_secret = ssm.get_parameter(Name=api_secret_path, WithDecryption=True)['Parameter']['Value']
    
    return api_key, api_secret

def setup_logging(config):
    log_level = config['monitoring'].get('log_level', 'INFO')
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger('magellan.daily_trend')

def is_signal_time():
    """Check if it's time to generate signals (16:05 ET)"""
    from pytz import timezone
    et = timezone('America/New_York')
    now = datetime.now(et)
    
    # Must be weekday
    if now.weekday() >= 5:
        return False
    
    # Check if 16:05
    target_time = dt_time(16, 5)
    current_time = now.time()
    
    # Window: 16:05:00 - 16:05:59
    return target_time.hour == current_time.hour and target_time.minute == current_time.minute

def is_execution_time():
    """Check if it's time to execute orders (09:30 ET)"""
    from pytz import timezone
    et = timezone('America/New_York')
    now = datetime.now(et)
    
    if now.weekday() >= 5:
        return False
    
    target_time = dt_time(9, 30)
    current_time = now.time()
    
    # Window: 09:30:00 - 09:31:00
    return target_time.hour == current_time.hour and target_time.minute == current_time.minute

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
        
    def generate_signals(self):
        """Generate entry/exit signals based on RSI"""
        logger = logging.getLogger('magellan.daily_trend')
        logger.info("Generating daily signals...")
        
        params = self.config['strategy_parameters']
        
        for symbol in self.symbols:
            try:
                # Fetch daily data
                data = get_cached_data(
                    symbol=symbol,
                    start_date=(datetime.now() - timedelta(days=150)).strftime('%Y-%m-%d'),
                    end_date=datetime.now().strftime('%Y-%m-%d'),
                    interval='1Day'
                )
                
                # Calculate RSI
                rsi = calculate_rsi(data['close'], period=params['rsi_period'])
                current_rsi = rsi.iloc[-1]
                
                # Determine signal
                if current_rsi > params['hysteresis_upper']:
                    self.signals[symbol] = 'BUY'
                    logger.info(f"{symbol}: RSI={current_rsi:.2f} > {params['hysteresis_upper']} → BUY")
                elif current_rsi < params['hysteresis_lower']:
                    self.signals[symbol] = 'SELL'
                    logger.info(f"{symbol}: RSI={current_rsi:.2f} < {params['hysteresis_lower']} → SELL")
                else:
                    self.signals[symbol] = 'HOLD'
                    logger.info(f"{symbol}: RSI={current_rsi:.2f} → HOLD")
                    
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")
        
        # Save signals to file for execution tomorrow
        signal_file = '/home/ec2-user/magellan/deployable_strategies/daily_trend_hysteresis/aws_deployment/signals.json'
        with open(signal_file, 'w') as f:
            json.dump({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'signals': self.signals
            }, f, indent=2)
        
        logger.info(f"Signals saved to {signal_file}")
    
    def execute_signals(self):
        """Execute pending signals at market open"""
        logger = logging.getLogger('magellan.daily_trend')
        logger.info("Executing signals...")
        
        # Load signals from file
        signal_file = '/home/ec2-user/magellan/deployable_strategies/daily_trend_hysteresis/aws_deployment/signals.json'
        try:
            with open(signal_file, 'r') as f:
                signal_data = json.load(f)
                signals = signal_data['signals']
        except FileNotFoundError:
            logger.warning("No signal file found, skipping execution")
            return
        
        # Execute each signal
        for symbol, signal in signals.items():
            try:
                if signal == 'BUY':
                    self._place_buy_order(symbol)
                elif signal == 'SELL':
                    self._place_sell_order(symbol)
                else:
                    logger.info(f"{symbol}: HOLD - no action")
            except Exception as e:
                logger.error(f"Error executing signal for {symbol}: {e}")
        
        logger.info("Signal execution complete")
    
    def _place_buy_order(self, symbol):
        """Place buy order via Alpaca API"""
        logger = logging.getLogger('magellan.daily_trend')
        # TODO: Implement actual Alpaca order placement
        logger.info(f"[PAPER] Placing BUY order for {symbol}")
    
    def _place_sell_order(self, symbol):
        """Place sell order via Alpaca API"""
        logger = logging.getLogger('magellan.daily_trend')
        # TODO: Implement actual Alpaca order placement
        logger.info(f"[PAPER] Placing SELL order for {symbol}")

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
    
    account_id = config['account_info']['account_id']
    try:
        api_key, api_secret = get_alpaca_credentials(account_id)
        logger.info("✓ Retrieved Alpaca API credentials from SSM")
    except Exception as e:
        logger.error(f"✗ Failed to retrieve credentials: {e}")
        return 1
    
    executor = DailyTrendExecutor(
        api_key=api_key,
        api_secret=api_secret,
        base_url=config['ssm_parameters']['base_url'],
        symbols=config['symbols'],
        config=config
    )
    
    logger.info("✓ Executor initialized")
    logger.info("Waiting for signal generation time (16:05 ET) or execution time (09:30 ET)...")
    
    signal_generated_today = False
    execution_done_today = False
    
    try:
        while not shutdown_flag:
            current_date = datetime.now().strftime('%Y-%m-%d')
            
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

if __name__ == '__main__':
    sys.exit(main())
