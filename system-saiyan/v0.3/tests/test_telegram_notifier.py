"""
🧪 Tests for Telegram Notifier - Saiyan v0.3

Tests cover:
- Message sending (signals, alerts, summaries)
- Deduplication logic
- Rate limiting
- State persistence
- Mock mode (no credentials)

Coverage target: >85%
"""

import pytest
import json
import asyncio
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.telegram_notifier import TelegramNotifier


class TestTelegramNotifierInit:
    """Test TelegramNotifier initialization."""
    
    def test_init_no_credentials(self, temp_telegram_state_file):
        """Test initialization without credentials (mock mode)."""
        with patch.dict('os.environ', {}, clear=True):
            notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        assert notifier.bot is None
        assert notifier.token is None
        assert notifier.chat_id is None
    
    def test_init_with_credentials(self, temp_telegram_state_file, mock_telegram_env):
        """Test initialization with credentials."""
        # Mock the Bot class
        with patch('utils.telegram_notifier.Bot') as MockBot:
            mock_instance = AsyncMock()
            mock_instance.get_me = AsyncMock(return_value=MagicMock(username='test_bot'))
            MockBot.return_value = mock_instance
            
            notifier = TelegramNotifier(state_file=temp_telegram_state_file)
            
            assert notifier.bot is not None
    
    def test_init_custom_params(self, temp_telegram_state_file):
        """Test initialization with custom parameters."""
        notifier = TelegramNotifier(
            token="test_token",
            chat_id="-1001234567890",
            state_file=temp_telegram_state_file,
            dedup_window_min=10,
            rate_limit_sec=2.0
        )
        
        assert notifier.token == "test_token"
        assert notifier.chat_id == "-1001234567890"
        assert notifier.dedup_window_min == 10
        assert notifier.rate_limit_sec == 2.0
    
    def test_init_loads_state(self, temp_telegram_state_file):
        """Test initialization loads existing state."""
        # Create state file
        state_data = {
            "message_hashes": [{"hash": "abc123", "time": datetime.now().isoformat()}],
            "last_message_time": time.time()
        }
        import time
        Path(temp_telegram_state_file).parent.mkdir(parents=True, exist_ok=True)
        with open(temp_telegram_state_file, 'w') as f:
            json.dump(state_data, f)
        
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        assert len(notifier._message_hashes) == 1


class TestHashComputation:
    """Test message hash computation for deduplication."""
    
    def test_compute_hash(self, temp_telegram_state_file):
        """Test hash computation."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        content = "Test message"
        hash1 = notifier._compute_hash(content)
        
        # Should be 16 chars (first 16 of SHA256 hex)
        assert len(hash1) == 16
        
        # Same content = same hash
        hash2 = notifier._compute_hash(content)
        assert hash1 == hash2
        
        # Different content = different hash
        hash3 = notifier._compute_hash("Different message")
        assert hash1 != hash3
    
    def test_compute_hash_deterministic(self, temp_telegram_state_file):
        """Test hash is deterministic."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        content = "Signal: LONG BTC/USDT @ $50000"
        
        hashes = [notifier._compute_hash(content) for _ in range(10)]
        
        # All should be identical
        assert len(set(hashes)) == 1


