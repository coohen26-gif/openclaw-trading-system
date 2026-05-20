# 📊 Scan Trading Quotidien — 17 Mai 2026

**Généré:** 2026-05-17 05:00 UTC  
**Session:** cron:602099bf-77e6-4713-9656-26fb445d931d  
**Phase Système:** ML Phase D (emitter paper-deploy)  
**Statut Auto-Signaux:** ✅ ACTIF (1 signal détecté cette nuit)

---

## 1️⃣ État des Marchés

| Actif | Prix (17/05 05:00 UTC) | 24h | 7j | Régime HMM* | Tendance |
|---|---|---|---|---|---|
| **BTC** | $78,139 | +1.01% | +3.23% | RANGE | Consolidation post-$80k |
| **ETH** | $2,187 | +1.58% | +6.06% | RANGE | Rebond haussier |
| **SOL** | $86.87 | +1.90% | +6.92% | BULL | Forte momentum |
| **XRP** | $1.41 | +0.53% | +0.10% | BULL | Stable |
| **BNB** | $654.40 | +1.09% | +0.98% | RANGE | Consolidation |

*Régimes HMM mis à jour via heartbeat Scan System (dernière détection: 2026-05-17 01:06 UTC)

### 📈 Contexte Marché
- **Market Cap Total:** $2.78 Trillion (+0.3%)
- **Volume 24h Global:** $115B+
- **Sentiment:** Neutre à légèrement haussier
- **Catalyseur récent:** CLARITY Act (régulation crypto) voté au Sénat US → boost marché
- **BTC:** Correction après franchissement $80k, consolidation autour de $78k
- **ETH:** Performance supérieure (+6% sur 7j), outperforme BTC
- **SOL:** Momentum fort (+6.92% sur 7j), régime BULL confirmé

---

## 2️⃣ Performance des Edges

### 📊 Vue d'Ensemble (Signal System)

| Métrique | Valeur |
|---|---|
| **Stratégies Actives** | 3 (BB_RSI_ADX, ZSCORE_HMM, DOUBLE_BB) |
| **Signaux Détectés (24h)** | 1 ✅ |
| **Dernier Signal:** | BTC/USDT LONG @ $77,969 (01:06 UTC) |
| **Confiance Moyenne** | 65/100 |
| **Régime Dominant** | RANGE |

### 🎯 Performance Historique (Yagati v4 - Paper)

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

**Constat:** Le système de signaux (Scan System) est **actif et fonctionnel** avec 1 signal détecté cette nuit. Cependant, les backtests Yagati v4 historiques montrent des performances insuffisantes (WR < 65%).

---

## 3️⃣ Signaux Auto Générés

### ✅ État: ACTIF (1 signal depuis 24h)

| Timestamp | Type | Actif | Prix | TP | SL | Confiance | Régime | Statut |
|---|---|---|---|---|---|---|---|---|
| **2026-05-17 01:06 UTC** | LONG | BTC/USDT | $77,969 | $79,462 | $76,137 | 65/100 | RANGE | 🟡 En cours |

### 📊 Détails du Signal (BTC/USDT LONG)

**Indicateurs au moment du signal:**
- **BB Lower:** $77,105 | **BB Middle:** $79,462 | **BB Upper:** $81,819
- **RSI:** 4.67 (oversold extrême ⚠️)
- **ADX:** 27.15 (légèrement > 25, trend faible)
- **Volume:** 430.5 vs MA20: 2556 (volume faible ⚠️)
- **Prix vs BB Lower:** ✅ Prix touche la bande inférieure
- **RSI Oversold:** ✅ RSI < 28 (condition remplie)

**Analyse:**
- ✅ Conditions techniques remplies (prix ≤ BB Lower, RSI oversold)
- ⚠️ Volume faible (16.8% de la moyenne) → risque de faux signal
- ⚠️ ADX > 25 (seuil gate: 25) → légère tendance baissière
- 🟡 Confidence: 65/100 (au-dessus du seuil min 60)

### 📈 Historique Récent (16-17 Mai)

| Date | Signaux | Actifs | Types |
|---|---|---|---|
| 2026-05-16 14:43 UTC | 1 | ETH | LONG (score: 78, envoyé ✅) |
| 2026-05-17 01:06 UTC | 1 | BTC | LONG (score: 65, en cours) |

**Progress:** Le système génère à nouveau des signaux après 7 jours de silence (2026-05-09 → 2026-05-16).

---

## 4️⃣ Anomalies Détectées

| # | Anomalie | Sévérité | Impact | Statut |
|---|---|---|---|---|
| **A1** | 0 auto-signaux depuis 7 jours (09-16/05) | 🔴 CRITIQUE | Système trading inopérant | ✅ RÉSOLU (1 signal 16/05, 1 signal 17/05) |
| **A2** | 0 edges ENABLED sur 141 (Yagati v4) | 🟠 ÉLEVÉE | Pipeline R&D → PROD bloqué | ⚠️ EN COURS |
| **A3** | Gates trop strictes (CPCV, DSR, PSR, PBO) | 🟠 ÉLEVÉE | Filtre 100% des signaux | ⚠️ À REVIEW |
| **A4** | Backtests récents FAIL (WR < 65%) | 🟠 ÉLEVÉE | Stratégies actuelles non viables | ⚠️ À REVIEW |
| **A5** | Volume faible sur signal BTC (16.8% MA20) | 🟡 MOYENNE | Risque faux signal | 🟡 À SURVEILLER |
| **A6** | ADX > seuil gate (27.15 > 25) | 🟡 MOYENNE | Signal borderline | 🟡 À SURVEILLER |

