"""
Système Saiyan v0.1 - Telegram Notification
Envoi des signaux vers Telegram (vers W pour exécution manuelle)
"""

import requests
from typing import Dict, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Envoi de signaux de trading vers Telegram
    Via OpenClaw ou Bot API directe
    """
    
    def __init__(self, 
                 bot_token: Optional[str] = None,
                 chat_id: Optional[str] = None,
                 use_openclaw: bool = True):
        """
        Args:
            bot_token: Telegram Bot Token (si use_openclaw=False)
            chat_id: Chat ID destinataire
            use_openclaw: Utiliser OpenClaw pour l'envoi (défaut: True)
        """
        self.use_openclaw = use_openclaw
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}" if bot_token else None
    
    def send_signal(self, 
                    signal: Dict,
                    trade_params: Optional[Dict] = None) -> bool:
        """
        Envoie un signal de trading vers Telegram
        
        Args:
            signal: Dict du signal generator
            trade_params: Dict du risk manager (optionnel)
        
        Returns:
            True si envoyé avec succès
        """
        message = self._format_signal_message(signal, trade_params)
        
        if self.use_openclaw:
            return self._send_via_openclaw(message)
        else:
            return self._send_via_bot_api(message)
    
    def _format_signal_message(self, signal: Dict, trade_params: Optional[Dict] = None) -> str:
        """
        Formate le message Telegram
        
        Args:
            signal: Dict signal
            trade_params: Dict risk manager
        
        Returns:
            Message formaté
        """
        emoji = "🟢" if signal['direction'] == 'LONG' else "🔴"
        
        # Header
        message = f"""
🐉 **SYSTÈME SAIYAN v0.1 - SIGNAL** {emoji}

**Symbol:** `{signal['symbol']}`
**Direction:** {signal['direction']}
**Strategy:** {signal['strategy'].replace('_', ' ').title()}

---

**Entry Price:** ${signal['entry_price']:,.2f}
**Confidence:** {signal['confidence']:.1f}/100

"""
        
        # Ajout des paramètres de trade si disponibles
        if trade_params:
            message += f"""
**💰 Risk Management:**
• Position: {trade_params['position_size_pct']:.1f}% (${trade_params['position_value_usdt']:,.2f})
• Stop Loss: ${trade_params['stop_loss_price']:,.2f} (-{trade_params['stop_loss_pct']}%)
• Take Profit: ${trade_params['take_profit_price']:,.2f} (+{trade_params['take_profit_pct']}%)

**Expected PnL:** +${trade_params['expected_profit_usdt']:.2f} / -${trade_params['expected_loss_usdt']:.2f}
**Risk/Reward:** {trade_params['risk_reward_ratio']:.2f}

"""
        
        # Indicators
        message += f"""
**📊 Indicators:**
• RSI: {signal['rsi']:.1f}
• BB Position: {signal['bb_position']:.2f}
• Volume Surge: {signal['volume_surge']:.2f}x
• Momentum: {signal['momentum']:.2f}%

---

⚠️ **Exécution Manuelle** - Vérifier avant d'entrer
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        
        return message
    
    def _send_via_openclaw(self, message: str) -> bool:
        """
        Envoie via OpenClaw (méthode préférée)
        
        Note: Dans OpenClaw, utiliser le tool sessions_spawn ou message
        pour envoyer vers Telegram.
        """
        logger.info("📤 Signal ready for Telegram (via OpenClaw)")
        logger.info(f"Message length: {len(message)} chars")
        
        # Dans le contexte OpenClaw, le message sera envoyé via le canal Telegram
        # automatiquement par l'agent principal
        print(message)  # Output pour capture par OpenClaw
        
        return True
    
    def _send_via_bot_api(self, message: str) -> bool:
        """
        Envoie via Telegram Bot API directe
        
        Args:
            message: Message à envoyer
        
        Returns:
            True si succès
        """
        if not self.bot_token or not self.chat_id:
            logger.error("❌ Bot token or chat_id missing")
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✓ Signal sent to Telegram")
                return True
            else:
                logger.error(f"❌ Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending Telegram message: {e}")
            return False
    
    def send_alert(self, message: str) -> bool:
        """
        Envoie une alerte générale (pas un signal)
        
        Args:
            message: Message d'alerte
        
        Returns:
            True si envoyé
        """
        alert_message = f"⚠️ **SAIYAN ALERT**\n\n{message}"
        
        if self.use_openclaw:
            return self._send_via_openclaw(alert_message)
        else:
            return self._send_via_bot_api(alert_message)
    
    def send_daily_summary(self,
                           total_signals: int,
                           executed_trades: int,
                           daily_pnl: float,
                           win_rate: float) -> bool:
        """
        Envoie un résumé quotidien
        
        Args:
            total_signals: Nombre de signaux générés
            executed_trades: Nombre de trades exécutés
            daily_pnl: PnL du jour
            win_rate: Win rate en %
        
        Returns:
            True si envoyé
        """
        emoji = "🟢" if daily_pnl >= 0 else "🔴"
        
        summary = f"""
🐉 **SAIYAN DAILY SUMMARY** {emoji}

📊 **Performance:**
• Signals: {total_signals}
• Executed: {executed_trades}
• Win Rate: {win_rate:.1f}%
• Daily PnL: {daily_pnl:+.2f} USDT

🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        
        if self.use_openclaw:
            return self._send_via_openclaw(summary)
        else:
            return self._send_via_bot_api(summary)


if __name__ == "__main__":
    # Test
    print("🐉 Testing Saiyan Telegram Notifier v0.1\n")
    
    notifier = TelegramNotifier(use_openclaw=True)
    
    # Test signal
    test_signal = {
        'symbol': 'BTC/USDT',
        'direction': 'LONG',
        'strategy': 'mean_reversion',
        'entry_price': 95000,
        'confidence': 78.5,
        'rsi': 22.3,
        'bb_position': 0.15,
        'volume_surge': 1.8,
        'momentum': 2.5
    }
    
    test_params = {
        'position_size_pct': 3.0,
        'position_value_usdt': 300,
        'stop_loss_price': 92625,
        'take_profit_price': 95950,
        'stop_loss_pct': 2.5,
        'take_profit_pct': 1.0,
        'expected_profit_usdt': 3.0,
        'expected_loss_usdt': 7.5,
        'risk_reward_ratio': 0.4
    }
    
    notifier.send_signal(test_signal, test_params)
