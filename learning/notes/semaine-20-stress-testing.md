# Semaine 20 - Stress Testing & Scenario Analysis

**Date:** 24 Mai 2026  
**Niveau:** Master 4 - Risk Management Advanced  
**Temps estimé:** 3-4h

---

## 🎯 Objectifs du Module

1. Comprendre l'importance du stress testing dans le risk management
2. Identifier les périodes de stress historiques pour la crypto
3. Simuler l'impact de scénarios de crise sur un portfolio
4. Calculer VaR/CVaR sous stress
5. Concevoir des circuit breakers robustes
6. Visualiser les drawdowns et paths de simulation

---

## 📚 Théorie Fondamentale

### 1. Pourquoi le Stress Testing?

**Limites des modèles "normaux":**
- VaR/CVaR basés sur données historiques récentes
- Assume une certaine continuité dans les distributions
- **Ne capturent pas les événements extrêmes rares**

**Le stress testing répond à:**
> "Que se passe-t-il quand tout va mal EN MÊME TEMPS?"

**Définition (Basel Committee):**
> "Le stress testing est l'identification et l'analyse des effets de mouvements de marché défavorables ou d'événements rares sur les positions de trading."

### 2. Types de Scénarios de Stress

| Type | Description | Exemples |
|------|-------------|----------|
| **Historique** | Reproduit des crises passées | COVID mars 2020, FTX nov 2022 |
| **Hypothétique** | Scénarios "what-if" jamais vus | -50% en 1 jour, correlation → 1 |
| **Sensibilité** | Choc sur un facteur spécifique | Vol ×3, liquidity -80% |
| **Systemique** | Effets domino, contagion | Crypto → TradFi spillover |

### 3. Méthodologie de Stress Testing

**Étapes:**

1. **Identifier les facteurs de risque:**
   - Prix (BTC, ETH, etc.)
   - Volatilité
   - Corrélations
   - Liquidité

2. **Définir les scénarios:**
   - Basé sur événements historiques
   - Ou scénarios hypothétiques extrêmes

3. **Appliquer les chocs:**
   - Shock sur les returns (mean shift)
   - Shock sur la volatilité (vol multiplier)
   - Shock sur les corrélations (correlation breakdown)

4. **Simuler l'impact:**
   - Monte Carlo avec paramètres stressés
   - Calculer nouvelles métriques de risque

5. **Interpréter et agir:**
   - Concevoir circuit breakers
   - Ajuster position sizing
   - Définir plans de contingence

---

## 🔧 Scénarios Historiques Crypto

### 1. COVID-19 Crash (Mars 2020)

**Contexte:**
- Pandémie globale, panic selling
- Tout s'est vendu (actions, crypto, or, pétrole)
- Liquidity dry-up extrême

**Choc BTC:**
- Perte: ~35% en mars 2020
- Volatilité: ×3.5 vs normale
- Duration: ~20 jours
- Type: Global risk-off

**Leçon:**
> En crise systémique, TOUTES les corrélations → 1. La diversification disparaît.

### 2. FTX Collapse (Novembre 2022)

**Contexte:**
- Faillite frauduleuse de FTX (2ème plus gros exchange)
- Contagion: Genesis, BlockFi, Voyager
- Perte de confiance massive

**Choc BTC:**
- Perte: ~25% en novembre 2022
- Volatilité: ×2.8
- Duration: ~15 jours
- Type: Crypto-specific (contagion risk)

**Leçon:**
> Le risque de contrepartie (exchange risk) est aussi important que le risque de marché.

### 3. LUNA/UST Depeg (Mai 2022)

**Contexte:**
- Effondrement de l'algo-stablecoin UST ($40B → $0)
- LUNA token: $80 → $0.0001 en quelques jours
- Effet de contagion sur tout l'écosystème DeFi

**Choc BTC:**
- Perte: ~30% en mai 2022
- Volatilité: ×3.0
- Duration: ~18 jours
- Type: Crypto-specific (stablecoin risk)

**Leçon:**
> Les stablecoins "safe" peuvent être le maillon faible.

### 4. China Mining Ban (Mai-Juin 2021)

**Contexte:**
- Chine interdit le mining de Bitcoin
- ~65% du hash rate mondial concerné
- Panic sur la sécurité du réseau

**Choc BTC:**
- Perte: ~50% de mai à juin 2021
- Volatilité: ×2.5
- Duration: ~30 jours
- Type: Réglementaire

**Leçon:**
> Le risque réglementaire est imprévisible et peut être sévère.

---

## 💻 Implémentation Python

