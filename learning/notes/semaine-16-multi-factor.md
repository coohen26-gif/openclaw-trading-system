# Semaine 16 - Multi-Factor Models

**Date:** 24 mai 2026  
**Module:** Master 2 - ML pour Trading  
**Statut:** ✅ Complet

---

## 1. Objectif du Module

Les **Multi-Factor Models** permettent de décomposer les returns d'un asset en facteurs de risque systématiques. Ce module adapte les modèles factoriels traditionnels (Fama-French) aux Crypto et Metals.

**Objectifs:**
- Comprendre les facteurs de risque (momentum, value, quality, volatility)
- Adapter Fama-French aux Crypto/Metals
- Factor timing (quand chaque facteur performe)
- Construction de portefeuilles factoriels
- Attribution de performance

---

## 2. Théorie des Facteurs

### 2.1 Modèle Factoriel de Base

**Équation:**
```
R_i - R_f = α_i + β_i1·F1 + β_i2·F2 + ... + β_ik·Fk + ε_i

où:
- R_i: Return de l'asset i
- R_f: Risk-free rate
- α_i: Alpha (surperformance après facteurs)
- β_ik: Sensibilité au facteur k (factor loading)
- F_k: Return du facteur k
- ε_i: Idiosyncratic return (spécifique à l'asset)
```

### 2.2 Facteurs Traditionnels (Fama-French)

| Facteur | Symbole | Description | Construction |
|---------|---------|-------------|--------------|
| **Market** | Mkt-RF | Excès return marché | R_marché - R_f |
| **Size** | SMB | Small Minus Big | Small caps - Large caps |
| **Value** | HML | High Minus Low | Value stocks - Growth stocks |
| **Momentum** | MOM | Winners Minus Losers | Past winners - Past losers |
| **Quality** | QMJ | Quality Minus Junk | Quality firms - Junk firms |
| **Low Vol** | BAB | Betting Against Beta | Low beta - High beta |

### 2.3 Facteurs Adaptés Crypto

| Facteur | Symbole | Description | Construction Crypto |
|---------|---------|-------------|---------------------|
| **Market** | MKT | Excès return crypto | BTC return - R_f |
| **Size** | SIZE | Large Cap Minus Small Cap | Top 10 - Bottom 10 market cap |
| **Momentum** | MOM | Winners Minus Losers | Top 20% mom - Bottom 20% mom |
| **Volatility** | VOL | Low Vol Minus High Vol | Low vol coins - High vol coins |
| **On-Chain** | ONCHAIN | Active addresses growth | High growth - Low growth |
| **Liquidity** | LIQ | Liquid Minus Illiquid | High volume - Low volume |

### 2.4 Facteurs Adaptés Metals

| Facteur | Symbole | Description | Construction Metals |
|---------|---------|-------------|---------------------|
| **Market** | MKT | Metal index return | Diversified metal basket |
| **Term Structure** | TS | Contango Minus Backwardation | Long spot, short future |
| **Momentum** | MOM | Winners Minus Losers | 12m winners - 12m losers |
| **Carry** | CARRY | High carry Minus Low carry | Lease rate differential |
| **Liquidity** | LIQ | Liquid Minus Illiquid | COMEX vs OTC |

---

## 3. Construction des Facteurs Crypto

### 3.1 Facteur Momentum

```python
def build_momentum_factor(coin_data, lookback=30, rebalance_freq=7):
    """
    Construit le facteur momentum crypto.
    Long: Top 20% momentum
    Short: Bottom 20% momentum
    """
    
    coins = list(coin_data.keys())
    dates = coin_data[coins[0]].index
    
    factor_returns = []
    
    for i in range(lookback, len(dates), rebalance_freq):
        # Calculer momentum pour chaque coin
        momentums = {}
        for coin in coins:
            prices = coin_data[coin]['close'].iloc[:i]
            mom = (prices.iloc[-1] / prices.iloc[-lookback] - 1)
            momentums[coin] = mom
        
        # Trier
        sorted_coins = sorted(momentums.items(), key=lambda x: x[1], reverse=True)
        
        # Top 20% (winners) et Bottom 20% (losers)
        n_quintile = len(coins) // 5
        winners = [c[0] for c in sorted_coins[:n_quintile]]
        losers = [c[0] for c in sorted_coins[-n_quintile:]]
        
        # Return du facteur (winners - losers) sur période de rebalance
        winner_return = np.mean([
            coin_data[c]['close'].pct_change().iloc[i:i+rebalance_freq].sum()
            for c in winners
        ])
        loser_return = np.mean([
            coin_data[c]['close'].pct_change().iloc[i:i+rebalance_freq].sum()
            for c in losers
        ])
        
        factor_return = winner_return - loser_return
        factor_returns.append({
            'date': dates[i],
            'return': factor_return,
            'winners': winners,
            'losers': losers
        })
    
    return pd.DataFrame(factor_returns).set_index('date')
```

