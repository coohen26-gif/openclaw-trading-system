# Semaine 23 - HFT & Market Microstructure Avancée

**Date:** 24 Mai 2026  
**Niveau:** Master 5 - Advanced Topics  
**Temps estimé:** 4-5h

---

## 🎯 Objectifs du Module

1. Comprendre la microstructure des marchés: Order Book, Spread, Liquidité
2. Maîtriser les métriques HFT: Latency, Fill Rate, Slippage
3. Implémenter des stratégies market-making basiques
4. Analyser l'order book dynamics: Imbalance, Order Flow
5. Comprendre les risques HFT: Adverse Selection, Latency Arms Race

---

## 📚 Théorie Fondamentale

### 1. Microstructure: De Quoi Parle-t-on?

**Définition:**
> L'étude du processus d'échange des actifs financiers: comment les ordres sont soumis, matchés, et exécutés.

**Acteurs du marché:**

| Acteur | Rôle | Objectif |
|--------|------|----------|
| **Market Makers (MM)** | Fournissent liquidité (bid + ask) | Gagner le spread, rebates |
| **Takers** | Consomment liquidité | Exécution immédiate |
| **HFT Firms** | MM + arbitrage + stat arb | Profit latency + spread |
| **Institutional** | Gros ordres (blocks) | Best execution, min impact |
| **Retail** | Petits ordres | Simple execution |

### 2. Order Book: Structure et Dynamique

**Limit Order Book (LOB):**

```
ASKS (Offers to Sell)
  Price    Size    Cumulative
  $50,100   0.5     0.5
  $50,150   1.2     1.7
  $50,200   2.0     3.7
  $50,250   0.8     4.5
  ...

SPREAD: $50,100 - $50,050 = $50 (0.10%)

BIDS (Offers to Buy)
  Price    Size    Cumulative
  $50,050   0.7     0.7
  $50,000   1.5     2.2
  $49,950   2.3     4.5
  $49,900   1.0     5.5
  ...
```

**Métriques clés:**

| Métrique | Formule | Interprétation |
|----------|---------|----------------|
| **Spread (absolute)** | Ask - Bid | Coût de trading immédiat |
| **Spread (relative)** | (Ask - Bid) / Mid | Spread en % du prix |
| **Mid Price** | (Ask + Bid) / 2 | Prix de référence |
| **Order Book Imbalance** | (Bid Vol - Ask Vol) / (Bid Vol + Ask Vol) | Pressure direction [-1, +1] |
| **Depth** | Sum of sizes at N levels | Liquidité disponible |
| **Market Impact** | ΔPrice / Size | Comment prix bouge avec taille |

### 3. Types d'Ordres

**Limit Order:**
- Ordre à prix limité (ou meilleur)
- **Maker:** Ajoute liquidité à l'order book
- Rebates sur certains exchanges (maker rebate)
- Risque: Non-exécuté si prix ne touche pas

**Market Order:**
- Exécution immédiate au meilleur prix disponible
- **Taker:** Consomme liquidité
- Pays le spread + taker fee
- Garantie d'exécution (mais pas de prix)

**Stop Order:**
- Devient market order quand stop price touché
- Pour stop-loss ou breakout entries
- Risque: Slippage en marché volatil

**IOC (Immediate or Cancel):**
- Exécute ce qui peut l'être immédiatement
- Cancel le reste
- Utile pour tester liquidité

**FOK (Fill or Kill):**
- Tout ou rien
- Si ne peut pas être fully filled → cancel entier

### 4. Costs de Trading

**Explicit Costs:**
```
Trading Cost = Spread + Fees + Slippage

Fees:
- Maker fee: -0.01% à 0.02% (parfois rebate!)
- Taker fee: 0.02% à 0.10%

Exemple Binance Futures:
- Maker: 0.02%
- Taker: 0.04%
```

**Implicit Costs:**
```
Slippage = Execution Price - Expected Price

Slippage ≈ (Order Size / Market Depth) × Impact Coefficient

Exemple:
- Order: 10 BTC
- Depth at bid: 50 BTC
- Impact coeff: 0.001
- Slippage ≈ (10/50) × 0.001 = 0.02%
```

