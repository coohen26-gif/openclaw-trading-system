#!/usr/bin/env python3
"""
GARCH(1,1) Volatility Modeling for BTC Trading
Semaine 02 - Apprentissage Théorique

Run: cd /root/.openclaw/workspace/learning && source venv/bin/activate && python code/garch_btc.py
"""

import pandas as pd
import numpy as np
from arch import arch_model
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import sys
import os

# Add workspace to path
sys.path.insert(0, '/root/.openclaw/workspace/learning')

def generate_btc_returns(n_days=500, seed=42):
    """Generate simulated BTC returns with volatility clustering."""
    np.random.seed(seed)
    dates = pd.date_range(end=datetime.now(), periods=n_days, freq='D')
    
    # Base returns with clustering
    returns = np.random.normal(0.001, 0.04, n_days)
    
    # Add volatility regimes
    returns[100:150] *= 3    # High vol period
    returns[300:350] *= 2.5  # Medium-high vol period
    
    return pd.Series(returns, index=dates, name='BTC_returns')

def fit_garch(returns_series):
    """Fit GARCH(1,1) model."""
    model = arch_model(returns_series, vol='GARCH', p=1, q=1, mean='Constant')
    fitted = model.fit(disp='off')
    return fitted

def forecast_volatility(fitted_model, horizon=1):
    """Forecast volatility N days ahead."""
    forecast = fitted_model.forecast(horizon=horizon)
    variance_forecast = forecast.variance.iloc[-1].values[0]
    vol_forecast = np.sqrt(variance_forecast)
    return vol_forecast

def calculate_realized_vol(returns_series, window=20):
    """Calculate rolling realized volatility (annualized)."""
    realized = returns_series.rolling(window).std() * np.sqrt(252)
    return realized

def validate_garch(fitted_model, realized_vol):
    """Validate GARCH model against realized volatility."""
    conditional_vol = np.sqrt(fitted_model.conditional_volatility) * np.sqrt(252)
    
    # Alignment
    valid_idx = ~conditional_vol.isna() & ~realized_vol.isna()
    
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    
    mse = mean_squared_error(realized_vol[valid_idx], conditional_vol[valid_idx])
    mae = mean_absolute_error(realized_vol[valid_idx], conditional_vol[valid_idx])
    r2 = conditional_vol[valid_idx].corr(realized_vol[valid_idx])**2
    
    return {
        'mse': mse,
        'mae': mae,
        'r2': r2,
        'correlation': conditional_vol[valid_idx].corr(realized_vol[valid_idx]),
        'conditional_vol': conditional_vol,
        'realized_vol': realized_vol
    }

def plot_results(returns_series, fitted_model, validation, vol_forecast, output_path):
    """Generate visualization."""
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot 1: Cumulative returns
    axes[0].plot(returns_series.index, returns_series.cumsum(), 
                 label='Cumulative Returns', linewidth=1.5, color='blue')
    axes[0].set_title('BTC Performance (Simulated)', fontsize=14, fontweight='bold')
    axes[0].set_ylabel('Cumulative Return')
    axes[0].legend(loc='upper left')
    axes[0].grid(alpha=0.3)
    
    # Plot 2: Volatility comparison
    axes[1].plot(validation['conditional_vol'].index, 
                 validation['conditional_vol'].values, 
                 label='GARCH Conditional Vol', alpha=0.8, linewidth=2)
    axes[1].plot(validation['realized_vol'].index, 
                 validation['realized_vol'].values, 
                 label='Realized Vol (20d)', alpha=0.7, linewidth=1.5)
    
    # Forecast line
    forecast_annual = vol_forecast * np.sqrt(252) * 100
    axes[1].axhline(forecast_annual, color='red', linestyle='--', 
                    linewidth=2, label=f'1-Day Forecast: {forecast_annual:.2f}%')
    
    axes[1].set_title('Volatility: GARCH vs Realized', fontsize=14, fontweight='bold')
    axes[1].set_ylabel('% Annualized')
    axes[1].legend(loc='upper left')
    axes[1].grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path

def main():
    print("=" * 60)
    print("📊 GARCH(1,1) Volatility Modeling - BTC Trading")
    print("=" * 60)
    
    # Step 1: Generate/Load data
    print("\n[1/5] Loading return data...")
    returns = generate_btc_returns(n_days=500)
    print(f"  ✓ {len(returns)} days of returns ({returns.index[0].date()} to {returns.index[-1].date()})")
    print(f"  ✓ Mean daily return: {returns.mean()*100:.3f}%")
    print(f"  ✓ Std daily return: {returns.std()*100:.2f}%")
    
    # Step 2: Fit GARCH model
    print("\n[2/5] Fitting GARCH(1,1) model...")
    fitted = fit_garch(returns)
    
    print("\n" + "=" * 60)
    print("GARCH(1,1) COEFFICIENTS")
    print("=" * 60)
    print(f"  ω (omega) = {fitted.params['omega']:.6f}  [long-run variance]")
    print(f"  α (alpha) = {fitted.params['alpha[1]']:.4f}  [news impact]")
    print(f"  β (beta)  = {fitted.params['beta[1]']:.4f}  [persistence]")
    print(f"  α + β     = {fitted.params['alpha[1]'] + fitted.params['beta[1]']:.4f}  [persistence total]")
    
    # Step 3: Forecast
    print("\n[3/5] Forecasting volatility (1 day ahead)...")
    vol_forecast_daily = forecast_volatility(fitted, horizon=1)
    vol_forecast_annual = vol_forecast_daily * np.sqrt(252) * 100
    print(f"  ✓ Daily volatility forecast: {vol_forecast_daily*100:.3f}%")
    print(f"  ✓ Annualized: {vol_forecast_annual:.2f}%")
    
    # Step 4: Validation
    print("\n[4/5] Validating against realized volatility...")
    realized_vol = calculate_realized_vol(returns, window=20) * 100
    validation = validate_garch(fitted, realized_vol)
    
    print(f"  ✓ Mean GARCH vol: {validation['conditional_vol'].mean():.2f}%")
    print(f"  ✓ Mean Realized vol: {validation['realized_vol'].mean():.2f}%")
    print(f"  ✓ Correlation: {validation['correlation']:.3f}")
    print(f"  ✓ R²: {validation['r2']:.4f}")
    print(f"  ✓ MAE: {validation['mae']:.4f}")
    print(f"  ✓ MSE: {validation['mse']:.4f}")
    
    # Step 5: Visualization
    print("\n[5/5] Generating visualization...")
    output_dir = '/root/.openclaw/workspace/learning/code'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'garch_btc_output.png')
    plot_results(returns, fitted, validation, vol_forecast_daily, output_path)
    print(f"  ✓ Chart saved: {output_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    print(f"  Model: GARCH(1,1) on BTC simulated returns")
    print(f"  Persistence (α+β): {fitted.params['alpha[1]'] + fitted.params['beta[1]']:.4f}")
    print(f"  1-Day Vol Forecast: {vol_forecast_annual:.2f}% (annualized)")
    print(f"  Model Fit (R²): {validation['r2']:.4f}")
    print(f"  Status: ✅ Complete")
    print("=" * 60)
    
    return {
        'model': fitted,
        'forecast_daily': vol_forecast_daily,
        'forecast_annual': vol_forecast_annual,
        'validation': validation
    }

if __name__ == '__main__':
    results = main()
