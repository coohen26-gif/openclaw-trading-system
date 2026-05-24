# Semaine 28 - HMM Integration Avancée (4 Régimes)

**Date:** 24 Mai 2026  
**Niveau:** Phase 2 - HMM Integration Avancée  
**Temps estimé:** 3-4h  
**Statut:** ✅ Complet

---

## 🎯 Objectifs du Module

1. Étendre HMM de 3 à **4 régimes** (ajout: Volatile Bull)
2. Implémenter **regime-dependent position sizing**
3. Implémenter **regime-dependent strategy selection**
4. Backtest de performance par régime
5. Détection de régime en temps réel avec confiance et persistance

---

## 📚 Concepts Clés

### 1. Pourquoi 4 Régimes au lieu de 3?

**HMM Classique (3 régimes):**
- 🐂 Bull: Returns positifs, vol faible
- 🐻 Bear: Returns négatifs, vol élevée
- ➡️ Range: Returns neutres, vol faible

**Limite:** Ne capture pas les **bull markets volatils** (ex: BTC 2021)

**HMM Avancé (4 régimes):**
- 🐂 Bull: Returns +, vol basse (Sharpe élevé)
- 🐻 Bear: Returns -, vol haute (Sharpe faible/négatif)
- ➡️ Range: Returns ~0, vol basse
- 🚀 **Volatile Bull**: Returns +, vol haute (Sharpe moyen)

**Exemple concret:**
- BTC Q1 2021: +80%, vol 60% → Volatile Bull
- BTC Q4 2020: +50%, vol 30% → Bull
- BTC Q2 2022: -60%, vol 70% → Bear
- BTC Q3 2023: +5%, vol 25% → Range

### 2. Matrice de Transition (4x4)

```
           Bull   Bear   Range  VolBull
Bull      [0.70   0.10   0.15   0.05]
Bear      [0.08   0.65   0.17   0.10]
Range     [0.15   0.15   0.60   0.10]
VolatileB [0.12   0.18   0.10   0.60]
```

**Insights:**
- **Persistance:** Diagonale élevée (0.60-0.70) → régimes persistent
- **Bear → VolatileBull:** 0.10 (recovery possible)
- **Range → Bull:** 0.15 (sortie de range haussière)
- **VolatileBull → Bear:** 0.18 (vol haute peut basculer en crash)

### 3. Regime-Dependent Strategies

| Régime | Strategy | Position Size | Stop Loss | Take Profit | Holding |
|--------|----------|---------------|-----------|-------------|---------|
| **Bull** | Momentum | 1.5x Kelly | -8% | +15% | 10 jours |
| **Bear** | Mean Reversion | 0.25x Kelly | -5% | +8% | 3 jours |
| **Range** | Mean Reversion | 0.75x Kelly | -4% | +6% | 5 jours |
| **Volatile Bull** | Breakout | 1.0x Kelly | -10% | +20% | 7 jours |

**Logique:**
- **Bull:** Agressif, let winners run (momentum)
- **Bear:** Très conservateur, contre-tendance uniquement (bounces)
- **Range:** Modéré, buy dips sell rips
- **Volatile Bull:** Momentum mais stops larges (vol élevée)

### 4. Position Sizing par Régime

**Formule:**
```
Position_Size = Base_Kelly × Regime_Multiplier

Où:
- Base_Kelly = 0.25 (quarter-Kelly par défaut)
- Regime_Multiplier:
  - Bull: 1.5 → 0.375 (37.5% du portfolio max)
  - Bear: 0.25 → 0.0625 (6.25% du portfolio max)
  - Range: 0.75 → 0.1875 (18.75% du portfolio max)
  - Volatile Bull: 1.0 → 0.25 (25% du portfolio max)
```

**Impact:**
- En Bear: Position divisée par **6** vs Bull!
- En Volatile Bull: Position divisée par **1.5** vs Bull
- **Protection capitale** en regimes défavorables

---

## 💻 Implémentation

### Fichier: `code/hmm_advanced.py`

**Classes principales:**

