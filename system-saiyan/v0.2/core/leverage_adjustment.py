"""
🐉 Leverage Adjustment Module - Système Saiyan v0.2

Implements leverage effect adjustment based on EGARCH findings (Semaine 33):
- γ = -0.0467 < 0 → Bad news increases vol MORE than good news
- Half-life: ~7 jours pour un choc de volatilité
- Critical pour risk management: renforcer stops après bad news

Semaine 33 Results (BTC Real Data 2023-2026):
- EGARCH γ = -0.0467 (leverage effect confirmé)
- AIC: 4567.70 (vs 4573.18 GARCH) → EGARCH meilleur ✅
- Vol daily: 2.08% | Annualized: 39.75%
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class LeverageState(Enum):
    """Leverage effect state based on recent returns."""
    NORMAL = "NORMAL"  # No recent bad news
    WARNING = "WARNING"  # Minor bad news (-2% to -5%)
    CRITICAL = "CRITICAL"  # Major bad news (<-5%)
    RECOVERY = "RECOVERY"  # Recovering from bad news (within half-life)


@dataclass
class LeverageAdjustment:
    """Leverage adjustment factors."""
    state: LeverageState
    position_size_multiplier: float  # 0.5x to 1.0x
    circuit_breaker_penalty: float  # Tighten thresholds by this %
    half_life_remaining_days: int
    last_bad_news_date: Optional[datetime]
    last_bad_news_return: float


class LeverageAdjustmentModel:
    """
    Leverage effect adjustment based on EGARCH findings.
    
    Key insights from Semaine 33:
    - γ = -0.0467 < 0 → Bad news increases vol more than good news
    - Half-life = 6.9 jours → Shock takes ~7 days to halve
    - After crash (-5%): vol spike durable
    
    Applications:
    1. Position sizing: Reduce after bad news
    2. Circuit breakers: Tighten thresholds after crashes
    3. Strategy routing: Prefer mean-reversion after shocks
    """
    
    # Return thresholds for leverage state
    RETURN_THRESHOLDS = {
        LeverageState.CRITICAL: -0.05,   # <-5% = crash
        LeverageState.WARNING: -0.02,    # -2% to -5% = bad news
        LeverageState.NORMAL: 0.0        # >-2% = normal
    }
    
    # Position size multipliers by state
    POSITION_MULTIPLIERS = {
        LeverageState.NORMAL: 1.0,       # Full size
        LeverageState.RECOVERY: 0.7,     # -30% after bad news
        LeverageState.WARNING: 0.5,      # -50% on warning
        LeverageState.CRITICAL: 0.3      # -70% on crash!
    }
    
    # Circuit breaker tightening by state
    CB_PENALTIES = {
        LeverageState.NORMAL: 0.0,       # No penalty
        LeverageState.RECOVERY: 0.15,    # -15% thresholds
        LeverageState.WARNING: 0.25,     # -25% thresholds
        LeverageState.CRITICAL: 0.40     # -40% thresholds!
    }
    
    # EGARCH half-life (Semaine 33)
    HALF_LIFE_DAYS = 6.9
    
    def __init__(self, lookback_days: int = 30):
        """
        Initialize leverage adjustment model.
        
        Args:
            lookback_days: Days to track for recent bad news
        """
        self.lookback_days = lookback_days
        self.recent_returns: List[Tuple[datetime, float]] = []
        self.last_bad_news_date: Optional[datetime] = None
        self.last_bad_news_return: float = 0.0
        self.current_state = LeverageState.NORMAL
        
    def add_return(self, date: datetime, return_pct: float) -> LeverageAdjustment:
        """
        Add a daily return and update leverage state.
        
        Args:
            date: Date of return
            return_pct: Daily return in decimal (e.g., -0.05 for -5%)
            
        Returns:
            LeverageAdjustment with current state and multipliers
        """
        # Add to history
        self.recent_returns.append((date, return_pct))
        
        # Trim to lookback window
        cutoff = date - timedelta(days=self.lookback_days)
        self.recent_returns = [
            (d, r) for d, r in self.recent_returns if d >= cutoff
        ]
        
        # Check if this is bad news
        if return_pct < self.RETURN_THRESHOLDS[LeverageState.WARNING]:
            self.last_bad_news_date = date
            self.last_bad_news_return = return_pct
            
            # Determine state based on severity
            if return_pct < self.RETURN_THRESHOLDS[LeverageState.CRITICAL]:
                self.current_state = LeverageState.CRITICAL
            else:
                self.current_state = LeverageState.WARNING
        else:
            # Check if we're in recovery
            if self.last_bad_news_date is not None:
                days_since = (date - self.last_bad_news_date).days
                if days_since <= self.HALF_LIFE_DAYS:
                    self.current_state = LeverageState.RECOVERY
                else:
                    self.current_state = LeverageState.NORMAL
            else:
                self.current_state = LeverageState.NORMAL
        
        # Calculate adjustment
        return self.get_adjustment(date)
    
    def get_adjustment(self, current_date: Optional[datetime] = None) -> LeverageAdjustment:
        """
        Get current leverage adjustment factors.
        
        Args:
            current_date: Current date (default: now)
            
        Returns:
            LeverageAdjustment with multipliers and state
        """
        if current_date is None:
            current_date = datetime.now()
        
        # Calculate half-life remaining
        half_life_remaining = 0
        if self.last_bad_news_date is not None:
            days_since = (current_date - self.last_bad_news_date).days
            half_life_remaining = max(0, int(self.HALF_LIFE_DAYS - days_since))
        
        # Determine state if no recent return added
        if self.current_state == LeverageState.RECOVERY:
            if half_life_remaining == 0:
                self.current_state = LeverageState.NORMAL
        
        # Get multipliers
        position_mult = self.POSITION_MULTIPLIERS.get(
            self.current_state, 1.0
        )
        cb_penalty = self.CB_PENALTIES.get(
            self.current_state, 0.0
        )
        
        return LeverageAdjustment(
            state=self.current_state,
            position_size_multiplier=position_mult,
            circuit_breaker_penalty=cb_penalty,
            half_life_remaining_days=half_life_remaining,
            last_bad_news_date=self.last_bad_news_date,
            last_bad_news_return=self.last_bad_news_return
        )
    
    def adjust_position_size(self, base_size: float, 
                             current_date: Optional[datetime] = None) -> float:
        """
        Adjust position size based on leverage effect.
        
        Args:
            base_size: Base position size (from Kelly, risk parity, etc.)
            current_date: Current date
            
        Returns:
            Adjusted position size
        """
        adjustment = self.get_adjustment(current_date)
        return base_size * adjustment.position_size_multiplier
    
    def adjust_circuit_breaker_threshold(self, base_threshold: float,
                                         current_date: Optional[datetime] = None) -> float:
        """
        Adjust circuit breaker threshold based on leverage effect.
        
        After bad news, tighten thresholds (make more conservative).
        
        Args:
            base_threshold: Base CB threshold (e.g., -10% for kill switch)
            current_date: Current date
            
        Returns:
            Adjusted threshold (more negative = more conservative)
        """
        adjustment = self.get_adjustment(current_date)
        penalty = adjustment.circuit_breaker_penalty
        
        # Tighten threshold (make it less negative)
        # Example: -10% with 40% penalty → -6%
        adjusted = base_threshold * (1 - penalty)
        
        return adjusted
    
    def get_leverage_adjusted_var(self, base_var: float,
                                   current_date: Optional[datetime] = None) -> float:
        """
        Adjust VaR estimate for leverage effect.
        
        After bad news, increase VaR estimate (more conservative).
        
        Args:
            base_var: Base VaR estimate (positive number, e.g., 3.6 for 3.6%)
            current_date: Current date
            
        Returns:
            Adjusted VaR (higher = more conservative)
        """
        adjustment = self.get_adjustment(current_date)
        
        # EGARCH shows vol increases ~20-30% after bad news
        # Use position multiplier inverse as proxy
        vol_increase = (1.0 / adjustment.position_size_multiplier) - 1.0
        
        adjusted_var = base_var * (1.0 + vol_increase)
        return adjusted_var
    
    def get_recent_bad_news(self, days: int = 7) -> List[Tuple[datetime, float]]:
        """
        Get recent bad news events.
        
        Args:
            days: Lookback window
            
        Returns:
            List of (date, return) tuples for bad news days
        """
        cutoff = datetime.now() - timedelta(days=days)
        return [
            (d, r) for d, r in self.recent_returns
            if d >= cutoff and r < self.RETURN_THRESHOLDS[LeverageState.WARNING]
        ]
    
    def reset(self) -> None:
        """Reset leverage tracking (use with caution)."""
        self.recent_returns = []
        self.last_bad_news_date = None
        self.last_bad_news_return = 0.0
        self.current_state = LeverageState.NORMAL


class LeverageAdjustedRiskMonitor:
    """
    Risk monitor with leverage effect adjustments.
    
    Wraps standard RiskMonitor with EGARCH-based adjustments:
    - Position sizing reduced after bad news
    - Circuit breakers tightened after crashes
    - VaR/CVaR increased during leverage effect periods
    """
    
    def __init__(self, risk_monitor, leverage_model: Optional[LeverageAdjustmentModel] = None):
        """
        Initialize leverage-adjusted risk monitor.
        
        Args:
            risk_monitor: Base RiskMonitor instance
            leverage_model: LeverageAdjustmentModel (created if None)
        """
        self.risk_monitor = risk_monitor
        self.leverage_model = leverage_model or LeverageAdjustmentModel()
    
    def update_return(self, date: datetime, return_pct: float) -> LeverageAdjustment:
        """
        Update leverage model with new return.
        
        Args:
            date: Date of return
            return_pct: Daily return in decimal
            
        Returns:
            LeverageAdjustment with current state
        """
        return self.leverage_model.add_return(date, return_pct)
    
    def get_adjusted_position_limit(self, base_limit: float,
                                     current_date: Optional[datetime] = None) -> float:
        """
        Get leverage-adjusted position size limit.
        
        Args:
            base_limit: Base position limit from risk monitor
            current_date: Current date
            
        Returns:
            Adjusted limit (reduced after bad news)
        """
        return self.leverage_model.adjust_position_size(base_limit, current_date)
    
    def get_adjusted_cb_thresholds(self, 
                                    current_date: Optional[datetime] = None) -> Dict:
        """
        Get leverage-adjusted circuit breaker thresholds.
        
        Args:
            current_date: Current date
            
        Returns:
            Dict with adjusted thresholds for each CB level
        """
        from system_saiyan.v0.2.core.risk_monitor import CircuitBreakerLevel
        
        base_thresholds = self.risk_monitor.CB_THRESHOLDS.copy()
        adjusted = {}
        
        for level, threshold in base_thresholds.items():
            adjusted[level] = {
                'daily_pnl_pct': self.leverage_model.adjust_circuit_breaker_threshold(
                    threshold['daily_pnl_pct'], current_date
                ),
                'drawdown_pct': self.leverage_model.adjust_circuit_breaker_threshold(
                    threshold['drawdown_pct'], current_date
                ),
                'action': threshold['action'],
                'position_limit_pct': threshold['position_limit_pct']
            }
        
        return adjusted
    
    def get_status(self) -> Dict:
        """
        Get current leverage adjustment status.
        
        Returns:
            Dict with current state and adjustments
        """
        adjustment = self.leverage_model.get_adjustment()
        
        return {
            'leverage_state': adjustment.state.value,
            'position_multiplier': adjustment.position_size_multiplier,
            'cb_penalty_pct': adjustment.circuit_breaker_penalty * 100,
            'half_life_remaining_days': adjustment.half_life_remaining_days,
            'last_bad_news_date': adjustment.last_bad_news_date.isoformat() if adjustment.last_bad_news_date else None,
            'last_bad_news_return_pct': adjustment.last_bad_news_return * 100,
            'recent_bad_news_7d': len(self.leverage_model.get_recent_bad_news(7))
        }


# Example usage
if __name__ == "__main__":
    # Simulate leverage effect tracking
    model = LeverageAdjustmentModel()
    
    # Normal period
    adj = model.add_return(datetime(2026, 5, 20), 0.01)  # +1%
    print(f"Normal: position_mult={adj.position_size_multiplier}")
    
    # Bad news (-3%)
    adj = model.add_return(datetime(2026, 5, 21), -0.03)  # -3%
    print(f"Warning: position_mult={adj.position_size_multiplier}, state={adj.state.value}")
    
    # Crash (-7%)
    adj = model.add_return(datetime(2026, 5, 22), -0.07)  # -7%
    print(f"Critical: position_mult={adj.position_size_multiplier}, state={adj.state.value}")
    
    # Recovery days
    for i in range(10):
        date = datetime(2026, 5, 23) + timedelta(days=i)
        adj = model.add_return(date, 0.005)  # Small gains
        print(f"Day {i+1}: state={adj.state.value}, half_life_remaining={adj.half_life_remaining_days}d")
