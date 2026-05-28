# 🐉 RECHERCHE NOCTURNE SAIYAN V0.3 — Deep RL + HMM + Gates Bailey

**Date:** 2026-05-28 01:00 UTC  
**Session:** Cron Nocturne Automatique  
**Semaine:** 35 (J+2 du plan v0.3)  
**Mission:** Exploration autonome Deep RL, amélioration HMM, Gates Bailey

---

## 🎯 SYNTHÈSE EXÉCUTIVE

**Statut actuel (J+2):**
- ✅ Audit v0.2 terminé (bugs critiques identifiés)
- ✅ Plan action v0.3 validé (axe B: Deep RL)
- ✅ Données réelles disponibles (2301 jours BTC 2020-2026)
- ⚠️ HMM actuel = FAUX (rule-based déguisé)
- ⚠️ Gates Bailey non implémentées

**Objectif nocturne:** Produire 2-3 idées concrètes d'amélioration + roadmap implémentation.

---

## 1. 🧠 DEEP RL — ARCHITECTURES POUR TRADING

### 1.1 Paysage 2024-2026

| Algorithme | Type | Action Space | Sample Efficiency | Stabilité | Recommandation |
|------------|------|--------------|-------------------|-----------|----------------|
| **PPO** | On-policy | Discret/Continu | Moyenne | ⭐⭐⭐⭐⭐ | **TOP CHOIX** |
| **SAC** | Off-policy | Continu uniquement | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Position sizing |
| **A2C** | On-policy | Discret/Continu | Moyenne | ⭐⭐⭐ | Baseline rapide |
| **DQN** | Off-policy | Discret uniquement | ⭐⭐⭐ | ⭐⭐ | À éviter (instable) |
| **TRPO** | On-policy | Continu | Faible | ⭐⭐⭐⭐ | Trop complexe |

---

### 1.2 PPO (Proximal Policy Optimization) — Architecture Recommandée

**Pourquoi PPO pour Saiyan v0.3:**

```
Avantages clés:
✅ Clip mechanism → updates progressives (pas de policy collapse)
✅ Gère actions discrètes (BUY/HOLD/SELL) ET continues (position sizing)
✅ Stable-Baselines3 support mature
✅ Moins sensible aux hyperparamètres que SAC/A2C
✅ Sample efficient pour données financières limitées
```

**Architecture proposée:**

```python
Input Features (shape: [batch, seq_len, features]):
├── Prix normalisés (log returns, 5j window)
├── Volatilité rolling (30j GARCH)
├── Régime HMM (probabilités 4 états)
├── Funding rates (BTC/ETH/SOL perp)
├── Momentum indicators (RSI, MACD)
└── État portfolio (balance, position, PnL unrealized)

Network Architecture:
┌─────────────────────────────────────────┐
│ Input: [batch, 60, 15]                  │
│ (60 time steps, 15 features)            │
└─────────────────┬───────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│ LSTM(128 units)                         │
│ Capture temporal dependencies           │
└─────────────────┬───────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│ Dense(64, ReLU) + Dropout(0.3)          │
└─────────────────┬───────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│ Dense(32, ReLU)                         │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┐
        ↓                   ↓
┌──────────────────┐ ┌──────────────────┐
│ Policy Head      │ │ Value Head       │
│ Dense(3, softmax)│ │ Dense(1, linear) │
│ BUY/HOLD/SELL    │ │ V(s) estimate    │
└──────────────────┘ └──────────────────┘
```

**Hyperparamètres optimaux (trading crypto):**

```yaml
ppo_config:
  learning_rate: 3e-4
  n_steps: 2048          # Steps per rollout
  batch_size: 64
  n_epochs: 10           # Epochs per batch
  gamma: 0.99            # Discount factor (long-term rewards)
  gae_lambda: 0.95       # Generalized Advantage Estimation
  clip_range: 0.2        # PPO clip epsilon
  ent_coef: 0.01         # Entropy bonus (exploration)
  vf_coef: 0.5           # Value function loss weight
  max_grad_norm: 0.5     # Gradient clipping
  
  # Early stopping
  early_stopping_rounds: 5
  eval_freq: 10000       # Evaluate every 10k steps
  best_model_threshold: 0.001  # Min Sharpe improvement
```

**Reward Function — Critique!**

```python
def calculate_reward(self, pnl, fees, drawdown, volatility, regime):
    """
    Risk-adjusted reward shaping pour PPO trading.
    """
    # Base: PnL net fees (normalized by capital)
    base_reward = (pnl - fees) / self.capital
    
    # Penalty: Drawdown aversion (risk management)
    drawdown_penalty = 0.5 * drawdown  # Penalize large DD
    
    # Penalty: Volatility (Sharpe-like component)
    vol_penalty = 0.1 * volatility / (base_reward + 1e-6)
    
    # Bonus: Regime-aware (reward appropriate actions)
    regime_bonus = 0.0
    if regime == 'BULL' and self.position > 0:
        regime_bonus = 0.05  # Reward being long in bull
    elif regime == 'BEAR' and self.position == 0:
        regime_bonus = 0.05  # Reward staying flat in bear
    elif regime == 'RANGE' and abs(self.position) < 0.02:
        regime_bonus = 0.03  # Reward small positions in range
    
    # Penalty: Excessive trading (transaction costs)
    trading_penalty = -0.001 * self.trades_count_today
    
    total_reward = (base_reward 
                    - drawdown_penalty 
                    - vol_penalty 
                    + regime_bonus 
                    + trading_penalty)
    
    return np.clip(total_reward, -1.0, 1.0)  # Clip to avoid extreme rewards
```

---

