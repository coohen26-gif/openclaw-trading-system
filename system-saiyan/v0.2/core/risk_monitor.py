"""
🐉 Risk Monitor - Système Saiyan v0.2

Components:
- VaR/CVaR calculation (3 methods: Historical, Parametric, Monte Carlo)
- 4-Level Circuit Breakers
- Real-time PnL tracking
- Drawdown monitoring
- Kill Switch implementation

Validated thresholds:
- VaR 95% BTC: -3.63% | CVaR 95%: -5.20% (gap 43%!)
- Circuit Breakers: 4 levels (Warning → Reduce → Stop → Kill)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import warnings


class AlertSeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class CircuitBreakerLevel(Enum):
    LEVEL_1_WARNING = "LEVEL_1_WARNING"
    LEVEL_2_REDUCE = "LEVEL_2_REDUCE"
    LEVEL_3_STOP = "LEVEL_3_STOP"
    LEVEL_4_KILL = "LEVEL_4_KILL"
    NORMAL = "NORMAL"


@dataclass
class Alert:
    timestamp: pd.Timestamp
    severity: AlertSeverity
    message: str
    metric: str
    value: float
    threshold: float
    cb_level: Optional[CircuitBreakerLevel] = None


@dataclass
class RiskMetrics:
    timestamp: pd.Timestamp
    var_95: float
    cvar_95: float
    var_99: Optional[float]
    cvar_99: Optional[float]
    daily_pnl_pct: float
    drawdown_pct: float
    volatility: float
    circuit_breaker_level: CircuitBreakerLevel
    trading_allowed: bool
    position_size_limit_pct: float
    alerts: List[Alert]


class RiskMonitor:
    """
    Real-time risk monitoring with VaR/CVaR and circuit breakers.
    
    Circuit Breaker Levels:
    - Level 1 (Warning): Daily PnL < -3.6% OR Drawdown < -10% → Alert
    - Level 2 (Reduce): Daily PnL < -5% OR Drawdown < -15% → Reduce 50%
    - Level 3 (Stop): Daily PnL < -8% OR Drawdown < -20% → Stop new trades
    - Level 4 (Kill): Daily PnL < -10% OR Drawdown < -25% → Kill Switch
    """
    
    # Circuit breaker thresholds (validated from stress testing)
    CB_THRESHOLDS = {
        CircuitBreakerLevel.LEVEL_1_WARNING: {
            'daily_pnl_pct': -3.6,
            'drawdown_pct': -10.0,
            'action': 'alert',
            'position_limit_pct': 100.0
        },
        CircuitBreakerLevel.LEVEL_2_REDUCE: {
            'daily_pnl_pct': -5.0,
            'drawdown_pct': -15.0,
            'action': 'reduce_50_pct',
            'position_limit_pct': 50.0
        },
        CircuitBreakerLevel.LEVEL_3_STOP: {
            'daily_pnl_pct': -8.0,
            'drawdown_pct': -20.0,
            'action': 'stop_new_trades',
            'position_limit_pct': 0.0
        },
        CircuitBreakerLevel.LEVEL_4_KILL: {
            'daily_pnl_pct': -10.0,
            'drawdown_pct': -25.0,
            'action': 'kill_switch',
            'position_limit_pct': 0.0
        }
    }
    
    def __init__(self, initial_capital: float, rolling_window: int = 30,
                 var_confidence: float = 0.95, var_method: str = 'historical'):
        self.initial_capital = initial_capital
        self.rolling_window = rolling_window
        self.var_confidence = var_confidence
        self.var_method = var_method
        
        # State tracking
        self.peak_capital = initial_capital
        self.current_capital = initial_capital
        self.daily_start_capital = initial_capital
        self.returns_history: List[float] = []
        self.equity_curve: List[float] = [initial_capital]
        self.alerts_history: List[Alert] = []
        self.current_cb_level = CircuitBreakerLevel.NORMAL
        self.kill_switch_active = False
        
    def update_capital(self, new_capital: float) -> None:
        """Update current capital and track metrics."""
        if new_capital > self.peak_capital:
            self.peak_capital = new_capital
            
        # Calculate daily PnL (reset at start of each day)
        daily_pnl = (new_capital - self.daily_start_capital) / self.daily_start_capital * 100
        
        # Calculate drawdown
        drawdown = (new_capital - self.peak_capital) / self.peak_capital * 100
        
        # Track returns for VaR calculation
        if len(self.equity_curve) > 0:
            prev_capital = self.equity_curve[-1]
            if prev_capital > 0:
                daily_return = (new_capital - prev_capital) / prev_capital
                self.returns_history.append(daily_return)
                
                # Keep only rolling window
                if len(self.returns_history) > self.rolling_window:
                    self.returns_history = self.returns_history[-self.rolling_window:]
        
        self.current_capital = new_capital
        self.equity_curve.append(new_capital)
        
    def reset_daily(self) -> None:
        """Reset daily PnL tracking (call at start of each trading day)."""
        self.daily_start_capital = self.current_capital
        
    def calculate_var_historical(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """Calculate VaR using historical method."""
        if len(returns) < 10:
            return 0.0
        return np.percentile(returns, (1 - confidence) * 100) * 100  # Convert to %
    
    def calculate_cvar_historical(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """Calculate CVaR (Expected Shortfall) using historical method."""
        if len(returns) < 10:
            return 0.0
        var = self.calculate_var_historical(returns, confidence)
        tail_returns = returns[returns <= var / 100]
        if len(tail_returns) == 0:
            return var
        return np.mean(tail_returns) * 100  # Convert to %
    
    def calculate_var_parametric(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """Calculate VaR using parametric (normal) method."""
        if len(returns) < 10:
            return 0.0
        mean = np.mean(returns)
        std = np.std(returns)
        from scipy.stats import norm
        z_score = norm.ppf(1 - confidence)
        return (mean + z_score * std) * 100  # Convert to %
    
    def calculate_cvar_parametric(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """Calculate CVaR using parametric method."""
        if len(returns) < 10:
            return 0.0
        var = self.calculate_var_parametric(returns, confidence)
        from scipy.stats import norm
        z_score = norm.ppf(1 - confidence)
        # CVaR for normal distribution: mean - std * phi(z) / (1-confidence)
        pdf_z = norm.pdf(z_score)
        cvar = np.mean(returns) - np.std(returns) * pdf_z / (1 - confidence)
        return cvar * 100  # Convert to %
    
    def calculate_var_monte_carlo(self, returns: np.ndarray, confidence: float = 0.95,
                                   n_sims: int = 10000) -> float:
        """Calculate VaR using Monte Carlo simulation."""
        if len(returns) < 10:
            return 0.0
        mean = np.mean(returns)
        std = np.std(returns)
        
        # Simulate returns
        simulated_returns = np.random.normal(mean, std, n_sims)
        return np.percentile(simulated_returns, (1 - confidence) * 100) * 100
    
    def calculate_cvar_monte_carlo(self, returns: np.ndarray, confidence: float = 0.95,
                                    n_sims: int = 10000) -> float:
        """Calculate CVaR using Monte Carlo simulation."""
        if len(returns) < 10:
            return 0.0
        var = self.calculate_var_monte_carlo(returns, confidence, n_sims)
        mean = np.mean(returns)
        std = np.std(returns)
        simulated_returns = np.random.normal(mean, std, n_sims)
        tail_returns = simulated_returns[simulated_returns <= var / 100]
        if len(tail_returns) == 0:
            return var
        return np.mean(tail_returns) * 100
    
    def calculate_var(self, returns: Optional[np.ndarray] = None) -> Tuple[float, float]:
        """
        Calculate VaR and CVaR.
        
        Returns: (VaR, CVaR) in percentage terms
        """
        if returns is None:
            returns = np.array(self.returns_history)
        
        if len(returns) < 10:
            return 0.0, 0.0
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            if self.var_method == 'historical':
                var = self.calculate_var_historical(returns, self.var_confidence)
                cvar = self.calculate_cvar_historical(returns, self.var_confidence)
            elif self.var_method == 'parametric':
                var = self.calculate_var_parametric(returns, self.var_confidence)
                cvar = self.calculate_cvar_parametric(returns, self.var_confidence)
            elif self.var_method == 'monte_carlo':
                var = self.calculate_var_monte_carlo(returns, self.var_confidence)
                cvar = self.calculate_cvar_monte_carlo(returns, self.var_confidence)
            else:
                var = self.calculate_var_historical(returns, self.var_confidence)
                cvar = self.calculate_cvar_historical(returns, self.var_confidence)
        
        return var, cvar
    
    def determine_circuit_breaker_level(self, daily_pnl: float, drawdown: float) -> CircuitBreakerLevel:
        """Determine current circuit breaker level based on metrics."""
        # Check from most severe to least severe
        for level in [CircuitBreakerLevel.LEVEL_4_KILL, 
                      CircuitBreakerLevel.LEVEL_3_STOP,
                      CircuitBreakerLevel.LEVEL_2_REDUCE,
                      CircuitBreakerLevel.LEVEL_1_WARNING]:
            threshold = self.CB_THRESHOLDS[level]
            if daily_pnl <= threshold['daily_pnl_pct'] or drawdown <= threshold['drawdown_pct']:
                return level
        
        return CircuitBreakerLevel.NORMAL
    
    def generate_alerts(self, daily_pnl: float, drawdown: float, 
                        cb_level: CircuitBreakerLevel) -> List[Alert]:
        """Generate alerts based on current metrics and CB level."""
        alerts = []
        now = pd.Timestamp.now()
        
        if cb_level != CircuitBreakerLevel.NORMAL:
            threshold = self.CB_THRESHOLDS[cb_level]
            
            # Determine severity
            if cb_level == CircuitBreakerLevel.LEVEL_4_KILL:
                severity = AlertSeverity.EMERGENCY
            elif cb_level == CircuitBreakerLevel.LEVEL_3_STOP:
                severity = AlertSeverity.CRITICAL
            elif cb_level == CircuitBreakerLevel.LEVEL_2_REDUCE:
                severity = AlertSeverity.WARNING
            else:
                severity = AlertSeverity.INFO
            
            # Create alert for the triggering metric
            if daily_pnl <= threshold['daily_pnl_pct']:
                alert = Alert(
                    timestamp=now,
                    severity=severity,
                    message=f"Circuit Breaker {cb_level.value} triggered by Daily PnL",
                    metric="daily_pnl_pct",
                    value=daily_pnl,
                    threshold=threshold['daily_pnl_pct'],
                    cb_level=cb_level
                )
                alerts.append(alert)
            
            if drawdown <= threshold['drawdown_pct']:
                alert = Alert(
                    timestamp=now,
                    severity=severity,
                    message=f"Circuit Breaker {cb_level.value} triggered by Drawdown",
                    metric="drawdown_pct",
                    value=drawdown,
                    threshold=threshold['drawdown_pct'],
                    cb_level=cb_level
                )
                alerts.append(alert)
        
        return alerts
    
    def check_risk_metrics(self) -> RiskMetrics:
        """
        Check all risk metrics and return comprehensive RiskMetrics object.
        
        Call this before each trade decision.
        """
        now = pd.Timestamp.now()
        
        # Calculate current metrics
        daily_pnl = (self.current_capital - self.daily_start_capital) / self.daily_start_capital * 100
        drawdown = (self.current_capital - self.peak_capital) / self.peak_capital * 100
        
        # Calculate volatility
        if len(self.returns_history) > 5:
            volatility = np.std(self.returns_history) * np.sqrt(365) * 100
        else:
            volatility = 0.0
        
        # Calculate VaR/CVaR
        var_95, cvar_95 = self.calculate_var()
        var_99, cvar_99 = self.calculate_var(np.array(self.returns_history), )
        var_99 = self.calculate_var_historical(np.array(self.returns_history), 0.99)
        cvar_99 = self.calculate_cvar_historical(np.array(self.returns_history), 0.99)
        
        # Determine circuit breaker level
        cb_level = self.determine_circuit_breaker_level(daily_pnl, drawdown)
        
        # Update state
        self.current_cb_level = cb_level
        
        if cb_level == CircuitBreakerLevel.LEVEL_4_KILL:
            self.kill_switch_active = True
        
        # Generate alerts
        alerts = self.generate_alerts(daily_pnl, drawdown, cb_level)
        self.alerts_history.extend(alerts)
        
        # Determine trading status
        trading_allowed = cb_level not in [
            CircuitBreakerLevel.LEVEL_3_STOP,
            CircuitBreakerLevel.LEVEL_4_KILL
        ] and not self.kill_switch_active
        
        position_limit = self.CB_THRESHOLDS[cb_level]['position_limit_pct'] if cb_level != CircuitBreakerLevel.NORMAL else 100.0
        
        return RiskMetrics(
            timestamp=now,
            var_95=var_95,
            cvar_95=cvar_95,
            var_99=var_99,
            cvar_99=cvar_99,
            daily_pnl_pct=daily_pnl,
            drawdown_pct=drawdown,
            volatility=volatility,
            circuit_breaker_level=cb_level,
            trading_allowed=trading_allowed,
            position_size_limit_pct=position_limit,
            alerts=alerts
        )
    
    def activate_kill_switch(self) -> None:
        """Manually activate kill switch (emergency stop)."""
        self.kill_switch_active = True
        self.current_cb_level = CircuitBreakerLevel.LEVEL_4_KILL
        
        alert = Alert(
            timestamp=pd.Timestamp.now(),
            severity=AlertSeverity.EMERGENCY,
            message="Kill Switch manually activated",
            metric="manual_override",
            value=1.0,
            threshold=0.0,
            cb_level=CircuitBreakerLevel.LEVEL_4_KILL
        )
        self.alerts_history.append(alert)
    
    def reset_kill_switch(self) -> None:
        """Reset kill switch (requires manual approval)."""
        self.kill_switch_active = False
        self.current_cb_level = CircuitBreakerLevel.NORMAL
        
    def get_summary(self) -> Dict:
        """Get human-readable risk summary."""
        metrics = self.check_risk_metrics()
        
        return {
            "status": "KILL_SWITCH_ACTIVE" if self.kill_switch_active else metrics.circuit_breaker_level.value,
            "trading_allowed": metrics.trading_allowed,
            "daily_pnl": f"{metrics.daily_pnl_pct:.2f}%",
            "drawdown": f"{metrics.drawdown_pct:.2f}%",
            "var_95": f"{metrics.var_95:.2f}%",
            "cvar_95": f"{metrics.cvar_95:.2f}%",
            "volatility": f"{metrics.volatility:.1f}%",
            "position_limit": f"{metrics.position_size_limit_pct:.0f}%",
            "n_alerts": len(self.alerts_history)
        }


if __name__ == "__main__":
    # Test Risk Monitor
    print("🐉 Risk Monitor Test")
    print("=" * 50)
    
    monitor = RiskMonitor(initial_capital=10000, rolling_window=30)
    
    # Simulate some returns
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.03, 50)
    
    capital = 10000
    for i, ret in enumerate(returns):
        capital = capital * (1 + ret)
        monitor.update_capital(capital)
        
        if i % 10 == 0:
            metrics = monitor.check_risk_metrics()
            print(f"\nDay {i}:")
            print(f"  Capital: ${capital:,.2f}")
            print(f"  Daily PnL: {metrics.daily_pnl_pct:.2f}%")
            print(f"  Drawdown: {metrics.drawdown_pct:.2f}%")
            print(f"  VaR 95%: {metrics.var_95:.2f}%")
            print(f"  CVaR 95%: {metrics.cvar_95:.2f}%")
            print(f"  CB Level: {metrics.circuit_breaker_level.value}")
            print(f"  Trading Allowed: {metrics.trading_allowed}")
    
    print("\n" + "=" * 50)
    print("Final Summary:")
    summary = monitor.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
