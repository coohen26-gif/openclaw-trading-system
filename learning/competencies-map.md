# 🗺️ Carte des Compétences - Quant Trader

**Objectif:** Liste EXACTE de ce que je dois apprendre + tester + sources de données

---

## 📚 **1. THÉORIE À APPRENDRE** (Connaissances)

### **A. Mathématiques & Statistiques** ⭐⭐⭐
| Concept | Pourquoi | Priorité |
|---------|----------|----------|
| Distributions (normale, Student, fat tails) | Comprendre les returns | P0 |
| Moments statistiques (mean, variance, skewness, kurtosis) | Caractériser les distributions | P0 |
| Tests de normalité (Shapiro-Wilk, Jarque-Bera) | Valider/modèles | P0 |
| Stationnarité (ADF test, cointégration) | Prérequis pour ARIMA | P0 |
| Autocorrélation (ACF, PACF) | Identifier modèles time-series | P1 |
| Processus stochastiques (Brownien, Itô) | Pricing options, théorie | P2 |

### **B. Séries Temporelles Financières** ⭐⭐⭐
| Modèle | Usage | Priorité |
|--------|-------|----------|
| ARIMA(p,d,q) | Prediction direction | P0 |
| GARCH(1,1) | Forecast volatilité | P0 |
| Ornstein-Uhlenbeck | Mean reversion (demi-vie) | P0 |
| Cointégration (Johansen) | Pairs trading | P1 |
| VAR/VECM | Multi-séries, correlations | P2 |

### **C. Machine Learning** ⭐⭐⭐
| Type | Modèles | Priorité |
|------|---------|----------|
| Supervised | Random Forest, XGBoost, Logistic Regression | P0 |
| Unsupervised | KMeans, DBSCAN, PCA | P1 |
| Deep Learning | LSTM, GRU, Transformers | P1 |
| Reinforcement | PPO, DQN (allocation dynamique) | P2 |
| Ensemble | Voting, stacking, blending | P0 |

### **D. Trading Spécifique** ⭐⭐⭐
| Concept | Pourquoi | Priorité |
|---------|----------|----------|
| Mean reversion | Stratégie principale | P0 |
| Momentum/Trend following | Stratégie secondaire | P0 |
| Market microstructure | Order book, spread, slippage | P0 |
| Risk management (VaR, ES, Kelly) | Survie > performance | P0 |
| Walk-forward validation | Éviter overfitting | P0 |
| Hidden Markov Models | Regime detection | P0 |
| Multi-factor models | Alpha diversification | P1 |

### **E. Finance de Marché** ⭐⭐
| Sujet | Pourquoi | Priorité |
|-------|----------|----------|
| Asset classes (crypto, Forex, indices, commodities) | Choisir où trader | P0 |
| Produits (spot, futures, options, perps) | Instruments disponibles | P1 |
| Macro economics (rates, inflation, GDP) | Drivers de marché | P1 |
| Portfolio theory (Markowitz, Efficient Frontier) | Allocation optimale | P2 |

---

## 🧪 **2. PRATIQUE À TESTER** (Compétences)

### **A. Analyses Statistiques de Base**
- [ ] Calculer returns (simples, log) sur différents TF
- [ ] Analyser distributions (histogrammes, Q-Q plots)
- [ ] Tester normalité (p-values, interprétation)
- [ ] Calculer volatilités (rolling, exponentielle)
- [ ] Détecter volatility clustering

### **B. Modélisation Time-Series**
- [ ] Implémenter ARIMA (identification p,d,q)
- [ ] Implémenter GARCH(1,1)
- [ ] Forecast volatilité à 1j, 1j+5
- [ ] Backtester forecasts vs realized vol

### **C. Stratégies de Trading**
- [ ] Mean reversion (RSI, BB, OU process)
- [ ] Momentum (breakouts, moving averages)
- [ ] Pairs trading (cointégration)
- [ ] Multi-timeframe analysis
- [ ] Regime-aware strategies (HMM)

### **D. Machine Learning Appliqué**
- [ ] Feature engineering (technical, on-chain, macro)
- [ ] Training/test split (purged, embargo)
- [ ] Walk-forward optimization
- [ ] Feature importance (SHAP, permutation)
- [ ] Model comparison (RF vs XGB vs LSTM)

