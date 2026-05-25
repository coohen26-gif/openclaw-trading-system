# Semaine 21 - Multi-Asset Allocation (BTC/ETH/SOL)

**Date:** 24 Mai 2026  
**Niveau:** Phase 2 - Intégration Saiyan  
**Temps estimé:** 2-3h

---

## 🎯 Objectifs du Module

1. Implémenter 3 stratégies d'allocation: Equal Weight, Risk Parity, Kelly
2. Analyser les performances sur portfolio crypto (BTC/ETH/SOL)
3. Comparer les risk contributions de chaque approche
4. Visualiser l'évolution des weights dans le temps
5. Recommander une allocation pour le Système Saiyan

---

## 📚 Théorie Fondamentale

### 1. Equal Weight (Naïve Diversification)

**Principe:**
```
wᵢ = 1/n  pour tous les assets
```

**Avantages:**
- ✅ Simple, pas d'estimation requise
- ✅ Pas de model risk
- ✅ Se rebalance automatiquement (vend les gagnants, achète les perdants)

**Inconvénients:**
- ❌ Ignore les différences de risque
- ❌ Les assets volatils dominent le risque total
- ❌ Sous-optimal pour le risk-adjusted return

### 2. Risk Parity (Allouer le Risque, pas le Capital)

**Principe:**
```
RCᵢ = RCⱼ  pour tous i, j

Où RCᵢ = wᵢ × (Σw)ᵢ / σ_p = risk contribution de l'asset i
```

**Intuition:**
- BTC est moins volatil que ETH et SOL
- Donc Risk Parity donne PLUS de poids à BTC
- Chaque asset contribue ÉGALEMENT au risque total

**Formule simplifiée (inverse volatility):**
```
wᵢ ∝ 1/σᵢ
```

**Avantages:**
- ✅ Meilleur risk-adjusted return (Sharpe)
- ✅ Diversification véritable (pas illusionnaire)
- ✅ Réduit l'exposition aux assets volatils

**Inconvénients:**
- ❌ Nécessite estimation de covariance (Σ)
- ❌ Σ n'est pas stationnaire → weights varient dans le temps
- ❌ Peut underperform en bull market (les assets risqués montent plus)

### 3. Kelly Criterion (Optimisation de Croissance)

**Principe:**
```
f* = μ / σ²  (forme continue)

Fractional Kelly: f = α × f*  où α ∈ [0.25, 0.75]
```

**Avantages:**
- ✅ Maximise la croissance à long terme
- ✅ Prend en compte l'edge (μ) et le risque (σ²)
- ✅ Fractional Kelly réduit la volatilité drastiquement

**Inconvénients:**
- ❌ Très sensible à l'estimation de μ
- ❌ Peut donner des weights >100% (nécessite leverage)
- ❌ Si μ est négatif ou mal estimé → weights bizarres

---

## 💻 Implémentation Python

### 1. Risk Parity (Sans cvxpy)

```python
def risk_parity_weights(returns, target_risk_contrib=None):
    """
    Calculate Risk Parity weights that equalize risk contribution.
    Simplified version without cvxpy dependency.
    """
    n_assets = returns.shape[1]
    cov_matrix = returns.cov().values
    
    if target_risk_contrib is None:
        target_risk_contrib = np.ones(n_assets) / n_assets
    
    # Initialize with inverse volatility
    vols = np.sqrt(np.diag(cov_matrix))
    weights = 1 / vols
    weights = weights / weights.sum()
    
    # Iterative refinement to equalize risk contributions
    for _ in range(100):
        portfolio_var = weights @ cov_matrix @ weights
        portfolio_vol = np.sqrt(portfolio_var)
        marginal_risk = cov_matrix @ weights
        risk_contrib = weights * marginal_risk / portfolio_vol
        risk_contrib_pct = risk_contrib / portfolio_vol
        
        # Adjust weights to equalize risk contributions
        for i in range(n_assets):
            if risk_contrib_pct[i] > target_risk_contrib[i]:
                weights[i] *= 0.98  # Reduce weight if contributing too much risk
            elif risk_contrib_pct[i] < target_risk_contrib[i]:
                weights[i] *= 1.02  # Increase weight if contributing too little risk
        
        # Renormalize
        weights = weights / weights.sum()
        weights = np.maximum(weights, 0.01)  # Minimum 1% weight
        weights = weights / weights.sum()
    
    return weights
```

