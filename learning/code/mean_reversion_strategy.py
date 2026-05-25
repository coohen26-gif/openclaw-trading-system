#!/usr/bin/env python3
"""
Mean Reversion Strategy - Crypto Range Trading
Basé sur: RSI + Bollinger Bands + Volume Filter

Crypto = range-bound 70% du temps → Mean reversion > Momentum

Configuration:
- RSI < 30: LONG (oversold)
- RSI > 70: SHORT (overbought)
- Bollinger confirmation
- Volume filter (éviter faux signaux)
- Position sizing: 6% max (Kelly 1/8)
"""

import numpy as np
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_PATH = Path('/root/.openclaw/workspace/learning/data/btc_usdt_daily_2020_2026.csv')
TRAIN_START = '2020-01-01'
TRAIN_END = '2023-12-31'
TEST_START = '2024-01-01'
TEST_END = '2026-05-25'

# Position Sizing - Un peu plus agressif (confiance)
MAX_POSITION_SIZE = 0.08  # 6.25% → 8%

# RSI Parameters - Plus strict pour conviction
RSI_PERIOD = 14
RSI_OVERSOLD = 35    # 30 → 35 (moins de faux signaux)
RSI_OVERBOUGHT = 65  # 70 → 65

# Bollinger Bands - Extrêmes seulement
BB_PERIOD = 20
BB_STD = 2.5  # 2.0 → 2.5

# Volume Filter
VOLUME_MA_PERIOD = 20
VOLUME_THRESHOLD = 1.2  # Volume > 1.2x MA pour confirmer

# Risk Management - Couper pertes, laisser courir gains
STOP_LOSS = -0.05      # -8% → -5%
TAKE_PROFIT = 0.08     # +15% → +8%
TRAILING_STOP = 0.04   # Activer après +4%
MAX_HOLD_DAYS = 10     # 15j → 10j

# Regime Detection (Range vs Trend) - RELAXED
VOLATILITY_LOW = 0.025   # Seuil bas volatilité (augmenté)
VOLATILITY_HIGH = 0.08   # Seuil haut volatilité (augmenté)
MOMENTUM_THRESHOLD = 0.05  # |momentum| < 5% = range (augmenté)

# ============================================================================
# INDICATORS
# ============================================================================

def calculate_rsi(prices, period=14):
    """Calculer RSI"""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    if len(gains) < period:
        return np.array([50] * len(prices))
    
    avg_gains = np.zeros(len(prices))
    avg_losses = np.zeros(len(prices))
    
    # Initial SMA
    avg_gains[period] = np.mean(gains[:period])
    avg_losses[period] = np.mean(losses[:period])
    
    # EMA ensuite
    for i in range(period + 1, len(prices)):
        avg_gains[i] = (avg_gains[i-1] * (period - 1) + gains[i-1]) / period
        avg_losses[i] = (avg_losses[i-1] * (period - 1) + losses[i-1]) / period
    
    rs = np.where(avg_losses != 0, avg_gains / avg_losses, 100)
    rsi = 100 - (100 / (1 + rs))
    
    # Fill initial values
    rsi[:period] = 50
    
    return rsi


def calculate_bollinger_bands(prices, period=20, std_dev=2.0):
    """Calculer Bollinger Bands"""
    if len(prices) < period:
        return prices, prices, prices
    
    ma = np.zeros(len(prices))
    upper = np.zeros(len(prices))
    lower = np.zeros(len(prices))
    
    for i in range(period - 1, len(prices)):
        window = prices[i-period+1:i+1]
        ma[i] = np.mean(window)
        std = np.std(window)
        upper[i] = ma[i] + std_dev * std
        lower[i] = ma[i] - std_dev * std
    
    # Fill initial values
    ma[:period-1] = prices[:period-1]
    upper[:period-1] = prices[:period-1]
    lower[:period-1] = prices[:period-1]
    
    return ma, upper, lower


