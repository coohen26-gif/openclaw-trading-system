#!/usr/bin/env python3
"""
Backtest Engine - Walk-Forward Validation with Real Data

Module: Phase 3 - Production Readiness
Author: Saiyan Autonomous Trading System
Date: May 25, 2026

Features:
- Walk-forward backtesting (expanding & rolling window)
- Multiple strategies support
- Real historical data (2020-2026)
- Transaction costs modeling
- Risk metrics (Sharpe, Sortino, Max DD, VaR, CVaR)
- Regime-aware backtesting
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Signal(Enum):
    STRONG_BUY = 2
    BUY = 1
    HOLD = 0
    SELL = -1
    STRONG_SELL = -2


@dataclass
class Trade:
    """Trade record"""
    entry_date: datetime
    exit_date: Optional[datetime]
    symbol: str
    side: str
    entry_price: float
    exit_price: Optional[float]
    amount: float
    pnl: float
    pnl_pct: float
    duration_days: int
    exit_reason: str


@dataclass
class BacktestMetrics:
    """Backtest performance metrics"""
    total_return: float
    annualized_return: float
    total_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_duration_days: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    var_95: float
    cvar_95: float
    calmar_ratio: float


class BacktestEngine:
    """
    Walk-forward backtesting engine with support for multiple strategies.
    
    Features:
    - Expanding window (train on all history)
    - Rolling window (train on last N days)
    - Transaction costs
    - Position sizing
    - Risk management
    """
    
    def __init__(
        self,
        initial_capital: float = 10000.0,
        transaction_cost_bps: float = 10.0,
        slippage_bps: float = 5.0,
        max_position_pct: float = 1.0,
        risk_free_rate: float = 0.02
    ):
        """
        Initialize backtest engine.
        
        Args:
            initial_capital: Starting capital in USDT
            transaction_cost_bps: Transaction cost in basis points (10 bps = 0.1%)
            slippage_bps: Slippage in basis points
            max_position_pct: Maximum position size as % of portfolio
            risk_free_rate: Annual risk-free rate for Sharpe calculation
        """
        self.initial_capital = initial_capital
        self.transaction_cost_bps = transaction_cost_bps
        self.slippage_bps = slippage_bps
        self.max_position_pct = max_position_pct
        self.risk_free_rate = risk_free_rate
        
        # State
        self.capital = initial_capital
        self.position = 0.0
        self.entry_price = 0.0
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = [initial_capital]
        self.daily_returns: List[float] = []
    
    def reset(self):
        """Reset engine state"""
        self.capital = self.initial_capital
        self.position = 0.0
        self.entry_price = 0.0
        self.trades = []
        self.equity_curve = [self.initial_capital]
        self.daily_returns = []
    
    def _calculate_transaction_cost(self, amount: float, price: float) -> float:
        """Calculate transaction cost + slippage"""
        notional = amount * price
        cost = notional * (self.transaction_cost_bps + self.slippage_bps) / 10000
        return cost
    
    def _execute_signal(
        self,
        signal: Signal,
        price: float,
        date: datetime,
        volatility: float = None,
        regime: str = None
    ) -> Optional[Trade]:
        """Execute trading signal"""
        trade = None
        
        if signal == Signal.STRONG_BUY or signal == Signal.BUY:
            # Buy signal
            if self.position == 0:
                # Open position
                size_pct = 1.0 if signal == Signal.STRONG_BUY else 0.5
                position_size = (self.capital * size_pct * self.max_position_pct) / price
                
                cost = self._calculate_transaction_cost(position_size, price)
                if cost < self.capital * 0.5:  # Can afford
                    self.position = position_size
                    self.entry_price = price
                    self.capital -= cost
                    
                    logger.debug(f"BUY {position_size:.6f} @ {price:.2f} (cost: ${cost:.2f})")
        
        elif signal == Signal.STRONG_SELL or signal == Signal.SELL:
            # Sell signal
            if self.position > 0:
                # Close position
                exit_price = price
                cost = self._calculate_transaction_cost(self.position, exit_price)
                
                pnl = (exit_price - self.entry_price) * self.position - cost
                pnl_pct = (exit_price - self.entry_price) / self.entry_price
                
                trade = Trade(
                    entry_date=self.trades[-1].entry_date if self.trades else date,
                    exit_date=date,
                    symbol='BTC',
                    side='long',
                    entry_price=self.entry_price,
                    exit_price=exit_price,
                    amount=self.position,
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    duration_days=0,
                    exit_reason='signal'
                )
                
                self.capital += (self.position * exit_price) - cost
                self.position = 0.0
                self.entry_price = 0.0
                self.trades.append(trade)
                
                logger.debug(f"SELL {trade.amount:.6f} @ {exit_price:.2f} (PnL: ${pnl:.2f}, {pnl_pct:.2%})")
        
        return trade
    
    def run_backtest(
        self,
        data: pd.DataFrame,
        signal_generator,
        train_window_days: int = None,
        test_window_days: int = 252,
        step_days: int = 63
    ) -> BacktestMetrics:
        """
        Run walk-forward backtest.
        
        Args:
            data: DataFrame with OHLCV data
            signal_generator: Function that returns Signal given data and current index
            train_window_days: Training window (None for expanding)
            test_window_days: Test window length
            step_days: Step size for walk-forward
        
        Returns:
            BacktestMetrics object
        """
        self.reset()
        
        logger.info(f"Starting backtest: {len(data)} bars from {data.index[0]} to {data.index[-1]}")
        
        # Walk-forward loop
        if train_window_days is None:
            # Expanding window
            train_end = data.index[0] + timedelta(days=365)  # Start with 1 year
        else:
            train_end = data.index[0] + timedelta(days=train_window_days)
        
        test_start = train_end
        test_end = test_start + timedelta(days=test_window_days)
        
        fold = 0
        while test_end <= data.index[-1]:
            fold += 1
            train_data = data[data.index < train_end]
            test_data = data[(data.index >= test_start) & (data.index < test_end)]
            
            logger.info(f"Fold {fold}: Train {train_data.index[0]} to {train_data.index[-1]}, "
                       f"Test {test_data.index[0]} to {test_data.index[-1]}")
            
            # Run signal generator on test period
            for idx, (date, row) in enumerate(test_data.iterrows()):
                signal = signal_generator(train_data, test_data, idx, row)
                self._execute_signal(signal, row['close'], date)
                
                # Update equity curve
                if self.position > 0:
                    equity = self.capital + (self.position * row['close'])
                else:
                    equity = self.capital
                self.equity_curve.append(equity)
                
                # Daily return
                if len(self.equity_curve) > 1:
                    daily_ret = (self.equity_curve[-1] - self.equity_curve[-2]) / self.equity_curve[-2]
                    self.daily_returns.append(daily_ret)
            
            # Move window
            train_end += timedelta(days=step_days)
            test_start += timedelta(days=step_days)
            test_end += timedelta(days=step_days)
        
        # Calculate metrics
        return self._calculate_metrics(data)
    
    def _calculate_metrics(self, data: pd.DataFrame) -> BacktestMetrics:
        """Calculate performance metrics"""
        equity = np.array(self.equity_curve)
        returns = np.array(self.daily_returns)
        
        # Basic metrics
        total_return = (equity[-1] - equity[0]) / equity[0]
        days = len(equity)
        annualized_return = (1 + total_return) ** (365 / days) - 1
        
        # Volatility
        daily_vol = np.std(returns)
        annual_vol = daily_vol * np.sqrt(365)
        
        # Sharpe ratio
        excess_return = annualized_return - self.risk_free_rate
        sharpe = excess_return / annual_vol if annual_vol > 0 else 0
        
        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_dev = np.std(downside_returns) * np.sqrt(365) if len(downside_returns) > 0 else 0
        sortino = excess_return / downside_dev if downside_dev > 0 else 0
        
        # Drawdown
        peak = np.maximum.accumulate(equity)
        drawdown = (equity - peak) / peak
        max_dd = np.min(drawdown)
        
        # Drawdown duration
        in_drawdown = drawdown < 0
        dd_starts = np.diff(in_drawdown.astype(int)) == 1
        dd_ends = np.diff(in_drawdown.astype(int)) == -1
        dd_durations = []
        for start in np.where(dd_starts)[0]:
            end = np.where(dd_ends[start:])[0]
            if len(end) > 0:
                dd_durations.append(end[0])
        max_dd_duration = max(dd_durations) if dd_durations else 0
        
        # Trade statistics
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl <= 0]
        
        win_rate = len(winning_trades) / len(self.trades) if self.trades else 0
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # VaR/CVaR
        var_95 = np.percentile(returns, 5) if len(returns) > 0 else 0
        cvar_95 = np.mean(returns[returns <= var_95]) if len(returns) > 0 else 0
        
        # Calmar ratio
        calmar = annualized_return / abs(max_dd) if max_dd != 0 else 0
        
        return BacktestMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            total_volatility=annual_vol,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_dd,
            max_drawdown_duration_days=max_dd_duration,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            total_trades=len(self.trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            var_95=var_95,
            cvar_95=cvar_95,
            calmar_ratio=calmar
        )


# ==================== Example Strategy: Fat Tail Hunter ====================

def fat_tail_hunter_signal(train_data, test_data, idx, row):
    """
    Fat Tail Hunter Strategy: Mean reversion after >3σ moves
    
    Logic:
    - Calculate 30-day rolling mean and std
    - If price drops >3σ below mean → BUY
    - If price rises >3σ above mean → SELL
    """
    lookback = 30
    
    if idx < lookback:
        return Signal.HOLD
    
    # Get recent prices
    recent_prices = test_data['close'].iloc[max(0, idx-lookback):idx+1]
    
    mean = recent_prices.mean()
    std = recent_prices.std()
    
    if std == 0:
        return Signal.HOLD
    
    z_score = (row['close'] - mean) / std
    
    if z_score < -3.0:
        return Signal.STRONG_BUY
    elif z_score < -2.0:
        return Signal.BUY
    elif z_score > 3.0:
        return Signal.STRONG_SELL
    elif z_score > 2.0:
        return Signal.SELL
    else:
        return Signal.HOLD


# ==================== Example Strategy: Momentum Breakout ====================

def momentum_breakout_signal(train_data, test_data, idx, row):
    """
    Momentum Breakout Strategy
    
    Logic:
    - Calculate 20-day high and low
    - Breakout above high → BUY
    - Breakdown below low → SELL
    """
    lookback = 20
    
    if idx < lookback:
        return Signal.HOLD
    
    recent_high = test_data['high'].iloc[max(0, idx-lookback):idx].max()
    recent_low = test_data['low'].iloc[max(0, idx-lookback):idx].min()
    
    if row['close'] > recent_high * 1.02:  # 2% buffer
        return Signal.STRONG_BUY
    elif row['close'] > recent_high:
        return Signal.BUY
    elif row['close'] < recent_low * 0.98:
        return Signal.STRONG_SELL
    elif row['close'] < recent_low:
        return Signal.SELL
    else:
        return Signal.HOLD


# ==================== Main ====================

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, '..')
    
    # Load historical data
    print("Loading BTC historical data (2020-2026)...")
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'btc_2020_2026_1h.csv')
    btc_data = pd.read_csv(data_path, index_col=0, parse_dates=True)
    print(f"Loaded {len(btc_data)} candles")
    
    # Initialize engine
    engine = BacktestEngine(
        initial_capital=10000.0,
        transaction_cost_bps=10,
        slippage_bps=5,
        max_position_pct=1.0
    )
    
    # Run Fat Tail Hunter backtest
    print("\n=== Fat Tail Hunter Backtest ===")
    metrics_fth = engine.run_backtest(btc_data, fat_tail_hunter_signal, 
                                       train_window_days=365, 
                                       test_window_days=90,
                                       step_days=30)
    
    print(f"\nTotal Return: {metrics_fth.total_return:.2%}")
    print(f"Annualized Return: {metrics_fth.annualized_return:.2%}")
    print(f"Sharpe Ratio: {metrics_fth.sharpe_ratio:.2f}")
    print(f"Sortino Ratio: {metrics_fth.sortino_ratio:.2f}")
    print(f"Max Drawdown: {metrics_fth.max_drawdown:.2%}")
    print(f"Win Rate: {metrics_fth.win_rate:.2%}")
    print(f"Total Trades: {metrics_fth.total_trades}")
    print(f"Profit Factor: {metrics_fth.profit_factor:.2f}")
    print(f"VaR 95%: {metrics_fth.var_95:.2%}")
    print(f"CVaR 95%: {metrics_fth.cvar_95:.2%}")
    print(f"Calmar Ratio: {metrics_fth.calmar_ratio:.2f}")
    
    # Run Momentum Breakout backtest
    print("\n=== Momentum Breakout Backtest ===")
    engine.reset()
    metrics_mom = engine.run_backtest(btc_data, momentum_breakout_signal,
                                       train_window_days=365,
                                       test_window_days=90,
                                       step_days=30)
    
    print(f"\nTotal Return: {metrics_mom.total_return:.2%}")
    print(f"Annualized Return: {metrics_mom.annualized_return:.2%}")
    print(f"Sharpe Ratio: {metrics_mom.sharpe_ratio:.2f}")
    print(f"Max Drawdown: {metrics_mom.max_drawdown:.2%}")
    print(f"Win Rate: {metrics_mom.win_rate:.2%}")
    print(f"Total Trades: {metrics_mom.total_trades}")
    
    print("\n=== Backtest Complete ===")
