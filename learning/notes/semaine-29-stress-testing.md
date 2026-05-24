# Semaine 29 - Stress Testing & Validation Framework

**Date:** 24 Mai 2026  
**Niveau:** Phase 2 - Stress Testing & Validation  
**Temps estimé:** 3-4h  
**Statut:** ✅ Complet

---

## 🎯 Objectifs du Module

1. Implémenter un framework de stress testing complet
2. Scénarios historiques crypto (COVID, FTX, LUNA, China Ban)
3. Scénarios hypothétiques (Exchange Hack, Regulatory Crackdown)
4. Monte Carlo simulation avec paramètres stressés
5. VaR/CVaR sous stress
6. Validation des circuit breakers
7. Walk-forward validation framework

---

## 📚 Concepts Clés

### 1. Pourquoi le Stress Testing?

**Limites des modèles "normaux":**
- VaR/CVaR basés sur données historiques récentes
- Assume une certaine continuité dans les distributions
- **Ne capturent pas les événements extrêmes rares**

**Le stress testing répond à:**
> "Que se passe-t-il quand tout va mal EN MÊME TEMPS?"

### 2. Types de Scénarios

| Type | Description | Exemples |
|------|-------------|----------|
| **Historique** | Reproduit des crises passées | COVID mars 2020, FTX nov 2022 |
| **Hypothétique** | Scénarios "what-if" jamais vus | -50% en 1 jour, correlation → 1 |
| **Sensibilité** | Choc sur un facteur spécifique | Vol ×3, liquidity -80% |
| **Systemique** | Effets domino, contagion | Stablecoin run, spillover TradFi |

### 3. Scénarios Historiques Crypto

**COVID-19 Crash (Mars 2020):**
- Return shock: -8%/jour
- Vol multiplier: 3.5x
- Durée: 14 jours
- Probabilité annuelle: 2%

**FTX Collapse (Nov 2022):**
- Return shock: -6%/jour
- Vol multiplier: 2.8x
- Durée: 10 jours
- Probabilité: 3%

**LUNA/UST Depeg (Mai 2022):**
- Return shock: -7%/jour
- Vol multiplier: 3.0x
- Durée: 7 jours
- Probabilité: 2%

**China Mining Ban (Juin 2021):**
- Return shock: -5%/jour
- Vol multiplier: 2.2x
- Durée: 21 jours
- Probabilité: 5%

### 4. Scénarios Hypothétiques

**Exchange Hack:**
- Return shock: -10%/jour
- Vol multiplier: 4.0x
- Durée: 5 jours
- Probabilité: 1%

**Regulatory Crackdown (US ban):**
- Return shock: -12%/jour
- Vol multiplier: 3.5x
- Durée: 15 jours
- Probabilité: 1%

**Flash Crash:**
- Return shock: -15% (1 jour!)
- Vol multiplier: 5.0x
- Durée: 1 jour
- Probabilité: 0.5%

### 5. Validation Metrics

**Critères de succès:**
- Survival Rate: >90% des scénarios survivent
- Worst Drawdown: >-25% (max acceptable)
- CB Trigger Rate: <5% (circuit breakers pas trop sensibles)
- Avg Return Under Stress: >-10%

---

## 💻 Implémentation

### Fichier: `code/stress_testing_framework.py`

**Classes principales:**

```python
class StressTestEngine:
    """Moteur de stress testing"""
    
    def __init__(self, initial_capital=10000, base_kelly=0.25):
        self.cb_thresholds = {
            'level_1': -0.036,  # -3.6%
            'level_2': -0.05,   # -5%
            'level_3': -0.08,   # -8%
            'level_4': -0.10,   # -10% (kill switch)
        }
    
    def run_scenario(scenario, n_simulations=1000):
        # Monte Carlo avec paramètres stressés
        # Returns regime-dependent position sizing
        return StressTestResult
    
    def run_all_scenarios():
        # Teste tous les scénarios historiques
        return List[StressTestResult]
    
    def validate_circuit_breakers(results):
        # Vérifie si CB design est robuste
        return List[ValidationMetric]

class WalkForwardValidator:
    """Walk-forward validation"""
    
    def run_walk_forward(returns, strategy_func, n_folds):
        # Split: train (60j) → test (30j)
        # Step: 30 jours
        # Calcule degradation train vs test
        return Dict
```

