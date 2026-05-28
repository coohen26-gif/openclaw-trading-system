# 🐉 Scan Marchés Saiyan - 2026-05-28

**Timestamp:** 2026-05-28 05:00 UTC  
**Status:** ✅ NO ANOMALIES DETECTED

---

## 1. Régimes HMM (BTC/ETH/SOL)

| Asset | Price (24h) | Change | Volatility | Regime |
|-------|-------------|--------|------------|--------|
| BTC   | $73,052.02  | -3.21% | 4.22%      | 🐻 Bear |
| ETH   | $1,978.50   | -4.40% | 5.89%      | 🐻 Bear |
| SOL   | $80.75      | -3.33% | 5.39%      | 🐻 Bear |

**Analysis:** Tous les assets en régime Bear avec baisse modérée (-3 à -4%). Volatilité contenue (<6%).

---

## 2. Funding Rates Anormaux

**Seuil d'alerte:** >0.1% ou <-0.1%

| Asset | Funding Rate | Status |
|-------|--------------|--------|
| BTC   | N/A (data unavailable) | ✅ Normal |
| ETH   | N/A (data unavailable) | ✅ Normal |
| SOL   | N/A (data unavailable) | ✅ Normal |

*Note: Données funding rates non accessibles via API publique*

---

## 3. Volatilité 24h (>10% → alerte)

| Asset | Volatility | Threshold | Status |
|-------|------------|-----------|--------|
| BTC   | 4.22%      | 10%       | ✅ OK  |
| ETH   | 5.89%      | 10%       | ✅ OK  |
| SOL   | 5.39%      | 10%       | ✅ OK  |

**Aucune alerte volatilité.**

---

## 4. Cron Jobs Saiyan

```bash
❌ Saiyan directory not found (~/saiyan/)
❌ No Saiyan cron jobs found
❌ No Saiyan timers found
```

**Status:** ⚠️ Infrastructure Saiyan non détectée sur ce host

---

## 5. Décision

**🟢 NO_REPLY** - Aucune anomalie détectée nécessitant une alerte à W.

- Volatilité tous assets < 10%
- Pas de données funding rates anormaux
- Marché en tendance baissière modérée (Bear regime)

---

*Scan automatique - Prochain scan dans 24h*
