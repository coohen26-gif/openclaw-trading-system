# Semaine 18 - Risk Parity & Kelly Criterion

**Date:** 24 Mai 2026  
**Niveau:** Master 3 - Finance Quantitative  
**Temps estimé:** 4-6h

---

## 🎯 Objectifs du Module

1. Comprendre les limites de l'allocation traditionnelle (60/40, equipondéré)
2. Maîtriser le Risk Parity: allouer le risque, pas le capital
3. Apprendre le Kelly Criterion pour l'optimisation de position sizing
4. Implémenter des algorithmes de Risk Budgeting
5. Comprendre quand et comment appliquer ces méthodes au trading crypto

---

## 📚 Théorie Fondamentale

### 1. Le Problème de l'Allocation Traditionnelle

**Allocation 60/40 (stocks/bonds):**
- 60% en actions, 40% en obligations
- **Problème:** Les actions contribuent à ~90% du risque total!
- Le "40%" bonds est une illusion de diversification

**Pourquoi?**
```
Contribution au risque = poids × volatilité × corrélation

Actions: 0.60 × 15% × 0.9 ≈ 8.1% risk contribution
Bonds:   0.40 × 5%  × 0.9 ≈ 1.8% risk contribution

Total risk: ~9.9%
→ Actions: 82% du risque
→ Bonds: 18% du risque
```

**Conclusion:** Le portfolio 60/40 est en réalité un portfolio ~80/20 en termes de risque.

### 2. Risk Parity - La Révolution

**Idée centrale (Bridgewater, Ray Dalio ~1996):**
> "Chaque actif devrait contribuer également au risque total du portfolio."

**Formellement:**
```
wᵢ × σᵢ = wⱼ × σⱼ  pour tous i, j

Donc: wᵢ ∝ 1/σᵢ
```

**Exemple simple (2 assets):**
- Actions: σ = 15%
- Bonds: σ = 5%
- Ratio de volatilité: 3:1

**Allocation Risk Parity:**
- Actions: 25% (contribue 25% × 15% = 3.75% risk)
- Bonds: 75% (contribue 75% × 5% = 3.75% risk)
- ✅ Risk contribution égale!

**Avec corrélation:**
Quand les assets sont corrélés, on doit utiliser la **risk contribution marginale**:

```
RCᵢ = wᵢ × (Σw)ᵢ / σ_p
```

Où:
- `RCᵢ` = Risk Contribution de l'actif i
- `(Σw)ᵢ` = i-ème élément de Σw (covariance avec le portfolio)
- `σ_p` = volatilité du portfolio

**Condition Risk Parity:**
```
RC₁ = RC₂ = ... = RCₙ = σ_p / n
```

### 3. Kelly Criterion - L'Optimisation de Croissance

