# Semaine 26 - Risk Monitoring & Circuit Breakers

**Date:** 24 Mai 2026  
**Niveau:** Phase 2 - Risk Management Core  
**Temps estimé:** 3-4h  
**Statut:** ✅ Complet

---

## 🎯 Objectifs du Module

1. Implémenter un système de monitoring VaR/CVaR en temps réel
2. Créer des circuit breakers à 4 niveaux (Warning → Kill Switch)
3. Suivi du PnL quotidien et drawdown
4. Détection de volatilité anormale
5. Système d'alertes avec niveaux de sévérité

---

## 📚 Concepts Clés

### 1. Value at Risk (VaR)

**Définition:**
> La perte maximale attendue sur un horizon donné, avec un niveau de confiance spécifié.

**Formule:**
```
P(Loss > VaR_α) = 1 - α

Où:
- α = niveau de confiance (95%, 99%)
- Horizon = 1 jour (typiquement)
```

**Exemple concret:**
- VaR 95% = -3.63%
- "Il y a 95% de chance que la perte quotidienne ne dépasse pas 3.63%"
- "Dans 5% des cas (1 jour sur 20), on perd PLUS que 3.63%"

### 2. Conditional VaR (CVaR / Expected Shortfall)

**Définition:**
> La perte **moyenne** attendue **quand on dépasse la VaR**.

**Pourquoi CVaR est meilleur:**

| Problème | VaR | CVaR |
|----------|-----|------|
| Ignore la queue de distribution | ❌ | ✅ |
| Non cohérent (subadditivity) | ❌ | ✅ |
| Capture les événements extrêmes | ❌ | ✅ |
| Convexe (optimisation) | ❌ | ✅ |

**Exemple:**
- VaR 95% = -3.63% → "On perd max 3.63% dans 95% des cas"
- CVaR 95% = -5.20% → "QUAND on dépasse les 3.63%, on perd en moyenne 5.20%"

### 3. Méthodes de Calcul

#### Méthode Historique
```python
def historical_var(returns, confidence=0.95):
    return np.percentile(returns, (1 - confidence) * 100)
```
- ✅ Simple, non-paramétrique
- ✅ Capture les fat tails réelles
- ❌ Nécessite beaucoup de données
- ❌ Assume le passé = futur

#### Méthode Paramétrique (Gaussian)
```python
def parametric_var(returns, confidence=0.95):
    mean = np.mean(returns)
    std = np.std(returns)
    z_score = stats.norm.ppf(1 - confidence)
    return mean + z_score * std
```
- ✅ Rapide, peu de données
- ✅ Lisse le bruit
- ❌ Assume normalité (FAUX pour crypto!)
- ❌ Sous-estime les queues

#### Monte Carlo
```python
def monte_carlo_var(returns, confidence=0.95, n_sim=10000):
    mean = np.mean(returns)
    std = np.std(returns)
    simulated = np.random.normal(mean, std, n_sim)
    return np.percentile(simulated, (1 - confidence) * 100)
```
- ✅ Flexible, peut modéliser n'importe quelle distribution
- ✅ Bon pour stress testing
- ❌ Lent (10k+ simulations)
- ❌ Dépend des hypothèses

---

## 🔧 Circuit Breakers (4 Niveaux)

Basés sur les résultats de stress testing (Semaine 20):

| Niveau | Déclencheur | Action | Couleur |
|--------|-------------|--------|---------|
| **Level 1** | Daily PnL < -3.6% OU Drawdown < -10% | Alert only | 🟡 Warning |
| **Level 2** | Daily PnL < -5% OU Drawdown < -15% | Réduire 50% | 🟠 Critical |
| **Level 3** | Daily PnL < -8% OU Drawdown < -20% | Stop new trades | 🔴 Critical |
| **Level 4** | Daily PnL < -10% OU Drawdown < -25% | Kill Switch | 🔴 Emergency |

**Kill Switch (Level 4):**
- Ferme TOUTES les positions immédiatement
- Bloque tout nouveau trade
- Nécessite intervention manuelle pour reset
- Logging complet pour post-mortem

---

## 💻 Implémentation

### Fichier: `code/risk_monitor.py`

**Classes principales:**

```python
class RiskMonitor:
    """Monitoring temps réel avec circuit breakers"""
    
    def __init__(self, initial_capital=10000, var_confidence=0.95):
        # Configuration
        self.circuit_breaker_thresholds = {
            LEVEL_1: {'daily_pnl': -0.036, 'drawdown': -0.10},
            LEVEL_2: {'daily_pnl': -0.05, 'drawdown': -0.15},
            LEVEL_3: {'daily_pnl': -0.08, 'drawdown': -0.20},
            LEVEL_4: {'daily_pnl': -0.10, 'drawdown': -0.25}
        }
    
    def update_capital(self, new_capital):
        # Met à jour le capital et check circuit breakers
        daily_pnl, cb_level = self._check_circuit_breakers(...)
        self._generate_alerts(daily_pnl, cb_level)
    
    def get_risk_metrics(self):
        # Retourne VaR, CVaR, vol, daily_pnl, drawdown, CB level
        return RiskMetrics(...)
    
    def check_trading_allowed(self):
        # Vérifie si trading est permis
        return (allowed: bool, reason: str)
```

**Alertes:**
```python
class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"
```

### Tests et Résultats

**Test 1: Conditions normales**
```
Capital initial: $10,000
100 returns simulés (mean=0.1%, vol=3%)
→ VaR 95%: -5.08%
→ CVaR 95%: -6.05%
→ Circuit breaker: Normal ✅
```

