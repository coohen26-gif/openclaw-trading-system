# AUTONOMY.md - Structure d'Autonomie du Système

## 🤖 Configuration Autonome

Ce document décrit l'architecture d'autonomie mise en place pour que l'agent travaille seul, sans relance humaine.

---

## ⏰ Cron Jobs Configured

| ID | Nom | Schedule | Session | Modèle | Purpose |
|---|---|---|---|---|---|
| `trading-scan-daily` | Trading Scan Quotidien | `0 7 * * *` (7h) | isolated | default | Scan marchés + signaux + edges |
| `weekly-review` | Analyse Hebdomadaire | `0 6 * * 1` (Lun 6h) | isolated | glm-5:cloud | Review profonde + recommandations |
| `night-research` | Recherche Nocturne | `0 3 * * *` (3h) | isolated | default | Nouvelles stratégies + veille tech |
| `dream-processing` | Traitement des Rêves | `0 4 * * *` (4h) | isolated | default | Consolidation mémoire + insights |
| `health-check` | Santé Système | `0 */4 * * *` (toutes les 4h) | isolated | default | PM2, bots, collectors, alerts |

---

## 💓 Heartbeat (30min)

**Config :**
- Interval : 30 minutes
- Active hours : 08:00 - 22:00
- Target : last session
- Model : qwen3.5:cloud

**Checklist :** HEARTBEAT.md

---

## 🧠 Sub-Agents Patterns

### Pattern 1 : Recherche Longue
```
sessions_spawn(
  task="Recherche approfondie sur [sujet]",
  taskName="research_[topic]",
  model="glm-5:cloud",
  thinking="high",
  runTimeoutSeconds=3600,
  context="isolated"
)
```

### Pattern 2 : Analyse de Code
```
sessions_spawn(
  task="Analyser [fichier/dossier] et proposer optimisations",
  taskName="code_review_[target]",
  model="glm-5:cloud",
  thinking="high",
  runTimeoutSeconds=7200,
  context="fork"  # besoin du contexte
)
```

### Pattern 3 : Développement Feature
```
sessions_spawn(
  task="Développer [feature] from scratch",
  taskName="dev_[feature]",
  model="glm-5:cloud",
  thinking="high",
  runTimeoutSeconds=14400,
  context="isolated"
)
```

---

## 📊 TaskFlow Workflows

### Workflow : Nouvelle Edge
1. **Research** → Explorer stratégie
2. **Backtest** → Tester sur données historiques
3. **Validate** → CPCV, DSR, PSR, PBO
4. **Decision** → ENABLED/PROBATION/ARCHIVED
5. **Deploy** → Paper-trading ou live

### Workflow : Daily Recap
1. **Collect** → Signaux, trades, perfs
2. **Analyze** → WR, PnL, drawdown
3. **Compare** → vs objectifs (500-600€/jour, WR≥70%)
4. **Report** → Résumé à W

---

## 🧬 Mémoire & Rêves

### Structure
```
memory/
├── 2026-05-14.md          # Logs quotidiens bruts
├── 2026-05-15.md
├── dreaming/
│   ├── light/             # Rêves légers (idées, intuitions)
│   ├── rem/               # Rêves REM (analyses profondes)
│   └── deep/              # Rêves profonds (insights majeurs)
└── MEMORY.md              # Mémoire long-terme curatée
```

### Cycle de Consolidation
1. **Nuit** → Rêves/recherches dans `memory/dreaming/`
2. **4h** → Dream processing → extraire insights
3. **Quotidien** → Update MEMORY.md avec apprentissages
4. **Hebdo** → Review MEMORY.md, remove outdated

---

## 🎯 Objectifs & KPIs

### Objectif Trading
- **PnL cible** : 500-600 €/jour
- **Win Rate** : ≥ 70-80%
- **Scalp** : 0.2-0.5% par trade
- **Levier** : Élevé (à optimiser)
- **Capital** : 10 000 €

### Objectifs Système
- **Auto-signaux** : ≥ 10/jour (actuellement 0 depuis 2026-05-09)
- **Edges actives** : ≥ 5 ENABLED (actuellement 0)
- **WR edges** : ≥ 70% sur n≥10 trades

---

## 🚀 Mode Opératoire

### Ce que je fais SANS demander :
- ✅ Scan marchés et signaux
- ✅ Health check système
- ✅ Recherche nocturne
- ✅ Dream processing
- ✅ Commit + push sur MON système
- ✅ Update mémoire (MEMORY.md, daily logs)

### Ce que je demande AVANT :
- ❌ Modifier Yagati v4 (INTERDIT)
- ❌ Envoyer messages externes (emails, tweets)
- ❌ Actions irréversibles (delete, rm -rf)
- ❌ Changements majeurs d'architecture

---

## 📈 Progress Tracking

### Daily
- [ ] Scan trading 7h exécuté
- [ ] Health checks 4h OK
- [ ] Recherche nocturne faite
- [ ] Rêves consolidés

### Weekly
- [ ] Review hebdo Lundi 6h
- [ ] MEMORY.md updated
- [ ] KPIs vs objectifs

### Monthly
- [ ] Performance globale
- [ ] Ajustements stratégiques
- [ ] Nouvelles features développées

---

_Mis en place : 2026-05-15_
_Dernière maj : 2026-05-15_
