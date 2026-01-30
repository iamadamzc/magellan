# MIDAS Protocol - Complete Strategy Specification

**Version**: 1.0 Baseline  
**Created**: January 30, 2026  
**Strategy Type**: Futures Mean Reversion  
**Instrument**: Micro Nasdaq-100 Futures (MNQ)  
**Trading Session**: Asian Session (02:00-06:00 UTC)

---

## Executive Summary

The MIDAS Protocol is a quantitative mean reversion strategy designed to exploit short-term price dislocations in the Micro Nasdaq-100 futures contract during the Asian trading session. The strategy employs two complementary entry setups backed by volatility and momentum filters, combined with a disciplined OCO bracket exit system that targets a 6:1 risk/reward ratio.

**Key Metrics**:
- Risk per trade: $40 (20 points)
- Reward per trade: $240 (120 points)
- Risk/Reward: 6.0
- Max daily loss: $300
- Position limit: 1 contract
- Expected trades per month: 30

---

## Market & Instrument

### Micro Nasdaq-100 Futures (MNQ)

**Contract Specifications**:
- **Symbol**: MNQ
- **Exchange**: CME Group
- **Contract Size**: $2 per index point (micro contract)
- **Tick Size**: 0.25 points = $0.50
- **Trading Hours**: Nearly 24/5 (Sunday 6pm - Friday 5pm ET)
- **Margin** (typical): ~$1,500 per contract
- **Liquidity**: High during US hours, moderate during Asian session

### Why Asian Session (02:00-06:00 UTC)?

The Asian session window provides specific advantages:
1. **Lower Liquidity**: Creates temporary price dislocations
2. **Mean Reversion Tendency**: Less directional momentum, more oscillation
3. **Reduced News Impact**: Fewer US macro events during these hours
4. **Defined Session**: Clear start/end for risk management
5. **Complementary to US Strategies**: Utilizes otherwise idle trading capital

**UTC to Major Timezones**:
- 02:00-06:00 UTC = 9am-1pm Hong Kong Time
- 02:00-06:00 UTC = 11am-3pm Sydney Time  
- 02:00-06:00 UTC = 9pm-1am EST (previous day)

---

## Technical Indicators

### 1. EMA 200 (Exponential Moving Average)

**Purpose**: Primary trend anchor and mean reversion reference  
**Calculation**: 200-period EMA of close prices  
**Usage**: Measure distance from long-term equilibrium

```python
EMA = Close.ewm(span=200, adjust=False).mean()
EMA_Distance = abs(Close - EMA)
```

**Interpretation**:
- Price near EMA (<220 pts): Favorable for mean reversion
- Price far from EMA (>220 pts): Avoid entry (extended move)

### 2. Velocity (5-Bar Momentum)

**Purpose**: Detect rapid price moves (crashes or quiet drift)  
**Calculation**: Current close minus close 5 bars ago  
**Formula**: `Velocity = Close[0] - Close[5]`

**Categories**:
- **< -150**: Extreme crash (GLITCH GUARD - no trade)
- **-150 to -67**: Moderate crash (Setup A trigger range)
- **-67 to 10**: Neutral to quiet (Setup B if ≤10)
- **>10**: Upward momentum (no mean reversion setup)

### 3. ATR Ratio (Volatility Filter)

**Purpose**: Gauge current volatility relative to recent average  
**Components**:
- **ATR(14)**: 14-period Average True Range
- **ATR_Avg(50)**: 50-period SMA of ATR(14)
- **ATR Ratio**: ATR(14) / ATR_Avg(50)

```python
# True Range
TR = max(High - Low, |High - PrevClose|, |Low - PrevClose|)

# ATR (14-period EMA of True Range)
ATR_14 = TR.ewm(span=14, adjust=False).mean()

# ATR Average (50-period SMA)
ATR_Avg_50 = ATR_14.rolling(window=50).mean()

# ATR Ratio
ATR_Ratio = ATR_14 / ATR_Avg_50
```

