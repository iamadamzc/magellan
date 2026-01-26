# Master Config Integration - Quick Guide

**Date**: 2026-01-16  
**Status**: ✅ COMPLETE (MES and MNQ integrated)

---

## HOW IT WORKS

The Magellan system uses a **decentralized config management** approach:

1. **Individual Asset Configs**: Each approved asset has its own `config.json` file in:
   ```
   docs/operations/strategies/<STRATEGY>/assets/<SYMBOL>/config.json
   ```

2. **Master Config Sync**: The `update_master_config.py` script **automatically scans** all asset configs and syncs them to the centralized:
   ```
   config/nodes/master_config.json
   ```

3. **Deployment Status Filter**: Only assets with these statuses are synced:
   - `"active"` ← **Used for MES/MNQ**
   - `"ready"`
   - `"production"`
   - `"secondary"`

---

## WHAT WAS DONE FOR FUTURES

### Step 1: Created Asset Configs ✅
Created individual config files for approved futures:
- `daily_trend_hysteresis/assets/MES/config.json`
- `daily_trend_hysteresis/assets/MNQ/config.json`

### Step 2: Set Status to "active" ✅
Updated both configs:
```json
{
    "deployment_status": "active",  // Changed from "approved"
    ...
}
```

### Step 3: Ran Sync Script ✅
Executed:
```bash
python scripts/update_master_config.py
```

Output:
```
Found Valid Config: MES (daily_trend_hysteresis)
Found Valid Config: MNQ (daily_trend_hysteresis)
✅ Master Config Updated at: config/nodes/master_config.json
Active Tickers: 18
```

---

## RESULT

**master_config.json now contains:**

```json
{
    "tickers": [
        ...
        "MES",  // Added!
        "MNQ",  // Added!
        ...
    ],
    "MES": {
        "interval": "1Day",
        "rsi_lookback": 28,
        "hysteresis_upper_rsi": 55,
        "hysteresis_lower_rsi": 45,
        "enable_hysteresis": true,
        "allow_shorts": false
    },
    "MNQ": {
        "interval": "1Day",
        "rsi_lookback": 28,
        "hysteresis_upper_rsi": 55,
        "hysteresis_lower_rsi": 45,
        "enable_hysteresis": true,
        "allow_shorts": false
    }
}
```

---

## HOW THE SYSTEM USES THIS

### For Live Trading
The trading system reads `master_config.json` to:
1. Know which symbols to trade
2. Get strategy parameters for each symbol
3. Enable/disable features (hysteresis, earnings, regime filters)
4. Set position limits

### For Futures (MES/MNQ)
The system will now:
- ✅ Include MES and MNQ in active trading universe
- ✅ Apply Daily Trend Hysteresis strategy (RSI-28, bands 55/45)
- ✅ Use long-only positioning
- ✅ Trade on daily timeframe

---

## UPDATING CONFIGS IN THE FUTURE

### To Add a New Asset:
1. Create `docs/operations/strategies/<STRATEGY>/assets/<SYMBOL>/config.json`
2. Set `"deployment_status": "active"`
3. Run `python scripts/update_master_config.py`

### To Modify Existing Asset:
1. Edit the individual asset config file
2. Run `python scripts/update_master_config.py`
3. Restart trading system to pick up changes

### To Remove an Asset:
1. Change `"deployment_status": "archived"` in asset config
2. Run `python scripts/update_master_config.py`
3. Symbol will be removed from active trading

---

## FUTURES INTEGRATION COMPLETE

✅ **MES and MNQ are now integrated into master_config.json**  
✅ **System is ready to trade futures contracts**

**Next Steps**:
1. Deploy to paper trading environment
2. Monitor execution on futures contracts
3. Validate fills and slippage match expectations
4. Scale to live after 2-week validation period

---

## TECHNICAL DETAILS

### Config Normalization
The update script automatically translates from asset config format to master config format:

| Asset Config | Master Config |
|--------------|---------------|
| `timeframe` | `interval` |
| `parameters.rsi_period` | `rsi_lookback` |
| `parameters.rsi_upper` | `hysteresis_upper_rsi` |
| `parameters.rsi_lower` | `hysteresis_lower_rsi` |
| `risk_management.max_position_size_usd` | `position_cap_usd` |

### Script Location
```
scripts/update_master_config.py
```

### Auto-Detection
The script automatically:
- Scans all `/assets/*/config.json` files
- Filters by `deployment_status`
- Merges into master config
- Updates tickers list
- Preserves existing configurations

---

**Integration Complete**: 2026-01-16  
**Futures Contracts Added**: 2 (MES, MNQ)  
**Total Active Tickers**: 18