### 2. Kelly Fractionnaire

```python
def kelly_weights(returns, max_position=0.40, fraction=0.5):
    """
    Calculate Fractional Kelly weights.
    """
    n_assets = returns.shape[1]
    mu = returns.mean().values * 252  # Annualized
    cov_matrix = returns.cov().values * 252
    
    # Simplified Kelly: f* = μ / σ² for each asset
    kelly_fractions = mu / np.diag(cov_matrix)
    
    # Apply fractional Kelly (Half-Kelly = 0.5)
    kelly_fractions = fraction * kelly_fractions
    
    # Apply constraints
    kelly_fractions = np.clip(kelly_fractions, 0, max_position)
    
    # Normalize to sum to 1
    if kelly_fractions.sum() > 0:
        kelly_fractions = kelly_fractions / kelly_fractions.sum()
    else:
        kelly_fractions = np.ones(n_assets) / n_assets
    
    return kelly_fractions
```

### 3. Rolling Allocation (Évolution dans le Temps)

```python
def rolling_allocation(returns, window=60, method='risk_parity'):
    """
    Calculate rolling allocation weights to show evolution over time.
    """
    n = len(returns)
    weights_history = []
    dates = []
    
    for i in range(window, n, 5):  # Every 5 days for efficiency
        returns_window = returns.iloc[i-window:i]
        
        if method == 'risk_parity':
            w = risk_parity_weights(returns_window)
        elif method == 'kelly':
            w = kelly_weights(returns_window)
        else:  # equal weight
            w = np.ones(returns.shape[1]) / returns.shape[1]
        
        weights_history.append(w)
        dates.append(returns.index[i])
    
    return pd.DataFrame(weights_history, index=dates, columns=returns.columns)
```

---

## 📊 Résultats sur Portfolio Crypto (BTC/ETH/SOL)

### Données Utilisées

- **BTC:** Données réelles (Binance, 719 jours)
- **ETH:** Données synthétiques (réalistes, basées sur stats historiques)
- **SOL:** Données synthétiques (réalistes, basées sur stats historiques)

**Période:** ~2 ans (719 observations)

### Statistiques Individuelles

| Asset | Ann. Return | Ann. Vol | Sharpe | VaR 95% (daily) |
|-------|-------------|----------|--------|-----------------|
| **BTC** | +11.2% | 38.3% | 0.29 | -3.63% |
| **ETH** | -4.2% | 52.1% | -0.08 | -5.17% |
| **SOL** | -3.5% | 73.2% | -0.05 | -7.26% |

**Observations:**
- BTC est le seul avec return positif et Sharpe positif
- ETH et SOL ont des returns négatifs sur cette période (bear market altcoins)
- Volatilité: BTC < ETH < SOL (comme attendu)

### Comparaison des Stratégies d'Allocation

#### 1. Equal Weight

**Weights:** BTC 33.3%, ETH 33.3%, SOL 33.3%

| Métrique | Valeur |
|----------|--------|
| Annual Return | +1.2% |
| Annual Volatility | 43.6% |
| Sharpe Ratio | -0.02 |
| Max Drawdown | -56.1% |
| Total Return | -21.2% |
| VaR 95% (daily) | -4.46% |
| CVaR 95% (daily) | -5.67% |

**Analyse:**
- Diversification naïve ne fonctionne PAS bien ici
- ETH et SOL (négatifs) draguent le portfolio vers le bas
- Volatilité élevée, Sharpe négatif

#### 2. Risk Parity 🏆

**Weights:** BTC 52.3%, ETH 27.9%, SOL 19.8%

| Métrique | Valeur |
|----------|--------|
| Annual Return | +4.0% |
| Annual Volatility | 35.2% |
| Sharpe Ratio | **0.06** |
| Max Drawdown | **-50.5%** |
| Total Return | -6.1% |
| VaR 95% (daily) | -3.66% |
| CVaR 95% (daily) | -4.56% |

**Analyse:**
- ✅ **Meilleur Sharpe** (0.06 vs -0.02 pour Equal Weight)
- ✅ **Volatilité réduite** (35.2% vs 43.6%)
- ✅ **Max Drawdown réduit** (-50.5% vs -56.1%)
- ✅ **VaR/CVaR améliorés**
- BTC a le plus gros poids (le moins volatil)

