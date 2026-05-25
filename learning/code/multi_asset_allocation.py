#!/usr/bin/env python3
"""
Multi-Asset Allocation Analysis - Crypto Portfolio
Phase 2 - Intégration Saiyan
Semaine 21: Multi-Asset Allocation (BTC/ETH/SOL)

Allocates capital using Risk Parity, Equal Weight, and Kelly approaches.
"""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)

def fetch_crypto_data():
    """Fetch BTC, ETH, SOL data from CSV or generate if not available"""
    import os
    
    # Try to load existing data
    data_files = {
        'BTC': '/root/.openclaw/workspace/learning/data/btc_1d.csv',
        'ETH': '/root/.openclaw/workspace/learning/data/eth_1d.csv',
        'SOL': '/root/.openclaw/workspace/learning/data/sol_1d.csv'
    }
    
    returns_data = {}
    
    for symbol, path in data_files.items():
        if os.path.exists(path):
            df = pd.read_csv(path, parse_dates=['timestamp'])
            df = df.sort_values('timestamp')
            df['returns'] = df['close'].pct_change()
            df = df.dropna()
            returns_data[symbol] = df['returns']
        else:
            print(f"Warning: {path} not found. Generating synthetic data for {symbol}.")
            # Generate synthetic data with realistic crypto statistics
            np.random.seed(42)
            n_days = 720  # ~2 years
            if symbol == 'BTC':
                mu, sigma = 0.0004, 0.024  # Daily return, vol
            elif symbol == 'ETH':
                mu, sigma = 0.0005, 0.032
            else:  # SOL
                mu, sigma = 0.0008, 0.045
            
            returns = np.random.normal(mu, sigma, n_days)
            # Add some fat tails
            returns[np.random.random(n_days) < 0.02] *= 3  # 2% extreme events
            returns_data[symbol] = pd.Series(returns, name=symbol)
    
    # Combine into DataFrame
    returns_df = pd.DataFrame(returns_data)
    returns_df = returns_df.dropna()
    
    return returns_df

