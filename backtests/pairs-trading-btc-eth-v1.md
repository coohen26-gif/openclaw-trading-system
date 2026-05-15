# Backtest Pairs Trading BTC-ETH — Rapport Final v1

## 📋 Synthèse Exécutive

**Statut : ❌ FAIL — Stratégie non viable en l'état**

La stratégie de Pairs Trading BTC-ETH par mean-reversion du ratio montre des résultats insuffisants sur la période testée (90 jours, fév-mai 2026).

| Métrique | Résultat | Objectif | Écart |
|---|---|---|---|
| **Win Rate** | 45.5% | ≥70% | -24.5 pts ❌ |
| **PnL Total** | -521.52€ (-5.22%) | +45 000€* | -45 521€ ❌ |
| **PnL/jour** | -5.86€/jour | 500-600€/jour | -506€/jour ❌ |
| **Sharpe Ratio** | -14.31 | >1 | ❌ |
| **Max Drawdown** | -5.90% | <20% | ✅ |
| **Profit Factor** | 0.35 | >1.5 | ❌ |

*Objectif annualisé implicite

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
- **Corrélation BTC-ETH** : 0.906 (excellente)

### Paramètres Testés (v1)
| Paramètre | Valeur |
|---|---|
| Z-score entry | ±2.0 |
| Z-score exit | ±0.5 |
| Stop-loss | ±3.5 |
| Fees | 0.05% |
| Slippage | 0.02% |
| Capital | 10 000 € |
| Levier | 1x |

---

## 🔍 Analyse Détaillée

### 1. Pourquoi ça ne marche pas ?

**Hypothèse de base invalidée :** Le ratio BTC/ETH ne mean-reverte pas assez rapidement ou prévisiblement sur cette période.

**Observations clés :**

1. **Trend fort du ratio** : Sur la période, le ratio BTC/ETH a connu des mouvements directionnels soutenus (trend > mean-reversion)
   
2. **Faux signaux** : Beaucoup d'entrées à Z=±2 sont suivies d'une continuation du mouvement (Z continue à ±3+) plutôt que d'une reversal

3. **Durée trop courte** : Les trades durent en moyenne 4h (1 bougie), ce qui suggère des sorties prématurées ou des stop-loss fréquents

4. **Asymétrie des pertes** : Les pertes moyennes sont bien supérieures aux gains moyens

### 2. Distribution des Trades

```
Trades winners : 10/22 (45.5%)
Trades losers  : 12/22 (54.5%)

Gains moyens   : +28.5€
Pertes moyennes: -62.3€
Ratio G/P      : 0.46 (défavorable)
```

### 3. Problèmes Identifiés

| Problème | Impact | Sévérité |
|---|---|---|
| Mean-reversion trop faible | Le ratio ne revient pas à sa moyenne assez souvent | 🔴 Haute |
| Trend dominance | Les mouvements directionnels dominent la mean-reversion | 🔴 Haute |
| Sorties trop précoces | Exit à Z=±0.5 rate la pleine mean-reversion | 🟠 Moyenne |
| Fees impact | 0.07% round-trip mange les petits gains | 🟡 Basse |

---

## 🧪 Tests Alternatifs Effectués

Plusieurs configurations ont été testées durant ce backtest :

| Version | TF | Z-entry | Z-exit | WR | PnL | Conclusion |
|---|---|---|---|---|---|---|
| v1.0 | 1h | ±2.0 | ±0.5 | 12.8% | -1057€ | ❌ Trop de noise |
| v1.1 | 4h | ±2.5 | 0.0 | 35.7% | -532€ | ❌ Exit à 0 trop rare |
| v1.2 | 4h | ±3.0 | ±1.0 | 60.0% | -154€ | ⚠️ WR OK mais PnL KO |
| v1.3 | 4h | ±2.0 | ±0.5 | 45.5% | -522€ | ❌ Version finale |

**Meilleure configuration** : v1.2 (Z=±3, exit=±1) avec 60% WR mais trop peu de trades (5 sur 90j)

---

## 💡 Pistes d'Amélioration

### 1. Changer de Paradigme

**Problem** : La mean-reversion pure ne fonctionne pas car le ratio BTC/ETH est **trending** plus que **mean-reverting**.

**Solutions envisageables :**

a) **Suivre le trend du ratio** au lieu de la mean-reversion
   - LONG ratio quand il break sa MA
   - SHORT ratio quand il break sa MA à la baisse

b) **Ajouter un filtre de regime**
   - Identifier si le ratio est en mode "trend" ou "range"
   - Ne trader la mean-reversion qu'en mode range

c) **Changer de paire**
   - Tester BTC-ETH sur des périodes différentes
   - Tester d'autres paires corrélées (ETH-SOL, BTC-LTC, etc.)

### 2. Ajustements Paramétriques

| Ajustement | Effet attendu | Risque |
|---|---|---|
| Z-entry ±2.5 ou ±3 | Moins de trades, meilleure qualité | Trop peu d'opportunités |
| Z-exit ±0.2 ou 0 | Capturer plus de mean-reversion | Trades plus longs, plus de risque |
| Stop-loss ±4 ou ±5 | Réduire les sorties prématurées | Pertes plus grandes |
| Timeframe 1D | Réduire le noise | Beaucoup moins de trades |

### 3. Améliorations Techniques

- **Filtre ADX** : Ne trader que si ADX < 25 (marché range)
- **Filtre de volatilité** : Éviter les périodes de haute volatilité
- **Position sizing dynamique** : Réduire taille après pertes consécutives
- **Trailing stop** : Au lieu de fixed exit à Z=±0.5

---

## 📈 Graphiques (à produire)

Les données brutes sont sauvegardées dans :
- `backtests/pairs-trading-btc-eth-v1_data.csv`

Graphiques recommandés :
1. Ratio BTC/ETH + MA20 + bandes ±2σ
2. Z-score over time avec zones d'entrée/sortie
3. Courbe de PnL cumulé
4. Drawdown curve
5. Distribution des trades winners vs losers

---

## ✅ Conclusion

### Verdict : **❌ FAIL — Ne pas passer en production**

La stratégie de Pairs Trading BTC-ETH par mean-reversion du ratio **n'est pas viable** dans sa forme actuelle sur la période testée.

### Reasons principales :
1. **WR de 45.5%** bien en-dessous des 70% requis
2. **PnL négatif** de -521€ sur 90 jours
3. **Le ratio BTC/ETH est plus trending que mean-reverting** sur cette période

### Recommandation :

**Option A — Abandonner cette approche**
- La mean-reversion pure n'est pas adaptée à cette paire sur cette période
- Explorer d'autres stratégies (trend-following du ratio, momentum, etc.)

**Option B — Recherche approfondie**
- Tester sur 1+ année de données (plus de régimes de marché)
- Identifier les périodes où la mean-reversion fonctionne
- Développer un filtre de regime (trend vs range)
- Tester d'autres paires crypto corrélées

**Option C — Pivot vers trend-following**
- Au lieu de parier contre le mouvement, le suivre
- LONG ratio quand il break sa MA à la hausse
- SHORT ratio quand il break sa MA à la baisse

---

## 📁 Fichiers Produits

| Fichier | Description |
|---|---|
| `src/pairs_trading_backtest.py` | Moteur de backtest complet |
| `backtests/pairs-trading-btc-eth-v1.md` | Rapport détaillé |
| `backtests/pairs-trading-btc-eth-v1_data.csv` | Données brutes (OHLCV + signaux + PnL) |

---

*Généré le 2026-05-15 11:55 UTC*
*Backtest engine v1.0 — Python 3.12.3*
