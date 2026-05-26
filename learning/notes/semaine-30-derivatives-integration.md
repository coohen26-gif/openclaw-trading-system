# 🎯 Master 5: Derivatives & Advanced Risk Integration

**Date:** 26 Mai 2026  
**Status:** 🔄 In Progress  
**Priority:** P0 (Production Readiness)

---

## Objectif

Intégrer les concepts de dérivés (Greeks, IV monitoring) dans le risk management du Système Saiyan.

---

## Concepts Clés (Semaine 22)

### Greeks à Surveiller

| Greek | Mesure | Impact Crypto | Threshold Saiyan |
|-------|--------|---------------|------------------|
| **Delta** | Sensibilité au prix sous-jacent | Directional risk | Monitor portfolio net delta |
| **Gamma** | Rate of change du Delta | Convexity risk | Alert si Gamma > threshold |
| **Vega** | Sensibilité à la volatilité | CRUCIAL crypto (IV 50-80%) | **Vega limit: -5% portfolio/1% IV drop** |
| **Theta** | Time decay | Impact options short | Monitor daily theta burn |
| **Rho** | Sensibilité taux | Moins pertinent crypto | Ignore pour l'instant |

### Volatilité Implicite (IV)

- **IV crypto typique:** 50-80% (vs 15-25% S&P 500)
- **Vega risk:** IV peut doubler en jours → pertes massives sur short options
- **Sources:** Deribit API (BTC/ETH options)

---

## Intégration Saiyan v0.2

### 1. Vega Risk Monitoring

```python
# Dans risk_monitor.py
def check_vega_exposure(self, portfolio_vega: float, iv_change_pct: float) -> Alert:
    """
    Check Vega exposure against IV moves.
    
    Crypto IV can double in days → massive losses on short options.
    Rule: Max -5% portfolio loss per 1% IV drop.
    """
    max_vega_loss = self.portfolio_value * 0.05  # 5% limit
    estimated_loss = portfolio_vega * (iv_change_pct / 100)
    
    if estimated_loss > max_vega_loss:
        return Alert(
            severity=AlertSeverity.CRITICAL,
            message=f"Vega exposure too high: {estimated_loss:.2f} loss for 1% IV move",
            metric="vega_limit",
            value=estimated_loss,
            threshold=max_vega_loss
        )
    return None
```

### 2. IV Monitoring (Deribit API)

```python
# Fetch IV from Deribit
async def fetch_crypto_iv(asset: str = "BTC") -> Dict:
    """
    Fetch Implied Volatility from Deribit API.
    
    Returns: {
        "asset": "BTC",
        "iv_25d": 65.2,  # 25-day IV
        "iv_50d": 72.1,  # 50-day IV
        "skew": 1.15,    # Put/Call IV ratio
        "timestamp": "2026-05-26T00:00:00Z"
    }
    """
    url = f"https://www.deribit.com/api/v2/public/get_volatility?instrument={asset}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            return data["result"]
```

### 3. Delta Monitoring

```python
# Track portfolio net delta
def calculate_portfolio_delta(positions: List[Position]) -> float:
    """
    Calculate net portfolio delta.
    
    Delta = 1.0 for long spot, -1.0 for short spot
    Delta varies for options (0 to 1 for calls, -1 to 0 for puts)
    """
    net_delta = 0.0
    for pos in positions:
        if pos.type == "spot_long":
            net_delta += pos.value
        elif pos.type == "spot_short":
            net_delta -= pos.value
        elif pos.type == "option":
            net_delta += pos.delta * pos.value
    return net_delta
```

---

## Risk Limits Proposés

| Risk Metric | Limit | Action |
|-------------|-------|--------|
| **Net Delta** | ±50% portfolio | Reduce directional exposure |
| **Vega** | -5% portfolio / 1% IV drop | Hedge with long volatility |
| **Gamma** | Alert if large negative | Monitor closely near expiry |
| **IV Percentile** | >80th percentile | Avoid short options |
| **IV Skew** | Put/Call >1.3 | Market fearful, reduce risk |

---

## Prochaines Étapes

- [ ] Ajouter Vega monitoring dans `risk_monitor.py`
- [ ] Intégrer Deribit API fetcher (IV data)
- [ ] Ajouter Delta tracking pour portfolio
- [ ] Alerts Telegram pour IV spikes
- [ ] Documentation dans `notes/semaine-30-derivatives-integration.md`

---

## Insights

1. **Vega > Delta pour crypto:** La volatilité est le risque principal, pas la direction.
2. **IV mean-reverts:** IV crypto oscille 40-100%, trader les extrêmes.
3. **Skew predictif:** Put/Call IV ratio >1.3 = market fear, souvent suivi de dips.
4. **Deribit dominance:** 80%+ options volume → reference price discovery.

---

**Status:** Module démarré, intégration en cours.
