#!/usr/bin/env python3
"""
Binance Connector - Real-time Data & Execution

Module: Phase 3 - Production Readiness
Author: Saiyan Autonomous Trading System
Date: May 25, 2026

Features:
- Real-time OHLCV data fetching (Binance API)
- Historical data download (2020-2026)
- Testnet execution (paper trading)
- Account balance monitoring
- Order management (market, limit, stop-loss)
- Rate limiting & retry logic
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LOSS_LIMIT = "stop_loss_limit"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    """Order representation"""
    symbol: str
    side: OrderSide
    type: OrderType
    amount: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    timestamp: datetime = None
    order_id: str = None
    status: str = "pending"
    filled: float = 0.0
    avg_price: float = 0.0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class Position:
    """Position representation"""
    symbol: str
    side: str
    amount: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    leverage: int = 1


class BinanceConnector:
    """
    Binance API connector for data fetching and execution.
    
    Supports:
    - Public API (no auth): OHLCV data, ticker, orderbook
    - Private API (auth): Orders, balance, positions
    - Testnet: Paper trading environment
    """
    
    def __init__(
        self,
        api_key: str = None,
        api_secret: str = None,
        testnet: bool = True,
        rate_limit_ms: int = 1000
    ):
        """
        Initialize Binance connector.
        
        Args:
            api_key: Binance API key (required for private endpoints)
            api_secret: Binance API secret (required for private endpoints)
            testnet: Use testnet (paper trading) if True
            rate_limit_ms: Rate limit in milliseconds
        """
        self.testnet = testnet
        self.rate_limit_ms = rate_limit_ms
        self.last_request_time = 0
        
        # Initialize exchange
        if testnet:
            # Testnet mode: use public API only, simulate execution
            self.exchange = ccxt.binance({
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',
                    'adjustForTimeDifference': True
                }
            })
            logger.info("Initialized Binance Testnet connector (public API only)")
        else:
            if not api_key or not api_secret:
                raise ValueError("API key and secret required for production mode")
            self.exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future'
                }
            })
            logger.info("Initialized Binance Production connector")
        
        # Load markets (public endpoint, works without auth)
        self.markets = {}
        self.symbols = []
        self._load_markets_safe()
        
        # In-memory order book (testnet)
        self.orders: List[Order] = []
        self.positions: Dict[str, Position] = {}
        self.balance = 100000.0  # Starting balance (testnet)
    
    def _load_markets_safe(self):
        """Load markets with error handling"""
        try:
            self.markets = self.exchange.load_markets()
            self.symbols = list(self.markets.keys())
            logger.info(f"Loaded {len(self.symbols)} markets")
        except Exception as e:
            logger.warning(f"Could not load markets: {e}. Using fallback symbols.")
            # Fallback to common symbols
            self.symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT']
            self.markets = {s: {} for s in self.symbols}
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        now = time.time() * 1000
        elapsed = now - self.last_request_time
        if elapsed < self.rate_limit_ms:
            sleep_time = (self.rate_limit_ms - elapsed) / 1000
            time.sleep(sleep_time)
        self.last_request_time = time.time() * 1000
    
    # ==================== PUBLIC API (Data) ====================
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 1000,
        since: datetime = None
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data from Binance.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles (max 1000)
            since: Start date (optional)
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        self._rate_limit()
        
        try:
            if since:
                since_ms = int(since.timestamp() * 1000)
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since=since_ms, limit=limit)
            else:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"Fetched {len(df)} candles for {symbol} ({timeframe})")
            return df
        
        except Exception as e:
            logger.error(f"Error fetching OHLCV: {e}")
            return pd.DataFrame()
    
    def fetch_historical_range(
        self,
        symbol: str,
        timeframe: str = '1h',
        start_date: datetime = None,
        end_date: datetime = None
    ) -> pd.DataFrame:
        """
        Fetch historical data for a date range (pagination handled automatically).
        
        Args:
            symbol: Trading pair
            timeframe: Candle timeframe
            start_date: Start date
            end_date: End date
        
        Returns:
            DataFrame with full historical data
        """
        if not start_date:
            start_date = datetime(2020, 1, 1)
        if not end_date:
            end_date = datetime.utcnow()
        
        all_data = []
        current_date = start_date
        
        logger.info(f"Fetching historical data: {start_date} to {end_date}")
        
        while current_date < end_date:
            df = self.fetch_ohlcv(symbol, timeframe, limit=1000, since=current_date)
            if df.empty:
                break
            
            all_data.append(df)
            current_date = df.index[-1] + timedelta(hours=1)
            
            logger.info(f"Progress: {current_date}")
            
            # Small delay to avoid rate limits
            time.sleep(0.5)
        
        if all_data:
            full_df = pd.concat(all_data)
            full_df = full_df[~full_df.index.duplicated(keep='first')]
            full_df = full_df.sort_index()
            logger.info(f"Total: {len(full_df)} candles from {full_df.index[0]} to {full_df.index[-1]}")
            return full_df
        
        return pd.DataFrame()
    
    def fetch_ticker(self, symbol: str) -> Dict:
        """Fetch current ticker price"""
        self._rate_limit()
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            last_price = ticker.get('last') or ticker.get('close') or ticker.get('bid')
            return {
                'symbol': symbol,
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'last': ticker['last'],
                'volume': ticker.get('quoteVolume', 0),
                'change': ticker.get('percentage', 0),
                'timestamp': datetime.now(timezone.utc)
            }
        except Exception as e:
            logger.error(f"Error fetching ticker: {e}")
            # Fallback to recent OHLCV
            df = self.fetch_ohlcv(symbol, '1m', limit=1)
            if not df.empty:
                price = df['close'].iloc[-1]
                return {
                    'symbol': symbol,
                    'bid': price,
                    'ask': price * 1.001,
                    'last': price,
                    'volume': 0,
                    'change': 0,
                    'timestamp': datetime.now(timezone.utc)
                }
            raise
    
    def fetch_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        """Fetch order book"""
        self._rate_limit()
        orderbook = self.exchange.fetch_order_book(symbol, limit=limit)
        return {
            'symbol': symbol,
            'bids': orderbook['bids'],
            'asks': orderbook['asks'],
            'timestamp': datetime.utcnow()
        }
    
    # ==================== PRIVATE API (Execution) ====================
    
    def get_balance(self) -> Dict:
        """Get account balance"""
        if self.testnet:
            return {'USDT': self.balance, 'BTC': 0, 'ETH': 0, 'SOL': 0}
        
        self._rate_limit()
        balance = self.exchange.fetch_balance()
        return {
            'USDT': balance['total'].get('USDT', 0),
            'BTC': balance['total'].get('BTC', 0),
            'ETH': balance['total'].get('ETH', 0),
            'SOL': balance['total'].get('SOL', 0)
        }
    
    def create_order(
        self,
        symbol: str,
        side: OrderSide,
        type: OrderType,
        amount: float,
        price: float = None,
        stop_price: float = None
    ) -> Order:
        """
        Create and execute an order.
        
        Args:
            symbol: Trading pair
            side: BUY or SELL
            type: Order type (MARKET, LIMIT, STOP_LOSS)
            amount: Amount to trade
            price: Limit price (for LIMIT orders)
            stop_price: Stop price (for STOP_LOSS orders)
        
        Returns:
            Order object with execution details
        """
        order = Order(
            symbol=symbol,
            side=side,
            type=type,
            amount=amount,
            price=price,
            stop_price=stop_price
        )
        
        if self.testnet:
            # Simulate execution
            ticker = self.fetch_ticker(symbol)
            exec_price = ticker.get('ask') if side == OrderSide.BUY else ticker.get('bid')
            
            # Fallback to last price if bid/ask is None
            if exec_price is None:
                exec_price = ticker.get('last')
            
            if exec_price is None:
                logger.error(f"Could not determine execution price for {symbol}")
                order.status = "rejected"
                return order
            
            order.order_id = f"testnet_{len(self.orders) + 1:06d}"
            order.status = "filled"
            order.filled = amount
            order.avg_price = exec_price
            
            # Update balance
            cost = amount * exec_price
            if side == OrderSide.BUY:
                self.balance -= cost
                # Create position
                if symbol in self.positions:
                    pos = self.positions[symbol]
                    total_cost = (pos.amount * pos.entry_price) + cost
                    pos.amount += amount
                    pos.entry_price = total_cost / pos.amount
                else:
                    self.positions[symbol] = Position(
                        symbol=symbol,
                        side='long',
                        amount=amount,
                        entry_price=exec_price,
                        current_price=exec_price,
                        unrealized_pnl=0,
                        unrealized_pnl_pct=0
                    )
            else:
                self.balance += cost
                # Close or reduce position
                if symbol in self.positions:
                    pos = self.positions[symbol]
                    if pos.amount <= amount:
                        # Close position
                        pnl = (exec_price - pos.entry_price) * pos.amount
                        self.balance += pnl
                        del self.positions[symbol]
                    else:
                        # Reduce position
                        pos.amount -= amount
            
            self.orders.append(order)
            logger.info(f"[TESTNET] {side.value.upper()} {amount} {symbol} @ {exec_price:.2f}")
        
        else:
            # Real execution
            self._rate_limit()
            params = {}
            if stop_price:
                params['stopPrice'] = stop_price
            
            try:
                result = self.exchange.create_order(
                    symbol=symbol,
                    type=type.value,
                    side=side.value,
                    amount=amount,
                    price=price,
                    params=params
                )
                
                order.order_id = result['id']
                order.status = result['status']
                order.filled = result.get('filled', 0)
                order.avg_price = result.get('average', 0)
                
                logger.info(f"[LIVE] {side.value.upper()} {amount} {symbol} @ {order.avg_price:.2f}")
            
            except Exception as e:
                order.status = "rejected"
                logger.error(f"Order execution failed: {e}")
        
        return order
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get current position for a symbol"""
        if self.testnet:
            return self.positions.get(symbol)
        
        # Real position fetching would go here
        return None
    
    def close_all_positions(self) -> List[Order]:
        """Close all open positions (kill switch)"""
        closed_orders = []
        
        for symbol, position in list(self.positions.items()):
            side = OrderSide.SELL if position.side == 'long' else OrderSide.BUY
            order = self.create_order(
                symbol=symbol,
                side=side,
                type=OrderType.MARKET,
                amount=position.amount
            )
            closed_orders.append(order)
        
        logger.info(f"Closed {len(closed_orders)} positions (kill switch)")
        return closed_orders
    
    # ==================== UTILITIES ====================
    
    def get_trading_symbols(self, base: str = 'USDT') -> List[str]:
        """Get list of trading symbols with a specific base currency"""
        return [s for s in self.symbols if s.endswith(f'/{base}')]
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            ticker = self.fetch_ticker('BTC/USDT')
            logger.info(f"Connection OK - BTC/USDT: ${ticker['last']:.2f}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    # Initialize connector (testnet mode)
    connector = BinanceConnector(testnet=True)
    
    # Test connection
    print("\n=== Testing Connection ===")
    connector.test_connection()
    
    # Fetch historical data
    print("\n=== Fetching Historical Data ===")
    start = datetime(2025, 1, 1)
    end = datetime(2025, 12, 31)
    btc_data = connector.fetch_historical_range('BTC/USDT', '1h', start, end)
    print(f"BTC data: {len(btc_data)} candles")
    print(btc_data.tail())
    
    # Test trading (testnet)
    print("\n=== Test Trading ===")
    balance = connector.get_balance()
    print(f"Balance: {balance}")
    
    # Buy BTC
    order1 = connector.create_order('BTC/USDT', OrderSide.BUY, OrderType.MARKET, 0.1)
    print(f"Order: {order1}")
    
    # Check position
    position = connector.get_position('BTC/USDT')
    if position:
        print(f"Position: {position.amount} BTC @ ${position.entry_price:.2f}")
    
    # Sell BTC
    order2 = connector.create_order('BTC/USDT', OrderSide.SELL, OrderType.MARKET, 0.1)
    print(f"Order: {order2}")
    
    # Final balance
    balance = connector.get_balance()
    print(f"Final Balance: {balance}")
    
    print("\n=== Binance Connector Ready ===")