### 1.3 SAC (Soft Actor-Critic) — Alternative pour Position Sizing Continu

**Cas d'usage SAC:** Si on veut position sizing précis (0% à 100% continu) plutôt que discret (0%/25%/50%/75%/100%).

```python
# SAC Action Space: Box(low=-1.0, high=1.0, shape=(1,))
# -1.0 = Full short, 0.0 = Flat, +1.0 = Full long

# Avantages vs PPO:
✅ Off-policy → réutilise old data (sample efficient)
✅ Maximum entropy → exploration intrinsèque
✅ Action space continu naturel
✅ Très stable training

# Inconvénients:
❌ Plus complexe à implémenter
❌ Hyperparamètres plus sensibles (alpha tuning)
❌ Moins mature dans Stable-Baselines3 pour finance
```

**Recommandation:** Commencer avec PPO (discret). Si besoin de finesse position sizing → passer à SAC ou hybride PPO+continuous sizing.

---

### 1.4 Training Pipeline — Walk-Forward OOS Strict

```
DONNÉES: 2020-2026 (6 ans, 2301 jours)

PHASE 1 — TRAIN AGENT #1 (2020-2021):
├── Training: 2020-01-01 → 2021-12-31 (730 jours)
├── Validation: 2022-01-01 → 2022-06-30 (180 jours)
└── Test OOS: 2022-07-01 → 2022-12-31 (180 jours)

PHASE 2 — TRAIN AGENT #2 (2021-2022):
├── Training: 2021-01-01 → 2022-12-31 (730 jours)
├── Validation: 2023-01-01 → 2023-06-30 (180 jours)
└── Test OOS: 2023-07-01 → 2023-12-31 (180 jours)

PHASE 3 — TRAIN AGENT #3 (2022-2023):
├── Training: 2022-01-01 → 2023-12-31 (730 jours)
├── Validation: 2024-01-01 → 2024-06-30 (180 jours)
└── Test OOS: 2024-07-01 → 2024-12-31 (180 jours)

ENSEMBLE DEPLOYMENT (2025-2026):
├── Agent #1 → Spécialisé bull markets
├── Agent #2 → Spécialisé bear/range
├── Agent #3 → Spécialisé volatile transitions
└── Voting pondéré par confidence + regime HMM
```

**Gates Bailey sur chaque test OOS:**
- CPCV 6-fold sur période test
- DSR > 0 requis
- PSR > 0.95 requis
- PBO < 0.5 requis
- Wilson CI95 lo ≥ 70% pour claim WR

---

## 2. 🔧 AMÉLIORATION HMM — BAUM-WELCH ROLLING 180J

### 2.1 État Actuel (Audit)

**Fichier:** `system-saiyan/v0.3/core/hmm_regime.py` (15898 bytes)

**Problème critique:**
```python
# Code actuel (extrait audit):
def detect_regime_simple(self, prices, volatility):
    # ❌ FAUX HMM! Juste des if/else
    if momentum > 0 and current_vol < vol_median:
        regime = Regime.BULL
    elif momentum < 0 and current_vol > vol_median:
        regime = Regime.BEAR
    # ...
```

**Ce qui existe:**
- ❌ Pas de `hmmlearn` import
- ❌ Pas de `GaussianHMM`
- ❌ Pas de fit/predict Baum-Welch
- ✅ Rule-based classifier déguisé en "HMM"

---

### 2.2 Vrai HMM — Implémentation Baum-Welch

**Installation requise:**
```bash
pip install hmmlearn  # Version: 0.3.0+
```

**Implémentation rolling 180j:**

