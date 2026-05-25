#!/usr/bin/env python3
"""
VaR and CVaR Analysis for BTC/ETH
Master 4 - Risk Management Advanced
"""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)

def load_btc_data():
    """Load BTC data and calculate returns"""
    df = pd.read_csv('/root/.openclaw/workspace/learning/data/btc_1d.csv', parse_dates=['timestamp'])
    df = df.sort_values('timestamp')
    df['returns'] = df['close'].pct_change()
    df = df.dropna()
    return df

def historical_var(returns, confidence_level=0.95):
    """Calculate Historical VaR"""
    return np.percentile(returns, (1 - confidence_level) * 100)

def parametric_var(returns, confidence_level=0.95):
    """Calculate Parametric (Gaussian) VaR"""
    mu = returns.mean()
    sigma = returns.std()
    z = stats.norm.ppf(1 - confidence_level)
    return mu + z * sigma

def monte_carlo_var(returns, confidence_level=0.95, n_simulations=10000):
    """Calculate Monte Carlo VaR"""
    mu = returns.mean()
    sigma = returns.std()
    
    # Simulate returns
    simulated_returns = np.random.normal(mu, sigma, n_simulations)
    return np.percentile(simulated_returns, (1 - confidence_level) * 100)

def historical_cvar(returns, confidence_level=0.95):
    """Calculate Historical CVaR (Expected Shortfall)"""
    var = historical_var(returns, confidence_level)
    return returns[returns <= var].mean()

def parametric_cvar(returns, confidence_level=0.95):
    """Calculate Parametric CVaR"""
    mu = returns.mean()
    sigma = returns.std()
    z = stats.norm.ppf(1 - confidence_level)
    # CVaR for normal distribution
    return mu - sigma * stats.norm.pdf(z) / (1 - confidence_level)

def monte_carlo_cvar(returns, confidence_level=0.95, n_simulations=10000):
    """Calculate Monte Carlo CVaR"""
    mu = returns.mean()
    sigma = returns.std()
    
    simulated_returns = np.random.normal(mu, sigma, n_simulations)
    var = np.percentile(simulated_returns, (1 - confidence_level) * 100)
    return simulated_returns[simulated_returns <= var].mean()

def calculate_var_metrics(returns, portfolio_value=100000):
    """Calculate all VaR metrics"""
    confidence_levels = [0.95, 0.99]
    results = []
    
    for cl in confidence_levels:
        h_var = historical_var(returns, cl)
        p_var = parametric_var(returns, cl)
        mc_var = monte_carlo_var(returns, cl)
        
        h_cvar = historical_cvar(returns, cl)
        p_cvar = parametric_cvar(returns, cl)
        mc_cvar = monte_carlo_cvar(returns, cl)
        
        results.append({
            'confidence_level': cl,
            'historical_var': h_var,
            'parametric_var': p_var,
            'monte_carlo_var': mc_var,
            'historical_cvar': h_cvar,
            'parametric_cvar': p_cvar,
            'monte_carlo_cvar': mc_cvar,
            'var_dollar_95': h_var * portfolio_value if cl == 0.95 else None,
            'cvar_dollar_95': h_cvar * portfolio_value if cl == 0.95 else None
        })
    
    return results

def plot_var_distribution(returns, results, save_path=None):
    """Plot return distribution with VaR and CVaR markers"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Return distribution with Historical VaR/CVaR
    ax1 = axes[0, 0]
    sns.histplot(returns, bins=50, kde=True, ax=ax1, color='steelblue', alpha=0.7)
    ax1.axvline(historical_var(returns, 0.95), color='red', linestyle='--', linewidth=2, label='VaR 95%')
    ax1.axvline(historical_cvar(returns, 0.95), color='darkred', linestyle='-', linewidth=2, label='CVaR 95%')
    ax1.axvline(historical_var(returns, 0.99), color='orange', linestyle='--', linewidth=2, label='VaR 99%')
    ax1.axvline(historical_cvar(returns, 0.99), color='darkorange', linestyle='-', linewidth=2, label='CVaR 99%')
    ax1.set_xlabel('Daily Returns')
    ax1.set_ylabel('Frequency')
    ax1.set_title('BTC Daily Returns Distribution with VaR and CVaR Markers')
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # 2. Q-Q Plot
    ax2 = axes[0, 1]
    stats.probplot(returns, dist="norm", plot=ax2)
    ax2.set_title('Q-Q Plot vs Normal Distribution')
    ax2.grid(alpha=0.3)
    
    # 3. Rolling VaR (95%)
    ax3 = axes[1, 0]
    rolling_var = returns.rolling(window=30).apply(lambda x: historical_var(x, 0.95))
    rolling_var.plot(ax=ax3, color='red', linewidth=2)
    ax3.set_xlabel('Date')
    ax3.set_ylabel('Rolling 30-day VaR (95%)')
    ax3.set_title('Time-Varying Risk: Rolling VaR')
    ax3.grid(alpha=0.3)
    
    # 4. VaR Comparison (Historical vs Parametric vs Monte Carlo)
    ax4 = axes[1, 1]
    confidence_levels = np.linspace(0.90, 0.99, 10)
    hist_vars = [historical_var(returns, cl) for cl in confidence_levels]
    param_vars = [parametric_var(returns, cl) for cl in confidence_levels]
    mc_vars = [monte_carlo_var(returns, cl) for cl in confidence_levels]
    
    ax4.plot(confidence_levels, hist_vars, 'o-', label='Historical', linewidth=2, markersize=8)
    ax4.plot(confidence_levels, param_vars, 's-', label='Parametric (Gaussian)', linewidth=2, markersize=8)
    ax4.plot(confidence_levels, mc_vars, '^-', label='Monte Carlo', linewidth=2, markersize=8)
    ax4.set_xlabel('Confidence Level')
    ax4.set_ylabel('VaR')
    ax4.set_title('VaR Methods Comparison Across Confidence Levels')
    ax4.legend()
    ax4.grid(alpha=0.3)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    plt.close()

def plot_cvar_comparison(returns, save_path=None):
    """Plot CVaR comparison"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    confidence_levels = np.linspace(0.90, 0.99, 10)
    hist_cvars = [historical_cvar(returns, cl) for cl in confidence_levels]
    param_cvars = [parametric_cvar(returns, cl) for cl in confidence_levels]
    
    ax.plot(confidence_levels, hist_cvars, 'o-', label='Historical CVaR', linewidth=2, markersize=8, color='darkred')
    ax.plot(confidence_levels, param_cvars, 's-', label='Parametric CVaR', linewidth=2, markersize=8, color='red')
    ax.fill_between(confidence_levels, hist_cvars, param_cvars, alpha=0.3, label='Gap (Model Risk)')
    
    ax.set_xlabel('Confidence Level')
    ax.set_ylabel('CVaR (Expected Shortfall)')
    ax.set_title('CVaR Comparison: Historical vs Parametric')
    ax.legend()
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    plt.close()

