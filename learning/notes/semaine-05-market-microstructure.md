# Semaine 05 - Market Microstructure

## 1. Introduction

La market microstructure étudie comment les mécanismes de trading affectent la formation des prix, la liquidité et les coûts de transaction. C'est crucial pour tout trader quantitatif car cela détermine **comment** vos ordres sont exécutés, pas juste **quand**.

---

## 2. Order Book Dynamics

### Structure du Carnet d'Ordres

```
BEST ASK (Lowest Sell)  →  $95,105  |  0.5 BTC   ← Level 1 (Best Ask)
                          →  $95,110  |  1.2 BTC   ← Level 2
                          →  $95,115  |  0.8 BTC   ← Level 3
                          →  $95,125  |  2.5 BTC
                          →  $95,140  |  5.0 BTC
                          ...
                          →  $95,200  |  10.0 BTC  ← Level N
---------------------------------------------------------
                          →  $95,095  |  0.7 BTC   ← Level 1 (Best Bid)
                          →  $95,090  |  1.5 BTC   ← Level 2
                          →  $95,085  |  0.9 BTC   ← Level 3
                          →  $95,075  |  3.0 BTC
                          →  $95,060  |  4.5 BTC
                          ...
                          →  $95,000  |  15.0 BTC  ← Level N
BEST BID (Highest Buy)
```

### Métriques Clés

#### Bid-Ask Spread
```
Spread (absolute) = Best Ask - Best Bid
Spread (%) = (Best Ask - Best Bid) / Mid Price × 100
```

**Exemple BTC:**
- Best Ask: $95,105
- Best Bid: $95,095
- Mid Price: $95,100
- Spread: $10 (0.0105%)

**Exemple ETH:**
- Best Ask: $3,452.50
- Best Bid: $3,451.00
- Spread: $1.50 (0.043%)

**Exemple Gold (Forex/CFD):**
- Best Ask: $2,351.20
- Best Bid: $2,350.80
- Spread: $0.40 (0.017%)

#### Order Book Depth
```python
def calculate_depth(order_book, levels=5):
    """
    Calculate total volume available within N levels
    """
    ask_depth = sum(level['volume'] for level in order_book['asks'][:levels])
    bid_depth = sum(level['volume'] for level in order_book['bids'][:levels])
    return {
        'ask_depth': ask_depth,
        'bid_depth': bid_depth,
        'total_depth': ask_depth + bid_depth,
        'imbalance': (ask_depth - bid_depth) / (ask_depth + bid_depth)
    }
```

**Order Book Imbalance:**
- Positive (>0): More selling pressure (more asks)
- Negative (<0): More buying pressure (more bids)
- Prédicteur à court terme du prix

#### Order Book Slope
```python
def calculate_slope(order_book, side='ask'):
    """
    Measure how quickly liquidity diminishes away from mid
    Steeper slope = less liquidity = higher impact
    """
    levels = order_book[side][:10]
    if len(levels) < 2:
        return np.nan
    
    prices = [level['price'] for level in levels]
    volumes = [level['volume'] for level in levels]
    
    # Linear regression: volume ~ price
    slope = np.polyfit(prices, volumes, 1)[0]
    return slope
```

---

## 3. Slippage Modeling

### Définition
Le slippage est la différence entre le prix attendu d'un trade et le prix d'exécution réel.

### Types de Slippage

1. **Spread Slippage:** Payé même pour les petites tailles
   ```
   Slippage_spread = Spread / 2  (pour un market order)
   ```

2. **Impact Slippage:** Dû à la consommation de liquidité
   ```
   Slippage_impact = f(taille_order, depth_book)
   ```

3. **Timing Slippage:** Dû au délai entre décision et exécution
   - Latence réseau
   - Temps de traitement exchange
   - Particulièrement critique en HFT

### Modèle de Slippage Linéaire

