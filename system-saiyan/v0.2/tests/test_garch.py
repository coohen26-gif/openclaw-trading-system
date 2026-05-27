"""
🐉 GARCH Model Unit Tests

Tests for volatility/garch_model.py
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from volatility.garch_model import GARCHVolatilityModel, EGARCHVolatilityModel


class TestGARCHVolatilityModel:
    """Test suite for GARCHVolatilityModel."""
    
    @pytest.fixture
    def sample_prices(self):
        """Generate synthetic BTC-like price series."""
        np.random.seed(42)
        n_days = 500
        
        # Simulate volatility clustering
        base_vol = 0.03
        vol_persistence = 0.85
        
        vol = np.ones(n_days) * base_vol
        returns = np.zeros(n_days)
        
        for t in range(1, n_days):
            vol[t] = np.sqrt(0.1 * base_vol**2 + 0.1 * returns[t-1]**2 + vol_persistence * vol[t-1]**2)
            returns[t] = np.random.normal(0, vol[t])
        
        prices = 100 * np.exp(np.cumsum(returns))
        return pd.Series(prices)
    
    @pytest.fixture
    def garch_model(self):
        """Create fresh GARCH model."""
        return GARCHVolatilityModel()
    
    def test_initialization(self, garch_model):
        """Test model initialization."""
        assert garch_model.model_type == 'GARCH'
        assert garch_model.p == 1
        assert garch_model.q == 1
        assert garch_model.mean == 'Zero'
        assert not garch_model.is_fitted()
    
    def test_fit_with_prices(self, garch_model, sample_prices):
        """Test fitting model with price series."""
        result = garch_model.fit(prices=sample_prices)
        
        assert result is not None
        assert result.alpha > 0
        assert result.beta > 0
        assert result.persistence > 0
        assert result.persistence < 1.5  # Should be stationary-ish
        assert result.half_life_days > 0
        assert result.daily_vol_forecast > 0
        assert result.annualized_vol > 0
        assert result.n_observations == len(sample_prices) - 1
        assert garch_model.is_fitted()
    
    def test_fit_with_returns(self, garch_model, sample_prices):
        """Test fitting model with pre-computed returns."""
        returns = np.diff(np.log(sample_prices.values))
        result = garch_model.fit(returns=returns)
        
        assert result is not None
        assert result.alpha > 0
        assert result.beta > 0
    
    def test_fit_insufficient_data(self, garch_model):
        """Test fitting with insufficient data."""
        short_prices = pd.Series([100, 101, 102])
        
        with pytest.raises(ValueError, match="Need at least 10"):
            garch_model.fit(prices=short_prices)
    
    def test_forecast(self, garch_model, sample_prices):
        """Test volatility forecasting."""
        garch_model.fit(prices=sample_prices)
        forecast = garch_model.forecast()
        
        assert forecast is not None
        assert forecast.daily_volatility > 0
        assert forecast.weekly_volatility >= forecast.daily_volatility
        assert forecast.monthly_volatility >= forecast.weekly_volatility
        assert forecast.annualized_volatility > 0
        assert forecast.regime in ['LOW', 'NORMAL', 'HIGH', 'EXTREME']
        assert forecast.confidence_lower >= 0
        assert forecast.confidence_upper >= forecast.confidence_lower
    
    def test_position_size_multiplier(self, garch_model, sample_prices):
        """Test position size multiplier calculation."""
        garch_model.fit(prices=sample_prices)
        
        multiplier = garch_model.get_position_size_multiplier()
        assert multiplier > 0
        assert multiplier <= 2.0  # Capped at 2x
        assert multiplier >= 0.25  # Minimum 0.25x
    
    def test_position_size_multiplier_custom_target(self, garch_model, sample_prices):
        """Test position size with custom target volatility."""
        garch_model.fit(prices=sample_prices)
        
        # Higher target → higher multiplier
        mult_high = garch_model.get_position_size_multiplier(target_vol=5.0)
        mult_low = garch_model.get_position_size_multiplier(target_vol=1.0)
        
        assert mult_high > mult_low
    
    def test_cache(self, garch_model, sample_prices):
        """Test parameter caching."""
        # First fit
        result1 = garch_model.fit(prices=sample_prices)
        alpha1 = result1.alpha
        
        # Second fit (should use cache)
        result2 = garch_model.fit(prices=sample_prices)
        alpha2 = result2.alpha
        
        assert alpha1 == alpha2  # Cached
        
        # Force refit
        result3 = garch_model.fit(prices=sample_prices, force_refit=True)
        # May differ slightly due to numerical optimization
    
    def test_clear_cache(self, garch_model, sample_prices):
        """Test cache clearing."""
        garch_model.fit(prices=sample_prices)
        assert garch_model.is_fitted()
        
        garch_model.clear_cache()
        assert not garch_model.is_fitted()
    
    def test_get_parameters(self, garch_model, sample_prices):
        """Test getting fitted parameters."""
        garch_model.fit(prices=sample_prices)
        params = garch_model.get_parameters()
        
        assert params is not None
        assert 'omega' in params
        assert 'alpha' in params
        assert 'beta' in params
        assert 'persistence' in params
        assert 'half_life_days' in params
        assert 'r_squared' in params
    
    def test_get_summary(self, garch_model, sample_prices):
        """Test summary generation."""
        garch_model.fit(prices=sample_prices)
        summary = garch_model.get_summary()
        
        assert summary is not None
        assert summary['status'] == 'FITTED'
        assert 'parameters' in summary
        assert 'forecast' in summary
        assert 'position_sizing' in summary
    
    def test_not_fitted_summary(self, garch_model):
        """Test summary when not fitted."""
        summary = garch_model.get_summary()
        assert summary['status'] == 'NOT_FITTED'
    
    def test_vol_regimes(self, garch_model, sample_prices):
        """Test volatility regime classification."""
        garch_model.fit(prices=sample_prices)
        forecast = garch_model.forecast()
        
        # Verify regime matches volatility level
        daily_vol = forecast.daily_volatility
        
        if daily_vol < 1.5:
            assert forecast.regime == 'LOW'
        elif daily_vol < 3.0:
            assert forecast.regime == 'NORMAL'
        elif daily_vol < 5.0:
            assert forecast.regime == 'HIGH'
        else:
            assert forecast.regime == 'EXTREME'


class TestEGARCHVolatilityModel:
    """Test suite for EGARCHVolatilityModel."""
    
    @pytest.fixture
    def sample_prices(self):
        """Generate synthetic price series with leverage effect."""
        np.random.seed(42)
        n_days = 500
        
        returns = np.zeros(n_days)
        vol = np.ones(n_days) * 0.03
        
        for t in range(1, n_days):
            # Asymmetric response (negative shocks increase vol more)
            shock = np.random.normal(0, 1)
            if shock < 0:
                vol[t] = vol[t-1] * 1.05  # Negative shock increases vol
            else:
                vol[t] = vol[t-1] * 0.98  # Positive shock decreases vol
            vol[t] = max(0.01, min(vol[t], 0.10))  # Clamp
            returns[t] = shock * vol[t]
        
        prices = 100 * np.exp(np.cumsum(returns))
        return pd.Series(prices)
    
    @pytest.fixture
    def egarch_model(self):
        """Create fresh EGARCH model."""
        return EGARCHVolatilityModel()
    
    def test_initialization(self, egarch_model):
        """Test EGARCH initialization."""
        assert egarch_model.model_type == 'EGARCH'
    
    def test_fit_and_forecast(self, egarch_model, sample_prices):
        """Test EGARCH fit and forecast."""
        result = egarch_model.fit(prices=sample_prices)
        
        assert result is not None
        assert result.alpha is not None
        assert result.beta is not None
        
        forecast = egarch_model.forecast()
        assert forecast is not None
        assert forecast.daily_volatility > 0
    
    def test_asymmetry_parameter(self, egarch_model, sample_prices):
        """Test asymmetry (gamma) parameter."""
        egarch_model.fit(prices=sample_prices)
        gamma = egarch_model.get_asymmetry()
        
        # Gamma should exist (may be 0 if no asymmetry detected)
        assert gamma is not None
    
    def test_egarch_summary(self, egarch_model, sample_prices):
        """Test EGARCH-specific summary."""
        egarch_model.fit(prices=sample_prices)
        summary = egarch_model.get_summary()
        
        assert 'asymmetry' in summary
        assert 'gamma' in summary['asymmetry']
        assert 'interpretation' in summary['asymmetry']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
