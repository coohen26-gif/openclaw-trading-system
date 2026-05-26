"""
🐉 Momentum + HMM Strategy - Saiyan v0.3

REAL HMM regime detection (not fake if/else like v0.2).
Uses core.hmm_regime.HMMRegimeDetector with Baum-Welch algorithm.

Features:
- 4 regimes: Bull, Bear, Range, Volatile Bull
- Regime-dependent position sizing
- Regime-dependent stops/take-profit
- Trailing stop mechanism
- Time-based exit
- Fees applied (0.12% round-trip)

Usage:
    from strategies.momentum_hmm import MomentumHMMStrategy
    
    strategy = MomentumHMMStrategy(rolling_window=180)
    signal = strategy.generate_signal(prices, current_position=None)
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
from enum import Enum

from core.hmm_regime import HMMRegimeDetector, Regime


class SignalType(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"


@dataclass
class Signal:
    """Trading signal with all parameters."""
    direction: SignalType
    confidence: float  # 0-1
    position_pct: float  # 0-1 of capital
    stop_loss: float  # Price level
    take_profit: float  # Price level
    trailing_stop_pct: float  # Trailing stop percentage
    max_holding_days: int
    regime: Regime
    rationale: str


@dataclass
class Trade:
    """Active trade."""
    entry_price: float
    entry_date: pd.Timestamp
    direction: SignalType
    position_pct: float
    stop_loss: float
    take_profit: float
    trailing_stop_pct: float
    max_holding_days: int
    highest_price: float  # For trailing stop
    lowest_price: float  # For trailing stop (short)
    regime: Regime


class MomentumHMMStrategy:
    """
    Momentum strategy with real HMM regime detection.
    
    Uses 20-day momentum for signal generation.
    Uses HMM for regime detection and position sizing.
    """
    
    # Configuration by regime
    REGIME_CONFIG = {
        Regime.BULL: {
            'kelly_multiplier': 0.75,
            'momentum_period': 20,
            'stop_loss_pct': 5.0,
            'take_profit_pct': 15.0,
            'trailing_stop_pct': 8.0,
            'max_holding_days': 10,
            'min_confidence': 0.5,
        },
        Regime.BEAR: {
            'kelly_multiplier': 0.25,
            'momentum_period': 20,
            'stop_loss_pct': 3.0,
            'take_profit_pct': 8.0,
            'trailing_stop_pct': 5.0,
            'max_holding_days': 3,
            'min_confidence': 0.6,
            'no_trading': True,  # Conservative: no trading in bear
        },
        Regime.RANGE: {
            'kelly_multiplier': 0.25,
            'momentum_period': 10,
            'stop_loss_pct': 4.0,
            'take_profit_pct': 6.0,
            'trailing_stop_pct': 4.0,
            'max_holding_days': 5,
            'min_confidence': 0.55,
        },
        Regime.VOLATILE_BULL: {
            'kelly_multiplier': 0.50,
            'momentum_period': 15,
            'stop_loss_pct': 8.0,
            'take_profit_pct': 20.0,
            'trailing_stop_pct': 10.0,
            'max_holding_days': 7,
            'min_confidence': 0.5,
        },
    }
    
    # Fee configuration
    MAKER_FEE = 0.0002  # 0.02%
    TAKER_FEE = 0.0006  # 0.06%
    SLIPPAGE = 0.0005   # 0.05%
    ROUND_TRIP_FEE = 2 * TAKER_FEE + 2 * SLIPPAGE  # 0.22%
    
    def __init__(self, rolling_window: int = 180, momentum_period: int = 20):
        """
        Initialize strategy.
        
        Args:
            rolling_window: Days for HMM retraining (default: 180)
            momentum_period: Days for momentum calculation (default: 20)
        """
        self.rolling_window = rolling_window
        self.momentum_period = momentum_period
        
        # HMM detector
        self.hmm = HMMRegimeDetector(n_regimes=4, rolling_window=rolling_window)
        self.hmm_fitted = False
        
        # Active trade
        self.active_trade: Optional[Trade] = None
        
        # Performance tracking
        self.trades_closed = 0
        self.trades_won = 0
        self.total_pnl = 0.0
        
    def fit(self, prices: pd.Series) -> 'MomentumHMMStrategy':
        """
        Fit HMM on price history.
        
        Args:
            prices: Price series
            
        Returns:
            Self for chaining
        """
        returns = prices.pct_change().dropna()
        
        if len(returns) >= self.rolling_window:
            self.hmm.fit(returns)
            self.hmm_fitted = True
        
        return self
    
    def update(self, new_price: float, new_date: pd.Timestamp) -> Optional[Signal]:
        """
        Update strategy with new price and check for exit/entry.
        
        Args:
            new_price: Latest price
            new_date: Latest date
            
        Returns:
            Signal if action needed (entry or exit), None otherwise
        """
        # Check if we need to exit active trade
        if self.active_trade:
            exit_signal = self._check_exit(new_price, new_date)
            if exit_signal:
                return exit_signal
        
        # Check if we should enter new trade
        if not self.active_trade:
            entry_signal = self._check_entry(new_price, new_date)
            return entry_signal
        
        return None
    
    def _check_entry(self, price: float, date: pd.Timestamp) -> Optional[Signal]:
        """Check for entry signal."""
        # Need price history for momentum and HMM
        if not hasattr(self, '_price_history'):
            self._price_history = pd.Series([price], index=[date])
            return None
        
        # Update history
        new_hist = pd.Series([price], index=[date])
        self._price_history = pd.concat([self._price_history, new_hist])
        
        # Need enough data
        min_data = max(self.rolling_window, self.momentum_period * 2)
        if len(self._price_history) < min_data:
            return None
        
        # Calculate momentum
        returns = self._price_history.pct_change().dropna()
        momentum = returns.tail(self.momentum_period).mean()
        
        # Get regime from HMM
        if self.hmm_fitted:
            regime, confidence = self.hmm.predict(returns.tail(60))
        else:
            # Fallback: simple heuristic
            regime = self._simple_regime_detection(returns)
            confidence = 0.6
        
        # Get config for regime
        config = self.REGIME_CONFIG.get(regime, self.REGIME_CONFIG[Regime.RANGE])
        
        # Check if trading allowed
        if config.get('no_trading', False):
            return None
        
        # Check momentum signal
        if momentum <= 0:
            return None  # No long signal
        
        # Check confidence
        if confidence < config['min_confidence']:
            return None
        
        # Calculate position size (Kelly fractional, capped)
        position_pct = self._calculate_position_size(regime, confidence, momentum)
        
        # Calculate stops
        stop_loss = price * (1 - config['stop_loss_pct'] / 100)
        take_profit = price * (1 + config['take_profit_pct'] / 100)
        
        return Signal(
            direction=SignalType.LONG,
            confidence=confidence,
            position_pct=position_pct,
            stop_loss=stop_loss,
            take_profit=take_profit,
            trailing_stop_pct=config['trailing_stop_pct'] / 100,
            max_holding_days=config['max_holding_days'],
            regime=regime,
            rationale=f"Momentum {momentum:.2%}, {regime.value} regime, confidence {confidence:.0%}"
        )
    
    def _check_exit(self, price: float, date: pd.Timestamp) -> Optional[Signal]:
        """Check if we should exit active trade."""
        trade = self.active_trade
        
        # Update highest/lowest for trailing stop
        if trade.direction == SignalType.LONG:
            if price > trade.highest_price:
                trade.highest_price = price
        else:
            if price < trade.lowest_price:
                trade.lowest_price = price
        
        # Check stop loss
        if trade.direction == SignalType.LONG and price <= trade.stop_loss:
            return self._create_exit_signal(trade, price, date, "Stop Loss")
        
        # Check take profit
        if trade.direction == SignalType.LONG and price >= trade.take_profit:
            return self._create_exit_signal(trade, price, date, "Take Profit")
        
        # Check trailing stop (for long)
        if trade.direction == SignalType.LONG:
            trailing_stop = trade.highest_price * (1 - trade.trailing_stop_pct)
            if price <= trailing_stop:
                return self._create_exit_signal(trade, price, date, "Trailing Stop")
        
        # Check time exit
        holding_days = (date - trade.entry_date).days
        if holding_days >= trade.max_holding_days:
            return self._create_exit_signal(trade, price, date, f"Time Exit ({holding_days}j)")
        
        return None
    
    def _create_exit_signal(self, trade: Trade, price: float, date: pd.Timestamp, reason: str) -> Signal:
        """Create exit signal from active trade."""
        # Calculate PnL (including fees)
        if trade.direction == SignalType.LONG:
            gross_pnl = (price - trade.entry_price) / trade.entry_price
        else:
            gross_pnl = (trade.entry_price - price) / trade.entry_price
        
        net_pnl = gross_pnl - self.ROUND_TRIP_FEE
        
        # Update stats
        self.trades_closed += 1
        if net_pnl > 0:
            self.trades_won += 1
        self.total_pnl += net_pnl * trade.position_pct
        
        return Signal(
            direction=SignalType.FLAT,
            confidence=1.0,
            position_pct=0,
            stop_loss=0,
            take_profit=0,
            trailing_stop_pct=0,
            max_holding_days=0,
            regime=trade.regime,
            rationale=f"{reason} - PnL: {net_pnl:.2%} (gross: {gross_pnl:.2%}, fees: {self.ROUND_TRIP_FEE:.2%})"
        )
    
    def _calculate_position_size(self, regime: Regime, confidence: float, momentum: float) -> float:
        """
        Calculate position size using Kelly criterion with regime adjustment.
        
        Kelly formula: f* = (p * b - q) / b
        where p = win probability, q = loss probability, b = win/loss ratio
        
        Simplified: Use momentum as edge proxy, apply Kelly multiplier by regime.
        Cap at 5% of capital per trade.
        """
        config = self.REGIME_CONFIG[regime]
        kelly_mult = config['kelly_multiplier']
        
        # Simplified Kelly: use momentum as edge
        # Assume win rate ~55% when momentum positive, win/loss ratio ~2:1
        p = 0.55  # Base win rate
        b = 2.0   # Win/loss ratio
        
        # Adjust for momentum strength
        momentum_adj = min(1.0, momentum * 10)  # Cap adjustment
        p_adj = p + momentum_adj * 0.1  # Up to +10% win rate
        
        q = 1 - p_adj
        kelly = (p_adj * b - q) / b
        
        # Apply regime multiplier and cap
        kelly = max(0, kelly) * kelly_mult * confidence
        
        # Hard cap: 5% of capital per trade
        position_pct = min(kelly, 0.05)
        
        return position_pct
    
    def _simple_regime_detection(self, returns: pd.Series) -> Regime:
        """
        Simple regime detection fallback if HMM not fitted.
        
        Uses momentum and volatility heuristics.
        """
        recent_ret = returns.tail(20).mean()
        recent_vol = returns.tail(20).std()
        overall_vol = returns.std()
        
        if recent_ret > 0 and recent_vol < overall_vol:
            return Regime.BULL
        elif recent_ret < 0 and recent_vol > overall_vol:
            return Regime.BEAR
        elif abs(recent_ret) < 0.001:
            return Regime.RANGE
        else:
            return Regime.VOLATILE_BULL
    
    def execute_signal(self, signal: Signal, price: float, date: pd.Timestamp) -> None:
        """
        Execute a trading signal.
        
        Args:
            signal: Signal to execute
            price: Current price
            date: Current date
        """
        if signal.direction == SignalType.FLAT:
            # Close position
            self.active_trade = None
        elif signal.direction in [SignalType.LONG, SignalType.SHORT]:
            # Open position
            self.active_trade = Trade(
                entry_price=price,
                entry_date=date,
                direction=signal.direction,
                position_pct=signal.position_pct,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                trailing_stop_pct=signal.trailing_stop_pct,
                max_holding_days=signal.max_holding_days,
                highest_price=price,
                lowest_price=price,
                regime=signal.regime
            )
    
    def get_stats(self) -> Dict:
        """Get strategy statistics."""
        win_rate = self.trades_won / max(1, self.trades_closed)
        return {
            'trades_closed': self.trades_closed,
            'trades_won': self.trades_won,
            'win_rate': win_rate,
            'total_pnl': self.total_pnl,
            'active_trade': self.active_trade is not None,
            'hmm_fitted': self.hmm_fitted,
        }


def backtest_strategy(prices: pd.Series, initial_capital: float = 10000) -> Dict:
    """
    Backtest momentum+HMM strategy on historical data.
    
    Args:
        prices: Price series
        initial_capital: Starting capital
        
    Returns:
        Backtest results dictionary
    """
    strategy = MomentumHMMStrategy(rolling_window=180, momentum_period=20)
    strategy.fit(prices)
    
    capital = initial_capital
    positions = []
    pnl_history = []
    
    for i in range(len(prices)):
        price = prices.iloc[i]
        date = prices.index[i]
        
        # Get signal
        signal = strategy.update(price, date)
        
        if signal:
            if signal.direction != SignalType.FLAT:
                # Enter position
                strategy.execute_signal(signal, price, date)
            else:
                # Exit position
                strategy.execute_signal(signal, price, date)
        
        # Track PnL
        positions.append(strategy.active_trade)
        pnl_history.append(capital * (1 + strategy.total_pnl))
    
    results = {
        'final_capital': capital * (1 + strategy.total_pnl),
        'total_return': strategy.total_pnl,
        'n_trades': strategy.trades_closed,
        'win_rate': strategy.trades_won / max(1, strategy.trades_closed),
        'pnl_history': pnl_history,
        'stats': strategy.get_stats(),
    }
    
    return results


if __name__ == "__main__":
    # Test strategy
    print("🧪 Testing Momentum+HMM Strategy (v0.3 - REAL HMM)...\n")
    
    from data.loader import load_btc_data
    
    # Load data
    btc = load_btc_data("2020-01-01", "2026-04-18")
    prices = btc.set_index('date')['close']
    
    print(f"📊 Data: {len(prices)} days")
    print(f"   Price range: ${prices.min():.0f} - ${prices.max():.0f}")
    print()
    
    # Backtest
    print("🚀 Backtesting Momentum+HMM strategy...")
    results = backtest_strategy(prices, initial_capital=10000)
    
    print()
    print("📈 Results:")
    print(f"   Total Return: {results['total_return']:.2%}")
    print(f"   N Trades: {results['n_trades']}")
    print(f"   Win Rate: {results['win_rate']:.1%}")
    print(f"   Final Capital: ${results['final_capital']:.2f}")
    print()
    
    # Show stats
    stats = results['stats']
    print("📊 Strategy Stats:")
    print(f"   HMM Fitted: {stats['hmm_fitted']}")
    print(f"   Active Trade: {stats['active_trade']}")
    print()
    
    print("✅ Test completed!")