**Origine:** John Kelly, Bell Labs, 1956 (théorie de l'information)

**Problème:** Comment maximiser la croissance à long terme d'un capital quand on a un edge?

**Formule simple (bet binaire):**
```
f* = (p × b - q) / b

Où:
- f* = fraction du capital à parier
- p = probabilité de gagner
- q = 1 - p = probabilité de perdre
- b = odds (gain net par unité pariée)
```

**Exemple:**
- Edge: 60% de chance de gagner (p=0.6)
- Odds: 1:1 (b=1)
- Kelly: `f* = (0.6 × 1 - 0.4) / 1 = 0.20`
- → Parier 20% du capital

**Formule continue (trading):**
```
f* = μ / σ²

Où:
- μ = return attendu (drift)
- σ² = variance des returns
```

**Interprétation:** 
- Plus l'edge (μ) est grand → parier plus
- Plus l'incertitude (σ²) est grande → parier moins

### 4. Half-Kelly et Fractional Kelly

**Problème du Full Kelly:**
- Volatilité extrême (drawdowns de 50-80% possibles)
- Estimation error: si μ est surestimé, on overbet → ruine

**Solution:** Fractional Kelly
```
f_fractional = α × f*_Kelly  où α ∈ [0.25, 0.75]
```

**Half-Kelly (α=0.5):**
- Réduit la volatilité de 50%
- Réduit le retour de seulement ~25%
- **Much better risk-adjusted returns!**

**Pourquoi ça marche:**
```
Croissance = μ - σ²/2  (approximation)

Avec Half-Kelly:
- μ' = 0.5 × μ
- σ'² = 0.25 × σ²  (variance scale avec le carré!)

Croissance' = 0.5μ - 0.25σ²/2 = 0.5μ - 0.125σ²

Perte de croissance: ~25%
Réduction de risque: ~75%
→ Trade-off excellent!
```

---

## 💻 Implémentation Python

### 1. Risk Parity avec cvxpy

```python
import cvxpy as cp
import numpy as np

def risk_parity_weights(Sigma, target_risk_contrib=None):
    """
    Calcule les poids Risk Parity qui égalisent la contribution au risque.
    
    Parameters:
    - Sigma: matrice de covariance
    - target_risk_contrib: vector cible (par défaut: égale pour tous)
    
    Returns:
    - w: poids optimaux
    """
    n_assets = Sigma.shape[0]
    
    if target_risk_contrib is None:
        target_risk_contrib = np.ones(n_assets) / n_assets
    
    # Variable: poids
    w = cp.Variable(n_assets)
    
    # Portfolio variance et volatilité
    portfolio_var = cp.quad_form(w, Sigma)
    portfolio_vol = cp.sqrt(portfolio_var)
    
    # Risk contribution de chaque actif
    # RC_i = w_i * (Sigma @ w)_i / sigma_p
    marginal_risk = Sigma @ w
    risk_contrib = cp.multiply(w, marginal_risk) / portfolio_vol
    
    # Objectif: minimiser l'écart aux cibles
    objective = cp.Minimize(cp.sum_squares(risk_contrib - target_risk_contrib * portfolio_vol))
    
    # Contraintes
    constraints = [
        cp.sum(w) == 1,
        w >= 0
    ]
    
    prob = cp.Problem(objective, constraints)
    prob.solve()
    
    return w.value

# Exemple d'utilisation
Sigma = returns.cov().values * 252  # Annualisé
rp_weights = risk_parity_weights(Sigma)

print("Risk Parity weights:")
for ticker, weight in zip(tickers, rp_weights):
    if weight > 0.01:
        print(f"  {ticker}: {weight:.1%}")
```

### 2. Vérification des Risk Contributions

```python
def compute_risk_contributions(w, Sigma):
    """
    Calcule la contribution au risque de chaque actif.
    """
    portfolio_var = w @ Sigma @ w
    portfolio_vol = np.sqrt(portfolio_var)
    
    marginal_risk = Sigma @ w
    risk_contrib = w * marginal_risk / portfolio_vol
    
    # En pourcentage du risque total
    risk_contrib_pct = risk_contrib / portfolio_vol
    
    return risk_contrib, risk_contrib_pct, portfolio_vol

# Comparer Risk Parity vs Equal Weight
equal_weights = np.ones(len(tickers)) / len(tickers)

rc_rp, rc_pct_rp, vol_rp = compute_risk_contributions(rp_weights, Sigma)
rc_eq, rc_pct_eq, vol_eq = compute_risk_contributions(equal_weights, Sigma)

print("\nRisk Contributions (% du risque total):")
print(f"{'Asset':<10} {'Risk Parity':>12} {'Equal Weight':>12}")
print("-" * 36)
for i, ticker in enumerate(tickers):
    print(f"{ticker:<10} {rc_pct_rp[i]:>11.1%} {rc_pct_eq[i]:>11.1%}")
print("-" * 36)
print(f"{'Total Vol':<10} {vol_rp:>11.1%} {vol_eq:>11.1%}")
```

### 3. Kelly Criterion Implementation

```python
def kelly_fraction(mu, sigma, risk_free_rate=0.0):
    """
    Calcule la fraction de Kelly optimale.
    
    Parameters:
    - mu: return attendu annualisé
    - sigma: volatilité annualisée
    - risk_free_rate: taux sans risque
    
    Returns:
    - f_kelly: fraction optimale (peut être >1, nécessite leverage)
    """
    excess_return = mu - risk_free_rate
    variance = sigma ** 2
    
    f_kelly = excess_return / variance
    
    return f_kelly

def kelly_portfolio(mu, Sigma, risk_free_rate=0.0, max_leverage=1.0):
    """
    Optimisation de portfolio avec critère de Kelly.
    
    Maximise: E[log(1 + r_p)] ≈ μ_p - σ_p²/2
    """
    n_assets = len(mu)
    w = cp.Variable(n_assets)
    
    portfolio_return = mu @ w
    portfolio_var = cp.quad_form(w, Sigma)
    
    # Kelly objective: maximize μ - σ²/2
    kelly_objective = portfolio_return - portfolio_var / 2
    
    constraints = [
        cp.sum(w) == 1,
    ]
    
    if max_leverage < 1.0:
        constraints.append(cp.sum(cp.abs(w)) <= max_leverage)
    else:
        constraints.append(w >= 0)  # Long-only si pas de leverage
    
    prob = cp.Problem(cp.Maximize(kelly_objective), constraints)
    prob.solve()
    
    return w.value, kelly_objective.value

# Exemple
mu_annual = returns.mean().values * 252
Sigma_annual = returns.cov().values * 252

kelly_weights, kelly_growth = kelly_portfolio(mu_annual, Sigma_annual)

print("\nKelly Optimal weights:")
for ticker, weight in zip(tickers, kelly_weights):
    if abs(weight) > 0.01:
        print(f"  {ticker}: {weight:+.1%}")
print(f"\nCroissance optimale: {kelly_growth:.1%} annualisé")
```

### 4. Half-Kelly avec Constraints Pratiques

```python
def fractional_kelly(mu, Sigma, fraction=0.5, max_position=0.30, 
                     min_position=0.02, risk_free_rate=0.0):
    """
    Kelly fractionnaire avec constraints pratiques.
    """
    n_assets = len(mu)
    w = cp.Variable(n_assets)
    
    portfolio_return = mu @ w
    portfolio_var = cp.quad_form(w, Sigma)
    
    # Fractional Kelly objective
    objective = portfolio_return - fraction * portfolio_var / 2
    
    constraints = [
        cp.sum(w) == 1,
        w >= 0,
        w <= max_position,  # Risk management
    ]
    
    # Optionnel: minimum position si inclus (évite les poids trop petits)
    # Implémenté via variable binaire (MIP) - omis pour simplicité
    
    prob = cp.Problem(cp.Maximize(objective), constraints)
    prob.solve()
    
    return w.value

# Half-Kelly avec max 30% par actif
half_kelly_weights = fractional_kelly(mu_annual, Sigma_annual, 
                                       fraction=0.5, max_position=0.30)

print("\nHalf-Kelly (max 30% per asset):")
for ticker, weight in zip(tickers, half_kelly_weights):
    if weight > 0.01:
        print(f"  {ticker}: {weight:.1%}")
```

### 5. Risk Parity Dynamique (Rolling Window)

```python
def rolling_risk_parity(returns, window=60):
    """
    Calcule les weights Risk Parity sur une fenêtre rolling.
    Simule un rebalancing mensuel/trimestriel.
    """
    n = len(returns)
    weights_history = []
    dates = []
    
    for i in range(window, n):
        # Données rolling
        returns_window = returns.iloc[i-window:i]
        Sigma_window = returns_window.cov().values * 252
        
        # Risk Parity
        w = risk_parity_weights(Sigma_window)
        weights_history.append(w)
        dates.append(returns.index[i])
    
    return pd.DataFrame(weights_history, index=dates, columns=returns.columns)

# Exemple
rp_rolling = rolling_risk_parity(returns, window=60)

# Plot evolution des weights
plt.figure(figsize=(14, 8))
for ticker in tickers[:5]:  # Top 5 pour lisibilité
    plt.plot(rp_rolling.index, rp_rolling[ticker], label=ticker, linewidth=2)

plt.xlabel('Date')
plt.ylabel('Weight')
plt.title('Risk Parity Weights - Evolution (Rolling 60j)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('learning/figures/semaine-18-rp-rolling.png', dpi=150)
plt.show()
```

---

## 📊 Visualisations

### 1. Comparaison Risk Contributions

```python
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Risk Parity
axes[0].bar(range(len(rc_pct_rp)), rc_pct_rp)
axes[0].set_xticks(range(len(tickers)))
axes[0].set_xticklabels(tickers, rotation=45, ha='right')
axes[0].axhline(0.1, color='red', linestyle='--', alpha=0.5, 
                label='Cible (10% chacun)')
axes[0].set_title('Risk Parity - Risk Contributions')
axes[0].set_ylabel('% du Risque Total')
axes[0].legend()

# Equal Weight
axes[1].bar(range(len(rc_pct_eq)), rc_pct_eq)
axes[1].set_xticks(range(len(tickers)))
axes[1].set_xticklabels(tickers, rotation=45, ha='right')
axes[1].axhline(0.1, color='red', linestyle='--', alpha=0.5)
axes[1].set_title('Equal Weight - Risk Contributions')

# Weights comparison
width = 0.35
x = np.arange(len(tickers))
axes[2].bar(x - width/2, rp_weights, width, label='Risk Parity')
axes[2].bar(x + width/2, equal_weights, width, label='Equal Weight')
axes[2].set_xticks(x)
axes[2].set_xticklabels(tickers, rotation=45, ha='right')
axes[2].set_title('Weights Comparison')
axes[2].legend()

plt.tight_layout()
plt.savefig('learning/figures/semaine-18-risk-contributions.png', dpi=150)
plt.show()
```

### 2. Growth Comparison: Kelly vs Half-Kelly vs Equal Weight

```python
def simulate_growth(returns, weights, initial_capital=10000):
    """
    Simule la croissance du capital avec des poids donnés.
    """
    portfolio_returns = (returns * weights).sum(axis=1)
    cumulative = initial_capital * (1 + portfolio_returns).cumprod()
    return cumulative

# Simuler
equal_growth = simulate_growth(returns, equal_weights)
rp_growth = simulate_growth(returns, rp_weights)

# Kelly (sans constraints, pour illustration)
kelly_growth_sim = simulate_growth(returns, kelly_weights)

# Half-Kelly
half_kelly_growth = simulate_growth(returns, half_kelly_weights)

plt.figure(figsize=(14, 8))
plt.plot(equal_growth.index, equal_growth.values, label='Equal Weight', 
         linewidth=2, alpha=0.7)
plt.plot(rp_growth.index, rp_growth.values, label='Risk Parity', 
         linewidth=2, alpha=0.7)
plt.plot(half_kelly_growth.index, half_kelly_growth.values, 
         label='Half-Kelly (constrained)', linewidth=2, alpha=0.7)
plt.plot(kelly_growth_sim.index, kelly_growth_sim.values, 
         label='Full Kelly (theoretical)', linewidth=2, linestyle='--', alpha=0.5)

plt.xlabel('Date')
plt.ylabel('Capital ($)')
plt.title('Comparaison Stratégies d\'Allocation - Croissance du Capital')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('learning/figures/semaine-18-growth-comparison.png', dpi=150)
plt.show()

# Stats
print("\nPerformance Comparison:")
print(f"{'Strategy':<20} {'Final Capital':>15} {'CAGR':>10} {'Max DD':>10}")
print("-" * 50)

def calc_stats(cumulative, returns):
    final = cumulative.iloc[-1]
    initial = cumulative.iloc[0]
    years = len(cumulative) / 252
    cagr = (final / initial) ** (1/years) - 1
    
    # Max drawdown
    rolling_max = cumulative.expanding().max()
    drawdown = (cumulative - rolling_max) / rolling_max
    max_dd = drawdown.min()
    
    return final, cagr, max_dd

for name, weights in [('Equal Weight', equal_weights), 
                       ('Risk Parity', rp_weights),
                       ('Half-Kelly', half_kelly_weights)]:
    cum = simulate_growth(returns, weights)
    final, cagr, max_dd = calc_stats(cum, returns)
    print(f"{name:<20} ${final:>12,.0f} {cagr:>9.1%} {max_dd:>9.1%}")
```

### 3. Efficient Frontier avec Risk Parity

```python
# Calculer return et risque de Risk Parity
rp_return = mu.values @ rp_weights
rp_risk = np.sqrt(rp_weights @ Sigma.values @ rp_weights)

# Replot frontière efficiente (de semaine 17)
plt.figure(figsize=(12, 8))
plt.plot(frontier['risk'], frontier['return'], 'b-', linewidth=2, 
         label='Frontière Efficiente (Markowitz)')

# Assets individuels
asset_risks = np.sqrt(np.diag(Sigma.values))
plt.scatter(asset_risks, mu.values, s=50, alpha=0.5, c='gray')

# Risk Parity
plt.scatter(rp_risk, rp_return, s=200, c='green', marker='*', 
            label=f'Risk Parity (σ={rp_risk:.1%}, μ={rp_return:.1%})')

# Equal Weight
eq_return = mu.values @ equal_weights
eq_risk = np.sqrt(equal_weights @ Sigma.values @ equal_weights)
plt.scatter(eq_risk, eq_return, s=200, c='orange', marker='s', 
            label=f'Equal Weight (σ={eq_risk:.1%}, μ={eq_return:.1%})')

plt.xlabel('Risque (Volatilité Annualisée)')
plt.ylabel('Return Annualisé')
plt.title('Risk Parity vs Markowitz - Position sur la Frontière')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('learning/figures/semaine-18-rp-on-frontier.png', dpi=150)
plt.show()
```

---

## 🔍 Analyse des Résultats

### Exemple Typique (Crypto Portfolio 2024-2026)

**Risk Parity Weights:**
```
BTC: 35%   (plus basse vol → plus haut poids)
ETH: 25%
SOL: 15%   (haute vol → basse poids)
LINK: 10%
 Autres: 15%

→ Volatilité totale: ~42%
→ Risk contribution: ~10% chacun ✅
```

**Equal Weight Weights:**
```
Chaque crypto: 10%

→ Volatilité totale: ~58%
→ Risk contribution: BTC 7%, SOL 18% (déséquilibré!)
```

**Half-Kelly Weights:**
```
BTC: 25%
SOL: 30%   (haut μ → haut poids, mais capped)
ETH: 25%
LINK: 20%

→ Croissance optimale: ~85% annualisé (théorique)
→ Volatilité: ~52%
```

### Observations Clés

1. **Risk Parity réduit la volatilité:**
   - Equal Weight: 58% vol
   - Risk Parity: 42% vol
   - → **27% de réduction de risque!**

2. **Risk Parity surpondère les assets "stables":**
   - BTC devient le plus gros poids (le "bond" crypto)
   - Les small-caps volatiles sont sous-pondérées

3. **Kelly est agressif:**
   - Full Kelly peut donner des weights >100% (nécessite leverage)
   - Half-Kelly est beaucoup plus raisonnable

4. **Sharpe Ratio:**
   - Equal Weight: ~1.2
   - Risk Parity: ~1.5
   - Half-Kelly: ~1.6
   - → **Meilleur risk-adjusted return**

---

## ⚠️ Limites et Mises en Garde

### 1. Risk Parity

**Problèmes:**
1. **Estimation de Σ:** Même problème que Markowitz (non-stationnarité)
2. **Pas de view sur les returns:** Risk Parity ignore complètement μ
3. **Leverage requis:** Pour atteindre des returns cibles, souvent besoin de leverage
4. **Correlations extrêmes:** En crise, toutes les corrélations → 1, la diversification disparaît

**En crypto:**
- Les "low vol" assets crypto sont toujours très volatils
- BTC à 35% peut sembler conservateur, mais reste très risqué

### 2. Kelly Criterion

**Problèmes:**
1. **Estimation error catastrophique:**
   - Si μ est surestimé de 2x → f* est 2x trop grand → overbetting → ruine
   - La formule est TRÈS sensible à l'input μ

2. **Non-stationnarité:**
   - μ et σ changent dans le temps
   - Le Kelly "optimal" d'hier n'est pas optimal aujourd'hui

3. **Drawdowns extrêmes:**
   - Full Kelly: 80% drawdowns sont POSSIBLES (et même "normaux" mathématiquement)
   - Psychologiquement intenable pour 99% des investisseurs

4. **Continuous vs Discrete:**
   - La formule continue suppose des returns normaux et continus
   - En réalité: gaps, fat tails, jumps → Kelly overbet

**Recommandation pratique:**
> **Toujours utiliser Fractional Kelly (0.25 à 0.5) avec des constraints stricts.**

---

## 🧪 Extensions Avancées

### 1. Risk Parity avec Views (Black-Litterman + Risk Parity)

**Idée:** Combiner Risk Parity avec des views directionnelles.

```python
def risk_parity_with_views(Sigma, mu_views, view_confidence=0.5):
    """
    Risk Parity tilté par des views directionnelles.
    
    mu_views: vector des returns attendus (views)
    view_confidence: 0 = pure RP, 1 = pure mean-variance
    """
    n = len(mu_views)
    
    # Risk Parity weights
    w_rp = risk_parity_weights(Sigma)
    
    # Mean-variance weights (avec views)
    w_mv = max_sharpe_portfolio(mu_views, Sigma)[0]
    
    # Combinaison
    w = (1 - view_confidence) * w_rp + view_confidence * w_mv
    
    # Renormaliser
    w = w / w.sum()
    
    return w
```

### 2. Hierarchical Risk Parity (HRP) - Lopez de Prado

**Algorithme complet:**

```python
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform

def hierarchical_risk_parity(returns):
    """
    Implémentation complète de HRP.
    """
    # 1. Matrice de corrélation et distance
    corr = returns.corr()
    dist = np.sqrt(0.5 * (1 - corr))
    
    # 2. Clustering hiérarchique
    link = linkage(squareform(dist), method='single')
    
    # 3. Allocation récursive
    def recursive_bisection(cov, sort_ix):
        n = len(sort_ix)
        if n == 1:
            return np.array([1.0])
        
        # Split en 2 clusters
        cluster_size = n // 2
        left = sort_ix[:cluster_size]
        right = sort_ix[cluster_size:]
        
        # Variances des clusters
        var_left = np.sum(cov[np.ix_(left, left)])
        var_right = np.sum(cov[np.ix_(right, right)])
        
        # Allocation inverse variance
        alpha = 1 - var_left / (var_left + var_right)
        
        # Récursion
        w_left = recursive_bisection(cov, left) * alpha
        w_right = recursive_bisection(cov, right) * (1 - alpha)
        
        return np.concatenate([w_left, w_right])
    
    # Ordre de clustering
    sort_ix = fcluster(link, len(returns.columns), criterion='maxclust')
    sort_ix = np.argsort(sort_ix)
    
    # Allocation
    weights = recursive_bisection(cov.values, sort_ix)
    
    # Réordonner
    weights_final = np.zeros(len(returns.columns))
    weights_final[sort_ix] = weights
    
    return weights_final

hrp_weights = hierarchical_risk_parity(returns)
```

**Avantages de HRP:**
- Pas besoin d'inverser Σ (stable même si Σ est singulière)
- Utilise la structure hiérarchique naturelle des corrélations
- Meilleure diversification que Risk Parity classique

### 3. Dynamic Risk Parity (DCC-GARCH)

**Idée:** Utiliser une matrice de covariance dynamique (DCC-GARCH) pour mettre à jour les weights.

```python
# Pseudo-code (nécessite package arch ou rugarch en R)

from arch import arch_model

def dcc_garch_risk_parity(returns):
    """
    Risk Parity avec covariance dynamique DCC-GARCH.
    """
    # 1. Fit GARCH sur chaque asset
    volatilities = {}
    for col in returns.columns:
        am = arch_model(returns[col], vol='Garch', p=1, q=1)
        res = am.fit()
        volatilities[col] = res.conditional_volatility
    
    # 2. DCC pour correlations dynamiques
    # (implémentation complexe, nécessite package spécialisé)
    
    # 3. Risk Parity à chaque date
    # ...
    
    pass
```

---

## 📝 Résumé des Concepts Clés

| Concept | Formule | Insight |
|---------|---------|---------|
| **Risk Contribution** | `RCᵢ = wᵢ × (Σw)ᵢ / σ_p` | Chaque asset contribue au risque total |
| **Risk Parity** | `RC₁ = RC₂ = ... = RCₙ` | Égaliser les contributions, pas les weights |
| **Kelly (simple)** | `f* = p×b - q / b` | Maximise croissance logarithmique |
| **Kelly (continu)** | `f* = μ / σ²` | Edge / Variance |
| **Half-Kelly** | `f = 0.5 × f*_Kelly` | Réduit volatilité 50%, retour seulement 25% |
| **HRP** | Clustering + allocation récursive | Diversification hiérarchique, pas besoin d'inverser Σ |

---

## 🎯 Applications pour Saiyan

### 1. Position Sizing Dynamique

**Actuellement:** Position sizing fixe ou basé sur volatilité simple.

**Après Master 3:**
```python
# Kelly fractionnaire par trade
def saiyan_position_size(signal_strength, mu_estimate, sigma_estimate):
    kelly_full = mu_estimate / (sigma_estimate ** 2)
    kelly_half = 0.5 * kelly_full
    
    # Apply signal strength (confidence from HMM/ML)
    position_size = kelly_half * signal_strength
    
    # Constraints
    position_size = np.clip(position_size, 0.01, 0.30)  # 1-30%
    
    return position_size
```

### 2. Multi-Strategy Allocation

**Idée:** Traiter chaque stratégie comme un "asset" et appliquer Risk Parity.

```python
# Risk contributions par stratégie
strategies = ['mean_reversion', 'momentum', 'hmm_breakout', 'ml_classifier']

# Historical returns par stratégie
strategy_returns = pd.DataFrame({
    'mean_reversion': mr_returns,
    'momentum': mom_returns,
    ...
})

# Risk Parity allocation
Sigma_strat = strategy_returns.cov() * 252
strat_weights = risk_parity_weights(Sigma_strat.values)

# Chaque stratégie reçoit un budget de risque égal!
```

### 3. Regime-Dependent Allocation

**Combinaison avec HMM (Semaine 15):**

```python
def regime_aware_allocation(hmm_state, base_weights):
    """
    Ajuste les weights selon le régime HMM.
    """
    if hmm_state == 'bull':
        # Overweight high-beta, momentum
        return base_weights * np.array([1.2, 1.3, 0.8, 0.9, ...])
    elif hmm_state == 'bear':
        # Overweight low-vol, defensive
        return base_weights * np.array([0.8, 0.7, 1.2, 1.3, ...])
    else:  # range
        # Balanced
        return base_weights
```

---

## 📚 Références

1. **Qian, E. (2005).** "Risk Parity Portfolios." *Journal of Portfolio Management.*
2. **Kelly, J.L. (1956).** "A New Interpretation of Information Rate." *Bell System Technical Journal.*
3. **Thorp, E. (2006).** "The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market."
4. **Lopez de Prado, M. (2016).** "Hierarchical Risk Parity." *Journal of Investment Strategies.*
5. **Bridgewater Associates.** "All Weather Strategy" (Risk Parity appliqué).

---

## ✅ Checklist Validation

- [x] Théorie Risk Parity comprise
- [x] Risk contributions calculées et vérifiées
- [x] Kelly Criterion implémenté (full et fractional)
- [x] Visualisations générées (contributions, growth, frontier)
- [x] Limites identifiées (estimation error, non-stationnarité)
- [x] Extensions documentées (HRP, DCC-GARCH)
- [x] Applications Saiyan définies

---

*Prochain module: Semaine 19 - VaR & CVaR (Risk Management Avancé)*
