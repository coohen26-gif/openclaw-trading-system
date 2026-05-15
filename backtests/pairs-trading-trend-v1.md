# Backtest #4 : Pairs Trading Trend-Following BTC-ETH v1

## 📋 Synthèse Exécutive

**Statut : ❌ FAIL — Stratégie trend-following du ratio**

| Métrique | Résultat | Objectif | Écart |
|---|---|---|---|
| **Win Rate** | 36.4% | ≥60% | -23.6 pts ❌ |
| **PnL Total** | -432.91€ (-4.33%) | - | - |
| **PnL/jour** | -4.86€/jour | - | - |
| **Sharpe Ratio** | -11.76 | >1 | ❌ |
| **Max Drawdown** | -4.79% | <20% | ✅ |
| **Profit Factor** | 0.47 | >1.2 | ❌ |

---

## 📊 Données du Backtest

### Période
- **Start** : 2026-02-14
- **End** : 2026-05-15
- **Durée** : 89 jours

### Données
- **Timeframe** : 4h
- **Source** : Binance (CCXT)
- **N bougies** : 540
- **Corrélation BTC-ETH** : 0.906

### Paramètres (Trend-Following v1)
| Paramètre | Valeur |
|---|---|
| MA | 20 périodes |
| Entry | Z-score > +2.0 ou < -2.0 |
| Exit | Z-score < +0.5 (longs) ou > -0.5 (shorts) |
| Stop-loss | Z-score > ±3.5 (adverse move) |
| Fees | 0.1% |
| Slippage | 0.05% |
| Capital | 10000 € |
| Levier | 1x |

---

## 🔍 Analyse Détaillée

### 1. Concept Trend-Following

