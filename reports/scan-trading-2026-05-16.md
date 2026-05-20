# 📊 Scan Trading Quotidien — 16 Mai 2026

**Généré:** 2026-05-16 05:00 UTC  
**Session:** cron:602099bf-77e6-4713-9656-26fb445d931d  
**Phase Système:** ML Phase D (emitter paper-deploy)  
**Statut Auto-Signaux:** ❌ AUCUN (depuis 2026-05-09, pivot "Voie Z")

---

## 1️⃣ État des Marchés

| Actif | Prix (16/05) | 24h | Régime HMM* | Tendance |
|---|---|---|---|---|
| **BTC** | ~$79,081 - $81,000 | +0.03% | BULL | Consolidation haussière |
| **ETH** | ~$2,228 | +0.21% | RANGE | Latéralisation |
| **SOL** | Données ambiguës** | -0.20% | BULL | À clarifier |
| **XRP** | ~$1.44 | +0.19% | BULL | Légère hausse |
| **BNB** | ~$668.76 | -0.49% | RANGE | Baisse légère, flip XRP (market cap $91B) |

*Régimes HMM du 2026-05-14 (dernière détection disponible)  
**Donnée Yahoo Finance semble être une action (SOL Investments Corp), pas Solana crypto

### 📈 Contexte Marché
- **Market Cap Total:** $2.67T (+0.33%)
- **Catalyseur:** CLARITY Act (régulation crypto) voté au Sénat US → boost marché
- **BTC:** Franchissement $80k-81k, consolidation en cours
- **BNB vs XRP:** BNB dépasse XRP en market cap ($91B vs ~$76B)

---

## 2️⃣ Performance des Edges

### 📊 Vue d'Ensemble
| Métrique | Valeur |
|---|---|
| **Total Edges** | 141 |
| **ARCHIVED** | 109 (77.3%) |
| **RESEARCH** | 32 (22.7%) |
| **ENABLED** | 0 ❌ |
| **PROBATION** | 0 ❌ |
| **Actives** | 0/141 (0%) |

### 🎯 Performance par Edge (n=31 trades paper)

| Edge | Actif | n_trades | Win Rate | PnL Avg | Statut |
|---|---|---|---|---|---|
| **ma_distance_revert** | ETHUSDT | 3 | **100%** ✅ | N/A | ARCHIVED |
| **bb_walk** | ETHUSDT | 3 | **66.7%** ✅ | +7.8% | ARCHIVED |
| **ma_ribbon** | ETHUSDT | 6 | **33.3%** ❌ | N/A | ARCHIVED |

### 📉 Backtests Récents

| Stratégie | Période | Win Rate | PnL Total | PnL/jour | Statut |
|---|---|---|---|---|---|
| **Bollinger-RSI Dual** | 89 jours | 47.4% ❌ | +34.33€ | +0.39€/jour | ❌ FAIL |
| **Volume Surge Breakout** | 41 jours | 37.0% ❌ | -501.74€ | -12.24€/jour | ❌ FAIL |

**Problème Central:** Gates de robustesse (CPCV, DSR, PSR, PBO) **trop strictes** → 0 edge activée malgré certaines performances correctes (bb_walk WR=66.7%).

---

## 3️⃣ Signaux Auto Générés

### 🚨 État: AUCUN SIGNAL DEPUIS LE 09/05/2026

| Période | Signaux Générés | Statut |
|---|---|---|
| Avant 2026-05-09 | Variables (selon edges actives) | ✅ |
| 2026-05-09 → 2026-05-16 | **0** | ❌ BLOQUÉ |

### 🔍 Causes Racines
1. **Gates binaires ON/OFF** → soit 100% soit 0%, pas de nuance
2. **Seuils CPCV/DSR/PSR/PBO** mal calibrés pour le régime actuel
3. **Aucune edge en ENABLED/PROBATION** → système en mode "observability" pure

### 💡 Insight Nocturne (2026-05-16 01:00-02:30 UTC)
> "Un système qui s'auto-ajuste comme un Super Saiyan qui monte en puissance progressivement. Pas de gate binaire (ON/OFF), mais une courbe de confidence qui fait varier la size automatiquement."

**Solution proposée:** Remplacer gates binaires par **Confluence Scoring 0-100** avec position sizing adaptif.