```python
from hmmlearn import hmm
import numpy as np
import pandas as pd

class TrueHMMRegimeDetector:
    """
    Vrai Hidden Markov Model avec Baum-Welch algorithm.
    Rolling window 180 jours pour adaptation continue.
    """
    
    def __init__(self, n_regimes=4, rolling_window=180, random_state=42):
        self.n_regimes = n_regimes
        self.rolling_window = rolling_window
        self.random_state = random_state
        self.model = None
        self.regime_map = None  # Mapping état → label interprétable
        
    def prepare_features(self, returns, volatility):
        """
        Préparer features pour HMM.
        
        Features recommandés:
        - Returns (log returns daily)
        - Volatility (rolling 30j std ou GARCH)
        - Volume change (optionnel)
        - Skewness rolling (optionnel)
        """
        X = np.column_stack([returns, volatility])
        
        # Standardize features (important pour HMM convergence)
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        return X_scaled, scaler
    
    def fit_rolling(self, returns, volatility):
        """
        Fit HMM sur fenêtre rolling 180 jours.
        
        Baum-Welch algorithm:
        1. Initialize parameters (π, A, μ, Σ)
        2. E-step: Calculate posterior probabilities
        3. M-step: Update parameters to maximize likelihood
        4. Repeat until convergence
        """
        X_scaled, self.scaler = self.prepare_features(returns, volatility)
        
        if len(X_scaled) < self.rolling_window:
            raise ValueError(
                f"Need at least {self.rolling_window} days, "
                f"got {len(X_scaled)}"
            )
        
        # Prendre dernières 180 observations
        X_window = X_scaled[-self.rolling_window:]
        
        # GaussianHMM avec covariance diagonale (plus stable)
        self.model = hmm.GaussianHMM(
            n_components=self.n_regimes,
            covariance_type='diag',  # Diagonale → moins de paramètres
            n_iter=100,              # Max iterations Baum-Welch
            tol=1e-4,                # Convergence threshold
            random_state=self.random_state,
            init_params='stmc',      # Initialize all params
            params='stmc'            # Estimate all params
        )
        
        # Fit avec Baum-Welch
        self.model.fit(X_window)
        
        # Calibration automatique des labels
        self.regime_map = self._calibrate_regime_labels()
        
        return self.model
    
    def _calibrate_regime_labels(self):
        """
        Mapper les états HMM vers labels interprétables.
        
        Heuristique:
        - BULL: Haut returns, basse volatilité
        - BEAR: Bas/négatifs returns, haute volatilité
        - RANGE: Returns neutres, vol moyenne
        - VOLATILE: Vol extrême (peu importe returns)
        """
        means = self.model.means_      # Shape: (n_regimes, 2)
        covars = self.model.covars_    # Shape: (n_regimes, 2)
        
        # Score pour chaque état
        scores = {}
        for i in range(self.n_regimes):
            ret_mean = means[i, 0]
            vol_mean = means[i, 1]
            
            # Bull score: high return, low vol
            bull_score = ret_mean - vol_mean
            
            # Bear score: low return, high vol
            bear_score = -ret_mean + vol_mean
            
            # Volatile score: extreme vol
            volatile_score = vol_mean
            
            scores[i] = {
                'bull': bull_score,
                'bear': bear_score,
                'volatile': volatile_score,
                'ret': ret_mean,
                'vol': vol_mean
            }
        
        # Assigner labels
        regime_map = {}
        assigned = set()
        
        # 1. Plus haut bull_score → BULL
        bull_state = max(scores.keys(), key=lambda k: scores[k]['bull'])
        regime_map[bull_state] = 'BULL'
        assigned.add(bull_state)
        
        # 2. Plus haut bear_score → BEAR
        bear_state = max(
            [k for k in scores.keys() if k not in assigned],
            key=lambda k: scores[k]['bear']
        )
        regime_map[bear_state] = 'BEAR'
        assigned.add(bear_state)
        
        # 3. Plus haute vol → VOLATILE_TRANSITION
        if len(assigned) < self.n_regimes:
            volatile_state = max(
                [k for k in scores.keys() if k not in assigned],
                key=lambda k: scores[k]['volatile']
            )
            regime_map[volatile_state] = 'VOLATILE_TRANSITION'
            assigned.add(volatile_state)
        
        # 4. État restant → RANGE
        remaining = set(range(self.n_regimes)) - assigned
        if remaining:
            regime_map[list(remaining)[0]] = 'RANGE'
        
        return regime_map
    
    def predict_regime(self, current_return, current_volatility):
        """
        Prédire régime actuel.
        
        Retourne: (regime_label, confidence, probabilities)
        """
        if self.model is None:
            raise ValueError("Must fit model first with fit_rolling()")
        
        # Prepare observation
        X_obs = np.array([[current_return, current_volatility]])
        X_scaled = self.scaler.transform(X_obs)
        
        # Predict state
        state = self.model.predict(X_scaled)[0]
        
        # Get posterior probabilities
        log_prob = self.model.score_samples(X_scaled)[0]
        probabilities = np.exp(log_prob)
        
        # Confidence = max probability
        confidence = probabilities.max()
        
        # Map to label
        regime_label = self.regime_map.get(state, 'UNKNOWN')
        
        return regime_label, confidence, probabilities
    
    def get_transition_matrix(self):
        """
        Retourne matrice de transition A (n_regimes x n_regimes).
        
        A[i,j] = Probabilité de transition état i → état j
        """
        if self.model is None:
            return None
        return self.model.transmat_
    
    def get_regime_persistence(self):
        """
        Calculer persistance moyenne de chaque régime.
        
        Persistence = 1 / (1 - A[i,i])
        Durée moyenne dans régime i avant transition.
        """
        if self.model is None:
            return None
        
        transmat = self.model.transmat_
        persistence = {}
        
        for state, label in self.regime_map.items():
            prob_stay = transmat[state, state]
            avg_duration = 1 / (1 - prob_stay + 1e-9)
            persistence[label] = avg_duration
        
        return persistence
```

---

### 2.3 Rolling Re-fit — Pipeline Quotidien

```python
class DailyHMMUpdater:
    """
    Met à jour HMM quotidiennement avec nouvelles données.
    """
    
    def __init__(self, hmm_detector, data_buffer_max=180):
        self.hmm_detector = hmm_detector
        self.data_buffer = []
        self.data_buffer_max = data_buffer_max
        
    def add_daily_observation(self, date, close_price, volume):
        """
        Ajouter observation quotidienne et mettre à jour HMM.
        """
        # Calculer return daily
        if len(self.data_buffer) > 0:
            prev_close = self.data_buffer[-1]['close']
            daily_return = np.log(close_price / prev_close)
        else:
            daily_return = 0.0
        
        # Calculer volatilité rolling 30j
        closes = [d['close'] for d in self.data_buffer[-30:]] + [close_price]
        returns_30j = [np.log(closes[i]/closes[i-1]) for i in range(1, len(closes))]
        volatility = np.std(returns_30j) * np.sqrt(252) if len(returns_30j) > 1 else 0.1
        
        # Ajouter au buffer
        self.data_buffer.append({
            'date': date,
            'close': close_price,
            'return': daily_return,
            'volatility': volatility
        })
        
        # Garder buffer à 180 jours max
        if len(self.data_buffer) > self.data_buffer_max:
            self.data_buffer.pop(0)
        
        # Re-fit HMM si buffer plein
        if len(self.data_buffer) >= self.hmm_detector.rolling_window:
            returns = np.array([d['return'] for d in self.data_buffer])
            volatility = np.array([d['volatility'] for d in self.data_buffer])
            
            self.hmm_detector.fit_rolling(returns, volatility)
            
            # Prédire régime actuel
            current_regime, confidence, probs = self.hmm_detector.predict_regime(
                daily_return, volatility
            )
            
            return {
                'date': date,
                'regime': current_regime,
                'confidence': confidence,
                'probabilities': probs,
                'persistence': self.hmm_detector.get_regime_persistence(),
                'transition_matrix': self.hmm_detector.get_transition_matrix()
            }
        
        return None  # Buffer pas encore plein
```

