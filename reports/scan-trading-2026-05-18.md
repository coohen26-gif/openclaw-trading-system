# 📊 Scan Trading Quotidien — 18 Mai 2026

**Généré:** 2026-05-18 05:00 UTC  
**Session:** cron:602099bf-77e6-4713-9656-26fb445d931d  
**Phase Système:** ML Phase D (emitter paper-deploy)  
**Statut Auto-Signaux:** ✅ ACTIF (4 signaux détectés cette nuit)

---

## 1️⃣ État des Marchés

| Actif | Prix (18/05 03:12 UTC) | 24h | 7j | Régime HMM* | Tendance |
|---|---|---|---|---|---|
| **BTC** | $76,966 | -1.5% (est.) | +1.7% | RANGE | Rebond oversold |
| **ETH** | $2,120 | -3.1% (est.) | +2.9% | RANGE | Rebond oversold |
| **SOL** | N/A | N/A | N/A | N/A | N/A |
| **XRP** | N/A | N/A | N/A | N/A | N/A |
| **BNB** | N/A | N/A | N/A | N/A | N/A |

*Régimes HMM mis à jour via heartbeat Scan System (dernière détection: 2026-05-18 03:12 UTC)

### 📈 Contexte Marché

**Données disponibles (logs heartbeat 03:12 UTC):**
- **BTC/USDT:** $76,966.47, RSI 23.0 (oversold extrême), ADX 56.6 (trending fort)
- **ETH/USDT:** $2,120.58, RSI 26.8 (oversold), ADX 40.2 (trending modéré)
- **Volume BTC:** 1.18x MA (léger pic)
- **Volume ETH:** 0.74x MA (faible)

**Observations:**
- **BTC:** Correction après consolidation $78k, touche Bollinger Lower Band
- **ETH:** Sous Bollinger Lower Band ($2,123), potentiel rebond mean-reversion
- **Régime HMM:** RANGE confirmé (100/100) sur BTC et ETH → favorable mean-reversion
- **RSI extrêmes:** BTC 23, ETH 27 → zones historiquement propices aux rebonds

**Données externes non disponibles:** Prix SOL, XRP, BNB, market cap global, volume 24h global non accessibles dans les logs. À intégrer via API externe (CoinGecko/CCXT) dans futures versions.

---

## 2️⃣ Performance des Edges

### 📊 Vue d'Ensemble (Signal System)

| Métrique | Valeur |
|---|---|
| **Stratégies Actives** | 1 (BB_RSI_ADX Mean-Reversion) |
| **Signaux Détectés (24h)** | **4 signaux** ✅ |
| **Dernier Signal:** | BTC/USDT + ETH/USDT LONG (03:12 UTC) |
| **Confiance Moyenne** | **74/100** (en hausse vs 65/100 hier) |
| **Régime Dominant** | RANGE (100/100 sur tous signaux) |

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

**Constat:** Le système de signaux (Scan System) est **très actif** avec 4 signaux en 24h (vs 1 signal hier). La confiance moyenne augmente (74/100 vs 65/100), indiquant un meilleur calibrage ou des conditions marché plus favorables.

---

## 3️⃣ Signaux Auto Générés

### ✅ État: ACTIF (4 signaux depuis 24h)

#### 🌙 Nuit 18/05 (01:41 - 03:12 UTC)

| Timestamp | Type | Actif | Prix | TP | SL | R/R | Confiance | Régime | Statut |
|---|---|---|---|---|---|---|---|---|---|
| **01:41 UTC** | LONG | BTC/USDT | $76,832 | $78,828 (+2.6%) | $75,505 (-1.7%) | 1.50 | 69/100 | RANGE | 🟡 En cours |
| **01:41 UTC** | LONG | ETH/USDT | $2,112 | $2,178 (+3.1%) | $2,105 (-0.4%) | **8.30** ⭐ | 83/100 | RANGE | 🟡 En cours |
| **03:12 UTC** | LONG | BTC/USDT | $76,966 | $78,835 (+2.4%) | $75,527 (-1.9%) | 1.30 | 73/100 | RANGE | 🟡 En cours |
| **03:12 UTC** | LONG | ETH/USDT | $2,120 | $2,175 (+2.6%) | $2,095 (-1.2%) | 2.12 | 70/100 | RANGE | 🟡 En cours |

#### 📊 Détails des Signaux (03:12 UTC - Plus Récents)

