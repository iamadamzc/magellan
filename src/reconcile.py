"""
Position Reconciliation Utility for Magellan
Verifies current inventory and account status.
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to path to ensure imports work if run from src/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.executor import AlpacaTradingClient

def reconcile():
    """Fetch and display account reconciliation data."""
    load_dotenv()
    
    # Check credentials
    if not os.getenv('APCA_API_KEY_ID') or not os.getenv('APCA_API_SECRET_KEY'):
        print("[ERROR] Missing credentials. Please check .env file.")
        return

    print("\nInitializing Alpaca Client...")
    try:
        client = AlpacaTradingClient()
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return

    print("\n" + "═"*60)
    print(" 🔍 POSITION RECONCILIATION REPORT")
    print("═"*60)

    # 1. Account Snapshot
    try:
        acct = client.api.get_account()
        print(f"\n[ACCOUNT SNAPSHOT]")
        print(f"• ID:           {acct.id}")
        print(f"• Status:       {acct.status.upper()}")
        print(f"• Equity:       ${float(acct.equity):,.2f}")
        print(f"• Buying Power: ${float(acct.buying_power):,.2f}")
        print(f"• Cash:         ${float(acct.cash):,.2f}")
        print(f"• Day Trades:   {acct.daytrade_count}")
    except Exception as e:
        print(f"[ERROR] Failed to fetch account info: {e}")

    # 2. Position Inspection
    print(f"\n[INVENTORY CHECK]")
    try:
        positions = client.api.list_positions()
        
        if not positions:
            print(">> NO OPEN POSITIONS (FLAT)")
        else:
            # Header
            print(f"{'SYMBOL':<8} | {'QTY':<8} | {'AVG PRICE':<12} | {'MKT VALUE':<12} | {'UNREAL P&L':<12}")
            print("─"*62)
            
            for pos in positions:
                symbol = pos.symbol
                qty = pos.qty
                avg_entry = float(pos.avg_entry_price)
                mkt_val = float(pos.market_value)
                unreal_pl = float(pos.unrealized_pl)
                
                # Format P&L with color indicators if supported (using simple signs here)
                pl_str = f"${unreal_pl:,.2f}"
                if unreal_pl > 0:
                    pl_str = f"+{pl_str}"
                
                print(f"{symbol:<8} | {qty:<8} | ${avg_entry:<11,.2f} | ${mkt_val:<11,.2f} | {pl_str:<12}")
                
            print("─"*62)
            
    except Exception as e:
        print(f"[ERROR] Failed to fetch positions: {e}")

    print("\n" + "═"*60 + "\n")

if __name__ == "__main__":
    reconcile()
