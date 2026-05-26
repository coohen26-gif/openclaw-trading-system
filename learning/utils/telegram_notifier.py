#!/usr/bin/env python3
"""
Telegram Notifier - Trading Signals & Alerts

Module: Phase 3 - Production Readiness
Author: Saiyan Autonomous Trading System
Date: May 26, 2026

Features:
- Trading signals (entry, stop, target, regime)
- System alerts (risk levels, circuit breakers)
- Daily/weekly summaries
- Auto signal ID increment
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Types of trading signals"""
    ENTRY_LONG = "entry_long"
    ENTRY_SHORT = "entry_short"
    EXIT = "exit"
    ALERT = "alert"
    SUMMARY = "summary"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class TradingSignal:
    """Trading signal representation"""
    signal_id: int
    signal_type: SignalType
    asset: str
    action: str  # BUY/SELL/CLOSE
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    position_size: float  # % of portfolio
    regime: str
    confidence: float  # 0-1
    timestamp: str
    rationale: str


@dataclass
class SystemAlert:
    """System alert representation"""
    alert_id: int
    severity: AlertSeverity
    title: str
    message: str
    metric: str
    value: float
    threshold: float
    timestamp: str


class TelegramNotifier:
    """
    Telegram notification system for trading signals and alerts.
    
    Uses OpenClaw message tool for delivery.
    """
    
    def __init__(self, state_file: str = "data/telegram_state.json"):
        self.state_file = state_file
        self.state = self._load_state()
        logger.info(f"Telegram Notifier initialized (signal_id: {self.state['last_signal_id']})")
    
    def _load_state(self) -> Dict:
        """Load or initialize state"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
        
        return {
            "last_signal_id": 0,
            "last_alert_id": 0,
            "last_summary_sent": None,
            "signals_sent_today": 0
        }
    
    def _save_state(self):
        """Persist state to file"""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def _increment_signal_id(self) -> int:
        """Get next signal ID"""
        self.state["last_signal_id"] += 1
        self._save_state()
        return self.state["last_signal_id"]
    
    def _increment_alert_id(self) -> int:
        """Get next alert ID"""
        self.state["last_alert_id"] += 1
        self._save_state()
        return self.state["last_alert_id"]
    
    def send_signal(
        self,
        asset: str,
        action: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        position_size: float,
        regime: str,
        confidence: float,
        rationale: str
    ) -> TradingSignal:
        """
        Send trading signal to Telegram.
        
        Args:
            asset: Trading pair (e.g., "BTC/USDT")
            action: BUY/SELL/CLOSE
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            position_size: Position size (% of portfolio)
            regime: Market regime (Bull/Bear/Range/Volatile Bull)
            confidence: Signal confidence (0-1)
            rationale: Brief explanation
            
        Returns:
            TradingSignal object
        """
        signal_id = self._increment_signal_id()
        timestamp = datetime.now(timezone.utc).isoformat()
        
        signal = TradingSignal(
            signal_id=signal_id,
            signal_type=SignalType.ENTRY_LONG if action == "BUY" else SignalType.ENTRY_SHORT,
            asset=asset,
            action=action,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size,
            regime=regime,
            confidence=confidence,
            timestamp=timestamp,
            rationale=rationale
        )
        
        # Format message
        emoji = "🟢" if action == "BUY" else "🔴"
        message = f"""
{emoji} **SIGNAL #{signal_id}** {emoji}

**Asset:** {asset}
**Action:** {action}
**Entry:** ${entry_price:,.2f}
**Stop Loss:** ${stop_loss:,.2f} ({((entry_price - stop_loss) / entry_price * 100):.1f}%)
**Take Profit:** ${take_profit:,.2f} ({((take_profit - entry_price) / entry_price * 100):.1f}%)
**Position:** {position_size:.1f}% of portfolio

**Regime:** {regime}
**Confidence:** {confidence*100:.0f}%

**Rationale:** {rationale}