Contrairement à la mean-reversion (Backtest #1), cette stratégie **suit le trend** du ratio BTC/ETH :

- **Z > +2** → Ratio monte fort → **LONG BTC + SHORT ETH** (on suit la hausse)
- **Z < -2** → Ratio descend fort → **SHORT BTC + LONG ETH** (on suit la baisse)
- **Sortie** : Quand le trend faiblit (Z retour vers 0)

### 2. Distribution des Trades

```
Trades winners : 8/22 (36.4%)
Trades losers  : 14/22 (63.6%)

Gains moyens   : +48.71€
Pertes moyennes: -58.76€
Ratio G/P      : 0.83 (défavorable)
```

### 3. Comparaison avec Mean-Reversion (Backtest #1)

| Métrique | Mean-Rev v1 | Trend-Follow v1 | Delta |
|---|---|---|---|
| Win Rate | 45.5% | 36.4% | -9.1 pts |
| PnL Total | -521.52€ | -432.91€ | +88.61€ |
| Profit Factor | 0.35 | 0.47 | +0.12 |
| Max DD | -5.90% | -4.79% | +1.11 pts |

---

## 💡 Observations

### Points forts
- (objectif ≥60% non atteint ❌) Win Rate ≥ 60%
- (objectif >1.2 non atteint ❌) Profit Factor > 1.2
- ✅ Drawdown maîtrisé (<20%)
- ❌ Sharpe > 1

### Points faibles
- Trend following capture mieux les mouvements directionnels que mean-reversion

### Pistes d'amélioration
- Ajuster Z-entry (±2.5 pour moins de signaux mais meilleure qualité)
- Ajouter filtre de momentum (RSI, ADX)
- Tester trailing stop au lieu de fixed exit
- Explorer timeframe 1D pour réduire le noise

---

## 📈 Détail des Trades

| # | Date Entry | Date Exit | Type | Entry Z | Exit Z | Duration | PnL (€) | Exit Reason |
|---|---|---|---|---|---|---|---|---|
| 1 | 02-22 16:00 | 02-22 20:00 | LONG_BTC_SHORT_ETH | 2.17 | 0.48 | 4.0h | 🔴 -70.25 | EXIT_TREND_WEAKENED |
| 2 | 02-23 00:00 | 02-23 04:00 | LONG_BTC_SHORT_ETH | 2.88 | 2.87 | 4.0h | 🟢 +5.86 |  |
| 3 | 02-25 08:00 | 02-25 12:00 | SHORT_BTC_LONG_ETH | -2.81 | -3.20 | 4.0h | 🟢 +112.71 |  |
| 4 | 03-08 08:00 | 03-08 12:00 | LONG_BTC_SHORT_ETH | 2.02 | 1.69 | 4.0h | 🔴 -32.82 |  |
| 5 | 03-13 00:00 | 03-13 04:00 | SHORT_BTC_LONG_ETH | -2.61 | -0.49 | 4.0h | 🔴 -152.16 | EXIT_TREND_WEAKENED |
| 6 | 03-15 20:00 | 03-16 00:00 | SHORT_BTC_LONG_ETH | -3.00 | -3.43 | 4.0h | 🟢 +123.46 |  |
| 7 | 03-19 12:00 | 03-19 16:00 | LONG_BTC_SHORT_ETH | 2.04 | 1.96 | 4.0h | 🔴 -11.98 |  |
| 8 | 03-23 00:00 | 03-23 04:00 | LONG_BTC_SHORT_ETH | 2.07 | 2.89 | 4.0h | 🟢 +46.26 |  |
| 9 | 03-26 08:00 | 03-26 12:00 | LONG_BTC_SHORT_ETH | 2.77 | 2.27 | 4.0h | 🔴 -67.50 |  |
| 10 | 03-30 00:00 | 03-30 04:00 | SHORT_BTC_LONG_ETH | -2.11 | -2.65 | 4.0h | 🟢 +18.68 |  |
| 11 | 04-05 04:00 | 04-05 08:00 | LONG_BTC_SHORT_ETH | 2.01 | 1.84 | 4.0h | 🔴 -27.92 |  |
| 12 | 04-07 20:00 | 04-08 00:00 | SHORT_BTC_LONG_ETH | -2.63 | -2.74 | 4.0h | 🟢 +34.71 |  |
| 13 | 04-11 16:00 | 04-11 20:00 | SHORT_BTC_LONG_ETH | -3.00 | -2.11 | 4.0h | 🔴 -76.80 |  |
| 14 | 04-13 20:00 | 04-14 00:00 | SHORT_BTC_LONG_ETH | -3.22 | -2.37 | 4.0h | 🔴 -49.81 |  |
| 15 | 04-18 08:00 | 04-18 12:00 | LONG_BTC_SHORT_ETH | 2.25 | 1.52 | 4.0h | 🔴 -57.53 |  |
| 16 | 04-22 12:00 | 04-22 16:00 | LONG_BTC_SHORT_ETH | 2.03 | 1.24 | 4.0h | 🔴 -57.52 |  |
| 17 | 04-26 12:00 | 04-26 16:00 | SHORT_BTC_LONG_ETH | -2.69 | -3.19 | 4.0h | 🟢 +29.07 |  |
| 18 | 05-04 00:00 | 05-04 04:00 | SHORT_BTC_LONG_ETH | -2.13 | -1.50 | 4.0h | 🔴 -45.51 |  |
| 19 | 05-05 12:00 | 05-05 16:00 | LONG_BTC_SHORT_ETH | 2.28 | 2.62 | 4.0h | 🟢 +18.95 |  |
| 20 | 05-10 16:00 | 05-10 20:00 | SHORT_BTC_LONG_ETH | -2.50 | -0.65 | 4.0h | 🔴 -97.82 |  |
| 21 | 05-11 16:00 | 05-11 20:00 | LONG_BTC_SHORT_ETH | 2.34 | 1.69 | 4.0h | 🔴 -52.08 |  |
| 22 | 05-15 00:00 | 05-15 04:00 | LONG_BTC_SHORT_ETH | 2.11 | 2.00 | 4.0h | 🔴 -22.93 |  |

---

## ✅ Conclusion

### Verdict : **❌ FAIL**

La stratégie de Pairs Trading BTC-ETH par **trend-following** du ratio n'est pas viable dans sa forme actuelle.

### Résultats clés :
- **WR** : 36.4% (objectif ≥60% non atteint ❌)
- **Profit Factor** : 0.47 (objectif >1.2 non atteint ❌)
- **PnL** : -432.91€ sur 89 jours (-4.86€/jour)
- **Risque** : Max DD -4.79%

### Comparaison Mean-Rev vs Trend-Follow :
Le trend-following performe mieux que la mean-reversion sur cette période, ce qui confirme que le ratio BTC/ETH est plus **trending** que **mean-reverting**.

### Recommandation :
❌ AJUSTER — Modifier paramètres ou abandonner

---

## 📁 Fichiers Produits

| Fichier | Description |
|---|---|
| `src/pairs_trading_trend_v1.py` | Moteur de backtest trend-following |
| `backtests/pairs-trading-trend-v1.md` | Rapport détaillé |
| `backtests/pairs-trading-trend-v1_data.csv` | Données brutes (OHLCV + signaux + PnL) |

---

*Généré le 2026-05-15 19:32 UTC*
*Backtest engine v1.0 — Python 3.12.3*
