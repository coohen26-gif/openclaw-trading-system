# Semaine 14 - Momentum & Breakouts

**Date:** 24 mai 2026  
**Module:** Master 2 - ML pour Trading  
**Statut:** ✅ Complet

---

## 1. Objectif du Module

Le **momentum** est l'un des facteurs de risque les plus documentés en finance. Ce module couvre l'identification des vrais breakouts vs fakeouts, avec confirmation par le volume.

**Objectifs:**
- Comprendre le momentum et ses anomalies
- Identifier les vrais breakouts vs fakeouts
- Utiliser le volume comme confirmation
- Corriger le bug momentum "de la nuit" (overnight gap)
- Backtest comparatif Crypto vs Metals

---

## 2. Théorie du Momentum

### 2.1 Définition et Évidence Empirique

**Momentum:** Tendance des assets qui ont performé dans le passé à continuer de performer.

**Deux types:**
1. **Time-series momentum:** Un asset qui monte continue de monter
2. **Cross-sectional momentum:** Les meilleurs assets surpassent les pires

**Évidence:**
- Jegadeesh & Titman (1993): Momentum sur actions US (3-12 mois)
- Moskowitz et al. (2012): Momentum sur futures (1-12 mois)
- Asness et al. (2013): Momentum présent dans toutes les asset classes

### 2.2 Momentum en Crypto vs Metals

| Caractéristique | Crypto | Metals |
|-----------------|--------|--------|
| Persistence | 1-4 semaines | 1-3 mois |
| Volatilité | Très élevée | Modérée |
| Overnight gap | Important (24/7) | Important (gaps weekend) |
| Volume signal | Fort | Modéré |
| Fakeouts | Fréquents | Moins fréquents |

---

## 3. Calcul du Momentum

### 3.1 Momentum Simple

```python
def calculate_momentum(prices, lookback=20):
    """
    Momentum simple: return sur lookback périodes.
    """
    return prices.pct_change(lookback)

# Exemple: Momentum 20 jours
mom_20d = calculate_momentum(df['close'], lookback=20)
```

### 3.2 Momentum Exponentiel (EMA-based)

```python
def calculate_ema_momentum(prices, fast=12, slow=26):
    """
    Momentum basé sur la divergence des EMAs.
    """
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    
    # Momentum = distance entre EMAs (normalisée)
    momentum = (ema_fast - ema_slow) / ema_slow
    
    return momentum, ema_fast, ema_slow
```

### 3.3 Momentum Risk-Adjusted

```python
def calculate_risk_adjusted_momentum(prices, lookback=60):
    """
    Momentum ajusté pour le risque (Sharpe-like).
    """
    returns = prices.pct_change()
    
    rolling_mean = returns.rolling(lookback).mean()
    rolling_std = returns.rolling(lookback).std()
    
    # Risk-adjusted momentum
    ram = rolling_mean / rolling_std * np.sqrt(252)
    
    return ram
```

---

## 4. Le Bug Momentum "de la Nuit"

### 4.1 Problème: Overnight Gap

**Situation:**
```
Jour J:   Close = 100
Jour J+1: Open = 105, Close = 103

Momentum traditionnel: (103 - 100) / 100 = +3%
Mais: Overnight gap = (105 - 100) / 100 = +5%
      Intraday = (103 - 105) / 105 = -1.9%
```

**Problème:** Le momentum calcule le return Close-to-Close, mais:
- En Crypto: Trading 24/7, moins de gaps
- En Metals/Actions: Gaps overnight significatifs

### 4.2 Solution: Momentum Intraday vs Overnight

```python
def decompose_momentum(open_prices, close_prices, lookback=20):
    """
    Décompose le momentum en composantes overnight et intraday.
    """
    
    # Returns overnight (Close → Open suivant)
    overnight_returns = (open_prices - close_prices.shift(1)) / close_prices.shift(1)
    
    # Returns intraday (Open → Close)
    intraday_returns = (close_prices - open_prices) / open_prices
    
    # Momentum total
    total_returns = close_prices.pct_change(lookback)
    
    # Momentum components (rolling sum)
    mom_overnight = overnight_returns.rolling(lookback).sum()
    mom_intraday = intraday_returns.rolling(lookback).sum()
    
    return {
        'total': total_returns,
        'overnight': mom_overnight,
        'intraday': mom_intraday
    }
```

