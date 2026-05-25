# 🧠 Second Cerveau Saiyan - Knowledge Base

**Créé:** 24 Mai 2026  
**Objectif:** Transformer connaissances → Applications → Tests → Décisions  
**Méthode:** Zettelkasten + Building a Second Brain (Tiago Forte)

---

## 📊 Vue d'ensemble

| Niveau | Contenu | Location | Action |
|--------|---------|----------|--------|
| **1. Théorie** | Ce que j'ai appris | `learning/notes/` | 📚 Lire |
| **2. Insights** | Ce que ça signifie | `learning/insights/` | 💡 Comprendre |
| **3. Applications** | Comment j'utilise | `saiyan-v1/` | 🛠️ Coder |
| **4. Tests** | Est-ce que ça marche | `saiyan-v1/backtests/` | ✅ Valider |

---

## 🗂️ Index des Connaissances

### Master 1: Finance de Base

| Module | Insight Clé | Application Saiyan | Statut |
|--------|-------------|-------------------|--------|
| S01: Returns BTC | Fat tails (kurtosis 22) = FEATURE | Fat Tail Hunter strat | ✅ Insight → 🔄 Code |
| S02: GARCH | Vol prévisible (persistance 0.94) | Vola-Targeting sizing | ✅ Insight → 🔄 Code |
| S02: Multi-Asset | Corrélations crypto ~0.6-0.8 | Risk Parity allocation | ✅ Insight → 🔄 Code |
| S03: ARIMA | Forecast mean-reversion | Filtre MeanRev vs Momentum | ✅ Insight → ⏳ À coder |
| S04: Black-Scholes | Options pricing, Greeks | (Plus tard, hedging) | ⏳ À appliquer |
| S05: Microstructure | Slippage ∝ √(size/liquidity) | Microstructure Executor | ✅ Insight → 🔄 Code |

### Master 2: ML Trading

| Module | Insight Clé | Application Saiyan | Statut |
|--------|-------------|-------------------|--------|
| S09: Feature Eng | 50-60 features → 15-25 (SHAP+RFE) | ML Confidence Engine | ✅ Insight → 🔄 Code |
| S10: ML Supervised | XGBoost > RF > LR, Purged CV | ML Confidence Engine | ✅ Insight → 🔄 Code |
| S11: ML Unsupervised | Clustering, PCA, Autoencoders | Regime detection (backup HMM) | ⏳ À appliquer |
| S12: Walk-Forward | Backtest robuste (no lookahead) | Validation framework | ✅ Insight → 🔄 Code |
| S13: Mean Reversion | RSI, BB, Bollinger Walk | Fat Tail Hunter strat | ✅ Insight → 🔄 Code |
| S14: Momentum | Breakout detectors | Momentum Fade Detector | ✅ Insight → 🔄 Code |
| S15: HMM | 3 régimes (BULL/RANGE/BEAR) | Regime-dependent trading | ✅ Insight → 🔄 Code |
| S16: Multi-Factor | Combinaison facteurs | Confluence Scoring | ✅ Insight → 🔄 Code |

### Master 3: Portfolio Optimization

| Module | Insight Clé | Application Saiyan | Statut |
|--------|-------------|-------------------|--------|
| S17: Markowitz | Corrélations > Poids | Risk Parity allocation | ✅ Insight → 🔄 Code |
| S18: Risk Parity | Equal risk > Equal weight | Multi-asset sizing | ✅ Insight → 🔄 Code |
| S18: Kelly | Full Kelly = dangereux, Half-Kelly = optimal | Position sizing | ✅ Insight → 🔄 Code |

### Master 4: Risk Management

| Module | Insight Clé | Application Saiyan | Statut |
|--------|-------------|-------------------|--------|
| S19: VaR | Perte max attendue (95%) | Risk monitoring temps réel | ✅ Insight → 🔄 Code |
| S19: CVaR | Perte moyenne SI dépasse VaR | Risk monitoring (meilleur que VaR) | ✅ Insight → 🔄 Code |
| S20: Stress Testing | Scénarios historiques requis | Circuit breakers design | ✅ Insight → 🔄 Code |