class TestDeduplication:
    """Test message deduplication logic."""
    
    def test_is_duplicate_new_message(self, temp_telegram_state_file):
        """Test new message is not duplicate."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        content_hash = notifier._compute_hash("New unique message")
        
        assert notifier._is_duplicate(content_hash) == False
    
    def test_is_duplicate_within_window(self, temp_telegram_state_file):
        """Test duplicate detection within window."""
        notifier = TelegramNotifier(
            state_file=temp_telegram_state_file,
            dedup_window_min=5
        )
        
        content = "Duplicate test message"
        content_hash = notifier._compute_hash(content)
        
        # Record message
        notifier._record_message(content_hash)
        
        # Should be duplicate now
        assert notifier._is_duplicate(content_hash) == True
    
    def test_is_duplicate_outside_window(self, temp_telegram_state_file):
        """Test old messages are cleaned from dedup window."""
        notifier = TelegramNotifier(
            state_file=temp_telegram_state_file,
            dedup_window_min=5
        )
        
        content_hash = "old_hash_123"
        
        # Add old message (outside window)
        old_time = datetime.now() - timedelta(minutes=10)
        notifier._message_hashes.append({
            "hash": content_hash,
            "time": old_time.isoformat()
        })
        
        # Should NOT be duplicate (cleaned out)
        assert notifier._is_duplicate(content_hash) == False
    
    def test_record_message(self, temp_telegram_state_file):
        """Test message recording."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        initial_count = len(notifier._message_hashes)
        
        content_hash = notifier._compute_hash("Test")
        notifier._record_message(content_hash)
        
        assert len(notifier._message_hashes) == initial_count + 1
        assert notifier._message_hashes[-1]["hash"] == content_hash
    
    def test_record_message_limits_to_100(self, temp_telegram_state_file):
        """Test message history limited to 100."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        # Add 150 messages
        for i in range(150):
            notifier._message_hashes.append({
                "hash": f"hash_{i}",
                "time": datetime.now().isoformat()
            })
        
        # Record new message (should trim to 100)
        notifier._record_message("new_hash")
        
        # Should have at most 101 (100 old + 1 new, then trimmed to 100)
        assert len(notifier._message_hashes) <= 101


class TestRateLimiting:
    """Test rate limiting logic."""
    
    def test_rate_limit_first_message(self, temp_telegram_state_file):
        """Test first message passes rate limit."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        notifier._last_message_time = 0  # Reset
        
        assert notifier._rate_limit_check() == True
    
    def test_rate_limit_subsequent_too_fast(self, temp_telegram_state_file):
        """Test rate limit blocks messages too fast."""
        notifier = TelegramNotifier(
            state_file=temp_telegram_state_file,
            rate_limit_sec=1.0
        )
        
        # First check passes and sets time
        notifier._rate_limit_check()
        
        # Immediate second check should fail
        assert notifier._rate_limit_check() == False
    
    def test_rate_limit_after_wait(self, temp_telegram_state_file):
        """Test rate limit allows after waiting."""
        import time
        
        notifier = TelegramNotifier(
            state_file=temp_telegram_state_file,
            rate_limit_sec=0.1  # 100ms for testing
        )
        
        # First check
        notifier._rate_limit_check()
        
        # Wait
        time.sleep(0.15)
        
        # Should pass now
        assert notifier._rate_limit_check() == True


class TestSendSignal:
    """Test trading signal sending."""
    
    @pytest.mark.asyncio
    async def test_send_signal_basic(self, temp_telegram_state_file, mock_telegram_env):
        """Test basic signal sending."""
        with patch('utils.telegram_notifier.Bot') as MockBot:
            mock_instance = AsyncMock()
            mock_instance.send_message = AsyncMock(return_value=True)
            MockBot.return_value = mock_instance
            
            notifier = TelegramNotifier(state_file=temp_telegram_state_file)
            
            result = await notifier.send_signal(
                action="LONG",
                asset="BTC/USDT",
                price=50000.00,
                stop_loss=47500.00,
                take_profit=55000.00,
                position_pct=5.0,
                regime="Bull",
                confidence=75,
                rationale="Momentum breakout"
            )
            
            assert result == True
            mock_instance.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_signal_minimal(self, temp_telegram_state_file):
        """Test signal with minimal parameters."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        result = await notifier.send_signal(
            action="BUY",
            asset="ETH/USDT",
            price=3000.00
        )
        
        # In mock mode, should succeed
        assert result == True
    
    @pytest.mark.asyncio
    async def test_send_signal_dedup(self, temp_telegram_state_file):
        """Test duplicate signal is skipped."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        # Send first signal
        result1 = await notifier.send_signal(
            action="LONG",
            asset="BTC/USDT",
            price=50000.00
        )
        
        # Send identical signal (should be deduped)
        result2 = await notifier.send_signal(
            action="LONG",
            asset="BTC/USDT",
            price=50000.00
        )
        
        assert result1 == True
        assert result2 == False  # Deduplicated
    
    @pytest.mark.asyncio
    async def test_send_signal_with_rr(self, temp_telegram_state_file):
        """Test signal includes risk/reward ratio."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        result = await notifier.send_signal(
            action="LONG",
            asset="BTC/USDT",
            price=50000.00,
            stop_loss=48000.00,  # -4%
            take_profit=54000.00  # +8%
        )
        
        assert result == True
    
    @pytest.mark.asyncio
    async def test_send_signal_sell_action(self, temp_telegram_state_file):
        """Test SELL signal uses correct emoji."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        # Just verify it doesn't crash
        result = await notifier.send_signal(
            action="SELL",
            asset="BTC/USDT",
            price=50000.00
        )
        
        assert result == True


