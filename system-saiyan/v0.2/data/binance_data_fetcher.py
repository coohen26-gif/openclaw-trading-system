"""
🐉 Binance Data Fetcher - Système Saiyan v0.2

Real-time and historical data fetching from Binance API.

Features:
- OHLCV data fetching (public API, no auth required)
- Historical data download (2020-2026)
- Rate limiting & retry logic
- Local caching (CSV)
- Multi-asset support (BTC, ETH, SOL)

Usage:
    python data/binance_data_fetcher.py --symbol BTC/USDT --timeframe 1d --limit 500
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import time
import logging
import argparse


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('saiyan_data')


class BinanceDataFetcher:
    """
    Binance data fetcher with rate limiting and caching.
    
    Uses public API only (no authentication required) for OHLCV data.
    """
    
    DEFAULT_SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d', '1w']
    MAX_CANDLES_PER_REQUEST = 1000
    
    def __init__(self, cache_dir: str = 'data/cache', rate_limit_ms: int = 1200):
        """
        Initialize data fetcher.
        
        Args:
            cache_dir: Directory for cached CSV files
            rate_limit_ms: Rate limit in milliseconds (Binance: 1200ms for weight)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit_ms = rate_limit_ms
        self.last_request_time = 0
        
        # Initialize exchange (public API only)
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',  # Use futures data (more liquid)
                'adjustForTimeDifference': True
            }
        })
        
        # Load markets
        self.markets = {}
        self.symbols = []
        self._load_markets_safe()
        
        logger.info(f"Binance Data Fetcher initialized ({len(self.symbols)} symbols)")
    
    def _load_markets_safe(self):
        """Load markets with error handling"""
        try:
            self.markets = self.exchange.load_markets()
            self.symbols = list(self.markets.keys())
            logger.info(f"Loaded {len(self.symbols)} markets")
        except Exception as e:
            logger.warning(f"Could not load markets: {e}. Using fallback symbols.")
            self.symbols = self.DEFAULT_SYMBOLS.copy()
            self.markets = {s: {'symbol': s} for s in self.symbols}
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        now = time.time() * 1000
        elapsed = now - self.last_request_time
        if elapsed < self.rate_limit_ms:
            sleep_time = (self.rate_limit_ms - elapsed) / 1000
            time.sleep(sleep_time)
        self.last_request_time = time.time() * 1000
    
    def _get_cache_path(self, symbol: str, timeframe: str, limit: int) -> Path:
        """Generate cache file path"""
        symbol_safe = symbol.replace('/', '_').replace(':', '_')
        return self.cache_dir / f"{symbol_safe}_{timeframe}_{limit}.csv"
    
    def _load_from_cache(self, symbol: str, timeframe: str, limit: int) -> Optional[pd.DataFrame]:
        """Load data from cache if available and fresh (<1h)"""
        cache_path = self._get_cache_path(symbol, timeframe, limit)
        
        if not cache_path.exists():
            return None
        
        # Check if cache is fresh (<1 hour old)
        cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        if cache_age.total_seconds() > 3600:
            logger.debug(f"Cache too old ({cache_age}), refreshing")
            return None
        
        try:
            df = pd.read_csv(cache_path, index_col='timestamp', parse_dates=True)
            logger.debug(f"Loaded {len(df)} candles from cache")
            return df
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None
    
    def _save_to_cache(self, df: pd.DataFrame, symbol: str, timeframe: str, limit: int):
        """Save data to cache"""
        cache_path = self._get_cache_path(symbol, timeframe, limit)
        df.to_csv(cache_path)
        logger.debug(f"Cached {len(df)} candles to {cache_path}")
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1d',
        limit: int = 500,
        use_cache: bool = True,
        since: datetime = None
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data from Binance.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles (max 1000)
            use_cache: Use cached data if available
            since: Start date (optional)
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        # Validate inputs
        if symbol not in self.symbols:
            logger.warning(f"Symbol {symbol} not found, using fallback")
            symbol = 'BTC/USDT'
        
        if timeframe not in self.TIMEFRAMES:
            raise ValueError(f"Invalid timeframe: {timeframe}. Choose from {self.TIMEFRAMES}")
        
        if limit > self.MAX_CANDLES_PER_REQUEST:
            logger.warning(f"Limit {limit} exceeds max {self.MAX_CANDLES_PER_REQUEST}, capping")
            limit = self.MAX_CANDLES_PER_REQUEST
        
        # Try cache first
        if use_cache:
            cached = self._load_from_cache(symbol, timeframe, limit)
            if cached is not None:
                return cached
        
        # Fetch from API
        self._rate_limit()
        
        try:
            if since:
                since_ms = int(since.timestamp() * 1000)
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since=since_ms, limit=limit)
            else:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            if not ohlcv:
                logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Convert to float
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            # Cache the result
            if use_cache:
                self._save_to_cache(df, symbol, timeframe, limit)
            
            logger.info(f"Fetched {len(df)} candles for {symbol} ({timeframe})")
            return df
            
        except Exception as e:
            logger.error(f"Fetch error for {symbol}: {e}")
            # Return cached data even if old on error
            if use_cache:
                old_cache = self._load_from_cache(symbol, timeframe, limit)
                if old_cache is not None:
                    logger.warning(f"Returning stale cache for {symbol}")
                    return old_cache
            raise
    
    def fetch_multi_asset(
        self,
        symbols: Optional[List[str]] = None,
        timeframe: str = '1d',
        limit: int = 500
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch OHLCV data for multiple assets.
        
        Args:
            symbols: List of symbols (default: BTC, ETH, SOL)
            timeframe: Candle timeframe
            limit: Number of candles
        
        Returns:
            Dict of symbol -> DataFrame
        """
        if symbols is None:
            symbols = self.DEFAULT_SYMBOLS
        
        results = {}
        for symbol in symbols:
            try:
                df = self.fetch_ohlcv(symbol, timeframe, limit)
                if len(df) > 0:
                    results[symbol] = df
                    logger.info(f"✓ {symbol}: {len(df)} candles")
                else:
                    logger.warning(f"✗ {symbol}: No data")
            except Exception as e:
                logger.error(f"✗ {symbol}: {e}")
        
        return results
    
    def fetch_historical_range(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = '1d'
    ) -> pd.DataFrame:
        """
        Fetch historical data for a specific date range.
        
        Args:
            symbol: Trading pair
            start_date: Start date
            end_date: End date
            timeframe: Candle timeframe
        
        Returns:
            DataFrame with OHLCV data
        """
        all_data = []
        current_date = start_date
        
        while current_date < end_date:
            logger.info(f"Fetching {symbol} from {current_date.date()}")
            df = self.fetch_ohlcv(symbol, timeframe, limit=1000, since=current_date)
            
            if len(df) == 0:
                break
            
            all_data.append(df)
            
            # Move to next batch
            current_date = df.index[-1] + timedelta(days=1)
            
            # Rate limit between requests
            time.sleep(1.5)
        
        if not all_data:
            return pd.DataFrame()
        
        # Concatenate and deduplicate
        result = pd.concat(all_data)
        result = result[~result.index.duplicated()]
        result = result.sort_index()
        
        # Filter to requested range
        result = result[(result.index >= start_date) & (result.index <= end_date)]
        
        logger.info(f"Fetched {len(result)} candles for {symbol} ({start_date.date()} to {end_date.date()})")
        return result
    
    def get_ticker(self, symbol: str) -> Dict:
        """
        Get current ticker (price, volume, etc).
        
        Args:
            symbol: Trading pair
        
        Returns:
            Dict with ticker data
        """
        self._rate_limit()
        
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'high': ticker['high'],
                'low': ticker['low'],
                'volume': ticker['baseVolume'],
                'timestamp': datetime.now(timezone.utc)
            }
        except Exception as e:
            logger.error(f"Ticker fetch error for {symbol}: {e}")
            return {}


def main():
    """CLI interface for data fetching"""
    parser = argparse.ArgumentParser(description='Binance Data Fetcher')
    parser.add_argument('--symbol', type=str, default='BTC/USDT', help='Trading pair')
    parser.add_argument('--timeframe', type=str, default='1d', help='Candle timeframe')
    parser.add_argument('--limit', type=int, default=500, help='Number of candles')
    parser.add_argument('--output', type=str, default=None, help='Output CSV file')
    parser.add_argument('--no-cache', action='store_true', help='Disable caching')
    
    args = parser.parse_args()
    
    # Initialize fetcher
    fetcher = BinanceDataFetcher()
    
    # Fetch data
    logger.info(f"Fetching {args.limit} candles for {args.symbol} ({args.timeframe})")
    df = fetcher.fetch_ohlcv(
        args.symbol,
        args.timeframe,
        args.limit,
        use_cache=not args.no_cache
    )
    
    if len(df) == 0:
        logger.error("No data fetched")
        return
    
    # Display summary
    print(f"\n📊 {args.symbol} - {args.timeframe}")
    print("=" * 50)
    print(f"Candles: {len(df)}")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    print(f"Price range: ${df['close'].min():,.2f} - ${df['close'].max():,.2f}")
    print(f"Current price: ${df['close'].iloc[-1]:,.2f}")
    
    # Save to file
    if args.output:
        df.to_csv(args.output)
        logger.info(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