### **E. Risk Management**
- [ ] Calculer VaR (historique, paramétrique, Monte Carlo)
- [ ] Calculer Expected Shortfall (CVaR)
- [ ] Position sizing (Kelly, fractional Kelly)
- [ ] Drawdown analysis (max, duration, recovery)
- [ ] Circuit breakers (stop trading après X losses)

### **F. Backtesting Rigoureux**
- [ ] Éviter look-ahead bias
- [ ] Éviter survivorship bias
- [ ] Inclure transaction costs (fees, slippage)
- [ ] Walk-forward (pas de k-fold simple)
- [ ] Out-of-sample testing

---

## 📊 **3. SOURCES DE DONNÉES** (Gratuites & Open Source)

### **A. Crypto** ✅ (Déjà configuré)
| Source | API | Données | Qualité |
|--------|-----|---------|---------|
| **Binance** | CCXT (Python) | OHLCV, trades, funding rates | ⭐⭐⭐ |
| **Coinbase** | API REST | OHLCV, order book | ⭐⭐⭐ |
| **Kraken** | API REST/WebSocket | OHLCV, trades | ⭐⭐⭐ |
| **Glassnode** | API (freemium) | On-chain metrics | ⭐⭐ |
| **CryptoQuant** | API (freemium) | Flows exchanges, miners | ⭐⭐ |

**Exemple Python:**
```python
import ccxt
exchange = ccxt.binance()
ohlcv = exchange.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=1000)
```

---

### **B. Forex** 🆓
| Source | API | Données | Qualité |
|--------|-----|---------|---------|
| **OANDA** | API REST (gratuit avec compte) | OHLCV, rates | ⭐⭐⭐ |
| **FXCM** | API REST (gratuit avec compte) | OHLCV, sentiment | ⭐⭐⭐ |
| **Dukascopy** | API (gratuit, pas de compte) | OHLCV historique | ⭐⭐⭐ |
| **Alpha Vantage** | API (freemium) | Forex, crypto, stocks | ⭐⭐ |
| **Exchangerate.host** | API (gratuit) | Rates historiques | ⭐⭐ |

**Exemple Python:**
```python
import oandapyV2
# ou
import dukascopy
data = dukascopy.get_data('EURUSD', timeframe='H1')
```

---

### **C. Indices US (NASDAQ, S&P500)** 🆓
| Source | API | Données | Qualité |
|--------|-----|---------|---------|
| **Yahoo Finance** | `yfinance` (Python) | OHLCV, dividends, splits | ⭐⭐⭐ |
| **Alpha Vantage** | API (freemium) | Indices, stocks | ⭐⭐ |
| **Polygon.io** | API (freemium) | Stocks, indices, options | ⭐⭐⭐ |
| **IEX Cloud** | API (payant) | Stocks, fundamentals | ⭐⭐ |

**Exemple Python:**
```python
import yfinance as yf
nasdaq = yf.Ticker('^NDX')
hist = nasdaq.history(period='1y', interval='1h')
```

---

### **D. Commodities (Or, Argent, Pétrole)** 🆓
| Source | API | Données | Qualité |
|--------|-----|---------|---------|
| **Yahoo Finance** | `yfinance` | XAU/USD, XAG/USD, CL (oil) | ⭐⭐⭐ |
| **Alpha Vantage** | API | Commodities | ⭐⭐ |
| **Quandl** | API (freemium) | Futures, commodities | ⭐⭐⭐ |
| **Metals-API** | API (freemium) | Precious metals | ⭐⭐ |

**Exemple Python:**
```python
import yfinance as yf
gold = yf.Ticker('GC=F')  # Gold futures
hist = gold.history(period='1y')
```

---

### **E. Macro Economics** 🆓
| Source | API | Données | Qualité |
|--------|-----|---------|---------|
| **FRED (St. Louis Fed)** | API (gratuit) | Rates, inflation, GDP, unemployment | ⭐⭐⭐ |
| **World Bank** | API (gratuit) | Macro global | ⭐⭐ |
| **IMF** | API (gratuit) | Macro global | ⭐⭐ |
| **Trading Economics** | API (freemium) | Macro + calendar | ⭐⭐ |

