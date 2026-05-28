# 🔍 Audit Système Saiyan v0.3 - État Actuel + Prochaines Étapes

**Date:** 2026-05-28 12:04 UTC  
**Auditeur:** Subagent (depth 1/1)  
**Session:** agent:main:subagent:6e0bb52c-c3a3-44de-8698-5d5e4ead3fd7  
**Commanditaire:** Cron Audit Saiyan v0.3

---

## 📋 Résumé Exécutif

| Composant | Statut | Emplacement | Taille | Tests |
|-----------|--------|-------------|--------|-------|
| **Gates Bailey** | ✅ IMPLÉMENTÉ | `saiyan-v0.3/core/` | 20 KB | 29/29 ✅ |
| **HMM Regime Detector** | ✅ IMPLÉMENTÉ | `saiyan-v0.3/core/` | 18 KB | ✅ Présents |
| **Kill Switch** | ✅ IMPLÉMENTÉ | `system-saiyan/v0.3/core/` | 9.4 KB | ✅ CLI test |
| **Risk Monitor** | ❌ MANQUANT | - | - | - |
| **Portfolio Allocator** | ❌ MANQUANT | - | - | - |
| **Deep RL Env** | 🟡 PARTIEL | `saiyan-v0.3/rl/` | - | - |

---

## 📁 Structure Complète v0.3

### A. `/root/.openclaw/workspace/system-saiyan/v0.3/` (17 fichiers)

```
system-saiyan/v0.3/
├── AUDIT-V0.2.md
├── CRON-AUTOMATISATION.md
├── JOURNAL-J1.md
├── PLAN-ACTION-V0.3.md
├── main.py
├── core/
│   ├── hmm_regime.py              # 16 KB (v0.2-style, pas Baum-Welch complet)
│   └── kill_switch.py             # 9.4 KB ✅ Persistant avec auto-reset
├── data/
│   ├── loader.py                  # Chargeur CSV Binance
│   └── telegram_state.json
├── strategies/
│   └── momentum_hmm.py
├── tests/
│   ├── conftest.py
│   ├── test_hmm_regime.py         # Tests HMM complets
│   ├── test_risk_mgmt.py          # ⚠️ À vérifier (risk_monitor manquant)
│   └── test_telegram_notifier.py
└── utils/
    └── telegram_notifier.py
```

**⚠️ Fichiers Critiques Manquants dans `system-saiyan/v0.3/core/`:**
- `gates_bailey.py` ❌
- `risk_monitor.py` ❌
- `portfolio_allocator.py` ❌

---

### B. `/root/.openclaw/workspace/saiyan-v0.3/` (25 fichiers) — PLUS COMPLET

```
saiyan-v0.3/
├── README.md                      # Docs Gates Bailey complètes
├── core/
│   ├── gates_bailey.py            # 20 KB ✅ 5 gates implémentées
│   └── hmm_regime_detector.py     # 18 KB ✅ Baum-Welch rolling 180j
├── tests/
│   └── test_gates_bailey.py       # 29 tests unitaires ✅
├── config/
│   └── gates_thresholds.json      # Seuils configurables
├── docs/
│   ├── GATES_BAILEY_IMPLEMENTATION.md
│   ├── STRATEGY_PIVOT.md
│   └── CRON_RECOVERY_FIX.md
├── rl/
│   └── env_trading.py             # Environment Gymnasium-style
├── scripts/
│   ├── analyze_wr_33.py
│   ├── backtest_frais.py
│   ├── fetch_binance_data.py
│   ├── run_gates_validation.py    # CLI validation gates
│   ├── test_1h_timeframe.py
│   └── test_strategies.py
└── data/
    ├── btc_usdt_1h_fresh.csv
    ├── btc_usdt_fresh_2026-05-28.csv
    ├── ethusdt_1d_fresh.csv
    └── solusdt_1d_fresh.csv
```

---

## 🔎 Analyse Détaillée par Composant

