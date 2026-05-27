# Semaine 2 : GARCH Volatility Modeling 📊

**Module :** Licence 2 - Modélisation de la Volatilité  
**Date de début :** 2026-05-27  
**Statut :** 🔄 En cours

---

## 🎯 Objectifs de la Semaine

1. Comprendre le concept d'**hétéroscédasticité conditionnelle**
2. Maîtriser le modèle **GARCH(1,1)** et ses variantes
3. Implémenter GARCH sur BTC/ETH/SOL
4. Intégrer la volatilité prédite dans le Système Saiyan

---

## 📖 Concepts Clés

### 1. Pourquoi la Volatilité N'est Pas Constante

**Observation :** La volatilité des marchés crypto (et financiers en général) :
- Se regroupe en **clusters** (périodes calmes → périodes agitées)
- Est **persistante** (un choc aujourd'hui impacte demain)
- Présente des **pics soudains** (crashes, pumps)

→ Les modèles à volatilité constante (comme CAPM) échouent à capturer cette dynamique.

---

### 2. Hétéroscédasticité Conditionnelle

**Définition :** La variance des returns **dépend du passé** (conditionnelle à l'information disponible).

Formellement :
```
σ²_t = Var(ε_t | F_{t-1})
```
où F_{t-1} est l'information disponible à t-1.

**Conséquence :** On peut **prédire** la volatilité future en utilisant l'historique !

---

### 3. Modèle ARCH (AutoRegressive Conditional Heteroskedasticity)

Introduit par **Engle (1982)** - Prix Nobel 2003.

**ARCH(q) :**
```
σ²_t = α₀ + α₁·ε²_{t-1} + α₂·ε²_{t-2} + ... + α_q·ε²_{t-q}
```

où :
- α₀ > 0 (terme constant)
- α_i ≥ 0 (coefficients positifs)
- ε_t = σ_t · z_t, avec z_t ~ N(0,1)

**Problème :** Besoin de beaucoup de lags (q élevé) → trop de paramètres.

---

### 4. Modèle GARCH (Generalized ARCH)

Introduit par **Bollerslev (1986)** - extension d'ARCH.

**GARCH(p,q) :**
```
σ²_t = α₀ + Σ(α_i·ε²_{t-i}) + Σ(β_j·σ²_{t-j})
       i=1..q          j=1..p
```

**GARCH(1,1) - Le plus utilisé :**
```
σ²_t = α₀ + α₁·ε²_{t-1} + β₁·σ²_{t-1}
```

où :
- α₀ > 0 (constante)
- α₁ ≥ 0 (réaction aux chocs récents = "news")
- β₁ ≥ 0 (persistance de la volatilité)
- α₁ + β₁ < 1 (stationnarité)

**Interprétation :**
- α₁·ε²_{t-1} : impact des **nouvelles récentes** (chocs)
- β₁·σ²_{t-1} : **mémoire** de la volatilité passée
- Plus β₁ est proche de 1, plus la volatilité est persistante

---

### 5. Variantes de GARCH

#### EGARCH (Exponential GARCH) - Nelson (1991)
Modélise **log(σ²_t)** pour éviter contraintes de positivité.

**Avantage :** Capture l'**asymétrie** (bad news > good news en volatilité).

```
log(σ²_t) = ω + β·log(σ²_{t-1}) + α·|z_{t-1}| + γ·z_{t-1}
```

γ ≠ 0 → effet asymétrique (γ < 0 : bad news augmente plus la volatilité)

---

#### GJR-GARCH - Glosten, Jagannathan, Runkle (1993)
Ajoute un terme dummy pour les chocs négatifs.

```
σ²_t = α₀ + α·ε²_{t-1} + γ·I_{t-1}·ε²_{t-1} + β·σ²_{t-1}
```

où I_{t-1} = 1 si ε_{t-1} < 0, else 0.

**Interprétation :** γ > 0 → les baisses (bad news) augmentent plus la volatilité que les hausses.

---

#### TGARCH (Threshold GARCH)
Similaire à GJR, avec seuil explicite.

---

### 6. Estimation des Paramètres

**Méthode :** Maximum de Vraisemblance (MLE)

**Log-likelihood (Gaussian) :**
```
L = Σ [-0.5·log(2π) - 0.5·log(σ²_t) - 0.5·(ε²_t / σ²_t)]
```

**Optimisation :** BFGS, Nelder-Mead, etc.

**Packages Python :**
- `arch` (le plus complet)
- `statsmodels` (GARCH basique)
- `pyflux` (Bayesian)

---

## 🔧 Implémentation Python

### Installation
```bash
pip install arch pandas numpy matplotlib
```

### Code de Base - GARCH(1,1) sur BTC

```python
import pandas as pd
import numpy as np
from arch import arch_model
import matplotlib.pyplot as plt

# Charger les données (exemple : returns BTC 5min)
returns = pd.read_csv('btc_returns_5min.csv')['return'] * 100  # en %

# Fit GARCH(1,1)
model = arch_model(returns, vol='Garch', p=1, q=1, dist='Normal')
fit = model.fit()

print(fit.summary())

# Paramètres typiques pour BTC :
# ω (alpha0) ≈ 0.01-0.05
# α1 (news)  ≈ 0.05-0.15
# β1 (persist) ≈ 0.80-0.90
# α1 + β1 ≈ 0.90-0.98 (très persistant!)

# Prédire volatilité future
forecast = fit.forecast(horizon=5)
print(forecast.variance)

# Plot
plt.figure(figsize=(12,6))
plt.plot(fit.conditional_volatility, label='Volatilité Conditionnelle')
plt.title('Volatilité GARCH(1,1) - BTC')
plt.legend()
plt.show()
```

---

## 📊 Application au Système Saiyan

### 1. Position Sizing Dynamique

Au lieu de size fixe :
```
size_t = capital_risk_pct / (stop_distance × volatilité_prédite_t)
```

→ Réduire size quand volatilité élevée, augmenter quand calme.

### 2. Stops Dynamiques

```
SL_distance_t = ATR_multiplier × σ_t (volatilité GARCH)
```

→ Stops plus larges en période volatile (évite stop hunting).

### 3. Filtrage de Signaux

```
if σ_t > σ_seuil_high:
    confidence *= 0.7  # Réduire confiance en marché agité
elif σ_t < σ_seuil_low:
    confidence *= 1.2  # Augmenter confiance en marché calme
```

### 4. Détection de Régimes (complément HMM)

Volatilité élevée + HMM "High Vol" → Stratégies breakout/momentum  
Volatilité basse + HMM "Range" → Stratégies mean reversion

---

## 📝 Exercices Pratiques

### Exercice 1 : Fit GARCH(1,1) sur BTC
- Données : returns 5min, 1h, 1D
- Comparer α₁ et β₁ selon TF
- Observer persistance (β₁)

### Exercice 2 : EGARCH et Asymétrie
- Fit EGARCH sur mêmes données
- Vérifier γ (coefficient asymétrie)
- Bad news > Good news ?

### Exercice 3 : Forecast Accuracy
- Split train/test (80/20)
- Prédire volatilité J+1 à J+5
- Comparer avec volatilité réalisée (RMSE)

### Exercice 4 : Intégration Saiyan
- Ajouter module `volatility/garch.py`
- Calculer σ_t en temps réel
- Ajuster position sizing dans emitter

---

## 🧠 Insights Attendus

1. **Persistance élevée** : β₁ ≈ 0.85-0.95 pour crypto (volatilité très persistante)
2. **Asymétrie** : γ < 0 dans EGARCH (baisses → plus de volatilité que hausses)
3. **Clustering** : visualiser périodes calmes vs agitées
4. **Prédictibilité** : GARCH capture ~50-70% de la variance de volatilité future

---

## 📚 Ressources

- **Engle (1982)** : "Autoregressive Conditional Heteroscedasticity..."
- **Bollerslev (1986)** : "Generalized Autoregressive Conditional Heteroskedasticity"
- **Documentation `arch`** : https://bashtage.github.io/arch/
- **QuantStart GARCH Guide** : https://www.quantstart.com/articles/GARCH-Model-in-Python/

---

## ✅ Checklist Semaine 2

- [ ] Comprendre hétéroscédasticité conditionnelle
- [ ] Implémenter GARCH(1,1) en Python
- [ ] Tester EGARCH/GJR pour asymétrie
- [ ] Analyser BTC/ETH/SOL (multi-TF)
- [ ] Comparer volatilité prédite vs réalisée
- [ ] Intégrer dans Système Saiyan (position sizing)
- [ ] Documenter résultats dans journal

---

**Prochaine semaine :** HMM Regime Detection 🎯