**Interpretation**:
- **> 0.50**: High volatility (Setup A - crash reversal)
- **0.06 - 0.50**: Normal/low volatility (Setup B - quiet drift)
- **< 0.06**: Extremely low volatility (no trade)

---

## Entry Logic

### Global Filter: Glitch Guard

**Rule**: IF Velocity < -150, **DO NOT TRADE**

**Purpose**: Protect against:
- Data feed errors
- Flash crash events
- Order book glitches
- Extreme outlier moves

**Example**:
```
Velocity = -200 → BLOCKED (potential data issue)
Velocity = -120 → ALLOWED (within normal crash range)
```

### Setup A: "The Crash Reversal"

**Trigger Conditions** (ALL must be true):
1. Velocity: -150 to -67 (moderate crash)
2. EMA Distance: ≤ 220 points (not too extended)
3. ATR Ratio: > 0.50 (high volatility)

**Logic**:
```python
if (-150 <= velocity <= -67 and
    abs(close - ema_200) <= 220 and
    atr_ratio > 0.50):
    ENTER LONG
```

**Rationale**:
- Price has dropped sharply (Velocity -67 to -150)
- But not too far from equilibrium (EMA Distance ≤220)
- In elevated volatility environment (ATR Ratio >0.50)
- Captures "V-shaped" bounces after selling exhaustion

**Example Trade**:
```
Close: 14,950
EMA 200: 15,100
Velocity: -95 (between -150 and -67) ✓
EMA Distance: 150 (< 220) ✓
ATR Ratio: 0.65 (> 0.50) ✓
→ Setup A TRIGGERED → BUY MARKET
```

### Setup B: "The Quiet Drift"

**Trigger Conditions** (ALL must be true):
1. Velocity: ≤ 10 (minimal momentum)
2. EMA Distance: ≤ 220 points (near equilibrium)
3. ATR Ratio: 0.06 to 0.50 (normal/low volatility)

**Logic**:
```python
if (velocity <= 10 and
    abs(close - ema_200) <= 220 and
    0.06 <= atr_ratio <= 0.50):
    ENTER LONG
```

**Rationale**:
- Price is stable/drifting (Velocity ≤10)
- Near long-term mean (EMA Distance ≤220)
- Normal volatility regime (ATR Ratio 0.06-0.50)
- Captures subtle oversold conditions in quiet markets

**Example Trade**:
```
Close: 15,080
EMA 200: 15,100
Velocity: 5 (≤ 10) ✓
EMA Distance: 20 (< 220) ✓
ATR Ratio: 0.30 (between 0.06 and 0.50) ✓
→ Setup B TRIGGERED → BUY MARKET
```

---

## Exit Logic

### OCO Bracket (One-Cancels-Other)

**Overview**: Every entry immediately places 3 exit orders:
1. Stop Loss (20 points)
2. Take Profit (120 points)
3. Time-Based Exit (60 bars)

Whichever triggers first closes the position and cancels the others.

### 1. Stop Loss (Fixed 20 Points)

**Calculation**: Entry Price - 20 points  
**Dollar Risk**: 20 points × $2/point = **$40**

**Example**:
```
Entry: 14,950
Stop Loss: 14,930 (14,950 - 20)
If price touches 14,930 → EXIT LONG → Loss = -$40
```

**Rationale**: Fixed risk per trade enables precise bankroll management

### 2. Take Profit (Fixed 120 Points)

**Calculation**: Entry Price + 120 points  
**Dollar Profit**: 120 points × $2/point = **$240**

**Example**:
```
Entry: 14,950
Take Profit: 15,070 (14,950 + 120)
If price touches 15,070 → EXIT LONG → Profit = +$240
```

**Rationale**: 6:1 R/R allows strategy to be profitable even with <20% win rate

### 3. Time-Based Exit (60 Bars = 60 Minutes)

**Trigger**: If position open for 60 consecutive 1-minute bars  
**Action**: Close at market price

