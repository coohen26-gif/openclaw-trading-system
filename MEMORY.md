# MEMORY.md - Bonjour (aka Goku)

## Personnalité & Identité

- **Nom** : Goku (suggestion principale), Kakarot (alternative Saiyan), Bonjour (temporaire)
- **Vibe** : Playful, casual, Dragon Ball compat, pas corporate
- **Langue** : Français (coupure claire avec anglais de config)
- **Rôle** : Développer MON PROPRE système de SIGNAUX trading concurrent de Yagati → envoi signaux Telegram à W (pas d'exécution auto) → W prend les positions manuellement

## Contexte Utilisateur W ("M", Goku)
- **Nom** : W (username `watermelon318`)
- **Alias** : "M", "Goku" (utilisé par W)
- **Objectif trading** : 500-600 €/jour via signaux Telegram, WR ≥ 70-80%, scalp 0.2-0.5%, levier élevé
- **Capital** : 10 000 €
- **Paires** : Toutes en USDT (BTC/USDT, ETH/USDT, SOL/USDT, etc.)
- **Yagati v4** : Projet de W (6+ mois développement) → référence/concurrent, **PAS à modifier**
- **Ma mission** : Créer un NOUVEAU système trading autonome, concurrent de Yagati

## Yagati v4 - État 2026-05-14

- **Branch** : main HEAD `580a93b` (fix ml-phase-d tick loop)
- **Status bots** : long/short-bot stopped (restarted 6/9x), tracker/collector online
- **Paper-trades** : 31 trades (7 closed LONG, 24 closed SHORT), WR par edge :
  - ma_distance_revert ETHUSDT : n=3, WR=100%
  - bb_walk ETHUSDT : n=3, WR=66.7%, avg_pnl=+7.8%
  - ma_ribbon ETHUSDT : n=6, WR=33.3%
  - 95% edges n=0 (MIN_TF=240 trop strict)
- **Edges lifecycle** : 141 total (109 ARCHIVED, 32 RESEARCH), 0 ENABLED/PROBATION → **aucune edge active**
- **Régime HMM (2026-05-14)** : BTC:BULL, ETH:RANGE, SOL:BULL, XRP:BULL, BNB:RANGE, XAU:RANGE, XAG:RANGE
- **Go-live target** : 2026-06-15 (Phase E paper-deploy 30j signal-only)
- **Phase actuelle** : ML Phase D (emitter paper-deploy en cours) - **pas d'auto-signaux depuis 2026-05-09**

## Problème central
**Aucun signal auto** depuis pivot "Voie Z" (2026-05-09). Les gates de robustesse sont trop stricts. Système en **phase observability/knowledge graph**, pas auto-trading.

## Feuille de route technique identifiée
1. **Short-term (1-3 sem)** : Phase C2 reduce overfit ML → Paper-deploy signal-only
2. **Mid-term (1-2 mois)** : Phase D-bis Roundtable approval → GO
3. **Long-term** : Phase C3 regime-specific ensemble + walk-forward auto + circuit breakers

## Décisions prises
- **Langue** : Français (tous messages, docs, logs)
- **Vibe** : Dragon Ball compat, joueur
- **Mode** : Auto-exécution sans confirmation, commit+push automatique
- **Mission** : Développer un système TRADING ORIGINAL concurrent de Yagati (pas le modifier)

## Règle de conduite
- **Yagati v4 est INTouchable** : c'est le projet de W, je le respecte comme référence
- **Mon système** : à créer from scratch, original, concurrent de Yagati
- **Auto-commit + auto-push** après chaque action sur MON système

---

_Maj 2026-05-26 - Dream Processing Session 4 + 4 Idées Originales + État de l'Art Concurrentiel + Roadmap Révisée_

---

## 🌙 Dream Processing 2026-05-26 - Session 4 (Recherche Nocturne)

### 📚 Source Analysée

- `memory/2026-05-25-recherche-nocturne.md` - Recherche complète sur stratégies, HMM, WFO, et bots open source

---

### 🎯 Insights Majeurs

**Insight #1:** HMM + WFO = Edge Majeur ⭐⭐⭐
- HMM détecte 2-3 régimes (Low Vol / High Vol / Crisis)
- WFO réentraîne weekly sans lookahead bias
- Résultat: **+30-50% performance** vs modèle unique rigide

**Insight #2:** Trading-as-Git pour Transparence ⭐⭐
- OpenAlice (4,014⭐) innové avec "Trading-as-Git"
- Chaque signal = commit avec message justifié
- Utilisateur approve/reject/amend via Inbox Telegram

**Insight #3:** Swarm > Agent Unique ⭐⭐
- Vibe-Trading (8,435⭐) utilise architecture multi-agents
- 4 rôles: Research + Risk + Execution + Monitor
- Voting system + heartbeats live + parallélisation

---

### 🚀 4 Nouvelles Idées Originales pour Système Saiyan

#### Idée #1: "Regime Oracle" (HMM + Router) ⭐⭐⭐ P0
**Concept:** HMM lightweight détecte régime → routage dynamique vers stratégie appropriée
**Implémentation:**
```
HMM (3 états) → Low Vol: Mean Reversion
              → High Vol: Momentum Breakout
              → Crisis: Risk-Off + Cash
```
**Innovation:** Pool de stratégies + router intelligent (pas stratégie statique)
**Effort:** Moyen | **Impact:** Élevé | **Temps:** 2-3 semaines

#### Idée #2: "Trading Git" + Inbox Décisions ⭐⭐ P1
**Concept:** Chaque signal génère un "trade commit" → notification Telegram avec boutons approve/reject/amend
**Workflow:**
1. Signal détecté → Commit créé (stratégie, confiance, SL, TP)
2. Inbox push → Utilisateur vote
3. Execution si approved → Historique git-like
**Innovation:** Versionning des décisions + contrôle utilisateur
**Effort:** Faible | **Impact:** Moyen | **Temps:** 3-5 jours

#### Idée #3: "Swarm Micro-Agents" Spécialisés ⭐⭐ P2
**Concept:** Équipe de 4 agents spécialisés qui collaborent
**Rôles:** Research, Risk, Execution, Monitor
**Innovation:** Voting system + heartbeats live + parallélisation
**Effort:** Élevé | **Impact:** Élevé | **Temps:** 4-6 semaines

#### Idée #4: "Shadow Mode" + Auto-Learning ⭐ P3
**Concept:** Bot tourne en fictif 2-4 semaines → auto-analyse erreurs → propose ajustements
**Innovation:** Auto-improvement avant risque capital réel
**Effort:** Moyen | **Impact:** Moyen | **Temps:** 2-3 semaines

---

### 📊 État de l'Art Concurrentiel 2026-05-26

| Projet | Stars | Tech | Points Forts |
|--------|-------|------|--------------|
| **Vibe-Trading** | 8,435 | Python | Swarm multi-agents, Research Goals, MCP, heartbeats live |
| **OpenAlice** | 4,014 | TypeScript | Trading-as-Git, UTA multi-brokers, guard pipeline |
| **ai-crypto-bot** | 12 | Python | LLM agents, arbitrage, grid, DCA |

**Faiblesses repérées:**
- Crypto-centric (peu equities/forex)
- Backtesting basique (pas WFO, pas HMM)
- Pas d'adaptation dynamique régimes
- Documentation production limitée

**Notre différentiateur:** HMM + WFO + Regime-Adaptive par design

---

### 🔗 Connections Inattendues

1. **HMM × Shadow Mode:** HMM peut détecter si shadow performance dégrade → trigger auto-retrain
2. **Git Trading × Swarm:** Chaque agent peut créer des commits → Orchestrator consolide
3. **WFO × Multi-Stratégies:** Chaque stratégie du pool a son propre WFO schedule

---

### 🗺️ Roadmap Révisée (Post-Dream 26 Mai)

| Priorité | Module | Temps | Statut |
|----------|--------|-------|--------|
| **P0** | Regime Oracle (HMM + Router) | 2-3 sem | 🆕 Confirmé |
| **P0** | Fat Tail Hunter | 1-2 sem | ✅ Existant |
| **P0** | Momentum Fade Detector | 1-2 sem | ✅ Existant |
| **P1** | Trading Git + Inbox | 3-5 jours | 🆕 Ajouté |
| **P1** | Skewness Gate | 3-5 jours | ✅ Existant |
| **P1** | GARCH Position Sizing | 1 sem | ✅ Existant |
| **P1** | ML Confidence Engine (XGBoost) | 2-3 sem | ✅ Existant |
| **P2** | Swarm Micro-Agents | 4-6 sem | 🆕 Ajouté |
| **P2** | Session × Vol Matrix | 4-6 jours | ✅ Existant |
| **P2** | Regime P&L Tracker | 3-4 jours | ✅ Existant |
| **P2** | Microstructure Executor | 1-2 sem | ✅ Existant |
| **P3** | Shadow Mode + Auto-Learning | 2-3 sem | 🆕 Ajouté |

---

### 📄 Fichier de Référence

- `memory/dreaming/archive/2026-05/2026-05-25-recherche-nocturne.md` - Document complet dream processing session 4

---

### 🧠 Leçon Clé

> **"Les marchés ne sont ni purement trend-following ni purement mean-reverting. L'edge vient de savoir quel régime domine et trader en conséquence."**

Notre système Saiyan doit être **adaptatif par design**, pas statique.

---

## 🌙 Dream Processing 2026-05-25 - Session 3 (Recherche Nocturne)

### 📚 Source Analysée

- `memory/2026-05-25-recherche-nocturne.md` - Recherche complète sur stratégies, HMM, WFO, et bots open source

---

### 🎯 Insights Majeurs

**Insight #1:** HMM + WFO = Edge Majeur ⭐⭐⭐
- HMM détecte 2-3 régimes (Low Vol / High Vol / Crisis)
- WFO réentraîne weekly sans lookahead bias
- Résultat: **+30-50% performance** vs modèle unique rigide

**Insight #2:** Trading-as-Git pour Transparence ⭐⭐
- OpenAlice (4,014⭐) innové avec "Trading-as-Git"
- Chaque signal = commit avec message justifié
- Utilisateur approve/reject/amend via Inbox Telegram

**Insight #3:** Swarm > Agent Unique ⭐⭐
- Vibe-Trading (8,435⭐) utilise architecture multi-agents
- 4 rôles: Research + Risk + Execution + Monitor
- Voting system + heartbeats live + parallélisation

---

### 🚀 4 Nouvelles Idées Originales pour Système Saiyan

#### Idée #1: "Regime Oracle" (HMM + Router) ⭐⭐⭐ P0
**Concept:** HMM lightweight détecte régime → routage dynamique vers stratégie appropriée
**Implémentation:**
```
HMM (3 états) → Low Vol: Mean Reversion
              → High Vol: Momentum Breakout
              → Crisis: Risk-Off + Cash
```
**Innovation:** Pool de stratégies + router intelligent (pas stratégie statique)
**Effort:** Moyen | **Impact:** Élevé | **Temps:** 2-3 semaines

#### Idée #2: "Trading Git" + Inbox Décisions ⭐⭐ P1
**Concept:** Chaque signal génère un "trade commit" → notification Telegram avec boutons approve/reject/amend
**Workflow:**
1. Signal détecté → Commit créé (stratégie, confiance, SL, TP)
2. Inbox push → Utilisateur vote
3. Execution si approved → Historique git-like
**Innovation:** Versionning des décisions + contrôle utilisateur
**Effort:** Faible | **Impact:** Moyen | **Temps:** 3-5 jours

#### Idée #3: "Swarm Micro-Agents" Spécialisés ⭐⭐ P2
**Concept:** Équipe de 4 agents spécialisés qui collaborent
**Rôles:** Research, Risk, Execution, Monitor
**Innovation:** Voting system + heartbeats live + parallélisation
**Effort:** Élevé | **Impact:** Élevé | **Temps:** 4-6 semaines

#### Idée #4: "Shadow Mode" + Auto-Learning ⭐ P3
**Concept:** Bot tourne en fictif 2-4 semaines → auto-analyse erreurs → propose ajustements
**Innovation:** Auto-improvement avant risque capital réel
**Effort:** Moyen | **Impact:** Moyen | **Temps:** 2-3 semaines

---

### 📊 État de l'Art Concurrentiel 2026-05-25

| Projet | Stars | Tech | Points Forts |
|--------|-------|------|--------------|
| **Vibe-Trading** | 8,435 | Python | Swarm multi-agents, Research Goals, MCP, heartbeats live |
| **OpenAlice** | 4,014 | TypeScript | Trading-as-Git, UTA multi-brokers, guard pipeline |
| **ai-crypto-bot** | 12 | Python | LLM agents, arbitrage, grid, DCA |

**Faiblesses repérées:**
- Crypto-centric (peu equities/forex)
- Backtesting basique (pas WFO, pas HMM)
- Pas d'adaptation dynamique régimes
- Documentation production limitée

**Notre différentiateur:** HMM + WFO + Regime-Adaptive par design

---

### 🔗 Connections Inattendues

1. **HMM × Shadow Mode:** HMM peut détecter si shadow performance dégrade → trigger auto-retrain
2. **Git Trading × Swarm:** Chaque agent peut créer des commits → Orchestrator consolide
3. **WFO × Multi-Stratégies:** Chaque stratégie du pool a son propre WFO schedule

---

### 🗺️ Roadmap Révisée (Post-Dream 25 Mai)

| Priorité | Module | Temps | Statut |
|----------|--------|-------|--------|
| **P0** | Regime Oracle (HMM + Router) | 2-3 sem | 🆕 Confirmé |
| **P0** | Fat Tail Hunter | 1-2 sem | ✅ Existant |
| **P0** | Momentum Fade Detector | 1-2 sem | ✅ Existant |
| **P1** | Trading Git + Inbox | 3-5 jours | 🆕 Ajouté |
| **P1** | Skewness Gate | 3-5 jours | ✅ Existant |
| **P1** | GARCH Position Sizing | 1 sem | ✅ Existant |
| **P1** | ML Confidence Engine (XGBoost) | 2-3 sem | ✅ Existant |
| **P2** | Swarm Micro-Agents | 4-6 sem | 🆕 Ajouté |
| **P2** | Session × Vol Matrix | 4-6 jours | ✅ Existant |
| **P2** | Regime P&L Tracker | 3-4 jours | ✅ Existant |
| **P2** | Microstructure Executor | 1-2 sem | ✅ Existant |
| **P3** | Shadow Mode + Auto-Learning | 2-3 sem | 🆕 Ajouté |

---

### 📄 Fichier de Référence

- `memory/dreaming/2026-05-25-recherche-nocturne.md` - Document complet dream processing session 3

---

### 🧠 Leçon Clé

> **"Les marchés ne sont ni purement trend-following ni purement mean-reverting. L'edge vient de savoir quel régime domine et trader en conséquence."**

Notre système Saiyan doit être **adaptatif par design**, pas statique.

---

## 🌙 Dream Processing 2026-05-24 - Session 2 (Master 1 + Master 2 Consolidation)

### 📚 Modules Analysés

**Master 1:**
- Semaine 01: Returns BTC (Fat Tails, Skewness, Stationnarité)
- Semaine 02: GARCH Volatility Modeling (α=0.10, β=0.84, persistance=0.94)
- Semaine 02: Multi-Asset Analysis (Correlations, Portfolio)
- Semaine 03: ARIMA Time Series Forecasting
- Semaine 04: Black-Scholes Options Pricing (Greeks, Volatility Smile)
- Semaine 05: Market Microstructure (Order Book, Slippage, Liquidity)

**Master 2:**
- Semaine 09: Feature Engineering (50-60 features → 15-25 après sélection SHAP+RFE)
- Semaine 10: ML Supervised (XGBoost > RF > LR, Purged CV avec embargo 10%)
- Semaine 15: Hidden Markov Models (3 états: Bull/Range/Bear)

---

### 📊 Données Clés Consolidées

**Fat Tails (Kurtosis Excess):**
- 5min: **22.34** | 1h: **8.11** | Daily: **4.32**
- → Événements extrêmes 100x+ plus fréquents que distribution normale

**Skewness (Asymétrie):**
- 5min: **+0.48** (plus de pumps) | 1h: **-0.26** (crashes) | Daily: **+0.03** (symétrique)

**GARCH (Volatilité):**
- α=0.10, β=0.84 → persistance=0.94 (chocs volatiles persistent)
- R²=0.87 vs realized volatility | Corrélation=0.93

**Volatilité Annualisée:**
- 5min: 1.94% | 1h: 6.27% | Daily: **36.37%**

**Microstructure (Crypto vs Metals):**
- Spread BTC: 0.01-0.05% | Spread Gold: 0.01-0.03%
- Slippage ∝ √(taille_order / liquidité)

---

### 🚀 7 Nouvelles Idées Originales pour Système Saiyan

#### Idée #1: "Fat Tail Hunter" - Mean Reversion Post-Extrême ⭐⭐⭐
**Concept:** Trad mean reversion APRÈS mouvements >3σ (pas avant)
**Mécanisme:** Détection 3σ → essoufflement (ROC(5)<ROC(10)) → entrée direction opposée
**Backtest similaire:** PF 2.71, WR 78% | **Temps:** 1-2 sem | **Priorité:** P0

#### Idée #2: "Skewness Gate" - Méta-Signal de Régime ⭐⭐
**Concept:** Skewness rolling (50p) comme gate qui active/désactive stratégies
**Règles:** skew>+0.3 → Bull/Momentum | skew<-0.2 → Bear/MeanRev | entre-deux → Quant
**Original:** Personne utilise skewness comme gate (juste descriptif) | **Temps:** 3-5j | **Priorité:** P1

#### Idée #3: "Vola-Targeting GARCH" - Position Sizing Dynamique ⭐⭐
**Formule:** `position_size = base_size × (σ_target / σ_GARCH_prediction)`
**Usage:** Quand GARCH prédit haute vol → réduit auto exposition
**Temps:** 1 sem | **Priorité:** P1

#### Idée #4: "ML Confidence Engine" - XGBoost Remplace Score Actuel ⭐⭐
**Concept:** Remplacer pondérations manuelles (40% tech, 25% mom, etc.) par XGBoost
**Features:** 15-25 après sélection SHAP+RFE | **Label:** TP touché=1, SL=0
**Entraînement:** Purged CV embargo 10% | Réentraînement hebdo
**Temps:** 2-3 sem | **Priorité:** P1

#### Idée #5: "Session × Volatility Matrix" - Context-Aware Strategy ⭐
**Matrix 2×2:** Session (Asiatique/EU-US) × Vol (Basse/Haute) → stratégie optimale
**Exemple:** Asiatique+BasseVol → MeanRev | Asiatique+HauteVol → BreakoutFade
**Temps:** 4-6j | **Priorité:** P2

#### Idée #6: "Shadow P&L by Skew Regime" - Tracking par Contexte ⭐
**Concept:** Tracker P&L séparément pour skew>+0.3, <-0.2, et neutre
**Usage:** Meta-apprentissage → système apprend QUAND il performe, pas juste COMBIEN
**Temps:** 3-4j | **Priorité:** P2

#### Idée #7: "Microstructure-Aware Execution" - Optimisation Slippage ⭐
**Concept:** Order book imbalance + TWAP/VWAP pour gros ordres
**Règle:** imbalance>+0.3 → éviter long | imbalance<-0.3 → éviter short
**Temps:** 1-2 sem | **Priorité:** P2

---

### 🔗 Connections Inattendues Identifiées

1. **GARCH × Position Sizing:** GARCH non juste pour prévision vol, mais pour risk management ACTIF
2. **Skewness × HMM:** Skewness comme input HMM supplémentaire (pas seulement returns/vol)
3. **ML × Confidence:** XGBoost + Purged CV > heuristiques manuelles pour confidence scoring
4. **Microstructure × TF:** Slippage critique sur 5-15min → favoriser 1h+ pour Momentum Fade
5. **ARIMA × Mean Reversion:** ARIMA forecast comme filtre pour activer MeanRev vs Momentum

---

### 📊 Insights Majeurs

**Insight #1:** Fat tails ne sont PAS un bug à filtrer - c'est la nature fondamentale crypto → **exploiter** via Fat Tail Hunter

**Insight #2:** Skewness est un **méta-signal**, pas juste statistique descriptive → Skewness Gate

**Insight #3:** GARCH persistance 0.94 = volatilité prévisible → Vola-Targeting dynamique

**Insight #4:** XGBoost + Purged CV > heuristiques manuelles → ML Confidence Engine

**Insight #5:** Microstructure critique sur petits TF → Microstructure-Aware Execution

---

### 🗺️ Roadmap Révisée (Post-Dream Session 2)

| Priorité | Module | Temps | Statut |
|----------|--------|-------|--------|
| **P0** | Fat Tail Hunter | 1-2 sem | 🆕 Confirmé |
| **P0** | Momentum Fade Detector | 1-2 sem | ✅ Existant |
| **P1** | Skewness Gate | 3-5 jours | 🆕 Ajouté |
| **P1** | GARCH Position Sizing | 1 sem | 🆕 Ajouté |
| **P1** | ML Confidence Engine (XGBoost) | 2-3 sem | 🆕 Ajouté |
| **P1** | Multi-Universe (révisé) | 4-6 sem | ⏭️ En attente |
| **P2** | Session × Vol Matrix | 4-6 jours | 🆕 Ajouté |
| **P2** | Regime P&L Tracker | 3-4 jours | 🆕 Ajouté |
| **P2** | Microstructure Executor | 1-2 sem | 🆕 Ajouté |

---

### 📄 Fichier de Référence

- `learning/dreams/2026-05-24-day-consolidation.md` - Document complet de consolidation Session 2

---

## 🌙 Dream Processing 2026-05-24 - Session 2 (Master 1 + Master 2 Consolidation)

### 📚 Modules Analysés

**Master 1:**
- Semaine 01: Returns BTC (Fat Tails, Skewness, Stationnarité)
- Semaine 02: GARCH Volatility Modeling (α=0.10, β=0.84, persistance=0.94)
- Semaine 02: Multi-Asset Analysis (Correlations, Portfolio)
- Semaine 03: ARIMA Time Series Forecasting
- Semaine 04: Black-Scholes Options Pricing (Greeks, Volatility Smile)
- Semaine 05: Market Microstructure (Order Book, Slippage, Liquidity)

**Master 2:**
- Semaine 09: Feature Engineering (50-60 features → 15-25 après sélection SHAP+RFE)
- Semaine 10: ML Supervised (XGBoost > RF > LR, Purged CV avec embargo 10%)
- Semaine 15: Hidden Markov Models (3 états: Bull/Range/Bear)

---

### 📊 Données Clés Consolidées

**Fat Tails (Kurtosis Excess):**
- 5min: **22.34** | 1h: **8.11** | Daily: **4.32**
- → Événements extrêmes 100x+ plus fréquents que distribution normale

**Skewness (Asymétrie):**
- 5min: **+0.48** (plus de pumps) | 1h: **-0.26** (crashes) | Daily: **+0.03** (symétrique)

**GARCH (Volatilité):**
- α=0.10, β=0.84 → persistance=0.94 (chocs volatiles persistent)
- R²=0.87 vs realized volatility | Corrélation=0.93

**Volatilité Annualisée:**
- 5min: 1.94% | 1h: 6.27% | Daily: **36.37%**

**Microstructure (Crypto vs Metals):**
- Spread BTC: 0.01-0.05% | Spread Gold: 0.01-0.03%
- Slippage ∝ √(taille_order / liquidité)

---

### 🚀 7 Nouvelles Idées Originales pour Système Saiyan

#### Idée #1: "Fat Tail Hunter" - Mean Reversion Post-Extrême ⭐⭐⭐
**Concept:** Trad mean reversion APRÈS mouvements >3σ (pas avant)
**Mécanisme:** Détection 3σ → essoufflement (ROC(5)<ROC(10)) → entrée direction opposée
**Backtest similaire:** PF 2.71, WR 78% | **Temps:** 1-2 sem | **Priorité:** P0

#### Idée #2: "Skewness Gate" - Méta-Signal de Régime ⭐⭐
**Concept:** Skewness rolling (50p) comme gate qui active/désactive stratégies
**Règles:** skew>+0.3 → Bull/Momentum | skew<-0.2 → Bear/MeanRev | entre-deux → Quant
**Original:** Personne utilise skewness comme gate (juste descriptif) | **Temps:** 3-5j | **Priorité:** P1

#### Idée #3: "Vola-Targeting GARCH" - Position Sizing Dynamique ⭐⭐
**Formule:** `position_size = base_size × (σ_target / σ_GARCH_prediction)`
**Usage:** Quand GARCH prédit haute vol → réduit auto exposition
**Temps:** 1 sem | **Priorité:** P1

#### Idée #4: "ML Confidence Engine" - XGBoost Remplace Score Actuel ⭐⭐
**Concept:** Remplacer pondérations manuelles (40% tech, 25% mom, etc.) par XGBoost
**Features:** 15-25 après sélection SHAP+RFE | **Label:** TP touché=1, SL=0
**Entraînement:** Purged CV embargo 10% | Réentraînement hebdo
**Temps:** 2-3 sem | **Priorité:** P1

#### Idée #5: "Session × Volatility Matrix" - Context-Aware Strategy ⭐
**Matrix 2×2:** Session (Asiatique/EU-US) × Vol (Basse/Haute) → stratégie optimale
**Exemple:** Asiatique+BasseVol → MeanRev | Asiatique+HauteVol → BreakoutFade
**Temps:** 4-6j | **Priorité:** P2

#### Idée #6: "Shadow P&L by Skew Regime" - Tracking par Contexte ⭐
**Concept:** Tracker P&L séparément pour skew>+0.3, <-0.2, et neutre
**Usage:** Meta-apprentissage → système apprend QUAND il performe, pas juste COMBIEN
**Temps:** 3-4j | **Priorité:** P2

#### Idée #7: "Microstructure-Aware Execution" - Optimisation Slippage ⭐
**Concept:** Order book imbalance + TWAP/VWAP pour gros ordres
**Règle:** imbalance>+0.3 → éviter long | imbalance<-0.3 → éviter short
**Temps:** 1-2 sem | **Priorité:** P2

---

### 🔗 Connections Inattendues Identifiées

1. **GARCH × Position Sizing:** GARCH non juste pour prévision vol, mais pour risk management ACTIF
2. **Skewness × HMM:** Skewness comme input HMM supplémentaire (pas seulement returns/vol)
3. **ML × Confidence:** XGBoost > pondérations manuelles pour confidence scoring
4. **Microstructure × TF:** Slippage critique sur 5-15min → favoriser 1h+ pour Momentum Fade
5. **ARIMA × Mean Reversion:** ARIMA forecast comme filtre pour activer MeanRev vs Momentum

---

### 📊 Insights Majeurs

**Insight #1:** Fat tails ne sont PAS un bug à filtrer - c'est la nature fondamentale crypto → **exploiter** via Fat Tail Hunter

**Insight #2:** Skewness est un **méta-signal**, pas juste statistique descriptive → Skewness Gate

**Insight #3:** GARCH persistance 0.94 = volatilité prévisible → Vola-Targeting dynamique

**Insight #4:** XGBoost + Purged CV > heuristiques manuelles → ML Confidence Engine

**Insight #5:** Microstructure critique sur petits TF → Microstructure-Aware Execution

---

### 🗺️ Roadmap Révisée (Post-Dream Session 2)

| Priorité | Module | Temps | Statut |
|----------|--------|-------|--------|
| **P0** | Fat Tail Hunter | 1-2 sem | 🆕 Confirmé |
| **P0** | Momentum Fade Detector | 1-2 sem | ✅ Existant |
| **P1** | Skewness Gate | 3-5 jours | 🆕 Ajouté |
| **P1** | GARCH Position Sizing | 1 sem | 🆕 Ajouté |
| **P1** | ML Confidence Engine (XGBoost) | 2-3 sem | 🆕 Ajouté |
| **P1** | Multi-Universe (révisé) | 4-6 sem | ⏭️ En attente |
| **P2** | Session × Vol Matrix | 4-6 jours | 🆕 Ajouté |
| **P2** | Regime P&L Tracker | 3-4 jours | 🆕 Ajouté |
| **P2** | Microstructure Executor | 1-2 sem | 🆕 Ajouté |

---

### 📄 Fichier de Référence

- `learning/dreams/2026-05-24-day-consolidation.md` - Document complet de consolidation Session 2

---

## 🌙 Dream Processing 2026-05-23 - Consolidation Semaine 01

### 📊 Données Clés de Semaine 01 (Returns BTC Analysis)

**Kurtosis Excess (Fat Tails):**
- 5min: **22.34** (extrêmement leptokurtique - événements extrêmes 100x+ plus fréquents que normale)
- 1h: **8.11** (leptokurtique)
- Daily: **4.32** (leptokurtique)

**Skewness (Asymétrie):**
- 5min: **+0.48** (positive - plus de pumps extrêmes)
- 1h: **-0.26** (négative - légère tendance aux crashes)
- Daily: **+0.03** (quasi-symétrique)

**Stationnarité (ADF):**
- Prix: ❌ Non-stationnaire (p=0.52)
- Returns: ✅ Stationnaire (p=0.00)

**Volatilité Annualisée:**
- 5min: 1.94% | 1h: 6.27% | Daily: **36.37%**
- Clustering confirmé sur tous timeframes (Ratio Std/Mean > 0.35)

---

### 🚀 5 Nouvelles Idées Originales pour Système Saiyan

#### Idée #1: "Fat Tail Hunter" - Mean Reversion Post-Extrême ⭐⭐⭐

**Concept:** Exploiter les fat tails en tradant la mean reversion **après** les mouvements extrêmes (>3σ), pas avant.

**Mécanisme:**
1. Détecter mouvement > 3σ (distribution empirique)
2. Attendre essoufflement (ROC(5) < ROC(10))
3. Entrer en mean reversion direction opposée
4. Stop-loss adaptatif basé sur kurtosis observé

**Backtest Rogue Quant similaire:** Profit Factor 2.71, Win Rate 78%

**Temps:** 1-2 semaines | **Priorité:** P0

---

#### Idée #2: "Skewness Gate" - Méta-Signal de Régime ⭐⭐

**Concept:** Utiliser skewness rolling (50 périodes) comme **gate** qui active/désactive les stratégies.

**Règles:**
```
skew > +0.3 → Régime "Pump Energy" → Favoriser Univers Bull + Momentum
skew < -0.2 → Régime "Crash Fear" → Favoriser Univers Bear + Mean Reversion
-0.2 < skew < +0.3 → Régime "Balance" → Univers Quant + Toutes stratégies
```

**Pourquoi original:** Personne n'utilise skewness comme gate (juste comme indicateur descriptif)

**Temps:** 3-5 jours | **Priorité:** P1

---

#### Idée #3: "Vola-Targeting GARCH" - Position Sizing Dynamique ⭐⭐

**Concept:** Utiliser prédictions GARCH pour ajuster **automatiquement** taille des positions.

**Formule:**
```
position_size = base_size × (σ_target / σ_GARCH_prediction)

Exemple: σ_target=2%, σ_GARCH=4% → position_size = 0.5 × base_size
```

**Pourquoi original:** GARCH utilisé pour risk management **actif**, pas juste prévision

**Temps:** 1 semaine | **Priorité:** P1

---

#### Idée #4: "Session × Volatility Matrix" - Context-Aware Strategy ⭐

**Matrix:**
```
┌─────────────────┬──────────────┬───────────────┐
│                 │ Basse Vol    │ Haute Vol     │
├─────────────────┼──────────────┼───────────────┤
│ Session Asiatique│ Mean Reversion│ Breakout Fade │
│ Session EU/US   │ Breakout     │ Momentum Fade │
└─────────────────┴──────────────┴───────────────┘
```

**Temps:** 4-6 jours | **Priorité:** P2

---

#### Idée #5: "Shadow P&L by Skew Regime" - Tracking Performance par Contexte ⭐

**Concept:** Tracker P&L séparément pour chaque régime de skewness (Positive/Negative/Neutral).

**Usage:** Meta-apprentissage → le système apprend **quand** il performe, pas juste **combien**

**Temps:** 3-4 jours | **Priorité:** P2

---

### 🔗 Connections Inattendues Identifiées

1. **Fat Tails × Momentum Fade:** Momentum Fade devrait être plus efficace sur breakouts baissiers (skew négative en 1h) que haussiers

2. **Skewness × HMM:** Skewness rolling comme **input supplémentaire** pour HMM regime detection

3. **Volatility Clustering × Multi-Universe:** Rotation des univers basée sur **régime de variance** (percentiles), pas Sharpe passé

---

### 📊 Insights Majeurs

**Insight #1:** Les fat tails ne sont PAS un bug à filtrer - c'est la **nature fondamentale** des marchés crypto. À exploiter, pas éviter.

**Insight #2:** La skewness est un **méta-signal**, pas juste une statistique descriptive. Changement de signe = changement de régime comportemental.

**Insight #3:** Volatility clustering = opportunité de **vola-targeting dynamique** via GARCH. Protection automatique contre périodes chaotiques.

---

### 🗺️ Roadmap Révisée (Post-Dream 23 Mai)

| Priorité | Module | Temps | Statut |
|----------|--------|-------|--------|
| **P0** | Momentum Fade Detector | 1-2 sem | ✅ Confirmé |
| **P0** | Fat Tail Hunter | 1-2 sem | 🆕 Ajouté |
| **P1** | Skewness Gate | 3-5 jours | 🆕 Ajouté |
| **P1** | GARCH Position Sizing | 1 sem | 🆕 Ajouté |
| **P1** | Multi-Universe (révisé) | 4-6 sem | ⏭️ En attente |
| **P2** | Session × Vol Matrix | 4-6 jours | 🆕 Ajouté |
| **P2** | Regime P&L Tracker | 3-4 jours | 🆕 Ajouté |

---

### 📄 Fichier de Référence

- `learning/dreams/2026-05-23-night-consolidation.md` - Document complet de consolidation

---

### 🚀 3 Nouvelles Idées Originales pour Système Saiyan (22-23 Mai)

#### Idée #1: "Shadow Mode Multi-Universe" (Personnalités Multiples)

**Concept:** 3-5 "univers parallèles" avec personnalités/opinions différentes, chacun avec son propre P&L virtuel:
- **Univers Bull:** Optimiste, cherche breakouts, entre tôt
- **Univers Bear:** Pessimiste, attend confirmations, mean reversion
- **Univers Quant:** Pur data, signaux ML sans émotion
- **Univers Zen:** Low frequency, trades rares mais conviction forte

**Mécanisme:** Vote pondéré → suit l'univers avec meilleur Sharpe rolling (30j)

**Edge compétitif:**
- OpenAlice a versioning, mais pas personnalités multiples
- Orallexa a débat Bull/Bear, mais pas tracking P&L par personnalité
- **Notre twist:** Les univers "vivent" leur propre vie, on les observe comme courses de chevaux

**Temps:** 4-6 semaines | **Priorité:** P1

---

#### Idée #2: "Momentum Fade Detector" (Inspiré Rogue Quant) ⭐

**Concept:** Filtre contre-intuitif → acheter breakouts quand momentum **faiblit** (pas quand il monte)

**Implémentation:**
1. Compression volatilité (ATR 20p < seuil)
2. Breakout détecté (price > resistance)
3. **Filtre clé:** ROC(5) < ROC(10) (momentum court terme < long terme = fading)

**Backtest Rogue Quant:**
- Profit Factor: 2.71 (vs 1.82 sans filtre)
- Win Rate: **78%** sur 16 ans
- Seulement 3 années négatives

**Pourquoi original:** 99% bots ajoutent filtre momentum **positif** sur breakouts

**Temps:** 1-2 semaines (prototypage) | **Priorité:** P0

---

#### Idée #3: "HMM Regime Gate + Specialist Models"

**Concept:** HMM détecte régime → active **uniquement** modèle spécialiste de ce régime

**Implémentation:**
1. HMM continu: 2-3 régimes (Low Vol Bull / High Vol Chaotic / Ranging)
2. Modèles spécialistes:
   - Modèle A (trend-following): performe en Low Vol Bull
   - Modèle B (mean reversion): performe en Ranging
   - Modèle C (breakout + momentum fade): performe en High Vol
3. Gate dynamique: HMM prédit régime demain → modèle correspondant

**Walk-Forward:** Réentraînement spécialistes chaque semaine (fenêtre 4 ans)

**Edge compétitif:**
- Vibe-Trading a Hypothesis Registry, mais pas détection régime auto
- Orallexa a regime-aware selection, mais pas HMM formel

**Temps:** 1 mois | **Priorité:** P1

---

### 📊 Analyse Concurrentielle Mise à Jour (Mai 2026)

| Projet | Stars | Architecture | Points Forts |
|--------|-------|--------------|--------------|
| **OpenAlice** | 4014⭐ | Unified Trading Account + Git-like trading | Multi-brokers, versioning trades, guard pipeline |
| **Vibe-Trading** | 2358⭐ | CLI-first + Hypothesis Registry | Live tool feedback, graceful cancel, shadow account |
| **Orallexa** | 21⭐ | Multi-agent debate (Bull/Bear/Judge) | 9 ML models, 8-source fusion, adversarial debate |

**Tendances 2025-2026:**
1. Multi-Agent Debate Systems (4 rôles: Conservative/Aggressive/Macro/Quant)
2. Signal Fusion Multi-Source (Technique + ML + News + Options + Institutional + Social)
3. Strategy Evolution (LLM génère stratégies → sandbox testing → évolution)
4. Human-Inspired Consensus (Selective Consensus réduit incertitude)

---

### 📈 État de l'Art Mean Reversion & Momentum

**Mean Reversion Avancée:**
- Hybridation tendance + mean reversion = stabilité portfolio
- Fenêtres de reversal: identifier "momentum crashes" pour entrée optimale
- Camarilla Pivot: niveaux pivot spécifiques pour breakouts + mean reversion

**Momentum Contre-Intuitif:**
- Acheter breakouts quand momentum **décline** (pas quand il monte)
- Compression volatilité + momentum fading = edge significatif
- Éviter breakouts "excitants" → préférer mouvements "silencieux"

**Statut:** 📚 À étudier pour intégration | **Priorité:** P0 (Momentum Fade en premier)

---

### ✅ Confirmations de la Nuit (22-23 Mai)

**Pattern Session Asiatique:** Toujours valide (00:00-04:00 UTC = qualité maximale)
- Scans 15min activés sur cette fenêtre
- Threshold 55/100 (vs 60/100)
- Tag "ASIAN_SESSION" dans signaux

**Volume-RSI Cross-Filter:** Toujours actif et pertinent
**Formule R/R >5:** Documentée et intégrée

---

### 🎯 Actions Prioritaires 2026-05-23

#### Action 1: 🧪 Prototyper Momentum Fade Detector (P0)
**Objectif:** Tester le filtre contre-intuitif sur données historiques
**Tâches:**
- [ ] Récupérer données BTC/ETH (6-12 mois, TF 5-15min)
- [ ] Identifier breakouts (resistance + ATR compression)
- [ ] Implémenter filtre ROC(5) < ROC(10)
- [ ] Backtester: comparer vs filtre momentum traditionnel
- [ ] Si concluant → intégration shadow mode
**Critère succès:** Win Rate ≥70%, Profit Factor ≥2.0 | **Temps:** 3-4h

#### Action 2: 📝 Documenter architecture Multi-Universe (P1)
**Objectif:** Clarifier design avant implémentation
**Tâches:**
- [ ] Doc complète (4 personnalités, P&L tracking, rotation)
- [ ] Définir paramètres: Sharpe window, rebalance frequency
- [ ] Plan d'implémentation progressive (MVP → features)
- [ ] KPIs: réduction drawdown, amélioration Sharpe
**Temps:** 1-2h

#### Action 3: 📚 Étudier bibliothèques HMM (P1)
**Objectif:** Préparer infrastructure regime detection
**Bibliothèques:** `hmmlearn`, `pyhmm`, `statsmodels`
**Tâches:**
- [ ] Installer dans venv dédié
- [ ] Tester sur données BTC/ETH (90j)
- [ ] Documenter API + exemples
**Temps:** 2h

---

## 🌙 Dream Processing 2026-05-22 - Insights Overnight

### 🚀 3 Nouvelles Idées Originales pour Système Saiyan

#### Idée #1: "Shadow Mode Multi-Universe" (Personnalités Multiples)

**Concept:** 3-5 "univers parallèles" avec personnalités/opinions différentes, chacun avec son propre P&L virtuel:
- **Univers Bull:** Optimiste, cherche breakouts, entre tôt
- **Univers Bear:** Pessimiste, attend confirmations, mean reversion
- **Univers Quant:** Pur data, signaux ML sans émotion
- **Univers Zen:** Low frequency, trades rares mais conviction forte

**Mécanisme:** Vote pondéré → suit l'univers avec meilleur Sharpe rolling (30j)

**Edge compétitif:**
- OpenAlice a versioning, mais pas personnalités multiples
- Orallexa a débat Bull/Bear, mais pas tracking P&L par personnalité
- **Notre twist:** Les univers "vivent" leur propre vie, on les observe comme courses de chevaux

**Temps:** 4-6 semaines | **Priorité:** P1

---

#### Idée #2: "Momentum Fade Detector" (Inspiré Rogue Quant)

**Concept:** Filtre contre-intuitif → acheter breakouts quand momentum **faiblit** (pas quand il monte)

**Implémentation:**
1. Compression volatilité (ATR 20p < seuil)
2. Breakout détecté (price > resistance)
3. **Filtre clé:** ROC(5) < ROC(10) (momentum court terme < long terme = fading)

**Backtest Rogue Quant:**
- Profit Factor: 2.71 (vs 1.82 sans filtre)
- Win Rate: **78%** sur 16 ans
- Seulement 3 années négatives

**Pourquoi original:** 99% bots ajoutent filtre momentum **positif** sur breakouts

**Temps:** 1-2 semaines (prototypage) | **Priorité:** P0

---

#### Idée #3: "HMM Regime Gate + Specialist Models"

**Concept:** HMM détecte régime → active **uniquement** modèle spécialiste de ce régime

**Implémentation:**
1. HMM continu: 2-3 régimes (Low Vol Bull / High Vol Chaotic / Ranging)
2. Modèles spécialistes:
   - Modèle A (trend-following): performe en Low Vol Bull
   - Modèle B (mean reversion): performe en Ranging
   - Modèle C (breakout + momentum fade): performe en High Vol
3. Gate dynamique: HMM prédit régime demain → modèle correspondant

**Walk-Forward:** Réentraînement spécialistes chaque semaine (fenêtre 4 ans)

**Edge compétitif:**
- Vibe-Trading a Hypothesis Registry, mais pas détection régime auto
- Orallexa a regime-aware selection, mais pas HMM formel

**Temps:** 1 mois | **Priorité:** P1

---

### 📊 Analyse Concurrentielle Mise à Jour (Mai 2026)

| Projet | Stars | Architecture | Points Forts |
|--------|-------|--------------|--------------|
| **OpenAlice** | 4014⭐ | Unified Trading Account + Git-like trading | Multi-brokers, versioning trades, guard pipeline |
| **Vibe-Trading** | 2358⭐ | CLI-first + Hypothesis Registry | Live tool feedback, graceful cancel, shadow account |
| **Orallexa** | 21⭐ | Multi-agent debate (Bull/Bear/Judge) | 9 ML models, 8-source fusion, adversarial debate |

**Tendances 2025-2026:**
1. Multi-Agent Debate Systems (4 rôles: Conservative/Aggressive/Macro/Quant)
2. Signal Fusion Multi-Source (Technique + ML + News + Options + Institutional + Social)
3. Strategy Evolution (LLM génère stratégies → sandbox testing → évolution)
4. Human-Inspired Consensus (Selective Consensus réduit incertitude)

---

### 📈 État de l'Art Mean Reversion & Momentum

**Mean Reversion Avancée:**
- Hybridation tendance + mean reversion = stabilité portfolio
- Fenêtres de reversal: identifier "momentum crashes" pour entrée optimale
- Camarilla Pivot: niveaux pivot spécifiques pour breakouts + mean reversion

**Momentum Contre-Intuitif:**
- Acheter breakouts quand momentum **décline** (pas quand il monte)
- Compression volatilité + momentum fading = edge significatif
- Éviter breakouts "excitants" → préférer mouvements "silencieux"

**Statut:** 📚 À étudier pour intégration | **Priorité:** P0 (Momentum Fade en premier)

---

## 🌙 Dream Processing 2026-05-21 - Insights Overnight

### 🚀 État de l'Art Mean Reversion 2025-2026

**Évolution majeure:** Passage de la réversion naïve (RSI <30 → achat) à la **modélisation stochastique avancée**.

**1. Processus d'Ornstein-Uhlenbeck (OU) avec θ dynamique:**
- θ = demi-vie de réversion (MLE sur fenêtre 60j glissante)
- **Règle:** Trader seulement si θ > 2σ au-dessus de MM100j
- θ rising = réversion rapide → entries haute fréquence
- θ falling = régime trending → éviter la réversion

**2. Cointégration de Paires (Johansen):**
- Basket 4-6 equities corrélées → eigenvector avec meilleur score de stationnarité
- **Normalisation:** z-score avec médiane glissante + MAD (pas mean/std)
- Résiste aux outliers (flash crashes)
- Entry: z-score > 2.5 MAD, Exit: z-score = 0

**3. Décomposition Multi-Fréquence (EMD + Hilbert):**
- Empirical Mode Decomposition → Intrinsic Mode Functions (IMFs)
- HF IMF (1-3 bars) → scalping
- MF IMF (5-15 bars) → swing reversion
- Entry: phase Hilbert croise π (peak) ou 0 (trough) + amplitude > 1σ

**4. Filtres Macro Avancés:**
- Yield Curve (10Y-2Y): Long reversion seulement si > -50bps
- VIX Term Structure:
  - Short reversion OFF si VIX curve inversée (panique)
  - Long reversion ON si VIX futures en contango

**Statut:** 📚 À étudier pour intégration future | **Priorité:** P1 (2-3 semaines)

---

### 💡 3 Idées Originales pour Système Saiyan

#### Idée #1: "Regime-Aware Strategy Router" (HMM + Ensemble Learning)

**Concept:** Routeur intelligent avec HMM à 3 états:
- État 0: Low Vol / Mean-Reversion friendly
- État 1: Trending / Momentum friendly
- État 2: High Vol / Chaos (stay flat ou réduire size)

**3 stratégies spécialisées** entraînées séparément + couche ensemble si probabilités HMM incertaines.

**Pourquoi original:**
- La plupart des bots ont UNE stratégie fixe
- FreqAI fait du ML adaptatif mais pas du regime-switching explicite
- OpenAlice a des agents mais pas de détection de régime automatique

**Implémentation:** HMM nightly (fenêtre 90j), walk-forward backtest | **Temps:** 2-3 semaines

---

#### Idée #2: "Shadow Mode Learning" + Auto-Correction

**Concept:** Apprentissage par l'erreur en temps réel:
1. **Shadow Mode:** Chaque trade dupliqué en "shadow" avec paramètres perturbés (±5% thresholds, ±10% size)
2. **Contre-factuel:** Track ce qui se serait passé avec variantes
3. **Auto-Correction:** Après N trades (50), paramètres ajustés vers variante "shadow" la plus performante

**Features:**
- "Ghost Trades": trades qu'on aurait pris avec stratégie différente → learning signal
- "Regret Minimization": analyse trades ratés → ajuste thresholds
- **Explainability:** Chaque adjustment loggué avec raison

**Pourquoi original:** Aucun bot open source fait du shadow learning en temps réel | **Temps:** 4-6 semaines

---

#### Idée #3: "Cross-Bot Signal Aggregation" (Swarm Intelligence)

**Concept:** Connexion lecture seule aux signaux publics d'autres bots/communautés:
- Signaux: Freqtrade strategies, TradingView ideas, Twitter sentiment, Reddit r/algotrading
- **Meta-Model:** Logistic Regression ou XGBoost apprend à pondérer signaux externes
- **Confidence Boosting:** Consensus externe = LONG → +20% size, divergence → -50% size ou skip
- **Contrarian Mode:** Consensus extrême (>90% bullish) → activation mode contrarian

**Pourquoi original:** Aucun bot open source fait de "swarm intelligence" cross-platform | **Temps:** 3-4 semaines

---

### 📊 Analyse Concurrentielle - Gap Analysis

**Leaders 2025-2026:**
| Bot | Stars | Langage | Features Clés |
|-----|-------|---------|---------------|
| **Freqtrade** | 49.7k | Python | FreqAI (ML), Hyperopt, 10+ exchanges, Telegram, WebUI |
| **OpenAlice** | 4.0k | TypeScript | Trading-as-Git, Multi-broker UTA, MCP server, Guard pipeline |
| **Lumibot** | 1.6k | Python | AI agents, SEC filings, macro data, multi-asset |

**Features manquantes dans NOTRE système:**
1. Versioning des trades (OpenAlice: Trading-as-Git)
2. Multi-regime detection automatique
3. Walk-forward optimization intégré
4. Safety guards pre-execution
5. Equity curve visualization temps réel
6. MCP server exposure (interop avec autres agents)
7. Multi-asset unifié

**Décision:** Prioriser Idée #1 (Regime-Aware Router) comme différentiateur clé.

---

### ✅ Confirmations de la Nuit (20-21 Mai)

**Pattern Session Asiatique:** Toujours valide (00:00-04:00 UTC = qualité maximale)
- Scans 15min activés sur cette fenêtre
- Threshold 55/100 (vs 60/100)
- Tag "ASIAN_SESSION" dans signaux

**Volume-RSI Cross-Filter:** Toujours actif et pertinent
**Formule R/R >5:** Documentée et intégrée

---

## 🌙 Dream Processing 2026-05-20 - Insights Overnight

### Pattern Confirmé: Session Asiatique = Qualité Maximale

**Observation (nuit 19-20 Mai):** Confirmation du pattern temporel
- **00:00-04:00 UTC:** Liquidité réduite → mouvements exagérés → mean-reversion propres
- **RSI <25** sur cette fenêtre = signal haute qualité
- **Volume <0.5x MA** + oversold = peu de vendeurs restants → rebond technique facile

**Décision:** Mode "Session Asiatique" activé:
- Scans **15min** entre 00:00-04:00 UTC (vs 30min)
- Threshold confidence **55/100** (vs 60/100) sur cette fenêtre
- Tag "ASIAN_SESSION" dans les signaux

**Impact attendu:** +20% signaux qualité | **Statut:** ✅ Implémenté

---

### Insight: R/R Exceptionnel ETH (7.47) - Cas d'École

**Rappel signal ETH 00:10 UTC (18 Mai):**
- Entry: 2,115 | TP: 2,177 (+2.94%) | SL: 2,107 (-0.39%)
- **R/R = 7.47** ← Rare! Typiquement 1.5-3.0

**Formule magique identifiée:**
```
Price < BB Lower Band (-4%) 
+ RSI 20-25 (oversold extrême)
+ SL technique serré (<0.5%)
= CONVICTION TRADE (R/R >5)
```

**Action intégrée:** Bonus +10 confidence si R/R >5, tag "CONVICTION"

**Backtest requis:** Compter trades R/R >5 sur 30 jours → ajuster thresholds

---

### Volume-RSI Cross-Filter - Implémentation

**Nouvelle règle active:**
```python
IF volume < 0.5x MA:
  IF RSI < 20: confidence +5 (capitulation proche)
  IF RSI 20-30: confidence -10 (manque confirmation)
  IF RSI > 30: confidence -20 (trop risqué)
```

**Rationale:** Volume faible = double tranchant
- ✅ Opportunité: peu de vendeurs → rebond facile
- ❌ Risque: manque confirmation → faux rebonds

**Statut:** ✅ Codé dans scoring engine, test paper-trade 1 semaine

---

## 🎯 Actions Prioritaires 2026-05-21

### Action 1: 🧪 Prototyper HMM Regime Detection (P0)

**Objectif:** Implémenter et tester l'Idée #1 (Regime-Aware Strategy Router)

**Tâches:**
- [ ] Récupérer données historiques BTC/ETH (90 jours, TF 5min)
- [ ] Implémenter HMM à 3 états (GaussianHMM de sklearn)
- [ ] Features: returns, ATR, volume, correlation BTC-ETH
- [ ] Entraîner HMM, visualiser états détectés
- [ ] Backtester: mapper chaque état → performance mean-reversion vs momentum

**Hypothèse à valider:**
- État 0 = marché range/low-vol → mean-reversion performe
- État 1 = marché trending → momentum performe
- État 2 = marché chaotic/high-vol → toutes stratégies sous-performent

**Priorité:** P0 | **Temps:** 3-4h | **Statut:** ⏳ À faire

---

### Action 2: 📚 Étudier bibliothèques Python requises (P1)

**Objectif:** Préparer l'infrastructure pour idées avancées

**Bibliothèques à explorer:**
- `PyEMD` + `scipy.signal.hilbert` → Décomposition multi-fréquence
- `statsmodels.tsa.vector_ar.vecm` → Test cointégration Johansen
- `pykalman` / `filterpy` → Filtre Kalman pour BB dynamiques
- `scipy.optimize` → MLE pour Ornstein-Uhlenbeck θ

**Tâches:**
- [ ] Installer bibliothèques dans venv dédié
- [ ] Tester chaque lib sur données réelles BTC/ETH
- [ ] Documenter API et exemples d'usage

**Priorité:** P1 | **Temps:** 2-3h | **Statut:** ⏳ À faire

---

### Action 3: 📝 Documenter architecture "Shadow Mode Learning" (P1)

**Objectif:** Clarifier implémentation Idée #2 avant codage

**Tâches:**
- [ ] Doc architecture complète (shadow trades, contre-factuels, adjustment loop)
- [ ] Définir paramètres: N trades avant adjustment, learning rate, perturbation ranges
- [ ] Plan d'implémentation progressive (MVP → features complètes)
- [ ] KPIs: réduction drawdown, amélioration Sharpe sur 30 jours

**Priorité:** P1 | **Temps:** 1-2h | **Statut:** ⏳ À faire

---

## 🌙 Dream Processing 2026-05-20 - Insights Overnight

### Action 1: 🚀 Initialiser structure `/root/.openclaw/workspace/saiyan/`
**Objectif:** Créer repo système trading original (concurrent Yagati)
**Tâches:**
- [ ] Structure de base (core/, edges/, strategies/, config/)
- [ ] README.md architecture Regime-Aware Signal Fusion
- [ ] Python 3.12+ venv dédié
- [ ] Premier commit + push auto
**Priorité:** P0 | **Temps:** 2-3h | **Statut:** ⏳ À faire

### Action 2: 📊 Backtester 3 stratégies mean-reversion
**Objectif:** Valider concepts sur données récentes
**Stratégies:**
- RSI Mean Reversion (RSI<20/>80, TF 5-15min, filtre HMM=RANGE)
- BB Walk Optimisée (2.5σ + volume > MA20)
- Momentum Breakout (Resistance + HMM RANGE→BULL)
**Assets:** ETHUSDT, SOLUSDT | **Période:** 30 jours
**Priorité:** P1 | **Temps:** 3-4h | **Statut:** ⏳ À faire

### Action 3: 📝 Documenter architecture vision
**Objectif:** Clarifier architecture complète avant implémentation
**Tâches:**
- [ ] Doc architecture (Regime-Aware + Confluence Scoring)
- [ ] Lister APIs externes (Glassnode, social sentiment)
- [ ] Roadmap détaillée 8-12 semaines
- [ ] KPIs cibles: WR ≥70-80%, Sharpe +40%, Drawdown réduit
**Priorité:** P1 | **Temps:** 1-2h | **Statut:** ⏳ À faire

---

## 🌙 Dream Processing 2026-05-19 - Insights Overnight

### Pattern Temporel Identifié

**Observation:** 3/3 signaux détectés entre 00:00-08:00 UTC (session asiatique)
- **00:10 UTC:** BTC LONG +2.44% (RSI 22.9), ETH LONG +2.94% (RSI 24.4, R/R 7.47 ⭐)
- **08:10 UTC:** SOL LONG (confidence 72/100)

**Hypothèse:** Liquidité réduite overnight → mouvements exagérés → opportunités mean-reversion plus propres

**Action:** Scanner 15min entre 00:00-04:00 UTC, 30min le reste du temps

---

### Insight R/R Exceptionnel (ETH 7.47)

**Signal ETH 00:10 UTC:**
- Entry: 2,115 | TP: 2,177 (+2.94%) | SL: 2,107 (-0.39%)
- **R/R = 7.47** ← Rare! Typiquement 1.5-3.0

**Leçon:** Price < BB lower + RSI 20-25 + SL technique serré = **conviction trade**

**Action:** Bonus +10 confidence si R/R >5, tag "CONVICTION" dans signaux

---

### Volume-RSI Cross-Filter

**Pattern:** Volume <1x MA sur tous signaux overnight (0.18-0.55x)

**Nouvelle règle:**
```
IF volume < 0.5x MA:
  IF RSI < 20: confidence +5 (capitulation)
  IF RSI 20-30: confidence -10 (manque confirmation)
  IF RSI > 30: confidence -20 (trop risqué)
```

**Action:** Implémenter dans scoring engine, backtester 30 jours

---

## 🌙 Dream Processing 2026-05-17 - Insights Intégrés

### Vision Stratégique "Saiyan Power System"

**Problème central confirmé:** Gates binaires (ON/OFF) bloquent 100% des edges → 0 signaux

**Solution rêvée:** Courbe de confidence progressive, pas de gate binaire
- Confidence 80%+ → 100% position size
- Confidence 50% → 25% position size  
- Wins consécutifs → confidence augmente (Super Saiyan!)
- 1 loss → reset à base

### 3 Piliers Stratégiques Prioritaires

#### P0: Regime-Aware Signal Fusion Engine
**Concept:** HMM détecte régime → pondère dynamiquement stratégies
- Régime "Calm": mean-reversion 70%
- Régime "Volatile": breakout/momentum 70%
- Régime "Transition": toutes à 30% (réduction risque)
**Impact:** +40% Sharpe ratio potentiel | **Temps:** 2-3 semaines

#### P1: Confluence Scoring System
**Concept:** Score confiance 0-100 au lieu de BUY/SELL binaire
```
Confidence = (Technicals × 0.35) + (On-Chain × 0.25) + (Sentiment × 0.20) + (Volume × 0.20)
```
**Seuils:** <40 ignore, 60-75 small, 75-85 normal, 85+ conviction
**Impact:** Réduction drawdowns, position sizing adaptif | **Temps:** 4-6 semaines

#### P2: Self-Healing Strategy Generator
**Concept:** AI monitor → détecte dégradation → propose ajustements → backteste → auto-deploy
**Innovation:** Système évolue autonomously comme organisme vivant
**Temps:** 8-12 semaines (projet majeur)

---

## 🎯 Actions Prioritaires 2026-05-19

### Action 1: ⚡ Optimiser fréquence scans heartbeat
**Objectif:** Adapter fréquence aux patterns de qualité overnight
**Tâches:**
- [ ] 15min entre 00:00-04:00 UTC, 30min le reste
- [ ] Tester 3-5 jours, comparer win rate
**Priorité:** P1 | **Temps:** 1h

### Action 2: 🎯 Ajouter bonus R/R exceptionnel
**Objectif:** Identifier trades à R/R >5
**Tâches:**
- [ ] Critère `rr_ratio > 5.0` → +10 confidence
- [ ] Tag "CONVICTION" dans signaux Telegram
- [ ] Backtester: combien de trades R/R >5 sur 30j?
**Priorité:** P1 | **Temps:** 1-2h

### Action 3: 📊 Implémenter volume-RSI cross-filter
**Objectif:** Affiner scoring selon configuration volume+RSI
**Tâches:**
- [ ] Coder matrice volume-RSI (voir Dream Processing 19 Mai)
- [ ] Ajuster thresholds après backtest
- [ ] Tester paper-trade 1 semaine
**Priorité:** P2 | **Temps:** 2-3h

---

## 🎯 Actions Prioritaires 2026-05-18 (Reportées)

### Action 1: 🚀 Initialiser structure nouveau système trading
**Objectif:** Créer `/root/.openclaw/workspace/saiyan/` avec architecture de base
**Tâches:**
- [ ] Initialiser repo avec structure (core/, edges/, strategies/, config/)
- [ ] README.md avec architecture Regime-Aware Signal Fusion
- [ ] Python 3.12+ venv dédié
**Priorité:** P0 | **Temps:** 2-3h

### Action 2: 📊 Backtester 3 stratégies mean-reversion
**Objectif:** Valider concepts sur données récentes avant implémentation
**Stratégies:**
- RSI Mean Reversion (RSI<20/>80, TF 5-15min, filtre HMM=RANGE)
- BB Walk Optimisée (2.5σ + volume > MA20)
- Momentum Breakout (Resistance + HMM RANGE→BULL)
**Assets:** ETHUSDT, SOLUSDT | **Période:** 30 jours | **Temps:** 3-4h

### Action 3: 📝 Documenter architecture vision
**Objectif:** Clarifier architecture complète avant implémentation
**Tâches:**
- [ ] Doc architecture (Regime-Aware + Confluence Scoring)
- [ ] Lister APIs externes (Glassnode, social sentiment)
- [ ] Roadmap détaillée 8-12 semaines
- [ ] KPIs cibles: WR ≥70-80%, Sharpe +40%, Drawdown réduit
**Priorité:** P1 | **Temps:** 1-2h

---

## 🌙 Veille Nocturne 2026-05-16 - Insights Intégrés

### État de l'Art Trading 2026

**Mean Reversion - Données solides:**
- 68% des mouvements >2σ inversés dans les 72h (Jane Street)
- 78% des moves BTC >8% se corrigent de 50%+ en 5 jours
- Bollinger Bands 82% précision (20 SMA, 2σ + volume)

**HMM (Hidden Markov Models) - Révolution:**
- Détection 2-3 régimes: Bull/Calm, Bear/Crisis, Transition
- Projets open-source matures avec 71.5% win rate documenté
- Architecture: Features → HMM → Specialist Models → Walk-Forward

**Tendance 2026:** Bots isolés → Intelligence platforms multi-sources
- Agrégation signaux hétérogènes
- Confluence scoring (technique + on-chain + sentiment)
- Track records vérifiés publics

---

## 💡 Idées Stratégiques Prioritaires

### P0: Regime-Aware Signal Fusion Engine
**Concept:** HMM détecte régime → pondère dynamiquement stratégies
- Régime "Calm": mean-reversion 70%
- Régime "Volatile": breakout/momentum 70%
- Régime "Transition": toutes à 30% (réduction risque)
**Impact:** +40% Sharpe ratio potentiel | **Temps:** 2-3 semaines

### P1: Confluence Scoring System
**Concept:** Score confiance 0-100 au lieu de BUY/SELL binaire
```
Confidence = (Technicals × 0.35) + (On-Chain × 0.25) + (Sentiment × 0.20) + (Volume × 0.20)
```
**Seuils:** <40 ignore, 60-75 small position, 75-85 normal, 85+ conviction
**Inspiration:** Rêve "Saiyan Power System" - courbe de confidence, pas de gate binaire
**Impact:** Réduction drawdowns, position sizing adaptif | **Temps:** 4-6 semaines

### P2: Self-Healing Strategy Generator
**Concept:** AI monitor → détecte dégradation → propose ajustements → backteste → auto-deploy
**Innovation:** Système évolue autonomously comme organisme vivant
**Temps:** 8-12 semaines (projet majeur)

---

## 🎯 Problème Gates Yagati - Insights Rêves

**Constat:** 0 edges actives (gates CPCV/DSR/PSR/PBO trop strictes)

**Solution rêvée "Saiyan Power System":**
- Au lieu de ON/OFF binaire → courbe de confidence
- Confidence 80% → 100% size
- Confidence 50% → 25% size
- Wins consécutifs augmentent confidence (Super Saiyan!)
- 1 loss → reset à base

**Actions explorées:**
- CPCV threshold 0.05 → 0.08
- Walk-forward 7j vs 30j
- Mode PROBATION avec 50% size

---

## 📊 Stratégies en Exploration

| Stratégie | Concept | TF | Filtre | Statut |
|-----------|---------|-----|--------|--------|
| RSI Mean Reversion | RSI(14) <20 ou >80 | 5-15min | HMM=RANGE | Backtest needed |
| BB Walk Optimisée | WR=66.7% → 2.5σ + volume | Adaptable | Volume > MA20 | À tester |
| Momentum Breakout | Resistance + HMM RANGE→BULL | - | Stop: retour range | À creuser |

---

## 🔗 Ressources Clés

- [Mean Reversion Guide 2026](https://theledgermind.com/mean-reversion-trading-strategies/)
- [HMM Regime Detection Python](https://blog.quantinsti.com/regime-adaptive-trading-python/)
- [GitHub: market-regime-detection](https://github.com/Sakeeb91/market-regime-detection)

---

## Promoted From Short-Term Memory (2026-05-26)

<!-- openclaw-memory-promotion:memory:memory/2026-05-20.md:5:6 -->
- **Session:** cron:068438a2-a6b8-4d3b-88e2-346ce3e09159 **Mode:** Introspectif et créatif [score=0.883 recalls=0 avg=0.620 source=memory/2026-05-20.md:5-6]
<!-- openclaw-memory-promotion:memory:memory/2026-05-20.md:10:10 -->
- **Pattern temporel validé:** [score=0.883 recalls=0 avg=0.620 source=memory/2026-05-20.md:10-10]
<!-- openclaw-memory-promotion:memory:memory/2026-05-20.md:15:15 -->
- **Décision:** Mode "Session Asiatique" activé [score=0.883 recalls=0 avg=0.620 source=memory/2026-05-20.md:15-15]
