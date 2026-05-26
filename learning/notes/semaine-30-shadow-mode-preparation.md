# Semaine 30 - Shadow Mode Preparation

**Date:** 26 Mai 2026  
**Phase:** Phase 3 - Production Readiness  
**Objectif:** Préparer et lancer le shadow mode 30 jours

---

## 📋 Qu'est-ce que le Shadow Mode?

Le **shadow mode** est une période de test en conditions réelles où le système:
- Reçoit les données temps réel (Binance)
- Génère des signaux de trading
- **N'exécute PAS** les trades (paper trading uniquement)
- Tracke la performance des signaux (WR, PnL, Sharpe, DD)
- Envoie des notifications Telegram pour validation humaine

**Durée:** 30 jours  
**Objectif:** Valider que les performances réelles correspondent aux backtests

---

## 🎯 Configuration Shadow Mode

### Paramètres de Trading

```python
# Asset & Timeframe
symbol = "BTC/USDT"
timeframe = "1d"  # Daily candles

# Position Sizing (conservateur pour shadow)
base_kelly = 0.25
regime_multipliers = {
    'BULL': 0.75,         # 18.75% max
    'VOLATILE_BULL': 0.5, # 12.5% max
    'RANGE': 0.25,        # 6.25% max
    'BEAR': 0.0           # OFF
}

# Stops & Targets
Bull: SL -5% / TP +15% / Trailing 5%
VolBull: SL -8% / TP +20% / Trailing 8%
Range: SL -4% / TP +6% / Trailing 3%
```

### Risk Limits

```python
# Circuit Breakers
Level 1 (Warning): -3.6% daily / -10% DD
Level 2 (Reduce): -5% daily / -15% DD → Reduce 50%
Level 3 (Stop): -8% daily / -20% DD → Stop new trades
Level 4 (Kill): -10% daily / -25% DD → Kill Switch

# Daily Loss Limit
max_daily_loss = -5%

# Max Drawdown
max_drawdown = -20%
```

---

## 🔧 Infrastructure Requise

### 1. Data Pipeline

**Binance Connector:**
- Fetch OHLCV daily (1d) à ~00:05 UTC
- Cache local (1h TTL)
- Rate limiting: 1200ms entre requêtes

**Deribit IV Fetcher:**
- Fetch IV 25d et skew Put/Call
- Cache local (1h TTL)
- Alert si IV percentile >80%

### 2. Signal Generation

**Cycle quotidien:**
1. ~00:05 UTC: Fetch nouvelles données Binance
2. ~00:10 UTC: Update HMM regime detection
3. ~00:15 UTC: Calculer signaux (si confidence ≥60%)
4. ~00:20 UTC: Envoyer notifications Telegram

**Signal Format:**
```
🟢 SIGNAL #42 — LONG BTC/USDT @ $77,159

Entry: $77,159
Stop Loss: $73,301 (-5%)
Take Profit: $88,733 (+15%)
Position: 18.75% (Bull regime)
Confidence: 72/100
Rationale: Momentum 20j > threshold, HMM Bull detected

Risk/Reward: 1:3
```

### 3. Performance Tracking

**Metrics à tracker:**
- Win Rate (cible: ≥50%)
- Avg Gain per trade (cible: 0.2-0.5%)
- Sharpe Ratio (cible: ≥0.8)
- Max Drawdown (cible: <-10%)
- N signaux/mois (cible: 10-15)

**Fichier de tracking:**
```json
{
  "shadow_mode_start": "2026-05-27",
  "signals": [
    {
      "id": 1,
      "date": "2026-05-27",
      "direction": "LONG",
      "entry": 77159,
      "exit": null,
      "exit_date": null,
      "pnl": null,
      "status": "open"
    }
  ],
  "metrics": {
    "total_signals": 0,
    "closed_trades": 0,
    "win_rate": 0,
    "avg_pnl": 0,
    "sharpe": 0,
    "max_dd": 0
  }
}
```

### 4. Notifications Telegram

**Types de messages:**
1. **Signaux trading** (🟢/🔴) - Entry/SL/TP/Position/Confidence
2. **Alertes système** (ℹ️/⚠️/🚨/🆘) - Risk levels, circuit breakers
3. **Résumés daily** (📊) - PnL, regime actuel, metrics
4. **Résumés weekly** (📈) - Performance hebdo, insights

**Rate limiting:**
- Max 1 message/sec
- Déduplication (hash SHA256, fenêtre 5min)

---

## 📅 Planning 30 Jours

### Semaine 1 (J1-J7): Validation Initiale

**Objectifs:**
- ✅ Système tourne sans bugs
- ✅ Données fetchées correctement
- ✅ Signaux générés cohérents avec backtests
- ✅ Notifications Telegram fonctionnelles