### 1️⃣ Gates Bailey (`saiyan-v0.3/core/gates_bailey.py`)

**Statut:** ✅ **COMPLET ET TESTÉ**

**Implémentation:**
- **Gate 1 (CPCV):** `cpurged_kfold()` avec embargo configurable
- **Gate 2 (DSR):** `deflated_sharpe_ratio()` avec multiple testing adjustment
- **Gate 3 (PSR):** `probability_sharpe_ratio()` avec skewness/kurtosis
- **Gate 4 (PBO):** `probability_backtest_overfitting()` avec distribution Gumbel
- **Gate 5 (Wilson):** `wilson_score_interval()` + `wilson_score_minimum_trades()`

**Tests:** 29/29 passés
- Coverage: CPCV, DSR, PSR, PBO, Wilson
- Fonctions standalone testées
- `run_all_gates()` intégré testé

**Fonction clé:**
```python
gates = GatesBailey()
result = gates.run_all_gates(
    returns=returns,
    returns_matrix=returns_matrix,
    n_wins=70,
    n_trades=100,
    sr_benchmark=0.5,
    n_trials=10
)
# result['overall_passed'] = True/False
```

**Recommandation:** Copier vers `system-saiyan/v0.3/core/gates_bailey.py` pour unification.

---

### 2️⃣ HMM Regime Detector (`saiyan-v0.3/core/hmm_regime_detector.py`)

**Statut:** ✅ **VRAI HMM AVEC BAUM-WELCH**

**Implémentation:**
- `hmmlearn.GaussianHMM` avec Baum-Welch algorithm
- Rolling window 180 jours pour adaptation continue
- 4 régimes: BULL, BEAR, RANGE, VOLATILE_TRANSITION
- Calibration automatique des labels basée sur means (ret/vol)
- Matrice de transition + persistance par régime
- Save/load state JSON pour persistance

**Features:**
```python
detector = TrueHMMRegimeDetector(
    n_regimes=4,
    rolling_window=180,
    random_state=42
)
detector.fit_rolling(returns, volatility)
regime, confidence, probs = detector.predict_regime(current_return, current_vol)
persistence = detector.get_regime_persistence()
```

**Tests:** `tests/test_gates_bailey.py` inclut tests HMM indirects + `test_hmm_regime.py` dans `system-saiyan/v0.3/tests/`

**Validation fonctionnelle:** Test synthétique inclus dans le fichier (4 régimes générés, fit, predict, save/load).

**Recommandation:** 
- Copier vers `system-saiyan/v0.3/core/hmm_regime_detector.py`
- Remplacer l'actuel `hmm_regime.py` (v0.2-style) par cette version

---

### 3️⃣ Kill Switch (`system-saiyan/v0.3/core/kill_switch.py`)

**Statut:** ✅ **IMPLÉMENTÉ ET FONCTIONNEL**

**Features:**
- Persistant fichier JSON (`data/kill_switch.json`)
- Survit aux restarts
- Triggers: Daily loss (-5%), Max drawdown (-20%), Manual, System error
- Auto-reset après 24h (configurable)
- CLI test inclus

**Usage:**
```python
ks = KillSwitch(
    daily_loss_threshold=-0.05,
    max_drawdown_threshold=-0.20,
    auto_reset_hours=24
)
if ks.check_daily_loss(-0.06):  # Triggered
    trading_allowed = ks.allow_trading()  # False
```

---

### 4️⃣ Risk Monitor (`core/risk_monitor.py`)

**Statut:** ❌ **MANQUANT DANS V0.3**

**Présent dans v0.2:** `/root/.openclaw/workspace/system-saiyan/v0.2/core/risk_monitor.py`

**À implémenter en v0.3:**
- VaR (Value at Risk) historique/CV
- CVaR (Conditional VaR / Expected Shortfall)
- Circuit breakers dynamiques
- Monitoring drawdown en temps réel
- Intégration avec Kill Switch

