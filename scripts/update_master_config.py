"""
Master Config Updater
Scans all docs/operations/strategies/*/assets/*/config.json files
and updates config/nodes/master_config.json with the latest validated parameters.
"""

import json
import os
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = PROJECT_ROOT / 'docs' / 'operations' / 'strategies'
MASTER_CONFIG_PATH = PROJECT_ROOT / 'config' / 'nodes' / 'master_config.json'

def load_master_config():
    if MASTER_CONFIG_PATH.exists():
        with open(MASTER_CONFIG_PATH, 'r') as f:
            return json.load(f)
    return {}

def scan_asset_configs():
    updates = {}
    
    # Iterate over strategies
    if not DOCS_DIR.exists():
        print(f"Docs dir not found: {DOCS_DIR}")
        return {}

    for strategy_dir in DOCS_DIR.iterdir():
        if not strategy_dir.is_dir(): continue
        
        assets_dir = strategy_dir / 'assets'
        if not assets_dir.exists(): continue
        
        # Iterate over assets
        for asset_dir in assets_dir.iterdir():
            if not asset_dir.is_dir(): continue
            
            config_file = asset_dir / 'config.json'
            if not config_file.exists(): continue
            
            try:
                with open(config_file, 'r') as f:
                    asset_config = json.load(f)
                
                # Check status
                status = asset_config.get('deployment_status', 'archived')
                if status not in ['active', 'ready', 'production', 'secondary']:
                    continue
                
                symbol = asset_config.get('symbol')
                if not symbol: continue
                
                # Normalize config for Master structure
                # Master structure expects:
                # "SYMBOL": { "interval": "...", "rsi_lookback": ..., ... }
                
                normalized = {}
                
                # Timeframe
                tf = asset_config.get('timeframe', '1Day')
                normalized['interval'] = tf
                
                # Strategy Parameters
                params = asset_config.get('parameters', {})
                if 'rsi_period' in params:
                    normalized['rsi_lookback'] = params['rsi_period']
                if 'rsi_upper' in params:
                    normalized['hysteresis_upper_rsi'] = params['rsi_upper']
                if 'rsi_lower' in params:
                    normalized['hysteresis_lower_rsi'] = params['rsi_lower']
                    
                # Enable Strategy Flags
                strategy_name = asset_config.get('strategy_name', '')
                if 'daily_trend' in strategy_name or 'hourly_swing' in strategy_name:
                    normalized['enable_hysteresis'] = True
                    normalized['allow_shorts'] = False # Default to long only for trend
                elif 'earnings' in strategy_name:
                    normalized['enable_earnings'] = True
                
                # Regime Filters
                if 'regime_filter' in asset_config:
                    normalized['use_regime_filter'] = True
                
                # Risk
                risk = asset_config.get('risk_management', {})
                if 'max_position_size_usd' in risk:
                    normalized['position_cap_usd'] = risk['max_position_size_usd']
                elif 'max_position_size_usd' in asset_config: # Root level fallback
                    normalized['position_cap_usd'] = asset_config['max_position_size_usd']
                    
                print(f"  Found Valid Config: {symbol} ({strategy_name})")
                updates[symbol] = normalized
                
            except Exception as e:
                print(f"  Error reading {config_file}: {e}")
                
    return updates

def update_master():
    print("="*60)
    print("MASTER CONFIG UPDATER")
    print("="*60)
    
    current_config = load_master_config()
    new_configs = scan_asset_configs()
    
    if not new_configs:
        print("No valid asset configs found.")
        return
        
    # Merge
    print(f"\nMerging {len(new_configs)} asset configurations...")
    
    # Update tickers list
    all_tickers = set(current_config.get('tickers', []))
    for sym in new_configs.keys():
        all_tickers.add(sym)
        
        # Merge individual node config
        if sym not in current_config:
            current_config[sym] = {}
        
        # Overlay new settings
        current_config[sym].update(new_configs[sym])
        
    current_config['tickers'] = sorted(list(all_tickers))
    
    # Save
    with open(MASTER_CONFIG_PATH, 'w') as f:
        json.dump(current_config, f, indent=4)
        
    print(f"✅ Master Config Updated at: {MASTER_CONFIG_PATH}")
    print(f"Active Tickers: {len(current_config['tickers'])}")

if __name__ == "__main__":
    update_master()
