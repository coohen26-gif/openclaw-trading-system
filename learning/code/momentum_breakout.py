"""
Momentum & Breakouts - Semaine 14
Détection de breakouts, confirmation volume, backtest Crypto vs Metals
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 1. CALCUL DU MOMENTUM
# ============================================================================

def calculate_momentum(prices, lookback=20):
    """Momentum simple: return sur lookback périodes"""
    return prices.pct_change(lookback)

def calculate_ema_momentum(prices, fast=12, slow=26):
    """Momentum basé sur divergence des EMAs"""
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    momentum = (ema_fast - ema_slow) / ema_slow
    return momentum, ema_fast, ema_slow

def calculate_risk_adjusted_momentum(prices, lookback=60):
    """Momentum ajusté pour le risque (Sharpe-like)"""
    returns = prices.pct_change()
    rolling_mean = returns.rolling(lookback).mean()
    rolling_std = returns.rolling(lookback).std()
    ram = rolling_mean / rolling_std * np.sqrt(252)
    return ram

# ============================================================================
# 2. DÉTECTION DE BREAKOUT
# ============================================================================

def detect_breakout(prices, high, low, volume, lookback=20, vol_threshold=1.5):
    """
    Détecte les breakouts avec confirmation volume.
    """
    # Resistance et Support
    resistance = high.rolling(lookback).max()
    support = low.rolling(lookback).min()
    
    current_price = prices.iloc[-1]
    prev_price = prices.iloc[-2]
    
    # Volume
    current_volume = volume.iloc[-1]
    avg_volume = volume.rolling(lookback).mean().iloc[-1]
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
    
    # Breakout detection
    breakout_signal = 0
    breakout_strength = 0
    
    # Breakout haussier
    if current_price > resistance.iloc[-1] and prev_price <= resistance.iloc[-2]:
        breakout_signal = 1
        breakout_strength = (current_price - resistance.iloc[-1]) / resistance.iloc[-1]
    
    # Breakout baissier
    elif current_price < support.iloc[-1] and prev_price >= support.iloc[-2]:
        breakout_signal = -1
        breakout_strength = abs((current_price - support.iloc[-1]) / support.iloc[-1])
    
    volume_confirmed = volume_ratio >= vol_threshold
    
    return {
        'signal': breakout_signal,
        'strength': min(1.0, breakout_strength * 10),
        'volume_confirmed': volume_confirmed,
        'volume_ratio': volume_ratio,
        'resistance': resistance.iloc[-1],
        'support': support.iloc[-1]
    }

# ============================================================================
# 3. VOLUME METRICS
# ============================================================================

def calculate_volume_metrics(volume, prices, lookback=20):
    """Calcule les metrics de volume"""
    
    # Volume ratio
    volume_ma = volume.rolling(lookback).mean()
    volume_ratio = volume / volume_ma
    
    # OBV
    direction = np.sign(prices.diff())
    obv = (direction * volume).cumsum()
    
    return {
        'volume_ratio': volume_ratio,
        'obv': obv
    }

# ============================================================================
# 4. SIGNAL COMPOSITE
# ============================================================================

def composite_momentum_signal(prices, volume, high, low, lookback=20):
    """Signal composite momentum + breakout + volume"""
    
    # Momentum score
    mom = prices.pct_change(lookback)
    mom_range = mom.rolling(252).max() - mom.rolling(252).min()
    mom_score = (mom - mom.rolling(252).min()) / mom_range.replace(0, 1)
    
    # Breakout
    breakout = detect_breakout(prices, high, low, volume, lookback)
    breakout_score = breakout['strength'] if breakout['signal'] > 0 else 0
    
    # Volume
    vol_metrics = calculate_volume_metrics(volume, prices, lookback)
    vol_score = np.clip(vol_metrics['volume_ratio'].iloc[-1] / 2, 0, 1)
    
    # Composite
    signal = 0.4 * mom_score.iloc[-1] + 0.4 * breakout_score + 0.2 * vol_score
    
    return {
        'composite_signal': signal,
        'momentum_score': mom_score.iloc[-1],
        'breakout_score': breakout_score,
        'volume_score': vol_score,
        'breakout_info': breakout
    }

# ============================================================================
# 5. GÉNÉRATION DE DONNÉES
# ============================================================================

def generate_crypto_data(n_days=500, seed=42):
    """Génère des données crypto simulées (haute volatilité, momentum fort)"""
    np.random.seed(seed)
    
    n_obs = n_days
    
    # Prix avec momentum fort
    initial_price = 50000
    returns = np.random.randn(n_obs) * 0.03  # Haute volatilité
    returns += 0.0005 * np.arange(n_obs)  # Trend haussier
    returns += 0.1 * np.roll(returns, 10)  # Momentum à 10 jours
    
    prices = initial_price * np.cumprod(1 + returns)
    
    # High/Low
    high = prices * (1 + np.abs(np.random.randn(n_obs)) * 0.02)
    low = prices * (1 - np.abs(np.random.randn(n_obs)) * 0.02)
    
    # Volume (corrélé avec mouvements)
    base_volume = 1e9
    volume = base_volume * np.exp(np.abs(returns) * 10)
    volume *= (1 + 0.5 * np.random.randn(n_obs))
    volume = np.abs(volume)
    
    dates = pd.date_range(start='2025-01-01', periods=n_obs, freq='D')
    
    df = pd.DataFrame({
        'close': prices,
        'high': high,
        'low': low,
        'volume': volume
    }, index=dates)
    
    return df

def generate_metals_data(n_days=500, seed=43):
    """Génère des données metals simulées (volatilité modérée, momentum stable)"""
    np.random.seed(seed)
    
    n_obs = n_days
    
    # Prix avec momentum modéré
    initial_price = 2000
    returns = np.random.randn(n_obs) * 0.012  # Volatilité modérée
    returns += 0.0002 * np.arange(n_obs)  # Trend doux
    returns += 0.05 * np.roll(returns, 20)  # Momentum à 20 jours
    
    prices = initial_price * np.cumprod(1 + returns)
    
    # High/Low
    high = prices * (1 + np.abs(np.random.randn(n_obs)) * 0.008)
    low = prices * (1 - np.abs(np.random.randn(n_obs)) * 0.008)
    
    # Volume (moins corrélé avec mouvements)
    base_volume = 1e6
    volume = base_volume * (1 + 0.3 * np.random.randn(n_obs))
    volume = np.abs(volume)
    
    dates = pd.date_range(start='2025-01-01', periods=n_obs, freq='D')
    
    df = pd.DataFrame({
        'close': prices,
        'high': high,
        'low': low,
        'volume': volume
    }, index=dates)
    
    return df

# ============================================================================
# 6. BACKTEST
# ============================================================================

def backtest_momentum_strategy(prices, volume, high, low, lookback=20, rebalance_freq=5):
    """Backtest stratégie momentum + breakout"""
    
    n_obs = len(prices)
    positions = np.zeros(n_obs)
    current_position = 0
    
    for i in range(lookback, n_obs - 1, rebalance_freq):
        signal_data = composite_momentum_signal(
            prices.iloc[:i+1],
            volume.iloc[:i+1],
            high.iloc[:i+1],
            low.iloc[:i+1],
            lookback
        )
        
        signal = signal_data['composite_signal']
        
        if signal > 0.6 and current_position == 0:
            positions[i:i+rebalance_freq] = 1
            current_position = 1
        elif signal < 0.3 and current_position == 1:
            positions[i:i+rebalance_freq] = 0
            current_position = 0
        else:
            positions[i:i+rebalance_freq] = current_position
    
    # Returns
    returns = prices.pct_change()
    strategy_returns = positions[:-1] * returns[1:]
    
    # Métriques
    cumulative = (1 + pd.Series(strategy_returns)).cumprod()
    total_return = cumulative.iloc[-1] - 1 if len(cumulative) > 0 else 0
    
    if np.std(strategy_returns) > 0:
        sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
    else:
        sharpe = 0
    
    max_dd = (cumulative / cumulative.cummax() - 1).min() if len(cumulative) > 0 else 0
    
    # Stats
    winning = strategy_returns[strategy_returns > 0]
    losing = strategy_returns[strategy_returns < 0]
    win_rate = len(winning) / len(strategy_returns) if len(strategy_returns) > 0 else 0
    
    return {
        'total_return': total_return,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'win_rate': win_rate,
        'n_trades': len(winning) + len(losing),
        'cumulative': cumulative,
        'positions': positions,
        'strategy_returns': strategy_returns
    }

# ============================================================================
# 7. VISUALISATION
# ============================================================================

def plot_momentum_analysis(crypto_df, metals_df, crypto_result, metals_result):
    """Visualise l'analyse momentum complète"""
    
    fig, axes = plt.subplots(3, 2, figsize=(16, 12))
    
    # 1. Prix Crypto
    ax1 = axes[0, 0]
    ax1.plot(crypto_df.index, crypto_df['close'], linewidth=1, color='orange')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Price')
    ax1.set_title('Crypto Prices (Simulated)')
    ax1.grid(True, alpha=0.3)
    
    # 2. Prix Metals
    ax2 = axes[0, 1]
    ax2.plot(metals_df.index, metals_df['close'], linewidth=1, color='gold')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Price')
    ax2.set_title('Metals Prices (Simulated)')
    ax2.grid(True, alpha=0.3)
    
    # 3. Momentum Crypto
    ax3 = axes[1, 0]
    mom_crypto = calculate_momentum(crypto_df['close'], 20)
    ax3.plot(crypto_df.index, mom_crypto, linewidth=0.5, color='blue')
    ax3.axhline(0, color='black', linestyle='-', alpha=0.3)
    ax3.set_xlabel('Date')
    ax3.set_ylabel('Momentum (20d)')
    ax3.set_title('Crypto Momentum')
    ax3.grid(True, alpha=0.3)
    
    # 4. Momentum Metals
    ax4 = axes[1, 1]
    mom_metals = calculate_momentum(metals_df['close'], 20)
    ax4.plot(metals_df.index, mom_metals, linewidth=0.5, color='blue')
    ax4.axhline(0, color='black', linestyle='-', alpha=0.3)
    ax4.set_xlabel('Date')
    ax4.set_ylabel('Momentum (20d)')
    ax4.set_title('Metals Momentum')
    ax4.grid(True, alpha=0.3)
    
    # 5. Cumulative Returns
    ax5 = axes[2, 0]
    ax5.plot(crypto_result['cumulative'].index, crypto_result['cumulative'], 
            linewidth=1.5, color='orange', label=f'Crypto (Sharpe={crypto_result["sharpe"]:.2f})')
    ax5.plot(metals_result['cumulative'].index, metals_result['cumulative'], 
            linewidth=1.5, color='gold', label=f'Metals (Sharpe={metals_result["sharpe"]:.2f})')
    ax5.axhline(1.0, color='black', linestyle='-', alpha=0.3)
    ax5.set_xlabel('Date')
    ax5.set_ylabel('Cumulative Return')
    ax5.set_title('Strategy Performance Comparison')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # 6. Returns Distribution
    ax6 = axes[2, 1]
    ax6.hist(crypto_result['strategy_returns'], bins=50, alpha=0.5, 
            color='orange', label='Crypto', edgecolor='black')
    ax6.hist(metals_result['strategy_returns'], bins=50, alpha=0.5, 
            color='gold', label='Metals', edgecolor='black')
    ax6.axvline(0, color='red', linestyle='--', linewidth=2)
    ax6.set_xlabel('Return')
    ax6.set_ylabel('Count')
    ax6.set_title('Strategy Returns Distribution')
    ax6.legend()
    ax6.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('/root/.openclaw/workspace/learning/code/momentum_breakout_output.png', dpi=150)
    print(f"      → Visualisation sauvegardée: momentum_breakout_output.png")

