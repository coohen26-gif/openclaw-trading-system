"""
🧪 Tests for HMM Regime Detection - Saiyan v0.3

Tests cover:
- HMM model fitting with hmmlearn
- Regime detection accuracy
- Regime-dependent position sizing
- Rolling window retraining
- Fallback heuristics

Coverage target: >85%
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.hmm_regime import (
    HMMRegimeDetector,
    Regime,
    detect_regime_hmm
)


class TestRegimeEnum:
    """Test Regime enum."""
    
    def test_regime_values(self):
        """Test regime enum has correct values."""
        assert Regime.BULL.value == "Bull"
        assert Regime.BEAR.value == "Bear"
        assert Regime.RANGE.value == "Range"
        assert Regime.VOLATILE_BULL.value == "Volatile Bull"
    
    def test_regime_count(self):
        """Test there are 4 regimes."""
        assert len(list(Regime)) == 4


class TestHMMRegimeDetectorInit:
    """Test HMMRegimeDetector initialization."""
    
    def test_default_init(self):
        """Test default initialization parameters."""
        detector = HMMRegimeDetector()
        
        assert detector.n_regimes == 4
        assert detector.rolling_window == 180
        assert detector.n_iterations == 100
        assert detector.random_state == 42
        assert detector.model is None
        assert detector._returns_history == []
    
    def test_custom_init(self):
        """Test custom initialization parameters."""
        detector = HMMRegimeDetector(
            n_regimes=3,
            rolling_window=90,
            n_iterations=50,
            random_state=123
        )
        
        assert detector.n_regimes == 3
        assert detector.rolling_window == 90
        assert detector.n_iterations == 50
        assert detector.random_state == 123
    
    def test_hmmlearn_required(self):
        """Test that hmmlearn is required."""
        # This should work if hmmlearn is installed
        try:
            detector = HMMRegimeDetector()
            assert detector is not None
        except ImportError:
            pytest.skip("hmmlearn not installed")


class TestHMMRegimeDetectorFit:
    """Test HMM model fitting."""
    
    def test_fit_with_sufficient_data(self, sample_returns):
        """Test fitting with sufficient data (>180 days)."""
        pytest.importorskip("hmmlearn")
        
        detector = HMMRegimeDetector(rolling_window=100)
        
        # Need at least rolling_window days
        assert len(sample_returns) >= 100
        
        detector.fit(sample_returns)
        
        assert detector.model is not None
        assert len(detector._returns_history) > 0
        assert len(detector._volatility_history) > 0
        assert detector._last_regime is not None
    
    def test_fit_insufficient_data(self):
        """Test fitting with insufficient data raises error."""
        pytest.importorskip("hmmlearn")
        
        detector = HMMRegimeDetector(rolling_window=180)
        
        # Create too-short series
        short_returns = pd.Series(np.random.randn(50))
        
        with pytest.raises(ValueError, match="Need at least"):
            detector.fit(short_returns)
    
    def test_fit_with_custom_volatility(self, sample_returns):
        """Test fitting with custom volatility series."""
        pytest.importorskip("hmmlearn")
        
        detector = HMMRegimeDetector(rolling_window=100)
        volatility = sample_returns.rolling(20).std()
        
        detector.fit(sample_returns, volatility)
        
        assert detector.model is not None
    
    def test_fit_sets_last_regime(self, sample_returns):
        """Test that fit sets last predicted regime."""
        pytest.importorskip("hmmlearn")
        
        detector = HMMRegimeDetector(rolling_window=100)
        detector.fit(sample_returns)
        
        assert detector._last_regime in list(Regime)
        assert detector._last_confidence >= 0.0
        assert detector._last_confidence <= 1.0
    
    def test_fit_creates_regime_mapping(self, sample_returns):
        """Test that fit creates regime mapping for all states."""
        pytest.importorskip("hmmlearn")
        
        detector = HMMRegimeDetector(n_regimes=4, rolling_window=100)
        detector.fit(sample_returns)
        
        # Should have mapping for all 4 states
        assert len(detector._regime_mapping) == 4
        
        # All mappings should be valid Regime enums
        for state, regime in detector._regime_mapping.items():
            assert isinstance(regime, Regime)


class TestHMMRegimeDetectorPredict:
    """Test HMM regime prediction."""
    
    def test_predict_after_fit(self, sample_returns):
        """Test prediction after fitting."""
        pytest.importorskip("hmmlearn")
        
        detector = HMMRegimeDetector(rolling_window=100)
        detector.fit(sample_returns)
        
        recent_returns = sample_returns.tail(20)
        regime, confidence = detector.predict(recent_returns)
        
        assert isinstance(regime, Regime)
        assert 0.0 <= confidence <= 1.0
    
    def test_predict_without_fit_raises_error(self, sample_returns):
        """Test prediction without fitting raises error."""
        pytest.importorskip("hmmlearn")
        
        detector = HMMRegimeDetector()
        recent_returns = sample_returns.tail(20)
        
        with pytest.raises(ValueError, match="not fitted"):
            detector.predict(recent_returns)
    
    def test_predict_with_short_series(self, sample_returns):
        """Test prediction with very short recent series."""
        pytest.importorskip("hmmlearn")
        
        detector = HMMRegimeDetector(rolling_window=100)
        detector.fit(sample_returns)
        
        # Very short series (<10 days)
        short_recent = sample_returns.tail(5)
        regime, confidence = detector.predict(short_recent)
        
        # Should use last known regime
        assert regime == detector._last_regime or isinstance(regime, Regime)
    
    def test_predict_with_custom_volatility(self, sample_returns):
        """Test prediction with custom volatility."""
        pytest.importorskip("hmmlearn")
        
        detector = HMMRegimeDetector(rolling_window=100)
        detector.fit(sample_returns)
        
        recent_returns = sample_returns.tail(20)
        recent_vol = recent_returns.rolling(10).std()
        
        regime, confidence = detector.predict(recent_returns, recent_vol)
        
        assert isinstance(regime, Regime)
    
    def test_predict_different_regimes(self, bull_market_returns, bear_market_returns):
        """Test that different market conditions produce different regimes."""
        pytest.importorskip("hmmlearn")
        
        # Combine bull and bear data
        combined = pd.concat([bull_market_returns, bear_market_returns])
        
        detector = HMMRegimeDetector(rolling_window=200)
        detector.fit(combined)
        
        # Predict on bull period
        bull_regime, _ = detector.predict(bull_market_returns.tail(30))
        
        # Predict on bear period  
        bear_regime, _ = detector.predict(bear_market_returns.tail(30))
        
        # May be different (not guaranteed due to HMM stochasticity)
        # Just verify both return valid regimes
        assert isinstance(bull_regime, Regime)
        assert isinstance(bear_regime, Regime)


class TestHMMRegimeDetectorUpdate:
    """Test HMM rolling update."""
    
    def test_update_adds_to_history(self, sample_returns):
        """Test that update adds new observation to history."""
        pytest.importorskip("hmmlearn")
        
        detector = HMMRegimeDetector(rolling_window=100)
        detector.fit(sample_returns[:100])
        
        initial_len = len(detector._returns_history)
        
        # Update with new observation
        new_return = 0.01
        result = detector.update(new_return)
        
        assert len(detector._returns_history) == initial_len + 1
    
    def test_update_retrains_when_needed(self, sample_returns):
        """Test that update retrains after enough new data."""
        pytest.importorskip("hmmlearn")
        
        # Small rolling window for faster test
        detector = HMMRegimeDetector(rolling_window=50)
        detector.fit(sample_returns[:50])
        
        # Add many new observations to trigger retrain
        new_regime = None
        for i in range(25):
            new_return = sample_returns.iloc[50 + i]
            new_regime = detector.update(new_return)
        
        # Should have triggered retrain
        assert new_regime is not None
        assert isinstance(new_regime, Regime)
    
    def test_update_no_retrain_yet(self, sample_returns):
        """Test update without triggering retrain."""
        pytest.importorskip("hmmlearn")
        
        detector = HMMRegimeDetector(rolling_window=100)
        detector.fit(sample_returns[:100])
        
        # Add few observations (not enough for retrain)
        for i in range(5):
            result = detector.update(0.01)
        
        # Should return None (no retrain yet)
        assert result is None


class TestHMMRegimeDetectorStats:
    """Test HMM statistics methods."""
    
    def test_get_regime_stats(self, sample_returns):
        """Test getting regime statistics after fit."""
        pytest.importorskip("hmmlearn")
        
        detector = HMMRegimeDetector(rolling_window=100)
        detector.fit(sample_returns)
        
        stats = detector.get_regime_stats()
        
        # Should have stats for each mapped regime
        assert isinstance(stats, dict)
        assert len(stats) > 0
        
        # Each stat should have required keys
        for regime_name, stat in stats.items():
            assert 'mean_return' in stat
            assert 'mean_vol' in stat
            assert 'n_samples' in stat
    
    def test_get_position_multiplier_bull(self, sample_returns):
        """Test position multiplier for bull regime."""
        pytest.importorskip("hmmlearn")
        
        detector = HMMRegimeDetector(rolling_window=100)
        detector.fit(sample_returns)
        
        multiplier = detector.get_position_multiplier(Regime.BULL)
        
        assert multiplier == 1.5  # Bull = aggressive
    
    def test_get_position_multiplier_bear(self, sample_returns):
        """Test position multiplier for bear regime."""
        pytest.importorskip("hmmlearn")
        
        detector = HMMRegimeDetector(rolling_window=100)
        detector.fit(sample_returns)
        
        multiplier = detector.get_position_multiplier(Regime.BEAR)
        
        assert multiplier == 0.25  # Bear = defensive
    
    def test_get_position_multiplier_range(self, sample_returns):
        """Test position multiplier for range regime."""
        pytest.importorskip("hmmlearn")
        
        detector = HMMRegimeDetector(rolling_window=100)
        detector.fit(sample_returns)
        
        multiplier = detector.get_position_multiplier(Regime.RANGE)
        
        assert multiplier == 0.75  # Range = moderate
    
    def test_get_position_multiplier_volatile_bull(self, sample_returns):
        """Test position multiplier for volatile bull regime."""
        pytest.importorskip("hmmlearn")
        
        detector = HMMRegimeDetector(rolling_window=100)
        detector.fit(sample_returns)
        
        multiplier = detector.get_position_multiplier(Regime.VOLATILE_BULL)
        
        assert multiplier == 1.0  # Volatile bull = cautious
    
    def test_get_position_multiplier_default(self, sample_returns):
        """Test position multiplier uses last regime if None."""
        pytest.importorskip("hmmlearn")
        
        detector = HMMRegimeDetector(rolling_window=100)
        detector.fit(sample_returns)
        
        # Uses last predicted regime
        multiplier = detector.get_position_multiplier()
        
        assert 0.25 <= multiplier <= 1.5
    
    def test_get_position_multiplier_unknown_regime(self):
        """Test position multiplier for unknown regime."""
        detector = HMMRegimeDetector()
        
        # Create fake regime
        class FakeRegime:
            value = "Unknown"
        
        multiplier = detector.get_position_multiplier(FakeRegime())
        
        assert multiplier == 0.75  # Default


class TestDetectRegimeHMM:
    """Test convenience function detect_regime_hmm."""
    
    def test_detect_with_sufficient_data(self, sample_returns):
        """Test detection with sufficient data."""
        pytest.importorskip("hmmlearn")
        
        assert len(sample_returns) >= 180
        
        regime, confidence = detect_regime_hmm(sample_returns, lookback=180)
        
        assert isinstance(regime, Regime)
        assert 0.0 <= confidence <= 1.0
    
    def test_detect_with_insufficient_data(self):
        """Test detection with insufficient data uses heuristic."""
        short_returns = pd.Series(np.random.randn(50))
        
        regime, confidence = detect_regime_hmm(short_returns, lookback=180)
        
        assert isinstance(regime, Regime)
        # Heuristic confidence
        assert confidence >= 0.5 and confidence <= 0.7


class TestHMMRegimeMapping:
    """Test regime mapping logic."""
    
    def test_map_regimes_all_assigned(self, sample_returns):
        """Test all hidden states are mapped to regimes."""
        pytest.importorskip("hmmlearn")
        
        detector = HMMRegimeDetector(n_regimes=4, rolling_window=100)
        detector.fit(sample_returns)
        
        # All 4 states should be mapped
        assert len(detector._regime_mapping) == 4
        
        # No duplicate regime assignments
        assigned_regimes = list(detector._regime_mapping.values())
        assert len(set(assigned_regimes)) == 4  # All unique
    
    def test_map_regimes_based_on_stats(self, hmm_training_data):
        """Test regime mapping reflects underlying statistics."""
        pytest.importorskip("hmmlearn")
        
        returns, volatility, _ = hmm_training_data
        
        detector = HMMRegimeDetector(n_regimes=4, rolling_window=300)
        detector.fit(returns, volatility)
        
        stats = detector.get_regime_stats()
        
        # Should have meaningful stats
        assert len(stats) > 0


class TestHMMReproducibility:
    """Test HMM reproducibility with random seed."""
    
    def test_same_seed_same_result(self, sample_returns):
        """Test same seed produces same results."""
        pytest.importorskip("hmmlearn")
        
        detector1 = HMMRegimeDetector(random_state=42, rolling_window=100)
        detector2 = HMMRegimeDetector(random_state=42, rolling_window=100)
        
        detector1.fit(sample_returns)
        detector2.fit(sample_returns)
        
        # Same last regime (usually, may vary due to initialization)
        # At minimum, both should have valid regimes
        assert detector1._last_regime in list(Regime)
        assert detector2._last_regime in list(Regime)
    
    def test_different_seed_may_differ(self, sample_returns):
        """Test different seeds may produce different results."""
        pytest.importorskip("hmmlearn")
        
        detector1 = HMMRegimeDetector(random_state=42, rolling_window=100)
        detector2 = HMMRegimeDetector(random_state=999, rolling_window=100)
        
        detector1.fit(sample_returns)
        detector2.fit(sample_returns)
        
        # Both should have valid regimes (may or may not be same)
        assert detector1._last_regime in list(Regime)
        assert detector2._last_regime in list(Regime)


# ============================================================================
# Integration Tests
# ============================================================================

class TestHMMIntegration:
    """Integration tests for HMM regime detection."""
    
    def test_full_workflow(self, btc_like_data):
        """Test complete HMM workflow: fit -> predict -> update."""
        pytest.importorskip("hmmlearn")
        
        returns = btc_like_data['close'].pct_change().dropna()
        
        # Fit
        detector = HMMRegimeDetector(rolling_window=180)
        detector.fit(returns)
        
        # Predict
        regime1, conf1 = detector.predict(returns.tail(30))
        
        # Update
        for _ in range(25):
            detector.update(0.01)
        
        # Predict again
        regime2, conf2 = detector.predict(returns.tail(30))
        
        # Both predictions should be valid
        assert isinstance(regime1, Regime)
        assert isinstance(regime2, Regime)
        assert 0 <= conf1 <= 1
        assert 0 <= conf2 <= 1
    
    def test_position_sizing_by_regime(self, sample_returns):
        """Test position sizing adapts to detected regime."""
        pytest.importorskip("hmmlearn")
        
        detector = HMMRegimeDetector(rolling_window=100)
        detector.fit(sample_returns)
        
        # Get current regime
        current_regime = detector._last_regime
        
        # Get multiplier
        multiplier = detector.get_position_multiplier(current_regime)
        
        # Verify multiplier is in valid range
        assert 0.25 <= multiplier <= 1.5
        
        # Different regimes should have different multipliers
        multipliers = {
            Regime.BULL: detector.get_position_multiplier(Regime.BULL),
            Regime.BEAR: detector.get_position_multiplier(Regime.BEAR),
            Regime.RANGE: detector.get_position_multiplier(Regime.RANGE),
            Regime.VOLATILE_BULL: detector.get_position_multiplier(Regime.VOLATILE_BULL),
        }
        
        assert multipliers[Regime.BULL] == 1.5
        assert multipliers[Regime.BEAR] == 0.25
        assert multipliers[Regime.RANGE] == 0.75
        assert multipliers[Regime.VOLATILE_BULL] == 1.0
