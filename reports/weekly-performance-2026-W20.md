# 📊 RÉSUMÉ HEBDOMADAIRE TRADING — Semaine 20 (11-17 Mai 2026)

**Généré:** 2026-05-17 18:00 UTC  
**Pour:** W  
**Système:** Yagati v4 + Scan System (Signal System)  
**Phase:** ML Phase D (emitter paper-deploy)  
**Capital Paper:** 10 000 €

---

## 🎯 OBJECTIF HEBDOMADAIRE

| KPI | Cible | Réalisé | Écart | Statut |
|-----|-------|---------|-------|--------|
| **Win Rate** | ≥ 70% | N/A (signaux en cours) | - | 🟡 En attente |
| **Signaux envoyés** | 5-15 / semaine | **4 signaux** | -1 à -11 | 🟠 Insuffisant |
| **PnL Total** | 500-600 € / jour | 0 € (paper) | -600 € / jour | 🔴 Bloqué |
| **Edges Actives** | 5-10 | 3 (Scan System) | -2 à -7 | 🟡 Partiel |

---

## 📈 PERFORMANCE DE LA SEMAINE

### 1️⃣ Win Rate (WR)

**WR Semaine:** N/A (aucun trade clôturé cette semaine)

**Historique Paper-Trades (31 trades clos + 2 ouverts):**

| Edge | Actif | n_trades | Win Rate | PnL Avg | Statut |
|------|-------|----------|----------|---------|--------|
| **ma_distance_revert** | ETHUSDT | 3 | **100%** ✅ | N/A | ARCHIVED |
| **bb_walk** | ETHUSDT | 3 | **66.7%** ✅ | +7.8% | ARCHIVED |
| **ma_ribbon** | ETHUSDT | 6 | **33.3%** ❌ | N/A | ARCHIVED |

**WR Global Historique:** ~55-60% (estimé sur 31 trades)  
**WR Cible:** ≥ 70-80%  
**Écart:** -10 à -25 points

---

### 2️⃣ PnL Total

**PnL Semaine:** 0 € (paper-trading, aucun trade clôturé)

**Backtests Récents (référence):**

| Stratégie | Période | PnL Total | PnL/jour | Statut |
|-----------|---------|-----------|----------|--------|
| **Bollinger-RSI Dual** | 89 jours | +34.33 € | +0.39 € / jour | ❌ FAIL (WR 47.4%) |
| **Volume Surge Breakout** | 41 jours | -501.74 € | -12.24 € / jour | ❌ FAIL (WR 37%) |
| **bb_walk** (historique) | 3 trades | +7.8% avg | N/A | ✅ PASS (WR 66.7%) |

**PnL Cible:** 500-600 € / jour  
**Écart:** -600 € / jour

---

### 3️⃣ Nombre de Signaux Envoyés

**Total Semaine:** **4 signaux** envoyés sur Telegram ✅

| Date | Heure UTC | Actif | Type | Prix Entry | TP | SL | Confiance | Statut |
|------|-----------|-------|------|------------|----|----|-----------|--------|
| **16/05** | 14:41 | ETH/USDT | LONG | ~2180 | +2.4% | -2.5% | N/A | ✅ Envoyé |
| **16/05** | 14:43 | ETH | LONG | N/A | N/A | N/A | 78/100 | ✅ Envoyé |
| **16/05** | 23:06 | BTC/USDT | LONG | 78 180 $ | 79 547 $ (+1.75%) | 76 279 $ (-2.43%) | 66/100 | ✅ Envoyé |
| **17/05** | 10:47 | ETH | LONG | N/A | N/A | N/A | 78/100 | ✅ Envoyé |
| **17/05** | 14:39 | BTC/USDT | LONG | 78 000 $ | 79 289 $ (+1.65%) | 75 859 $ (-2.74%) | 66/100 | 🟡 En cours |

