"""
Volatility Expansion Entry Strategy - Production Implementation
Discovered via blind backwards analysis on 2.46M 1-minute bars (2022-2026)

Entry Criteria (v2.0 Sanitized):
- effort_result_zscore < -0.5 (low volume absorption)
- range_ratio_mean > 1.4 (wide bars, momentum)
- volatility_ratio_mean > 1.0 (ATR expansion)
- trade_intensity_mean > 0.9 (normal liquidity)
- body_position_mean > 0.25 (bullish structure)

Exit Strategy:
- Target: 2.5 ATR from entry
- Stop Loss: 1.25 ATR from entry (2:1 R:R)
- Time Exit: 30 bars (30 minutes)
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.trade_logger import TradeLogger
from src.vol_expansion_features import (
    add_vol_expansion_features,
    check_vol_expansion_entry
)
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame


class VolatilityExpansionStrategy:
    """
    Production Volatility Expansion Entry Strategy (v2.0)
    
    Statistically-derived from unsupervised clustering of 2.46M 1-minute bars
    across SPY/QQQ/IWM (2022-2026). Positive expectancy across all VIX regimes.
    
    Performance (Research):
    - SPY: 57.9% hit rate, 0.368R expectancy
    - QQQ: 57.0% hit rate, 0.355R expectancy
    - IWM: 55.0% hit rate, 0.326R expectancy
    
    VIX Regime Performance (SPY):
    - Complacency (< 15): 60.9% hit rate, 0.413R expectancy
    - Normal (15-25): 56.9% hit rate, 0.353R expectancy
    - Panic (> 25): 46.0% hit rate, 0.190R expectancy
    """
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str,
        symbols: List[str],
        config: Dict,
    ):
        self.logger = logging.getLogger("magellan.vol_expansion")
        self.trade_logger = TradeLogger(strategy_name="vol_expansion")
        
        # Alpaca clients
        self.trading_client = TradingClient(api_key, api_secret, paper=True)
        
        # Use DataCache if USE_ARCHIVED_DATA is true, otherwise live API
        use_cache = os.getenv('USE_ARCHIVED_DATA', 'false').lower() == 'true'
        if use_cache:
            from src.data_cache import DataCache
            self.data_client = DataCache(api_key, api_secret)
            self.logger.info("📦 Using DataCache for historical data (USE_ARCHIVED_DATA=true)")
        else:
            self.data_client = StockHistoricalDataClient(api_key, api_secret)
            self.logger.info("🔴 Using live Alpaca API for historical data")
        
        self.symbols = symbols
        self.config = config
        self.params = config.get("risk_management", {})
        self.entry_config = config.get("entry_conditions", {})
        self.exit_config = config.get("exit_rules", {})
        self.feature_config = config.get("feature_engineering", {})
        
        # Strategy state
        self.positions = {}  # {symbol: position_data}
        self.daily_pnl = 0
        self.daily_trades = 0
        self.daily_loss_limit = self.params.get("max_daily_loss_dollars", 10000)
        self.max_trades_per_day = self.params.get("max_trades_per_day", 10)
        
        # Regime tracking
        self.regime_stats = {
            'COMPLACENCY': {'trades': 0, 'wins': 0},
            'NORMAL': {'trades': 0, 'wins': 0},
            'PANIC': {'trades': 0, 'wins': 0}
        }
        
        self.logger.info(f"✓ VolatilityExpansionStrategy v2.0 initialized for {len(symbols)} symbols")
        self.logger.info(f"  Entry thresholds: ER_zscore < {self.entry_config.get('effort_result_zscore_max', -0.5)}, "
                        f"RR > {self.entry_config.get('range_ratio_mean_min', 1.4)}, "
                        f"VR > {self.entry_config.get('volatility_ratio_min', 1.0)}")
    
    def process_market_data(self):
        """Fetch and process 1-minute bars for all symbols"""
        for symbol in self.symbols:
            try:
                # Fetch recent 1-min bars (need 100 for feature warmup)
                request = StockBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=TimeFrame.Minute,
                    start=datetime.now() - timedelta(minutes=120),
                    feed="sip",
                )
                bars = self.data_client.get_stock_bars(request)
                
                if bars and bars.data and symbol in bars.data:
                    self._evaluate_symbol(symbol, bars.data[symbol])
                else:
                    self.logger.warning(f"No data for {symbol}")
            
            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {e}", exc_info=True)
    
    def _evaluate_symbol(self, symbol: str, bars):
        """Evaluate entry/exit for a single symbol"""
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                "timestamp": bar.timestamp,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
                "trade_count": getattr(bar, 'trade_count', bar.volume // 100)  # Fallback
            }
            for bar in bars
        ])
        
        if len(df) < 100:
            return
        
        # Calculate features
        df = add_vol_expansion_features(df, config=self.feature_config)
        
        current = df.iloc[-1]
        
        # Check if we have a position
        if symbol in self.positions:
            self._manage_position(symbol, current, df)
        else:
            self._evaluate_entry(symbol, current, df)
    
    def _evaluate_entry(self, symbol: str, current, df):
        """Evaluate entry criteria"""
        # Check risk gates first
        if not self._check_risk_gates(symbol):
            return
        
        # Check entry conditions using v2.0 logic
        entry_signal = check_vol_expansion_entry(current, config=self.entry_config)
        
        if not entry_signal:
            self.trade_logger.log_decision(
                symbol=symbol,
                decision_type="SKIP_ENTRY",
                reason="Entry conditions not met",
                details=f"ER_z={current.get('effort_result_zscore', 0):.2f}, "
                       f"RR={current.get('range_ratio_mean', 0):.2f}, "
                       f"VR={current.get('volatility_ratio_mean', 0):.2f}",
                current_price=current["close"],
                indicator_values={
                    'effort_result_zscore': current.get('effort_result_zscore', 0),
                    'range_ratio_mean': current.get('range_ratio_mean', 0),
                    'volatility_ratio_mean': current.get('volatility_ratio_mean', 0),
                    'trade_intensity_mean': current.get('trade_intensity_mean', 0),
                    'body_position_mean': current.get('body_position_mean', 0)
                },
            )
            return
        
        # Calculate ATR for position sizing
        atr = self._calculate_atr(df)
        
        if pd.isna(atr) or atr <= 0:
            self.trade_logger.log_decision(
                symbol=symbol,
                decision_type="SKIP_ENTRY",
                reason="Invalid ATR",
                current_price=current["close"],
            )
            return
        
        # Calculate stop loss and target
        target_atr_mult = self.exit_config.get('target_atr_multiple', 2.5)
        stop_atr_mult = self.exit_config.get('stop_atr_multiple', 1.25)
        
        target_price = current["close"] + (target_atr_mult * atr)
        stop_loss = current["close"] - (stop_atr_mult * atr)
        risk_per_share = current["close"] - stop_loss
        
        if risk_per_share <= 0:
            self.trade_logger.log_decision(
                symbol=symbol,
                decision_type="SKIP_ENTRY",
                reason="Invalid risk calculation",
                details=f"Price: {current['close']}, Stop: {stop_loss}, ATR: {atr}",
                current_price=current["close"],
            )
            return
        
        # Position sizing: 2% risk per trade
        account = self.trading_client.get_account()
        risk_dollars = float(account.equity) * self.params.get('per_trade_risk_pct', 0.02)
        shares = int(risk_dollars / risk_per_share)
        position_dollars = shares * current["close"]
        
        # Cap at max position size
        max_position = self.params.get("max_position_dollars", 50000)
        if position_dollars > max_position:
            shares = int(max_position / current["close"])
            position_dollars = shares * current["close"]
        
        if shares > 0:
            self._enter_position(symbol, shares, current, stop_loss, target_price, atr, df)
    
    def _enter_position(self, symbol: str, shares: int, current, stop_loss: float, 
                       target: float, atr: float, df):
        """Execute entry order"""
        try:
            # Place market order
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=shares,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY,
            )
            
            order = self.trading_client.submit_order(order_request)
            
            # Detect VIX regime (estimate from volatility)
            regime = self._estimate_vix_regime(current.get('volatility_ratio_mean', 1.0))
            
            # Store position data
            self.positions[symbol] = {
                "entry_time": datetime.now(),
                "entry_price": current["close"],
                "shares": shares,
                "stop_loss": stop_loss,
                "target": target,
                "atr": atr,
                "highest_price": current["close"],
                "order_id": order.id,
                "regime": regime,
                "entry_features": {
                    'effort_result_zscore': current.get('effort_result_zscore', 0),
                    'range_ratio_mean': current.get('range_ratio_mean', 0),
                    'volatility_ratio_mean': current.get('volatility_ratio_mean', 0),
                }
            }
            
            # Log trade
            self.trade_logger.log_trade(
                symbol=symbol,
                action="ENTRY",
                side="BUY",
                quantity=shares,
                price=current["close"],
                order_id=order.id,
                position_size_before=0,
                position_size_after=shares,
                entry_reason=f"Vol expansion: ER_z={current.get('effort_result_zscore', 0):.2f}, "
                           f"RR={current.get('range_ratio_mean', 0):.2f}, "
                           f"VR={current.get('volatility_ratio_mean', 0):.2f}",
                market_conditions={
                    "vix_regime": regime,
                    "volatility_ratio": current.get('volatility_ratio_mean', 0),
                },
                indicators={
                    "atr": atr,
                    "effort_result_zscore": current.get('effort_result_zscore', 0),
                    "range_ratio_mean": current.get('range_ratio_mean', 0),
                },
                risk_metrics={
                    "stop_loss": stop_loss,
                    "target": target,
                    "risk_per_share": current["close"] - stop_loss,
                    "position_dollars": shares * current["close"],
                    "risk_reward_ratio": (target - current["close"]) / (current["close"] - stop_loss),
                },
            )
            
            self.daily_trades += 1
            self.regime_stats[regime]['trades'] += 1
            self.logger.info(
                f"✓ ENTRY {symbol}: {shares} shares @ ${current['close']:.2f} | "
                f"Regime: {regime} | Target: ${target:.2f} | Stop: ${stop_loss:.2f}"
            )
        
        except Exception as e:
            self.logger.error(f"Error entering {symbol}: {e}", exc_info=True)
            self.trade_logger.log_decision(
                symbol=symbol,
                decision_type="ENTRY_FAILED",
                reason=f"Order execution error: {str(e)}",
                current_price=current["close"],
            )
    
    def _manage_position(self, symbol: str, current, df):
        """Manage existing position"""
        pos = self.positions[symbol]
        
        # Update highest price
        if current["high"] > pos["highest_price"]:
            pos["highest_price"] = current["high"]
        
        # Check stop loss
        if current["low"] <= pos["stop_loss"]:
            self._exit_position(symbol, pos["stop_loss"], "STOP_LOSS", current)
            return
        
        # Check target
        if current["high"] >= pos["target"]:
            self._exit_position(symbol, pos["target"], "TARGET_HIT", current)
            return
        
        # Check time stop (30 bars)
        hold_time = (datetime.now() - pos["entry_time"]).total_seconds() / 60
        max_hold = self.exit_config.get('time_exit_minutes', 30)
        if hold_time >= max_hold:
            self._exit_position(symbol, current["close"], "TIME_STOP", current)
            return
        
        # EOD exit
        now = datetime.now()
        if now.hour >= 15 and now.minute >= 55:
            self._exit_position(symbol, current["close"], "EOD", current)
            return
    
    def _exit_position(self, symbol: str, exit_price: float, reason: str, current):
        """Execute exit order"""
        try:
            pos = self.positions[symbol]
            
            # Place market sell order
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=pos["shares"],
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )
            
            order = self.trading_client.submit_order(order_request)
            
            # Calculate P&L
            pnl_dollars = (exit_price - pos["entry_price"]) * pos["shares"]
            pnl_percent = (pnl_dollars / (pos["entry_price"] * pos["shares"])) * 100
            pnl_r = pnl_dollars / ((pos["entry_price"] - pos["stop_loss"]) * pos["shares"])
            hold_time = (datetime.now() - pos["entry_time"]).total_seconds() / 60
            
            is_win = pnl_dollars > 0
            if is_win:
                self.regime_stats[pos['regime']]['wins'] += 1
            
            # Log trade
            self.trade_logger.log_trade(
                symbol=symbol,
                action="EXIT",
                side="SELL",
                quantity=pos["shares"],
                price=exit_price,
                order_id=order.id,
                position_size_before=pos["shares"],
                position_size_after=0,
                exit_reason=reason,
                pnl_dollars=pnl_dollars,
                pnl_percent=pnl_percent,
                hold_time_minutes=hold_time,
                market_conditions={
                    "exit_price": exit_price,
                    "highest_reached": pos["highest_price"],
                    "vix_regime": pos["regime"],
                },
                additional_metrics={
                    "pnl_r": pnl_r,
                    "max_favorable_excursion": pos["highest_price"] - pos["entry_price"],
                },
            )
            
            self.daily_pnl += pnl_dollars
            self.logger.info(
                f"✓ EXIT {symbol}: {reason} | P&L: ${pnl_dollars:+.2f} ({pnl_percent:+.1f}% / {pnl_r:+.2f}R) | "
                f"Hold: {hold_time:.0f}min | Regime: {pos['regime']}"
            )
            
            # Remove position
            del self.positions[symbol]
        
        except Exception as e:
            self.logger.error(f"Error exiting {symbol}: {e}", exc_info=True)
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 20) -> float:
        """Calculate Average True Range"""
        if len(df) < period + 1:
            return None
        
        tr1 = df['high'] - df['low']
        tr2 = (df['high'] - df['close'].shift(1)).abs()
        tr3 = (df['low'] - df['close'].shift(1)).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(period).mean().iloc[-1]
        
        return atr
    
    def _estimate_vix_regime(self, volatility_ratio: float) -> str:
        """Estimate VIX regime from volatility ratio"""
        # Rough mapping: vol_ratio correlates with VIX
        # vol_ratio > 1.3 ~= VIX > 25 (PANIC)
        # 0.9 < vol_ratio <= 1.3 ~= 15 < VIX <= 25 (NORMAL)
        # vol_ratio <= 0.9 ~= VIX < 15 (COMPLACENCY)
        
        if volatility_ratio > 1.3:
            return 'PANIC'
        elif volatility_ratio > 0.9:
            return 'NORMAL'
        else:
            return 'COMPLACENCY'
    
    def _check_risk_gates(self, symbol: str) -> bool:
        """Check if risk gates allow trading"""
        # Check daily loss limit
        if self.daily_pnl <= -self.daily_loss_limit:
            self.trade_logger.log_risk_gate_failure(
                symbol=symbol,
                gate_name="MAX_DAILY_LOSS",
                gate_details={
                    "current_loss": self.daily_pnl,
                    "max_allowed": -self.daily_loss_limit,
                },
            )
            return False
        
        # Check max trades per day
        if self.daily_trades >= self.max_trades_per_day:
            self.trade_logger.log_risk_gate_failure(
                symbol=symbol,
                gate_name="MAX_TRADES_PER_DAY",
                gate_details={
                    "current_trades": self.daily_trades,
                    "max_allowed": self.max_trades_per_day,
                },
            )
            return False
        
        # Check max open positions
        max_positions = self.params.get('max_open_positions', 3)
        if len(self.positions) >= max_positions:
            self.trade_logger.log_risk_gate_failure(
                symbol=symbol,
                gate_name="MAX_OPEN_POSITIONS",
                gate_details={
                    "current_positions": len(self.positions),
                    "max_allowed": max_positions,
                },
            )
            return False
        
        return True
    
    def get_status(self) -> Dict:
        """Return current strategy status"""
        return {
            "open_positions": len(self.positions),
            "pnl_today": self.daily_pnl,
            "trades_today": self.daily_trades,
            "positions": list(self.positions.keys()),
            "regime_stats": self.regime_stats,
        }
    
    def close_all_positions(self, reason: str):
        """Emergency close all positions"""
        self.logger.warning(f"Closing all positions: {reason}")
        for symbol in list(self.positions.keys()):
            try:
                current_price = self._get_current_price(symbol)
                self._exit_position(symbol, current_price, f"EMERGENCY_{reason}", {})
            except Exception as e:
                self.logger.error(f"Error closing {symbol}: {e}")
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current market price"""
        try:
            quote = self.trading_client.get_latest_quote(symbol)
            return (quote.ask_price + quote.bid_price) / 2
        except:
            return 0
    
    def generate_end_of_day_report(self):
        """Generate EOD summary with regime breakdown"""
        summary = self.trade_logger.create_daily_summary()
        self.logger.info(
            f"EOD Summary: {summary['total_trades']} trades, P&L: ${summary['total_pnl']:.2f}"
        )
        
        # Regime performance
        for regime, stats in self.regime_stats.items():
            if stats['trades'] > 0:
                hit_rate = stats['wins'] / stats['trades']
                self.logger.info(
                    f"  {regime}: {stats['trades']} trades, {hit_rate:.1%} win rate"
                )
        
        # Reset daily counters
        self.daily_pnl = 0
        self.daily_trades = 0
        self.regime_stats = {k: {'trades': 0, 'wins': 0} for k in self.regime_stats}
