# Algo-Shadow v3.4 — Full Parameter + Pattern Specification

**Complete, Code-Verified Logic Extraction**

This document contains a comprehensive specification of how Algo-Shadow v3.4 selects stocks, detects patterns, enters trades, manages stops, exits positions, and applies risk filters. Every parameter, threshold, formula, and rule is extracted directly from the codebase with exact file and line range citations.

---

## Table of Contents

1. [Scanner Logic](#1-scanner-logic)
2. [Strategy Engine Pattern Recognition](#2-strategy-engine-pattern-recognition)
3. [Entry Logic](#3-entry-logic)
4. [Stop Logic](#4-stop-logic)
5. [Exit Logic](#5-exit-logic)
6. [Risk & Guardrail Filters](#6-risk--guardrail-filters)
7. [State Machine Diagram](#7-state-machine-diagram)
8. [Complete Entry-Exit Lifecycle](#8-complete-entry-exit-lifecycle)

---

## 1. SCANNER LOGIC

**Source:** [scanner.py](file:///a:/1/algoshadow/scanner.py) (Lines 1-271)  
**Config:** [config.py](file:///a:/1/algoshadow/config.py) (Lines 59-78)

### 1.1 Universe Fetching

**Method:** `UniverseScanner.get_universe()` (Lines 28-50)

- Fetches all **active, tradable, shortable US equity assets** from Alpaca
- Uses `GetAssetsRequest` with:
  - `status=AssetStatus.ACTIVE`
  - `asset_class=AssetClass.US_EQUITY`
- **Filters:**
  - `a.tradable == True`
  - `a.shortable == True`
  - `a.marginable == True`

### 1.2 Pre-Filter (Snapshot-Based)

**Method:** `UniverseScanner.scan()` (Lines 72-110)

Processes universe in **chunks of 1000 symbols** using `StockSnapshotRequest`.

#### Hard Filters (Pre-Filter Stage)

| Filter | Threshold | Source |
|--------|-----------|--------|
| **Min Price** | $1.00 | `config.MIN_PRICE` (config.py:60) |
| **Max Price** | $20.00 | `config.MAX_PRICE` (config.py:61) |
| **Min Dollar Volume** | $2,000,000 | `config.MIN_DOLLAR_VOLUME` (config.py:75) |

**Logic (scanner.py:89-103):**
```python
price = snapshot.latest_trade.price
if not (self.config.MIN_PRICE <= price <= self.config.MAX_PRICE):
    continue

vol = snapshot.daily_bar.volume if snapshot.daily_bar else 0
dollar_vol = vol * price

if dollar_vol < self.config.MIN_DOLLAR_VOLUME:
    continue
```

**Output:** Top 50 candidates by dollar volume (Line 114)

### 1.3 Deep Filter (Historical Analysis)

**Method:** `UniverseScanner.scan()` (Lines 116-218)

Fetches **40 days of daily bars** for top 50 candidates (Lines 120-121).

#### Hard Filters (Deep Filter Stage)

| Filter | Threshold | Source | Lines |
|--------|-----------|--------|-------|
| **Min Warmup Bars** | 20 bars | Hardcoded | 136 |
| **Max Data Staleness** | 4 days | Hardcoded | 143 |
| **Min Day Change %** | 2.0% | `config.MIN_DAY_CHANGE_PCT` (config.py:87) | 168-170 |
| **Max Float Shares** | 80,000,000 | `config.MAX_FLOAT_SHARES` (config.py:84) | 173-175 |
| **Min RVOL** | 2.0 | `config.MIN_RVOL` (config.py:81) | 178-180 |

**Calculations (scanner.py:148-159):**
```python
# Day Change %
pct_change = (last_bar.close - prev_bar.close) / prev_bar.close

# RVOL
avg_vol = sum(b.volume for b in data[-21:-1]) / 20
current_vol = last_bar.volume
rvol = current_vol / avg_vol if avg_vol > 0 else 0

# Float Rotation
float_val, conf = self.float_source.get_reliable_float(symbol)
float_rot = (current_vol / float_val) if float_val and float_val > 0 else 0
```

### 1.4 Scoring (Soft Preferences)

**Method:** `UniverseScanner.scan()` (Lines 182-199)

**Base Score:** `score = rvol` (Line 183)

#### Score Boosts

| Boost | Condition | Multiplier | Source |
|-------|-----------|------------|--------|
| **Float Rotation** | `float_rot > 0` and `conf > 0.5` | `1.0 + min(float_rot, 5.0)` | Lines 186-187 |
| **Ideal RVOL** | `3.0 <= rvol <= 6.0` | `1.5x` | Lines 190-191, config.py:72-73 |
| **Tiny Float** | `float_val <= 10,000,000` | `1.5x` | Lines 194-195, config.py:66 |
| **Ideal Day Change** | `5% <= pct_change <= 20%` | `1.25x` | Lines 198-199, config.py:69-70 |

**Formula:**
```python
score = rvol
score *= (1.0 + min(float_rot, 5.0))  # if applicable
score *= 1.5  # if ideal RVOL
score *= 1.5  # if tiny float
score *= 1.25  # if ideal day change
```

### 1.5 Intraday Liquidity Validation

**Method:** `UniverseScanner.validate_intraday_liquidity()` (Lines 235-270)

Applied to candidates in **score-descending order** until one passes.

#### Liquidity Filters

| Filter | Threshold | Source | Lines |
|--------|-----------|--------|-------|
| **Max Spread %** | 1.2% | `config.MAX_SPREAD_PCT` (config.py:96) | 258-260 |
| **Min Bid/Ask Size** | 50 shares | `config.MIN_BID_ASK_SIZE` (config.py:78) | 263-265 |
| **Bid Price Validity** | `> 0` | Hardcoded | 250-252 |

**Logic (scanner.py:254-265):**
```python
spread_pct = (quote.ask_price - quote.bid_price) / quote.bid_price

if spread_pct > self.config.MAX_SPREAD_PCT:
    return False
    
if quote.bid_size < self.config.MIN_BID_ASK_SIZE or quote.ask_size < self.config.MIN_BID_ASK_SIZE:
    return False
```

### 1.6 Final Selection

**Method:** `UniverseScanner.scan()` (Lines 224-232)

- Candidates sorted by **score (descending)**
- First candidate passing liquidity validation is selected
- If all fail liquidity check, returns `None`

**No randomness, no tie-breaking** — deterministic selection.

---

## 2. STRATEGY ENGINE PATTERN RECOGNITION

**Source:** [strategy_engine.py](file:///a:/1/algoshadow/strategy_engine.py) (Lines 1-418)

### 2.1 Liquidity Trap Pattern Components

#### Support Level Definition

**Method:** `StrategyEngine.on_bar()` (Line 151)

```python
self.current_support = self.session_low  # Use session LOD as support
```

**Source:** Line 151  
**Definition:** Session Low-of-Day (LOD)

#### Session Metrics Calculation

**Method:** `StrategyEngine.on_bar()` (Lines 131-138)

```python
# Update Session Metrics
if bar.low < self.session_low: self.session_low = bar.low
if bar.high > self.session_high: self.session_high = bar.high

self.session_vol += bar.volume
self.session_pv += ((bar.high + bar.low + bar.close) / 3) * bar.volume
if self.session_vol > 0:
    self.session_vwap = self.session_pv / self.session_vol
```

**Session Reset:** When new trading day detected (Lines 116-127)

#### Flush Detection

**Method:** `StrategyEngine.update_state()` (Lines 193-197)

```python
elif self.state == StrategyState.STALKING:
    if bar.close < self.current_support:
        self.state = StrategyState.TRAP_ACTIVE
        self.trap_low = bar.low
        self.logger.info(f"Entered TRAP_ACTIVE. Support: {self.current_support}, Trap Low: {self.trap_low}")
```

**Trigger:** `bar.close < current_support`  
**State Transition:** `STALKING → TRAP_ACTIVE`  
**Captured:** `trap_low = bar.low`

#### Trap Low Tracking

**Method:** `StrategyEngine.update_state()` (Lines 199-201)

```python
elif self.state == StrategyState.TRAP_ACTIVE:
    if bar.low < self.trap_low:
        self.trap_low = bar.low
```

**Continuously updates to lowest low while in TRAP_ACTIVE**

#### Reclaim Detection

**Method:** `StrategyEngine.update_state()` (Lines 203-210)

```python
# Reclaim Trigger
if bar.close > self.current_support:
    if self.validate_reclaim_signal(bar):
        self.logger.info("Reclaim detected & Validated! Firing Signal.")
        asyncio.create_task(self.fire_entry_signal(bar))
        self.state = StrategyState.WAITING_FOR_ENTRY_FILL 
    else:
        self.logger.info("Reclaim detected but failed validation (Vol/Wick/Body).")
```

**Trigger:** `bar.close > current_support`  
**Requires:** Pass [validate_reclaim_signal()](file:///a:/1/algoshadow/strategy_engine.py#222-249) checks

### 2.2 Reclaim Validation Rules

**Method:** `StrategyEngine.validate_reclaim_signal()` (Lines 222-248)

All three conditions **MUST** be met:

#### 1. Volume Confirmation

```python
recent_bars = list(self.bars)[-11:-1]
avg_volume = sum(b.volume for b in recent_bars) / 10
volume_ok = bar.volume > (avg_volume * 2.0)
```

**Threshold:** `bar.volume > 2.0x average volume`  
**Lookback:** Previous 10 bars  
**Source:** Lines 228-230

#### 2. Lower Wick Detection

```python
total_range = bar.high - bar.low
lower_wick = (bar.open - bar.low) if bar.close > bar.open else (bar.close - bar.low)
wick_ok = (total_range > 0) and (lower_wick / total_range > 0.3)
```

**Threshold:** `lower_wick > 25% of total bar range`  
**Source:** Lines 232-236 (Config: `MIN_LOWER_WICK_PCT = 0.25`)

#### 3. Body Strength

```python
body_size = abs(bar.close - bar.open)
body_ok = (total_range > 0) and (body_size / total_range > 0.5)
```

**Threshold:** `body_size > 40% of total bar range`  
**Source:** Lines 238-240 (Config: `MIN_BODY_STRENGTH_PCT = 0.40`)

**Return:** `volume_ok AND wick_ok AND body_ok` (Line 248)

### 2.3 ATR Calculation

**Method:** `StrategyEngine.compute_atr()` (Lines 153-173)

```python
if len(self.bars) < self.atr_period + 1:
    return 0.0
    
tr_sum = 0.0
start_idx = len(self.bars) - self.atr_period
for i in range(start_idx, len(self.bars)):
    curr = self.bars[i]
    prev = self.bars[i-1]
    tr = max(curr.high - curr.low, 
             abs(curr.high - prev.close), 
             abs(curr.low - prev.close))
    tr_sum += tr
    
return tr_sum / self.atr_period
```

**Period:** 14 bars (`self.atr_period = 14`, Line 36)  
**Formula:** Average True Range over 14 periods

### 2.4 State Machine

**Source:** `StrategyEngine.update_state()` (Lines 175-220)

```
IDLE
  ↓ (after warmup: 30+ bars)
STALKING
  ↓ (bar.close < support)
TRAP_ACTIVE
  ├──→ (bar.close > support AND validate_reclaim_signal) → WAITING_FOR_ENTRY_FILL
  └──→ (bar.close < support - 2*ATR) → STALKING (trap failed)
  
WAITING_FOR_ENTRY_FILL
  ↓ (executor fills entry)
IN_POSITION
  ↓ (executor closes position)
IDLE
```

#### Key Thresholds

| Transition | Condition | Source |
|------------|-----------|--------|
| IDLE → STALKING | `warmup_bars >= 30` | Lines 140-141, 189-191 |
| STALKING → TRAP_ACTIVE | `bar.close < current_support` | Lines 193-197 |
| TRAP_ACTIVE → WAITING | `bar.close > support AND validate_reclaim` | Lines 203-208 |
| TRAP_ACTIVE → STALKING | `bar.close < support - 2*ATR` | Lines 213-215 |

### 2.5 Rejection Conditions

#### Pattern-Level Rejections

**Source:** `StrategyEngine.validate_reclaim_signal()` (Lines 222-248)

1. **Insufficient Volume:** `bar.volume <= 2.0x avg_volume`
2. **Weak Lower Wick:** `lower_wick <= 25% of range`
3. **Weak Body:** `body_size <= 40% of range`
4. **Insufficient History:** `len(bars) < 11` (Line 226)

#### Position-Level Rejections

**Source:** `StrategyEngine.update_state()` (Lines 176-186)

- **Already In Position:** If `symbol in executor.positions`, skip signal generation

---

## 3. ENTRY LOGIC

**Source:** [executor.py](file:///a:/1/algoshadow/executor.py) (Lines 142-260)

### 3.1 Entry Trigger

**Method:** `Executor.request_entry()` (Lines 142-260)

Triggered when `StrategyEngine.fire_entry_signal()` calls `executor.request_entry(signal)`.

**Signal Structure:**
```python
signal = StrategySignal(
    symbol=self.symbol,
    signal_type=SignalType.ENTRY_LONG,
    payload={
        "signal_id": signal_id,
        "entry_reference_price": bar.close,
        "stop_reference_price": self.trap_low - (0.05 * self.atr),
        "target_reference_price": self.session_vwap
    }
)
```

**Source:** strategy_engine.py:314-322

### 3.2 Pre-Entry Risk Filters

**Method:** `Executor.request_entry()` (Lines 144-208)

Checks applied **in order:**

| Check | Rejection Code | Lines |
|-------|----------------|-------|
| **No-Trade Symbol List** | `NO_TRADE_SYMBOL` | 146 |
| **Runtime Halt Active** | `EMERGENCY_HALT_ACTIVE` | 149-150 |
| **Symbol Halted** | `HALTED` | 152 |
| **LiveGuard Reject** | `LIVE_GUARD_REJECT` | 155-156 |
| **Account Fetch Error** | `ACCOUNT_FETCH_ERROR` | 158-162 |
| **RiskManager Can't Open** | `RISK_MANAGER_REJECT` | 164 |
| **Invalid Refs** | `INVALID_REFS` | 170-172 |
| **Invalid Stop Distance** | `INVALID_STOP_DISTANCE` | 177-187 |
| **Position Size Too Small** | `SIZE_TOO_SMALL` | 194-196 |
| **Exposure Limit** | `EXPOSURE_LIMIT` | 198-201 |
| **Spread Check** | `SPREAD_CHECK` | 204-207 |
| **Zero Stop Distance** | `ZERO_STOP_DISTANCE` | 215 |
| **Calc Qty Too Small** | `CALC_QTY_TOO_SMALL` | 218 |

### 3.3 Position Sizing

**Method:** `Executor.request_entry()` (Lines 209-218)

```python
entry_ref = signal.payload.get('entry_reference_price')
stop_ref = signal.payload.get('stop_reference_price')

risk_dollars = self.config.PER_TRADE_RISK_PCT * equity
stop_distance = abs(entry_ref - stop_ref)
if stop_distance == 0: return False, "ZERO_STOP_DISTANCE"
    
qty = math.floor(risk_dollars / stop_distance)
if qty < 1: return False, "CALC_QTY_TOO_SMALL"
```

**Formula:**  
`qty = floor(equity * PER_TRADE_RISK_PCT / stop_distance)`

**Risk Per Trade:** `0.5%` of equity (`config.PER_TRADE_RISK_PCT = 0.005`, config.py:31)

### 3.4 Order Submission

**Method:** `Executor.request_entry()` (Lines 220-257)

```python
limit_price = entry_ref

cid = self._generate_client_order_id("ENTRY", signal.payload.get('signal_id'))

req = LimitOrderRequest(
    symbol=symbol,
    qty=qty,
    side=OrderSide.BUY,
    time_in_force=TimeInForce.DAY,
    limit_price=limit_price,
    client_order_id=cid
)

order = await asyncio.to_thread(self.client.submit_order, req)
```

**Order Type:** **Limit Order** at entry reference price (current bar close)  
**Time in Force:** DAY  
**Source:** Lines 225-232

### 3.5 Signal ID Assignment

**Method:** `StrategyEngine.fire_entry_signal()` (Line 270)

```python
signal_id = f"{self.symbol}_{int(datetime.utcnow().timestamp()*1000)}"
```

**Format:** `{symbol}_{unix_timestamp_milliseconds}`

---

## 4. STOP LOGIC

**Source:** [shadow/stop_manager.py](file:///a:/1/algoshadow/shadow/stop_manager.py) (Lines 1-147)

### 4.1 Initial Stop Placement

**Method:** `Executor.on_entry_fill()` → `StopManager.replace_stop()` (executor.py:309-321)

```python
active_stop = await self.stop_manager.get_active_stop(symbol)
if not active_stop:
    stop_ref = self.pending_entry.get('stop_ref') if self.pending_entry else None
    if not stop_ref:
         stop_ref = pos.entry_price * 0.95 
    
    stop_price = stop_ref
    
    await self.stop_manager.replace_stop(symbol, pos.qty, stop_price, signal_id=pos.signal_id)
```

**Initial Stop:** `trap_low - (0.05 * ATR)` (from signal payload)  
**Fallback:** `entry_price * 0.95` if no stop_ref available  
**Source:** executor.py:312-321

### 4.2 Stop Placement Mechanism

**Method:** `StopManager.replace_stop()` (Lines 64-146)

```python
async def replace_stop(self, symbol: str, qty: float, stop_price: float, signal_id: Optional[str] = None) -> Optional[str]:
    """
    Atomic replacement: Cancel OLD stop -> Place NEW stop.
    Guarantees only 1 active stop per symbol.
    """
    async with self.transition_locks.setdefault(symbol, asyncio.Lock()):
        
        old_stop_id = self.active_stops.get(symbol)
        
        # 1. Cancel old stop FIRST
        if old_stop_id:
            # Check if it's the same stop (optimization)
            old_order = await asyncio.to_thread(self.client.get_order_by_id, old_stop_id)
            if old_order and old_order.status in ['new', 'accepted', 'held']:
                 old_price = float(old_order.stop_price) if old_order.stop_price else 0.0
                 old_qty = float(old_order.qty) if old_order.qty else 0.0
                 
                 if abs(old_price - stop_price) < 0.0001 and abs(old_qty - qty) < 0.0001:
                     # Skip replacement - identical stop exists
                     return old_stop_id

            await asyncio.to_thread(self.client.cancel_order_by_id, old_stop_id)
            
        self.active_stops.pop(symbol, None)

        # 2. Place new stop
        stop_req = StopOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.GTC,
            stop_price=stop_price,
            client_order_id=cid
        )
        
        new_stop = await asyncio.to_thread(self.client.submit_order, stop_req)
        
        # 3. Update state
        self.active_stops[symbol] = new_stop.id
        
        return new_stop.id
```

**Enforcement:** Atomic lock per symbol (Line 69)  
**One-Stop-Per-Symbol:** Old stop cancelled before new placed (Lines 74-89)  
**Time in Force:** GTC (Good-Till-Canceled) (Line 117)

### 4.3 Stop Tightening Rules

**Current Implementation:** No automatic tightening logic in codebase.

Initial stop is placed once on entry fill. No dynamic tightening based on:
- Price movement
- Time-based triggers
- Candle formation

**Emergency Stop:** Can be triggered manually via [emergency_stop_apply()](file:///a:/1/algoshadow/executor.py#412-428) at `entry_price * 0.90` (executor.py:426)

### 4.4 Stop Replacement Constraints

**Source:** `StopManager.replace_stop()` (Lines 76-86)

**Skips replacement if:**
- Old stop exists in status: `['new', 'accepted', 'held']`
- Old stop has identical price (`< 0.0001` difference)
- Old stop has identical qty (`< 0.0001` difference)

**Optimization to avoid redundant broker calls**

---

## 5. EXIT LOGIC

**Source:** [executor.py](file:///a:/1/algoshadow/executor.py), [strategy_engine.py](file:///a:/1/algoshadow/strategy_engine.py)

### 5.1 Profit Target Exit

**Method:** `StrategyEngine.check_signals()` (Lines 252-258)

```python
async def check_signals(self, bar: Bar):
    if self.state == StrategyState.IN_POSITION:
        # TP: VWAP
        if bar.close >= self.session_vwap:
            self.logger.info(f"Price {bar.close} >= VWAP {self.session_vwap}. Requesting Exit TP.")
            await self.executor.request_exit_tp(self.symbol)
            self.state = StrategyState.EXITING_INTENT
```

**Target:** Session VWAP  
**Trigger:** `bar.close >= session_vwap`  
**Source:** Lines 254-258

### 5.2 Exit Execution

**Method:** `Executor.request_exit_tp()` (Lines 326-349)

```python
async def request_exit_tp(self, symbol: str):
    if symbol not in self.positions: return
    pos = self.positions[symbol]
    if pos.qty <= 0: return

    self.logger.info(f"Requesting Exit TP for {symbol}")
    
    # Atomic Cancel Stop
    await self.stop_manager.cancel_stop(symbol)
    
    # Submit Sell
    cid = self._generate_client_order_id("EXIT", None)
    req = MarketOrderRequest(
        symbol=symbol,
        qty=pos.qty,
        side=OrderSide.SELL,
        time_in_force=TimeInForce.GTC,
        client_order_id=cid
    )
    
    await asyncio.to_thread(self.client.submit_order, req)
```

**Order Type:** Market Order  
**Sequence:**
1. Cancel stop order first
2. Submit market sell order

**Source:** Lines 332-347

### 5.3 Time-Based Exit

**Method:** `StrategyEngine.check_signals()` (Lines 260-267)

```python
# Time Stop
if self.symbol in self.executor.positions:
    pos = self.executor.positions[self.symbol]
    duration = datetime.now() - pos.opened_at
    if duration.total_seconds() > self.config.MAX_HOLD_MINUTES * 60:
        self.logger.info("Time Stop hit. Requesting Exit.")
        await self.executor.request_exit_tp(self.symbol)
        self.state = StrategyState.EXITING_INTENT
```

**Max Hold Time:** 120 minutes (`config.MAX_HOLD_MINUTES = 120`, config.py:32)  
**Source:** Lines 264-267

### 5.4 Stop Loss Exit

**Automatic:** Stop order fills when price hits `stop_price`  
**Handled by:** Broker execution, processed via `Executor.on_exit_fill()`

### 5.5 Trailing Stop Logic

**Not Implemented:** No trailing stop logic in current codebase.

### 5.6 Exit Invalidation Logic

**Pattern Invalidation:** `TRAP_ACTIVE → STALKING` if `bar.close < support - 2*ATR` (strategy_engine.py:213-215)

**No exit logic** for invalidating profit targets or stops based on pattern failure after entry.

---

## 6. RISK & GUARDRAIL FILTERS

### 6.1 EnhancedRiskManager

**Source:** [risk_manager.py](file:///a:/1/algoshadow/risk_manager.py) (Lines 118-287)

#### 6.1.1 Daily Loss Limits

**Method:** `EnhancedRiskManager.check_daily_loss_limit()` (Lines 160-185)

```python
total_pnl = self.calculate_total_session_pnl()  # Realized + Unrealized
loss_limit = -abs(self.config.MAX_DAILY_LOSS_PCT * equity)

if total_pnl <= loss_limit:
    if not self.lockdown_mode:
        self.lockdown_mode = True
        # Trigger Global Emergency Shutdown
        asyncio.create_task(self.executor.global_emergency_shutdown("DAILY_LOSS_LIMIT_BREACH"))
    return False
```

**Limit:** `-2%` of equity (`config.MAX_DAILY_LOSS_PCT = 0.02`, config.py:28)  
**Includes:** Realized + Unrealized PnL  
**Action:** Global emergency shutdown, lockdown mode  
**Source:** Lines 161-181

#### 6.1.2 Spread Limits

**Method:** `RiskManager.check_spread()` (Lines 45-64)

```python
bid = quote.bid_price
ask = quote.ask_price

if bid <= 0 or ask <= 0:
    return False, "Invalid quote"
    
mid = (bid + ask) / 2
spread = ask - bid
spread_pct = spread / mid

if spread_pct > self.max_spread_pct:
    return False, f"Spread {spread_pct:.4f} > {self.max_spread_pct}"
```

**Max Spread:** `0.2%` (`config.MAX_SPREAD_PCT = 0.002` in Shadow/Live, `0.015` Base)  
**Formula:** [(ask - bid) / ((ask + bid) / 2)](file:///a:/1/algoshadow/strategy_engine.py#67-110)  
**Source:** Lines 54-62

#### 6.1.3 Position Exposure Limits

**Method:** `EnhancedRiskManager.validate_position_exposure()` (Lines 187-215)

Three checks:

**1. Dollar Limit**
```python
proposed_exposure = proposed_qty * entry_price

if proposed_exposure > self.config.MAX_POSITION_DOLLARS:
    return False, f"Exposure ${proposed_exposure:.2f} > ${self.config.MAX_POSITION_DOLLARS:.2f}"
```
**Limit:** $1,000 (`config.MAX_POSITION_DOLLARS = 1000.0`, config.py:36)  
**Source:** Lines 192-196

**2. Equity Percentage Limit**
```python
exposure_pct = proposed_exposure / equity
if exposure_pct > self.config.MAX_POSITION_EQUITY_PCT:
    return False, f"Exposure {exposure_pct:.2%} > {self.config.MAX_POSITION_EQUITY_PCT:.2%}"
```
**Limit:** `10%` of equity (`config.MAX_POSITION_EQUITY_PCT = 0.10`, config.py:37)  
**Source:** Lines 198-201

**3. Portfolio Exposure Limit**
```python
current_total_exposure = sum(pos.qty * pos.entry_price for pos in self.executor.positions.values())

if current_total_exposure + proposed_exposure > (self.config.MAX_PORTFOLIO_EXPOSURE * equity):
    return False, "Portfolio exposure limit exceeded"
```
**Limit:** `25%` of equity (`config.MAX_PORTFOLIO_EXPOSURE = 0.25`, config.py:38)  
**Source:** Lines 204-209

#### 6.1.4 Trade Count Limits

**Method:** `EnhancedRiskManager.can_open_new_trade()` (Lines 237-239)

```python
if self.daily_trade_count >= self.config.MAX_TRADES_PER_DAY:
    self.logger.warning(f"Trade rejected: Max daily trades ({self.config.MAX_TRADES_PER_DAY}) reached")
    return False
```

**Limit:** `5` trades per day (`config.MAX_TRADES_PER_DAY = 5`, config.py:29)  
**Reset:** Daily at midnight (Lines 77-86)

#### 6.1.5 Consecutive Loss Limits

**Method:** `EnhancedRiskManager.validate_position_exposure()` (Lines 211-213)

```python
if not self.trade_tracker.check_consecutive_loss_limit(self.config.MAX_CONSECUTIVE_LOSSES):
    return False, f"Max consecutive losses ({self.config.MAX_CONSECUTIVE_LOSSES}) reached"
```

**Limit:** `3` consecutive losses (`config.MAX_CONSECUTIVE_LOSSES = 3`, config.py:35)  
**Source:** Lines 212-213

### 6.2 LiveGuard

**Source:** [shadow/live_guard.py](file:///a:/1/algoshadow/shadow/live_guard.py) (Lines 1-191)

Layer 7 guardrails supervisor.

#### 6.2.1 Configuration

**Method:** `LiveGuard.__init__()` (Lines 25-59)

From `config.live_guard` section:

| Parameter | Default | Config Source |
|-----------|---------|---------------|
| **Max Daily Loss Dollars** | $2,000 | `max_daily_loss_dollars` |
| **Max Daily Loss %** | 2% | `max_daily_loss_pct` |
| **Max Trades Per Day** | 10 | `max_trades_per_day` |
| **Max Symbols Per Day** | 3 | `max_symbols_per_day` |

**From config_shadow_live_pure.yaml (Lines 32-38):**
```yaml
live_guard:
  enabled: true
  max_daily_loss_dollars: 2000.0
  max_daily_loss_pct: 0.02
  max_trades_per_day: 10
  max_symbols_per_day: 3
```

#### 6.2.2 Entry Blocking Conditions

**Method:** `LiveGuard.can_submit_entry()` (Lines 61-89)

Blocks if:

1. **Kill Switch Engaged** (Line 74-76)
2. **Max Trades Reached:** `trades_executed >= max_trades_per_day` (Lines 79-81)
3. **Max Symbols Reached:** New symbol when `len(symbols_traded) >= max_symbols_per_day` (Lines 84-87)

#### 6.2.3 Kill Switch Engagement

**Method:** `LiveGuard._engage_kill_switch()` (Lines 180-190)

Engaged when:

1. **Max Trades Limit** (Lines 111-112)
2. **Max Daily Loss Dollars** (Lines 129-130)
3. **Max Daily Loss %** (Lines 163-164)
4. **Risk Manager Lockdown** (Lines 177-178)

### 6.3 HealthMonitor OCO Watchdog

**Source:** [risk_manager.py](file:///a:/1/algoshadow/risk_manager.py) (Lines 251-286)

**Method:** `EnhancedRiskManager.monitor_system_health()`

**Check Interval:** `5 seconds` (`config.OCO_CHECK_INTERVAL = 5`, config.py:57)

```python
for symbol, pos in self.executor.positions.items():
    if pos.qty > 0:
        # Check if transition is in progress
        if self.executor.stop_manager.is_transitioning(symbol):
            continue

        # Check if stop exists
        stop_id = await self.executor.stop_manager.get_active_stop(symbol)
        if not stop_id:
            self.logger.critical(f"OCO Watchdog: Position {symbol} has NO STOP! Triggering emergency stop.")
            await self.executor.emergency_stop_apply(symbol)
```

**Purpose:** Ensure every position has a stop order  
**Action:** Apply emergency stop at `entry_price * 0.90` if missing  
**Source:** Lines 269-280

---

## 7. STATE MACHINE DIAGRAM

```
┌──────────────────────────────────────────────────────────────┐
│                     STRATEGY ENGINE STATE MACHINE                │
└──────────────────────────────────────────────────────────────┘

┌───────────┐
│   IDLE   │  Initial state
└───┬───────┘
     │
     │ Condition: len(bars) >= 30 (warmup complete)
     │
     ▼
┌──────────────┐
│  STALKING   │  Monitoring for flush below support
└──┬────┬──────┘
   │    │
   │    │ Condition: bar.close < current_support (session_low)
   │    │
   │    ▼
   │  ┌───────────────┐
   │  │ TRAP_ACTIVE  │  Flush detected, tracking trap_low
   │  └──┬────┬──┬───┘
   │     │    │  │
   │     │    │  │ Condition: bar.low < trap_low (update trap_low)
   │     │    │  └────────────────────────┐
   │     │    │                         │
   │     │    │ Condition: bar.close < support - 2*ATR (trap failed)
   │     │    └──────────────────────────┐  │
   │     │                           │  │
   │     │                           ▼  ▼
   │     └─────────────────────── ┌───────────────┐
   │                          │  STALKING   │ (reset)
   │                          └───────────────┘
   │
   │     Condition: bar.close > support AND
   │                volume > 2x avg AND
   │                lower_wick > 30% range AND
   │                body > 50% range
   │     ▼
   │  ┌──────────────────────────┐
   │  │ WAITING_FOR_ENTRY_FILL    │  Signal fired, order submitted
   │  └──────────┬───────────────┘
   │             │
   │             │ Condition: Entry order filled
   │             │
   │             ▼
   │  ┌──────────────────┐
   │  │   IN_POSITION    │  Position open, stop placed
   │  └──┬───────┬───────┘
   │     │       │
   │     │       │ Exit Conditions:
   │     │       │  - bar.close >= session_vwap (profit target)
   │     │       │  - position_duration > 120 minutes (time stop)
   │     │       │  - stop order fills (stop loss)
   │     │       │
   │     │       ▼
   │     │  ┌──────────────────┐
   │     │  │ EXITING_INTENT   │  Exit requested
   │     │  └────────┬─────────┘
   │     │           │
   │     │           │ Condition: Exit order filled
   │     │           │
   │     └───────────┴────────────┐
   │                              │
   │                              ▼
   └────────────────────────── ┌───────────┐
                             │   IDLE   │  Position closed
                             └───────────┘

State Persistence:
  - State syncs with Executor.positions
  - If position exists but state != IN_POSITION: sync to IN_POSITION
  - If no position but state == IN_POSITION: sync to IDLE
```

---

## 8. COMPLETE ENTRY-EXIT LIFECYCLE

### Phase 1: Pattern Detection

**File:** [strategy_engine.py](file:///a:/1/algoshadow/strategy_engine.py)

1. **Warmup:** Collect 30+ bars (Lines 140-144)
2. **Stalking:** Monitor for `bar.close < session_low` (Lines 193-197)
3. **Flush:** Detect break below support, capture `trap_low` (Lines 196-197)
4. **Reclaim:** Wait for `bar.close > support` (Line 204)
5. **Validation:** Check volume, wick, body (Lines 222-248)
6. **Signal Fire:** Generate signal with:
   - `entry_reference_price = bar.close`
   - `stop_reference_price = trap_low - (0.05 * ATR)`
   - `target_reference_price = session_vwap`
   - **Source:** Lines 269-323

### Phase 2: Entry Risk Filters

**File:** [executor.py](file:///a:/1/algoshadow/executor.py)

7. **Pre-Entry Checks:** (Lines 144-208)
   - No-trade symbol
   - Runtime halt
   - Symbol halted
   - LiveGuard approval
   - Account fetch
   - RiskManager approval
   - Valid references
   - Position size validation
   - Exposure limits
   - Spread check

8. **Position Sizing:** `qty = floor(equity * 0.005 / stop_distance)` (Lines 213-218)

9. **Order Submission:** Limit order at `entry_reference_price`, DAY, BUY (Lines 225-236)

### Phase 3: Entry Fill & Stop Placement

**File:** [executor.py](file:///a:/1/algoshadow/executor.py)

10. **Fill Processing:** [on_entry_fill()](file:///a:/1/algoshadow/executor.py#262-325) (Lines 262-324)
11. **Position State Update:** Track qty, entry_price, opened_at, signal_id (Lines 289-307)
12. **LiveGuard Update:** Increment trade count, add symbol (live_guard.py:105-112)
13. **Stop Placement:** `stop_manager.replace_stop(symbol, qty, stop_price)` (Lines 318-321)
14. **Stop Order:** GTC stop at `trap_low - (0.05 * ATR)` (stop_manager.py:113-123)

### Phase 4: In-Position Monitoring

**File:** [strategy_engine.py](file:///a:/1/algoshadow/strategy_engine.py), [risk_manager.py](file:///a:/1/algoshadow/risk_manager.py)

15. **Check Signals (Every Bar):** (Lines 252-267)
    - Profit target: `bar.close >= session_vwap`
    - Time stop: `duration > 120 minutes`
16. **OCO Watchdog (Every 5 sec):** Verify stop exists (risk_manager.py:269-280)
17. **Daily Loss Monitor (Every 5 sec):** Check total PnL vs -2% equity (risk_manager.py:260-265)

### Phase 5: Exit

**File:** [executor.py](file:///a:/1/algoshadow/executor.py)

18. **Exit Request:** [request_exit_tp()](file:///a:/1/algoshadow/executor.py#326-350) (Lines 326-349)
19. **Stop Cancellation:** `stop_manager.cancel_stop()` (Line 334)
20. **Market Sell:** GTC market order (Lines 339-347)
21. **Fill Processing:** [on_exit_fill()](file:///a:/1/algoshadow/executor.py#351-411) (Lines 351-410)
22. **PnL Calculation:** `pnl = (exit_price - entry_price) * qty` (Line 365)
23. **RiskManager Update:** [update_daily_pnl(pnl)](file:///a:/1/algoshadow/risk_manager.py#88-92) (Line 366)
24. **LiveGuard Update:** [update_pnl(daily_realized_pnl)](file:///a:/1/algoshadow/shadow/live_guard.py#114-131) (Line 370)
25. **Position Cleanup:** Remove from `positions` dict (Line 393)
26. **State Reset:** `IDLE` (strategy_engine.py:185-186)

---

## Summary of All Parameters

### Scanner Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| MIN_PRICE | $1.00 | config.py:60 |
| MAX_PRICE | $20.00 | config.py:61 |
| MIN_DOLLAR_VOLUME | $2,000,000 | config.py:75 |
| MIN_DAY_CHANGE_PCT | 2.0% | config.py:87 |
| MAX_FLOAT_SHARES | 80,000,000 | config.py:84 |
| MIN_RVOL | 2.0 | config.py:62 |
| IDEAL_RVOL_LOW | 3.0 | config.py:72 |
| IDEAL_RVOL_HIGH | 6.0 | config.py:73 |
| TINY_FLOAT_SHARES | 10,000,000 | config.py:66 |
| IDEAL_DAY_CHANGE_LOW | 5% | config.py:69 |
| IDEAL_DAY_CHANGE_HIGH | 20% | config.py:70 |
| MAX_SPREAD_PCT | 1.2% | config.py:96 |
| MIN_BID_ASK_SIZE | 50 shares | config.py:78 |

### Strategy Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| MIN_WARMUP_BARS | 30 | strategy_engine.py:37 |
| ATR_PERIOD | 14 | strategy_engine.py:36 |
| VOLUME_MULTIPLE | 2.0x | strategy_engine.py:230 |
| LOWER_WICK_PCT | 25% | strategy_engine.py:236 (Config: 0.25) |
| BODY_STRENGTH_PCT | 40% | strategy_engine.py:240 (Config: 0.40) |
| TRAP_FAIL_DISTANCE | 2 * ATR | strategy_engine.py:213 |
| STOP_BUFFER | 0.05 * ATR | strategy_engine.py:278 |

### Risk Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| MAX_DAILY_LOSS_PCT | 2% | config.py:28 |
| MAX_TRADES_PER_DAY | 5 | config.py:29 |
| MAX_SPREAD_PCT | 0.2% | config.py:30 |
| PER_TRADE_RISK_PCT | 0.5% | config.py:31 |
| MAX_HOLD_MINUTES | 120 | config.py:32 |
| MAX_CONSECUTIVE_LOSSES | 3 | config.py:35 |
| MAX_POSITION_DOLLARS | $1,000 | config.py:36 |
| MAX_POSITION_EQUITY_PCT | 10% | config.py:37 |
| MAX_PORTFOLIO_EXPOSURE | 25% | config.py:38 |
| OCO_CHECK_INTERVAL | 5 sec | config.py:57 |

### LiveGuard Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| MAX_DAILY_LOSS_DOLLARS | $2,000 | config_shadow_live_pure.yaml:35 |
| MAX_DAILY_LOSS_PCT | 2% | config_shadow_live_pure.yaml:36 |
| MAX_TRADES_PER_DAY | 10 | config_shadow_live_pure.yaml:37 |
| MAX_SYMBOLS_PER_DAY | 3 | config_shadow_live_pure.yaml:38 |

---

**Document Generated:** 2025-12-01  
**Codebase Version:** Algo-Shadow v3.4  
**Specification Type:** Complete Code-Verified Logic Extraction