```python
def linear_slippage_model(order_size, book_depth, spread_pct):
    """
    Simple linear slippage model
    
    order_size: Taille de l'ordre (en USD ou unités)
    book_depth: Liquidité disponible dans le book (en USD ou unités)
    spread_pct: Spread en pourcentage
    """
    # Spread cost (always paid)
    spread_cost = spread_pct / 2
    
    # Impact cost (proportional to size/depth ratio)
    if book_depth > 0:
        impact_cost = 0.5 * (order_size / book_depth)
    else:
        impact_cost = 1.0  # No liquidity = maximum slippage
    
    total_slippage_pct = spread_cost + impact_cost
    return total_slippage_pct


# Exemple concret
order_size_btc = 5.0  # 5 BTC
btc_price = 95000
order_size_usd = order_size_btc * btc_price  # $475,000

# Liquidité disponible dans les 5 niveaux
book_depth_usd = 2_000_000  # $2M disponible
spread_pct = 0.0001  # 0.01%

slippage = linear_slippage_model(order_size_usd, book_depth_usd, spread_pct)
print(f"Slippage estimé: {slippage*100:.3f}%")
print(f"Coût en USD: ${order_size_usd * slippage:,.0f}")
```

### Modèle de Slippage Non-Linéaire (Square Root)

Empiriquement, l'impact suit souvent une loi de puissance ~√(size):

```python
def square_root_slippage_model(order_size, daily_volume, volatility):
    """
    Almgren-Chriss / square-root impact model
    
    order_size: Taille de l'ordre (en USD)
    daily_volume: Volume quotidien moyen (en USD)
    volatility: Volatilité journalière
    """
    # Participation rate
    participation = order_size / daily_volume
    
    # Square-root impact model
    # a et b sont des constantes calibrées empiriquement
    a = 0.5  # Coefficient de spread
    b = 1.5  # Coefficient d'impact
    
    impact_pct = a * spread_pct + b * volatility * np.sqrt(participation)
    return impact_pct
```

---

## 4. Market Impact

### Définition
Le market impact est le mouvement de prix causé par votre propre trading.

### Composantes

1. **Temporary Impact:** 
   - Dû à l'absorption de liquidité
   - Se dissipe après le trade
   - Représente le coût de trading réel

2. **Permanent Impact:**
   - Dû à l'information révélée par le trade
   - Le marché s'ajuste au nouveau prix
   - Important pour les gros ordres

### Modèle d'Impact (Almgren-Chriss)

```python
def almgren_chriss_impact(order_size, daily_volume, volatility, execution_time_days=1/252):
    """
    Almgren-Chriss market impact model
    
    order_size: USD
    daily_volume: USD average daily volume
    volatility: Annual volatility
    execution_time_days: Temps d'exécution en jours de trading
    """
    # Participation rate
    q = order_size / daily_volume
    
    # Temporary impact (linear + square root)
    temporary_impact = 0.1 * volatility * np.sqrt(q / execution_time_days)
    
    # Permanent impact (linear)
    permanent_impact = 0.05 * volatility * q
    
    total_impact = temporary_impact + permanent_impact
    return {
        'temporary': temporary_impact,
        'permanent': permanent_impact,
        'total': total_impact
    }


# Exemple: Gros ordre BTC
btc_params = {
    'order_size': 10_000_000,  # $10M order
    'daily_volume': 50_000_000_000,  # $50B daily BTC volume
    'volatility': 0.65,  # 65% annual
    'execution_time_days': 1/252  # 1 day
}

impact = almgren_chriss_impact(**btc_params)
print(f"Temporary Impact: {impact['temporary']*100:.3f}%")
print(f"Permanent Impact: {impact['permanent']*100:.3f}%")
print(f"Total Impact: {impact['total']*100:.3f}%")
print(f"Cost: ${10_000_000 * impact['total']:,.0f}")
```

### Réduire l'Impact: TWAP & VWAP

