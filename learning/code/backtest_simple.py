#!/usr/bin/env python3
"""
Simple Backtest Engine - Robust Version

Module: Phase 3 - Production Readiness
Author: Saiyan Autonomous Trading System
Date: May 25, 2026
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Trade:
    entry_date: datetime
    exit_date: datetime
    entry_price: float
    exit_price: float
    pnl_pct: float
    pnl_usd: float


class SimpleBacktest:
    """Simple walk-forward backtest with proper PnL tracking"""
    
    def __init__(self, initial_capital: float = 10000.0, transaction_cost_bps: float = 10.0):
        self.initial_capital = initial_capital
        self.transaction_cost_bps = transaction_cost_bps
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
    
    def run(self, data: pd.DataFrame, signal_func, lookback: int = 30) -> dict:
        """Run backtest with given signal function"""
        capital = self.initial_capital
        position = 0.0
        entry_price = 0.0
        entry_date = None
        self.trades = []
        self.equity_curve = [capital]
        
        logger.info(f"Starting backtest: {len(data)} bars")
        
        for i in range(lookback, len(data)):
            row = data.iloc[i]
            prev_data = data.iloc[i-lookback:i]
            
            # Generate signal
            signal = signal_func(prev_data, row)
            
            # Execute signals
            if signal == 'BUY' and position == 0:
                # Open position
                position = capital / row['close']
                entry_price = row['close']
                entry_date = row.name
                cost = capital * self.transaction_cost_bps / 10000
                capital -= cost
                
            elif signal == 'SELL' and position > 0:
                # Close position
                exit_price = row['close']
                gross_pnl = (exit_price - entry_price) * position
                cost = position * exit_price * self.transaction_cost_bps / 10000
                net_pnl = gross_pnl - cost
                capital += net_pnl
                
                pnl_pct = (exit_price - entry_price) / entry_price
                
                self.trades.append(Trade(
                    entry_date=entry_date,
                    exit_date=row.name,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    pnl_pct=pnl_pct,
                    pnl_usd=net_pnl
                ))
                
                position = 0.0
                entry_price = 0.0
            
            # Update equity curve
            if position > 0:
                equity = capital + (position * row['close'])
            else:
                equity = capital
            self.equity_curve.append(equity)
        
        # Calculate metrics
        return self._calculate_metrics()
    
    def _calculate_metrics(self) -> dict:
        equity = np.array(self.equity_curve)
        returns = np.diff(equity) / equity[:-1]
        
        total_return = (equity[-1] - equity[0]) / equity[0]
        days = len(equity) / 24  # Hourly data
        annualized_return = (1 + total_return) ** (365 / max(days, 1)) - 1
        
        daily_vol = np.std(returns)
        annual_vol = daily_vol * np.sqrt(365)
        
        sharpe = annualized_return / annual_vol if annual_vol > 0 else 0
        
        # Drawdown
        peak = np.maximum.accumulate(equity)
        drawdown = (equity - peak) / peak
        max_dd = np.min(drawdown)
        
        # Trade stats
        winning = [t for t in self.trades if t.pnl_pct > 0]
        losing = [t for t in self.trades if t.pnl_pct <= 0]
        
        win_rate = len(winning) / len(self.trades) if self.trades else 0
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
            'total_trades': len(self.trades),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'final_capital': equity[-1]
        }


# ==================== Strategies ====================

def fat_tail_signal(prev_data, row):
    """Mean reversion after >2.5σ moves"""
    mean = prev_data['close'].mean()
    std = prev_data['close'].std()
    if std == 0:
        return 'HOLD'
    
    z = (row['close'] - mean) / std
    if z < -2.5:
        return 'BUY'
    elif z > 2.5:
        return 'SELL'
    return 'HOLD'


def momentum_signal(prev_data, row):
    """Breakout above/below 20-day high/low"""
    high_20 = prev_data['high'].max()
    low_20 = prev_data['low'].min()
    
    if row['close'] > high_20 * 1.01:
        return 'BUY'
    elif row['close'] < low_20 * 0.99:
        return 'SELL'
    return 'HOLD'


# ==================== Main ====================

if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, '..')
    
    # Load data
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'btc_2020_2026_1h.csv')
    print("Loading BTC data...")
    data = pd.read_csv(data_path, index_col=0, parse_dates=True)
    print(f"Loaded {len(data)} candles from {data.index[0]} to {data.index[-1]}")
    
    # Run Fat Tail Hunter
    print("\n=== Fat Tail Hunter (Mean Reversion) ===")
    bt1 = SimpleBacktest(initial_capital=10000, transaction_cost_bps=10)
    metrics1 = bt1.run(data, fat_tail_signal, lookback=30)
    
    print(f"Final Capital: ${metrics1['final_capital']:,.2f}")
    print(f"Total Return: {metrics1['total_return']:.2%}")
    print(f"Annualized Return: {metrics1['annualized_return']:.2%}")
    print(f"Sharpe Ratio: {metrics1['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {metrics1['max_drawdown']:.2%}")
    print(f"Win Rate: {metrics1['win_rate']:.2%}")
    print(f"Total Trades: {metrics1['total_trades']}")
    
    # Run Momentum
    print("\n=== Momentum Breakout ===")
    bt2 = SimpleBacktest(initial_capital=10000, transaction_cost_bps=10)
    metrics2 = bt2.run(data, momentum_signal, lookback=20)
    
    print(f"Final Capital: ${metrics2['final_capital']:,.2f}")
    print(f"Total Return: {metrics2['total_return']:.2%}")
    print(f"Annualized Return: {metrics2['annualized_return']:.2%}")
    print(f"Sharpe Ratio: {metrics2['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {metrics2['max_drawdown']:.2%}")
    print(f"Win Rate: {metrics2['win_rate']:.2%}")
    print(f"Total Trades: {metrics2['total_trades']}")
    
    print("\n=== Backtest Complete ===")