---

## 4️⃣ Anomalies Détectées

| # | Anomalie | Sévérité | Impact |
|---|---|---|---|
| **A1** | 0 auto-signaux depuis 7 jours | 🔴 CRITIQUE | Système trading inopérant |
| **A2** | 0 edges ENABLED sur 141 | 🔴 CRITIQUE | Pipeline R&D → PROD bloqué |
| **A3** | Gates trop strictes (CPCV, DSR, PSR, PBO) | 🟠 ÉLEVÉE | Filtre 100% des signaux |
| **A4** | Backtests récents FAIL (WR < 65%) | 🟠 ÉLEVÉE | Stratégies actuelles non viables |
| **A5** | Donnée SOL ambiguë (action vs crypto) | 🟡 MOYENNE | Risque confusion monitoring |
| **A6** | Bots long-bot/short-bot stopped (redémarrés 6/9 fois) | 🟠 ÉLEVÉE | Instabilité infrastructure |

---

## 5️⃣ Recommandations d'Ajustements

### 🚀 Priorité P0 (Cette Semaine)

| Action | Description | Impact | Effort |
|---|---|---|---|
| **R1** | **Relaxer gates CPCV/DSR** | Débloquer premiers signaux | 2-3h |
| **R2** | **Promouvoir bb_walk en PROBATION** | WR=66.7%, n=3, avg_pnl=+7.8% → mérite test | 1h |
| **R3** | **Implémenter Confluence Scoring (MVP)** | Score 0-100 au lieu de BUY/SELL binaire | 8-12h |
| **R4** | **Relancer bots long-bot/short-bot** | Stabiliser infrastructure | 30min |

### 📋 Priorité P1 (1-3 Semaines)

| Action | Description | Impact | Effort |
|---|---|---|---|
| **R5** | **Regime-Aware Signal Fusion** | Pondérer stratégies selon HMM (ex: mean-reversion 70% en RANGE) | 2-3 semaines |
| **R6** | **Backtester RSI Mean Reversion** | RSI(14) <20/>80, TF 5-15min, HMM=RANGE (ETHUSDT, SOLUSDT, 30j) | 4-6h |
| **R7** | **Backtester BB Walk Optimisée** | Bandes 2.5σ + volume > MA20 | 4-6h |
| **R8** | **Position Sizing Adaptif** | Varier size selon confidence score (25%-100%) | 6-8h |

### 🎯 Priorité P2 (1-2 Mois)

| Action | Description | Impact | Effort |
|---|---|---|---|
| **R9** | **Self-Healing Strategy Generator** | AI monitor → détecte dégradation → propose ajustements → auto-deploy | 4-6 semaines |
| **R10** | **Walk-Forward Auto** | Ré-optimisation automatique périodique | 2-3 semaines |
| **R11** | **Circuit Breakers** | Stop auto en cas de drawdown > X% | 4-6h |

---

## 📝 Plan d'Action Immédiat (24-48h)

```
[ ] 1. Relaxer seuils CPCV/DSR de 20% → permettre 1-2 edges en PROBATION
[ ] 2. Promouvoir bb_walk (ETHUSDT) en PROBATION → générer signaux paper
[ ] 3. Relancer long-bot/short-bot + vérifier stabilité
[ ] 4. Documenter nouveau Confluence Scoring dans research/
[ ] 5. Commit + push des ajustements
```

---

## 🎯 KPIs Cibles (Rappel)

| KPI | Actuel | Cible | Écart |
|---|---|---|---|
| **Win Rate** | 0% (aucun signal) | ≥70-80% | -70 pts |
| **Signaux/jour** | 0 | 5-15 | -15 |
| **PnL/jour** | 0€ | 500-600€ | -600€ |
| **Edges Actives** | 0 | 5-10 | -10 |
| **Sharpe Ratio** | N/A | >1 | - |

---

## 📌 Notes

- **Prochaine veille marché:** 2026-05-17 05:00 UTC
- **Go-live target:** 2026-06-15 (Phase E paper-deploy 30j signal-only)
- **Capital paper:** 10,000 €
- **Levier cible:** Élevé (scalp 0.2-0.5%)

---

*Rapport généré automatiquement par le système de scan trading quotidien.*  
*Données externes non vérifiées — à valider avant décision de trading.*
