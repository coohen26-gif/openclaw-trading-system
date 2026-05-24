#!/usr/bin/env python3
"""
Stress Testing & Validation Framework

Module: Phase 2 - Stress Testing & Validation (Semaine 29)
Author: Saiyan Autonomous Trading System
Date: May 24, 2026

Features:
- Historical scenario stress testing (COVID, FTX, LUNA, etc.)
- Hypothetical scenario generation
- Monte Carlo simulation with stressed parameters
- VaR/CVaR under stress
- Circuit breaker validation
- Walk-forward validation framework
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
    import ccxt
    HAS_CCXT = True
except ImportError:
    HAS_CCXT = False


class StressScenarioType(Enum):
    """Type of stress scenario"""
    HISTORICAL = "historical"
    HYPOTHETICAL = "hypothetical"
    SENSITIVITY = "sensitivity"
    SYSTEMIC = "systemic"


@dataclass
class StressScenario:
    """Definition of a stress scenario"""
    name: str
    scenario_type: StressScenarioType
    description: str
    return_shock: float  # Mean return shock
    vol_multiplier: float  # Volatility multiplier
    correlation_shock: float  # Correlation increase
    duration_days: int
    probability: float  # Estimated annual probability


@dataclass
class StressTestResult:
    """Results of a stress test"""
    scenario_name: str
    portfolio_return: float
    portfolio_vol: float
    var_95: float
    cvar_95: float
    max_drawdown: float
    worst_day: float
    n_days: int
    circuit_breaker_triggers: int
    survival: bool  # Did portfolio survive?


@dataclass
class ValidationMetric:
    """Validation metric for strategy"""
    name: str
    value: float
    threshold: float
    passed: bool
    description: str


class HistoricalScenarios:
    """
    Pre-defined historical stress scenarios for crypto.
    
    Based on actual market events 2020-2026.
    """
    
    @staticmethod
    def get_all_scenarios() -> List[StressScenario]:
        """Get all historical stress scenarios"""
        return [
            StressScenario(
                name="COVID-19 Crash (Mar 2020)",
                scenario_type=StressScenarioType.HISTORICAL,
                description="Global pandemic panic selling, all assets correlated → 1",
                return_shock=-0.08,  # -8% daily mean during crash
                vol_multiplier=3.5,  # 3.5x normal vol
                correlation_shock=0.4,  # Correlations increase by 0.4
                duration_days=14,
                probability=0.02  # ~2% annual probability
            ),
            StressScenario(
                name="FTX Collapse (Nov 2022)",
                scenario_type=StressScenarioType.HISTORICAL,
                description="Exchange bankruptcy, contagion, liquidity crisis",
                return_shock=-0.06,
                vol_multiplier=2.8,
                correlation_shock=0.3,
                duration_days=10,
                probability=0.03
            ),
            StressScenario(
                name="LUNA/UST Depeg (May 2022)",
                scenario_type=StressScenarioType.HISTORICAL,
                description="Stablecoin depeg, ecosystem collapse",
                return_shock=-0.07,
                vol_multiplier=3.0,
                correlation_shock=0.35,
                duration_days=7,
                probability=0.02
            ),
            StressScenario(
                name="China Mining Ban (Jun 2021)",
                scenario_type=StressScenarioType.HISTORICAL,
                description="Mining crackdown, hashrate -50%",
                return_shock=-0.05,
                vol_multiplier=2.2,
                correlation_shock=0.2,
                duration_days=21,
                probability=0.05
            ),
            StressScenario(
                name="COVID Recovery Rally (Apr 2020)",
                scenario_type=StressScenarioType.HISTORICAL,
                description="V-shaped recovery, massive stimulus",
                return_shock=+0.06,  # Positive shock!
                vol_multiplier=2.0,
                correlation_shock=0.1,
                duration_days=30,
                probability=0.05
            ),
            # Hypothetical scenarios
            StressScenario(
                name="Exchange Hack (Hypothetical)",
                scenario_type=StressScenarioType.HYPOTHETICAL,
                description="Major exchange hacked, $2B stolen",
                return_shock=-0.10,
                vol_multiplier=4.0,
                correlation_shock=0.5,
                duration_days=5,
                probability=0.01
            ),
            StressScenario(
                name="Regulatory Crackdown (Hypothetical)",
                scenario_type=StressScenarioType.HYPOTHETICAL,
                description="US bans crypto trading",
                return_shock=-0.12,
                vol_multiplier=3.5,
                correlation_shock=0.4,
                duration_days=15,
                probability=0.01
            ),
            StressScenario(
                name="Flash Crash (Hypothetical)",
                scenario_type=StressScenarioType.HYPOTHETICAL,
                description="Algorithmic cascade, -30% in hours",
                return_shock=-0.15,
                vol_multiplier=5.0,
                correlation_shock=0.6,
                duration_days=1,
                probability=0.005
            ),
            StressScenario(
                name="Stablecoin Run (Systemic)",
                scenario_type=StressScenarioType.SYSTEMIC,
                description="USDC/USDT depeg, liquidity evaporates",
                return_shock=-0.09,
                vol_multiplier=4.5,
                correlation_shock=0.5,
                duration_days=10,
                probability=0.01
            ),
        ]
    
    @staticmethod
    def get_worst_case() -> StressScenario:
        """Get the worst-case scenario"""
        return StressScenario(
            name="Perfect Storm (Worst Case)",
            scenario_type=StressScenarioType.SYSTEMIC,
            description="Multiple crises simultaneously",
            return_shock=-0.15,
            vol_multiplier=5.0,
            correlation_shock=0.7,
            duration_days=30,
            probability=0.001
        )


class StressTestEngine:
    """
    Stress testing engine for portfolio validation.
    """
    
    def __init__(
        self,
        initial_capital: float = 10000.0,
        base_return: float = 0.001,  # 0.1% daily
        base_vol: float = 0.03,  # 3% daily
        base_kelly: float = 0.25
    ):
        """
        Initialize stress test engine.
        
        Args:
            initial_capital: Starting capital
            base_return: Base daily return (normal conditions)
            base_vol: Base daily volatility (normal conditions)
            base_kelly: Base Kelly fraction
        """
        self.initial_capital = initial_capital
        self.base_return = base_return
        self.base_vol = base_vol
        self.base_kelly = base_kelly
        
        # Circuit breaker thresholds
        self.cb_thresholds = {
            'level_1': -0.036,  # -3.6%
            'level_2': -0.05,   # -5%
            'level_3': -0.08,   # -8%
            'level_4': -0.10,   # -10% (kill switch)
        }
        
        print(f"🧪 Stress Test Engine initialized")
        print(f"   Initial capital: ${initial_capital:,.2f}")
        print(f"   Base return: {base_return*100:.2f}% daily")
        print(f"   Base vol: {base_vol*100:.1f}% daily")
        print(f"   Base Kelly: {base_kelly*100:.0f}%")
    
    def run_scenario(
        self,
        scenario: StressScenario,
        n_simulations: int = 1000,
        regime_adjusted: bool = True
    ) -> StressTestResult:
        """
        Run stress test for a specific scenario.
        
        Args:
            scenario: Stress scenario to test
            n_simulations: Number of Monte Carlo simulations
            regime_adjusted: Use regime-dependent position sizing
            
        Returns:
            StressTestResult
        """
        # Stressed parameters
        stressed_return = self.base_return + scenario.return_shock
        stressed_vol = self.base_vol * scenario.vol_multiplier
        
        # Simulate paths
        capital_paths = []
        cb_triggers = 0
        worst_days = []
        
        for sim in range(n_simulations):
            # Generate returns for scenario duration
            returns = np.random.normal(
                stressed_return,
                stressed_vol,
                scenario.duration_days
            )
            
            # Apply regime-dependent position sizing if enabled
            if regime_adjusted:
                # Simplified: reduce position in high vol regimes
                if scenario.vol_multiplier > 2.5:
                    position_size = self.base_kelly * 0.25  # Bear regime sizing
                elif scenario.vol_multiplier > 1.5:
                    position_size = self.base_kelly * 0.75  # Range/Volatile Bull
                else:
                    position_size = self.base_kelly * 1.5  # Bull regime
            else:
                position_size = self.base_kelly
            
            # Simulate capital path
            capital = self.initial_capital
            path = [capital]
            cb_triggered = False
            
            for ret in returns:
                # Apply position sizing
                portfolio_ret = position_size * ret
                
                # Update capital
                capital = capital * (1 + portfolio_ret)
                path.append(capital)
                
                # Check circuit breakers
                daily_pnl = portfolio_ret
                if daily_pnl <= self.cb_thresholds['level_4']:
                    cb_triggers += 1
                    cb_triggered = True
                    # Kill switch: close position
                    capital = capital * (1 + self.cb_thresholds['level_4'])
                    break  # Stop trading for this simulation
            
            capital_paths.append(np.array(path))
            worst_days.append(np.min(np.diff(path) / path[:-1]) if len(path) > 1 else 0)
        
        # Aggregate results
        capital_paths = np.array(capital_paths)
        final_capitals = capital_paths[:, -1]
        
        # Calculate metrics
        portfolio_returns = (final_capitals - self.initial_capital) / self.initial_capital
        
        # VaR/CVaR of final returns
        var_95 = np.percentile(portfolio_returns, 5)
        cvar_95 = np.mean(portfolio_returns[portfolio_returns <= var_95]) if np.any(portfolio_returns <= var_95) else var_95
        
        # Max drawdown (worst path)
        max_dd = 0.0
        for path in capital_paths:
            cumulative = path / self.initial_capital
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            max_dd = min(max_dd, np.min(drawdown))
        
        # Survival rate
        survival_rate = np.mean(final_capitals > self.initial_capital * 0.5)  # Survived if >50% capital
        
        return StressTestResult(
            scenario_name=scenario.name,
            portfolio_return=np.mean(portfolio_returns),
            portfolio_vol=np.std(portfolio_returns),
            var_95=var_95,
            cvar_95=cvar_95,
            max_drawdown=max_dd,
            worst_day=np.mean(worst_days),
            n_days=scenario.duration_days,
            circuit_breaker_triggers=cb_triggers,
            survival=survival_rate > 0.95  # 95%+ survival rate
        )
    
    def run_all_scenarios(
        self,
        n_simulations: int = 1000
    ) -> List[StressTestResult]:
        """
        Run all historical scenarios.
        
        Args:
            n_simulations: Number of Monte Carlo simulations per scenario
            
        Returns:
            List of StressTestResult
        """
        scenarios = HistoricalScenarios.get_all_scenarios()
        results = []
        
        print(f"\n📊 Running stress tests ({n_simulations} simulations each)...")
        print("="*80)
        
        for scenario in scenarios:
            result = self.run_scenario(scenario, n_simulations)
            results.append(result)
            
            # Print progress
            status = "✅" if result.survival else "❌"
            print(f"{status} {scenario.name[:40]:<40} | " +
                  f"Return: {result.portfolio_return*100:+5.1f}% | " +
                  f"DD: {result.max_drawdown*100:6.1f}% | " +
                  f"Survival: {result.survival}")
        
        print("="*80)
        
        return results
    
    def validate_circuit_breakers(
        self,
        results: List[StressTestResult]
    ) -> List[ValidationMetric]:
        """
        Validate circuit breaker design against stress scenarios.
        
        Args:
            results: Stress test results
            
        Returns:
            List of validation metrics
        """
        metrics = []
        
        # Metric 1: Survival rate
        survival_rate = np.mean([r.survival for r in results])
        metrics.append(ValidationMetric(
            name="Survival Rate",
            value=survival_rate,
            threshold=0.90,  # 90% scenarios should survive
            passed=survival_rate >= 0.90,
            description=f"{survival_rate*100:.0f}% of scenarios survived (target: 90%+)"
        ))
        
        # Metric 2: Max drawdown across scenarios
        worst_dd = np.min([r.max_drawdown for r in results])
        metrics.append(ValidationMetric(
            name="Worst Drawdown",
            value=worst_dd,
            threshold=-0.25,  # Max 25% drawdown
            passed=worst_dd >= -0.25,
            description=f"Worst DD: {worst_dd*100:.1f}% (target: >-25%)"
        ))
        
        # Metric 3: Circuit breaker trigger rate
        total_triggers = sum(r.circuit_breaker_triggers for r in results)
        trigger_rate = total_triggers / (len(results) * 1000)  # Per 1000 sims
        metrics.append(ValidationMetric(
            name="CB Trigger Rate",
            value=trigger_rate,
            threshold=0.05,  # <5% trigger rate acceptable
            passed=trigger_rate <= 0.05,
            description=f"CB triggers: {trigger_rate*100:.1f}% (target: <5%)"
        ))
        
        # Metric 4: Average return under stress
        avg_return = np.mean([r.portfolio_return for r in results])
        metrics.append(ValidationMetric(
            name="Avg Return Under Stress",
            value=avg_return,
            threshold=-0.10,  # Better than -10% average
            passed=avg_return >= -0.10,
            description=f"Avg return: {avg_return*100:.1f}% (target: >-10%)"
        ))
        
        return metrics
    
    def print_validation_report(
        self,
        results: List[StressTestResult],
        metrics: List[ValidationMetric]
    ):
        """Print comprehensive validation report"""
        print("\n" + "="*80)
        print("📋 STRESS TESTING VALIDATION REPORT")
        print("="*80)
        
        # Summary statistics
        print("\n📊 Summary Statistics:")
        print(f"   Scenarios tested: {len(results)}")
        print(f"   Simulations per scenario: 1000")
        print(f"   Survival rate: {np.mean([r.survival for r in results])*100:.0f}%")
        print(f"   Worst drawdown: {np.min([r.max_drawdown for r in results])*100:.1f}%")
        print(f"   Best return: {np.max([r.portfolio_return for r in results])*100:+.1f}%")
        print(f"   Worst return: {np.min([r.portfolio_return for r in results])*100:+.1f}%")
        
        # Validation metrics
        print("\n✅ Validation Metrics:")
        all_passed = True
        for metric in metrics:
            status = "✅" if metric.passed else "❌"
            print(f"   {status} {metric.name}: {metric.value:.3f} (threshold: {metric.threshold})")
            print(f"       {metric.description}")
            if not metric.passed:
                all_passed = False
        
        # Overall result
        print("\n" + "-"*80)
        if all_passed:
            print("🎉 VALIDATION PASSED - Circuit breakers are robust")
        else:
            print("⚠️  VALIDATION FAILED - Circuit breakers need adjustment")
        print("-"*80)
        
        # Detailed results table
        print("\n📈 Detailed Results by Scenario:")
        print(f"{'Scenario':<35} {'Return':>10} {'DD':>10} {'VaR95':>10} {'CB':>6} {'Status':>8}")
        print("-"*80)
        
        for result in results:
            status = "✅" if result.survival else "❌"
            name_short = result.scenario_name[:35]
            print(f"{name_short:<35} " +
                  f"{result.portfolio_return*100:>9.1f}% " +
                  f"{result.max_drawdown*100:>9.1f}% " +
                  f"{result.var_95*100:>9.1f}% " +
                  f"{result.circuit_breaker_triggers:>6} " +
                  f"{status:>8}")
        
        print("="*80 + "\n")


class WalkForwardValidator:
    """
    Walk-forward validation framework for trading strategies.
    """
    
    def __init__(
        self,
        training_window: int = 60,  # 60 days training
        testing_window: int = 30,   # 30 days testing
        step_size: int = 30         # Step 30 days
    ):
        """
        Initialize walk-forward validator.
        
        Args:
            training_window: Days for training/fitting
            testing_window: Days for testing/validation
            step_size: Days to step forward
        """
        self.training_window = training_window
        self.testing_window = testing_window
        self.step_size = step_size
        
        print(f"🔄 Walk-Forward Validator initialized")
        print(f"   Training window: {training_window} days")
        print(f"   Testing window: {testing_window} days")
        print(f"   Step size: {step_size} days")
    
    def run_walk_forward(
        self,
        returns: np.ndarray,
        strategy_func,
        n_folds: Optional[int] = None
    ) -> Dict:
        """
        Run walk-forward validation.
        
        Args:
            returns: Full returns series
            strategy_func: Function that takes train returns, returns test predictions
            n_folds: Number of folds (optional, auto-calculated if None)
            
        Returns:
            Dict with validation results
        """
        n = len(returns)
        
        if n_folds is None:
            n_folds = (n - self.training_window) // self.step_size
        
        print(f"\n📊 Running walk-forward validation ({n_folds} folds)...")
        
        # Storage
        train_scores = []
        test_scores = []
        test_returns = []
        
        for fold in range(n_folds):
            # Define windows
            train_start = fold * self.step_size
            train_end = train_start + self.training_window
            test_end = train_end + self.testing_window
            
            if test_end > n:
                break
            
            # Split data
            train_returns = returns[train_start:train_end]
            test_returns_actual = returns[train_end:test_end]
            
            # Fit strategy on training data
            try:
                train_score, predictions = strategy_func(train_returns, test_returns_actual)
                
                # Calculate test score (simplified: correlation of predictions with actual)
                if len(predictions) == len(test_returns_actual):
                    test_score = np.corrcoef(predictions, test_returns_actual)[0, 1]
                    test_returns.extend(test_returns_actual)
                else:
                    test_score = 0.0
                
                train_scores.append(train_score)
                test_scores.append(test_score)
                
            except Exception as e:
                print(f"⚠️  Fold {fold} failed: {e}")
                train_scores.append(0.0)
                test_scores.append(0.0)
        
        # Aggregate results
        results = {
            'n_folds': len(train_scores),
            'train_mean': np.mean(train_scores),
            'train_std': np.std(train_scores),
            'test_mean': np.mean(test_scores),
            'test_std': np.std(test_scores),
            'degradation': np.mean(test_scores) - np.mean(train_scores),
            'train_scores': train_scores,
            'test_scores': test_scores
        }
        
        # Print summary
        print(f"\n📈 Walk-Forward Results:")
        print(f"   Folds completed: {results['n_folds']}")
        print(f"   Train score: {results['train_mean']:.3f} ± {results['train_std']:.3f}")
        print(f"   Test score: {results['test_mean']:.3f} ± {results['test_std']:.3f}")
        print(f"   Degradation: {results['degradation']:.3f}")
        
        # Interpretation
        if results['degradation'] > -0.1:
            print(f"   ✅ Good generalization (degradation < 10%)")
        elif results['degradation'] > -0.2:
            print(f"   ⚠️  Moderate overfitting (degradation 10-20%)")
        else:
            print(f"   ❌ Severe overfitting (degradation > 20%)")
        
        return results


def test_stress_testing():
    """Test stress testing framework"""
    print("🧪 Testing Stress Testing Framework...\n")
    
    # Initialize engine
    engine = StressTestEngine(
        initial_capital=10000,
        base_return=0.001,  # 0.1% daily
        base_vol=0.03,      # 3% daily
        base_kelly=0.25     # Quarter-Kelly
    )
    
    # Run all scenarios
    results = engine.run_all_scenarios(n_simulations=1000)
    
    # Validate circuit breakers
    metrics = engine.validate_circuit_breakers(results)
    
    # Print full report
    engine.print_validation_report(results, metrics)
    
    # Walk-forward validation test
    print("\n" + "="*80)
    print("🔄 Testing Walk-Forward Validation")
    print("="*80)
    
    # Generate synthetic returns
    np.random.seed(42)
    n_days = 365  # 1 year
    returns = np.random.normal(0.001, 0.03, n_days)
    
    # Simple strategy: predict based on recent momentum
    def momentum_strategy(train_returns, test_returns):
        # Train: calculate recent momentum
        momentum = np.mean(train_returns[-10:])
        # Predict: vary predictions slightly to avoid constant array
        predictions = momentum + np.random.normal(0, 0.01, len(test_returns))
        # Train score: Sharpe of momentum strategy on train
        train_sharpe = np.mean(train_returns[-10:]) / np.std(train_returns[-10:]) * np.sqrt(252) if np.std(train_returns[-10:]) > 0 else 0
        return train_sharpe, predictions
    
    validator = WalkForwardValidator(
        training_window=60,
        testing_window=30,
        step_size=30
    )
    
    wf_results = validator.run_walk_forward(returns, momentum_strategy)
    
    print("\n✅ Stress Testing Framework test complete!")
    return engine, results, metrics


if __name__ == "__main__":
    test_stress_testing()