### 4.3 Correction du Bug

```python
# ❌ MAUVAIS: Utilise close-to-close avec gaps
def momentum_bug(close_prices, lookback=20):
    return close_prices.pct_change(lookback)

# ✅ BON: Utilise open-to-open ou adjust pour gaps
def momentum_corrected(open_prices, close_prices, lookback=20):
    """
    Momentum corrigé: utilise open-to-open pour éviter les gaps.
    """
    # Option 1: Open-to-open momentum
    mom_open = open_prices.pct_change(lookback)
    
    # Option 2: Close-to-close avec pondération
    mom_close = close_prices.pct_change(lookback)
    
    # Option 3: Combiné (recommandé)
    # Privilégie intraday si volume élevé
    volume_avg = df['volume'].rolling(lookback).mean()
    volume_current = df['volume']
    
    # Poids sur intraday si volume > moyenne
    weight = np.clip(volume_current / volume_avg, 0, 1)
    
    mom_combined = weight * mom_open + (1 - weight) * mom_close
    
    return mom_combined
```

---

## 5. Breakout Detection

### 5.1 Types de Breakouts

| Type | Description | Fiabilité |
|------|-------------|-----------|
| Range breakout | Sortie d'un range consolidé | Moyenne |
| ATH breakout | Nouveau plus haut historique | Élevée |
| Moving Average breakout | Crossing MA clé (50, 200) | Moyenne |
| Volume breakout | Spike de volume + prix | Élevée |
| Volatility breakout | Expansion vol + direction | Moyenne |

### 5.2 Détection de Breakout

```python
def detect_breakout(prices, high, low, volume, lookback=20, vol_threshold=1.5):
    """
    Détecte les breakouts avec confirmation volume.
    
    Returns:
    - breakout_signal: 1 = breakout haussier, -1 = baissier, 0 = aucun
    - breakout_strength: Force du breakout (0-1)
    - volume_confirmed: True si volume confirme
    """
    
    # Resistance et Support (plus haut/plus bas sur lookback)
    resistance = high.rolling(lookback).max()
    support = low.rolling(lookback).min()
    
    # Prix actuel
    current_price = prices.iloc[-1]
    prev_price = prices.iloc[-2]
    
    # Volume
    current_volume = volume.iloc[-1]
    avg_volume = volume.rolling(lookback).mean().iloc[-1]
    volume_ratio = current_volume / avg_volume
    
    # Breakout detection
    breakout_signal = 0
    breakout_strength = 0
    
    # Breakout haussier
    if current_price > resistance.iloc[-1] and prev_price <= resistance.iloc[-2]:
        breakout_signal = 1
        # Force = distance au-dessus de la résistance
        breakout_strength = (current_price - resistance.iloc[-1]) / resistance.iloc[-1]
    
    # Breakout baissier
    elif current_price < support.iloc[-1] and prev_price >= support.iloc[-2]:
        breakout_signal = -1
        breakout_strength = abs((current_price - support.iloc[-1]) / support.iloc[-1])
    
    # Volume confirmation
    volume_confirmed = volume_ratio >= vol_threshold
    
    return {
        'signal': breakout_signal,
        'strength': min(1.0, breakout_strength * 10),  # Normalisé 0-1
        'volume_confirmed': volume_confirmed,
        'volume_ratio': volume_ratio,
        'resistance': resistance.iloc[-1],
        'support': support.iloc[-1]
    }
```

### 5.3 Vrai Breakout vs Fakeout