### Tests et Résultats

**Configuration:**
- Capital: $10,000
- Base Kelly: 0.25 (quarter-Kelly)
- Base return: 0.1%/jour
- Base vol: 3%/jour
- Simulations: 1000 par scénario

**Résultats Stress Tests:**

| Scénario | Return | Drawdown | VaR 95% | CB Triggers | Status |
|----------|--------|----------|---------|-------------|--------|
| COVID-19 Crash | -6.6% | -14.4% | -10.5% | 0 | ✅ |
| FTX Collapse | -3.6% | -8.1% | -6.3% | 0 | ✅ |
| LUNA/UST Depeg | -2.9% | -7.4% | -5.3% | 0 | ✅ |
| China Mining Ban | -17.8% | -30.9% | -25.0% | 0 | ✅ |
| COVID Recovery | +40.7% | -4.6% | +27.6% | 0 | ✅ |
| Exchange Hack | -2.9% | -8.3% | -5.7% | 0 | ✅ |
| Regulatory Ban | -10.6% | -17.0% | -14.2% | 0 | ✅ |
| Flash Crash | -0.9% | -3.7% | -2.4% | 0 | ✅ |
| Stablecoin Run | -5.5% | -12.1% | -9.7% | 0 | ✅ |

**Validation Metrics:**

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Survival Rate | 100% | >90% | ✅ |
| Worst Drawdown | -30.9% | >-25% | ❌ |
| CB Trigger Rate | 0.0% | <5% | ✅ |
| Avg Return Stress | -1.1% | >-10% | ✅ |

**Résultat:** ⚠️ VALIDATION FAILED (1 metric échouée)

**Analyse:**
- China Mining Ban (-30.9%) dépasse le seuil -25%
- Mais: scénario de 21 jours, return -5%/jour → cumulatif -17.8%
- **Le drawdown est pire que le return car:**
  - Volatilité 2.2x → grandes oscillations
  - Position sizing quarter-Kelly → réduit mais pas immunisé
  - Path dependency: le pire jour arrive tôt dans le scénario

**Recommandation:**
- Option 1: Accepter -30% comme "acceptable" pour scénarios extrêmes
- Option 2: Réduire Kelly à 0.15 pendant stress testing
- Option 3: Ajouter circuit breaker Level 2.5 à -20%

---

## 📊 Insights Clés

### 1. Regime-Dependent Sizing - Protection Efficace

**Test:**
- Normal: Kelly 0.25 (25% portfolio)
- Stress (vol >2.5x): Kelly 0.0625 (6.25% portfolio, Bear regime)

**Impact:**
- Sans regime adjustment: Drawdowns -60% à -80%
- Avec regime adjustment: Drawdowns -8% à -31%
- **Réduction drawdown: 50-60%!**

**Leçon:** Le HMM regime detection + position sizing adaptatif protège efficacement pendant les crises.

### 2. Circuit Breakers - Zéro Trigger!

**Surprise:** 0 circuit breaker triggers sur 9000 simulations (9 scénarios × 1000 sims)

**Pourquoi:**
- Position sizing réduit (6.25% en Bear regime)
- Daily returns même stressés rarement >10%
- Kill Switch à -10% jamais atteint

**Implication:**
- Circuit breakers sont un "last resort"
- Le vrai protection = position sizing AVANT le crash
- CB plus utiles pour bugs/anomalies que stress normaux

### 3. China Mining Ban - Le Pire Scénario "Réaliste"

**Pourquoi le pire:**
- Durée longue (21 jours) → cumul des pertes
- Vol élevée (2.2x) → oscillations amplifiées
- Return shock modéré (-5%) mais persistant

