"""
Daily Trend Strategy Tests
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_strategy_imports():
    """Test that strategy module can be imported"""
    import strategy as strategy_module

    assert strategy_module is not None


def test_config_loads():
    """Test that config.json can be loaded"""
    import json

    config_path = Path(__file__).parent.parent / "config.json"
    assert config_path.exists(), "config.json not found"

    with open(config_path) as f:
        config = json.load(f)

    # Verify required fields
    assert "symbols" in config
    assert "account_info" in config
    assert "risk_management" in config
    assert len(config["symbols"]) > 0


def test_runner_imports():
    """Test that runner can be imported"""
    import importlib.util

    runner_path = Path(__file__).parent.parent / "runner.py"
    spec = importlib.util.spec_from_file_location("runner", runner_path)
    module = importlib.util.module_from_spec(spec)

    assert module is not None


# TODO: Add more comprehensive tests
# - Test signal generation logic
# - Test RSI calculation
# - Test hysteresis thresholds
# - Test position sizing
# - Test order placement (mocked)
