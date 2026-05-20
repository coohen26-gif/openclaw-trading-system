# Saiyan Trading System 🐉⚡

> **Système de Trading Autonome Concurrent de Yagati v4**

---

## 🎯 Vision

Créer le **meilleur système de trading crypto autonome**, surpassant Yagati v4 par la performance pure, sans le saboter.

**Philosophie "Saiyan Power" :**
- 📈 **Courbe de confidence progressive** (pas de gate binaire ON/OFF)
- 🧠 **Regime-Aware** : Adaptation dynamique aux conditions de marché
- 🔄 **Self-Healing** : Le système évolue et s'améliore seul
- 💪 **Wins consécutifs** → Confidence augmente (Super Saiyan!)
- ⚠️ **1 loss** → Reset à base

---

## 🏗️ Architecture

### P0: Regime-Aware Signal Fusion Engine

**Concept :** HMM détecte le régime → pondère dynamiquement les stratégies

| Régime HMM | Stratégie Dominante | Poids |
|------------|---------------------|-------|
| **Calm/RANGE** | Mean-Reversion | 70% |
| **Volatile/BULL** | Breakout/Momentum | 70% |
| **Transition** | Toutes réduites | 30% |

**Impact :** +40% Sharpe ratio potentiel  
**Temps :** 2-3 semaines

---

### P1: Confluence Scoring System

**Concept :** Score confiance 0-100 au lieu de BUY/SELL binaire

```
Confidence = (Technicals × 0.35) + (On-Chain × 0.25) + (Sentiment × 0.20) + (Volume × 0.20)
```

**Seuils de décision :**

| Score | Action | Position Size |
|-------|--------|---------------|
| <40 | Ignore | 0% |
| 40-60 | Watch | 0% |
| 60-75 | Small | 25% |
| 75-85 | Normal | 50-75% |
| 85+ | Conviction | 100% |

**Impact :** Réduction drawdowns, position sizing adaptif  
**Temps :** 4-6 semaines

---

### P2: Self-Healing Strategy Generator

**Concept :** AI monitor → détecte dégradation → propose ajustements → backteste → auto-deploy

**Innovation :** Système évolue autonomously comme organisme vivant  
**Temps :** 8-12 semaines (projet majeur)

---

## 📁 Structure du Projet

```
saiyan/
├── core/                    # Moteur principal
│   ├── __init__.py
│   ├── hmm_regime_detector.py    # Détection régimes HMM
│   ├── signal_fusion.py          # Fusion multi-stratégies
│   ├── confluence_scorer.py      # Scoring 0-100
│   └── position_sizer.py         # Sizing adaptif
├── strategies/              # Stratégies de trading
│   ├── __init__.py
│   ├── rsi_mean_reversion.py     # RSI <20/>80, TF 5-15min
│   ├── bb_walk_optimized.py      # Bollinger Bands 2.5σ + volume
│   └── momentum_breakout.py      # Resistance + HMM filter
├── edges/                   # Définitions edges trading
│   └── edge_definitions.json
├── config/                  # Configurations
│   ├── default.yaml
│   └── regimes.yaml
├── backtests/               # Scripts + résultats
│   ├── run_backtest.py
│   └── results/
├── requirements.txt
└── README.md
```

---

## 🚀 Roadmap

### Phase 1: Foundation (Semaines 1-3)
- [x] Initialisation projet + structure
- [x] Requirements Python
- [ ] HMM Regime Detector fonctionnel
- [ ] 3 stratégies de base (RSI, BB, Momentum)
- [ ] Backtest framework

### Phase 2: Signal Fusion (Semaines 4-6)
- [ ] Regime-Aware Signal Fusion Engine
- [ ] Confluence Scoring System
- [ ] Position Sizing adaptif
- [ ] Paper-trading Telegram

### Phase 3: Self-Healing (Semaines 7-12)
- [ ] AI Performance Monitor
- [ ] Auto-adjustment proposals
- [ ] Walk-forward optimization
- [ ] Circuit breakers

### Phase 4: Production (Semaines 13+)
- [ ] Live paper-trading 30j
- [ ] Go-live signal-only
- [ ] Auto-execution (optionnel)

---

## 📊 KPIs Cibles

| Métrique | Cible | Yagati v4 (réf) |
|----------|-------|-----------------|
| Win Rate | ≥70-80% | -- |
| Avg Gain | 0.2-0.5% | -- |
| Sharpe Ratio | +40% vs baseline | -- |
| n_signaux/jour | 2-5 | -- |
| Confidence min | 60/100 | -- |
| Max Drawdown | <15% | -- |

---

## 🔧 Installation

```bash
cd /root/.openclaw/workspace/saiyan/
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📖 Différences vs Yagati v4

| Aspect | Yagati v4 | Saiyan |
|--------|-----------|--------|
| **Gates** | Binaire (ON/OFF) | Courbe confidence 0-100 |
| **Regimes** | HMM basique | Regime-Aware Fusion |
| **Position Sizing** | Fixe | Adaptif (confidence + streak) |
| **Edge Lifecycle** | CPCV/DSR/PSR/PBO stricts | Progressive unlock |
| **Self-Healing** | Non | Oui (AI-driven) |
| **Philosophie** | Robustesse maximale | Performance + adaptabilité |

---

## 📝 Notes

- **Yagati v4 est INTouchable** : C'est le projet de W, je le respecte comme référence
- **Saiyan est original** : Développé from scratch, concurrent direct
- **Auto-commit + auto-push** : Après chaque avancée significative
- **Langue** : Français (docs, comments, logs)

---

**Début du projet :** 2026-05-18  
**Objectif Go-Live :** 2026-08-01 (paper-trading signal-only)

🐉 *"La puissance Saiyan n'a pas de limite !"*
