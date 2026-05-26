#!/usr/bin/env python3
"""
Telegram Notifier - Saiyan V0.3

Features:
- Trading signals (entry, exit, PnL)
- System alerts (risk levels, circuit breakers)
- Daily/weekly summaries
- Deduplication (no duplicate messages <5min)
- Rate limiting (max 1 msg/sec)

Author: Saiyan Trading System
Date: May 2026
"""

import json
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

# Try to import telegram, fallback gracefully
try:
    from telegram import Bot
    from telegram.error import TelegramError, RetryAfter
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    Bot = None


class TelegramNotifier:
    """
    Telegram notification system with deduplication and rate limiting.
    """
    
    def __init__(
        self,
        token: Optional[str] = None,
        chat_id: Optional[str] = None,
        state_file: str = "data/telegram_state.json",
        dedup_window_min: int = 5,
        rate_limit_sec: float = 1.0
    ):
        """
        Initialize Telegram notifier.
        
        Args:
            token: Bot token (env var TELEGRAM_BOT_TOKEN if not provided)
            chat_id: Target chat ID (env var TELEGRAM_CHAT_ID if not provided)
            state_file: Path to state file for dedup tracking
            dedup_window_min: Minutes window for deduplication
            rate_limit_sec: Minimum seconds between messages
        """
        import os
        
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.state_file = Path(state_file)
        self.dedup_window_min = dedup_window_min
        self.rate_limit_sec = rate_limit_sec
        
        self.bot: Optional[Bot] = None
        self._last_message_time: float = 0
        self._message_hashes: List[Dict] = []
        
        # Load state
        self._load_state()
        
        # Initialize bot if credentials available
        if TELEGRAM_AVAILABLE and self.token and self.chat_id:
            try:
                self.bot = Bot(token=self.token)
                # Test connection
                self.bot.get_me()
                logger.info("✅ Telegram bot initialized")
            except Exception as e:
                logger.warning(f"⚠️  Telegram bot init failed: {e}")
                self.bot = None
        else:
            logger.info("ℹ️  Telegram notifier in mock mode (no credentials)")
    
    def _load_state(self):
        """Load dedup state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self._message_hashes = state.get("message_hashes", [])
                    self._last_message_time = state.get("last_message_time", 0)
                    logger.info(f"📊 Loaded {len(self._message_hashes)} message hashes")
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")
                self._message_hashes = []
                self._last_message_time = 0
    
    def _save_state(self):
        """Save dedup state to file."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            state = {
                "message_hashes": self._message_hashes[-100:],  # Keep last 100
                "last_message_time": self._last_message_time
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save state: {e}")
    
    def _compute_hash(self, content: str) -> str:
        """Compute hash for deduplication."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _is_duplicate(self, content_hash: str) -> bool:
        """Check if message is duplicate within dedup window."""
        now = datetime.now()
        cutoff = now - timedelta(minutes=self.dedup_window_min)
        
        # Clean old hashes
        self._message_hashes = [
            h for h in self._message_hashes
            if datetime.fromisoformat(h["time"]) > cutoff
        ]
        
        # Check for duplicate
        for h in self._message_hashes:
            if h["hash"] == content_hash:
                return True
        
        return False
    
    def _record_message(self, content_hash: str):
        """Record message hash for deduplication."""
        self._message_hashes.append({
            "hash": content_hash,
            "time": datetime.now().isoformat()
        })
        self._save_state()
    
    def _rate_limit_check(self) -> bool:
        """Check rate limit. Returns True if can send."""
        now = time.time()
        if now - self._last_message_time < self.rate_limit_sec:
            return False
        self._last_message_time = now
        return True
    
    async def _send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Send message to Telegram with rate limiting."""
        if not self.bot:
            logger.info(f"📤 [MOCK] {text[:100]}...")
            return True
        
        # Rate limit check
        if not self._rate_limit_check():
            logger.warning("⏳ Rate limit hit, waiting...")
            await asyncio.sleep(self.rate_limit_sec)
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode
            )
            logger.info("✅ Message sent")
            return True
        except RetryAfter as e:
            logger.warning(f"⏳ Rate limited by Telegram: {e.retry_after}s")
            await asyncio.sleep(e.retry_after)
            return await self._send_message(text, parse_mode)
        except TelegramError as e:
            logger.error(f"❌ Telegram error: {e}")
            return False
    
    async def send_signal(
        self,
        action: str,  # BUY, SELL, LONG, SHORT
        asset: str,
        price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        position_pct: Optional[float] = None,
        regime: Optional[str] = None,
        confidence: Optional[float] = None,
        rationale: Optional[str] = None
    ) -> bool:
        """
        Send trading signal.
        
        Args:
            action: BUY/SELL/LONG/SHORT
            asset: Asset symbol (e.g., BTC/USDT)
            price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            position_pct: Position size as % of capital
            regime: Market regime (Bull, Bear, Range, Volatile Bull)
            confidence: Signal confidence (0-100%)
            rationale: Brief explanation
        """
        # Build message
        emoji = "🟢" if action in ["BUY", "LONG"] else "🔴"
        
        text = f"{emoji} **SIGNAL #{self._get_signal_id()}**\n\n"
        text += f"**{action} {asset}**\n"
        text += f"💰 Entry: ${price:,.2f}\n"
        
        if stop_loss:
            sl_pct = ((price - stop_loss) / price) * 100 if action in ["BUY", "LONG"] else ((stop_loss - price) / price) * 100
            text += f"🛑 SL: ${stop_loss:,.2f} ({sl_pct:.1f}%)\n"
        
        if take_profit:
            tp_pct = ((take_profit - price) / price) * 100 if action in ["BUY", "LONG"] else ((price - take_profit) / price) * 100
            text += f"🎯 TP: ${take_profit:,.2f} (+{tp_pct:.1f}%)\n"
        
        if position_pct:
            text += f"📊 Position: {position_pct:.1f}% of capital\n"
        
        if regime:
            text += f"📈 Regime: {regime}\n"
        
        if confidence:
            text += f"🎯 Confidence: {confidence:.0f}%\n"
        
        if rationale:
            text += f"\n💡 _{rationale}_\n"
        
        # Risk/reward
        if stop_loss and take_profit:
            risk = abs(price - stop_loss) / price
            reward = abs(take_profit - price) / price
            rr = reward / risk if risk > 0 else 0
            text += f"\n📊 R/R: 1:{rr:.1f}"
        
        # Dedup check
        content_hash = self._compute_hash(text)
        if self._is_duplicate(content_hash):
            logger.info("⏭️  Duplicate signal skipped")
            return False
        
        # Send
        success = await self._send_message(text)
        if success:
            self._record_message(content_hash)
        
        return success
    
    async def send_alert(
        self,
        level: str,  # INFO, WARNING, CRITICAL, EMERGENCY
        title: str,
        message: str,
        metric_name: Optional[str] = None,
        metric_value: Optional[float] = None,
        threshold: Optional[float] = None
    ) -> bool:
        """
        Send system alert.
        
        Args:
            level: Alert level (INFO, WARNING, CRITICAL, EMERGENCY)
            title: Alert title
            message: Alert message
            metric_name: Name of triggered metric
            metric_value: Current metric value
            threshold: Threshold that was breached
        """
        emojis = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "CRITICAL": "🚨",
            "EMERGENCY": "🆘"
        }
        
        emoji = emojis.get(level, "ℹ️")
        
        text = f"{emoji} **{level}: {title}**\n\n"
        text += f"{message}\n"
        
        if metric_name and metric_value is not None:
            text += f"\n📊 **{metric_name}**: {metric_value:.4f}"
            if threshold is not None:
                text += f" (threshold: {threshold:.4f})"
        
        # Dedup check
        content_hash = self._compute_hash(text)
        if self._is_duplicate(content_hash):
            logger.info("⏭️  Duplicate alert skipped")
            return False
        
        # Send
        success = await self._send_message(text)
        if success:
            self._record_message(content_hash)
        
        return success
    
    async def send_daily_summary(
        self,
        pnl: float,
        pnl_pct: float,
        trades: int,
        win_rate: float,
        capital: float,
        exposure: float,
        risk_level: str
    ) -> bool:
        """Send daily PnL summary."""
        emoji = "🟢" if pnl >= 0 else "🔴"
        
        text = f"{emoji} **DAILY SUMMARY** — {datetime.now().strftime('%Y-%m-%d')}\n\n"
        text += f"💰 **PnL**: ${pnl:,.2f} ({pnl_pct:+.2f}%)\n"
        text += f"📊 **Trades**: {trades} (WR: {win_rate:.1f}%)\n"
        text += f"💵 **Capital**: ${capital:,.2f}\n"
        text += f"📈 **Exposure**: {exposure:.1f}%\n"
        text += f"🛡️  **Risk**: {risk_level}\n"
        
        content_hash = self._compute_hash(text)
        if self._is_duplicate(content_hash):
            return False
        
        success = await self._send_message(text)
        if success:
            self._record_message(content_hash)
        
        return success
    
    async def send_weekly_summary(
        self,
        weekly_pnl: float,
        weekly_pnl_pct: float,
        total_trades: int,
        sharpe: float,
        max_dd: float,
        best_trade: float,
        worst_trade: float
    ) -> bool:
        """Send weekly performance summary."""
        emoji = "🟢" if weekly_pnl >= 0 else "🔴"
        
        text = f"{emoji} **WEEKLY SUMMARY** — Week {datetime.now().isocalendar()[1]}\n\n"
        text += f"💰 **PnL**: ${weekly_pnl:,.2f} ({weekly_pnl_pct:+.2f}%)\n"
        text += f"📊 **Trades**: {total_trades}\n"
        text += f"📈 **Sharpe**: {sharpe:.2f}\n"
        text += f"📉 **Max DD**: {max_dd:.2f}%\n"
        text += f"🏆 **Best**: ${best_trade:,.2f}\n"
        text += f"💀 **Worst**: ${worst_trade:,.2f}\n"
        
        content_hash = self._compute_hash(text)
        if self._is_duplicate(content_hash):
            return False
        
        success = await self._send_message(text)
        if success:
            self._record_message(content_hash)
        
        return success
    
    def _get_signal_id(self) -> int:
        """Get next signal ID (based on sent messages count)."""
        return len(self._message_hashes) + 1
    
    def test_connection(self) -> bool:
        """Test Telegram connection."""
        if not self.bot:
            logger.info("ℹ️  Telegram not configured (mock mode)")
            return True
        
        try:
            self.bot.get_me()
            logger.info("✅ Telegram connection OK")
            return True
        except Exception as e:
            logger.error(f"❌ Telegram connection failed: {e}")
            return False


# CLI test
if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    
    notifier = TelegramNotifier()
    
    print("\n🧪 Testing Telegram Notifier...\n")
    
    # Test connection
    if notifier.test_connection():
        print("✅ Connection test passed\n")
    
    # Test signal
    async def test():
        await notifier.send_signal(
            action="LONG",
            asset="BTC/USDT",
            price=77159.00,
            stop_loss=73301.05,
            take_profit=92590.80,
            position_pct=5.0,
            regime="Bull",
            confidence=75,
            rationale="Momentum breakout + HMM Bull regime confirmed"
        )
        
        await notifier.send_alert(
            level="WARNING",
            title="Drawdown Alert",
            message="Daily drawdown approaching threshold",
            metric_name="Daily DD",
            metric_value=-0.045,
            threshold=-0.05
        )
    
    asyncio.run(test())
    
    print("\n✅ Tests completed\n")
