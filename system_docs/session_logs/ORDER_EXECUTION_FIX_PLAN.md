# ORDER EXECUTION FIX - IMPLEMENTATION PLAN
**Branch**: `fix/order-execution-blocker`  
**Priority**: CRITICAL - PRODUCTION BLOCKER  
**Date**: January 21, 2026  
**Status**: Ready for Implementation

---

## EXECUTIVE SUMMARY

All three Magellan trading strategies deployed on AWS EC2 are **generating signals correctly but NOT executing trades** with Alpaca. The order placement functions in all three strategy runners are stub implementations that only log messages without calling the Alpaca Trading API.

**Impact**: The entire production trading system is non-functional despite services running and signals being generated.

---

## CRITICAL FINDINGS

### Problem Confirmation

1. **Daily Trend Strategy** - Generated 8 signals on Jan 20, 2026 at 16:05 ET:
   - 1 BUY signal (GLD)
   - 7 SELL signals (META, AAPL, QQQ, SPY, MSFT, TSLA, AMZN)
   - **ZERO orders sent to Alpaca**

2. **Stub Implementations Found**:
   - `deployable_strategies/daily_trend_hysteresis/aws_deployment/run_strategy.py` (lines 205-215)
   - `deployable_strategies/hourly_swing/aws_deployment/run_strategy.py` (lines 152-160)
   - `deployable_strategies/bear_trap/aws_deployment/run_strategy.py` - uses BearTrapStrategy class

3. **Bear Trap Strategy** - Uses a separate class architecture:
   - Runner: `deployable_strategies/bear_trap/aws_deployment/run_strategy.py`
   - Implementation: `deployable_strategies/bear_trap/bear_trap_strategy_production.py`
   - Has stub implementations in `_enter_position()` and `_exit_position()` methods

---

## IMPLEMENTATION PLAN

### Phase 1: Daily Trend & Hourly Swing Fixes (Priority 1A)

These two strategies have similar architecture and can be fixed using the same pattern.

#### Files to Modify:
1. `deployable_strategies/daily_trend_hysteresis/aws_deployment/run_strategy.py`
2. `deployable_strategies/hourly_swing/aws_deployment/run_strategy.py`

#### Required Changes:

**A. Add Trading Client Import** (at top of file)
```python
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import csv
from pathlib import Path
```

**B. Initialize Trading Client** (in `__init__` method)
```python
# Add to DailyTrendExecutor.__init__ and HourlySwingExecutor.__init__
self.trading_client = TradingClient(api_key, api_secret, paper=True)
```

**C. Implement Order Placement Functions**

For **Daily Trend** (`_place_buy_order` and `_place_sell_order`):
- Check for existing positions before buying
- Calculate position size based on account equity (10% per position)
- Get current market price via quote API
- Place market order via Alpaca Trading API
- Log order confirmation with order ID
- Create trade log CSV file

For **Hourly Swing** (`_enter_long` and `_exit_position`):
- Same pattern as Daily Trend
- Adjust position sizing based on symbol (may be different for TSLA vs NVDA)

**D. Add Trade Logging Function**
```python
def _log_trade(self, symbol, action, qty, price, order_id):
    """Log trade to CSV file"""
    log_dir = self.config['monitoring']['log_directory']
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    date_str = datetime.now().strftime('%Y%m%d')
    log_file = Path(log_dir) / f'{strategy_name}_trades_{date_str}.csv'
    
    file_exists = log_file.is_file()
    
    with open(log_file, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'symbol', 'action', 'qty', 'price', 'order_id'])
        
        writer.writerow([
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            symbol,
            action,
            qty,
            f"{price:.2f}",
            order_id
        ])
```

#### Implementation Details:

**Position Sizing Logic**:
- Get account equity: `account = self.trading_client.get_account()`
- Calculate position size: `equity * 0.10` (10% per position)
- Convert to shares: `qty = int(position_size / current_price)`
- Minimum 1 share

**Error Handling**:
- Wrap all API calls in try/except blocks
- Log errors but don't crash the service
- Gracefully skip symbols that fail

**Position Tracking**:
- Before buying: Check `trading_client.get_open_position(symbol)` - skip if exists
- Before selling: Check `trading_client.get_open_position(symbol)` - skip if no position

---

### Phase 2: Bear Trap Strategy Fix (Priority 1B)

Bear Trap uses a more complex architecture with a separate strategy class.

#### Files to Modify:
1. `deployable_strategies/bear_trap/bear_trap_strategy_production.py`