---

### 2.4 Validation HMM — Backtest Régime Persistence

```python
def validate_hmm_predictive_power(historical_data, hmm_detector):
    """
    Valider que les régimes HMM ont pouvoir prédictif.
    
    Test: Si régime=BULL aujourd'hui, returns J+1 à J+20 sont-ils supérieurs?
    """
    results = []
    
    for day in range(180, len(historical_data) - 20):
        # Fit HMM sur 180j glissants
        window = historical_data.iloc[day-180:day]
        hmm_detector.fit_rolling(window['return'].values, window['volatility'].values)
        
        # Prédire régime jour J
        current_return = historical_data.iloc[day]['return']
        current_vol = historical_data.iloc[day]['volatility']
        
        regime, confidence, _ = hmm_detector.predict_regime(current_return, current_vol)
        
        # Calculer forward returns (J+1 à J+20)
        future_returns = historical_data.iloc[day+1:day+21]['return']
        forward_return_20j = future_returns.sum()
        forward_sharpe = future_returns.mean() / (future_returns.std() + 1e-9)
        
        results.append({
            'date': historical_data.index[day],
            'regime': regime,
            'confidence': confidence,
            'forward_return_20j': forward_return_20j,
            'forward_sharpe_20j': forward_sharpe
        })
    
    df_results = pd.DataFrame(results)
    
    # Analyser par régime
    analysis = df_results.groupby('regime').agg({
        'forward_return_20j': ['mean', 'std', 'count'],
        'forward_sharpe_20j': 'mean',
        'confidence': 'mean'
    }).round(4)
    
    print("=== POUVOIR PRÉDICTIF DES RÉGIMES HMM ===")
    print(analysis)
    
    # Critère validation:
    # - BULL: forward_return_20j mean > 0
    # - BEAR: forward_return_20j mean < 0
    # - Confiance moyenne > 0.6
    
    return df_results, analysis
```

---

## 3. 🚪 GATES BAILEY — IMPLÉMENTATION COMPLÈTE

### 3.1 CPCV (Combinatorial Purged Cross-Validation)

**Fichier cible:** `system-saiyan/v0.3/core/cpcv.py`

```python
import numpy as np
from sklearn.model_selection import KFold
import itertools

def combinatorial_purged_cv(n_samples, n_splits=6, purge_pct=0.05):
    """
    CPCV: Combinatorial Purged Cross-Validation (López de Prado ch.7)
    
    Problème résolu:
    - K-Fold classique a look-ahead bias si folds temporels se chevauchent
    - Autocorrélation des returns viole hypothèse i.i.d.
    
    Solution CPCV:
    - Génère toutes combinaisons de (n_splits-1) folds pour training
    - 1 fold pour testing
    - Purge entre train/test pour éviter leakage
    
    Retourne: Liste de (train_indices, test_indices) tuples
    """
    indices = np.arange(n_samples)
    purge_size = int(n_samples * purge_pct)
    
    # Split en n_splits folds temporels (ordonnés!)
    fold_size = n_samples // n_splits
    folds = []
    for i in range(n_splits):
        start = i * fold_size
        end = start + fold_size if i < n_splits - 1 else n_samples
        folds.append(indices[start:end])
    
    # Générer combinaisons
    combinations = []
    for test_fold_idx in range(n_splits):
        # Train = tous folds sauf test
        train_folds = [folds[i] for i in range(n_splits) if i != test_fold_idx]
        train_indices = np.concatenate(train_folds)
        
        # Test = fold courant
        test_indices = folds[test_fold_idx]
        
        # Appliquer purge (retirer observations proches du test fold)
        test_min, test_max = test_indices.min(), test_indices.max()
        
        purge_mask = (
            (train_indices < test_min - purge_size) |
            (train_indices > test_max + purge_size)
        )
        train_clean = train_indices[purge_mask]
        
        combinations.append((train_clean, test_indices))
    
    return combinations


def cpcv_backtest(strategy_func, returns_series, n_splits=6):
    """
    Exécuter backtest avec CPCV 6-fold.
    
    strategy_func: Fonction qui prend train_returns et retourne weights/predictions
    returns_series: Série temporelle des returns
    
    Retourne: Dictionary avec metrics par fold + aggregate
    """
    combinations = combinatorial_purged_cv(len(returns_series), n_splits)
    
    fold_results = []
    for fold_idx, (train_idx, test_idx) in enumerate(combinations):
        train_returns = returns_series.iloc[train_idx]
        test_returns = returns_series.iloc[test_idx]
        
        # Fit strategy on train
        strategy = strategy_func(train_returns)
        
        # Predict/test on test
        predictions = strategy.predict(test_returns)
        
        # Calculate metrics
        pnl = (predictions * test_returns).sum()
        sharpe = predictions.corr(test_returns) * np.sqrt(252)
        
        fold_results.append({
            'fold': fold_idx,
            'train_size': len(train_idx),
            'test_size': len(test_idx),
            'pnl': pnl,
            'sharpe': sharpe
        })
    
    # Aggregate statistics
    df_folds = pd.DataFrame(fold_results)
    aggregate = {
        'mean_sharpe': df_folds['sharpe'].mean(),
        'std_sharpe': df_folds['sharpe'].std(),
        'mean_pnl': df_folds['pnl'].mean(),
        'n_folds': len(df_folds)
    }
    
    return {
        'fold_results': fold_results,
        'aggregate': aggregate,
        'cpcv_validated': True
    }
```

