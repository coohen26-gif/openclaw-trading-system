#!/usr/bin/env python3
"""
HMM Advanced - Regime-Dependent Trading Strategies

Module: Phase 2 - HMM Integration Avancée (Semaine 28)
Author: Saiyan Autonomous Trading System
Date: May 24, 2026

Features:
- HMM 4 états (Bull, Bear, Range, Volatile Bull)
- Regime-dependent position sizing
- Regime-dependent strategy selection
- Backtest par régime
- Real-time regime detection
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
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
    import ccxt
    HAS_CCXT = True
except ImportError:
    HAS_CCXT = False


class MarketRegime(Enum):
    """Market regime classification (4 states)"""
    BULL = "bull"  # Low vol, positive returns
    BEAR = "bear"  # High vol, negative returns
    RANGE = "range"  # Low vol, neutral returns
    VOLATILE_BULL = "volatile_bull"  # High vol, positive returns


@dataclass
class RegimeCharacteristics:
    """Characteristics of a market regime"""
    mean_return: float
    volatility: float
    sharpe: float
    occurrence_pct: float
    avg_duration_days: int


@dataclass
class RegimeStrategy:
    """Strategy parameters for a specific regime"""
    regime: MarketRegime
    position_size: float  # Kelly multiplier
    strategy_type: str  # e.g., "momentum", "mean_reversion", "breakout"
    stop_loss: float
    take_profit: float
    max_holding_period: int
    description: str


class AdvancedHMM:
    """
    Advanced HMM with 4 regimes and regime-dependent strategies.
    
    Extends basic HMM with:
    - 4th state: Volatile Bull (high vol, positive returns)
    - Regime persistence analysis
    - Strategy mapping per regime
    - Real-time regime detection
    """
    
    def __init__(self, n_regimes: int = 4, lookback_days: int = 60):
        """
        Initialize advanced HMM.
        
        Args:
            n_regimes: Number of hidden states (4 recommended)
            lookback_days: Days of data for regime detection
        """
        self.n_regimes = n_regimes
        self.lookback_days = lookback_days
        self.model = None
        self.regime_mapping = None
        self.returns_history = None
        
        # Regime strategies (customizable)
        self.strategies = self._default_strategies()
        
        if not HAS_HMM:
            print("⚠️  HMM features disabled (hmmlearn not available)")
        else:
            print(f"🔮 Advanced HMM initialized ({n_regimes} regimes, {lookback_days}d lookback)")
    
    def _default_strategies(self) -> Dict[MarketRegime, RegimeStrategy]:
        """Define default strategies per regime"""
        return {
            MarketRegime.BULL: RegimeStrategy(
                regime=MarketRegime.BULL,
                position_size=1.5,  # Aggressive (1.5x Kelly)
                strategy_type="momentum",
                stop_loss=-0.08,
                take_profit=0.15,
                max_holding_period=10,
                description="Trend following, let winners run"
            ),
            MarketRegime.BEAR: RegimeStrategy(
                regime=MarketRegime.BEAR,
                position_size=0.25,  # Very conservative
                strategy_type="mean_reversion",
                stop_loss=-0.05,
                take_profit=0.08,
                max_holding_period=3,
                description="Counter-trend bounces only, quick exits"
            ),
            MarketRegime.RANGE: RegimeStrategy(
                regime=MarketRegime.RANGE,
                position_size=0.75,  # Moderate
                strategy_type="mean_reversion",
                stop_loss=-0.04,
                take_profit=0.06,
                max_holding_period=5,
                description="Buy dips, sell rips, range trading"
            ),
            MarketRegime.VOLATILE_BULL: RegimeStrategy(
                regime=MarketRegime.VOLATILE_BULL,
                position_size=1.0,  # Moderate (vol reduces size)
                strategy_type="breakout",
                stop_loss=-0.10,
                take_profit=0.20,
                max_holding_period=7,
                description="Ride momentum but wide stops for vol"
            )
        }
    
    def fit(self, returns: np.ndarray, n_iterations: int = 200) -> bool:
        """
        Fit HMM model to returns.
        
        Args:
            returns: Array of returns
            n_iterations: Number of EM iterations
            
        Returns:
            True if successful
        """
        if not HAS_HMM:
            return False
        
        if len(returns) < self.lookback_days:
            print(f"⚠️  Insufficient data: {len(returns)} < {self.lookback_days} days")
            return False
        
        # Reshape for hmmlearn
        returns_reshaped = returns[-self.lookback_days:].reshape(-1, 1)
        self.returns_history = returns[-self.lookback_days:]
        
        # Create Gaussian HMM (use 'diag' for numerical stability)
        self.model = hmm.GaussianHMM(
            n_components=self.n_regimes,
            covariance_type="diag",  # More stable than 'full'
            n_iter=n_iterations,
            random_state=42,
            tol=1e-4,
            min_covar=1e-6  # Prevent numerical issues
        )
        
        # Clean data (remove NaN/Inf)
        returns_clean = np.nan_to_num(returns_reshaped, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Fit model
        self.model.fit(returns_clean)
        
        # Predict regimes
        hidden_states = self.model.predict(returns_reshaped)
        
        # Map states to regimes
        self._map_regimes(returns_reshaped, hidden_states)
        
        print(f"✅ HMM model fitted ({n_iterations} iterations, {len(returns)} days)")
        self._print_regime_characteristics(returns_reshaped, hidden_states)
        
        return True
    
    def _map_regimes(self, returns: np.ndarray, hidden_states: np.ndarray):
        """
        Map hidden states to interpretable regimes.
        
        Uses mean return and volatility to classify:
        - High mean, low vol → Bull
        - Low mean, high vol → Bear
        - Neutral mean, low vol → Range
        - High mean, high vol → Volatile Bull
        """
        regime_stats = {}
        
        for state in range(self.n_regimes):
            mask = hidden_states == state
            state_returns = returns[mask]
            
            if len(state_returns) > 0:
                mean = np.mean(state_returns)
                std = np.std(state_returns)
                sharpe = mean / std if std > 0 else 0
                
                regime_stats[state] = {
                    'mean': mean,
                    'std': std,
                    'sharpe': sharpe,
                    'count': len(state_returns),
                    'pct': len(state_returns) / len(returns) * 100
                }
        
        # Handle states with no observations
        median_vol = np.median([s['std'] for s in regime_stats.values()]) if regime_stats else 0.02
        
        # Classify regimes based on mean/vol quadrants
        # Sort by Sharpe ratio (best risk-adjusted first)
        sorted_by_sharpe = sorted(regime_stats.items(), key=lambda x: x[1]['sharpe'], reverse=True)
        
        self.regime_mapping = {}
        assigned = set()
        
        # Best Sharpe → Bull (good returns, reasonable vol)
        if len(sorted_by_sharpe) >= 1:
            state = sorted_by_sharpe[0][0]
            self.regime_mapping[state] = MarketRegime.BULL
            assigned.add(state)
        
        # Worst Sharpe + high vol → Bear
        if len(sorted_by_sharpe) >= 2:
            for i in range(len(sorted_by_sharpe) - 1, -1, -1):
                state = sorted_by_sharpe[i][0]
                if state not in assigned and regime_stats[state]['std'] > median_vol:
                    self.regime_mapping[state] = MarketRegime.BEAR
                    assigned.add(state)
                    break
        
        # Low vol, neutral mean → Range
        if len(sorted_by_sharpe) >= 3:
            for state, stats in regime_stats.items():
                if state not in assigned and stats['std'] < median_vol and abs(stats['mean']) < median_vol:
                    self.regime_mapping[state] = MarketRegime.RANGE
                    assigned.add(state)
                    break
        
        # Remaining → Volatile Bull (or default)
        remaining = [s for s in range(self.n_regimes) if s not in assigned]
        for state in remaining:
            if state in regime_stats:
                stats = regime_stats[state]
                if stats['mean'] > 0 and stats['std'] > median_vol:
                    self.regime_mapping[state] = MarketRegime.VOLATILE_BULL
                else:
                    self.regime_mapping[state] = MarketRegime.RANGE  # Default
            else:
                # State not observed, default to Range
                self.regime_mapping[state] = MarketRegime.RANGE
    
    def _print_regime_characteristics(self, returns: np.ndarray, hidden_states: np.ndarray):
        """Print regime characteristics"""
        print("\n📊 Regime Characteristics:")
        print("-" * 70)
        
        for state in range(self.n_regimes):
            mask = hidden_states == state
            state_returns = returns[mask]
            
            if len(state_returns) > 0:
                regime = self.regime_mapping.get(state, MarketRegime.RANGE)
                mean = np.mean(state_returns) * 100
                std = np.std(state_returns) * 100
                sharpe = mean / std if std > 0 else 0
                pct = len(state_returns) / len(returns) * 100
                
                # Emoji based on regime
                emoji = {
                    MarketRegime.BULL: "🐂",
                    MarketRegime.BEAR: "🐻",
                    MarketRegime.RANGE: "➡️",
                    MarketRegime.VOLATILE_BULL: "🚀"
                }.get(regime, "❓")
                
                print(f"  {emoji} State {state} → {regime.value.upper()}")
                print(f"      Mean: {mean:+.2f}% | Vol: {std:.2f}% | Sharpe: {sharpe:.2f} | Occurrence: {pct:.1f}%")
        
        print("-" * 70)
    
    def get_current_regime(self, returns: np.ndarray, lookback: int = 20) -> Tuple[MarketRegime, float, int]:
        """
        Get current market regime with confidence and persistence.
        
        Args:
            returns: Full returns series
            lookback: Lookback window for regime detection
            
        Returns:
            Tuple of (regime, confidence, persistence_days)
        """
        if self.model is None:
            return MarketRegime.RANGE, 0.5, 0
        
        # Use recent returns
        recent = returns[-lookback:].reshape(-1, 1)
        
        # Predict regime
        recent_states = self.model.predict(recent)
        
        # Most recent state
        current_state = recent_states[-1]
        
        # Confidence = proportion of recent period in this state
        confidence = np.sum(recent_states == current_state) / len(recent_states)
        
        # Persistence = consecutive days in current state
        persistence = 0
        for i in range(len(recent_states) - 1, -1, -1):
            if recent_states[i] == current_state:
                persistence += 1
            else:
                break
        
        regime = self.regime_mapping.get(current_state, MarketRegime.RANGE)
        
        return regime, confidence, persistence
    
    def get_strategy_for_regime(self, regime: MarketRegime) -> RegimeStrategy:
        """Get strategy for a specific regime"""
        return self.strategies.get(regime, self.strategies[MarketRegime.RANGE])
    
    def get_position_size_multiplier(self, regime: MarketRegime) -> float:
        """Get position size multiplier for regime"""
        strategy = self.get_strategy_for_regime(regime)
        return strategy.position_size
    
    def calculate_regime_adjusted_position(
        self,
        base_position: float,
        regime: MarketRegime
    ) -> float:
        """
        Calculate regime-adjusted position size.
        
        Args:
            base_position: Base position size (e.g., from Kelly)
            regime: Current market regime
            
        Returns:
            Adjusted position size
        """
        multiplier = self.get_position_size_multiplier(regime)
        return base_position * multiplier
    
    def backtest_by_regime(
        self,
        returns: np.ndarray,
        strategy_returns: np.ndarray
    ) -> Dict[str, float]:
        """
        Backtest strategy performance by regime.
        
        Args:
            returns: Market returns
            strategy_returns: Strategy returns
            
        Returns:
            Dict with performance metrics per regime
        """
        if self.model is None:
            return {}
        
        # Get regimes for all periods
        returns_reshaped = returns.reshape(-1, 1)
        hidden_states = self.model.predict(returns_reshaped)
        
        # Ensure strategy_returns matches length
        min_len = min(len(hidden_states), len(strategy_returns))
        hidden_states = hidden_states[:min_len]
        strategy_returns = strategy_returns[:min_len]
        
        # Calculate metrics per regime
        results = {}
        
        for state in range(self.n_regimes):
            mask = hidden_states == state
            regime = self.regime_mapping.get(state, MarketRegime.RANGE)
            
            regime_returns = strategy_returns[mask]
            
            if len(regime_returns) > 0:
                total_return = np.prod(1 + regime_returns) - 1
                sharpe = np.mean(regime_returns) / np.std(regime_returns) * np.sqrt(252) if np.std(regime_returns) > 0 else 0
                max_dd = self._calculate_max_drawdown(regime_returns)
                
                results[regime.value] = {
                    'n_trades': len(regime_returns),
                    'total_return': total_return,
                    'sharpe': sharpe,
                    'max_drawdown': max_dd,
                    'avg_return': np.mean(regime_returns),
                    'win_rate': np.sum(regime_returns > 0) / len(regime_returns)
                }
        
        return results
    
    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate maximum drawdown from returns series"""
        if len(returns) == 0:
            return 0.0
        
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return np.min(drawdown)
    
    def print_regime_summary(self, returns: np.ndarray):
        """Print comprehensive regime summary"""
        if self.model is None:
            print("⚠️  Model not fitted")
            return
        
        regime, confidence, persistence = self.get_current_regime(returns)
        strategy = self.get_strategy_for_regime(regime)
        
        print("\n" + "="*70)
        print("🔮 CURRENT REGIME ANALYSIS")
        print("="*70)
        
        emoji = {
            MarketRegime.BULL: "🐂",
            MarketRegime.BEAR: "🐻",
            MarketRegime.RANGE: "➡️",
            MarketRegime.VOLATILE_BULL: "🚀"
        }.get(regime, "❓")
        
        print(f"Current Regime: {emoji} {regime.value.upper()}")
        print(f"Confidence: {confidence*100:.1f}%")
        print(f"Persistence: {persistence} days")
        print("-"*70)
        print(f"Recommended Strategy: {strategy.strategy_type}")
        print(f"Position Size Multiplier: {strategy.position_size}x")
        print(f"Stop Loss: {strategy.stop_loss*100:.0f}%")
        print(f"Take Profit: {strategy.take_profit*100:.0f}%")
        print(f"Max Holding: {strategy.max_holding_period} days")
        print(f"Description: {strategy.description}")
        print("="*70 + "\n")


