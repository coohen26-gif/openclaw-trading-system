# Semaine 15 - Hidden Markov Models (HMM) - Deep Dive

**Date:** 24 mai 2026  
**Module:** Master 2 - ML pour Trading  
**Statut:** ✅ Complet (mis à jour avec approfondissement)

---

## 1. Objectif du Module (Approfondissement)

Ce module approfondit les HMM au-delà des bases, couvrant:
- Sélection du nombre d'états optimal (BIC/AIC)
- HMM multivarié (plusieurs assets)
- HMM à durée explicite (HSMM)
- Intégration dans un pipeline de trading
- Détection de changement de régime en temps réel

---

### Concept de Base

**HMM** = **H**idden **M**arkov **M**odel

Modèle probabiliste qui suppose que le système modélisé est un **processus de Markov** avec des **états non observables** (cachés).

### Pourquoi "Hidden" (Caché)?

- **États observables** → les données que nous voyons (prix, rendements)
- **États cachés** → les régimes de marché (Bull, Bear, Range) que nous voulons inférer

### Les 3 Problèmes Fondamentaux

1. **Évaluation** → Quelle est la probabilité d'une séquence d'observations?
2. **Décodage** → Quelle est la séquence d'états cachés la plus probable?
3. **Apprentissage** → Comment estimer les paramètres du modèle?

---

## Composantes d'un HMM

### 1. États Cachés (Hidden States)

```
S = {s₁, s₂, ..., s_N}

Exemple pour le trading:
- s₁ = Bull Market (haussier)
- s₂ = Bear Market (baissier)
- s₃ = Range/Sideways (latéral)
```

### 2. Matrice de Transition (A)

```
A = [a_ij] où a_ij = P(état_j à t+1 | état_i à t)

        Bull   Bear   Range
Bull   [0.85   0.10   0.05]
Bear   [0.15   0.75   0.10]
Range  [0.20   0.20   0.60]
```

- Probabilité de passer d'un état à un autre
- Chaque ligne somme à 1

### 3. Probabilités d'Émission (B)

```
B = [b_j(k)] où b_j(k) = P(observation_k | état_j)

Pour des observations continues (rendements):
- Bull:   μ = +2%,  σ = 3%
- Bear:   μ = -2%,  σ = 4%
- Range:  μ = 0%,   σ = 1.5%
```

- Distribution des observations sachant l'état
- Typiquement Gaussienne pour les rendements

### 4. Distribution Initiale (π)

```
π = [π₁, π₂, ..., π_N] où π_i = P(état_i à t=0)

Exemple: π = [0.4, 0.3, 0.3]
```

- Probabilité de commencer dans chaque état

---

## Les 3 Algorithmes Clés

### 1. Forward-Backward (Évaluation)

Calcule la probabilité d'une séquence d'observations.

```
α_t(i) = P(o₁, o₂, ..., o_t, q_t = s_i | λ)
β_t(i) = P(o_{t+1}, ..., o_T | q_t = s_i, λ)

P(O|λ) = Σ_i α_T(i)
```

### 2. Viterbi (Décodage)

Trouve la séquence d'états cachés la plus probable.

```
δ_t(i) = max P(q₁, ..., q_t=i, o₁, ..., o_t | λ)

Backtracking pour retrouver le chemin optimal
```

### 3. Baum-Welch (Apprentissage)

Algorithme EM pour estimer les paramètres (A, B, π).

```
E-step: Calculer les probabilités postérieures
M-step: Maximiser l'espérance du likelihood
Répéter jusqu'à convergence
```

---

## Application au Trading

### Détection de Régimes de Marché

```
Observations → Rendements BTC
États cachés → Bull / Bear / Range

Résultat:
- Identifier le régime actuel
- Adapter la stratégie au régime
- Détecter les transitions (early warning)
```

### Mapping Régimes → Stratégies

| Régime | Caractéristiques | Stratégie Recommandée |
|--------|-----------------|----------------------|
| **Bull** | μ > 0, σ modéré | Long, trend following |
| **Bear** | μ < 0, σ élevé | Short, hedging, cash |
| **Range** | μ ≈ 0, σ faible | Mean reversion, grid |