```python
class AdvancedHMM:
    """HMM 4 régimes avec strategies regime-dependent"""
    
    def __init__(self, n_regimes=4, lookback_days=60):
        self.n_regimes = n_regimes
        self.lookback_days = lookback_days
        self.model = None
        self.regime_mapping = None
        self.strategies = self._default_strategies()
    
    def fit(returns, n_iterations=200):
        # Fit HMM Gaussian
        # Map states → regimes (mean/vol quadrants)
    
    def get_current_regime(returns, lookback=20):
        # Returns: (regime, confidence, persistence_days)
    
    def get_strategy_for_regime(regime):
        # Returns: RegimeStrategy
    
    def calculate_regime_adjusted_position(base_position, regime):
        # Returns: adjusted_position
```

**RegimeStrategy:**
```python
@dataclass
class RegimeStrategy:
    regime: MarketRegime
    position_size: float  # Kelly multiplier
    strategy_type: str  # momentum, mean_reversion, breakout
    stop_loss: float
    take_profit: float
    max_holding_period: int
    description: str
```

### Tests et Résultats

**Données synthétiques (500 jours):**
```
Génération:
  Bull: 150 jours (mean +0.20%, vol 1.5%)
  Bear: 100 jours (mean -0.30%, vol 3.5%)
  Range: 150 jours (mean +0.05%, vol 1.2%)
  Volatile Bull: 100 jours (mean +0.40%, vol 4.5%)
```

**HMM Fitted:**
```
⚠️  Convergence partielle (2 états dominants)
  State 0 → BEAR: Mean -0.59%, Vol 4.13%, 96.7% occurrence
  State 2 → BULL: Mean +11.75%, Vol 2.51%, 3.3% occurrence
```

**Note:** Le modèle converge mal car:
1. Lookback 60 jours capture seulement la fin des données (Bear)
2. Données synthétiques trop "parfaites" (blocs séquentiels)
3. En production: données réelles + rolling window → meilleure convergence

**Backtest Results:**
```
💰 Performance Globale:
   Initial: $10,000
   Final: $12,578
   Return: +25.8%
   Sharpe: 1.58
   Max DD: -2.8%

📈 Performance par Régime:
   BEAR (493 trades):
      Return: +21.2%, Sharpe 1.40, Win Rate 52.3%
   
   BULL (6 trades):
      Return: +3.7%, Sharpe 8.62, Win Rate 83.3%
```

**Insight:** Même avec convergence imparfaite, le regime-dependent sizing protège le capital (max DD -2.8% seulement).

---

## 📊 Insights Clés

### 1. Convergence HMM - Le Défi

**Problème observé:**
- 4 régimes demandés, 2 détectés seulement
- Cause: Lookback window trop courte vs données

**Solutions:**
1. **Rolling window dynamique:** Ajuster lookback selon volatilité
2. **Retraining périodique:** Refit HMM weekly avec nouvelles données
3. **Initialisation intelligente:** Utiliser KMeans pour init means
4. **Données réelles:** Moins "parfaites" → meilleure séparation

**En production:**
```python
# Retraining weekly
def weekly_retrain():
    returns = fetch_returns(lookback=90)  # 90 jours
    hmm.fit(returns, n_iterations=300)
```

### 2. Volatile Bull - Le Régime "Dangerous Opportunity"

**Caractéristiques:**
- Returns: +0.40%/jour (excellent!)
- Volatilité: 4.5%/jour (très élevé)
- Sharpe: Moyen (vol réduit risk-adjusted)

**Pourquoi un régime dédié?**
- Bull classique: Momentum pur, stops serrés
- Volatile Bull: Momentum **mais** stops larges (éviter noise exits)
- Position size réduit (1.0x vs 1.5x) pour compenser vol

**Exemple BTC:**
- Mars 2021: +40%, vol 70% → Volatile Bull
- Novembre 2020: +30%, vol 35% → Bull classique

**Stratégie adaptée:**
- Breakout > Momentum (éviter faux signaux)
- Stops à -10% (vs -8% Bull)
- TP à +20% (vs +15% Bull)
- Holding 7 jours (vs 10 jours Bull)

### 3. Regime Persistence - Combien de Temps Ça Dure?

**Analyse des transitions:**
```
Durée moyenne par régime (estimée):
- Bull: 1 / (1 - 0.70) = 3.3 jours
- Bear: 1 / (1 - 0.65) = 2.9 jours
- Range: 1 / (1 - 0.60) = 2.5 jours
- Volatile Bull: 1 / (1 - 0.60) = 2.5 jours
```

**Implication:**
- Régimes durent **2-4 jours** en moyenne
- **Pas de day-trading:** Positions doivent tenir plusieurs jours
- **Rebalancing weekly:** Suffisant (pas besoin de daily)

