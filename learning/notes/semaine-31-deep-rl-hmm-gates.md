# 📚 Semaine 31 — Deep RL + HMM + Gates Bailey

**Date:** 2026-05-27  
**Session:** Recherche Nocturne Saiyan V0.3  
**Objectif:** Exploration architectures Deep RL, amélioration HMM, gates Bailey

---

## 1. 🧠 DEEP REINFORCEMENT LEARNING POUR TRADING

### 1.1 Pourquoi Deep RL vs HMM Statique?

**HMM (approche Goku/Yagati):**
- Modèle figé après training
- Détecte des régimes, mais n'apprend pas de nouvelles stratégies
- Rule-based à l'intérieur de chaque régime
- **Limite:** Ne s'adapte pas aux changements structurels du marché

**Deep RL (approche Vegeta/Saiyan v0.3):**
- Agent apprend une policy π(a|s) par essai-erreur
- Reward = PnL net fees → optimisation directe
- Capture non-linéarités complexes
- **Avantage:** Adaptation continue, exploration de stratégies nouvelles

---

### 1.2 Architectures Deep RL — Survey 2024-2026

#### **PPO (Proximal Policy Optimization)** 🏆 Recommandé

**Principe:** Policy Gradient avec contrainte de mise à jour progressive

```python
# PPO Clip Objective
L^CLIP(θ) = E[min(r_t(θ) * A_t, clip(r_t(θ), 1-ε, 1+ε) * A_t)]
# où r_t(θ) = π_θ(a_t|s_t) / π_θ_old(a_t|s_t)
```

**Pourquoi PPO pour trading:**
- ✅ Stable training (clip évite les updates trop agressives)
- ✅ Sample efficient (important pour données financières limitées)
- ✅ Gère action spaces continus (position sizing) et discrets (BUY/HOLD/SELL)
- ✅ Moins sensible aux hyperparamètres que TRPO

**Architecture recommandée:**
```
Input: [prix_norm, returns_5j, volatilité, regime_HMM, funding_rate]
  ↓
LSTM(128 units) ← capture temporal dependencies
  ↓
Dense(64, ReLU)
  ↓
Dense(32, ReLU)
  ↓
┌───────────────┬───────────────┐
│ Action Head   │ Value Head    │
│ (softmax 3)   │ (linear 1)    │
│ BUY/HOLD/SELL │ V(s)          │
└───────────────┴───────────────┘
```

**Hyperparamètres typiques:**
- Learning rate: 3e-4 à 1e-3
- Clip ε: 0.1 à 0.2
- Gamma (discount): 0.99 (trading = long-term rewards)
- GAE λ: 0.95
- Batch size: 64-256
- Epochs per batch: 5-10

**Réfs 2024-2026:**
- FinRL-DeepSeek (arXiv:2502.07393) — LLM-infused risk-sensitive RL
- FinRL-X (arXiv:2603.21330) — Modular infrastructure AI-native
- MDPI Electronics 2026 — PPO pour portfolio optimization

---

#### **A2C (Advantage Actor-Critic)**

**Principe:** Version synchrone de A3C, gradient descent sur policy + value

```python
# Loss = Policy Loss + Value Loss + Entropy Bonus
Loss = -log(π(a|s)) * A(s,a) + 0.5 * (V_target - V(s))^2 - β * H(π)
```

**Pourquoi A2C:**
- ✅ Plus simple que PPO (pas de clip, pas de replay buffer)
- ✅ Parallelizable (multiple envs)
- ✅ Bon baseline pour comparer

**Inconvénients vs PPO:**
- ❌ Moins stable (updates plus agressives)
- ❌ Plus sensible au learning rate
- ❌ Performance généralement inférieure à PPO sur tâches complexes

**Quand utiliser A2C:**
- Prototypage rapide (plus simple à implémenter)
- Resource-constrained (moins de mémoire que PPO)
- Benchmarking (comparer PPO vs A2C)

---

#### **SAC (Soft Actor-Critic)** 🎯 Pour Position Sizing Continu

**Principe:** Off-policy + maximum entropy framework

```python
# SAC maximise: E[Σ r_t + α * H(π)]
# α = temperature parameter (auto-tuned dans SAC v2)
```