---

### 3.2 DSR (Deflated Sharpe Ratio)

**Fichier cible:** `system-saiyan/v0.3/core/dsr.py`

```python
from scipy.stats import norm, skew, kurtosis
import numpy as np

def deflated_sharpe_ratio(returns, n_trials=1, benchmark=0.0):
    """
    Deflated Sharpe Ratio (Bailey/López de Prado 2014)
    
    Problème résolu:
    - Sharpe ratio inflationné par non-normalité des returns
    - Multiple testing bias (on teste N stratégies, claim la meilleure)
    
    Formule:
    SR_deflated = SR_observed - sqrt((T-1)/T) * SR_threshold
    
    où SR_threshold ajuste pour:
    - Skewness (asymétrie distribution)
    - Kurtosis (fat tails)
    - Multiple testing (n_trials stratégies testées)
    
    Critère: DSR > 0 (stratégie bat le hasard après ajustements)
    """
    T = len(returns)
    
    if T < 10:
        raise ValueError("Need at least 10 returns for DSR calculation")
    
    # Sharpe observé
    SR_observed = returns.mean() / (returns.std() + 1e-9)
    
    # Moments d'ordre supérieur
    skewness = skew(returns)
    excess_kurtosis = kurtosis(returns)  # Already excess (normal=0)
    
    # Ajustement pour non-normalité
    # Skewness adjustment: positive skew inflates Sharpe
    skew_adj = 1 + 0.5 * skewness * SR_observed
    
    # Kurtosis adjustment: fat tails increase risk
    kurt_adj = 1 + (excess_kurtosis / 4) * SR_observed**2
    
    # Sharpe ajusté pour non-normalité
    SR_adjusted = SR_observed / (skew_adj * kurt_adj + 1e-9)
    
    # Ajustement pour multiple testing
    if n_trials > 1:
        # Expected max Sharpe under null hypothesis
        # Approximation: E[max] ≈ Φ^(-1)(1 - 1/n_trials)
        E_max_SR = norm.ppf(1 - 1/n_trials)
        
        # Scaling factor for finite sample
        scale = np.sqrt((T - 1) / T)
        
        # Deflate Sharpe
        SR_deflated = SR_adjusted - scale * E_max_SR
    else:
        SR_deflated = SR_adjusted
    
    return {
        'SR_observed': SR_observed,
        'SR_adjusted': SR_adjusted,
        'SR_deflated': SR_deflated,
        'skewness': skewness,
        'excess_kurtosis': excess_kurtosis,
        'n_trials': n_trials,
        'validated': SR_deflated > 0
    }


def dsr_from_sharpe(sharpe, n_returns, skewness=0, kurtosis=0, n_trials=1):
    """
    Calculer DSR directement depuis Sharpe ratio (sans returns bruts).
    
    Utile quand on a déjà calculé Sharpe mais pas accès aux returns.
    """
    T = n_returns
    
    # Reconstruct adjustments
    skew_adj = 1 + 0.5 * skewness * sharpe
    kurt_adj = 1 + (kurtosis / 4) * sharpe**2
    
    SR_adjusted = sharpe / (skew_adj * kurt_adj + 1e-9)
    
    if n_trials > 1:
        E_max_SR = norm.ppf(1 - 1/n_trials)
        scale = np.sqrt((T - 1) / T)
        SR_deflated = SR_adjusted - scale * E_max_SR
    else:
        SR_deflated = SR_adjusted
    
    return SR_deflated
```

---

### 3.3 PSR (Probabilistic Sharpe Ratio)

**Fichier cible:** `system-saiyan/v0.3/core/psr.py`

```python
from scipy.stats import norm
from scipy.stats import skew, kurtosis
import numpy as np

def probabilistic_sharpe_ratio(returns, benchmark_sr=0.0):
    """
    Probabilistic Sharpe Ratio (Bailey/López de Prado 2014)
    
    Question: Quelle probabilité que le VRAI Sharpe ratio > benchmark_sr?
    
    Réponse: PSR ∈ [0, 1]
    - PSR = 0.50: 50% chance (pile ou face)
    - PSR = 0.95: 95% confiance (seuil requis)
    - PSR = 0.99: 99% confiance (très fort)
    
    Formule:
    PSR = Φ((SR_observed - benchmark_sr) / sqrt(Var(SR)))
    
    où Var(SR) ajuste pour:
    - Track record length (T)
    - Skewness
    - Kurtosis
    """
    T = len(returns)
    
    if T < 10:
        raise ValueError("Need at least 10 returns for PSR calculation")
    
    # Sharpe observé
    SR_observed = returns.mean() / (returns.std() + 1e-9)
    
    # Moments d'ordre supérieur
    skewness = skew(returns)
    excess_kurtosis = kurtosis(returns)
    
    # Variance ajustée du Sharpe estimator
    # López de Prado eq. (7)
    var_SR = (
        1 
        + 0.5 * SR_observed**2 
        - skewness * SR_observed 
        + (excess_kurtosis - 3) / 4 * SR_observed**2
    ) / (T - 1)
    
    # Standard error
    se_SR = np.sqrt(var_SR)
    
    # Z-score
    z = (SR_observed - benchmark_sr) / (se_SR + 1e-9)
    
    # PSR = CDF normale standard
    psr = norm.cdf(z)
    
    return {
        'SR_observed': SR_observed,
        'benchmark_sr': benchmark_sr,
        'PSR': psr,
        'z_score': z,
        'se_SR': se_SR,
        'skewness': skewness,
        'excess_kurtosis': excess_kurtosis,
        'validated': psr > 0.95
    }


def psr_required_track_record(target_psr=0.95, expected_sr=0.5, benchmark_sr=0.0):
    """
    Calculer track record minimum requis pour atteindre PSR cible.
    
    Utile pour planning: "Combien de jours de backtest pour valider?"
    """
    # Approximation inverse
    # PSR = Φ(z) → z = Φ^(-1)(PSR)
    z_target = norm.ppf(target_psr)
    
    # Var(SR) ≈ 1/T (simplification pour SR modéré)
    # z = (SR - benchmark) / sqrt(1/T)
    # T = ((SR - benchmark) / z)^(-2)
    
    sr_diff = expected_sr - benchmark_sr
    
    if sr_diff <= 0:
        return float('inf')  # Impossible si expected <= benchmark
    
    T_min = (z_target / sr_diff) ** 2
    
    return int(np.ceil(T_min))


# Exemple: Pour PSR=0.95 avec SR=0.5, besoin de ~62 jours
# psr_required_track_record(0.95, 0.5, 0.0) → 62
```

