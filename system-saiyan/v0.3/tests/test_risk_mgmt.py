"""
🧪 Tests for Risk Management - Saiyan v0.3

Tests cover:
- Kill Switch (trigger, reset, persistence)
- Daily loss limits
- Max drawdown limits
- Auto-reset functionality

Coverage target: >90%
"""

import pytest
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.kill_switch import (
    KillSwitch,
    KillReason,
    KillSwitchState
)


class TestKillReason:
    """Test KillReason enum."""
    
    def test_kill_reason_values(self):
        """Test kill reason enum has correct values."""
        assert KillReason.DAILY_LOSS.value == "daily_loss"
        assert KillReason.MAX_DRAWDOWN.value == "max_drawdown"
        assert KillReason.MANUAL.value == "manual"
        assert KillReason.SYSTEM_ERROR.value == "system_error"
        assert KillReason.RISK_LIMIT.value == "risk_limit"
    
    def test_kill_reason_count(self):
        """Test there are 5 kill reasons."""
        assert len(list(KillReason)) == 5


class TestKillSwitchState:
    """Test KillSwitchState dataclass."""
    
    def test_default_state(self):
        """Test default state values."""
        state = KillSwitchState()
        
        assert state.is_active == False
        assert state.triggered_at is None
        assert state.reason is None
        assert state.daily_loss is None
        assert state.drawdown is None
        assert state.triggered_by is None
        assert state.reset_at is None
        assert state.notes is None
    
    def test_state_with_values(self):
        """Test state with custom values."""
        state = KillSwitchState(
            is_active=True,
            triggered_at="2024-01-01T12:00:00",
            reason="daily_loss",
            daily_loss=-0.06,
            triggered_by="risk_monitor"
        )
        
        assert state.is_active == True
        assert state.triggered_at == "2024-01-01T12:00:00"
        assert state.reason == "daily_loss"
        assert state.daily_loss == -0.06
        assert state.triggered_by == "risk_monitor"


class TestKillSwitchInit:
    """Test KillSwitch initialization."""
    
    def test_default_init(self, temp_kill_switch_file):
        """Test default initialization parameters."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        assert ks.daily_loss_threshold == -0.05  # -5%
        assert ks.max_drawdown_threshold == -0.20  # -20%
        assert ks.auto_reset_hours == 24
        assert ks.is_active() == False
    
    def test_custom_init(self, temp_kill_switch_file):
        """Test custom initialization parameters."""
        ks = KillSwitch(
            state_file=temp_kill_switch_file,
            daily_loss_threshold=-0.03,  # -3%
            max_drawdown_threshold=-0.15,  # -15%
            auto_reset_hours=12
        )
        
        assert ks.daily_loss_threshold == -0.03
        assert ks.max_drawdown_threshold == -0.15
        assert ks.auto_reset_hours == 12
    
    def test_no_auto_reset(self, temp_kill_switch_file):
        """Test initialization with no auto-reset."""
        ks = KillSwitch(
            state_file=temp_kill_switch_file,
            auto_reset_hours=None
        )
        
        assert ks.auto_reset_hours is None
    
    def test_creates_state_file_dir(self, tmp_path):
        """Test that init creates directory for state file."""
        state_file = str(tmp_path / "subdir" / "kill_switch.json")
        
        ks = KillSwitch(state_file=state_file)
        
        assert Path(state_file).parent.exists()


class TestKillSwitchDailyLoss:
    """Test daily loss checking."""
    
    def test_check_daily_loss_no_trigger(self, temp_kill_switch_file):
        """Test daily loss check below threshold."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        # Loss below threshold (-4% > -5%)
        triggered = ks.check_daily_loss(-0.04)
        
        assert triggered == False
        assert ks.is_active() == False
    
    def test_check_daily_loss_triggers(self, temp_kill_switch_file):
        """Test daily loss check triggers kill switch."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        # Loss above threshold (-6% < -5%)
        triggered = ks.check_daily_loss(-0.06)
        
        assert triggered == True
        assert ks.is_active() == True
        
        # Verify state
        state = ks.get_state()
        assert state['reason'] == 'daily_loss'
        assert state['daily_loss'] == -0.06
        assert state['triggered_by'] == 'risk_monitor'
    
    def test_check_daily_loss_at_threshold(self, temp_kill_switch_file):
        """Test daily loss exactly at threshold."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        # Exactly at threshold (-5%)
        triggered = ks.check_daily_loss(-0.05)
        
        # Should NOT trigger (need to be BELOW threshold)
        assert triggered == False
    
    def test_check_daily_loss_already_active(self, temp_kill_switch_file):
        """Test daily loss check when already active."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        # Trigger first
        ks.check_daily_loss(-0.06)
        assert ks.is_active() == True
        
        # Check again with smaller loss
        triggered = ks.check_daily_loss(-0.03)
        
        # Should return True (already active)
        assert triggered == True
    
    def test_check_daily_loss_positive_pnl(self, temp_kill_switch_file):
        """Test daily loss check with profit."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        triggered = ks.check_daily_loss(0.03)  # +3%
        
        assert triggered == False
        assert ks.is_active() == False


