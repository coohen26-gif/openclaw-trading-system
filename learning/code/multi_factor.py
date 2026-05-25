"""
Multi-Factor Models - Semaine 16
Construction de facteurs, régression factorielle, factor timing, attribution
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 1. GÉNÉRATION DE DONNÉES
# ============================================================================

def generate_crypto_universe(n_coins=50, n_days=500, seed=42):
    """
    Génère un univers de crypto avec différentes caractéristiques.
    """
    np.random.seed(seed)
    
    coins = [f'COIN_{i:02d}' for i in range(n_coins)]
    dates = pd.date_range(start='2025-01-01', periods=n_days, freq='D')
    
    coin_data = {}
    
    for i, coin in enumerate(coins):
        # Caractéristiques différentes par coin
        market_cap = 1e10 * np.exp(-i * 0.1)  # Décroissant
        base_vol = 0.02 + i * 0.001  # Small caps plus volatiles
        momentum_bias = 0.0005 * (n_coins - i)  # Large caps ont plus de momentum
        
        # Prix
        returns = np.random.randn(n_days) * base_vol
        returns += momentum_bias  # Momentum drift
        returns += 0.0001 * np.arange(n_days)  # Trend général
        
        prices = 100 * np.cumprod(1 + returns)
        
        # Volume (corrélé avec market cap)
        volume = market_cap * 0.01 * np.exp(np.random.randn(n_days) * 0.5)
        
        coin_data[coin] = pd.DataFrame({
            'close': prices,
            'volume': volume,
            'market_cap': market_cap
        }, index=dates)
    
    return coin_data, coins

# ============================================================================
# 2. CONSTRUCTION DES FACTEURS
# ============================================================================

def build_momentum_factor(coin_data, coins, lookback=30, rebalance_freq=7):
    """Facteur Momentum: Winners minus Losers"""
    
    dates = list(coin_data[coins[0]].index)
    factor_returns = []
    
    for i in range(lookback, len(dates), rebalance_freq):
        momentums = {}
        for coin in coins:
            prices = coin_data[coin]['close'].iloc[:i]
            mom = (prices.iloc[-1] / prices.iloc[-lookback] - 1)
            momentums[coin] = mom
        
        sorted_coins = sorted(momentums.items(), key=lambda x: x[1], reverse=True)
        n_quintile = len(coins) // 5
        winners = [c[0] for c in sorted_coins[:n_quintile]]
        losers = [c[0] for c in sorted_coins[-n_quintile:]]
        
        if i + rebalance_freq <= len(dates):
            winner_return = np.mean([
                coin_data[c]['close'].pct_change().iloc[i:i+rebalance_freq].sum()
                for c in winners if not np.isnan(coin_data[c]['close'].pct_change().iloc[i:i+rebalance_freq].sum())
            ])
            loser_return = np.mean([
                coin_data[c]['close'].pct_change().iloc[i:i+rebalance_freq].sum()
                for c in losers if not np.isnan(coin_data[c]['close'].pct_change().iloc[i:i+rebalance_freq].sum())
            ])
            
            factor_returns.append({
                'date': dates[i],
                'return': winner_return - loser_return
            })
    
    return pd.DataFrame(factor_returns).set_index('date')

def build_size_factor(coin_data, coins, rebalance_freq=30):
    """Facteur Size: Small caps minus Large caps"""
    
    dates = list(coin_data[coins[0]].index)
    factor_returns = []
    
    for i in range(0, len(dates), rebalance_freq):
        market_caps = {coin: coin_data[coin]['market_cap'].iloc[0] for coin in coins}
        sorted_coins = sorted(market_caps.items(), key=lambda x: x[1], reverse=True)
        
        n_tertile = len(coins) // 3
        large_caps = [c[0] for c in sorted_coins[:n_tertile]]
        small_caps = [c[0] for c in sorted_coins[-n_tertile:]]
        
        if i + rebalance_freq <= len(dates):
            large_return = np.mean([
                coin_data[c]['close'].pct_change().iloc[i:i+rebalance_freq].sum()
                for c in large_caps
            ])
            small_return = np.mean([
                coin_data[c]['close'].pct_change().iloc[i:i+rebalance_freq].sum()
                for c in small_caps
            ])
            
            factor_returns.append({
                'date': dates[i],
                'return': small_return - large_return
            })
    
    return pd.DataFrame(factor_returns).set_index('date')

def build_volatility_factor(coin_data, coins, lookback=30, rebalance_freq=7):
    """Facteur Volatility: Low vol minus High vol"""
    
    dates = list(coin_data[coins[0]].index)
    factor_returns = []
    
    for i in range(lookback, len(dates), rebalance_freq):
        volatilities = {}
        for coin in coins:
            returns = coin_data[coin]['close'].pct_change().iloc[:i]
            vol = returns.rolling(lookback).std().iloc[-1] * np.sqrt(365)
            volatilities[coin] = vol
        
        sorted_coins = sorted(volatilities.items(), key=lambda x: x[1])
        n_quintile = len(coins) // 5
        low_vol = [c[0] for c in sorted_coins[:n_quintile]]
        high_vol = [c[0] for c in sorted_coins[-n_quintile:]]
        
        if i + rebalance_freq <= len(dates):
            low_vol_return = np.mean([
                coin_data[c]['close'].pct_change().iloc[i:i+rebalance_freq].sum()
                for c in low_vol
            ])
            high_vol_return = np.mean([
                coin_data[c]['close'].pct_change().iloc[i:i+rebalance_freq].sum()
                for c in high_vol
            ])
            
            factor_returns.append({
                'date': dates[i],
                'return': low_vol_return - high_vol_return
            })
    
    return pd.DataFrame(factor_returns).set_index('date')

# ============================================================================
# 3. RÉGRESSION FACTORIELLE
# ============================================================================

def estimate_factor_loadings(asset_returns, factor_returns_dict):
    """Estime les factor loadings par régression"""
    
    df = pd.DataFrame({'asset': asset_returns})
    for name, factor in factor_returns_dict.items():
        df[name] = factor['return'] if isinstance(factor, pd.DataFrame) else factor
    df = df.dropna()
    
    if len(df) < 10:
        return None
    
    X = df[list(factor_returns_dict.keys())]
    X = sm.add_constant(X)
    y = df['asset']
    
    try:
        model = sm.OLS(y, X).fit()
        
        return {
            'alpha': model.params['const'],
            'alpha_tstat': model.tvalues['const'],
            'alpha_pvalue': model.pvalues['const'],
            'betas': {k: model.params[k] for k in factor_returns_dict.keys()},
            'beta_tstats': {k: model.tvalues[k] for k in factor_returns_dict.keys()},
            'r_squared': model.rsquared,
            'adj_r_squared': model.rsquared_adj
        }
    except:
        return None

# ============================================================================
# 4. FACTOR TIMING
# ============================================================================

def analyze_factor_timing(factor_returns_dict, regime_labels):
    """Analyse la performance des facteurs par régime"""
    
    df = pd.DataFrame({name: factor['return'] if isinstance(factor, pd.DataFrame) else factor 
                       for name, factor in factor_returns_dict.items()})
    df = df.dropna()
    
    if len(df) != len(regime_labels):
        min_len = min(len(df), len(regime_labels))
        df = df.iloc[:min_len]
        regime_labels = regime_labels[:min_len]
    
    df['regime'] = regime_labels[:len(df)]
    
    performance_by_regime = df.groupby('regime')[list(factor_returns_dict.keys())].mean()
    
    return performance_by_regime

# ============================================================================
# 5. ATTRIBUTION DE PERFORMANCE
# ============================================================================

def factor_attribution(portfolio_returns, factor_returns_dict, factor_loadings):
    """Décompose la performance par facteur"""
    
    if factor_loadings is None:
        return None
    
    contributions = {}
    for factor, beta in factor_loadings['betas'].items():
        factor_ret = factor_returns_dict[factor]
        factor_series = factor_ret['return'] if isinstance(factor_ret, pd.DataFrame) else factor_ret
        factor_contrib = beta * factor_series.sum()
        contributions[factor] = factor_contrib
    
    total_return = portfolio_returns.sum()
    factor_contribution_total = sum(contributions.values())
    alpha = total_return - factor_contribution_total
    
    return {
        'alpha': alpha,
        'alpha_pct': alpha / total_return * 100 if total_return != 0 else 0,
        'factors': contributions,
        'total_factor_contrib': factor_contribution_total,
        'total_return': total_return
    }

# ============================================================================
# 6. VISUALISATION
# ============================================================================

def plot_factor_analysis(factor_returns_dict, loadings, timing_results, attribution):
    """Visualise l'analyse factorielle complète"""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Factor returns over time
    ax1 = axes[0, 0]
    for name, factor in factor_returns_dict.items():
        factor_series = factor['return'] if isinstance(factor, pd.DataFrame) else pd.Series(factor)
        ax1.plot(factor_series.index, factor_series.cumsum(), label=name, linewidth=1.5, alpha=0.8)
    
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Cumulative Return')
    ax1.set_title('Factor Returns (Cumulative)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Factor loadings (betas)
    ax2 = axes[0, 1]
    if loadings:
        factors = list(loadings['betas'].keys())
        betas = [loadings['betas'][f] for f in factors]
        colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(factors)))
        
        bars = ax2.bar(factors, betas, color=colors, alpha=0.7)
        ax2.axhline(0, color='black', linestyle='-', linewidth=0.5)
        ax2.set_ylabel('Beta (Factor Loading)')
        ax2.set_title('Factor Loadings')
        ax2.tick_params(axis='x', rotation=45)
        
        for bar, beta in zip(bars, betas):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{beta:.2f}', ha='center', va='bottom', fontsize=9)
    
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Factor timing by regime
    ax3 = axes[1, 0]
    if timing_results is not None and len(timing_results) > 0:
        timing_df = timing_results.T
        timing_df.plot(kind='bar', ax=ax3, alpha=0.8)
        ax3.set_xlabel('Factor')
        ax3.set_ylabel('Mean Return by Regime')
        ax3.set_title('Factor Performance by Regime')
        ax3.legend(title='Regime', loc='upper right')
        ax3.tick_params(axis='x', rotation=45)
    
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. Performance attribution
    ax4 = axes[1, 1]
    if attribution:
        labels = ['Alpha'] + list(attribution['factors'].keys())
        values = [attribution['alpha']] + list(attribution['factors'].values())
        colors = ['gold'] + ['steelblue'] * (len(values) - 1)
        
        wedges, texts, autotexts = ax4.pie(values, labels=labels, autopct='%1.1f%%', 
                                           colors=colors, startangle=90)
        ax4.set_title('Performance Attribution')
    
    ax4.grid(False)
    
    plt.tight_layout()
    plt.savefig('/root/.openclaw/workspace/learning/code/multi_factor_output.png', dpi=150)
    print(f"      → Visualisation sauvegardée: multi_factor_output.png")

