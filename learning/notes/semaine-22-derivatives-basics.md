# Semaine 22 - Derivatives Basics (Futures, Options, Greeks)

**Date:** 24 Mai 2026  
**Niveau:** Master 5 - Advanced Topics  
**Temps estimé:** 4-5h

---

## 🎯 Objectifs du Module

1. Comprendre les instruments dérivés: Futures, Options, Swaps
2. Maîtriser le pricing d'options: Black-Scholes, Binomial Tree
3. Calculer et interpréter les Greeks: Delta, Gamma, Vega, Theta, Rho
4. Implémenter des stratégies options: Covered Call, Protective Put, Straddle
5. Appliquer au trading crypto: Futures perpétuels, options BTC/ETH

---

## 📚 Théorie Fondamentale

### 1. Qu'est-ce qu'un Dérivé?

**Définition:**
> Un instrument financier dont la valeur **dérive** d'un actif sous-jacent (underlying).

**Types principaux:**

| Instrument | Description | Usage typique |
|------------|-------------|---------------|
| **Forward** | Contrat OTC d'achat/vente à prix fixé | Hedging personnalisé |
| **Futures** | Forward standardisé, échangé sur exchange | Speculation, hedging |
| **Options** | Droit (pas obligation) d'acheter/vendre à prix fixé | Hedging, leverage, income |
| **Swaps** | Échange de flux (ex: fixed vs floating) | Hedging taux, devises |

### 2. Futures vs Forwards

**Similarities:**
- Tous deux engagent à acheter/vendre à un prix futur
- Prix fixé aujourd'hui (forward price / futures price)

**Différences:**

| Caractéristique | Forward | Futures |
|-----------------|---------|---------|
| Lieu d'échange | OTC (gré à gré) | Exchange (CME, Binance) |
| Standardisation | Personnalisé | Standardisé |
| Mark-to-market | À l'échéance | Quotidien (margin calls) |
| Risque de contrepartie | Élevé | Faible (clearing house) |
| Liquidité | Faible | Élevée |

**Futures Crypto:**
- Binance, Bybit, FTX (avant faillite), Deribit
- **Perpetual Futures** (perps): Pas d'échéance, funding rate
- Funding rate: Mécanisme pour ancrer le futures au spot

### 3. Options: Calls et Puts

**Call Option:**
> Droit d'**acheter** l'underlying à un prix fixé (strike) avant/après une date (expiration).

**Put Option:**
> Droit de **vendre** l'underlying à un prix fixé (strike) avant/après une date (expiration).

**Terminologie:**

| Terme | Définition |
|-------|------------|
| **Strike (K)** | Prix d'exercice de l'option |
| **Expiration (T)** | Date de fin de l'option |
| **Premium** | Prix payé pour acheter l'option |
| **In-the-Money (ITM)** | Call: Spot > Strike \| Put: Spot < Strike |
| **At-the-Money (ATM)** | Spot ≈ Strike |
| **Out-of-the-Money (OTM)** | Call: Spot < Strike \| Put: Spot > Strike |
| **Intrinsic Value** | max(0, Spot - Strike) pour Call \| max(0, Strike - Spot) pour Put |
| **Time Value** | Premium - Intrinsic Value |

**Payoff à l'expiration:**

```
Long Call:  max(S_T - K, 0) - Premium
Short Call: Premium - max(S_T - K, 0)

Long Put:   max(K - S_T, 0) - Premium
Short Put:  Premium - max(K - S_T, 0)

Où S_T = prix du spot à l'expiration
```

### 4. Black-Scholes Model (1973)

**Hypothèses:**
- L'underlying suit un mouvement brownien géométrique (log-normal)
- Pas de dividendes (ou dividendes connus)
- Pas de transaction costs
- Taux sans risque constant
- Trading continu possible
- Pas d'arbitrage

**Formule Call Européen:**

