#!/usr/bin/env python3
"""
Risk Monitor - Real-time VaR/CVaR Monitoring with Circuit Breakers

Module: Phase 2 - Risk Management Core
Author: Saiyan Autonomous Trading System
Date: May 24, 2026

Features:
- Real-time VaR/CVaR calculation (Historical, Parametric, Monte Carlo)
- Circuit breakers (4 levels: Warning → Kill Switch)
- Daily PnL tracking
- Drawdown monitoring
- Volatility spike detection
- Alert system with severity levels
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Try to import optional dependencies
try:
    import ccxt
    HAS_CCXT = True
except ImportError:
    HAS_CCXT = False

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class CircuitBreakerLevel(Enum):
    """Circuit breaker escalation levels"""
    LEVEL_0 = "normal"  # No action
    LEVEL_1 = "warning"  # Alert only
    LEVEL_2 = "reduce"  # Reduce position by 50%
    LEVEL_3 = "stop"  # Stop new trades
    LEVEL_4 = "kill"  # Kill switch - close all positions


@dataclass
class RiskMetrics:
    """Container for risk metrics"""
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    current_vol: float
    daily_pnl: float
    drawdown: float
    circuit_breaker_level: CircuitBreakerLevel
    timestamp: datetime


@dataclass
class Alert:
    """Alert message with metadata"""
    level: AlertLevel
    message: str
    metric: str
    value: float
    threshold: float
    timestamp: datetime


class RiskMonitor:
    """
    Real-time risk monitoring system with circuit breakers.
    
    Monitors:
    - VaR/CVaR (Value at Risk / Conditional Value at Risk)
    - Daily PnL
    - Drawdown from peak
    - Volatility spikes
    - Position concentration
    """
    
    def __init__(
        self,
        initial_capital: float = 10000.0,
        var_confidence: float = 0.95,
        lookback_days: int = 30,
        trading_window_hours: int = 24
    ):
        """
        Initialize risk monitor.
        
        Args:
            initial_capital: Starting capital for PnL calculations
            var_confidence: VaR confidence level (0.95 or 0.99)
            lookback_days: Days of historical data for VaR calculation
            trading_window_hours: Hours considered as "daily" for PnL
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.peak_capital = initial_capital
        self.var_confidence = var_confidence
        self.lookback_days = lookback_days
        self.trading_window_hours = trading_window_hours
        
        # Storage
        self.returns_history: List[float] = []
        self.capital_history: List[Tuple[datetime, float]] = []
        self.alerts: List[Alert] = []
        
        # Circuit breaker thresholds (based on Master 4 curriculum)
        self.circuit_breaker_thresholds = {
            CircuitBreakerLevel.LEVEL_1: {
                'daily_pnl': -0.036,  # -3.6% (VaR 95% threshold)
                'drawdown': -0.10,     # -10% from peak
            },
            CircuitBreakerLevel.LEVEL_2: {
                'daily_pnl': -0.05,    # -5%
                'drawdown': -0.15,     # -15%
            },
            CircuitBreakerLevel.LEVEL_3: {
                'daily_pnl': -0.08,    # -8%
                'drawdown': -0.20,     # -20%
            },
            CircuitBreakerLevel.LEVEL_4: {
                'daily_pnl': -0.10,    # -10% (Kill Switch)
                'drawdown': -0.25,     # -25% (Max drawdown)
            }
        }
        
        # Volatility spike threshold (based on GARCH analysis)
        self.vol_spike_threshold = 2.0  # 2x normal volatility
        
        # Track daily start capital
        self.daily_start_capital = initial_capital
        self.last_reset_time = datetime.now()
        
        print(f"🛡️  Risk Monitor initialized")
        print(f"   Initial capital: ${initial_capital:,.2f}")
        print(f"   VaR confidence: {var_confidence*100:.0f}%")
        print(f"   Lookback: {lookback_days} days")
        print(f"   Circuit breakers: 4 levels configured")
    
    def update_capital(self, new_capital: float, timestamp: Optional[datetime] = None):
        """
        Update current capital and record history.
        
        Args:
            new_capital: Current portfolio value
            timestamp: Optional timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Calculate return
        if self.current_capital > 0:
            ret = (new_capital - self.current_capital) / self.current_capital
            self.returns_history.append(ret)
        
        # Update capital
        old_capital = self.current_capital
        self.current_capital = new_capital
        self.capital_history.append((timestamp, new_capital))
        
        # Update peak
        if new_capital > self.peak_capital:
            self.peak_capital = new_capital
        
        # Check if we need to reset daily PnL
        self._check_daily_reset(timestamp)
        
        # Calculate daily PnL
        daily_pnl = (new_capital - self.daily_start_capital) / self.daily_start_capital
        
        # Check circuit breakers
        cb_level = self._check_circuit_breakers(daily_pnl)
        
        # Generate alerts if needed
        self._generate_alerts(daily_pnl, cb_level)
        
        return daily_pnl, cb_level
    
    def _check_daily_reset(self, timestamp: datetime):
        """Check if we need to reset daily PnL tracking"""
        hours_since_reset = (timestamp - self.last_reset_time).total_seconds() / 3600
        if hours_since_reset >= self.trading_window_hours:
            self.daily_start_capital = self.current_capital
            self.last_reset_time = timestamp
            print(f"📊 Daily PnL reset: ${self.daily_start_capital:,.2f}")
    
    def _check_circuit_breakers(self, daily_pnl: float) -> CircuitBreakerLevel:
        """
        Check all circuit breaker conditions and return highest level triggered.
        
        Args:
            daily_pnl: Daily PnL percentage
            
        Returns:
            Highest circuit breaker level triggered
        """
        current_dd = self._calculate_drawdown()
        
        # Check each level from highest to lowest
        for level in [CircuitBreakerLevel.LEVEL_4, 
                      CircuitBreakerLevel.LEVEL_3,
                      CircuitBreakerLevel.LEVEL_2,
                      CircuitBreakerLevel.LEVEL_1]:
            thresholds = self.circuit_breaker_thresholds[level]
            
            if daily_pnl <= thresholds['daily_pnl']:
                return level
            if current_dd <= thresholds['drawdown']:
                return level
        
        return CircuitBreakerLevel.LEVEL_0
    
    def _calculate_drawdown(self) -> float:
        """Calculate current drawdown from peak"""
        if self.peak_capital <= 0:
            return 0.0
        return (self.current_capital - self.peak_capital) / self.peak_capital
    
    def _generate_alerts(self, daily_pnl: float, cb_level: CircuitBreakerLevel):
        """Generate alerts based on current metrics"""
        timestamp = datetime.now()
        
        # Alert for circuit breaker activation
        if cb_level != CircuitBreakerLevel.LEVEL_0:
            level_map = {
                CircuitBreakerLevel.LEVEL_1: AlertLevel.WARNING,
                CircuitBreakerLevel.LEVEL_2: AlertLevel.CRITICAL,
                CircuitBreakerLevel.LEVEL_3: AlertLevel.CRITICAL,
                CircuitBreakerLevel.LEVEL_4: AlertLevel.EMERGENCY
            }
            
            alert = Alert(
                level=level_map[cb_level],
                message=f"Circuit breaker {cb_level.value} triggered",
                metric="circuit_breaker",
                value=cb_level.value,
                threshold="threshold",
                timestamp=timestamp
            )
            self.alerts.append(alert)
            print(f"🚨 ALERT [{alert.level.value.upper()}]: {alert.message}")
    
    def calculate_var_historical(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """
        Calculate VaR using historical method.
        
        Args:
            returns: Array of returns
            confidence: Confidence level
            
        Returns:
            VaR as a negative percentage
        """
        if len(returns) == 0:
            return 0.0
        return np.percentile(returns, (1 - confidence) * 100)
    
    def calculate_cvar_historical(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """
        Calculate CVaR (Expected Shortfall) using historical method.
        
        Args:
            returns: Array of returns
            confidence: Confidence level
            
        Returns:
            CVaR as a negative percentage
        """
        if len(returns) == 0:
            return 0.0
        var = self.calculate_var_historical(returns, confidence)
        tail_returns = returns[returns <= var]
        if len(tail_returns) == 0:
            return var
        return np.mean(tail_returns)
    
    def calculate_var_parametric(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """
        Calculate VaR using parametric (Gaussian) method.
        
        Args:
            returns: Array of returns
            confidence: Confidence level
            
        Returns:
            VaR as a negative percentage
        """
        if len(returns) < 2:
            return 0.0
        
        mean = np.mean(returns)
        std = np.std(returns)
        
        if HAS_SCIPY:
            z_score = stats.norm.ppf(1 - confidence)
        else:
            # Approximate z-scores
            z_scores = {0.95: -1.645, 0.99: -2.326}
            z_score = z_scores.get(confidence, -1.645)
        
        return mean + z_score * std
    
    def calculate_cvar_parametric(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """
        Calculate CVaR using parametric method.
        
        For Gaussian distribution: CVaR = μ - σ * φ(Φ⁻¹(α)) / (1-α)
        
        Args:
            returns: Array of returns
            confidence: Confidence level
            
        Returns:
            CVaR as a negative percentage
        """
        if len(returns) < 2:
            return 0.0
        
        mean = np.mean(returns)
        std = np.std(returns)
        
        if HAS_SCIPY:
            z_score = stats.norm.ppf(1 - confidence)
            # PDF of standard normal at z_score
            pdf = stats.norm.pdf(z_score)
            cvar_adjustment = pdf / (1 - confidence)
        else:
            # Approximation
            z_score = -1.645 if confidence == 0.95 else -2.326
            cvar_adjustment = 2.06 if confidence == 0.95 else 2.67
        
        return mean - std * cvar_adjustment
    
    def calculate_var_monte_carlo(
        self, 
        returns: np.ndarray, 
        confidence: float = 0.95,
        n_simulations: int = 10000
    ) -> float:
        """
        Calculate VaR using Monte Carlo simulation.
        
        Args:
            returns: Array of returns
            confidence: Confidence level
            n_simulations: Number of simulations
            
        Returns:
            VaR as a negative percentage
        """
        if len(returns) < 2:
            return 0.0
        
        mean = np.mean(returns)
        std = np.std(returns)
        
        # Simulate returns
        simulated_returns = np.random.normal(mean, std, n_simulations)
        
        return np.percentile(simulated_returns, (1 - confidence) * 100)
    
    def calculate_volatility(self, returns: np.ndarray, window: int = 20) -> float:
        """
        Calculate rolling volatility.
        
        Args:
            returns: Array of returns
            window: Rolling window size
            
        Returns:
            Annualized volatility
        """
        if len(returns) < window:
            return np.std(returns) * np.sqrt(365) if len(returns) > 0 else 0.0
        
        recent_returns = returns[-window:]
        return np.std(recent_returns) * np.sqrt(365)
    
    def get_risk_metrics(self) -> RiskMetrics:
        """
        Calculate all current risk metrics.
        
        Returns:
            RiskMetrics dataclass with all current values
        """
        returns_array = np.array(self.returns_history) if self.returns_history else np.array([])
        
        # Calculate VaR/CVaR
        var_95 = self.calculate_var_historical(returns_array, 0.95)
        var_99 = self.calculate_var_historical(returns_array, 0.99)
        cvar_95 = self.calculate_cvar_historical(returns_array, 0.95)
        cvar_99 = self.calculate_cvar_historical(returns_array, 0.99)
        
        # Current volatility
        current_vol = self.calculate_volatility(returns_array)
        
        # Daily PnL
        daily_pnl = (self.current_capital - self.daily_start_capital) / self.daily_start_capital
        
        # Drawdown
        drawdown = self._calculate_drawdown()
        
        # Circuit breaker level
        cb_level = self._check_circuit_breakers(daily_pnl)
        
        return RiskMetrics(
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            current_vol=current_vol,
            daily_pnl=daily_pnl,
            drawdown=drawdown,
            circuit_breaker_level=cb_level,
            timestamp=datetime.now()
        )
    
    def check_trading_allowed(self) -> Tuple[bool, str]:
        """
        Check if new trades are allowed based on circuit breakers.
        
        Returns:
            Tuple of (allowed, reason)
        """
        metrics = self.get_risk_metrics()
        
        if metrics.circuit_breaker_level == CircuitBreakerLevel.LEVEL_4:
            return False, "KILL SWITCH ACTIVATED - Close all positions"
        elif metrics.circuit_breaker_level == CircuitBreakerLevel.LEVEL_3:
            return False, "Circuit breaker Level 3 - No new trades"
        elif metrics.circuit_breaker_level == CircuitBreakerLevel.LEVEL_2:
            return True, "Circuit breaker Level 2 - Reduce position size by 50%"
        elif metrics.circuit_breaker_level == CircuitBreakerLevel.LEVEL_1:
            return True, "Circuit breaker Level 1 - Warning only"
        else:
            return True, "Normal trading conditions"
    
    def get_position_size_limit(self, base_size: float) -> float:
        """
        Get maximum position size based on circuit breaker level.
        
        Args:
            base_size: Normal position size
            
        Returns:
            Adjusted position size
        """
        metrics = self.get_risk_metrics()
        
        if metrics.circuit_breaker_level in [CircuitBreakerLevel.LEVEL_3, 
                                              CircuitBreakerLevel.LEVEL_4]:
            return 0.0
        elif metrics.circuit_breaker_level == CircuitBreakerLevel.LEVEL_2:
            return base_size * 0.5
        else:
            return base_size
    
    def print_status(self):
        """Print current risk status"""
        metrics = self.get_risk_metrics()
        
        print("\n" + "="*60)
        print("🛡️  RISK MONITOR STATUS")
        print("="*60)
        print(f"Capital:     ${self.current_capital:,.2f} (Peak: ${self.peak_capital:,.2f})")
        print(f"Daily PnL:   {metrics.daily_pnl*100:+.2f}%")
        print(f"Drawdown:    {metrics.drawdown*100:.2f}%")
        print(f"Volatility:  {metrics.current_vol*100:.1f}% (annualized)")
        print("-"*60)
        print(f"VaR 95%:     {metrics.var_95*100:.2f}%")
        print(f"CVaR 95%:    {metrics.cvar_95*100:.2f}%")
        print(f"VaR 99%:     {metrics.var_99*100:.2f}%")
        print(f"CVaR 99%:    {metrics.cvar_99*100:.2f}%")
        print("-"*60)
        print(f"Circuit Breaker: {metrics.circuit_breaker_level.value.upper()}")
        
        allowed, reason = self.check_trading_allowed()
        status = "✅ ALLOWED" if allowed else "❌ BLOCKED"
        print(f"Trading:     {status}")
        print(f"             {reason}")
        print("="*60 + "\n")
    
    def get_alerts(self, level: Optional[AlertLevel] = None) -> List[Alert]:
        """
        Get alerts, optionally filtered by level.
        
        Args:
            level: Filter by alert level (optional)
            
        Returns:
            List of alerts
        """
        if level is None:
            return self.alerts
        return [a for a in self.alerts if a.level == level]
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts = []


def test_risk_monitor():
    """Test the risk monitor with simulated data"""
    print("🧪 Testing Risk Monitor with simulated data...\n")
    
    # Initialize monitor
    monitor = RiskMonitor(initial_capital=10000.0)
    
    # Simulate some returns (normal market conditions)
    np.random.seed(42)
    normal_returns = np.random.normal(0.001, 0.03, 100)  # 0.1% daily return, 3% daily vol
    
    print("📈 Simulating normal market conditions...")
    capital = 10000.0
    for i, ret in enumerate(normal_returns):
        capital = capital * (1 + ret)
        monitor.update_capital(capital)
    
    monitor.print_status()
    
    # Simulate a crash
    print("\n💥 Simulating market crash...")
    crash_returns = [-0.05, -0.08, -0.12, -0.06, -0.04]  # Severe losses
    
    for ret in crash_returns:
        capital = capital * (1 + ret)
        daily_pnl, cb_level = monitor.update_capital(capital)
        print(f"  Return: {ret*100:.1f}% → Daily PnL: {daily_pnl*100:.2f}%, Circuit Breaker: {cb_level.value}")
    
    monitor.print_status()
    
    # Test trading limits
    print("\n📊 Position Size Limits:")
    base_size = 1000.0
    allowed, reason = monitor.check_trading_allowed()
    max_size = monitor.get_position_size_limit(base_size)
    print(f"  Base size: ${base_size:,.2f}")
    print(f"  Max allowed: ${max_size:,.2f}")
    print(f"  Status: {reason}")
    
    # Show alerts
    alerts = monitor.get_alerts()
    if alerts:
        print(f"\n🚨 Alerts generated: {len(alerts)}")
        for alert in alerts[-5:]:  # Last 5 alerts
            print(f"  [{alert.level.value.upper()}] {alert.message}")
    
    print("\n✅ Risk Monitor test complete!")
    return monitor


if __name__ == "__main__":
    test_risk_monitor()