# ============================================================================
# 7. PIPELINE COMPLET
# ============================================================================

def run_multi_factor_analysis():
    """Exécute l'analyse multi-factor complète"""
    
    print("=" * 70)
    print("MULTI-FACTOR MODELS - SEMAINE 16")
    print("=" * 70)
    
    # Données
    print("\n[INIT] Génération de l'univers crypto...")
    coin_data, coins = generate_crypto_universe(n_coins=50, n_days=500)
    print(f"      → {len(coins)} coins, {len(list(coin_data.values())[0])} jours")
    
    # Construction des facteurs
    print("\n[1/4] Construction des facteurs...")
    
    print("      → Facteur Momentum...")
    mom_factor = build_momentum_factor(coin_data, coins, lookback=30, rebalance_freq=7)
    
    print("      → Facteur Size...")
    size_factor = build_size_factor(coin_data, coins, rebalance_freq=30)
    
    print("      → Facteur Volatility...")
    vol_factor = build_volatility_factor(coin_data, coins, lookback=30, rebalance_freq=7)
    
    # Market factor (BTC-like = coin_00)
    market_returns = coin_data['COIN_00']['close'].pct_change().dropna()
    
    factor_returns_dict = {
        'MKT': pd.DataFrame({'return': market_returns}),
        'MOM': mom_factor,
        'SIZE': size_factor,
        'VOL': vol_factor
    }
    
    print(f"\n      Facteurs construits:")
    for name, factor in factor_returns_dict.items():
        factor_series = factor['return'] if isinstance(factor, pd.DataFrame) else factor
        print(f"         {name}: {len(factor_series)} observations, "
              f"mean={factor_series.mean()*100:.2f}%/jour")
    
    # Régression factorielle (sur COIN_01 par exemple)
    print("\n[2/4] Régression factorielle (COIN_01)...")
    asset_returns = coin_data['COIN_01']['close'].pct_change().dropna()
    
    # Aligner
    min_len = min(len(asset_returns), 
                  min(len(f['return']) if isinstance(f, pd.DataFrame) else len(f) 
                      for f in factor_returns_dict.values()))
    
    asset_returns = asset_returns.iloc[:min_len]
    factor_returns_aligned = {
        name: pd.DataFrame({'return': factor['return'].iloc[:min_len]}) if isinstance(factor, pd.DataFrame) 
            else pd.DataFrame({'return': factor[:min_len]})
        for name, factor in factor_returns_dict.items()
    }
    
    loadings = estimate_factor_loadings(asset_returns, factor_returns_aligned)
    
    if loadings:
        print(f"\n      Résultats régression:")
        print(f"         Alpha: {loadings['alpha']:.4f} (t={loadings['alpha_tstat']:.2f}, p={loadings['alpha_pvalue']:.3f})")
        print(f"         R²: {loadings['r_squared']:.1%}")
        print(f"         Betas:")
        for factor, beta in loadings['betas'].items():
            tstat = loadings['beta_tstats'][factor]
            sig = "✓" if abs(tstat) > 2 else ""
            print(f"            {factor}: {beta:.3f} (t={tstat:.2f}) {sig}")
    
    # Factor timing
    print("\n[3/4] Factor timing analysis...")
    
    # Régimes simulés (basés sur market returns)
    market_vol = market_returns.rolling(30).std()
    regime_labels = ['Bull' if r > 0 else 'Bear' for r in market_returns]
    
    timing_results = analyze_factor_timing(factor_returns_aligned, regime_labels)
    
    print(f"\n      Performance par régime:")
    print(timing_results.round(4).to_string())
    
    # Attribution (sur un portefeuille simple = COIN_01)
    print("\n[4/4] Attribution de performance...")
    attribution = factor_attribution(asset_returns, factor_returns_aligned, loadings)
    
    if attribution:
        print(f"\n      Return Total: {attribution['total_return']:.1%}")
        print(f"      Alpha: {attribution['alpha']:.1%} ({attribution['alpha_pct']:.1f}%)")
        print(f"      Contribution Facteurs: {attribution['total_factor_contrib']:.1%}")
        for factor, contrib in attribution['factors'].items():
            pct = contrib / attribution['total_return'] * 100 if attribution['total_return'] != 0 else 0
            print(f"         {factor}: {contrib:.1%} ({pct:.1f}%)")
    
    # Visualisation
    print("\n" + "=" * 70)
    print("GÉNÉRATION DES VISUALISATIONS...")
    print("=" * 70)
    plot_factor_analysis(factor_returns_aligned, loadings, timing_results, attribution)
    
    print("\n" + "=" * 70)
    print("✅ MULTI-FACTOR MODELS COMPLETE")
    print("=" * 70)
    
    return coin_data, factor_returns_dict, loadings, timing_results, attribution

if __name__ == "__main__":
    coin_data, factors, loadings, timing, attribution = run_multi_factor_analysis()