```python
def twap_execution(order_size, num_slices, interval_minutes=5):
    """
    Time-Weighted Average Price execution
    Split order into equal parts over time
    """
    slice_size = order_size / num_slices
    schedule = []
    
    for i in range(num_slices):
        schedule.append({
            'time_offset': i * interval_minutes,
            'size': slice_size,
            'type': 'limit'  # Use limit orders to reduce impact
        })
    
    return schedule


def vwap_execution(order_size, volume_profile, max_participation=0.1):
    """
    Volume-Weighted Average Price execution
    Trade proportionally to historical volume profile
    """
    total_volume = sum(volume_profile)
    schedule = []
    
    for i, vol in enumerate(volume_profile):
        participation = vol / total_volume
        order_slice = order_size * participation
        
        # Cap participation to avoid excessive impact
        if order_slice > vol * max_participation:
            order_slice = vol * max_participation
        
        schedule.append({
            'time_bucket': i,
            'size': order_slice,
            'expected_volume': vol
        })
    
    return schedule
```

---

## 5. Liquidity Metrics

### Mesures de Liquidité

#### 1. Bid-Ask Spread
```python
def spread_metrics(asks, bids):
    """
    asks: List of ask prices
    bids: List of bid prices
    """
    best_ask = min(asks)
    best_bid = max(bids)
    mid_price = (best_ask + best_bid) / 2
    
    absolute_spread = best_ask - best_bid
    relative_spread = absolute_spread / mid_price
    percentage_spread = relative_spread * 100
    
    return {
        'absolute': absolute_spread,
        'relative': relative_spread,
        'percentage': percentage_spread,
        'mid_price': mid_price
    }
```

#### 2. Market Depth
```python
def market_depth(order_book, pct_from_mid=0.01):
    """
    Calculate total volume within X% of mid price
    """
    mid = (order_book['asks'][0]['price'] + order_book['bids'][0]['price']) / 2
    
    ask_depth = sum(
        level['volume'] for level in order_book['asks']
        if level['price'] <= mid * (1 + pct_from_mid)
    )
    
    bid_depth = sum(
        level['volume'] for level in order_book['bids']
        if level['price'] >= mid * (1 - pct_from_mid)
    )
    
    return {
        'ask_depth': ask_depth,
        'bid_depth': bid_depth,
        'total_depth': ask_depth + bid_depth
    }
```

#### 3. Order Book Imbalance
```python
def order_book_imbalance(order_book, levels=5):
    """
    Measure buying vs selling pressure
    Range: [-1, 1]
    -1 = all bids (extreme buy pressure)
    +1 = all asks (extreme sell pressure)
    0 = balanced
    """
    ask_vol = sum(l['volume'] for l in order_book['asks'][:levels])
    bid_vol = sum(l['volume'] for l in order_book['bids'][:levels])
    
    if ask_vol + bid_vol == 0:
        return 0
    
    imbalance = (ask_vol - bid_vol) / (ask_vol + bid_vol)
    return imbalance
```

#### 4. Amihud Illiquidity Ratio
```python
def amihud_illiquidity(daily_returns, daily_volumes):
    """
    Amihud (2002) illiquidity measure
    Higher = less liquid (more price impact per $ traded)
    
    ILLIQ = (1/N) × Σ(|Return| / Volume)
    """
    illiq_ratios = []
    
    for ret, vol in zip(daily_returns, daily_volumes):
        if vol > 0:
            illiq_ratios.append(abs(ret) / vol)
    
    return np.mean(illiq_ratios)
```

---

## 6. Différences: Crypto vs Forex vs Metals

### Tableau Comparatif

| Métrique | Crypto (BTC/ETH) | Forex (EUR/USD) | Metals (Gold) |
|----------|------------------|-----------------|---------------|
| **Spread typique** | 0.01-0.05% | 0.001-0.01% | 0.01-0.03% |
| **Profondeur (top 5)** | $1-10M | $50-500M | $5-50M |
| **Volatilité (annuelle)** | 50-80% | 8-12% | 15-25% |
| **Trading 24/7** | ✅ Oui | ❌ Non (weekend closed) | ⚠️ Partiel |
| **Fragmentation** | Élevée (100+ exchanges) | Faible (interbank) | Moyenne |
| **Régulation** | Faible | Élevée | Moyenne |
| **Settlement** | Instant (on-chain) | T+2 | T+2 / Physical |
| **Market makers** | Algorithmiques | Banks | Banks + Specialists |

