# 🐉 Backtest Report : Système Saiyan v0.1

**Date :** 2026-05-24  
**Version :** 0.1 (Prototype Paper-Trade)  
**Stratégie :** Mean Reversion  
**Asset :** BTC/USDT  
**Timeframe :** 1h  

---

## 📋 Synthèse Exécutive

| Métrique | Résultat | Objectif | Statut |
|----------|----------|----------|--------|
| **Win Rate** | **70.27%** | ≥70% | ✅ **ATTEINT** |
| **Total Trades** | 111 | - | - |
| **PnL Total** | -51.18 USDT (-0.51%) | Positive | ❌ |
| **Sharpe Ratio** | -13.88 | >1 | ❌ |
| **Max Drawdown** | **-0.59%** | <15% | ✅ **EXCELLENT** |
| **Profit Factor** | 0.70 | >1.5 | ❌ |
| **Avg Trade Duration** | 23.7h | - | - |

---

## 📊 Performance Détaillée

### Distribution des Trades

| Type | N Trades | Win Rate | PnL Total | Avg PnL |
|------|----------|----------|-----------|---------|
| **Winners** | 78 | 70.3% | +117.00 USDT | +1.50 USDT |
| **Losers** | 33 | 29.7% | -167.97 USDT | -5.09 USDT |
| **Total** | 111 | 70.3% | **-51.18 USDT** | -0.46 USDT |

### Analyse par Exit Reason

| Exit Reason | N Trades | PnL Total | Avg PnL |
|-------------|----------|-----------|---------|
| TAKE_PROFIT | 78 | +117.00 USDT | +1.50 USDT |
| STOP_LOSS | 33 | -167.97 USDT | -5.09 USDT |

**Ratio G/P :** 0.30 (défavorable - pertes moyennes > gains moyens)

---

## 💰 Configuration du Backtest

| Paramètre | Valeur |
|-----------|--------|
| **Capital Initial** | 10,000 USDT |
| **Position Sizing** | 2-5% (confidence-based) |
| **Stop Loss** | 2.5% |
| **Take Profit** | 1.0% |
| **Trading Fees** | 0.1% (entry + exit) |
| **Slippage** | 0.05% |
| **Min Confidence** | 60/100 |
| **Fees Totales** | 44.20 USDT |

---

## 📈 Courbe de Capital

```
Capital Final : 9,948.82 USDT (-0.51%)
Max Drawdown  : -0.59% (excellent contrôle du risque)
```

**Observation :** La courbe de capital est très stable grâce au faible drawdown, mais le PnL est négatif à cause du ratio risk/reward défavorable.

---

## 🔍 Analyse des Résultats

### ✅ Points Forts

1. **Win Rate ≥70%** : Objectif principal ATTEINT (70.27%)
2. **Drawdown maîtrisé** : -0.59% seulement, excellent pour une stratégie mean reversion
3. **Nombre de trades** : 111 trades sur ~1000 bougies, bonne fréquence
4. **Durée moyenne** : 23.7h par trade, cohérent avec du 1h TF

### ❌ Points Faibles

1. **Profit Factor <1** : 0.70, le système perd de l'argent globalement
2. **Risk/Reward défavorable** : 
   - Avg Win : +1.50 USDT (+0.50%)
   - Avg Loss : -5.09 USDT (-1.70%)
   - Ratio : 1:3.4 (désavantageux)
3. **Fees impact** : 44.20 USDT de fees sur 111 trades (0.40 USDT/trade en moyenne)
4. **Sharpe négatif** : -13.88, volatilité des returns trop élevée par rapport au gain moyen

---

## 🎯 Problème Identifié : Risk/Reward

**Configuration actuelle :**
- Stop Loss : 2.5%
- Take Profit : 1.0%
- Ratio R/R : 0.40 (on risque 2.5% pour gagner 1%)

**Impact :**
Même avec 70% de win rate, le système est perdant car :
```
Espérance = (0.70 × 1.0%) - (0.30 × 2.5%) = 0.70% - 0.75% = -0.05%
```

