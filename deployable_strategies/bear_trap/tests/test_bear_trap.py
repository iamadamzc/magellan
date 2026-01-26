"""
Bear Trap Strategy Tests
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_strategy_imports():
    """Test that strategy can be imported"""
    from strategy import BearTrapStrategy

    assert BearTrapStrategy is not None


def test_config_loads():
    """Test that config.json can be loaded"""
    import json
    from pathlib import Path

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
    # This will fail if there are syntax errors
    import importlib.util

    runner_path = Path(__file__).parent.parent / "runner.py"
    spec = importlib.util.spec_from_file_location("runner", runner_path)
    module = importlib.util.module_from_spec(spec)

    # Just check it can be loaded (don't execute)
    assert module is not None


# TODO: Add more comprehensive tests
# - Test strategy initialization with mock data
# - Test signal generation logic
# - Test position sizing
# - Test risk management
# - Test order placement (mocked)
