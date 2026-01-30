"""
Unit tests for MIDAS Protocol Strategy
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent.parent)
sys.path.insert(0, project_root)

from prod.midas_protocol.strategy import MIDASProtocolStrategy


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        "indicators": {
            "ema_period": 200,
            "velocity_lookback": 5,
            "atr_period": 14,
            "atr_avg_period": 50,
        },
        "entry_logic": {
            "glitch_guard": {"velocity_threshold": -150},
            "setup_a_crash_reversal": {
                "velocity_min": -150,
                "velocity_max": -67,
                "ema_distance_max": 220,
                "atr_ratio_min": 0.50,
            },
            "setup_b_quiet_drift": {
                "velocity_max": 10,
                "ema_distance_max": 220,
                "atr_ratio_min": 0.06,
                "atr_ratio_max": 0.50,
            },
        },
        "exit_logic": {
            "stop_loss_points": 20,
            "take_profit_points": 120,
            "time_based_exit_bars": 60,
            "order_type": "oco_bracket",
        },
        "risk_management": {"max_daily_loss_dollars": 300, "max_position_size": 1},
        "symbol_parameters": {
            "MNQ": {"point_value": 2.0, "tick_size": 0.25, "contract_size": 1}
        },
    }


@pytest.fixture
def mock_strategy(mock_config):
    """Create a mock strategy instance"""
    with patch("prod.midas_protocol.strategy.TradingClient"), patch(
        "prod.midas_protocol.strategy.StockHistoricalDataClient"
    ):

        strategy = MIDASProtocolStrategy(
            api_key="test_key",
            api_secret="test_secret",
            base_url="https://paper-api.alpaca.markets",
            symbols=["MNQ"],
            config=mock_config,
        )
        return strategy


def test_calculate_ema(mock_strategy):
    """Test EMA calculation"""
    # Create test series
    data = pd.Series([100, 101, 102, 103, 104, 105])
    ema = mock_strategy.calculate_ema(data, period=3)

    # EMA should be smoothed
    assert len(ema) == len(data)
    assert ema.iloc[-1] > ema.iloc[0]  # Trending up


def test_calculate_atr(mock_strategy):
    """Test ATR calculation"""
    # Create test dataframe
    df = pd.DataFrame(
        {
            "high": [102, 103, 104, 105, 106],
            "low": [98, 99, 100, 101, 102],
            "close": [100, 101, 102, 103, 104],
        }
    )

    atr = mock_strategy.calculate_atr(df, period=3)

    # ATR should be positive
    assert len(atr) == len(df)
    assert (atr >= 0).all()


def test_calculate_indicators(mock_strategy):
    """Test full indicator calculation"""
    # Create test data
    np.random.seed(42)
    dates = pd.date_range(start="2024-01-01", periods=300, freq="1min")

    df = pd.DataFrame(
        {
            "timestamp": dates,
            "close": 15000 + np.cumsum(np.random.randn(300) * 10),
            "high": 15000 + np.cumsum(np.random.randn(300) * 10) + 5,
            "low": 15000 + np.cumsum(np.random.randn(300) * 10) - 5,
            "volume": np.random.randint(100, 1000, 300),
        }
    )

    result = mock_strategy.calculate_indicators(df)

    # Check all indicators are present
    assert "ema_200" in result.columns
    assert "velocity" in result.columns
    assert "atr_14" in result.columns
    assert "atr_avg_50" in result.columns
    assert "atr_ratio" in result.columns
    assert "ema_distance" in result.columns


def test_evaluate_entry_setup_a(mock_strategy):
    """Test Setup A (Crash Reversal) detection"""
    # Create test data that triggers Setup A
    df = pd.DataFrame(
        {
            "close": [15000, 14950, 14900, 14850, 14800, 14750],  # Crashing
            "high": [15010, 14960, 14910, 14860, 14810, 14760],
            "low": [14990, 14940, 14890, 14840, 14790, 14740],
            "volume": [1000] * 6,
        }
    )

    df = mock_strategy.calculate_indicators(df)

    # Manually set conditions for Setup A
    df.loc[df.index[-1], "velocity"] = -100  # Between -150 and -67
    df.loc[df.index[-1], "ema_distance"] = 150  # < 220
    df.loc[df.index[-1], "atr_ratio"] = 0.60  # > 0.50

    mock_strategy.current_bars["MNQ"] = df

    setup = mock_strategy.evaluate_entry("MNQ")

    assert setup == "setup_a"


def test_evaluate_entry_setup_b(mock_strategy):
    """Test Setup B (Quiet Drift) detection"""
    # Create test data that triggers Setup B
    df = pd.DataFrame(
        {
            "close": [15000, 15001, 15002, 15003, 15004, 15005],  # Quiet drift
            "high": [15010, 15011, 15012, 15013, 15014, 15015],
            "low": [14990, 14991, 14992, 14993, 14994, 14995],
            "volume": [1000] * 6,
        }
    )

    df = mock_strategy.calculate_indicators(df)

    # Manually set conditions for Setup B
    df.loc[df.index[-1], "velocity"] = 5  # <= 10
    df.loc[df.index[-1], "ema_distance"] = 150  # < 220
    df.loc[df.index[-1], "atr_ratio"] = 0.30  # Between 0.06 and 0.50

    mock_strategy.current_bars["MNQ"] = df

    setup = mock_strategy.evaluate_entry("MNQ")

    assert setup == "setup_b"


def test_glitch_guard(mock_strategy):
    """Test Glitch Guard blocks extreme velocity"""
    df = pd.DataFrame(
        {
            "close": [15000] * 6,
            "high": [15010] * 6,
            "low": [14990] * 6,
            "volume": [1000] * 6,
        }
    )

    df = mock_strategy.calculate_indicators(df)

    # Set extreme velocity (glitch/flash crash)
    df.loc[df.index[-1], "velocity"] = -200  # < -150 (BLOCKED)
    df.loc[df.index[-1], "ema_distance"] = 100
    df.loc[df.index[-1], "atr_ratio"] = 0.60

    mock_strategy.current_bars["MNQ"] = df

    setup = mock_strategy.evaluate_entry("MNQ")

    # Should be None (blocked by glitch guard)
    assert setup is None


def test_risk_gates(mock_strategy):
    """Test risk management gates"""
    # Test max daily loss
    mock_strategy.daily_pnl = -300
    assert not mock_strategy.check_risk_gates()

    # Reset and test max positions
    mock_strategy.daily_pnl = 0
    mock_strategy.positions = {"MNQ": {}}
    assert not mock_strategy.check_risk_gates()  # Already at max (1)

    # Reset and test session check (will depend on current time)
    mock_strategy.positions = {}
    # Note: is_in_session() depends on actual UTC time


def test_stop_loss_calculation(mock_strategy):
    """Test stop loss and take profit calculation"""
    entry_price = 15000

    expected_stop = entry_price - mock_strategy.stop_loss_points
    expected_take = entry_price + mock_strategy.take_profit_points

    assert expected_stop == 14980  # 15000 - 20
    assert expected_take == 15120  # 15000 + 120


def test_daily_state_reset(mock_strategy):
    """Test daily state reset"""
    mock_strategy.daily_pnl = -100
    mock_strategy.trades_today = 5
    mock_strategy.session_halted = True

    mock_strategy.reset_daily_state()

    assert mock_strategy.daily_pnl == 0
    assert mock_strategy.trades_today == 0
    assert mock_strategy.session_halted == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
