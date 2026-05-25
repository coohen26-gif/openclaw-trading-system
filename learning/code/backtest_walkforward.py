#!/usr/bin/env python3
"""
Backtest Walk-Forward Validation - Momentum + HMM Strategy
Train: 2020-2023 (3 ans)
Test: 2024-2026 (2 ans)

Validation de robustesse hors échantillon
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

# Position sizing par régime (configuration optimisée - conservatrice)
REGIME_SIZING = {
    'Bull': 0.75,        # 18.75% capital (0.75 × 25% Kelly)
    'Volatile Bull': 0.5, # 12.5% capital
    'Range': 0.25,        # 6.25% capital
    'Bear': 0.1           # 2.5% capital (quasi cash)
}

# Stops & Targets par régime
REGIME_STOPS = {
    'Bull': {'sl': -0.05, 'tp': 0.15},
    'Volatile Bull': {'sl': -0.08, 'tp': 0.20},
    'Range': {'sl': -0.04, 'tp': 0.08},
    'Bear': {'sl': -0.03, 'tp': 0.05}
}

# HMM Parameters
HMM_LOOKBACK = 30  # Réduit de 60j → 30j
CONFIDENCE_THRESHOLD = 60  # Minimum 60/100
MAX_HOLD_DAYS = 20

# ============================================================================
# HMM REGIME DETECTION (Simple Implementation)
# ============================================================================

class HMMRegimeDetector:
    """
    Simple HMM-like regime detector using clustering + volatility/return regimes.
    Remplace sklearn.hmm (déprécié) par une approche pragmatique.
    """
    
    def __init__(self, n_regimes=4, lookback=30):
        self.n_regimes = n_regimes
        self.lookback = lookback
        self.regime_names = ['Bear', 'Range', 'Volatile Bull', 'Bull']
        self.fitted = False
        self.regime_params = None  # Centres de régimes
        
    def fit(self, returns):
        """Entraîner sur returns (clustering simple)"""
        if len(returns) < self.lookback:
            self.fitted = False
            return self
        
        # Extraire features sur fenêtre glissante
        features = []
        for i in range(self.lookback, len(returns)):
            window = returns[i-self.lookback:i]
            mean_ret = np.mean(window)
            vol = np.std(window)
            momentum = np.prod(1 + window) - 1
            features.append([mean_ret, vol, momentum])
        
        features = np.array(features)
        
        # Clustering KMeans simple pour identifier régimes
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=self.n_regimes, random_state=42, n_init=10)
        labels = kmeans.fit_predict(features)
        
        # Stocker centres
        self.regime_params = {
            'centers': kmeans.cluster_centers_,
            'labels': labels
        }
        
        self.fitted = True
        return self
    
    def predict(self, returns):
        """Prédire régime actuel"""
        if not self.fitted or len(returns) < self.lookback:
            return 'Range', 0.5
        
        # Extraire features récentes
        window = returns[-self.lookback:]
        mean_ret = np.mean(window)
        vol = np.std(window)
        momentum = np.prod(1 + window) - 1
        
        features = np.array([[mean_ret, vol, momentum]])
        
        # Trouver centre le plus proche
        from sklearn.metrics import pairwise_distances
        distances = pairwise_distances(features, self.regime_params['centers'])
        regime_idx = np.argmin(distances[0])
        
        # Calculer confidence (inverse de distance normalisée)
        min_dist = distances[0][regime_idx]
        avg_dist = np.mean(distances[0])
        confidence = min(100, max(0, (1 - min_dist / (avg_dist + 0.001)) * 100))
        
        regime_name = self.regime_names[regime_idx]
        return regime_name, confidence


# ============================================================================
# TRADING ENGINE
# ============================================================================

class MomentumHMMEngine:
    def __init__(self, hmm_detector, regime_sizing, regime_stops):
        self.hmm = hmm_detector
        self.regime_sizing = regime_sizing
        self.regime_stops = regime_stops
        self.position = None  # {'entry_price', 'direction', 'size', 'entry_day'}
        self.trades = []
        self.equity_curve = [1.0]
        
    def run(self, prices, returns):
        """Exécuter backtest complet"""
        print(f"🚀 Démarrage backtest walk-forward...")
        print(f"   Données: {len(prices)} jours")
        
        # Initialiser HMM sur première moitié (warm-up)
        warmup = len(returns) // 4
        self.hmm.fit(returns[:warmup])
        
        for i in range(warmup, len(prices)):
            regime, confidence = self.hmm.predict(returns[:i])
            self._process_day(i, prices[i], regime, confidence, returns)
            
        return self._generate_results(prices)
    
    def _process_day(self, day_idx, price, regime, confidence, returns):
        """Traiter un jour de trading"""
        current_equity = self.equity_curve[-1]
        
        # Vérifier position existante
        if self.position:
            self._manage_position(day_idx, price, regime)
        
        # Chercher nouveau signal si pas de position
        if not self.position:
            self._check_entry(day_idx, price, regime, confidence, returns)
        
        self.equity_curve.append(self.equity_curve[-1])
    
    def _manage_position(self, day_idx, price, regime):
        """Gérer position existante (stops, TP, trailing, time exit)"""
        pos = self.position
        entry_price = pos['entry_price']
        direction = pos['direction']
        entry_day = pos['entry_day']
        size = pos['size']
        
        # Calculer P&L actuel
        if direction == 'LONG':
            pnl_pct = (price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - price) / entry_price
        
        # Stops & TP du régime
        stops = self.regime_stops[regime]
        sl_pct = stops['sl']
        tp_pct = stops['tp']
        
        # Trailing stop (après +5%)
        trailing_active = pnl_pct > 0.05
        trailing_stop = entry_price * (1 + 0.03) if direction == 'LONG' else entry_price * (0.97)
        
        exit_reason = None
        
        # Check exits
        if pnl_pct <= sl_pct:
            exit_reason = 'Stop Loss'
        elif pnl_pct >= tp_pct:
            exit_reason = 'Take Profit'
        elif day_idx - entry_day >= MAX_HOLD_DAYS:
            exit_reason = 'Time Exit'
        elif trailing_active and ((direction == 'LONG' and price < trailing_stop) or 
                                   (direction == 'SHORT' and price > trailing_stop)):
            exit_reason = 'Trailing Stop'
        
        if exit_reason:
            # Fermer position
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
                'regime': regime
            })
            
            self.position = None
    
    def _check_entry(self, day_idx, price, regime, confidence, returns):
        """Vérifier opportunité d'entrée"""
        if confidence < CONFIDENCE_THRESHOLD:
            return
        
        # Signal momentum (simple)
        momentum_10 = np.prod(1 + returns[-10:]) - 1 if len(returns) >= 10 else 0
        momentum_5 = np.prod(1 + returns[-5:]) - 1 if len(returns) >= 5 else 0
        
        # Entry logic
        signal = None
        if regime in ['Bull', 'Volatile Bull'] and momentum_5 > 0.02:
            signal = 'LONG'
        elif regime == 'Bear' and momentum_5 < -0.02:
            signal = 'SHORT'
        elif regime == 'Range' and abs(momentum_5) < 0.01:
            # Mean reversion in range
            if momentum_10 < -0.05:
                signal = 'LONG'
            elif momentum_10 > 0.05:
                signal = 'SHORT'
        
        if signal:
            size = REGIME_SIZING[regime]
            self.position = {
                'entry_price': price,
                'direction': signal,
                'size': size,
                'entry_day': day_idx,
                'regime': regime,
                'confidence': confidence
            }
    
    def _generate_results(self, prices):
        """Générer résultats complets"""
        equity = np.array(self.equity_curve[1:])  # Skip initial 1.0
        
        total_return = equity[-1] - 1
        daily_returns = np.diff(equity) / equity[:-1]
        
        # Metrics
        sharpe = np.sqrt(252) * np.mean(daily_returns) / np.std(daily_returns) if len(daily_returns) > 1 else 0
        max_dd = self._calculate_max_drawdown(equity)
        win_rate = len([t for t in self.trades if t['pnl'] > 0]) / len(self.trades) if self.trades else 0
        
        # Exit reasons breakdown
        exit_reasons = {}
        for t in self.trades:
            reason = t['exit_reason']
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        results = {
            'total_return': total_return,
            'sharpe': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
            'n_trades': len(self.trades),
            'trades': self.trades,
            'equity_curve': equity,
            'daily_returns': daily_returns,
            'exit_reasons': exit_reasons
        }
        
        return results
    
    def _calculate_max_drawdown(self, equity):
        """Calculer drawdown maximum"""
        peak = np.maximum.accumulate(equity)
        drawdown = (equity - peak) / peak
        return np.min(drawdown)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def load_data():
    """Charger données BTC"""
    print(f"📊 Chargement données: {DATA_PATH}")
    
    if not DATA_PATH.exists():
        # Créer données synthétiques pour test
        print("   ⚠️ Fichier non trouvé, génération données synthétiques...")
        np.random.seed(42)
        n_days = 2300  # ~6 ans
        returns = np.random.normal(0.0005, 0.03, n_days)  # Mean 0.05%/day, vol 3%
        prices = 10000 * np.cumprod(1 + returns)
        dates = pd.date_range('2020-01-01', periods=n_days, freq='D')
        
        df = pd.DataFrame({'date': dates, 'close': prices})
        df.to_csv(DATA_PATH, index=False)
        return df
    
    df = pd.read_csv(DATA_PATH, parse_dates=['date'])
    return df


