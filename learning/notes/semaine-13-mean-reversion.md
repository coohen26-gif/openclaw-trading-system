# Semaine 13 - Mean Reversion Avancée

**Date:** 24 mai 2026  
**Module:** Master 2 - ML pour Trading  
**Statut:** ✅ Complet

---

## 1. Objectif du Module

La **mean reversion** est l'un des phénomènes les plus exploitables en trading quantitatif. Ce module couvre l'approche mathématique rigoureuse avec le processus d'Ornstein-Uhlenbeck et son application pratique sur les Metals (notre asset class cible).

**Objectifs:**
- Comprendre le processus d'Ornstein-Uhlenbeck (OU)
- Calculer la demi-vie de réversion
- Identifier les paires/assets mean-reverting
- Implémenter des stratégies de trading optimisées
- Backtester sur Metals (Gold, Silver, Copper, etc.)

---

## 2. Processus d'Ornstein-Uhlenbeck

### 2.1 Théorie

**Définition:** Le processus OU est un processus stochastique de mean-reversion, solution de l'équation différentielle stochastique:

```
dX_t = θ(μ - X_t)dt + σdW_t

où:
- X_t: Valeur du processus au temps t
- θ: Vitesse de réversion (mean reversion speed)
- μ: Moyenne long terme (mean)
- σ: Volatilité (volatility)
- W_t: Mouvement brownien (Wiener process)
```

**Interprétation:**
- **θ(μ - X_t):** Force de rappel vers la moyenne μ
  - Si X_t > μ: Force négative (pousse vers le bas)
  - Si X_t < μ: Force positive (pousse vers le haut)
  - Plus θ est grand, plus la réversion est rapide
- **σdW_t:** Terme stochastique (bruit/aléatoire)

### 2.2 Discrétisation (Euler-Maruyama)

Pour implémentation numérique:

```
X_{t+Δt} = X_t + θ(μ - X_t)Δt + σ√Δt · ε

où ε ~ N(0, 1) (bruit gaussien)
```

**Formule récursive:**
```python
def ornstein_uhlenbeck(x0, theta, mu, sigma, n_steps, dt=1):
    """Génère un processus OU"""
    X = np.zeros(n_steps)
    X[0] = x0
    
    for t in range(1, n_steps):
        dW = np.random.normal(0, np.sqrt(dt))
        X[t] = X[t-1] + theta * (mu - X[t-1]) * dt + sigma * dW
    
    return X
```

---

## 3. Estimation des Paramètres OU

### 3.1 Méthode MLE (Maximum Likelihood Estimation)

```python
import numpy as np
from scipy.optimize import minimize

def fit_ou_mle(x, dt=1):
    """
    Estime les paramètres OU par MLE.
    
    Parameters:
    - x: Série temporelle (returns ou spread)
    - dt: Pas de temps (1 pour données discrètes)
    
    Returns:
    - theta: Vitesse de réversion
    - mu: Moyenne long terme
    - sigma: Volatilité
    """
    
    n = len(x)
    
    def negative_log_likelihood(params):
        theta, mu, sigma = params
        
        if theta <= 0 or sigma <= 0:
            return 1e10  # Pénalise paramètres invalides
        
        # Log-likelihood pour processus OU discret
        ll = 0
        for t in range(1, n):
            expected = x[t-1] + theta * (mu - x[t-1]) * dt
            variance = sigma**2 * dt
            residual = x[t] - expected
            
            ll += -0.5 * (np.log(2 * np.pi * variance) + residual**2 / variance)
        
        return -ll  # Négatif car on minimise
    
    # Initial guess
    x0_init = [0.1, np.mean(x), np.std(x)]
    
    # Optimization
    result = minimize(
        negative_log_likelihood,
        x0_init,
        method='L-BFGS-B',
        bounds=[(0.001, None), (None, None), (0.001, None)]
    )
    
    theta, mu, sigma = result.x
    
    return theta, mu, sigma
```

### 3.2 Méthode par Régression Linéaire (Approximation)

**Approximation discrète:**
```
X_{t+1} - X_t = θ(μ - X_t) + ε_t
X_{t+1} = θμ + (1-θ)X_t + ε_t
X_{t+1} = α + βX_t + ε_t

où:
- α = θμ
- β = 1 - θ
- θ = 1 - β
- μ = α / θ = α / (1 - β)
```

