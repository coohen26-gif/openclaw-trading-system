# Semaine 09 - Feature Engineering pour le Trading

**Date:** 24 mai 2026  
**Module:** Master 2 - ML pour Trading  
**Statut:** ✅ Complet

---

## 1. Objectif du Module

Le feature engineering est **l'étape la plus critique** dans un pipeline de ML pour le trading. La qualité des features détermine le plafond de performance de n'importe quel modèle, aussi sophistiqué soit-il.

**Objectifs:**
- Construire des features informatives et non-redondantes
- Éviter le look-ahead bias et data leakage
- Comprendre l'importance relative des features (SHAP, permutation)
- Adapter les features à l'asset class (Crypto vs Metals vs Forex)

---

## 2. Technical Features (Price-Based)

### 2.1 Indicateurs de Momentum

#### RSI (Relative Strength Index)

```python
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
```

**Interprétation:**
- RSI > 70: Surachat (potentiel reversal baissier)
- RSI < 30: Survente (potentiel reversal haussier)
- **Pour ML:** Utiliser comme feature continue, pas comme signal binaire

#### MACD (Moving Average Convergence Divergence)

```python
def calculate_macd(prices, fast=12, slow=26, signal=9):
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram
```

**Features dérivées:**
- `macd_line`: Valeur brute
- `macd_histogram`: Distance à la signal line
- `macd_cross`: Signal de croisement (binaire)
- `macd_divergence`: Divergence prix/MACD (avancé)

#### ATR (Average True Range)

```python
def calculate_atr(high, low, close, period=14):
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    return atr
```

**Usage:**
- Normalisation des stops (stop = entry ± k × ATR)
- Feature de volatilité pour le modèle
- Position sizing adaptatif

### 2.2 Bandes de Bollinger

```python
def calculate_bollinger_bands(prices, period=20, std_dev=2):
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    pct_b = (prices - lower) / (upper - lower)  # Position relative dans les bandes
    bandwidth = (upper - lower) / sma  # Largeur relative
    return upper, lower, pct_b, bandwidth
```

**Features:**
- `bb_pct_b`: Position dans les bandes (0-1)
- `bb_bandwidth`: Compression/expansion de la volatilité
- `bb_squeeze`: Bandwidth < seuil (signal de breakout imminent)

### 2.3 Features de Trend

```python
def calculate_trend_features(prices):
    # Pentes de MAs
    ma_20 = prices.rolling(20).mean()
    ma_50 = prices.rolling(50).mean()
    ma_200 = prices.rolling(200).mean()
    
    # Pentes (dérivées)
    ma_20_slope = ma_20.diff(5) / ma_20.shift(5)
    ma_50_slope = ma_50.diff(5) / ma_50.shift(5)
    
    # Alignement des MAs (trend strength)
    ma_alignment = (ma_20 > ma_50) & (ma_50 > ma_200)  # Bullish
    
    # Distance aux MAs
    dist_ma_20 = (prices - ma_20) / ma_20
    dist_ma_200 = (prices - ma_200) / ma_200
    
    return ma_20_slope, ma_50_slope, ma_alignment, dist_ma_20, dist_ma_200
```

---

## 3. Statistical Features (Rolling Windows)

### 3.1 Returns et Volatilité

```python
def calculate_statistical_features(prices, windows=[5, 10, 20, 60]):
    features = pd.DataFrame(index=prices.index)
    
    for w in windows:
        # Returns
        returns = prices.pct_change()
        features[f'return_{w}d'] = returns.rolling(w).mean()
        
        # Volatilité
        features[f'vol_{w}d'] = returns.rolling(w).std() * np.sqrt(252)  # Annualisée
        
        # Skewness (asymétrie)
        features[f'skew_{w}d'] = returns.rolling(w).skew()
        
        # Kurtosis (fat tails)
        features[f'kurt_{w}d'] = returns.rolling(w).kurt()
        
        # Sharpe ratio rolling
        features[f'sharpe_{w}d'] = features[f'return_{w}d'] / features[f'vol_{w}d']
    
    return features
```

**Interprétation:**
- **Skewness négative:** Risque de crash (queue gauche épaisse)
- **Kurtosis élevé:** Fat tails, événements extrêmes plus probables
- **Sharpe rolling:** Performance risk-adjusted dynamique

### 3.2 Autocorrélation et Mean Reversion