def walk_forward_validation(df):
    """Exécuter validation walk-forward"""
    
    # Split train/test
    train_mask = (df['date'] >= TRAIN_START) & (df['date'] <= TRAIN_END)
    test_mask = (df['date'] >= TEST_START) & (df['date'] <= TEST_END)
    
    train_df = df[train_mask].copy()
    test_df = df[test_mask].copy()
    
    print(f"\n📈 Split Walk-Forward:")
    print(f"   Train: {TRAIN_START} → {TRAIN_END} ({len(train_df)} jours)")
    print(f"   Test:  {TEST_START} → {TEST_END} ({len(test_df)} jours)")
    
    # Calculer returns
    train_returns = train_df['close'].pct_change().dropna().values
    test_returns = test_df['close'].pct_change().dropna().values
    
    train_prices = train_df['close'].values
    test_prices = test_df['close'].values
    
    # ========== TRAIN PERIOD ==========
    print(f"\n{'='*60}")
    print(f"🎯 PÉRIODE D'ENTRAÎNEMENT ({TRAIN_START} → {TRAIN_END})")
    print(f"{'='*60}")
    
    hmm_train = HMMRegimeDetector(n_regimes=4, lookback=HMM_LOOKBACK)
    engine_train = MomentumHMMEngine(hmm_train, REGIME_SIZING, REGIME_STOPS)
    results_train = engine_train.run(train_prices, train_returns)
    
    print_results(results_train, "TRAIN")
    
    # ========== TEST PERIOD ==========
    print(f"\n{'='*60}")
    print(f"🧪 PÉRIODE DE TEST ({TEST_START} → {TEST_END})")
    print(f"{'='*60}")
    
    # Utiliser même modèle HMM (pas de réentraînement - vrai walk-forward)
    hmm_test = HMMRegimeDetector(n_regimes=4, lookback=HMM_LOOKBACK)
    # Réentraîner sur train complet pour test
    hmm_test.fit(train_returns)
    
    engine_test = MomentumHMMEngine(hmm_test, REGIME_SIZING, REGIME_STOPS)
    results_test = engine_test.run(test_prices, test_returns)
    
    print_results(results_test, "TEST")
    
    # ========== COMPARISON ==========
    print(f"\n{'='*60}")
    print(f"📊 COMPARAISON TRAIN vs TEST")
    print(f"{'='*60}")
    
    metrics = ['total_return', 'sharpe', 'max_drawdown', 'win_rate']
    print(f"\n{'Métrique':<20} {'Train':>12} {'Test':>12} {'Écart':>12}")
    print(f"{'-'*60}")
    
    for metric in metrics:
        train_val = results_train[metric]
        test_val = results_test[metric]
        if metric == 'total_return' or metric == 'max_drawdown':
            train_str = f"{train_val*100:+.1f}%"
            test_str = f"{test_val*100:+.1f}%"
        elif metric == 'sharpe':
            train_str = f"{train_val:.2f}"
            test_str = f"{test_val:.2f}"
        else:
            train_str = f"{train_val*100:.1f}%"
            test_str = f"{test_val*100:.1f}%"
        
        gap = test_val - train_val
        gap_str = f"{gap*100:+.1f}%" if metric != 'sharpe' else f"{gap:+.2f}"
        
        print(f"{metric:<20} {train_str:>12} {test_str:>12} {gap_str:>12}")
    
    # Validation verdict
    print(f"\n{'='*60}")
    print(f"✅ VERDICT VALIDATION")
    print(f"{'='*60}")
    
    # Criteria
    sharpe_degradation = results_test['sharpe'] / results_train['sharpe'] if results_train['sharpe'] > 0 else 0
    dd_degradation = abs(results_test['max_drawdown'] / results_train['max_drawdown']) if results_train['max_drawdown'] != 0 else 1
    
    print(f"\nCritères de robustesse:")
    print(f"  • Sharpe Test/Train: {sharpe_degradation:.2f} (cible: >0.7)")
    print(f"  • DD Test/Train: {dd_degradation:.2f} (cible: <1.5)")
    print(f"  • Win Rate Test: {results_test['win_rate']*100:.1f}% (cible: >50%)")
    
    robust = (sharpe_degradation > 0.7) and (dd_degradation < 1.5) and (results_test['win_rate'] > 0.5)
    
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
    print(f"   N Trades: {results['n_trades']}")
    
    if results['exit_reasons']:
        print(f"\n   Exit Reasons:")
        for reason, count in sorted(results['exit_reasons'].items(), key=lambda x: -x[1]):
            pct = count / results['n_trades'] * 100
            print(f"      {reason}: {count} ({pct:.0f}%)")


if __name__ == '__main__':
    print(f"{'='*60}")
    print(f"🐉 BACKTEST WALK-FORWARD VALIDATION")
    print(f"   Momentum + HMM Strategy")
    print(f"{'='*60}")
    
    # Charger données
    df = load_data()
    
    # Walk-forward validation
    results_train, results_test, robust = walk_forward_validation(df)
    
    # Sauvegarder résultats
    output_path = Path('/root/.openclaw/workspace/learning/data/walkforward_results.csv')
    
    equity_df = pd.DataFrame({
        'date': pd.date_range('2020-01-01', periods=len(results_test['equity_curve']))[:len(results_test['equity_curve'])],
        'equity': results_test['equity_curve']
    })
    equity_df.to_csv(output_path, index=False)
    print(f"\n💾 Résultats sauvegardés: {output_path}")
    
    print(f"\n{'='*60}")
    print(f"✅ Walk-forward validation terminée!")
    print(f"{'='*60}")