```python
from statsmodels.api import OLS, add_constant

def fit_ou_regression(x):
    """
    Estime les paramètres OU par régression linéaire.
    Méthode plus rapide mais moins précise que MLE.
    """
    
    # X_{t+1} = α + βX_t + ε
    X = x[:-1]  # X_t
    y = x[1:]   # X_{t+1}
    
    X_const = add_constant(X)
    model = OLS(y, X_const).fit()
    
    alpha = model.params[0]
    beta = model.params[1]
    
    # Conversion paramètres OU
    theta = 1 - beta
    mu = alpha / theta if theta != 0 else np.mean(x)
    
    # Sigma (std des résidus)
    sigma = np.std(model.resid)
    
    return theta, mu, sigma
```

---

## 4. Demi-Vie de Réversion

### 4.1 Définition

**Demi-vie (half-life):** Temps nécessaire pour que le processus revienne à mi-chemin vers sa moyenne.

```
half_life = ln(2) / θ

où:
- θ: Vitesse de réversion
- ln(2) ≈ 0.693
```

**Interprétation:**
- **Half-life courte (1-5 jours):** Réversion rapide, trading fréquent
- **Half-life moyenne (5-20 jours):** Swing trading
- **Half-life longue (>20 jours):** Position trading

### 4.2 Calcul et Interprétation

```python
def calculate_half_life(theta, dt=1):
    """Calcule la demi-vie de réversion"""
    if theta <= 0:
        return np.inf  # Pas de mean reversion
    
    half_life = np.log(2) / theta
    return half_life * dt  # Convertir en unités de temps

# Exemple d'interprétation
theta = 0.15  # Vitesse de réversion quotidienne
half_life = calculate_half_life(theta, dt=1)
print(f"Demi-vie: {half_life:.1f} jours")

# Output: Demi-vie: 4.6 jours
```

**Guidelines de trading:**

| Half-Life | Stratégie | Fréquence | Holding Period |
|-----------|-----------|-----------|----------------|
| < 2 jours | HFT / Market making | Très haute | < 1 jour |
| 2-5 jours | Mean reversion court terme | Haute | 1-3 jours |
| 5-15 jours | Swing trading | Moyenne | 3-10 jours |
| 15-30 jours | Position trading | Basse | 10-25 jours |
| > 30 jours | Allocation tactique | Très basse | > 25 jours |

---

## 5. Application aux Metals

### 5.1 Pourquoi les Metals?

**Caractéristiques mean-reverting:**
- **Gold/Silver ratio:** Historiquement mean-reverting (range 40-80)
- **Term structure:** Contango/backwardation mean-revert
- **Gold vs Real Rates:** Correlation negative stable
- **Inter-metal spreads:** Gold/Silver, Gold/Platinum, Copper/Aluminum

**Données recommandées:**
- **COMEX:** Gold (GC), Silver (SI), Copper (HG)
- **LBMA:** Gold, Silver spot
- **ETF:** GLD, SLV, CPER

### 5.2 Gold/Silver Ratio

```python
def analyze_gold_silver_ratio(gold_prices, silver_prices):
    """Analyse le ratio Gold/Silver pour mean reversion"""
    
    # Ratio
    ratio = gold_prices / silver_prices
    
    # Test de stationnarité (ADF)
    from statsmodels.tsa.stattools import adfuller
    
    adf_result = adfuller(ratio.dropna())
    print(f"ADF p-value: {adf_result[1]:.4f}")
    
    if adf_result[1] < 0.05:
        print("✅ Ratio est stationnaire (mean-reverting)")
    else:
        print("⚠️  Ratio non-stationnaire")
    
    # Fit OU
    ratio_returns = ratio.pct_change().dropna()
    theta, mu, sigma = fit_ou_mle(ratio_returns.values)
    half_life = calculate_half_life(theta, dt=1)
    
    print(f"\nParamètres OU:")
    print(f"  θ (theta): {theta:.4f}")
    print(f"  μ (mu): {mu:.4f}")
    print(f"  σ (sigma): {sigma:.4f}")
    print(f"  Half-life: {half_life:.1f} jours")
    
    # Z-score pour trading
    ratio_mean = ratio.rolling(252).mean()
    ratio_std = ratio.rolling(252).std()
    z_score = (ratio - ratio_mean) / ratio_std
    
    return {
        'ratio': ratio,
        'theta': theta,
        'mu': mu,
        'sigma': sigma,
        'half_life': half_life,
        'z_score': z_score
    }
```