### 1. Définition des Scénarios

```python
def identify_stress_periods():
    """Define historical stress periods for crypto"""
    stress_periods = {
        'covid_crash': {
            'start': '2020-03-01',
            'end': '2020-03-31',
            'description': 'COVID-19 Market Crash',
            'type': 'global_risk_off'
        },
        'ftx_collapse': {
            'start': '2022-11-01',
            'end': '2022-11-30',
            'description': 'FTX Exchange Collapse',
            'type': 'crypto_specific'
        },
        'luna_terra': {
            'start': '2022-05-01',
            'end': '2022-05-31',
            'description': 'LUNA/UST Depeg & Collapse',
            'type': 'crypto_specific'
        },
        'china_ban': {
            'start': '2021-05-15',
            'end': '2021-06-15',
            'description': 'China Mining Ban',
            'type': 'regulatory'
        }
    }
    return stress_periods
```

### 2. Profils de Choc

```python
shock_profiles = {
    'covid_crash': {
        'mean_shock': -0.35,      # BTC dropped ~35%
        'vol_multiplier': 3.5,
        'correlation_breakdown': True,
        'duration_days': 20
    },
    'ftx_collapse': {
        'mean_shock': -0.25,      # BTC dropped ~25%
        'vol_multiplier': 2.8,
        'correlation_breakdown': True,
        'duration_days': 15
    },
    'luna_terra': {
        'mean_shock': -0.30,      # BTC dropped ~30%
        'vol_multiplier': 3.0,
        'correlation_breakdown': True,
        'duration_days': 18
    },
    'china_ban': {
        'mean_shock': -0.50,      # BTC dropped ~50%
        'vol_multiplier': 2.5,
        'correlation_breakdown': False,
        'duration_days': 30
    }
}
```

### 3. Simulation Monte Carlo sous Stress

```python
def simulate_stress_scenario(returns, scenario_name, stress_periods, n_simulations=10000):
    """
    Simulate portfolio performance under stress scenario
    """
    shock = apply_historical_scenario(returns, scenario_name, stress_periods)
    
    # Base statistics
    base_mean = returns.mean()
    base_std = returns.std()
    
    # Apply stress
    stressed_mean = base_mean + shock['mean_shock'] / shock['duration_days']
    stressed_std = base_std * shock['vol_multiplier']
    
    # Simulate returns for the duration
    duration = shock['duration_days']
    simulated_paths = np.random.normal(stressed_mean, stressed_std, (n_simulations, duration))
    
    # Calculate cumulative returns
    cumulative_returns = np.prod(1 + simulated_paths, axis=1) - 1
    
    # Calculate max drawdown for each path
    cumulative_wealth = np.cumprod(1 + simulated_paths, axis=1)
    running_max = np.maximum.accumulate(cumulative_wealth, axis=1)
    drawdowns = (cumulative_wealth - running_max) / running_max
    max_drawdowns = np.min(drawdowns, axis=1)
    
    return {
        'scenario_name': scenario_name,
        'final_returns': cumulative_returns,
        'max_drawdowns': max_drawdowns,
        'var_95': np.percentile(cumulative_returns, 5),
        'var_99': np.percentile(cumulative_returns, 1),
        'cvar_95': np.mean(cumulative_returns[cumulative_returns <= np.percentile(cumulative_returns, 5)]),
        'expected_return': np.mean(cumulative_returns),
        'prob_loss_gt_20pct': np.mean(cumulative_returns < -0.20),
        'prob_loss_gt_50pct': np.mean(cumulative_returns < -0.50)
    }
```

### 4. Calcul VaR/CVaR sous Stress

```python
def calculate_portfolio_var_under_stress(returns, stress_periods, portfolio_value=100000):
    """Calculate VaR/CVaR under different stress scenarios"""
    results = []
    
    # Normal conditions (baseline)
    baseline = {
        'scenario': 'Normal Conditions',
        'var_95': np.percentile(returns, 5),
        'var_99': np.percentile(returns, 1),
        'cvar_95': np.mean(returns[returns <= np.percentile(returns, 5)]),
        'daily_vol': returns.std()
    }
    results.append(baseline)
    
    # Stress scenarios
    for scenario_name in ['covid_crash', 'ftx_collapse', 'luna_terra', 'china_ban']:
        sim = simulate_stress_scenario(returns, scenario_name, stress_periods)
        stress_result = {
            'scenario': sim['description'],
            'var_95': sim['var_95'],
            'var_99': sim['var_99'],
            'cvar_95': sim['cvar_95'],
            'daily_vol': returns.std() * sim['shock']['vol_multiplier'],
            'expected_loss': sim['expected_return'],
            'max_drawdown_expected': np.mean(sim['max_drawdowns'])
        }
        results.append(stress_result)
    
    return results
```

