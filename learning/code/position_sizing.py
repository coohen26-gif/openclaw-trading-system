#!/usr/bin/env python3
"""
Position Sizing - Kelly Criterion with HMM Regime Detection

Module: Phase 2 - Risk Management Core
Author: Saiyan Autonomous Trading System
Date: May 24, 2026

Features:
- Kelly Criterion (full and fractional)
- HMM regime-dependent position sizing
- Risk Parity allocation
- Drawdown-based constraints
- Volatility-adjusted sizing
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Optional imports
try:
    from hmmlearn import hmm
    HAS_HMM = True
except ImportError:
    HAS_HMM = False
    print("⚠️  hmmlearn not available - HMM features disabled")

try:
    import cvxpy as cp
    HAS_CVXPY = True
except ImportError:
    HAS_CVXPY = False
    print("⚠️  cvxpy not available - Risk Parity optimization disabled")


class MarketRegime(Enum):
    """Market regime classification"""
    BULL = "bull"  # Low vol, positive returns
    BEAR = "bear"  # High vol, negative returns
    RANGE = "range"  # Low vol, neutral returns
    VOLATILE = "volatile"  # High vol, mixed returns


@dataclass
class PositionSizeResult:
    """Result of position sizing calculation"""
    recommended_size: float
    kelly_fraction: float
    regime: MarketRegime
    confidence: float
    constraints_applied: List[str]
    risk_adjusted: bool
    timestamp: datetime


class KellyPositionSizer:
    """
    Kelly Criterion-based position sizing with fractional Kelly and constraints.
    
    The Kelly Criterion maximizes expected logarithmic wealth growth:
    f* = (p * b - q) / b
    
    Where:
    - p = probability of winning
    - q = probability of losing (1 - p)
    - b = odds received (payoff ratio)
    
    For continuous returns:
    f* = μ / σ²
    
    Where:
    - μ = expected return
    - σ² = variance of returns
    """
    
    def __init__(
        self,
        kelly_fraction: float = 0.25,  # Quarter-Kelly by default
        max_position: float = 0.30,    # Max 30% per position
        min_position: float = 0.01,    # Min 1% per position
        max_drawdown_limit: float = 0.20,  # Stop at 20% DD
        current_drawdown: float = 0.0
    ):
        """
        Initialize Kelly position sizer.
        
        Args:
            kelly_fraction: Fraction of Kelly to use (0.25 = quarter-Kelly)
            max_position: Maximum position size as fraction of portfolio
            min_position: Minimum position size
            max_drawdown_limit: Maximum drawdown before stopping
            current_drawdown: Current drawdown from peak
        """
        self.kelly_fraction = kelly_fraction
        self.max_position = max_position
        self.min_position = min_position
        self.max_drawdown_limit = max_drawdown_limit
        self.current_drawdown = current_drawdown
        
        print(f"📊 Kelly Position Sizer initialized")
        print(f"   Kelly fraction: {kelly_fraction*100:.0f}% ({self._fraction_name()})")
        print(f"   Position limits: [{min_position*100:.0f}%, {max_position*100:.0f}%]")
        print(f"   Max drawdown limit: {max_drawdown_limit*100:.0f}%")
    
    def _fraction_name(self) -> str:
        """Get name for Kelly fraction"""
        if self.kelly_fraction >= 1.0:
            return "Full Kelly"
        elif self.kelly_fraction >= 0.5:
            return "Half-Kelly"
        elif self.kelly_fraction >= 0.25:
            return "Quarter-Kelly"
        else:
            return f"{self.kelly_fraction*100:.0f}%-Kelly"
    
    def calculate_kelly(
        self,
        expected_return: float,
        volatility: float,
        win_rate: Optional[float] = None,
        payoff_ratio: Optional[float] = None
    ) -> float:
        """
        Calculate Kelly fraction.
        
        Args:
            expected_return: Expected return (annualized or per-period)
            volatility: Volatility (same period as expected_return)
            win_rate: Probability of winning (optional, for discrete Kelly)
            payoff_ratio: Payoff ratio (optional, for discrete Kelly)
            
        Returns:
            Kelly fraction (before applying constraints)
        """
        # If we have discrete trade stats, use discrete Kelly
        if win_rate is not None and payoff_ratio is not None:
            p = win_rate
            q = 1 - p
            b = payoff_ratio
            
            if b == 0:
                return 0.0
            
            kelly = (p * b - q) / b
        else:
            # Continuous Kelly: f* = μ / σ²
            if volatility == 0:
                return 0.0
            
            kelly = expected_return / (volatility ** 2)
        
        return kelly
    
    def apply_constraints(self, kelly_fraction: float) -> Tuple[float, List[str]]:
        """
        Apply practical constraints to Kelly fraction.
        
        Args:
            kelly_fraction: Raw Kelly fraction
            
        Returns:
            Tuple of (constrained_fraction, list of constraints applied)
        """
        constraints = []
        constrained = kelly_fraction * self.kelly_fraction  # Apply fractional Kelly
        
        # No negative positions (no shorting for now)
        if constrained < 0:
            constrained = 0.0
            constraints.append("No shorting")
        
        # Apply drawdown constraint
        if self.current_drawdown < -self.max_drawdown_limit:
            constrained = 0.0
            constraints.append(f"Max drawdown exceeded ({self.current_drawdown*100:.1f}% < {-self.max_drawdown_limit*100:.0f}%)")
        elif self.current_drawdown < -self.max_drawdown_limit * 0.5:
            # Reduce by 50% when approaching max DD
            constrained *= 0.5
            constraints.append(f"Approaching max drawdown - reduced 50%")
        
        # Apply max position limit
        if constrained > self.max_position:
            old = constrained
            constrained = self.max_position
            constraints.append(f"Max position cap ({self.max_position*100:.0f}%)")
        
        # Apply min position limit (or zero)
        if 0 < constrained < self.min_position:
            constrained = 0.0
            constraints.append(f"Below minimum ({self.min_position*100:.0f}%) → 0%")
        
        return constrained, constraints
    
    def calculate_position(
        self,
        portfolio_value: float,
        expected_return: float,
        volatility: float,
        win_rate: Optional[float] = None,
        payoff_ratio: Optional[float] = None,
        price: Optional[float] = None
    ) -> PositionSizeResult:
        """
        Calculate position size with all constraints.
        
        Args:
            portfolio_value: Total portfolio value
            expected_return: Expected return
            volatility: Volatility
            win_rate: Win rate (optional)
            payoff_ratio: Payoff ratio (optional)
            price: Asset price (optional, for share calculation)
            
        Returns:
            PositionSizeResult with all details
        """
        # Calculate raw Kelly
        kelly = self.calculate_kelly(expected_return, volatility, win_rate, payoff_ratio)
        
        # Apply constraints
        constrained, constraints = self.apply_constraints(kelly)
        
        # Calculate dollar amount
        dollar_size = portfolio_value * constrained
        
        # Calculate shares if price provided
        shares = dollar_size / price if price and price > 0 else None
        
        return PositionSizeResult(
            recommended_size=dollar_size,
            kelly_fraction=constrained,
            regime=MarketRegime.RANGE,  # Default, overridden by HMM sizer
            confidence=1.0,  # Default
            constraints_applied=constraints,
            risk_adjusted=True,
            timestamp=datetime.now()
        )
    
    def update_drawdown(self, current_drawdown: float):
        """Update current drawdown"""
        self.current_drawdown = current_drawdown
        if current_drawdown < -self.max_drawdown_limit:
            print(f"🚨 WARNING: Drawdown {current_drawdown*100:.1f}% exceeds limit {-self.max_drawdown_limit*100:.0f}%")


class HMMRegimePositionSizer:
    """
    HMM Regime-dependent position sizing.
    
    Uses Hidden Markov Models to detect market regimes and adjust
    position sizes accordingly:
    - Bull: Higher positions (confidence high)
    - Bear: Lower positions or short
    - Range: Medium positions, mean-reversion strategies
    - Volatile: Reduced positions (risk management)
    """
    
    def __init__(
        self,
        n_regimes: int = 4,
        kelly_base: float = 0.25
    ):
        """
        Initialize HMM regime position sizer.
        
        Args:
            n_regimes: Number of hidden states
            kelly_base: Base Kelly fraction
        """
        self.n_regimes = n_regimes
        self.kelly_base = kelly_base
        self.model = None
        self.regime_mapping = None
        
        # Regime-specific Kelly multipliers
        self.regime_multipliers = {
            MarketRegime.BULL: 1.5,      # More aggressive in bull
            MarketRegime.BEAR: 0.25,     # Very conservative in bear
            MarketRegime.RANGE: 0.75,    # Moderate in ranging
            MarketRegime.VOLATILE: 0.5   # Reduced in volatile
        }
        
        if not HAS_HMM:
            print("⚠️  HMM features disabled (hmmlearn not available)")
        else:
            print(f"🔮 HMM Regime Sizer initialized ({n_regimes} regimes)")
    
    def fit(self, returns: np.ndarray, n_iterations: int = 100):
        """
        Fit HMM model to returns.
        
        Args:
            returns: Array of returns
            n_iterations: Number of EM iterations
        """
        if not HAS_HMM:
            print("⚠️  Cannot fit HMM: hmmlearn not available")
            return
        
        # Reshape for hmmlearn
        returns_reshaped = returns.reshape(-1, 1)
        
        # Create Gaussian HMM
        self.model = hmm.GaussianHMM(
            n_components=self.n_regimes,
            covariance_type="full",
            n_iter=n_iterations,
            random_state=42
        )
        
        # Fit model
        self.model.fit(returns_reshaped)
        
        # Predict regimes
        hidden_states = self.model.predict(returns_reshaped)
        
        # Map states to regimes based on mean/vol characteristics
        self._map_regimes(returns, hidden_states)
        
        print(f"✅ HMM model fitted ({n_iterations} iterations)")
        self._print_regime_characteristics(returns, hidden_states)
    
    def _map_regimes(self, returns: np.ndarray, hidden_states: np.ndarray):
        """
        Map hidden states to interpretable regimes.
        
        Args:
            returns: Original returns
            hidden_states: Predicted hidden states
        """
        regime_stats = {}
        
        for state in range(self.n_regimes):
            mask = hidden_states == state
            state_returns = returns[mask]
            
            if len(state_returns) > 0:
                mean = np.mean(state_returns)
                std = np.std(state_returns)
                regime_stats[state] = {
                    'mean': mean,
                    'std': std,
                    'count': len(state_returns),
                    'pct': len(state_returns) / len(returns) * 100
                }
        
        # Simple heuristic mapping
        # Sort by mean return
        sorted_states = sorted(regime_stats.items(), key=lambda x: x[1]['mean'], reverse=True)
        
        self.regime_mapping = {}
        
        if self.n_regimes >= 4:
            # 4 regimes: Bull, Range, Volatile, Bear
            self.regime_mapping[sorted_states[0][0]] = MarketRegime.BULL
            self.regime_mapping[sorted_states[1][0]] = MarketRegime.RANGE
            self.regime_mapping[sorted_states[2][0]] = MarketRegime.VOLATILE
            self.regime_mapping[sorted_states[3][0]] = MarketRegime.BEAR
        elif self.n_regimes == 3:
            # 3 regimes: Bull, Range, Bear
            self.regime_mapping[sorted_states[0][0]] = MarketRegime.BULL
            self.regime_mapping[sorted_states[1][0]] = MarketRegime.RANGE
            self.regime_mapping[sorted_states[2][0]] = MarketRegime.BEAR
        else:
            # 2 regimes: Bull, Bear
            self.regime_mapping[sorted_states[0][0]] = MarketRegime.BULL
            self.regime_mapping[sorted_states[1][0]] = MarketRegime.BEAR
    
    def _print_regime_characteristics(self, returns: np.ndarray, hidden_states: np.ndarray):
        """Print regime characteristics"""
        print("\n📊 Regime Characteristics:")
        print("-" * 60)
        
        for state in range(self.n_regimes):
            mask = hidden_states == state
            state_returns = returns[mask]
            
            if len(state_returns) > 0:
                regime = self.regime_mapping.get(state, MarketRegime.RANGE)
                mean = np.mean(state_returns) * 100
                std = np.std(state_returns) * 100
                pct = len(state_returns) / len(returns) * 100
                
                print(f"  State {state} → {regime.value.upper()}")
                print(f"    Mean: {mean:+.2f}% | Std: {std:.2f}% | Occurrence: {pct:.1f}%")
        
        print("-" * 60)
    
    def get_current_regime(self, returns: np.ndarray, lookback: int = 20) -> Tuple[MarketRegime, float]:
        """
        Get current market regime.
        
        Args:
            returns: Full returns series
            lookback: Lookback window for current regime
            
        Returns:
            Tuple of (regime, confidence)
        """
        if self.model is None:
            return MarketRegime.RANGE, 0.5
        
        # Use recent returns
        recent = returns[-lookback:].reshape(-1, 1)
        
        # Predict regime
        recent_states = self.model.predict(recent)
        
        # Most recent state
        current_state = recent_states[-1]
        
        # Confidence = proportion of recent period in this state
        confidence = np.sum(recent_states == current_state) / len(recent_states)
        
        regime = self.regime_mapping.get(current_state, MarketRegime.RANGE)
        
        return regime, confidence
    
    def calculate_regime_adjusted_kelly(
        self,
        base_kelly: float,
        regime: MarketRegime
    ) -> float:
        """
        Calculate regime-adjusted Kelly fraction.
        
        Args:
            base_kelly: Base Kelly fraction
            regime: Current market regime
            
        Returns:
            Regime-adjusted Kelly fraction
        """
        multiplier = self.regime_multipliers.get(regime, 1.0)
        return base_kelly * multiplier
    
    def calculate_position(
        self,
        portfolio_value: float,
        returns: np.ndarray,
        expected_return: float,
        volatility: float,
        lookback: int = 20
    ) -> PositionSizeResult:
        """
        Calculate HMM regime-adjusted position size.
        
        Args:
            portfolio_value: Portfolio value
            returns: Returns series for HMM
            expected_return: Expected return
            volatility: Volatility
            lookback: Lookback for regime detection
            
        Returns:
            PositionSizeResult
        """
        if self.model is None:
            # Fall back to base Kelly if HMM not fitted
            base_kelly = expected_return / (volatility ** 2) if volatility > 0 else 0
            return PositionSizeResult(
                recommended_size=portfolio_value * base_kelly * self.kelly_base,
                kelly_fraction=base_kelly * self.kelly_base,
                regime=MarketRegime.RANGE,
                confidence=0.5,
                constraints_applied=["HMM not fitted"],
                risk_adjusted=False,
                timestamp=datetime.now()
            )
        
        # Get current regime
        regime, confidence = self.get_current_regime(returns, lookback)
        
        # Calculate base Kelly
        base_kelly = expected_return / (volatility ** 2) if volatility > 0 else 0
        
        # Apply regime adjustment
        regime_kelly = self.calculate_regime_adjusted_kelly(base_kelly, regime)
        
        # Apply base Kelly fraction
        final_kelly = regime_kelly * self.kelly_base
        
        # Apply constraints
        final_kelly = max(0, min(final_kelly, 0.30))  # Max 30%
        
        dollar_size = portfolio_value * final_kelly
        
        return PositionSizeResult(
            recommended_size=dollar_size,
            kelly_fraction=final_kelly,
            regime=regime,
            confidence=confidence,
            constraints_applied=[f"Regime: {regime.value}"],
            risk_adjusted=True,
            timestamp=datetime.now()
        )


class RiskParityAllocator:
    """
    Risk Parity portfolio allocation.
    
    Equalizes risk contributions from each asset rather than
    equalizing capital allocation.
    """
    
    def __init__(self, n_assets: int = 3):
        """
        Initialize Risk Parity allocator.
        
        Args:
            n_assets: Number of assets in portfolio
        """
        self.n_assets = n_assets
        
        if HAS_CVXPY:
            print(f"📊 Risk Parity Allocator initialized ({n_assets} assets)")
        else:
            print("⚠️  Risk Parity optimization disabled (cvxpy not available)")
    
    def calculate_risk_parity_weights(
        self,
        returns_matrix: np.ndarray,
        target_risk: Optional[float] = None
    ) -> np.ndarray:
        """
        Calculate Risk Parity weights.
        
        Args:
            returns_matrix: T x N matrix of returns (T periods, N assets)
            target_risk: Target portfolio volatility (optional)
            
        Returns:
            Array of weights summing to 1
        """
        if not HAS_CVXPY:
            # Fall back to equal weight
            print("⚠️  CVXPY not available, using equal weights")
            return np.ones(self.n_assets) / self.n_assets
        
        n_assets = returns_matrix.shape[1]
        
        # Calculate covariance matrix
        cov_matrix = np.cov(returns_matrix.T)
        
        # Use coordinate descent for Risk Parity (simpler, more robust)
        weights = self._risk_parity_coordinate_descent(cov_matrix, n_assets)
        
        return weights
    
    def _risk_parity_coordinate_descent(
        self, cov_matrix: np.ndarray, n_assets: int, max_iter: int = 100, tol: float = 1e-6
    ) -> np.ndarray:
        """
        Calculate Risk Parity weights using coordinate descent.
        
        This is a simpler, guaranteed-convergent algorithm.
        
        Args:
            cov_matrix: Covariance matrix
            n_assets: Number of assets
            max_iter: Maximum iterations
            tol: Convergence tolerance
            
        Returns:
            Risk parity weights
        """
        # Initialize with equal weights
        w = np.ones(n_assets) / n_assets
        
        for iteration in range(max_iter):
            w_old = w.copy()
            
            # Update each weight
            for i in range(n_assets):
                # Marginal risk contribution
                marginal = cov_matrix[i, :] @ w
                
                # Portfolio variance
                port_var = w @ cov_matrix @ w
                
                if port_var > 0 and marginal > 0:
                    # Target: equal risk contribution
                    # w_i * marginal_i = port_var / n_assets
                    w[i] = (port_var / n_assets) / marginal
            
            # Normalize
            w = np.maximum(w, 0)  # Ensure non-negative
            if w.sum() > 0:
                w = w / w.sum()
            
            # Check convergence
            if np.max(np.abs(w - w_old)) < tol:
                break
        
        return w
    
    def allocate(
        self,
        portfolio_value: float,
        returns_matrix: np.ndarray,
        prices: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        Allocate portfolio using Risk Parity.
        
        Args:
            portfolio_value: Total portfolio value
            returns_matrix: Historical returns matrix
            prices: Current prices (optional)
            
        Returns:
            Dict with allocation details
        """
        weights = self.calculate_risk_parity_weights(returns_matrix)
        
        allocation = {
            'weights': weights,
            'values': weights * portfolio_value,
            'portfolio_value': portfolio_value
        }
        
        if prices is not None:
            allocation['shares'] = allocation['values'] / prices
        
        return allocation