```
C = S × N(d₁) - K × e^(-rT) × N(d₂)

Où:
d₁ = [ln(S/K) + (r + σ²/2)T] / (σ√T)
d₂ = d₁ - σ√T

S = Spot price
K = Strike price
r = Risk-free rate
T = Time to expiration (en années)
σ = Volatilité annualisée
N() = CDF de la normale standard
```

**Formule Put Européen (Put-Call Parity):**

```
P = K × e^(-rT) × N(-d₂) - S × N(-d₁)

Ou via Put-Call Parity:
C - P = S - K × e^(-rT)
→ P = C - S + K × e^(-rT)
```

**Limites de Black-Scholes:**
- Assume normalité des returns (FAUX pour crypto!)
- Volatilité constante (FAUX: vol clustering, vol smile)
- Ne capture pas les fat tails
- Options américaines (early exercise) nécessitent Binomial Tree

### 5. Les Greeks: Mesures de Risque

**Delta (Δ):**
> Sensibilité du premium aux variations du spot.

```
Δ_call = ∂C/∂S = N(d₁)
Δ_put = ∂P/∂S = N(d₁) - 1

Interprétation:
- Δ = 0.5 → Si spot +$1, option +$0.50
- Δ ≈ probabilité que l'option finisse ITM
```

**Gamma (Γ):**
> Sensibilité du Delta aux variations du spot (convexité).

```
Γ = ∂Δ/∂S = N'(d₁) / (S × σ × √T)

Interprétation:
- Γ élevé → Delta change vite → hedging difficile
- Γ maximum pour options ATM
- Γ → 0 quand option deep ITM ou OTM
```

**Vega (ν):**
> Sensibilité du premium aux variations de volatilité.

```
ν = ∂C/∂σ = S × N'(d₁) × √T

Interprétation:
- ν = 0.20 → Si vol +1%, option +$0.20
- Vega maximum pour options ATM
- Vega → 0 à l'approche de l'expiration
```

**Theta (Θ):**
> Sensibilité du premium au temps qui passe (time decay).

```
Θ = ∂C/∂t = -[S × N'(d₁) × σ] / (2√T) - r × K × e^(-rT) × N(d₂)

Interprétation:
- Θ = -0.05 → Chaque jour, option perd $0.05 (ceteris paribus)
- Theta est NÉGATIF pour long options (time decay)
- Theta est POSITIF pour short options (on encaisse le time decay)
```

**Rho (ρ):**
> Sensibilité du premium aux variations du taux d'intérêt.

```
ρ_call = ∂C/∂r = K × T × e^(-rT) × N(d₂)
ρ_put = ∂P/∂r = -K × T × e^(-rT) × N(-d₂)

Interprétation:
- Rho est généralement faible (sauf options long-dated)
- Moins important pour crypto (taux ~0 ou funding rate)
```

**Résumé des Greeks:**

| Greek | Symbole | Call | Put | Interprétation |
|-------|---------|------|-----|----------------|
| **Delta** | Δ | [0, 1] | [-1, 0] | Directionnel |
| **Gamma** | Γ | Toujours + | Toujours + | Convexité |
| **Vega** | ν | Toujours + | Toujours + | Sensibilité vol |
| **Theta** | Θ | Toujours - | Toujours - | Time decay |
| **Rho** | ρ | + | - | Sensibilité taux |

### 6. Stratégies Options de Base

#### Covered Call

**Setup:**
- Long underlying (ex: 1 BTC)
- Short Call OTM

**Payoff:**
- Si spot < strike à expiration: Garde underlying + premium
- Si spot > strike: Underlying appelé, garde premium + gain jusqu'au strike

**Usage:**
- Générer du revenu (yield enhancement)
- Bullish à neutre
- Risk: Opportunity cost si spot monte fort

#### Protective Put

**Setup:**
- Long underlying
- Long Put (ATM ou OTM)

**Payoff:**
- Si spot baisse: Put protège (floor de perte)
- Si spot monte: Participe à la hausse (moins le premium)

**Usage:**
- Assurance portfolio (hedging)
- Bearish ou担心 crash
- Coût: Premium du put

#### Straddle