**Solution requise :**
Pour être profitable avec 70% WR, il faut :
- Soit augmenter TP (1.5-2.0%)
- Soit réduire SL (1.5-2.0%)
- Soit les deux pour un ratio R/R ≥ 1.0

---

## 📝 Recommandations pour v0.2

### 1. Ajuster Risk/Reward (PRIORITAIRE)

**Option A : Augmenter TP**
```
TP : 1.0% → 2.0%
SL : 2.5% → 2.0%
Nouveau R/R : 1.0 (équilibré)
```

**Option B : Réduire SL**
```
TP : 1.0% (inchangé)
SL : 2.5% → 1.5%
Nouveau R/R : 0.67 (meilleur)
```

**Option C : Ajustement dynamique**
```
TP : 1.5% (moyen)
SL : 2.0% (moyen)
R/R : 0.75 + trailing stop pour capturer plus
```

### 2. Optimiser Paramètres Mean Reversion

**RSI Thresholds :**
- Actuel : <35 />65
- Tester : <30 />70 (signaux plus stricts, meilleure qualité)

**Bollinger Bands :**
- Actuel : 2.5σ
- Tester : 2.0-2.5σ dynamique selon volatilité

### 3. Filtres Additionnels

**Volume :**
- Ajouter filtre : volume_surge > 1.5x (déjà présent mais à renforcer)

**Tendance :**
- Ajouter MA 50/200 pour éviter mean reversion contre tendance forte

**Volatilité :**
- Éviter trades si ATR > seuil (trop risqué)

### 4. Gestion de Position

**Position Sizing :**
- Actuel : 2-5% selon confidence
- Tester : Kelly Criterion ou Fixed Fractional optimisé

**Trailing Stop :**
- Implémenter trailing stop après +0.5% pour sécuriser gains

---

## 🧪 Tests à Réaliser (v0.2)

### Backtest 1 : R/R Optimisé
```
TP: 2.0%, SL: 2.0% (R/R = 1.0)
Objectif : WR ≥65%, Profit Factor >1.2
```

### Backtest 2 : Paramètres Stricts
```
RSI: <30/>70, BB: 2.5σ
Objectif : WR ≥75%, moins de trades mais meilleure qualité
```

### Backtest 3 : Walk-Forward Validation
```
3 splits : in-sample / out-of-sample
Objectif : Vérifier robustesse sur données non vues
```

### Backtest 4 : Multi-Asset
```
BTC + ETH + Gold
Objectif : Diversification, corrélation réduite
```

---

## 📊 Métriques Cibles pour v0.2

| Métrique | v0.1 | v0.2 (Objectif) |
|----------|------|-----------------|
| Win Rate | 70.3% | ≥70% |
| Profit Factor | 0.70 | ≥1.3 |
| Sharpe Ratio | -13.88 | ≥1.0 |
| Max Drawdown | -0.59% | <5% |
| Total PnL | -0.51% | ≥+5% |
| Avg Win/Loss | 0.30 | ≥0.8 |

---

## 🚀 Conclusion

**Statut v0.1 :** ✅ **VALIDÉ pour Mean Reversion** (WR ≥70%)

**Problème majeur :** ❌ Risk/Reward défavorable (0.40)

**Prochaines étapes :**
1. ✅ Ajuster TP/SL pour R/R ≥1.0
2. ✅ Re-backtester avec nouveaux paramètres
3. ✅ Walk-forward validation (3 splits)
4. ✅ Tests multi-assets (Crypto + Metals)
5. ✅ Paper-trade 30 jours avec signaux Telegram

**Potentiel :** Le système montre une excellente capacité à identifier des points d'entrée mean reversion (70% WR). Avec un risk/reward optimisé, le système peut devenir profitable.

---

## 📁 Fichiers Généres

- **Code source :** `system-saiyan/v0.1/`
- **Configuration :** `system-saiyan/v0.1/config.json`
- **Documentation :** `system-saiyan/README.md`
- **Backtest data :** 111 trades sur BTC/USDT 1h (2026-04-13 → 2026-05-24)

---

*Généré le 2026-05-24 01:50 UTC*  
🐉 *"La puissance Saiyan n'a pas de limite !"*
