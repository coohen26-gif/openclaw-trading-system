# Semaine 24 - Alternative Data (On-chain, Sentiment, Flow)

**Date:** 24 Mai 2026  
**Niveau:** Master 5 - Advanced Topics  
**Temps estimé:** 4-5h

---

## 🎯 Objectifs du Module

1. Comprendre les catégories d'Alternative Data pour la crypto
2. Maîtriser les données on-chain: Transactions, Addresses, Mining
3. Analyser le sentiment: Social media, News, Search trends
4. Intégrer les données de flow: Exchange flows, Whale movements
5. Construire des signaux tradables à partir de ces données

---

## 📚 Théorie Fondamentale

### 1. Qu'est-ce que l'Alternative Data?

**Définition:**
> Données non-traditionnelles qui fournissent des insights sur un actif, au-delà des prix/volumes standards.

**Catégories pour la Crypto:**

| Catégorie | Sources | Fréquence | Exemple d'usage |
|-----------|---------|-----------|-----------------|
| **On-chain** | Blockchain itself | Real-time à 15min | Whale tracking, network health |
| **Sentiment** | Social media, news | Real-time à 1h | Contrarian signals, fear/greed |
| **Flow** | Exchange flows, OTC | 1h à daily | Supply/demand pressure |
| **Fundamental** | Network metrics | Daily à weekly | Valuation models |
| **Derivatives** | Options/futures data | Real-time | Positioning, hedging demand |

### 2. Données On-chain

#### a) Transaction Metrics

**Network Activity:**
```
- Transaction Count (daily)
- Active Addresses (daily active, monthly active)
- Transaction Volume (USD value)
- Average Transaction Size
- Transaction Fees (total, average)
```

**Interpretation:**
- ↑ Active addresses → ↑ Adoption → Bullish long-term
- ↑ Transaction count → ↑ Network usage → Bullish
- ↑ Avg transaction size → ↑ Institutional/whale activity
- ↑ Fees → ↑ Network congestion/demand → Mixed (bullish demand, bearish UX)

