"""
🧪 Pytest Configuration and Fixtures - Saiyan v0.3

Fixtures for:
- Test data (BTC returns, prices)
- Mocks (Telegram, Binance API)
- Random seeds for deterministic tests
- Common test utilities

Usage:
    pytest tests/ -v --cov=. --cov-report=html
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
import sys

# Add v0.3 to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# Random Seed Fixture - Deterministic Tests
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def set_random_seed():
    """Set random seeds for reproducible tests."""
    np.random.seed(42)
    return 42


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_prices() -> pd.Series:
    """
    Generate sample price series for testing.
    
    Returns realistic-looking BTC-like prices with:
    - Starting price ~$50,000
    - Daily volatility ~2-3%
    - Slight upward drift
    """
    np.random.seed(42)
    n_days = 500
    
    # Generate returns with realistic stats
    daily_returns = np.random.normal(loc=0.0003, scale=0.025, size=n_days)
    
    # Add some autocorrelation (momentum)
    daily_returns[1:] += 0.1 * daily_returns[:-1]
    
    # Generate prices from returns
    prices = pd.Series(50000, index=pd.date_range('2024-01-01', periods=n_days, freq='D'))
    for i in range(1, n_days):
        prices.iloc[i] = prices.iloc[i-1] * (1 + daily_returns[i])
    
    return prices


@pytest.fixture
def sample_returns(sample_prices: pd.Series) -> pd.Series:
    """Calculate returns from sample prices."""
    return sample_prices.pct_change().dropna()


@pytest.fixture
def btc_like_data() -> pd.DataFrame:
    """
    Generate realistic BTC-like OHLCV data.
    
    Returns DataFrame with columns: date, open, high, low, close, volume
    """
    np.random.seed(42)
    n_days = 730  # 2 years
    
    dates = pd.date_range('2024-01-01', periods=n_days, freq='D')
    
    # Generate close prices
    base_price = 40000
    returns = np.random.normal(loc=0.0002, scale=0.028, size=n_days)
    close = pd.Series(base_price, index=dates)
    for i in range(1, n_days):
        close.iloc[i] = close.iloc[i-1] * (1 + returns[i])
    
    # Generate OHLC from close
    daily_range = np.random.uniform(0.01, 0.04, size=n_days)
    high = close * (1 + daily_range * np.random.uniform(0.3, 0.7, size=n_days))
    low = close * (1 - daily_range * np.random.uniform(0.3, 0.7, size=n_days))
    open_price = low + (high - low) * np.random.uniform(0.2, 0.8, size=n_days)
    
    # Volume (higher on volatile days)
    base_volume = 1e9
    volume = base_volume * (1 + np.abs(returns) * 10) * np.random.uniform(0.5, 1.5, size=n_days)
    
    df = pd.DataFrame({
        'date': dates,
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })
    
    return df


@pytest.fixture
def bull_market_returns() -> pd.Series:
    """Returns series simulating bull market (positive drift, low vol)."""
    np.random.seed(123)
    n_days = 200
    returns = np.random.normal(loc=0.0015, scale=0.015, size=n_days)
    dates = pd.date_range('2024-01-01', periods=n_days, freq='D')
    return pd.Series(returns, index=dates)


@pytest.fixture
def bear_market_returns() -> pd.Series:
    """Returns series simulating bear market (negative drift, high vol)."""
    np.random.seed(456)
    n_days = 200
    returns = np.random.normal(loc=-0.0015, scale=0.035, size=n_days)
    dates = pd.date_range('2024-01-01', periods=n_days, freq='D')
    return pd.Series(returns, index=dates)


@pytest.fixture
def range_market_returns() -> pd.Series:
    """Returns series simulating ranging market (near-zero drift, low vol)."""
    np.random.seed(789)
    n_days = 200
    returns = np.random.normal(loc=0.0001, scale=0.012, size=n_days)
    dates = pd.date_range('2024-01-01', periods=n_days, freq='D')
    return pd.Series(returns, index=dates)


@pytest.fixture
def volatile_bull_returns() -> pd.Series:
    """Returns series simulating volatile bull market (positive drift, high vol)."""
    np.random.seed(321)
    n_days = 200
    returns = np.random.normal(loc=0.001, scale=0.04, size=n_days)
    dates = pd.date_range('2024-01-01', periods=n_days, freq='D')
    return pd.Series(returns, index=dates)


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_telegram_bot():
    """Mock Telegram Bot for testing."""
    mock_bot = AsyncMock()
    mock_bot.get_me = AsyncMock(return_value=MagicMock(username='saiyan_test_bot'))
    mock_bot.send_message = AsyncMock(return_value=True)
    return mock_bot


@pytest.fixture
def mock_telegram_env():
    """Mock environment variables for Telegram."""
    with patch.dict('os.environ', {
        'TELEGRAM_BOT_TOKEN': 'test_token_12345',
        'TELEGRAM_CHAT_ID': '-1001234567890'
    }):
        yield


@pytest.fixture
def mock_binance_api():
    """Mock Binance API responses."""
    mock_response = MagicMock()
    mock_response.read = MagicMock(return_value=json.dumps([{
        'open_time': 1704067200000,
        'open': '42000.00',
        'high': '42500.00',
        'low': '41800.00',
        'close': '42300.00',
        'volume': '1000.00'
    }]).encode())
    
    with patch('urllib.request.urlopen', return_value=mock_response):
        yield


# ============================================================================
# Temporary File Fixtures
# ============================================================================

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory for test files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def temp_kill_switch_file(temp_data_dir):
    """Create temporary kill switch state file path."""
    return str(temp_data_dir / "test_kill_switch.json")


@pytest.fixture
def temp_telegram_state_file(temp_data_dir):
    """Create temporary Telegram state file path."""
    return str(temp_data_dir / "test_telegram_state.json")


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def sample_ohlcv_data() -> pd.DataFrame:
    """Sample OHLCV DataFrame for backtest testing."""
    np.random.seed(42)
    n_days = 365
    
    dates = pd.date_range('2024-01-01', periods=n_days, freq='D')
    base_price = 50000
    
    # Generate realistic price path
    returns = np.random.normal(loc=0.0002, scale=0.025, size=n_days)
    prices = [base_price]
    for r in returns[1:]:
        prices.append(prices[-1] * (1 + r))
    
    # Create OHLCV
    daily_vol = np.random.uniform(0.015, 0.035, size=n_days)
    high = [p * (1 + v * np.random.uniform(0.4, 0.8)) for p, v in zip(prices, daily_vol)]
    low = [p * (1 - v * np.random.uniform(0.4, 0.8)) for p, v in zip(prices, daily_vol)]
    open_prices = [l + (h - l) * np.random.uniform(0.3, 0.7) for h, l in zip(high, low)]
    volume = np.random.uniform(1e8, 5e8, size=n_days)
    
    df = pd.DataFrame({
        'date': dates,
        'open': open_prices,
        'high': high,
        'low': low,
        'close': prices,
        'volume': volume
    })
    
    return df


@pytest.fixture
def trading_config() -> dict:
    """Sample trading configuration for tests."""
    return {
        'initial_capital': 10000,
        'position_size_pct': 0.05,
        'stop_loss_pct': 0.05,
        'take_profit_pct': 0.15,
        'max_drawdown': 0.20,
        'daily_loss_limit': 0.05,
        'fee_round_trip': 0.0022,
    }


# ============================================================================
# HMM-Specific Fixtures
# ============================================================================

@pytest.fixture
def hmm_training_data() -> tuple:
    """
    Generate training data for HMM testing.
    
    Returns:
        Tuple of (returns, volatility, regime_labels)
    """
    np.random.seed(42)
    
    # Generate data with 4 distinct regimes
    n_per_regime = 100
    
    # Bull regime: positive returns, low vol
    bull_ret = np.random.normal(0.002, 0.012, n_per_regime)
    bull_vol = np.abs(np.random.normal(0.012, 0.003, n_per_regime))
    
    # Bear regime: negative returns, high vol
    bear_ret = np.random.normal(-0.002, 0.025, n_per_regime)
    bear_vol = np.abs(np.random.normal(0.025, 0.005, n_per_regime))
    
    # Range regime: near-zero returns, low vol
    range_ret = np.random.normal(0.0001, 0.008, n_per_regime)
    range_vol = np.abs(np.random.normal(0.008, 0.002, n_per_regime))
    
    # Volatile bull: positive returns, high vol
    vol_bull_ret = np.random.normal(0.0015, 0.035, n_per_regime)
    vol_bull_vol = np.abs(np.random.normal(0.035, 0.008, n_per_regime))
    
    # Combine
    returns = np.concatenate([bull_ret, bear_ret, range_ret, vol_bull_ret])
    volatility = np.concatenate([bull_vol, bear_vol, range_vol, vol_bull_vol])
    regimes = ['bull'] * n_per_regime + ['bear'] * n_per_regime + \
              ['range'] * n_per_regime + ['vol_bull'] * n_per_regime
    
    dates = pd.date_range('2023-01-01', periods=len(returns), freq='D')
    
    return (
        pd.Series(returns, index=dates),
        pd.Series(volatility, index=dates),
        regimes
    )


# ============================================================================
# Import required modules after path setup
# ============================================================================

# These imports happen after fixtures are defined to avoid circular imports
import json
