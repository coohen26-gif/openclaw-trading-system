"""
Système Saiyan v0.1 - Data Pipeline
Récupération données crypto (Binance) et Metals (yfinance)
"""

import ccxt
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataPipeline:
    """Pipeline de récupération et nettoyage des données"""
    
    # Crypto assets (Binance)
    CRYPTO_SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT']
    
    # Metals (Yahoo Finance)
    METALS_SYMBOLS = ['GC=F',  # Gold
                      'SI=F',  # Silver
                      'PL=F',  # Platinum
                      'PA=F']  # Palladium
    
    def __init__(self):
        self.binance = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
    
    def fetch_crypto_data(self, 
                          symbol: str = 'BTC/USDT',
                          timeframe: str = '1h',
                          limit: int = 1000) -> pd.DataFrame:
        """
        Récupère les données crypto depuis Binance
        
        Args:
            symbol: Trading pair (ex: 'BTC/USDT')
            timeframe: '1h', '4h', '1d'
            limit: Nombre de bougies
        
        Returns:
            DataFrame avec OHLCV
        """
        try:
            logger.info(f"Fetching {symbol} {timeframe} data from Binance...")
            
            ohlcv = self.binance.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"✓ Retrieved {len(df)} candles for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching crypto data: {e}")
            return pd.DataFrame()
    
    def fetch_metals_data(self,
                          symbol: str = 'GC=F',
                          period: str = '6mo',
                          interval: str = '1h') -> pd.DataFrame:
        """
        Récupère les données Metals depuis Yahoo Finance
        
        Args:
            symbol: Yahoo Finance symbol (GC=F = Gold)
            period: '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'
            interval: '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'
        
        Returns:
            DataFrame avec OHLCV
        """
        try:
            logger.info(f"Fetching {symbol} data from Yahoo Finance...")
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()
            
            # Rename columns to match crypto format
            df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            }, inplace=True)
            
            logger.info(f"✓ Retrieved {len(df)} candles for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching metals data: {e}")
            return pd.DataFrame()
    
    def get_multi_asset_data(self,
                             timeframe: str = '1h',
                             limit: int = 1000) -> Dict[str, pd.DataFrame]:
        """
        Récupère les données pour tous les assets (60% Metals + 25% Crypto)
        
        Returns:
            Dict symbol -> DataFrame
        """
        data = {}
        
        # Crypto (25% of focus)
        for symbol in self.CRYPTO_SYMBOLS[:3]:  # Top 3 crypto
            df = self.fetch_crypto_data(symbol, timeframe, limit)
            if not df.empty:
                data[symbol] = df
        
        # Metals (60% of focus)
        for symbol in self.METALS_SYMBOLS[:2]:  # Gold + Silver
            df = self.fetch_metals_data(symbol, period='3mo', interval='1h')
            if not df.empty:
                data[symbol] = df
        
        logger.info(f"✓ Retrieved data for {len(data)} assets")
        return data
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Nettoie les données : remove NaN, duplicates
        
        Args:
            df: DataFrame brut
        
        Returns:
            DataFrame nettoyé
        """
        if df.empty:
            return df
        
        # Remove duplicates
        df = df[~df.index.duplicated(keep='first')]
        
        # Forward fill NaN values
        df = df.ffill()
        
        # Backward fill remaining NaN
        df = df.bfill()
        
        # Drop remaining NaN rows
        df = df.dropna()
        
        return df


if __name__ == "__main__":
    # Test du pipeline
    pipeline = DataPipeline()
    
    print("🐉 Testing Saiyan Data Pipeline v0.1\n")
    
    # Test crypto
    btc_data = pipeline.fetch_crypto_data('BTC/USDT', '1h', 100)
    print(f"\nBTC/USDT data shape: {btc_data.shape}")
    print(btc_data.tail())
    
    # Test metals
    gold_data = pipeline.fetch_metals_data('GC=F', '1mo', '1h')
    print(f"\nGold data shape: {gold_data.shape}")
    print(gold_data.tail())