**Pourquoi SAC pour trading:**
- ✅ **Action space continu** → position sizing précis (0% à 100%)
- ✅ Off-policy → réutilise old data (sample efficient)
- ✅ Maximum entropy → exploration intrinsèque (évite collapse policy)
- ✅ Très stable training

**Architecture SAC:**
```
Policy Network (Actor):
State → LSTM(256) → Dense(128) → μ(s), σ(s) → Action ~ N(μ, σ)

Q Networks (Critics, 2 pour overestimation bias):
State + Action → Dense(256) → Dense(128) → Q1, Q2

Value Network:
State → Dense(256) → Dense(128) → V(s)
```

**Hyperparamètres:**
- Buffer size: 100k-1M transitions
- Batch size: 256
- Target update τ: 0.005
- Alpha initial: 0.2 (auto-tune ensuite)
- Learning rate: 3e-4

**Réf:** "Best DRL Algorithm for FX Trading" — SAC surpasse PPO sur Sharpe ratio en Forex

---

### 1.3 Trading Environment Design (Gymnasium)

```python
import gymnasium as gym
from gymnasium import spaces
import numpy as np

class TradingEnv(gym.Env):
    def __init__(self, df, initial_capital=10000):
        super().__init__()
        self.df = df
        self.initial_capital = initial_capital
        
        # Action space: [action_type, position_size]
        # action_type: 0=SELL, 1=HOLD, 2=BUY
        # position_size: 0.0 à 1.0 (fraction du capital)
        self.action_space = spaces.Tuple((
            spaces.Discrete(3),
            spaces.Box(low=0.0, high=1.0, shape=(1,))
        ))
        
        # Observation space: [prix_norm, returns, vol, regime, funding, balance, position]
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32
        )
        
    def step(self, action):
        action_type, position_size = action
        
        # Exécuter trade
        if action_type == 2:  # BUY
            self.position = position_size[0] * self.capital / self.price
        elif action_type == 0:  # SELL
            self.position = 0
        
        # Calculer reward (PnL net fees)
        pnl = self._calculate_pnl()
        fees = self._calculate_fees(action_type, position_size[0])
        reward = pnl - fees
        
        # Step forward
        self.step_idx += 1
        done = self.step_idx >= len(self.df) or self.capital <= 0
        
        return self._get_obs(), reward, done, False, {}
    
    def _calculate_pnl(self):
        if self.position > 0:
            return self.position * (self.price - self.prev_price)
        return 0
    
    def _calculate_fees(self, action_type, position_size):
        if action_type in [0, 2]:  # BUY ou SELL
            trade_value = position_size * self.capital
            return trade_value * 0.0006  # 0.06% taker fee
        return 0
```

---

### 1.4 Reward Shaping — Critique!

**Mauvais reward:**
```python
reward = price_change  # ← Incite au gambling, ignore risk
```

**Bon reward:**
```python
# Risk-adjusted PnL
pnl = self.capital - self.prev_capital
sharpe_component = pnl / (self.rolling_std + 1e-6)
drawdown_penalty = max(0, self.max_capital - self.capital) / self.max_capital
reward = sharpe_component - 0.5 * drawdown_penalty
```

**Reward engineering avancé:**
```python
def calculate_reward(self, pnl, fees, drawdown, regime):
    # Base: PnL net fees
    base_reward = (pnl - fees) / self.capital
    
    # Bonus: Sharpe-like (penalize volatility)
    volatility_bonus = -abs(pnl) / (self.rolling_vol + 1e-6) * 0.1
    
    # Penalty: Drawdown (risk aversion)
    drawdown_penalty = drawdown * 0.5
    
    # Bonus: Regime-aware (reward different actions per regime)
    regime_bonus = 0
    if regime == 'BULL' and self.position > 0:
        regime_bonus = 0.05
    elif regime == 'BEAR' and self.position == 0:
        regime_bonus = 0.05  # Reward staying flat in bear
    
    return base_reward + volatility_bonus - drawdown_penalty + regime_bonus
```

---

### 1.5 Training Pipeline — Walk-Forward OOS

```
Timeline: 2020-2026 (6 ans)

PHASE TRAIN:
├── 2020-2021: Train PPO agent #1
├── 2021-2022: Train PPO agent #2
└── 2022-2023: Train PPO agent #3

PHASE TEST (OOS strict):
├── 2024: Test agent #1 (jamais vu 2024 pendant training)
├── 2025: Test agent #2
└── 2026 YTD: Test agent #3

GATES BAILEY sur chaque test:
- CPCV 6-fold sur période test
- DSR > 0
- PSR > 0.95
- PBO < 0.5
```