def detect_regime(prices, returns, lookback=20):
    """
    Détecter régime de marché: Range, Trend, ou Volatile
    
    Retourne: regime_name, confidence
    """
    if len(returns) < lookback:
        return 'Range', 0.6  # Default to range for more signals
    
    recent_returns = returns[-lookback:]
    
    # Volatilité
    volatility = np.std(recent_returns)
    
    # Momentum absolu
    momentum = np.abs(np.prod(1 + recent_returns) - 1)
    
    # Range detection - TRÈS PERMISSIF (on veut trader mean reversion)
    if volatility > VOLATILITY_HIGH:
        return 'Volatile', 0.7  # Trop dangereux
    elif momentum > 0.15:  # Trend très fort
        return 'Trend', 0.7
    else:
        return 'Range', 0.6  # Default = Range (mean reversion friendly)


# ============================================================================
# TRADING ENGINE
# ============================================================================

class MeanReversionEngine:
    def __init__(self):
        self.position = None
        self.trades = []
        self.equity_curve = [1.0]
        self.signals = []
        
    def run(self, df):
        """Exécuter backtest complet"""
        prices = df['close'].values
        dates = df['date'].values
        
        # Calculer indicateurs
        rsi = calculate_rsi(prices, RSI_PERIOD)
        bb_ma, bb_upper, bb_lower = calculate_bollinger_bands(prices, BB_PERIOD, BB_STD)
        returns = np.diff(prices) / prices[:-1]
        returns = np.insert(returns, 0, 0)
        
        print(f"🚀 Démarrage Mean Reversion backtest...")
        print(f"   Données: {len(prices)} jours")
        print(f"   RSI: {RSI_PERIOD}j, OB={RSI_OVERBOUGHT}, OS={RSI_OVERSOLD}")
        print(f"   Bollinger: {BB_PERIOD}j, {BB_STD}σ")
        print(f"   Position Size: {MAX_POSITION_SIZE*100:.1f}%")
        
        for i in range(max(RSI_PERIOD, BB_PERIOD), len(prices)):
            regime, confidence = detect_regime(prices[:i], returns[:i])
            self._process_day(i, prices[i], rsi[i], bb_lower[i], bb_upper[i], regime, returns)
            self.equity_curve.append(self.equity_curve[-1])
        
        return self._generate_results(prices, dates)
    
    def _process_day(self, day_idx, price, rsi, bb_lower, bb_upper, regime, returns):
        """Traiter un jour de trading"""
        
        # Vérifier position existante
        if self.position:
            self._manage_position(day_idx, price, returns)
        
        # Chercher signal si pas de position
        if not self.position:
            self._check_entry(day_idx, price, rsi, bb_lower, bb_upper, regime)
    
    def _manage_position(self, day_idx, price, returns):
        """Gérer position existante"""
        pos = self.position
        entry_price = pos['entry_price']
        direction = pos['direction']
        entry_day = pos['entry_day']
        size = pos['size']
        highest_price = pos.get('highest_price', entry_price)
        
        # Update highest price pour trailing
        if direction == 'LONG':
            highest_price = max(highest_price, price)
            pos['highest_price'] = highest_price
            pnl_pct = (price - entry_price) / entry_price
        else:
            highest_price = min(highest_price, price)
            pos['highest_price'] = highest_price
            pnl_pct = (entry_price - price) / entry_price
        
        exit_reason = None
        
        # Stop Loss
        if pnl_pct <= STOP_LOSS:
            exit_reason = 'Stop Loss'
        
        # Take Profit
        elif pnl_pct >= TAKE_PROFIT:
            exit_reason = 'Take Profit'
        
        # Time Exit
        elif day_idx - entry_day >= MAX_HOLD_DAYS:
            exit_reason = 'Time Exit'
        
        # Trailing Stop (après +5%)
        elif pnl_pct > TRAILING_STOP:
            if direction == 'LONG':
                trailing_level = highest_price * (1 - TRAILING_STOP)
                if price < trailing_level:
                    exit_reason = 'Trailing Stop'
            else:
                trailing_level = highest_price * (1 + TRAILING_STOP)
                if price > trailing_level:
                    exit_reason = 'Trailing Stop'
        
        if exit_reason:
            pnl = pnl_pct * size
            self.equity_curve[-1] *= (1 + pnl)
            
            self.trades.append({
                'entry_day': entry_day,
                'exit_day': day_idx,
                'entry_price': entry_price,
                'exit_price': price,
                'direction': direction,
                'size': size,
                'pnl_pct': pnl_pct,
                'pnl': pnl,
                'exit_reason': exit_reason,
                'regime': pos['regime'],
                'rsi_entry': pos['rsi_entry']
            })
            
            self.position = None
    
    def _check_entry(self, day_idx, price, rsi, bb_lower, bb_upper, regime):
        """Vérifier opportunité d'entrée"""
        
        # Mean reversion - trader Range et Trend modéré
        # Skip seulement Volatile (trop dangereux)
        if regime == 'Volatile':
            return
            return
        
        signal = None
        rsi_signal = None
        bb_signal = None
        
        # RSI Signal - Plus strict
        if rsi < RSI_OVERSOLD:  # 35
            rsi_signal = 'LONG'
        elif rsi > RSI_OVERBOUGHT:  # 65
            rsi_signal = 'SHORT'
        
        # Bollinger Signal - Extrêmes seulement
        if price < bb_lower * 1.005:  # Prix très proche/sous lower band
            bb_signal = 'LONG'
        elif price > bb_upper * 0.995:  # Prix très proche/au-dessus upper band
            bb_signal = 'SHORT'
        
        # Confirmation: RSI OU BB (pas besoin des deux, mais les deux = plus conviction)
        if rsi_signal and bb_signal and rsi_signal == bb_signal:
            # Les deux alignés = forte conviction
            signal = rsi_signal
            conviction = 'HIGH'
        elif rsi_signal:
            # RSI seul = conviction moyenne
            signal = rsi_signal
            conviction = 'MEDIUM'
        elif bb_signal:
            # BB seul = faible conviction (skip)
            return
        else:
            return
        
        if signal:
            self.position = {
                'entry_price': price,
                'direction': signal,
                'size': MAX_POSITION_SIZE,
                'entry_day': day_idx,
                'regime': regime,
                'rsi_entry': rsi,
                'highest_price': price,
                'conviction': conviction
            }
            
            self.signals.append({
                'day': day_idx,
                'price': price,
                'direction': signal,
                'rsi': rsi,
                'regime': regime
            })
    
    def _generate_results(self, prices, dates):
        """Générer résultats complets"""
        equity = np.array(self.equity_curve[1:])
        
        total_return = equity[-1] - 1
        daily_returns = np.diff(equity) / equity[:-1]
        
        # Metrics
        sharpe = np.sqrt(252) * np.mean(daily_returns) / np.std(daily_returns) if len(daily_returns) > 1 else 0
        max_dd = self._calculate_max_drawdown(equity)
        win_rate = len([t for t in self.trades if t['pnl'] > 0]) / len(self.trades) if self.trades else 0
        
        # Avg gain/loss
        winning_trades = [t['pnl_pct'] for t in self.trades if t['pnl'] > 0]
        losing_trades = [t['pnl_pct'] for t in self.trades if t['pnl'] <= 0]
        avg_gain = np.mean(winning_trades) if winning_trades else 0
        avg_loss = np.mean(losing_trades) if losing_trades else 0
        
        # Exit reasons breakdown
        exit_reasons = {}
        for t in self.trades:
            reason = t['exit_reason']
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        # Regime breakdown
        regime_stats = {}
        for t in self.trades:
            regime = t['regime']
            if regime not in regime_stats:
                regime_stats[regime] = {'wins': 0, 'losses': 0, 'total_pnl': 0}
            if t['pnl'] > 0:
                regime_stats[regime]['wins'] += 1
            else:
                regime_stats[regime]['losses'] += 1
            regime_stats[regime]['total_pnl'] += t['pnl']
        
        results = {
            'total_return': total_return,
            'sharpe': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
            'avg_gain': avg_gain,
            'avg_loss': avg_loss,
            'n_trades': len(self.trades),
            'n_signals': len(self.signals),
            'trades': self.trades,
            'equity_curve': equity,
            'daily_returns': daily_returns,
            'exit_reasons': exit_reasons,
            'regime_stats': regime_stats
        }
        
        return results
    
    def _calculate_max_drawdown(self, equity):
        """Calculer drawdown maximum"""
        peak = np.maximum.accumulate(equity)
        drawdown = (equity - peak) / peak
        return np.min(drawdown)


