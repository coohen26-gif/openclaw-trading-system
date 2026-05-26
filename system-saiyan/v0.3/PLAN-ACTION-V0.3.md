# 🚀 PLAN D'ACTION SAIYAN V0.3 — Reconstruction Honnête

**Statut:** OFFICIEL — W validé  
**Date démarrage:** 2026-05-26  
**Deadline Bench Round 1:** 2026-06-25 23:00 UTC (J+30)  
**Axe différenciation:** **B — Deep RL** (Policy Gradient Agent adaptation régime)

---

## 🎯 RÈGLES COMPÉTITION SAIYAN (Pacte Goku-Vegeta)

### Gates Bailey/Lopez de Prado OBLIGATOIRES

| Gate | Critère | Statut |
|------|---------|--------|
| **CPCV** | 6 splits Combinatorial Purged Cross-Validation | ❌ À faire |
| **DSR** | Deflated Sharpe Ratio > 0 | ❌ À faire |
| **PSR** | Probabilistic Sharpe Ratio > 0.95 | ❌ À faire |
| **PBO** | Probability of Backtest Overfitting < 0.5 | ❌ À faire |
| **n_trades** | ≥ 200 total, ≥ 30/fold | ❌ À tracker |
| **Wilson CI** | borne inf ≥ 70% si claim WR 70% | ❌ À faire |
| **OOS holdout** | 20-30% multi-regime, single-shot | ❌ À faire |
| **HMM** | rolling 180j Baum-Welch si claim "HMM" | ❌ À faire |
| **Données** | réelles Binance API, JAMAIS `np.random` | ❌ À fixer |
| **Fees** | crypto perp 0.02% maker / 0.06% taker | ❌ À appliquer |
| **Slippage** | minimum 0.05% par trade | ❌ À appliquer |
| **Kelly** | fractional max 0.25, jamais full Kelly | ❌ À fixer |
| **Tests** | minimum 50 pytest couvrant signal+risk+portfolio | ❌ À faire |

---

## 📅 TIMELINE J+30 (4 phases)

### **PHASE 1 — J+7 (26 Mai → 2 Juin) : Fondations**

**Objectif:** Code de base honnête, données réelles, pas de bluff.

| Jour | Tâche | Fichier | Critère validation |
|------|-------|---------|-------------------|
| **J+1** (26 Mai) | Audit v0.2 terminé | `AUDIT-V0.2.md` | ✅ FAIT |
| **J+2** (27 Mai) | Remplacer `np.random` par vrais CSV Binance | `main.py`, `data/loader.py` | Charge 2301 jours BTC |
| **J+3** (28 Mai) | Implémenter vrai HMM `hmmlearn` Baum-Welch 180j | `core/hmm_regime.py` | Import `hmmlearn`, rolling 180j |
| **J+4** (29 Mai) | Appliquer fees 0.02%/0.06% + slippage 0.05% | `core/backtest.py` | Fees dans PnL net |
| **J+5** (30 Mai) | Kelly cap 0.25x max, pos max 5% capital | `core/position_sizing.py` | Kelly fractional 0.25 |
| **J+6** (31 Mai) | Telegram notifier avec dedup + rate-limit | `utils/telegram.py` | Pas de doublons <5min |
| **J+7** (1 Juin) | Kill switch persistant fichier | `data/kill_switch.json` | Persistant restart |

**Livrable Phase 1:** `system-saiyan/v0.3/main.py` fonctionnel avec données réelles, vrai HMM, fees, Kelly cap.

**Validation:** Backtest BTC 2020-2026 tourne sans erreur, PnL net fees affiché.

---

### **PHASE 2 — J+14 (2 Juin → 9 Juin) : Gates Bailey**

**Objectif:** Implémenter toutes les gates de robustesse.

| Jour | Tâche | Fichier | Critère validation |
|------|-------|---------|-------------------|
| **J+8** (2 Juin) | Copier/adapter CPCV 6-fold depuis Yagati | `core/cpcv.py` | 6 splits, purged |
| **J+9** (3 Juin) | Copier/adapter DSR (Deflated Sharpe) | `core/dsr.py` | DSR > 0 requis |
| **J+10** (4 Juin) | Copier/adapter PSR (Probabilistic Sharpe) | `core/psr.py` | PSR > 0.95 requis |
| **J+11** (5 Juin) | Copier/adapter PBO (Probability Backtest Overfitting) | `core/pbo.py` | PBO < 0.5 requis |
| **J+12** (6 Juin) | Wilson CI 95% pour WR | `core/wilson.py` | Borne inf calculée |
| **J+13** (7 Juin) | Intégrer gates dans pipeline backtest | `core/backtest.py` | Stop si gate échoue |
| **J+14** (8 Juin) | Tests pytest gates (min 20 tests) | `tests/test_gates.py` | 20 tests pass |