---

## 2. 🔧 AMÉLIORATION HMM BAUM-WELCH ROLLING 180J

### 2.1 État Actuel (Audit v0.2)

**Problème identifié:**
```python
# momentum_hmm.py:114-170
def detect_regime_simple(self, prices, volatility):
    # FAUX HMM! Juste des if/else déguisés
    if momentum > 0 and current_vol < vol_median:
        regime = Regime.BULL
    # ...
```

**Ce qui existe vraiment:**
- ❌ Pas de `hmmlearn`
- ❌ Pas de `GaussianHMM`
- ❌ Pas de fit/predict
- ✅ Juste rule-based classifier

---

### 2.2 Vrai HMM avec `hmmlearn`

**Installation:**
```bash
pip install hmmlearn
```

**Implémentation rolling 180j:**
```python
from hmmlearn import hmm
import numpy as np

class TrueHMMRegimeDetector:
    def __init__(self, n_regimes=3, rolling_window=180):
        self.n_regimes = n_regimes
        self.rolling_window = rolling_window
        self.model = None
        
    def fit_rolling(self, returns, volatility):
        """Fit HMM sur fenêtre rolling 180 jours"""
        # Features: returns + volatility (2D)
        X = np.column_stack([returns, volatility])
        
        if len(X) < self.rolling_window:
            raise ValueError(f"Need at least {self.rolling_window} days")
        
        # Prendre dernières 180 observations
        X_window = X[-self.rolling_window:]
        
        # GaussianHMM avec covariance diagonale (plus stable)
        self.model = hmm.GaussianHMM(
            n_components=self.n_regimes,
            covariance_type='diag',
            n_iter=100,
            random_state=42
        )
        
        self.model.fit(X_window)
        return self.model
    
    def predict_regime(self, current_return, current_volatility):
        """Prédire régime actuel"""
        if self.model is None:
            raise ValueError("Must fit model first")
        
        X_obs = np.array([[current_return, current_volatility]])
        regime = self.model.predict(X_obs)[0]
        
        # Mapper regimes vers labels interprétables
        # (à calibrer post-fit selon means/volatilities)
        regime_map = {
            0: 'BEAR',      # Low returns, high vol
            1: 'BULL',      # High returns, low vol
            2: 'RANGE'      # Neutral returns, medium vol
        }
        
        return regime_map.get(regime, 'UNKNOWN'), self.model.score(X_obs)
    
    def get_regime_probabilities(self, current_return, current_volatility):
        """Probabilités postérieures pour chaque régime"""
        X_obs = np.array([[current_return, current_volatility]])
        log_prob = self.model.score_samples(X_obs)[0]
        return np.exp(log_prob)
```

**Calibration automatique des régimes:**
```python
def calibrate_regime_labels(self, hmm_model):
    """Mapper les états HMM vers labels interprétables"""
    means = hmm_model.means_  # Shape: (n_regimes, 2)
    
    # État avec plus haut mean return + basse vol → BULL
    bull_score = means[:, 0] - means[:, 1]  # return - vol
    bull_state = np.argmax(bull_score)
    
    # État avec plus bas mean return + haute vol → BEAR
    bear_score = means[:, 0] - 2 * means[:, 1]
    bear_state = np.argmin(bear_score)
    
    # État restant → RANGE
    all_states = {0, 1, 2}
    range_state = list(all_states - {bull_state, bear_state})[0]
    
    return {
        bull_state: 'BULL',
        bear_state: 'BEAR',
        range_state: 'RANGE'
    }
```

---

### 2.3 Rolling 180j — Re-fit Quotidien

**Pourquoi 180 jours?**
- Suffisant pour estimer paramètres HMM (≥100 obs)
- Assez récent pour capturer régime actuel
- Compromis stabilité/réactivité