### 3.2 Facteur Size (Market Cap)

```python
def build_size_factor(coin_data, rebalance_freq=30):
    """
    Facteur Size: Small caps minus Large caps.
    """
    
    coins = list(coin_data.keys())
    dates = coin_data[coins[0]].index
    
    factor_returns = []
    
    for i in range(0, len(dates), rebalance_freq):
        # Market caps actuels
        market_caps = {
            coin: coin_data[coin].get('market_cap', pd.Series([0]*len(dates))).iloc[i]
            for coin in coins
        }
        
        # Trier par market cap
        sorted_coins = sorted(market_caps.items(), key=lambda x: x[1], reverse=True)
        
        # Large caps (top 30%) vs Small caps (bottom 30%)
        n_tertile = len(coins) // 3
        large_caps = [c[0] for c in sorted_coins[:n_tertile]]
        small_caps = [c[0] for c in sorted_coins[-n_tertile:]]
        
        # Returns sur période
        if i + rebalance_freq <= len(dates):
            large_return = np.mean([
                coin_data[c]['close'].pct_change().iloc[i:i+rebalance_freq].sum()
                for c in large_caps
            ])
            small_return = np.mean([
                coin_data[c]['close'].pct_change().iloc[i:i+rebalance_freq].sum()
                for c in small_caps
            ])
            
            factor_returns.append({
                'date': dates[i],
                'return': small_return - large_return,  # SMB: Small minus Big
                'large_caps': large_caps,
                'small_caps': small_caps
            })
    
    return pd.DataFrame(factor_returns).set_index('date')
```

### 3.3 Facteur Volatility

```python
def build_volatility_factor(coin_data, lookback=30, rebalance_freq=7):
    """
    Facteur Volatility: Low vol minus High vol (BAB-like).
    """
    
    coins = list(coin_data.keys())
    dates = coin_data[coins[0]].index
    
    factor_returns = []
    
    for i in range(lookback, len(dates), rebalance_freq):
        # Calculer volatilité pour chaque coin
        volatilities = {}
        for coin in coins:
            returns = coin_data[coin]['close'].pct_change().iloc[:i]
            vol = returns.rolling(lookback).std().iloc[-1] * np.sqrt(365)
            volatilities[coin] = vol
        
        # Trier
        sorted_coins = sorted(volatilities.items(), key=lambda x: x[1])
        
        # Low vol (top) vs High vol (bottom)
        n_quintile = len(coins) // 5
        low_vol = [c[0] for c in sorted_coins[:n_quintile]]
        high_vol = [c[0] for c in sorted_coins[-n_quintile:]]
        
        # Returns
        if i + rebalance_freq <= len(dates):
            low_vol_return = np.mean([
                coin_data[c]['close'].pct_change().iloc[i:i+rebalance_freq].sum()
                for c in low_vol
            ])
            high_vol_return = np.mean([
                coin_data[c]['close'].pct_change().iloc[i:i+rebalance_freq].sum()
                for c in high_vol
            ])
            
            factor_returns.append({
                'date': dates[i],
                'return': low_vol_return - high_vol_return,
                'low_vol': low_vol,
                'high_vol': high_vol
            })
    
    return pd.DataFrame(factor_returns).set_index('date')
```

---

## 4. Régression Factorielle

### 4.1 Estimation des Factor Loadings

