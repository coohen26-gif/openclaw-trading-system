# Plan d'Action Saiyan v2 - Système Trading Autonome

**Date:** 25 Mai 2026, 07:00 UTC  
**Statut:** Phase 3 - Production Readiness (35% complété)  
**Mode:** Autonome ✅

---

## 📊 État des Lieux - Formation & Système

### Progression Cursus Quant Trader

| Niveau | Progression | Statut |
|--------|-------------|--------|
| Master 1-4 (Fondations) | 100% | ✅ |
| Master 5 (5 modules) | 100% | ✅ |
| Phase 2 (Intégration) | 100% | ✅ |
| **Phase 3 (Production)** | **35%** | 🔄 |
| **TOTAL** | **~88%** | 🟢 |

### Modules Complétés (29 semaines)

**Semaines 01-04:** Returns BTC, GARCH, ARIMA, Black-Scholes  
**Semaines 05-08:** Microstructure, Feature Engineering, ML Supervised, HMM  
**Semaines 09-12:** Risk Parity, VaR/CVaR, Stress Testing, Multi-Asset  
**Semaines 13-16:** Alternative Data, Production Systems, HFT, Derivatives  
**Semaines 17-20:** Risk Monitoring, Portfolio Allocator, HMM 4 Régimes, Stress Testing  
**Semaines 21-25:** Backtest Engine, Binance Connector, Momentum Optimization  
**Semaines 26-29:** Production Readiness (en cours)

### Code Produit

- **~400KB de code Python** (25+ fichiers)
- **Backtests:** 10+ stratégies testées
- **Visualisations:** 15+ figures générées
- **Documentation:** 30+ fichiers notes.md

---

## 🎯 Architecture Système Saiyan v0.2

### Décision Architecture (25 Mai 2026)

**CHOIX: Single-Asset BTC avec Filtre HMM**

**Pourquoi:**
- Multi-asset Risk Parity underperforme (0% vs +2% BTC seul)
- Concentration > dilution pour momentum strategies
- HMM 4 régimes capture mieux régimes BTC que régimes partagés

**Configuration Optimisée:**

```python
# Position Sizing par régime (conservateur)
Bull: 0.75x Kelly (18.75% capital)
Volatile Bull: 0.5x Kelly (12.5% capital)
Range: 0.25x Kelly (6.25% capital)
Bear: 0.1x Kelly (2.5% capital) - quasi cash

# Stops & Targets
Bull: SL -5% / TP +15%
Volatile Bull: SL -8% / TP +20%
Range: SL -4% / TP +8%
Bear: SL -3% / TP +5%

# Time Exit
Max hold: 20 jours (38% exits actuels par temps)
```

---

## ✅ Actions Immédiates Requises (P0 - 24-48h)

### 1. 📊 Backtest Walk-Forward Validation

**Objectif:** Valider robustesse sur données 2020-2026

**Tâches:**
- [ ] Train: 2020-2023 (3 ans)
- [ ] Test: 2024-2026 (2 ans)
- [ ] Metrics: Sharpe, Max DD, Win Rate, Calmar
- [ ] Comparaison: Optimized vs Baseline

**Fichier:** `learning/code/backtest_walkforward.py`  
**Deadline:** 25 Mai 2026, 23:59 UTC

---

### 2. 🔧 Optimisation Configuration Momentum+HMM

**Problèmes identifiés:**
- Drawdown -7.5% (trop élevé vs -5.1% baseline)
- 38% time exits (signaux peu convaincants)
- Position sizing trop agressif (1.5x Kelly!)

**Solutions:**
- [ ] Réduire Kelly: 1.5x → 0.75x (Bull), 1.0x → 0.5x (VolBull)
- [ ] Stops plus serrés: -12% → -5% (Bull), -15% → -8% (VolBull)
- [ ] HMM lookback: 60j → 30j (réduire lag)
- [ ] Confidence threshold: 50% → 60% minimum

**Fichier:** `learning/code/momentum_hmm_optimized.py` (v2)  
**Deadline:** 26 Mai 2026, 12:00 UTC

---

### 3. 📱 Intégration Telegram Signal Flow

**Objectif:** Signaux → Telegram → W exécute manuellement

**Workflow:**
1. Signal détecté (confidence ≥60/100)
2. Notification Telegram avec:
   - Asset (BTC/USDT)
   - Direction (LONG/SHORT)
   - Entry price
   - TP/SL
   - Confidence score
   - Régime HMM actuel
3. W exécute manuellement
4. Tracking performance (WR, PnL, n_signaux)

**Fichier:** `system-saiyan/v0.2/telegram_signaler.py`  
**Deadline:** 27 Mai 2026, 18:00 UTC

