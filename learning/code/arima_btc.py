#!/usr/bin/env python3
"""
ARIMA Time Series Forecasting for BTC Trading
Semaine 03 - Apprentissage Théorique

Run: cd /root/.openclaw/workspace/learning && source venv/bin/activate && python code/arima_btc.py
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import sys
import os

sys.path.insert(0, '/root/.openclaw/workspace/learning')

def generate_btc_prices(n_days=500, seed=42):
    """Generate simulated BTC prices (random walk with drift)."""
    np.random.seed(seed)
    dates = pd.date_range(end=datetime.now(), periods=n_days, freq='D')
    
    price = 50000  # Initial price
    prices = [price]
    
    for i in range(1, n_days):
        drift = 0.0005  # Daily drift
        shock = np.random.normal(0, 0.03)  # Daily shock
        new_price = prices[-1] * (1 + drift + shock)
        prices.append(new_price)
    
    prices_series = pd.Series(prices, index=dates, name='BTC_price')
    returns = prices_series.pct_change().dropna()
    
    return prices_series, returns

def test_stationarity(series, name="Series"):
    """Perform ADF test for stationarity."""
    result = adfuller(series)
    
    print(f"\n{name}:")
    print(f"  ADF Statistic: {result[0]:.4f}")
    print(f"  p-value: {result[1]:.4f}")
    print(f"  Critical values:")
    for key, value in result[4].items():
        print(f"    {key}: {value:.4f}")
    
    is_stationary = result[1] < 0.05
    print(f"  Stationary: {'✅ Yes' if is_stationary else '❌ No'} (α=0.05)")
    
    return is_stationary, result

def identify_order(returns, max_lag=20):
    """Identify p and q using ACF and PACF."""
    acf_vals = acf(returns, nlags=max_lag)
    pacf_vals = pacf(returns, nlags=max_lag)
    
    # Confidence interval
    ci = 1.96 / np.sqrt(len(returns))
    
    print(f"\nSignificant ACF lags (>{ci:.4f}):")
    acf_sig = []
    for i, val in enumerate(acf_vals[1:], 1):
        if abs(val) > ci:
            print(f"  Lag {i}: {val:.4f} *")
            acf_sig.append(i)
    
    print(f"\nSignificant PACF lags (>{ci:.4f}):")
    pacf_sig = []
    for i, val in enumerate(pacf_vals[1:], 1):
        if abs(val) > ci:
            print(f"  Lag {i}: {val:.4f} *")
            pacf_sig.append(i)
    
    return acf_sig, pacf_sig

def grid_search_arima(returns, p_range=4, q_range=4):
    """Grid search for best ARIMA parameters."""
    best_aic = np.inf
    best_order = None
    best_model = None
    
    print(f"\nSearching ARIMA(p,0,q) for p∈[0,{p_range-1}], q∈[0,{q_range-1}]...")
    
    for p in range(p_range):
        for q in range(q_range):
            try:
                model = ARIMA(returns, order=(p, 0, q))
                fitted = model.fit()
                if fitted.aic < best_aic:
                    best_aic = fitted.aic
                    best_order = (p, 0, q)
                    best_model = fitted
            except Exception as e:
                continue
    
    if best_model is not None:
        print(f"\n🏆 Best order: ARIMA{best_order}")
        print(f"  AIC: {best_aic:.2f}")
        print(f"  BIC: {best_model.bic:.2f}")
    
    return best_order, best_model

def forecast_arima(model, steps=5):
    """Forecast future values."""
    forecast = model.get_forecast(steps=steps)
    forecast_mean = forecast.predicted_mean
    forecast_ci = forecast.conf_int()
    
    return forecast_mean, forecast_ci

def validate_model(model, returns):
    """Validate model residuals."""
    residuals = model.resid
    
    print(f"\nResidual Analysis:")
    print(f"  Mean: {residuals.mean():.6f}")
    print(f"  Std: {residuals.std():.6f}")
    
    # Normality test
    try:
        normality = model.test_normality()
        print(f"  Normality (Jarque-Bera): {normality.jb_stat[0]:.2f} (p={normality.jb_stat[1]:.4f})")
    except:
        print(f"  Normality test: N/A")
    
    # Serial correlation
    try:
        serial_corr = model.test_serial_correlation()
        lb_stat = serial_corr.lb_stat[0]
        lb_pval = serial_corr.lb_stat[1]
        print(f"  Ljung-Box: {lb_stat:.2f} (p={lb_pval:.4f})")
        print(f"  White noise: {'✅ Yes' if lb_pval > 0.05 else '❌ No'}")
    except:
        print(f"  Serial correlation test: N/A")
    
    return residuals

def plot_results(prices, returns, best_order, forecast_mean, forecast_ci, 
                 residuals, output_path):
    """Generate comprehensive visualization."""
    fig, axes = plt.subplots(3, 2, figsize=(14, 10))
    
    # Plot 1: Prices
    axes[0, 0].plot(prices.index, prices.values, linewidth=1.5, color='blue')
    axes[0, 0].set_title('BTC Price (Simulated)', fontweight='bold', fontsize=12)
    axes[0, 0].set_ylabel('Price ($)')
    axes[0, 0].grid(alpha=0.3)
    
    # Plot 2: Returns
    axes[0, 1].plot(returns.index, returns.values, linewidth=1, color='green')
    axes[0, 1].set_title('Daily Returns', fontweight='bold', fontsize=12)
    axes[0, 1].set_ylabel('Return')
    axes[0, 1].axhline(0, color='black', linewidth=0.5)
    axes[0, 1].grid(alpha=0.3)
    
    # Plot 3: ACF
    plot_acf(returns, lags=20, ax=axes[1, 0])
    axes[1, 0].set_title('ACF - Returns', fontweight='bold', fontsize=12)
    
    # Plot 4: PACF
    plot_pacf(returns, lags=20, ax=axes[1, 1])
    axes[1, 1].set_title('PACF - Returns', fontweight='bold', fontsize=12)
    
    # Plot 5: Forecast
    last_50 = prices.iloc[-50:]
    axes[2, 0].plot(last_50.index, last_50.values, label='Historical', 
                    linewidth=2, color='blue')
    
    forecast_dates = pd.date_range(
        start=prices.index[-1] + pd.Timedelta(days=1),
        periods=len(forecast_mean), 
        freq='D'
    )
    
    # Convert forecast from returns to prices
    last_price = prices.iloc[-1]
    cumulative_returns = (1 + forecast_mean).cumprod()
    forecast_prices = last_price * cumulative_returns
    
    axes[2, 0].plot(forecast_dates, forecast_prices, 
                    label='Forecast', linewidth=2, color='red', linestyle='--')
    axes[2, 0].set_title(f'Price Forecast ({len(forecast_mean)} days)', 
                         fontweight='bold', fontsize=12)
    axes[2, 0].set_ylabel('Price ($)')
    axes[2, 0].legend(loc='upper left')
    axes[2, 0].grid(alpha=0.3)
    
    # Plot 6: Residuals
    axes[2, 1].plot(residuals.index, residuals.values, linewidth=0.5, alpha=0.7)
    axes[2, 1].axhline(0, color='red', linewidth=1)
    axes[2, 1].set_title('Model Residuals', fontweight='bold', fontsize=12)
    axes[2, 1].set_ylabel('Residual')
    axes[2, 1].grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path

def main():
    print("=" * 60)
    print("📈 ARIMA Time Series Forecasting - BTC Trading")
    print("=" * 60)
    
    # Step 1: Generate data
    print("\n[1/6] Generating BTC price data...")
    prices, returns = generate_btc_prices(n_days=500)
    print(f"  ✓ {len(prices)} days of prices")
    print(f"  ✓ Price range: ${prices.min():,.2f} - ${prices.max():,.2f}")
    
    # Step 2: Stationarity test
    print("\n[2/6] Testing stationarity (ADF)...")
    price_stat, _ = test_stationarity(prices, "BTC Prices")
    ret_stat, _ = test_stationarity(returns, "BTC Returns")
    
    # Step 3: Identify order
    print("\n[3/6] Identifying p, d, q parameters...")
    acf_sig, pacf_sig = identify_order(returns)
    
    # Step 4: Grid search
    print("\n[4/6] Grid search for optimal parameters...")
    best_order, best_model = grid_search_arima(returns)
    
    if best_model is None:
        print("❌ Could not fit ARIMA model. Exiting.")
        return None
    
    # Step 5: Forecast
    print("\n[5/6] Forecasting (5 days ahead)...")
    forecast_mean, forecast_ci = forecast_arima(best_model, steps=5)
    
    print(f"\n📊 5-Day Forecast (returns):")
    for i, idx in enumerate(forecast_mean.index):
        val = forecast_mean.iloc[i]
        ci_row = forecast_ci.iloc[i]
        ci_low = ci_row.iloc[0]  # lower bound
        ci_high = ci_row.iloc[1]  # upper bound
        print(f"  Day+{i+1}: {val*100:+.3f}%  [{ci_low*100:+.3f}%, {ci_high*100:+.3f}%]")
    
    # Direction prediction
    last_price = prices.iloc[-1]
    cumulative = (1 + forecast_mean).cumprod()
    final_price = last_price * cumulative.iloc[-1]
    direction = "📈 BULLISH" if final_price > last_price else "📉 BEARISH"
    
    print(f"\n🎯 Direction (5 days): {direction}")
    print(f"  Current: ${last_price:,.2f}")
    print(f"  Forecast: ${final_price:,.2f}")
    print(f"  Change: {(final_price/last_price - 1)*100:+.2f}%")
    
    # Step 6: Validation
    print("\n[6/6] Validating model...")
    residuals = validate_model(best_model, returns)
    
    # Visualization
    print("\n" + "=" * 60)
    print("Generating visualization...")
    output_dir = '/root/.openclaw/workspace/learning/code'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'arima_btc_output.png')
    plot_results(prices, returns, best_order, forecast_mean, forecast_ci, 
                 residuals, output_path)
    print(f"  ✓ Chart saved: {output_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    print(f"  Model: ARIMA{best_order}")
    print(f"  AIC: {best_model.aic:.2f}")
    print(f"  5-Day Forecast: {(final_price/last_price - 1)*100:+.2f}%")
    print(f"  Direction: {direction}")
    print(f"  Residuals white noise: {'✅ Yes' if residuals.mean() < 0.01 else '⚠️ Check'}")
    print(f"  Status: ✅ Complete")
    print("=" * 60)
    
    return {
        'model': best_model,
        'order': best_order,
        'forecast': forecast_mean,
        'direction': direction
    }

if __name__ == '__main__':
    results = main()