def test_position_sizing():
    """Test position sizing modules"""
    print("🧪 Testing Position Sizing Modules...\n")
    
    # Test 1: Kelly Criterion
    print("="*60)
    print("📊 TEST 1: Kelly Criterion")
    print("="*60)
    
    kelly_sizer = KellyPositionSizer(
        kelly_fraction=0.25,  # Quarter-Kelly
        max_position=0.30,
        min_position=0.01
    )
    
    # Example: BTC with 50% annual return, 80% annual vol
    annual_return = 0.50
    annual_vol = 0.80
    
    # Convert to daily (assuming 365 days)
    daily_return = annual_return / 365
    daily_vol = annual_vol / np.sqrt(365)
    
    kelly = kelly_sizer.calculate_kelly(daily_return, daily_vol)
    print(f"\n📈 BTC Example:")
    print(f"   Annual return: {annual_return*100:.0f}%")
    print(f"   Annual vol: {annual_vol*100:.0f}%")
    print(f"   Daily return: {daily_return*100:.3f}%")
    print(f"   Daily vol: {daily_vol*100:.2f}%")
    print(f"   Raw Kelly: {kelly*100:.2f}%")
    
    constrained, constraints = kelly_sizer.apply_constraints(kelly)
    print(f"   Constrained: {constrained*100:.2f}%")
    if constraints:
        print(f"   Constraints: {', '.join(constraints)}")
    
    # Full position calculation
    result = kelly_sizer.calculate_position(
        portfolio_value=10000,
        expected_return=daily_return,
        volatility=daily_vol
    )
    print(f"\n💰 Position for $10,000 portfolio:")
    print(f"   Size: ${result.recommended_size:,.2f}")
    print(f"   Kelly fraction: {result.kelly_fraction*100:.2f}%")
    
    # Test 2: HMM Regime Sizer
    print("\n" + "="*60)
    print("🔮 TEST 2: HMM Regime Position Sizer")
    print("="*60)
    
    if HAS_HMM:
        hmm_sizer = HMMRegimePositionSizer(n_regimes=4, kelly_base=0.25)
        
        # Generate synthetic returns with regime changes
        np.random.seed(42)
        n = 500
        
        # Bull market (first 150)
        bull_returns = np.random.normal(0.002, 0.02, 150)
        # Bear market (next 100)
        bear_returns = np.random.normal(-0.003, 0.04, 100)
        # Range (next 150)
        range_returns = np.random.normal(0.0005, 0.015, 150)
        # Volatile (last 100)
        volatile_returns = np.random.normal(0.001, 0.05, 100)
        
        all_returns = np.concatenate([bull_returns, bear_returns, range_returns, volatile_returns])
        
        # Fit HMM
        hmm_sizer.fit(all_returns)
        
        # Get current regime (should be volatile)
        regime, confidence = hmm_sizer.get_current_regime(all_returns)
        print(f"\n📊 Current Regime: {regime.value.upper()} (confidence: {confidence*100:.1f}%)")
        
        # Calculate position
        result = hmm_sizer.calculate_position(
            portfolio_value=10000,
            returns=all_returns,
            expected_return=np.mean(all_returns),
            volatility=np.std(all_returns)
        )
        print(f"\n💰 HMM-Adjusted Position:")
        print(f"   Size: ${result.recommended_size:,.2f}")
        print(f"   Kelly fraction: {result.kelly_fraction*100:.2f}%")
        print(f"   Regime: {result.regime.value}")
    else:
        print("⚠️  Skipped (hmmlearn not available)")
    
    # Test 3: Risk Parity
    print("\n" + "="*60)
    print("📊 TEST 3: Risk Parity Allocation")
    print("="*60)
    
    if HAS_CVXPY:
        rp_allocator = RiskParityAllocator(n_assets=3)
        
        # Generate correlated returns for BTC, ETH, SOL
        np.random.seed(42)
        n = 252  # 1 year daily
        
        # Correlated returns (crypto typically 0.7-0.8 correlation)
        base = np.random.normal(0, 0.03, n)
        btc_returns = base * 0.8 + np.random.normal(0, 0.02, n)
        eth_returns = base * 0.85 + np.random.normal(0, 0.025, n)
        sol_returns = base * 0.75 + np.random.normal(0, 0.04, n)
        
        returns_matrix = np.column_stack([btc_returns, eth_returns, sol_returns])
        
        # Calculate weights
        weights = rp_allocator.calculate_risk_parity_weights(returns_matrix)
        
        print(f"\n📊 Risk Parity Weights:")
        print(f"   BTC: {weights[0]*100:.1f}%")
        print(f"   ETH: {weights[1]*100:.1f}%")
        print(f"   SOL: {weights[2]*100:.1f}%")
        
        # Allocate
        allocation = rp_allocator.allocate(10000, returns_matrix)
        print(f"\n💰 Allocation for $10,000:")
        print(f"   BTC: ${allocation['values'][0]:,.2f}")
        print(f"   ETH: ${allocation['values'][1]:,.2f}")
        print(f"   SOL: ${allocation['values'][2]:,.2f}")
    else:
        print("⚠️  Skipped (cvxpy not available)")
    
    print("\n✅ Position Sizing tests complete!")


if __name__ == "__main__":
    test_position_sizing()