---

## 💡 Insights Consolidés (Top 10)

### 1. Fat Tails = Feature, pas Bug
**Source:** S01 (Returns BTC)  
**Insight:** Kurtosis 22 en 5min → événements extrêmes 100x+ plus fréquents que Gaussian  
**Application:** Fat Tail Hunter (mean-rev APRÈS 3σ, pas avant)  
**Test:** Backtest sur 6 mois de données 5min  
**Décision:** ✅ P0 - À implémenter en premier

### 2. Skewness = Méta-Signal
**Source:** S01 + S15 (Returns + HMM)  
**Insight:** Skewness change de signe selon TF → régime de marché  
**Application:** Skewness Gate (active/désactive stratégies)  
**Test:** Corrélation skewness → performance par régime  
**Décision:** ✅ P1 - À implémenter après Fat Tail Hunter

### 3. GARCH × Position Sizing
**Source:** S02 (GARCH)  
**Insight:** Persistance 0.94 → vol prévisible  
**Application:** Vola-Targeting (`position = base × σ_target / σ_GARCH`)  
**Test:** Backtest avec/without GARCH sizing  
**Décision:** ✅ P1 - À implémenter

### 4. HMM Regime Detection
**Source:** S15 (HMM)  
**Insight:** 3 états (BULL/RANGE/BEAR) détectables  
**Application:** Regime-dependent strategy selection  
**Test:** Performance par régime (backtest)  
**Décision:** ✅ P0 - Core du système

### 5. Risk Parity > Equal Weight
**Source:** S17-18 (Portfolio Opt)  
**Insight:** Equal weight → 90% risque sur 50% assets  
**Application:** BTC/ETH/SOL allocation par risk contribution  
**Test:** Sharpe ratio Risk Parity vs Equal Weight  
**Décision:** ✅ P1 - À implémenter

### 6. Half-Kelly Optimal
**Source:** S18 (Kelly Criterion)  
**Insight:** Full Kelly → drawdowns 50-80%, Half-Kelly = sweet spot  
**Application:** `position = 0.5 × (μ / σ²)` avec constraints  
**Test:** Drawdown comparison Full vs Half Kelly  
**Décision:** ✅ P1 - À implémenter

### 7. VaR/CVaR Monitoring
**Source:** S19 (VaR/CVaR)  
**Insight:** VaR seule dangereuse, CVaR capture queue  
**Application:** Monitoring temps réel + circuit breakers  
**Test:** Alertes sur données historiques (COVID, FTX)  
**Décision:** ✅ P0 - Risk management core

### 8. ML > Heuristiques
**Source:** S10 (ML Supervised)  
**Insight:** XGBoost + Purged CV > pondérations manuelles  
**Application:** ML Confidence Engine (remplace score manuel)  
**Test:** AUC XGBoost vs heuristiques  
**Décision:** ✅ P1 - À implémenter

### 9. Walk-Forward Obligatoire
**Source:** S12 (Walk-Forward)  
**Insight:** Backtest simple = lookahead bias  
**Application:** Walk-forward expanding/rolling window  
**Test:** Comparison simple vs walk-forward  
**Décision:** ✅ P0 - Validation framework

### 10. Stress Testing Requis
**Source:** S20 (Stress Testing)  
**Insight:** Backtest seul insuffisant  
**Application:** 5 scénarios (COVID, FTX, Luna, Flash, Correlation)  
**Test:** Performance sous chaque scénario  
**Décision:** ✅ P1 - Validation finale

---

## 🛠️ Plan d'Action: Théorie → Code

### Phase 1: Foundation (Semaine 1-2)

| Insight | Code à Créer | Fichier | Priorité |
|---------|--------------|---------|----------|
| Fat Tails | `fat_tail_hunter.py` | `saiyan-v1/strategies/` | P0 |
| HMM Regime | `regime_detector.py` | `saiyan-v1/regime/` | P0 |
| VaR/CVaR | `risk_monitor.py` | `saiyan-v1/risk/` | P0 |
| Walk-Forward | `backtest_engine.py` | `saiyan-v1/backtest/` | P0 |

