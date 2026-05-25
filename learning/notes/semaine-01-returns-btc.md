# Semaine 01 - Analyse des distributions de returns BTC

**Date:** 23 mai 2026  
**Timeframes analysés:** 5min, 1h, daily  
**Période:** 6-24 mois selon timeframe  
**Source:** Binance via CCXT

---

## 1. Objectif du module

Comprendre le comportement statistique des prix du BTC avant de coder des stratégies de trading. Cette analyse fondamentale permet de:

- Caractériser la distribution des returns
- Tester les hypothèses de normalité
- Vérifier la stationnarité des séries
- Observer les phénomènes de clustering de volatilité

---

## 2. Données récupérées

| Timeframe | Période | Nombre de records | Date range |
|-----------|---------|-------------------|------------|
| 5min | 6 mois | 51,840 | 2025-11-24 → 2026-05-23 |
| 1h | 12 mois | 8,640 | 2025-05-28 → 2026-05-23 |
| daily | 24 mois | 720 | 2024-06-03 → 2026-05-23 |

---

## 3. Calcul des returns

### Formules utilisées

**Return simple:**
```
R_t = (P_t - P_{t-1}) / P_{t-1}
```

**Return log:**
```
r_t = ln(P_t / P_{t-1})
```

### Statistiques descriptives

#### 5 minutes

| Métrique | Simple Return | Log Return |
|----------|---------------|------------|
| Mean | -0.000002 | -0.000003 |
| Std | 0.001468 | 0.001467 |
| Skewness | 0.5367 | 0.4831 |
| Kurtosis (excess) | 23.0642 | 22.3381 |
| JB p-value | 0.00e+00 | 0.00e+00 |

#### 1 heure

| Métrique | Simple Return | Log Return |
|----------|---------------|------------|
| Mean | -0.000029 | -0.000039 |
| Std | 0.004423 | 0.004426 |
| Skewness | -0.1954 | -0.2619 |
| Kurtosis (excess) | 8.0480 | 8.1073 |
| JB p-value | 0.00e+00 | 0.00e+00 |

#### Daily

| Métrique | Simple Return | Log Return |
|----------|---------------|------------|
| Mean | 0.000443 | 0.000153 |
| Std | 0.024099 | 0.024058 |
| Skewness | 0.2574 | 0.0341 |
| Kurtosis (excess) | 4.1843 | 4.3171 |
| JB p-value | 2.56e-114 | 7.40e-120 |

---

## 4. Analyse des distributions

### 4.1 Normalité des returns

**Conclusion majeure:** Les returns **NE SUIVENT PAS** une loi normale sur aucun timeframe.

**Preuves:**

1. **Test de Jarque-Bera:** p-value ≈ 0 pour tous les timeframes
   - Rejet massif de l'hypothèse de normalité
   - Valeurs extrêmes dues aux fat tails

2. **Kurtosis (excess kurtosis):**
   - 5m: **22.34** (extrêmement leptokurtique)
   - 1h: **8.11** (leptokurtique)
   - 1d: **4.32** (leptokurtique)
   
   Une distribution normale a un kurtosis excess = 0. Toutes les distributions observées ont des **fat tails** (queues épaisses).

3. **Skewness (asymétrie):**
   - 5m: **+0.48** (asymétrie positive - plus de grands mouvements positifs)
   - 1h: **-0.26** (asymétrie négative - légère tendance aux crashes)
   - 1d: **+0.03** (quasi-symétrique)

### 4.2 Interprétation

**Fat tails (leptokurtique):**
- Les événements extrêmes sont **beaucoup plus fréquents** que prédit par une normale
- Un mouvement de >5σ arrive bien plus souvent qu'1 fois tous les 3.5 millions d'observations
- **Implication trading:** Les risques de queue (tail risk) sont sous-estimés par les modèles normaux

**Pourquoi c'est important:**
- Les modèles type Black-Scholes (normaux) sous-estiment le risque
- Les Value-at-Risk (VaR) gaussiennes sont dangereusement optimistes
- Les stratégies de trading doivent intégrer ce risque extrême

---

## 5. Tests de stationnarité (ADF)

### Résultats Augmented Dickey-Fuller

