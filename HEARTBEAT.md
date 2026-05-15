# Heartbeat Checklist - Trading Autonomous System

## 🎯 Mission
Développer MON système trading concurrent de Yagati (Yagati v4 est INTouchable)

## ✅ Checks Périodiques (toutes les 30min)

### Marchés
- [ ] BTC, ETH, SOL régimes HMM (BULL/RANGE/BEAR)
- [ ] Volatilité 24h (si >10% → alerte)
- [ ] Funding rates anormaux

### Système Trading
- [ ] Signaux auto générés depuis dernier check
- [ ] Performance edges (WR, PnL, n_trades)
- [ ] Gates de robustesse (CPCV, DSR, PSR, PBO) - blocages ?

### Background Tasks
- [ ] Sub-agents en cours → status
- [ ] Cron jobs exécutés → résultats
- [ ] Tâches échouées → retry/alert

### Mémoire & Rêves
- [ ] Nouveaux rêves/insights à consolider
- [ ] MEMORY.md à mettre à jour
- [ ] Actions concrètes identifiées

## 📝 Notes du Jour
_(À remplir pendant la journée)_

---

**Si rien à signaler → HEARTBEAT_OK**
**Si urgent → Message détaillé à W**