### Phase 2: Risk Management (Semaine 3)

| Insight | Code à Créer | Fichier | Priorité |
|---------|--------------|---------|----------|
| GARCH Sizing | `garch_sizing.py` | `saiyan-v1/sizing/` | P1 |
| Half-Kelly | `kelly_sizing.py` | `saiyan-v1/sizing/` | P1 |
| Circuit Breakers | `breakers.py` | `saiyan-v1/risk/` | P1 |

### Phase 3: Allocation (Semaine 4)

| Insight | Code à Créer | Fichier | Priorité |
|---------|--------------|---------|----------|
| Risk Parity | `allocator.py` | `saiyan-v1/portfolio/` | P1 |
| Rebalancing | `rebalance.py` | `saiyan-v1/portfolio/` | P1 |

### Phase 4: ML (Semaine 5)

| Insight | Code à Créer | Fichier | Priorité |
|---------|--------------|---------|----------|
| XGBoost | `ml_confidence.py` | `saiyan-v1/ml/` | P1 |
| Feature Sel. | `feature_selector.py` | `saiyan-v1/ml/` | P1 |

### Phase 5: Validation (Semaine 6)

| Insight | Test à Créer | Fichier | Priorité |
|---------|--------------|---------|----------|
| Walk-Forward | `walk_forward_test.py` | `saiyan-v1/tests/` | P0 |
| Stress Test | `stress_test.py` | `saiyan-v1/tests/` | P1 |

---

## 📊 Tracking: Connaissances → Applications

| Connaissance | Insight | Application | Code | Test | Décision |
|--------------|---------|-------------|------|------|----------|
| Fat Tails | ✅ | ✅ | 🔄 | ⏳ | ✅ P0 |
| GARCH | ✅ | ✅ | 🔄 | ⏳ | ✅ P1 |
| HMM | ✅ | ✅ | 🔄 | ⏳ | ✅ P0 |
| Risk Parity | ✅ | ✅ | ⏳ | ⏳ | ✅ P1 |
| Kelly | ✅ | ✅ | ⏳ | ⏳ | ✅ P1 |
| VaR/CVaR | ✅ | ✅ | 🔄 | ⏳ | ✅ P0 |
| XGBoost | ✅ | ✅ | ⏳ | ⏳ | ✅ P1 |
| Walk-Forward | ✅ | ✅ | 🔄 | ⏳ | ✅ P0 |

**Légende:**
- ✅ Fait
- 🔄 En cours
- ⏳ À faire

---

## 🎯 Règles de Mise à Jour

1. **Après chaque module appris:**
   - Créer/mettre à jour ligne dans index
   - Extraire insight clé (1-2 phrases)
   - Identifier application concrète
   - Prioriser (P0/P1/P2)

2. **Après chaque code créé:**
   - Mettre à jour colonne "Code"
   - Lier fichier dans `saiyan-v1/`
   - Noter problèmes rencontrés

3. **Après chaque test:**
   - Mettre à jour colonne "Test"
   - Documenter résultats
   - Décision: Keep/Iterate/Discard

4. **Weekly Review (dimanche):**
   - Relire tous les insights
   - Identifier connections inattendues
   - Ajuster priorités si besoin

---

## 🔗 Connections Inattendues (À Découvrir)

*Espace pour insights émergents:*

- **GARCH × Kelly:** GARCH forecast → ajuster Kelly fraction dynamically
- **HMM × Skewness:** Skewness comme input HMM supplémentaire
- **VaR × Position Sizing:** Max position = Risk Budget / VaR
- **ML × Regime:** XGBoost par régime (3 modèles séparés)

---

**Mise à jour:** 24 Mai 2026  
**Prochaine review:** Dimanche 18h UTC (cron hebdo)  
**Objectif:** 100% des insights → code → test → décision

---

*"Connaître n'est pas prévoir. Prévoir, c'est construire."* - Gaston Bachelard (adapté pour Saiyan) 🐉