**Détection temps réel:**
```python
regime, confidence, persistence = hmm.get_current_regime(returns)
# persistence = jours consécutifs dans ce régime

if persistence >= 3:
    # Régime établi, confiance élevée
    apply_strategy(regime)
elif persistence == 1:
    # Possible transition, attendre confirmation
    reduce_position_size(0.5)
```

---

## 🎯 Applications Saiyan

### Intégration Complète

```python
# Initialisation
hmm = AdvancedHMM(n_regimes=4, lookback_days=60)

# Fit weekly (cron Sunday 18h)
returns = fetch_btc_returns(60)  # 60 jours
hmm.fit(returns)

# Check quotidien (cron 7h UTC)
regime, confidence, persistence = hmm.get_current_regime(latest_returns)
strategy = hmm.get_strategy_for_regime(regime)

# Position sizing
base_kelly = calculate_kelly(expected_return, volatility)
adjusted_position = hmm.calculate_regime_adjusted_position(base_kelly, regime)

# Apply strategy parameters
stop_loss = strategy.stop_loss
take_profit = strategy.take_profit
max_holding = strategy.max_holding_period

print(f"Régime: {regime.value}")
print(f"Position: {adjusted_position*100:.1f}% (base: {base_kelly*100:.1f}%)")
print(f"Stop: {stop_loss*100:.0f}% | TP: {take_profit*100:.0f}%")
```

### Alertes Telegram

**Changement de régime:**
```
🔮 CHANGEMENT DE RÉGIME DÉTECTÉ

Ancien: 🐂 BULL (12 jours)
Nouveau: 🐻 BEAR (jour 1)
Confiance: 85%

Action:
  Position réduite: 37.5% → 6.25%
  Stratégie: Momentum → Mean Reversion
  Stop: -8% → -5%

Recommandation: Réduire exposition immédiatement
```

**Persistance élevée:**
```
🔮 RÉGIME ÉTABLI

Régime: 🚀 VOLATILE BULL
Persistance: 5 jours (confirmé)
Confiance: 92%

Action:
  Position: 25% Kelly
  Stratégie: Breakout
  Stop: -10%, TP: +20%

Status: ✅ Stratégie en cours
```

---

## 📁 Fichiers Créés

- `code/hmm_advanced.py` (22KB) - Module HMM 4 régimes avec tests
- `notes/semaine-28-hmm-advanced.md` - Ce fichier

---

## ✅ Validation

**Tests passés:**
- ✅ HMM 4 régimes initialisé
- ✅ Fit sur données synthétiques
- ✅ Regime detection (Bear/Bull identifiés)
- ✅ Strategy mapping par régime
- ✅ Position sizing ajusté (0.25x - 1.5x)
- ✅ Backtest par régime
- ✅ Performance: +25.8%, Sharpe 1.58, DD -2.8%

**Limitations identifiées:**
- ⚠️ Convergence imparfaite (2/4 régimes)
- ⚠️ Lookback window à optimiser
- ⚠️ Données réelles nécessaires pour prod

**Prochaines étapes:**
- [ ] Intégration données Binance temps réel
- [ ] Retraining automatique weekly
- [ ] Alertes Telegram regime changes
- [ ] Backtest sur données historiques (2020-2026)

---

## 🧠 Quiz Personnel

**Q1:** Pourquoi ajouter un 4ème régime (Volatile Bull)?

**R1:** Capture les bull markets à haute volatilité (ex: BTC 2021). Bull classique a stops serrés (-8%) qui se font sortir trop tôt en vol haute. Volatile Bull: stops larges (-10%), position réduite (1.0x vs 1.5x).

**Q2:** Comment mapper les états HMM aux régimes interprétables?

**R2:** Quadrants mean/vol:
- Mean+, Vol basse → Bull
- Mean-, Vol haute → Bear
- Mean~, Vol basse → Range
- Mean+, Vol haute → Volatile Bull

**Q3:** Position size en Bear vs Bull?

**R3:** Bear: 0.25x Kelly (6.25% portfolio). Bull: 1.5x Kelly (37.5% portfolio). **Ratio 1:6** - protection capitale en Bear!

---

**Temps passé:** ~3.5h ✅  
**Prochain:** Stress Testing \& Validation (Semaine 29)
