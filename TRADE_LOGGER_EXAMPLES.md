# Trade Logger Integration Examples

## How to Use the Trade Logger in Your Strategies

### Example 1: Bear Trap Strategy Integration

```python
from src.trade_logger import TradeLogger

# Initialize logger
logger = TradeLogger(strategy_name="bear_trap")

# When evaluating entry
logger.log_signal(
    symbol="MULN",
    signal_type="BUY",
    signal_strength=0.85,
    indicator_values={
        'rsi': 45.2,
        'price': 2.15,
        'session_low': 2.05,
        'reclaim_wick_ratio': 0.18,
        'volume_ratio': 1.35
    },
    entry_criteria_met=True,
    risk_gates_passed=True,
    action_taken="EXECUTED",
    skip_reason=""
)

# When entering position
logger.log_trade(
    symbol="MULN",
    action="ENTRY",
    side="BUY",
    quantity=1000,
    price=2.15,
    order_id="abc123",
    position_size_before=0,
    position_size_after=1000,
    entry_reason="Bear trap reclaim: RSI=45.2, broke session low then reclaimed with strong volume",
    market_conditions={
        'session_low': 2.05,
        'session_high': 2.45,
        'day_change_pct': -18.5,
        'time': '10:35:00'
    },
    indicators={
        'atr': 0.12,
        'volume_ratio': 1.35,
        'wick_ratio': 0.18
    },
    risk_metrics={
        'stop_loss': 2.00,
        'risk_per_share': 0.15,
        'position_dollars': 2150
    }
)

# When skipping due to risk gate
logger.log_risk_gate_failure(
    symbol="AMC",
    gate_name="MAX_DAILY_LOSS",
    gate_details={
        'current_loss': -9500,
        'max_allowed': -10000,
        'remaining_capacity': 500
    }
)

# When exiting position
logger.log_trade(
    symbol="MULN",
    action="EXIT",
    side="SELL",
    quantity=1000,
    price=2.35,
    order_id="def456",
    position_size_before=1000,
    position_size_after=0,
    exit_reason="Hit TP1 target at mid-range",
    pnl_dollars=200,
    pnl_percent=9.3,
    hold_time_minutes=25,
    market_conditions={
        'session_high': 2.45,
        'current_price': 2.35,
        'time': '11:00:00'
    }
)

# End of day summary
summary = logger.create_daily_summary()
print(f"Today's trades: {summary['total_trades']}, P&L: ${summary['total_pnl']:.2f}")
```

### Example 2: Daily Trend Strategy Integration

```python
from src.trade_logger import TradeLogger

logger = TradeLogger(strategy_name="daily_trend")

# Signal generation at 4:05 PM
for symbol in ['AAPL', 'GOOGL', 'META']:
    rsi = calculate_rsi(symbol)
    
    if rsi > 65:
        logger.log_signal(
            symbol=symbol,
            signal_type="BUY",
            signal_strength=(rsi - 65) / 35,  # Normalized strength
            indicator_values={'rsi': rsi, 'upper_band': 65, 'lower_band': 35},
            entry_criteria_met=True,
            risk_gates_passed=True,
            action_taken="PENDING",  # Will execute tomorrow at 9:30
            skip_reason=""
        )
    elif rsi < 35:
        logger.log_signal(
            symbol=symbol,
            signal_type="SELL",
            signal_strength=(35 - rsi) / 35,
            indicator_values={'rsi': rsi, 'upper_band': 65, 'lower_band': 35},
            exit_criteria_met=True,
            risk_gates_passed=True,
            action_taken="PENDING"
        )
    else:
        logger.log_decision(
            symbol=symbol,
            decision_type="HOLD",
            reason=f"RSI in neutral zone: {rsi:.2f}",
            details=f"Upper={65}, Lower={35}, Current={rsi:.2f}",
            current_price=get_price(symbol),
            indicator_values={'rsi': rsi}
        )
```

### Example 3: Hourly Swing Strategy Integration

```python
from src.trade_logger import TradeLogger

logger = TradeLogger(strategy_name="hourly_swing")

# Hourly check
def check_hourly_signals():
    for symbol in ['TSLA', 'NVDA']:
        data = fetch_hourly_data(symbol)
        rsi = calculate_rsi(data)
        
        # Log every scan
        logger.log_market_scan(
            symbol=symbol,
            scan_results={
                'price': data['close'][-1],
                'indicators': {
                    'rsi': rsi,
                    'upper_band': 60,
                    'lower_band': 40
                },
                'risk_status': {
                    'daily_loss': get_daily_loss(),
                    'open_positions': get_position_count()
                }
            }
        )
        
        # Evaluate entry
        if rsi > 60 and not has_position(symbol):
            if check_risk_gates():
                logger.log_signal(
                    symbol=symbol,
                    signal_type="BUY",
                    signal_strength=(rsi - 60) / 40,
                    indicator_values={'rsi': rsi},
                    entry_criteria_met=True,
                    risk_gates_passed=True,
                    action_taken="EXECUTED"
                )
                execute_entry(symbol)
            else:
                logger.log_decision(
                    symbol=symbol,
                    decision_type="SKIP_ENTRY",
                    reason="Risk gates failed",
                    details="Max positions reached or daily loss limit",
                    current_price=data['close'][-1],
                    indicator_values={'rsi': rsi},
                    risk_status=get_risk_status()
                )
```

## Log File Locations

All logs are stored in `/home/ssm-user/magellan/logs/` with daily rotation:

- `{strategy}_trades_YYYYMMDD.csv` - All trade executions
- `{strategy}_signals_YYYYMMDD.csv` - All signal evaluations  
- `{strategy}_decisions_YYYYMMDD.csv` - All decisions (including skips)
- `{strategy}_summary_YYYYMMDD.json` - Daily summary

## Downloading Logs from EC2

```bash
# SSH to EC2
aws ssm start-session --target i-0cd7857b7e6b2e1a8 --region us-east-2

# View today's trades
cat /home/ssm-user/magellan/logs/bear_trap_trades_$(date +%Y%m%d).csv

# Copy logs to local machine (from local terminal)
scp -i your-key.pem ec2-user@instance:/home/ssm-user/magellan/logs/*.csv ./
```

## Analyzing Logs

```python
import pandas as pd

# Load trade log
trades = pd.read_csv('bear_trap_trades_20260120.csv')

# Analyze performance
print(f"Total trades: {len(trades)}")
print(f"Win rate: {(trades['pnl_dollars'] > 0).mean():.1%}")
print(f"Total P&L: ${trades['pnl_dollars'].sum():.2f}")

# Load signal log to see what was skipped
signals = pd.read_csv('bear_trap_signals_20260120.csv')
skipped = signals[signals['action_taken'] == 'SKIPPED']
print(f"\nSkipped signals: {len(skipped)}")
print(skipped['skip_reason'].value_counts())
```