| Timeframe | Prix stationnaire? | Returns stationnaire? |
|-----------|-------------------|----------------------|
| 5m | ❌ Non (p=0.52) | ✅ Oui (p=0.00) |
| 1h | ❌ Non (p=0.78) | ✅ Oui (p=0.00) |
| 1d | ❌ Non (p=0.50) | ✅ Oui (p=0.00) |

### Interprétation

**Prix:** Non-stationnaires (comme attendu)
- Présence d'une racine unitaire
- La moyenne et la variance changent dans le temps
- **Implication:** On ne peut pas modéliser les prix directement avec des ARIMA standards

**Returns:** Stationnaires (comme attendu)
- Pas de racine unitaire
- Moyenne et variance constantes dans le temps (en première approximation)
- **Implication:** Les returns sont modélisables (ARMA, GARCH, etc.)

**Pourquoi c'est important:**
- La plupart des modèles de séries temporelles requièrent la stationnarité
- On travaille sur les returns, pas les prix
- La stationnarité des returns justifie l'utilisation de modèles de volatilité (GARCH)

---

## 6. Analyse de la volatilité

### Volatilité annualisée (rolling 20 périodes)

| Timeframe | Mean Vol | Std Vol | Ratio Std/Mean | Clustering? |
|-----------|----------|---------|----------------|-------------|
| 5m | 1.94% | 1.30% | 0.67 | ✅ Oui |
| 1h | 6.27% | 3.17% | 0.51 | ✅ Oui |
| 1d | 36.37% | 12.80% | 0.35 | ✅ Oui |

### Clustering de volatilité

**Observation:** La volatilité se regroupe dans le temps.

**Caractéristiques:**
- Périodes de haute volatilité tendent à persister
- Périodes de calme persistent aussi
- Ratio Std/Mean élevé (>0.3) indique un clustering marqué

**Implications trading:**
- La volatilité est **prévisible** dans une certaine mesure
- Modèles GARCH sont appropriés
- Le risk management doit s'adapter dynamiquement
- Les stratégies vola-targeting sont pertinentes

---

## 7. Visualisations générées

1. **01_distributions.png** - Histogrammes + courbe normale théorique + Q-Q plots
2. **02_volatility_clustering.png** - Volatilité rolling par timeframe
3. **03_price_evolution.png** - Évolution des prix BTC/USDT
4. **04_returns_timeseries.png** - Série temporelle des log returns

---

## 8. Conclusions principales

### ✅ Ce qu'on a confirmé

1. **Les returns ne sont PAS normaux** - Fat tails massives, surtout en 5m
2. **Les prix sont non-stationnaires** - Comme attendu pour un actif financier
3. **Les returns sont stationnaires** - Permet la modélisation
4. **Clustering de volatilité présent** - Justifie les modèles GARCH

### 🎯 Implications pour la suite

1. **Risk management:**
   - Ne jamais utiliser de VaR gaussienne
   - Utiliser VaR historique ou Monte Carlo avec distributions empiriques
   - Stress tests essentiels

2. **Modélisation:**
   - Distributions: Student-t, skewed-t, ou non-paramétrique
   - Volatilité: GARCH, EGARCH, ou modèles stochastiques
   - Éviter les hypothèses normales

3. **Stratégies:**
   - Les breaks de volatilité sont exploitables
   - Le momentum peut persister à cause du clustering
   - Attention aux queues de distribution (stop-loss adaptatifs)

### ⚠️ Surprises / Insights

- **5m extrêmement leptokurtique** (kurtosis > 22!): le trading haute fréquence expose à des risques extrêmes
- **Skewness change selon timeframe:** positif en 5m, négatif en 1h, neutre en daily
- **Volatilité daily ~36% annualisée:** BTC reste très volatil même après 2 ans de données

---

## 9. Prochaines étapes (Semaine 2+)

- [ ] Modélisation GARCH de la volatilité
- [ ] Tests d'autocorrélation des returns
- [ ] Analyse des corrélations intra/inter-timeframe
- [ ] Backtesting de stratégies simples
- [ ] Intégration du risk management adaptatif

---

**Références:**
- Cont, R. (2001). "Empirical properties of asset returns: stylized facts and statistical issues"
- Tsay, R. (2010). "Analysis of Financial Time Series"
- Documentation CCXT: https://docs.ccxt.com/
