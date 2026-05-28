# Cron Recovery Fix - Recherche Nocturne

## 🐛 Problème Identifié (Audit Claude 2026-05-28)

**Symptôme:**
- Job "Recherche Nocturne" stale age=227s
- lastProgress=model_call:started age=144s
- Qwen3.5 timeout sans recovery
- Cron perd des cycles silencieusement

**Root Cause:**
- Pas de timeout configuré sur le payload `agentTurn`
- Sub-agent tourne indéfiniment jusqu'à gateway restart
- Pas de mécanisme de retry ou fallback

---

## ✅ Solution Implémentée (2026-05-28)

### 1. Timeout Explicite

```json
{
  "payload": {
    "kind": "agentTurn",
    "timeoutSeconds": 900  // 15 minutes max
  }
}
```

**Effet:** Le sub-agent est automatiquement killé après 15min, évitant les sessions stalled.

### 2. Instructions de Sauvegarde Partielle

Message du cron mis à jour :
```
**Timeout:** 15 minutes max. Si timeout → sauvegarder progression partielle et exit propre.
```

**Effet:** L'agent sait qu'il doit checkpoint sa progression avant timeout.

### 3. Monitoring Amélioré

À ajouter (recommandé) :
- Alertes Telegram si `consecutiveErrors > 3`
- Log des durations pour détecter patterns (ex: toujours timeout à 3h)
- Fallback model si Qwen3.5 timeout répété

---

## 📊 Cron Jobs Saiyan v0.3 - État 2026-05-28

| Job | Schedule | Timeout | Status |
|-----|----------|---------|--------|
| Formation Autonome Saiyan | */4 UTC | 0 (illimité) | ✅ OK |
| **Recherche Nocturne** | **3h Paris** | **900s** | **✅ Fixé** |
| Dream Processing | 4h Paris | 0 | ✅ OK |
| Memory Promotion | 3h UTC | 0 | ✅ OK |
| Trading Scan Quotidien | 7h Paris | 0 | ✅ OK |
| Weekly Checkpoint | Sam 18h UTC | 0 | ✅ OK |
| Weekly Performance | Dim 18h UTC | 0 | ⚠️ Échec delivery |
| Résumé Hebdo Formation | Dim 18h UTC | 0 | ✅ OK |
| Analyse Hebdomadaire | Lun 6h Paris | 0 | ✅ OK |
| Monthly Backtest | 1er du mois 10h | 0 | ✅ OK |
| Bench Round 1 | 25 Juin 23h UTC | 0 | ✅ One-shot |

---

## 🔧 Recommandations Futures

### Court Terme (J+7)
- [ ] Ajouter timeout sur TOUS les cron jobs (pas juste Recherche Nocturne)
- [ ] Configurer `failureAlert` avec cooldown pour alertes Telegram
- [ ] Log duration history pour détection anomalies

### Moyen Terme (J+30)
- [ ] Retry automatique avec backoff exponentiel
- [ ] Fallback model (Qwen3.5 → Ollama local autre model)
- [ ] Dashboard monitoring cron jobs (Grafana?)

---

## 📝 Références

- Audit Claude: `audir_openclaw_par_claude---899ec068-07e0-4c36-a180-15d8bb6f144d.txt`
- Cron job ID: `b62d7344-5b4c-49b6-aedc-e5523dcfe7c8`
- Gateway config: `/root/.openclaw/openclaw.json`

---

*Fix appliqué: 2026-05-28 07:45 UTC*
*Par: Bonjour (Goku) 👋*
