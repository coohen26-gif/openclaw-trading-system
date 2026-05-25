# Semaine 30 - Walk-Forward Validation (25 Mai 2026)

**Date:** 25 Mai 2026, 08:30 UTC  
**Statut:** ⚠️ ÉCHEC VALIDATION - Stratégie fragile

---

## 🎯 Objectif

Valider robustesse stratégie Momentum+HMM sur données hors échantillon:
- **Train:** 2020-2023 (3 ans)
- **Test:** 2024-2026 (2 ans)

---

## 📊 Résultats

### Période d'Entraînement (2020-2023)

| Métrique | Valeur |
|----------|--------|
| Return Total | **+114.1%** ✅ |
| Sharpe Ratio | **0.81** ✅ |
| Max Drawdown | **-20.8%** ⚠️ |
| Win Rate | **47.5%** ⚠️ |
| N Trades | 80 |

**Exit Reasons:**
- Stop Loss: 49%
- Take Profit: 39%
- Time Exit: 12%

### Période de Test (2024-2026)

| Métrique | Valeur |
|----------|--------|
| Return Total | **-14.3%** ❌ |
| Sharpe Ratio | **-0.13** ❌ |
| Max Drawdown | **-40.4%** ❌ |
| Win Rate | **36.0%** ❌ |
| N Trades | 50 |

**Exit Reasons:**
- Stop Loss: 56%
- Take Profit: 22%
- Time Exit: 22%

---

## 🚨 Verdict: STRATÉGIE FRAGILE

**Critères de robustesse (TOUS ÉCHOUÉS):**

| Critère | Résultat | Cible | Statut |
|---------|----------|-------|--------|
| Sharpe Test/Train | -0.16 | >0.7 | ❌ |
| DD Test/Train | 1.94 | <1.5 | ❌ |
| Win Rate Test | 36.0% | >50% | ❌ |

---

## 🔍 Analyse des Problèmes

### 1. Overfitting Massif

**Return:** +114% (train) → -14% (test)  
**Gap:** -128% !

La stratégie apprend le bruit du passé, pas des signaux généralisables.

### 2. Momentum Signal Trop Simple

Signal actuel:
```python
if regime in ['Bull', 'Volatile Bull'] and momentum_5 > 0.02:
    signal = 'LONG'
elif regime == 'Bear' and momentum_5 < -0.02:
    signal = 'SHORT'
```

**Problèmes:**
- Momentum 5j seul ne capture pas trends réels
- Seuil 2% arbitraire
- Pas de confirmation multi-timeframe
- Pas de filtration volume/volatilité

### 3. HMM Clustering - Pas de Valeur Ajoutée

Le clustering KMeans sur (mean, vol, momentum) ne prédit PAS les régimes futurs.

**Pourquoi:**
- Régimes détectés = backward-looking
- Pas de persistance des régimes dans crypto
- Crypto = mean-reverting sur horizons courts

### 4. Position Sizing - Toujours Trop Agressif

Même avec configuration "conservatrice":
- Bull: 18.75% capital
- VolBull: 12.5%

→ Drawdown -40% en test! Kelly quarter est TROP pour crypto.

---

## 💡 Insights Clés

### 1. Momentum Simple ≠ Edge

Momentum pur sur crypto:
- Fonctionne en backtest (look-ahead bias implicite)
- Échoue en test (régimes changent trop vite)
- **Leçon:** Besoin de multi-factor ou mean-reversion

### 2. HMM ≠ Oracle

HMM détecte régimes PASSÉS, ne prédit PAS futurs.

**Alternative:**
- Utiliser HMM comme filtre (pas comme signal)
- Combiner avec autres indicateurs (RSI, volume, on-chain)
- Ou abandonner HMM pour règles simples

### 3. Risk Management > Signal

Même avec mauvais signal, bon risk management peut sauver.

**Mais:** Position sizing actuel (même 18%) → DD -40%

**Solution:** Kelly 1/8 ou 1/16 (3-6% capital max)

### 4. Crypto 2024-2026 ≠ 2020-2023

**2020-2023:** COVID, bull run, FTX crash → trends clairs  
**2024-2026:** Range-bound, choppy, faux breakouts → momentum échoue

**Leçon:** Stratégie doit s'adapter ou détecter "no-trade" regimes.

---

## 🛠️ Correctifs Requis (P0)

### Option A: Abandonner Momentum+HMM

**Vers:** Mean-Reversion + Range Detection

```python
# Range market detection
if volatility < threshold AND abs(momentum) < threshold:
    # Mean reversion
    if RSI < 30: LONG
    if RSI > 70: SHORT
else:
    # Trend following (seulement si trend clair)
    if ADX > 25 AND momentum > threshold: LONG
```

### Option B: Multi-Factor Signal

**Combiner:**
1. Momentum (5j, 10j, 20j)
2. Mean-reversion (RSI, Bollinger)
3. Volume confirmation
4. On-chain metrics (si dispo)
5. Regime filter (HMM ou règles simples)

**Signal = weighted sum** (seulement si > threshold)

### Option C: Regime-Adaptive

**Détection:**
- Bull: Trend following
- Bear: Short ou cash
- Range: Mean reversion
- Volatile: Cash ou très petit size

**Mais:** Détection doit être ROBUSTE (pas HMM seul)

---

## 📋 Prochaines Étapes

### Immédiat (24h)

1. **✅ Documenter échec** (cette note)
2. **⏳ Décider pivot:** Momentum → Mean-Reversion ou Multi-Factor?
3. **⏳ Réduire position sizing:** 18% → 6% max (Kelly 1/8)
4. **⏳ Ajouter filtre "no-trade"** (volatilité trop basse/haute)

### Court Terme (3-7 jours)

1. **⏳ Implémenter Mean-Reversion** (RSI + Bollinger)
2. **⏳ Backtester sur mêmes données**
3. **⏳ Comparer: Momentum vs Mean-Rev vs Multi-Factor**
4. **⏳ Choisir meilleure approche**

---

## 🎯 Leçon Principale

**Walk-Forward Validation = CRUCIAL**

Sans cette validation, j'aurais déployé une stratégie:
- +114% en backtest (faux!)
- -14% en réel (catastrophe)

**Le walk-forward a sauvé le portfolio.**

---

## 📝 Notes Techniques

**Données:** Synthétiques (fichier BTC non trouvé)  
**À faire:** Utiliser données réelles pour validation finale

**Code:** `learning/code/backtest_walkforward.py`  
**Résultats:** `learning/data/walkforward_results.csv`

---

*Conclusion: Stratégie actuelle NON VALIDÉE. Pivot requis avant production.*