**Risk Contributions (vérification):**
- BTC: ~33%, ETH: ~33%, SOL: ~34%
- ✅ Risk Parity fonctionne: chaque asset contribue également au risque!

#### 3. Half-Kelly

**Weights:** BTC 100% (concentré!)

| Métrique | Valeur |
|----------|--------|
| Annual Return | +11.2% |
| Annual Volatility | 38.3% |
| Sharpe Ratio | 0.24 |
| Max Drawdown | -49.5% |
| Total Return | +11.7% |
| VaR 95% (daily) | -3.63% |
| CVaR 95% (daily) | -5.20% |

**Analyse:**
- Kelly a détecté que ETH et SOL ont des μ négatifs
- → Weight = 0 pour ETH et SOL
- → 100% BTC (le seul avec return positif)
- **Meilleur Sharpe (0.24)** mais **pas diversifié**

**Problème:**
- Kelly est TRÈP sensible à l'estimation de μ
- Sur cette période, ETH/SOL ont eu des returns négatifs
- Mais dans le futur, ils pourraient surperformer
- **Kelly pur = manque de diversification**

---

## 💡 Insights Clés

### 1. Risk Parity > Equal Weight

| Métrique | Equal Weight | Risk Parity | Amélioration |
|----------|--------------|-------------|--------------|
| Sharpe | -0.02 | 0.06 | +0.08 |
| Volatilité | 43.6% | 35.2% | **-19%** |
| Max DD | -56.1% | -50.5% | **-10%** |
| VaR 95% | -4.46% | -3.66% | **-18%** |

**Conclusion:** Risk Parity réduit le risque de ~20% sans sacrifier le return.

### 2. Kelly est Dangereux sans Contraintes

- Kelly pur → 100% BTC (concentration extrême)
- Si BTC avait eu un return négatif, Kelly aurait pu donner des weights négatifs (short)
- **Toujours utiliser Fractional Kelly avec des constraints:**
  - Max position par asset (ex: 40%)
  - Min position pour diversification (ex: 10%)
  - Long-only (pas de short)

### 3. Risk Parity s'Adapte à la Volatilité

**Rolling Risk Parity (60 jours):**
- Les weights évoluent dans le temps
- Quand BTC devient plus volatil → son poids diminue
- Quand SOL devient moins volatil → son poids augmente
- **Allocation dynamique = meilleure adaptation aux régimes**

### 4. Correlations Crypto

**Matrice de corrélation (BTC/ETH/SOL):**
```
       BTC    ETH    SOL
BTC   1.00   0.78   0.72
ETH   0.78   1.00   0.81
SOL   0.72   0.81   1.00
```

**Observations:**
- Fortes corrélations (0.72-0.81)
- → La diversification est LIMITÉE dans crypto
- → Risk Parity aide, mais ne peut pas créer de diversification magique
- → Besoin d'assets non-crypto pour vraie diversification

---

## 🛠️ Application pour Saiyan

### 1. Allocation Recommandée

**Pour le Système Saiyan (crypto-only):**

```python
SAIYAN_ALLOCATION = {
    'method': 'risk_parity',
    'assets': ['BTC', 'ETH', 'SOL'],
    'constraints': {
        'max_position': 0.50,  # Max 50% par asset
        'min_position': 0.10,  # Min 10% pour diversification
        'rebalance_frequency': 'weekly'  # Rebalancer chaque semaine
    }
}
```

**Weights typiques (Risk Parity):**
- BTC: 50-55% (le "stable" crypto)
- ETH: 25-30%
- SOL: 15-20%

### 2. Rebalancing Dynamique

```python
def saiyan_rebalance(current_weights, target_weights, threshold=0.05):
    """
    Rebalance portfolio if weights drift beyond threshold.
    """
    drift = np.abs(current_weights - target_weights)
    
    if np.any(drift > threshold):
        # Rebalance needed
        return target_weights, 'REBALANCED'
    else:
        return current_weights, 'NO_ACTION'

# Exemple:
# current = [0.60, 0.25, 0.15]  # BTC a monté, poids dérivé
# target = [0.52, 0.28, 0.20]
# drift = [0.08, 0.03, 0.05]
# → Rebalance (BTC drift > 5%)
```

### 3. Risk-Adjusted Position Sizing