---

### 4. 🧹 Classification & Rangement (Demande W)

**Objectif:** "Deuxième cerveau" - tout organiser pour retrieval facile

**Structure créée:**

```
learning/
├── journal.md                    # Journal quotidien
├── MODULES_COMPLETED.md          # Modules validés
├── plan-action-saiyan-v2.md      # Ce fichier
├── code/                         # Code Python (~400KB)
│   ├── backtest_*.py            # Backtesting engine
│   ├── momentum_*.py            # Stratégies momentum
│   ├── hmm_*.py                 # HMM detection
│   ├── risk_*.py                # Risk management
│   └── binance_connector.py     # API integration
├── notes/                        # Notes par semaine
│   ├── semaine-01-returns-btc.md
│   ├── semaine-02-garch.md
│   └── ... (30+ fichiers)
├── data/                         # Données BTC
│   └── btc_usdt_*.csv
├── figures/                      # Visualisations
│   └── *.png (15+ figures)
├── insights/                     # Insights clés
└── dreams/                       # Dream processing
    └── light/
        └── 2026-05-*.md
```

**MEMORY.md:** Déjà consolidé avec:
- Personnalité & Identité
- Contexte Utilisateur W
- Yagati v4 état (référence)
- Dream Processing Sessions 1-4
- Roadmap complète
- Décisions prises

**Deadline:** ✅ Déjà fait (25 Mai 2026)

---

## 📋 TodoList Détaillée

### P0 - Critique (24-48h)

| ID | Tâche | Temps | Statut | Deadline |
|----|-------|-------|--------|----------|
| P0.1 | Backtest Walk-Forward | 2h | ⏳ | 25 Mai 23:59 |
| P0.2 | Optimisation config HMM | 1h | ⏳ | 26 Mai 12:00 |
| P0.3 | Telegram Signaler | 3h | ⏳ | 27 Mai 18:00 |
| P0.4 | Git commit + push | 15min | ⏳ | Après chaque tâche |

### P1 - Important (3-7 jours)

| ID | Tâche | Temps | Statut |
|----|-------|-------|--------|
| P1.1 | Dashboard monitoring (Prometheus+Grafana) | 4h | ⏳ |
| P1.2 | Alertes Telegram (changement régime, DD) | 2h | ⏳ |
| P1.3 | Weekly stress testing (cron auto) | 2h | ⏳ |
| P1.4 | Documentation système v0.2 | 2h | ⏳ |

### P2 - Secondaire (1-2 semaines)

| ID | Tâche | Temps | Statut |
|----|-------|-------|--------|
| P2.1 | Regime Oracle (HMM + Router multi-stratégies) | 8h | ⏳ |
| P2.2 | Trading Git + Inbox Décisions | 4h | ⏳ |
| P2.3 | Shadow Mode + Auto-Learning | 6h | ⏳ |
| P2.4 | Swarm Micro-Agents | 12h | ⏳ |

---

## 🎯 KPIs & Targets

### Performance Trading (Cible)

| Métrique | Cible | Actuel | Écart |
|----------|-------|--------|-------|
| Win Rate | ≥70% | -- | -- |
| Avg Gain | 0.2-0.5% | -- | -- |
| n_signaux/jour | 2-5 | -- | -- |
| Confidence min | 60/100 | -- | -- |
| Sharpe Ratio | ≥1.5 | -- | -- |
| Max Drawdown | <-10% | -- | -- |

### Performance Formation

| Métrique | Cible | Actuel | Écart |
|----------|-------|--------|-------|
| Progression totale | 100% | 88% | -12% |
| Phase 3 complétée | 100% | 35% | -65% |
| Code produit | 500KB | 400KB | -20% |
| Backtests validés | 10 | 6 | -4 |

---

## 🔒 Règles de Conduite

1. **Yagati v4 INTouchable** → Système Saiyan concurrent en parallèle
2. **Auto-commit + auto-push** → Après chaque action
3. **Mode autonome** → Pas de questions, que de l'action
4. **SILENCE par défaut** → Parle seulement si:
   - Signal trading détecté
   - Urgence/anomalie
   - Résumé programmé
   - W pose question
5. **Synthèse en fin de message** → Quelques phrases simples

---

## 📅 Prochain Rapport

**Dans:** 2 heures (comme demandé par W)  
**Contenu:**
- Backtest Walk-Forward résultats
- Optimisation config HMM appliquée
- Avancement Telegram Signaler
- KPIs à jour

**Signature:** Goku, Saiyan du trading 🐉

---

*Mis à jour: 25 Mai 2026, 07:03 UTC*
