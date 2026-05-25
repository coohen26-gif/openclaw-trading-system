# Semaine 30 - Validation sur Données Réelles (25 Mai 2026)

**Date:** 25 Mai 2026, 09:00 UTC  
**Statut:** 🟡 EN COURS - Problème génération signaux identifié

---

## 🎯 Objectif

Valider Mean Reversion v2 sur **données réelles BTC** (vs données synthétiques précédentes)

**Configuration testée:**
- RSI: 35/65
- Bollinger: 2.5σ
- TP: +8%, SL: -5%
- Time Exit: 10j max
- Position: 8%

---

## 📊 Résultats

### Données Réelles Fetchées ✅

- **Source:** Binance API
- **Période:** 2020-01-01 → 2026-05-25 (2337 jours)
- **Prix:** $4,800 → $124,658 (+2500%)
- **Fichier:** `learning/data/btc_usdt_daily.csv`

### Backtest v2 (RSI 35/65 OR BB 2.5σ)

| Période | Return | Sharpe | Max DD | Win Rate | N Trades |
|---------|--------|--------|--------|----------|----------|
| **Train (2020-2023)** | -0.68% | -7.52 | -0.68% | 0% | 1 |
| **Test (2024-2026)** | **+0.71%** | -4.71 | -0.00% | **100%** | 1 |

**Verdict:** 🟢 Test positif, MAIS **1 trade seulement** → stats non significatives

### Backtest v3 (RSI 40/60 OR BB 2.0σ)

| Période | Return | Sharpe | Max DD | Win Rate | N Trades |
|---------|--------|--------|--------|----------|----------|
| **Train** | +0.17% | -27.17 | -0.00% | 100% | 1 |
| **Test** | +0.11% | -32.40 | -0.00% | 100% | 1 |

**Verdict:** 🟡 Positif mais **1 trade** → insuffisant

### Backtest v4 (RSI 45/55 OR BB 1.5σ - Scalp)

| Période | Return | Sharpe | Max DD | Win Rate | N Trades |
|---------|--------|--------|--------|----------|----------|
| **Train** | +0.08% | 0.42 | -0.00% | 100% | 1 |
| **Test** | +0.09% | 0.54 | -0.00% | 100% | 1 |

**Verdict:** 🔴 **1 trade** → échec génération signaux

---

## 🔍 Problème Identifié

**Toutes les configurations génèrent 1 trade seulement!**

**Cause probable:** Logique de position unique (pas de ré-entry après exit)

**Code actuel:**
```python
if row['signal'] != 0 and position is None:
    # Enter position
```

**Problème:** Une fois la position fermée, `position = None` mais le signal n'est plus capté correctement.

---

## 🛠️ Solution: v5 (Multi-Trades)

**Changement clé:** Permettre ré-entry immédiate après exit

**Configuration v5:**
- RSI: 30/70 (plus strict que v4)
- Bollinger: 2.0σ
- TP: +4%, SL: -3%
- Time Exit: 5j
- Position: 5%
- **Cooldown: 0j** (ré-entry immédiate)

**Logique:**
```python
# Exit
if exit_reason:
    capital += trade_pnl
    position = None
    # Pas de cooldown → peut re-enter immédiatement

# Enter
if row['signal'] != 0 and position is None:
    position = {...}
```

---

## 📋 Prochaines Étapes

1. **Créer v5** (multi-trades, cooldown 0)
2. **Tester v5** → objectif: 20+ trades test
3. **Si OK:** Telegram Signaler integration
4. **Si KO:** Debug logique signaux

---

## 💡 Insights

1. **Données synthétiques ≠ réelles:** Backtests précédents (synthétiques) avaient 40-100 trades. Réelles = 1 trade → logique buguée.

2. **Toutes configs échouent:** v2, v3, v4 = 1 trade → problème structurel, pas configuration.

3. **Sharpe négatifs:** Volatilité equity curve très basse (quasiment pas de trades) → Sharpe undefined/négatif.

---

*Mis à jour: 25 Mai 2026, 09:03 UTC*