### Crypto: Caractéristiques Spécifiques

**Avantages:**
- Trading 24/7/365
- Settlement rapide
- Accès retail facile
- Volatilité = opportunités

**Risques:**
- Fragmentation de liquidité
- Risk d'exchange (FTX, etc.)
- Manipulation moins régulée
- Latence variable

```python
def crypto_specific_risks():
    """
    Additional risk factors for crypto trading
    """
    return {
        'exchange_risk': 'Risk of exchange failure/hack',
        'fragmentation': 'Liquidity split across 100+ venues',
        'arbitrage_opportunities': 'Price differences between exchanges',
        'funding_rates': 'Perpetual swap funding payments',
        'on_chain_delays': 'Blockchain confirmation times',
        'regulatory_risk': 'Changing regulations by jurisdiction'
    }
```

### Forex: Caractéristiques Spécifiques

**Avantages:**
- Liquidité massive
- Spreads très serrés
- Marché régulé
- Faible manipulation

**Contraintes:**
- Fermé le weekend
- Settlement T+2
- Accès institutionnel dominant
- Moins de volatilité

### Metals (Or, Argent): Caractéristiques Spécifiques

**Avantages:**
- Valeur refuge
- Corrélation faible avec equities
- Inflation hedge

**Contraintes:**
- Physical settlement possible
- Storage costs (si physical)
- Moins liquide que Forex
- Influencé par données macro

---

## 7. Implémentation Python: Order Book Analyzer

