#!/usr/bin/env python3
"""
GARCH Volatility Modeling - BTC Real Data

Uses real BTC/USDT data from Binance (2020-2026)
Validates GARCH model on actual market conditions
"""

import ccxt
import pandas as pd
import numpy as np
from arch import arch_model
import matplotlib.pyplot as plt
from datetime import datetime, timezone
import warnings
warnings.filterwarnings('ignore')

# Initialize Binance exchange
exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

def fetch_btc_data(timeframe='1d', limit=2000):
    """Fetch BTC/USDT OHLCV data from Binance"""
    print(f"[1/5] Fetching BTC/USDT data from Binance ({timeframe}, {limit} candles)...")
    
    ohlcv = exchange.fetch_ohlcv('BTC/USDT', timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    # Calculate returns
    df['returns'] = df['close'].pct_change()
    df.dropna(inplace=True)
    
    print(f"  ✓ Data range: {df.index[0].date()} to {df.index[-1].date()}")
    print(f"  ✓ Total days: {len(df)}")
    print(f"  ✓ Mean daily return: {df['returns'].mean():.4f} ({df['returns'].mean()*100:.2f}%)")
    print(f"  ✓ Std daily return: {df['returns'].std():.4f} ({df['returns'].std()*100:.2f}%)")
    
    return df

def fit_garch_model(returns):
    """Fit GARCH(1,1) model"""
    print("\n[2/5] Fitting GARCH(1,1) model...")
    
    # Scale returns to improve convergence (multiply by 100 to get percentage)
    returns_scaled = returns * 100
    
    model = arch_model(returns_scaled, vol='GARCH', p=1, q=1, mean='Constant', rescale=False)
    fitted = model.fit(disp='off')
    
    print("\n" + "="*60)
    print("GARCH(1,1) COEFFICIENTS")
    print("="*60)
    
    params = fitted.params
    omega = params['omega']
    alpha = params['alpha[1]']
    beta = params['beta[1]']
    persistence = alpha + beta
    
    print(f"  ω (omega)   = {omega:.6f}  [long-run variance]")
    print(f"  α (alpha)   = {alpha:.4f}  [news impact]")
    print(f"  β (beta)    = {beta:.4f}  [persistence]")
    print(f"  α + β       = {persistence:.4f}  [persistence total]")
    
    # Calculate half-life of volatility shocks
    half_life = np.log(0.5) / np.log(persistence)
    print(f"  Half-life   = {half_life:.1f} days")
    
    return fitted, returns_scaled

def forecast_volatility(fitted, returns_scaled):
    """Forecast volatility 1 day ahead"""
    print("\n[3/5] Forecasting volatility (1 day ahead)...")
    
    forecast = fitted.forecast(horizon=1)
    variance_forecast = forecast.variance.iloc[-1].values[0]
    
    # Convert back to daily volatility (was scaled by 100)
    daily_vol = np.sqrt(variance_forecast) / 100
    annualized_vol = daily_vol * np.sqrt(252) * 100
    
    print(f"  ✓ Daily volatility forecast: {daily_vol*100:.3f}%")
    print(f"  ✓ Annualized volatility: {annualized_vol:.2f}%")
    
    return daily_vol, annualized_vol

def validate_model(fitted, returns_scaled):
    """Validate model against realized volatility"""
    print("\n[4/5] Validating against realized volatility...")
    
    # Conditional volatility from GARCH
    conditional_vol = np.sqrt(fitted.conditional_volatility) / 100
    
    # Realized volatility (20-day rolling)
    realized_vol = returns_scaled.rolling(20).std() / 100
    
    # Calculate metrics
    valid_mask = ~conditional_vol.isna() & ~realized_vol.isna()
    
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    mse = mean_squared_error(realized_vol[valid_mask], conditional_vol[valid_mask])
    mae = mean_absolute_error(realized_vol[valid_mask], conditional_vol[valid_mask])
    correlation = conditional_vol[valid_mask].corr(realized_vol[valid_mask])
    r_squared = correlation ** 2
    
    print(f"  ✓ Mean GARCH vol: {conditional_vol.mean()*100:.2f}%")
    print(f"  ✓ Mean Realized vol (20d): {realized_vol.mean()*100:.2f}%")
    print(f"  ✓ Correlation: {correlation:.3f}")
    print(f"  ✓ R²: {r_squared:.4f}")
    print(f"  ✓ MAE: {mae:.6f}")
    print(f"  ✓ MSE: {mse:.6f}")
    
    return conditional_vol, realized_vol, r_squared

def create_visualization(df, conditional_vol, realized_vol, annualized_vol):
    """Generate visualization"""
    print("\n[5/5] Generating visualization...")
    
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))
    
    # Plot 1: BTC Price
    axes[0].plot(df.index, df['close'], label='BTC Price', linewidth=1, color='blue')
    axes[0].set_title('BTC/USDT Price History', fontsize=12, fontweight='bold')
    axes[0].set_ylabel('Price (USDT)')
    axes[0].legend(loc='upper left')
    axes[0].grid(alpha=0.3)
    
    # Plot 2: Returns
    axes[1].plot(df.index, df['returns']*100, label='Daily Returns (%)', linewidth=0.5, color='green', alpha=0.7)
    axes[1].axhline(0, color='black', linestyle='-', linewidth=0.5)
    axes[1].set_title('BTC Daily Returns', fontsize=12, fontweight='bold')
    axes[1].set_ylabel('Return (%)')
    axes[1].legend(loc='upper left')
    axes[1].grid(alpha=0.3)
    
    # Plot 3: Volatility Comparison
    axes[2].plot(conditional_vol.index, conditional_vol.values*100, 
                 label='GARCH Conditional Vol', alpha=0.7, linewidth=1.5, color='orange')
    axes[2].plot(realized_vol.index, realized_vol.values*100, 
                 label='Realized Vol (20d)', alpha=0.7, linewidth=1.5, color='red')
    axes[2].axhline(annualized_vol, color='purple', linestyle='--', 
                    label=f'Forecast 1j ({annualized_vol:.1f}%)', linewidth=2)
    axes[2].set_title('Volatility: GARCH Model vs Realized', fontsize=12, fontweight='bold')
    axes[2].set_ylabel('Volatility (% annualized)')
    axes[2].legend(loc='upper left')
    axes[2].grid(alpha=0.3)
    
    plt.tight_layout()
    output_path = 'code/garch_btc_realdata_output.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  ✓ Chart saved: {output_path}")
    
    return output_path

def main():
    print("="*60)
    print("📊 GARCH(1,1) Volatility Modeling - BTC Real Data")
    print("="*60)
    
    try:
        # Fetch real data
        df = fetch_btc_data(timeframe='1d', limit=2000)
        
        # Fit model
        fitted, returns_scaled = fit_garch_model(df['returns'])
        
        # Forecast
        daily_vol, annualized_vol = forecast_volatility(fitted, returns_scaled)
        
        # Validate
        conditional_vol, realized_vol, r_squared = validate_model(fitted, returns_scaled)
        
        # Visualize
        output_path = create_visualization(df, conditional_vol, realized_vol, annualized_vol)
        
        # Summary
        print("\n" + "="*60)
        print("📋 SUMMARY")
        print("="*60)
        print(f"  Data: {len(df)} days ({df.index[0].date()} to {df.index[-1].date()})")
        print(f"  Model: GARCH(1,1) on BTC/USDT real data")
        print(f"  Persistence (α+β): {fitted.params['alpha[1]'] + fitted.params['beta[1]']:.4f}")
        print(f"  1-Day Vol Forecast: {annualized_vol:.2f}% (annualized)")
        print(f"  Model Fit (R²): {r_squared:.4f}")
        print(f"  Status: ✅ Complete")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