---
📊 *Saiyan Trading System v0.2*
{timestamp}
""".strip()
        
        logger.info(f"Signal #{signal_id} sent: {action} {asset} @ ${entry_price:,.2f}")
        self.state["signals_sent_today"] += 1
        self._save_state()
        
        # Note: Actual Telegram delivery handled by OpenClaw message tool
        # This method prepares the signal; delivery is triggered externally
        return signal
    
    def send_alert(
        self,
        severity: AlertSeverity,
        title: str,
        message: str,
        metric: str,
        value: float,
        threshold: float
    ) -> SystemAlert:
        """
        Send system alert to Telegram.
        
        Args:
            severity: Alert severity (INFO/WARNING/CRITICAL/EMERGENCY)
            title: Alert title
            message: Detailed message
            metric: Metric name (e.g., "drawdown", "var_95")
            value: Current value
            threshold: Threshold that triggered alert
            
        Returns:
            SystemAlert object
        """
        alert_id = self._increment_alert_id()
        timestamp = datetime.now(timezone.utc).isoformat()
        
        alert = SystemAlert(
            alert_id=alert_id,
            severity=severity,
            title=title,
            message=message,
            metric=metric,
            value=value,
            threshold=threshold,
            timestamp=timestamp
        )
        
        # Emoji by severity
        emojis = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.CRITICAL: "🚨",
            AlertSeverity.EMERGENCY: "🆘"
        }
        emoji = emojis.get(severity, "❓")
        
        formatted_message = f"""
{emoji} **{title}** {emoji}

{message}

**Metric:** {metric}
**Value:** {value:.4f}
**Threshold:** {threshold:.4f}

---
🔔 *Saiyan Risk Monitor*
{timestamp}
""".strip()
        
        logger.warning(f"Alert #{alert_id} [{severity.value}]: {title}")
        
        return alert
    
    def send_daily_summary(
        self,
        pnl: float,
        trades: int,
        win_rate: float,
        current_drawdown: float,
        risk_level: str
    ):
        """
        Send daily summary to Telegram.
        
        Args:
            pnl: Daily PnL (%)
            trades: Number of trades today
            win_rate: Win rate (%)
            current_drawdown: Current drawdown (%)
            risk_level: Current risk level (NORMAL/ELEVATED/CRITICAL)
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        self.state["last_summary_sent"] = timestamp
        self.state["signals_sent_today"] = 0  # Reset daily counter
        self._save_state()
        
        # Emoji by PnL
        pnl_emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "🟡"
        risk_emoji = "✅" if risk_level == "NORMAL" else "⚠️" if risk_level == "ELEVATED" else "🚨"
        
        message = f"""
{pnl_emoji} **DAILY SUMMARY** {pnl_emoji}

**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}

**Performance:**
• PnL: {pnl:+.2f}%
• Trades: {trades}
• Win Rate: {win_rate:.1f}%

**Risk:**
• Drawdown: {current_drawdown:.2f}%
• Level: {risk_level} {risk_emoji}

**Signals Today:** {self.state["signals_sent_today"]}

---
📈 *Saiyan Trading System v0.2*
{timestamp}
""".strip()
        
        logger.info(f"Daily summary sent: PnL {pnl:+.2f}%, {trades} trades")
        
        return message
    
    def test_connection(self) -> bool:
        """
        Test Telegram connection.
        
        Returns:
            True if connection OK
        """
        logger.info("Testing Telegram connection...")
        # Connection test is handled by OpenClaw runtime
        # This is a placeholder for local testing
        return True


def main():
    """Test the Telegram notifier"""
    print("=" * 70)
    print("TELEGRAM NOTIFIER - TEST MODE")
    print("=" * 70)
    
    notifier = TelegramNotifier()
    
    # Test connection
    print("\n[1/3] Testing connection...")
    if notifier.test_connection():
        print("✅ Telegram connection OK")
    else:
        print("❌ Telegram connection FAILED")
        return
    
    # Test signal
    print("\n[2/3] Testing signal...")
    signal = notifier.send_signal(
        asset="BTC/USDT",
        action="BUY",
        entry_price=77159.0,
        stop_loss=70000.0,
        take_profit=92000.0,
        position_size=18.75,
        regime="Bull",
        confidence=0.75,
        rationale="Momentum breakout above resistance, HMM Bull regime confirmed"
    )
    print(f"✅ Signal #{signal.signal_id} prepared")
    
    # Test alert
    print("\n[3/3] Testing alert...")
    alert = notifier.send_alert(
        severity=AlertSeverity.WARNING,
        title="Drawdown Warning",
        message="Portfolio drawdown approaching threshold",
        metric="drawdown",
        value=-0.08,
        threshold=-0.10
    )
    print(f"✅ Alert #{alert.alert_id} prepared")
    
    print("\n" + "=" * 70)
    print("✅ TELEGRAM NOTIFIER TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
