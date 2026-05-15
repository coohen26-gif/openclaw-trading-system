# Backtest #2 : Bollinger-RSI Dual

## 📋 Synthèse Exécutive

**Statut : ❌ FAIL — Mean reversion sur prix avec confirmation RSI**

| Métrique | Résultat | Objectif | Écart |
|---|---|---|---|
| **Win Rate** | 47.4% | ≥70% | -22.6 pts ❌ |
| **PnL Total** | +34.33€ (+0.34%) | - | - |
| **PnL/jour** | +0.39€/jour | - | - |
| **Sharpe Ratio** | 1.09 | >1 | ✅ |
| **Max Drawdown** | -3.78% | <20% | ✅ |
| **Profit Factor** | 1.06 | >1.5 | ❌ |

---

## 📊 Données du Backtest

### Période
- **Start** : 2026-02-14
- **End** : 2026-05-15
- **Durée** : 89 jours

### Données
- **Symbol** : BTC/USDT
- **Timeframe** : 4h
- **Source** : Binance (CCXT)
- **N bougies** : 540

### Paramètres
| Paramètre | Valeur |
|---|---|
| **Bollinger Bands** | 20 périodes, 2.0σ |
| **RSI** | 14 périodes |
| **Thresholds RSI** | LONG < 30, SHORT > 70 |
| **Take Profit** | percent (0.8% si percent) |
| **Stop Loss** | 2.0%  |
| **Fees** | 0.1% |
| **Slippage** : 0.05% |
| **Capital** | 10000 € |
| **Levier** | 1x |

---

## 🔍 Analyse Détaillée

### 1. Performance par Type de Trade

| Type | N Trades | Win Rate | PnL Total |
|---|---|---|---|
| LONG | 7 | 57.1% | +88.60€ |
| SHORT | 12 | 41.7% | -54.27€ |

### 2. Distribution des Trades

```
Trades winners : 9/19 (47.4%)
Trades losers  : 10/19 (52.6%)

Gains moyens   : +67.09€
Pertes moyennes: -56.95€
Ratio G/P      : 1.18 (favorable)
```

### 3. Analyse par Exit Reason

| Exit Reason | N Trades | PnL Total | Avg PnL |
|---|---|---|---|
|  | 14 | -451.00€ | -32.21€ |
| TP_PERCENT | 5 | +485.33€ | +97.07€ |

### 4. Points Forts
- ❌ Win Rate < 70%
- ❌ Profit Factor ≤ 1.5
- ✅ Drawdown maîtrisé (<20%)
- ✅ Sharpe Ratio > 1

### 5. Points Faibles
- PnL quotidien à optimiser
- RAS

### 6. Ajustements Recommandés
- Tester BB à 2.5σ pour réduire les faux signaux
- Ajuster thresholds RSI (25/75 au lieu de 30/70)
- Tester TP à 0.5% au lieu du retour à la moyenne
- Ajouter filtre de volume

---

## 📈 Détail des Trades

| # | Entry Date | Exit Date | Type | Entry Price | Exit Price | Entry RSI | Exit RSI | Duration | PnL (€) | Exit Reason |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 02-23 00:00 | 02-23 04:00 | LONG | 64934.17 | 65958.94 | 28.6 | 35.3 | 4.0h | 🟢 +127.82 | EXIT_TP_PERCENT |
| 2 | 02-23 16:00 | 02-23 20:00 | LONG | 64295.10 | 64656.02 | 27.3 | 25.9 | 4.0h | 🟢 +26.47 |  |
| 3 | 02-28 04:00 | 02-28 08:00 | LONG | 63826.00 | 63844.20 | 19.7 | 17.1 | 4.0h | 🔴 -27.57 |  |
| 4 | 03-02 12:00 | 03-02 16:00 | SHORT | 69130.20 | 68966.53 | 73.8 | 72.7 | 4.0h | 🔴 -6.40 |  |
| 5 | 03-04 12:00 | 03-04 16:00 | SHORT | 73396.88 | 73611.10 | 78.4 | 78.2 | 4.0h | 🔴 -59.90 |  |
| 6 | 03-10 08:00 | 03-10 12:00 | SHORT | 70580.94 | 71346.16 | 72.3 | 73.8 | 4.0h | 🔴 -139.25 |  |
| 7 | 03-13 08:00 | 03-13 12:00 | SHORT | 72228.82 | 71831.46 | 71.6 | 66.8 | 4.0h | 🟢 +24.82 |  |
| 8 | 03-16 00:00 | 03-16 04:00 | SHORT | 73573.32 | 73456.68 | 74.2 | 76.4 | 4.0h | 🔴 -14.07 |  |
| 9 | 03-19 04:00 | 03-19 08:00 | LONG | 70191.17 | 69952.75 | 17.9 | 18.4 | 4.0h | 🔴 -63.53 |  |
| 10 | 03-22 08:00 | 03-22 12:00 | LONG | 68217.95 | 68847.96 | 26.5 | 32.8 | 4.0h | 🟢 +61.53 | EXIT_TP_PERCENT |
| 11 | 03-27 08:00 | 03-27 12:00 | LONG | 66702.78 | 66112.82 | 23.3 | 19.5 | 4.0h | 🔴 -117.62 |  |
| 12 | 04-05 20:00 | 04-06 00:00 | SHORT | 69034.18 | 69123.69 | 80.5 | 80.6 | 4.0h | 🔴 -42.16 |  |
| 13 | 04-07 20:00 | 04-08 00:00 | SHORT | 71924.22 | 71287.39 | 78.0 | 72.3 | 4.0h | 🟢 +57.20 | EXIT_TP_PERCENT |
| 14 | 04-17 12:00 | 04-17 16:00 | SHORT | 77785.02 | 77393.58 | 78.0 | 72.3 | 4.0h | 🟢 +19.97 |  |
| 15 | 04-19 20:00 | 04-20 00:00 | LONG | 73801.79 | 74634.00 | 13.9 | 26.8 | 4.0h | 🟢 +81.50 | EXIT_TP_PERCENT |
| 16 | 04-22 04:00 | 04-22 08:00 | SHORT | 78012.79 | 78300.00 | 75.5 | 73.8 | 4.0h | 🔴 -66.34 |  |
| 17 | 04-27 00:00 | 04-27 04:00 | SHORT | 79105.49 | 77606.60 | 71.2 | 51.8 | 4.0h | 🟢 +157.29 | EXIT_TP_PERCENT |
| 18 | 05-04 00:00 | 05-04 04:00 | SHORT | 80316.31 | 79696.75 | 74.0 | 66.0 | 4.0h | 🟢 +47.23 |  |
| 19 | 05-10 12:00 | 05-10 16:00 | SHORT | 81418.01 | 81437.83 | 80.8 | 76.3 | 4.0h | 🔴 -32.65 |  |

---

## 🎯 Conclusion

❌ FAIL — Ajustements nécessaires avant production

### Résumé
- **Win Rate** : 47.4% (objectif ❌)
- **Profit Factor** : 1.06 (objectif ❌)
- **PnL Total** : +34.33€ sur 89 jours
- **Risque** : Max DD -3.78%

### Prochaines Étapes
1. Optimiser paramètres (BB σ, RSI thresholds)
2. Tester sur données out-of-sample
3. Ajouter gestion de position sizing dynamique
4. Implémenter surveillance temps réel

---
*Généré le 2026-05-15 19:43 UTC*