class TestKillSwitchDrawdown:
    """Test drawdown checking."""
    
    def test_check_drawdown_no_trigger(self, temp_kill_switch_file):
        """Test drawdown check below threshold."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        # Drawdown below threshold (-15% > -20%)
        triggered = ks.check_drawdown(-0.15)
        
        assert triggered == False
        assert ks.is_active() == False
    
    def test_check_drawdown_triggers(self, temp_kill_switch_file):
        """Test drawdown check triggers kill switch."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        # Drawdown above threshold (-25% < -20%)
        triggered = ks.check_drawdown(-0.25)
        
        assert triggered == True
        assert ks.is_active() == True
        
        # Verify state
        state = ks.get_state()
        assert state['reason'] == 'max_drawdown'
        assert state['drawdown'] == -0.25
        assert state['triggered_by'] == 'risk_monitor'
    
    def test_check_drawdown_at_threshold(self, temp_kill_switch_file):
        """Test drawdown exactly at threshold."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        # Exactly at threshold (-20%)
        triggered = ks.check_drawdown(-0.20)
        
        # Should NOT trigger (need to be BELOW threshold)
        assert triggered == False
    
    def test_check_drawdown_already_active(self, temp_kill_switch_file):
        """Test drawdown check when already active."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        # Trigger first
        ks.check_drawdown(-0.25)
        
        # Check again
        triggered = ks.check_drawdown(-0.10)
        
        assert triggered == True  # Already active


class TestKillSwitchTrigger:
    """Test manual trigger."""
    
    def test_manual_trigger(self, temp_kill_switch_file):
        """Test manual trigger."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        ks.trigger(
            reason=KillReason.MANUAL,
            triggered_by="api_endpoint",
            notes="Emergency stop"
        )
        
        assert ks.is_active() == True
        
        state = ks.get_state()
        assert state['reason'] == 'manual'
        assert state['triggered_by'] == 'api_endpoint'
        assert state['notes'] == 'Emergency stop'
    
    def test_manual_trigger_with_daily_loss(self, temp_kill_switch_file):
        """Test manual trigger with daily loss info."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        ks.trigger(
            reason=KillReason.DAILY_LOSS,
            daily_loss=-0.08,
            triggered_by="manual_override"
        )
        
        state = ks.get_state()
        assert state['reason'] == 'daily_loss'
        assert state['daily_loss'] == -0.08
    
    def test_manual_trigger_with_drawdown(self, temp_kill_switch_file):
        """Test manual trigger with drawdown info."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        ks.trigger(
            reason=KillReason.MAX_DRAWDOWN,
            drawdown=-0.30,
            triggered_by="risk_committee"
        )
        
        state = ks.get_state()
        assert state['reason'] == 'max_drawdown'
        assert state['drawdown'] == -0.30
    
    def test_manual_trigger_system_error(self, temp_kill_switch_file):
        """Test manual trigger for system error."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        ks.trigger(
            reason=KillReason.SYSTEM_ERROR,
            triggered_by="monitoring_system",
            notes="API connection lost"
        )
        
        state = ks.get_state()
        assert state['reason'] == 'system_error'
        assert state['notes'] == 'API connection lost'


