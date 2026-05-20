# Heartbeat Checklist - Trading Autonomous System

## 🎯 Mission
Développer MON système trading concurrent de Yagati (Yagati v4 est INTouchable)

## ✅ Checks Périodiques (2-3 fois/jour MAX - SILENCIEUX)

### Marchés
- [ ] BTC, ETH, SOL régimes HMM (BULL/RANGE/BEAR)
- [ ] Volatilité 24h (si >10% → alerte)
- [ ] Funding rates anormaux

### Système Trading
- [ ] Signaux générés → envoyés à W sur Telegram (W exécute manuellement)
- [ ] Performance signaux (WR cible ≥70%, PnL, n_signaux)
- [ ] Gates de robustesse (CPCV, DSR, PSR, PBO) - blocages ?

### Background Tasks
- [ ] Sub-agents en cours → status
- [ ] Cron jobs exécutés → résultats
- [ ] Tâches échouées → retry/alert

### Mémoire & Rêves
- [ ] Nouveaux rêves/insights à consolider
- [ ] MEMORY.md à mettre à jour
- [ ] Actions concrètes identifiées

## 📊 Performance Targets

| Métrique | Cible | Actuel |
|----------|-------|--------|
| Win Rate | ≥70% | -- |
| Avg Gain | 0.2-0.5% | -- |
| n_signaux/jour | 2-5 | -- |
| Confidence min | 60/100 | -- |

## 📝 Notes du Jour
_(À remplir pendant la journée)_

### 2026-05-17 00:38 UTC - Scan HEARTBEAT
- ✅ Signal LONG BTC/USDT détecté (confidence 64/100)
- ✅ Telegram envoyé avec succès à W
- Prix entry: 78207.93 USDT
- TP: 79472.70 (+1.6%), SL: 76210.85 (-2.5%)
- Régime HMM: RANGE (optimal)

---

## 📢 Règle de Communication

**SILENCE PAR DÉFAUT** - Ne parle à W que si :
- ✅ Signal trading détecté (confidence ≥60/100)
- ⚠️ Urgence/anomalie système
- 📊 Résumé quotidien/hebdo programmé
- ❓ W pose une question

**Sinon → NO_REPLY** (pas de message, pas de HEARTBEAT_OK)

### 🕐 Fréquence des checks
- **Scan marchés** : 1x/jour (7h) + scan léger midi (optionnel)
- **Health check système** : 2x/jour (matin/soir)
- **Recherche/Dream processing** : Nuit (pas de notification)
- **Gateway watchdog** : 1x/jour (pas de notification si OK)