**Setup:**
- Long Call ATM + Long Put ATM (même strike, même expiration)

**Payoff:**
- Profit si spot bouge BEAUCOUP (dans les 2 sens)
- Perte si spot reste range (time decay)

**Usage:**
- Parier sur volatilité (earnings, events)
- Direction-neutral, vol-long
- Break-even: Strike ± total premium

#### Strangle

**Setup:**
- Long Call OTM + Long Put OTM (même expiration)

**Payoff:**
- Similaire à Straddle, mais moins cher
- Besoin de mouvement PLUS GRAND pour profiter

**Usage:**
- Volatility play moins cher que Straddle
- Direction-neutral

#### Bull Call Spread

**Setup:**
- Long Call (strike bas) + Short Call (strike haut)

**Payoff:**
- Profit max: Strike_haut - Strike_bas - net_premium
- Perte max: Net premium payé

**Usage:**
- Bullish modéré
- Réduit le coût vs long call seul
- Cap le profit potentiel

#### Bear Put Spread

**Setup:**
- Long Put (strike haut) + Short Put (strike bas)

**Payoff:**
- Profit max: Strike_haut - Strike_bas - net_premium
- Perte max: Net premium payé

**Usage:**
- Bearish modéré
- Réduit le coût vs long put seul

---

## 💻 Implémentation Python

### 1. Black-Scholes Pricing

```python
import numpy as np
from scipy.stats import norm

def black_scholes_call(S, K, T, r, sigma):
    """
    Calculate Black-Scholes call option price.
    
    Parameters:
    - S: Spot price
    - K: Strike price
    - T: Time to expiration (years)
    - r: Risk-free rate (annual)
    - sigma: Volatility (annual)
    """
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    call_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    
    return call_price, d1, d2

def black_scholes_put(S, K, T, r, sigma):
    """Calculate Black-Scholes put option price using put-call parity."""
    call_price, d1, d2 = black_scholes_call(S, K, T, r, sigma)
    
    put_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    
    return put_price, d1, d2

# Exemple d'utilisation
S = 50000  # BTC spot
K = 52000  # Strike
T = 30/365  # 30 jours
r = 0.05  # 5% risk-free rate
sigma = 0.60  # 60% annual vol (crypto!)

call, d1, d2 = black_scholes_call(S, K, T, r, sigma)
put, _, _ = black_scholes_put(S, K, T, r, sigma)

print(f"Call Price: ${call:.2f}")
print(f"Put Price: ${put:.2f}")
```

### 2. Calcul des Greeks

```python
def calculate_greeks(S, K, T, r, sigma, option_type='call'):
    """
    Calculate all Greeks for an option.
    """
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    # Premium
    if option_type == 'call':
        premium = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        premium = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    
    # Delta
    if option_type == 'call':
        delta = norm.cdf(d1)
    else:
        delta = norm.cdf(d1) - 1
    
    # Gamma (same for call and put)
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    
    # Vega (same for call and put)
    vega = S * norm.pdf(d1) * np.sqrt(T) / 100  # Per 1% vol change
    
    # Theta (per day)
    if option_type == 'call':
        theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) 
                 - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
    else:
        theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) 
                 + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365
    
    # Rho (per 1% rate change)
    if option_type == 'call':
        rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
    else:
        rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
    
    return {
        'premium': premium,
        'delta': delta,
        'gamma': gamma,
        'vega': vega,
        'theta': theta,
        'rho': rho,
        'd1': d1,
        'd2': d2
    }

# Exemple
greeks = calculate_greeks(S, K, T, r, sigma, 'call')
print(f"\nCall Greeks:")
print(f"  Delta: {greeks['delta']:.4f}")
print(f"  Gamma: {greeks['gamma']:.6f}")
print(f"  Vega: {greeks['vega']:.4f} (per 1% vol)")
print(f"  Theta: {greeks['theta']:.4f} (per day)")
print(f"  Rho: {greeks['rho']:.4f} (per 1% rate)")
```

### 3. Binomial Tree (Options Américaines)