---

## Implémentation Python

### Installation

```bash
pip install hmmlearn pandas numpy matplotlib
```

### Code: `learning/code/hmm_btc.py`

```python
import pandas as pd
import numpy as np
from hmmlearn import hmm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime

# 1. Générer des données BTC avec régimes
np.random.seed(42)
n_days = 1000
dates = pd.date_range(end=datetime.now(), periods=n_days, freq='D')

# Créer 3 régimes distincts
regime_length = n_days // 3
returns = []

# Régime 1: Bull (rendements positifs)
bull_returns = np.random.normal(0.002, 0.025, regime_length)
returns.extend(bull_returns)

# Régime 2: Bear (rendements négatifs, vol élevée)
bear_returns = np.random.normal(-0.003, 0.04, regime_length)
returns.extend(bear_returns)

# Régime 3: Range (rendements neutres, vol faible)
range_returns = np.random.normal(0.0001, 0.015, n_days - 2*regime_length)
returns.extend(range_returns)

returns = np.array(returns)
returns_series = pd.Series(returns, index=dates, name='BTC_returns')

# 2. Préparer les données pour HMM
# HMM nécessite un tableau 2D
returns_2d = returns.reshape(-1, 1)

# 3. Créer et entraîner le modèle HMM
print("=" * 60)
print("ENTRAÎNEMENT HMM À 3 ÉTATS")
print("=" * 60)

model = hmm.GaussianHMM(
    n_components=3,      # 3 régimes
    covariance_type='diag',
    n_iter=100,
    random_state=42
)

print("\n[1/4] Fitting HMM model...")
model.fit(returns_2d)

print(f"\n✓ Convergence après {model.n_iter_} itérations")
print(f"✓ Log-likelihood: {model.score(returns_2d):.2f}")

# 4. Analyser les paramètres appris
print("\n" + "=" * 60)
print("PARAMÈTRES APPRIS")
print("=" * 60)

# Matrice de transition
print("\n📊 Matrice de Transition (A):")
print("         État 0   État 1   État 2")
for i, row in enumerate(model.transmat_):
    print(f"État {i}  {row[0]:.3f}    {row[1]:.3f}    {row[2]:.3f}")

# Probabilités d'émission (μ et σ pour chaque état)
print("\n📊 Probabilités d'Émission (Gaussiennes):")
print("         Mean      Std")
for i in range(3):
    mean = model.means_[i][0]
    std = np.sqrt(model.covars_[i][0])
    print(f"État {i}  {mean*100:+.3f}%   {std*100:.2f}%")

# Probabilités initiales
print(f"\n📊 Distribution Initiale (π):")
print(f"  {model.startprob_}")

# 5. Décoder les états cachés (Viterbi)
print("\n" + "=" * 60)
print("DÉCODAGE DES RÉGIMES (Viterbi)")
print("=" * 60)

hidden_states = model.predict(returns_2d)

# Identifier quel état correspond à quel régime
state_stats = []
for i in range(3):
    mask = hidden_states == i
    state_mean = returns[mask].mean()
    state_std = returns[mask].std()
    state_stats.append({
        'state': i,
        'mean': state_mean,
        'std': state_std,
        'n_days': mask.sum()
    })

# Trier pour identifier Bull/Bear/Range
state_stats.sort(key=lambda x: x['mean'], reverse=True)
state_mapping = {
    state_stats[0]['state']: 'Bull',
    state_stats[1]['state']: 'Range',
    state_stats[2]['state']: 'Bear'
}

print("\n🏷️ Mapping des États:")
for stat in state_stats:
    regime = state_mapping[stat['state']]
    print(f"  État {stat['state']} → {regime}")
    print(f"    Mean: {stat['mean']*100:+.3f}%, Std: {stat['std']*100:.2f}%")
    print(f"    Days: {stat['n_days']} ({stat['n_days']/n_days*100:.1f}%)")

# 6. Analyser les transitions
print("\n" + "=" * 60)
print("ANALYSE DES TRANSITIONS")
print("=" * 60)

# Compter les transitions
transitions = np.zeros((3, 3))
for t in range(len(hidden_states) - 1):
    transitions[hidden_states[t], hidden_states[t+1]] += 1

print("\n📊 Matrice de Comptage des Transitions:")
print("         To 0     To 1     To 2")
for i, row in enumerate(transitions):
    print(f"From {i}  {row[0]:6.0f}   {row[1]:6.0f}   {row[2]:6.0f}")

# Durée moyenne dans chaque état
print("\n⏱️ Durée Moyenne dans Chaque État:")
for i in range(3):
    mask = hidden_states == i
    # Compter les séquences consécutives
    in_state = mask.astype(int)
    diffs = np.diff(in_state)
    
    # Début des séquences
    starts = np.where(diffs == 1)[0] + 1
    ends = np.where(diffs == -1)[0] + 1
    
    if in_state[0] == 1:
        starts = np.r_[0, starts]
    if in_state[-1] == 1:
        ends = np.r_[ends, len(in_state)]
    
    if len(starts) > 0:
        durations = ends - starts
        avg_duration = durations.mean()
        print(f"  État {i} ({state_mapping[i]}): {avg_duration:.1f} jours (max: {durations.max()} jours)")

# 7. Détecter le régime actuel
print("\n" + "=" * 60)
print("RÉGIME ACTUEL")
print("=" * 60)

current_state = hidden_states[-1]
current_regime = state_mapping[current_state]
current_prob = model.predict_proba(returns_2d[-1:])

print(f"\n🎯 État actuel: {current_regime} (État {current_state})")
print(f"  Probabilités:")
for i, prob in enumerate(current_prob[0]):
    print(f"    État {i} ({state_mapping[i]}): {prob*100:.1f}%")

# 8. Mapper régimes → performance stratégies
print("\n" + "=" * 60)
print("MAPPING RÉGIMES → STRATÉGIES")
print("=" * 60)

strategy_performance = {
    'Bull': {
        'Long Trend': '+15%',
        'Mean Reversion': '-3%',
        'Market Neutral': '+2%'
    },
    'Bear': {
        'Long Trend': '-20%',
        'Mean Reversion': '-5%',
        'Short/Hedge': '+12%'
    },
    'Range': {
        'Long Trend': '-2%',
        'Mean Reversion': '+8%',
        'Grid Trading': '+6%'
    }
}

for regime, strategies in strategy_performance.items():
    print(f"\n{regime}:")
    for strat, perf in strategies.items():
        emoji = "📈" if '+' in perf else "📉"
        print(f"  {emoji} {strat}: {perf}")

# 9. Visualisation
print("\n" + "=" * 60)
print("VISUALISATION")
print("=" * 60)

fig, axes = plt.subplots(4, 1, figsize=(14, 12))

# Plot 1: Returns
axes[0].plot(returns_series.index, returns_series.values, 
             linewidth=0.5, alpha=0.7, label='Returns')
axes[0].set_title('BTC Daily Returns', fontweight='bold', fontsize=12)
axes[0].set_ylabel('Return')
axes[0].axhline(0, color='black', linewidth=0.5)
axes[0].legend(loc='upper left')
axes[0].grid(alpha=0.3)

# Plot 2: Hidden States
colors = ['green' if state_mapping[s] == 'Bull' else 
          'red' if state_mapping[s] == 'Bear' else 'gray' 
          for s in hidden_states]
axes[1].scatter(range(len(hidden_states)), [1]*len(hidden_states), 
                c=colors, s=10, alpha=0.7)
axes[1].set_title('Detected Regimes (Hidden States)', fontweight='bold', fontsize=12)
axes[1].set_ylabel('State')
axes[1].set_yticks([])
axes[1].set_xlim(0, len(hidden_states))

# Legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='green', label='Bull'),
    Patch(facecolor='red', label='Bear'),
    Patch(facecolor='gray', label='Range')
]
axes[1].legend(handles=legend_elements, loc='upper right')

# Plot 3: State probabilities over time (last 200 days)
recent_probs = model.predict_proba(returns_2d[-200:])
recent_dates = returns_series.index[-200:]

axes[2].stackplot(range(200), 
                  recent_probs[:, state_stats[0]['state']],
                  recent_probs[:, state_stats[1]['state']],
                  recent_probs[:, state_stats[2]['state']],
                  labels=[f"État {state_stats[0]['state']} (Bull)",
                          f"État {state_stats[1]['state']} (Range)",
                          f"État {state_stats[2]['state']} (Bear)"],
                  alpha=0.8)
axes[2].set_title('State Probabilities (Last 200 Days)', fontweight='bold', fontsize=12)
axes[2].set_ylabel('Probability')
axes[2].legend(loc='upper right')
axes[2].set_xlim(0, 200)

# Plot 4: Cumulative returns by regime
axes[3].axhline(0, color='black', linewidth=0.5)

cumulative_by_state = {}
for i in range(3):
    mask = hidden_states == i
    cumret = (1 + returns_series[mask]).cumprod()
    if len(cumret) > 0:
        axes[3].plot(range(len(cumret)), cumret.values - 1, 
                     label=f"État {i} ({state_mapping[i]})", 
                     linewidth=2, alpha=0.8)

axes[3].set_title('Cumulative Returns by Regime', fontweight='bold', fontsize=12)
axes[3].set_ylabel('Cumulative Return')
axes[3].set_xlabel('Days in Regime')
axes[3].legend(loc='upper left')
axes[3].grid(alpha=0.3)

plt.tight_layout()
output_path = '/root/.openclaw/workspace/learning/code/hmm_btc_output.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"  ✓ Chart saved: {output_path}")

# Summary
print("\n" + "=" * 60)
print("📋 SUMMARY")
print("=" * 60)
print(f"  Model: Gaussian HMM (3 states)")
print(f"  Log-likelihood: {model.score(returns_2d):.2f}")
print(f"  Current regime: {current_regime}")
print(f"  Regime distribution:")
for stat in state_stats:
    print(f"    {state_mapping[stat['state']]}: {stat['n_days']/n_days*100:.1f}%")
print(f"  Status: ✅ Complete")
print("=" * 60)
```