```python
def classify_breakout(prices, volume, breakout_info, hold_period=3):
    """
    Classe un breakout comme vrai ou fakeout après hold_period.
    
    Un vrai breakout:
    - Prix reste au-dessus (pour bullish) après hold_period
    - Volume reste élevé
    - Pullback limité (< 50% du breakout)
    """
    
    signal = breakout_info['signal']
    entry_price = prices.iloc[0]
    
    if hold_period >= len(prices):
        return 'pending'
    
    exit_price = prices.iloc[hold_period]
    
    if signal == 1:  # Bullish breakout
        # Prix reste au-dessus du niveau de breakout
        if exit_price > entry_price * 0.98:  # Max -2%
            if breakout_info['volume_confirmed']:
                return 'true_breakout'
            else:
                return 'weak_breakout'
        else:
            return 'fakeout'
    
    elif signal == -1:  # Bearish breakout
        if exit_price < entry_price * 1.02:  # Max +2%
            if breakout_info['volume_confirmed']:
                return 'true_breakout'
            else:
                return 'weak_breakout'
        else:
            return 'fakeout'
    
    return 'unknown'
```

---

## 6. Volume Confirmation

### 6.1 Metrics de Volume

```python
def calculate_volume_metrics(volume, prices, lookback=20):
    """
    Calcule les metrics de volume pour confirmation.
    """
    
    # Volume ratio (vs moyenne)
    volume_ma = volume.rolling(lookback).mean()
    volume_ratio = volume / volume_ma
    
    # OBV (On-Balance Volume)
    direction = np.sign(prices.diff())
    obv = (direction * volume).cumsum()
    
    # Volume-weighted momentum
    returns = prices.pct_change()
    vw_momentum = (returns * volume).rolling(lookback).sum() / volume.rolling(lookback).sum()
    
    # Accumulation/Distribution
    typical_price = (prices['high'] + prices['low'] + prices['close']) / 3
    adl = ((typical_price - prices['low']) - (prices['high'] - typical_price)) / (prices['high'] - prices['low'])
    adl = (adl * volume).cumsum()
    
    return {
        'volume_ratio': volume_ratio,
        'obv': obv,
        'vw_momentum': vw_momentum,
        'adl': adl
    }
```

### 6.2 Volume Profile

```python
def calculate_volume_profile(prices, volume, n_bins=20):
    """
    Calcule le volume profile par niveau de prix.
    Identifie les zones de haute concentration (support/resistance).
    """
    
    # Discrétiser les prix en bins
    price_min = prices.min()
    price_max = prices.max()
    bins = np.linspace(price_min, price_max, n_bins + 1)
    
    # Volume par bin
    volume_profile = np.zeros(n_bins)
    for i in range(n_bins):
        mask = (prices >= bins[i]) & (prices < bins[i+1])
        volume_profile[i] = volume[mask].sum()
    
    # Normaliser
    volume_profile = volume_profile / volume_profile.sum()
    
    # Point de contrôle (Price with highest volume)
    poc_idx = np.argmax(volume_profile)
    poc_price = (bins[poc_idx] + bins[poc_idx+1]) / 2
    
    return {
        'bins': bins,
        'volume_profile': volume_profile,
        'poc': poc_price,
        'high_volume_nodes': bins[:-1][volume_profile > volume_profile.mean() * 1.5]
    }
```

---

## 7. Stratégie Momentum + Breakout

### 7.1 Signal Composite

```python
def composite_momentum_signal(prices, volume, high, low, lookback=20):
    """
    Signal composite combinant momentum, breakout, et volume.
    """
    
    # 1. Momentum score (0-1)
    mom = prices.pct_change(lookback)
    mom_score = (mom - mom.rolling(252).min()) / (mom.rolling(252).max() - mom.rolling(252).min())
    
    # 2. Breakout detection
    breakout = detect_breakout(prices, high, low, volume, lookback)
    breakout_score = breakout['strength'] if breakout['signal'] > 0 else 0
    
    # 3. Volume confirmation
    vol_metrics = calculate_volume_metrics(volume, prices, lookback)
    vol_score = np.clip(vol_metrics['volume_ratio'].iloc[-1] / 2, 0, 1)  # Normalisé 0-1
    
    # 4. Signal composite (pondéré)
    signal = 0.4 * mom_score.iloc[-1] + 0.4 * breakout_score + 0.2 * vol_score
    
    return {
        'composite_signal': signal,
        'momentum_score': mom_score.iloc[-1],
        'breakout_score': breakout_score,
        'volume_score': vol_score,
        'breakout_info': breakout
    }
```

### 7.2 Backtest Comparatif Crypto vs Metals