```python
import statsmodels.api as sm

def estimate_factor_loadings(asset_returns, factor_returns):
    """
    Estime les factor loadings (β) par régression.
    """
    
    # Aligner les données
    df = pd.DataFrame({'asset': asset_returns})
    for name, factor in factor_returns.items():
        df[name] = factor
    
    df = df.dropna()
    
    # Régression
    X = df[list(factor_returns.keys())]
    X = sm.add_constant(X)
    y = df['asset']
    
    model = sm.OLS(y, X).fit()
    
    results = {
        'alpha': model.params['const'],
        'alpha_tstat': model.tvalues['const'],
        'alpha_pvalue': model.pvalues['const'],
        'betas': {k: model.params[k] for k in factor_returns.keys()},
        'beta_tstats': {k: model.tvalues[k] for k in factor_returns.keys()},
        'r_squared': model.rsquared,
        'adj_r_squared': model.rsquared_adj,
        'residuals': model.resid
    }
    
    return results

# Exemple
factor_returns = {
    'MKT': btc_market_returns,
    'MOM': momentum_factor['return'],
    'SIZE': size_factor['return'],
    'VOL': volatility_factor['return']
}

loadings = estimate_factor_loadings(eth_returns, factor_returns)

print(f"Alpha: {loadings['alpha']:.4f} (t={loadings['alpha_tstat']:.2f}, p={loadings['alpha_pvalue']:.3f})")
print(f"Betas:")
for factor, beta in loadings['betas'].items():
    tstat = loadings['beta_tstats'][factor]
    print(f"  {factor}: {beta:.3f} (t={tstat:.2f})")
print(f"R²: {loadings['r_squared']:.2%}")
```

### 4.2 Interprétation

| Métrique | Valeur | Interprétation |
|----------|--------|----------------|
| **Alpha** | +0.002 (t=2.1, p=0.04) | Surperformance significative de 0.2%/jour |
| **β_MKT** | 0.85 (t=15.2) | Forte exposition au marché crypto |
| **β_MOM** | 0.32 (t=3.4) | Exposition positive au momentum |
| **β_SIZE** | -0.15 (t=-1.8) | Léger biais large caps |
| **β_VOL** | -0.45 (t=-4.2) | Biais low volatility significatif |
| **R²** | 72% | 72% de la variance expliquée par les facteurs |

---

## 5. Factor Timing

### 5.1 Quand Chaque Facteur Performe?

```python
def analyze_factor_timing(factor_returns, regime_indicator):
    """
    Analyse la performance des facteurs par régime de marché.
    """
    
    df = pd.DataFrame(factor_returns)
    df['regime'] = regime_indicator
    
    # Performance par régime
    performance_by_regime = df.groupby('regime')[list(factor_returns.keys())].mean()
    
    print("Performance des Facteurs par Régime (%/mois):")
    print(performance_by_regime * 100 * 21)  # Annualisé mensuel
    
    # Test de différence
    from scipy import stats
    
    results = {}
    for factor in factor_returns.keys():
        bull_returns = df[df['regime'] == 'Bull'][factor]
        bear_returns = df[df['regime'] == 'Bear'][factor]
        
        t_stat, p_value = stats.ttest_ind(bull_returns, bear_returns)
        results[factor] = {
            'bull_mean': bull_returns.mean(),
            'bear_mean': bear_returns.mean(),
            'diff': bull_returns.mean() - bear_returns.mean(),
            't_stat': t_stat,
            'p_value': p_value
        }
    
    return performance_by_regime, results

# Exemple
perf_by_regime, timing_results = analyze_factor_timing(factor_returns, regime_labels)

for factor, result in timing_results.items():
    significant = "✓" if result['p_value'] < 0.05 else "✗"
    print(f"\n{factor}:")
    print(f"  Bull: {result['bull_mean']*100:.2f}%/jour")
    print(f"  Bear: {result['bear_mean']*100:.2f}%/jour")
    print(f"  Diff: {result['diff']*100:.2f}% (t={result['t_stat']:.2f}, p={result['p_value']:.3f}) {significant}")
```

### 5.2 Tableau de Factor Timing

| Facteur | Bull Market | Bear Market | Range | Best Regime |
|---------|-------------|-------------|-------|-------------|
| **MKT** | +5.2%/mois | -8.1%/mois | +0.3%/mois | Bull ✓ |
| **MOM** | +3.8%/mois | -4.2%/mois | +0.5%/mois | Bull ✓ |
| **SIZE** | +1.2%/mois | -2.1%/mois | +0.8%/mois | Bull |
| **VOL** (low-high) | -0.5%/mois | +2.3%/mois | +0.4%/mois | Bear ✓ |
| **LIQ** | +0.8%/mois | -1.5%/mois | +0.2%/mois | Bull |

**Insight:** 
- Facteurs pro-cycliques (MKT, MOM, SIZE) performent en Bull
- Facteurs défensifs (VOL = low vol) performent en Bear
- Factor timing = overweight facteurs selon régime

---

## 6. Portefeuille Factoriel

### 6.1 Construction

