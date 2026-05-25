"""
Système Saiyan v0.1 - Feature Engineering
Calcul des indicateurs techniques : RSI, Bollinger Bands, Volatilité, etc.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Calcul des features techniques pour le trading
    Focus : Mean Reversion (prioritaire) + Momentum
    """
    
    def __init__(self):
        pass
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        RSI (Relative Strength Index)
        Mean reversion indicator
        
        Args:
            df: DataFrame avec colonne 'close'
            period: Période RSI (default 14)
        
        Returns:
            Series RSI
        """
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_bollinger_bands(self, 
                                   df: pd.DataFrame, 
                                   period: int = 20, 
                                   std_dev: float = 2.5) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands
        Mean reversion indicator
        
        Args:
            df: DataFrame avec 'close'
            period: Période moyenne mobile (20)
            std_dev: Nombre d'écart-types (2.5 pour signaux plus stricts)
        
        Returns:
            (upper_band, middle_band, lower_band)
        """
        middle = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        
        return upper, middle, lower
    
    def calculate_volatility(self, 
                             df: pd.DataFrame, 
                             period: int = 20) -> pd.Series:
        """
        Volatilité historique (écart-type des rendements)
        
        Args:
            df: DataFrame avec 'close'
            period: Période de calcul
        
        Returns:
            Series volatilité annualisée
        """
        returns = df['close'].pct_change()
        volatility = returns.rolling(window=period).std() * np.sqrt(365 * 24)  # Annualisé hourly
        
        return volatility
    
    def calculate_momentum(self,
                           df: pd.DataFrame,
                           period: int = 14) -> pd.Series:
        """
        Momentum (Rate of Change)
        
        Args:
            df: DataFrame avec 'close'
            period: Période de calcul
        
        Returns:
            Series momentum en %
        """
        momentum = (df['close'] / df['close'].shift(period) - 1) * 100
        
        return momentum
    
    def calculate_volume_surge(self,
                               df: pd.DataFrame,
                               period: int = 20) -> pd.Series:
        """
        Volume Surge (ratio volume actuel / volume moyen)
        
        Args:
            df: DataFrame avec 'volume'
            period: Période moyenne
        
        Returns:
            Series volume ratio
        """
        avg_volume = df['volume'].rolling(window=period).mean()
        volume_surge = df['volume'] / avg_volume
        
        return volume_surge
    
    def calculate_atr(self,
                      df: pd.DataFrame,
                      period: int = 14) -> pd.Series:
        """
        ATR (Average True Range) - Mesure de volatilité
        
        Args:
            df: DataFrame avec 'high', 'low', 'close'
            period: Période de calcul
        
        Returns:
            Series ATR
        """
        high = df['high']
        low = df['low']
        close = df['close'].shift(1)
        
        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def calculate_all_features(self, 
                                df: pd.DataFrame,
                                rsi_period: int = 14,
                                bb_period: int = 20,
                                bb_std: float = 2.5) -> pd.DataFrame:
        """
        Calcule toutes les features d'un coup
        
        Args:
            df: DataFrame OHLCV
            rsi_period: Période RSI
            bb_period: Période Bollinger Bands
            bb_std: Écart-types pour BB
        
        Returns:
            DataFrame avec toutes les features
        """
        df = df.copy()
        
        # RSI
        df['rsi'] = self.calculate_rsi(df, rsi_period)
        
        # Bollinger Bands
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = self.calculate_bollinger_bands(
            df, bb_period, bb_std
        )
        
        # Position dans les BB (0 = lower, 0.5 = middle, 1 = upper)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Volatility
        df['volatility'] = self.calculate_volatility(df)
        
        # Momentum
        df['momentum'] = self.calculate_momentum(df)
        
        # Volume Surge
        df['volume_surge'] = self.calculate_volume_surge(df)
        
        # ATR
        df['atr'] = self.calculate_atr(df)
        
        # Returns
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Drop NaN rows
        df = df.dropna()
        
        logger.info(f"✓ Calculated {len(df.columns)} features for {len(df)} candles")
        
        return df
    
    def detect_mean_reversion_signals(self, 
                                       df: pd.DataFrame,
                                       rsi_oversold: float = 25,
                                       rsi_overbought: float = 75) -> pd.DataFrame:
        """
        Détecte les signaux mean reversion
        
        Args:
            df: DataFrame avec features
            rsi_oversold: Threshold RSI oversold
            rsi_overbought: Threshold RSI overbought
        
        Returns:
            DataFrame avec colonnes signal_long/signal_short
        """
        df = df.copy()
        
        # Signal LONG : RSI oversold + prix < BB lower
        df['signal_long'] = (
            (df['rsi'] < rsi_oversold) & 
            (df['close'] < df['bb_lower'])
        ).astype(int)
        
        # Signal SHORT : RSI overbought + prix > BB upper
        df['signal_short'] = (
            (df['rsi'] > rsi_overbought) & 
            (df['close'] > df['bb_upper'])
        ).astype(int)
        
        return df
    
    def detect_momentum_signals(self,
                                 df: pd.DataFrame,
                                 momentum_threshold: float = 2.0,
                                 volume_surge_threshold: float = 1.5) -> pd.DataFrame:
        """
        Détecte les signaux momentum (à corriger/optimiser)
        
        Args:
            df: DataFrame avec features
            momentum_threshold: Seuil momentum en %
            volume_surge_threshold: Seuil volume surge
        
        Returns:
            DataFrame avec colonnes momentum_long/momentum_short
        """
        df = df.copy()
        
        # Signal LONG : Momentum positif + volume surge
        df['momentum_long'] = (
            (df['momentum'] > momentum_threshold) &
            (df['volume_surge'] > volume_surge_threshold)
        ).astype(int)
        
        # Signal SHORT : Momentum négatif + volume surge
        df['momentum_short'] = (
            (df['momentum'] < -momentum_threshold) &
            (df['volume_surge'] > volume_surge_threshold)
        ).astype(int)
        
        return df


if __name__ == "__main__":
    # Test
    from data_pipeline import DataPipeline
    
    print("🐉 Testing Saiyan Feature Engineering v0.1\n")
    
    pipeline = DataPipeline()
    df = pipeline.fetch_crypto_data('BTC/USDT', '1h', 200)
    
    fe = FeatureEngineer()
    df_features = fe.calculate_all_features(df)
    
    print(f"\nFeatures calculated: {list(df_features.columns)}")
    print(f"\nLast 5 rows:\n{df_features.tail()}")
    
    # Test signal detection
    df_signals = fe.detect_mean_reversion_signals(df_features)
    print(f"\nMean reversion signals: {df_signals['signal_long'].sum()} LONG, {df_signals['signal_short'].sum()} SHORT")