def main():
    print("=" * 60)
    print("VaR and CVaR Analysis - BTC Daily Returns")
    print("=" * 60)
    
    # Load data
    df = load_btc_data()
    returns = df['returns']
    
    print(f"\nData period: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Number of observations: {len(returns)}")
    print(f"\nReturn statistics:")
    print(f"  Mean: {returns.mean():.4f}")
    print(f"  Std Dev: {returns.std():.4f}")
    print(f"  Skewness: {stats.skew(returns):.4f}")
    print(f"  Kurtosis: {stats.kurtosis(returns):.4f}")
    print(f"  Min: {returns.min():.4f}")
    print(f"  Max: {returns.max():.4f}")
    
    # Calculate VaR metrics
    print("\n" + "=" * 60)
    print("VaR and CVaR Results (Portfolio: $100,000)")
    print("=" * 60)
    
    results = calculate_var_metrics(returns)
    
    for r in results:
        cl = r['confidence_level']
        print(f"\n{int(cl*100)}% Confidence Level:")
        print(f"  Historical VaR:  {r['historical_var']:.4f} ({r['historical_var']*100:.2f}%)")
        print(f"  Parametric VaR:  {r['parametric_var']:.4f} ({r['parametric_var']*100:.2f}%)")
        print(f"  Monte Carlo VaR: {r['monte_carlo_var']:.4f} ({r['monte_carlo_var']*100:.2f}%)")
        print(f"  Historical CVaR: {r['historical_cvar']:.4f} ({r['historical_cvar']*100:.2f}%)")
        print(f"  Parametric CVaR: {r['parametric_cvar']:.4f} ({r['parametric_cvar']*100:.2f}%)")
        print(f"  Monte Carlo CVaR:{r['monte_carlo_cvar']:.4f} ({r['monte_carlo_cvar']*100:.2f}%)")
        
        if cl == 0.95:
            print(f"\n  Dollar Terms ($100k portfolio):")
            print(f"    VaR 95%:  ${abs(r['historical_var'] * 100000):,.2f}")
            print(f"    CVaR 95%: ${abs(r['historical_cvar'] * 100000):,.2f}")
            print(f"    → Expected loss on worst 5% days: ${abs(r['historical_cvar'] * 100000):,.2f}")
    
    # Generate visualizations
    print("\n" + "=" * 60)
    print("Generating Visualizations")
    print("=" * 60)
    
    plot_var_distribution(returns, results, '/root/.openclaw/workspace/learning/figures/var-cvar-distribution.png')
    plot_cvar_comparison(returns, '/root/.openclaw/workspace/learning/figures/cvar-comparison.png')
    
    # Additional: Rolling volatility and VaR
    fig, ax = plt.subplots(figsize=(14, 6))
    rolling_vol = returns.rolling(window=30).std()
    rolling_var_95 = returns.rolling(window=30).apply(lambda x: historical_var(x, 0.95))
    
    ax2 = ax.twinx()
    rolling_vol.plot(ax=ax, color='blue', linewidth=2, label='30-day Volatility')
    rolling_var_95.plot(ax=ax2, color='red', linewidth=2, label='30-day VaR 95%', alpha=0.7)
    
    ax.set_xlabel('Date')
    ax.set_ylabel('Volatility', color='blue')
    ax2.set_ylabel('VaR 95%', color='red')
    ax.set_title('Rolling Volatility vs Rolling VaR')
    
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    plt.savefig('/root/.openclaw/workspace/learning/figures/rolling-vol-var.png', dpi=150, bbox_inches='tight')
    print("Saved: /root/.openclaw/workspace/learning/figures/rolling-vol-var.png")
    plt.close()
    
    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print("=" * 60)
    
    # Return results for documentation
    return {
        'data_period': f"{df['timestamp'].min()} to {df['timestamp'].max()}",
        'n_observations': len(returns),
        'statistics': {
            'mean': returns.mean(),
            'std': returns.std(),
            'skewness': stats.skew(returns),
            'kurtosis': stats.kurtosis(returns),
            'min': returns.min(),
            'max': returns.max()
        },
        'var_results': results
    }

if __name__ == "__main__":
    main()