### 5. Design de Circuit Breakers

```python
def design_circuit_breakers(returns, stress_results):
    """
    Design circuit breakers based on stress test results
    """
    circuit_breakers = []
    
    # Level 1: Warning threshold (based on normal VaR)
    normal_var_95 = np.percentile(returns, 5)
    circuit_breakers.append({
        'level': 1,
        'name': 'Warning',
        'trigger': f"Daily loss > {abs(normal_var_95)*100:.1f}%",
        'action': 'Alert sent, review positions',
        'threshold': normal_var_95
    })
    
    # Level 2: Reduce risk (based on mild stress)
    mild_stress_var = stress_results[1]['var_95']
    circuit_breakers.append({
        'level': 2,
        'name': 'Risk Reduction',
        'trigger': f"Daily loss > {abs(mild_stress_var)*100:.1f}%",
        'action': 'Reduce position size by 50%',
        'threshold': mild_stress_var
    })
    
    # Level 3: Emergency stop (based on severe stress)
    severe_stress_var = stress_results[2]['var_95']
    circuit_breakers.append({
        'level': 3,
        'name': 'Emergency Stop',
        'trigger': f"Daily loss > {abs(severe_stress_var)*100:.1f}%",
        'action': 'Close all positions, halt trading',
        'threshold': severe_stress_var
    })
    
    # Level 4: Portfolio-level circuit breaker (drawdown)
    circuit_breakers.append({
        'level': 4,
        'name': 'Max Drawdown',
        'trigger': 'Portfolio drawdown > 20% from peak',
        'action': 'Delever to 25% exposure, risk review required',
        'threshold': -0.20
    })
    
    return circuit_breakers
```

---

## 📊 Résultats sur BTC (Données Réelles)

### Données Utilisées

- **Période:** 4 Juin 2024 → 23 Mai 2026
- **Observations:** 719 jours
- **Source:** Binance (daily closes)

### Conditions Normales (Baseline)

| Métrique | Valeur |
|----------|--------|
| Daily Volatility | 2.41% |
| VaR 95% | -3.63% |
| VaR 99% | -5.84% |
| CVaR 95% | -5.20% |

**En dollars ($100k portfolio):**
- VaR 95%: $3,630/jour
- CVaR 95%: $5,201/jour (dans les pires cas)

### Résultats Stress Testing

#### 1. COVID-19 Crash

| Métrique | Valeur |
|----------|--------|
| Daily Volatility (stressée) | 8.43% (×3.5) |
| VaR 95% | -65.23% |
| CVaR 95% | -70.69% |
| Expected Loss | -29.09% |
| Expected Max Drawdown | -42.48% |

**En dollars ($100k):**
- VaR 95%: $65,228
- CVaR 95%: $70,693

#### 2. FTX Collapse

| Métrique | Valeur |
|----------|--------|
| Daily Volatility (stressée) | 6.75% (×2.8) |
| VaR 95% | -50.76% |
| CVaR 95% | -55.90% |
| Expected Loss | -21.60% |
| Expected Max Drawdown | -31.01% |

**En dollars ($100k):**
- VaR 95%: $50,758
- CVaR 95%: $55,902

#### 3. LUNA/UST Collapse

| Métrique | Valeur |
|----------|--------|
| Daily Volatility (stressée) | 7.23% (×3.0) |
| VaR 95% | -58.02% |
| CVaR 95% | -62.88% |
| Expected Loss | -25.62% |
| Expected Max Drawdown | -36.33% |

#### 4. China Mining Ban

| Métrique | Valeur |
|----------|--------|
| Daily Volatility (stressée) | 6.02% (×2.5) |
| VaR 95% | -66.97% |
| CVaR 95% | -71.22% |
| Expected Loss | -38.93% |
| Expected Max Drawdown | -46.40% |

---

## 🛡️ Circuit Breakers Design

Basé sur les résultats du stress testing:

| Niveau | Nom | Trigger | Action |
|--------|-----|---------|--------|
| **Level 1** | Warning | Daily loss > 3.6% | Alert sent, review positions |
| **Level 2** | Risk Reduction | Daily loss > 65.2% | Reduce position size by 50% |
| **Level 3** | Emergency Stop | Daily loss > 50.8% | Close all positions, halt trading |
| **Level 4** | Max Drawdown | Portfolio DD > 20% | Delever to 25% exposure |