**Test 2: Crash simulé**
```
5 jours de crash: -5%, -8%, -12%, -6%, -4%
→ Capital final: $5,411 (-46%)
→ Drawdown: -53%
→ Circuit breaker: KILL SWITCH ACTIVATED 🔴
→ Trading: BLOQUÉ
```

**Résultat:**
- Kill switch se déclenche correctement à -10% daily ou -25% drawdown
- Alertes générées à chaque niveau
- Position sizing bloqué à $0 quand Level 4

---

## 📊 Insights Clés

### 1. VaR vs CVaR - Le Vrai Risque

**Découverte importante:**
- VaR 95% BTC (historique): -3.63%
- CVaR 95% BTC: -5.20%
- **Gap: 43% de perte supplémentaire dans la queue!**

La VaR dit "tu perds max 3.63% dans 95% des cas".  
Le CVaR dit "quand ça va vraiment mal (les 5% restants), tu perds en moyenne 5.20%".

**Pour le trading:**
- Position sizing basé sur VaR seul = SOUS-ESTIME le risque
- CVaR donne une vue plus réaliste du "worst case"
- Utiliser CVaR pour les scénarios extrêmes (stress testing)

### 2. Circuit Breakers - Pourquoi 4 Niveaux?

**Niveau 1 (Warning, -3.6%):**
- Juste au-delà de la VaR 95% normale
- "Hey, aujourd'hui est un jour inhabituel"
- Action: Surveillance accrue

**Niveau 2 (Reduce, -5%):**
- Proche du CVaR 95%
- "Le risque de queue se matérialise"
- Action: Réduire l'exposition de 50%

**Niveau 3 (Stop, -8%):**
- "Quelque chose ne va pas"
- Action: Stopper les nouveaux trades, garder l'existant

**Niveau 4 (Kill, -10%):**
- "CRASH - Protection du capital avant tout"
- Action: FERMER TOUT, survie du système

**Leçon:** L'escalade progressive évite:
- Les false positives (un seul seuil trop sensible)
- Les réactions tardives (un seul seuil trop tardif)

### 3. Volatilité Annualisée - Attention au Multiplicateur

**Erreur commune:**
```python
daily_vol = 0.03  # 3% daily
annual_vol = daily_vol * np.sqrt(365)  # 57% ✅

# MAIS pour crypto avec trading 24/7:
annual_vol = daily_vol * np.sqrt(365)  # Toujours correct
# PAS np.sqrt(252) comme pour les actions!
```

**Pourquoi:**
- Actions: 252 jours de trading/an
- Crypto: 365 jours (24/7, pas de weekend)
- Le sqrt(365) est correct pour annualiser

---

## 🎯 Applications Saiyan

### Monitoring Temps Réel

```python
# Initialisation
monitor = RiskMonitor(initial_capital=10000)

# Update après chaque trade
monitor.update_capital(new_portfolio_value)

# Check avant nouveau trade
allowed, reason = monitor.check_trading_allowed()
if not allowed:
    print(f"❌ Trade bloqué: {reason}")
    return

# Position sizing avec circuit breaker
base_size = 1000
max_size = monitor.get_position_size_limit(base_size)
# Level 0-1: $1000
# Level 2: $500 (réduit 50%)
# Level 3-4: $0 (bloqué)
```

### Alertes Telegram

**À implémenter:**
```python
# Quand Level 1 triggered
🟡 WARNING: Daily PnL -4.2% dépasse seuil VaR 95% (-3.6%)
   → Surveillance accrue, pas d'action requise

# Quand Level 2 triggered
🟠 CRITICAL: Circuit breaker Level 2 activé
   → Réduction position 50% automatique
   → Daily PnL: -5.8%

# Quand Level 4 triggered (Kill Switch)
🔴 EMERGENCY: KILL SWITCH ACTIVÉ
   → Drawdown: -26% (seuil: -25%)
   → TOUTES positions fermées
   → Trading bloqué jusqu'intervention manuelle
   → Post-mortem requis
```

---

## 📁 Fichiers Créés

- `code/risk_monitor.py` (19KB) - Module complet avec tests
- `notes/semaine-26-risk-monitoring.md` - Ce fichier

---

## ✅ Validation

**Tests passés:**
- ✅ VaR/CVaR historique (3 méthodes)
- ✅ Circuit breakers 4 niveaux
- ✅ Alertes avec sévérité
- ✅ Position sizing dynamique
- ✅ Kill switch fonctionnel

**Prochaines étapes:**
- [ ] Intégration avec données Binance temps réel
- [ ] Alertes Telegram automatisées
- [ ] Dashboard Grafana pour visualisation
- [ ] Backtesting des circuit breakers sur données historiques

---

## 🧠 Quiz Personnel

**Q1:** Quelle est la différence entre VaR 95% et CVaR 95%?

**R1:** VaR 95% = "Perte max dans 95% des cas". CVaR 95% = "Perte moyenne QUAND on dépasse la VaR". CVaR capture le risque de queue, VaR non.

**Q2:** Pourquoi 4 niveaux de circuit breakers?

**R2:** Escalade progressive: Warning → Reduce → Stop → Kill. Évite false positives ET réactions tardives. Chaque niveau a une action spécifique.

**Q3:** Quel seuil pour le Kill Switch?

**R3:** Daily PnL < -10% OU Drawdown < -25%. Basé sur stress testing (Semaine 20) - au-delà, la survie du système est en jeu.

---

**Temps passé:** ~3.5h ✅  
**Prochain module:** Position Sizing (Kelly + HMM)