```python
def binomial_tree_option(S, K, T, r, sigma, N=100, option_type='call', american=False):
    """
    Price options using Binomial Tree (Cox-Ross-Rubinstein).
    Supports American options (early exercise).
    """
    dt = T / N
    u = np.exp(sigma * np.sqrt(dt))  # Up factor
    d = 1 / u  # Down factor
    p = (np.exp(r * dt) - d) / (u - d)  # Risk-neutral probability
    
    # Initialize asset prices at maturity
    asset_prices = np.zeros(N + 1)
    asset_prices[0] = S * (d ** N)
    
    for i in range(1, N + 1):
        asset_prices[i] = asset_prices[0] * (u ** (2 * i))
    
    # Initialize option values at maturity
    option_values = np.zeros(N + 1)
    for i in range(N + 1):
        if option_type == 'call':
            option_values[i] = max(0, asset_prices[i] - K)
        else:
            option_values[i] = max(0, K - asset_prices[i])
    
    # Backward induction
    for j in range(N - 1, -1, -1):
        for i in range(j + 1):
            option_values[i] = np.exp(-r * dt) * (p * option_values[i + 1] + (1 - p) * option_values[i])
            
            # Check early exercise for American options
            if american:
                asset_price = S * (u ** i) * (d ** (j - i))
                if option_type == 'call':
                    exercise_value = max(0, asset_price - K)
                else:
                    exercise_value = max(0, K - asset_price)
                option_values[i] = max(option_values[i], exercise_value)
    
    return option_values[0]

# Exemple: American vs European
euro_call = black_scholes_call(S, K, T, r, sigma)[0]
amer_call = binomial_tree_option(S, K, T, r, sigma, N=100, option_type='call', american=True)

print(f"\nEuropean Call: ${euro_call:.2f}")
print(f"American Call: ${amer_call:.2f}")
print(f"Early exercise premium: ${amer_call - euro_call:.2f}")
```

### 4. Implied Volatility

```python
from scipy.optimize import brentq

def implied_volatility(market_price, S, K, T, r, option_type='call'):
    """
    Calculate implied volatility from market option price.
    """
    def bs_price(sigma):
        if option_type == 'call':
            return black_scholes_call(S, K, T, r, sigma)[0]
        else:
            return black_scholes_put(S, K, T, r, sigma)[0]
    
    # Brent's method for root finding
    try:
        iv = brentq(lambda sigma: bs_price(sigma) - market_price, 0.001, 5.0)
        return iv
    except ValueError:
        return None  # No solution found

# Exemple
market_call_price = 2500  # Observed market price
iv = implied_volatility(market_call_price, S, K, T, r, 'call')
print(f"\nImplied Volatility: {iv*100:.1f}%")
```

### 5. Option Strategies Payoff

