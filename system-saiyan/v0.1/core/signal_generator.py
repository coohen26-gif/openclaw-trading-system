"""
Système Saiyan v0.1 - Signal Generator
Génération de signaux avec confidence score (0-100)
Stratégies : Mean Reversion (prioritaire) + Momentum
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    Générateur de signaux avec scoring de confiance
    Seuil minimum : 60/100 pour exécution
    """
    
    # Configuration
    MIN_CONFIDENCE = 60  # Seuil minimum pour trade
    MAX_TRADES_PER_DAY = 5
    
    def __init__(self):
        self.signals_today = 0
        self.last_signal_time = None
    
    def calculate_confidence_score(self,
                                    df: pd.DataFrame,
                                    signal_type: str = 'long') -> pd.Series:
        """
        Calcule un confidence score 0-100 pour chaque signal
        
        Composantes :
        - Technical (RSI, BB) : 40%
        - Momentum : 25%
        - Volume : 20%
        - Volatility : 15%
        
        Args:
            df: DataFrame avec features
            signal_type: 'long' ou 'short'
        
        Returns:
            Series confidence score (0-100)
        """
        scores = []
        
        for idx, row in df.iterrows():
            score = 0.0
            
            if signal_type == 'long':
                # Technical (40%) - RSI very oversold = high score
                rsi_score = max(0, min(40, (35 - row['rsi']) * 2))  # RSI <25 = 40 pts
                bb_score = max(0, min(40, (1 - row['bb_position']) * 40))  # Bottom of BB = 40 pts
                technical_score = (rsi_score + bb_score) / 2
                
                # Momentum (25%) - slight positive or recovering
                momentum_score = max(0, min(25, 12.5 + row['momentum'] * 2.5))  # Base 12.5 + momentum
                
                # Volume (20%) - any surge helps
                volume_score = min(20, max(10, row['volume_surge'] * 10))  # Min 10 pts for volume
                
                # Volatility (15%) - moderate vol preferred
                vol_score = max(0, 15 - abs(row['volatility'] - 0.6) * 10)
                
            else:  # short
                # Technical (40%) - RSI very overbought = high score
                rsi_score = max(0, min(40, (row['rsi'] - 65) * 2))  # RSI >75 = 40 pts
                bb_score = max(0, min(40, row['bb_position'] * 40))  # Top of BB = 40 pts
                technical_score = (rsi_score + bb_score) / 2
                
                # Momentum (25%) - negative or reversing
                momentum_score = max(0, min(25, 12.5 - row['momentum'] * 2.5))
                
                # Volume (20%)
                volume_score = min(20, max(10, row['volume_surge'] * 10))
                
                # Volatility (15%)
                vol_score = max(0, 15 - abs(row['volatility'] - 0.6) * 10)
            
            # Pondération finale - les scores sont déjà sur la bonne échelle
            total_score = (
                technical_score * 0.40 +  # 0-40 * 0.40 = 0-16
                momentum_score * 0.25 +   # 0-25 * 0.25 = 0-6.25
                volume_score * 0.20 +     # 0-20 * 0.20 = 0-4
                vol_score * 0.15          # 0-15 * 0.15 = 0-2.25
            )
            # Scale to 0-100
            total_score = total_score * 3.5  # (16+6.25+4+2.25=28.5) * 3.5 ≈ 100
            
            scores.append(min(100, max(0, total_score)))
        
        return pd.Series(scores, index=df.index)
    
    def generate_signals(self,
                         df: pd.DataFrame,
                         strategy: str = 'mean_reversion',
                         apply_daily_limit: bool = True) -> List[Dict]:
        """
        Génère les signaux de trading
        
        Args:
            df: DataFrame avec features
            strategy: 'mean_reversion' ou 'momentum'
            apply_daily_limit: Appliquer la limite max trades/jour (True pour live, False pour backtest)
        
        Returns:
            Liste de dicts signal
        """
        signals = []
        
        # Calcul des scores de confidence
        df['confidence_long'] = self.calculate_confidence_score(df, 'long')
        df['confidence_short'] = self.calculate_confidence_score(df, 'short')
        
        # Filtrage par stratégie
        if strategy == 'mean_reversion':
            # Mean Reversion : RSI extrême + BB (relaxed thresholds)
            long_candidates = df[
                (df['rsi'] < 35) & 
                (df['bb_position'] < 0.2) &  # Bottom 20% of BB
                (df['confidence_long'] >= self.MIN_CONFIDENCE)
            ]
            
            short_candidates = df[
                (df['rsi'] > 65) & 
                (df['bb_position'] > 0.8) &  # Top 20% of BB
                (df['confidence_short'] >= self.MIN_CONFIDENCE)
            ]
            
        elif strategy == 'momentum':
            # Momentum : breakout + volume
            long_candidates = df[
                (df['momentum'] > 2.0) &
                (df['volume_surge'] > 1.5) &
                (df['confidence_long'] >= self.MIN_CONFIDENCE)
            ]
            
            short_candidates = df[
                (df['momentum'] < -2.0) &
                (df['volume_surge'] > 1.5) &
                (df['confidence_short'] >= self.MIN_CONFIDENCE)
            ]
        else:
            logger.warning(f"Unknown strategy: {strategy}")
            return []
        
        # Création des signaux
        for idx, row in long_candidates.iterrows():
            signal = {
                'timestamp': idx,
                'symbol': df.attrs.get('symbol', 'UNKNOWN'),
                'direction': 'LONG',
                'strategy': strategy,
                'confidence': round(row['confidence_long'], 1),
                'entry_price': row['close'],
                'rsi': row['rsi'],
                'bb_position': row['bb_position'],
                'volume_surge': row['volume_surge'],
                'momentum': row['momentum']
            }
            signals.append(signal)
        
        for idx, row in short_candidates.iterrows():
            signal = {
                'timestamp': idx,
                'symbol': df.attrs.get('symbol', 'UNKNOWN'),
                'direction': 'SHORT',
                'strategy': strategy,
                'confidence': round(row['confidence_short'], 1),
                'entry_price': row['close'],
                'rsi': row['rsi'],
                'bb_position': row['bb_position'],
                'volume_surge': row['volume_surge'],
                'momentum': row['momentum']
            }
            signals.append(signal)
        
        # Tri par confidence décroissante
        signals.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Limite max trades/jour (seulement pour live trading)
        if apply_daily_limit and len(signals) > self.MAX_TRADES_PER_DAY:
            signals = signals[:self.MAX_TRADES_PER_DAY]
            logger.info(f"⚠️ Limited to {self.MAX_TRADES_PER_DAY} signals/day")
        
        logger.info(f"✓ Generated {len(signals)} signals (min confidence: {self.MIN_CONFIDENCE})")
        
        return signals
    
    def should_execute_signal(self, signal: Dict) -> bool:
        """
        Vérifie si un signal doit être exécuté
        
        Critères :
        - Confidence >= 60
        - Max trades/jour non atteint
        - Pas de signal récent (cooldown 1h)
        
        Args:
            signal: Dict signal
        
        Returns:
            True si exécutable
        """
        # Confidence check
        if signal['confidence'] < self.MIN_CONFIDENCE:
            return False
        
        # Max trades/day check
        if self.signals_today >= self.MAX_TRADES_PER_DAY:
            logger.warning(f"Max trades/day ({self.MAX_TRADES_PER_DAY}) reached")
            return False
        
        # Cooldown check (1h)
        if self.last_signal_time:
            # Ensure both timestamps are tz-naive or both tz-aware
            sig_time = signal['timestamp']
            if hasattr(sig_time, 'tzinfo') and hasattr(self.last_signal_time, 'tzinfo'):
                if sig_time.tzinfo is None and self.last_signal_time.tzinfo is not None:
                    sig_time = sig_time.replace(tzinfo=self.last_signal_time.tzinfo)
                elif sig_time.tzinfo is not None and self.last_signal_time.tzinfo is None:
                    sig_time = sig_time.tz_localize(None)
            
            time_diff = sig_time - self.last_signal_time
            if time_diff.total_seconds() < 3600:  # 1h
                return False
        
        return True
    
    def record_signal(self, signal: Dict):
        """Enregistre un signal exécuté"""
        self.signals_today += 1
        self.last_signal_time = signal['timestamp']
        logger.info(f"📝 Signal recorded: {signal['direction']} @ {signal['entry_price']} (conf: {signal['confidence']})")
    
    def reset_daily_counter(self):
        """Reset le compteur quotidien"""
        self.signals_today = 0
        logger.info("🔄 Daily signal counter reset")


if __name__ == "__main__":
    # Test
    from data_pipeline import DataPipeline
    from feature_engineering import FeatureEngineer
    
    print("🐉 Testing Saiyan Signal Generator v0.1\n")
    
    pipeline = DataPipeline()
    df = pipeline.fetch_crypto_data('BTC/USDT', '1h', 500)
    df.attrs['symbol'] = 'BTC/USDT'
    
    fe = FeatureEngineer()
    df = fe.calculate_all_features(df)
    
    sg = SignalGenerator()
    signals = sg.generate_signals(df, 'mean_reversion')
    
    print(f"\nGenerated {len(signals)} signals:")
    for sig in signals[:5]:
        print(f"  {sig['timestamp']} | {sig['direction']:5} | Conf: {sig['confidence']:5.1f} | Price: {sig['entry_price']:.2f}")