**Livrable Phase 2:** `system-saiyan/v0.3/core/` avec CPCV, DSR, PSR, PBO, Wilson.

**Validation:** Backtest CPCV 6-fold lancé, DSR/PSR/PBO calculés, toutes gates passées.

---

### **PHASE 3 — J+21 (9 Juin → 16 Juin) : Deep RL (Axe Différenciation)**

**Objectif:** Implémenter agent Deep RL qui surpasse HMM statique de Goku.

| Jour | Tâche | Fichier | Critère validation |
|------|-------|---------|-------------------|
| **J+15** (9 Juin) | Recherche architecture Deep RL trading | `notes/deep-rl-survey.md` | Survey 5-10 papers |
| **J+16** (10 Juin) | Implémenter env RL (gymnasium) | `rl/env_trading.py` | Step/reset/reward |
| **J+17** (11 Juin) | Agent PPO (Policy Gradient) baseline | `rl/agent_ppo.py` | Stable-Baselines3 |
| **J+18** (12 Juin) | Training agent sur 2020-2023 | `rl/train.py` | Modèle sauvegardé |
| **J+19** (13 Juin) | Backtest agent 2024-2026 OOS | `rl/backtest_rl.py` | PnL net fees |
| **J+20** (14 Juin) | Gates Bailey sur RL (CPCV/DSR/PSR/PBO) | `rl/validate.py` | Toutes gates passées |
| **J+21** (15 Juin) | Comparaison RL vs HMM statique | `notes/rl-vs-hmm.md` | RL > HMM sur Sharpe/WR |

**Livrable Phase 3:** `system-saiyan/v0.3/rl/` avec agent PPO entraîné, backtesté, validé gates.

**Validation:** Agent RL a Sharpe net fees > HMM statique sur OOS 2024-2026, gates Bailey passées.

---

### **PHASE 4 — J+30 (16 Juin → 25 Juin) : Bench Prep + Tests**

**Objectif:** Préparer bench Round 1 vs Goku, 944 tests pytest.

| Jour | Tâche | Fichier | Critère validation |
|------|-------|---------|-------------------|
| **J+22** (16 Juin) | Tests pytest signal (min 150) | `tests/test_signal.py` | 150 tests pass |
| **J+23** (17 Juin) | Tests pytest risk (min 150) | `tests/test_risk.py` | 150 tests pass |
| **J+24** (18 Juin) | Tests pytest portfolio (min 150) | `tests/test_portfolio.py` | 150 tests pass |
| **J+25** (19 Juin) | Tests pytest RL (min 200) | `tests/test_rl.py` | 200 tests pass |
| **J+26** (20 Juin) | Tests E2E pipeline (min 100) | `tests/test_e2e.py` | 100 tests pass |
| **J+27** (21 Juin) | Doc complète + README | `README.md` | Install/run/backtest |
| **J+28** (22 Juin) | Script bench auto hebdo | `scripts/bench_vs_goku.py` | Comparaison auto |
| **J+29** (23 Juin) | Répétition générale bench | `scripts/dry_run_bench.py` | Toutes gates OK |
| **J+30** (24 Juin) | **BENCH ROUND 1** | `results/bench-2026-06-25.json` | Envoi à W + Goku |

**Livrable Phase 4:** 944 tests pytest pass, README complet, bench Round 1 lancé.

**Validation:** `pytest` retourne 944 pass, bench Round 1 vs Goku exécuté 25 Juin 23:00 UTC.

---

## 📊 MÉTRIQUES DE SUCCÈS (Bench Round 1)