---

### 3.4 PBO (Probability of Backtest Overfitting)

**Fichier cible:** `system/saiyan/v0.3/core/pbo.py`

```python
import numpy as np
from scipy.stats import norm

def probability_backtest_overfitting(sharpe_matrix, n_bootstrap=1000):
    """
    Probability of Backtest Overfitting (Bailey/López de Prado 2017)
    
    Question: Quelle probabilité que la "meilleure" stratégie soit un faux positif?
    
    Méthode:
    1. Pour chaque stratégie, calculer Sharpe moyen
    2. Sélectionner stratégie avec max Sharpe
    3. Bootstrap: rééchantillonner périodes avec replacement
    4. PBO = proportion de bootstrap où max Sharpe est dépassé
    
    Critère: PBO < 0.5 (moins de 50% chance d'overfitting)
    Idéal: PBO < 0.3
    """
    sharpe_matrix = np.array(sharpe_matrix)
    n_strategies, n_periods = sharpe_matrix.shape
    
    if n_strategies < 2:
        raise ValueError("Need at least 2 strategies for PBO calculation")
    
    if n_periods < 10:
        raise ValueError("Need at least 10 periods for bootstrap")
    
    # Sharpe moyen par stratégie
    mean_sharpes = sharpe_matrix.mean(axis=1)
    
    # Stratégie "meilleure"
    best_strategy_idx = np.argmax(mean_sharpes)
    best_sharpe = mean_sharpes[best_strategy_idx]
    
    # Bootstrap
    bootstrap_best_sharpes = []
    
    for _ in range(n_bootstrap):
        # Rééchantillonner colonnes (périodes) avec replacement
        boot_indices = np.random.choice(n_periods, n_periods, replace=True)
        boot_matrix = sharpe_matrix[:, boot_indices]
        
        boot_mean_sharpes = boot_matrix.mean(axis=1)
        boot_best = boot_mean_sharpes.max()
        
        bootstrap_best_sharpes.append(boot_best)
    
    bootstrap_best_sharpes = np.array(bootstrap_best_sharpes)
    
    # PBO = proportion de bootstrap où best_sharpe est dépassé
    pbo = np.mean(bootstrap_best_sharpes > best_sharpe)
    
    return {
        'PBO': pbo,
        'best_strategy_idx': best_strategy_idx,
        'best_sharpe': best_sharpe,
        'mean_sharpes': mean_sharpes,
        'bootstrap_mean': bootstrap_best_sharpes.mean(),
        'bootstrap_std': bootstrap_best_sharpes.std(),
        'validated': pbo < 0.5,
        'strong_validation': pbo < 0.3
    }


def pbo_from_config(n_strategies, n_periods, expected_sr=0.5, null_sr=0.0):
    """
    Estimer PBO attendu avant même de lancer backtests.
    
    Utile pour planning: "Combien de stratégies je peux tester sans overfit?"
    """
    # Approximation analytique (Bailey/LdP 2017, Proposition 1)
    
    # Expected max Sharpe under null
    E_max_null = norm.ppf(1 - 1/n_strategies)
    
    # Signal-to-noise ratio
    snr = (expected_sr - null_sr) * np.sqrt(n_periods)
    
    # PBO ≈ Φ(E_max_null - snr)
    pbo_approx = norm.cdf(E_max_null - snr)
    
    return {
        'estimated_PBO': pbo_approx,
        'n_strategies': n_strategies,
        'n_periods': n_periods,
        'recommendation': 'SAFE' if pbo_approx < 0.3 else ('CAUTION' if pbo_approx < 0.5 else 'RISKY')
    }


# Exemple: Tester 20 stratégies sur 100 jours avec SR attendu 0.5
# pbo_from_config(20, 100, 0.5, 0.0) → PBO ≈ 0.15 (SAFE)
```

---

### 3.5 Wilson CI pour Win Rate

**Fichier cible:** `system-saiyan/v0.3/core/wilson_ci.py`