```python
def strategy_payoff(strategy_name, S_T, params):
    """
    Calculate payoff for various option strategies at expiration.
    
    Parameters:
    - strategy_name: 'covered_call', 'protective_put', 'straddle', etc.
    - S_T: Spot price at expiration
    - params: Dict with strategy parameters (strikes, premiums, etc.)
    """
    if strategy_name == 'covered_call':
        # Long underlying + Short Call
        underlying_pnl = S_T - params['S0']
        call_pnl = params['premium'] - max(0, S_T - params['K'])
        return underlying_pnl + call_pnl
    
    elif strategy_name == 'protective_put':
        # Long underlying + Long Put
        underlying_pnl = S_T - params['S0']
        put_pnl = max(0, params['K'] - S_T) - params['premium']
        return underlying_pnl + put_pnl
    
    elif strategy_name == 'straddle':
        # Long Call + Long Put (ATM)
        call_pnl = max(0, S_T - params['K']) - params['call_premium']
        put_pnl = max(0, params['K'] - S_T) - params['put_premium']
        return call_pnl + put_pnl
    
    elif strategy_name == 'strangle':
        # Long Call OTM + Long Put OTM
        call_pnl = max(0, S_T - params['K_call']) - params['call_premium']
        put_pnl = max(0, params['K_put'] - S_T) - params['put_premium']
        return call_pnl + put_pnl
    
    elif strategy_name == 'bull_call_spread':
        # Long Call (K1) + Short Call (K2)
        long_call = max(0, S_T - params['K1']) - params['premium1']
        short_call = params['premium2'] - max(0, S_T - params['K2'])
        return long_call + short_call
    
    elif strategy_name == 'bear_put_spread':
        # Long Put (K1) + Short Put (K2)
        long_put = max(0, params['K1'] - S_T) - params['premium1']
        short_put = params['premium2'] - max(0, params['K2'] - S_T)
        return long_put + short_put
    
    return 0

# Exemple: Straddle payoff analysis
params = {
    'S0': 50000,
    'K': 50000,
    'call_premium': 2000,
    'put_premium': 1800
}

S_T_range = np.linspace(40000, 60000, 100)
payoffs = [strategy_payoff('straddle', S_T, params) for S_T in S_T_range]

# Break-even points
breakeven_upper = params['K'] + params['call_premium'] + params['put_premium']
breakeven_lower = params['K'] - params['call_premium'] - params['put_premium']
print(f"\nStraddle Break-even points:")
print(f"  Upper: ${breakeven_upper:,.0f}")
print(f"  Lower: ${breakeven_lower:,.0f}")
```

---

## 📊 Application Crypto: Options BTC/ETH

### 1. Marché des Options Crypto

**Exchanges:**
- **Deribit:** Leader (80%+ du marché), options BTC/ETH
- **Binance:** Options européennes, settlement cash
- **Bybit, OKX, FTX (RIP):** Alternatives
- **Premia, Lyra:** Options DeFi (on-chain)

**Caractéristiques:**
- Settlement: Cash (USDC/USDT) ou physique (BTC/ETH)
- Expiration: Daily, weekly, monthly, quarterly
- Style: Européen (la plupart), Américain (certains)

### 2. Volatilité Implicite Crypto

**Observations:**
- IV crypto BEAUCOUP plus élevée que traditionnelle
- BTC IV: 50-80% typique (vs 15-25% pour S&P 500)
- ETH IV: 60-100% typique
- **Volatility Smile/Skew:** OTM puts ont IV plus élevée (crash fear)

**Term Structure:**
- Short-dated IV > Long-dated IV (typiquement)
- Mean reversion de la volatilité

### 3. Funding Rate (Futures Perpétuels)

**Mécanisme:**
```
Funding Rate = Interest Rate Component + Premium Component

Typiquement:
- Funding > 0: Longs payent Shorts (bullish sentiment)
- Funding < 0: Shorts payent Longs (bearish sentiment)
```

**Impact:**
- Annualisé: Funding × 3 × 365 (payé toutes les 8h)
- Peut atteindre 50-100%+ annualisé en extremes
- Arbitrage: Spot + Short Perp → capture funding

### 4. Greeks en Crypto

**Particularités:**

| Greek | Crypto vs Traditionnel |
|-------|------------------------|
| **Delta** | Plus volatil (underlying très volatil) |
| **Gamma** | Plus élevé (besoin de rehedging fréquent) |
| **Vega** | TRÈS important (vol change beaucoup) |
| **Theta** | Time decay rapide (surtout short-dated) |
| **Rho** | Négligeable (taux ~0, mais funding rate à considérer) |

**Hedging en Crypto:**
- Delta hedging: Complexe à cause de la volatilité
- Gamma hedging: Nécessite options (coûteux)
- Vega hedging: Important pour market makers

---

## 💡 Insights Clés

### 1. Black-Scholes est Limité pour Crypto

**Problèmes:**
- Assume normalité → sous-estime événements extrêmes
- Volatilité constante → faux (vol clustering, vol of vol)
- Ne capture pas le volatility smile/skew

**Solutions:**
- Utiliser IV observée (pas historical vol)
- Modèles alternatifs: Heston (stochastic vol), Jump-Diffusion
- Ou simplement: être conscient des limites

