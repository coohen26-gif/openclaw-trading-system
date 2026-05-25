# Semaine 04 - Options Pricing & Black-Scholes

## 1. Introduction au Modèle Black-Scholes

Le modèle Black-Scholes-Merton (1973) est la pierre angulaire de la pricing d'options européennes. Il permet de calculer le prix théorique d'une option call ou put.

### Hypothèses du Modèle
- Marché efficient (pas d'arbitrage)
- Volatilité constante
- Taux d'intérêt sans risque constant
- Pas de dividendes (version de base)
- Trading continu
- Distribution log-normale des prix

### Formule Black-Scholes

**Call Option:**
```
C = S₀ × N(d₁) - K × e^(-rT) × N(d₂)
```

**Put Option:**
```
P = K × e^(-rT) × N(-d₂) - S₀ × N(-d₁)
```

Où:
- `d₁ = [ln(S₀/K) + (r + σ²/2)T] / (σ√T)`
- `d₂ = d₁ - σ√T`
- `S₀` = prix spot actuel
- `K` = strike price
- `r` = taux sans risque
- `σ` = volatilité (annualisée)
- `T` = temps jusqu'à expiration (en années)
- `N()` = fonction de répartition de la loi normale standard

---

## 2. Les Greeks - Mesures de Sensibilité

Les Greeks mesurent la sensibilité du prix de l'option aux différents paramètres.

### Delta (Δ)
**Définition:** Sensibilité du prix de l'option au prix du sous-jacent.

- **Call:** Δ = N(d₁) ∈ [0, 1]
- **Put:** Δ = N(d₁) - 1 ∈ [-1, 0]

**Usage:** 
- Hedging directionnel
- Approximation de la probabilité ITM (In-The-Money)
- Delta-neutral strategies

### Gamma (Γ)
**Définition:** Taux de changement du Delta par rapport au sous-jacent.

```
Γ = N'(d₁) / (S₀ × σ × √T)
```

**Usage:**
- Mesure du risque de convexité
- Important pour le rebalancing de hedge
- Gamma maximum pour les options ATM (At-The-Money)

### Vega (ν)
**Définition:** Sensibilité à la volatilité.

```
Vega = S₀ × N'(d₁) × √T
```

**Usage:**
- Toutes les options longues ont un Vega positif
- Critique pour le trading de volatilité
- Vega plus élevé pour les options ATM et longues maturités

### Theta (Θ)
**Définition:** Sensibilité au temps (time decay).

**Call:**
```
Θ = -[S₀ × N'(d₁) × σ] / (2√T) - r × K × e^(-rT) × N(d₂)
```

**Put:**
```
Θ = -[S₀ × N'(d₁) × σ] / (2√T) + r × K × e^(-rT) × N(-d₂)
```

**Usage:**
- Mesure du coût du temps
- Négatif pour les options longues (perte de valeur avec le temps)
- Accélère près de l'expiration

### Rho (ρ)
**Définition:** Sensibilité au taux d'intérêt.

- **Call:** ρ = K × T × e^(-rT) × N(d₂)
- **Put:** ρ = -K × T × e^(-rT) × N(-d₂)

**Usage:** Moins critique à court terme, important pour les options longues maturités.

---

## 3. Volatilité: Implicite vs Historique

### Volatilité Historique
- Calculée à partir des prix passés
- Méthode: écart-type des rendements logarithmiques annualisé
- Regarde dans le passé

```python
# Calcul de la volatilité historique
import numpy as np

def historical_volatility(prices, window=252):
    returns = np.log(prices / prices.shift(1))
    vol = returns.rolling(window=window).std() * np.sqrt(252)
    return vol
```

### Volatilité Implicite
- Volatilité "inversée" du prix de marché de l'option
- Utilise Black-Scholes en sens inverse
- Représente les attentes du marché (forward-looking)
- Trouvée par méthode numérique (Newton-Raphson, Brent)

```python
from scipy.optimize import brentq

def implied_volatility(market_price, S, K, T, r, option_type='call'):
    """Trouve la volatilité implicite par Brent's method"""
    
    def bs_price(sigma):
        d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
        d2 = d1 - sigma*np.sqrt(T)
        
        if option_type == 'call':
            return S * norm.cdf(d1) - K * np.exp(-r*T) * norm.cdf(d2)
        else:
            return K * np.exp(-r*T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    
    def objective(sigma):
        return bs_price(sigma) - market_price
    
    # La volatilité implicite est entre 0.01 et 5 (1% à 500%)
    return brentq(objective, 0.01, 5.0)
```

### Volatility Smile/Skew
- La volatilité implicite varie selon le strike
- **Smile:** IV plus élevée pour les options ITM et OTM
- **Skew:** IV plus élevée pour les puts OTM (equity markets)
- **Crypto:** Souvent un smile prononcé dû aux tails risks

---

## 4. Implémentation Python Complète

```python
# learning/code/black_scholes.py
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
from typing import Tuple, Dict

class BlackScholes:
    """
    Black-Scholes Options Pricing Model
    Support: Call, Put, Greeks, Implied Volatility
    """
    
    def __init__(self, S: float, K: float, T: float, r: float, sigma: float):
        """
        S: Spot price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free rate (annual)
        sigma: Volatility (annual)
        """
        self.S = S
        self.K = K
        self.T = T
        self.r = r
        self.sigma = sigma
        
        # Pré-calcul des termes intermédiaires
        self.d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
        self.d2 = self.d1 - sigma*np.sqrt(T)
    
    def price(self, option_type: str = 'call') -> float:
        """Calculate option price"""
        if option_type == 'call':
            return self.S * norm.cdf(self.d1) - self.K * np.exp(-self.r*self.T) * norm.cdf(self.d2)
        elif option_type == 'put':
            return self.K * np.exp(-self.r*self.T) * norm.cdf(-self.d2) - self.S * norm.cdf(-self.d1)
        else:
            raise ValueError("option_type must be 'call' or 'put'")
    
    def delta(self, option_type: str = 'call') -> float:
        """Delta: sensitivity to underlying price"""
        if option_type == 'call':
            return norm.cdf(self.d1)
        else:
            return norm.cdf(self.d1) - 1
    
    def gamma(self) -> float:
        """Gamma: rate of change of delta"""
        return norm.pdf(self.d1) / (self.S * self.sigma * np.sqrt(self.T))
    
    def vega(self) -> float:
        """Vega: sensitivity to volatility"""
        return self.S * norm.pdf(self.d1) * np.sqrt(self.T)
    
    def theta(self, option_type: str = 'call') -> float:
        """Theta: sensitivity to time (daily)"""
        term1 = -(self.S * norm.pdf(self.d1) * self.sigma) / (2 * np.sqrt(self.T))
        
        if option_type == 'call':
            term2 = self.r * self.K * np.exp(-self.r*self.T) * norm.cdf(self.d2)
            return (term1 - term2) / 365  # Daily theta
        else:
            term2 = -self.r * self.K * np.exp(-self.r*self.T) * norm.cdf(-self.d2)
            return (term1 + term2) / 365
    
    def rho(self, option_type: str = 'call') -> float:
        """Rho: sensitivity to interest rate"""
        if option_type == 'call':
            return self.K * self.T * np.exp(-self.r*self.T) * norm.cdf(self.d2) / 100
        else:
            return -self.K * self.T * np.exp(-self.r*self.T) * norm.cdf(-self.d2) / 100
    
    def all_greeks(self, option_type: str = 'call') -> Dict[str, float]:
        """Return all Greeks in one call"""
        return {
            'delta': self.delta(option_type),
            'gamma': self.gamma(),
            'vega': self.vega(),
            'theta': self.theta(option_type),
            'rho': self.rho(option_type)
        }


def implied_volatility(market_price: float, S: float, K: float, T: float, 
                       r: float, option_type: str = 'call') -> float:
    """
    Calculate implied volatility using Brent's method
    """
    def bs_price(sigma):
        if sigma < 0.001:
            return 0  # Avoid division by zero
        
        d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
        d2 = d1 - sigma*np.sqrt(T)
        
        if option_type == 'call':
            return S * norm.cdf(d1) - K * np.exp(-r*T) * norm.cdf(d2)
        else:
            return K * np.exp(-r*T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    
    def objective(sigma):
        return bs_price(sigma) - market_price
    
    # Boundaries: 0.1% to 500% annual vol
    try:
        return brentq(objective, 0.001, 5.0)
    except ValueError:
        return np.nan  # No solution found


# ============================================================================
# EXEMPLES CONCRETS - CRYPTO & METALS
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("BLACK-SCHOLES: EXEMPLES PRATIQUES")
    print("=" * 60)
    
    # ----------------------------------------------------------------------
    # Exemple 1: Bitcoin Call Option
    # ----------------------------------------------------------------------
    print("\n📊 EXEMPLE 1: BTC Call Option")
    print("-" * 40)
    
    btc_params = {
        'S': 95000,      # BTC spot price
        'K': 100000,     # Strike
        'T': 30/365,     # 30 days to expiration
        'r': 0.05,       # 5% risk-free rate
        'sigma': 0.65    # 65% annual volatility (typical crypto)
    }
    
    bs_btc = BlackScholes(**btc_params)
    call_price = bs_btc.price('call')
    greeks = bs_btc.all_greeks('call')
    
    print(f"Spot BTC: ${btc_params['S']:,.0f}")
    print(f"Strike: ${btc_params['K']:,.0f}")
    print(f"Days to expiry: {btc_params['T']*365:.0f}")
    print(f"Volatility: {btc_params['sigma']*100:.1f}%")
    print(f"\nCall Price: ${call_price:,.2f}")
    print(f"\nGreeks:")
    print(f"  Delta: {greeks['delta']:.4f} ({greeks['delta']*100:.1f}% probability ITM)")
    print(f"  Gamma: {greeks['gamma']:.6f}")
    print(f"  Vega: {greeks['vega']:.2f} (per 1% vol change: ${greeks['vega']*0.01:.2f})")
    print(f"  Theta: {greeks['theta']:.2f} (daily decay)")
    print(f"  Rho: {greeks['rho']:.2f}")
    
    # ----------------------------------------------------------------------
    # Exemple 2: Gold Put Option
    # ----------------------------------------------------------------------
    print("\n\n📊 EXEMPLE 2: Gold Put Option")
    print("-" * 40)
    
    gold_params = {
        'S': 2350,       # Gold spot price ($/oz)
        'K': 2300,       # Strike
        'T': 90/365,     # 90 days
        'r': 0.045,      # 4.5% risk-free rate
        'sigma': 0.18    # 18% annual volatility (typical metals)
    }
    
    bs_gold = BlackScholes(**gold_params)
    put_price = bs_gold.price('put')
    greeks_gold = bs_gold.all_greeks('put')
    
    print(f"Spot Gold: ${gold_params['S']:,.0f}/oz")
    print(f"Strike: ${gold_params['K']:,.0f}/oz")
    print(f"Days to expiry: {gold_params['T']*365:.0f}")
    print(f"Volatility: {gold_params['sigma']*100:.1f}%")
    print(f"\nPut Price: ${put_price:,.2f}")
    print(f"\nGreeks:")
    print(f"  Delta: {greeks_gold['delta']:.4f}")
    print(f"  Gamma: {greeks_gold['gamma']:.6f}")
    print(f"  Vega: {greeks_gold['vega']:.2f}")
    print(f"  Theta: {greeks_gold['theta']:.2f} (daily decay)")
    
    # ----------------------------------------------------------------------
    # Exemple 3: Implied Volatility Calculation
    # ----------------------------------------------------------------------
    print("\n\n📊 EXEMPLE 3: Implied Volatility")
    print("-" * 40)
    
    # Market price of ETH option
    eth_market_params = {
        'market_price': 2850,  # Observed market price
        'S': 3400,             # ETH spot
        'K': 3500,             # Strike
        'T': 45/365,           # 45 days
        'r': 0.05,
        'option_type': 'call'
    }
    
    iv = implied_volatility(**eth_market_params)
    
    print(f"ETH Call Option:")
    print(f"  Spot: ${eth_market_params['S']:,.0f}")
    print(f"  Strike: ${eth_market_params['K']:,.0f}")
    print(f"  Market Price: ${eth_market_params['market_price']:,.0f}")
    print(f"\n  Implied Volatility: {iv*100:.2f}%")
    print(f"  vs Historical (typical): ~55-70%")
    
    if iv > 0.70:
        print(f"  → Volatility is HIGH (option expensive)")
    elif iv < 0.50:
        print(f"  → Volatility is LOW (option cheap)")
    else:
        print(f"  → Volatility is MODERATE")
    
    # ----------------------------------------------------------------------
    # Exemple 4: Delta-Hedging Simulation
    # ----------------------------------------------------------------------
    print("\n\n📊 EXEMPLE 4: Delta-Hedging Concept")
    print("-" * 40)
    
    # Sell 10 call options, hedge with underlying
    num_options = 10
    option_delta = bs_btc.delta('call')
    
    print(f"Position: Short {num_options} BTC Call Options")
    print(f"Option Delta: {option_delta:.4f}")
    print(f"\nTo be Delta-Neutral:")
    print(f"  Hedge required: {num_options * option_delta:.4f} BTC")
    print(f"  Value of hedge: ${num_options * option_delta * btc_params['S']:,.0f}")
    print(f"\nIf BTC moves +1%:")
    print(f"  Option loss ≈ ${num_options * option_delta * btc_params['S'] * 0.01:,.0f}")
    print(f"  Hedge gain ≈ ${num_options * option_delta * btc_params['S'] * 0.01:,.0f}")
    print(f"  Net P&L ≈ $0 (delta-neutral)")
    
    print("\n" + "=" * 60)
    print("✅ Black-Scholes Module Complete")
    print("=" * 60)
```

---

## 5. Points Clés à Retenir

1. **Black-Scholes** est un modèle de pricing, pas une prédiction de prix futur
2. **Delta** ≈ probabilité que l'option expire ITM
3. **Gamma** est maximal pour les options ATM → risque de hedge plus élevé
4. **Vega** mesure l'exposition à la volatilité → crucial en crypto
5. **Theta** est le "loyer" payé pour l'effet de levier de l'option
6. **Volatilité implicite** > historique = option "chère" (sentiment haussier du risque)
7. **Limites du modèle:** volatilité non-constante, jumps, queues épaisses (surtout crypto)

---

## 6. Prochaines Étapes

- Comprendre la microstructure des marchés (semaine 05)
- Intégrer les Greeks dans une stratégie de trading
- Backtester des stratégies options avec données réelles
- Explorer les modèles alternatifs (Heston, Local Vol, etc.)