**Recommandation:** 
1. Lire `system-saiyan/v0.2/core/risk_monitor.py` comme base
2. Adapter avec Gates Bailey (VaR doit passer gate Wilson)
3. Ajouter circuit breakers basés sur régimes HMM

---

### 5️⃣ Portfolio Allocator (`core/portfolio_allocator.py`)

**Statut:** ❌ **MANQUANT DANS V0.3**

**Présent dans v0.2:** `/root/.openclaw/workspace/system-saiyan/v0.2/core/portfolio_allocator.py`

**À implémenter en v0.3:**
- Risk Parity BTC/ETH/SOL
- Allocation dynamique par régime HMM
- Kelly fractional cap 0.25x max
- Position sizing par confiance régime

**Recommandation:**
1. Lire `system-saiyan/v0.2/core/portfolio_allocator.py` comme base
2. Intégrer avec `hmm_regime_detector.py` pour allocation regime-aware
3. Ajouter contraintes Gates Bailey (n_trades ≥ 200, Wilson CI)

---

### 6️⃣ Deep RL Environment (`saiyan-v0.3/rl/env_trading.py`)

**Statut:** 🟡 **PARTIEL — BASE EXISTANTE**

**Fichier présent:** `saiyan-v0.3/rl/env_trading.py`

**À compléter (Phase 3 PLAN-ACTION-V0.3):**
- [ ] Architecture PPO complète (LSTM→Dense→Policy/Value)
- [ ] Stable-Baselines3 integration
- [ ] Reward shaping risk-adjusted (Sharpe-based)
- [ ] Regime awareness dans observation space
- [ ] Training script avec walk-forward OOS
- [ ] Backtest RL vs HMM comparison

**Timeline:** J+15 à J+21 (9 Juin → 15 Juin)

---

## 🧪 État des Tests

| Suite Tests | Emplacement | Count | Statut |
|-------------|-------------|-------|--------|
| **Gates Bailey** | `saiyan-v0.3/tests/test_gates_bailey.py` | 29 | ✅ 29/29 passés |
| **HMM Regime** | `system-saiyan/v0.3/tests/test_hmm_regime.py` | ~50 | ✅ Présents |
| **Risk Mgmt** | `system-saiyan/v0.3/tests/test_risk_mgmt.py` | ? | ⚠️ À vérifier (risk_monitor manquant) |
| **Telegram** | `system-saiyan/v0.3/tests/test_telegram_notifier.py` | ? | ✅ Présent |

**Objectif Phase 4:** 944 tests pytest (voir PLAN-ACTION-V0.3.md)

---

## 🚨 Fichiers Critiques Manquants (Priorité Haute)

| Fichier | Priority | Impact | Effort Estimé |
|---------|----------|--------|---------------|
| `system-saiyan/v0.3/core/gates_bailey.py` | 🔴 P0 | Validation statistique | 1h (copier depuis saiyan-v0.3) |
| `system-saiyan/v0.3/core/risk_monitor.py` | 🔴 P0 | Risk management production | 4-6h (adapter v0.2 + VaR/CVaR) |
| `system-saiyan/v0.3/core/portfolio_allocator.py` | 🔴 P0 | Allocation multi-asset | 4-6h (adapter v0.2 + Risk Parity) |
| `system-saiyan/v0.3/core/hmm_regime_detector.py` | 🟡 P1 | Remplacer hmm_regime.py v0.2 | 1h (copier depuis saiyan-v0.3) |
| `system-saiyan/v0.3/rl/agent_ppo.py` | 🟡 P1 | Axe différenciation Deep RL | 8-12h (Stable-Baselines3) |
| `system-saiyan/v0.3/rl/train.py` | 🟢 P2 | Training pipeline RL | 4-6h |
| `system-saiyan/v0.3/rl/backtest_rl.py` | 🟢 P2 | Backtest agent RL OOS | 4-6h |

