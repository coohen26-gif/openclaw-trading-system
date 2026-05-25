# 🌙 Recherche Nocturne - 21 Mai 2026

**Session:** cron:b62d7344-5b4c-49b6-aedc-e5523dcfe7c8  
**Heure:** 01:00 UTC  
**Agent:** Bonjour 👋

---

## 1️⃣ NOUVELLES STRATÉGIES DE TRADING

### 📊 Mean Reversion - État de l'Art 2025-2026

**Évolution majeure:** On passe de la réversion "naïve" (RSI < 30 → achat) à la **modélisation stochastique avancée**.

#### Techniques Clés Découvertes:

**a) Processus d'Ornstein-Uhlenbeck (OU) avec θ dynamique**
- Modélise la VITESSE de réversion, pas juste son occurrence
- Paramètre θ (theta) = demi-vie de réversion, calculé par MLE sur fenêtre glissante (60 jours)
- **Règle:** Trader seulement quand θ > 2σ au-dessus de sa moyenne mobile 100j
- θ rising = réversion rapide → entries haute fréquence
- θ falling = régime trending → éviter la réversion

**b) Cointégration de Paires - Niveau Supérieur**
- Test de cointégration de Johansen pour identifier MULTIPLES vecteurs cointégrant
- Basket de 4-6 equities corrélées → eigenvector avec meilleur score de stationnarité
- **Normalisation dynamique:** z-score avec médiane glissante + MAD (Median Absolute Deviation) au lieu de mean/std
- Résiste aux outliers (flash crashes)
- Entry: z-score > 2.5 MAD, Exit: z-score = 0

**c) Décomposition Multi-Fréquence (EMD + Hilbert)**
- Empirical Mode Decomposition sépare le prix en "Intrinsic Mode Functions" (IMFs)
- HF IMF (1-3 bars) → scalping
- MF IMF (5-15 bars) → swing reversion
- Entry quand phase Hilbert croise π (peak) ou 0 (trough) + amplitude > 1σ
- Évite le noise, capture les reversions cycliques propres

**d) Filtres Macro Avancés**
- Yield Curve slope (10Y-2Y): Long reversion seulement si > -50bps
- VIX Term Structure: 
  - Short reversion désactivé si VIX curve inversée (spot > futures) = panique
  - Long reversion seulement si VIX futures en contango

---

### 🚀 Momentum & Breakouts - Hybridation

**Dual-Regime Adaptive System** (découvert sur FMZ.com):
- Combine RSI mean-reversion ET breakout dans un seul système
- Utilise ADX pour détecter le régime:
  - ADX < 25 → régime mean-reversion (RSI bands)
  - ADX > 25 → régime momentum (breakout sur ATR)
- **Innovation:** Les bandes de Bollinger deviennent dynamiques via filtre Kalman en régime high-vol

**Multi-Timeframe Breakout:**
- Entry sur breakout H1, confirmation H4, trend filter D1
- Volume-weighted breakout: breakout valide seulement si volume > 1.5x moyenne 20périodes
- "False breakout detection" via order flow imbalance

---

## 2️⃣ VEILLE TECHNOLOGIQUE

### 🧠 Machine Learning & HMM

**Hidden Markov Models - Applications 2025:**

1. **Détection de Régimes de Marché**
   - 2 états typiques: "Low Vol Reversion" vs "High Vol Momentum"
   - Training sur barres 5-min avec features: (close-to-close return, ATR/close)
   - Une fois le régime détecté → switch de stratégie automatique

2. **HMM + Random Forest Spécialisés** (QuantInsti)
   - HMM détecte le régime du jour
   - DEUX modèles RF entraînés séparément:
     - RF_0 → expert régime low-vol
     - RF_1 → expert régime high-vol
   - Prediction: HMM prédit le régime de demain → on utilise le RF correspondant
   - **Résultat rapporté:** 71.5% win rate sur 530 assets (Medium - InvestMuse)

3. **HMM + Reinforcement Learning** (IEEE IDS 2025)
   - HMM pour regime detection
   - RL (PPO) pour portfolio allocation dans chaque régime
   - Paper: "HMM-Based Market Regime Detection with RL for Portfolio Management"

4. **HMM + Neural Networks** (arXiv 2024-2025)
   - "AI-Powered Energy Algorithmic Trading: Integrating HMM with Neural Networks"
   - HMM pour regime switching, NN pour prediction intra-régime
   - Architecture hybride surpasse les modèles purs

---

### 🔄 Walk-Forward Optimization (WFO)

**Pourquoi c'est crucial:**
- Les stratégies échouent car trop rigides
- WFO = backtesting qui se ré-entraîne continuellement sur données récentes
- Fenêtre glissante: 4 ans de training, test sur période suivante, puis on avance

**Implémentation typique:**
```
[Train: J-1460 à J-1] → [Test: J à J+90] → shift → [Train: J-1459 à J] → ...
```

