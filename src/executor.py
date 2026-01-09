"""
Alpaca Live Execution Module
Handles real-time trade execution via Alpaca Paper Trading API.
Uses "Marketable Limit" orders to mimic institutional execution stealth.
"""

import os
import time
import asyncio
import logging
from datetime import datetime
from typing import Optional
from alpaca_trade_api.rest import REST


# Configure live trade logger
def _setup_live_logger() -> logging.Logger:
    """Set up logger for live trade recording."""
    logger = logging.getLogger('live_trades')
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.FileHandler('live_trades.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(handler)
    
    return logger


class AlpacaTradingClient:
    """Client for executing trades via Alpaca Paper Trading API."""
    
    # PDT threshold
    PDT_EQUITY_THRESHOLD = 25000.0
    
    def __init__(self):
        """
        Initialize the Alpaca Trading Client.
        
        Credentials loaded from environment variables:
        - APCA_API_KEY_ID: Alpaca API key
        - APCA_API_SECRET_KEY: Alpaca secret key
        
        Uses Paper Trading endpoint by default.
        """
        self.api = REST(base_url='https://paper-api.alpaca.markets')
        self.logger = _setup_live_logger()
        
        # Validate connection
        try:
            account = self.api.get_account()
            print(f"[EXECUTOR] Connected to Alpaca Paper Trading")
            print(f"[EXECUTOR] Account Status: {account.status}")
            print(f"[EXECUTOR] Equity: ${float(account.equity):,.2f}")
            print(f"[EXECUTOR] Buying Power: ${float(account.buying_power):,.2f}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Alpaca: {e}")
    
    def get_account_info(self) -> dict:
        """Fetch current account information."""
        account = self.api.get_account()
        return {
            'equity': float(account.equity),
            'buying_power': float(account.buying_power),
            'cash': float(account.cash),
            'status': account.status,
            'pattern_day_trader': account.pattern_day_trader,
            'daytrade_count': int(account.daytrade_count) if hasattr(account, 'daytrade_count') else 0
        }
    
    def get_current_quote(self, symbol: str) -> dict:
        """Fetch real-time bid/ask quote for a symbol."""
        quote = self.api.get_latest_quote(symbol)
        return {
            'symbol': symbol,
            'bid_price': quote.bid_price,
            'ask_price': quote.ask_price,
            'bid_size': int(quote.bid_size),
            'ask_size': int(quote.ask_size),
            'timestamp': datetime.utcnow()
        }
    
    def check_pdt_protection(self) -> tuple[bool, str]:
        """
        Check PDT (Pattern Day Trader) protection.
        
        Returns:
            Tuple of (can_trade: bool, message: str)
        """
        account = self.get_account_info()
        equity = account['equity']
        
        if equity < self.PDT_EQUITY_THRESHOLD:
            return False, f"PDT PROTECTION: Equity ${equity:,.2f} < ${self.PDT_EQUITY_THRESHOLD:,.2f} minimum"
        
        return True, f"PDT OK: Equity ${equity:,.2f}"
    
    def check_buying_power(self, required_amount: float) -> tuple[bool, str]:
        """
        Verify sufficient buying power for trade.
        
        Args:
            required_amount: Dollar amount needed for the trade
            
        Returns:
            Tuple of (has_funds: bool, message: str)
        """
        account = self.get_account_info()
        buying_power = account['buying_power']
        
        if buying_power < required_amount:
            return False, f"INSUFFICIENT FUNDS: ${buying_power:,.2f} < ${required_amount:,.2f} required"
        
        return True, f"FUNDS OK: ${buying_power:,.2f} available"
    
    def _log_trade(self, order_id: str, symbol: str, side: str, qty: int, 
                   limit_price: float, status: str,
                   filled_avg_price: Optional[float] = None,
                   filled_qty: Optional[int] = None,
                   filled_at: Optional[str] = None):
        """
        Log trade to live_trades.log.
        
        Args:
            order_id: Unique order identifier
            symbol: Trading symbol
            side: 'buy' or 'sell'
            qty: Order quantity
            limit_price: Submitted limit price
            status: Order status (e.g., pending_new, filled, TIMEOUT_REJECTION)
            filled_avg_price: (Optional) Actual fill price
            filled_qty: (Optional) Actual filled quantity
            filled_at: (Optional) Timestamp of fill
        """
        log_entry = (
            f"ORDER_ID={order_id} | SYMBOL={symbol} | SIDE={side} | "
            f"QTY={qty} | LIMIT_PRICE=${limit_price:.2f} | STATUS={status}"
        )
        
        if filled_avg_price is not None:
            log_entry += f" | FILLED_AVG_PRICE=${filled_avg_price:.2f}"
        if filled_qty is not None:
            log_entry += f" | FILLED_QTY={filled_qty}"
        if filled_at is not None:
            log_entry += f" | FILLED_AT={filled_at}"
            
        self.logger.info(log_entry)
    
    def liquidate_all_positions(self) -> dict:
        """
        Emergency liquidation: Close ALL open positions with market orders.
        
        This is a kill-switch function for emergency situations.
        
        Returns:
            Dict with summary of liquidated positions
        """
        print("\n[EXECUTOR] ⚠ EMERGENCY LIQUIDATION INITIATED ⚠")
        print("[EXECUTOR] Fetching all open positions...")
        
        try:
            positions = self.api.list_positions()
        except Exception as e:
            error_msg = f"Failed to fetch positions: {e}"
            print(f"[EXECUTOR] ✗ {error_msg}")
            return {'success': False, 'error': error_msg, 'closed_positions': []}
        
        if not positions:
            print("[EXECUTOR] No open positions to liquidate")
            return {'success': True, 'closed_positions': [], 'message': 'No positions'}
        
        print(f"[EXECUTOR] Found {len(positions)} position(s) to liquidate")
        
        closed_positions = []
        failed_positions = []
        
        for pos in positions:
            symbol = pos.symbol
            qty = int(pos.qty)
            side = 'sell' if qty > 0 else 'buy'  # Close long or short
            abs_qty = abs(qty)
            
            print(f"[EXECUTOR] Closing {symbol}: {side.upper()} {abs_qty} shares (market order)")
            
            try:
                order = self.api.submit_order(
                    symbol=symbol,
                    qty=abs_qty,
                    side=side,
                    type='market',
                    time_in_force='day'
                )
                
                print(f"[EXECUTOR] ✓ {symbol} liquidation order submitted: ID={order.id}")
                
                # Log to file
                self._log_trade(
                    order_id=order.id,
                    symbol=symbol,
                    side=side,
                    qty=abs_qty,
                    limit_price=0.0,  # Market order has no limit
                    status=f"LIQUIDATION_{order.status}"
                )
                
                closed_positions.append({
                    'symbol': symbol,
                    'qty': qty,
                    'order_id': order.id,
                    'status': order.status
                })
                
            except Exception as e:
                error_msg = f"Failed to close {symbol}: {e}"
                print(f"[EXECUTOR] ✗ {error_msg}")
                self._log_trade(
                    order_id='FAILED',
                    symbol=symbol,
                    side=side,
                    qty=abs_qty,
                    limit_price=0.0,
                    status=f"LIQUIDATION_ERROR: {str(e)}"
                )
                failed_positions.append({'symbol': symbol, 'error': str(e)})
        
        # Summary
        print(f"\n[EXECUTOR] Liquidation Summary:")
        print(f"[EXECUTOR]   Positions Closed: {len(closed_positions)}")
        print(f"[EXECUTOR]   Failures: {len(failed_positions)}")
        
        if failed_positions:
            print(f"[EXECUTOR] ⚠ Some positions failed to close:")
            for fail in failed_positions:
                print(f"[EXECUTOR]   - {fail['symbol']}: {fail['error']}")
        
        return {
            'success': len(failed_positions) == 0,
            'closed_positions': closed_positions,
            'failed_positions': failed_positions
        }



def execute_trade(client: AlpacaTradingClient, signal: int, symbol: str = 'SPY', allocation_pct: float = 0.25) -> dict:
    """
    Execute a trade based on the alpha signal with position-aware logic.
    
    Uses "Marketable Limit" strategy for institutional-grade execution:
    - Buy: Limit at ask_price + $0.01 (ensures fill with slippage protection)
    - Sell: Limit at bid_price - $0.01 (ensures fill with slippage protection)
    
    Position-Aware Logic:
    - If signal == BUY and already LONG: Do nothing (already positioned)
    - If signal == SELL and already LONG: Sell everything to go flat
    - If signal == BUY and FLAT: Execute buy
    - If signal == SELL and FLAT: Do nothing (no position to sell)
    
    Args:
        client: AlpacaTradingClient instance
        signal: 1 for BUY, -1 for SELL
        symbol: Stock symbol (default 'SPY')
        
    Returns:
        Dict with order details or rejection reason
    """
    result = {
        'timestamp': datetime.utcnow().isoformat(),
        'symbol': symbol,
        'signal': signal,
        'executed': False,
        'order_id': None,
        'limit_price': None,
        'qty': None,
        'side': None,
        'rejection_reason': None
    }
    
    # Validate signal
    if signal not in [1, -1]:
        result['rejection_reason'] = f"Invalid signal: {signal}. Must be 1 (BUY) or -1 (SELL)"
        return result
    
    side = 'buy' if signal == 1 else 'sell'
    result['side'] = side
    
    print(f"\n[EXECUTOR] Processing {side.upper()} signal for {symbol}...")
    
    # Check current position (handles 404 gracefully)
    current_position_qty = 0
    try:
        position = client.api.get_position(symbol)
        current_position_qty = int(position.qty)
        print(f"[EXECUTOR] Current Position: {current_position_qty} shares of {symbol}")
    except Exception:
        # No position exists (404 or other error) - we are flat
        current_position_qty = 0
        print(f"[EXECUTOR] Current Position: FLAT (no {symbol} position)")
    
    # Position-Aware Logic
    if signal == 1:  # BUY signal
        if current_position_qty > 0:
            # Already long - do nothing
            result['rejection_reason'] = f"Already LONG {current_position_qty} shares. No action needed."
            print(f"[EXECUTOR] ⏸ {result['rejection_reason']}")
            return result
        # Else: we are flat, proceed to buy
    else:  # SELL signal
        if current_position_qty <= 0:
            # Already flat - nothing to sell
            result['rejection_reason'] = f"Already FLAT. No position to sell."
            print(f"[EXECUTOR] ⏸ {result['rejection_reason']}")
            return result
        # Else: we have a position, proceed to sell
    
    # Safety Check 1: PDT Protection
    pdt_ok, pdt_msg = client.check_pdt_protection()
    print(f"[EXECUTOR] {pdt_msg}")
    if not pdt_ok:
        result['rejection_reason'] = pdt_msg
        client._log_trade('REJECTED', symbol, side, 0, 0.0, pdt_msg)
        return result
    
    # Get current market quote
    try:
        quote = client.get_current_quote(symbol)
        bid_price = quote['bid_price']
        ask_price = quote['ask_price']
        print(f"[EXECUTOR] Quote: Bid=${bid_price:.2f}, Ask=${ask_price:.2f}")
    except Exception as e:
        result['rejection_reason'] = f"Failed to get quote: {e}"
        return result
    
    # Calculate limit price (Marketable Limit strategy)
    if signal == 1:  # BUY
        limit_price = round(ask_price + 0.01, 2)
    else:  # SELL
        limit_price = round(bid_price - 0.01, 2)
    
    result['limit_price'] = limit_price
    
    # Calculate quantity
    account_info = client.get_account_info()
    available_funds = account_info['buying_power']
    
    if signal == -1:
        # SELL: Use the entire current position
        qty = current_position_qty
    else:
        # BUY: Use allocation_pct of total equity (supports multi-symbol basket)
        account_equity = account_info['equity']
        allocated_capital = account_equity * allocation_pct
        qty = int(allocated_capital / ask_price)
        if qty <= 0:
            result['rejection_reason'] = f"Insufficient funds for even 1 share (allocated ${allocated_capital:,.2f})"
            return result
        print(f"[EXECUTOR] Allocation: {allocation_pct*100:.0f}% of ${account_equity:,.2f} = ${allocated_capital:,.2f} -> {qty} shares")
    
    result['qty'] = qty
    required_amount = qty * limit_price
    
    # Safety Check 2: Buying Power (for buys only)
    if signal == 1:
        bp_ok, bp_msg = client.check_buying_power(required_amount)
        print(f"[EXECUTOR] {bp_msg}")
        if not bp_ok:
            result['rejection_reason'] = bp_msg
            client._log_trade('REJECTED', symbol, side, qty, limit_price, bp_msg)
            return result
    
    # Submit the order
    print(f"[EXECUTOR] Submitting {side.upper()} LIMIT order: {qty} x {symbol} @ ${limit_price:.2f}")
    
    try:
        order = client.api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type='limit',
            time_in_force='day',
            limit_price=limit_price
        )
        
        result['executed'] = True
        result['order_id'] = order.id
        
        print(f"[EXECUTOR] ✓ Order submitted: ID={order.id}")
        print(f"[EXECUTOR]   Status: {order.status}")
        
        # Log initial submission
        client._log_trade(order.id, symbol, side, qty, limit_price, order.status)
        
        # ---------------------------------------------------------------------
        # ACTIVE ORDER POLLING & FILL TELEMETRY
        # ---------------------------------------------------------------------
        print(f"[EXECUTOR] ⏳ Polling for fill (max 10s)...")
        
        start_time = time.time()
        is_filled = False
        current_status = order.status
        
        # Polling Loop (Max 10 seconds)
        while (time.time() - start_time) < 10:
            time.sleep(1)  # 1-second interval protection
            
            try:
                # Fetch latest order status
                updated_order = client.api.get_order(order.id)
                current_status = updated_order.status
                
                if current_status == 'filled':
                    is_filled = True
                    filled_avg_price = float(updated_order.filled_avg_price) if updated_order.filled_avg_price else limit_price
                    filled_qty = int(updated_order.filled_qty)
                    filled_at = updated_order.filled_at
                    
                    print(f"[EXECUTOR] ✓ Order FILLED: {filled_qty} @ ${filled_avg_price:.2f}")
                    
                    # Log FILL confirmation with telemetry
                    client._log_trade(
                        order.id, symbol, side, qty, limit_price, 'filled',
                        filled_avg_price=filled_avg_price,
                        filled_qty=filled_qty,
                        filled_at=str(filled_at)
                    )
                    
                    # Update result dict
                    result['executed'] = True
                    result['limit_price'] = filled_avg_price  # Update to actual execution price
                    result['status'] = 'FILLED'
                    break
                
                elif current_status in ['canceled', 'expired', 'rejected']:
                    print(f"[EXECUTOR] ✗ Order {current_status.upper()}")
                    client._log_trade(order.id, symbol, side, qty, limit_price, current_status)
                    result['status'] = current_status.upper()
                    result['rejection_reason'] = f"Order {current_status}"
                    break

            except Exception as poll_err:
                print(f"[EXECUTOR] ⚠ Polling Error: {poll_err}")
        
        # Timeout handling
        if not is_filled and current_status not in ['filled', 'canceled', 'expired', 'rejected']:
            print(f"[EXECUTOR] ⏱ Timeout (10s) - Cancelling Order...")
            try:
                client.api.cancel_order(order.id)
                client._log_trade(order.id, symbol, side, qty, limit_price, 'TIMEOUT_REJECTION')
                result['status'] = 'TIMEOUT'
                result['rejection_reason'] = "Order TIMEOUT (10s) - Cancelled to prevent zombie fill"
            except Exception as cancel_err:
                print(f"[EXECUTOR] ✗ Failed to cancel: {cancel_err}")
                result['rejection_reason'] = f"Timeout & Cancel Failed: {cancel_err}"
        
    except Exception as e:
        result['rejection_reason'] = f"Order submission failed: {e}"
        client._log_trade('FAILED', symbol, side, qty, limit_price, str(e))
        print(f"[EXECUTOR] ✗ Order failed: {e}")
    
    return result