**Total Cost Example:**
```
Trade: Buy 1 BTC @ $50,000

Explicit:
- Spread (0.10%): $50
- Taker fee (0.04%): $20

Implicit:
- Slippage (0.02%): $10

Total Cost: $80 (0.16%)
```

### 5. Market Making: Le Business Model

**Principe:**
> Coter bid et ask simultanément, gagner le spread, gérer le risque d'inventaire.

**P&L Market Maker:**
```
P&L = Spread Captured + Rebates - Inventory Loss - Adverse Selection

Où:
- Spread Captured: (Ask - Bid) × Volume
- Rebates: Maker rebate × Volume
- Inventory Loss: ΔPrice × Inventory Position
- Adverse Selection: Perte quand informed traders trade against you
```

**Risque Principal: Adverse Selection**
> Quand un trader informé trade contre toi, tu perds.

**Exemple:**
- Tu cotes: Bid $50,000 / Ask $50,100
- Trader informé sait que BTC va monter à $51,000
- Il achète à ton ask $50,100
- Tu es short 1 BTC @ $50,100, maintenant ça vaut $51,000
- **Perte: $900** (bien plus que le spread de $100 gagné)

**Protection contre Adverse Selection:**
1. **Toxic flow detection:** Identifier les traders informés
2. **Inventory management:** Réduire exposition quand inventory déséquilibré
3. **Widen spreads:** Quand volatilité ↑ ou incertitude ↑
4. **Latency:** Être plus rapide pour cancel quotes

### 6. Order Flow Analysis

**Order Flow:**
> Flux des ordres qui arrivent sur le marché.

**Métriques:**

| Métrique | Formule | Signal |
|----------|---------|--------|
| **Trade Imbalance** | (Buy Vol - Sell Vol) / Total Vol | Directional pressure |
| **Order Flow Imbalance (OFI)** | Σ(ΔBid Size - ΔAsk Size) | Predicts short-term returns |
| **VPIN (Volume-Synchronized Probability of Informed Trading)** | Estimate de % informed trades | Toxic flow indicator |

**Order Flow Imbalance (OFI):**
```
OFI = Σ(ΔBid Size - ΔAsk Size) sur N périodes

Si OFI > 0: Plus d'achat que vente → Prix va monter
Si OFI < 0: Plus de vente qu'achat → Prix va descendre

Predictive power: OFI prédit returns à 1-10 min horizon
```

### 7. Latency et HFT

**Latency Components:**
```
Total Latency = Network + Exchange + Processing

Network:
- Fiber optic: ~5 μs/km (speed of light in glass)
- Microwave: ~3 μs/km (faster, line-of-sight only)
- Satellite: ~240 ms (too slow for HFT)

Exchange:
- Matching engine: 50-500 μs
- Gateway: 10-100 μs

Processing:
- Order decision: 1-10 μs (FPGA) ou 10-100 μs (CPU)
```

**Latency Arms Race:**
- 2010: Milliseconds → Microseconds
- 2020: Microseconds → Nanoseconds
- Co-location: Serveurs dans le datacenter de l'exchange
- FPGA: Hardware acceleration pour ordre submission

