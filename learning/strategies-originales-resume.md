# 🚀 7 Stratégies Originales - Système Saiyan

**Date:** 24 mai 2026  
**Source:** Dream Processing Session 2 (Master 1+2 Consolidation)  
**Statut:** En attente d'implémentation (post-Master 3-4)

---

## 📊 Vue d'ensemble

| # | Nom | Priorité | Temps | Impact | Statut |
|---|-----|----------|-------|--------|--------|
| 1 | Fat Tail Hunter | P0 | 1-2 sem | ⭐⭐⭐ | 🆕 Confirmé |
| 2 | Skewness Gate | P1 | 3-5j | ⭐⭐ | 🆕 Ajouté |
| 3 | Vola-Targeting GARCH | P1 | 1 sem | ⭐⭐ | 🆕 Ajouté |
| 4 | ML Confidence Engine | P1 | 2-3 sem | ⭐⭐ | 🆕 Ajouté |
| 5 | Session × Vol Matrix | P2 | 4-6j | ⭐ | 🆕 Ajouté |
| 6 | Shadow P&L by Skew | P2 | 3-4j | ⭐ | 🆕 Ajouté |
| 7 | Microstructure Executor | P2 | 1-2 sem | ⭐ | 🆕 Ajouté |

---

## 🎯 Stratégie #1: Fat Tail Hunter (P0) ⭐⭐⭐

### Concept
**Mean reversion APRÈS mouvements extrêmes (>3σ), pas avant.**

La plupart des stratégies mean-reversion échouent car elles entrent TÔP. Fat Tail Hunter attend l'essoufflement.

### Mécanisme
```
1. Détection: |return| > 3σ (rolling 50p)
2. Confirmation: ROC(5) < ROC(10) → essoufflement
3. Entrée: Direction opposée au mouvement extrême
4. Sortie: Retour à la moyenne (MA20) ou TP fixe 0.3-0.5%
```

### Pourquoi ça marche
- Kurtosis BTC 5min = 22.34 → événements 3σ arrivent plusieurs fois/semaine
- Après un pump/dump extrême, la probabilité de mean-reversion est >70%
- Backtest similaire (BB Walk ETHUSDT): WR=66.7%, avg_pnl=+7.8%

### Risques
- Mouvement >3σ peut continuer (momentum fort)
- → Filtre HMM: activer seulement en régime RANGE (pas BULL/BEAR fort)

### Temps d'implémentation: 1-2 semaines

---

## 🎯 Stratégie #2: Skewness Gate (P1) ⭐⭐

### Concept
**Skewness rolling (50p) comme MÉTA-SIGNAL qui active/désactive stratégies.**

Personne n'utilise la skewness comme gate dynamique. C'est notre edge.

### Règles
```
skew > +0.3   → Régime "Pump Energy"
                → Activer: Bull strategies, Momentum, Breakout
                → Désactiver: Mean reversion short

skew < -0.2   → Régime "Crash Fear"
                → Activer: Bear strategies, Mean reversion long
                → Désactiver: Momentum long

-0.2 ≤ skew ≤ +0.3 → Régime "Balance"
                     → Toutes stratégies actives (pondérées)
```

### Données
- BTC 5min: skew = +0.48 (plus de pumps)
- BTC 1h: skew = -0.26 (crashes plus fréquents)
- Daily: skew = +0.03 (symétrique)

### Originalité
La skewness est toujours utilisée comme statistique **descriptive**, jamais comme signal **actif**.

### Temps d'implémentation: 3-5 jours

---

## 🎯 Stratégie #3: Vola-Targeting GARCH (P1) ⭐⭐

### Concept
**Position sizing dynamique basé sur la prévision GARCH(1,1).**

GARCH ne sert pas juste à prévoir la volatilité, mais à ajuster l'exposition EN TEMPS RÉEL.

### Formule
```
position_size = base_size × (σ_target / σ_GARCH_prediction)

où:
- σ_target = volatilité cible (ex: 50% annualisé)
- σ_GARCH_prediction = prévision GARCH(1,1) next-period
```

### Paramètres GARCH(1,1) BTC
- α = 0.10 (réaction aux chocs récents)
- β = 0.84 (persistance long-terme)
- Persistance totale = 0.94 → volatilité très prévisible

### Exemple
```
σ_target = 50%
σ_GARCH = 80% (prédit haute vol)
→ position_size = base × (50/80) = 62.5% de la taille normale

σ_GARCH = 30% (prédit basse vol)
→ position_size = base × (50/30) = 167% de la taille normale
```

### Impact
- Protection automatique pendant périodes chaotiques
- Amplification pendant périodes calmes
- R²=0.87 vs realized volatility → prévision fiable

### Temps d'implémentation: 1 semaine

---

## 🎯 Stratégie #4: ML Confidence Engine (P1) ⭐⭐

### Concept
**Remplacer les pondérations manuelles (40% tech, 25% mom, etc.) par XGBoost.**

### Architecture
```
Features (50-60 générées):
- Techniques: RSI, MACD, BB, MA, ROC, etc.
- Volatilité: GARCH forecast, realized vol, ATR
- Volume: OBV, volume/MA20, order book imbalance
- Régime: HMM state, skewness, kurtosis rolling

→ Sélection SHAP+RFE → 15-25 features finales

Label:
- 1 = TP touché avant SL
- 0 = SL touché avant TP

Entraînement:
- Purged CV avec embargo 10% (évite lookahead bias)
- Réentraînement hebdomadaire (walk-forward)

Output:
- Confidence score 0-100%
- Remplace le score actuel (40% tech + 25% mom + ...)
```