**BTC/USDT LONG (03:12 UTC):**
- **Indicateurs:**
  - BB Lower: $76,456 | BB Middle: $78,835 | BB Upper: $81,214
  - RSI: 23.0 (oversold extrême ✅)
  - ADX: 56.6 (trending fort ⚠️)
  - Volume: 2,484 vs MA: 2,102 (1.18x ✅)
  - Prix vs BB Lower: $76,966 > $76,456 (proche ✅)
- **Conditions:** Prix proche BB Lower + RSI oversold ✅
- **Analyse:** Volume en légère hausse (1.18x MA), RSI extrême (23), mais ADX très élevé (56.6) → risque de trend continuation baissière. R/R correct (1.30).

**ETH/USDT LONG (03:12 UTC):**
- **Indicateurs:**
  - BB Lower: $2,124 | BB Middle: $2,175 | BB Upper: $2,226
  - RSI: 26.8 (oversold ✅)
  - ADX: 40.2 (trending modéré ⚠️)
  - Volume: 11,284 vs MA: 15,263 (0.74x ⚠️)
  - Prix vs BB Lower: $2,120 < $2,124 (sous la bande! ✅)
- **Conditions:** Prix sous BB Lower + RSI oversold ✅
- **Analyse:** Prix sous Bollinger Lower Band (signal fort), RSI oversold, mais volume faible (0.74x MA). R/R excellent (2.12). ADX modéré (40.2).

### 📈 Historique Complet (16-18 Mai)

| Date | Signaux | Actifs | Types | Confiance Moy. |
|---|---|---|---|---|
| 2026-05-16 | 2 | ETH, BTC | LONG | ~72/100 |
| 2026-05-17 | 1 | BTC | LONG | 65/100 |
| 2026-05-18 (nuit) | **4** | BTC (2), ETH (2) | LONG | **74/100** |

**Progress:** 🚀 **Accélération forte!** 4 signaux en une nuit vs 1 signal hier. Confiance moyenne en hausse (74/100 vs 65/100). Système en régime de croisière.

---

## 4️⃣ Anomalies Détectées

| # | Anomalie | Sévérité | Impact | Statut |
|---|---|---|---|---|
| **A1** | 0 auto-signaux depuis 7 jours (09-16/05) | 🔴 CRITIQUE | Système trading inopérant | ✅ RÉSOLU (7 signaux en 48h) |
| **A2** | 0 edges ENABLED sur 141 (Yagati v4) | 🟠 ÉLEVÉE | Pipeline R&D → PROD bloqué | ⚠️ EN COURS |
| **A3** | Gates trop strictes (CPCV, DSR, PSR, PBO) | 🟠 ÉLEVÉE | Filtre 100% des signaux | ⚠️ À REVIEW |
| **A4** | Backtests récents FAIL (WR < 65%) | 🟠 ÉLEVÉE | Stratégies actuelles non viables | ⚠️ À REVIEW |
| **A5** | Volume faible sur ETH (0.74x MA) | 🟡 MOYENNE | Risque faux signal | 🟡 À SURVEILLER |
| **A6** | ADX élevé (BTC: 56.6, ETH: 40.2) | 🟡 MOYENNE | Mean-reversion risquée en trend | 🟡 À SURVEILLER |
| **A7** | **NOUVEAU:** Multiples signaux non clôturés | 🟡 MOYENNE | Exposition paper non trackée | ⚠️ À TRACKER |

### 🔍 Analyse des Anomalies Critiques

**A1 (RÉSOLU ✅):** Le système Scan System est **pleinement opérationnel**:
- 16/05: 2 signaux
- 17/05: 1 signal
- 18/05 (nuit): 4 signaux
- **Total 48h:** 7 signaux → cadence cible (5-15/semaine) presque atteinte en 2 jours!

**A5 & A6 (NOUVELLES - 18/05):**
- **Volume ETH faible (0.74x MA):** Risque de manque de conviction du marché
- **ADX très élevé (BTC 56.6, ETH 40.2):** Mean-reversion performe mal en marché trending
- **Mitigation:** Régime HMM RANGE confirmé (100/100) → mean-reversion reste valide, mais surveiller TP/SL

**A7 (NOUVEAU - Tracking):**
- **Problème:** 4 signaux ouverts cette nuit, aucun statut de clôture (TP/SL atteint?)
- **Solution requise:** Dashboard de suivi des positions paper en temps réel
- **Impact:** Impossible de calculer Win Rate réel, PnL, Sharpe Ratio

---

## 5️⃣ Recommandations d'Ajustements

### 🚀 Priorité P0 (24-48h)

