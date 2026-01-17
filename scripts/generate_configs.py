import json
from pathlib import Path

# Define Tier 1 Assets and Parameters
configs = {
    "META": {
        "symbol": "META",
        "position_limit": 0.10,
        "notes": "Tier 1 - Top Performer (Sharpe 1.67 in Bear)"
    },
    "NVDA": {
        "symbol": "NVDA",
        "position_limit": 0.10,
        "notes": "Tier 1 - Strong Momentum (Sharpe 1.19 in Bear)"
    },
    "AMZN": {
        "symbol": "AMZN",
        "position_limit": 0.10,
        "notes": "Tier 1 - Consistent (Sharpe 0.95 in Bear)"
    },
    "COIN": {
        "symbol": "COIN",
        "position_limit": 0.05,  # Lower size due to volatility
        "notes": "Tier 1 - High Volatility (Sharpe 0.84 in Bear)"
    },
    "QQQ": {
        "symbol": "QQQ",
        "position_limit": 0.15,  # Higher size for ETF
        "notes": "Tier 1 - Core ETF (Sharpe 0.97 in Bear)"
    }
}

# Common Strategy Parameters
strategy_params = {
    "strategy_name": "regime_sentiment_filter",
    "version": "1.0.0",
    "timeframe": "1day",
    "parameters": {
        "rsi_period": 28,
        "entry_regime_bull": {
            "rsi_threshold": 55,
            "spy_ma_period": 200,
            "sentiment_threshold": -0.2
        },
        "entry_breakout_strong": {
            "rsi_threshold": 65,
            "sentiment_threshold": 0.0
        },
        "exit_conditions": {
            "rsi_threshold": 45,
            "sentiment_threshold": -0.3
        }
    }
}

def generate_configs():
    base_path = Path("deployment_configs/regime_sentiment")
    base_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating configs in {base_path}...")
    
    for symbol, asset_config in configs.items():
        # Merge specific asset config with common params
        config = strategy_params.copy()
        config.update(asset_config)
        
        file_path = base_path / f"{symbol}.json"
        with open(file_path, "w") as f:
            json.dump(config, f, indent=4)
        print(f"✓ Created {file_path}")

if __name__ == "__main__":
    generate_configs()
