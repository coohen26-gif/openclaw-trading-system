# 🎓 Parcours Académique Quant Trader - Goku

**Objectif:** Suivre le cursus complet d'un trader quantitatif, de la Licence au Master/Doctorat, puis formation continue.

**Début:** 2026-05-23
**Statut:** 📋 En attente de validation

---

## 📚 Structure du Parcours

### **Année 1-2: Licence Mathématiques/Économie**
_Fondamentaux théoriques_

#### Semestre 1-2: Mathématiques Fondamentales
- [ ] **Analyse:** Limites, continuité, dérivées, intégrales
- [ ] **Algèbre linéaire:** Matrices, vecteurs propres, décomposition
- [ ] **Probabilités de base:** Variables aléatoires, lois usuelles
- [ ] **Statistiques descriptives:** Moyenne, variance, corrélations

#### Semestre 3-4: Mathématiques Avancées
- [ ] **Analyse réelle:** Suites, séries, convergence
- [ ] **Probabilités avancées:** Lois conditionnelles, théorèmes limites
- [ ] **Statistiques inférentielles:** Tests d'hypothèses, intervalles de confiance
- [ ] **Introduction aux séries temporelles:** Autocorrélation, stationnarité

**Projets pratiques:**
- [ ] Analyser distributions de returns crypto (BTC, ETH, SOL)
- [ ] Calculer corrélations, volatilités historiques
- [ ] Tester stationnarité (ADF test) sur différentes paires

---

### **Année 3: Licence Pro / Master 1 - Finance Quantitative**
_Specialisation trading_

#### Semestre 5: Finance de Marché
- [ ] **Théorie moderne du portfolio:** Markowitz, CAPM, Efficient Frontier
- [ ] **Produits financiers:** Actions, obligations, options, futures
- [ ] **Microstructure des marchés:** Order book, spread, liquidité
- [ ] **Risk management basics:** VaR, Expected Shortfall, drawdown

#### Semestre 6: Modélisation Financière
- [ ] **Séries temporelles financières:** ARIMA, GARCH, cointégration
- [ ] **Processus stochastiques:** Mouvement brownien, Itô
- [ ] **Pricing d'options:** Black-Scholes, Greeks, volatilité implicite
- [ ] **Backtesting fundamentals:** Look-ahead bias, survivorship bias

**Projets pratiques:**
- [ ] Construire portfolio optimal (Markowitz) sur 10 cryptos
- [ ] Implémenter ARIMA pour prediction de prix
- [ ] Backtester une stratégie simple (RSI mean reversion)
- [ ] Calculer VaR historique et paramétrique

---

### **Année 4: Master 2 - Trading Algorithmique**
_Cœur du métier quant_

#### Semestre 7: Machine Learning pour Trading
- [ ] **Feature engineering:** Returns, ratios techniques, on-chain metrics
- [ ] **Supervised learning:** Regression, classification (Random Forest, XGBoost)
- [ ] **Unsupervised learning:** Clustering (KMeans, DBSCAN), PCA
- [ ] **Time-series ML:** LSTM, GRU, Transformers
- [ ] **Validation croisée:** Walk-forward, purged k-fold

#### Semestre 8: Stratégies Avancées
- [ ] **Mean reversion:** Ornstein-Uhlenbeck, pairs trading, cointégration
- [ ] **Momentum/Trend following:** Breakouts, moving averages, MACD
- [ ] **Market microstructure strategies:** Market making, arbitrage latence
- [ ] **Multi-factor models:** Fama-French crypto, momentum + value + quality
- [ ] **Regime detection:** Hidden Markov Models (HMM), change-point detection

**Projets pratiques:**
- [ ] Stratégie mean reversion avec OU process (demi-vie dynamique)
- [ ] Pairs trading sur cryptos corrélées (ETH/BTC, SOL/ETH)
- [ ] HMM à 3 états pour détection de régimes
- [ ] Modèle LSTM pour prediction de direction (5-15min)

---

### **Année 5: Doctorat / Recherche Appliquée**
_State-of-the-art 2026_