async def async_execute_trade(client: AlpacaTradingClient, signal: int, symbol: str = 'SPY', allocation_pct: float = 0.25) -> dict:
    """
    Async wrapper for execute_trade using thread pool to avoid blocking.
    
    Alpaca's REST client is synchronous, so this wraps execute_trade in
    asyncio.to_thread() to enable concurrent order processing for multi-symbol baskets.
    
    Args:
        client: AlpacaTradingClient instance
        signal: 1 for BUY, -1 for SELL
        symbol: Stock symbol
        allocation_pct: Fraction of equity to allocate per ticker (default 0.25 = 25%)
        
    Returns:
        Dict with order details or rejection reason
    """
    return await asyncio.to_thread(execute_trade, client, signal, symbol, allocation_pct)


def main():
    """CLI entry point for executor operations."""
    import argparse
    from dotenv import load_dotenv
    
    parser = argparse.ArgumentParser(description='Magellan Trade Executor')
    parser.add_argument(
        '--action',
        type=str,
        choices=['liquid-all'],
        help='Action to perform: liquid-all = Emergency liquidate all positions'
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Verify required environment variables
    if not os.getenv('APCA_API_KEY_ID') or not os.getenv('APCA_API_SECRET_KEY'):
        print("[ERROR] Missing Alpaca API credentials in environment variables")
        print("Please ensure APCA_API_KEY_ID and APCA_API_SECRET_KEY are set in .env file")
        return 1
    
    if args.action == 'liquid-all':
        print("=" * 70)
        print("EMERGENCY LIQUIDATION MODE")
        print("=" * 70)
        print("\nThis will close ALL open positions immediately using market orders.")
        
        # Require user confirmation
        confirmation = input("\nType 'CONFIRM' to proceed: ")
        if confirmation != 'CONFIRM':
            print("\n[CANCELLED] Liquidation aborted")
            return 0
        
        # Initialize client and liquidate
        try:
            client = AlpacaTradingClient()
            result = client.liquidate_all_positions()
            
            if result['success']:
                print("\n[SUCCESS] All positions liquidated successfully")
                return 0
            else:
                print("\n[WARNING] Liquidation completed with errors (see above)")
                return 1
                
        except Exception as e:
            print(f"\n[ERROR] Liquidation failed: {e}")
            return 1
    
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    exit(main())

