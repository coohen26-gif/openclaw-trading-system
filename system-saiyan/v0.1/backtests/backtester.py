"""
Système Saiyan v0.1 - Backtester
Backtest avec transaction costs, walk-forward validation, metrics
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration du backtest"""
    initial_capital: float = 10000.0
    trading_fee_pct: float = 0.1  # 0.1% per trade (Binance)
    slippage_pct: float = 0.05    # 0.05% slippage
    position_size_pct: float = 3.0  # 3% par trade
    stop_loss_pct: float = 2.5    # 2.5% SL
    take_profit_pct: float = 1.0  # 1.0% TP
    min_confidence: int = 60      # Confidence minimum


@dataclass
class Trade:
    """Trade exécuté"""
    entry_date: datetime
    exit_date: datetime
    symbol: str
    direction: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    fees: float
    slippage: float
    exit_reason: str
    confidence: float


class Backtester:
    """
    Moteur de backtest avec costs réels
    """
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.capital = config.initial_capital
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
    
    def run_backtest(self,
                     df: pd.DataFrame,
                     signals: List[Dict]) -> Dict:
        """
        Exécute le backtest
        
        Args:
            df: DataFrame OHLCV avec features
            signals: Liste des signaux
        
        Returns:
            Dict avec résultats et metrics
        """
        self.capital = self.config.initial_capital
        self.trades = []
        self.equity_curve = [self.capital]
        
        # Index pour accès rapide aux données OHLCV (déjà indexé par timestamp)
        df_indexed = df
        
        for signal in signals:
            signal_time = signal['timestamp']
            
            # Vérifier confidence minimum
            if signal['confidence'] < self.config.min_confidence:
                continue
            
            # Trouver les données OHLCV pour ce timestamp (pandas 2.x compatible)
            try:
                idx_list = df_indexed.index.tolist()
                idx = min(range(len(idx_list)), key=lambda i: abs(idx_list[i] - signal_time))
                candle = df_indexed.iloc[idx]
            except Exception as e:
                logger.debug(f"Error finding candle for {signal_time}: {e}")
                continue
            
            # Calcul position size
            position_value = self.capital * (self.config.position_size_pct / 100)
            
            # Calcul quantité avec slippage
            if signal['direction'] == 'LONG':
                entry_price = signal['entry_price'] * (1 + self.config.slippage_pct / 100)
            else:
                entry_price = signal['entry_price'] * (1 - self.config.slippage_pct / 100)
            
            quantity = position_value / entry_price
            
            # Calcul stop-loss et take-profit
            if signal['direction'] == 'LONG':
                sl_price = entry_price * (1 - self.config.stop_loss_pct / 100)
                tp_price = entry_price * (1 + self.config.take_profit_pct / 100)
            else:
                sl_price = entry_price * (1 + self.config.stop_loss_pct / 100)
                tp_price = entry_price * (1 - self.config.take_profit_pct / 100)
            
            # Simuler la sortie (trouver SL ou TP touché en premier)
            exit_price, exit_date, exit_reason = self._find_exit_price(
                df_indexed, 
                signal_time,
                signal['direction'],
                sl_price,
                tp_price,
                max_bars=100  # Max 100 bougies (100h pour TF 1h)
            )
            
            if exit_price is None:
                continue  # Pas de sortie trouvée
            
            # Calcul PnL
            if signal['direction'] == 'LONG':
                gross_pnl = (exit_price - entry_price) * quantity
            else:
                gross_pnl = (entry_price - exit_price) * quantity
            
            # Fees (entry + exit)
            fees = (entry_price * quantity + exit_price * quantity) * (self.config.trading_fee_pct / 100)
            
            # Slippage cost
            slippage_cost = abs(entry_price - signal['entry_price']) * quantity
            
            # Net PnL
            net_pnl = gross_pnl - fees - slippage_cost
            net_pnl_pct = (net_pnl / position_value) * 100
            
            # Update capital
            self.capital += net_pnl
            self.equity_curve.append(self.capital)
            
            # Créer trade
            trade = Trade(
                entry_date=signal_time,
                exit_date=exit_date,
                symbol=signal['symbol'],
                direction=signal['direction'],
                entry_price=entry_price,
                exit_price=exit_price,
                quantity=quantity,
                pnl=net_pnl,
                pnl_pct=net_pnl_pct,
                fees=fees,
                slippage=slippage_cost,
                exit_reason=exit_reason,
                confidence=signal['confidence']
            )
            self.trades.append(trade)
        
        logger.info(f"✓ Backtest completed: {len(self.trades)} trades")
        
        return self._calculate_metrics()
    
    def _find_exit_price(self,
                         df: pd.DataFrame,
                         entry_time: datetime,
                         direction: str,
                         sl_price: float,
                         tp_price: float,
                         max_bars: int = 100) -> Tuple[Optional[float], Optional[datetime], str]:
        """
        Trouve le prix de sortie (SL ou TP touché en premier)
        
        Returns:
            (exit_price, exit_date, exit_reason)
        """
        try:
            # Find closest index (pandas 2.x compatible)
            idx_list = df.index.tolist()
            entry_idx = min(range(len(idx_list)), key=lambda i: abs(idx_list[i] - entry_time))
        except:
            return None, None, "NOT_FOUND"
        
        # Parcourir les bougies suivantes
        for i in range(entry_idx + 1, min(entry_idx + max_bars, len(df))):
            candle = df.iloc[i]
            
            if direction == 'LONG':
                # Check SL first (prix baisse)
                if candle['low'] <= sl_price:
                    return sl_price, candle.name, 'STOP_LOSS'
                # Check TP (prix monte)
                elif candle['high'] >= tp_price:
                    return tp_price, candle.name, 'TAKE_PROFIT'
            else:  # SHORT
                # Check SL first (prix monte)
                if candle['high'] >= sl_price:
                    return sl_price, candle.name, 'STOP_LOSS'
                # Check TP (prix baisse)
                elif candle['low'] <= tp_price:
                    return tp_price, candle.name, 'TAKE_PROFIT'
        
        # Pas de sortie trouvée dans max_bars
        last_candle = df.iloc[min(entry_idx + max_bars - 1, len(df) - 1)]
        return last_candle['close'], last_candle.name, 'TIME_EXIT'
    
    def _calculate_metrics(self) -> Dict:
        """
        Calcule les metrics de performance
        
        Returns:
            Dict avec tous les metrics
        """
        if not self.trades:
            return {'error': 'No trades executed'}
        
        trades_df = pd.DataFrame([
            {
                'entry_date': t.entry_date,
                'exit_date': t.exit_date,
                'direction': t.direction,
                'pnl': t.pnl,
                'pnl_pct': t.pnl_pct,
                'fees': t.fees,
                'exit_reason': t.exit_reason,
                'confidence': t.confidence
            }
            for t in self.trades
        ])
        
        # Win/Loss
        winning_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] <= 0]
        
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        total_trades = len(trades_df)
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        
        # PnL
        total_pnl = trades_df['pnl'].sum()
        avg_win = winning_trades['pnl'].mean() if win_count > 0 else 0
        avg_loss = losing_trades['pnl'].mean() if loss_count > 0 else 0
        
        # Profit Factor
        gross_profit = winning_trades['pnl'].sum() if win_count > 0 else 0
        gross_loss = abs(losing_trades['pnl'].sum()) if loss_count > 0 else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')
        
        # Drawdown
        equity_series = pd.Series(self.equity_curve)
        running_max = equity_series.cummax()
        drawdown = (equity_series - running_max) / running_max * 100
        max_drawdown = drawdown.min()
        
        # Sharpe Ratio (simplifié, supposant 24/7 trading)
        returns = trades_df['pnl_pct']
        sharpe_ratio = (returns.mean() / returns.std() * np.sqrt(365 * 24)) if len(returns) > 1 and returns.std() > 0 else 0
        
        # Fees totales
        total_fees = trades_df['fees'].sum()
        
        # Durée moyenne des trades
        trades_df['duration'] = (trades_df['exit_date'] - trades_df['entry_date']).dt.total_seconds() / 3600
        avg_duration = trades_df['duration'].mean()
        
        metrics = {
            'total_trades': total_trades,
            'winning_trades': win_count,
            'losing_trades': loss_count,
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'total_pnl_pct': round((total_pnl / self.config.initial_capital) * 100, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'total_fees': round(total_fees, 2),
            'avg_trade_duration_h': round(avg_duration, 2),
            'final_capital': round(self.capital, 2),
            'initial_capital': self.config.initial_capital
        }
        
        logger.info(f"📊 Metrics: WR={win_rate:.1f}% | PnL={total_pnl:.2f} | Sharpe={sharpe_ratio:.2f} | DD={max_drawdown:.1f}%")
        
        return metrics
    
    def walk_forward_validation(self,
                                 df: pd.DataFrame,
                                 signals: List[Dict],
                                 n_splits: int = 3) -> Dict:
        """
        Walk-forward validation : divise les données en n périodes
        
        Args:
            df: DataFrame OHLCV
            signals: Liste des signaux
            n_splits: Nombre de splits
        
        Returns:
            Dict avec metrics par split + moyenne
        """
        if len(signals) < n_splits * 10:
            logger.warning(f"Not enough signals for {n_splits}-fold walk-forward")
            return self.run_backtest(df, signals)
        
        # Diviser les signaux en n périodes
        split_size = len(signals) // n_splits
        results = []
        
        for i in range(n_splits):
            start_idx = i * split_size
            end_idx = start_idx + split_size if i < n_splits - 1 else len(signals)
            
            split_signals = signals[start_idx:end_idx]
            
            # Reset backtester pour ce split
            self.capital = self.config.initial_capital
            self.trades = []
            
            metrics = self.run_backtest(df, split_signals)
            metrics['split'] = i + 1
            results.append(metrics)
        
        # Calcul moyenne
        valid_results = [r for r in results if 'win_rate' in r]
        
        if not valid_results:
            return {'error': 'No valid splits', 'splits': results}
        
        avg_metrics = {
            'validation_type': 'walk_forward',
            'n_splits': n_splits,
            'avg_win_rate': np.mean([r['win_rate'] for r in valid_results]),
            'avg_total_pnl': np.mean([r['total_pnl'] for r in valid_results]),
            'avg_sharpe': np.mean([r['sharpe_ratio'] for r in valid_results]),
            'avg_max_drawdown': np.mean([r['max_drawdown'] for r in valid_results]),
            'splits': results
        }
        
        logger.info(f"✓ Walk-forward validation: {n_splits} splits | Avg WR={avg_metrics['avg_win_rate']:.1f}%")
        
        return avg_metrics


if __name__ == "__main__":
    # Test
    from data_pipeline import DataPipeline
    from feature_engineering import FeatureEngineer
    from signal_generator import SignalGenerator
    
    print("🐉 Testing Saiyan Backtester v0.1\n")
    
    pipeline = DataPipeline()
    df = pipeline.fetch_crypto_data('BTC/USDT', '1h', 1000)
    df.attrs['symbol'] = 'BTC/USDT'
    
    fe = FeatureEngineer()
    df = fe.calculate_all_features(df)
    
    sg = SignalGenerator()
    signals = sg.generate_signals(df, 'mean_reversion')
    
    config = BacktestConfig(
        initial_capital=10000,
        trading_fee_pct=0.1,
        slippage_pct=0.05
    )
    
    backtester = Backtester(config)
    metrics = backtester.run_backtest(df, signals)
    
    print(f"\n📊 Backtest Results:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