```python
def backtest_momentum_strategy(prices, volume, high, low, 
                               lookback=20, rebalance_freq=5):
    """
    Backtest d'une stratégie momentum + breakout.
    """
    
    n_obs = len(prices)
    positions = np.zeros(n_obs)
    
    current_position = 0
    
    for i in range(lookback, n_obs - 1, rebalance_freq):
        # Signal
        signal_data = composite_momentum_signal(
            prices.iloc[:i+1],
            volume.iloc[:i+1],
            high.iloc[:i+1],
            low.iloc[:i+1],
            lookback
        )
        
        signal = signal_data['composite_signal']
        
        # Entry/Exit rules
        if signal > 0.6 and current_position == 0:
            # Entry long
            positions[i:i+rebalance_freq] = 1
            current_position = 1
        
        elif signal < 0.3 and current_position == 1:
            # Exit long
            positions[i:i+rebalance_freq] = 0
            current_position = 0
        
        else:
            # Hold
            positions[i:i+rebalance_freq] = current_position
    
    # Returns
    returns = prices.pct_change()
    strategy_returns = positions[:-1] * returns[1:]
    
    # Métriques
    cumulative = (1 + pd.Series(strategy_returns)).cumprod()
    total_return = cumulative.iloc[-1] - 1
    sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252) if strategy_returns.std() > 0 else 0
    max_dd = (cumulative / cumulative.cummax() - 1).min()
    
    return {
        'total_return': total_return,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'cumulative': cumulative,
        'positions': positions,
        'strategy_returns': strategy_returns
    }
```

### 7.3 Résultats Attendus

| Asset Class | Total Return (ann.) | Sharpe | Max DD | Win Rate |
|-------------|---------------------|--------|--------|----------|
| Crypto (BTC) | 40-80% | 0.8-1.2 | -25% | 52-55% |
| Crypto (ETH) | 50-100% | 0.7-1.0 | -30% | 50-53% |
| Gold | 8-15% | 0.5-0.8 | -12% | 48-52% |
| Silver | 10-20% | 0.4-0.7 | -18% | 47-51% |
| Copper | 12-25% | 0.6-0.9 | -15% | 50-54% |

**Observations:**
- Crypto: Momentum plus fort mais plus volatil
- Metals: Momentum plus stable, moins de fakeouts
- Volume confirmation réduit les fakeouts de ~30%

---

## 8. Code Sample

Voir `learning/code/momentum_breakout.py` pour l'implémentation complète.

**Fonctionnalités:**
- Calcul momentum (simple, EMA, risk-adjusted)
- Détection breakout avec volume confirmation
- Classification vrai breakout vs fakeout
- Backtest comparatif Crypto vs Metals
- Visualisations complètes

---

## 9. Best Practices

### ✅ DO

1. **Utiliser volume confirmation** pour filtrer les fakeouts
2. **Attendre la confirmation** (clôture au-dessus, pas juste wick)
3. **Ajuster lookback** selon l'asset (court pour crypto, long pour metals)
4. **Gérer les gaps** overnight correctement
5. **Stop-loss** sous le niveau de breakout

### ❌ DON'T

1. **Trader les breakouts sans volume** (taux d'échec élevé)
2. **Entry trop tôt** (avant la confirmation)
3. **Ignorer le contexte** (breakout contre trend = risqué)
4. **Over-leverage** sur crypto (volatilité extrême)
5. **Oublier les frais** (trading fréquent = costs élevés)

---

## 10. Prochaines Étapes

- [x] Momentum & Breakouts documenté
- [ ] Semaine 15: HMM Deep Dive (mise à jour du fichier existant)
- [ ] Semaine 16: Multi-Factor Models
- [ ] Synthèse et projet final

---

**Références:**
- Jegadeesh, N., Titman, S. (1993). "Returns to Buying Winners and Selling Losers"
- Moskowitz, T.J., Ooi, Y.H., Pedersen, L.H. (2012). "Time Series Momentum"
- Asness, C.S., Moskowitz, T.J., Pedersen, L.H. (2013). "Value and Momentum Everywhere"
- Bulkowski, T.N. (2005). "Encyclopedia of Chart Patterns"
