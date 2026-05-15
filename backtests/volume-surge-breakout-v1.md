# Backtest Volume Surge Breakout — Rapport v1

## 📋 Synthèse Exécutive

**Statut : ❌ FAIL — Stratégie non viable selon les critères**

| Critère | Résultat | Objectif | Statut |
|---|---|---|---|
| **Win Rate** | 37.0% | ≥65% | ❌ |
| **Profit Factor** | 0.70 | >1.3 | ❌ |
| **PnL Total** | -501.74€ (-5.02%) | - | - |
| **PnL/jour** | -12.24€/jour | - | - |
| **Sharpe Ratio** | -10.92 | >1 | ❌ |
| **Max Drawdown** | -6.80% | <20% | ✅ |

---

## 📊 Données du Backtest

### Période
- **Start** : 2026-02-14
- **End** : 2026-03-28
- **Durée** : 41 jours

### Données
- **Symbole** : BTC/USDT
- **Timeframe** : 1h
- **Source** : Binance (CCXT)
- **N bougies** : 1000

### Paramètres
| Paramètre | Valeur |
|---|---|
| Consolidation | 20 bougies |
| Volume Filter | > 1.5x MA20 |
| Breakout | close > high(20) ou close < low(20) |
| TP | 1.0x ATR |
| SL | Retour dans le range |
| Fees | 0.1% |
| Slippage | 0.05% |
| Capital | 10000 € |
| Levier | 1x |

---

## 🔍 Analyse Détaillée

### 1. Performance des Trades

```
Total Trades  : 46
Trades winners: 16/46 (37.0%)
Trades losers : 30/46 (63.0%)

Gains moyens  : +68.73€
Pertes moyennes: -57.59€
Ratio G/P     : 1.19
```

### 2. TP vs SL

| Sortie | Nombre | % |
|---|---|---|
| Take Profit | 15 | 32.6% |
| Stop Loss | 9 | 19.6% |

### 3. Streaks

- **Plus longue série gagnante** : 4 trades
- **Plus longue série perdante** : 7 trades

### 4. Duration Moyenne

- **Temps moyen par trade** : 1.0 heures (0.0 jours)

---

## 🧪 Observations

### Points Forts
- ✅ Drawdown maîtrisé à -6.80%

### Points Faibles
- ❌ Win Rate de 37.0% insuffisant (objectif: 65%)
- ❌ Profit Factor de 0.70 trop faible (objectif: >1.3)

---

## 📈 Courbes

### PnL Curve
- **Départ** : 10000€
- **Final** : 9498.26€
- **Peak** : 10191.27€

### Drawdown
- **Max DD** : -6.80%

---

## 🎯 Conclusion

**Verdict : STRATÉGIE À REVOIR**

La stratégie ne remplit pas les critères de performance.

**Pistes d'amélioration :**
- Ajuster le volume multiplier (actuellement 1.5x)
- Modifier la période de consolidation (actuellement 20 bougies)
- Revoir les niveaux de TP/SL
- Ajouter des filtres supplémentaires (trend, volatilité)
- Tester sur un autre timeframe (1h au lieu de 4h ou inversement)

---

*Backtest généré le 2026-05-15 19:46:10 UTC*
