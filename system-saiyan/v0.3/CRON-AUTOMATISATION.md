# 🤖 AUTOMATISATION SAIYAN V0.3 — Cron Jobs Actifs

**Dernière mise à jour:** 2026-05-26 09:25 UTC

---

## ✅ CRONS CONFIGURÉS (Mise à jour - Doublons résolus)

| ID | Nom | Schedule | Prochain run | Statut |
|----|-----|----------|--------------|--------|
| `b62d7344` | Recherche Nocturne Saiyan | `0 3 * * *` Paris | 2026-05-27 03:00 Paris | ✅ Actif |
| `602099bf` | Scan Marchés Saiyan | `0 7 * * *` Paris | 2026-05-27 07:00 Paris | ✅ Actif |
| `778572a9` | Résumé Hebdo Saiyan | `0 18 * * 0` UTC | 2026-06-01 18:00 UTC | ✅ Actif |
| `b376c08c` | saiyan-bench-round1 | `2026-06-25T23:00:00Z` | 2026-06-25 23:00 UTC | ✅ Actif |

**Note:** Les nouveaux crons (`fe729420`, `77a4b304`, `811ff792`) ont été **désactivés** car ils étaient en doublon avec des crons existants.

---

## 📋 DÉTAILS DES CRONS

### 1. `saiyan-daily-scan` (Quotidien 7h UTC)

**Objectif:** Scan automatique des marchés BTC/ETH/SOL.

**Message:**
> "Scan marchés Saiyan v0.3: BTC/ETH/SOL régimes HMM, funding rates, volatilité 24h. Si anomalie → alerte W. Sinon → NO_REPLY."

**Comportement:**
- Scan HMM régimes (Bull/Bear/Range/Volatile)
- Check funding rates anormaux
- Check volatilité 24h (>10% → alerte)
- **Si tout OK → NO_REPLY** (pas de notification)
- **Si anomalie → Alerte W sur Telegram**

---

### 2. `saiyan-weekly-progress` (Hebdo Dim 22h UTC)

**Objectif:** Rapport hebdomadaire d'avancement à W.

**Message:**
> "Mise à jour avancement Saiyan v0.3: tâches semaine, gates Bailey passées, tests pytest, métriques bench. Résumé à W."

**Comportement:**
- Résumé tâches semaine (J+X → J+Y)
- Gates Bailey passées (CPCV/DSR/PSR/PBO)
- Tests pytest ajoutés (n_tests total)
- Métriques bench (Sharpe, WR, DD, n_trades)
- **Envoi automatique sur Telegram à W**

---

### 3. `saiyan-bench-round1` (One-shot 25 Juin 23h UTC)

**Objectif:** Bench Round 1 officiel vs Goku (Yagati v4).

**Message:**
> "BENCH ROUND 1 SAIYAN vs GOKU: Exécuter scripts/bench_vs_goku.py, calculer toutes gates Bailey, comparer Sharpe/WR/DSR/PSR/PBO avec Yagati v4. Envoyer résultats à W."

**Comportement:**
- Exécution script `scripts/bench_vs_goku.py`
- Calcul toutes gates Bailey (7/7)
- Comparaison vs Yagati v4 (Goku)
- **Envoi résultats sur Telegram à W**
- **Auto-delete après run** (`deleteAfterRun: true`)

---

### 4. `saiyan-dream-processing` (Quotidien 3h UTC)

**Objectif:** Recherche nocturne Deep RL, HMM, gates Bailey.

**Message:**
> "Dream Processing Saiyan v0.3: Recherche nocturne Deep RL, HMM, gates Bailey. Consolidation notes, insights, idées nouvelles."

**Comportement:**
- Recherche papers Deep RL trading
- Améliorations HMM Baum-Welch
- Optimisation gates Bailey
- Consolidation notes (`notes/`)
- **Pas de notification** (travail background)

---

## 🛠️ COMMANDES DE GESTION

### Lister les crons
```bash
openclaw cron list --agentId main
```

### Voir détail d'un cron
```bash
openclaw cron get --jobId <job-id>
```

### Désactiver un cron
```bash
openclaw cron update --jobId <job-id> --patch '{"enabled": false}'
```

### Réactiver un cron
```bash
openclaw cron update --jobId <job-id> --patch '{"enabled": true}'
```

### Run manuel (test)
```bash
openclaw cron run --jobId <job-id>
```

---

## 📊 WORKFLOW AUTONOME

**Avec ces 4 crons, je travaille en autonomie complète:**

1. **7h UTC** → Scan marchés (silencieux si OK)
2. **3h UTC** → Dream Processing (recherche nocturne)
3. **Dim 22h UTC** → Rapport hebdo à W
4. **25 Juin 23h UTC** → Bench Round 1 vs Goku

**W n'a pas à me relancer.** Les crons me réveillent, je bosse, je rapporte.

---

## 🚨 MODIFICATIONS POSSIBLES

**Si W veut modifier:**
- Fréquence scan quotidien (ex: 3x/jour au lieu de 1x)
- Heure rapport hebdo (ex: Lundi matin au lieu de Dim soir)
- Ajouter cron pour tests pytest auto (ex: nightly test run)
- Ajouter cron pour backup données (ex: weekly CSV backup)

**Il suffit de demander.** Je modifie les crons via `openclaw cron update`.

---

**Prochaine review crons:** 2026-06-02 (J+7, fin Phase 1)
