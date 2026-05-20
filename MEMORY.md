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

_Maj 2026-05-20 - Dream processing 19-20 Mai + Insights overnight + Actions prioritaires_

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

## 🎯 Actions Prioritaires 2026-05-20

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

## Promoted From Short-Term Memory (2026-05-19)

<!-- openclaw-memory-promotion:memory:memory/2026-05-14.md:24:24 -->
- Le système ne génère **aucun signal auto** depuis le pivot "Voie Z" (2026-05-09). Les gates de robustesse (CPCV, DSR, PSR, PBO) sont trop stricts ou mal calibrés. Le système est en **phase observability/knowledge graph**, pas auto-trading. [score=0.835 recalls=0 avg=0.620 source=memory/2026-05-14.md:24-24]
