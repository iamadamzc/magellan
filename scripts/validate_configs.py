"""
Configuration validator for Magellan trading strategies.
Ensures all config files are valid JSON and contain required fields.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set

REQUIRED_FIELDS = {
    "symbols": list,
    "risk_management": dict,
    "trading_hours": dict,
}

REQUIRED_RISK_FIELDS = {
    "per_trade_risk_pct": (float, int),
    "max_daily_loss_pct": (float, int),
}


def validate_config(config_path: Path) -> List[str]:
    """Validate a single configuration file."""
    errors = []
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON in {config_path}: {e}"]
    except Exception as e:
        return [f"Error reading {config_path}: {e}"]
    
    # Check required top-level fields
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in config:
            errors.append(f"{config_path}: Missing required field '{field}'")
        elif not isinstance(config[field], expected_type):
            errors.append(
                f"{config_path}: Field '{field}' should be {expected_type.__name__}, "
                f"got {type(config[field]).__name__}"
            )
    
    # Validate symbols list
    if "symbols" in config:
        if not config["symbols"]:
            errors.append(f"{config_path}: 'symbols' list is empty")
        elif not all(isinstance(s, str) for s in config["symbols"]):
            errors.append(f"{config_path}: All symbols must be strings")
    
    # Validate risk management
    if "risk_management" in config:
        risk = config["risk_management"]
        for field, expected_types in REQUIRED_RISK_FIELDS.items():
            if field not in risk:
                errors.append(f"{config_path}: Missing risk field '{field}'")
            elif not isinstance(risk[field], expected_types):
                errors.append(
                    f"{config_path}: Risk field '{field}' should be numeric"
                )
    
    return errors


def main():
    """Validate all configuration files."""
    repo_root = Path(__file__).parent.parent
    config_files = list(repo_root.glob("deployable_strategies/*/aws_deployment/config.json"))
    
    if not config_files:
        print("❌ No configuration files found!")
        sys.exit(1)
    
    print(f"Found {len(config_files)} configuration files to validate:\n")
    
    all_errors = []
    for config_file in config_files:
        strategy_name = config_file.parent.parent.name
        print(f"Validating {strategy_name}...")
        
        errors = validate_config(config_file)
        if errors:
            all_errors.extend(errors)
            print(f"  ❌ {len(errors)} error(s) found")
            for error in errors:
                print(f"    - {error}")
        else:
            print(f"  ✅ Valid")
    
    print(f"\n{'='*60}")
    if all_errors:
        print(f"❌ Validation failed with {len(all_errors)} error(s)")
        sys.exit(1)
    else:
        print("✅ All configuration files are valid!")
        sys.exit(0)


if __name__ == "__main__":
    main()