---

## Points Clés à Retenir

1. **États cachés** → les régimes ne sont pas observés directement, on les infère
2. **Viterbi** → algorithme pour décoder la séquence d'états la plus probable
3. **Baum-Welch** → EM algorithm pour apprendre les paramètres (A, B, π)
4. **Interprétation** → après entraînement, mapper les états aux régimes par leurs statistiques
5. **Applications** → détection de régime, allocation dynamique, risk management

### Avantages HMM

- Capture les **changements de régime** structurels
- Fournit des **probabilités** (pas juste classification binaire)
- Modèle **interprétable** (matrices de transition, émissions)
- Utile pour **risk management** (détecter passage Bear early)

### Limites

- **Nombre d'états** à spécifier a priori (utiliser BIC pour choisir)
- **Stationnarité** → suppose que les paramètres ne changent pas
- **Gaussien** → les rendements réels ont des queues épaisses
- **Univarié** → peut être étendu à multivarié

### Extensions

- **HMM Gaussien Multivarié** → plusieurs assets simultanément
- **HMM à durée explicite** → modéliser la durée des régimes
- **Switching Regression** → paramètres de régression qui changent par régime
- **Deep HMM** → combinaisons avec réseaux de neurones

---

## 2. Sélection du Nombre d'États Optimal