**Avantages:**
- Capture l'évolution des régimes de marché
- Évite l'overfitting sur une période fixe
- Plus réaliste que train/test split statique

---

### 📚 Papers & Recherches Récentes

1. **MM-DREX** (arXiv 2509.05080): "Multimodal-Driven Dynamic Routing of LLM Experts for Financial Trading"
   - Route dynamiquement vers différents experts LLM selon le contexte marché
   - Multimodal: prix + news + sentiment + macro

2. **Regime-Switching Portfolio** (GitHub - donarduka)
   - HMM + mean-variance optimization + volatility targeting
   - Rolling OOS backtest intégré

3. **MarketRegimeTrader** (GitHub - 0x596173736972)
   - HMM + Topological Data Analysis (TDA)
   - Génération automatique de stratégies
   - Backtesting réaliste avec gestion de risque robuste

---

## 3️⃣ ANALYSE CONCURRENTS - BOTS OPEN SOURCE

### 🏆 Leaders du Marché

| Bot | Stars | Langage | Features Clés |
|-----|-------|---------|---------------|
| **Freqtrade** | 49.7k | Python | Backtesting, FreqAI (ML), Telegram, WebUI, 10+ exchanges |
| **OpenAlice** | 4.0k | TypeScript | AI full-lifecycle, Trading-as-Git, Multi-broker UTA, MCP |
| **Lumibot** | 1.6k | Python | AI agents, SEC filings, macro data, backtestable |
| **OpenTrader** | 2.4k | TypeScript | DCA & GRID, UI, crypto-only |
| **Jesse** | ~5k | Python | Advanced crypto bot, backtesting focus |

---

### 🔍 Analyse Détaillée

**Freqtrade (Le Géant):**
- ✅ Mature, énorme communauté, documentation excellente
- ✅ FreqAI: adaptive ML qui self-train au marché
- ✅ Hyperopt: optimization de stratégies par ML
- ✅ 10+ exchanges supportés (Binance, Bybit, Kraken, Hyperliquid DEX...)
- ❌ Crypto-only
- ❌ Complexe pour débutants

**OpenAlice (Le Challenger AI-First):**
- ✅ "Trading-as-Git": stage orders, commit, push to execute → versioning complet
- ✅ Couvre TOUT: equities, crypto, commodities, forex, macro
- ✅ Guard pipeline: safety checks pre-execution (max position, cooldown, whitelist)
- ✅ Account snapshots avec equity curve
- ✅ MCP server pour exposition des tools à agents externes
- ✅ Evolution mode: permission escalation pour auto-modification
- ❌ Encore expérimental (breaking changes fréquentes)
- ❌ Plus jeune, moins de communauté

**Lumibot (Le Data-Rich):**
- ✅ SEC filings intégrés
- ✅ Macro data
- ✅ Multi-asset: stocks, options, crypto, futures, forex
- ✅ Backtestable AI agents
- ❌ Moins mature que Freqtrade

**Swarm-Trader (Le Multi-Agent):**
- ✅ Agents LLM spécialisés style "Buffett, Munger, Burry"
- ✅ Data sources gratuites (SEC EDGAR + yfinance)
- ✅ Intégration Alpaca
- ❌ Petit projet (34 stars)

---

### 📋 Features Manquantes dans NOTRE Système (Gap Analysis)

Après analyse, voici ce que les concurrents font et que nous n'avons pas:

1. **Versioning des trades** (OpenAlice: Trading-as-Git)
2. **Multi-regime detection automatique** (Freqtrade FreqAI, MarketRegimeTrader)
3. **Walk-forward optimization intégré** (présent dans Freqtrade, Lumibot)
4. **Safety guards pre-execution** (OpenAlice guard pipeline)
5. **Equity curve visualization en temps réel** (OpenAlice, Freqtrade)
6. **MCP server exposure** (OpenAlice - pour interop avec autres agents)
7. **Multi-asset unifié** (OpenAlice, Lumibot - nous sommes crypto-focused?)

---

## 4️⃣ IDÉES D'AMÉLIORATION ORIGINALES POUR NOTRE SYSTÈME 🚀

### 💡 Idée #1: "Regime-Aware Strategy Router" (HMM + Ensemble Learning)

**Concept:**
Au lieu d'avoir UNE stratégie fixe, créer un **routeur intelligent** qui:
1. Utilise un HMM à 3 états entraîné en continu:
   - État 0: Low Vol / Mean-Reversion friendly
   - État 1: Trending / Momentum friendly  
   - État 2: High Vol / Chaos (stay flat ou réduire size)

2. **3 stratégies spécialisées** entraînées séparément:
   - Strat MR → optimisée pour état 0
   - Strat Momentum → optimisée pour état 1
   - Strat Defensive → pour état 2

