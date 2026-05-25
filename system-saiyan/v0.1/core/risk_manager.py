"""
Système Saiyan v0.1 - Risk Management
Position sizing, stop-loss, take-profit
Configuration : 2-5% par trade, SL 2-3%, TP 0.5-1.5%
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TradeParams:
    """Paramètres d'un trade"""
    symbol: str
    direction: str
    entry_price: float
    position_size_pct: float
    stop_loss_pct: float
    take_profit_pct: float
    confidence: float
    
    @property
    def stop_loss_price(self) -> float:
        """Prix du stop-loss"""
        if self.direction == 'LONG':
            return self.entry_price * (1 - self.stop_loss_pct / 100)
        else:
            return self.entry_price * (1 + self.stop_loss_pct / 100)
    
    @property
    def take_profit_price(self) -> float:
        """Prix du take-profit"""
        if self.direction == 'LONG':
            return self.entry_price * (1 + self.take_profit_pct / 100)
        else:
            return self.entry_price * (1 - self.take_profit_pct / 100)
    
    @property
    def risk_reward_ratio(self) -> float:
        """Ratio risk/reward"""
        return self.take_profit_pct / self.stop_loss_pct


class RiskManager:
    """
    Gestion du risque et position sizing
    """
    
    # Configuration
    MIN_POSITION_PCT = 2.0   # 2% minimum
    MAX_POSITION_PCT = 5.0   # 5% maximum
    DEFAULT_STOP_LOSS = 2.5  # 2.5%
    DEFAULT_TAKE_PROFIT = 1.0  # 1.0%
    MAX_DAILY_LOSS = 5.0     # 5% max loss/jour
    
    def __init__(self, total_capital: float = 10000.0):
        """
        Args:
            total_capital: Capital total en USDT
        """
        self.total_capital = total_capital
        self.daily_pnl = 0.0
        self.daily_loss_limit = total_capital * (self.MAX_DAILY_LOSS / 100)
    
    def calculate_position_size(self,
                                 signal: Dict,
                                 volatility: Optional[float] = None) -> TradeParams:
        """
        Calcule la taille de position basée sur la confidence
        
        Rule :
        - Confidence 60-70 : 2%
        - Confidence 70-80 : 3%
        - Confidence 80-90 : 4%
        - Confidence 90+ : 5%
        
        Args:
            signal: Dict signal du generator
            volatility: Volatilité actuelle (optionnel, pour ajustement)
        
        Returns:
            TradeParams
        """
        confidence = signal['confidence']
        
        # Position sizing basé sur confidence
        if confidence >= 90:
            position_pct = self.MAX_POSITION_PCT
        elif confidence >= 80:
            position_pct = 4.0
        elif confidence >= 70:
            position_pct = 3.0
        else:  # 60-70
            position_pct = self.MIN_POSITION_PCT
        
        # Ajustement pour volatilité élevée
        if volatility and volatility > 1.0:  # Volatilité très haute
            position_pct *= 0.75  # Réduit de 25%
            logger.info(f"⚠️ Reduced position size due to high volatility ({volatility:.2f})")
        
        # Vérification daily loss limit
        if self.daily_pnl < -self.daily_loss_limit:
            logger.warning(f"⚠️ Daily loss limit reached! No new trades.")
            position_pct = 0
        
        params = TradeParams(
            symbol=signal['symbol'],
            direction=signal['direction'],
            entry_price=signal['entry_price'],
            position_size_pct=position_pct,
            stop_loss_pct=self.DEFAULT_STOP_LOSS,
            take_profit_pct=self.DEFAULT_TAKE_PROFIT,
            confidence=confidence
        )
        
        logger.info(f"💰 Position: {position_pct:.1f}% | SL: {params.stop_loss_pct:.1f}% | TP: {params.take_profit_pct:.1f}%")
        
        return params
    
    def calculate_position_value(self, params: TradeParams) -> float:
        """
        Calcule la valeur de position en USDT
        
        Args:
            params: TradeParams
        
        Returns:
            Valeur en USDT
        """
        return self.total_capital * (params.position_size_pct / 100)
    
    def calculate_quantity(self, params: TradeParams) -> float:
        """
        Calcule la quantité d'asset à acheter
        
        Args:
            params: TradeParams
        
        Returns:
            Quantité
        """
        position_value = self.calculate_position_value(params)
        return position_value / params.entry_price
    
    def calculate_expected_pnl(self, params: TradeParams) -> Tuple[float, float]:
        """
        Calcule PnL attendu (gain/perte)
        
        Args:
            params: TradeParams
        
        Returns:
            (expected_profit, expected_loss) en USDT
        """
        position_value = self.calculate_position_value(params)
        
        expected_profit = position_value * (params.take_profit_pct / 100)
        expected_loss = position_value * (params.stop_loss_pct / 100)
        
        return expected_profit, expected_loss
    
    def update_daily_pnl(self, pnl: float):
        """
        Met à jour le PnL quotidien
        
        Args:
            pnl: PnL réalisé (positif ou négatif)
        """
        self.daily_pnl += pnl
        logger.info(f"📊 Daily PnL: {self.daily_pnl:.2f} USDT ({self.daily_pnl/self.total_capital*100:.2f}%)")
        
        if self.daily_pnl < -self.daily_loss_limit:
            logger.warning(f"⚠️ DAILY LOSS LIMIT REACHED! Trading halted.")
    
    def reset_daily_pnl(self):
        """Reset le PnL quotidien (nouveau jour)"""
        logger.info(f"🔄 Daily PnL reset. Previous: {self.daily_pnl:.2f} USDT")
        self.daily_pnl = 0.0
    
    def get_trade_summary(self, params: TradeParams) -> Dict:
        """
        Génère un résumé complet du trade
        
        Args:
            params: TradeParams
        
        Returns:
            Dict avec toutes les infos
        """
        position_value = self.calculate_position_value(params)
        quantity = self.calculate_quantity(params)
        expected_profit, expected_loss = self.calculate_expected_pnl(params)
        
        return {
            'symbol': params.symbol,
            'direction': params.direction,
            'entry_price': params.entry_price,
            'position_size_pct': params.position_size_pct,
            'position_value_usdt': round(position_value, 2),
            'quantity': round(quantity, 6),
            'stop_loss_price': round(params.stop_loss_price, 2),
            'take_profit_price': round(params.take_profit_price, 2),
            'stop_loss_pct': params.stop_loss_pct,
            'take_profit_pct': params.take_profit_pct,
            'expected_profit_usdt': round(expected_profit, 2),
            'expected_loss_usdt': round(expected_loss, 2),
            'risk_reward_ratio': round(params.risk_reward_ratio, 2),
            'confidence': params.confidence
        }