**Checkpoints:**
- J1: System startup ✅
- J3: Premier signal généré ✅
- J7: Review hebdo (WR, PnL, N signaux) ✅

### Semaine 2-3 (J8-J21): Collecte Data

**Objectifs:**
- Accumuler 10-15 signaux
- Tracker performance réelle
- Identifier anomalies/divergences vs backtest

**Checkpoints:**
- J14: Review mid-period (ajustements si besoin)

### Semaine 4 (J22-J30): Validation Finale

**Objectifs:**
- Comparer performance réelle vs backtest
- Décider: Production ✅ ou Ajustements 🔧

**Critères de succès:**
- Win Rate ≥50% ✅
- Sharpe ≥0.8 ✅
- Max DD <-10% ✅
- N signaux ≥10 ✅

**J30:** Décision finale (Production Go/No-Go)

---

## 🚨 Gestion des Anomalies

### Scénarios et Actions

| Scénario | Action |
|----------|--------|
| Bug système (crash, freeze) | Debug immédiat, restart, log erreur |
| Données manquantes | Retry avec backoff, alert si >3j manquants |
| Performance << backtest (-50%) | Pause, analyse root cause, ajustement |
| Drawdown >15% | Review risk params, possible reduction sizing |
| Telegram down | Fallback: logs locaux, retry connection |

### Escalation

**Niveau 1 (Auto):** Le système gère seul (retry, fallback)  
**Niveau 2 (Log):** Erreur loggée, notification discrète  
**Niveau 3 (Alerte):** Notification W requise (⚠️/🚨)  
**Niveau 4 (Stop):** Kill Switch activé, W doit intervenir

---

## 📊 Critères de Succès

### Performance Trading (Cible)

| Métrique | Cible | Backtest | Statut |
|----------|-------|----------|--------|
| Win Rate | ≥50% | 57.1% | 🎯 |
| Avg Gain | 0.2-0.5% | +0.43% | 🎯 |
| Sharpe | ≥0.8 | 0.91 | 🎯 |
| Max DD | <-10% | -7.5% | 🎯 |
| N signaux/mois | 10-15 | ~11 | 🎯 |

### Performance Système (Cible)

| Métrique | Cible | Statut |
|----------|-------|--------|
| Uptime | ≥99% | 🎯 |
| Data freshness | <1h delay | 🎯 |
| Signal latency | <5min après candle | 🎯 |
| Telegram delivery | ≥95% | 🎯 |

---

## 🔒 Sécurité & Compliance

### Règles de Sécurité

1. **Jamais de trading automatique** en shadow mode
2. **Toujours paper trading** (pas d'orders réels)
3. **Logs complets** de tous les signaux et décisions
4. **Backup quotidien** des données et état

### Kill Switch

**Conditions d'activation:**
- Daily loss > -10%
- Max drawdown > -25%
- Bug critique (données corrompues, etc.)
- Demande manuelle de W

**Procédure:**
1. Stop trading immédiatement
2. Close toutes les positions (si live)
3. Notification W (🆘 EMERGENCY)
4. Log complet de l'incident

---

## 📝 Checklist Pré-Lancement

### Infrastructure

- [x] Binance connector testé ✅
- [x] Deribit IV fetcher testé ✅
- [x] Telegram notifier testé ✅
- [x] Risk monitor configuré ✅
- [x] Portfolio allocator configuré ✅

### Configuration

- [x] config.json validé ✅
- [x] Params shadow mode définis ✅
- [x] Circuit breakers configurés ✅
- [x] Notifications Telegram activées ✅

### Testing

- [x] System status testé ✅
- [ ] Backtest final sur données réelles
- [ ] Simulation cycle complet (fetch → signal → notify)
- [ ] Test kill switch

### Documentation

- [x] Journal mis à jour ✅
- [x] Notes shadow mode créées ✅
- [ ] README shadow mode (optionnel)

---

## 🎯 Prochaines Étapes

**J0 (26 Mai 2026):**
- [x] Système testé et opérationnel ✅
- [ ] Backtest final validation
- [ ] Simulation cycle complet

**J1 (27 Mai 2026):**
- [ ] Lancement shadow mode officiel
- [ ] Premier signal attendu
- [ ] Log et tracking initiés

**J7 (2 Juin 2026):**
- [ ] Review hebdo #1
- [ ] Ajustements si besoin

**J30 (25 Juin 2026):**
- [ ] Review finale
- [ ] Décision Production Go/No-Go

---

**Statut:** 🟡 **PRÊT POUR LANCEMENT** (95%)

**Dernière mise à jour:** 26 Mai 2026, 20:10 UTC
