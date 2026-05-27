# 🐉 Saiyan Market Scan - 2026-05-27

**Scan Time:** 05:00 UTC  
**Status:** ✅ NO ANOMALIES DETECTED

---

## 1. HMM Regime Analysis

| Asset | Price | 24h Change | Regime |
|-------|-------|------------|--------|
| BTC | ~$75,670-$76,711 | -1.26% to +1.35% | 🟡 RANGE |
| ETH | ~$2,060-$2,102 | -1.51% to +0.7% | 🟡 RANGE |
| SOL | ~$83.64 | +0.5% | 🟡 RANGE |

**Assessment:** All three major assets showing low volatility, sideways movement. Classic range-bound behavior. No clear bull/bear signals.

---

## 2. Funding Rates

⚠️ **Data Unavailable** - Could not fetch real-time funding rates from exchanges. Would need direct exchange API access (Binance, Bybit, OKX) for accurate readings.

**Threshold for alert:** >0.1% (long squeeze risk) or <-0.1% (short squeeze risk)

---

## 3. Volatility Check (24h)

| Asset | 24h Move | Alert Threshold | Status |
|-------|----------|-----------------|--------|
| BTC | ~1.3% max | >10% | ✅ OK |
| ETH | ~1.5% max | >10% | ✅ OK |
| SOL | ~0.5% | >10% | ✅ OK |

**No volatility alerts triggered.** All assets well below 10% threshold.

---

## 4. Saiyan Cron Jobs Status

❌ **No Saiyan cron jobs found** on this system.

```bash
crontab -l | grep -i saiyan
# → No results
```

**Recommendation:** If automated scans are expected, cron jobs may need to be configured.

---

## 5. Anomaly Summary

| Check | Result |
|-------|--------|
| Extreme volatility (>10%) | ❌ None |
| Abnormal funding rates | ⚠️ Not checked (no API) |
| HMM regime shifts | ❌ All stable (RANGE) |
| Cron job health | ⚠️ No jobs found |

---

## Conclusion

**🟢 NO_REPLY** - Quiet market conditions. No anomalies requiring immediate alert to W.

Markets are consolidating. Good time for observation, not action.

---

*Scan completed by Bonjour 🤖*
