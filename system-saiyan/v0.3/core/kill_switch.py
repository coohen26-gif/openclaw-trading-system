#!/usr/bin/env python3
"""
Kill Switch - Saiyan V0.3

Persistent kill switch that survives restarts.
Triggers on:
- Daily loss > threshold
- Max drawdown > threshold
- Manual trigger (API/emergency)

Author: Saiyan Trading System
Date: May 2026
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class KillReason(Enum):
    DAILY_LOSS = "daily_loss"
    MAX_DRAWDOWN = "max_drawdown"
    MANUAL = "manual"
    SYSTEM_ERROR = "system_error"
    RISK_LIMIT = "risk_limit"


@dataclass
class KillSwitchState:
    """Kill switch state."""
    is_active: bool = False
    triggered_at: Optional[str] = None
    reason: Optional[str] = None
    daily_loss: Optional[float] = None
    drawdown: Optional[float] = None
    triggered_by: Optional[str] = None
    reset_at: Optional[str] = None
    notes: Optional[str] = None


class KillSwitch:
    """
    Persistent kill switch for trading system.
    
    Survives restarts by persisting state to file.
    """
    
    def __init__(
        self,
        state_file: str = "data/kill_switch.json",
        daily_loss_threshold: float = -0.05,  # -5%
        max_drawdown_threshold: float = -0.20,  # -20%
        auto_reset_hours: Optional[int] = 24
    ):
        """
        Initialize kill switch.
        
        Args:
            state_file: Path to persist state
            daily_loss_threshold: Daily loss % to trigger
            max_drawdown_threshold: Max drawdown % to trigger
            auto_reset_hours: Auto-reset after N hours (None = manual only)
        """
        self.state_file = Path(state_file)
        self.daily_loss_threshold = daily_loss_threshold
        self.max_drawdown_threshold = max_drawdown_threshold
        self.auto_reset_hours = auto_reset_hours
        
        self.state = KillSwitchState()
        self._load_state()
    
    def _load_state(self):
        """Load state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.state = KillSwitchState(**data)
                    logger.info(f"📊 Kill switch state loaded: active={self.state.is_active}")
                    
                    # Check auto-reset
                    if self.state.is_active and self.auto_reset_hours:
                        triggered = datetime.fromisoformat(self.state.triggered_at)
                        if datetime.now() - triggered > timedelta(hours=self.auto_reset_hours):
                            logger.info("⏰ Auto-reset trigger (24h elapsed)")
                            self.reset(reason="auto_reset")
            except Exception as e:
                logger.error(f"Failed to load kill switch state: {e}")
                self.state = KillSwitchState()
        else:
            logger.info("ℹ️  Kill switch initialized (no prior state)")
    
    def _save_state(self):
        """Save state to file."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(asdict(self.state), f, indent=2)
            logger.debug("💾 Kill switch state saved")
        except Exception as e:
            logger.error(f"Failed to save kill switch state: {e}")
    
    def check_daily_loss(self, daily_pnl_pct: float) -> bool:
        """
        Check if daily loss threshold breached.
        
        Args:
            daily_pnl_pct: Daily PnL as % (negative for loss)
        
        Returns:
            True if kill switch triggered
        """
        if self.state.is_active:
            return True
        
        if daily_pnl_pct < self.daily_loss_threshold:
            logger.warning(
                f"🚨 KILL SWITCH: Daily loss {daily_pnl_pct:.2%} < threshold {self.daily_loss_threshold:.2%}"
            )
            self.trigger(
                reason=KillReason.DAILY_LOSS,
                daily_loss=daily_pnl_pct,
                triggered_by="risk_monitor"
            )
            return True
        
        return False
    
    def check_drawdown(self, current_drawdown: float) -> bool:
        """
        Check if max drawdown threshold breached.
        
        Args:
            current_drawdown: Current drawdown as % (negative)
        
        Returns:
            True if kill switch triggered
        """
        if self.state.is_active:
            return True
        
        if current_drawdown < self.max_drawdown_threshold:
            logger.warning(
                f"🚨 KILL SWITCH: Drawdown {current_drawdown:.2%} < threshold {self.max_drawdown_threshold:.2%}"
            )
            self.trigger(
                reason=KillReason.MAX_DRAWDOWN,
                drawdown=current_drawdown,
                triggered_by="risk_monitor"
            )
            return True
        
        return False
    
    def trigger(
        self,
        reason: KillReason,
        daily_loss: Optional[float] = None,
        drawdown: Optional[float] = None,
        triggered_by: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """
        Manually trigger kill switch.
        
        Args:
            reason: Reason for triggering
            daily_loss: Daily loss % if applicable
            drawdown: Drawdown % if applicable
            triggered_by: Component that triggered
            notes: Additional notes
        """
        self.state.is_active = True
        self.state.triggered_at = datetime.now().isoformat()
        self.state.reason = reason.value
        self.state.daily_loss = daily_loss
        self.state.drawdown = drawdown
        self.state.triggered_by = triggered_by
        self.state.notes = notes
        self.state.reset_at = None
        
        self._save_state()
        
        logger.critical(
            f"🆘 KILL SWITCH ACTIVATED: {reason.value} by {triggered_by}"
        )
    
    def reset(self, reason: str = "manual", notes: Optional[str] = None):
        """
        Reset kill switch.
        
        Args:
            reason: Reason for reset
            notes: Additional notes
        """
        old_state = asdict(self.state)
        
        self.state.is_active = False
        self.state.reset_at = datetime.now().isoformat()
        self.state.notes = f"Reset: {reason}. " + (notes or "")
        
        # Keep historical data
        self.state.reason = f"{old_state.get('reason')} (reset: {reason})"
        
        self._save_state()
        
        logger.info(f"✅ Kill switch RESET: {reason}")
    
    def is_active(self) -> bool:
        """Check if kill switch is active."""
        # Auto-reset check
        if self.state.is_active and self.auto_reset_hours:
            triggered = datetime.fromisoformat(self.state.triggered_at)
            if datetime.now() - triggered > timedelta(hours=self.auto_reset_hours):
                self.reset(reason="auto_reset")
                return False
        
        return self.state.is_active
    
    def allow_trading(self) -> bool:
        """Check if trading is allowed."""
        return not self.is_active()
    
    def get_state(self) -> Dict[str, Any]:
        """Get full state as dict."""
        return asdict(self.state)
    
    def get_status_message(self) -> str:
        """Get human-readable status message."""
        if not self.state.is_active:
            return "✅ Kill switch: INACTIVE (trading allowed)"
        
        msg = f"🆘 KILL SWITCH ACTIVE\n"
        msg += f"Reason: {self.state.reason}\n"
        msg += f"Triggered: {self.state.triggered_at}\n"
        
        if self.state.daily_loss is not None:
            msg += f"Daily loss: {self.state.daily_loss:.2%}\n"
        
        if self.state.drawdown is not None:
            msg += f"Drawdown: {self.state.drawdown:.2%}\n"
        
        if self.state.triggered_by:
            msg += f"By: {self.state.triggered_by}\n"
        
        if self.state.reset_at:
            msg += f"Reset at: {self.state.reset_at}\n"
        
        return msg


# CLI test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n🧪 Testing Kill Switch...\n")
    
    # Initialize
    ks = KillSwitch(state_file="data/test_kill_switch.json")
    
    # Test 1: Normal state
    print(f"Initial state: {ks.get_status_message()}")
    assert ks.allow_trading() == True
    
    # Test 2: Trigger on daily loss
    triggered = ks.check_daily_loss(-0.06)  # -6% loss
    print(f"After -6% daily: {ks.get_status_message()}")
    assert triggered == True
    assert ks.allow_trading() == False
    
    # Test 3: Reset
    ks.reset(reason="test_reset", notes="Testing purposes")
    print(f"After reset: {ks.get_status_message()}")
    assert ks.allow_trading() == True
    
    # Test 4: Trigger on drawdown
    triggered = ks.check_drawdown(-0.25)  # -25% DD
    print(f"After -25% DD: {ks.get_status_message()}")
    assert triggered == True
    
    # Test 5: Manual trigger
    ks.reset()
    ks.trigger(
        reason=KillReason.MANUAL,
        triggered_by="api_endpoint",
        notes="Emergency stop"
    )
    print(f"Manual trigger: {ks.get_status_message()}")
    
    # Cleanup
    Path("data/test_kill_switch.json").unlink(missing_ok=True)
    
    print("\n✅ All tests passed\n")