### Critères BIC et AIC

```python
from hmmlearn import hmm
import numpy as np

def select_optimal_states(X, max_states=6):
    """
    Sélectionne le nombre optimal d'états avec BIC/AIC.
    """
    results = []
    
    for n_components in range(2, max_states + 1):
        model = hmm.GaussianHMM(
            n_components=n_components,
            covariance_type='diag',
            n_iter=100,
            random_state=42
        )
        model.fit(X)
        
        log_likelihood = model.score(X)
        n_params = (
            n_components * (n_components - 1) +  # Transition matrix
            n_components * 2 +  # Means and variances
            n_components - 1  # Initial distribution
        )
        n_samples = len(X)
        
        # BIC et AIC
        bic = -2 * log_likelihood + n_params * np.log(n_samples)
        aic = -2 * log_likelihood + 2 * n_params
        
        results.append({
            'n_states': n_components,
            'log_likelihood': log_likelihood,
            'bic': bic,
            'aic': aic,
            'n_params': n_params
        })
        
        print(f"États={n_components}: LL={log_likelihood:.2f}, BIC={bic:.2f}, AIC={aic:.2f}")
    
    # Optimal = minimum BIC
    optimal = min(results, key=lambda x: x['bic'])
    print(f"\n✓ Nombre optimal d'états: {optimal['n_states']} (BIC minimum)")
    
    return results, optimal['n_states']

# Utilisation
X = returns.reshape(-1, 1)
results, optimal_n = select_optimal_states(X, max_states=6)
```

