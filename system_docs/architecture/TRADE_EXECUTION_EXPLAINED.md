# How Trade Execution Works - Complete Flow Diagram

**Created:** 2026-01-18  
**Purpose:** Explain how strategies know when to enter/exit trades  
**Focus:** Hourly Swing Strategy as example

---

## 🎯 **The Big Picture: Two Modes**

Your system has **TWO separate execution paths**:

1. **Backtesting** (Simulation) - Test strategies on historical data
2. **Live Trading** - Execute real trades via Alpaca API

---

## 📊 **MODE 1: BACKTESTING (How Hourly Swing Works in Simulation)**

### **Step-by-Step Flow:**

```
1. FETCH DATA
   ↓
   cache.get_or_fetch_equity('TSLA', '1hour', '2024-10-01', '2024-12-31')
   ↓
   Returns: DataFrame with OHLCV data (open, high, low, close, volume)

2. CALCULATE INDICATOR  
   ↓
   df['rsi'] = calculate_rsi(df['close'], period=14)
   ↓
   Each row now has: [timestamp, open, high, low, close, volume, rsi]

3. GENERATE SIGNALS (RSI Hysteresis Logic)
   ↓
   position = 0  # Start flat
   for each bar:
       if position == 0:  # Currently flat
           if RSI > 60:    # Upper band
               position = 1  # GO LONG
       
       elif position == 1:  # Currently long
           if RSI < 40:    # Lower band
               position = 0  # EXIT (go flat)
       
       signal = position
   ↓
   df['signal'] = [0, 0, 0, 1, 1, 1, 0, 0, ...]  # Signal for each bar

4. CALCULATE RETURNS
   ↓
   df['returns'] = df['close'].pct_change()  # Price change each bar
   df['strategy_returns'] = df['signal'].shift(1) * df['returns']
   ↓
   shift(1) = Can't act on current bar, use previous signal

5. SIMULATE TRADES (Automatic Position Changes)
   ↓
   When signal changes from 0 → 1: BUY
   When signal changes from 1 → 0: SELL
   ↓
   Count trades = signal.diff() != 0
   Apply friction (transaction costs)
   
6. CALCULATE PERFORMANCE
   ↓
   Total return = (1 + strategy_returns).prod() - 1 - friction
   Number of trades = signal changes
   ↓
   Result: +10.86% for TSLA in December!
```

### **Key Code (from `simulate_all_strategies_december.py`):**

```python
# Lines 132-167: Hourly Swing Backtesting Logic
def run_hourly_swing(symbol, config, lookback_start, test_start, test_end):
    # 1. Fetch data
    df = cache.get_or_fetch_equity(symbol, '1hour', lookback_start, test_end)
    
    # 2. Calculate RSI
    df['rsi'] = calculate_rsi(df['close'], period=config['rsi_period'])
    
    # 3. Generate signals (Hysteresis logic)
    position = 0
    signals = []
    
    for i in range(len(df)):
        rsi_val = df['rsi'].iloc[i]
        
        if position == 0:              # Flat
            if rsi_val > config['upper_band']:  # RSI > 60
                position = 1            # Go long
        elif position == 1:            # Long
            if rsi_val < config['lower_band']:  # RSI < 40
                position = 0            # Go flat
        
        signals.append(position)
    
    # 4. Calculate returns
    df['signal'] = signals
    df['returns'] = df['close'].pct_change()
    df['strategy_returns'] = df['signal'].shift(1) * df['returns']
    
    # 5. Count trades and apply friction
    trades = (df['signal'].diff() != 0).sum()
    friction = trades * 0.0005  # 5 bps per trade
    
    # 6. Total return
    total_return = (1 + df['strategy_returns']).prod() - 1 - friction
    
    return {'return_pct': total_return * 100, 'trades': trades}
```

---

## 🚀 **MODE 2: LIVE TRADING (Real Executing via Alpaca)**

### **Step-by-Step Flow:**