#### Current Architecture:
- Has TradingClient already initialized (line ~55)
- Has `_enter_position()` method (lines 206-270)
- Has `_exit_position()` method (lines 300-347)
- **Problem**: These methods log but don't place actual orders

#### Required Changes:

**A. Update `_enter_position()` method**:
- Currently logs: `logger.info(f"[STUB] Would place BUY order...")`
- Need to add actual order placement:
  ```python
  order_request = MarketOrderRequest(
      symbol=symbol,
      qty=shares,
      side=OrderSide.BUY,
      time_in_force=TimeInForce.DAY
  )
  order = self.trading_client.submit_order(order_request)
  logger.info(f"✅ BUY order placed: {symbol} x{shares} (Order ID: {order.id})")
  ```

**B. Update `_exit_position()` method**:
- Currently logs: `logger.info(f"[STUB] Would place SELL order...")`
- Need to add actual order closure logic
- Get position quantity from Alpaca
- Place market sell order

**C. Position State Tracking**:
- Bear Trap maintains internal `self.positions` dict
- Must sync with actual Alpaca positions
- On startup, query Alpaca for existing positions

---

### Phase 3: Code Quality Fixes (Priority 2)

#### Black Formatting
The CI/CD pipeline is failing due to Black formatting issues (21 files need reformatting).

**Action Required**:
```bash
cd a:\1\Magellan
black deployable_strategies/
black scripts/
black src/
git add -A
git commit -m "fix: Apply Black formatting to all Python files"
```

**Files Reported by CI/CD**:
- All files in `deployable_strategies/*/aws_deployment/`
- Various files in `deployable_strategies/*/`

---

### Phase 4: Testing & Validation (Priority 3)

#### Local Testing Checklist:
- [ ] Black formatting passes: `black --check .`
- [ ] Pylint passes (or at least no new errors)
- [ ] Config validation passes: `python scripts/validate_configs.py`

#### EC2 Deployment Testing:
1. Deploy code to EC2
2. Restart all three services
3. Monitor logs for errors
4. **Place TEST orders** (small quantities)
5. **Verify orders appear in Alpaca dashboard** (CRITICAL PROOF OF LIFE)
6. Check trade log CSV files created

#### End-to-End Validation:
- [ ] Daily Trend: Wait for 16:05 ET signal generation, then 09:30 ET execution
- [ ] Hourly Swing: Monitor hourly signal processing during market hours
- [ ] Bear Trap: Monitor intraday for -15% crash signals
- [ ] All orders visible in Alpaca dashboard
- [ ] Trade logs created in `/home/ssm-user/magellan/logs/`
- [ ] No service crashes or errors

---

## DESIGN DECISIONS REQUIRED

Before implementation, clarify these details with the user:

### 1. Order Type
- **Market orders** (immediate execution at current price) - RECOMMENDED
- **Limit orders** (execute at specified price or better)

**Recommendation**: Market orders for production simplicity

### 2. Position Sizing
- **Current Plan**: 10% of account equity per position
- **Alternatives**: Fixed dollar amount, volatility-based sizing

**Recommendation**: 10% per position (validates to backtest assumptions)

### 3. Stop Losses
- **Option A**: Implement in order placement logic (bracket orders)
- **Option B**: Handle in strategy monitoring loop
- **Option C**: No automated stops (rely on strategy exit logic)

**Recommendation**: Option C for Daily Trend/Hourly Swing (they have exit logic), Option B for Bear Trap (it has active position management)

### 4. Maximum Daily Trade Limits
- **Option A**: No limits (trust strategy logic)
- **Option B**: Max 10 trades per day per strategy
- **Option C**: Max total allocation (e.g., 50% of equity)

**Recommendation**: Option C - Max 5 positions per strategy (10% each = 50% max allocation)

### 5. Order Fill Confirmation
- **Option A**: Wait for fill confirmation before updating internal state
- **Option B**: Assume immediate fill (paper trading)
- **Option C**: Async order tracking

**Recommendation**: Option B for simplicity (paper trading fills instantly)

---

## RISK MITIGATION

### Safety Guards to Implement:

1. **Position Limits**: Max 5 positions per strategy (already in configs)
2. **Size Validation**: Minimum 1 share, maximum based on account equity
3. **Duplicate Entry Prevention**: Check existing positions before buying
4. **Error Isolation**: Errors in one symbol don't crash entire strategy
5. **Graceful Degradation**: Continue processing other symbols if one fails