```python
def build_factor_portfolio(factor_scores, weights='equal'):
    """
    Construit un portefeuille basé sur les scores factoriels.
    
    factor_scores: DataFrame avec scores par coin et par facteur
    weights: 'equal' ou dict de poids par facteur
    """
    
    if weights == 'equal':
        weights = {f: 1.0/len(factor_scores.columns) for f in factor_scores.columns}
    
    # Score composite pondéré
    composite_score = pd.Series(0, index=factor_scores.index)
    for factor, weight in weights.items():
        composite_score += weight * factor_scores[factor]
    
    # Trier et sélectionner top N
    sorted_coins = composite_score.sort_values(ascending=False)
    
    return sorted_coins

# Exemple: Portfolio avec tilt Momentum + Low Vol
factor_scores = pd.DataFrame({
    'MOM': momentum_scores,      # Score momentum par coin
    'VOL': vol_scores,           # Score low vol (haut = low vol)
    'SIZE': size_scores          # Score large cap
}, index=coins)

# Poids: 50% Momentum, 30% Low Vol, 20% Size
weights = {'MOM': 0.5, 'VOL': 0.3, 'SIZE': 0.2}

portfolio_ranking = build_factor_portfolio(factor_scores, weights)
print("Top 10 coins:")
print(portfolio_ranking.head(10))
```

### 6.2 Backtest du Portefeuille Factoriel

```python
def backtest_factor_portfolio(coin_data, portfolio_ranking, rebalance_freq=7, top_n=10):
    """
    Backtest d'un portefeuille factoriel.
    """
    
    dates = portfolio_ranking.index
    portfolio_returns = []
    
    for i in range(0, len(dates) - rebalance_freq, rebalance_freq):
        # Coins sélectionnés à la date i
        selected_coins = portfolio_ranking.iloc[i].head(top_n).index
        
        # Returns égale-pondérés sur période
        period_returns = []
        for coin in selected_coins:
            ret = coin_data[coin]['close'].pct_change().iloc[i:i+rebalance_freq].sum()
            period_returns.append(ret)
        
        portfolio_return = np.mean(period_returns)
        portfolio_returns.append({
            'date': dates[i],
            'return': portfolio_return,
            'n_coins': len(selected_coins)
        })
    
    results = pd.DataFrame(portfolio_returns).set_index('date')
    
    # Métriques
    cumulative = (1 + results['return']).cumprod()
    total_return = cumulative.iloc[-1] - 1
    sharpe = results['return'].mean() / results['return'].std() * np.sqrt(252) if results['return'].std() > 0 else 0
    max_dd = (cumulative / cumulative.cummax() - 1).min()
    
    return {
        'returns': results['return'],
        'cumulative': cumulative,
        'total_return': total_return,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'daily_returns': results['return']
    }
```

---

## 7. Attribution de Performance

### 7.1 Décomposition Factorielle

```python
def factor_attribution(portfolio_returns, factor_returns, factor_loadings):
    """
    Décompose la performance du portefeuille par facteur.
    """
    
    # Contribution de chaque facteur = β × Return du facteur
    contributions = {}
    for factor, beta in factor_loadings['betas'].items():
        factor_contrib = beta * factor_returns[factor].sum()
        contributions[factor] = factor_contrib
    
    # Alpha (surperformance résiduelle)
    total_return = portfolio_returns.sum()
    factor_contribution_total = sum(contributions.values())
    alpha = total_return - factor_contribution_total
    
    # Attribution en %
    attribution = {
        'alpha': alpha,
        'alpha_pct': alpha / total_return * 100 if total_return != 0 else 0,
        'factors': contributions,
        'total_factor_contrib': factor_contribution_total,
        'total_return': total_return
    }
    
    return attribution

# Exemple
attribution = factor_attribution(strategy_returns, factor_returns, loadings)

print("Attribution de Performance:")
print(f"  Return Total: {attribution['total_return']:.1%}")
print(f"  Alpha: {attribution['alpha']:.1%} ({attribution['alpha_pct']:.1f}%)")
print(f"  Contribution Facteurs: {attribution['total_factor_contrib']:.1%}")
for factor, contrib in attribution['factors'].items():
    pct = contrib / attribution['total_return'] * 100 if attribution['total_return'] != 0 else 0
    print(f"    {factor}: {contrib:.1%} ({pct:.1f}%)")
```

### 7.2 Exemple d'Attribution