### 5.3 Signals de Trading

```python
def generate_mean_reversion_signals(z_score, entry_threshold=2.0, exit_threshold=0.5):
    """
    Génère des signals de trading mean-reversion.
    
    Parameters:
    - z_score: Z-score actuel du spread/ratio
    - entry_threshold: Z-score pour entrer (ex: 2.0 = 2σ)
    - exit_threshold: Z-score pour sortir (ex: 0.5)
    
    Returns:
    - position: 1 = long, -1 = short, 0 = flat
    """
    
    position = 0
    
    if z_score > entry_threshold:
        # Ratio trop haut: short ratio (long silver, short gold)
        position = -1
    elif z_score < -entry_threshold:
        # Ratio trop bas: long ratio (long gold, short silver)
        position = 1
    elif abs(z_score) < exit_threshold:
        # Retour vers la moyenne: sortir
        position = 0
    else:
        # Maintenir position existante
        position = None  # Hold
    
    return position

# Exemple d'usage
z = 2.3  # Ratio est 2.3σ au-dessus de la moyenne
signal = generate_mean_reversion_signals(z, entry_threshold=2.0)
print(f"Signal: {signal}")  # -1 (short ratio)
```

---

## 6. Entry/Exit Thresholds Optimisés

### 6.1 Optimisation par Sharpe Ratio

```python
from scipy.optimize import minimize_scalar

def optimize_thresholds(z_scores, returns, thresholds_range=(1.0, 3.0)):
    """
    Optimise les thresholds d'entry/exit pour maximiser le Sharpe ratio.
    """
    
    def sharpe_ratio(threshold):
        entry_thresh = threshold
        exit_thresh = threshold * 0.25  # Exit à 25% du chemin
        
        positions = np.zeros(len(z_scores))
        
        in_position = 0
        for i, z in enumerate(z_scores):
            if in_position == 0:
                if z > entry_thresh:
                    positions[i:] = -1
                    in_position = -1
                elif z < -entry_thresh:
                    positions[i:] = 1
                    in_position = 1
            else:
                if abs(z) < exit_thresh:
                    positions[i:] = 0
                    in_position = 0
        
        # Strategy returns
        strategy_returns = positions[:-1] * returns[1:]
        
        # Sharpe
        if np.std(strategy_returns) == 0:
            return 0
        
        sharpe = np.mean(strategy_returns) / np.std(strategy_returns) * np.sqrt(252)
        return -sharpe  # Négatif car on minimise
    
    # Optimization
    result = minimize_scalar(
        sharpe_ratio,
        bounds=thresholds_range,
        method='bounded'
    )
    
    optimal_threshold = result.x
    optimal_sharpe = -result.fun
    
    return optimal_threshold, optimal_sharpe
```

### 6.2 Position Sizing Optimal (Kelly Criterion)

```python
def kelly_criterion(wins, losses, win_rate):
    """
    Calcule la fraction optimale de capital à allouer (Kelly).
    
    Parameters:
    - wins: Gain moyen sur les trades gagnants
    - losses: Perte moyenne sur les trades perdants (valeur absolue)
    - win_rate: Fraction de trades gagnants
    
    Returns:
    - kelly_fraction: Fraction optimale du capital
    """
    
    if losses == 0:
        return 1.0
    
    b = wins / losses  # Odds
    p = win_rate
    q = 1 - p
    
    kelly = (b * p - q) / b
    
    # Fractional Kelly (plus conservateur)
    return max(0, kelly * 0.5)  # Half-Kelly

# Exemple
wins = 0.02  # 2% gain moyen
losses = 0.015  # 1.5% perte moyenne
win_rate = 0.55  # 55% de trades gagnants

kelly = kelly_criterion(wins, losses, win_rate)
print(f"Kelly fraction: {kelly:.1%}")  # Ex: 23%
```

---

## 7. Backtest Mean Reversion sur Metals

### 7.1 Framework de Backtest