**Pipeline quotidien:**
```python
def daily_regime_update(self, new_data):
    """Mettre à jour HMM chaque jour"""
    # 1. Ajouter nouvelle observation
    self.data_buffer.append(new_data)
    
    # 2. Garder buffer à 180 jours
    if len(self.data_buffer) > 180:
        self.data_buffer.pop(0)
    
    # 3. Re-fit HMM (coût: ~100-200ms)
    returns = np.array([d['return'] for d in self.data_buffer])
    volatility = np.array([d['volatility'] for d in self.data_buffer])
    
    self.hmm_detector.fit_rolling(returns, volatility)
    
    # 4. Prédire régime actuel
    current_regime, confidence = self.hmm_detector.predict_regime(
        new_data['return'], new_data['volatility']
    )
    
    return current_regime, confidence
```

---

### 2.4 Validation HMM — Backtest Régime Persistence

```python
def validate_hmm_regimes(self, historical_data):
    """Valider que les régimes HMM ont du sens"""
    results = []
    
    for day in range(180, len(historical_data)):
        # Fit sur 180j glissants
        window = historical_data[day-180:day]
        hmm.fit(window)
        
        # Prédire régime jour J
        regime, conf = hmm.predict(historical_data[day])
        
        # Calculer performance régime+1 à régime+N
        future_returns = historical_data[day+1:day+21]  # 20j forward
        regime_return = future_returns.mean()
        
        results.append({
            'date': historical_data.index[day],
            'regime': regime,
            'confidence': conf,
            'future_return_20j': regime_return
        })
    
    df_results = pd.DataFrame(results)
    
    # Analyser: Bull → hauts returns? Bear → bas/negatifs returns?
    print(df_results.groupby('regime')['future_return_20j'].mean())
    
    return df_results
```

---

## 3. 🚪 GATES BAILEY — CPCV/DSR/PSR/PBO

### 3.1 CPCV (Combinatorial Purged Cross-Validation)

**Problème avec K-Fold classique:**
- Look-ahead bias si folds se chevauchent temporellement
- Autocorrélation des returns viole hypothèse i.i.d.

**Solution CPCV (López de Prado ch.7):**
```python
from sklearn.model_selection import KFold
import itertools

def combinatorial_purged_cv(n_samples, n_splits=6, purge_pct=0.05):
    """
    CPCV: Génère tous les combinaisons de (n_splits-1) folds pour training,
    1 fold pour testing, avec purge entre train/test.
    """
    indices = np.arange(n_samples)
    
    # Purge: retirer observations autour de chaque split point
    purge_size = int(n_samples * purge_pct)
    
    # Générer toutes les combinaisons
    folds = np.array_split(indices, n_splits)
    
    combinations = []
    for test_idx in range(n_splits):
        train_indices = []
        for i in range(n_splits):
            if i != test_idx:
                train_indices.append(folds[i])
        
        # Appliquer purge
        test_fold = folds[test_idx]
        if len(train_indices) > 0:
            train_concat = np.concatenate(train_indices)
            
            # Retirer observations proches du test fold
            train_clean = apply_purge(train_concat, test_fold, purge_size)
            
            combinations.append((train_clean, test_fold))
    
    return combinations

def apply_purge(train_indices, test_fold, purge_size):
    """Retirer observations dans la zone de purge"""
    test_min, test_max = test_fold.min(), test_fold.max()
    
    purge_mask = (
        (train_indices < test_min - purge_size) |
        (train_indices > test_max + purge_size)
    )
    
    return train_indices[purge_mask]
```

**Implémentation pratique (depuis Yagati):**
```bash
# Copier depuis /opt/yagati/core/cpcv.py
cp /opt/yagati/core/cpcv.py /root/.openclaw/workspace/system-saiyan/v0.3/core/
```

**Validation:**
- 6 splits → C(6,5) = 6 combinaisons
- Chaque observation apparaît dans multiple test folds
- Estimateur non-biaisé de performance OOS

---

### 3.2 DSR (Deflated Sharpe Ratio)

**Problème:** Sharpe ratio inflationné par:
- Non-normalité des returns (skew, kurtosis)
- Track record length insuffisant
- Multiple testing (on teste N stratégies, claim la meilleure)