**Est-ce accessible aux petits players?**
- **Non** pour true HFT (latency arbitrage)
- **Oui** pour market-making "slow" (seconds/minutes)
- **Oui** pour order flow analysis (pas besoin d'être le plus rapide)

### 8. Stratégies HFT/Microstructure

#### Market Making (Basic)

```python
def market_maker_quotes(spread_target, inventory, inventory_limit):
    """
    Generate bid/ask quotes based on inventory.
    """
    mid_price = get_mid_price()
    
    # Skew quotes based on inventory
    # If long inventory: Lower bid/ask to encourage selling
    inventory_skew = (inventory / inventory_limit) * (spread_target / 2)
    
    bid = mid_price - (spread_target / 2) - inventory_skew
    ask = mid_price + (spread_target / 2) - inventory_skew
    
    return bid, ask
```

#### Latency Arbitrage

```
Opportunity:
- Exchange A: BTC @ $50,000
- Exchange B: BTC @ $50,050
- Latency: 5 ms pour detect + execute

Action:
- Buy on A @ $50,000
- Sell on B @ $50,050
- Profit: $50 (minus fees)

Reality:
- Only works if you're faster than others
- Requires co-location, FPGA, direct market access
```

#### Order Book Imbalance Trading

```python
def imbalance_signal(order_book, threshold=0.3):
    """
    Trade based on order book imbalance.
    """
    bid_vol = sum(level['size'] for level in order_book['bids'][:5])
    ask_vol = sum(level['size'] for level in order_book['asks'][:5])
    
    imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol)
    
    if imbalance > threshold:
        return 'LONG'  # More buying pressure
    elif imbalance < -threshold:
        return 'SHORT'  # More selling pressure
    else:
        return 'NEUTRAL'
```

#### TWAP/VWAP Execution

```python
def twap_execution(total_size, duration_minutes):
    """
    Time-Weighted Average Price execution.
    Slice order into N pieces over time.
    """
    n_slices = duration_minutes * 4  # Every 15 seconds
    slice_size = total_size / n_slices
    
    for i in range(n_slices):
        submit_market_order(slice_size)
        sleep(15)  # Wait 15 seconds
```

```python
def vwap_execution(total_size, duration_minutes):
    """
    Volume-Weighted Average Price execution.
    Slice order proportional to historical volume profile.
    """
    volume_profile = get_historical_volume_profile()  # By time bucket
    
    for time_bucket in duration_minutes:
        slice_size = total_size * volume_profile[time_bucket]
        submit_market_order(slice_size)
        sleep(60)  # Wait 1 minute
```

---

## 💻 Implémentation Python

### 1. Order Book Analysis

```python
import numpy as np
import pandas as pd

class OrderBookAnalyzer:
    def __init__(self):
        self.bids = []  # List of (price, size)
        self.asks = []
    
    def update_book(self, bids, asks):
        """Update order book from exchange data."""
        self.bids = sorted(bids, reverse=True)  # Highest bid first
        self.asks = sorted(asks)  # Lowest ask first
    
    def get_spread(self):
        """Calculate spread."""
        if not self.bids or not self.asks:
            return None
        return self.asks[0][0] - self.bids[0][0]
    
    def get_mid_price(self):
        """Calculate mid price."""
        if not self.bids or not self.asks:
            return None
        return (self.asks[0][0] + self.bids[0][0]) / 2
    
    def get_spread_pct(self):
        """Calculate spread as percentage of mid."""
        spread = self.get_spread()
        mid = self.get_mid_price()
        if spread is None or mid is None:
            return None
        return spread / mid
    
    def get_depth(self, n_levels=5):
        """Calculate total depth at N levels."""
        bid_depth = sum(size for _, size in self.bids[:n_levels])
        ask_depth = sum(size for _, size in self.asks[:n_levels])
        return bid_depth, ask_depth
    
    def get_imbalance(self, n_levels=5):
        """Calculate order book imbalance."""
        bid_vol, ask_vol = self.get_depth(n_levels)
        if bid_vol + ask_vol == 0:
            return 0
        return (bid_vol - ask_vol) / (bid_vol + ask_vol)
    
    def get_vwap_price(self, side, size):
        """Calculate VWAP price for executing given size."""
        if side == 'buy':
            book = self.asks
        else:
            book = self.bids
        
        remaining = size
        total_cost = 0
        
        for price, level_size in book:
            if remaining <= 0:
                break
            exec_size = min(remaining, level_size)
            total_cost += exec_size * price
            remaining -= exec_size
        
        if remaining > 0:
            return None  # Not enough liquidity
        
        return total_cost / size

# Exemple d'utilisation
analyzer = OrderBookAnalyzer()

# Mock order book
bids = [(50000, 1.5), (49950, 2.0), (49900, 3.0)]
asks = [(50050, 1.2), (50100, 2.5), (50150, 1.8)]

analyzer.update_book(bids, asks)

print(f"Spread: ${analyzer.get_spread()}")
print(f"Spread %: {analyzer.get_spread_pct()*100:.3f}%")
print(f"Mid Price: ${analyzer.get_mid_price()}")
print(f"Imbalance: {analyzer.get_imbalance():.3f}")
print(f"VWAP Buy 2 BTC: ${analyzer.get_vwap_price('buy', 2.0)}")
```

### 2. Market Making Strategy

```python
class SimpleMarketMaker:
    def __init__(self, spread_target=0.001, inventory_limit=10.0):
        self.spread_target = spread_target  # 0.1%
        self.inventory_limit = inventory_limit
        self.inventory = 0.0
        self.pnl = 0.0
    
    def generate_quotes(self, mid_price):
        """Generate bid/ask quotes."""
        # Base spread
        half_spread = mid_price * self.spread_target / 2
        
        # Inventory skew: If long, lower quotes to encourage selling
        inventory_ratio = self.inventory / self.inventory_limit
        inventory_skew = half_spread * inventory_ratio
        
        bid = mid_price - half_spread - inventory_skew
        ask = mid_price + half_spread - inventory_skew
        
        return bid, ask
    
    def on_trade(self, side, size, price):
        """Update inventory and PnL on trade."""
        if side == 'buy':  # We bought (hit our bid)
            self.inventory += size
            self.pnl -= size * price
        else:  # We sold (hit our ask)
            self.inventory -= size
            self.pnl += size * price
    
    def calculate_pnl(self, current_price):
        """Calculate total PnL including inventory."""
        realized_pnl = self.pnl
        unrealized_pnl = self.inventory * current_price
        return realized_pnl + unrealized_pnl

# Exemple
mm = SimpleMarketMaker(spread_target=0.001, inventory_limit=5.0)

mid = 50000
bid, ask = mm.generate_quotes(mid)
print(f"Quotes: Bid ${bid:.2f} / Ask ${ask:.2f}")
print(f"Spread: ${ask - bid:.2f} ({(ask-bid)/mid*100:.3f}%)")

# Simulate trades
mm.on_trade('buy', 1.0, bid)  # Someone sold to us
print(f"\nAfter buy: Inventory = {mm.inventory} BTC")

mm.on_trade('sell', 0.5, ask)  # Someone bought from us
print(f"After sell: Inventory = {mm.inventory} BTC")

pnl = mm.calculate_pnl(50100)
print(f"PnL @ $50,100: ${pnl:.2f}")
```

### 3. Order Flow Imbalance (OFI)

```python
def calculate_ofi(order_book_history, n_periods=10):
    """
    Calculate Order Flow Imbalance.
    
    Parameters:
    - order_book_history: List of (bid_sizes, ask_sizes) tuples
    - n_periods: Number of periods to consider
    
    Returns:
    - OFI value
    """
    if len(order_book_history) < n_periods:
        return 0
    
    ofi = 0
    for i in range(len(order_book_history) - n_periods, len(order_book_history) - 1):
        prev_bids, prev_asks = order_book_history[i]
        curr_bids, curr_asks = order_book_history[i + 1]
        
        delta_bid = sum(curr_bids) - sum(prev_bids)
        delta_ask = sum(curr_asks) - sum(prev_asks)
        
        ofi += delta_bid - delta_ask
    
    return ofi

# Exemple
history = [
    ([10, 20, 30], [15, 25, 35]),  # (bid_sizes, ask_sizes)
    ([12, 22, 32], [14, 24, 34]),
    ([15, 25, 35], [12, 22, 32]),
    ([18, 28, 38], [10, 20, 30]),
]

ofi = calculate_ofi(history, n_periods=3)
print(f"Order Flow Imbalance: {ofi}")
# Positive OFI → Buying pressure → Price likely to rise
```

### 4. Slippage Estimation

```python
def estimate_slippage(order_size, order_book_depth, impact_coeff=0.001):
    """
    Estimate slippage for a market order.
    
    Parameters:
    - order_size: Size of order (in base currency)
    - order_book_depth: Total size available at top N levels
    - impact_coeff: Market impact coefficient (empirical)
    
    Returns:
    - Estimated slippage (as decimal)
    """
    if order_book_depth == 0:
        return float('inf')
    
    # Square-root impact law (empirical)
    slippage = impact_coeff * np.sqrt(order_size / order_book_depth)
    
    return slippage

# Exemple
order_size = 10.0  # BTC
depth = 50.0  # BTC available in order book
slippage = estimate_slippage(order_size, depth)

print(f"Order: {order_size} BTC")
print(f"Depth: {depth} BTC")
print(f"Estimated Slippage: {slippage*100:.3f}%")
print(f"Cost on $50k BTC: ${50000 * order_size * slippage:.2f}")
```

### 5. TWAP Execution

```python
import time

class TWAPExecutor:
    def __init__(self, total_size, duration_minutes, exchange_api):
        self.total_size = total_size
        self.duration = duration_minutes * 60  # Convert to seconds
        self.exchange = exchange_api
        self.executed = 0.0
        self.avg_price = 0.0
    
    def execute(self, slice_interval=15):
        """
        Execute TWAP strategy.
        
        Parameters:
        - slice_interval: Seconds between slices
        """
        n_slices = self.duration // slice_interval
        slice_size = self.total_size / n_slices
        
        print(f"Starting TWAP: {self.total_size} BTC over {self.duration//60} min")
        print(f"  → {n_slices} slices of {slice_size:.4f} BTC every {slice_interval}s")
        
        for i in range(int(n_slices)):
            # Submit market order
            exec_price = self.exchange.submit_market_order('buy', slice_size)
            
            # Update running average
            self.executed += slice_size
            self.avg_price = (self.avg_price * (self.executed - slice_size) + 
                             exec_price * slice_size) / self.executed
            
            print(f"  Slice {i+1}/{n_slices}: Executed {slice_size:.4f} @ ${exec_price:.2f}")
            
            # Wait for next slice
            time.sleep(slice_interval)
        
        print(f"\nTWAP Complete:")
        print(f"  Total Executed: {self.executed:.4f} BTC")
        print(f"  Average Price: ${self.avg_price:.2f}")
        
        return self.avg_price

# Mock exchange API
class MockExchange:
    def submit_market_order(self, side, size):
        # Simulate execution at random price near $50k
        import random
        price = 50000 + random.uniform(-50, 50)
        return price

# Exemple (commenté pour ne pas exécuter)
# exchange = MockExchange()
# twap = TWAPExecutor(total_size=1.0, duration_minutes=1, exchange_api=exchange)
# avg_price = twap.execute(slice_interval=5)
```

---

## 📊 Applications Crypto

### 1. Binance/Bybit Order Book

**Caractéristiques:**
- Update frequency: 100ms (websocket)
- Depth: 5, 10, 20 levels (selon subscription)
- Snapshot + Delta updates

**Exemple WebSocket Subscription:**
```python
import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    if 'bids' in data and 'asks' in data:
        bids = [(float(p), float(s)) for p, s in data['bids']]
        asks = [(float(p), float(s)) for p, s in data['asks']]
        
        # Analyze order book
        analyzer.update_book(bids, asks)
        print(f"Spread: {analyzer.get_spread_pct()*100:.4f}%")
        print(f"Imbalance: {analyzer.get_imbalance():.3f}")

ws = websocket.WebSocketStream('wss://stream.binance.com:9443/ws/btcusdt@depth10@100ms')
ws.on_message = on_message
ws.run_forever()
```

### 2. Crypto Market Making

**Particularités:**
- 24/7 trading (pas de market close)
- Volatilité extrême → spreads plus larges
- Multiple exchanges → arbitrage opportunities
- Funding rate impact sur perpetual futures

**Exemple de paramètres:**
```python
CRYPTO_MM_PARAMS = {
    'spread_target': 0.002,  # 0.2% (plus large que equities)
    'inventory_limit': 5.0,  # BTC
    'max_position_usd': 250000,
    'cancel_threshold': 0.001,  # Cancel if mid moves 0.1%
    'requote_frequency': 1.0,  # Requote every 1 second
}
```

### 3. Latency en Crypto

**Comparaison vs Traditional:**
- Crypto exchanges: ~50-200 ms round-trip (beaucoup plus lent!)
- Traditional (NYSE/Nasdaq): ~50-500 μs
- **Opportunity:** Pas besoin de FPGA pour être compétitif en crypto

**Exchanges par Latency:**
| Exchange | Avg Latency | Co-location |
|----------|-------------|-------------|
| Binance | 50-100 ms | Non |
| Bybit | 80-150 ms | Non |
| Deribit | 100-200 ms | Non |
| Coinbase | 30-80 ms | Oui (AWS) |

---

## 💡 Insights Clés

### 1. Spread ≠ Profit pour Market Maker

**Pourquoi?**
```
Gross Profit = Spread × Volume
Net Profit = Gross - Inventory Loss - Adverse Selection - Fees

Exemple réel:
- Spread capturé: $100
- Inventory loss (price moved against): -$150
- Adverse selection (informed trader): -$50
- Net: -$100 ❌
```

**Leçon:** Market making est un business de **risk management**, pas juste de spread capture.

### 2. Order Flow Imbalance est Predictive

**Recherche académique:**
- OFI prédit returns à horizon 1-10 minutes
- R² ~ 5-15% (énorme pour du short-term!)
- Fonctionne mieux sur liquid assets (BTC, ETH)

**Application:**
- OFI > 0.3 → Long signal
- OFI < -0.3 → Short signal
- Hold time: 1-5 minutes

### 3. Slippage Scale avec √(Size/Depth)

**Square-root impact law:**
```
Slippage ∝ √(Order Size / Market Depth)

Implications:
- 4x plus gros order → 2x plus de slippage (pas 4x!)
- Pour réduire slippage de moitié: 4x plus de depth OU 1/4 size
```

**Application:**
- Split large orders (TWAP/VWAP)
- Avoid market orders when depth is low
- Use limit orders when possible

### 4. HFT en Crypto est Accessible

**Contrairement à Traditional Finance:**
- Pas besoin de co-location ($$$)
- Pas besoin de FPGA ($$$)
- Latency exchanges: 50-200 ms (vs 50 μs en equity)
- **Python est suffisant** pour beaucoup de stratégies crypto

**Mais:**
- Competition augmente (HFT firms traditionnelles entrent en crypto)
- Edge se réduit avec le temps
- Need to move up the value chain (more sophisticated strategies)

---

## ⚠️ Risques et Mises en Garde

### 1. Adverse Selection Risk

**Le plus grand risque pour market makers:**
- Trader informé sait quelque chose que tu ne sais pas
- Il trade contre toi
- Tu perds bien plus que le spread gagné

**Mitigation:**
- Toxic flow detection (identifier patterns)
- Reduce exposure when uncertainty high
- Widen spreads during news/events

### 2. Inventory Risk

**Scenario:**
- Tu es long 10 BTC @ $50,000
- BTC crash à $45,000
- **Perte: $50,000** (bien plus que tous les spreads gagnés)

**Mitigation:**
- Inventory limits stricts
- Hedge avec futures/perps
- Skew quotes pour réduire inventory

### 3. Technical Risk

**Crypto-specific:**
- Exchange downtime (FTX, etc.)
- API rate limits
- WebSocket disconnections
- Smart contract risk (DeFi)

**Mitigation:**
- Multi-exchange redundancy
- Circuit breakers
- Monitoring/alerting
- Regular backups

### 4. Regulatory Risk

**Incertitude:**
- Crypto regulation evolving
- Market making could be classified differently
- Tax implications complex

**Mitigation:**
- Stay informed
- Legal counsel
- Diversify jurisdictions

---

## ✅ Checklist de Compréhension

- [ ] Comprendre structure Limit Order Book (LOB)
- [ ] Savoir calculer spread, mid price, imbalance
- [ ] Comprendre différence Maker vs Taker
- [ ] Connaître components de trading costs (spread + fees + slippage)
- [ ] Comprendre adverse selection risk
- [ ] Savoir implémenter market making basique
- [ ] Comprendre Order Flow Imbalance (OFI)
- [ ] Connaître stratégies execution (TWAP/VWAP)
- [ ] Comprendre latency arms race (et pourquoi crypto est différent)

---

## 📚 Références

1. **O'Hara, M. (1995).** "Market Microstructure Theory" ⭐
2. **Harris, L. (2003).** "Trading and Exchanges: Market Microstructure for Practitioners" ⭐
3. **Cont, R. (2014).** "Price Impact" in Encyclopedia of Quantitative Finance
4. **Donier, J., et al. (2015).** "Fully Consistent Microstructure Model of Market Impact"
5. **Binance API Docs:** https://binance-docs.github.io/apidocs/

---

## 🎯 Prochaines Étapes

**Master 5+ Suite:**
- [ ] Semaine 24: Alternative Data (On-chain, Sentiment)
- [ ] Semaine 25: Production Systems (Latency, Monitoring)
- [ ] Semaine 26: Reinforcement Learning pour Trading

**Phase 2 - Intégration Saiyan:**
- [ ] Order book analyzer module
- [ ] Simple market maker (testnet)
- [ ] TWAP/VWAP execution for large orders
- [ ] OFI signal integration

---

*Module Master 5 - HFT & Microstructure complété ✅*
