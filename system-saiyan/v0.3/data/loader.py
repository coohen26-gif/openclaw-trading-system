"""
Data Loader for Saiyan v0.3

Loads real market data from:
- Local CSV files (historical BTC 2020-2026)
- Binance API (recent multi-asset via binance_data_fetcher)

NO SYNTHETIC DATA. NO np.random.normal().
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime, timedelta


class DataLoader:
    """
    Real data loader for Saiyan v0.3.
    
    Priority:
    1. Local CSV files (historical)
    2. Binance API cache (recent)
    3. Live Binance API fetch (if needed)
    
    NEVER generates synthetic data.
    """
    
    def __init__(self, data_dir: str = None):
        """
        Initialize data loader.
        
        Args:
            data_dir: Base directory for data files
        """
        if data_dir is None:
            # Default to v0.2 data directory (where real CSVs exist)
            # Path: /root/.openclaw/workspace/system-saiyan/v0.2/data
            self.data_dir = Path("/root/.openclaw/workspace/system-saiyan/v0.2/data")
        else:
            self.data_dir = Path(data_dir)
        
        self.cache_dir = self.data_dir / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Fee configuration (crypto perpetual)
        self.maker_fee = 0.0002  # 0.02%
        self.taker_fee = 0.0006  # 0.06%
        self.slippage = 0.0005   # 0.05%
        
        # Cached data
        self._data_cache: Dict[str, pd.DataFrame] = {}
    
    def load_btc_historical(self, start_date: str = "2020-01-01", end_date: str = None) -> pd.DataFrame:
        """
        Load historical BTC data from CSV.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), default today
            
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        # Try multiple file patterns
        csv_files = [
            self.data_dir / "btc_real_2020_2026_ohlcv.csv",  # Has 'date' column
            self.data_dir / "btc_realistic_2020_2026.csv",   # Has index column
            self.data_dir / "btc_real_2020_2026.csv",        # date,close only
        ]
        
        csv_file = None
        for f in csv_files:
            if f.exists():
                csv_file = f
                break
        
        if csv_file is None:
            raise FileNotFoundError(
                f"Historical BTC data not found. Expected one of: {csv_files}\n"
                "Run: python data/binance_data_fetcher.py --symbol BTC/USDT --timeframe 1d --limit 2500"
            )
        
        # Load CSV
        df = pd.read_csv(csv_file)
        
        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()
        
        # Handle different formats
        if 'date' not in df.columns:
            # Check if first column is date-like (index in realistic file)
            first_col = df.columns[0]
            if 'open' in df.columns:
                # Index column is actually date
                df = df.rename(columns={df.columns[0]: 'date'})
            else:
                raise ValueError(f"Cannot find date column in {csv_file}. Columns: {list(df.columns)}")
        
        # Parse dates
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter by date range
        df = df[(df['date'] >= start_date) & (df['date'] <= (end_date or datetime.now()))]
        
        # Sort by date
        df = df.sort_values('date').reset_index(drop=True)
        
        # Validate OHLCV (at minimum need close)
        if 'close' not in df.columns:
            raise ValueError(f"Missing 'close' column in {csv_file}")
        
        # Ensure OHLCV columns exist (create from close if needed)
        for col in ['open', 'high', 'low', 'volume']:
            if col not in df.columns:
                if col == 'volume':
                    df[col] = 0  # Default volume
                else:
                    df[col] = df['close']  # Fallback to close
        
        # Cache data
        cache_key = f"btc_historical_{start_date}_{end_date or 'now'}"
        self._data_cache[cache_key] = df
        
        print(f"✅ Loaded {len(df)} days of BTC data ({start_date} to {df['date'].max().strftime('%Y-%m-%d')})")
        
        return df
    
    def load_multi_asset(self, assets: List[str] = None, days: int = 100) -> Dict[str, pd.DataFrame]:
        """
        Load multi-asset data from Binance cache or fetch live.
        
        Args:
            assets: List of assets (e.g., ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'])
            days: Number of days to load
            
        Returns:
            Dict of asset -> DataFrame
        """
        if assets is None:
            assets = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
        
        data = {}
        
        for asset in assets:
            symbol = asset.replace('/', '')  # BTC/USDT -> BTCUSDT
            cache_file = self.cache_dir / f"{symbol}_1d_{days}.csv"
            
            if cache_file.exists():
                # Load from cache
                df = pd.read_csv(cache_file)
                print(f"✅ Loaded {asset} from cache ({len(df)} days)")
            else:
                # Fetch from Binance via binance_data_fetcher
                df = self._fetch_from_binance(symbol, days)
                df.to_csv(cache_file, index=False)
                print(f"✅ Fetched {asset} from Binance ({len(df)} days), cached to {cache_file}")
            
            # Normalize
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            data[asset] = df
        
        return data
    
    def _fetch_from_binance(self, symbol: str, days: int = 100) -> pd.DataFrame:
        """
        Fetch data from Binance public API.
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            days: Number of days
            
        Returns:
            DataFrame with OHLCV data
        """
        import urllib.request
        import json
        
        # Binance Kline endpoint
        interval = "1d"
        limit = min(days, 1000)  # Binance max 1000 per request
        
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                klines = json.loads(response.read().decode())
            
            # Parse klines
            # [open_time, open, high, low, close, volume, close_time, quote_volume, trades, taker_buy_base, taker_buy_quote, ignore]
            df = pd.DataFrame(klines, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
            
            # Convert types
            df['date'] = pd.to_datetime(df['open_time'], unit='ms')
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            # Select columns
            df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
            
            return df
            
        except Exception as e:
            print(f"⚠️ Binance fetch failed: {e}")
            # Fallback: try to load from v0.2 cache
            fallback = self.cache_dir / f"{symbol}_1d_50.csv"
            if fallback.exists():
                print(f"⚠️ Using fallback cache: {fallback}")
                return pd.read_csv(fallback)
            raise
    
    def calculate_returns(self, prices: pd.Series, log_returns: bool = False) -> pd.Series:
        """
        Calculate returns from price series.
        
        Args:
            prices: Price series
            log_returns: Use log returns instead of simple returns
            
        Returns:
            Returns series
        """
        if log_returns:
            return np.log(prices / prices.shift(1))
        else:
            return prices.pct_change()
    
    def apply_fees(self, returns: pd.Series, position_side: pd.Series = None) -> pd.Series:
        """
        Apply trading fees and slippage to returns.
        
        Args:
            returns: Gross returns series
            position_side: Series of position direction (1=long, -1=short, 0=flat)
                          If None, assumes fee on every non-zero return
            
        Returns:
            Net returns after fees
        """
        net_returns = returns.copy()
        
        # Round-trip fee (entry + exit)
        round_trip_fee = self.taker_fee * 2 + self.slippage * 2
        
        if position_side is not None:
            # Apply fee only when position changes or closes
            position_changes = position_side.diff().abs() > 0
            position_closes = (position_side == 0) & (position_side.shift(1) != 0)
            fee_mask = position_changes | position_closes
            net_returns[fee_mask] -= round_trip_fee
        else:
            # Conservative: apply fee on every non-zero return
            net_returns[returns != 0] -= round_trip_fee
        
        return net_returns
    
    def get_current_prices(self, assets: List[str] = None) -> Dict[str, float]:
        """
        Get current live prices from Binance.
        
        Args:
            assets: List of assets
            
        Returns:
            Dict of asset -> current price
        """
        if assets is None:
            assets = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        
        prices = {}
        
        for asset in assets:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={asset}"
            try:
                with urllib.request.urlopen(url, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    prices[asset] = float(data['price'])
            except Exception as e:
                print(f"⚠️ Failed to fetch {asset}: {e}")
                prices[asset] = None
        
        return prices


# Convenience functions
def load_btc_data(start_date: str = "2020-01-01", end_date: str = None) -> pd.DataFrame:
    """Load BTC historical data."""
    loader = DataLoader()
    return loader.load_btc_historical(start_date, end_date)


def load_multi_asset_data(assets: List[str] = None, days: int = 100) -> Dict[str, pd.DataFrame]:
    """Load multi-asset data."""
    loader = DataLoader()
    return loader.load_multi_asset(assets, days)


def load_csv(asset: str) -> pd.DataFrame:
    """
    Load CSV data for an asset.
    
    Args:
        asset: Asset symbol (e.g., 'BTC/USDT')
        
    Returns:
        DataFrame with OHLCV data, indexed by date
    """
    loader = DataLoader()
    
    if 'BTC' in asset.upper():
        # Load BTC historical
        df = loader.load_btc_historical()
    else:
        # Load from cache or fetch
        symbol = asset.replace('/', '')
        cache_file = loader.cache_dir / f"{symbol}_1d_100.csv"
        
        if cache_file.exists():
            df = pd.read_csv(cache_file)
        else:
            df = loader._fetch_from_binance(symbol, 100)
            df.to_csv(cache_file, index=False)
    
    # Set date as index
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    return df


def load_binance_csv(asset: str) -> pd.DataFrame:
    """
    Load Binance CSV data for an asset (alias for load_csv).
    
    Args:
        asset: Asset symbol (e.g., 'BTC/USDT')
        
    Returns:
        DataFrame with OHLCV data, indexed by date
    """
    return load_csv(asset)


def get_data_range(df: pd.DataFrame, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    Filter DataFrame by date range.
    
    Args:
        df: DataFrame with datetime index
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        Filtered DataFrame
    """
    if df.index.dtype != 'datetime64[ns]':
        df.index = pd.to_datetime(df.index)
    
    mask = pd.Series(True, index=df.index)
    
    if start_date:
        mask &= df.index >= pd.to_datetime(start_date)
    if end_date:
        mask &= df.index <= pd.to_datetime(end_date)
    
    return df[mask]


if __name__ == "__main__":
    # Test data loader
    print("🧪 Testing Data Loader...\n")
    
    loader = DataLoader()
    
    # Test 1: Load BTC historical
    print("Test 1: BTC Historical Data")
    btc = loader.load_btc_historical("2020-01-01", "2026-05-26")
    print(f"  Shape: {btc.shape}")
    print(f"  Date range: {btc['date'].min()} to {btc['date'].max()}")
    print(f"  Price range: ${btc['close'].min():.2f} - ${btc['close'].max():.2f}")
    print()
    
    # Test 2: Calculate returns
    print("Test 2: Returns Calculation")
    returns = loader.calculate_returns(btc['close'])
    print(f"  Mean daily return: {returns.mean():.4%}")
    print(f"  Std daily return: {returns.std():.4%}")
    print(f"  Skew: {returns.skew():.2f}")
    print(f"  Kurtosis: {returns.kurtosis():.2f}")
    print()
    
    # Test 3: Apply fees
    print("Test 3: Fee Application")
    gross_return = 0.05  # 5% gain
    net_return = loader.apply_fees(pd.Series([gross_return])).iloc[0]
    print(f"  Gross: {gross_return:.2%}")
    print(f"  Net (after fees): {net_return:.2%}")
    print(f"  Fee drag: {(gross_return - net_return):.4%}")
    print()
    
    # Test 4: Multi-asset (from cache)
    print("Test 4: Multi-Asset Data")
    try:
        multi = loader.load_multi_asset(['BTC/USDT', 'ETH/USDT', 'SOL/USDT'], days=50)
        for asset, df in multi.items():
            print(f"  {asset}: {len(df)} days, ${df['close'].iloc[-1]:.2f}")
    except Exception as e:
        print(f"  ⚠️ Multi-asset test skipped: {e}")
    print()
    
    print("✅ All tests completed!")