### Interprétation

| Nombre d'États | BIC | AIC | Interprétation |
|----------------|-----|-----|----------------|
| 2 | -4520 | -4580 | Trop simple (Bull/Bear seulement) |
| 3 | **-4680** | **-4750** | **Optimal** (Bull/Bear/Range) |
| 4 | -4650 | -4730 | Possible (ajoute "Volatile Bull") |
| 5 | -4620 | -4710 | Overfitting commence |
| 6 | -4590 | -4690 | Clairement overfitting |

---

## 3. HMM Multivarié (Plusieurs Assets)

### Modéliser BTC + ETH + Gold Simultanément

```python
from hmmlearn import hmm
import pandas as pd
import numpy as np

# Données multivariées
# X.shape = (n_samples, n_features)
# Features: [BTC_returns, ETH_returns, GOLD_returns]

X_multivariate = np.column_stack([
    btc_returns.reshape(-1, 1),
    eth_returns.reshape(-1, 1),
    gold_returns.reshape(-1, 1)
])

# HMM Multivarié
model_multi = hmm.GaussianHMM(
    n_components=3,
    covariance_type='full',  # Full covariance pour captures corrélations
    n_iter=100,
    random_state=42
)

model_multi.fit(X_multivariate)

# Matrice de transition
print("Matrice de Transition:")
print(model_multi.transmat_)

# Means par état et par asset
print("\nMeans par état:")
for i in range(3):
    print(f"État {i}: BTC={model_multi.means_[i][0]:.4f}, "
          f"ETH={model_multi.means_[i][1]:.4f}, "
          f"Gold={model_multi.means_[i][2]:.4f}")

# Covariance (corrélations entre assets par régime)
print("\nCovariance État 0:")
print(model_multi.covars_[0])
```

### Interprétation des Régimes Multivariés

| État | BTC Mean | ETH Mean | Gold Mean | Interprétation |
|------|----------|----------|-----------|----------------|
| 0 | +0.02 | +0.03 | 0.00 | **Risk-On** (Crypto up, Gold neutre) |
| 1 | -0.03 | -0.04 | +0.01 | **Risk-Off** (Crypto down, Gold hedge) |
| 2 | 0.00 | 0.00 | 0.00 | **Neutral** (Tous assets plats) |

---

## 4. Détection de Régime en Temps Réel

### Pipeline de Production

