#!/usr/bin/env python3
"""
Portfolio Allocator - Multi-Asset Risk Parity with Automatic Rebalancing

Module: Phase 2 - Portfolio Multi-Asset
Author: Saiyan Autonomous Trading System
Date: May 24, 2026

Features:
- Risk Parity allocation (BTC/ETH/SOL)
- Automatic rebalancing (threshold-based)
- Real-time data from Binance
- Drift monitoring
- Transaction cost optimization
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Try to import CCXT for real data
try:
    import ccxt
    HAS_CCXT = True
except ImportError:
    HAS_CCXT = False
    print("⚠️  CCXT not available - using simulated data")


class RebalanceTrigger(Enum):
    """Reasons for rebalancing"""
    THRESHOLD = "threshold_breach"  # Drift > threshold
    SCHEDULED = "scheduled"  # Weekly rebalance
    MANUAL = "manual"  # Manual trigger
    EMERGENCY = "emergency"  # Circuit breaker triggered


@dataclass
class PortfolioState:
    """Current portfolio state"""
    total_value: float
    positions: Dict[str, float]  # asset -> amount held
    weights: Dict[str, float]  # asset -> current weight
    prices: Dict[str, float]  # asset -> current price
    timestamp: datetime


@dataclass
class RebalanceRecommendation:
    """Rebalancing recommendation"""
    should_rebalance: bool
    trigger: Optional[RebalanceTrigger]
    drift_max: float
    trades: List[Dict]  # List of trades to execute
    estimated_cost: float
    reason: str
    timestamp: datetime


class PortfolioAllocator:
    """
    Multi-asset portfolio allocator with Risk Parity and automatic rebalancing.
    
    Supports:
    - Risk Parity weights calculation
    - Threshold-based rebalancing
    - Scheduled rebalancing (weekly)
    - Transaction cost estimation
    - Drift monitoring
    """
    
    def __init__(
        self,
        assets: List[str] = ['BTC', 'ETH', 'SOL'],
        rebalance_threshold: float = 0.05,  # 5% drift triggers rebalance
        rebalance_schedule_days: int = 7,  # Weekly rebalance
        transaction_cost_bps: float = 10,  # 10 bps per trade
        min_trade_size: float = 10.0  # Minimum trade size in USD
    ):
        """
        Initialize portfolio allocator.
        
        Args:
            assets: List of assets to allocate
            rebalance_threshold: Drift threshold to trigger rebalance (0.05 = 5%)
            rebalance_schedule_days: Days between scheduled rebalances
            transaction_cost_bps: Transaction cost in basis points
            min_trade_size: Minimum trade size in USD
        """
        self.assets = assets
        self.n_assets = len(assets)
        self.rebalance_threshold = rebalance_threshold
        self.rebalance_schedule_days = rebalance_schedule_days
        self.transaction_cost_bps = transaction_cost_bps
        self.min_trade_size = min_trade_size
        
        # State
        self.current_weights = {asset: 1.0 / self.n_assets for asset in assets}
        self.target_weights = {asset: 1.0 / self.n_assets for asset in assets}
        self.last_rebalance = datetime.now() - timedelta(days=rebalance_schedule_days)
        
        # Price cache
        self.prices = {}
        
        # Risk Parity weights (will be calculated)
        self.risk_parity_weights = None
        
        print(f"📊 Portfolio Allocator initialized")
        print(f"   Assets: {', '.join(assets)}")
        print(f"   Rebalance threshold: {rebalance_threshold*100:.1f}%")
        print(f"   Rebalance schedule: Every {rebalance_schedule_days} days")
        print(f"   Transaction cost: {transaction_cost_bps} bps")
    
    def set_risk_parity_weights(self, weights: Dict[str, float]):
        """
        Set Risk Parity weights as target.
        
        Args:
            weights: Dict of asset -> weight
        """
        if set(weights.keys()) != set(self.assets):
            raise ValueError("Weights must cover all assets")
        
        self.risk_parity_weights = weights
        self.target_weights = weights
        
        print(f"\n🎯 Risk Parity weights set:")
        for asset, weight in weights.items():
            print(f"   {asset}: {weight*100:.1f}%")
    
    def update_prices(self, prices: Dict[str, float]):
        """
        Update current prices.
        
        Args:
            prices: Dict of asset -> price
        """
        self.prices = prices
    
    def calculate_current_weights(
        self,
        positions: Dict[str, float],
        prices: Dict[str, float]
    ) -> Tuple[Dict[str, float], float]:
        """
        Calculate current portfolio weights from positions and prices.
        
        Args:
            positions: Dict of asset -> amount held
            prices: Dict of asset -> current price
            
        Returns:
            Tuple of (weights dict, total value)
        """
        # Calculate value per asset
        values = {asset: positions.get(asset, 0) * prices.get(asset, 0) 
                  for asset in self.assets}
        
        # Total value
        total_value = sum(values.values())
        
        if total_value <= 0:
            # No value, return equal weights
            return {asset: 1.0 / self.n_assets for asset in self.assets}, 0.0
        
        # Calculate weights
        weights = {asset: values[asset] / total_value for asset in self.assets}
        
        return weights, total_value
    
    def calculate_drift(self) -> Tuple[float, str]:
        """
        Calculate maximum drift from target weights.
        
        Returns:
            Tuple of (max_drift, asset_with_max_drift)
        """
        max_drift = 0.0
        max_asset = None
        
        for asset in self.assets:
            current = self.current_weights.get(asset, 0)
            target = self.target_weights.get(asset, 0)
            drift = abs(current - target)
            
            if drift > max_drift:
                max_drift = drift
                max_asset = asset
        
        return max_drift, max_asset or self.assets[0]
    
    def check_rebalance_needed(
        self,
        positions: Dict[str, float],
        prices: Dict[str, float],
        force: bool = False
    ) -> RebalanceRecommendation:
        """
        Check if rebalancing is needed.
        
        Args:
            positions: Current positions
            prices: Current prices
            force: Force rebalance check
            
        Returns:
            RebalanceRecommendation
        """
        # Update prices
        self.update_prices(prices)
        
        # Calculate current weights
        current_weights, total_value = self.calculate_current_weights(positions, prices)
        self.current_weights = current_weights
        
        # Calculate drift
        max_drift, max_asset = self.calculate_drift()
        
        # Check if rebalance needed
        should_rebalance = False
        trigger = None
        reason = ""
        
        # Check threshold breach
        if max_drift >= self.rebalance_threshold:
            should_rebalance = True
            trigger = RebalanceTrigger.THRESHOLD
            reason = f"Drift {max_drift*100:.1f}% >= threshold {self.rebalance_threshold*100:.1f}% ({max_asset})"
        
        # Check scheduled rebalance
        days_since_rebalance = (datetime.now() - self.last_rebalance).days
        if days_since_rebalance >= self.rebalance_schedule_days:
            should_rebalance = True
            trigger = RebalanceTrigger.SCHEDULED
            reason = f"Scheduled rebbalance ({days_since_rebalance} days since last)"
        
        # Override if forced
        if force:
            should_rebalance = True
            trigger = RebalanceTrigger.MANUAL
            reason = "Manual trigger"
        
        # If no rebalance needed
        if not should_rebalance:
            return RebalanceRecommendation(
                should_rebalance=False,
                trigger=None,
                drift_max=max_drift,
                trades=[],
                estimated_cost=0.0,
                reason=f"No rebalance needed (max drift: {max_drift*100:.1f}%)",
                timestamp=datetime.now()
            )
        
        # Calculate trades needed
        trades = self._calculate_rebalance_trades(current_weights, total_value)
        
        # Estimate transaction cost
        total_trade_value = sum(abs(trade['value_usd']) for trade in trades)
        estimated_cost = total_trade_value * (self.transaction_cost_bps / 10000)
        
        return RebalanceRecommendation(
            should_rebalance=True,
            trigger=trigger,
            drift_max=max_drift,
            trades=trades,
            estimated_cost=estimated_cost,
            reason=reason,
            timestamp=datetime.now()
        )
    
    def _calculate_rebalance_trades(
        self,
        current_weights: Dict[str, float],
        total_value: float
    ) -> List[Dict]:
        """
        Calculate trades needed to rebalance to target weights.
        
        Args:
            current_weights: Current portfolio weights
            total_value: Total portfolio value
            
        Returns:
            List of trades to execute
        """
        trades = []
        
        for asset in self.assets:
            current_weight = current_weights.get(asset, 0)
            target_weight = self.target_weights.get(asset, 0)
            
            # Weight difference
            weight_diff = target_weight - current_weight
            
            # Value to trade
            value_diff = weight_diff * total_value
            
            # Skip if below minimum trade size
            if abs(value_diff) < self.min_trade_size:
                continue
            
            # Determine trade type
            trade_type = "BUY" if value_diff > 0 else "SELL"
            
            # Calculate quantity
            price = self.prices.get(asset, 0)
            quantity = abs(value_diff) / price if price > 0 else 0
            
            trades.append({
                'asset': asset,
                'action': trade_type,
                'quantity': quantity,
                'price': price,
                'value_usd': value_diff,
                'current_weight': current_weight,
                'target_weight': target_weight,
                'weight_change': weight_diff
            })
        
        return trades
    
    def execute_rebalance(self, trades: List[Dict]) -> Dict[str, float]:
        """
        Simulate execution of rebalance trades.
        
        Args:
            trades: List of trades to execute
            
        Returns:
            Updated positions
        """
        # This would integrate with actual exchange API
        # For now, just return the theoretical new positions
        
        print(f"\n💰 Executing rebalance ({len(trades)} trades):")
        for trade in trades:
            action_icon = "🟢" if trade['action'] == "BUY" else "🔴"
            print(f"   {action_icon} {trade['action']} {trade['quantity']:.6f} {trade['asset']} @ ${trade['price']:,.2f}")
            print(f"      Value: ${abs(trade['value_usd']):,.2f} | " +
                  f"Weight: {trade['current_weight']*100:.1f}% → {trade['target_weight']*100:.1f}%")
        
        return {}  # Would return updated positions
    
    def get_portfolio_summary(self, positions: Dict[str, float]) -> Dict:
        """
        Get comprehensive portfolio summary.
        
        Args:
            positions: Current positions
            
        Returns:
            Summary dict
        """
        current_weights, total_value = self.calculate_current_weights(positions, self.prices)
        max_drift, max_asset = self.calculate_drift()
        days_since_rebalance = (datetime.now() - self.last_rebalance).days
        
        return {
            'total_value': total_value,
            'current_weights': current_weights,
            'target_weights': self.target_weights,
            'max_drift': max_drift,
            'max_drift_asset': max_asset,
            'days_since_rebalance': days_since_rebalance,
            'rebalance_needed': max_drift >= self.rebalance_threshold,
            'timestamp': datetime.now()
        }
    
    def print_portfolio_state(self, positions: Dict[str, float]):
        """Print current portfolio state"""
        summary = self.get_portfolio_summary(positions)
        
        print("\n" + "="*70)
        print("📊 PORTFOLIO STATE")
        print("="*70)
        print(f"Total Value: ${summary['total_value']:,.2f}")
        print(f"Days Since Rebalance: {summary['days_since_rebalance']}")
        print("-"*70)
        print(f"{'Asset':<10} {'Current':<12} {'Target':<12} {'Drift':<12} {'Status':<15}")
        print("-"*70)
        
        for asset in self.assets:
            current = summary['current_weights'].get(asset, 0) * 100
            target = summary['target_weights'].get(asset, 0) * 100
            drift = (current - target)
            
            if abs(drift) >= self.rebalance_threshold * 100:
                status = "⚠️  REBALANCE"
            elif abs(drift) >= self.rebalance_threshold * 100 * 0.5:
                status = "⚡ Monitoring"
            else:
                status = "✅ OK"
            
            print(f"{asset:<10} {current:>8.1f}%   {target:>8.1f}%   {drift:>+8.1f}%   {status:<15}")
        
        print("-"*70)
        print(f"Max Drift: {summary['max_drift']*100:.1f}% ({summary['max_drift_asset']})")
        
        if summary['rebalance_needed']:
            print(f"🚨 REBALANCE NEEDED (drift >= {self.rebalance_threshold*100:.1f}%)")
        else:
            print(f"✅ No rebalance needed")
        
        print("="*70 + "\n")


class BinanceDataFetcher:
    """
    Fetch real-time prices from Binance.
    """
    
    def __init__(self):
        """Initialize Binance exchange"""
        if not HAS_CCXT:
            print("⚠️  CCXT not available - cannot fetch real data")
            self.exchange = None
            return
        
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
        })
        print("📈 Binance connection initialized")
    
    def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get current prices for symbols.
        
        Args:
            symbols: List of symbols (e.g., ['BTC/USDT', 'ETH/USDT'])
            
        Returns:
            Dict of symbol -> price
        """
        if not self.exchange:
            return {}
        
        prices = {}
        for symbol in symbols:
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                prices[symbol] = ticker['last']
            except Exception as e:
                print(f"⚠️  Error fetching {symbol}: {e}")
                prices[symbol] = 0.0
        
        return prices
    
    def get_historical_returns(
        self,
        symbols: List[str],
        timeframe: str = '1d',
        limit: int = 252
    ) -> pd.DataFrame:
        """
        Fetch historical returns for correlation/risk parity calculation.
        
        Args:
            symbols: List of symbols
            timeframe: Candle timeframe
            limit: Number of candles
            
        Returns:
            DataFrame of returns
        """
        if not self.exchange:
            return pd.DataFrame()
        
        returns_data = {}
        
        for symbol in symbols:
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit+1)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                
                # Calculate returns
                returns = df['close'].pct_change().dropna()
                returns_data[symbol] = returns.values
                
            except Exception as e:
                print(f"⚠️  Error fetching {symbol}: {e}")
        
        # Create DataFrame
        if returns_data:
            min_len = min(len(v) for v in returns_data.values())
            returns_data = {k: v[-min_len:] for k, v in returns_data.items()}
            return pd.DataFrame(returns_data)
        
        return pd.DataFrame()


