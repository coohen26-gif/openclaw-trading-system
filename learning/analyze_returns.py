#!/usr/bin/env python3
"""
Analyze BTC return distributions - Semaine 1
Calculate returns, statistics, and generate visualizations.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.tsa.stattools import adfuller
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

def load_data():
    """Load BTC data from CSV files."""
    data = {}
    for tf in ['5m', '1h', '1d']:
        path = f'/root/.openclaw/workspace/learning/data/btc_{tf}.csv'
        df = pd.read_csv(path, index_col='timestamp', parse_dates=True)
        data[tf] = df
        print(f"Loaded {tf}: {len(df)} records, {df.index.min()} to {df.index.max()}")
    return data

def calculate_returns(df):
    """Calculate simple and log returns."""
    df = df.copy()
    
    # Simple returns: (P_t - P_{t-1}) / P_{t-1}
    df['simple_return'] = df['close'].pct_change()
    
    # Log returns: ln(P_t / P_{t-1})
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    
    return df

def calculate_statistics(returns, name=''):
    """Calculate comprehensive statistics for returns."""
    stats_dict = {}
    
    # Basic stats
    stats_dict['mean'] = returns.mean()
    stats_dict['std'] = returns.std()
    stats_dict['min'] = returns.min()
    stats_dict['max'] = returns.max()
    stats_dict['median'] = returns.median()
    
    # Skewness (asymétrie)
    stats_dict['skewness'] = returns.skew()
    
    # Kurtosis (excess kurtosis, so >0 means fat tails)
    stats_dict['kurtosis'] = returns.kurtosis()
    
    # Normality tests
    # Shapiro-Wilk (better for smaller samples)
    try:
        shapiro_stat, shapiro_p = stats.shapiro(returns.dropna().values[:5000])  # limit for speed
        stats_dict['shapiro_stat'] = shapiro_stat
        stats_dict['shapiro_p'] = shapiro_p
    except:
        stats_dict['shapiro_stat'] = np.nan
        stats_dict['shapiro_p'] = np.nan
    
    # Jarque-Bera test
    jb_stat, jb_p = stats.jarque_bera(returns.dropna())
    stats_dict['jb_stat'] = jb_stat
    stats_dict['jb_p'] = jb_p
    
    return stats_dict

def plot_distribution(returns, timeframe, return_type, ax):
    """Plot histogram with normal overlay."""
    returns_clean = returns.dropna()
    
    # Histogram
    ax.hist(returns_clean, bins=100, density=True, alpha=0.7, label='Actual', color='steelblue', edgecolor='black')
    
    # Normal distribution overlay
    mu, sigma = returns_clean.mean(), returns_clean.std()
    x = np.linspace(returns_clean.min(), returns_clean.max(), 100)
    ax.plot(x, stats.norm.pdf(x, mu, sigma), 'r-', linewidth=2, label='Normal Distribution')
    
    ax.set_xlabel(f'{return_type.capitalize()} Return')
    ax.set_ylabel('Density')
    ax.set_title(f'{timeframe} - {return_type.capitalize()} Returns Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)

def plot_qq(returns, timeframe, return_type, ax):
    """Plot Q-Q plot against normal distribution."""
    returns_clean = returns.dropna()
    stats.probplot(returns_clean, dist="norm", plot=ax)
    ax.set_title(f'{timeframe} - {return_type.capitalize()} Returns Q-Q Plot')
    ax.grid(True, alpha=0.3)

def test_stationarity(prices, returns, name=''):
    """Perform ADF test for stationarity."""
    # ADF test on prices
    adf_prices = adfuller(prices.dropna(), maxlag=10, autolag='AIC')
    
    # ADF test on returns
    adf_returns = adfuller(returns.dropna(), maxlag=10, autolag='AIC')
    
    return {
        'prices_adf_stat': adf_prices[0],
        'prices_p_value': adf_prices[1],
        'prices_is_stationary': adf_prices[1] < 0.05,
        'returns_adf_stat': adf_returns[0],
        'returns_p_value': adf_returns[1],
        'returns_is_stationary': adf_returns[1] < 0.05,
    }

def calculate_volatility(df, window=20):
    """Calculate rolling volatility."""
    df = df.copy()
    df['rolling_vol'] = df['log_return'].rolling(window=window).std() * np.sqrt(252)  # annualized
    return df

def plot_volatility_clustering(df, timeframe, ax):
    """Plot volatility over time to show clustering."""
    ax.plot(df.index, df['rolling_vol'], linewidth=0.5, color='steelblue')
    ax.set_xlabel('Date')
    ax.set_ylabel('Annualized Volatility')
    ax.set_title(f'{timeframe} - Rolling Volatility (20-period)')
    ax.grid(True, alpha=0.3)
    ax.axhline(df['rolling_vol'].mean(), color='red', linestyle='--', label='Mean Vol', alpha=0.7)
    ax.legend()

def main():
    print("=" * 60)
    print("SEMAINE 1 - Analyse des distributions de returns BTC")
    print("=" * 60)
    
    # Load data
    print("\n[1] Chargement des données...")
    data = load_data()
    
    # Calculate returns
    print("\n[2] Calcul des returns...")
    for tf in data:
        data[tf] = calculate_returns(data[tf])
        print(f"  {tf}: Mean simple return = {data[tf]['simple_return'].mean():.6f}, "
              f"Std = {data[tf]['simple_return'].std():.6f}")
    
    # Calculate statistics
    print("\n[3] Statistiques descriptives...")
    all_stats = {}
    for tf in data:
        print(f"\n  {tf.upper()}:")
        simple_stats = calculate_statistics(data[tf]['simple_return'], f'{tf}_simple')
        log_stats = calculate_statistics(data[tf]['log_return'], f'{tf}_log')
        all_stats[tf] = {'simple': simple_stats, 'log': log_stats}
        
        print(f"    Simple Return:")
        print(f"      Mean: {simple_stats['mean']:.6f}")
        print(f"      Std: {simple_stats['std']:.6f}")
        print(f"      Skewness: {simple_stats['skewness']:.4f}")
        print(f"      Kurtosis (excess): {simple_stats['kurtosis']:.4f}")
        print(f"      Jarque-Bera p-value: {simple_stats['jb_p']:.2e}")
        print(f"    Log Return:")
        print(f"      Mean: {log_stats['mean']:.6f}")
        print(f"      Std: {log_stats['std']:.6f}")
        print(f"      Skewness: {log_stats['skewness']:.4f}")
        print(f"      Kurtosis (excess): {log_stats['kurtosis']:.4f}")
        print(f"      Jarque-Bera p-value: {log_stats['jb_p']:.2e}")
    
    # Stationarity tests
    print("\n[4] Tests de stationnarité (ADF)...")
    stationarity_results = {}
    for tf in data:
        result = test_stationarity(data[tf]['close'], data[tf]['log_return'], tf)
        stationarity_results[tf] = result
        print(f"\n  {tf.upper()}:")
        print(f"    Prices: ADF stat = {result['prices_adf_stat']:.4f}, "
              f"p-value = {result['prices_p_value']:.4f}, "
              f"Stationary: {result['prices_is_stationary']}")
        print(f"    Returns: ADF stat = {result['returns_adf_stat']:.4f}, "
              f"p-value = {result['returns_p_value']:.4f}, "
              f"Stationary: {result['returns_is_stationary']}")
    
    # Volatility analysis
    print("\n[5] Analyse de la volatilité...")
    for tf in data:
        data[tf] = calculate_volatility(data[tf])
        print(f"  {tf}: Mean annualized vol = {data[tf]['rolling_vol'].mean():.4f}, "
              f"Std of vol = {data[tf]['rolling_vol'].std():.4f}")
    
    # Generate plots
    print("\n[6] Génération des graphiques...")
    
    # Figure 1: Distributions
    fig1, axes = plt.subplots(3, 2, figsize=(14, 12))
    for idx, tf in enumerate(['5m', '1h', '1d']):
        plot_distribution(data[tf]['log_return'], tf, 'log', axes[idx, 0])
        plot_qq(data[tf]['log_return'], tf, 'log', axes[idx, 1])
    plt.tight_layout()
    fig1.savefig('/root/.openclaw/workspace/learning/figures/01_distributions.png', dpi=150, bbox_inches='tight')
    print("  Saved: 01_distributions.png")
    
    # Figure 2: Volatility clustering
    fig2, axes = plt.subplots(3, 1, figsize=(14, 10))
    for idx, tf in enumerate(['5m', '1h', '1d']):
        plot_volatility_clustering(data[tf], tf, axes[idx])
    plt.tight_layout()
    fig2.savefig('/root/.openclaw/workspace/learning/figures/02_volatility_clustering.png', dpi=150, bbox_inches='tight')
    print("  Saved: 02_volatility_clustering.png")
    
    # Figure 3: Price evolution
    fig3, axes = plt.subplots(3, 1, figsize=(14, 10))
    for idx, tf in enumerate(['5m', '1h', '1d']):
        axes[idx].plot(data[tf].index, data[tf]['close'], linewidth=0.5, color='steelblue')
        axes[idx].set_xlabel('Date')
        axes[idx].set_ylabel('Price (USDT)')
        axes[idx].set_title(f'{tf} - BTC/USDT Price Evolution')
        axes[idx].grid(True, alpha=0.3)
    plt.tight_layout()
    fig3.savefig('/root/.openclaw/workspace/learning/figures/03_price_evolution.png', dpi=150, bbox_inches='tight')
    print("  Saved: 03_price_evolution.png")
    
    # Figure 4: Returns time series
    fig4, axes = plt.subplots(3, 1, figsize=(14, 10))
    for idx, tf in enumerate(['5m', '1h', '1d']):
        axes[idx].plot(data[tf].index, data[tf]['log_return'], linewidth=0.3, color='darkred', alpha=0.7)
        axes[idx].set_xlabel('Date')
        axes[idx].set_ylabel('Log Return')
        axes[idx].set_title(f'{tf} - Log Returns Time Series')
        axes[idx].grid(True, alpha=0.3)
        axes[idx].axhline(0, color='black', linestyle='-', linewidth=0.5)
    plt.tight_layout()
    fig4.savefig('/root/.openclaw/workspace/learning/figures/04_returns_timeseries.png', dpi=150, bbox_inches='tight')
    print("  Saved: 04_returns_timeseries.png")
    
    # Summary
    print("\n" + "=" * 60)
    print("RÉSUMÉ DES CONCLUSIONS")
    print("=" * 60)
    
    print("\n📊 DISTRIBUTION DES RETURNS:")
    for tf in ['5m', '1h', '1d']:
        s = all_stats[tf]['log']
        print(f"\n  {tf}:")
        print(f"    • Skewness: {s['skewness']:.4f} "
              f"({'asymétrie négative' if s['skewness'] < 0 else 'asymétrie positive'})")
        print(f"    • Kurtosis (excess): {s['kurtosis']:.4f} "
              f"({'fat tails - leptokurtique' if s['kurtosis'] > 0 else 'thin tails'})")
        print(f"    • Normalité rejetée: {s['jb_p'] < 0.05} (JB p-value = {s['jb_p']:.2e})")
    
    print("\n📈 STATIONNARITÉ:")
    for tf in ['5m', '1h', '1d']:
        r = stationarity_results[tf]
        print(f"  {tf}: Prix stationnaire = {r['prices_is_stationary']}, "
              f"Returns stationnaire = {r['returns_is_stationary']}")
    
    print("\n📉 VOLATILITÉ:")
    for tf in ['5m', '1h', '1d']:
        vol = data[tf]['rolling_vol']
        print(f"  {tf}: Mean = {vol.mean():.4f}, Std = {vol.std():.4f}, "
              f"Ratio Std/Mean = {vol.std()/vol.mean():.2f} "
              f"({'clustering visible' if vol.std()/vol.mean() > 0.3 else 'peu de clustering'})")
    
    print("\n✅ Analyse terminée! Graphiques sauvegardés dans learning/figures/")
    
    return {
        'data': data,
        'stats': all_stats,
        'stationarity': stationarity_results
    }

if __name__ == '__main__':
    results = main()