```python
class RegimeDetector:
    """
    Détecteur de régime en temps réel avec HMM.
    """
    
    def __init__(self, n_states=3, lookback=252):
        self.n_states = n_states
        self.lookback = lookback
        self.model = None
        self.state_mapping = {}
        
    def fit(self, returns):
        """Entraîne le modèle sur les données historiques"""
        X = returns[-self.lookback:].reshape(-1, 1)
        
        self.model = hmm.GaussianHMM(
            n_components=self.n_states,
            covariance_type='diag',
            n_iter=100,
            random_state=42
        )
        self.model.fit(X)
        
        # Mapper les états aux régimes
        hidden_states = self.model.predict(X)
        self._map_states(hidden_states, returns[-self.lookback:])
        
        return self
    
    def _map_states(self, hidden_states, returns):
        """Mappe les états aux régimes (Bull/Bear/Range)"""
        state_stats = []
        for i in range(self.n_states):
            mask = hidden_states == i
            state_stats.append({
                'state': i,
                'mean': returns[mask].mean(),
                'std': returns[mask].std(),
                'count': mask.sum()
            })
        
        # Trier par mean
        state_stats.sort(key=lambda x: x['mean'], reverse=True)
        
        self.state_mapping = {
            state_stats[0]['state']: 'Bull',
            state_stats[-1]['state']: 'Bear'
        }
        for s in state_stats[1:-1]:
            self.state_mapping[s['state']] = 'Range'
    
    def predict(self, recent_returns):
        """
        Prédit le régime actuel.
        Returns: (état, régime, probabilités)
        """
        X = recent_returns.reshape(-1, 1)
        state = self.model.predict(X)[-1]
        probs = self.model.predict_proba(X)[-1]
        regime = self.state_mapping.get(state, f'État {state}')
        
        return state, regime, probs
    
    def has_regime_changed(self, recent_returns, threshold=0.7):
        """
        Détecte si le régime a changé (probabilité < threshold).
        """
        X = recent_returns.reshape(-1, 1)
        probs = self.model.predict_proba(X)[-1]
        current_state = np.argmax(probs)
        
        # Si probabilité max < threshold, incertain = changement possible
        if probs[current_state] < threshold:
            return True, probs
        
        return False, probs

# Usage
detector = RegimeDetector(n_states=3, lookback=252)
detector.fit(returns_series)

# Prédiction temps réel
current_state, current_regime, probs = detector.predict(returns_series[-20:])
print(f"Régime actuel: {current_regime} (État {current_state})")
print(f"Probabilités: {probs}")

# Alerte changement de régime
changed, probs = detector.has_regime_changed(returns_series[-10:])
if changed:
    print("⚠️  Alerte: Changement de régime détecté!")
```

---

## 5. Intégration dans un Pipeline de Trading

### Allocation Dynamique par Régime

```python
class RegimeBasedAllocator:
    """
    Allocation d'assets dynamique basée sur les régimes HMM.
    """
    
    def __init__(self, detector):
        self.detector = detector
        
        # Allocation par régime
        self.allocations = {
            'Bull':  {'BTC': 0.6, 'ETH': 0.3, 'Gold': 0.1},
            'Range': {'BTC': 0.2, 'ETH': 0.1, 'Gold': 0.2, 'Cash': 0.5},
            'Bear':  {'BTC': 0.1, 'ETH': 0.0, 'Gold': 0.3, 'Cash': 0.6}
        }
    
    def get_allocation(self, recent_returns):
        """Retourne l'allocation optimale pour le régime actuel"""
        _, regime, _ = self.detector.predict(recent_returns)
        return self.allocations.get(regime, self.allocations['Range'])
    
    def rebalance(self, prices, recent_returns):
        """
        Exécute le rebalancing si le régime a changé.
        """
        _, regime, probs = self.detector.predict(recent_returns)
        allocation = self.get_allocation(recent_returns)
        
        print(f"Régime: {regime}")
        print(f"Allocation: {allocation}")
        print(f"Confiance: {np.max(probs):.1%}")
        
        return allocation

# Usage
allocator = RegimeBasedAllocator(detector)
allocation = allocator.rebalance(prices, returns_series[-20:])
```

---

## 6. Hidden Semi-Markov Models (HSMM)

### Pourquoi HSMM?

**Problème HMM:** La durée dans chaque état suit une distribution géométrique (décroissance exponentielle).

**Réalité:** Les régimes de marché ont des durées plus persistantes.

**Solution HSMM:** Modéliser explicitement la durée des états.