def test_portfolio_allocator():
    """Test portfolio allocator with simulated data"""
    print("🧪 Testing Portfolio Allocator...\n")
    
    # Initialize allocator
    allocator = PortfolioAllocator(
        assets=['BTC', 'ETH', 'SOL'],
        rebalance_threshold=0.05,  # 5%
        rebalance_schedule_days=7
    )
    
    # Set Risk Parity weights (from Module 21)
    risk_parity_weights = {
        'BTC': 0.52,
        'ETH': 0.28,
        'SOL': 0.20
    }
    allocator.set_risk_parity_weights(risk_parity_weights)
    
    # Simulate current prices
    prices = {
        'BTC': 67500.0,
        'ETH': 3800.0,
        'SOL': 145.0
    }
    allocator.update_prices(prices)
    
    # Simulate positions (slightly drifted from target)
    positions = {
        'BTC': 0.10,  # $6,750
        'ETH': 1.50,  # $5,700
        'SOL': 30.0   # $4,350
    }
    
    # Print current state
    allocator.print_portfolio_state(positions)
    
    # Check if rebalance needed
    rec = allocator.check_rebalance_needed(positions, prices)
    
    print(f"\n📋 Rebalance Check:")
    print(f"   Needed: {'✅ YES' if rec.should_rebalance else '❌ NO'}")
    print(f"   Trigger: {rec.trigger.value if rec.trigger else 'None'}")
    print(f"   Max Drift: {rec.drift_max*100:.1f}%")
    print(f"   Reason: {rec.reason}")
    
    if rec.trades:
        print(f"\n💹 Recommended Trades ({len(rec.trades)}):")
        for trade in rec.trades:
            action_icon = "🟢" if trade['action'] == "BUY" else "🔴"
            print(f"   {action_icon} {trade['action']} {trade['quantity']:.4f} {trade['asset']} " +
                  f"(${abs(trade['value_usd']):,.2f})")
        
        print(f"\n💰 Estimated Cost: ${rec.estimated_cost:.2f} ({allocator.transaction_cost_bps} bps)")
    
    # Test with Binance real data (if available)
    if HAS_CCXT:
        print("\n" + "="*70)
        print("📈 Testing with Real Binance Data")
        print("="*70)
        
        fetcher = BinanceDataFetcher()
        
        # Get real prices
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
        real_prices = fetcher.get_prices(symbols)
        
        if real_prices:
            print(f"\n💰 Real Prices:")
            for symbol, price in real_prices.items():
                print(f"   {symbol}: ${price:,.2f}")
            
            # Get historical returns
            returns_df = fetcher.get_historical_returns(symbols)
            
            if not returns_df.empty:
                print(f"\n📊 Historical Returns ({len(returns_df)} days):")
                print(returns_df.describe())
                
                # Calculate correlation matrix
                corr_matrix = returns_df.corr()
                print(f"\n🔗 Correlation Matrix:")
                print(corr_matrix.round(3))
    
    print("\n✅ Portfolio Allocator test complete!")


if __name__ == "__main__":
    test_portfolio_allocator()