### 🔍 Analyse des Anomalies Critiques

**A1 (RÉSOLU):** Le système Scan System a repris la génération de signaux:
- 2026-05-16 14:43: Signal ETH LONG (score 78, envoyé Telegram)
- 2026-05-17 01:06: Signal BTC LONG (score 65, en cours)

**A5 & A6 (NOUVELLES):** Le signal BTC présente des faiblesses:
- Volume anormalement faible (risque de manque de conviction)
- ADX légèrement au-dessus du seuil (trend faible mais présent)
- RSI extrême (4.67) → peut indiquer un overshoot ou un vrai rebond

---

## 5️⃣ Recommandations d'Ajustements

### 🚀 Priorité P0 (24-48h)

| Action | Description | Impact | Effort | Statut |
|---|---|---|---|---|
| **R1** | **Monitorer signal BTC en cours** | TP: +$1,493 (+1.9%), SL: -$1,832 (-2.3%) | 1h | 🟡 EN COURS |
| **R2** | **Vérifier envoi Telegram signal ETH (16/05)** | Confirmer delivery à W | 30min | ⏳ À FAIRE |
| **R3** | **Ajuster gate volume** | Volume multiplier 1.5 → 1.2 ou ajouter warning au lieu de blocage | 2h | ⏳ À FAIRE |
| **R4** | **Relaxer gate ADX** | ADX max 25 → 30 avec scoring adaptif | 2h | ⏳ À FAIRE |

### 📋 Priorité P1 (1-3 Semaines)

| Action | Description | Impact | Effort |
|---|---|---|---|
| **R5** | **Implémenter Confluence Scoring (MVP)** | Score 0-100 au lieu de BUY/SELL binaire | 8-12h |
| **R6** | **Regime-Aware Signal Fusion** | Pondérer stratégies selon HMM (ex: mean-reversion 70% en RANGE) | 2-3 semaines |
| **R7** | **Backtester RSI Mean Reversion** | RSI(14) <20/>80, TF 5-15min, HMM=RANGE (ETHUSDT, SOLUSDT, 30j) | 4-6h |
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
[✅] 1. Signal BTC détecté (01:06 UTC) → monitorer évolution
[ ] 2. Vérifier envoi Telegram signal ETH (16/05 14:43 UTC)
[ ] 3. Ajuster gate volume (1.5 → 1.2) pour éviter faux négatifs
[ ] 4. Ajuster gate ADX (25 → 30) avec warning au lieu de blocage
[ ] 5. Documenter performance signal BTC (TP/SL atteint ou non)
[ ] 6. Commit + push des ajustements gates
```

---

## 🎯 KPIs Cibles vs Actuels

| KPI | Actuel (17/05) | Cible | Écart | Trend |
|---|---|---|---|---|
| **Win Rate** | N/A (1 signal en cours) | ≥70-80% | - | 🟡 À déterminer |
| **Signaux/jour** | 0.5 (1 signal/2j) | 5-15 | -14.5 | 🟢 En amélioration |
| **PnL/jour** | 0€ (paper) | 500-600€ | -600€ | 🔴 Bloqué |
| **Edges Actives** | 3 (Scan System) | 5-10 | -2 à -7 | 🟢 Actif |
| **Confiance Moyenne** | 65/100 | ≥70/100 | -5 | 🟡 Correct |
| **Sharpe Ratio** | N/A | >1 | - | 🟡 À calculer |

---

## 📌 Notes

- **Prochaine veille marché:** 2026-05-18 05:00 UTC
- **Go-live target:** 2026-06-15 (Phase E paper-deploy 30j signal-only)
- **Capital paper:** 10,000 €
- **Levier cible:** Élevé (scalp 0.2-0.5%)
- **Signal BTC en cours:** TP à +1.9%, SL à -2.3% → RR ratio 0.81 (légèrement défavorable)

---

## 🔮 Insights Nocturnes (2026-05-17 02:00 UTC)

### Vision Stratégique
> "Le système reprend vie. Un signal BTC avec RSI à 4.67 est soit une opportunité en or, soit un piège. La clé: confluence scoring + position sizing adaptif."

### Idées à Explorer
1. **RSI Extrême Filter:** RSI < 5 ou > 95 → augmenter confidence de 10-15 points (oversold/overbought extrêmes sont rares)
2. **Volume Anomaly Detection:** Volume < 20% MA20 → réduire confidence de 20 points ou ajouter warning
3. **ADX Flex Gate:** ADX 25-35 → confidence réduite de 10%, ADX > 35 → blocage (trend trop fort pour mean-reversion)

---

*Rapport généré automatiquement par le système de scan trading quotidien.*  
*Données externes non vérifiées — à valider avant décision de trading.*  
*Signal BTC/USDT LONG en cours — monitorer jusqu'à TP ou SL.*