```python
def calculate_mean_reversion_features(prices, lags=[1, 5, 10]):
    returns = prices.pct_change()
    features = pd.DataFrame(index=prices.index)
    
    for lag in lags:
        # Autocorrélation des returns
        features[f'acf_lag{lag}'] = returns.rolling(60).apply(
            lambda x: x.autocorr(lag=lag) if len(x) > lag else np.nan
        )
        
        # Hurst exponent (rolling)
        features[f'hurst_{lag}d'] = returns.rolling(lag).apply(
            lambda x: calculate_hurst(x) if len(x) > 10 else np.nan
        )
    
    return features

def calculate_hurst(series):
    """Hurst exponent: H < 0.5 = mean-reverting, H > 0.5 = trending"""
    lags = range(2, 20)
    tau = [np.sqrt(np.std(np.subtract(series[lag:], series[:-lag]))) for lag in lags]
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return poly[0]
```

**Interprétation:**
- **H < 0.5:** Série mean-reverting (stratégies de range trading)
- **H ≈ 0.5:** Random walk
- **H > 0.5:** Série trending (stratégies momentum)

---

## 4. On-Chain Features (Crypto-Specific)

### 4.1 Flux et Volumes

| Feature | Description | Source |
|---------|-------------|--------|
| `exchange_inflow` | BTC entrant sur les exchanges (vente potentielle) | Glassnode |
| `exchange_outflow` | BTC sortant des exchanges (accumulation) | Glassnode |
| `net_flow` | Inflow - Outflow | Calculé |
| `whale_transactions` | Transactions > $100k | Whale Alert API |
| `active_addresses` | Adresses actives quotidiennes | Glassnode |
| `transaction_volume` | Volume on-chain total | Blockchain API |

### 4.2 Funding Rates et Sentiment

```python
def calculate_funding_features(funding_rates, open_interest):
    features = pd.DataFrame(index=funding_rates.index)
    
    # Funding rate brut
    features['funding_rate'] = funding_rates
    
    # Funding rate annualisé
    features['funding_annual'] = funding_rates * 3 * 365  # 3 funding/day
    
    # Open Interest
    features['open_interest'] = open_interest
    
    # OI × Funding (leveraged positioning)
    features['oi_funding_product'] = open_interest * funding_rates
    
    # Changement d'OI
    features['oi_change'] = open_interest.pct_change()
    
    return features
```

**Interprétation:**
- **Funding positif élevé:** Longs dominants, risque de long squeeze
- **Funding négatif élevé:** Courts dominants, risque de short squeeze
- **OI ↑ + Prix ↑:** Trend sain, nouvelle money
- **OI ↑ + Prix →:** Divergence, reversal possible

### 4.3 Metrics Avancées

| Feature | Formule/Description | Signal |
|---------|---------------------|--------|
| `MVRV_ratio` | Market Cap / Realized Cap | >3.5 = overvalued |
| `NUPL` | Net Unrealized Profit/Loss | >0.75 = euphoria |
| `SOPR` | Spent Output Profit Ratio | <1 = capitulation |
| `Reserve_Risk` | Price / (HODL Waves × Time) | Bas = opportunité |

---

## 5. Macro Features (Metals/Forex)

### 5.1 Taux et Inflation

| Feature | Description | Impact |
|---------|-------------|--------|
| `real_rates_10y` | Taux réel 10Y (nominal - inflation) | Or inversement corrélé |
| `tip_yield` | TIPS yield 10Y | Proxy real rates |
| `inflation_expectations` | Breakeven inflation 5Y5Y | Anticipations marché |
| `dxy` | Dollar Index | Or/Forex inversement corrélé |
| `credit_spread` | Spread corporate vs treasury | Risk-on/off |

### 5.2 Features Spécifiques Metals

```python
def calculate_metals_features(gold_prices, silver_prices, bond_yields):
    features = pd.DataFrame(index=gold_prices.index)
    
    # Gold/Silver ratio
    features['gold_silver_ratio'] = gold_prices / silver_prices
    
    # Real yields (inverse correlation with gold)
    features['real_yield_10y'] = bond_yields - inflation_expectations
    
    # Gold momentum vs real rates
    features['gold_momentum'] = gold_prices.pct_change(20)
    
    # Term spread (10Y-2Y)
    features['term_spread'] = bond_yields_10y - bond_yields_2y
    
    return features
```

---

## 6. Feature Importance et Sélection

### 6.1 Permutation Importance