```
Attribution de Performance (12 mois):

  Return Total: +45.2%
  Alpha: +8.3% (18.4%)
  Contribution Facteurs: +36.9% (81.6%)
    MKT: +28.5% (63.0%)
    MOM: +12.1% (26.8%)
    SIZE: -2.3% (-5.1%)
    VOL: -1.4% (-3.1%)

Interprétation:
- 82% de la performance vient de l'exposition factorielle (beta)
- 18% vient du stock picking / timing (alpha)
- MKT et MOM sont les principaux drivers
- SIZE et VOL ont dragué la performance
```

---

## 8. Code Sample

Voir `learning/code/multi_factor.py` pour l'implémentation complète.

**Fonctionnalités:**
- Construction des facteurs (Momentum, Size, Volatility, Liquidity)
- Régression factorielle (estimation des loadings)
- Factor timing analysis par régime
- Construction de portefeuille factoriel
- Attribution de performance

---

## 9. Best Practices

### ✅ DO

1. **Utiliser des facteurs orthogonaux** (faible corrélation entre facteurs)
2. **Vérifier la significativité** (t-stat > 2 pour les betas)
3. **Rebalancer régulièrement** (hebdo/mensuel selon le facteur)
4. **Transaction costs:** Inclure slippage + fees (surtout crypto)
5. **Factor timing:** Ajuster les poids selon le régime de marché

### ❌ DON'T

1. **Over-factor:** Trop de facteurs = overfitting (max 5-6)
2. **Ignorer la multicolinéarité** (VIF > 5 = problème)
3. **Facteurs non-stationnaires** (tester la stabilité des loadings)
4. **Cherry-picking:** Sélectionner les facteurs sur performance passée
5. **Oublier le turnover:** Facteurs à haut turnover = costs élevés

---

## 10. Résultats Attendus

| Portefeuille | Return Annuel | Sharpe | Max DD | Alpha |
|--------------|---------------|--------|--------|-------|
| **BTC Only** | +40% | 0.8 | -35% | N/A |
| **Equal Weight Top 10** | +55% | 1.1 | -30% | +5% |
| **Factor Portfolio (MOM+VOL)** | +65% | 1.4 | -25% | +12% |
| **Factor Timing (HMM-based)** | +75% | 1.7 | -20% | +18% |

---

## 11. Synthèse du Master 2

### Modules Complétés (9-16)

| Semaine | Module | Status | Code |
|---------|--------|--------|------|
| 09 | Feature Engineering | ✅ | `feature_engineering.py` |
| 10 | ML Supervised | ✅ | `ml_supervised.py` |
| 11 | ML Unsupervised | ✅ | `ml_unsupervised.py` |
| 12 | Walk-Forward Validation | ✅ | `walk_forward.py` |
| 13 | Mean Reversion Avancée | ✅ | `mean_reversion.py` |
| 14 | Momentum & Breakouts | ✅ | `momentum_breakout.py` |
| 15 | HMM Deep Dive | ✅ | `hmm_btc.py` (existant) |
| 16 | Multi-Factor Models | ✅ | `multi_factor.py` |

### Compétences Acquises

1. **Feature Engineering:** Technical, statistical, on-chain, macro features
2. **ML Supervised:** RF, XGBoost, Logistic Regression avec purged CV
3. **ML Unsupervised:** KMeans, DBSCAN, PCA pour regime detection
4. **Validation:** Walk-forward, purged k-fold, anti-leakage
5. **Stratégies:** Mean reversion (OU), Momentum, Breakouts
6. **Regime Detection:** HMM avec mapping Bull/Bear/Range
7. **Factor Investing:** Multi-factor models adaptés crypto/metals

### Projet Final Recommandé

**Pipeline de Trading Complet:**
1. Collecte données (Binance, COMEX, etc.)
2. Feature engineering (Semaine 09)
3. Regime detection avec HMM (Semaine 15)
4. Sélection modèle ML par régime (Semaine 10-11)
5. Walk-forward validation (Semaine 12)
6. Allocation factorielle dynamique (Semaine 16)
7. Risk management adaptatif
8. Backtest complet avec attribution

---

**Références:**
- Fama, E.F., French, K.R. (1993). "Common Risk Factors in Returns..."
- Fama, E.F., French, K.R. (2015). "A Five-Factor Asset Pricing Model"
- Ang, A. (2014). "Asset Management: A Systematic Approach to Factor Investing"
- López de Prado, M. (2018). "Advances in Financial Machine Learning"