```python
def backtest_mean_reversion(prices_gold, prices_silver, entry_thresh=2.0, exit_thresh=0.5):
    """
    Backtest complet d'une stratégie mean-reversion Gold/Silver.
    """
    
    # Ratio et z-score
    ratio = prices_gold / prices_silver
    rolling_mean = ratio.rolling(252).mean()
    rolling_std = ratio.rolling(252).std()
    z_score = (ratio - rolling_mean) / rolling_std
    
    # Positions
    positions = np.zeros(len(prices_gold))
    in_position = 0
    
    for i in range(1, len(z_score)):
        z = z_score.iloc[i]
        
        if in_position == 0:
            if z > entry_thresh:
                positions[i:] = -1  # Short ratio
                in_position = -1
            elif z < -entry_thresh:
                positions[i:] = 1  # Long ratio
                in_position = 1
        else:
            if abs(z) < exit_thresh:
                positions[i:] = 0
                in_position = 0
    
    # Returns
    returns_gold = prices_gold.pct_change()
    returns_silver = prices_silver.pct_change()
    
    # Return du spread (long gold, short silver quand position=1)
    spread_returns = returns_gold - returns_silver
    strategy_returns = positions[:-1] * spread_returns[1:]
    
    # Métriques
    cumulative = (1 + pd.Series(strategy_returns)).cumprod()
    total_return = cumulative.iloc[-1] - 1
    sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252) if strategy_returns.std() > 0 else 0
    max_dd = (cumulative / cumulative.cummax() - 1).min()
    
    # Trade statistics
    trades = np.diff(positions != 0)
    n_trades = np.sum(trades != 0) // 2  # Entry + exit = 1 trade
    
    winning_trades = strategy_returns[strategy_returns > 0]
    losing_trades = strategy_returns[strategy_returns < 0]
    
    win_rate = len(winning_trades) / len(strategy_returns) if len(strategy_returns) > 0 else 0
    avg_win = winning_trades.mean() if len(winning_trades) > 0 else 0
    avg_loss = abs(losing_trades.mean()) if len(losing_trades) > 0 else 0
    
    return {
        'total_return': total_return,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'n_trades': n_trades,
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'cumulative': cumulative,
        'positions': positions,
        'z_score': z_score
    }
```

### 7.2 Résultats Attendus (Gold/Silver)

| Métrique | Valeur Typique | Interprétation |
|----------|----------------|----------------|
| Total Return | 15-40% / an | Dépend de la volatilité |
| Sharpe Ratio | 0.8-1.5 | Bon risk-adjusted |
| Max Drawdown | -10 à -20% | Gérable avec position sizing |
| Win Rate | 45-55% | Proche de 50% (mean-reversion) |
| Avg Win/Avg Loss | 1.2-1.5 | Gains > Pertes |
| N Trades / an | 10-25 | Fréquence modérée |
| Half-life | 5-15 jours | Swing trading |

---

## 8. Code Sample

Voir `learning/code/mean_reversion.py` pour l'implémentation complète.

**Fonctionnalités:**
- Simulation processus OU
- Estimation paramètres (MLE et régression)
- Calcul half-life
- Backtest Gold/Silver ratio
- Optimisation thresholds
- Visualisations complètes

---

## 9. Best Practices

### ✅ DO

1. **Tester la stationnarité** (ADF test) avant de trader
2. **Utiliser rolling window** pour paramètres (ils changent!)
3. **Transaction costs:** Inclure slippage + commissions
4. **Position sizing:** Kelly fractionnel (half-Kelly)
5. **Stop-loss:** Basé sur half-life (sortir si pas de réversion après 2-3x half-life)

### ❌ DON'T

1. **Trader sans ADF test:** Risque de trend caché
2. **Paramètres statiques:** Ré-estimer régulièrement (monthly)
3. **Over-leverage:** Mean reversion peut avoir drawdowns prolongés
4. **Ignorer le regime:** Mean reversion échoue en trend fort
5. **Entry trop tôt:** Attendre 2σ+ pour entry

---

## 10. Prochaines Étapes

- [x] Mean Reversion Avancée documenté
- [ ] Semaine 14: Momentum & Breakouts
- [ ] Semaine 15: HMM Deep Dive (mise à jour)
- [ ] Semaine 16: Multi-Factor Models

---

**Références:**
- Ornstein, L.S., Uhlenbeck, G.E. (1930). "On the Theory of the Brownian Motion"
- Gatev, E., Goetzmann, W.N., Rouwenhorst, K.G. (2006). "Pairs Trading"
- Avellaneda, M., Lee, J.H. (2010). "Statistical Arbitrage in the US Equities Market"
- López de Prado, M. (2018). "Advances in Financial Machine Learning"
