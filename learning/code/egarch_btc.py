#!/usr/bin/env python3
"""
EGARCH(1,1) - Exponential GARCH pour BTC
Modélise l'asymétrie leverage effect: bad news > good news

Auteur: Goku (Système Saiyan)
Date: 27 Mai 2026
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from arch import arch_model
import warnings
warnings.filterwarnings('ignore')

# Configuration
plt.style.use('seaborn-v0_8-darkgrid')
np.random.seed(42)

print("=" * 70)
print("EGARCH(1,1) - EXCESSIVE GARCH BTC/USDT")
print("Données réelles Binance API (2023-2026)")
print("=" * 70)

# ============================================================================
# 1. FETCH DONNÉES RÉELLES
# ============================================================================

def fetch_btc_data(days=999):
    """Fetch BTC/USDT daily data from Binance API"""
    import requests
    
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "BTCUSDT",
        "interval": "1d",
        "limit": days
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
        'taker_buy_quote', 'ignore'
    ])
    
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = df['close'].astype(float)
    df['returns'] = df['close'].pct_change() * 100  # en %
    
    return df.dropna().reset_index(drop=True)

print("\n[1/5] Fetch données Binance API...")
df = fetch_btc_data(days=999)
print(f"  ✓ Période: {df['date'].min().strftime('%Y-%m-%d')} à {df['date'].max().strftime('%Y-%m-%d')}")
print(f"  ✓ Nombre de jours: {len(df)}")
print(f"  ✓ Mean return: {df['returns'].mean():.3f}%")
print(f"  ✓ Std return: {df['returns'].std():.3f}%")

# ============================================================================
# 2. FIT EGARCH(1,1)
# ============================================================================

print("\n[2/5] Fit EGARCH(1,1)...")

# EGARCH capture leverage effect: gamma ≠ 0
# log(σ²) = ω + β*log(σ²_lag) + γ*(ε/σ) + α*(|ε/σ| - E|ε/σ|)

model = arch_model(
    df['returns'].values,  # arch attend en %
    vol='EGARCH',
    p=1,  # ARCH term
    q=1,  # GARCH term
    o=1,  # Asymmetry term
    dist='Normal',
    rescale=True
)

fitted = model.fit(disp='off', show_warning=False)

print("\n" + "=" * 70)
print("EGARCH(1,1) COEFFICIENTS - DONNÉES RÉELLES")
print("=" * 70)

params = fitted.params
print(f"  ω (omega)   = {params['omega']:.6f}  [long-run variance]")
print(f"  α (alpha)   = {params['alpha[1]']:.6f}  [magnitude effect]")
print(f"  β (beta)    = {params['beta[1]']:.6f}  [persistence]")
print(f"  γ (gamma)   = {params['gamma[1]']:.6f}  [leverage effect]")

# Interprétation gamma
gamma = params['gamma[1]']
if gamma < 0:
    print(f"\n  ⚠️ Leverage effect CONFIRMÉ (γ = {gamma:.4f} < 0)")
    print(f"     Bad news (returns -) augmente PLUS la vol que good news")
elif gamma > 0:
    print(f"\n  ✓ Asymétrie inverse (γ = {gamma:.4f} > 0)")
    print(f"     Good news augmente PLUS la vol (typique crypto bull)")
else:
    print(f"\n  → Pas d'asymétrie détectée")

# Persistence
persistence = params['beta[1]']
half_life = np.log(0.5) / np.log(persistence) if persistence < 1 else float('inf')
print(f"\n  Persistence β = {persistence:.4f}")
print(f"  Half-life chocs: {half_life:.1f} jours")

print("=" * 70)

# ============================================================================
# 3. PRÉVISION VOLATILITÉ
# ============================================================================

print("\n[3/5] Prévision volatilité...")

# EGARCH: conditional volatility
cond_vol = fitted.conditional_volatility
# Handle both array and Series
if hasattr(cond_vol, 'iloc'):
    daily_vol_forecast = cond_vol.iloc[-1]
    cond_vol_values = cond_vol.values
else:
    daily_vol_forecast = cond_vol[-1]
    cond_vol_values = cond_vol

annual_vol_forecast = daily_vol_forecast * np.sqrt(365)
long_run_vol = np.mean(cond_vol_values)

print(f"\n  ✓ Daily volatility (dernière cond.): {daily_vol_forecast:.3f}%")
print(f"  ✓ Annualized volatility: {annual_vol_forecast:.2f}%")
print(f"  ✓ Long-run average vol: {long_run_vol:.3f}%")

# Prévision multi-jours (mean-reversion)
print("\n  Prévision 5 jours (mean-reversion):")
for i in range(5):
    vol = long_run_vol + (daily_vol_forecast - long_run_vol) * (persistence ** i)
    print(f"    J+{i+1}: {vol:.3f}%")

# ============================================================================
# 4. COMPARAISON GARCH vs EGARCH
# ============================================================================

print("\n[4/5] Comparaison GARCH vs EGARCH...")

# GARCH standard
garch_model = arch_model(df['returns'].values, vol='GARCH', p=1, q=1, dist='Normal', rescale=True)
garch_fitted = garch_model.fit(disp='off', show_warning=False)

# Critères d'information
egarch_aic = fitted.aic
egarch_bic = fitted.bic
garch_aic = garch_fitted.aic
garch_bic = garch_fitted.bic

print("\n  Critères d'information:")
print(f"    GARCH:  AIC = {garch_aic:.2f}, BIC = {garch_bic:.2f}")
print(f"    EGARCH: AIC = {egarch_aic:.2f}, BIC = {egarch_bic:.2f}")

if egarch_aic < garch_aic:
    delta = ((garch_aic - egarch_aic) / garch_aic) * 100
    print(f"\n  ✓ EGARCH meilleur de {delta:.2f}% (AIC)")
    print(f"     → Asymétrie importante pour BTC")
else:
    print(f"\n  → GARCH suffisant (pas d'asymétrie forte)")

# ============================================================================
# 5. VISUALISATION
# ============================================================================

print("\n[5/5] Génération visualisation...")

fig, axes = plt.subplots(3, 2, figsize=(16, 12))

# 1. Returns BTC
axes[0, 0].plot(df['date'].values, df['returns'].values, linewidth=0.8, color='#2E86AB')
axes[0, 0].axhline(y=0, color='black', linestyle='--', alpha=0.5)
axes[0, 0].set_title('BTC/USDT Daily Returns', fontsize=12, fontweight='bold')
axes[0, 0].set_ylabel('Return (%)')
axes[0, 0].grid(True, alpha=0.3)

# 2. Volatilité EGARCH (conditional variance)
vol_dates = df['date'].values[-len(cond_vol_values):]
axes[0, 1].plot(vol_dates, cond_vol_values, linewidth=1.5, color='#A23B72')
axes[0, 1].axhline(y=long_run_vol, color='#F18F01', linestyle='--', label=f'Long-run: {long_run_vol:.2f}%')
axes[0, 1].set_title('EGARCH Conditional Volatility', fontsize=12, fontweight='bold')
axes[0, 1].set_ylabel('Volatility (%)')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# 3. Histogramme des returns
axes[1, 0].hist(df['returns'].values, bins=50, color='#2E86AB', alpha=0.7, edgecolor='black')
axes[1, 0].axvline(x=df['returns'].mean(), color='#A23B72', linestyle='--', linewidth=2, label=f'Mean: {df["returns"].mean():.2f}%')
axes[1, 0].axvline(x=df['returns'].std(), color='#F18F01', linestyle='--', linewidth=2, label=f'+1σ: {df["returns"].std():.2f}%')
axes[1, 0].axvline(x=-df['returns'].std(), color='#F18F01', linestyle='--', linewidth=2, label=f'-1σ: {-df["returns"].std():.2f}%')
axes[1, 0].set_title('Distribution des Returns', fontsize=12, fontweight='bold')
axes[1, 0].set_xlabel('Return (%)')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# 4. QQ-Plot (normalité des résidus)
from scipy import stats
residuals = fitted.std_resid
# Handle both array and Series
if hasattr(residuals, 'dropna'):
    residuals_clean = residuals.dropna()
else:
    residuals_clean = residuals[~np.isnan(residuals)]
stats.probplot(residuals_clean, dist="norm", plot=axes[1, 1])
axes[1, 1].set_title('Q-Q Plot des Résidus Standardisés', fontsize=12, fontweight='bold')
axes[1, 1].grid(True, alpha=0.3)

# 5. Volatility forecast (mean-reversion)
forecast_days = 5
forecast_vol = [long_run_vol + (daily_vol_forecast - long_run_vol) * (persistence ** i) for i in range(forecast_days)]
axes[2, 0].bar(range(1, forecast_days+1), forecast_vol, color='#2E86AB', alpha=0.7, edgecolor='black')
axes[2, 0].axhline(y=long_run_vol, color='#A23B72', linestyle='--', label=f'Long-run: {long_run_vol:.3f}%')
axes[2, 0].set_title('Prévision Volatilité (5 jours - mean-reversion)', fontsize=12, fontweight='bold')
axes[2, 0].set_xlabel('Jours ahead')
axes[2, 0].set_ylabel('Volatility (%)')
axes[2, 0].set_xticks(range(1, forecast_days+1))
axes[2, 0].legend()
axes[2, 0].grid(True, alpha=0.3)

# 6. Leverage effect visualization
# Scatter: negative returns vs volatility increase
returns_vals = df['returns'].values[1:]
vol_changes = cond_vol_values[1:] - cond_vol_values[:-1]
valid_mask = ~(np.isnan(returns_vals) | np.isnan(vol_changes))

axes[2, 1].scatter(returns_vals[valid_mask], vol_changes[valid_mask], alpha=0.3, s=10, color='#2E86AB')
axes[2, 1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
axes[2, 1].axvline(x=0, color='black', linestyle='--', alpha=0.5)
axes[2, 1].set_title('Leverage Effect: Returns vs ΔVolatility', fontsize=12, fontweight='bold')
axes[2, 1].set_xlabel('Return t (%)')
axes[2, 1].set_ylabel('Δ Volatility t+1')
axes[2, 1].grid(True, alpha=0.3)

# Annotation leverage
if gamma < 0:
    axes[2, 1].text(0.05, 0.95, f'Leverage Effect Confirmé\nγ = {gamma:.4f}', 
                   transform=axes[2, 1].transAxes, fontsize=10,
                   bbox=dict(boxstyle='round', facecolor='#F18F01', alpha=0.8))
else:
    axes[2, 1].text(0.05, 0.95, f'Asymétrie Inverse\nγ = {gamma:.4f}', 
                   transform=axes[2, 1].transAxes, fontsize=10,
                   bbox=dict(boxstyle='round', facecolor='#A23B72', alpha=0.8))

plt.tight_layout()
output_path = '/root/.openclaw/workspace/learning/code/egarch_btc_output.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"  ✓ Visualisation sauvegardée: {output_path}")

# ============================================================================
# 6. RÉSUMÉ
# ============================================================================

print("\n" + "=" * 70)
print("RÉSUMÉ EGARCH(1,1)")
print("=" * 70)

print(f"""
Coefficients:
  ω (omega)   = {params['omega']:.6f}
  α (alpha)   = {params['alpha[1]']:.6f}
  β (beta)    = {params['beta[1]']:.6f}
  γ (gamma)   = {params['gamma[1]']:.6f} {'< 0 → Leverage effect' if gamma < 0 else '> 0 → Asymétrie inverse'}

Volatilité:
  Daily (actuelle):  {daily_vol_forecast:.3f}%
  Annualized:        {annual_vol_forecast:.2f}%
  Long-run average:  {long_run_vol:.3f}%
  Half-life:         {half_life:.1f} jours

Modèle:
  AIC: {egarch_aic:.2f} (vs GARCH: {garch_aic:.2f})
  {'✓ EGARCH supérieur' if egarch_aic < garch_aic else '→ GARCH suffisant'}
""")

print("=" * 70)
print("✅ EGARCH(1,1) COMPLÉTÉ")
print("=" * 70)
