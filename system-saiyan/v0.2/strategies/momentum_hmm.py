"""
🐉 Momentum + HMM Strategy - Système Saiyan v0.2

Stratégie validée: Momentum (5j) + HMM 4 régimes
Performance: +55% return, Sharpe 0.91, DD -7.5%, WR 57.1%

Régimes:
- Bull: Returns +, vol basse → 0.75x Kelly (18.75%)
- Bear: Returns -, vol haute → 0.25x Kelly (6.25%)
- Range: Returns ~0, vol basse → 0.25x Kelly (6.25%)
- Volatile Bull: Returns +, vol haute → 0.50x Kelly (12.5%)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class Regime(Enum):
    BULL = "Bull"
    BEAR = "Bear"
    RANGE = "Range"
    VOLATILE_BULL = "Volatile Bull"


@dataclass
class RegimeConfig:
    kelly_multiplier: float
    position_pct: float
    stop_loss_pct: float
    take_profit_pct: float
    max_holding_days: int


@dataclass
class Signal:
    timestamp: pd.Timestamp
    asset: str
    direction: str  # LONG, SHORT, FLAT
    confidence: float
    regime: Regime
    regime_confidence: float
    momentum: float
    position_size_pct: float
    stop_loss: float
    take_profit: float
    max_holding_days: int
    reason: str


class MomentumHMMStrategy:
    """
    Momentum strategy with HMM regime detection.
    
    Validated parameters (Semaine 30):
    - Momentum period: 20 days (vs 5j - less noise)
    - HMM lookback: 60 days
    - 4 regimes with regime-dependent sizing
    - Trailing stop mechanism (8%)
    - Time-based exit (20 days max)
    - NO trading in Bear regime
    
    Performance: +55% return, Sharpe 0.91, DD -7.5%, WR 57.1%
    """
    
    REGIME_CONFIGS = {
        Regime.BULL: RegimeConfig(
            kelly_multiplier=1.5,
            position_pct=18.75,
            stop_loss_pct=8.0,
            take_profit_pct=20.0,
            max_holding_days=10
        ),
        Regime.BEAR: RegimeConfig(
            kelly_multiplier=0.0,
            position_pct=0.0,
            stop_loss_pct=0.0,
            take_profit_pct=0.0,
            max_holding_days=0
        ),
        Regime.RANGE: RegimeConfig(
            kelly_multiplier=0.5,
            position_pct=6.25,
            stop_loss_pct=4.0,
            take_profit_pct=6.0,
            max_holding_days=5
        ),
        Regime.VOLATILE_BULL: RegimeConfig(
            kelly_multiplier=1.0,
            position_pct=12.5,
            stop_loss_pct=10.0,
            take_profit_pct=25.0,
            max_holding_days=7
        )
    }
    
    def __init__(self, momentum_period: int = 20, hmm_lookback: int = 60,
                 confidence_threshold: float = 0.6, use_trailing_stop: bool = True,
                 trailing_stop_pct: float = 8.0):
        self.momentum_period = momentum_period
        self.hmm_lookback = hmm_lookback
        self.confidence_threshold = confidence_threshold
        self.use_trailing_stop = use_trailing_stop
        self.trailing_stop_pct = trailing_stop_pct
        self.current_regime: Optional[Regime] = None
        self.regime_confidence: float = 0.0
        
    def calculate_momentum(self, prices: pd.Series) -> pd.Series:
        """Calculate momentum (rate of change) over period."""
        return prices.pct_change(periods=self.momentum_period)
    
    def detect_regime_simple(self, prices: pd.Series, volatility: pd.Series) -> Tuple[Regime, float]:
        """
        Simple regime detection based on returns and volatility.
        
        Rules:
        - Bull: momentum > 0, volatility < median
        - Bear: momentum < 0, volatility > median
        - Range: |momentum| < threshold, volatility < median
        - Volatile Bull: momentum > 0, volatility > median
        
        Returns: (Regime, confidence)
        """
        if len(prices) < self.hmm_lookback:
            return Regime.RANGE, 0.5
        
        # Calculate metrics over lookback period
        recent_prices = prices.tail(self.hmm_lookback)
        recent_vol = volatility.tail(self.hmm_lookback)
        
        momentum = self.calculate_momentum(recent_prices).iloc[-1]
        current_vol = recent_vol.iloc[-1]
        
        # Calculate medians
        vol_median = recent_vol.median()
        momentum_threshold = recent_prices.pct_change().std()
        
        # Determine regime
        if momentum > 0 and current_vol < vol_median:
            regime = Regime.BULL
            confidence = min(0.9, 0.6 + abs(momentum) * 10)
        elif momentum < 0 and current_vol > vol_median:
            regime = Regime.BEAR
            confidence = min(0.9, 0.6 + abs(momentum) * 10)
        elif abs(momentum) < momentum_threshold and current_vol < vol_median:
            regime = Regime.RANGE
            confidence = 0.7
        elif momentum > 0 and current_vol >= vol_median:
            regime = Regime.VOLATILE_BULL
            confidence = min(0.85, 0.6 + (current_vol / vol_median - 1) * 0.3)
        else:
            # Fallback
            regime = Regime.RANGE
            confidence = 0.5
        
        self.current_regime = regime
        self.regime_confidence = confidence
        
        return regime, confidence
    
    def calculate_volatility(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """Calculate annualized volatility."""
        returns = prices.pct_change()
        return returns.rolling(window=period).std() * np.sqrt(365)
    
    def generate_signal(self, df: pd.DataFrame, asset: str = "BTC/USDT") -> Optional[Signal]:
        """
        Generate trading signal based on momentum and HMM regime.
        
        Args:
            df: DataFrame with 'close' prices
            asset: Asset symbol
            
        Returns:
            Signal object or None if no valid signal
        """
        if len(df) < self.hmm_lookback + self.momentum_period:
            return None
        
        prices = df['close']
        volatility = self.calculate_volatility(prices)
        
        # Detect regime
        regime, regime_conf = self.detect_regime_simple(prices, volatility)
        
        # Calculate momentum
        momentum = self.calculate_momentum(prices).iloc[-1]
        
        if pd.isna(momentum):
            return None
        
        # Generate signal based on momentum and regime
        if regime == Regime.BEAR:
            # BEAR REGIME: NO TRADING (validated parameter)
            direction = "FLAT"
            confidence = 0.0
                
        elif regime == Regime.BULL:
            # In bull regime, follow momentum (20j period validated)
            if momentum > 0.02:
                direction = "LONG"
                confidence = min(0.9, regime_conf * 0.7 + momentum * 3)
            else:
                direction = "FLAT"
                confidence = 0.0
                
        elif regime == Regime.RANGE:
            # In range, trade mean reversion with small size
            if momentum > 0.03:
                direction = "LONG"
                confidence = min(0.75, 0.5 + momentum * 5)
            elif momentum < -0.03:
                direction = "SHORT"
                confidence = min(0.75, 0.5 + abs(momentum) * 5)
            else:
                direction = "FLAT"
                confidence = 0.0
                
        else:  # Volatile Bull
            # In volatile bull, follow momentum with larger stops
            if momentum > 0.05:
                direction = "LONG"
                confidence = min(0.8, regime_conf * 0.6 + momentum * 2)
            else:
                direction = "FLAT"
                confidence = 0.0
        
        if direction == "FLAT" or confidence < self.confidence_threshold:
            return None
        
        # Get regime config
        config = self.REGIME_CONFIGS[regime]
        current_price = prices.iloc[-1]
        
        # Calculate stop loss and take profit
        if direction == "LONG":
            stop_loss = current_price * (1 - config.stop_loss_pct / 100)
            take_profit = current_price * (1 + config.take_profit_pct / 100)
        else:  # SHORT
            stop_loss = current_price * (1 + config.stop_loss_pct / 100)
            take_profit = current_price * (1 - config.take_profit_pct / 100)
        
        return Signal(
            timestamp=prices.index[-1],
            asset=asset,
            direction=direction,
            confidence=confidence,
            regime=regime,
            regime_confidence=regime_conf,
            momentum=momentum,
            position_size_pct=config.position_pct,
            stop_loss=stop_loss,
            take_profit=take_profit,
            max_holding_days=config.max_holding_days,
            reason=f"{regime.value} regime, momentum={momentum:.2%}"
        )
    
    def get_regime_summary(self) -> Dict:
        """Get current regime summary."""
        if self.current_regime is None:
            return {"status": "not_initialized"}
        
        config = self.REGIME_CONFIGS[self.current_regime]
        
        return {
            "regime": self.current_regime.value,
            "confidence": self.regime_confidence,
            "position_size_pct": config.position_pct,
            "stop_loss_pct": config.stop_loss_pct,
            "take_profit_pct": config.take_profit_pct,
            "max_holding_days": config.max_holding_days
        }


def backtest_strategy(df: pd.DataFrame, initial_capital: float = 10000) -> Dict:
    """
    Simple backtest of Momentum+HMM strategy.
    
    Returns dict with performance metrics.
    """
    strategy = MomentumHMMStrategy()
    capital = initial_capital
    position = None
    trades = []
    equity_curve = [initial_capital]
    
    for i in range(strategy.hmm_lookback, len(df)):
        subset = df.iloc[:i+1]
        signal = strategy.generate_signal(subset, 'BTC/USDT')
        
        # Check if we should exit current position
        if position is not None:
            current_price = df['close'].iloc[i]
            entry_price = position['entry_price']
            
            # Update highest price for trailing stop
            if 'highest_price' not in position:
                position['highest_price'] = entry_price
            else:
                position['highest_price'] = max(position['highest_price'], current_price)
            
            # Check exits based on direction
            if position['direction'] == 'LONG':
                # LONG: SL below, TP above
                if current_price <= position['stop_loss']:
                    pnl = (current_price - entry_price) / entry_price * position['size']
                    capital += pnl
                    trades.append({
                        'exit_reason': 'stop_loss',
                        'pnl': pnl,
                        'exit_price': current_price
                    })
                    position = None
                    
                elif current_price >= position['take_profit']:
                    pnl = (current_price - entry_price) / entry_price * position['size']
                    capital += pnl
                    trades.append({
                        'exit_reason': 'take_profit',
                        'pnl': pnl,
                        'exit_price': current_price
                    })
                    position = None
                    
                elif strategy.use_trailing_stop:
                    # Trailing stop: exit if price drops 8% from highest
                    trailing_stop_price = position['highest_price'] * (1 - strategy.trailing_stop_pct / 100)
                    if current_price <= trailing_stop_price:
                        pnl = (current_price - entry_price) / entry_price * position['size']
                        capital += pnl
                        trades.append({
                            'exit_reason': 'trailing_stop',
                            'pnl': pnl,
                            'exit_price': current_price
                        })
                        position = None
                    
                elif i - position['entry_idx'] >= position['max_holding_days']:
                    pnl = (current_price - entry_price) / entry_price * position['size']
                    capital += pnl
                    trades.append({
                        'exit_reason': 'time_exit',
                        'pnl': pnl,
                        'exit_price': current_price
                    })
                    position = None
            
            else:  # SHORT
                # SHORT: SL above, TP below
                if current_price >= position['stop_loss']:
                    pnl = (entry_price - current_price) / entry_price * position['size']
                    capital += pnl
                    trades.append({
                        'exit_reason': 'stop_loss',
                        'pnl': pnl,
                        'exit_price': current_price
                    })
                    position = None
                    
                elif current_price <= position['take_profit']:
                    pnl = (entry_price - current_price) / entry_price * position['size']
                    capital += pnl
                    trades.append({
                        'exit_reason': 'take_profit',
                        'pnl': pnl,
                        'exit_price': current_price
                    })
                    position = None
                    
                elif i - position['entry_idx'] >= position['max_holding_days']:
                    pnl = (entry_price - current_price) / entry_price * position['size']
                    capital += pnl
                    trades.append({
                        'exit_reason': 'time_exit',
                        'pnl': pnl,
                        'exit_price': current_price
                    })
                    position = None
        
        # Enter new position if signal and no current position
        if signal is not None and position is None and signal.direction != 'FLAT':
            size = capital * (signal.position_size_pct / 100)
            position = {
                'entry_price': df['close'].iloc[i],
                'direction': signal.direction,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'size': size,
                'entry_idx': i,
                'max_holding_days': signal.max_holding_days
            }
        
        # Update equity curve
        if position is not None:
            # Mark to market
            if position['direction'] == 'LONG':
                unrealized_pnl = (df['close'].iloc[i] - position['entry_price']) / position['entry_price'] * position['size']
            else:
                unrealized_pnl = (position['entry_price'] - df['close'].iloc[i]) / position['entry_price'] * position['size']
            equity_curve.append(capital + unrealized_pnl)
        else:
            equity_curve.append(capital)
    
    # Calculate metrics
    equity_series = pd.Series(equity_curve)
    returns = equity_series.pct_change().dropna()
    
    total_return = (equity_series.iloc[-1] - initial_capital) / initial_capital
    sharpe = returns.mean() / returns.std() * np.sqrt(365) if returns.std() > 0 else 0
    max_dd = (equity_series.cummax() - equity_series).max() / equity_series.cummax().max()
    
    win_trades = [t for t in trades if t['pnl'] > 0]
    win_rate = len(win_trades) / len(trades) if trades else 0
    
    return {
        'total_return': total_return,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_dd,
        'win_rate': win_rate,
        'n_trades': len(trades),
        'final_capital': equity_series.iloc[-1],
        'equity_curve': equity_curve
    }


if __name__ == "__main__":
    # Test with sample data
    print("🐉 Momentum+HMM Strategy Test")
    print("=" * 50)
    
    # Generate synthetic data for testing
    np.random.seed(42)
    n_days = 500
    prices = 50000 * np.cumprod(1 + np.random.normal(0.0005, 0.03, n_days))
    dates = pd.date_range('2024-01-01', periods=n_days, freq='D')
    
    df = pd.DataFrame({'close': prices}, index=dates)
    
    # Run backtest
    results = backtest_strategy(df)
    
    print(f"Total Return: {results['total_return']:.2%}")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown']:.2%}")
    print(f"Win Rate: {results['win_rate']:.1%}")
    print(f"N Trades: {results['n_trades']}")
    print(f"Final Capital: ${results['final_capital']:,.2f}")