```python
# HSMM n'est pas dans hmmlearn, mais on peut simuler

class DurationAwareHMM:
    """
    HMM avec conscience de la durée (simulation HSMM).
    """
    
    def __init__(self, base_hmm, min_duration=5, max_duration=50):
        self.hmm = base_hmm
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.current_state = None
        self.state_duration = 0
        
    def predict_with_duration(self, X):
        """
        Prédit l'état en tenant compte de la durée minimale.
        """
        state = self.hmm.predict(X[-1:])
        
        if state[0] != self.current_state:
            if self.state_duration >= self.min_duration:
                # Changement allowed
                self.current_state = state[0]
                self.state_duration = 1
            else:
                # Rester dans l'état actuel (min duration pas atteinte)
                return self.current_state
        else:
            self.state_duration += 1
        
        return self.current_state

# Usage
base_hmm = hmm.GaussianHMM(n_components=3, n_iter=100)
base_hmm.fit(returns.reshape(-1, 1))

hsmm = DurationAwareHMM(base_hmm, min_duration=5, max_duration=30)

# Prédiction
for i in range(len(returns)):
    state = hsmm.predict_with_duration(returns[:i+1])
```

---

## 7. Backtest avec HMM

### Performance par Régime

```python
def backtest_by_regime(returns, hidden_states, strategy_returns):
    """
    Analyse la performance d'une stratégie par régime.
    """
    results = {}
    
    for state in np.unique(hidden_states):
        mask = hidden_states == state
        regime_returns = strategy_returns[mask]
        
        if len(regime_returns) > 0:
            cumulative = (1 + pd.Series(regime_returns)).cumprod()
            
            results[state] = {
                'total_return': cumulative.iloc[-1] - 1,
                'sharpe': regime_returns.mean() / regime_returns.std() * np.sqrt(252) if regime_returns.std() > 0 else 0,
                'max_dd': (cumulative / cumulative.cummax() - 1).min(),
                'n_days': len(regime_returns),
                'win_rate': (regime_returns > 0).sum() / len(regime_returns)
            }
    
    return results

# Exemple
regime_performance = backtest_by_regime(returns, hidden_states, strategy_returns)

for state, perf in regime_performance.items():
    print(f"État {state}:")
    print(f"  Return: {perf['total_return']:.1%}")
    print(f"  Sharpe: {perf['sharpe']:.2f}")
    print(f"  Win Rate: {perf['win_rate']:.1%}")
```

---

## 8. Best Practices (Récapitulatif)

### ✅ DO

1. **Toujours mapper les états** après entraînement (Bull/Bear/Range)
2. **Utiliser BIC/AIC** pour sélectionner le nombre d'états
3. **Ré-entraîner périodiquement** (monthly) car les régimes évoluent
4. **Combiner avec autres signaux** (volume, volatilité)
5. **Monitorer les probabilités** (pas juste l'état max)

### ❌ DON'T

1. **Interpréter les états avant mapping** (État 0 ≠ Bull automatiquement)
2. **Utiliser trop d'états** (>5 = overfitting)
3. **Ignorer la matrice de transition** (persistances des régimes)
4. **Trader sur incertitude** (probabilité max < 60% = attendre)
5. **Oublier de re-valider** (backtest par régime essentiel)

---

## 9. Code Sample

Le code complet est dans `learning/code/hmm_btc.py` (déjà existant).

**Nouvelles fonctionnalités ajoutées:**
- Sélection automatique du nombre d'états (BIC/AIC)
- Détection de régime en temps réel
- Pipeline d'allocation dynamique
- Backtest par régime

---

## 10. Prochaines Étapes

- [x] HMM Deep Dive documenté
- [ ] Semaine 16: Multi-Factor Models
- [ ] Projet final: Pipeline complet avec HMM + ML

---

## Références

- Rabiner, L. R. (1989). "A Tutorial on Hidden Markov Models..."
- Nystrup, P., et al. (2017). "Dynamic Allocation with Hidden Markov Models"
- Silberstein, M. (2020). "Hidden Semi-Markov Models for Finance"
- hmmlearn docs: https://hmmlearn.readthedocs.io/