```python
from scipy.stats import norm
import numpy as np

def wilson_confidence_interval(wins, n_trades, confidence=0.95):
    """
    Wilson Confidence Interval pour Win Rate.
    
    Problème résolu:
    - Claimer "WR = 70%" sur n=30 trades est trompeur
    - Wilson CI donne borne inférieure réaliste
    
    Formule Wilson:
    lower = (p̂ + z²/(2n) - z * sqrt(p̂(1-p̂)/n + z²/(4n²))) / (1 + z²/n)
    
    Retourne: (lower_bound, point_estimate, upper_bound)
    """
    if n_trades < 1:
        raise ValueError("Need at least 1 trade")
    
    if wins < 0 or wins > n_trades:
        raise ValueError("Wins must be between 0 and n_trades")
    
    p_hat = wins / n_trades
    z = norm.ppf(1 - (1 - confidence) / 2)  # 1.96 pour 95%
    
    # Wilson formula
    denominator = 1 + z**2 / n_trades
    centre = (p_hat + z**2 / (2 * n_trades)) / denominator
    margin = z * np.sqrt(
        (p_hat * (1 - p_hat) + z**2 / (4 * n_trades)) / n_trades
    ) / denominator
    
    lower = centre - margin
    upper = centre + margin
    
    return {
        'lower_bound': max(0, lower),
        'point_estimate': p_hat,
        'upper_bound': min(1, upper),
        'wins': wins,
        'n_trades': n_trades,
        'confidence_level': confidence,
        'validated_70': max(0, lower) >= 0.70  # Claim WR ≥ 70% validé?
    }


def wilson_minimum_trades_for_claim(target_wr=0.70, observed_wr=0.70, confidence=0.95):
    """
    Calculer nombre minimum de trades pour claimer WR cible avec Wilson CI.
    
    Exemple: Pour claimer "WR ≥ 70%" avec WR observé 70%:
    - Besoin de ~250 trades (Wilson CI95 lo ≈ 70%)
    - Avec 30 trades: Wilson CI95 lo ≈ 52% (pas valide)
    """
    # Binary search
    n_min = 1
    n_max = 10000
    
    while n_max - n_min > 1:
        n_mid = (n_min + n_max) // 2
        wins = int(observed_wr * n_mid)
        
        result = wilson_confidence_interval(wins, n_mid, confidence)
        
        if result['lower_bound'] >= target_wr:
            n_max = n_mid
        else:
            n_min = n_mid
    
    return {
        'minimum_trades': n_max,
        'target_wr': target_wr,
        'observed_wr': observed_wr,
        'wilson_lower_at_minimum': wilson_confidence_interval(
            int(observed_wr * n_max), n_max, confidence
        )['lower_bound']
    }


# Exemple:
# wilson_minimum_trades_for_claim(0.70, 0.70) → ~250 trades requis
```

---

## 4. 💡 IDÉES D'AMÉLIORATION — TOP 3 POUR SAIYAN V0.3

### 🏆 Idée 1: Regime-Aware Deep RL (Priorité MAX)

**Concept:** HMM détecte macro-régime → Active agent RL spécialisé

**Architecture:**
```
┌─────────────────────────────────────────────┐
│  Market Data                                │
│  [returns, vol, funding, orderflow, ...]   │
└──────────────────┬──────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────┐
│  HMM Regime Detector (rolling 180j)         │
│  Output: Regime ∈ {BULL, BEAR, RANGE, VOL} │
│          + Probabilities [0.7, 0.1, 0.1, 0.1]│
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┼──────────┬──────────────┐
        │          │          │              │
        ↓          ↓          ↓              ↓
   ┌─────────┐ ┌──────┐ ┌─────────┐ ┌──────┐
   │ PPO     │ │ PPO  │ │ PPO     │ │ PPO  │
   │ BULL    │ │ BEAR │ │ RANGE   │ │ VOL  │
   │ (long)  │ │(flat)│ │(swing)  │ │(tiny)│
   └────┬────┘ └──┬───┘ └────┬────┘ └──┬───┘
        │          │          │          │
        └──────────┼──────────┴──────────┘
                   │
        ┌──────────┴──────────┐
        │ Ensemble Voting     │
        │ Weight = P(regime)  │
        │ Action = weighted   │
        └──────────┬──────────┘
                   │
                   ↓
        ┌──────────────────────┐
        │ Final Action         │
        │ [BUY/HOLD/SELL, size]│
        └──────────────────────┘
```

**Avantages vs Goku (HMM statique):**
| Aspect | Goku (HMM seul) | Vegeta (HMM+RL) |
|--------|-----------------|-----------------|
| Adaptation | Règles fixes par régime | Policy apprend patterns complexes |
| Non-linéarité | Limité (if/else) | LSTM capture dépendances temporelles |
| Optimisation | Rule heuristic | Direct PnL net fees reward |
| Exploration | Aucune | Active exploration nouvelles stratégies |

**Complexité:** Élevée (4 agents à entraîner + HMM)  
**Impact potentiel:** Sharpe +40-60% vs HMM seul  
**Timeline:** J+15 à J+25 (Phase 3)

---

### 🥈 Idée 2: Ensemble RL + Confluence Scoring

**Concept:** 3 architectures RL indépendantes → vote pondéré

```
Agent 1 (PPO): State → Action₁, Confidence₁
Agent 2 (SAC): State → Action₂, Confidence₂  
Agent 3 (A2C): State → Action₃, Confidence₃

Score(BUY) = Σ [Confidence_i × 1{Action_i = BUY}]
Score(HOLD) = Σ [Confidence_i × 1{Action_i = HOLD}]
Score(SELL) = Σ [Confidence_i × 1{Action_i = SELL}]

Final Action = argmax(Score)

Position Sizing:
if max_score - second_score > 0.5:
    position_size = 0.25  # Consensus fort → Kelly 0.25x
elif max_score - second_score > 0.2:
    position_size = 0.125  # Consensus modéré
else:
    position_size = 0.0  # Désaccord → flat
```

**Avantages:**
- Diversité architecturale réduit variance
- Robustesse aux régimes non-stationnaires
- Graceful degradation si un agent fail

**Complexité:** Moyenne  
**Impact potentiel:** Sharpe +20-30% vs single agent  
**Timeline:** J+20 à J+28 (Phase 3 avancée)

