# 💡 Insight #01: Fat Tails = Feature, pas Bug

**Date:** 24 Mai 2026  
**Source:** Semaine 01 - Returns BTC  
**Priorité:** P0 (Core)

---

## 📚 Connaissance (Théorie)

**Observation:**
- Kurtosis excess BTC 5min: **22.34**
- Normal distribution: Kurtosis = 0
- → Événements extrêmes **100x+ plus fréquents** que Gaussian

**Données:**
```
Timeframe | Kurtosis Excess | Skewness
----------|-----------------|----------
5min      | 22.34           | +0.48
1h        | 8.11            | -0.26
Daily     | 4.32            | +0.03
```

**Interprétation:**
- 5min: Fat tails extrêmes + skew positive (plus de pumps)
- 1h: Fat tails modérées + skew négative (crashes)
- Daily: Plus proche de normal (mais toujours fat tails)

---

## 💡 Insight (Conclusion)

**Ce que la plupart font:**
- Filtrer les outliers
- Utiliser modèles Gaussian (échouent)
- Considérer fat tails comme un "bug"

**Ce que Saiyan fait:**
- **Exploiter** les fat tails
- Mean reversion APRÈS mouvements >3σ (pas avant)
- Les fat tails sont une **FEATURE** → edge de trading

**Pourquoi:**
- Mouvement >3σ en 5min arrive plusieurs fois/semaine (pas 1 fois/siècle)
- Après un pump/dump extrême → probabilité mean-reversion >70%
- Edge statistique exploitable

---

## 🛠️ Application (Code)

### Stratégie: Fat Tail Hunter

**Mécanisme:**
```python
def fat_tail_signal(returns, window=50):
    """
    Détecte mouvements >3σ et attend essoufflement.
    """
    # 1. Calcul rolling mean/std
    rolling_mean = returns.rolling(window).mean()
    rolling_std = returns.rolling(window).std()
    
    # 2. Détection >3σ
    z_score = (returns - rolling_mean) / rolling_std
    extreme_move = abs(z_score) > 3.0
    
    # 3. Confirmation essoufflement
    roc_5 = returns.rolling(5).sum()
    roc_10 = returns.rolling(10).sum()
    exhaustion = roc_5 < roc_10  # Momentum diminue
    
    # 4. Signal
    signal = extreme_move & exhaustion
    
    # 5. Direction: opposée au mouvement
    direction = -np.sign(returns) * signal
    
    return direction
```

**Règles:**
1. `|return| > 3σ` (rolling 50p)
2. `ROC(5) < ROC(10)` (essoufflement)
3. Entrée: Direction opposée
4. Sortie: Retour à MA20 ou TP 0.3-0.5%
5. Filtre HMM: Actif seulement en RANGE (pas BULL/BEAR fort)

---

## ✅ Test (Validation)

### Backtest Requis

**Données:**
- BTC/USDT 5min, 6 mois
- ~51,000 records

**Métriques:**
- WR cible: ≥70%
- Avg gain: 0.2-0.5%
- n_trades: ≥50 (fréquence suffisante)
- Max drawdown: <15%

**Benchmark:**
- Mean reversion simple (RSI<20/>80)
- BB Walk (WR=66.7% sur ETHUSDT)

### Résultats Attendus

| Métrique | Cible | Benchmark | Fat Tail Hunter |
|----------|-------|-----------|-----------------|
| WR | ≥70% | 66.7% (BB Walk) | **~75-80%** |
| Avg Gain | 0.2-0.5% | 0.3% | **~0.3-0.4%** |
| n_trades | ≥50 | 20-30 | **~60-80** |
| Max DD | <15% | 12% | **<10%** |

---

## 🎯 Décision

**Statut:** ✅ **P0 - À implémenter en premier**

**Rationale:**
1. Edge statistique solide (kurtosis 22 = exploitable)
2. Fréquence suffisante (plusieurs fois/semaine)
3. Risk/reward favorable (WR ~75-80%, gain 0.3-0.4%)
4. Simple à implémenter (z-score + ROC)

**Prochaine Action:**
- [ ] Créer `saiyan-v1/strategies/fat_tail_hunter.py`
- [ ] Backtest sur 6 mois de données
- [ ] Comparer vs benchmark (BB Walk, RSI mean-rev)
- [ ] Si WR ≥70% → Intégrer Saiyan v1

---

## 🔗 Connections

**Lié à:**
- Insight #02: Skewness Gate (filtre direction)
- Insight #04: HMM Regime (filtre activation)
- Insight #07: VaR/CVaR (risk monitoring)

**Inspire:**
- Stratégie Fat Tail Hunter (P0)
- Filtre Skewness (P1)
- Filtre HMM (P0)

---

**Créé:** 24 Mai 2026  
**Dernière MAJ:** 24 Mai 2026  
**Review:** Dimanche 18h UTC (cron hebdo)