if __name__ == "__main__":
    # Test
    print("🐉 Testing Saiyan Risk Manager v0.1\n")
    
    rm = RiskManager(total_capital=10000)
    
    # Signal test
    test_signal = {
        'symbol': 'BTC/USDT',
        'direction': 'LONG',
        'entry_price': 95000,
        'confidence': 78.5
    }
    
    params = rm.calculate_position_size(test_signal)
    summary = rm.get_trade_summary(params)
    
    print("\n📋 Trade Summary:")
    print(f"  Symbol: {summary['symbol']}")
    print(f"  Direction: {summary['direction']}")
    print(f"  Entry: ${summary['entry_price']:,.2f}")
    print(f"  Position: {summary['position_size_pct']:.1f}% = ${summary['position_value_usdt']:,.2f}")
    print(f"  Quantity: {summary['quantity']:.6f}")
    print(f"  Stop Loss: ${summary['stop_loss_price']:,.2f} (-{summary['stop_loss_pct']}%)")
    print(f"  Take Profit: ${summary['take_profit_price']:,.2f} (+{summary['take_profit_pct']}%)")
    print(f"  Expected PnL: +${summary['expected_profit_usdt']:.2f} / -${summary['expected_loss_usdt']:.2f}")
    print(f"  Risk/Reward: {summary['risk_reward_ratio']:.2f}")
    print(f"  Confidence: {summary['confidence']:.1f}/100")