class RegimeBacktester:
    """
    Backtest trading strategies by market regime.
    """
    
    def __init__(self, initial_capital: float = 10000.0):
        """
        Initialize backtester.
        
        Args:
            initial_capital: Starting capital
        """
        self.initial_capital = initial_capital
    
    def run_backtest(
        self,
        returns: np.ndarray,
        hmm: AdvancedHMM,
        base_kelly: float = 0.25
    ) -> Dict:
        """
        Run regime-dependent backtest.
        
        Args:
            returns: Market returns
            hmm: Fitted HMM model
            base_kelly: Base Kelly fraction
            
        Returns:
            Backtest results
        """
        if hmm.model is None:
            return {'error': 'HMM model not fitted'}
        
        # Get regimes
        returns_reshaped = returns.reshape(-1, 1)
        hidden_states = hmm.model.predict(returns_reshaped)
        
        # Simulate trading
        capital = self.initial_capital
        capital_curve = [capital]
        trades = []
        
        for i in range(len(returns)):
            state = hidden_states[i]
            regime = hmm.regime_mapping.get(state, MarketRegime.RANGE)
            strategy = hmm.get_strategy_for_regime(regime)
            
            # Regime-adjusted position
            position_size = base_kelly * strategy.position_size
            
            # Apply stop loss / take profit logic (simplified)
            market_return = returns[i]
            
            # Simple execution
            if position_size > 0:
                trade_return = position_size * market_return
                capital = capital * (1 + trade_return)
                
                trades.append({
                    'date': i,
                    'regime': regime.value,
                    'position_size': position_size,
                    'market_return': market_return,
                    'trade_return': trade_return
                })
            
            capital_curve.append(capital)
        
        # Calculate metrics
        capital_curve = np.array(capital_curve[1:])  # Remove initial
        total_return = (capital_curve[-1] / self.initial_capital) - 1
        
        # Daily returns of strategy
        strategy_returns = np.diff(capital_curve) / capital_curve[:-1]
        sharpe = np.mean(strategy_returns) / np.std(strategy_returns) * np.sqrt(252) if len(strategy_returns) > 1 and np.std(strategy_returns) > 0 else 0
        
        # Max drawdown
        cumulative = capital_curve / self.initial_capital
        running_max = np.maximum.accumulate(cumulative)
        max_dd = np.min((cumulative - running_max) / running_max)
        
        return {
            'total_return': total_return,
            'sharpe': sharpe,
            'max_drawdown': max_dd,
            'final_capital': capital_curve[-1],
            'n_trades': len(trades),
            'capital_curve': capital_curve,
            'trades': trades
        }


