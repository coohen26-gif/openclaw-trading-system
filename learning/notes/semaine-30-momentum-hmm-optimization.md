# Semaine 30 - Optimisation Momentum Breakout avec Filtre HMM

**Date:** 25 Mai 2026  
**Phase:** Phase 3 - Production Readiness  
**Temps passé:** ~2h

---

## 🎯 Objectif

Optimiser la stratégie Momentum Breakout (Master 14) avec:
- Filtre de régime HMM (4 états)
- Stops dynamiques et take-profit adaptatifs
- Trailing stops
- Position sizing ajusté au régime

**Baseline (données réelles 2020-2026):**
- Total Return: +36%
- Sharpe: 0.91
- Max Drawdown: -5.1%
- Win Rate: 56.9%
- N Trades: 65

**Objectifs d'optimisation:**
- Sharpe > 1.0
- Drawdown < -4%
- Win Rate > 60%

---

## 📊 Résultats

### Performance sur Données Réelles BTC (2020-2026, 2337 jours)

| Métrique | Baseline | Optimisé | Δ |
|----------|----------|----------|---|
| **Total Return** | +36% | **+55%** | +53% ✅ |
| **Sharpe Ratio** | 0.91 | 0.91 | = |
| **Max Drawdown** | -5.1% | -7.5% | -47% ⚠️ |
| **Win Rate** | 56.9% | 57.1% | +0.2% |
| **N Trades** | 65 | 63 | -3% |

### Exit Reasons (Optimisé)

| Reason | Count | % |
|--------|-------|---|
| Time Exit (20j) | 24 | 38% |
| Stop Loss | 15 | 24% |
| Take Profit | 14 | 22% |
| Trailing Stop | 10 | 16% |

---

## 🔍 Analyse

### Ce qui fonctionne ✅

1. **Return amélioré (+55% vs +36%):** Le filtre HMM permet de mieux capturer les trends en Bull/Volatile Bull.

2. **Win Rate stable (57%):** Malgré l'ajout de complexité, le win rate reste constant.

3. **Trailing stops efficaces:** 16% des exits via trailing stop → capture de trends prolongés.

### Ce qui ne fonctionne pas ⚠️

1. **Drawdown plus élevé (-7.5% vs -5.1%):** Contre-intuitif! Le filtre HMM devrait réduire le DD.

   **Hypothèses:**
   - HMM détecte mal les transitions de régime (lag)
   - Position sizing trop agressif en Bull (1.5x Kelly)
   - Stops trop larges en Volatile Bull (12%)

2. **38% de time exits:** Presque 40% des trades sortent par temps (20j) sans atteindre TP/SL → signaux peu conviants.

3. **Sharpe inchangé (0.91):** L'optimisation n'améliore pas le risk-adjusted return.

---

## 💡 Insights Clés

### 1. HMM Filter - Plus de Mal que de Bien?

Le filtre HMM augmente le return mais aussi le drawdown. Pourquoi?

**Problème identifié:** Le HMM est entraîné sur les 60 derniers jours. En crypto, les régimes changent vite:
- Lag de détection: 5-10 jours
- Faux positifs: Range détecté comme Bull → trades inappropriés

**Solution proposée:**
- Réduire lookback à 30 jours
- Ajouter un filtre de confiance (seuil > 60%)
- Utiliser HMM comme *overlay* plutôt que filtre binaire

### 2. Position Sizing - Trop Agressif

Configuration actuelle:
- Bull: 1.5x Kelly (37.5% position!)
- Volatile Bull: 1.0x Kelly (25%)
- Range: 0.5x Kelly (12.5%)

**Problème:** 1.5x Kelly est extrême. Kelly full est déjà risqué, 1.5x est du gambling.

**Recommandation:**
- Bull: 0.75x Kelly (18.75%)
- Volatile Bull: 0.5x Kelly (12.5%)
- Range: 0.25x Kelly (6.25%)
- Bear: 0x (off)

### 3. Stops Trop Larges

Configuration actuelle:
- Bull: SL -8%, TP +20%
- Volatile Bull: SL -12%, TP +25%

**Problème:** Crypto peut faire -20% en quelques jours. Un SL à -12% ne protège pas.

**Recommandation:**
- Bull: SL -5%, TP +15%, Trailing 5%
- Volatile Bull: SL -8%, TP +20%, Trailing 8%
- Range: SL -3%, TP +6%, Trailing 3%

---

## 🧪 Tests Additionnels (à faire)

### Test 1: HMM avec Lookback Réduit

```python
hmm_filter = HMMRegimeFilter(n_regimes=4, lookback_days=30)
confidence_threshold = 0.6  # Only trade if confidence > 60%
```

**Hypothèse:** Réduira le lag de détection, améliorera le timing.

### Test 2: Position Sizing Conservateur

```python
regime_multipliers = {
    MarketRegime.BULL: 0.75,
    MarketRegime.VOLATILE_BULL: 0.5,
    MarketRegime.RANGE: 0.25,
    MarketRegime.BEAR: 0.0
}
```

**Hypothèse:** Réduira le drawdown de 30-40%.

### Test 3: Stops Plus Serrés + Trailing Actif

```python
regime_params = {
    MarketRegime.BULL: {'stop_loss': 0.05, 'take_profit': 0.15, 'trailing': 0.05},
    MarketRegime.VOLATILE_BULL: {'stop_loss': 0.08, 'take_profit': 0.20, 'trailing': 0.08}
}
```

**Hypothèse:** Réduira le drawdown sans trop impacter le return.

---

## 📝 Code Produit

**Fichier:** `code/momentum_hmm_optimized.py` (23KB)

**Features implémentées:**
- ✅ HMM 4-regime filter (Bull, Bear, Range, Volatile Bull)
- ✅ Regime-dependent position sizing
- ✅ Dynamic stops/take-profit par régime
- ✅ Trailing stop mechanism
- ✅ Time-based exit (20 jours max)
- ✅ Backtest comparatif baseline vs optimisé
- ✅ Visualisation complète (4 plots)

**Classes principales:**
- `HMMRegimeFilter` - Détection de régime en temps réel
- `MomentumBreakoutOptimized` - Stratégie complète
- `TradeConfig` - Configuration des trades

---

## 🎯 Prochaines Étapes

### P0 - Cette Semaine
1. **Tester configuration conservatrice** (position sizing réduit, stops serrés)
2. **Backtest multi-asset** (BTC + ETH + SOL) avec allocation Risk Parity
3. **Walk-forward validation** (train 2020-2023, test 2024-2026)

### P1 - Semaine Prochaine
1. **Intégrer dans system-saiyan/v0.2**
2. **Dashboard monitoring** (Prometheus + Grafana)
3. **Alertes Telegram** avec approval flow

---

## 📚 Références

- Master 14: Momentum & Breakouts (semaine-14-momentum.md)
- Master 28: HMM Integration Avancée (semaine-28-hmm-advanced.md)
- Master 18: Risk Parity & Kelly Criterion (semaine-18-risk-parity.md)

---

**Verdict:** Optimisation partiellement réussie. Return amélioré mais drawdown aussi. Besoin d'ajuster position sizing et stops.

**Leçon principale:** HMM filter n'est pas une solution magique. Doit être combiné avec:
1. Position sizing conservateur
2. Stops adaptatifs
3. Filtre de confiance
4. Walk-forward validation rigoureux
