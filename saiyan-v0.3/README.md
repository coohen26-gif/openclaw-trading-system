# Saiyan v0.3 - Système Trading Autonome

> **Statut:** Gates Bailey 5/5 implémentées ✅ | Tests: 29/29 passés ✅

## 🎯 Mission

Développer un système de trading autonome concurrent de Yagati v4, avec validation statistique robuste selon les standards académiques (Bailey, López de Prado).

## 📊 Performance Cible

| Métrique | Objectif | Statut |
|----------|----------|--------|
| Win Rate | ≥70% | 🟡 En validation |
| Avg Gain | 0.2-0.5% | 🟡 En validation |
| Sharpe Ratio | >1.5 | 🟡 En validation |
| Gates Bailey | 5/5 | ✅ Implémentées |

---

## 🚀 Gates Bailey - 5 Portes de Robustesse

### ✅ Gate 1: CPCV (Combinatorial Purged Cross-Validation)
- Élimine le lookahead bias dans la validation
- Embargo autour des splits train/test
- **Statut:** Implémentée + testée

### ✅ Gate 2: DSR (Deflated Sharpe Ratio)
- Ajuste le Sharpe Ratio pour le multiple testing bias
- **Statut:** Implémentée + testée

### ✅ Gate 3: PSR (Probability of Sharpe Ratio)
- Probabilité que le vrai SR > benchmark
- Ajuste pour skewness/kurtosis (fat tails)
- **Statut:** Implémentée + testée

### ✅ Gate 4: PBO (Probability of Backtest Overfitting)
- Probabilité que la meilleure stratégie soit due au hasard
- Distribution Gumbel pour les extrêmes
- **Statut:** Implémentée + testée

### ✅ Gate 5: Wilson Score Interval
- Intervalle de confiance pour Win Rate
- Plus robuste que normal pour petits échantillons
- **Statut:** Implémentée + testée

---

## 📁 Structure

```
saiyan-v0.3/
├── core/
│   └── gates_bailey.py      # Module principal des gates (600+ lignes)
├── tests/
│   └── test_gates_bailey.py # 29 tests unitaires pytest
├── config/
│   └── gates_thresholds.json # Seuils configurables
├── docs/
│   └── GATES_BAILEY_IMPLEMENTATION.md # Documentation complète
├── scripts/
│   └── run_gates_validation.py # Script de validation CLI
└── README.md
```

---

## 🔧 Installation

```bash
cd /root/.openclaw/workspace/saiyan-v0.3
pip install numpy scipy scikit-learn statsmodels pytest pytest-cov
```

---

## 🧪 Tests

```bash
# Lancer tous les tests
pytest tests/test_gates_bailey.py -v

# Avec couverture
pytest tests/test_gates_bailey.py -v --cov=core/gates_bailey --cov-report=term-missing
```

**Résultats:** 29/29 tests passés en 0.74s

---

## 🚀 Validation Rapide

```bash
# Avec données synthétiques (démo)
python scripts/run_gates_validation.py --synthetic

# Avec vraies données
python scripts/run_gates_validation.py --data data/btc_returns.npy --config config/gates_thresholds.json
```

---

## 📈 Roadmap

### ✅ Phase 1 (2026-05-28) - Gates Bailey Sprint
- [x] core/gates_bailey.py - 5 gates implémentées
- [x] tests/test_gates_bailey.py - 29 tests
- [x] config/gates_thresholds.json - Seuils
- [x] docs/GATES_BAILEY_IMPLEMENTATION.md - Docs
- [x] scripts/run_gates_validation.py - CLI validation

### 🔄 Phase 2 (2026-05-29 à 2026-05-30) - Intégration
- [ ] Intégration avec backtest engine Saiyan
- [ ] Calcul automatique n_trials
- [ ] Support multi-asset (BTC, ETH, SOL)
- [ ] Dashboard visualisation gates

### 🔄 Phase 3 (2026-05-31 à 2026-06-07) - Shadow Mode
- [ ] Paper-deploy signal-only sur Telegram
- [ ] Collecte feedback réel W
- [ ] Ajustement seuils selon performance terrain
- [ ] Cohen-tap integration

### 🔄 Phase 4 (2026-06-08+) - Deep RL
- [ ] Architecture PPO (LSTM→Dense→Policy/Value)
- [ ] Reward shaping risk-adjusted
- [ ] Comparison HMM vs Deep RL performance

---

## 📚 Références Académiques

1. Bailey et al. (2017) - "The Probability of Backtest Overfitting"
2. Bailey & López de Prado (2014) - "The Deflated Sharpe Ratio"
3. López de Prado (2018) - "Advances in Financial Machine Learning"

---

## ⚠️ Avertissements

- **Ne pas utiliser en production sans Shadow Mode préalable**
- **Les seuils doivent être fixés AVANT validation (pas d'optimisation a posteriori)**
- **Conserver holdout set pour validation finale**

---

*Dernière mise à jour: 2026-05-28*
*Version: 1.0.0*
*Auteur: Bonjour (Goku) 👋*