def test_advanced_hmm():
    """Test advanced HMM with simulated data"""
    print("🧪 Testing Advanced HMM with 4 Regimes...\n")
    
    if not HAS_HMM:
        print("⚠️  hmmlearn not available, skipping test")
        return
    
    # Generate synthetic data with 4 regimes
    np.random.seed(42)
    n = 500
    
    # Regime 1: Bull (positive, low vol)
    bull = np.random.normal(0.002, 0.015, 150)
    # Regime 2: Bear (negative, high vol)
    bear = np.random.normal(-0.003, 0.035, 100)
    # Regime 3: Range (neutral, low vol)
    range_ = np.random.normal(0.0005, 0.012, 150)
    # Regime 4: Volatile Bull (positive, high vol)
    vol_bull = np.random.normal(0.004, 0.045, 100)
    
    all_returns = np.concatenate([bull, bear, range_, vol_bull])
    
    print(f"Generated {len(all_returns)} days of synthetic returns")
    print(f"  Bull: 150 days (mean +0.20%, vol 1.5%)")
    print(f"  Bear: 100 days (mean -0.30%, vol 3.5%)")
    print(f"  Range: 150 days (mean +0.05%, vol 1.2%)")
    print(f"  Volatile Bull: 100 days (mean +0.40%, vol 4.5%)")
    
    # Initialize and fit HMM
    hmm_model = AdvancedHMM(n_regimes=4, lookback_days=60)
    hmm_model.fit(all_returns)
    
    # Get current regime
    regime, confidence, persistence = hmm_model.get_current_regime(all_returns)
    print(f"\n📊 Current Regime Detection:")
    print(f"   Regime: {regime.value}")
    print(f"   Confidence: {confidence*100:.1f}%")
    print(f"   Persistence: {persistence} days")
    
    # Get strategy
    strategy = hmm_model.get_strategy_for_regime(regime)
    print(f"\n📋 Recommended Strategy:")
    print(f"   Type: {strategy.strategy_type}")
    print(f"   Position Size: {strategy.position_size}x Kelly")
    print(f"   Stop Loss: {strategy.stop_loss*100:.0f}%")
    print(f"   Take Profit: {strategy.take_profit*100:.0f}%")
    
    # Backtest
    print("\n" + "="*70)
    print("📊 BACKTEST RESULTS")
    print("="*70)
    
    backtester = RegimeBacktester(initial_capital=10000)
    results = backtester.run_backtest(all_returns, hmm_model, base_kelly=0.25)
    
    if 'error' not in results:
        print(f"\n💰 Performance:")
        print(f"   Initial Capital: $10,000")
        print(f"   Final Capital: ${results['final_capital']:,.2f}")
        print(f"   Total Return: {results['total_return']*100:.1f}%")
        print(f"   Sharpe Ratio: {results['sharpe']:.2f}")
        print(f"   Max Drawdown: {results['max_drawdown']*100:.1f}%")
        print(f"   Number of Trades: {results['n_trades']}")
        
        # Performance by regime
        print(f"\n📈 Performance by Regime:")
        by_regime = hmm_model.backtest_by_regime(all_returns, np.diff(results['capital_curve']) / results['capital_curve'][:-1])
        
        for regime_name, metrics in by_regime.items():
            print(f"\n   {regime_name.upper()}:")
            print(f"      Trades: {metrics['n_trades']}")
            print(f"      Total Return: {metrics['total_return']*100:.1f}%")
            print(f"      Sharpe: {metrics['sharpe']:.2f}")
            print(f"      Win Rate: {metrics['win_rate']*100:.1f}%")
    
    print("\n✅ Advanced HMM test complete!")
    return hmm_model


if __name__ == "__main__":
    test_advanced_hmm()