```
1. FETCH REAL-TIME DATA (every minute)
   ↓
   alpaca_client.fetch_historical_bars('TSLA', '1hour', yesterday, today)
   ↓
   Gets latest hourly bars including current forming bar

2. CALCULATE INDICATOR
   ↓
   df['rsi'] = calculate_rsi(df['close'], period=14)
   ↓
   RSI value for most recent complete bar

3. GENERATE SIGNAL (same logic as backtest)
   ↓
   if position == 0 and RSI > 60:
       signal = 1  # BUY
   elif position == 1 and RSI < 40:
       signal = 0  # SELL
   ↓
   Current signal: BUY (1), SELL (-1), or HOLD (0)

4. CHECK CURRENT POSITION
   ↓
   trading_client.get_account_info()
   ↓
   Do we already own TSLA? Yes/No

5. EXECUTE TRADE (if signal changed)
   ↓
   If signal says BUY and we don't own it:
       ├─ Calculate position size: $10,000 / current_price
       ├─ Check buying power: Do we have $10,000?
       ├─ Submit order: BUY 47 shares @ $212.50 limit
       └─ Wait for fill confirmation
   
   If signal says SELL and we own it:
       ├─ Get current position: 47 shares
       ├─ Submit order: SELL 47 shares @ $212.45 limit
       └─ Close position

6. LOG TRADE
   ↓
   Writes to live_trades.log:
   "2024-12-15 10:30 | BUY TSLA | 47 shares @ $212.50 | Order #xyz123"
   ↓
   Also prints to terminal:
   "✓ TSLA BUY executed | +47 shares @ $212.50"
```

### **Key Code (from `main.py` + `executor.py`):**

```python
# main.py lines 246-263: Signal Generation (LIVE)
if position == 0:
    if rsi_val > config['upper_band']:
        signal = 1  # BUY
elif position == 1:
    if rsi_val < config['lower_band']:
        signal = 0  # SELL/EXIT

latest_signal = signal

# main.py lines 266-273: Execute Trade
trade_result = await async_execute_trade(
    trading_client,    # Alpaca client
    latest_signal,     # 1 = BUY, 0 = SELL
    'TSLA',
    allocation_pct=0.25  # 25% of equity
)

# executor.py executes the actual Alpaca API call:
# - Checks PDT protection
# - Calculates shares to buy/sell
# - Submits "Marketable Limit" order (ask + $0.01)
# - Logs to live_trades.log
```

---

## 🔑 **Key Differences: Backtest vs Live**

| Aspect | Backtesting | Live Trading |
|--------|-------------|--------------|
| **Data** | Historical (cache) | Real-time (Alpaca API) |
| **Signals** | Generated for entire period | Generated every minute |
| **Execution** | Simulated (math on returns) | Real (Alpaca API orders) |
| **Timing** | All at once (batch) | Continuous loop |
| **Risk** | Zero (paper money) | Real (paper trading account) |
| **Speed** | Fast (processes months in seconds) | Slow (waits between bars) |
| **Output** | Performance metrics | Actual positions + P&L |

---

## 📍 **Entry/Exit Decision Logic (RSI Hysteresis)**

```python
# This is THE core logic that decides when to trade:

position = 0  # 0 = flat, 1 = long

# ENTRY LOGIC
if position == 0:              # Not in position
    if RSI > upper_band:       # RSI crosses above 60
        position = 1           # ✅ ENTER LONG
        # Backtest: Record signal=1
        # Live: Execute BUY order

# EXIT LOGIC  
elif position == 1:            # Currently long
    if RSI < lower_band:       # RSI crosses below 40
        position = 0           # ✅ EXIT POSITION
        # Backtest: Record signal=0
        # Live: Execute SELL order

# The "hysteresis" part:
# - Must cross ABOVE 60 to enter
# - Must cross BELOW 40 to exit
# - Prevents whipsaw between 40-60 (HOLD zone)
```

### **Visual Example:**

```
Time    Close   RSI    Signal  Action
──────────────────────────────────────
10:00   $210    45     0       HOLD (in dead zone)
11:00   $215    61     1       🟢 BUY! (RSI > 60)
12:00   $217    58     1       HOLD (still long)
13:00   $216    52     1       HOLD (still long)
14:00   $213    38     0       🔴 SELL! (RSI < 40)
15:00   $214    42     0       HOLD (flat, in dead zone)
```

---

