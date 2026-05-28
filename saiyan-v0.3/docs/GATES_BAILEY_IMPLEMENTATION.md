# Gates Bailey - Implémentation Saiyan v0.3

## 🎯 Objectif

Implémenter les 5 gates de robustesse de Bailey & López de Prado pour filtrer les stratégies overfittées et ne garder que les edges statistiquement solides.

## 📚 Références Académiques

1. **Bailey, Borwein, López de Prado, Zhu (2017)** - "The Probability of Backtest Overfitting"
2. **Bailey & López de Prado (2014)** - "The Deflated Sharpe Ratio"
3. **Bailey & López de Prado (2012)** - "The Sharpe Ratio Efficiency of Multi-Strategy Portfolios"
4. **López de Prado (2018)** - "Advances in Financial Machine Learning" (Chapitres 7, 12, 13)

---

## 🔧 Les 5 Gates

### Gate 1: CPCV (Combinatorial Purged Cross-Validation)

**Problème résolu:** Lookahead bias dans la validation croisée traditionnelle.

**Méthode:**
- Split purgé avec embargo autour des boundaries
- Combinaisons multiples de train/test
- Estimation non-biaisée de la performance OOS

**Seuil de passage:** Mean score > 0 sur tous les chemins combinatoires

**Implémentation:** `core/gates_bailey.py::GatesBailey.cpurged_kfold()`

```python
gates = GatesBailey()
splits = gates.cpurged_kfold(X, y, n_splits=5, embargo=0.05)
```

---

### Gate 2: DSR (Deflated Sharpe Ratio)

**Problème résolu:** Multiple testing bias - plus on teste de stratégies, plus on trouve de "bons" résultats par chance.

**Formule:**
```
DSR = SR_observed - E[max(SR) | H0]
```

où E[max(SR)] est l'espérance du maximum Sharpe Ratio sous l'hypothèse nulle.

**Seuil de passage:**
- DSR > 0
- P-value < 0.05

**Implémentation:** `core/gates_bailey.py::GatesBailey.deflated_sharpe_ratio()`

```python
result = gates.deflated_sharpe_ratio(returns, n_trials=10)
if result['passed']:
    print(f"DSR={result['dsr']:.3f}, p-value={result['p_value']:.4f}")
```

---

### Gate 3: PSR (Probability of Sharpe Ratio)

**Problème résolu:** Incertitude statistique sur le vrai Sharpe Ratio.

**Méthode:**
- Calcule la probabilité que SR_vrai > SR_benchmark
- Ajuste pour skewness et kurtosis (non-normalité des returns)

**Formule:**
```
PSR = Φ(Z) où Z = (SR_obs - SR_benchmark) / SE(SR)
```

**Seuil de passage:** PSR > 0.95 (95% confiance)

**Implémentation:** `core/gates_bailey.py::GatesBailey.probability_sharpe_ratio()`

```python
result = gates.probability_sharpe_ratio(
    returns, 
    sr_benchmark=0.5,  # Benchmark agressif
    skewness=-0.5,     # Skewness négative typique
    kurtosis=3.0       # Fat tails
)
```

---

### Gate 4: PBO (Probability of Backtest Overfitting)

**Problème résolu:** Probabilité que la "meilleure" stratégie soit due au hasard.

**Méthode:**
- Modélise la distribution du maximum Sharpe Ratio
- Utilise la distribution Gumbel (Fisher-Tippett) pour les extrêmes

**Seuil de passage:** PBO < 0.10 (< 10% chance d'overfitting)

**Implémentation:** `core/gates_bailey.py::GatesBailey.probability_backtest_overfitting()`

```python
# returns_matrix: N stratégies × T périodes
result = gates.probability_backtest_overfitting(returns_matrix)
print(f"PBO estimate: {result['pbo_estimate']:.2%}")
```

---

### Gate 5: Wilson Score Interval

**Problème résolu:** Incertitude sur la Win Rate avec petit échantillon.

**Méthode:**
- Intervalle de confiance Bayesian-like pour proportions
- Plus robuste que l'intervalle normal pour petits n

**Formule:**
```
Wilson CI = [p̂ + z²/(2n) ± z√(p̂(1-p̂)/n + z²/(4n²))] / (1 + z²/n)
```

**Seuil de passage:** Borne inférieure > 0.50 (target: > 0.70)

**Implémentation:** `core/gates_bailey.py::GatesBailey.wilson_score_interval()`

```python
result = gates.wilson_score_interval(n_wins=70, n_total=100)
print(f"WR: {result['wr_observed']:.1%} [{result['wr_lower']:.1%}, {result['wr_upper']:.1%}]")
```

---

## 📊 Workflow Complet

```python
from core.gates_bailey import GatesBailey

gates = GatesBailey()

# Données de la stratégie
returns = ...  # Série de returns
returns_matrix = ...  # Matrix N×T pour PBO
n_wins = ...
n_trades = ...

# Run toutes les gates
result = gates.run_all_gates(
    returns=returns,
    returns_matrix=returns_matrix,
    n_wins=n_wins,
    n_trades=n_trades,
    sr_benchmark=0.5,
    n_trials=10
)

if result['overall_passed']:
    print("✅ Stratégie validée - Prête pour paper-deploy")
else:
    print(f"❌ Échec gates: {result['gates_failed']}")
```

---

## ⚙️ Configuration des Seuils

Voir `config/gates_thresholds.json` pour les seuils ajustables.

**Recommandations:**
- **Phase research:** Seuils relâchés (exploration)
- **Phase validation:** Seuils stricts (confirmation)
- **Phase production:** Seuils très stricts + monitoring continu

---

## 🧪 Tests Unitaires

```bash
cd /root/.openclaw/workspace/saiyan-v0.3
pytest tests/test_gates_bailey.py -v --cov=core/gates_bailey
```

**Couverture cible:** ≥80%

---

## 🚨 Interprétation des Résultats

| Gate | Résultat | Interprétation | Action |
|------|----------|----------------|--------|
| DSR ❌ | DSR ≤ 0 | Performance due au hasard | Rejeter stratégie |
| PSR ❌ | PSR < 0.95 | Incertitude trop élevée | Collecter plus de données |
| PBO ❌ | PBO > 0.10 | Overfitting probable | Réduire complexité modèle |
| Wilson ❌ | WR_lower < 0.50 | WR pas statistiquement > 50% | Plus de trades nécessaires |
| CPCV ❌ | Mean ≤ 0 | Pas de skill OOS | Revoir features/labels |

---

## 📈 Roadmap d'Amélioration

- [ ] Intégration avec backtest engine Saiyan
- [ ] Calcul automatique n_trials (nombre stratégies testées)
- [ ] Support multi-asset (matrix retours corrélés)
- [ ] Visualisation dashboard des gates
- [ ] Alertes Telegram si gate échoue en production

---

## 🔐 Notes de Sécurité

- **Ne jamais optimiser les seuils sur les mêmes données** (lookahead bias)
- **Documenter tous les tests effectués** (n_trials réel)
- **Conserver holdout set** pour validation finale post-gates

---

*Dernière mise à jour: 2026-05-28*
*Version: 1.0.0*