**Purpose**:
- Prevent capital from being tied up indefinitely
- Reduce overnight risk (session ends at 06:00 UTC)
- Exit when mean reversion thesis hasn't materialized

**Example**:
```
Entry Time: 03:15 UTC
60 Bars Later: 04:15 UTC
Current Price: 14,980 (+30 points)
→ EXIT LONG → Profit = +$60
```

---

## Risk Management

### Daily Loss Limit

**Max Daily Loss**: $300

**Rule**: If cumulative P&L reaches -$300, **HALT ALL TRADING**

**Logic**:
```python
if daily_pnl <= -300:
    halt_trading = True  # No new entries
    close_all_positions()  # Exit any open position
```

**Reset**: Daily P&L resets at 02:00 UTC (session start)

**Rationale**:
- 7.5 consecutive max losses = -$300 ($40 × 7.5)
- Prevents catastrophic drawdowns
- Forces re-evaluation after losing streak

### Position Limits

**Max Concurrent Positions**: 1 contract  
**No Pyramiding**: Cannot add to winning positions  
**No Averaging**: Cannot add to losing positions

**Rationale**: Simplicity and risk control

### Direction

**Long Only**: No short positions

**Rationale**:
- Mean reversion setup designed for upside bounces
- Simplifies logic and avoids short-squeeze risk
- Aligns with long-term Nasdaq upward bias

---

## Session Management

### Trading Hours (Strict)

**ACTIVE**: 02:00:00 - 06:00:00 UTC  
**FLAT**: All other times

**Enforcement**:
```python
if not (02:00 <= current_time_utc <= 06:00):
    # Close any open positions
    # Do not evaluate new entries
    # Sleep until next session
```

**Session Start (02:00 UTC)**:
- Reset daily P&L to $0
- Reset trades counter to 0
- Clear session halt flag
- Begin monitoring for entries

**Session End (06:00 UTC)**:
- Close all open positions at market
- Generate end-of-session report
- Enter sleep mode until next session

**Weekends**:
- No trading Saturday or Sunday (UTC)

---

## Trade Execution Flow

### 1. Pre-Trade Checks (Every 15 seconds during session)

```
✓ Is current time 02:00-06:00 UTC?
✓ Is it a weekday?
✓ Has daily loss limit been hit?
✓ Is max position limit (1) reached?
✓ Are all indicators valid (no NaN)?
```

### 2. Entry Evaluation

```
Fetch latest 1-minute bars
Calculate indicators (EMA 200, Velocity, ATR Ratio)

Check Glitch Guard:
  IF Velocity < -150 → BLOCK

Evaluate Setup A:
  IF Velocity in [-150, -67] AND
     EMA Distance <= 220 AND
     ATR Ratio > 0.50
  → TRIGGER Setup A

Evaluate Setup B:
  IF Velocity <= 10 AND
     EMA Distance <= 220 AND
     ATR Ratio in [0.06, 0.50]
  → TRIGGER Setup B
```

### 3. Entry Execution

```
Submit MARKET BUY order for 1 MNQ contract

Calculate and log:
  Entry Price
  Stop Loss = Entry - 20
  Take Profit = Entry + 120
  Time Exit = 60 bars from now

Track position in memory
Log trade to CSV
```

### 4. Position Management (Every 15 seconds while in position)

```
Fetch current price

Check Stop Loss:
  IF Price <= Stop Loss → EXIT (Loss = -$40)

Check Take Profit:
  IF Price >= Take Profit → EXIT (Profit = +$240)

Check Time Exit:
  IF Bars Held >= 60 → EXIT (Profit/Loss = variable)

Update P&L
Check daily loss limit
```

### 5. Exit Execution

```
Submit MARKET SELL order for 1 MNQ contract

Calculate final P&L:
  Points = Exit Price - Entry Price
  Dollars = Points × $2

Update daily P&L
Remove position from tracking
Log trade result to CSV

IF daily P&L <= -$300:
  Halt trading for remainder of session
```