### Pourquoi XGBoost > Heuristiques
- Capture interactions non-linéaires
- S'adapte aux changements de régime
- Feature importance via SHAP → interprétable

### Temps d'implémentation: 2-3 semaines

---

## 🎯 Stratégie #5: Session × Volatility Matrix (P2) ⭐

### Concept
**Matrix 2×2: Session (Asiatique/EU-US) × Vol (Basse/Haute) → stratégie optimale.**

### Matrix
```
                | Vol Basse      | Vol Haute
----------------|----------------|----------------
Session Asie    | Mean Rev       | Breakout Fade
(00h-08h UTC)   | (range-bound)  | (fake breakouts)
----------------|----------------|----------------
Session EU-US   | Momentum       | Risk-Off
(08h-16h UTC)   | (trending)     | (réduire exposition)
```

### Justification
- Session Asie: volume faible → ranges, mean-reversion
- Session EU-US: volume fort → trends, momentum
- Vol haute en Asie: souvent des fake breakouts (low liquidity)
- Vol haute en EU-US: vrais mouvements → réduire risque

### Temps d'implémentation: 4-6 jours

---

## 🎯 Stratégie #6: Shadow P&L by Skew Regime (P2) ⭐

### Concept
**Tracker P&L séparément pour chaque régime de skewness.**

### Tracking
```
P&L_skew_positive   (skew > +0.3)   → Performance en régime "pump"
P&L_skew_negative   (skew < -0.2)   → Performance en régime "crash"
P&L_skew_neutral    (-0.2 à +0.3)   → Performance en régime "balance"
```

### Usage: Meta-Apprentissage
Le système apprend **QUAND** il performe, pas juste **COMBIEN**.

```
Si P&L_skew_positive >> P&L_skew_negative:
  → Système performe mieux en régime bull
  → Ajuster: favoriser longs, réduire shorts

Si P&L_skew_negative >> P&L_skew_positive:
  → Système performe mieux en régime bear
  → Ajuster: favoriser shorts, réduire longs
```

### Temps d'implémentation: 3-4 jours

---

## 🎯 Stratégie #7: Microstructure Executor (P2) ⭐

### Concept
**Order book imbalance + TWAP/VWAP pour optimiser l'exécution et réduire le slippage.**

### Règles
```
Order Book Imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)

imbalance > +0.3   → Pression acheteuse → Éviter d'entrer LONG (slippage élevé)
imbalance < -0.3   → Pression vendeuse → Éviter d'entrer SHORT (slippage élevé)
```

### Execution pour gros ordres (>10k USDT)
```
TWAP (Time-Weighted Average Price):
- Découper ordre en N tranches
- Exécuter une tranche toutes les X minutes
- Réduit l'impact marché

VWAP (Volume-Weighted Average Price):
- Découper ordre proportionnellement au volume
- Exécuter plus quand volume élevé, moins quand volume faible
- Minimise le slippage
```

### Données
- Spread BTC: 0.01-0.05% (très tight)
- Slippage ∝ √(taille_order / liquidité)
- Critique sur TF < 1h (5-15min)

### Temps d'implémentation: 1-2 semaines

---

## 🔗 Connections Inattendues Identifiées

1. **GARCH × Position Sizing:** GARCH non juste pour prévision vol, mais pour **risk management ACTIF**
2. **Skewness × HMM:** Skewness comme **input HMM supplémentaire** (pas seulement returns/vol)
3. **ML × Confidence:** XGBoost + Purged CV > heuristiques manuelles pour confidence scoring
4. **Microstructure × TF:** Slippage critique sur petits TF → favoriser 1h+ pour Momentum Fade
5. **ARIMA × Mean Reversion:** ARIMA forecast comme **filtre** pour activer MeanRev vs Momentum

---

## 📊 Insights Majeurs

### Insight #1: Fat tails = FEATURE, pas bug
Les événements extrêmes sont 100x+ plus fréquents que distribution normale → **exploiter** via Fat Tail Hunter, pas filtrer.

### Insight #2: Skewness = MÉTA-SIGNAL
Pas juste statistique descriptive → **Skewness Gate** active/désactive stratégies dynamiquement.

### Insight #3: GARCH persistance 0.94 = volatilité PRÉVISIBLE
→ **Vola-Targeting** dynamique pour risk management actif.

### Insight #4: XGBoost + Purged CV > heuristiques manuelles
→ **ML Confidence Engine** remplace pondérations manuelles.

### Insight #5: Microstructure critique sur petits TF
→ **Microstructure Executor** pour optimiser slippage sur 5-15min.

---

## 🎯 Prochaines Étapes

1. **Finir Master 3-4** (Portfolio Optimization, Risk Management Advanced)
2. **Backtester chaque stratégie** individuellement
3. **Tester combinaisons** (ex: Fat Tail Hunter + Skewness Gate + GARCH Vola-Targeting)
4. **Paper trading** en live (signal-only, W exécute manuellement)
5. **Itérer** basé sur performance réelle

---

**Note:** Ces 7 stratégies sont 100% originales, inspirées des insights Dream Processing + consolidation Master 1+2. Aucune n'est copiée de Yagati v4.