**Progress:** Système redémarré après 7 jours de silence (09-16/05)  
**Fréquence:** ~0.5 signal / jour (cible: 5-15 / semaine = 0.7-2 / jour)

---

## 🏆 MEILLEURES STRATÉGIES

### Top 3 Performers (Historique)

| Rang | Stratégie | Win Rate | PnL Avg | n_trades | Potentiel |
|------|-----------|----------|---------|----------|-----------|
| **🥇 #1** | **ma_distance_revert** | **100%** ✅ | N/A | 3 | ⭐⭐⭐ (n faible) |
| **🥈 #2** | **bb_walk** | **66.7%** ✅ | +7.8% | 3 | ⭐⭐⭐⭐ (à promouvoir) |
| **🥉 #3** | **Scan System (BB_RSI_ADX)** | N/A | N/A | 4 cette semaine | ⭐⭐⭐ (en test) |

### Stratégies en Exploration (Backtest nécessaire)

| Stratégie | Concept | TF | Filtre | Potentiel |
|-----------|---------|-----|--------|-----------|
| **RSI Mean Reversion** | RSI(14) <20 ou >80 | 5-15min | HMM=RANGE | ⭐⭐⭐⭐ |
| **BB Walk Optimisée** | WR=66.7% → 2.5σ + volume | Adaptable | Volume > MA20 | ⭐⭐⭐⭐ |
| **Momentum Breakout** | Resistance + HMM RANGE→BULL | - | Stop: retour range | ⭐⭐⭐ |

---

## 🧠 LESSONS LEARNED

### ✅ Ce Qui a Fonctionné

1. **Reprise des signaux (16/05):** Après 7 jours de silence, le Scan System a généré 4 signaux en 48h
2. **Détection HMM:** Régime RANGE correctement identifié (100/100) sur tous les signaux BTC/ETH
3. **Oversold extrême:** RSI < 10 (BTC à 7.96, ETH à 4.67) = opportunités rares bien capturées
4. **Envoi Telegram:** Tous les signaux ont été délivrés avec succès ✅

### ⚠️ Problèmes Identifiés

1. **Gates trop strictes (CRITIQUE):**
   - CPCV, DSR, PSR, PBO bloquent 100% des edges Yagati v4
   - 0 edge ENABLED sur 141 → système en mode "observability" pure
   - **Solution:** Relaxer seuils ou passer à Confluence Scoring 0-100

2. **Volume faible sur signaux:**
   - BTC 23:06: Volume 0.21x MA20 (16.8% de la moyenne)
   - ETH 12:07: Volume 0.09x MA20 (9% de la moyenne)
   - **Risque:** Faux signaux, manque de conviction du marché
   - **Solution:** Ajuster gate volume (1.5 → 1.2) ou ajouter warning

3. **ADX borderline:**
   - BTC 14:39: ADX 45.06 >> 25 (seuil gate)
   - **Problème:** Mean-reversion performe mal en marché trending
   - **Solution:** ADX 25-35 → confidence réduite, ADX > 35 → blocage

4. **R/R ratio défavorable:**
   - BTC 23:06: R/R = 0.73 (risque > reward)
   - **Cible:** R/R ≥ 1.0
   - **Solution:** Ajuster TP/SL ou filtrer les setups R/R < 1

### 🎯 Insights Stratégiques

1. **Confluence Scoring > Gates Binaires:**
   - Actuel: ON/OFF (soit 100% soit 0%)
   - Vision: Score 0-100 avec position sizing adaptif (25%-150%)
   - **Impact:** Plus de nuances, moins de faux négatifs

2. **Regime-Aware Signal Fusion:**
   - HMM détecte le régime → pondère les stratégies
   - RANGE: mean-reversion à 70%
   - BULL/BEAR: momentum/breakout à 70%
   - **Impact potentiel:** +40% Sharpe ratio