```python
from sklearn.inspection import permutation_importance

def calculate_permutation_importance(model, X_test, y_test, n_repeats=10):
    """Mesure la baisse de performance quand on shuffle une feature"""
    result = permutation_importance(
        model, X_test, y_test,
        n_repeats=n_repeats,
        random_state=42,
        scoring='accuracy'  # ou 'f1', 'roc_auc'
    )
    
    importance_df = pd.DataFrame({
        'feature': X_test.columns,
        'importance_mean': result.importances_mean,
        'importance_std': result.importances_std
    }).sort_values('importance_mean', ascending=False)
    
    return importance_df
```

**Avantages:**
- Model-agnostic (fonctionne avec RF, XGBoost, etc.)
- Capture les interactions non-linéaires
- Interprétable directement

### 6.2 SHAP Values

```python
import shap

def calculate_shap_importance(model, X_train, X_test, feature_names):
    """SHAP: SHapley Additive exPlanations"""
    # Create explainer
    explainer = shap.TreeExplainer(model)  # Pour RF/XGBoost
    
    # Calculate SHAP values
    shap_values = explainer.shap_values(X_test)
    
    # Summary plot (importance + direction)
    shap.summary_plot(shap_values, X_test, feature_names=feature_names)
    
    # Mean absolute SHAP value per feature
    shap_importance = pd.DataFrame({
        'feature': feature_names,
        'shap_importance': np.abs(shap_values).mean(axis=0)
    }).sort_values('shap_importance', ascending=False)
    
    return shap_importance, shap_values
```

**Avantages SHAP vs Permutation:**
- Donne la **direction** de l'impact (positif/négatif)
- Valeurs cohérentes (somme = prediction)
- Visualisations riches (summary, dependence, force plots)

### 6.3 Feature Selection Strategy

```python
def select_features(X, y, method='recursive', n_features=20):
    """Sélection de features optimale"""
    
    if method == 'recursive':
        from sklearn.feature_selection import RFE
        from sklearn.ensemble import RandomForestClassifier
        
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        rfe = RFE(estimator=model, n_features_to_select=n_features, step=1)
        rfe.fit(X, y)
        
        selected = X.columns[rfe.support_]
        ranking = pd.DataFrame({
            'feature': X.columns,
            'ranking': rfe.ranking_
        }).sort_values('ranking')
        
    elif method == 'correlation':
        # Remove highly correlated features
        corr_matrix = X.corr().abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        to_drop = [column for column in upper.columns if any(upper[column] > 0.9)]
        selected = X.columns.difference(to_drop)
        ranking = None
    
    return selected, ranking
```

---

## 7. Best Practices et Pièges

### ✅ DO

1. **Normaliser les features** avant ML (StandardScaler, RobustScaler)
2. **Vérifier la stationnarité** des features (ADF test)
3. **Documenter chaque feature** (source, calcul, interprétation)
4. **Tester la robustesse** (stabilité dans le temps)
5. **Utiliser purged CV** pour évaluer l'importance (voir Semaine 12)

### ❌ DON'T

1. **Look-ahead bias:** Utiliser des données futures dans le calcul
2. **Data leakage:** Normaliser avant split train/test
3. **Overfitting:** Trop de features vs nombre d'observations
4. **Multicollinéarité:** Features fortement corrélées entre elles
5. **Cherry-picking:** Sélectionner les features sur le test set

### ⚠️ Points Critiques

```python
# ❌ MAUVAIS: Normalisation avant split
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)  # Fuite d'info du test vers train!
X_train, X_test = train_test_split(X_scaled, y)

# ✅ BON: Normalisation après split
X_train, X_test = train_test_split(X, y)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)  # Seulement transform!
```

---

## 8. Code Sample: Feature Engineering Pipeline

Voir `learning/code/feature_engineering.py` pour l'implémentation complète.

**Features générées:**
- 15 technical indicators (RSI, MACD, BB, ATR, etc.)
- 20 statistical features (returns, vol, skew, kurt sur multiples windows)
- 10 on-chain metrics (si données crypto disponibles)
- 8 macro features (si données Metals/Forex)

**Total:** ~50-60 features avant sélection

**Après sélection (SHAP + RFE):** 15-25 features les plus informatives

---

## 9. Prochaines Étapes

- [x] Feature engineering documenté
- [ ] Semaine 10: ML Supervised (RF, XGBoost, Logistic Regression)
- [ ] Implémenter le pipeline complet avec purged CV
- [ ] Backtest des signaux générés

---

**Références:**
- López de Prado, M. (2018). "Advances in Financial Machine Learning"
- Scikit-learn: Feature selection documentation
- SHAP documentation: https://shap.readthedocs.io/
- Glassnode Academy: On-chain metrics