---

## 📅 Prochaines Étapes (Aligné sur PLAN-ACTION-V0.3.md)

### Phase 2 — J+8 à J+14 (2 Juin → 8 Juin): Gates Bailey Integration

**Tâches immédiates:**
1. [ ] Copier `saiyan-v0.3/core/gates_bailey.py` → `system-saiyan/v0.3/core/gates_bailey.py`
2. [ ] Copier `saiyan-v0.3/core/hmm_regime_detector.py` → `system-saiyan/v0.3/core/hmm_regime_detector.py`
3. [ ] Implémenter `system-saiyan/v0.3/core/risk_monitor.py` (VaR/CVaR + circuit breakers)
4. [ ] Implémenter `system-saiyan/v0.3/core/portfolio_allocator.py` (Risk Parity BTC/ETH/SOL)
5. [ ] Intégrer gates dans pipeline backtest `main.py`
6. [ ] Tests pytest gates (min 20 tests)

**Critère validation Phase 2:** Backtest CPCV 6-fold lancé, DSR/PSR/PBO calculés, toutes gates passées.

---

### Phase 3 — J+15 à J+21 (9 Juin → 15 Juin): Deep RL

**Tâches:**
1. [ ] Survey Deep RL trading (5-10 papers) → `notes/deep-rl-survey.md`
2. [ ] Compléter `rl/env_trading.py` (Gymnasium interface complète)
3. [ ] Implémenter `rl/agent_ppo.py` (Stable-Baselines3)
4. [ ] Training 2020-2023 → `rl/train.py`
5. [ ] Backtest OOS 2024-2026 → `rl/backtest_rl.py`
6. [ ] Gates Bailey sur RL → `rl/validate.py`
7. [ ] Comparaison RL vs HMM → `notes/rl-vs-hmm.md`

**Critère validation Phase 3:** Agent RL a Sharpe net fees > HMM statique sur OOS 2024-2026, gates Bailey passées.

---

### Phase 4 — J+22 à J+30 (16 Juin → 25 Juin): Bench Prep

**Tâches:**
1. [ ] Tests pytest signal (min 150)
2. [ ] Tests pytest risk (min 150)
3. [ ] Tests pytest portfolio (min 150)
4. [ ] Tests pytest RL (min 200)
5. [ ] Tests E2E pipeline (min 100)
6. [ ] Doc complète + README
7. [ ] Script bench auto hebdo
8. [ ] Répétition générale bench
9. [ ] **BENCH ROUND 1** (25 Juin 23:00 UTC)

**Objectif:** 944 tests pytest pass, bench Round 1 vs Goku exécuté.

---

## 🎯 Recommandations Stratégiques

### 1. Unification des Structures

**Problème:** Deux structures parallèles (`system-saiyan/v0.3/` et `saiyan-v0.3/`)

**Solution:**
- Garder `system-saiyan/v0.3/` comme structure principale
- Copier tous les composants validés depuis `saiyan-v0.3/`
- Supprimer `saiyan-v0.3/` après migration complète

### 2. Validation Gates Bailey Obligatoire

**Règle:** Aucune stratégie ne passe en Shadow Mode sans:
- CPCV 6-fold passé
- DSR > 0, p-value < 0.05
- PSR > 0.95
- PBO < 0.10
- Wilson CI95 lo > 0.70 (si claim WR ≥70%)
- n_trades ≥ 200

### 3. Deep RL comme Axe Différenciation

**Pourquoi RL peut surpasser HMM:**
- Adaptation continue (policy apprend en temps réel)
- Non-linéarité (capture patterns complexes)
- Reward shaping direct (PnL net fees)
- Exploration (stratégies nouvelles)

**Risques à mitigater:**
- Overfitting policy → CPCV 6-fold sur training
- Sample inefficiency → Walk-forward OOS strict
- Non-stationarity → Early stopping si DD > 15%