### 2. Vega Risk est CRUCIAL en Crypto

- Vol crypto peut doubler en quelques jours
- Position long options: Vega positif → profite de vol ↑
- Position short options: Vega négatif → danger si vol ↑

**Exemple:**
- Long straddle, Vega = 0.40
- Si IV passe de 60% → 80%: Profit = 0.40 × 20 = $8 par option

### 3. Theta Decay est l'Ennemi du Long Options

- Options crypto sont CHERS (haute IV)
- Time decay est RAPIDE (surtout <7 jours)
- Long options besoin de mouvement SIGNIFICATIF pour profiler

**Règle empirique:**
- Long options: Besoin mouvement > premium payé
- Short options: Time decay travaille pour toi

### 4. Implied Volatility ≠ Realized Volatility

- IV = vol attendue par le marché (forward-looking)
- RV = vol réalisée (backward-looking)
- **IV > RV typiquement** (volatility risk premium)

**Trading signal:**
- IV >> RV historique → Options chères → Favoriser short options
- IV << RV historique → Options bon marché → Favoriser long options

---

## ⚠️ Limites et Mises en Garde

### 1. Black-Scholes Limitations

- Normalité assumée (FAUX pour crypto)
- Volatilité constante (FAUX)
- Pas de jumps/gaps (FAUX pour crypto)
- Européen seulement (pas d'early exercise)

### 2. Liquidity Risk

- Options crypto: Liquidité concentrée sur ATM, short-dated
- OTM, long-dated: Spreads larges, slippage élevé
- Market risk + liquidity risk

### 3. Model Risk

- IV calculée dépend du modèle (BS, Binomial, etc.)
- Different exchanges → different IVs
- Comparer IVs only if same model/assumptions

### 4. Counterparty Risk (DeFi Options)

- Options on-chain: Smart contract risk
- Exchange options: Platform risk (FTX!)
- Préférer: Collateralized, overcollateralized protocols

---

## 📈 Visualisations (à générer)

1. **Black-Scholes Call/Put Prices** vs Spot (different strikes)
2. **Greeks Evolution** vs Spot (Delta, Gamma, Vega, Theta)
3. **Strategy Payoff Diagrams** (Straddle, Strangle, Spreads)
4. **Implied Volatility Surface** (strike × expiration)
5. **Binomial Tree Visualization** (asset prices + option values)

---

## ✅ Checklist de Compréhension

- [ ] Comprendre différence Futures vs Forwards vs Options
- [ ] Savoir calculer Black-Scholes call/put
- [ ] Comprendre et calculer les 5 Greeks
- [ ] Interpréter Delta comme probabilité ITM
- [ ] Comprendre Vega risk (critique en crypto)
- [ ] Savoir calculer Implied Volatility
- [ ] Connaître stratégies de base (Covered Call, Straddle, etc.)
- [ ] Comprendre limitations de Black-Scholes pour crypto

---

## 📚 Références

1. **Black, F. & Scholes, M. (1973).** "The Pricing of Options and Corporate Liabilities." *Journal of Political Economy.*
2. **Hull, J. (2018).** "Options, Futures, and Other Derivatives" (10th ed.) ⭐
3. **Natenberg, S. (2014).** "Option Volatility and Pricing" ⭐
4. **Deribit Insights:** https://insights.deribit.com/
5. **CoinVol, Volmex:** Crypto IV data sources

---

## 🎯 Prochaines Étapes

**Master 5+ Suite:**
- [ ] Semaine 23: HFT & Market Microstructure Avancée
- [ ] Semaine 24: Alternative Data (On-chain, Sentiment)
- [ ] Semaine 25: Production Systems (Latency, Monitoring)
- [ ] Semaine 26: Reinforcement Learning pour Trading

**Phase 2 - Intégration Saiyan:**
- [ ] Implémenter calcul Greeks dans Saiyan
- [ ] Monitoring IV crypto (Deribit API)
- [ ] Strategies options simples (Covered Call pour yield)

---

*Module Master 5 - Derivatives Basics complété ✅*