**Exemple Python:**
```python
import fredapi
fred = fredapi.Fred(api_key='YOUR_KEY')
rates = fred.get_series('DGS10')  # 10Y Treasury yield
```

---

### **F. Sentiment & News** 🆓
| Source | API | Données | Qualité |
|--------|-----|---------|---------|
| **Twitter API** | API (freemium) | Social sentiment | ⭐⭐ |
| **Reddit API** | `praw` (gratuit) | Social sentiment | ⭐⭐ |
| **NewsAPI** | API (freemium) | News headlines | ⭐⭐ |
| **CryptoPanic** | API (gratuit) | Crypto news aggregator | ⭐⭐ |

---

## 🛠️ **4. OUTILS & BIBLIOTHÈQUES PYTHON**

### **Core Stack**
```python
# Data manipulation
import pandas as pd
import numpy as np

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns
import plotly

# Statistics
from scipy import stats
from statsmodels.tsa.stattools import adfuller, acf, pacf
from arch import arch_model  # GARCH

# Machine Learning
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import walk_forward_validation

# Deep Learning
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

# Trading
import ccxt  # Crypto exchanges
import yfinance as yf  # Yahoo Finance
import backtrader  # Backtesting
import zipline  # Backtesting (Quantopian)

# HMM
from hmmlearn import hmm
```

---

## 🎯 **5. REPOS GITHUB À ÉTUDIER**

| Repo | Stars | Pourquoi |
|------|-------|----------|
| `je-suis-tm/quant-trading` | 10k+ | Stratégies Python complètes |
| `EliteQuant/EliteQuant` | 5k+ | Ressources curatées |
| `TradeMaster-NTU/TradeMaster` | 3k+ | Plateforme complète |
| `backtrader/backtrader` | 10k+ | Framework backtesting |
| `quantopian/zipline` | 15k+ | Backtesting (Quantopian legacy) |
| `pyquant/quant` | 2k+ | Outils quantitatifs |
| `hidden-regime/hidden-regime` | 3 | HMM pour trading |

---

## 📋 **6. CHECKLIST FINALE - Compétences Validées**

### **Niveau Licence (Semaine 1-4)**
- [ ] Comprendre distributions fat-tailed
- [ ] Tester stationnarité (ADF)
- [ ] Calculer autocorrélations
- [ ] Analyser volatility clustering

### **Niveau Master 1 (Semaine 5-8)**
- [ ] Implémenter ARIMA
- [ ] Implémenter GARCH
- [ ] Calculer VaR/Expected Shortfall
- [ ] Construire portfolio Markowitz
- [ ] Backtester stratégie simple

### **Niveau Master 2 (Semaine 9-16)**
- [ ] Feature engineering complet
- [ ] Random Forest + XGBoost
- [ ] LSTM pour time-series
- [ ] HMM regime detection
- [ ] Mean reversion (OU process)
- [ ] Pairs trading (cointégration)
- [ ] Walk-forward validation

### **Niveau Doctorat (Semaine 17-21)**
- [ ] Reinforcement Learning (PPO)
- [ ] LLM + signal fusion
- [ ] Multi-agent systems
- [ ] **Analyse comparative multi-asset**
- [ ] **Décision finale : Quelle asset class**
- [ ] **Système Saiyan complet**

---

## 🚀 **Prochaines Actions Immédiates**

1. **Cette nuit:**
   - [ ] Installer bibliothèques Python (statsmodels, arch, hmmlearn, ccxt, yfinance)
   - [ ] Récupérer données Forex (EUR/USD via Dukascopy)
   - [ ] Récupérer données NASDAQ (via yfinance)
   - [ ] Récupérer données Or (via yfinance)
   - [ ] Analyse comparative rapide (distributions, volatilités)

2. **Cette semaine:**
   - [ ] Backtester mean reversion sur chaque asset class
   - [ ] Backtester momentum sur chaque asset class
   - [ ] Comparer performance (Sharpe, max drawdown, WR)
   - [ ] **Recommandation finale**

---

**TL;DR:** J'ai besoin d'apprendre **stats + time-series + ML + trading**, de tester sur **crypto + Forex + indices + or**, avec des données **gratuites** (Binance, yfinance, Dukascopy, FRED).

**Objectif final:** Te dire **où trader** basé sur des backtests, pas sur des intuitions.