### Implémentation pour Saiyan

```python
class SaiyanCircuitBreaker:
    def __init__(self, portfolio_value, stress_results):
        self.portfolio_value = portfolio_value
        self.thresholds = self.design_thresholds(stress_results)
        self.current_drawdown = 0.0
        self.peak_value = portfolio_value
    
    def check_daily_loss(self, daily_pnl_pct):
        """Check if daily loss triggers circuit breaker"""
        if daily_pnl_pct < self.thresholds['level_3']:
            return 'EMERGENCY_STOP'
        elif daily_pnl_pct < self.thresholds['level_2']:
            return 'RISK_REDUCTION'
        elif daily_pnl_pct < self.thresholds['level_1']:
            return 'WARNING'
        return 'NORMAL'
    
    def update_drawdown(self, current_value):
        """Track portfolio drawdown"""
        self.peak_value = max(self.peak_value, current_value)
        self.current_drawdown = (current_value - self.peak_value) / self.peak_value
        
        if self.current_drawdown < self.thresholds['max_drawdown']:
            return 'DELEVER_REQUIRED'
        return 'NORMAL'
    
    def design_thresholds(self, stress_results):
        """Design thresholds based on stress test results"""
        return {
            'level_1': stress_results[0]['var_95'],  # Normal VaR 95%
            'level_2': stress_results[1]['var_95'],  # COVID stress VaR
            'level_3': stress_results[2]['var_95'],  # FTX stress VaR
            'max_drawdown': -0.20  # 20% max drawdown
        }
```

---

## 💡 Insights Clés

### 1. Le Gap Normal vs Stress est ÉNORME

**Normal VaR 95%:** -3.63%  
**Stress VaR 95%:** -50% à -67%

→ **Le risque en crise est 15-20x plus élevé qu'en temps normal!**

**Implication:**
- Les modèles basés sur données récentes sous-estiment drastiquement le risque
- Le position sizing "normal" devient dangereux en stress
- **Il faut des circuit breakers pour protéger le portfolio**

### 2. CVaR > VaR Toujours

Dans TOUS les scénarios:
```
CVaR 95% ≈ 1.1 × VaR 95%
```

→ Quand on dépasse la VaR, la perte moyenne est ~10% PLUS ÉLEVÉE

**Implication:**
- Utiliser CVaR pour le capital requirement, pas VaR
- La VaR donne un faux sentiment de sécurité

### 3. Duration Matters

| Scénario | Duration | Impact Total |
|----------|----------|--------------|
| FTX | 15 jours | -21.6% |
| COVID | 20 jours | -29.1% |
| LUNA | 18 jours | -25.6% |
| China | 30 jours | -38.9% |

→ Les crises plus longues ont un impact PLUS grand, même avec des chocs daily similaires

**Implication:**
- Le risk management doit considérer l'hypothèse de duration
- Un circuit breaker qui agit J-1 peut sauver 10-20% de perte

### 4. Correlation Breakdown

Pendant les stress de type "global risk-off" (COVID):
- Toutes les corrélations → 1
- La diversification DISPARAÎT
- BTC, ETH, SOL, etc. tombent ENSEMBLE

**Implication:**
- En crise, on ne peut pas compter sur la diversification cross-asset
- Il faut des hedges vrais (options, futures, stablecoins)

---

## ⚠️ Limites et Mises en Garde

### 1. Historical Bias

**Problème:**
- On utilise des crises PASSÉES
- La prochaine crise pourrait être DIFFÉRENTE
- "This time is different" peut être vrai

**Mitigation:**
- Ajouter des scénarios hypothétiques PLUS PIRES que l'historique
- Ex: -70% en 10 jours (jamais vu, mais possible)

### 2. Parameter Uncertainty

**Problème:**
- Les shock profiles (mean_shock, vol_multiplier) sont des estimations
- Une erreur de 20% sur ces paramètres change beaucoup les résultats

**Mitigation:**
- Sensitivity analysis: tester plusieurs valeurs
- Utiliser des ranges, pas des point estimates

### 3. Liquidity Risk Ignored

**Problème:**
- Les simulations assume qu'on peut vendre au prix de marché
- En crise: spreads widening, slippage, voire impossibilité de vendre

**Mitigation:**
- Liquidity-adjusted VaR (LVaR)
- Réduire les position sizes pour les assets moins liquides

### 4. Model Risk

**Problème:**
- Monte Carlo assume une distribution normale (même stressée)
- En réalité: fat tails, jumps, gaps

