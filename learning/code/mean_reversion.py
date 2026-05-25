"""
Mean Reversion Avancée - Semaine 13
Ornstein-Uhlenbeck, Half-Life, Backtest Gold/Silver Ratio
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize, minimize_scalar
from statsmodels.api import OLS, add_constant
from statsmodels.tsa.stattools import adfuller
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 1. PROCESSUS ORNSTEIN-UHLENBECK
# ============================================================================

def ornstein_uhlenbeck(x0, theta, mu, sigma, n_steps, dt=1, seed=None):
    """
    Simule un processus d'Ornstein-Uhlenbeck.
    
    Parameters:
    - x0: Valeur initiale
    - theta: Vitesse de réversion (mean reversion speed)
    - mu: Moyenne long terme
    - sigma: Volatilité
    - n_steps: Nombre de pas de temps
    - dt: Pas de temps
    - seed: Random seed
    """
    if seed is not None:
        np.random.seed(seed)
    
    X = np.zeros(n_steps)
    X[0] = x0
    
    for t in range(1, n_steps):
        dW = np.random.normal(0, np.sqrt(dt))
        X[t] = X[t-1] + theta * (mu - X[t-1]) * dt + sigma * dW
    
    return X

# ============================================================================
# 2. ESTIMATION DES PARAMÈTRES OU
# ============================================================================

def fit_ou_mle(x, dt=1):
    """
    Estime les paramètres OU par Maximum Likelihood Estimation.
    """
    n = len(x)
    
    def negative_log_likelihood(params):
        theta, mu, sigma = params
        
        if theta <= 0 or sigma <= 0:
            return 1e10
        
        ll = 0
        for t in range(1, n):
            expected = x[t-1] + theta * (mu - x[t-1]) * dt
            variance = sigma**2 * dt
            residual = x[t] - expected
            ll += -0.5 * (np.log(2 * np.pi * variance) + residual**2 / variance)
        
        return -ll
    
    # Initial guess
    x0_init = [0.1, np.mean(x), np.std(x)]
    
    # Optimization
    result = minimize(
        negative_log_likelihood,
        x0_init,
        method='L-BFGS-B',
        bounds=[(0.001, None), (None, None), (0.001, None)]
    )
    
    theta, mu, sigma = result.x
    
    return theta, mu, sigma

def fit_ou_regression(x):
    """
    Estime les paramètres OU par régression linéaire.
    Plus rapide mais moins précis que MLE.
    """
    X = x[:-1]
    y = x[1:]
    
    X_const = add_constant(X)
    model = OLS(y, X_const).fit()
    
    alpha = model.params[0]
    beta = model.params[1]
    
    theta = 1 - beta
    mu = alpha / theta if theta != 0 else np.mean(x)
    sigma = np.std(model.resid)
    
    return theta, mu, sigma

# ============================================================================
# 3. DEMI-VIE DE RÉVERSION
# ============================================================================

def calculate_half_life(theta, dt=1):
    """
    Calcule la demi-vie de réversion.
    half_life = ln(2) / theta
    """
    if theta <= 0:
        return np.inf
    
    half_life = np.log(2) / theta
    return half_life * dt

# ============================================================================
# 4. GÉNÉRATION DE DONNÉES METALS
# ============================================================================

def generate_metals_data(n_days=500, seed=42):
    """
    Génère des prix simulés pour Gold et Silver avec ratio mean-reverting.
    """
    np.random.seed(seed)
    
    n_obs = n_days
    
    # Gold: Random walk avec drift
    gold_returns = np.random.randn(n_obs) * 0.01 + 0.0002
    gold_prices = 2000 * np.cumprod(1 + gold_returns)
    
    # Silver: Plus volatil, corrélé avec Gold
    silver_returns = 0.7 * gold_returns + np.random.randn(n_obs) * 0.015
    silver_prices = 25 * np.cumprod(1 + silver_returns)
    
    # Ajuster pour que le ratio soit mean-reverting
    ratio_target = 80  # Ratio moyen historique
    ratio_current = gold_prices / silver_prices
    
    # Adjust silver pour mean-reverting ratio
    adjustment = np.cumsum(0.001 * (ratio_target - ratio_current))
    silver_prices *= np.exp(adjustment - adjustment[0])
    
    dates = pd.date_range(start='2025-01-01', periods=n_obs, freq='D')
    
    df = pd.DataFrame({
        'gold': gold_prices,
        'silver': silver_prices
    }, index=dates)
    
    return df

# ============================================================================
# 5. SIGNALS DE TRADING
# ============================================================================

def generate_mean_reversion_signals(z_score, entry_threshold=2.0, exit_threshold=0.5):
    """
    Génère des signals de trading mean-reversion.
    """
    positions = np.zeros(len(z_score))
    in_position = 0
    
    for i, z in enumerate(z_score):
        if in_position == 0:
            if z > entry_threshold:
                positions[i:] = -1
                in_position = -1
            elif z < -entry_threshold:
                positions[i:] = 1
                in_position = 1
        else:
            if abs(z) < exit_threshold:
                positions[i:] = 0
                in_position = 0
    
    return positions

# ============================================================================
# 6. BACKTEST
# ============================================================================

def backtest_mean_reversion(prices_gold, prices_silver, entry_thresh=2.0, exit_thresh=0.5):
    """
    Backtest complet d'une stratégie mean-reversion Gold/Silver.
    """
    
    # Ratio et z-score
    ratio = prices_gold / prices_silver
    rolling_mean = ratio.rolling(252).mean()
    rolling_std = ratio.rolling(252).std()
    z_score = (ratio - rolling_mean) / rolling_std
    
    # Positions
    positions = np.zeros(len(prices_gold))
    in_position = 0
    
    for i in range(1, len(z_score)):
        z = z_score.iloc[i]
        
        if in_position == 0:
            if z > entry_thresh:
                positions[i:] = -1
                in_position = -1
            elif z < -entry_thresh:
                positions[i:] = 1
                in_position = 1
        else:
            if abs(z) < exit_thresh:
                positions[i:] = 0
                in_position = 0
    
    # Returns
    returns_gold = prices_gold.pct_change()
    returns_silver = prices_silver.pct_change()
    
    # Return du spread
    spread_returns = returns_gold - returns_silver
    strategy_returns = positions[:-1] * spread_returns[1:]
    
    # Métriques
    cumulative = (1 + pd.Series(strategy_returns)).cumprod()
    total_return = cumulative.iloc[-1] - 1 if len(cumulative) > 0 else 0
    
    if np.std(strategy_returns) > 0:
        sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
    else:
        sharpe = 0
    
    max_dd = (cumulative / cumulative.cummax() - 1).min() if len(cumulative) > 0 else 0
    
    # Trade statistics
    winning_trades = strategy_returns[strategy_returns > 0]
    losing_trades = strategy_returns[strategy_returns < 0]
    
    win_rate = len(winning_trades) / len(strategy_returns) if len(strategy_returns) > 0 else 0
    avg_win = winning_trades.mean() if len(winning_trades) > 0 else 0
    avg_loss = abs(losing_trades.mean()) if len(losing_trades) > 0 else 0
    
    # Compter les trades
    position_changes = np.diff(positions != 0)
    n_trades = int(np.sum(position_changes != 0) // 2)
    
    return {
        'total_return': total_return,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'n_trades': n_trades,
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'cumulative': cumulative,
        'positions': positions,
        'z_score': z_score,
        'ratio': ratio,
        'strategy_returns': strategy_returns
    }

def optimize_thresholds(prices_gold, prices_silver, thresholds_range=(1.0, 3.0)):
    """
    Optimise les thresholds pour maximiser le Sharpe ratio.
    """
    
    def sharpe_objective(threshold):
        entry_thresh = threshold
        exit_thresh = threshold * 0.25
        
        result = backtest_mean_reversion(
            prices_gold, prices_silver,
            entry_thresh=entry_thresh,
            exit_thresh=exit_thresh
        )
        
        return -result['sharpe']  # Négatif car on minimise
    
    result = minimize_scalar(
        sharpe_objective,
        bounds=thresholds_range,
        method='bounded'
    )
    
    optimal_threshold = result.x
    optimal_sharpe = -result.fun
    
    return optimal_threshold, optimal_sharpe

# ============================================================================
# 7. VISUALISATION
# ============================================================================

def plot_mean_reversion_analysis(df, ou_params, backtest_result):
    """Visualise l'analyse mean-reversion complète"""
    
    fig, axes = plt.subplots(3, 2, figsize=(16, 12))
    
    # 1. Prix Gold et Silver
    ax1 = axes[0, 0]
    ax1.plot(df.index, df['gold'], label='Gold', linewidth=1, color='gold')
    ax1.plot(df.index, df['silver'], label='Silver', linewidth=1, color='silver')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Price')
    ax1.set_title('Gold & Silver Prices')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Ratio Gold/Silver
    ax2 = axes[0, 1]
    ax2.plot(df.index, backtest_result['ratio'], linewidth=1, color='purple')
    ax2.axhline(backtest_result['ratio'].mean(), color='red', linestyle='--', 
               label=f'Moyenne: {backtest_result["ratio"].mean():.1f}')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Ratio')
    ax2.set_title('Gold/Silver Ratio')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Z-Score avec thresholds
    ax3 = axes[1, 0]
    ax3.plot(df.index, backtest_result['z_score'], linewidth=0.5, label='Z-Score')
    ax3.axhline(2.0, color='red', linestyle='--', alpha=0.7, label='Entry (+2σ)')
    ax3.axhline(-2.0, color='red', linestyle='--', alpha=0.7)
    ax3.axhline(0.5, color='green', linestyle=':', alpha=0.7, label='Exit (±0.5σ)')
    ax3.axhline(-0.5, color='green', linestyle=':', alpha=0.7)
    ax3.fill_between(df.index, backtest_result['z_score'], 0, 
                    where=(backtest_result['positions'] == 1), 
                    alpha=0.3, color='green', label='Long Ratio')
    fill_neg = np.where(backtest_result['positions'] == -1, backtest_result['z_score'], 0)
    ax3.fill_between(df.index, fill_neg, 0, 
                    alpha=0.3, color='red', label='Short Ratio')
    ax3.set_xlabel('Date')
    ax3.set_ylabel('Z-Score')
    ax3.set_title('Z-Score & Positions')
    ax3.legend(loc='upper right', fontsize=8)
    ax3.grid(True, alpha=0.3)
    
    # 4. Cumulative returns
    ax4 = axes[1, 1]
    ax4.plot(backtest_result['cumulative'].index, backtest_result['cumulative'], 
            linewidth=1.5, color='blue', label='Strategy')
    ax4.axhline(1.0, color='black', linestyle='-', alpha=0.3)
    ax4.set_xlabel('Date')
    ax4.set_ylabel('Cumulative Return')
    ax4.set_title(f'Strategy Performance (Total: {backtest_result["total_return"]:.1%})')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 5. OU Process simulation
    ax5 = axes[2, 0]
    theta, mu, sigma = ou_params
    half_life = calculate_half_life(theta)
    ou_sim = ornstein_uhlenbeck(x0=mu, theta=theta, mu=mu, sigma=sigma, 
                                n_steps=500, dt=1, seed=42)
    ax5.plot(ou_sim, linewidth=0.5, color='orange')
    ax5.axhline(mu, color='red', linestyle='--', label=f'Mean (μ={mu:.3f})')
    ax5.set_xlabel('Time Steps')
    ax5.set_ylabel('Value')
    ax5.set_title(f'Simulated OU Process (θ={theta:.3f}, Half-Life={half_life:.1f})')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # 6. Returns distribution
    ax6 = axes[2, 1]
    ax6.hist(backtest_result['strategy_returns'], bins=50, alpha=0.7, 
            color='steelblue', edgecolor='black')
    ax6.axvline(0, color='red', linestyle='--', linewidth=2)
    ax6.set_xlabel('Return')
    ax6.set_ylabel('Count')
    ax6.set_title(f'Strategy Returns Distribution (Sharpe={backtest_result["sharpe"]:.2f})')
    ax6.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('/root/.openclaw/workspace/learning/code/mean_reversion_output.png', dpi=150)
    print(f"      → Visualisation sauvegardée: mean_reversion_output.png")