```python
# learning/code/market_microstructure.py
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class OrderBookLevel:
    price: float
    volume: float
    timestamp: datetime


@dataclass
class OrderBook:
    symbol: str
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    timestamp: datetime


class MarketMicrostructureAnalyzer:
    """
    Analyze order book dynamics, slippage, and liquidity
    """
    
    def __init__(self, order_book: OrderBook):
        self.ob = order_book
        self.best_bid = order_book.bids[0].price if order_book.bids else None
        self.best_ask = order_book.asks[0].price if order_book.asks else None
        self.mid_price = (self.best_bid + self.best_ask) / 2 if (self.best_bid and self.best_ask) else None
    
    def spread_analysis(self) -> Dict[str, float]:
        """Calculate spread metrics"""
        if not self.mid_price:
            return {}
        
        absolute_spread = self.best_ask - self.best_bid
        relative_spread = absolute_spread / self.mid_price
        
        return {
            'absolute_spread': absolute_spread,
            'relative_spread': relative_spread,
            'percentage_spread': relative_spread * 100,
            'mid_price': self.mid_price
        }
    
    def depth_analysis(self, levels: int = 5) -> Dict[str, float]:
        """Calculate order book depth"""
        ask_depth = sum(level.volume for level in self.ob.asks[:levels])
        bid_depth = sum(level.volume for level in self.ob.bids[:levels])
        
        return {
            'ask_depth': ask_depth,
            'bid_depth': bid_depth,
            'total_depth': ask_depth + bid_depth,
            'depth_ratio': ask_depth / bid_depth if bid_depth > 0 else np.inf
        }
    
    def imbalance(self, levels: int = 5) -> float:
        """
        Calculate order book imbalance
        Positive = more asks (sell pressure)
        Negative = more bids (buy pressure)
        """
        ask_vol = sum(l.volume for l in self.ob.asks[:levels])
        bid_vol = sum(l.volume for l in self.ob.bids[:levels])
        
        if ask_vol + bid_vol == 0:
            return 0.0
        
        return (ask_vol - bid_vol) / (ask_vol + bid_vol)
    
    def slippage_estimate(self, order_size_usd: float, side: str = 'buy') -> Dict[str, float]:
        """
        Estimate slippage for a market order
        
        order_size_usd: Size in USD
        side: 'buy' or 'sell'
        """
        if not self.mid_price:
            return {}
        
        spread = self.spread_analysis()
        depth = self.depth_analysis(levels=10)
        
        # Spread slippage (always paid)
        spread_slippage = spread['relative_spread'] / 2
        
        # Impact slippage
        if side == 'buy':
            available_liquidity = depth['ask_depth']
        else:
            available_liquidity = depth['bid_depth']
        
        if available_liquidity > 0:
            # Square-root impact model
            participation = order_size_usd / (available_liquidity * self.mid_price)
            impact_slippage = 0.5 * np.sqrt(participation)
        else:
            impact_slippage = 1.0  # No liquidity
        
        total_slippage = spread_slippage + impact_slippage
        
        return {
            'spread_slippage_pct': spread_slippage * 100,
            'impact_slippage_pct': impact_slippage * 100,
            'total_slippage_pct': total_slippage * 100,
            'estimated_cost_usd': order_size_usd * total_slippage
        }
    
    def vwap_price(self, order_size: float, side: str = 'buy') -> float:
        """
        Calculate VWAP price for executing given size
        """
        levels = self.ob.asks if side == 'buy' else self.ob.bids
        
        remaining_size = order_size
        total_cost = 0.0
        executed_volume = 0.0
        
        for level in levels:
            if remaining_size <= 0:
                break
            
            exec_volume = min(remaining_size, level.volume)
            total_cost += exec_volume * level.price
            executed_volume += exec_volume
            remaining_size -= exec_volume
        
        if executed_volume == 0:
            return self.mid_price
        
        return total_cost / executed_volume


# ============================================================================
# EXEMPLES CONCRETS
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("MARKET MICROSTRUCTURE ANALYZER")
    print("=" * 70)
    
    # ----------------------------------------------------------------------
    # Exemple 1: BTC Order Book Analysis
    # ----------------------------------------------------------------------
    print("\n📊 EXEMPLE 1: BTC Order Book Analysis")
    print("-" * 50)
    
    # Simulated BTC order book
    btc_bids = [
        OrderBookLevel(95095, 0.7, datetime.now()),
        OrderBookLevel(95090, 1.5, datetime.now()),
        OrderBookLevel(95085, 0.9, datetime.now()),
        OrderBookLevel(95075, 3.0, datetime.now()),
        OrderBookLevel(95060, 4.5, datetime.now()),
    ]
    
    btc_asks = [
        OrderBookLevel(95105, 0.5, datetime.now()),
        OrderBookLevel(95110, 1.2, datetime.now()),
        OrderBookLevel(95115, 0.8, datetime.now()),
        OrderBookLevel(95125, 2.5, datetime.now()),
        OrderBookLevel(95140, 5.0, datetime.now()),
    ]
    
    btc_ob = OrderBook(
        symbol='BTC/USD',
        bids=btc_bids,
        asks=btc_asks,
        timestamp=datetime.now()
    )
    
    analyzer = MarketMicrostructureAnalyzer(btc_ob)
    
    spread = analyzer.spread_analysis()
    print(f"Symbol: {btc_ob.symbol}")
    print(f"Mid Price: ${spread['mid_price']:,.2f}")
    print(f"Spread: ${spread['absolute_spread']:.2f} ({spread['percentage_spread']:.3f}%)")
    
    depth = analyzer.depth_analysis()
    print(f"\nDepth (5 levels):")
    print(f"  Ask Depth: {depth['ask_depth']:.2f} BTC")
    print(f"  Bid Depth: {depth['bid_depth']:.2f} BTC")
    print(f"  Total: {depth['total_depth']:.2f} BTC (${depth['total_depth']*spread['mid_price']:,.0f})")
    
    imbalance = analyzer.imbalance()
    print(f"\nOrder Book Imbalance: {imbalance:.3f}")
    if imbalance > 0.2:
        print("  → Sell pressure detected")
    elif imbalance < -0.2:
        print("  → Buy pressure detected")
    else:
        print("  → Balanced book")
    
    # Slippage for different order sizes
    print(f"\nSlippage Estimates:")
    for size_usd in [10_000, 100_000, 1_000_000]:
        slippage = analyzer.slippage_estimate(size_usd, side='buy')
        print(f"  ${size_usd:>10,}: {slippage['total_slippage_pct']:.3f}% (${slippage['estimated_cost_usd']:,.0f})")
    
    # ----------------------------------------------------------------------
    # Exemple 2: Gold vs BTC Comparison
    # ----------------------------------------------------------------------
    print("\n\n📊 EXEMPLE 2: Gold vs BTC Microstructure")
    print("-" * 50)
    
    # Gold order book (tighter spread, less vol)
    gold_bids = [
        OrderBookLevel(2350.80, 50, datetime.now()),
        OrderBookLevel(2350.60, 100, datetime.now()),
        OrderBookLevel(2350.40, 75, datetime.now()),
    ]
    
    gold_asks = [
        OrderBookLevel(2351.20, 45, datetime.now()),
        OrderBookLevel(2351.40, 90, datetime.now()),
        OrderBookLevel(2351.60, 80, datetime.now()),
    ]
    
    gold_ob = OrderBook('XAU/USD', gold_bids, gold_asks, datetime.now())
    gold_analyzer = MarketMicrostructureAnalyzer(gold_ob)
    
    gold_spread = gold_analyzer.spread_analysis()
    btc_spread = analyzer.spread_analysis()
    
    print(f"{'Metric':<20} | {'Gold':<15} | {'BTC':<15}")
    print("-" * 55)
    print(f"{'Spread %':<20} | {gold_spread['percentage_spread']:<15.4f} | {btc_spread['percentage_spread']:<15.4f}")
    print(f"{'Mid Price':<20} | ${gold_spread['mid_price']:<14.2f} | ${btc_spread['mid_price']:<14.2f}")
    
    # ----------------------------------------------------------------------
    # Exemple 3: VWAP Execution
    # ----------------------------------------------------------------------
    print("\n\n📊 EXEMPLE 3: VWAP Execution for Large Order")
    print("-" * 50)
    
    order_size_btc = 10.0  # 10 BTC order
    vwap_price = analyzer.vwap_price(order_size_btc, side='buy')
    
    print(f"Order Size: {order_size_btc} BTC")
    print(f"Mid Price: ${analyzer.mid_price:,.2f}")
    print(f"VWAP Execution Price: ${vwap_price:,.2f}")
    print(f"Slippage vs Mid: ${(vwap_price - analyzer.mid_price):,.2f} ({(vwap_price/analyzer.mid_price - 1)*100:.3f}%)")
    print(f"Total Cost: ${vwap_price * order_size_btc:,.0f}")
    
    print("\n" + "=" * 70)
    print("✅ Market Microstructure Module Complete")
    print("=" * 70)
```

---

## 8. Points Clés à Retenir

1. **Spread** = coût de trading minimum, même pour les petits ordres
2. **Depth** = capacité du marché à absorber de gros ordres
3. **Imbalance** = indicateur de pression acheteur/vendeur à court terme
4. **Slippage** ∝ √(taille_order) selon modèle square-root
5. **Impact** a des composantes temporary et permanent
6. **TWAP/VWAP** réduisent l'impact pour les gros ordres
7. **Crypto** = plus de volatilité, fragmentation, mais trading 24/7

---

## 9. Prochaines Étapes

- Intégrer ces métriques dans un système de trading
- Optimiser l'exécution (limit vs market orders)
- Comprendre le risk management (semaine 06)
- Backtester avec coûts de transaction réalistes