class TestKillSwitchReset:
    """Test kill switch reset."""
    
    def test_reset_manual(self, temp_kill_switch_file):
        """Test manual reset."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        # Trigger first
        ks.check_daily_loss(-0.06)
        assert ks.is_active() == True
        
        # Reset
        ks.reset(reason="manual_reset", notes="Risk committee approved")
        
        assert ks.is_active() == False
        
        state = ks.get_state()
        assert 'reset: manual_reset' in state['reason']
        assert 'Risk committee approved' in state['notes']
        assert state['reset_at'] is not None
    
    def test_reset_auto(self, temp_kill_switch_file):
        """Test auto-reset after timeout."""
        ks = KillSwitch(
            state_file=temp_kill_switch_file,
            auto_reset_hours=24
        )
        
        # Trigger
        ks.check_daily_loss(-0.06)
        assert ks.is_active() == True
        
        # Mock time to simulate 25 hours later
        old_triggered_at = datetime.fromisoformat(ks.state.triggered_at)
        fake_now = old_triggered_at + timedelta(hours=25)
        
        with patch('core.kill_switch.datetime') as mock_datetime:
            mock_datetime.now.return_value = fake_now
            mock_datetime.fromisoformat = datetime.fromisoformat
            
            # Should auto-reset
            assert ks.is_active() == False
    
    def test_reset_keeps_history(self, temp_kill_switch_file):
        """Test reset preserves historical data."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        # Trigger
        ks.check_daily_loss(-0.06)
        original_reason = ks.state.reason
        
        # Reset
        ks.reset(reason="test_reset")
        
        state = ks.get_state()
        # Original reason should be preserved in modified form
        assert original_reason.split()[0] in state['reason'] or 'daily_loss' in state['reason']
    
    def test_allow_trading_after_reset(self, temp_kill_switch_file):
        """Test trading allowed after reset."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        # Trigger and reset
        ks.check_daily_loss(-0.06)
        ks.reset(reason="test")
        
        assert ks.allow_trading() == True


class TestKillSwitchPersistence:
    """Test kill switch state persistence."""
    
    def test_state_persisted_to_file(self, temp_kill_switch_file):
        """Test state is saved to file."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        # Trigger
        ks.check_daily_loss(-0.06)
        
        # Verify file exists
        assert Path(temp_kill_switch_file).exists()
        
        # Read and verify content
        with open(temp_kill_switch_file, 'r') as f:
            data = json.load(f)
        
        assert data['is_active'] == True
        assert data['reason'] == 'daily_loss'
    
    def test_state_loaded_on_init(self, temp_kill_switch_file):
        """Test state is loaded on initialization."""
        ks1 = KillSwitch(state_file=temp_kill_switch_file)
        
        # Trigger and save
        ks1.check_daily_loss(-0.06)
        
        # Create new instance (should load saved state)
        ks2 = KillSwitch(state_file=temp_kill_switch_file)
        
        assert ks2.is_active() == True
        assert ks2.state.reason == 'daily_loss'
    
    def test_state_corrupted_handled(self, temp_kill_switch_file):
        """Test handling of corrupted state file."""
        # Write invalid JSON
        with open(temp_kill_switch_file, 'w') as f:
            f.write("not valid json {{{")
        
        # Should not crash, should start fresh
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        assert ks.is_active() == False
    
    def test_state_file_not_exists(self, tmp_path):
        """Test initialization when state file doesn't exist."""
        state_file = str(tmp_path / "new_kill_switch.json")
        
        ks = KillSwitch(state_file=state_file)
        
        assert ks.is_active() == False
        assert not Path(state_file).exists()  # Not created until first save