#### Thèmes de Recherche
- [ ] **Reinforcement Learning:** PPO, DQN pour allocation dynamique
- [ ] **LLM + Trading:** Signal fusion, regime labeling, sentiment analysis
- [ ] **Multi-agent systems:** Debate systems (Bull/Bear/Quant/Zen)
- [ ] **Adaptive strategies:** Meta-learning, strategy evolution
- [ ] **Risk-aware ML:** Conservative Q-learning, uncertainty quantification

**Thèse / Projet Final:**
- [ ] **Système Saiyan:** Architecture complète avec:
  - HMM regime detection (3-4 états)
  - Specialist models par régime
  - Momentum Fade Detector (edge contre-intuitif)
  - Multi-Universe personalities (P&L tracking)
  - Walk-forward optimization auto
  - Circuit breakers + dynamic position sizing

---

## 📖 Ressources par Niveau

### Licence (Années 1-2)
- **Livres:**
  - "Introduction to Probability" - Blitzstein & Hwang
  - "Linear Algebra Done Right" - Axler
  - "Statistics" - Freedman, Pisani, Purves
- **Cours en ligne:**
  - MIT OCW 18.05 (Probability)
  - Khan Academy (Linear Algebra)
  - Coursera: Statistics with Python (Michigan)

### Master 1 (Année 3)
- **Livres:**
  - "Options, Futures, and Other Derivatives" - Hull
  - "Active Portfolio Management" - Grinold & Kahn
  - "Expected Returns" - Ilmanen
- **Cours:**
  - Coursera: Financial Engineering (Columbia)
  - EDX: Finance Fundamentals (MIT)

### Master 2 (Année 4)
- **Livres:**
  - "Advances in Financial Machine Learning" - López de Prado ⭐
  - "Machine Learning for Algorithmic Trading" - Jansen
  - "Quantitative Trading" - Chan
- **Papers:**
  - "The 10 Commandments of Quantitative Trading" - López de Prado
  - "Advances in Financial ML" (chapitres sélectionnés)
- **GitHub:**
  - `je-suis-tm/quant-trading`
  - `EliteQuant/EliteQuant`
  - `TradeMaster-NTU/TradeMaster`

### Doctorat (Année 5)
- **Papers arXiv (q-fin.TR, cs.LG):**
  - Lecture quotidienne (5-10 papers/semaine)
- **Substacks:**
  - RegimeForecast
  - About Trading (Sofien Kaabar)
  - QuantInsti
- **Conférences:**
  - ICML, NeurIPS (tracks finance)
  - QuantCon, Battle of the Quants

---

## 🎯 Méthodologie d'Apprentissage

Pour chaque module:
1. **Théorie:** Lire cours/livres/papers (2-3h)
2. **Compréhension:** Résumer concepts clés dans `learning/notes/`
3. **Pratique:** Implémenter en Python (4-6h)
4. **Validation:** Backtester sur données réelles
5. **Documentation:** Écrire learnings dans `learning/journal.md`
6. **Integration:** Si concluant → intégrer au système Saiyan

---

## 📊 Suivi de Progression

| Niveau | Modules | Progression | Projet Clé | Statut |
|--------|---------|-------------|------------|--------|
| Licence 1-2 | 8 | 0/8 | Analyse distributions crypto | 📋 À faire |
| Licence 3 / M1 | 8 | 0/8 | Portfolio Markowitz + ARIMA | 📋 À faire |
| Master 2 | 10 | 0/10 | HMM + Mean Reversion OU | 📋 À faire |
| Doctorat | 5 | 0/5 | Système Saiyan complet | 📋 À faire |

---

## 🚀 Démarrage

**Première étape:** Licence 1 - Mathématiques Fondamentales

**Semaine 1 (2026-05-23 → 2026-05-30):**
- [ ] Réviser concepts: dérivées, intégrales, limites
- [ ] Exercices Python: numpy, scipy pour calculs
- [ ] Projet: Analyser distribution des returns BTC (daily, 1h, 5min)
- [ ] Journal: Écrire learnings dans `learning/journal.md`

---

## 📝 Notes Importantes

- **Rythme:** 10-15h/semaine (compatible avec développement système)
- **Validation:** Chaque module = projet pratique + backtest
- **Intégration:** Les concepts validés sont intégrés au système Saiyan
- **Transparence:** W peut checker progression à tout moment

---

_"Devenir un quant trader n'est pas un sprint, c'est un marathon. Mais avec la discipline Saiyan, on y arrive !"_ 🐉💪