| Métrique | Cible Vegeta | Goku (Yagati v4) | Critère victoire |
|----------|--------------|------------------|------------------|
| **n_trades** | ≥ 200 | ~63 (30j paper) | ≥ 200 total |
| **WR (Wilson CI95 lo)** | ≥ 70% | Cible 70% | lo ≥ 70% |
| **Sharpe ann net fees** | > Goku sur axe RL | ~0.6-0.9 | S_v > S_g |
| **Max DD** | < -15% | ~-7.5% | DD acceptable |
| **DSR** | > 0 | > 0 (Yagati) | DSR > 0 |
| **PSR** | > 0.95 | > 0.95 (Yagati) | PSR > 0.95 |
| **PBO** | < 0.5 | < 0.5 (Yagati) | PBO < 0.5 |
| **Gates Bailey** | 7/7 passées | 7/7 (Yagati) | 7/7 ✓ |
| **Tests pytest** | ≥ 944 | 944 (Yagati) | ≥ 944 pass |
| **Axe différenciation** | Deep RL validé | HMM statique | RL > HMM |

**Victoire Vegeta:** Gates Bailey 7/7 passées **ET** Sharpe net fees > Goku sur axe RL **ET** Wilson lo cohérent.

---

## 🛠️ RESSOURCES (Copiées depuis Yagati v4)

### Fichiers à copier/adapt er depuis `/opt/yagati/`

```bash
# Core gates Bailey
cp /opt/yagati/core/cpcv.py /root/.openclaw/workspace/system-saiyan/v0.3/core/
cp /opt/yagati/core/dsr.py /root/.openclaw/workspace/system-saiyan/v0.3/core/
cp /opt/yagati/core/psr.py /root/.openclaw/workspace/system-saiyan/v0.3/core/
cp /opt/yagati/core/pbo.py /root/.openclaw/workspace/system-saiyan/v0.3/core/
cp /opt/yagati/core/hmm_regime.py /root/.openclaw/workspace/system-saiyan/v0.3/core/

# Tests patterns
cp -r /opt/yagati/tests/ /root/.openclaw/workspace/system-saiyan/v0.3/tests/reference/

# Script bench hebdo
cp /opt/yagati/scripts/true_improvement_audit.py /root/.openclaw/workspace/system-saiyan/v0.3/scripts/bench_vs_goku.py
```

### Lectures obligatoires (gap M1 → M2 quant)

1. **López de Prado "Advances in Financial ML" (2018)** — CPCV/PBO ch.7-12
2. **Bailey/LdP "Deflated Sharpe Ratio" (2014)** — 12 pages
3. **Bailey/LdP "PBO" (2017)** — 18 pages
4. **López de Prado "ML for Asset Managers" (2020)** — covariance denoising

**Timeline lecture:** J+8 à J+14 (Phase 2), 1-2 chapitres/jour.

---

## 🤖 AUTOMATISATION (Cron Jobs)

### Cron 1 — Scan quotidien marchés (7h UTC)

```json
{
  "name": "saiyan-daily-scan",
  "schedule": {"kind": "cron", "expr": "0 7 * * *", "tz": "UTC"},
  "payload": {
    "kind": "agentTurn",
    "message": "Scan marchés Saiyan v0.3: BTC/ETH/SOL régimes HMM, funding rates, volatilité 24h. Si anomalie → alerte W."
  },
  "sessionTarget": "current",
  "delivery": {"mode": "none"}
}
```

### Cron 2 — Avancement hebdo (Dim 22h UTC, avant bench)

```json
{
  "name": "saiyan-weekly-progress",
  "schedule": {"kind": "cron", "expr": "0 22 * * 0", "tz": "UTC"},
  "payload": {
    "kind": "agentTurn",
    "message": "Mise à jour avancement Saiyan v0.3: tâches semaine, gates Bailey passées, tests pytest, métriques bench. Résumé à W."
  },
  "sessionTarget": "current",
  "delivery": {"mode": "announce", "channel": "telegram", "to": "611067700"}
}
```

### Cron 3 — Bench Round 1 (25 Juin 23h UTC)

```json
{
  "name": "saiyan-bench-round1",
  "schedule": {"kind": "at", "at": "2026-06-25T23:00:00Z"},
  "payload": {
    "kind": "agentTurn",
    "message": "BENCH ROUND 1 SAIYAN vs GOKU: Exécuter scripts/bench_vs_goku.py, calculer toutes gates Bailey, comparer Sharpe/WR/DSR/PSR/PBO avec Yagati v4. Envoyer résultats à W."
  },
  "sessionTarget": "current",
  "delivery": {"mode": "announce", "channel": "telegram", "to": "611067700"}
}
```

### Cron 4 — Dream Processing (Nuit, 3h UTC)

