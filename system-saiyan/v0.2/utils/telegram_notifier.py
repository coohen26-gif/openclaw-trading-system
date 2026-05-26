"""
🐉 Telegram Notifier - Système Saiyan v0.2

Sends trading signals and system alerts via Telegram.

Integration with OpenClaw telegram_sender.py or direct API.

Usage:
    from utils.telegram_notifier import TelegramNotifier
    
    notifier = TelegramNotifier()
    notifier.send_signal(signal_data)
    notifier.send_alert("Risk level: WARNING")
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Try to import parent telegram_sender
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'signal-system'))
    from telegram.telegram_sender import send_telegram_message, format_signal
    HAS_SIGNAL_SYSTEM = True
except ImportError:
    HAS_SIGNAL_SYSTEM = False
    logging.warning("signal-system not found, using direct API")

logger = logging.getLogger('saiyan_telegram')


class TelegramNotifier:
    """
    Telegram notification handler for Saiyan system.
    
    Supports:
    - Trading signals (entry, stop, target)
    - System alerts (risk level changes, circuit breakers)
    - Daily/weekly summaries
    - Error notifications
    """
    
    def __init__(self, enabled: bool = True, config_path: str = None):
        """
        Initialize notifier.
        
        Args:
            enabled: Enable/disable notifications
            config_path: Path to config.json with telegram settings
        """
        self.enabled = enabled
        self.config = self._load_config(config_path)
        
        # Get credentials from env or config
        self.token = os.getenv('TELEGRAM_BOT_TOKEN', self.config.get('telegram', {}).get('bot_token'))
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', self.config.get('telegram', {}).get('chat_id'))
        
        # State tracking
        self.last_signal_id = 0
        self.last_summary_time = None
        
        if not self.token or not self.chat_id:
            logger.warning("Telegram credentials not configured, notifications disabled")
            self.enabled = False
        else:
            logger.info(f"Telegram notifier initialized (chat: {self.chat_id})")
    
    def _load_config(self, config_path: str = None) -> Dict:
        """Load configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config.json'
        
        if Path(config_path).exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}
    
    def send_signal(self, signal: Dict[str, Any]) -> bool:
        """
        Send trading signal notification.
        
        Args:
            signal: Signal data with asset, direction, entry, stop, target, etc.
        
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.debug("Notifications disabled, skipping signal")
            return False
        
        self.last_signal_id += 1
        
        if HAS_SIGNAL_SYSTEM:
            # Use signal-system formatter
            message = format_signal(signal, self.last_signal_id)
            return send_telegram_message(self.token, self.chat_id, message)
        else:
            # Fallback: simple format
            message = self._format_signal_simple(signal, self.last_signal_id)
            return self._send_direct(message)
    
    def _format_signal_simple(self, signal: Dict, signal_id: int) -> str:
        """Simple signal formatting (fallback)"""
        asset = signal.get('asset', 'UNKNOWN')
        direction = signal.get('direction', 'LONG')
        confidence = signal.get('confidence', 0)
        entry = signal.get('entry_price', 0)
        stop = signal.get('stop_loss', 0)
        target = signal.get('take_profit', 0)
        regime = signal.get('regime', 'UNKNOWN')
        
        # Confidence emoji
        if confidence >= 80:
            level, emoji = "MAX", "🟣"
        elif confidence >= 60:
            level, emoji = "HIGH", "🟢"
        elif confidence >= 40:
            level, emoji = "MEDIUM", "🟡"
        else:
            level, emoji = "LOW", "⚪"
        
        message = f"""🎯 SIGNAL #{signal_id:03d}

📊 {asset}
📈 {direction}

💰 Entry: ${entry:,.2f}
🛑 Stop: ${stop:,.2f}
🎯 Target: ${target:,.2f}

🔮 Regime: {regime}
📊 Confidence: {confidence:.0f}/100 ({level}) {emoji}

🐉 Saiyan System v0.2"""
        
        return message
    
    def send_alert(self, message: str, severity: str = "INFO") -> bool:
        """
        Send system alert.
        
        Args:
            message: Alert message
            severity: INFO, WARNING, CRITICAL, EMERGENCY
        
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        # Severity emoji
        emojis = {
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'CRITICAL': '🚨',
            'EMERGENCY': '🆘'
        }
        emoji = emojis.get(severity, 'ℹ️')
        
        full_message = f"""{emoji} {severity}

{message}

🐉 Saiyan Risk Monitor"""
        
        return self._send_direct(full_message)
    
    def send_summary(self, summary: Dict[str, Any], period: str = "daily") -> bool:
        """
        Send daily/weekly summary.
        
        Args:
            summary: Summary data (pnl, trades, sharpe, etc.)
            period: "daily" or "weekly"
        
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        emoji = "📊" if period == "daily" else "📈"
        
        message = f"""{emoji} {period.upper()} SUMMARY

💰 PnL: {summary.get('pnl_pct', 0):+.2f}%
📊 Trades: {summary.get('n_trades', 0)}
🎯 Win Rate: {summary.get('win_rate', 0):.1f}%
📉 Sharpe: {summary.get('sharpe', 0):.2f}
📉 Max DD: {summary.get('max_dd', 0):.2f}%

🔮 Current Regime: {summary.get('regime', 'UNKNOWN')}
⚡ Risk Level: {summary.get('risk_level', 'NORMAL')}

🐉 Saiyan System v0.2"""
        
        return self._send_direct(message)
    
    def _send_direct(self, message: str) -> bool:
        """Send message via direct API call"""
        if not self.token or not self.chat_id:
            logger.error("Telegram credentials not configured")
            return False
        
        try:
            import urllib.request
            import urllib.parse
            
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            encoded = urllib.parse.urlencode(data).encode('utf-8')
            req = urllib.request.Request(url, data=encoded, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if result.get('ok'):
                    logger.info(f"Telegram message sent")
                    return True
                else:
                    logger.error(f"Telegram API error: {result.get('description', 'Unknown')}")
                    return False
                    
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test Telegram connection"""
        return self.send_alert("🐉 Saiyan System v0.2 - Connection test successful", "INFO")


if __name__ == "__main__":
    # Test
    notifier = TelegramNotifier()
    
    if notifier.test_connection():
        print("✅ Telegram connection OK")
    else:
        print("❌ Telegram connection failed")