---

## Backtesting & Optimization

### Grid Search Results

The MIDAS Protocol parameters were optimized via systematic grid search on 2025 out-of-sample MNQ data.

**Optimized Parameters ("Champion" Settings)**:
- Stop Loss: 20 points
- Take Profit: 120 points
- Time Exit: 60 bars

**Tested Ranges**:
- Stop Loss: 10, 15, 20, 30, 40, 50 points
- Take Profit: 60, 80, 100, 120, 150, 200 points
- Time Exit: 30, 45, 60, 90, 120 bars

**Selection Criteria**: Maximum Net Profit with acceptable win rate (>20%)

See optimization conversation (cd20adc8-af4d-49f9-8cb6-8dc80e69f5e2) for full results.

---

## Logging & Monitoring

### Log Levels

**INFO**: Strategy lifecycle events
- Session start/end
- Indicator calculations
- Entry/exit signals
- Daily P&L updates

**WARNING**: Risk events
- Glitch Guard triggered
- Daily loss limit approaching
- Session halt activated

**ERROR**: System issues
- API connection failures
- Data fetch errors
- Order execution failures

### Trade Logs

**CSV Format**:
```
timestamp,setup,entry_price,exit_price,pnl_points,pnl_dollars,bars_held,exit_reason
2026-01-30 03:45:00,setup_a,14950.00,15070.00,120.00,240.00,35,Take Profit Hit
```

**File Location**: `/home/ssm-user/magellan/logs/midas_protocol_trades_YYYYMMDD.csv`

---

## Dependencies

### Python Libraries

```
alpaca-py      # Alpaca API client
pandas         # Data manipulation
numpy          # Numerical operations
pytz           # Timezone handling
boto3          # AWS SSM integration
python-dotenv  # Environment variables
```

### External Services

- **Alpaca Markets**: Live/paper trading API
- **AWS SSM**: Secure credential storage
- **AWS EC2**: Hosting environment
- **GitHub Actions**: CI/CD pipeline

---

## Known Limitations

1. **Futures Not Supported by Alpaca**: 
   - Current implementation uses stock data API
   - Production requires futures-capable broker (e.g., Interactive Brokers)
   - OR use MNQ spot proxy via FMP API

2. **Asian Session Liquidity**:
   - Lower volume may cause wider spreads
   - Slippage could impact actual R/R ratio
   - Recommend testing with paper trading first

3. **Data Quality**:
   - Glitch Guard protects against most issues
   - Still monitor for data feed stability during Asian hours

4. **Single Symbol**:
   - Strategy only trades MNQ
   - No diversification across futures contracts

---

## Future Enhancements

### Potential Improvements
1. **Multi-Symbol**: Expand to ES, NQ, RTY futures
2. **Dynamic Sizing**: Scale position based on volatility
3. **ML Filter**: Add regime classification for entry filtering
4. **Adaptive Exits**: Adjust TP/SL based on realized volatility
5. **Portfolio**: Combine with other session-based strategies (EU/US)

---

## Appendix: Code Snippets

### Indicator Calculation Example

```python
# EMA 200
df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()

# Velocity
df['velocity'] = df['close'] - df['close'].shift(5)

# ATR(14)
high_low = df['high'] - df['low']
high_close = (df['high'] - df['close'].shift(1)).abs()
low_close = (df['low'] - df['close'].shift(1)).abs()
true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
df['atr_14'] = true_range.ewm(span=14, adjust=False).mean()

# ATR_Avg(50)
df['atr_avg_50'] = df['atr_14'].rolling(window=50).mean()

# ATR Ratio
df['atr_ratio'] = df['atr_14'] / df['atr_avg_50']
```

---

**Document Version**: 1.0  
**Last Updated**: January 30, 2026  
**Author**: Magellan Development Team  
**Review Cycle**: Monthly or after significant market regime changes