**Limites:**
- Une adresse ≠ une personne (exchanges ont des milliers d'adresses)
- Transactions internes (exchange wallets) ne comptent pas vraiment
- Wash trading possible

#### b) Address Metrics

**HODL Waves:**
> Distribution des coins par âge (quand ils ont bougé pour la dernière fois).

```
Age Bands:
- 1d-7d: Traders (short-term)
- 1m-3m: Swing traders
- 3m-6m: Medium-term holders
- 6m-12m: Long-term holders
- 1y-2y: Conviction holders
- 2y+: True believers (diamond hands)

Signal:
- Si 1y+ band GROWS → Accumulation → Bullish
- Si 1y+ band SHRINKS → Distribution → Bearish
```

**Supply Distribution:**
```
- Addresses with 0-0.1 BTC: Retail
- Addresses with 0.1-1 BTC: Small holders
- Addresses with 1-10 BTC: Medium holders
- Addresses with 10-100 BTC: Large holders
- Addresses with 100-1000 BTC: Whales
- Addresses with 1000+ BTC: Mega whales (exchanges, institutions)
```

**Signal:**
- Concentration ↑ → Centralization risk
- Distribution ↑ → Decentralization, healthier

#### c) Mining Metrics

**Hash Rate:**
```
- Network Hash Rate: Total computational power
- Hash Rate ↑ → Network security ↑ → Bullish long-term
- Hash Rate ↓ → Miners capitulating → Bearish (short-term)
```

**Miner Positioning:**
```
- Miner Reserves: BTC held by miners
- Miner Outflow: BTC sent from miner wallets
- Miner Inflow: BTC received by miner wallets

Signal:
- Miner Outflow ↑ → Miners selling → Bearish pressure
- Miner Reserves ↓ → Miners distributing → Bearish
```

**Mining Difficulty:**
```
- Adjusts every 2016 blocks (~2 weeks)
- Difficulty ↑ → More miners competing → Network healthy
- Difficulty ↓ → Miners exiting → Network stress
```

#### d) Valuation Metrics

**NVT Ratio (Network Value to Transactions):**
```
NVT = Market Cap / Daily Transaction Volume (USD)

Analogy: P/E ratio for stocks

Interpretation:
- NVT élevé → Overvalued (price high relative to utility)
- NVT bas → Undervalued (price low relative to utility)
- NVT ratio > 90th percentile → Top signal
- NVT ratio < 10th percentile → Bottom signal
```

**MVRV Ratio (Market Value to Realized Value):**
```
Realized Cap = Σ(UTXO value × price when UTXO was created)
MVRV = Market Cap / Realized Cap

Interpretation:
- MVRV > 3.5 → Overvalued (holders in significant profit)
- MVRV < 1 → Undervalued (holders at loss, capitulation)
- MVRV ~1 → Fair value
```

**NUPL (Net Unrealized Profit/Loss):**
```
NUPL = (Market Cap - Realized Cap) / Market Cap

Ranges:
- NUPL > 0.75 → Euphoria (top)
- NUPL 0.5-0.75 → Greed
- NUPL 0-0.5 → Hope/optimism
- NUPL -0.5-0 → Denial/fear
- NUPL < -0.5 → Capitulation (bottom)
```

### 3. Sentiment Data

#### a) Social Media Metrics

**Twitter/X:**
```
- Mention volume (BTC, ETH, etc.)
- Sentiment score (positive/negative/neutral)
- Influencer sentiment (tracked accounts)
- Hashtag trends
```

**Reddit:**
```
- r/CryptoCurrency, r/Bitcoin posts/comments
- Upvote ratios
- Sentiment analysis on comments
```

**Telegram/Discord:**
```
- Group message volume
- Sentiment in crypto trading groups
```

**Interpretation:**
- ↑ Volume + ↑ Positive → FOMO building → Caution
- ↑ Volume + ↑ Negative → Panic → Potential bottom
- ↓ Volume + Neutral → Apathy → Accumulation phase

**Contrarian Signal:**
> Extreme sentiment (very bullish or very bearish) is often a contrarian indicator.

#### b) News Sentiment

**Sources:**
- CoinDesk, Cointelegraph, The Block
- Crypto Twitter influencers
- Mainstream media coverage

**Metrics:**
```
- News volume (articles per day)
- Sentiment score (NLP analysis)
- Topic clustering (regulation, adoption, hacks, etc.)
```

**Events Impact:**
| Event Type | Typical Impact | Duration |
|------------|----------------|----------|
| Regulation (positive) | +5-15% | 1-7 days |
| Regulation (negative) | -10-30% | 1-14 days |
| Exchange hack | -5-20% | 1-5 days |
| Major adoption | +10-30% | 3-14 days |
| Macro (Fed, etc.) | ±5-15% | 1-3 days |

#### c) Search Trends

**Google Trends:**
```
- "Bitcoin" search volume
- "Buy Bitcoin" search volume
- "Crypto" search volume
- Regional breakdown
```

**Interpretation:**
- ↑ "Buy Bitcoin" → Retail FOMO → Late cycle signal
- ↑ "Bitcoin" general → Awareness ↑ → Neutral/bullish
- ↓ All searches → Apathy → Accumulation phase

**Correlation:**
- Google Trends correlate with price at tops (retail FOMO)
- Low search volume at bottoms (no one cares)

### 4. Flow Data

#### a) Exchange Flows

**Exchange Inflow:**
```
BTC sent TO exchanges → Likely preparing to sell → Bearish pressure
```

**Exchange Outflow:**
```
BTC sent FROM exchanges → Likely to cold storage → Bullish (reducing sell pressure)
```

**Exchange Balance:**
```
Total BTC on exchanges:
- Balance ↓ → Supply shock (less available to sell) → Bullish
- Balance ↑ → More supply available → Bearish
```

**Typical Thresholds:**
- Exchange Net Flow > +5k BTC/day → Significant selling pressure
- Exchange Net Flow < -5k BTC/day → Significant accumulation

#### b) Whale Movements

**Whale Alert (transactions > $100k):**
```
- Large transfers (exchange ↔ unknown)
- Large transfers (exchange ↔ exchange)
- Large transfers (unknown ↔ unknown)

Interpretation:
- Unknown → Exchange: Potential selling
- Exchange → Unknown: Potential accumulation
- Exchange → Exchange: OTC deal or rebalancing
```

**Whale Holdings:**
```
- Top 100 addresses concentration
- Changes in top holders
- New entries/exits from top 100
```

#### c) Stablecoin Flows

**USDT/USDC Issuance:**
```
- New USDT minted → Fresh buying power → Bullish
- USDT redeemed → Buying power reduced → Bearish
```

**Stablecoin Supply Ratio (SSR):**
```
SSR = Market Cap / Stablecoin Market Cap

Interpretation:
- SSR élevé → Less dry powder → Caution
- SSR bas → Lots of stablecoins waiting → Bullish
```

### 5. Derivatives Data

#### a) Futures Metrics

**Open Interest:**
```
Total outstanding futures contracts.

Interpretation:
- OI ↑ + Price ↑ → New money, strong trend
- OI ↑ + Price flat → Building pressure (breakout coming)
- OI ↓ + Price ↓ → Longs liquidating (capitulation)
- OI ↓ + Price ↑ → Shorts covering (squeeze)
```

**Funding Rates:**
```
Perpetual futures funding rate (paid every 8h).

Interpretation:
- Funding > 0.01% (annualized >10%) → Longs crowded → Caution
- Funding < -0.01% → Shorts crowded → Squeeze potential
- Funding extreme (>0.05%) → Reversal likely
```

**Long/Short Ratio:**
```
Ratio of long positions to short positions.

Interpretation:
- L/S > 2 → Too many longs → Contrarian bearish
- L/S < 0.5 → Too many shorts → Contrarian bullish
```

#### b) Options Metrics

**Put/Call Ratio:**
```
PCR = Put Volume / Call Volume

Interpretation:
- PCR > 1 → More puts (bearish hedging) → Contrarian bullish
- PCR < 0.5 → More calls (bullish speculation) → Contrarian bearish
```

**Implied Volatility:**
```
- IV ↑ → Expectation of big moves → Uncertainty
- IV ↓ → Expectation of calm → Complacency
- IV percentile: Compare to historical IV range
```

**Max Pain:**
```
Strike price where most options expire worthless.

Theory: Price tends to gravitate toward max pain at expiration.
```

---

## 💻 Implémentation Python

### 1. On-chain Data Fetcher (Glassnode-style)

```python
import requests
import pandas as pd
from datetime import datetime, timedelta

class OnChainDataFetcher:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.base_url = "https://api.glassnode.com/v1"  # Example
    
    def fetch_active_addresses(self, asset='btc', timeframe='1d'):
        """Fetch active addresses count."""
        # Mock data for demonstration
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        active_addresses = pd.Series(
            [900000 + int(100000 * pd.np.sin(i/5)) for i in range(30)],
            index=dates
        )
        return active_addresses
    
    def fetch_nvt_ratio(self, asset='btc'):
        """Fetch NVT ratio."""
        # Mock data
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        nvt = pd.Series(
            [50 + int(30 * pd.np.sin(i/7)) for i in range(30)],
            index=dates
        )
        return nvt
    
    def fetch_mvrv_ratio(self, asset='btc'):
        """Fetch MVRV ratio."""
        dates = pd.date_range(end=datetime.now(), periods=90, freq='D')
        mvrv = pd.Series(
            [1.5 + 0.8 * pd.np.sin(i/15) + 0.3 * pd.np.random.randn() for i in range(90)],
            index=dates
        )
        return mvrv
    
    def fetch_exchange_flows(self, asset='btc'):
        """Fetch exchange inflows/outflows."""
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        inflows = pd.Series(pd.np.random.normal(5000, 2000, 30), index=dates)
        outflows = pd.Series(pd.np.random.normal(6000, 2000, 30), index=dates)
        net_flow = inflows - outflows
        return inflows, outflows, net_flow
    
    def calculate_nupl(self, market_cap, realized_cap):
        """Calculate NUPL from market cap and realized cap."""
        return (market_cap - realized_cap) / market_cap

# Exemple d'utilisation
fetcher = OnChainDataFetcher()

active_addr = fetcher.fetch_active_addresses()
nvt = fetcher.fetch_nvt_ratio()
mvrv = fetcher.fetch_mvrv_ratio()

print(f"Active Addresses (avg): {active_addr.mean():,.0f}")
print(f"NVT Ratio (current): {nvt.iloc[-1]:.1f}")
print(f"MVRV Ratio (current): {mvrv.iloc[-1]:.2f}")
```

### 2. Sentiment Analyzer

```python
from textblob import TextBlob
import pandas as pd

class SentimentAnalyzer:
    def __init__(self):
        self.sentiment_history = []
    
    def analyze_text(self, text):
        """Analyze sentiment of a single text."""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 to +1
        subjectivity = blob.sentiment.subjectivity  # 0 to 1
        
        if polarity > 0.1:
            sentiment = 'positive'
        elif polarity < -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'polarity': polarity,
            'subjectivity': subjectivity,
            'sentiment': sentiment
        }
    
    def analyze_batch(self, texts):
        """Analyze sentiment of multiple texts."""
        results = []
        for text in texts:
            result = self.analyze_text(text)
            result['text'] = text[:50] + '...'  # Truncated
            results.append(result)
        
        df = pd.DataFrame(results)
        return df
    
    def calculate_sentiment_score(self, df):
        """Calculate aggregate sentiment score."""
        avg_polarity = df['polarity'].mean()
        positive_ratio = (df['sentiment'] == 'positive').mean()
        negative_ratio = (df['sentiment'] == 'negative').mean()
        
        return {
            'avg_polarity': avg_polarity,
            'positive_ratio': positive_ratio,
            'negative_ratio': negative_ratio,
            'neutral_ratio': 1 - positive_ratio - negative_ratio,
            'sentiment_signal': 'bullish' if avg_polarity > 0.1 else 'bearish' if avg_polarity < -0.1 else 'neutral'
        }

# Exemple
analyzer = SentimentAnalyzer()

tweets = [
    "Bitcoin is going to the moon! 🚀",
    "Crypto market is crashing, panic selling!",
    "BTC holding steady around $50k, neutral outlook",
    "Just bought more ETH, long term bullish",
    "Regulation fears spooking investors"
]

df = analyzer.analyze_batch(tweets)
score = analyzer.calculate_sentiment_score(df)

print(f"Sentiment Analysis:")
print(f"  Avg Polarity: {score['avg_polarity']:.2f}")
print(f"  Positive: {score['positive_ratio']*100:.1f}%")
print(f"  Negative: {score['negative_ratio']*100:.1f}%")
print(f"  Signal: {score['sentiment_signal']}")
```

### 3. Fear & Greed Index

```python
def calculate_fear_greed(metrics):
    """
    Calculate custom Fear & Greed Index.
    
    Parameters:
    - metrics: Dict with various metrics
    
    Returns:
    - fg_index: 0-100 (0=Extreme Fear, 100=Extreme Greed)
    """
    weights = {
        'volatility': 0.25,
        'momentum': 0.25,
        'social_media': 0.15,
        'dominance': 0.10,
        'trends': 0.10,
        'onchain': 0.15
    }
    
    scores = {}
    
    # Volatility (high vol = fear)
    vol_zscore = (metrics['current_vol'] - metrics['avg_vol']) / metrics['std_vol']
    scores['volatility'] = 50 - vol_zscore * 20  # Inverted
    
    # Momentum (positive momentum = greed)
    mom_7d = metrics['price_7d_change']
    scores['momentum'] = 50 + mom_7d * 5  # e.g., +10% → 100
    scores['momentum'] = max(0, min(100, scores['momentum']))
    
    # Social media sentiment
    scores['social_media'] = 50 + metrics['sentiment_polarity'] * 50
    
    # BTC dominance
    dom_change = metrics['btc_dominance_change']
    scores['dominance'] = 50 + dom_change * 100
    
    # Google trends
    trends_ratio = metrics['current_searches'] / metrics['avg_searches']
    scores['trends'] = 50 + (trends_ratio - 1) * 50
    
    # On-chain (MVRV)
    mvrv = metrics['mvrv_ratio']
    if mvrv < 1:
        scores['onchain'] = 20  # Undervalued = fear
    elif mvrv > 3:
        scores['onchain'] = 80  # Overvalued = greed
    else:
        scores['onchain'] = 50 + (mvrv - 1) * 25
    
    # Weighted average
    fg_index = sum(scores[k] * weights[k] for k in weights.keys())
    fg_index = max(0, min(100, fg_index))
    
    # Interpretation
    if fg_index < 25:
        interpretation = 'Extreme Fear'
    elif fg_index < 45:
        interpretation = 'Fear'
    elif fg_index < 55:
        interpretation = 'Neutral'
    elif fg_index < 75:
        interpretation = 'Greed'
    else:
        interpretation = 'Extreme Greed'
    
    return {
        'index': fg_index,
        'interpretation': interpretation,
        'scores': scores
    }

# Exemple
metrics = {
    'current_vol': 0.03,
    'avg_vol': 0.025,
    'std_vol': 0.008,
    'price_7d_change': 0.05,  # +5%
    'sentiment_polarity': 0.2,
    'btc_dominance_change': 0.002,
    'current_searches': 120,
    'avg_searches': 100,
    'mvrv_ratio': 1.8
}

fg = calculate_fear_greed(metrics)
print(f"Fear & Greed Index: {fg['index']:.0f}/100 ({fg['interpretation']})")
```

### 4. Exchange Flow Analyzer

```python
class ExchangeFlowAnalyzer:
    def __init__(self, threshold_significant=5000):
        self.threshold = threshold_significant  # BTC
    
    def analyze_flow(self, inflow, outflow):
        """
        Analyze exchange flow and generate signal.
        
        Parameters:
        - inflow: BTC inflow to exchanges
        - outflow: BTC outflow from exchanges
        
        Returns:
        - signal: 'bullish', 'bearish', or 'neutral'
        - strength: 0-100
        """
        net_flow = inflow - outflow
        
        if net_flow > self.threshold:
            signal = 'bearish'
            strength = min(100, (net_flow / self.threshold) * 50)
            interpretation = f"Significant selling pressure (+{net_flow:.0f} BTC)"
        elif net_flow < -self.threshold:
            signal = 'bullish'
            strength = min(100, (abs(net_flow) / self.threshold) * 50)
            interpretation = f"Significant accumulation (-{abs(net_flow):.0f} BTC)"
        else:
            signal = 'neutral'
            strength = abs(net_flow) / self.threshold * 50
            interpretation = f"Balanced flows ({net_flow:+.0f} BTC)"
        
        return {
            'signal': signal,
            'strength': strength,
            'net_flow': net_flow,
            'interpretation': interpretation
        }
    
    def detect_whale_movements(self, transactions, threshold_btc=100):
        """
        Detect whale movements from transaction list.
        """
        whale_txs = [tx for tx in transactions if tx['amount'] >= threshold_btc]
        
        if len(whale_txs) == 0:
            return {'count': 0, 'signal': 'neutral'}
        
        # Analyze direction
        to_exchange = sum(1 for tx in whale_txs if tx['to_type'] == 'exchange')
        from_exchange = sum(1 for tx in whale_txs if tx['from_type'] == 'exchange')
        
        if to_exchange > from_exchange * 1.5:
            signal = 'bearish'  # Whales moving to sell
        elif from_exchange > to_exchange * 1.5:
            signal = 'bullish'  # Whales accumulating
        else:
            signal = 'neutral'
        
        return {
            'count': len(whale_txs),
            'to_exchange': to_exchange,
            'from_exchange': from_exchange,
            'signal': signal,
            'total_volume': sum(tx['amount'] for tx in whale_txs)
        }

# Exemple
analyzer = ExchangeFlowAnalyzer(threshold_significant=5000)

# Daily flows
result = analyzer.analyze_flow(inflow=8000, outflow=5000)
print(f"Flow Analysis: {result['interpretation']}")
print(f"  Signal: {result['signal']} ({result['strength']:.0f}/100)")

# Whale movements
transactions = [
    {'amount': 150, 'from_type': 'unknown', 'to_type': 'exchange'},
    {'amount': 200, 'from_type': 'exchange', 'to_type': 'unknown'},
    {'amount': 120, 'from_type': 'unknown', 'to_type': 'exchange'},
    {'amount': 80, 'from_type': 'unknown', 'to_type': 'unknown'},
]

whale_analysis = analyzer.detect_whale_movements(transactions)
print(f"\nWhale Movements: {whale_analysis['count']} transactions")
print(f"  Signal: {whale_analysis['signal']}")
```

### 5. Composite Signal Generator

```python
class CompositeSignalGenerator:
    def __init__(self):
        self.signal_weights = {
            'onchain': 0.30,
            'sentiment': 0.20,
            'flows': 0.25,
            'derivatives': 0.25
        }
    
    def generate_signal(self, signals):
        """
        Generate composite trading signal from multiple sources.
        
        Parameters:
        - signals: Dict with signals from different categories
                   Each signal: {'signal': 'bullish'|'bearish'|'neutral', 'strength': 0-100}
        
        Returns:
        - composite_signal: 'bullish', 'bearish', or 'neutral'
        - confidence: 0-100
        - breakdown: Detailed breakdown
        """
        # Convert signals to numeric (-1 to +1)
        signal_map = {'bullish': 1, 'neutral': 0, 'bearish': -1}
        
        weighted_score = 0
        total_weight = 0
        
        breakdown = {}
        
        for category, signal_data in signals.items():
            weight = self.signal_weights.get(category, 0.1)
            signal_value = signal_map.get(signal_data['signal'], 0)
            strength = signal_data.get('strength', 50) / 100
            
            category_score = signal_value * strength * weight
            weighted_score += category_score
            total_weight += weight
            
            breakdown[category] = {
                'signal': signal_data['signal'],
                'strength': signal_data.get('strength', 50),
                'contribution': category_score
            }
        
        # Normalize
        if total_weight > 0:
            normalized_score = weighted_score / total_weight
        else:
            normalized_score = 0
        
        # Convert to signal
        if normalized_score > 0.2:
            composite_signal = 'bullish'
        elif normalized_score < -0.2:
            composite_signal = 'bearish'
        else:
            composite_signal = 'neutral'
        
        # Confidence
        confidence = abs(normalized_score) * 100
        
        return {
            'signal': composite_signal,
            'confidence': confidence,
            'score': normalized_score,
            'breakdown': breakdown
        }

# Exemple
generator = CompositeSignalGenerator()

signals = {
    'onchain': {'signal': 'bullish', 'strength': 70},  # MVRV low, accumulation
    'sentiment': {'signal': 'neutral', 'strength': 40},  # Mixed sentiment
    'flows': {'signal': 'bullish', 'strength': 60},  # Exchange outflows
    'derivatives': {'signal': 'bearish', 'strength': 50}  # High funding rate
}

result = generator.generate_signal(signals)
print(f"Composite Signal: {result['signal'].upper()}")
print(f"Confidence: {result['confidence']:.0f}/100")
print(f"Score: {result['score']:.2f}")
print(f"\nBreakdown:")
for category, data in result['breakdown'].items():
    print(f"  {category}: {data['signal']} ({data['contribution']:+.3f})")
```

---

## 📊 Applications Pratiques

### 1. Sources de Données

**On-chain (Gratuites):**
- Blockchain.com Explorer
- Blockchair
- Mempool.space (BTC)
- Etherscan (ETH)

**On-chain (Payantes - API):**
- Glassnode ($29-$799/mo)
- CryptoQuant ($29-$299/mo)
- IntoTheBlock ($99-$499/mo)
- Dune Analytics (free + paid)

**Sentiment:**
- LunarCrush (social metrics)
- Santiment (social + on-chain)
- TheTie (news + social)
- Google Trends API (gratuit)

**Flows:**
- Whale Alert (Twitter API, gratuit)
- CryptoQuant exchange flows
- Glassnode exchange metrics

**Derivatives:**
- Deribit API (options)
- Binance Futures API
- Bybit API
- Coinglass (agrégateur)

### 2. Signaux Tradables

#### Signal 1: MVRV Bottom Fishing

```python
def mvrv_bottom_signal(mvrv_ratio):
    """
    Buy signal when MVRV indicates undervaluation.
    """
    if mvrv_ratio < 1.0:
        return {'signal': 'STRONG BUY', 'confidence': 80}
    elif mvrv_ratio < 1.5:
        return {'signal': 'BUY', 'confidence': 60}
    elif mvrv_ratio > 3.5:
        return {'signal': 'SELL', 'confidence': 70}
    elif mvrv_ratio > 4.0:
        return {'signal': 'STRONG SELL', 'confidence': 85}
    else:
        return {'signal': 'HOLD', 'confidence': 30}
```

#### Signal 2: Exchange Flow Reversal

```python
def exchange_flow_signal(net_flow_7d_avg, threshold=3000):
    """
    Signal based on 7-day average exchange net flow.
    """
    if net_flow_7d_avg < -threshold:
        return {'signal': 'BULLISH', 'strength': min(100, abs(net_flow_7d_avg)/threshold * 50)}
    elif net_flow_7d_avg > threshold:
        return {'signal': 'BEARISH', 'strength': min(100, net_flow_7d_avg/threshold * 50)}
    else:
        return {'signal': 'NEUTRAL', 'strength': 30}
```

#### Signal 3: Sentiment Extremes (Contrarian)

```python
def sentiment_contrarian_signal(fear_greed_index):
    """
    Contrarian signal: Buy fear, sell greed.
    """
    if fear_greed_index < 20:
        return {'signal': 'STRONG BUY', 'rationale': 'Extreme Fear'}
    elif fear_greed_index < 35:
        return {'signal': 'BUY', 'rationale': 'Fear'}
    elif fear_greed_index > 80:
        return {'signal': 'STRONG SELL', 'rationale': 'Extreme Greed'}
    elif fear_greed_index > 65:
        return {'signal': 'SELL', 'rationale': 'Greed'}
    else:
        return {'signal': 'NEUTRAL', 'rationale': 'Balanced'}
```

### 3. Backtesting Alternative Data Signals

```python
def backtest_signal(signal_func, data, price_data, hold_period=7):
    """
    Backtest a signal strategy.
    
    Parameters:
    - signal_func: Function that generates signal from data
    - data: Input data for signal
    - price_data: Price series for returns calculation
    - hold_period: Days to hold after signal
    
    Returns:
    - returns: Strategy returns
    - sharpe: Sharpe ratio
    - win_rate: Win rate
    """
    signals = data.apply(signal_func)
    
    # Generate positions
    positions = pd.Series(0, index=price_data.index)
    positions[signals == 'BUY'] = 1
    positions[signals == 'SELL'] = -1
    
    # Calculate returns
    returns = price_data.pct_change().shift(-1)  # Next day return
    strategy_returns = positions * returns
    
    # Metrics
    total_return = (1 + strategy_returns).prod() - 1
    sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
    win_rate = (strategy_returns > 0).mean()
    
    return {
        'total_return': total_return,
        'sharpe': sharpe,
        'win_rate': win_rate,
        'returns': strategy_returns
    }
```

---

## 💡 Insights Clés

### 1. On-chain Data est Plus Fiable que le Sentiment

**Pourquoi?**
- On-chain: Argent réel, actions vérifiables
- Sentiment: Paroles, easily manipulated

**Hiérarchie de fiabilité:**
```
1. On-chain (whale movements, exchange flows) - PLUS FIABLE
2. Derivatives (OI, funding rates)
3. Sentiment institutionnel
4. Sentiment retail (Twitter, Reddit) - MOINS FIABLE
```

### 2. Les Signaux Fonctionnent Mieux en Combinaison

**Aucun signal seul n'est suffisant:**
- MVRV bas peut rester bas pendant des mois
- Sentiment extrême peut devenir PLUS extrême
- Exchange flows peuvent être noise

**Solution:**
- Composite signals (pondérer multiple sources)
- Confirmation required (2-3 signaux alignés)
- Timeframe alignment (short-term + long-term)

### 3. Context Matters

**Même signal, différent contexte = différent impact:**

| Signal | Bull Market | Bear Market |
|--------|-------------|-------------|
| Exchange Inflow | Minor selling | MAJOR selling panic |
| Negative News | Buy the dip | Continuation down |
| High Funding | Normal | Warning sign |

### 4. Latency Varies by Data Type

| Data Type | Latency | Trading Horizon |
|-----------|---------|-----------------|
| On-chain (tx) | 10min-1h | Days-weeks |
| Exchange flows | 1-4h | Days |
| Sentiment | Real-time | Hours-days |
| Derivatives | Real-time | Minutes-hours |

---

## ⚠️ Limites et Mises en Garde

### 1. Data Quality Issues

**Problèmes:**
- On-chain: Adresses ≠ personnes (exchanges)
- Sentiment: Bots, manipulation
- Flows: OTC deals non-détectés
- Retards: Certaines données sont lagging

### 2. Overfitting Risk

**Danger:**
- Tester 100 signaux → 5 vont marcher par chance
- Backtest period spécifique → ne généralise pas

**Mitigation:**
- Out-of-sample testing
- Walk-forward analysis
- Multiple market regimes

### 3. Data Snooping

**Problème:**
- Regarder les données AVANT de formuler le signal
- Biais de survie (seuls les signaux qui ont marché sont publiés)

**Solution:**
- Formulate hypothesis FIRST
- Then test
- Pre-register signals (like clinical trials)

### 4. Structural Breaks

**Risque:**
- Crypto market evolves rapidly
- Signal that worked in 2021 may not work in 2026
- Institutionalization changes dynamics

**Mitigation:**
- Regular signal review
- Adaptive models
- Decay old data in training

---

## ✅ Checklist de Compréhension

- [ ] Comprendre catégories d'Alternative Data (on-chain, sentiment, flows, derivatives)
- [ ] Savoir interpréter NVT, MVRV, NUPL ratios
- [ ] Comprendre exchange flows (inflow = selling pressure)
- [ ] Savoir analyser sentiment (et être contrarian aux extremes)
- [ ] Comprendre futures metrics (OI, funding rates, L/S ratio)
- [ ] Savoir construire composite signals
- [ ] Connaître sources de données (Glassnode, CryptoQuant, etc.)
- [ ] Comprendre limites et risques (data quality, overfitting)

---

## 📚 Références

1. **Glassnode:** https://glassnode.com/ (on-chain data)
2. **CryptoQuant:** https://cryptoquant.com/ (exchange flows, on-chain)
3. **Santiment:** https://santiment.net/ (social + on-chain)
4. **Coinglass:** https://www.coinglass.com/ (derivatives data)
5. **Burniske, C. (2017).** "Cryptoassets: The Innovative Investor's Guide"

---

## 🎯 Prochaines Étapes

**Master 5+ Suite:**
- [ ] Semaine 25: Production Systems (Latency, Monitoring, CI/CD)
- [ ] Semaine 26: Reinforcement Learning pour Trading

**Phase 2 - Intégration Saiyan:**
- [ ] On-chain data fetcher module
- [ ] Sentiment analyzer (Twitter, Reddit)
- [ ] Composite signal generator
- [ ] Backtesting framework pour alternative data signals

---

*Module Master 5 - Alternative Data complété ✅*