**Formule DSR (Bailey/LdP 2014):**
```python
from scipy.stats import norm, skew, kurtosis

def deflated_sharpe_ratio(returns, n_trials=1):
    """
    DSR = Sharpe ajusté pour non-normalité + multiple testing
    
    SR_deflated = SR_observed - sqrt((T-1)/T) * SR_threshold
    """
    T = len(returns)
    SR_observed = returns.mean() / (returns.std() + 1e-9)
    
    # Moments d'ordre supérieur
    skewness = skew(returns)
    kurt = kurtosis(returns)  # excess kurtosis
    
    # Ajustement pour non-normalité
    skew_adj = (1 + 0.5 * skewness * SR_observed) 
    kurt_adj = (1 + (kurt - 3) / 4 * SR_observed**2)
    
    SR_adjusted = SR_observed / (skew_adj * kurt_adj)
    
    # Ajustement pour multiple testing (n_trials stratégies testées)
    if n_trials > 1:
        # Expected max Sharpe under null
        E_max_SR = norm.ppf(1 - 1/n_trials)
        SR_adjusted -= E_max_SR * np.sqrt((T-1)/T)
    
    return SR_adjusted

# Critère: DSR > 0 (stratégie bat le hasard après ajustements)
```

**Interprétation:**
- DSR > 0: Stratégie significative (bat null hypothesis)
- DSR < 0: Performance probablement due au chance/multiple testing
- DSR > 0.5: Forte évidence de skill

---

### 3.3 PSR (Probabilistic Sharpe Ratio)

**Question:** Quelle probabilité que le vrai Sharpe > Sharpe threshold (ex: 0)?

**Formule PSR:**
```python
def probabilistic_sharpe_ratio(returns, benchmark_sr=0):
    """
    PSR = Probabilité que vrai Sharpe ratio > benchmark_sr
    
    Retourne valeur entre 0 et 1.
    PSR > 0.95 requis pour validation.
    """
    T = len(returns)
    SR_observed = returns.mean() / (returns.std() + 1e-9)
    
    skewness = skew(returns)
    kurt = kurtosis(returns)
    
    # Variance ajustée du Sharpe estimator
    var_SR = (1 + 0.5 * SR_observed**2 - skewness * SR_observed 
              + (kurt - 3) / 4 * SR_observed**2) / (T - 1)
    
    # Z-score
    z = (SR_observed - benchmark_sr) / np.sqrt(var_SR)
    
    # PSR = CDF normale standard
    psr = norm.cdf(z)
    
    return psr

# Critère: PSR > 0.95 (95% confiance que Sharpe > benchmark)
```

**Interprétation:**
- PSR = 0.50: 50% chance que Sharpe > 0 (pile ou face)
- PSR = 0.95: 95% confiance (seuil requis)
- PSR = 0.99: 99% confiance (très fort)

---

### 3.4 PBO (Probability of Backtest Overfitting)

**Question:** Quelle probabilité que la "meilleure" stratégie soit un faux positif?

**Méthode (Bailey/LdP 2017):**
```python
def probability_backtest_overfitting(sharpe_matrix):
    """
    sharpe_matrix: shape (n_strategies, n_periods)
    Chaque ligne = Sharpe ratios d'une stratégie sur différentes périodes
    
    PBO = Probabilité que la stratégie sélectionnée soit overfittée
    """
    n_strategies, n_periods = sharpe_matrix.shape
    
    # Pour chaque stratégie, calculer Sharpe moyen
    mean_sharpes = sharpe_matrix.mean(axis=1)
    
    # Stratégie "meilleure" = max Sharpe moyen
    best_strategy_idx = np.argmax(mean_sharpes)
    best_sharpe = mean_sharpes[best_strategy_idx]
    
    # Bootstrap: rééchantillonner les périodes
    n_bootstrap = 1000
    bootstrap_best_sharpes = []
    
    for _ in range(n_bootstrap):
        # Rééchantillonner colonnes (périodes) avec replacement
        boot_indices = np.random.choice(n_periods, n_periods, replace=True)
        boot_matrix = sharpe_matrix[:, boot_indices]
        
        boot_mean_sharpes = boot_matrix.mean(axis=1)
        boot_best = boot_mean_sharpes.max()
        
        bootstrap_best_sharpes.append(boot_best)
    
    # PBO = proportion de bootstrap où best_sharpe est dépassé
    pbo = np.mean(np.array(bootstrap_best_sharpes) > best_sharpe)
    
    return pbo

# Critère: PBO < 0.5 (moins de 50% chance d'overfitting)
# Idéal: PBO < 0.3
```

**Interprétation:**
- PBO = 0.10: 10% chance d'overfitting (excellent)
- PBO = 0.50: 50% chance (seuil maximal acceptable)
- PBO = 0.80: 80% chance d'overfitting (stratégie probablement fake)