def calculate_portfolio_metrics(returns, weights, risk_free_rate=0.02):
    """Calculate portfolio metrics for given weights"""
    portfolio_returns = (returns * weights).sum(axis=1)
    
    # Annualized metrics (252 trading days)
    ann_return = portfolio_returns.mean() * 252
    ann_vol = portfolio_returns.std() * np.sqrt(252)
    sharpe = (ann_return - risk_free_rate) / ann_vol if ann_vol > 0 else 0
    
    # Drawdown
    cumulative = (1 + portfolio_returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # VaR and CVaR
    var_95 = np.percentile(portfolio_returns, 5)
    cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
    
    return {
        'annual_return': ann_return,
        'annual_vol': ann_vol,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown,
        'var_95': var_95,
        'cvar_95': cvar_95,
        'total_return': cumulative.iloc[-1] - 1
    }

def risk_parity_weights(returns, target_risk_contrib=None):
    """
    Calculate Risk Parity weights that equalize risk contribution.
    Simplified version without cvxpy dependency.
    """
    n_assets = returns.shape[1]
    cov_matrix = returns.cov().values
    
    if target_risk_contrib is None:
        target_risk_contrib = np.ones(n_assets) / n_assets
    
    # Initialize with inverse volatility
    vols = np.sqrt(np.diag(cov_matrix))
    weights = 1 / vols
    weights = weights / weights.sum()
    
    # Iterative refinement to equalize risk contributions
    for _ in range(100):
        portfolio_var = weights @ cov_matrix @ weights
        portfolio_vol = np.sqrt(portfolio_var)
        marginal_risk = cov_matrix @ weights
        risk_contrib = weights * marginal_risk / portfolio_vol
        risk_contrib_pct = risk_contrib / portfolio_vol
        
        # Adjust weights to equalize risk contributions
        for i in range(n_assets):
            if risk_contrib_pct[i] > target_risk_contrib[i]:
                weights[i] *= 0.98  # Reduce weight if contributing too much risk
            elif risk_contrib_pct[i] < target_risk_contrib[i]:
                weights[i] *= 1.02  # Increase weight if contributing too little risk
        
        # Renormalize
        weights = weights / weights.sum()
        weights = np.maximum(weights, 0.01)  # Minimum 1% weight
        weights = weights / weights.sum()
    
    return weights

def kelly_weights(returns, max_position=0.40, fraction=0.5):
    """
    Calculate Fractional Kelly weights.
    """
    n_assets = returns.shape[1]
    mu = returns.mean().values * 252  # Annualized
    cov_matrix = returns.cov().values * 252
    
    # Simplified Kelly: f* = μ / σ² for each asset
    kelly_fractions = mu / np.diag(cov_matrix)
    
    # Apply fractional Kelly (Half-Kelly = 0.5)
    kelly_fractions = fraction * kelly_fractions
    
    # Apply constraints
    kelly_fractions = np.clip(kelly_fractions, 0, max_position)
    
    # Normalize to sum to 1
    if kelly_fractions.sum() > 0:
        kelly_fractions = kelly_fractions / kelly_fractions.sum()
    else:
        kelly_fractions = np.ones(n_assets) / n_assets
    
    return kelly_fractions

def rolling_allocation(returns, window=60, method='risk_parity'):
    """
    Calculate rolling allocation weights to show evolution over time.
    """
    n = len(returns)
    weights_history = []
    dates = []
    
    for i in range(window, n, 5):  # Every 5 days for efficiency
        returns_window = returns.iloc[i-window:i]
        
        if method == 'risk_parity':
            w = risk_parity_weights(returns_window)
        elif method == 'kelly':
            w = kelly_weights(returns_window)
        else:  # equal weight
            w = np.ones(returns.shape[1]) / returns.shape[1]
        
        weights_history.append(w)
        dates.append(returns.index[i])
    
    return pd.DataFrame(weights_history, index=dates, columns=returns.columns)

def compare_allocation_strategies(returns):
    """Compare Equal Weight, Risk Parity, and Kelly allocations"""
    
    strategies = {
        'Equal Weight': np.ones(returns.shape[1]) / returns.shape[1],
        'Risk Parity': risk_parity_weights(returns),
        'Half-Kelly': kelly_weights(returns, fraction=0.5)
    }
    
    results = []
    
    for name, weights in strategies.items():
        metrics = calculate_portfolio_metrics(returns, weights)
        metrics['strategy'] = name
        metrics['weights'] = weights
        results.append(metrics)
    
    return results

def plot_allocation_comparison(returns, results, save_path=None):
    """Plot allocation strategy comparison"""
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    strategies = [r['strategy'] for r in results]
    
    # 1. Weights comparison (bar chart)
    ax1 = axes[0, 0]
    weights_matrix = np.array([r['weights'] for r in results])
    x = np.arange(len(returns.columns))
    width = 0.25
    
    for i, strategy in enumerate(strategies):
        ax1.bar(x + i*width, weights_matrix[i], width, label=strategy)
    
    ax1.set_xlabel('Asset')
    ax1.set_ylabel('Weight')
    ax1.set_title('Allocation Weights Comparison')
    ax1.set_xticks(x + width)
    ax1.set_xticklabels(returns.columns)
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # 2. Risk contributions (Risk Parity should be equal)
    ax2 = axes[0, 1]
    cov_matrix = returns.cov().values
    
    for i, r in enumerate(results):
        weights = r['weights']
        portfolio_var = weights @ cov_matrix @ weights
        portfolio_vol = np.sqrt(portfolio_var)
        marginal_risk = cov_matrix @ weights
        risk_contrib = weights * marginal_risk / portfolio_vol
        risk_contrib_pct = risk_contrib / portfolio_vol
        
        ax2.bar(x + i*width, risk_contrib_pct, width, label=r['strategy'])
    
    ax2.axhline(1/len(returns.columns), color='red', linestyle='--', alpha=0.5, 
                label='Target (Equal)')
    ax2.set_xlabel('Asset')
    ax2.set_ylabel('Risk Contribution (%)')
    ax2.set_title('Risk Contributions by Strategy')
    ax2.set_xticks(x + width)
    ax2.set_xticklabels(returns.columns)
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)
    
    # 3. Performance metrics (Sharpe, Vol, Return)
    ax3 = axes[0, 2]
    metrics_names = ['Sharpe Ratio', 'Ann. Vol (%)', 'Ann. Return (%)']
    metrics_values = [
        [r['sharpe_ratio'] for r in results],
        [r['annual_vol'] * 100 for r in results],
        [r['annual_return'] * 100 for r in results]
    ]
    
    x = np.arange(len(strategies))
    width = 0.2
    
    for i, (name, values) in enumerate(zip(metrics_names, metrics_values)):
        ax3.bar(x + i*width, values, width, label=name)
    
    ax3.set_xlabel('Strategy')
    ax3.set_ylabel('Value')
    ax3.set_title('Performance Metrics Comparison')
    ax3.set_xticks(x + width)
    ax3.set_xticklabels(strategies)
    ax3.legend()
    ax3.grid(axis='y', alpha=0.3)
    
    # 4. Cumulative returns
    ax4 = axes[1, 0]
    for r in results:
        weights = r['weights']
        portfolio_returns = (returns * weights).sum(axis=1)
        cumulative = (1 + portfolio_returns).cumprod()
        ax4.plot(cumulative.index, cumulative.values, label=r['strategy'], linewidth=2)
    
    ax4.set_xlabel('Date')
    ax4.set_ylabel('Cumulative Return')
    ax4.set_title('Cumulative Returns by Strategy')
    ax4.legend()
    ax4.grid(alpha=0.3)
    
    # 5. Drawdown comparison
    ax5 = axes[1, 1]
    for r in results:
        weights = r['weights']
        portfolio_returns = (returns * weights).sum(axis=1)
        cumulative = (1 + portfolio_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        ax5.plot(drawdown.index, drawdown.values * 100, label=r['strategy'], linewidth=2)
    
    ax5.set_xlabel('Date')
    ax5.set_ylabel('Drawdown (%)')
    ax5.set_title('Drawdown Comparison')
    ax5.legend()
    ax5.grid(alpha=0.3)
    
    # 6. Rolling weights evolution (Risk Parity)
    ax6 = axes[1, 2]
    rolling_rp = rolling_allocation(returns, window=60, method='risk_parity')
    
    for col in rolling_rp.columns:
        ax6.plot(rolling_rp.index, rolling_rp[col] * 100, label=col, linewidth=2)
    
    ax6.set_xlabel('Date')
    ax6.set_ylabel('Weight (%)')
    ax6.set_title('Risk Parity Weights Evolution (Rolling 60j)')
    ax6.legend()
    ax6.grid(alpha=0.3)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    plt.close()

def plot_risk_return_scatter(returns, save_path=None):
    """Plot risk-return scatter for individual assets and portfolios"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Individual assets
    for col in returns.columns:
        ann_ret = returns[col].mean() * 252
        ann_vol = returns[col].std() * np.sqrt(252)
        ax.scatter(ann_vol * 100, ann_ret * 100, s=200, alpha=0.6, label=f'{col} (asset)')
        ax.annotate(col, (ann_vol * 100, ann_ret * 100), fontsize=10, 
                   xytext=(5, 5), textcoords='offset points')
    
    # Portfolio strategies
    results = compare_allocation_strategies(returns)
    for r in results:
        ax.scatter(r['annual_vol'] * 100, r['annual_return'] * 100, 
                  s=300, marker='*', label=f"{r['strategy']} (portfolio)", 
                  edgecolors='black', linewidths=2)
    
    ax.set_xlabel('Annualized Volatility (%)')
    ax.set_ylabel('Annualized Return (%)')
    ax.set_title('Risk-Return Profile: Assets vs Portfolio Strategies')
    ax.legend()
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    plt.close()

def main():
    print("=" * 70)
    print("Multi-Asset Allocation Analysis - Crypto Portfolio")
    print("Phase 2 - Intégration Saiyan")
    print("=" * 70)
    
    # Load data
    returns = fetch_crypto_data()
    
    print(f"\nData period: {returns.index.min()} to {returns.index.max()}")
    print(f"Number of observations: {len(returns)}")
    print(f"\nAssets: {', '.join(returns.columns)}")
    
    # Individual asset statistics
    print("\n" + "=" * 70)
    print("INDIVIDUAL ASSET STATISTICS")
    print("=" * 70)
    
    for col in returns.columns:
        ann_ret = returns[col].mean() * 252
        ann_vol = returns[col].std() * np.sqrt(252)
        sharpe = ann_ret / ann_vol if ann_vol > 0 else 0
        var_95 = np.percentile(returns[col], 5)
        print(f"\n{col}:")
        print(f"   Annual Return: {ann_ret*100:.1f}%")
        print(f"   Annual Volatility: {ann_vol*100:.1f}%")
        print(f"   Sharpe Ratio: {sharpe:.2f}")
        print(f"   VaR 95% (daily): {var_95*100:.2f}%")
    
    # Compare allocation strategies
    print("\n" + "=" * 70)
    print("ALLOCATION STRATEGY COMPARISON")
    print("=" * 70)
    
    results = compare_allocation_strategies(returns)
    
    for r in results:
        print(f"\n{r['strategy']}:")
        print(f"   Weights: ", end="")
        for asset, weight in zip(returns.columns, r['weights']):
            if weight > 0.01:
                print(f"{asset} {weight*100:.1f}% ", end="")
        print()
        print(f"   Annual Return: {r['annual_return']*100:.1f}%")
        print(f"   Annual Volatility: {r['annual_vol']*100:.1f}%")
        print(f"   Sharpe Ratio: {r['sharpe_ratio']:.2f}")
        print(f"   Max Drawdown: {r['max_drawdown']*100:.1f}%")
        print(f"   Total Return: {r['total_return']*100:.1f}%")
        print(f"   VaR 95% (daily): {r['var_95']*100:.2f}%")
        print(f"   CVaR 95% (daily): {r['cvar_95']*100:.2f}%")
    
    # Best strategy
    best_sharpe = max(results, key=lambda x: x['sharpe_ratio'])
    print(f"\n🏆 Best Risk-Adjusted: {best_sharpe['strategy']} (Sharpe: {best_sharpe['sharpe_ratio']:.2f})")
    
    # Generate visualizations
    print("\n" + "=" * 70)
    print("GENERATING VISUALIZATIONS")
    print("=" * 70)
    
    plot_allocation_comparison(returns, results, 
                               '/root/.openclaw/workspace/learning/figures/multi-asset-allocation-comparison.png')
    plot_risk_return_scatter(returns, 
                             '/root/.openclaw/workspace/learning/figures/multi-asset-risk-return.png')
    
    # Correlation matrix
    fig, ax = plt.subplots(figsize=(10, 8))
    corr_matrix = returns.corr()
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0, 
                ax=ax, square=True, linewidths=1)
    ax.set_title('Asset Correlation Matrix')
    plt.tight_layout()
    plt.savefig('/root/.openclaw/workspace/learning/figures/multi-asset-correlation.png', 
                dpi=150, bbox_inches='tight')
    print("Saved: /root/.openclaw/workspace/learning/figures/multi-asset-correlation.png")
    plt.close()
    
    print("\n" + "=" * 70)
    print("Multi-Asset Allocation Analysis Complete!")
    print("=" * 70)
    
    return results

if __name__ == "__main__":
    main()