# ============================================================================
# 8. PIPELINE COMPLET
# ============================================================================

def run_mean_reversion_analysis():
    """Exécute l'analyse mean-reversion complète"""
    
    print("=" * 70)
    print("MEAN REVERSION AVANCÉE - SEMAINE 13")
    print("=" * 70)
    
    # Données
    print("\n[INIT] Génération des données Metals...")
    df = generate_metals_data(n_days=500)
    print(f"      → {len(df)} observations générées")
    
    # Ratio et test ADF
    print("\n[1/4] Test de stationnarité (ADF)...")
    ratio = df['gold'] / df['silver']
    adf_result = adfuller(ratio.dropna())
    print(f"      → ADF Statistic: {adf_result[0]:.4f}")
    print(f"      → p-value: {adf_result[1]:.4f}")
    
    if adf_result[1] < 0.05:
        print(f"      ✅ Ratio est stationnaire (mean-reverting)")
    else:
        print(f"      ⚠️  Ratio non-stationnaire (p > 0.05)")
    
    # Fit OU
    print("\n[2/4] Estimation paramètres OU (MLE)...")
    ratio_returns = ratio.pct_change().dropna().values
    theta, mu, sigma = fit_ou_mle(ratio_returns)
    half_life = calculate_half_life(theta, dt=1)
    
    print(f"      → θ (theta): {theta:.6f}")
    print(f"      → μ (mu): {mu:.6f}")
    print(f"      → σ (sigma): {sigma:.6f}")
    print(f"      → Half-life: {half_life:.1f} jours")
    
    ou_params = (theta, mu, sigma)
    
    # Backtest
    print("\n[3/4] Backtest stratégie mean-reversion...")
    backtest_result = backtest_mean_reversion(
        df['gold'], df['silver'],
        entry_thresh=2.0,
        exit_thresh=0.5
    )
    
    print(f"\n      Performance:")
    print(f"         → Total Return: {backtest_result['total_return']:.1%}")
    print(f"         → Sharpe Ratio: {backtest_result['sharpe']:.2f}")
    print(f"         → Max Drawdown: {backtest_result['max_drawdown']:.1%}")
    print(f"         → N Trades: {backtest_result['n_trades']}")
    print(f"         → Win Rate: {backtest_result['win_rate']:.1%}")
    print(f"         → Avg Win: {backtest_result['avg_win']:.2%}")
    print(f"         → Avg Loss: {backtest_result['avg_loss']:.2%}")
    
    # Optimisation
    print("\n[4/4] Optimisation des thresholds...")
    optimal_thresh, optimal_sharpe = optimize_thresholds(df['gold'], df['silver'])
    print(f"      → Optimal Entry Threshold: {optimal_thresh:.2f}σ")
    print(f"      → Optimal Sharpe: {optimal_sharpe:.2f}")
    
    # Visualisation
    print("\n" + "=" * 70)
    print("GÉNÉRATION DES VISUALISATIONS...")
    print("=" * 70)
    plot_mean_reversion_analysis(df, ou_params, backtest_result)
    
    print("\n" + "=" * 70)
    print("✅ MEAN REVERSION COMPLETE")
    print("=" * 70)
    
    return df, ou_params, backtest_result

if __name__ == "__main__":
    df, ou_params, backtest_result = run_mean_reversion_analysis()
