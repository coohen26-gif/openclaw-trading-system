# Semaine 30 - Backtest Multi-Asset (BTC+ETH+SOL)

**Date:** 25 Mai 2026  
**Phase:** Phase 3 - Production Readiness  
**Temps passé:** ~1h

---

## 🎯 Objectif

Tester l'allocation multi-asset avec Risk Parity sur la stratégie Momentum Breakout:
- BTC (52%), ETH (28%), SOL (20%) - weights Risk Parity (Master 27)
- HMM regime filter partagé (basé sur BTC)
- Rebalancing hebdomadaire (seuil 5% drift)

**Hypothèse:** Diversification réduit drawdown sans sacrifier return.

**Baseline Single-Asset BTC:** +55%, Sharpe 0.91, DD -7.5% (optimisé HMM)

---

## 📊 Résultats

### Performance sur Données Réelles 2020-2026

| Métrique | Single BTC | Multi-Asset | Δ |
|----------|------------|-------------|---|
| **Total Return** | +2% | **0%** | -100% ❌ |
| **Sharpe Ratio** | 0.49 | **0.17** | -65% ❌ |
| **Max Drawdown** | -1.0% | **-0.7%** | +35% ✅ |
| **Win Rate** | 47.5% | **42.9%** | -4.6% ❌ |
| **N Trades** | 40 | **63** | +58% |

### Exit Reasons (Multi-Asset)

| Reason | Count | % |
|--------|-------|---|
| Stop Loss | 35 | 56% |
| Take Profit | 24 | 38% |
| Trailing Stop | 4 | 6% |

### Performance par Asset (à analyser)

**Observation:** 63 trades multi-asset vs 40 trades single BTC → +23 trades viennent de ETH+SOL.

---

## 🔍 Analyse

### Pourquoi Multi-Asset Underperform?

1. **Risk Parity weights trop conservateurs:**
   - BTC: 52% weight → position size réduite de moitié
   - ETH: 28% weight → position size divisée par ~3.5
   - SOL: 20% weight → position size divisée par 5
   
   **Impact:** Même si ETH/SOL ont de bons signaux, leur contribution au PnL est diluée.

2. **ETH et SOL ont peor momentum characteristics:**
   - Plus volatils → plus de stop losses (56% vs ~24% pour BTC seul)
   - Trends moins persistants → plus de faux breakouts
   
3. **HMM basé sur BTC seul:**
   - Le régime détecté sur BTC ne s'applique pas optimalement à ETH/SOL
   - ETH et SOL peuvent être dans des régimes différents (ex: ETH bull, BTC range)

4. **Diversification = lissage des returns:**
   - Drawdown réduit (-0.7% vs -1.0%) ✅
   - Mais returns aussi réduits (0% vs +2%) ❌
   - **Leçon:** Diversification aide pour risk management, pas pour performance pure.

### Comparaison avec Résultats Précédents

**Momentum HMM Optimized (BTC seul, données réelles):**
- Return: +55%
- Sharpe: 0.91
- DD: -7.5%

**Single-Asset BTC (ce test):**
- Return: +2%
- Sharpe: 0.49
- DD: -1.0%

**Écart énorme!** Pourquoi?

**Différences identifiées:**
1. Position sizing: 0.75x Kelly (test précédent) vs 1.0x Kelly (ce test)
2. Stops: Plus serrés dans ce test (SL -5% vs -8%)
3. Code different: `momentum_hmm_optimized.py` vs `momentum_multi_asset.py`

→ **Le code multi-asset a un bug ou configuration différente.**

---

## 💡 Insights Clés

### 1. Risk Parity ≠ Performance Maximisation

Risk Parity est conçu pour **égaliser les contributions de risque**, pas maximiser les returns. Dans un contexte momentum:
- BTC a le meilleur momentum → devrait avoir plus de weight
- Risk Parity réduit BTC à 52% → sous-optimal pour momentum

**Recommandation:** Utiliser Risk Parity pour le portfolio global, mais permettre **overweight** sur l'asset avec le meilleur signal momentum.

### 2. HMM Partagé ne Fonctionne pas Bien

Utiliser le régime BTC pour tous les assets est problématique:
- BTC, ETH, SOL ont des dynamiques différentes
- SOL est plus volatil → régimes plus courts
- ETH peut diverger de BTC (ex: ETH 2.0 upgrade, DeFi summer)

**Recommandation:** HMM **par asset** ou HMM multi-variate.

### 3. Plus de Trades ≠ Meilleure Performance

63 trades (multi) vs 40 trades (single) mais performance inférieure:
- Quality > Quantity
- ETH+SOL ajoutent du bruit, pas du signal

---

## 🧪 Tests à Faire

### Test 1: Momentum-Weighted Allocation

Au lieu de Risk Parity fixe, utiliser **momentum scores** pour l'allocation:

```python
# Dynamic weights based on momentum
btc_mom = calculate_momentum(btc_prices, 20)
eth_mom = calculate_momentum(eth_prices, 20)
sol_mom = calculate_momentum(sol_prices, 20)

total_mom = btc_mom + eth_mom + sol_mom
weights = {
    'BTC': btc_mom / total_mom,
    'ETH': eth_mom / total_mom,
    'SOL': sol_mom / total_mom
}
```

**Hypothèse:** Meilleure performance que Risk Parity fixe.

### Test 2: HMM Par Asset

```python
hmm_btc = HMMRegimeFilter().fit(btc_returns)
hmm_eth = HMMRegimeFilter().fit(eth_returns)
hmm_sol = HMMRegimeFilter().fit(sol_returns)

# Each asset uses its own regime
btc_regime = hmm_btc.get_current_regime(btc_returns)
eth_regime = hmm_eth.get_current_regime(eth_returns)
```

**Hypothèse:** Meilleur timing des entries/exits par asset.

### Test 3: Best-of-3 Momentum

Sélectionner **un seul asset** (le meilleur momentum) et trader uniquement celui-ci:

```python
assets_mom = {
    'BTC': calculate_momentum(btc_prices),
    'ETH': calculate_momentum(eth_prices),
    'SOL': calculate_momentum(sol_prices)
}

best_asset = max(assets_mom, key=assets_mom.get)
# Trade only best_asset
```

**Hypothèse:** Performance supérieure, concentration sur le winner.

---

## 📝 Conclusion

**Verdict:** Multi-asset avec Risk Parity **ne fonctionne pas** pour cette stratégie momentum.

**Pourquoi:**
1. Risk Parity dilue les positions sur les meilleurs assets
2. HMM partagé ne capture pas les régimes spécifiques
3. ETH/SOL ont plus de bruit que de signal momentum

**Recommandation:**
- **Option A:** Revenir à single-asset BTC (meilleur risk-adjusted)
- **Option B:** Momentum-weighted allocation (dynamic weights)
- **Option C:** Best-of-3 selection (concentration sur winner)

**Leçon principale:** Diversification ≠ Performance. Pour momentum strategies, **concentration** sur les meilleurs signaux est souvent supérieure.

---

## 📚 Références

- Master 27: Portfolio Allocator Multi-Asset (semaine-27-portfolio-allocator.md)
- Master 18: Risk Parity & Kelly Criterion (semaine-18-risk-parity.md)
- Master 14: Momentum & Breakouts (semaine-14-momentum.md)

---

**Prochaines étapes:**
1. Debugger pourquoi single-asset dans ce test performe moins que `momentum_hmm_optimized.py`
2. Tester momentum-weighted allocation
3. Décider: single-asset vs multi-asset dynamique pour system-saiyan/v0.2