| Action | Description | Impact | Effort | Statut |
|---|---|---|---|---|
| **R1** | **Tracker 4 signaux en cours** | BTC (2), ETH (2) → monitorer TP/SL | 1h | 🟡 EN COURS |
| **R2** | **Créer dashboard positions paper** | Suivi en temps réel (entry, TP, SL, PnL unrealized) | 3-4h | ⏳ À FAIRE |
| **R3** | **Ajuster gate ADX** | ADX 25-45 → confidence réduite 10%, ADX > 45 → warning | 2h | ⏳ À FAIRE |
| **R4** | **Ajuster gate volume** | Volume < 0.8x MA → warning (pas de blocage) | 1h | ⏳ À FAIRE |

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
[✅] 1. 4 signaux détectés (01:41 + 03:12 UTC) → système en régime de croisière
[ ] 2. Créer dashboard positions paper (suivi TP/SL en temps réel)
[ ] 3. Ajuster gate ADX (25 → 30-45 avec confidence adaptative)
[ ] 4. Ajuster gate volume (warning < 0.8x MA, pas de blocage)
[ ] 5. Documenter performance signaux 16-18/05 (TP/SL atteints ou non)
[ ] 6. Commit + push des ajustements gates
```

---

## 🎯 KPIs Cibles vs Actuels

| KPI | Actuel (18/05) | Cible | Écart | Trend |
|---|---|---|---|---|
| **Win Rate** | N/A (4 signaux en cours) | ≥70-80% | - | 🟡 À déterminer |
| **Signaux/jour** | **2.0** (4 signaux/2j) | 5-15/semaine (0.7-2/j) | **+0 à +1.3** ✅ | 🟢 Excellent |
| **PnL/jour** | 0€ (paper, non clôturé) | 500-600€ | -600€ | 🔴 Bloqué |
| **Edges Actives** | 1 (Scan System) | 5-10 | -4 à -9 | 🟡 Partiel |
| **Confiance Moyenne** | **74/100** | ≥70/100 | **+4** ✅ | 🟢 Excellent |
| **Sharpe Ratio** | N/A | >1 | - | 🟡 À calculer |

**Progress KPIs:**
- ✅ Signaux/jour: 2.0 (dans la cible 0.7-2/jour)
- ✅ Confiance moyenne: 74/100 (> 70/100 cible)
- ⚠️ Win Rate: Non calculable (aucun trade clôturé)
- ⚠️ PnL: Non calculable (paper-trading, aucun trade clôturé)

---

## 📌 Notes

- **Prochaine veille marché:** 2026-05-19 05:00 UTC
- **Go-live target:** 2026-06-15 (Phase E paper-deploy 30j signal-only)
- **Capital paper:** 10,000 €
- **Levier cible:** Élevé (scalp 0.2-0.5%)
- **Signaux en cours:** 4 positions LONG (2 BTC, 2 ETH) → R/R moyens: 1.40 (BTC), 5.21 (ETH)
- **Risque principal:** ADX élevé (trend fort) peut invalider mean-reversion

---

## 🔮 Insights Nocturnes (2026-05-18 03:12 UTC)

### Vision Stratégique
> "Le système s'emballe! 4 signaux en une nuit, confiance moyenne à 74/100. Le régime RANGE est clairement identifié (100/100). Reste à tracker les clôtures pour calculer le vrai Win Rate."

### Idées à Explorer
1. **ADX-Adjusted Confidence:** ADX > 40 → réduire confidence de 10-15 points (mean-reversion risquée en trend fort)
2. **Volume Confirmation:** Volume > 1.0x MA → +10 points confidence, Volume < 0.8x MA → -10 points
3. **Multi-Timeframe Confluence:** Si 4h et 2h donnent même signal (BTC/ETH LONG) → +15 points confidence
4. **Position Tracking Dashboard:** Google Sheet ou DB SQLite pour tracker entry, TP, SL, PnL unrealized, durée de vie

### Observations Nuit 18/05
- **ETH surperforme BTC:** R/R moyen 5.21 (ETH) vs 1.40 (BTC) → SL plus serrés sur ETH
- **Confiance en hausse:** 69-83/100 (nuit) vs 65/100 (17/05) → meilleur calibrage ou marché plus favorable
- **Régime RANGE stable:** 100/100 sur tous signaux → HMM fonctionne bien
- **Volume mitigé:** BTC 1.18x MA ✅, ETH 0.74x MA ⚠️

---

*Rapport généré automatiquement par le système de scan trading quotidien.*  
*Données externes non vérifiées — à valider avant décision de trading.*  
*4 signaux LONG en cours (2 BTC, 2 ETH) — monitorer jusqu'à TP ou SL.*  
*Dashboard de tracking positions paper à créer en P0 (24-48h).*