**Mitigation:**
- Utiliser des distributions non-normales (Student-t, skewed)
- Ajouter des jumps dans les simulations

---

## 🚀 Applications pour Saiyan

### 1. Dynamic Circuit Breakers

**Actuellement:** Pas de circuit breakers implémentés.

**Après Master 4:**
```python
def saiyan_risk_check(daily_pnl, portfolio_value, peak_value):
    """
    Check circuit breakers and return action
    """
    drawdown = (portfolio_value - peak_value) / peak_value
    
    # Level 3: Emergency Stop
    if daily_pnl < -0.50:  # -50% daily loss
        return 'CLOSE_ALL_POSITIONS'
    
    # Level 4: Max Drawdown
    if drawdown < -0.20:  # -20% from peak
        return 'DELEVER_TO_25_PERCENT'
    
    # Level 2: Risk Reduction
    if daily_pnl < -0.10:  # -10% daily loss
        return 'REDUCE_POSITIONS_50_PERCENT'
    
    # Level 1: Warning
    if daily_pnl < -0.036:  # -3.6% daily loss
        return 'SEND_ALERT_REVIEW_POSITIONS'
    
    return 'NORMAL_TRADING'
```

### 2. Stress-Adjusted Position Sizing

```python
def stress_adjusted_position_size(base_size, stress_scenario='ftx'):
    """
    Reduce position size based on stress scenario severity
    """
    stress_factors = {
        'normal': 1.0,
        'ftx': 0.5,      # 50% reduction
        'covid': 0.3,    # 70% reduction
        'luna': 0.4,
        'china': 0.25
    }
    
    factor = stress_factors.get(stress_scenario, 1.0)
    return base_size * factor
```

### 3. Pre-Emptive Deleveraging

**Idée:** Quand les signaux de stress apparaissent (vol ↑, corr ↑), réduire l'exposition AVANT que la crise n'arrive.

```python
def pre_emptive_risk_check(volatility_ratio, correlation_avg):
    """
    Detect early warning signs of stress
    """
    # Volatility spike detection
    if volatility_ratio > 2.0:  # Vol is 2x normal
        return 'REDUCE_EXPOSURE_30_PERCENT'
    
    # Correlation spike (diversification breaking down)
    if correlation_avg > 0.8:  # All assets moving together
        return 'REDUCE_EXPOSURE_20_PERCENT'
    
    return 'NORMAL'
```

---

## 📈 Visualisations Générées

1. **Stress Scenarios Comparison:** VaR 95%/99% across all scenarios
2. **Return Distribution (FTX):** Histogram with VaR/CVaR markers
3. **Max Drawdown Comparison:** Bar chart of expected MDD by scenario
4. **Circuit Breaker Levels:** Horizontal bar chart of trigger thresholds
5. **Simulated Price Paths:** Normal vs FTX stress (50 paths each)
6. **Historical Drawdown:** Fill-area plot of drawdown over time

**Fichiers créés:**
- `learning/figures/stress-scenarios-comparison.png`
- `learning/figures/stress-scenario-paths.png`
- `learning/figures/historical-drawdown.png`

---

## ✅ Checklist de Compréhension

- [ ] Comprendre pourquoi stress testing est nécessaire (limites VaR normale)
- [ ] Connaître les 4 scénarios historiques majeurs crypto
- [ ] Savoir simuler un stress scenario avec Monte Carlo
- [ ] Calculer VaR/CVaR sous stress
- [ ] Concevoir des circuit breakers basés sur les résultats
- [ ] Comprendre les limites (historical bias, model risk, liquidity)
- [ ] Savoir implémenter pour Saiyan

---

## 📚 Références

1. **Basel Committee (2009):** "Principles for Sound Stress Testing Practices"
2. **Hull, J. (2018):** "Risk Management and Financial Institutions" - Chapter 15
3. **Alexander, C. (2008):** "Market Risk Analysis, Volume IV: Value at Risk Models"
4. **Crypto-specific:**
   - "The Bitcoin Standard" - Ammous (contexte historique)
   - CoinDesk, The Block (reporting sur FTX, LUNA, etc.)

---

## 🎯 Prochaines Étapes

- **Semaine 21:** Production Systems & Infrastructure
  - Architecture temps réel
  - Latency optimization
  - Monitoring & alerting
  - Disaster recovery

- **Phase 2 - Intégration Saiyan:**
  - Implémenter circuit breakers
  - Stress-adjusted position sizing
  - Pre-emptive risk monitoring

---

*Module Master 4 complété ✅ - Risk Management Advanced terminé*
