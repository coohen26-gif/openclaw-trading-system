# Semaine 03 - ARIMA Time Series Forecasting

## Théorie ARIMA(p,d,q)

### Concept de Base

**ARIMA** = **A**uto**R**egressive **I**ntegrated **M**oving **A**verage

Modélise une série temporelle pour prédire ses **valeurs futures** (direction, pas volatilité).

### Les 3 Composantes

#### 1. AR(p) - AutoRegressive

```
X_t = c + φ₁·X_{t-1} + φ₂·X_{t-2} + ... + φ_p·X_{t-p} + ε_t

La valeur actuelle dépend des p valeurs précédentes.
```

- **p** = nombre de lags (retards)
- Capture la **mémoire** de la série

#### 2. I(d) - Integrated (Différenciation)

```
Y_t = X_t - X_{t-1}  (différence d'ordre 1)
Y_t = (X_t - X_{t-1}) - (X_{t-1} - X_{t-2})  (ordre 2)
```

- **d** = nombre de différenciations pour rendre la série **stationnaire**
- Stationnarité = moyenne et variance constantes dans le temps
- Test: **ADF (Augmented Dickey-Fuller)**

#### 3. MA(q) - Moving Average

```
X_t = μ + ε_t + θ₁·ε_{t-1} + θ₂·ε_{t-2} + ... + θ_q·ε_{t-q}

La valeur actuelle dépend des q erreurs de prédiction précédentes.
```

- **q** = nombre de termes d'erreur retardés
- Capture les **chocs temporaires**

### Modèle ARIMA(p,d,q) Complet

```
(1 - φ₁B - ... - φ_pB^p)(1 - B)^d X_t = (1 + θ₁B + ... + θ_qB^q)ε_t

où B est l'opérateur de retard: B·X_t = X_{t-1}
```

---

## Identification des Paramètres

### Méthode: ACF et PACF

| Modèle | ACF | PACF |
|--------|-----|------|
| AR(p) | Décroissance exponentielle | Cut-off après lag p |
| MA(q) | Cut-off après lag q | Décroissance exponentielle |
| ARMA(p,q) | Décroissance exponentielle | Décroissance exponentielle |

- **ACF** (AutoCorrelation Function) → corrélation avec les lags
- **PACF** (Partial ACF) → corrélation avec les lags, contrôlant les intermédiaires

### Procédure

1. **Tester stationnarité** (ADF test)
2. **Différencier** si nécessaire (trouver d)
3. **Observer ACF/PACF** pour identifier p et q
4. **Ajuster** avec AIC/BIC

---

## Implémentation Python

### Installation

```bash
pip install statsmodels pandas numpy matplotlib
```

### Code: `learning/code/arima_btc.py`