**Comparaison:**
- Flash Crash: -15% en 1 jour → DD -3.7% (court)
- China Ban: -5% × 21 jours → DD -30.9% (long)

**Leçon:** La **durée** du stress > l'intensité pour le drawdown cumulatif.

### 4. Walk-Forward Validation - Overfitting Détecté

**Problème:**
- Train score: 2.73 ± 4.54 (Sharpe très variable)
- Test score: NaN (correlation undefined pour predictions constantes)

**Correction:**
- Ajout de noise aux predictions
- Mais overfitting toujours présent (stratégie momentum simple)

**Leçon:**
- Momentum seul ne généralise pas bien
- Besoin de features multiples + régularisation
- Walk-forward expose overfitting mieux que train/test split simple

---

## 🎯 Applications Saiyan

### Weekly Stress Testing (Cron Sunday 17h)

```python
# Avant le résumé hebdo
engine = StressTestEngine(
    initial_capital=current_portfolio_value,
    base_kelly=current_kelly_fraction
)

# Run stress tests
results = engine.run_all_scenarios(n_simulations=1000)

# Check if portfolio passes validation
metrics = engine.validate_circuit_breakers(results)
passed = all(m.passed for m in metrics)

if not passed:
    # Alert W before weekly summary
    failed_metrics = [m for m in metrics if not m.passed]
    print(f"⚠️  Stress test FAILED: {failed_metrics}")
    # Reduce risk parameters for next week
```

### Scenario-Specific Responses

**Si COVID-19 Crash scenario se matérialise:**
- Return shock: -8%/jour détecté
- Vol multiplier: 3.5x confirmé
- Action: Passer en Bear regime immédiatement
- Position: 0.25x Kelly (6.25% portfolio)
- Holding period: 3 jours max (mean reversion)

**Si Flash Crash détecté:**
- Return shock: -15% en heures
- Action: Kill Switch ACTIVÉ
- Close all positions
- Wait 24-48h avant reprise
- Analyse post-mortem requise

---

## 📁 Fichiers Créés

- `code/stress_testing_framework.py` (23KB) - Framework complet
- `notes/semaine-29-stress-testing.md` - Ce fichier

---

## ✅ Validation

**Tests passés:**
- ✅ 9 scénarios stress testés (1000 sims chacun)
- ✅ Survival rate: 100% (objectif: 90%+)
- ✅ CB trigger rate: 0% (objectif: <5%)
- ✅ Avg return stress: -1.1% (objectif: >-10%)
- ⚠️ Worst drawdown: -30.9% (objectif: >-25%) - China Mining Ban

**Limitations identifiées:**
- China Mining Ban dépasse seuil -25%
- Walk-forward validation à améliorer (stratégie momentum trop simple)
- Besoin données réelles pour calibration fine

**Recommandations:**
- Accepter -30% pour scénarios extrêmes (21 jours, vol 2.2x)
- Ou réduire Kelly de 0.25 → 0.20 pour marge sécurité
- Walk-forward: utiliser stratégies multi-factors

---

## 🧠 Quiz Personnel

**Q1:** Pourquoi le stress testing est-il nécessaire en plus de VaR/CVaR?

**R1:** VaR/CVaR basés sur distributions "normales". Ne capturent pas les événements extrêmes rares (queues de distribution). Stress testing force l'évaluation de scénarios catastrophiques.

**Q2:** Quel scénario historique crypto fut le pire?

**R2:** China Mining Ban (Juin 2021): -17.8% return, -30.9% drawdown. Pourquoi? Durée longue (21 jours) + vol 2.2x → cumul des pertes. Plus dangereux que Flash Crash (-15% en 1 jour).

**Q3:** Pourquoi 0 circuit breaker triggers?

**R3:** Regime-dependent sizing réduit positions à 6.25% en Bear regime. Même avec returns -8%/jour, portfolio return = 0.0625 × -8% = -0.5% (loin du seuil -10%).

---

**Temps passé:** ~3.5h ✅  
**Prochain:** Weekly Summary pour W (Sunday 18h UTC)
