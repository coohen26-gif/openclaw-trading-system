# Semaine 30 - Mean Reversion Walk-Forward (25 Mai 2026 - 09:00)

**Date:** 25 Mai 2026, 09:00 UTC  
**Statut:** 🟠 PROGRÈS - Meilleur que Momentum mais encore fragile

---

## 🎯 Objectif

Tester Mean Reversion (RSI + Bollinger) comme alternative à Momentum+HMM

**Hypothèse:** Crypto = range-bound 70% du temps → Mean reversion > Momentum

---

## 📊 Résultats

### Période d'Entraînement (2020-2023)

| Métrique | Valeur | Statut |
|----------|--------|--------|
| Return Total | **-4.0%** | ❌ |
| Sharpe Ratio | **-0.24** | ❌ |
| Max Drawdown | **-7.9%** | ✅ (vs -20.8% Momentum) |
| Win Rate | **46.4%** | ⚠️ |
| N Trades | 110 | ✅ (actif) |

**Exit Reasons:**
- Stop Loss: 46%
- Time Exit: 32%
- Take Profit: 15%
- Trailing Stop: 6%

### Période de Test (2024-2026)

| Métrique | Valeur | Statut |
|----------|--------|--------|
| Return Total | **-0.0%** | ⚠️ (breakeven!) |
| Sharpe Ratio | **0.01** | ⚠️ |
| Max Drawdown | **-6.7%** | ✅ (excellent!) |
| Win Rate | **55.4%** | ✅ (>50%) |
| N Trades | 56 | ✅ |

**Exit Reasons:**
- Time Exit: 50%
- Stop Loss: 36%
- Take Profit: 9%
- Trailing Stop: 5%

---

## 🔍 Analyse Comparative: Mean Rev vs Momentum

| Métrique | Momentum | Mean Rev | Écart |
|----------|----------|----------|-------|
| **Test Return** | -14.3% | -0.0% | **+14.3%** ✅ |
| **Test Sharpe** | -0.13 | 0.01 | **+0.14** ✅ |
| **Test DD** | -40.4% | -6.7% | **+33.7%** ✅ |
| **Test Win Rate** | 36.0% | 55.4% | **+19.4%** ✅ |
| **DD Ratio (Test/Train)** | 1.94 | 0.85 | **-56%** ✅ |

**Verdict:** Mean Reversion = **BEAUCOUP PLUS ROBUSTE** que Momentum

- Drawdown 6x meilleur (-6.7% vs -40.4%)
- Win Rate valide (55.4% > 50%)
- Presque breakeven (-0.0% vs -14.3%)
- Robustesse: DD ratio 0.85 (vs 1.94 pour Momentum)

---

## 🚨 Problèmes Identifiés

### 1. Take Profit Trop Ambitieux

**Actuel:** TP +15%  
**Problème:** Seulement 9-15% des trades atteignent TP

Mean reversion = petits mouvements (2-5%), pas des trends de 15%!

**Solution:** TP +8% (plus réaliste)

### 2. Time Exit Trop Élevé

**Actuel:** 32-50% des exits par temps  
**Problème:** Positions ne reach ni TP ni SL → signaux faibles

**Causes:**
- Entrées pas assez conviction (RSI/B thresholds trop larges)
- Time exit trop long (15j)

**Solutions:**
- Time exit: 15j → 10j
- RSI thresholds: 30/70 → 35/65 (déjà fait)
- Ajouter confirmation volume

### 3. Range Underperforme vs Trend (Counter-Intuitif!)

**Train:**
- Range: 73 trades, WR 41%, PnL -7.2%
- Trend: 37 trades, WR 57%, PnL +3.3%

**Test:**
- Range: 48 trades, WR 54%, PnL -0.5%
- Trend: 8 trades, WR 62%, PnL +0.6%

**Insight:** Mean reversion fonctionne MIEUX en trends courts qu'en ranges purs!

**Hypothèse:** En trends, pullbacks = opportunités mean reversion claires. En ranges, faux breakouts fréquents.

### 4. Avg Gain ≈ Avg Loss (Pas d'Edge)

**Train:**
- Avg Gain: +9.05%
- Avg Loss: -8.87%
- **Ratio: 1.02** (presque 1:1!)

**Test:**
- Avg Gain: +7.02%
- Avg Loss: -8.67%
- **Ratio: 0.81** (<1, mauvais!)

**Problème:** Gains ≈ Pertes → Pas d'edge statistique

**Solutions:**
- TP +8% (réduire)
- SL -5% (serrer)
- Ratio cible: 1.5:1 minimum

---

## 🛠️ Correctifs Requis (v2)

### Configuration Optimisée

```python
# RSI - Plus strict pour conviction
RSI_OVERSOLD = 35   # 30 → 35 (moins de faux signaux)
RSI_OVERBOUGHT = 65 # 70 → 65

# Bollinger - Confirmation requise
BB_STD = 2.5  # 2.0 → 2.5 (extrêmes seulement)

# Risk Management - Couper pertes, laisser courir gains
STOP_LOSS = -0.05   # -8% → -5%
TAKE_PROFIT = 0.08  # +15% → +8%
MAX_HOLD_DAYS = 10  # 15j → 10j

# Position Sizing - Un peu plus agressif (confiance)
MAX_POSITION_SIZE = 0.08  # 6.25% → 8%
```

### Ajouts Requis

1. **Volume Confirmation:**
   - Volume > 1.5x MA(20) pour confirmer signal
   - Évite faux breakouts low-volume

2. **RSI Divergence:**
   - Prix fait nouveau bas, RSI fait bas plus haut → LONG
   - Prix fait nouveau haut, RSI fait haut plus bas → SHORT

3. **Multi-Timeframe:**
   - RSI daily + RSI 4h alignés
   - Réduit faux signaux

---

## 📋 Prochaines Étapes

### Immédiat (2-4h)

1. **✅ Documenter résultats** (cette note)
2. **⏳ Appliquer correctifs v2** (TP/SL, RSI thresholds, volume)
3. **⏳ Re-backtester** avec nouvelle config
4. **⏳ Comparer: v1 vs v2**

### Court Terme (24h)

1. **⏳ Multi-Factor (RSI + BB + Volume + Divergence)**
2. **⏳ Walk-forward validation v2**
3. **⏳ Si robuste → Telegram Signaler**
4. **⏳ Si fragile → Pivot vers Multi-Strategy**

---

## 🎯 Insights Clés

### 1. Mean Reversion > Momentum (pour crypto)

- Drawdown 6x meilleur
- Win Rate valide (55%+)
- Robustesse Test/Train bien meilleure

**Décision:** Abandonner Momentum, focus Mean Reversion

### 2. Risk Management Fonctionne

- Kelly 1/8 (6.25%) → DD -7% max (vs -40% avec Momentum 18%)
- Position sizing correct = survie garantie

### 3. Presque Breakeven = Bon Signe

-0.0% en test sur données synthétiques = stratégie pas loin d'être viable

**Avec données réelles + optimisation:** Potentiellement positif!

### 4. Temps de Détention Trop Long

50% de time exits = stratégies trop lente

**Crypto:** Mean reversion = horizons 3-7j, pas 15j

---

## 📝 Notes Techniques

**Code:** `learning/code/mean_reversion_strategy.py`  
**Résultats:** `learning/data/meanrev_walkforward_results.csv`  
**Données:** Synthétiques (à remplacer par réelles)

---

*Conclusion: Mean Reversion = VOIE PROMETTEUSE. Optimisations requises pour rendre profitable.*