class TestKillSwitchStatusMessage:
    """Test status message generation."""
    
    def test_status_inactive(self, temp_kill_switch_file):
        """Test status message when inactive."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        msg = ks.get_status_message()
        
        assert "INACTIVE" in msg
        assert "trading allowed" in msg.lower()
    
    def test_status_active_daily_loss(self, temp_kill_switch_file):
        """Test status message with daily loss trigger."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        ks.check_daily_loss(-0.06)
        
        msg = ks.get_status_message()
        
        assert "ACTIVE" in msg
        assert "Daily loss" in msg
        assert "-6.00%" in msg or "-0.06" in msg
    
    def test_status_active_drawdown(self, temp_kill_switch_file):
        """Test status message with drawdown trigger."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        ks.check_drawdown(-0.25)
        
        msg = ks.get_status_message()
        
        assert "ACTIVE" in msg
        assert "Drawdown" in msg
        assert "-25.00%" in msg or "-0.25" in msg
    
    def test_status_includes_trigger_info(self, temp_kill_switch_file):
        """Test status includes trigger details."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        ks.trigger(
            reason=KillReason.MANUAL,
            triggered_by="admin_user",
            notes="Scheduled maintenance"
        )
        
        msg = ks.get_status_message()
        
        assert "manual" in msg.lower()
        assert "admin_user" in msg
        assert "Scheduled maintenance" in msg


class TestKillSwitchEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_very_small_loss(self, temp_kill_switch_file):
        """Test very small loss doesn't trigger."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        triggered = ks.check_daily_loss(-0.0001)  # -0.01%
        
        assert triggered == False
    
    def test_very_large_loss(self, temp_kill_switch_file):
        """Test very large loss triggers."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        triggered = ks.check_daily_loss(-0.50)  # -50%
        
        assert triggered == True
    
    def test_zero_pnl(self, temp_kill_switch_file):
        """Test zero PnL doesn't trigger."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        triggered = ks.check_daily_loss(0.0)
        
        assert triggered == False
    
    def test_rapid_trigger_reset_cycle(self, temp_kill_switch_file):
        """Test rapid trigger/reset cycles."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        for _ in range(5):
            ks.check_daily_loss(-0.06)
            assert ks.is_active() == True
            ks.reset(reason="test_cycle")
            assert ks.is_active() == False
    
    def test_multiple_daily_loss_checks_same_day(self, temp_kill_switch_file):
        """Test multiple daily loss checks."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        # First check triggers
        ks.check_daily_loss(-0.06)
        
        # Second check returns True (already active)
        assert ks.check_daily_loss(-0.03) == True
        
        # State should still reflect original trigger
        state = ks.get_state()
        assert state['daily_loss'] == -0.06


# ============================================================================
# Integration Tests
# ============================================================================

class TestKillSwitchIntegration:
    """Integration tests for kill switch."""
    
    def test_full_workflow(self, temp_kill_switch_file):
        """Test complete kill switch workflow."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        # Initial state
        assert ks.allow_trading() == True
        
        # Simulate trading day with losses
        daily_returns = [-0.02, -0.015, -0.025, -0.01]  # Total: -7%
        total_loss = sum(daily_returns)
        
        # Check at end of day
        triggered = ks.check_daily_loss(total_loss)
        
        assert triggered == True
        assert ks.allow_trading() == False
        
        # Status message
        msg = ks.get_status_message()
        assert "ACTIVE" in msg
        
        # Reset next day
        ks.reset(reason="new_day", notes="Fresh start")
        
        assert ks.allow_trading() == True
        assert ks.is_active() == False
    
    def test_combined_risk_checks(self, temp_kill_switch_file):
        """Test both daily loss and drawdown checks."""
        ks = KillSwitch(state_file=temp_kill_switch_file)
        
        # Daily loss check passes
        assert ks.check_daily_loss(-0.03) == False
        
        # But drawdown triggers
        assert ks.check_drawdown(-0.25) == True
        
        # System is now blocked
        assert ks.allow_trading() == False
    
    def test_persistence_across_instances(self, temp_kill_switch_file, tmp_path):
        """Test state persists across different instances."""
        # Create and trigger
        ks1 = KillSwitch(state_file=temp_kill_switch_file)
        ks1.check_daily_loss(-0.06)
        
        # Create new instance in same "session"
        ks2 = KillSwitch(state_file=temp_kill_switch_file)
        
        # Should have same state
        assert ks2.is_active() == ks1.is_active()
        assert ks2.state.reason == ks1.state.reason
        assert ks2.state.daily_loss == ks1.state.daily_loss
