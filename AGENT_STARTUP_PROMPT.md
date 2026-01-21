# AGENT STARTUP PROMPT - MAGELLAN ORDER EXECUTION FIX

## CONTEXT
You are taking over a critical production issue with the Magellan trading system. Three trading strategies are deployed on AWS EC2 and running successfully, but they are NOT placing orders with Alpaca because the order placement functions are stub implementations.

## CRITICAL BLOCKER
**The strategies generate signals correctly but DO NOT execute trades**. Daily Trend generated 1 BUY and 7 SELL signals on Jan 20, 2026 but none were sent to Alpaca. The `_place_buy_order()` and `_place_sell_order()` functions in all three strategy runners are just TODOs that log messages without calling the Alpaca API.

## YOUR IMMEDIATE MISSION

### Priority 1: Fix Order Placement (CRITICAL - PRODUCTION BLOCKER)
Implement actual Alpaca API order placement in these files:
- `deployable_strategies/bear_trap/aws_deployment/run_strategy.py`
- `deployable_strategies/daily_trend_hysteresis/aws_deployment/run_strategy.py`
- `deployable_strategies/hourly_swing/aws_deployment/run_strategy.py`

Required functionality:
1. Import and use `alpaca.trading.client.TradingClient`
2. Check for existing positions before buying (prevent double-entry)
3. Calculate position size based on account equity
4. Place market orders via Alpaca API
5. Log order confirmations with order IDs
6. Create trade log CSV files in `/home/ssm-user/magellan/logs/`

### Priority 2: Deep QA Pipeline for Each Strategy
End-to-end testing to verify:
1. Services start and load configs correctly
2. Credentials retrieved from AWS SSM
3. Data fetching works (direct Alpaca API with SIP feed)
4. Signals generated at correct times
5. **Orders placed with Alpaca API** ← Currently failing
6. Position tracking prevents double-entry
7. Exit signals close positions
8. Trade logging captures all activity
9. Error handling prevents crashes
10. Graceful shutdown works

### Priority 3: Fix GitHub Actions CI/CD
The deployment pipeline fails due to Black formatting:
```
21 files would be reformatted.
Error: Process completed with exit code 1.
```
Run `black .` on all files and commit the changes.

## HANDOFF DOCUMENT LOCATION
**READ THIS FIRST**: `a:\1\Magellan\CRITICAL_HANDOFF_ORDER_EXECUTION_BLOCKER.md`

This document contains:
- Complete system architecture and AWS access details
- Evidence of the order execution blocker
- Detailed implementation guidance with code examples
- EC2 instance details and SSH commands
- All three strategy configurations and schedules
- Service management commands
- Verification checklist

## SYSTEM ACCESS

**Local Workspace**: `a:\1\Magellan`

**AWS EC2 Access**:
```powershell
$env:AWS_PROFILE="magellan_deployer"
aws ssm start-session --target i-0cd785630b55dd9a2 --region us-east-2
```

**Region**: us-east-2  
**Instance**: i-0cd785630b55dd9a2 (Amazon Linux 2023)

## DEPLOYED STRATEGIES

1. **Bear Trap** (Account PA3DDLQCBJSE) - 19 symbols, momentum reclaim
2. **Daily Trend** (Account PA3A2699UCJM) - 10 symbols, RSI 55/45, signals at 16:05 ET
3. **Hourly Swing** (Account PA3ASNTJV624) - 2 symbols, RSI on 1H bars

All services are running and healthy. All are using direct Alpaca API with SIP feed (verified working). **NONE are placing orders** (verified broken).

## EVIDENCE OF THE PROBLEM

**Daily Trend signals.json** (generated Jan 20 at 21:05 UTC / 4:05 PM ET):
```json
{
  "date": "2026-01-20",
  "signals": {
    "GLD": "BUY",
    "META": "SELL",
    "AAPL": "SELL",
    "QQQ": "SELL",
    "SPY": "SELL",
    "MSFT": "SELL",
    "TSLA": "SELL",
    "AMZN": "SELL",
    "GOOGL": "HOLD",
    "IWM": "HOLD"
  }
}
```

**All Alpaca accounts show ZERO activity** - no orders, no positions, no trades.

**Why**: The order functions are stubs:
```python
def _place_buy_order(self, symbol):
    logger.info(f"[PAPER] Placing BUY order for {symbol}")
    # TODO: Implement actual Alpaca order placement  ← THIS IS THE PROBLEM
```

## YOUR FIRST ACTIONS

1. Say "I've read the handoff document and understand the critical blocker"
2. Confirm AWS SSM access to EC2 instance
3. Review the three `run_strategy.py` files and locate the stub order functions
4. Ask the user for clarification on:
   - Position sizing strategy (suggest 10% of equity per position)
   - Market orders vs Limit orders preference
   - Whether to implement stop-losses
   - Maximum daily trade limits
5. Implement order placement functions with proper error handling
6. Test locally, then deploy to EC2
7. Verify orders appear in Alpaca dashboard (PROOF OF LIFE)

## SUCCESS CRITERIA

You will have succeeded when:
- [ ] Order placement functions call Alpaca Trading API
- [ ] Test orders appear in Alpaca dashboard
- [ ] Trade log CSV files created in `/home/ssm-user/magellan/logs/`
- [ ] Position tracking prevents double-entry
- [ ] All three strategies can execute end-to-end (signal → order → confirmation)
- [ ] GitHub Actions CI/CD pipeline passes
- [ ] User confirms "proof of life" in Alpaca dashboard

## WARNING

**DO NOT** assume the previous fixes were complete just because services are running. The data fetching fix was completed successfully, but order placement was never implemented - only documented as a TODO.

**DO** verify every claim with actual evidence from EC2 logs or Alpaca dashboard.

**DO** ask the user if unsure about implementation details (position sizing, order types, etc.)

## START HERE

Begin by saying:
"I'm taking over from the previous agent to fix the critical order execution blocker in the Magellan trading system. I've read the handoff document and understand that all three strategies are running but NOT placing orders with Alpaca because the order placement functions are stub implementations. Before I implement the fixes, I need to clarify a few design decisions with you..."

Then ask the questions from "YOUR FIRST ACTIONS" section above.