# ============================================================================
# 8. PIPELINE COMPLET
# ============================================================================

def run_momentum_analysis():
    """Exécute l'analyse momentum complète"""
    
    print("=" * 70)
    print("MOMENTUM & BREAKOUTS - SEMAINE 14")
    print("=" * 70)
    
    # Données Crypto
    print("\n[INIT] Génération des données...")
    crypto_df = generate_crypto_data(n_days=500)
    metals_df = generate_metals_data(n_days=500)
    print(f"      → Crypto: {len(crypto_df)} observations")
    print(f"      → Metals: {len(metals_df)} observations")
    
    # Backtest Crypto
    print("\n[1/3] Backtest stratégie Crypto...")
    crypto_result = backtest_momentum_strategy(
        crypto_df['close'], crypto_df['volume'],
        crypto_df['high'], crypto_df['low'],
        lookback=20, rebalance_freq=5
    )
    
    print(f"\n      Performance Crypto:")
    print(f"         → Total Return: {crypto_result['total_return']:.1%}")
    print(f"         → Sharpe Ratio: {crypto_result['sharpe']:.2f}")
    print(f"         → Max Drawdown: {crypto_result['max_drawdown']:.1%}")
    print(f"         → Win Rate: {crypto_result['win_rate']:.1%}")
    print(f"         → N Trades: {crypto_result['n_trades']}")
    
    # Backtest Metals
    print("\n[2/3] Backtest stratégie Metals...")
    metals_result = backtest_momentum_strategy(
        metals_df['close'], metals_df['volume'],
        metals_df['high'], metals_df['low'],
        lookback=20, rebalance_freq=5
    )
    
    print(f"\n      Performance Metals:")
    print(f"         → Total Return: {metals_result['total_return']:.1%}")
    print(f"         → Sharpe Ratio: {metals_result['sharpe']:.2f}")
    print(f"         → Max Drawdown: {metals_result['max_drawdown']:.1%}")
    print(f"         → Win Rate: {metals_result['win_rate']:.1%}")
    print(f"         → N Trades: {metals_result['n_trades']}")
    
    # Comparaison
    print("\n[3/3] Comparaison Crypto vs Metals...")
    print(f"\n      {'Métrique':<20} {'Crypto':<15} {'Metals':<15}")
    print(f"      {'-'*50}")
    print(f"      {'Total Return':<20} {crypto_result['total_return']:<15.1%} {metals_result['total_return']:<15.1%}")
    print(f"      {'Sharpe Ratio':<20} {crypto_result['sharpe']:<15.2f} {metals_result['sharpe']:<15.2f}")
    print(f"      {'Max Drawdown':<20} {crypto_result['max_drawdown']:<15.1%} {metals_result['max_drawdown']:<15.1%}")
    print(f"      {'Win Rate':<20} {crypto_result['win_rate']:<15.1%} {metals_result['win_rate']:<15.1%}")
    
    # Visualisation
    print("\n" + "=" * 70)
    print("GÉNÉRATION DES VISUALISATIONS...")
    print("=" * 70)
    plot_momentum_analysis(crypto_df, metals_df, crypto_result, metals_result)
    
    print("\n" + "=" * 70)
    print("✅ MOMENTUM & BREAKOUTS COMPLETE")
    print("=" * 70)
    
    return crypto_df, metals_df, crypto_result, metals_result

if __name__ == "__main__":
    crypto_df, metals_df, crypto_result, metals_result = run_momentum_analysis()
