#!/usr/bin/env python3
"""
Momentum Breakout Multi-Asset avec Allocation Risk Parity

Module: Phase 3 - Production Readiness (Semaine 30)
Author: Saiyan Autonomous Trading System
Date: May 25, 2026

Features:
- Momentum + HMM sur 3 assets (BTC, ETH, SOL)
- Allocation Risk Parity dynamique
- Rebalancing hebdomadaire
- Backtest comparatif: Single-asset vs Multi-asset
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

try:
    from hmmlearn import hmm
    HAS_HMM = True
except ImportError:
    HAS_HMM = False


class MarketRegime(Enum):
    BULL = "bull"
    BEAR = "bear"
    RANGE = "range"
    VOLATILE_BULL = "volatile_bull"


@dataclass
class Position:
    """Represents an open position"""
    entry_date: int
    entry_price: float
    position_size: float
    stop_loss: float
    take_profit: float
    trailing_stop_pct: float
    regime: MarketRegime


@dataclass
class Trade:
    """Represents a completed trade"""
    symbol: str
    entry_date: int
    exit_date: int
    entry_price: float
    exit_price: float
    position_size: float
    pnl: float
    exit_reason: str
    regime: str


class HMMRegimeFilter:
    """HMM-based regime detection"""
    
    def __init__(self, n_regimes: int = 4, lookback_days: int = 30):
        self.n_regimes = n_regimes
        self.lookback_days = lookback_days
        self.model = None
        self.regime_mapping = None
        
        self.regime_multipliers = {
            MarketRegime.BULL: 1.0,
            MarketRegime.VOLATILE_BULL: 0.75,
            MarketRegime.RANGE: 0.4,
            MarketRegime.BEAR: 0.0
        }
        
        if HAS_HMM:
            print(f"🔮 HMM Regime Filter ({n_regimes} regimes, {lookback_days}d)")
    
    def fit(self, returns: np.ndarray) -> bool:
        if not HAS_HMM or len(returns) < self.lookback_days:
            return False
        
        returns_reshaped = returns[-self.lookback_days:].reshape(-1, 1)
        
        self.model = hmm.GaussianHMM(
            n_components=self.n_regimes,
            covariance_type="diag",
            n_iter=200,
            random_state=42,
            tol=1e-4,
            min_covar=1e-6
        )
        
        returns_clean = np.nan_to_num(returns_reshaped, nan=0.0, posinf=0.0, neginf=0.0)
        self.model.fit(returns_clean)
        
        hidden_states = self.model.predict(returns_clean)
        self._map_regimes(returns_clean, hidden_states)
        
        print(f"✅ HMM fitted ({len(returns)} days)")
        return True
    
    def _map_regimes(self, returns: np.ndarray, hidden_states: np.ndarray):
        regime_stats = {}
        
        for state in range(self.n_regimes):
            mask = hidden_states == state
            state_returns = returns[mask]
            if len(state_returns) > 0:
                mean = np.mean(state_returns)
                std = np.std(state_returns)
                regime_stats[state] = {'mean': mean, 'std': std}
        
        if not regime_stats:
            return
        
        median_vol = np.median([s['std'] for s in regime_stats.values()])
        sorted_by_sharpe = sorted(regime_stats.items(),
                                   key=lambda x: x[1]['mean']/x[1]['std'] if x[1]['std'] > 0 else 0,
                                   reverse=True)
        
        self.regime_mapping = {}
        assigned = set()
        
        if len(sorted_by_sharpe) >= 1:
            self.regime_mapping[sorted_by_sharpe[0][0]] = MarketRegime.BULL
            assigned.add(sorted_by_sharpe[0][0])
        
        for i in range(len(sorted_by_sharpe) - 1, -1, -1):
            state = sorted_by_sharpe[i][0]
            if state not in assigned and regime_stats[state]['std'] > median_vol:
                self.regime_mapping[state] = MarketRegime.BEAR
                assigned.add(state)
                break
        
        for state, stats in regime_stats.items():
            if state not in assigned and stats['std'] < median_vol and abs(stats['mean']) < median_vol:
                self.regime_mapping[state] = MarketRegime.RANGE
                assigned.add(state)
                break
        
        for state in range(self.n_regimes):
            if state not in assigned:
                if state in regime_stats and regime_stats[state]['mean'] > 0 and regime_stats[state]['std'] > median_vol:
                    self.regime_mapping[state] = MarketRegime.VOLATILE_BULL
                else:
                    self.regime_mapping[state] = MarketRegime.RANGE
    
    def get_current_regime(self, returns: np.ndarray, lookback: int = 20) -> MarketRegime:
        if self.model is None:
            return MarketRegime.RANGE
        
        recent = returns[-lookback:].reshape(-1, 1)
        recent_states = self.model.predict(recent)
        current_state = recent_states[-1]
        
        return self.regime_mapping.get(current_state, MarketRegime.RANGE)
    
    def get_position_multiplier(self, regime: MarketRegime) -> float:
        return self.regime_multipliers.get(regime, 0.0)


class MomentumMultiAsset:
    """Momentum strategy across multiple assets with Risk Parity allocation"""
    
    def __init__(self, base_kelly: float = 0.25, lookback: int = 20,
                 transaction_cost: float = 0.001, rebalance_days: int = 7):
        self.base_kelly = base_kelly
        self.lookback = lookback
        self.transaction_cost = transaction_cost
        self.rebalance_days = rebalance_days
        
        self.hmm_filter = HMMRegimeFilter(n_regimes=4, lookback_days=30)
        
        self.regime_params = {
            MarketRegime.BULL: {'stop_loss': 0.05, 'take_profit': 0.15, 'trailing': 0.05},
            MarketRegime.VOLATILE_BULL: {'stop_loss': 0.08, 'take_profit': 0.20, 'trailing': 0.08},
            MarketRegime.RANGE: {'stop_loss': 0.03, 'take_profit': 0.06, 'trailing': 0.03},
            MarketRegime.BEAR: {'stop_loss': 0.05, 'take_profit': 0.08, 'trailing': 0.06}
        }
        
        # Risk Parity weights (from Master 27)
        self.risk_parity_weights = {'BTC': 0.52, 'ETH': 0.28, 'SOL': 0.20}
        
        print(f"🚀 Momentum Multi-Asset (Kelly={base_kelly*100:.0f}%, Lookback={lookback}d)")
    
    def detect_breakout(self, prices: pd.Series, high: pd.Series, low: pd.Series) -> Dict:
        resistance = high.rolling(self.lookback).max()
        support = low.rolling(self.lookback).min()
        
        current_price = prices.iloc[-1]
        prev_price = prices.iloc[-2] if len(prices) > 1 else current_price
        
        breakout_signal = 0
        breakout_strength = 0
        
        if current_price > resistance.iloc[-1] and prev_price <= resistance.iloc[-2]:
            breakout_signal = 1
            breakout_strength = (current_price - resistance.iloc[-1]) / resistance.iloc[-1]
        elif current_price < support.iloc[-1] and prev_price >= support.iloc[-2]:
            breakout_signal = -1
            breakout_strength = abs((current_price - support.iloc[-1]) / support.iloc[-1])
        
        return {'signal': breakout_signal, 'strength': min(1.0, breakout_strength * 10)}
    
    def calculate_momentum_score(self, prices: pd.Series) -> float:
        momentum = prices.pct_change(self.lookback)
        
        if len(momentum) < 60:
            norm = (momentum - momentum.min()) / (momentum.max() - momentum.min() + 1e-10)
        else:
            rolling_max = momentum.rolling(60).max()
            rolling_min = momentum.rolling(60).min()
            norm = (momentum - rolling_min) / (rolling_max - rolling_min + 1e-10)
        
        return norm.iloc[-1] if not np.isnan(norm.iloc[-1]) else 0.5
    
    def generate_signal(self, prices: pd.Series, high: pd.Series, low: pd.Series,
                       returns: np.ndarray) -> Tuple[int, float]:
        regime = self.hmm_filter.get_current_regime(returns)
        breakout = self.detect_breakout(prices, high, low)
        mom_score = self.calculate_momentum_score(prices)
        
        # Entry conditions
        if breakout['signal'] == 1 and regime != MarketRegime.BEAR:
            mult = self.hmm_filter.get_position_multiplier(regime)
            return 1, self.base_kelly * mult
        
        if mom_score > 0.7 and regime != MarketRegime.BEAR:
            mult = self.hmm_filter.get_position_multiplier(regime)
            return 1, self.base_kelly * mult * 0.5
        
        return 0, 0.0
    
    def run_backtest(self, assets_data: Dict[str, pd.DataFrame],
                     benchmark: str = 'BTC', use_single_asset: bool = False) -> Dict:
        """
        Run backtest.
        
        Args:
            assets_data: Dict of symbol -> DataFrame
            benchmark: Asset for HMM regime detection
            use_single_asset: If True, only trade the benchmark asset
        """
        # Get benchmark returns for HMM
        benchmark_returns = assets_data[benchmark]['close'].pct_change().dropna().values
        self.hmm_filter.fit(benchmark_returns)
        
        # Align data lengths
        min_len = min(len(df) for df in assets_data.values())
        assets_data = {k: v.iloc[-min_len:].reset_index(drop=True) for k, v in assets_data.items()}
        
        n_obs = min_len
        capital = 10000.0
        capital_curve = [capital]
        trades: List[Trade] = []
        
        # Positions per asset
        positions: Dict[str, Optional[Position]] = {}
        highest_prices: Dict[str, float] = {}
        
        # Determine which assets to trade
        if use_single_asset:
            trade_assets = [benchmark]
        else:
            trade_assets = list(assets_data.keys())
        
        warmup = self.lookback + 30
        
        for i in range(warmup, n_obs - 1):
            # Get regime from benchmark
            bench_returns_slice = assets_data[benchmark]['close'].pct_change().dropna().values
            regime = self.hmm_filter.get_current_regime(bench_returns_slice[:min(i+1, len(bench_returns_slice))])
            
            # Process each asset
            for symbol in trade_assets:
                df = assets_data[symbol]
                current_price = df['close'].iloc[i]
                
                # Initialize tracking
                if symbol not in positions:
                    positions[symbol] = None
                    highest_prices[symbol] = 0.0
                
                # Check exit for existing position
                if positions[symbol]:
                    pos = positions[symbol]
                    highest_prices[symbol] = max(highest_prices[symbol], current_price)
                    
                    exit_reason, exit_price = None, None
                    
                    if current_price <= pos.stop_loss:
                        exit_reason, exit_price = "stop_loss", pos.stop_loss
                    elif current_price >= pos.take_profit:
                        exit_reason, exit_price = "take_profit", pos.take_profit
                    elif current_price <= highest_prices[symbol] * (1 - pos.trailing_stop_pct):
                        exit_reason = "trailing_stop"
                        exit_price = highest_prices[symbol] * (1 - pos.trailing_stop_pct)
                    elif i - pos.entry_date >= 20:
                        exit_reason, exit_price = "time_exit", current_price
                    
                    if exit_reason:
                        # Calculate PnL
                        price_return = (exit_price - pos.entry_price) / pos.entry_price
                        pnl = price_return * pos.position_size
                        pnl -= self.transaction_cost * pos.position_size * 2
                        
                        capital = capital * (1 + pnl)
                        
                        trades.append(Trade(
                            symbol=symbol,
                            entry_date=pos.entry_date,
                            exit_date=i,
                            entry_price=pos.entry_price,
                            exit_price=exit_price,
                            position_size=pos.position_size,
                            pnl=pnl,
                            exit_reason=exit_reason,
                            regime=pos.regime.value
                        ))
                        
                        positions[symbol] = None
                        highest_prices[symbol] = 0.0
                
                # Check entry
                if positions[symbol] is None:
                    signal, position_size = self.generate_signal(
                        df['close'].iloc[:i+1],
                        df['high'].iloc[:i+1],
                        df['low'].iloc[:i+1],
                        bench_returns_slice[:min(i+1, len(bench_returns_slice))]
                    )
                    
                    if signal == 1 and position_size > 0:
                        params = self.regime_params.get(regime, self.regime_params[MarketRegime.RANGE])
                        entry_price = current_price
                        
                        # Apply Risk Parity weight for multi-asset
                        if not use_single_asset:
                            weight = self.risk_parity_weights.get(symbol, 0.33)
                            position_size = position_size * weight
                        
                        positions[symbol] = Position(
                            entry_date=i,
                            entry_price=entry_price,
                            position_size=min(position_size, 0.25),
                            stop_loss=entry_price * (1 - params['stop_loss']),
                            take_profit=entry_price * (1 + params['take_profit']),
                            trailing_stop_pct=params['trailing'],
                            regime=regime
                        )
                        
                        highest_prices[symbol] = entry_price
            
            capital_curve.append(capital)
        
        # Calculate metrics
        capital_curve = np.array(capital_curve[1:])
        total_return = (capital_curve[-1] / 10000.0) - 1
        
        strategy_returns = np.diff(capital_curve) / capital_curve[:-1]
        sharpe = np.mean(strategy_returns) / np.std(strategy_returns) * np.sqrt(252) if len(strategy_returns) > 1 and np.std(strategy_returns) > 0 else 0
        
        cumulative = capital_curve / 10000.0
        running_max = np.maximum.accumulate(cumulative)
        max_dd = np.min((cumulative - running_max) / running_max)
        
        # Trade stats
        winning = [t for t in trades if t.pnl > 0]
        losing = [t for t in trades if t.pnl < 0]
        win_rate = len(winning) / len(trades) if trades else 0
        
        exit_reasons = {}
        for t in trades:
            exit_reasons[t.exit_reason] = exit_reasons.get(t.exit_reason, 0) + 1
        
        return {
            'total_return': total_return,
            'sharpe': sharpe,
            'max_drawdown': max_dd,
            'final_capital': capital_curve[-1],
            'n_trades': len(trades),
            'win_rate': win_rate,
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'exit_reasons': exit_reasons,
            'trades': trades,
            'capital_curve': capital_curve
        }


def load_multi_asset_data() -> Dict[str, pd.DataFrame]:
    """Load real data for BTC, ETH, SOL"""
    import os
    
    data_files = {
        'BTC': '/root/.openclaw/workspace/learning/data/btc_2020_2026_1h.csv',
        'ETH': '/root/.openclaw/workspace/learning/data/eth_2020_2026_1h.csv',
        'SOL': '/root/.openclaw/workspace/learning/data/sol_2021_2026_1h.csv'
    }
    
    data = {}
    for symbol, path in data_files.items():
        if os.path.exists(path):
            df = pd.read_csv(path, parse_dates=['timestamp'], index_col='timestamp')
            df = df.resample('D').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            data[symbol] = df
            print(f"✅ Loaded {symbol}: {len(df)} days")
        else:
            print(f"⚠️  {symbol} data not found")
    
    return data


def plot_comparison(single_results: Dict, multi_results: Dict):
    """Plot single vs multi-asset comparison"""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    
    # 1. Capital curves
    ax1 = axes[0, 0]
    single_curve = single_results['capital_curve']
    multi_curve = multi_results['capital_curve']
    min_len = min(len(single_curve), len(multi_curve))
    
    ax1.plot(single_curve[:min_len] / single_curve[0], 'orange', linewidth=1.5,
             label=f'Single BTC (Sharpe={single_results["sharpe"]:.2f})')
    ax1.plot(multi_curve[:min_len] / multi_curve[0], 'green', linewidth=1.5,
             label=f'Multi-Asset (Sharpe={multi_results["sharpe"]:.2f})')
    ax1.axhline(1.0, color='black', linestyle='-', alpha=0.3)
    ax1.set_xlabel('Time (days)')
    ax1.set_ylabel('Cumulative Return')
    ax1.set_title('Capital Curve Comparison')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Drawdown
    ax2 = axes[0, 1]
    single_dd = single_curve[:min_len] / np.maximum.accumulate(single_curve[:min_len]) - 1
    multi_dd = multi_curve[:min_len] / np.maximum.accumulate(multi_curve[:min_len]) - 1
    
    ax2.fill_between(range(len(single_dd)), single_dd, 0, color='orange', alpha=0.3,
                     label=f'Single DD: {single_results["max_drawdown"]*100:.1f}%')
    ax2.fill_between(range(len(multi_dd)), multi_dd, 0, color='green', alpha=0.3,
                     label=f'Multi DD: {multi_results["max_drawdown"]*100:.1f}%')
    ax2.set_xlabel('Time (days)')
    ax2.set_ylabel('Drawdown')
    ax2.set_title('Drawdown Comparison')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Returns distribution
    ax3 = axes[1, 0]
    single_returns = np.diff(single_curve) / single_curve[:-1]
    multi_returns = np.diff(multi_curve) / multi_curve[:-1]
    
    ax3.hist(single_returns, bins=50, alpha=0.5, color='orange', label='Single BTC', edgecolor='black')
    ax3.hist(multi_returns, bins=50, alpha=0.5, color='green', label='Multi-Asset', edgecolor='black')
    ax3.axvline(0, color='red', linestyle='--', linewidth=2)
    ax3.set_xlabel('Daily Return')
    ax3.set_ylabel('Count')
    ax3.set_title('Returns Distribution')
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. Performance table
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    table_data = [
        ['Total Return', f"{single_results['total_return']*100:.0f}%", f"{multi_results['total_return']*100:.0f}%"],
        ['Sharpe Ratio', f"{single_results['sharpe']:.2f}", f"{multi_results['sharpe']:.2f}"],
        ['Max Drawdown', f"{single_results['max_drawdown']*100:.1f}%", f"{multi_results['max_drawdown']*100:.1f}%"],
        ['Win Rate', f"{single_results['win_rate']*100:.1f}%", f"{multi_results['win_rate']*100:.1f}%"],
        ['N Trades', f"{single_results['n_trades']}", f"{multi_results['n_trades']}"]
    ]
    
    table = ax4.table(cellText=table_data, colLabels=['Metric', 'Single BTC', 'Multi-Asset'],
                      loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 1.8)
    
    for i in range(5):
        table[(i, 1)].set_facecolor('#FFE5B4')
        table[(i, 2)].set_facecolor('#C1FFC1')
    
    ax4.set_title('Performance Summary', pad=20, fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('/root/.openclaw/workspace/learning/code/momentum_multi_asset_output.png', dpi=150)
    print(f"      → Visualisation: momentum_multi_asset_output.png")


def run_comparison():
    """Run comparison"""
    
    print("=" * 70)
    print("MOMENTUM MULTI-ASSET WITH RISK PARITY - PHASE 3")
    print("=" * 70)
    
    print("\n[1/4] Loading data...")
    data = load_multi_asset_data()
    
    if len(data) < 3:
        print("⚠️  Insufficient data")
        return None, None
    
    print("\n[2/4] Running Single-Asset BTC...")
    single_strategy = MomentumMultiAsset(base_kelly=0.25, lookback=20, rebalance_days=7)
    single_results = single_strategy.run_backtest({'BTC': data['BTC']}, benchmark='BTC', use_single_asset=True)
    
    print(f"\n      Single-Asset BTC:")
    print(f"         → Return: {single_results['total_return']*100:.0f}%")
    print(f"         → Sharpe: {single_results['sharpe']:.2f}")
    print(f"         → DD: {single_results['max_drawdown']*100:.1f}%")
    print(f"         → Win Rate: {single_results['win_rate']*100:.1f}%")
    print(f"         → Trades: {single_results['n_trades']}")
    
    print("\n[3/4] Running Multi-Asset (BTC+ETH+SOL)...")
    multi_strategy = MomentumMultiAsset(base_kelly=0.25, lookback=20, rebalance_days=7)
    multi_results = multi_strategy.run_backtest(data, benchmark='BTC', use_single_asset=False)
    
    print(f"\n      Multi-Asset:")
    print(f"         → Return: {multi_results['total_return']*100:.0f}%")
    print(f"         → Sharpe: {multi_results['sharpe']:.2f}")
    print(f"         → DD: {multi_results['max_drawdown']*100:.1f}%")
    print(f"         → Win Rate: {multi_results['win_rate']*100:.1f}%")
    print(f"         → Trades: {multi_results['n_trades']}")
    
    if multi_results['exit_reasons']:
        print(f"\n      Exit Reasons:")
        for reason, count in multi_results['exit_reasons'].items():
            pct = count / multi_results['n_trades'] * 100 if multi_results['n_trades'] > 0 else 0
            print(f"         → {reason}: {count} ({pct:.0f}%)")
    
    print("\n[4/4] Comparison...")
    if single_results['max_drawdown'] != 0:
        dd_improvement = (single_results['max_drawdown'] - multi_results['max_drawdown']) / abs(single_results['max_drawdown']) * 100
        sharpe_improvement = (multi_results['sharpe'] - single_results['sharpe']) / single_results['sharpe'] * 100 if single_results['sharpe'] != 0 else 0
        
        print(f"\n      📊 Diversification Benefits:")
        print(f"         → DD: {single_results['max_drawdown']*100:.1f}% → {multi_results['max_drawdown']*100:.1f}% ({dd_improvement:+.1f}%)")
        print(f"         → Sharpe: {single_results['sharpe']:.2f} → {multi_results['sharpe']:.2f} ({sharpe_improvement:+.1f}%)")
    
    print("\n" + "=" * 70)
    print("Generating plots...")
    print("=" * 70)
    plot_comparison(single_results, multi_results)
    
    print("\n" + "=" * 70)
    print("✅ COMPLETE")
    print("=" * 70)
    
    return single_results, multi_results


if __name__ == "__main__":
    single_results, multi_results = run_comparison()
