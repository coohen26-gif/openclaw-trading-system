# Semaine 02 - GARCH Volatility Modeling

## Théorie GARCH(1,1)

### Concept de Base

**GARCH** = **G**eneralized **A**uto**R**egressive **C**onditional **H**eteroskedasticity

Modélise la **volatilité** (variance conditionnelle) d'une série temporelle financière.

### Équation GARCH(1,1)

```
σ²_t = ω + α·ε²_{t-1} + β·σ²_{t-1}

où:
- σ²_t = variance conditionnelle au temps t
- ω = terme constant (long-run variance)
- α = coefficient des chocs récents (news coefficient)
- β = coefficient de la volatilité passée (persistence)
- ε_{t-1} = résidu au temps t-1
```

### Contraintes

- ω > 0
- α ≥ 0, β ≥ 0
- α + β < 1 (stationnarité)
- α + β ≈ 1 → volatilité très persistante (typique en finance)

### Interprétation

- **α élevé** → réactions fortes aux nouvelles (chocs)
- **β élevé** → volatilité persistante (clustering)
- **α + β** → taux de décroissance des chocs de volatilité

---

## Implémentation Python

### Installation

```bash
pip install arch pandas numpy matplotlib
```

### Code: `learning/code/garch_btc.py`

```python
import pandas as pd
import numpy as np
from arch import arch_model
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# 1. Générer des données BTC simulées (remplacer par données réelles)
np.random.seed(42)
n_days = 500
dates = pd.date_range(end=datetime.now(), periods=n_days, freq='D')

# Simulation de rendements BTC (volatilité clustering)
returns = np.random.normal(0.001, 0.04, n_days)
returns[100:150] *= 3  # Période de haute volatilité
returns[300:350] *= 2.5

returns_series = pd.Series(returns, index=dates)

# 2. Modèle GARCH(1,1)
model = arch_model(returns_series, vol='GARCH', p=1, q=1, mean='Constant')
fitted = model.fit(disp='off')

print("=" * 50)
print("RÉSULTATS GARCH(1,1)")
print("=" * 50)
print(fitted.summary())

# 3. Prévision volatilité 1 jour ahead
forecast = fitted.forecast(horizon=1)
vol_forecast = forecast.variance.iloc[-1].values[0]
vol_forecast_daily = np.sqrt(vol_forecast) * 100  # En %

print(f"\n📊 Prévision volatilité (1 jour): {vol_forecast_daily:.2f}%")

# 4. Validation vs realized volatility
realized_vol = returns_series.rolling(20).std() * np.sqrt(252) * 100
conditional_vol = np.sqrt(fitted.conditional_volatility) * np.sqrt(252) * 100

print(f"\n📈 Statistiques:")
print(f"  Volatilité annualisée moyenne: {conditional_vol.mean():.2f}%")
print(f"  Volatilité realized (20j) moy: {realized_vol.mean():.2f}%")
print(f"  Corrélation: {conditional_vol.corr(realized_vol):.3f}")

# 5. Visualisation
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

axes[0].plot(returns_series.index, returns_series.cumsum(), label='Returns cumulés', linewidth=1)
axes[0].set_title('Performance BTC (simulée)')
axes[0].set_ylabel('Cumul')
axes[0].legend()
axes[0].grid(alpha=0.3)

axes[1].plot(conditional_vol.index, conditional_vol.values, label='GARCH vol', alpha=0.7)
axes[1].plot(realized_vol.index, realized_vol.values, label='Realized vol (20j)', alpha=0.7)
axes[1].axhline(vol_forecast_daily * np.sqrt(252), color='red', linestyle='--', label='Forecast 1j')
axes[1].set_title('Volatilité: GARCH vs Realized')
axes[1].set_ylabel('% annualisé')
axes[1].legend()
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('learning/code/garch_btc_output.png', dpi=150)
print("\n✅ Graphique sauvegardé: learning/code/garch_btc_output.png")

# 6. Métriques de validation
from sklearn.metrics import mean_squared_error, mean_absolute_error

# Comparer GARCH vol (lagged) vs realized vol
valid_idx = ~conditional_vol.isna() & ~realized_vol.isna()
mse = mean_squared_error(realized_vol[valid_idx], conditional_vol[valid_idx])
mae = mean_absolute_error(realized_vol[valid_idx], conditional_vol[valid_idx])

print(f"\n🎯 Métriques de validation:")
print(f"  MSE: {mse:.4f}")
print(f"  MAE: {mae:.4f}")
print(f"  R²: {conditional_vol[valid_idx].corr(realized_vol[valid_idx])**2:.4f}")
```

---

## Exécution et Résultats Attendus

### Sortie Type

```
==================================================
RÉSULTATS GARCH(1,1)
==================================================
                         Constant Mean - GARCH Model Results                        
====================================================================================
Dep. Variable:                   y   R-squared:                 -0.001              
Mean Model:                 Constant   Adj. R-squared:           -0.003              
Vol Model:                     GARCH   Log-Likelihood:           1234.56             
Distribution:            Normal   AIC:                         -2463.12              
Method:            Maximum Likelihood   BIC:                         -2450.45              
                                        No. Observations:                  500                 
Date:                Sat, May 23 2026   Df Residuals:                      498                 
Time:                        22:12:00   Df Model:                            2                 
...

coef    std err   t       p-value
omega   0.0001   0.00005   2.00    0.045
alpha   0.15     0.03      5.00    0.000
beta    0.80     0.04      20.00   0.000

📊 Prévision volatilité (1 jour): 2.85%

📈 Statistiques:
  Volatilité annualisée moyenne: 45.2%
  Volatilité realized (20j) moy: 42.8%
  Corrélation: 0.78

🎯 Métriques de validation:
  MSE: 12.34
  MAE: 2.89
  R²: 0.61
```

---

## Points Clés à Retenir

1. **GARCH capture le volatility clustering** → périodes calmes/agitées se regroupent
2. **α + β proche de 1** → chocs de volatilité persistent longtemps (typique crypto)
3. **Prévision 1 jour** = meilleure estimation de risque à court terme
4. **Validation** → comparer conditional volatility vs realized volatility rolling
5. **Limites** → GARCH suppose symétrie (ne capture pas leverage effect)

### Extensions Possibles

- **EGARCH** → capture asymétrie (mauvaises nouvelles → plus de vol)
- **GJR-GARCH** → similaire, paramétrisation différente
- **Multivariate GARCH** → volatilité + corrélations entre assets

---

## Références

- Engle, R. F. (1982). "Autoregressive Conditional Heteroscedasticity..."
- Bollerslev, T. (1986). "Generalized Autoregressive Conditional Heteroskedasticity"
- Documentation arch: https://arch.readthedocs.io/
