# Semaine 30 - Mean Reversion v6 Résultats (25 Mai 2026)

**Date:** 25 Mai 2026, 12:15 UTC  
**Statut:** 🔴 ÉCHEC - Strategy underperforme sur données réelles

---

## 📊 Résultats Backtest v6

**Configuration testée:**
- RSI: 30/70
- Bollinger: 2.0σ
- TP: +5%, SL: -4%
- Time Exit: 7j max
- Position: 5%

**Données:** BTC/USDT Daily 2020-2026 (2337 jours)

### Résultats

| Période | Return | Sharpe | Max DD | Win Rate | N Trades |
|---------|--------|--------|--------|----------|----------|
| **Train (2020-2023)** | **-7.91%** | -0.74 | -8.49% | 36.8% | 136 |
| **Test (2024-2026)** | **-0.63%** | -0.12 | -2.77% | 45.9% | 74 |

**Verdict:** 🔴 **STRATÉGIE NON PROFITABLE**

---

## 🔍 Analyse des Causes d'Échec

### 1. Win Rate Trop Basse

- Train: 36.8% (vs cible 50%+)
- Test: 45.9% (vs cible 50%+)

**Problème:** Presque 1 trade sur 2 est perdant → edge statistique insuffisant

### 2. Plus de SL que de TP

**Test (2024-2026):**
- Take Profit: 21 (28%)
- Stop Loss: 29 (39%) ← **TROP**
- Time Exit: 24 (32%)

**Ratio TP/SL:** 0.72 (devrait être >1.0)

### 3. Avg PnL Négatif

- Train: -1.20% par trade
- Test: -0.16% par trade

**Problème:** Les pertes moyennes > gains moyens

### 4. Meilleur Trade vs Pire Trade

- Best: +14.19%
- Worst: -14.02%

**Ratio:** ~1:1 (devrait être >1.5:1)

---

## 💡 Insights Clés

### 1. Mean Reversion "Pure" Ne Fonctionne Pas

RSI < 30 OU BB < 2.0σ génère trop de faux signaux:
- Crypto peut rester oversold/overbought longtemps
- Pas de confirmation de "reversion imminente"
- Besoin de **catalyseur** pour le timing

### 2. Time Exit = Signal d'Échec

32% des trades sortent par temps (7j max):
- Prix n'atteint ni TP ni SL
- Signale que le signal d'entrée était **faible**
- Capital immobilisé sans mouvement

### 3. Test > Train (mais toujours négatif)

- Train: -7.91%
- Test: -0.63%

**Interprétation:** Mean reversion fonctionne MIEUX en 2024-2026 (range-bound) qu'en 2020-2023 (trending), mais toujours pas assez pour être profitable.

---

## 🎯 Décision: PIVOT Vers Approche Hybride

**Problème fondamental:** Mean reversion "pure" (RSI/BB seuls) n'a pas d'edge statistique.

**Solution:** Combiner mean reversion avec **confirmation momentum/catalyseur**

### Nouvelle Approche: "Mean Reversion + Momentum Confirmation"

**Logique:**
1. RSI/BB détectent niveau extrême (oversold/overbought)
2. **MAIS** on n'entre que si momentum court terme confirme le rebond
3. Évite d'attraper un couteau qui tombe

**Configuration à tester (v8):**
- RSI < 30 (oversold)
- **ET** prix > close d'hier (confirmation haussière)
- **ET** volume > 1.2x moyenne (intérêt)
- TP: +8%, SL: -4% (R/R 2:1)
- Time Exit: 10j

**Pourquoi ça pourrait marcher:**
- Filtre les "falling knives"
- Attend confirmation avant d'entrer
- Garde bon R/R ratio

---

## 📋 Prochaines Étapes

### Priorité P0 (24h)

1. **Implémenter v8** (Mean Rev + Momentum Confirmation)
2. **Backtester v8** sur mêmes données
3. **Comparer:** v6 vs v8

### Priorité P1 (48h)

Si v8 échoue:
- **Option A:** Retourner à Momentum + HMM (validé à +55%)
- **Option B:** Combiner Momentum + Mean Rev (regime-dependent)
  - Range regime → Mean Rev
  - Trend regime → Momentum

### Priorité P2 (72h)

- Documentation complète
- Décision architecture finale pour system-saiyan/v0.2

---

## 🧠 Leçons Apprises

1. **Backtest synthétique ≠ réel:** Données synthétiques montraient +6.9% return, 59% WR. Réel = -0.63%, 46% WR.

2. **Walk-forward validation = crucial:** A détecté l'échec avant déploiement.

3. **Mean reversion pure = dangereux:** Crypto peut trendre longtemps, RSI peut rester extrême.

4. **Confirmation requise:** Un indicateur seul (RSI/BB) ≠ edge. Besoin de confluence.

5. **Time exit révèle faiblesse:** Si trade n'atteint pas TP/SL, signal d'entrée était probablement mauvais.

---

## 📊 Comparaison: Momentum vs Mean Reversion

| Métrique | Momentum+HMM | Mean Rev v6 | Gagnant |
|----------|--------------|-------------|---------|
| **Return Test** | +55% | -0.63% | Momentum ✅ |
| **Sharpe** | 0.91 | -0.12 | Momentum ✅ |
| **Win Rate** | 57.1% | 45.9% | Momentum ✅ |
| **Max DD** | -7.5% | -2.77% | Mean Rev ✅ |
| **N Trades** | 63 | 74 | Similaire |

**Verdict:** Momentum + HMM surperforme Mean Reversion pure sur données réelles.

**Décision potentielle:** Abandonner Mean Reversion pure, garder Momentum + HMM comme stratégie principale.

---

*Mis à jour: 25 Mai 2026, 12:15 UTC*