---

### 3.5 Wilson CI pour Win Rate

**Problème:** Claimer "WR = 70%" sur n=30 trades est trompeur

**Solution:** Wilson Confidence Interval 95%

```python
def wilson_confidence_interval(wins, n_trades, confidence=0.95):
    """
    Calcule borne inférieure du Win Rate avec Wilson CI
    
    Retourne: (lower_bound, point_estimate, upper_bound)
    """
    from scipy.stats import norm
    
    p_hat = wins / n_trades
    z = norm.ppf(1 - (1 - confidence) / 2)  # 1.96 pour 95%
    
    denominator = 1 + z**2 / n_trades
    centre = (p_hat + z**2 / (2 * n_trades)) / denominator
    margin = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n_trades)) / n_trades) / denominator
    
    lower = centre - margin
    upper = centre + margin
    
    return max(0, lower), p_hat, min(1, upper)

# Exemple:
# wins=21, n_trades=30 → WR=70%, mais Wilson CI95 lo = 51.9%
# wins=70, n_trades=100 → WR=70%, Wilson CI95 lo = 60.1%
# wins=210, n_trades=300 → WR=70%, Wilson CI95 lo = 64.5%

# Critère: Wilson CI95 lo ≥ 70% pour claimer "WR ≥ 70%"
```

---

## 4. 💡 IDÉES D'AMÉLIORATION POUR SAIYAN V0.3

### Idée 1: **Regime-Aware Deep RL** 🏆 Top Priorité

**Concept:** Combiner HMM (détection régime) + Deep RL (policy optimale par régime)

**Architecture:**
```
┌─────────────────────────────────────────────┐
│  Input: Market Data                         │
│  [returns, vol, funding, orderflow, ...]   │
└──────────────────┬──────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────┐
│  HMM Regime Detector (rolling 180j)         │
│  Output: Regime ∈ {BULL, BEAR, RANGE, VOL} │
└──────────────────┬──────────────────────────┘
                   │
                   ↓
        ┌──────────┴──────────┬──────────────┐
        │                     │              │
        ↓                     ↓              ↓
┌──────────────┐    ┌──────────────┐  ┌──────────────┐
│ PPO Agent    │    │ PPO Agent    │  │ PPO Agent    │
│ BULL         │    │ BEAR         │  │ RANGE        │
│ (aggressive) │    │ (defensive)  │  │ (neutral)    │
└──────────────┘    └──────────────┘  └──────────────┘
        │                     │              │
        └──────────┬──────────┴──────────────┘
                   │
                   ↓
        ┌──────────────────────┐
        │ Ensemble Voting      │
        │ Weight = P(regime)   │
        └──────────────────────┘
                   │
                   ↓
        ┌──────────────────────┐
        │ Final Action         │
        │ [BUY/HOLD/SELL, size]│
        └──────────────────────┘
```

**Avantages:**
- HMM capture macro-régime (lente évolution)
- RL apprend micro-patterns dans chaque régime
- Meilleure généralisation OOS (chaque agent spécialisé)

**Différenciation vs Goku:**
- Goku: HMM statique → rule-based fixed
- Vegeta: HMM dynamique → RL adaptatif par régime

**Complexité:** Moyenne-Élevée  
**Impact potentiel:** +++ (Sharpe +40-60% vs HMM seul)

---

### Idée 2: **Ensemble RL + Confluence Scoring**

**Concept:** 3 agents RL indépendants → vote pondéré par confiance

**Architecture:**
```
Agent 1 (PPO): State → Action₁, Confidence₁
Agent 2 (SAC): State → Action₂, Confidence₂
Agent 3 (A2C): State → Action₃, Confidence₃

Score(BUY) = Σ [Confidence_i × 1{Action_i = BUY}]
Score(HOLD) = Σ [Confidence_i × 1{Action_i = HOLD}]
Score(SELL) = Σ [Confidence_i × 1{Action_i = SELL}]

Final Action = argmax(Score)
```

**Avantages:**
- Diversité des architectures réduit variance
- Robustesse aux régimes non-stationnaires
- Confidence scoring permet position sizing adaptatif

**Position sizing:**
```python
if max_score - second_score > 0.5:
    # Consensus fort → full position (Kelly 0.25x)
    position_size = 0.25
elif max_score - second_score > 0.2:
    # Consensus modéré → half position
    position_size = 0.125
else:
    # Désaccord → stay flat
    position_size = 0.0
```

