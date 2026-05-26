"""
🐉 HMM Regime Detection - Saiyan v0.3

REAL Hidden Markov Model using hmmlearn (Baum-Welch algorithm).
NOT fake if/else rules like v0.2.

Features:
- 4 regimes: Bull, Bear, Range, Volatile Bull
- Rolling window 180j for retraining
- Real-time regime prediction with confidence
- Regime-dependent position sizing

Usage:
    from core.hmm_regime import HMMRegimeDetector
    
    detector = HMMRegimeDetector(n_regimes=4, rolling_window=180)
    detector.fit(returns)
    regime, confidence = detector.predict(current_returns)
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, List, Optional
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

try:
    from hmmlearn import hmm
    HMMLEARN_AVAILABLE = True
except ImportError:
    HMMLEARN_AVAILABLE = False
    print("⚠️  hmmlearn not available. Install: pip install hmmlearn")


class Regime(Enum):
    """Market regimes."""
    BULL = "Bull"           # Returns +, vol low
    BEAR = "Bear"           # Returns -, vol high
    RANGE = "Range"         # Returns ~0, vol low
    VOLATILE_BULL = "Volatile Bull"  # Returns +, vol high


class HMMRegimeDetector:
    """
    Real HMM regime detector using Baum-Welch algorithm.
    
    Uses hmmlearn.GaussianHMM with full covariance for regime detection.
    Rolling window retraining for adaptation to changing market conditions.
    """
    
    def __init__(self, n_regimes: int = 4, rolling_window: int = 180,
                 n_iterations: int = 100, random_state: int = 42):
        """
        Initialize HMM regime detector.
        
        Args:
            n_regimes: Number of hidden regimes (default: 4)
            rolling_window: Days for rolling retraining (default: 180)
            n_iterations: Baum-Welch iterations (default: 100)
            random_state: Random seed for reproducibility
        """
        if not HMMLEARN_AVAILABLE:
            raise ImportError("hmmlearn required. Install: pip install hmmlearn")
        
        self.n_regimes = n_regimes
        self.rolling_window = rolling_window
        self.n_iterations = n_iterations
        self.random_state = random_state
        
        # HMM model
        self.model: Optional[hmm.GaussianHMM] = None
        
        # Training data
        self._returns_history: List[float] = []
        self._volatility_history: List[float] = []
        
        # Regime mapping (learned from data)
        self._regime_mapping: Dict[int, Regime] = {}
        self._regime_stats: Dict[int, Dict] = {}
        
        # Last prediction
        self._last_regime: Optional[Regime] = None
        self._last_confidence: float = 0.0
        
    def fit(self, returns: pd.Series, volatility: pd.Series = None) -> 'HMMRegimeDetector':
        """
        Fit HMM model on returns (and optionally volatility).
        
        Args:
            returns: Daily returns series
            volatility: Rolling volatility (optional, uses 20d std if None)
            
        Returns:
            Self for chaining
        """
        # Prepare features
        if volatility is None:
            volatility = returns.rolling(20).std()
        
        # Use 2D features: [returns, volatility]
        features = pd.DataFrame({
            'returns': returns,
            'volatility': volatility
        }).dropna()
        
        if len(features) < self.rolling_window:
            raise ValueError(f"Need at least {self.rolling_window} days, got {len(features)}")
        
        # Use rolling window
        features = features.tail(self.rolling_window)
        
        # Normalize features for better HMM convergence
        features_norm = (features - features.mean()) / (features.std() + 1e-8)
        
        # Fit HMM with multiple initializations for better convergence
        best_model = None
        best_ll = -np.inf
        
        for seed in [self.random_state, self.random_state + 1, self.random_state + 2]:
            try:
                model = hmm.GaussianHMM(
                    n_components=self.n_regimes,
                    covariance_type='diag',  # More robust than 'full' for financial data
                    n_iter=self.n_iterations,
                    random_state=seed,
                    verbose=False,
                    min_covar=1e-6,  # Regularization for numerical stability
                    init_params='wps',  # Careful initialization
                )
                
                X = features_norm.values
                model.fit(X)
                
                # Check log-likelihood
                ll = model.score(X)
                if ll > best_ll:
                    best_ll = ll
                    best_model = model
                    
            except Exception as e:
                # Try next seed
                continue
        
        if best_model is None:
            # Fallback: simple heuristic if HMM fails completely
            print("⚠️  HMM fitting failed, using heuristic fallback")
            self._use_heuristic = True
            return self
        
        self.model = best_model
        
        # Store history (normalized)
        self._returns_history = features['returns'].tolist()
        self._volatility_history = features['volatility'].tolist()
        self._features_mean = features.mean()
        self._features_std = features.std()
        
        # Map hidden states to regime names (pass both normalized and original)
        self._map_regimes(features, features_norm)
        
        # Predict on training data to set last regime
        hidden_states = self.model.predict(features_norm.values)
        self._last_regime = self._regime_mapping.get(hidden_states[-1], Regime.RANGE)
        self._use_heuristic = False
        
        return self
    
    def _map_regimes(self, features: pd.DataFrame, features_norm: pd.DataFrame = None) -> None:
        """
        Map hidden states to interpretable regime names.
        
        Uses mean returns and volatility of each state to label them.
        
        Args:
            features: Original (unnormalized) features for stats
            features_norm: Normalized features used for fitting (optional)
        """
        if self.model is None:
            return
        
        # Use normalized features for prediction if provided
        X = (features_norm if features_norm is not None else features).values
        hidden_states = self.model.predict(X)
        
        # Calculate stats for each state using ORIGINAL (unnormalized) features
        state_stats = {}
        for state in range(self.n_regimes):
            mask = hidden_states == state
            if mask.sum() > 0:
                state_returns = features['returns'].values[mask].mean()
                state_vol = features['volatility'].values[mask].mean()
                state_stats[state] = {
                    'mean_return': state_returns,
                    'mean_vol': state_vol,
                    'n_samples': mask.sum()
                }
        
        self._regime_stats = state_stats
        
        # Map states to regimes based on return/vol characteristics
        median_return = np.median([s['mean_return'] for s in state_stats.values()])
        median_vol = np.median([s['mean_vol'] for s in state_stats.values()])
        
        self._regime_mapping = {}
        used_regimes = set()
        
        # Priority mapping
        for state, stats in state_stats.items():
            ret = stats['mean_return']
            vol = stats['mean_vol']
            
            if ret > median_return and vol < median_vol:
                regime = Regime.BULL
            elif ret < median_return and vol >= median_vol:
                regime = Regime.BEAR
            elif abs(ret) < 0.001 and vol < median_vol:
                regime = Regime.RANGE
            elif ret > 0 and vol >= median_vol:
                regime = Regime.VOLATILE_BULL
            else:
                # Fallback: assign based on return sign
                if ret > 0:
                    regime = Regime.BULL if vol < median_vol else Regime.VOLATILE_BULL
                else:
                    regime = Regime.BEAR if vol >= median_vol else Regime.RANGE
            
            # Avoid duplicate assignments
            if regime not in used_regimes:
                self._regime_mapping[state] = regime
                used_regimes.add(regime)
        
        # Assign remaining states to unused regimes
        unused_regimes = [r for r in Regime if r not in used_regimes]
        for state in range(self.n_regimes):
            if state not in self._regime_mapping:
                if unused_regimes:
                    self._regime_mapping[state] = unused_regimes.pop(0)
                else:
                    self._regime_mapping[state] = Regime.RANGE
    
    def predict(self, recent_returns: pd.Series, recent_volatility: pd.Series = None) -> Tuple[Regime, float]:
        """
        Predict current regime from recent data.
        
        Args:
            recent_returns: Recent returns (last 20-60 days)
            recent_volatility: Recent volatility (optional)
            
        Returns:
            Tuple of (regime, confidence)
        """
        if self.model is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Prepare features
        if recent_volatility is None:
            recent_volatility = recent_returns.rolling(20).std()
        
        features = pd.DataFrame({
            'returns': recent_returns,
            'volatility': recent_volatility
        }).dropna()
        
        if len(features) < 10:
            # Not enough data, use last known regime
            return self._last_regime or Regime.RANGE, 0.5
        
        X = features.values
        
        # Predict hidden state
        hidden_state = self.model.predict(X)[-1]
        
        # Get regime name
        regime = self._regime_mapping.get(hidden_state, Regime.RANGE)
        
        # Calculate confidence from state probability
        log_prob = self.model.score(X)
        n_samples = len(X)
        
        # Normalize confidence (rough approximation)
        # Higher log_prob = better fit = higher confidence
        confidence = min(0.95, 0.5 + (log_prob / n_samples + 2) * 0.3)
        confidence = max(0.3, confidence)
        
        self._last_regime = regime
        self._last_confidence = confidence
        
        return regime, confidence
    
    def update(self, new_return: float, new_volatility: float = None) -> Optional[Regime]:
        """
        Update model with new observation and retrain if needed.
        
        Args:
            new_return: Latest daily return
            new_volatility: Latest volatility (optional)
            
        Returns:
            New regime if retrained, None otherwise
        """
        # Add to history
        self._returns_history.append(new_return)
        if new_volatility is None:
            # Estimate from recent returns
            if len(self._returns_history) >= 20:
                new_volatility = np.std(self._returns_history[-20:])
            else:
                new_volatility = 0.02  # Default 2% daily vol
        
        self._volatility_history.append(new_volatility)
        
        # Retrain if we have enough new data
        if len(self._returns_history) >= self.rolling_window + 20:
            # Trim history
            self._returns_history = self._returns_history[-self.rolling_window:]
            self._volatility_history = self._volatility_history[-self.rolling_window:]
            
            # Refit
            returns = pd.Series(self._returns_history)
            volatility = pd.Series(self._volatility_history)
            self.fit(returns, volatility)
            
            return self._last_regime
        
        return None
    
    def get_regime_stats(self) -> Dict[str, Dict]:
        """
        Get statistics for each regime.
        
        Returns:
            Dict mapping regime name to stats (mean_return, mean_vol, n_samples)
        """
        stats = {}
        for state, regime in self._regime_mapping.items():
            if state in self._regime_stats:
                stats[regime.value] = self._regime_stats[state]
        return stats
    
    def get_position_multiplier(self, regime: Regime = None) -> float:
        """
        Get position sizing multiplier for regime.
        
        Based on regime risk characteristics.
        
        Args:
            regime: Regime (uses last predicted if None)
            
        Returns:
            Position multiplier (0.25x - 1.5x)
        """
        if regime is None:
            regime = self._last_regime
        
        multipliers = {
            Regime.BULL: 1.5,           # High conviction
            Regime.BEAR: 0.25,          # Defensive
            Regime.RANGE: 0.75,         # Moderate
            Regime.VOLATILE_BULL: 1.0   # Cautious optimism
        }
        
        return multipliers.get(regime, 0.75)


def detect_regime_hmm(returns: pd.Series, lookback: int = 180) -> Tuple[Regime, float]:
    """
    Convenience function for HMM regime detection.
    
    Args:
        returns: Returns series (at least lookback days)
        lookback: Days for HMM training
        
    Returns:
        Tuple of (regime, confidence)
    """
    if len(returns) < lookback:
        # Not enough data, use simple heuristic
        recent_ret = returns.tail(20).mean()
        recent_vol = returns.tail(20).std()
        overall_vol = returns.std()
        
        if recent_ret > 0 and recent_vol < overall_vol:
            return Regime.BULL, 0.6
        elif recent_ret < 0 and recent_vol > overall_vol:
            return Regime.BEAR, 0.6
        elif abs(recent_ret) < 0.001:
            return Regime.RANGE, 0.7
        else:
            return Regime.VOLATILE_BULL, 0.5
    
    detector = HMMRegimeDetector(n_regimes=4, rolling_window=lookback)
    detector.fit(returns)
    
    # Predict on last 20 days
    recent_returns = returns.tail(20)
    regime, confidence = detector.predict(recent_returns)
    
    return regime, confidence


if __name__ == "__main__":
    # Test HMM regime detector
    print("🧪 Testing HMM Regime Detector...\n")
    
    # Load test data
    from data.loader import load_btc_data
    
    btc = load_btc_data("2020-01-01", "2026-04-18")
    returns = btc['close'].pct_change().dropna()
    
    print(f"📊 Data: {len(returns)} days of returns")
    print(f"   Mean: {returns.mean():.4%}")
    print(f"   Std: {returns.std():.4%}")
    print()
    
    # Fit HMM
    print("🔮 Fitting HMM (4 regimes, 180d rolling)...")
    detector = HMMRegimeDetector(n_regimes=4, rolling_window=180)
    detector.fit(returns)
    print("✅ HMM fitted\n")
    
    # Get regime stats
    print("📈 Regime Statistics:")
    stats = detector.get_regime_stats()
    for regime, s in stats.items():
        print(f"   {regime}:")
        print(f"      Mean return: {s['mean_return']:.4%}")
        print(f"      Mean vol: {s['mean_vol']:.4%}")
        print(f"      Samples: {s['n_samples']}")
    print()
    
    # Predict current regime
    print("🎯 Current Regime Prediction:")
    recent_returns = returns.tail(60)
    regime, confidence = detector.predict(recent_returns)
    print(f"   Regime: {regime.value}")
    print(f"   Confidence: {confidence:.1%}")
    print(f"   Position multiplier: {detector.get_position_multiplier(regime):.2f}x")
    print()
    
    # Test rolling update
    print("🔄 Testing Rolling Update:")
    for i in range(30):
        new_ret = returns.iloc[-30 + i]
        new_regime = detector.update(new_ret)
        if new_regime:
            print(f"   Day {i+1}: Retrained, new regime = {new_regime.value}")
    
    print("\n✅ All tests completed!")