## 🔄 **Where Does Each File Fit?**

### **Backtesting:**
1. `data_cache.py` - Fetches historical data
2. **Your script** - Calculates RSI, generates signals
3. **Your script** - Simulates returns from signals
4. `logger.py` - Prints results

### **Live Trading:**
1. `main.py` - Main loop (runs every minute)
2. `data_handler.py` - Fetches real-time data from Alpaca
3. `main.py` - Calculates RSI, generates signal
4. `executor.py` - Executes BUY/SELL via Alpaca API
5. `monitor.py` - Tracks positions
6. `logger.py` - Logs everything

---

## 📝 **Simple Example: TSLA Hourly Swing**

### **Configuration:**
```json
{
  "symbol": "TSLA",
  "rsi_period": 14,
  "upper_band": 60,
  "lower_band": 40,
  "timeframe": "1hour"
}
```

### **Backtest (December 2024):**
```
1. Fetch TSLA 1-hour data: Oct 1 - Dec 31
2. Calculate RSI-14 for each hour
3. Generate signals:
   - RSI > 60 → signal = 1 (long)
   - RSI < 40 → signal = 0 (flat)
4. Count signal changes: 20 trades
5. Calculate returns: +10.86%
6. Print: "TSLA +10.86% | 20 trades"
```

### **Live Trading (Real-time):**
```
Every minute:
1. Fetch latest TSLA 1-hour bars
2. Calculate RSI-14 for most recent hour
3. Check RSI value:
   - If RSI just crossed 60 and we're flat → BUY
   - If RSI just crossed 40 and we're long → SELL
4. If signal changed:
   - Call executor.execute_trade()
   - Submit order to Alpaca
   - Log trade
5. Wait 60 seconds, repeat
```

---

## 💡 **Key Insights:**

1. **The strategy IS the signal generation logic**
   - Hourly Swing strategy = RSI Hysteresis (60/40 bands)
   - Bear Trap = Session low reclaim with volume
   - GSB = Opening range breakout + VWAP

2. **Execution is separate from strategy**
   - Backtest: Math on returns (fast, safe)
   - Live: API calls to Alpaca (slow, real)

3. **Same logic, different execution**
   - The `if RSI > 60 then BUY` logic is **identical**
   - Only difference is HOW the buy happens:
     - Backtest: `signal = 1` (simulation)
     - Live: `alpaca.submit_order()` (real trade)

4. **Trading is EVENT-DRIVEN**
   - Strategy watches for conditions (RSI > 60)
   - When condition met → trigger action (BUY)
   - Not random - purely rule-based

5. **Hysteresis prevents overtrading**
   - Need RSI > 60 to enter
   - Need RSI < 40 to exit
   - Dead zone (40-60) = HOLD position
   - Prevents buying at 51, selling at 49, buying at 51...

---

## 🎓 **Complete Trade Example:**

```
Date: December 10, 2024
Symbol: TSLA
Strategy: Hourly Swing
Mode: Backtest

Hour    Close   RSI-14  Signal  Position    Action
────────────────────────────────────────────────────
09:00   $208    52      0       Flat        HOLD
10:00   $212    61      1       ENTER       🟢 BUY @ $212
11:00   $215    64      1       Long        HOLD
12:00   $218    67      1       Long        HOLD
13:00   $217    62      1       Long        HOLD
14:00   $214    58      1       Long        HOLD (hysteresis!)
15:00   $210    38      0       EXIT        🔴 SELL @ $210
16:00   $211    42      0       Flat        HOLD

Trade Summary:
- Entry: $212 @ 10:00
- Exit: $210 @ 15:00
- Result: -$2 loss (-0.94%)
- Hold time: 5 hours
```

---

## 🚀 **You Can Test This Yourself!**

### **Run a simple backtest:**
```powershell
cd a:\1\Magellan
python simulate_all_strategies_december.py
```

This will:
1. Fetch TSLA hourly data
2. Calculate RSI-14
3. Generate signals with 60/40 bands
4. Count trades automatically
5. Show you the P&L

You'll see **exactly** when it bought and sold based on RSI!

---

**Last Updated:** 2026-01-18  
**Status:** Complete trade execution explanation