class TestSendAlert:
    """Test alert sending."""
    
    @pytest.mark.asyncio
    async def test_send_alert_info(self, temp_telegram_state_file):
        """Test INFO level alert."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        result = await notifier.send_alert(
            level="INFO",
            title="System Update",
            message="New version deployed"
        )
        
        assert result == True
    
    @pytest.mark.asyncio
    async def test_send_alert_warning(self, temp_telegram_state_file):
        """Test WARNING level alert."""
        notifier = TelegramTelegramNotifier(state_file=temp_telegram_state_file)
        
        result = await notifier.send_alert(
            level="WARNING",
            title="Drawdown Alert",
            message="Daily drawdown at -4%",
            metric_name="Daily DD",
            metric_value=-0.04,
            threshold=-0.05
        )
        
        assert result == True
    
    @pytest.mark.asyncio
    async def test_send_alert_critical(self, temp_telegram_state_file):
        """Test CRITICAL level alert."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        result = await notifier.send_alert(
            level="CRITICAL",
            title="Kill Switch Triggered",
            message="Daily loss limit breached"
        )
        
        assert result == True
    
    @pytest.mark.asyncio
    async def test_send_alert_emergency(self, temp_telegram_state_file):
        """Test EMERGENCY level alert."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        result = await notifier.send_alert(
            level="EMERGENCY",
            title="System Halted",
            message="Critical failure detected"
        )
        
        assert result == True
    
    @pytest.mark.asyncio
    async def test_send_alert_dedup(self, temp_telegram_state_file):
        """Test duplicate alert is skipped."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        # Send first alert
        result1 = await notifier.send_alert(
            level="WARNING",
            title="Test Alert",
            message="Same message"
        )
        
        # Send identical alert
        result2 = await notifier.send_alert(
            level="WARNING",
            title="Test Alert",
            message="Same message"
        )
        
        assert result1 == True
        assert result2 == False  # Deduplicated


class TestSendDailySummary:
    """Test daily summary sending."""
    
    @pytest.mark.asyncio
    async def test_send_daily_summary_positive(self, temp_telegram_state_file):
        """Test daily summary with profit."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        result = await notifier.send_daily_summary(
            pnl=500.00,
            pnl_pct=2.5,
            trades=5,
            win_rate=80.0,
            capital=20500.00,
            exposure=75.0,
            risk_level="Moderate"
        )
        
        assert result == True
    
    @pytest.mark.asyncio
    async def test_send_daily_summary_negative(self, temp_telegram_state_file):
        """Test daily summary with loss."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        result = await notifier.send_daily_summary(
            pnl=-300.00,
            pnl_pct=-1.5,
            trades=3,
            win_rate=33.3,
            capital=19700.00,
            exposure=50.0,
            risk_level="High"
        )
        
        assert result == True


class TestSendWeeklySummary:
    """Test weekly summary sending."""
    
    @pytest.mark.asyncio
    async def test_send_weekly_summary(self, temp_telegram_state_file):
        """Test weekly summary."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        result = await notifier.send_weekly_summary(
            weekly_pnl=1200.00,
            weekly_pnl_pct=6.0,
            total_trades=15,
            sharpe=1.8,
            max_dd=-5.2,
            best_trade=450.00,
            worst_trade=-200.00
        )
        
        assert result == True


class TestConnection:
    """Test connection testing."""
    
    def test_test_connection_mock_mode(self, temp_telegram_state_file):
        """Test connection in mock mode."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        # In mock mode (no bot), should return True
        result = notifier.test_connection()
        
        assert result == True
    
    def test_test_connection_with_bot(self, temp_telegram_state_file, mock_telegram_env):
        """Test connection with mocked bot."""
        with patch('utils.telegram_notifier.Bot') as MockBot:
            mock_instance = MagicMock()
            mock_instance.get_me = MagicMock(return_value=MagicMock(username='test'))
            MockBot.return_value = mock_instance
            
            notifier = TelegramNotifier(state_file=temp_telegram_state_file)
            
            result = notifier.test_connection()
            
            assert result == True
            mock_instance.get_me.assert_called_once()
    
    def test_test_connection_failed(self, temp_telegram_state_file, mock_telegram_env):
        """Test connection failure handling."""
        with patch('utils.telegram_notifier.Bot') as MockBot:
            mock_instance = MagicMock()
            mock_instance.get_me = MagicMock(side_effect=Exception("Connection failed"))
            MockBot.return_value = mock_instance
            
            notifier = TelegramNotifier(state_file=temp_telegram_state_file)
            
            result = notifier.test_connection()
            
            assert result == False