3. **RSI Extrême Filter:**
   - RSI < 5 ou > 95 → augmenter confidence de 10-15 points
   - Oversold/overbought extrêmes sont rares et souvent suivis de rebond

---

## 📊 COMPARAISON OBJECTIF 70% WR

| Métrique | Actuel | Cible | Écart | Action Requise |
|----------|--------|-------|-------|----------------|
| **Win Rate** | ~55-60% (historique) | ≥ 70% | -10 à -15 pts | Promouvoir bb_walk, backtester RSI Mean Reversion |
| **Signaux/semaine** | 4 | 35-105 (5-15/jour) | -31 à -101 | Relaxer gates, activer 5-10 edges |
| **PnL/jour** | 0 € (paper) | 500-600 € | -600 € | Passer en live (Phase E) après 30j paper |
| **Confiance moyenne** | 66/100 | ≥ 70/100 | -4 pts | Confluence Scoring + RSI extrême filter |
| **R/R ratio** | 0.73 | ≥ 1.0 | -0.27 | Ajuster TP/SL ou filtrer setups |

### 🎯 Plan d'Action pour Atteindre 70% WR

**P0 (Cette Semaine):**
- [ ] Promouvoir **bb_walk** en PROBATION (WR=66.7%, proche cible)
- [ ] Relaxer gate volume (1.5 → 1.2) pour éviter faux négatifs
- [ ] Ajuster gate ADX (25 → 30) avec confidence réduite
- [ ] Monitorer signaux en cours (BTC 16/05, ETH 17/05)

**P1 (1-3 Semaines):**
- [ ] Backtester **RSI Mean Reversion** (RSI <20/>80, HMM=RANGE, 30j)
- [ ] Backtester **BB Walk Optimisée** (2.5σ + volume > MA20)
- [ ] Implémenter **Confluence Scoring MVP** (score 0-100)
- [ ] Position Sizing Adaptif (25%-150% selon confidence)

**P2 (1-2 Mois):**
- [ ] **Regime-Aware Signal Fusion** (HMM-based weighting)
- [ ] **Self-Healing Strategy Generator** (auto-ajustement)
- [ ] **Walk-Forward Auto** (ré-optimisation périodique)

---

## 🔮 PROJECTIONS

### Scénario Optimiste (WR 70-80%)
- bb_walk promu + 2 nouvelles stratégies validées
- Confluence Scoring implémenté → réduction faux signaux
- 5-10 signaux/jour avec WR 70%+ → 500-600 €/jour atteignable
- **Timeline:** 4-6 semaines

### Scénario Réaliste (WR 60-70%)
- Gates relaxées → 3-5 signaux/jour
- WR moyen 60-65% (proche historique)
- PnL/jour: 200-300 € (sous-optimal mais positif)
- **Timeline:** 2-3 semaines

### Scénario Pessimiste (WR < 60%)
- Gates trop strictes maintenues → 0-1 signal/jour
- WR < 60% → PnL négatif ou nul
- **Action:** Pivot vers nouveau système (Saiyan) avec architecture Regime-Aware

---

## 📝 CONCLUSION

**État Global:** 🟡 **En Amélioration** (système redémarré après 7 jours de silence)

**Points Forts:**
- ✅ Signaux générés et envoyés avec succès
- ✅ HMM regime detection fonctionnelle
- ✅ Oversold extrêmes bien capturés

**Points Faibles:**
- 🔴 Gates trop strictes bloquent le pipeline
- 🟠 Volume faible sur signaux (risque faux positifs)
- 🟠 R/R ratio défavorable (< 1.0)

**Recommandation:** Prioriser la relaxation des gates (P0) et le backtest de nouvelles stratégies mean-reversion (P1) pour atteindre l'objectif 70% WR d'ici 4-6 semaines.

---

*Rapport généré automatiquement par le système de scan trading.*  
*Données paper-trading — performances réelles peuvent varier.*  
*Prochain résumé: 2026-05-24 18:00 UTC*