### Rollback Plan:
- Keep stub implementations commented out in first commit
- Deploy incrementally (Daily Trend → Hourly Swing → Bear Trap)
- Monitor each deployment for 1 trading day before proceeding

---

## SUCCESS CRITERIA

Implementation is complete when:

✅ **Code Quality**:
- [ ] All Python files pass Black formatting
- [ ] No new Pylint errors introduced
- [ ] All three runner files have complete order placement implementations

✅ **Functionality**:
- [ ] Trading clients initialized in all strategies
- [ ] Order placement functions call Alpaca Trading API
- [ ] Position tracking prevents double-entry
- [ ] Trade logging creates CSV files
- [ ] Error handling prevents service crashes

✅ **Production Validation**:
- [ ] Test orders successfully placed via Alpaca API
- [ ] Orders visible in Alpaca dashboard
- [ ] Trade log files created in `/home/ssm-user/magellan/logs/`
- [ ] Services remain stable for 24 hours
- [ ] User confirms "proof of life" in Alpaca dashboard

✅ **CI/CD**:
- [ ] GitHub Actions pipeline passes all checks
- [ ] Automated deployment to EC2 successful

---

## IMPLEMENTATION SEQUENCE

### Step 1: Fix Daily Trend Strategy (Simplest)
- Single implementation pattern
- Clear entry/exit signals
- 2 functions to implement

**Estimate**: 1-2 hours

### Step 2: Fix Hourly Swing Strategy (Similar Pattern)
- Reuse Daily Trend pattern
- Adjust for continuous monitoring
- 2 functions to implement

**Estimate**: 1 hour

### Step 3: Fix Bear Trap Strategy (Most Complex)
- Modify existing class methods
- More complex entry/exit logic
- Position state synchronization

**Estimate**: 2-3 hours

### Step 4: Black Formatting & Code Quality
- Run Black on all files
- Fix any breaking changes
- Commit formatted code

**Estimate**: 30 minutes

### Step 5: Local Testing
- Config validation
- Smoke tests
- Review all changes

**Estimate**: 1 hour

### Step 6: EC2 Deployment
- Deploy to production instance
- Restart services
- Monitor logs
- Place test orders

**Estimate**: 1-2 hours

### Step 7: Production Validation
- Monitor for 24-48 hours
- Verify orders execute correctly
- Confirm no crashes

**Estimate**: Ongoing

**Total Active Development Time**: 6-9 hours  
**Total Validation Time**: 24-48 hours

---

## FILES TO MODIFY

### Primary Implementation Files:
1. `a:\1\Magellan\deployable_strategies\daily_trend_hysteresis\aws_deployment\run_strategy.py`
2. `a:\1\Magellan\deployable_strategies\hourly_swing\aws_deployment\run_strategy.py`
3. `a:\1\Magellan\deployable_strategies\bear_trap\bear_trap_strategy_production.py`

### Supporting Files (Black Formatting):
- All `.py` files in `deployable_strategies/`
- All `.py` files in `scripts/`
- All `.py` files in `src/`

### Configuration Files (Verify, No Changes Expected):
- `deployable_strategies/*/aws_deployment/config.json`

### Documentation Files (Update After Implementation):
- `AGENT_STARTUP_PROMPT.md` - Mark as resolved
- `CRITICAL_HANDOFF_ORDER_EXECUTION_BLOCKER.md` - Update status
- `PRODUCTION_STATUS_2026-01-20.md` - Update with fix completion

---

## NEXT ACTIONS

1. **Review this plan** with the user
2. **Clarify design decisions** (order types, position sizing, etc.)
3. **Begin implementation** starting with Daily Trend
4. **Test incrementally** after each strategy fix
5. **Deploy to EC2** once all local tests pass
6. **Monitor production** for 24-48 hours

---

## QUESTIONS FOR USER

Before proceeding with implementation, please confirm:

1. **Order Type**: Market orders acceptable for all strategies?
2. **Position Sizing**: 10% of account equity per position acceptable?
3. **Stop Losses**: Rely on strategy exit logic (no bracket orders)?
4. **Max Positions**: 5 positions max per strategy acceptable?
5. **Fill Confirmation**: Assume immediate fill for paper trading?
6. **Deployment Timing**: Deploy all three strategies simultaneously or incrementally?
7. **Risk Tolerance**: Acceptable to test with small real orders or prefer extended paper testing?

---

**Plan Status**: ✅ READY FOR REVIEW  
**Next Step**: User approval to proceed with implementation