```python
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime

# 1. Générer des données BTC simulées
np.random.seed(42)
n_days = 500
dates = pd.date_range(end=datetime.now(), periods=n_days, freq='D')

# Prix BTC simulé (random walk avec drift)
price = 50000  # Prix initial
prices = [price]
for i in range(1, n_days):
    drift = 0.0005  # Drift quotidien
    shock = np.random.normal(0, 0.03)  # Choc quotidien
    new_price = prices[-1] * (1 + drift + shock)
    prices.append(new_price)

prices_series = pd.Series(prices, index=dates, name='BTC_price')
returns = prices_series.pct_change().dropna()

# 2. Test de stationnarité (ADF)
print("=" * 60)
print("TEST DE STATIONNARITÉ (ADF)")
print("=" * 60)

adf_price = adfuller(prices_series)
adf_returns = adfuller(returns)

print(f"\nPrix BTC:")
print(f"  ADF Statistic: {adf_price[0]:.4f}")
print(f"  p-value: {adf_price[1]:.4f}")
print(f"  Stationnaire: {'✅ Oui' if adf_price[1] < 0.05 else '❌ Non'}")

print(f"\nRendements BTC:")
print(f"  ADF Statistic: {adf_returns[0]:.4f}")
print(f"  p-value: {adf_returns[1]:.4f}")
print(f"  Stationnaire: {'✅ Oui' if adf_returns[1] < 0.05 else '❌ Non'}")

# 3. Identifier p et q avec ACF/PACF
print("\n" + "=" * 60)
print("IDENTIFICATION p, d, q")
print("=" * 60)

# Sur les rendements (déjà stationnaires, d=0)
acf_vals = acf(returns, nlags=20)
pacf_vals = pacf(returns, nlags=20)

print(f"\nACF significatif (lag > 0):")
for i, val in enumerate(acf_vals[1:], 1):
    if abs(val) > 1.96/np.sqrt(len(returns)):
        print(f"  Lag {i}: {val:.4f} *")

print(f"\nPACF significatif (lag > 0):")
for i, val in enumerate(pacf_vals[1:], 1):
    if abs(val) > 1.96/np.sqrt(len(returns)):
        print(f"  Lag {i}: {val:.4f} *")

# 4. Grid search pour meilleurs paramètres
print("\n" + "=" * 60)
print("GRID SEARCH - MEILLEURS PARAMÈTRES")
print("=" * 60)

best_aic = np.inf
best_order = None
best_model = None

for p in range(0, 4):
    for q in range(0, 4):
        try:
            model = ARIMA(returns, order=(p, 0, q))
            fitted = model.fit()
            if fitted.aic < best_aic:
                best_aic = fitted.aic
                best_order = (p, 0, q)
                best_model = fitted
        except:
            continue

print(f"\n🏆 Meilleur ordre: ARIMA{best_order}")
print(f"  AIC: {best_aic:.2f}")
print(f"  BIC: {best_model.bic:.2f}")

# 5. Résumé du modèle
print("\n" + "=" * 60)
print("RÉSUMÉ DU MODÈLE ARIMA")
print("=" * 60)
print(best_model.summary())

# 6. Prévision
print("\n" + "=" * 60)
print("PRÉVISION (5 jours)")
print("=" * 60)

forecast = best_model.get_forecast(steps=5)
forecast_mean = forecast.predicted_mean
forecast_ci = forecast.conf_int()

for i, (idx, val) in enumerate(forecast_mean.items(), 1):
    ci_low = forecast_ci.loc[idx, 'lower returns']
    ci_high = forecast_ci.loc[idx, 'upper returns']
    print(f"  J+{i}: {val*100:+.3f}%  [{ci_low*100:+.3f}%, {ci_high*100:+.3f}%]")

# Direction prediction
last_price = prices_series.iloc[-1]
predicted_prices = [last_price]
for val in forecast_mean:
    predicted_prices.append(predicted_prices[-1] * (1 + val))

direction = "📈 HAUSSE" if predicted_prices[-1] > last_price else "📉 BAISSE"
print(f"\n🎯 Direction prévue (5j): {direction}")
print(f"  Prix actuel: ${last_price:,.2f}")
print(f"  Prix prévu (J+5): ${predicted_prices[-1]:,.2f}")
print(f"  Changement: {(predicted_prices[-1]/last_price - 1)*100:+.2f}%")

# 7. Validation
print("\n" + "=" * 60)
print("VALIDATION DU MODÈLE")
print("=" * 60)

residuals = best_model.resid
print(f"\nRésidus:")
print(f"  Moyenne: {residuals.mean():.6f}")
print(f"  Std: {residuals.std():.6f}")
print(f"  Normalité (Jarque-Bera): {best_model.test_normality().jb_stat[0]:.2f} (p={best_model.test_normality().jb_stat[1]:.4f})")

# Test d'autocorrélation des résidus
acf_resid = acf(residuals, nlags=20)
ljung_box = best_model.test_serial_correlation()
print(f"  Ljung-Box: {ljung_box.lb_stat[0]:.2f} (p={ljung_box.lb_stat[1]:.4f})")
print(f"  Résidus blancs: {'✅ Oui' if ljung_box.lb_stat[1] > 0.05 else '❌ Non'}")

# 8. Visualisation
print("\n" + "=" * 60)
print("VISUALISATION")
print("=" * 60)

fig, axes = plt.subplots(3, 2, figsize=(14, 10))

# Plot 1: Prix
axes[0, 0].plot(prices_series.index, prices_series.values, linewidth=1.5)
axes[0, 0].set_title('Prix BTC (simulé)', fontweight='bold')
axes[0, 0].set_ylabel('Prix ($)')
axes[0, 0].grid(alpha=0.3)

# Plot 2: Rendements
axes[0, 1].plot(returns.index, returns.values, linewidth=1, color='green')
axes[0, 1].set_title('Rendements Quotidiens', fontweight='bold')
axes[0, 1].set_ylabel('Return')
axes[0, 1].axhline(0, color='black', linewidth=0.5)
axes[0, 1].grid(alpha=0.3)

# Plot 3: ACF
plot_acf(returns, lags=20, ax=axes[1, 0])
axes[1, 0].set_title('ACF - Rendements', fontweight='bold')

# Plot 4: PACF
plot_pacf(returns, lags=20, ax=axes[1, 1])
axes[1, 1].set_title('PACF - Rendements', fontweight='bold')

# Plot 5: Forecast
axes[2, 0].plot(prices_series.index[-50:], prices_series.values[-50:], 
                label='Historique', linewidth=2)
forecast_dates = pd.date_range(start=prices_series.index[-1] + pd.Timedelta(days=1), 
                                periods=5, freq='D')
forecast_prices = pd.Series(predicted_prices[1:], index=forecast_dates)
axes[2, 0].plot(forecast_dates, forecast_prices, 
                label='Prévision', linewidth=2, color='red', linestyle='--')
axes[2, 0].set_title('Prévision Prix (5 jours)', fontweight='bold')
axes[2, 0].set_ylabel('Prix ($)')
axes[2, 0].legend()
axes[2, 0].grid(alpha=0.3)

# Plot 6: Résidus
axes[2, 1].plot(residuals.index, residuals.values, linewidth=0.5, alpha=0.7)
axes[2, 1].axhline(0, color='red', linewidth=1)
axes[2, 1].set_title('Résidus du Modèle', fontweight='bold')
axes[2, 1].set_ylabel('Résidu')
axes[2, 1].grid(alpha=0.3)

plt.tight_layout()
output_path = '/root/.openclaw/workspace/learning/code/arima_btc_output.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"  ✓ Graphique sauvegardé: {output_path}")

print("\n" + "=" * 60)
print("✅ ARIMA ANALYSIS COMPLETE")
print("=" * 60)
```

---

## Points Clés à Retenir

1. **Stationnarité requise** → toujours tester avec ADF avant ARIMA
2. **d = 0 pour les rendements** → les prix sont non-stationnaires, les rendements oui
3. **ACF/PACF** → outils visuels pour identifier p et q
4. **AIC/BIC** → critères pour comparer modèles (plus bas = mieux)
5. **Validation** → résidus doivent être du bruit blanc (pas d'autocorrélation)

### Limites ARIMA

- **Linéaire** → ne capture pas les relations non-linéaires
- **Univarié** → utilise seulement l'historique de la série
- **Stationnarité** → suppose structure stable dans le temps
- **Court terme** → meilleures prévisions à court terme

### Extensions

- **SARIMA** → saisonnalité
- **ARIMAX** → variables exogènes
- **VAR** → multivarié (plusieurs séries)
- **Prophet** → trend + saisonnalité + holidays (Facebook)

---

## Références

- Box, G. E. P., & Jenkins, G. M. (1976). "Time Series Analysis: Forecasting and Control"
- Hyndman, R. J., & Athanasopoulos, G. (2021). "Forecasting: Principles and Practice"
- Statsmodels docs: https://www.statsmodels.org/stable/index.html