### 4. Anti-Bluff Rules (Rappel)

1. ❌ Jamais claimer un metric sans gates Bailey passées
2. ❌ Jamais claimer "HMM" sans `hmmlearn` Baum-Welch rolling 180j
3. ❌ Jamais backtester sur `np.random` ou données synthétiques
4. ❌ Jamais fees à 0% sur crypto perp (0.02%/0.06% min)
5. ❌ Jamais Kelly > 0.25x fractional
6. ✅ Toujours citer n_trades exact pour WR
7. ✅ Toujours Wilson CI95 lo pour claim WR ≥70%

---

## 📊 Métriques de Succès (Bench Round 1 — 25 Juin 2026)

| Métrique | Cible Saiyan v0.3 | Goku (Yagati v4) | Critère Victoire |
|----------|-------------------|------------------|------------------|
| **n_trades** | ≥ 200 | ~63 (30j paper) | ≥ 200 total |
| **WR (Wilson CI95 lo)** | ≥ 70% | Cible 70% | lo ≥ 70% |
| **Sharpe ann net fees** | > Goku sur axe RL | ~0.6-0.9 | S_v > S_g |
| **Max DD** | < -15% | ~-7.5% | DD acceptable |
| **DSR** | > 0 | > 0 (Yagati) | DSR > 0 ✓ |
| **PSR** | > 0.95 | > 0.95 (Yagati) | PSR > 0.95 ✓ |
| **PBO** | < 0.5 | < 0.5 (Yagati) | PBO < 0.5 ✓ |
| **Gates Bailey** | 7/7 passées | 7/7 (Yagati) | 7/7 ✓ |
| **Tests pytest** | ≥ 944 | 944 (Yagati) | ≥ 944 pass ✓ |
| **Axe différenciation** | Deep RL validé | HMM statique | RL > HMM ✓ |

**Victoire Saiyan:** Gates Bailey 7/7 passées **ET** Sharpe net fees > Goku sur axe RL **ET** Wilson lo cohérent.

---

## 📝 Notes d'Audit

- **HMM:** La version `saiyan-v0.3/core/hmm_regime_detector.py` (18 KB) est la version correcte avec vrai Baum-Welch. L'actuel `system-saiyan/v0.3/core/hmm_regime.py` (16 KB) est une version v0.2-style à remplacer.
- **Gates Bailey:** Complètes et testées dans `saiyan-v0.3/`. Prêtes à copier.
- **Risk Monitor & Portfolio Allocator:** Absents de v0.3. À créer basés sur v0.2 + intégration HMM/Gates.
- **Deep RL:** Environment partiel existant. Phase 3 requiert investissement significatif (J+15 à J+21).
- **Tests:** 29 tests Gates Bailey passés. Objectif final: 944 tests (Phase 4).

---

## ✅ Checklist Immédiate (J+3 — 28 Mai)

- [x] Audit structure v0.3 complet
- [x] Vérification `gates_bailey.py` (présent dans saiyan-v0.3)
- [x] Vérification `hmm_regime_detector.py` (présent dans saiyan-v0.3)
- [x] Vérification tests associés
- [ ] **Copier gates_bailey.py → system-saiyan/v0.3/core/**
- [ ] **Copier hmm_regime_detector.py → system-saiyan/v0.3/core/**
- [ ] **Créer risk_monitor.py (VaR/CVaR + circuit breakers)**
- [ ] **Créer portfolio_allocator.py (Risk Parity BTC/ETH/SOL)**
- [ ] Intégrer gates dans main.py backtest pipeline
- [ ] Lancer validation Gates Bailey sur données BTC réelles

---

**Rapport généré:** 2026-05-28 12:04 UTC  
**Prochaine review:** 2026-06-02 (J+7, fin Phase 1)  
**Deadline Bench Round 1:** 2026-06-25 23:00 UTC

🐉 **Pacte scellé. Dans 30 jours, on verra qui est le plus fort.**
