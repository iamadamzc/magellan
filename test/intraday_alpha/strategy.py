#!/usr/bin/env python3
"""
Magellan Intraday Alpha Strategy (V1.0 Archive)
Strategy: Multi-Factor Alpha (RSI + Volume + Sentiment) on 3-5 minute bars
Original Deployment: January 10, 2026 (SPY/QQQ/IWM on Alpaca Paper Trading)

This is an archived version of the original V1.0 "Laminar DNA" deployment.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from src.features import calculate_rsi
import pandas as pd


class IntradayAlphaStrategy:
    """
    Multi-factor intraday alpha strategy using RSI, Volume, and Sentiment.
    
    Original V1.0 Configuration (Jan 10, 2026):
    - SPY: 5Min bars, 90% RSI / 0% Vol / 10% Sent, Gate 0.0
    - QQQ: 5Min bars, 80% RSI / 10% Vol / 10% Sent, Gate 0.0
    - IWM: 3Min bars, 100% RSI / 0% Vol / 0% Sent, Gate -0.2
    """

    def __init__(self, api_key, api_secret, symbols, config):
        self.api_key = api_key
        self.api_secret = api_secret
        self.symbols = symbols
        self.config = config
        self.positions = {}
        self.logger = logging.getLogger("magellan.intraday_alpha")

        # Initialize data client (with cache support for testing)
        use_cache = os.getenv('USE_ARCHIVED_DATA', 'false').lower() == 'true'
        if use_cache:
            from src.data_cache import DataCache
            self.data_client = DataCache(api_key, api_secret)
            self.logger.info("📦 Using DataCache for historical data")
        else:
            self.data_client = StockHistoricalDataClient(api_key, api_secret)
            self.logger.info("🔴 Using live Alpaca API for historical data")

        # Initialize trading client
        self.trading_client = TradingClient(api_key, api_secret, paper=True)

        # Strategy parameters per symbol
        self.params = config["strategy_parameters"]

    def calculate_alpha_score(self, symbol, df):
        """
        Calculate multi-factor alpha score.
        
        Alpha = (RSI_weight * RSI_signal) + (Vol_weight * Vol_signal) + (Sent_weight * Sent_signal)
        
        Returns:
            float: Alpha score in range [-1, 1]
        """
        params = self.params[symbol]
        
        # Calculate RSI
        rsi = calculate_rsi(df['close'], period=params['rsi_lookback'])
        current_rsi = rsi.iloc[-1]
        
        # Normalize RSI to [-1, 1] range
        # RSI > 50 → positive signal, RSI < 50 → negative signal
        rsi_signal = (current_rsi - 50) / 50.0  # Maps 0-100 to [-1, 1]
        
        # Volume signal (simplified - compare to moving average)
        vol_ma = df['volume'].rolling(window=20).mean()
        current_vol = df['volume'].iloc[-1]
        vol_ratio = current_vol / vol_ma.iloc[-1] if vol_ma.iloc[-1] > 0 else 1.0
        vol_signal = min(max((vol_ratio - 1.0), -1.0), 1.0)  # Clamp to [-1, 1]
        
        # Sentiment signal (placeholder - in V1.0 this came from external sentiment data)
        # For now, use a neutral signal
        sent_signal = 0.0
        
        # Combine signals with weights
        alpha = (
            params['rsi_wt'] * rsi_signal +
            params['vol_wt'] * vol_signal +
            params['sent_wt'] * sent_signal
        )
        
        return alpha, current_rsi, vol_ratio

    def apply_sentry_gate(self, symbol, alpha, sentiment=0.0):
        """
        Apply sentiment gate - kills alpha if sentiment below threshold.
        
        Args:
            symbol: Trading symbol
            alpha: Raw alpha score
            sentiment: Current market sentiment (default 0.0)
            
        Returns:
            float: Gated alpha score
        """
        params = self.params[symbol]
        gate_threshold = params['sentry_gate']
        
        if sentiment < gate_threshold:
            self.logger.info(
                f"{symbol}: Sentry gate activated (sentiment {sentiment:.2f} < {gate_threshold}) → Alpha killed"
            )
            return 0.0
        
        return alpha

    def generate_signal(self, symbol):
        """
        Generate trading signal for a symbol.
        
        Returns:
            int: 1 (buy), -1 (sell), 0 (hold/filter)
        """
        params = self.params[symbol]
        
        # Determine timeframe
        interval_map = {
            "3Min": TimeFrame.Minute,
            "5Min": TimeFrame.Minute,
        }
        timeframe = interval_map.get(params['interval'], TimeFrame.Minute)
        
        # Fetch intraday data
        start_date = datetime.now() - timedelta(days=5)
        end_date = datetime.now()
        
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=timeframe,
            start=start_date,
            end=end_date,
            feed="sip",
        )
        
        bars = self.data_client.get_stock_bars(request)
        
        if not bars or not bars.data or symbol not in bars.data:
            self.logger.warning(f"No data for {symbol}")
            return 0
        
        # Convert to DataFrame
        bar_list = bars.data[symbol]
        df = pd.DataFrame([
            {
                "timestamp": bar.timestamp,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            }
            for bar in bar_list
        ])
        df.set_index("timestamp", inplace=True)
        
        # Resample to correct interval if needed
        if params['interval'] == "3Min":
            df = df.resample('3T').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        elif params['interval'] == "5Min":
            df = df.resample('5T').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        
        # Calculate alpha score
        alpha, rsi, vol_ratio = self.calculate_alpha_score(symbol, df)
        
        # Apply sentry gate
        alpha = self.apply_sentry_gate(symbol, alpha, sentiment=0.0)
        
        # Generate signal from alpha
        # Alpha > 0.5 → BUY, Alpha < -0.5 → SELL, else FILTER
        if alpha > 0.5:
            signal = 1
        elif alpha < -0.5:
            signal = -1
        else:
            signal = 0
        
        self.logger.info(
            f"{symbol}: RSI={rsi:.1f}, Vol={vol_ratio:.2f}x, Alpha={alpha:.3f} → Signal={signal}"
        )
        
        return signal

    def execute_signal(self, symbol, signal):
        """Execute trading signal"""
        if signal == 1:
            self._enter_long(symbol)
        elif signal == -1:
            self._exit_position(symbol)
        # signal == 0: do nothing

    def _enter_long(self, symbol):
        """Place buy order"""
        try:
            # Check if already have position
            try:
                position = self.trading_client.get_open_position(symbol)
                self.logger.warning(f"Already have position in {symbol}, skipping")
                return
            except Exception:
                pass  # No position, proceed

            # Get account equity
            account = self.trading_client.get_account()
            equity = float(account.equity)
            
            # Position sizing with cap
            params = self.params[symbol]
            position_cap = params['position_cap_usd']
            allocated_capital = equity * 0.25  # 25% allocation
            
            if allocated_capital > position_cap:
                self.logger.info(
                    f"{symbol}: Position cap enforced ${allocated_capital:,.0f} → ${position_cap:,.0f}"
                )
                allocated_capital = position_cap

            # Get current price
            quote_request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quote = self.data_client.get_stock_latest_quote(quote_request)
            current_price = float(quote[symbol].ask_price)

            # Calculate quantity
            qty = int(allocated_capital / current_price)

            if qty < 1:
                self.logger.warning(f"Position size too small for {symbol}, skipping")
                return

            # Place order
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY,
            )

            order = self.trading_client.submit_order(order_request)
            self.logger.info(
                f"✅ LONG {symbol}: {qty} shares @ ${current_price:.2f} (Order: {order.id})"
            )

        except Exception as e:
            self.logger.error(f"❌ Error entering LONG {symbol}: {e}", exc_info=True)

    def _exit_position(self, symbol):
        """Close position"""
        try:
            # Check if have position
            try:
                position = self.trading_client.get_open_position(symbol)
                qty = int(float(position.qty))
            except Exception:
                self.logger.info(f"No position in {symbol} to exit")
                return

            # Get current price
            quote_request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quote = self.data_client.get_stock_latest_quote(quote_request)
            current_price = float(quote[symbol].bid_price)

            # Place sell order
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )

            order = self.trading_client.submit_order(order_request)
            self.logger.info(
                f"✅ EXIT {symbol}: {qty} shares @ ${current_price:.2f} (Order: {order.id})"
            )

        except Exception as e:
            self.logger.error(f"❌ Error exiting {symbol}: {e}", exc_info=True)

    def process_signals(self):
        """Process signals for all symbols"""
        for symbol in self.symbols:
            try:
                signal = self.generate_signal(symbol)
                self.execute_signal(symbol, signal)
            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {e}", exc_info=True)