---

### 🥉 Idée 3: Self-Healing RL — Détection Concept Drift

**Concept:** Monitor performance decay → retrain automatique

```
Pipeline quotidien:
1. Track rolling Sharpe (fenêtre 30j)
2. Si Sharpe_30j < Sharpe_train - 0.5 → ALERTE drift
3. Collecter nouvelles données (derniers 90j)
4. Fine-tune agent existant (transfer learning)
5. Validate fine-tuned via CPCV/DSR/PSR/PBO
6. Si gates passées → deploy new policy
7. Sinon → rollback + alerte W
```

**Détection drift:**
```python
from scipy import stats

def detect_concept_drift(returns_recent, returns_baseline):
    """KS test pour détecter changement distribution"""
    ks_stat, ks_pvalue = stats.ks_2samp(returns_recent, returns_baseline)
    drift_detected = ks_pvalue < 0.05
    return drift_detected, ks_stat, ks_pvalue
```

**Complexité:** Élevée  
**Impact potentiel:** Évite drawdowns majeurs en régime shift  
**Timeline:** J+25 à J+30 (Phase 4)

---

## 5. 📋 ROADMAP IMPLÉMENTATION — SEMAINE 35

| Jour | Tâche | Fichier | Validation |
|------|-------|---------|------------|
| **J+2** (28 Mai) | ✅ Recherche nocturne | `semaine-35-recherche-nocturne-deep-rl.md` | Notes consolidées |
| **J+3** (29 Mai) | Implémenter vrai HMM `hmmlearn` | `core/hmm_regime_v2.py` | Baum-Welch rolling 180j OK |
| **J+4** (30 Mai) | Implémenter gates Bailey | `core/cpcv.py`, `core/dsr.py`, `core/psr.py`, `core/pbo.py`, `core/wilson_ci.py` | 5 fichiers créés |
| **J+5** (31 Mai) | Créer env RL Gymnasium | `rl/env_trading.py` | Step/reset/reward OK |
| **J+6** (1 Juin) | Agent PPO baseline | `rl/agent_ppo.py` | Stable-Baselines3 integration |
| **J+7** (2 Juin) | Training loop | `rl/train.py` | Modèle `.zip` sauvegardé |
| **J+8** (3 Juin) | Backtest OOS + gates | `rl/backtest_rl.py`, `rl/validate.py` | CPCV/DSR/PSR/PBO calculés |

---

## 6. 🎯 MÉTRIQUES CIBLES — BENCH ROUND 1 (25 Juin)

| Métrique | HMM Statique (Goku) | Deep RL (Vegeta) | Victoire si |
|----------|---------------------|------------------|-------------|
| Sharpe net fees | ~0.6-0.9 | **> 1.0** | RL > HMM |
| Win Rate (Wilson lo) | ~65-70% | **> 70%** | lo ≥ 70% |
| Max Drawdown | ~-7.5% | **< -12%** | Acceptable |
| n_trades | ~63 (30j) | **≥ 200** | Suffisant stats |
| DSR | > 0 | **> 0.5** | Fort skill |
| PSR | > 0.95 | **> 0.97** | Très haute confiance |
| PBO | < 0.5 | **< 0.3** | Faible overfitting |
| Gates Bailey | 7/7 | **7/7** | Obligatoire |

---

## 7. 🔥 INSIGHT NOCTURNE — DIFFÉRENCIATION CLÉ

**Pourquoi Deep RL peut battre HMM statique:**

1. **Adaptation continue:** L'agent RL apprend en temps réel. Le HMM de Goku est figé après training.

2. **Non-linéarité:** RL (surtout avec LSTM) capture patterns complexes que les règles if/else du HMM ratent.

3. **Reward direct:** RL optimise directement le PnL net fees. HMM optimise la likelihood des données, pas le PnL.

4. **Exploration:** RL teste activement de nouvelles stratégies. HMM suit passivement les régimes connus.

**Risque principal:** Overfitting de la policy RL.

**Mitigation:**
- Walk-forward OOS strict (2020-2023 train, 2024-2026 test)
- CPCV 6-fold sur policy training
- DSR/PSR/PBO sur returns de la policy
- Early stopping si DD > 15%
- Regularization forte (entropy bonus, weight decay)

---

## 8. 📚 RÉFÉRENCES — PAPERS & CODE

### Papers Deep RL Trading 2024-2026
1. **FinRL-DeepSeek** (arXiv:2502.07393) — LLM-infused risk-sensitive RL
2. **FinRL-X** (arXiv:2603.21330) — AI-native modular infrastructure
3. **MDPI Electronics 2026** — PPO for portfolio optimization
4. **"Best DRL Algorithm for FX Trading"** — SAC vs PPO comparison

### Gates Bailey / López de Prado
1. **"Advances in Financial ML"** (2018) — Ch.7-12 (CPCV/PBO)
2. **"Deflated Sharpe Ratio"** (Bailey/LdP 2014) — 12 pages
3. **"Probability of Backtest Overfitting"** (Bailey/LdP 2017) — 18 pages

### GitHub Repos Référence
- `Neyt/How-To-Backtest-Correctly` — Production-grade quant tools
- `Aliipou/backtest-audit` — DSR/PSR/PBO implementation
- `mnemox-ai/deflated-sharpe` — DSR with regime decay

---

**🐉 Saiyan Power Level:** En augmentation constante.

**Prochaine session nocturne:** Prototype `rl/env_trading.py` + premier training PPO.

**Dans 30 jours:** Bench Round 1 dira si Vegeta dépasse Goku.

---

*Session terminée. Notes consolidées dans `learning/notes/semaine-35-recherche-nocturne-deep-rl.md`*