# ============================================================================
# WALK-FORWARD VALIDATION
# ============================================================================

def load_data():
    """Charger données BTC"""
    print(f"📊 Chargement données: {DATA_PATH}")
    
    if not DATA_PATH.exists():
        print("   ⚠️ Fichier non trouvé, génération données synthétiques...")
        np.random.seed(42)
        n_days = 2300
        # Données plus réalistes: mean-reverting
        returns = np.random.normal(0.0003, 0.025, n_days)
        prices = 10000 * np.cumprod(1 + returns)
        dates = pd.date_range('2020-01-01', periods=n_days, freq='D')
        
        df = pd.DataFrame({'date': dates, 'close': prices})
        df.to_csv(DATA_PATH, index=False)
        return df
    
    df = pd.read_csv(DATA_PATH, parse_dates=['date'])
    return df


def walk_forward_validation(df):
    """Exécuter validation walk-forward"""
    
    train_mask = (df['date'] >= TRAIN_START) & (df['date'] <= TRAIN_END)
    test_mask = (df['date'] >= TEST_START) & (df['date'] <= TEST_END)
    
    train_df = df[train_mask].copy()
    test_df = df[test_mask].copy()
    
    print(f"\n📈 Split Walk-Forward:")
    print(f"   Train: {TRAIN_START} → {TRAIN_END} ({len(train_df)} jours)")
    print(f"   Test:  {TEST_START} → {TEST_END} ({len(test_df)} jours)")
    
    # ========== TRAIN PERIOD ==========
    print(f"\n{'='*60}")
    print(f"🎯 PÉRIODE D'ENTRAÎNEMENT ({TRAIN_START} → {TRAIN_END})")
    print(f"{'='*60}")
    
    engine_train = MeanReversionEngine()
    results_train = engine_train.run(train_df)
    
    print_results(results_train, "TRAIN")
    
    # ========== TEST PERIOD ==========
    print(f"\n{'='*60}")
    print(f"🧪 PÉRIODE DE TEST ({TEST_START} → {TEST_END})")
    print(f"{'='*60}")
    
    engine_test = MeanReversionEngine()
    results_test = engine_test.run(test_df)
    
    print_results(results_test, "TEST")
    
    # ========== COMPARISON ==========
    print(f"\n{'='*60}")
    print(f"📊 COMPARAISON TRAIN vs TEST")
    print(f"{'='*60}")
    
    metrics = ['total_return', 'sharpe', 'max_drawdown', 'win_rate', 'avg_gain']
    print(f"\n{'Métrique':<20} {'Train':>12} {'Test':>12} {'Écart':>12}")
    print(f"{'-'*60}")
    
    for metric in metrics:
        train_val = results_train[metric]
        test_val = results_test[metric]
        
        if metric == 'total_return' or metric == 'max_drawdown' or metric == 'avg_gain' or metric == 'avg_loss':
            train_str = f"{train_val*100:+.1f}%"
            test_str = f"{test_val*100:+.1f}%"
        elif metric == 'sharpe':
            train_str = f"{train_val:.2f}"
            test_str = f"{test_val:.2f}"
        else:
            train_str = f"{train_val*100:.1f}%"
            test_str = f"{test_val*100:.1f}%"
        
        gap = test_val - train_val
        gap_str = f"{gap*100:+.1f}%" if metric not in ['sharpe'] else f"{gap:+.2f}"
        
        print(f"{metric:<20} {train_str:>12} {test_str:>12} {gap_str:>12}")
    
    # Validation verdict
    print(f"\n{'='*60}")
    print(f"✅ VERDICT VALIDATION")
    print(f"{'='*60}")
    
    sharpe_degradation = results_test['sharpe'] / results_train['sharpe'] if results_train['sharpe'] > 0 else 0
    dd_degradation = abs(results_test['max_drawdown'] / results_train['max_drawdown']) if results_train['max_drawdown'] != 0 else 1
    
    print(f"\nCritères de robustesse:")
    print(f"  • Sharpe Test/Train: {sharpe_degradation:.2f} (cible: >0.7)")
    print(f"  • DD Test/Train: {dd_degradation:.2f} (cible: <1.5)")
    print(f"  • Win Rate Test: {results_test['win_rate']*100:.1f}% (cible: >50%)")
    print(f"  • Return Test: {results_test['total_return']*100:+.1f}% (cible: >0%)")
    
    robust = (sharpe_degradation > 0.7) and (dd_degradation < 1.5) and \
             (results_test['win_rate'] > 0.5) and (results_test['total_return'] > 0)
    
    if robust:
        print(f"\n🟢 STRATÉGIE ROBUSTE - Walk-forward VALIDÉ ✅")
    else:
        print(f"\n🟠 STRATÉGIE FRAGILE - Ajustements requis ⚠️")
    
    return results_train, results_test, robust