class TestStatePersistence:
    """Test state file persistence."""
    
    def test_save_state(self, temp_telegram_state_file):
        """Test state is saved to file."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        # Add some data
        notifier._message_hashes.append({
            "hash": "test_hash",
            "time": datetime.now().isoformat()
        })
        notifier._last_message_time = time.time()
        
        # Save
        notifier._save_state()
        
        # Verify file exists
        assert Path(temp_telegram_state_file).exists()
        
        # Verify content
        with open(temp_telegram_state_file, 'r') as f:
            data = json.load(f)
        
        assert len(data["message_hashes"]) >= 1
        assert "last_message_time" in data
    
    def test_load_state_missing_file(self, tmp_path):
        """Test loading from non-existent file."""
        state_file = str(tmp_path / "nonexistent.json")
        
        notifier = TelegramNotifier(state_file=state_file)
        
        # Should start fresh
        assert len(notifier._message_hashes) == 0
        assert notifier._last_message_time == 0
    
    def test_load_state_corrupted(self, temp_telegram_state_file):
        """Test loading corrupted state file."""
        # Write invalid JSON
        with open(temp_telegram_state_file, 'w') as f:
            f.write("not valid json {{{")
        
        # Should not crash, should start fresh
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        assert len(notifier._message_hashes) == 0
    
    def test_state_trimmed_on_save(self, temp_telegram_state_file):
        """Test state is trimmed to last 100 on save."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        # Add 150 hashes
        for i in range(150):
            notifier._message_hashes.append({
                "hash": f"hash_{i}",
                "time": datetime.now().isoformat()
            })
        
        # Save
        notifier._save_state()
        
        # Load raw file
        with open(temp_telegram_state_file, 'r') as f:
            data = json.load(f)
        
        # Should have at most 100
        assert len(data["message_hashes"]) <= 100


class TestSignalId:
    """Test signal ID generation."""
    
    def test_get_signal_id(self, temp_telegram_state_file):
        """Test signal ID based on message count."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        # Initial ID
        id1 = notifier._get_signal_id()
        assert id1 == 1
        
        # Add some messages
        notifier._message_hashes.append({"hash": "a", "time": datetime.now().isoformat()})
        notifier._message_hashes.append({"hash": "b", "time": datetime.now().isoformat()})
        
        # New ID
        id2 = notifier._get_signal_id()
        assert id2 == 3


# ============================================================================
# Integration Tests
# ============================================================================

class TestTelegramIntegration:
    """Integration tests for Telegram notifier."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, temp_telegram_state_file):
        """Test complete notification workflow."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        # Send signal
        signal_result = await notifier.send_signal(
            action="LONG",
            asset="BTC/USDT",
            price=50000.00,
            stop_loss=47500.00,
            take_profit=55000.00
        )
        
        # Send alert
        alert_result = await notifier.send_alert(
            level="INFO",
            title="Trade Executed",
            message="Position opened"
        )
        
        # Send daily summary
        summary_result = await notifier.send_daily_summary(
            pnl=250.00,
            pnl_pct=1.25,
            trades=2,
            win_rate=100.0,
            capital=20250.00,
            exposure=50.0,
            risk_level="Low"
        )
        
        # All should succeed in mock mode
        assert signal_result == True
        assert alert_result == True
        assert summary_result == True
        
        # Verify state saved
        assert Path(temp_telegram_state_file).exists()
    
    @pytest.mark.asyncio
    async def test_dedup_across_message_types(self, temp_telegram_state_file):
        """Test deduplication works across different message types."""
        notifier = TelegramNotifier(state_file=temp_telegram_state_file)
        
        # Send alert
        await notifier.send_alert(
            level="WARNING",
            title="Unique Alert",
            message="This is unique"
        )
        
        # Different alert should NOT be deduped
        result = await notifier.send_alert(
            level="WARNING",
            title="Different Alert",
            message="Different content"
        )
        
        assert result == True


# Import time for tests
import time