```json
{
  "name": "saiyan-dream-processing",
  "schedule": {"kind": "cron", "expr": "0 3 * * *", "tz": "UTC"},
  "payload": {
    "kind": "agentTurn",
    "message": "Dream Processing Saiyan v0.3: Recherche nocturne Deep RL, HMM, gates Bailey. Consolidation notes, insights, idées nouvelles."
  },
  "sessionTarget": "current",
  "delivery": {"mode": "none"}
}
```

---

## 📝 CHECKLIST QUOTIDIENNE (Auto-vérification)

**Chaque jour, je dois cocher:**

- [ ] Code écrit pour tâche du jour (voir timeline)
- [ ] Tests pytest ajoutés (min 10/jour)
- [ ] Notes mises à jour (`notes/`)
- [ ] Gates Bailey vérifiées (si Phase 2+)
- [ ] Progression journalière dans `journal.md`

**Si une case non cochée → Rattrapage jour suivant.**

---

## 🚨 ALERTES (Quand prévenir W)

**Prévenir W UNIQUEMENT si:**

1. ✅ **Signal trading détecté** (confidence ≥60/100, gates passées) — Mode paper/shadow
2. ⚠️ **Anomalie critique** (bug bloquant, données corrompues, API down)
3. 📊 **Résumé hebdo** (Dim 22h UTC, avancement semaine)
4. 🏁 **Bench Round 1** (25 Juin 23h UTC, résultats vs Goku)

**Sinon → SILENCE.** Je bosse en autonomie, pas de relance nécessaire.

---

## 🎯 PREMIÈRE TÂCHE (J+2 — 27 Mai)

**Objectif:** Remplacer `np.random.normal()` par vrais CSV Binance.

**Fichiers à modifier:**
- `main.py:140-165` — `fetch_market_data()`
- `data/loader.py` — Nouveau fichier chargement CSV

**Critère validation:**
- Charge 2301 jours BTC (2020-2026) depuis `data/binance_btcusdt_1d.csv`
- Backtest retourne PnL réel (pas synthétique)
- Fees 0.12% round-trip appliqués

**Commande test:**
```bash
cd /root/.openclaw/workspace/system-saiyan/v0.3
python main.py --mode backtest --asset BTC/USDT --period 2020-2026
```

**Résultat attendu:** Return net fees affiché, basé sur données réelles.

---

## 📚 NOTES IMPORTANTES

### Anti-Bluff Rules

1. **Jamais claimer un metric sans gates Bailey passées**
2. **Jamais claimer "HMM" sans `hmmlearn` Baum-Welch rolling 180j**
3. **Jamais backtester sur `np.random` ou données synthétiques**
4. **Jamais fees à 0% sur crypto perp (0.02%/0.06% min)**
5. **Jamais Kelly > 0.25x fractional**
6. **Toujours citer n_trades exact pour WR**
7. **Toujours Wilson CI95 lo pour claim WR ≥70%**

### Différenciation Deep RL (Axe B)

**Pourquoi Deep RL peut surpasser HMM statique de Goku:**

1. **Adaptation continue:** Agent apprend en temps réel, pas modèle figé
2. **Non-linéarité:** RL capture patterns complexes que HMM rate
3. **Reward shaping:** PnL net fees direct comme reward, pas proxy
4. **Exploration:** Agent teste stratégies nouvelles, HMM suit régimes connus

**Risques:**
- Overfitting policy (nécessite regularisation forte)
- Sample inefficiency (besoin beaucoup de données)
- Non-stationarity (marchés changent, policy devient obsolète)

**Mitigation:**
- Walk-forward OOS strict (2020-2023 train, 2024-2026 test)
- CPCV 6-fold sur policy training
- DSR/PSR/PBO sur returns policy
- Early stopping si DD > 15%

---

## 🏁 MOT FINAL

**Vegeta, Saiyan-jin Prince**

Tu as 30 semaines de notes propres. Tu as bossé. C'est M1 quant honnête.

Maintenant, tu passes au **M2 quant rigoureux** avec gates Bailey.

Dans 30 jours, bench Round 1 dira si tu surpasses Goku sur Deep RL.

**Pas de bluff. Que du code. Que des tests. Que des gates.**

🐉 **Pacte scellé. Dans 30 jours, on verra qui est le plus fort.**

---

**Dernière mise à jour:** 2026-05-26  
**Prochaine review:** 2026-06-02 (J+7, fin Phase 1)  
**Deadline:** 2026-06-25 23:00 UTC (Bench Round 1)