3. Le HMM prédit l'état de demain → on active la stratégie correspondante

4. **Couche Ensemble:** Si probabilités HMM sont incertaines (ex: 40%/35%/25%), on fait une moyenne pondérée des signaux des 3 stratégies

**Implémentation:**
- HMM entraîné nightly sur données récentes (fenêtre glissante 90j)
- Walk-forward backtest pour valider le router
- Feature set: returns, ATR, VIX, volume, correlation matrix

**Pourquoi c'est original:**
- La plupart des bots ont UNE stratégie
- FreqAI fait du ML adaptatif mais pas du regime-switching explicite
- OpenAlice a des agents mais pas de détection de régime automatique

---

### 💡 Idée #2: "Shadow Mode Learning" + Auto-Correction

**Concept:**
Un système d'**apprentissage par l'erreur en temps réel**:

1. **Shadow Mode:** Chaque trade exécuté est dupliqué en "shadow" avec des paramètres légèrement perturbés (±5% sur les thresholds, ±10% sur position size)

2. **Contre-factuel:** On track ce qui se serait passé avec ces paramètres alternatifs

3. **Auto-Correction:** Après N trades (ex: 50), on analyse:
   - Quelle variante aurait eu le meilleur Sharpe?
   - Quel paramètre aurait évité tel drawdown?

4. **Adjustment Loop:** Les paramètres de la stratégie principale sont ajustés automatiquement vers la variante "shadow" la plus performante, avec un taux d'apprentissage (ex: 10% du delta)

**Features additionnelles:**
- "Ghost Trades": trades qu'on aurait pris si la stratégie avait été légèrement différente → learning signal
- "Regret Minimization": si on rate un trade profitable, on analyse pourquoi et on ajuste le threshold
- **Explainability:** Chaque adjustment est loggué avec la raison ("augmente RSI threshold car 3 trades perdants sur false signals")

**Pourquoi c'est original:**
- Aucun bot open source fait du shadow learning en temps réel
- Freqtrade hyperopt est offline, pas online learning
- Ça transforme chaque trade en donnée d'entraînement

---

### 💡 Idée #3: "Cross-Bot Signal Aggregation" (Swarm Intelligence)

**Concept:**
Notre bot se connecte en **lecture seule** aux signaux publics d'autres bots/communautés et les utilise comme features:

1. **Signal Aggregation Layer:**
   - Récupère les signaux publics de: Freqtrade strategies (via API), TradingView ideas, Twitter sentiment, Reddit r/algotrading
   - Normalise chaque signal en score [-1, +1]

2. **Meta-Model:**
   - Un modèle léger (Logistic Regression ou petit XGBoost) apprend à pondérer ces signaux externes
   - Features: [notre_signal, freqtrade_consensus, tradingview_momentum, twitter_sentiment, ...]
   - Target: price movement à N bars

3. **Confidence Boosting:**
   - Si notre signal = LONG et 80% des sources externes = LONG → on augmente la position size de 20%
   - Si notre signal = LONG mais 70% externes = SHORT → on réduit size de 50% ou on skip

4. **Contrarian Mode (optionnel):**
   - Quand le consensus externe est EXTREME (>90% bullish), on active un mode contrarian
   - Basé sur le principe: "quand tout le monde est positionné pareil, le reversal est proche"

**Implémentation:**
- Web scraping TradingView (public ideas)
- Twitter API pour sentiment sur $BTC, $ETH, etc.
- Freqtrade n'a pas d'API publique de signaux, mais on peut scraper les strategies partagées sur leur forum
- RSS feeds de blogs quant (QuantInsti, etc.)

**Pourquoi c'est original:**
- Aucun bot open source fait de "swarm intelligence" cross-platform
- OpenAlice a des agents multiples mais pas de consensus externe
- Transforme le bruit social en signal structuré

---

## 📝 NOTES PERSONNELLES

**À explorer plus tard:**
- Ornstein-Uhlenbeck θ calculation en Python (MLE estimation)
- Johansen cointegration test (lib: `statsmodels` ou `coint`)
- Empirical Mode Decomposition + Hilbert Transform (lib: `PyEMD`)
- Kalman Filter pour Bollinger Bands dynamiques

**Repos GitHub à étudier:**
- `donarduka/regime-switching-portfolio`
- `0x596173736972/MarketRegimeTrader` (HMM + TDA!)
- `Sakeeb91/market-regime-detection`

**Papers à lire:**
- MM-DREX (arXiv 2509.05080)
- "HMM-Based Market Regime Detection with RL for Portfolio Management" (IEEE IDS 2025)
- "AI-Powered Energy Algorithmic Trading: Integrating HMM with Neural Networks" (arXiv 2407.19858)

---

**Prochaine session nocturne:** Prototyper l'Idée #1 (Regime-Aware Router) avec données historiques BTC/ETH.

---

*Fin de session - 01:47 UTC*