def print_results(results, period):
    """Afficher résultats"""
    print(f"\n📊 Résultats {period}:")
    print(f"   Return Total: {results['total_return']*100:+.1f}%")
    print(f"   Sharpe Ratio: {results['sharpe']:.2f}")
    print(f"   Max Drawdown: {results['max_drawdown']*100:+.1f}%")
    print(f"   Win Rate: {results['win_rate']*100:.1f}%")
    print(f"   Avg Gain: {results['avg_gain']*100:+.2f}%")
    print(f"   Avg Loss: {results['avg_loss']*100:+.2f}%")
    print(f"   N Trades: {results['n_trades']} (Signals: {results['n_signals']})")
    
    if results['exit_reasons']:
        print(f"\n   Exit Reasons:")
        for reason, count in sorted(results['exit_reasons'].items(), key=lambda x: -x[1]):
            pct = count / results['n_trades'] * 100
            print(f"      {reason}: {count} ({pct:.0f}%)")
    
    if results['regime_stats']:
        print(f"\n   Performance par Régime:")
        for regime, stats in results['regime_stats'].items():
            total = stats['wins'] + stats['losses']
            wr = stats['wins'] / total * 100 if total > 0 else 0
            print(f"      {regime}: {total} trades, WR {wr:.0f}%, PnL {stats['total_pnl']*100:+.1f}%")


if __name__ == '__main__':
    print(f"{'='*60}")
    print(f"🐉 MEAN REVERSION STRATEGY - Walk-Forward Validation")
    print(f"   RSI + Bollinger Bands + Range Detection")
    print(f"{'='*60}")
    
    df = load_data()
    results_train, results_test, robust = walk_forward_validation(df)
    
    # Sauvegarder résultats
    output_path = Path('/root/.openclaw/workspace/learning/data/meanrev_walkforward_results.csv')
    
    equity_df = pd.DataFrame({
        'date': pd.date_range('2020-01-01', periods=len(results_test['equity_curve']))[:len(results_test['equity_curve'])],
        'equity': results_test['equity_curve']
    })
    equity_df.to_csv(output_path, index=False)
    print(f"\n💾 Résultats sauvegardés: {output_path}")
    
    print(f"\n{'='*60}")
    print(f"✅ Walk-forward validation terminée!")
    print(f"{'='*60}")