```python
def saiyan_position_size(base_size, asset_vol, target_vol=0.35):
    """
    Adjust position size based on asset volatility.
    Target: 35% annualized portfolio volatility.
    """
    vol_ratio = target_vol / asset_vol
    position_size = base_size * vol_ratio
    
    # Constraints
    position_size = np.clip(position_size, base_size * 0.5, base_size * 1.5)
    
    return position_size

# Exemple:
# base_size = $10,000
# BTC vol = 38% → position = $10,000 × (35/38) = $9,210
# SOL vol = 73% → position = $10,000 × (35/73) = $4,790
```

---

## ⚠️ Limites et Mises en Garde

### 1. Données Synthétiques (ETH/SOL)

**Problème:**
- ETH et SOL utilisent des données synthétiques (pas de fichiers CSV)
- Les stats sont réalistes mais pas exactes

**Mitigation:**
- Fetcher les vraies données via CCXT (Binance)
- Ou utiliser Yahoo Finance si disponible

### 2. Non-Stationnarité

**Problème:**
- Les corrélations crypto changent dans le temps
- En crise: corrélations → 1 (diversification disparaît)
- Les weights Risk Parity optimisés sur le passé ne sont pas optimaux pour le futur

**Mitigation:**
- Rolling window (60 jours) pour estimation
- Rebalancing fréquent (hebdomadaire)
- Monitoring des corrélations en temps réel

### 3. Kelly Overfitting

**Problème:**
- Kelly a donné 100% BTC car ETH/SOL ont des μ négatifs
- C'est un overfit sur la période historique
- Dans le futur, ETH/SOL pourraient surperformer

**Mitigation:**
- **Toujours utiliser Fractional Kelly** (α = 0.25 à 0.5)
- Ajouter des constraints de diversification (min 10% par asset)
- Ou utiliser Risk Parity (plus robuste)

### 4. Transaction Costs

**Problème:**
- Le rebalancing génère des frais de transaction
- Si rebalancing trop fréquent → costs mangent les gains

**Mitigation:**
- Rebalancer seulement si drift > threshold (ex: 5%)
- Ou rebalancing calendaire (hebdomadaire/mensuel)
- Inclure transaction costs dans l'optimisation

---

## 📈 Visualisations Générées

1. **Allocation Comparison:** Weights, Risk Contributions, Performance Metrics
2. **Cumulative Returns:** Equal Weight vs Risk Parity vs Kelly
3. **Drawdown Comparison:** Max DD par stratégie
4. **Rolling Weights:** Évolution Risk Parity dans le temps
5. **Risk-Return Scatter:** Assets individuels vs portfolios
6. **Correlation Matrix:** Heatmap BTC/ETH/SOL

**Fichiers créés:**
- `learning/figures/multi-asset-allocation-comparison.png`
- `learning/figures/multi-asset-risk-return.png`
- `learning/figures/multi-asset-correlation.png`

---

## ✅ Checklist de Compréhension

- [ ] Comprendre différence Equal Weight vs Risk Parity vs Kelly
- [ ] Savoir calculer Risk Parity weights (itératif ou cvxpy)
- [ ] Comprendre pourquoi Kelly peut donner des weights extrêmes
- [ ] Savoir implémenter Fractional Kelly avec constraints
- [ ] Comprendre l'impact des corrélations sur la diversification
- [ ] Savoir calculer risk contributions et vérifier Risk Parity
- [ ] Implémenter rebalancing avec threshold

---

## 📚 Références

1. **Qian, E. (2005).** "Risk Parity Portfolios." *Journal of Portfolio Management.*
2. **Lopez de Prado, M. (2016).** "Hierarchical Risk Parity." *Journal of Investment Strategies.*
3. **Thorp, E. (2006).** "The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market."
4. **Bridgewater Associates.** "All Weather Strategy" (Risk Parity appliqué).

---

## 🎯 Prochaines Étapes

**Phase 2 - Intégration Saiyan:**
- [ ] Implémenter Risk Parity dans le code Saiyan
- [ ] Ajouter rebalancing automatique (seuil 5%)
- [ ] Risk-adjusted position sizing par asset
- [ ] Monitoring des corrélations en temps réel

**Master 5+:**
- [ ] Semaine 22: Production Systems & Infrastructure
- [ ] Semaine 23: Derivatives (Options, Futures)
- [ ] Semaine 24: HFT & Market Microstructure Avancée

---

*Module Phase 2 - Multi-Asset Allocation complété ✅*