**Complexité:** Moyenne  
**Impact potentiel:** ++ (Sharpe +20-30% vs single agent)

---

### Idée 3: **Self-Healing RL — Détection Concept Drift**

**Concept:** Monitor performance decay → retrain agent automatiquement

**Pipeline:**
```
1. Track rolling Sharpe (fenêtre 30j)
2. Si Sharpe_30j < Sharpe_train - 0.5 → ALERTE drift
3. Collecter nouvelles données (derniers 90j)
4. Fine-tune agent existant (transfer learning)
5. Validate fine-tuned via CPCV/DSR/PSR/PBO
6. Si gates passées → deploy new policy
7. Sinon → rollback + alerte W
```

**Détection concept drift:**
```python
def detect_concept_drift(returns_recent, returns_baseline):
    """Test si distribution des returns a changé"""
    from scipy import stats
    
    # KS test (Kolmogorov-Smirnov)
    ks_stat, ks_pvalue = stats.ks_2samp(returns_recent, returns_baseline)
    
    # Si p-value < 0.05 → distributions différentes (drift détecté)
    drift_detected = ks_pvalue < 0.05
    
    return drift_detected, ks_stat, ks_pvalue
```

**Avantages:**
- Adaptation automatique aux changements de marché
- Réduit besoin d'intervention manuelle
- Préserve capital en dégradant gracefully

**Complexité:** Élevée  
**Impact potentiel:** ++ (évite drawdowns majeurs en régime shift)

---

## 5. 📋 PLAN D'ACTION — PHASE 3 (J+15 à J+21)

| Jour | Tâche | Fichier | Validation |
|------|-------|---------|------------|
| J+15 (27 Mai) | ✅ Cette recherche nocturne | `semaine-31-deep-rl-hmm-gates.md` | Notes consolidées |
| J+16 (28 Mai) | Implémenter `rl/env_trading.py` | Gymnasium env | Step/reset/reward OK |
| J+17 (29 Mai) | Implémenter `rl/agent_ppo.py` | Stable-Baselines3 | Training loop OK |
| J+18 (30 Mai) | Entraîner agent sur 2020-2023 | `rl/train.py` | Modèle `.zip` sauvegardé |
| J+19 (31 Mai) | Backtest OOS 2024-2026 | `rl/backtest_rl.py` | PnL net fees calculé |
| J+20 (1 Juin) | Gates Bailey sur RL | `rl/validate.py` | CPCV/DSR/PSR/PBO passés |
| J+21 (2 Juin) | Comparaison RL vs HMM | `notes/rl-vs-hmm.md` | RL > HMM sur Sharpe/WR |

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

---

## 7. 📚 RÉFÉRENCES CLÉS

### Papers Deep RL Trading
1. **FinRL-DeepSeek** (arXiv:2502.07393) — LLM-infused risk-sensitive RL
2. **FinRL-X** (arXiv:2603.21330) — AI-native modular infrastructure
3. **MDPI Electronics 2026** — PPO for portfolio optimization
4. **"Best DRL Algorithm for FX Trading"** — SAC vs PPO vs DQN comparison

### Gates Bailey / López de Prado
1. **"Advances in Financial ML"** (2018) — Ch.7-12 (CPCV/PBO)
2. **"Deflated Sharpe Ratio"** (Bailey/LdP 2014) — 12 pages
3. **"Probability of Backtest Overfitting"** (Bailey/LdP 2017) — 18 pages
4. **"ML for Asset Managers"** (LdP 2020) — Covariance denoising

### GitHub Repos
- `Neyt/How-To-Backtest-Correctly` — Production-grade quant tools
- `Aliipou/backtest-audit` — DSR/PSR/PBO implementation
- `mnemox-ai/deflated-sharpe` — DSR with regime decay
- `denis-mikhalev/reinforcement-learning-trading-agent` — PPO/A2C/SAC

---

## 8. 🔥 INSIGHT NOCTURNE — DIFFÉRENCIATION CLÉ

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

**🐉 Saiyan Power Level:** En augmentation. Dans 30 jours, bench Round 1 dira si Vegeta dépasse Goku.

**Prochaine session nocturne:** Prototype `rl/env_trading.py` + premier training PPO.
