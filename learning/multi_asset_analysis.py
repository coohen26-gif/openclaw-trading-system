#!/usr/bin/env python3
"""
Multi-Asset Analysis - Nuit du 23-24 Mai 2026
Analyse complète de 4 asset classes pour le Système Saiyan
"""

import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.tsa.stattools import adfuller
import yfinance as yf
import ccxt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configuration
plt.style.use('dark_background')
COLORS = {'crypto': '#FFD700', 'forex': '#00CED1', 'indices': '#FF6347', 'metals': '#C0C0C0'}

def fetch_crypto_data(symbols=['BTC/USDT', 'ETH/USDT'], timeframe='1h', limit=4320):
    """Fetch crypto data from Binance via CCXT (6 months of 1h data)"""
    print("🔮 Fetching Crypto data from Binance...")
    exchange = ccxt.binance()
    data = {}
    
    for symbol in symbols:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            data[symbol] = df['close']
            print(f"  ✓ {symbol}: {len(df)} candles")
        except Exception as e:
            print(f"  ✗ {symbol}: {e}")
    
    return data

def fetch_yfinance_data(tickers, period='1y', interval='1h'):
    """Fetch data from Yahoo Finance"""
    print(f"📈 Fetching Yahoo Finance data ({period}, {interval})...")
    data = {}
    
    for ticker in tickers:
        try:
            df = yf.download(ticker, period=period, interval=interval, progress=False)
            if len(df) > 0:
                if 'Close' in df.columns:
                    data[ticker] = df['Close']
                elif 'Adj Close' in df.columns:
                    data[ticker] = df['Adj Close']
                print(f"  ✓ {ticker}: {len(df)} candles")
            else:
                print(f"  ✗ {ticker}: No data returned")
        except Exception as e:
            print(f"  ✗ {ticker}: {e}")
    
    return data

def calculate_returns(prices):
    """Calculate log returns"""
    return np.log(prices / prices.shift(1)).dropna()

def analyze_distribution(returns, name):
    """Analyze return distribution: kurtosis, skewness, normality test"""
    returns_clean = returns.dropna()
    results = {
        'asset': name,
        'mean': float(returns.mean()),
        'std': float(returns.std()),
        'skewness': float(stats.skew(returns_clean)),
        'kurtosis': float(stats.kurtosis(returns_clean)),  # excess kurtosis
        'jarque_bera_stat': None,
        'jarque_bera_pvalue': None,
        'normal': None
    }
    
    # Jarque-Bera test for normality
    jb_stat, jb_pvalue = stats.jarque_bera(returns_clean)
    results['jarque_bera_stat'] = float(jb_stat)
    results['jarque_bera_pvalue'] = float(jb_pvalue)
    results['normal'] = jb_pvalue > 0.05  # Cannot reject normality
    
    return results

def test_stationarity(returns, name):
    """ADF test for stationarity"""
    adf_result = adfuller(returns.dropna(), maxlag=10, regression='c')
    return {
        'asset': name,
        'adf_statistic': adf_result[0],
        'adf_pvalue': adf_result[1],
        'stationary': adf_result[1] < 0.05
    }

def calculate_volatility_metrics(returns, window=24):
    """Calculate volatility clustering and other metrics"""
    rolling_std = returns.rolling(window=window).std()
    rolling_mean = returns.rolling(window=window).mean()
    
    # Volatility clustering: ratio of std to mean of squared returns
    squared_returns = returns ** 2
    vol_clustering = squared_returns.rolling(window=window).mean() / squared_returns.rolling(window=window).std()
    
    return {
        'avg_vol': float(rolling_std.mean()),
        'vol_of_vol': float(rolling_std.std()),
        'vol_clustering': float(vol_clustering.mean()) if not pd.isna(vol_clustering.mean()) else 0.0
    }

def backtest_mean_reversion(prices, returns, rsi_period=14, oversold=30, overbought=70):
    """Backtest mean reversion strategy using RSI"""
    # Calculate RSI
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # Signals
    positions = pd.Series(0, index=prices.index)
    positions[rsi < oversold] = 1  # Long when oversold
    positions[rsi > overbought] = -1  # Short when overbought
    
    # Returns
    strategy_returns = positions.shift(1) * returns
    cumulative = (1 + strategy_returns).cumprod()
    
    # Metrics
    total_return = cumulative.iloc[-1] - 1 if len(cumulative) > 0 else 0
    sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252) if strategy_returns.std() > 0 else 0
    max_dd = (cumulative / cumulative.cummax() - 1).min()
    win_rate = (strategy_returns > 0).sum() / len(strategy_returns) if len(strategy_returns) > 0 else 0
    
    return {
        'total_return': total_return,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'win_rate': win_rate,
        'cumulative': cumulative
    }

def backtest_momentum(prices, returns, lookback=20):
    """Backtest momentum/breakout strategy"""
    # Breakout: long if price > rolling max, short if price < rolling min
    rolling_max = prices.rolling(window=lookback).max()
    rolling_min = prices.rolling(window=lookback).min()
    
    positions = pd.Series(0, index=prices.index)
    positions[prices > rolling_max] = 1
    positions[prices < rolling_min] = -1
    
    # Returns
    strategy_returns = positions.shift(1) * returns
    cumulative = (1 + strategy_returns).cumprod()
    
    # Metrics
    total_return = cumulative.iloc[-1] - 1 if len(cumulative) > 0 else 0
    sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252) if strategy_returns.std() > 0 else 0
    max_dd = (cumulative / cumulative.cummax() - 1).min()
    win_rate = (strategy_returns > 0).sum() / len(strategy_returns) if len(strategy_returns) > 0 else 0
    
    return {
        'total_return': total_return,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'win_rate': win_rate,
        'cumulative': cumulative
    }

def create_comparison_charts(results_dict, distribution_results, volatility_results, backtest_results):
    """Create comprehensive comparison charts"""
    fig, axes = plt.subplots(3, 2, figsize=(16, 14))
    fig.suptitle('Multi-Asset Analysis - Système Saiyan\nNuit du 23-24 Mai 2026', fontsize=16, fontweight='bold')
    
    asset_classes = list(results_dict.keys())
    colors = [COLORS.get(ac, '#FFFFFF') for ac in asset_classes]
    
    # 1. Distribution Comparison (Kurtosis & Skewness)
    ax1 = axes[0, 0]
    kurtosis_vals = [distribution_results[ac]['kurtosis'] for ac in asset_classes]
    skewness_vals = [distribution_results[ac]['skewness'] for ac in asset_classes]
    
    x = np.arange(len(asset_classes))
    width = 0.35
    bars1 = ax1.bar(x - width/2, kurtosis_vals, width, label='Kurtosis (Excess)', color=colors, alpha=0.8)
    bars2 = ax1.bar(x + width/2, skewness_vals, width, label='Skewness', color=colors, alpha=0.5, hatch='//')
    
    ax1.set_ylabel('Value')
    ax1.set_title('Distribution Shape: Fat Tails & Asymmetry', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([ac.replace('-', ' ').title() for ac in asset_classes], rotation=15)
    ax1.axhline(y=0, color='white', linestyle='--', alpha=0.5)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Volatility Comparison
    ax2 = axes[0, 1]
    vol_vals = [volatility_results[ac]['avg_vol'] * np.sqrt(252) for ac in asset_classes]  # Annualized
    vol_of_vol = [volatility_results[ac]['vol_of_vol'] * np.sqrt(252) for ac in asset_classes]
    
    bars3 = ax2.bar(x - width/2, vol_vals, width, label='Annualized Vol', color=colors, alpha=0.8)
    bars4 = ax2.bar(x + width/2, vol_of_vol, width, label='Vol of Vol', color=colors, alpha=0.5, hatch='//')
    
    ax2.set_ylabel('Annualized Volatility')
    ax2.set_title('Volatility Characteristics', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels([ac.replace('-', ' ').title() for ac in asset_classes], rotation=15)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Backtest Comparison - Sharpe Ratio
    ax3 = axes[1, 0]
    mr_sharpe = [backtest_results[ac]['mean_reversion']['sharpe'] for ac in asset_classes]
    mom_sharpe = [backtest_results[ac]['momentum']['sharpe'] for ac in asset_classes]
    
    x2 = np.arange(len(asset_classes))
    bars5 = ax3.bar(x2 - width/2, mr_sharpe, width, label='Mean Reversion', color=colors, alpha=0.8)
    bars6 = ax3.bar(x2 + width/2, mom_sharpe, width, label='Momentum', color=colors, alpha=0.5, hatch='//')
    
    ax3.set_ylabel('Sharpe Ratio')
    ax3.set_title('Strategy Performance: Sharpe Ratio', fontweight='bold')
    ax3.set_xticks(x2)
    ax3.set_xticklabels([ac.replace('-', ' ').title() for ac in asset_classes], rotation=15)
    ax3.axhline(y=0, color='white', linestyle='--', alpha=0.5)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Backtest Comparison - Max Drawdown
    ax4 = axes[1, 1]
    mr_dd = [backtest_results[ac]['mean_reversion']['max_drawdown'] for ac in asset_classes]
    mom_dd = [backtest_results[ac]['momentum']['max_drawdown'] for ac in asset_classes]
    
    bars7 = ax4.bar(x2 - width/2, mr_dd, width, label='Mean Reversion', color=colors, alpha=0.8)
    bars8 = ax4.bar(x2 + width/2, mom_dd, width, label='Momentum', color=colors, alpha=0.5, hatch='//')
    
    ax4.set_ylabel('Max Drawdown')
    ax4.set_title('Risk: Maximum Drawdown', fontweight='bold')
    ax4.set_xticks(x2)
    ax4.set_xticklabels([ac.replace('-', ' ').title() for ac in asset_classes], rotation=15)
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 5. Stationarity Summary
    ax5 = axes[2, 0]
    ax5.axis('off')
    
    stationarity_text = "STATIONARITY ANALYSIS (ADF Test)\n" + "="*40 + "\n\n"
    for ac in asset_classes:
        stat = '✓ STATIONARY' if distribution_results[ac].get('stationary', False) else '✗ NON-STATIONARY'
        pval = distribution_results[ac].get('adf_pvalue', 'N/A')
        pval_str = f"{pval:.4f}" if isinstance(pval, float) else str(pval)
        stationarity_text += f"{ac.replace('-', ' ').title():15} {stat:15} (p={pval_str})\n"
    
    ax5.text(0.1, 0.5, stationarity_text, transform=ax5.transAxes, fontsize=11, 
             verticalalignment='center', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='#1a1a2e', edgecolor='#4a4a6a', alpha=0.8))
    
    # 6. Summary & Recommendation
    ax6 = axes[2, 1]
    ax6.axis('off')
    
    # Calculate scores
    scores = {}
    for ac in asset_classes:
        fat_tails_score = abs(distribution_results[ac]['kurtosis'])  # Higher = more opportunities
        mr_score = backtest_results[ac]['mean_reversion']['sharpe']  # Higher = better for mean reversion
        mom_score = backtest_results[ac]['momentum']['sharpe']
        vol_score = volatility_results[ac]['avg_vol']  # Higher = more movement
        
        scores[ac] = {
            'fat_tails': fat_tails_score,
            'mean_reversion': mr_score,
            'momentum': mom_score,
            'volatility': vol_score
        }
    
    best_fat_tails = max(scores.items(), key=lambda x: x[1]['fat_tails'])[0]
    best_mr = max(scores.items(), key=lambda x: x[1]['mean_reversion'])[0]
    best_mom = max(scores.items(), key=lambda x: x[1]['momentum'])[0]
    best_vol = max(scores.items(), key=lambda x: x[1]['volatility'])[0]
    
    summary_text = "RECOMMENDATION SUMMARY\n" + "="*40 + "\n\n"
    summary_text += f"🎯 Most Fat Tails:      {best_fat_tails.replace('-', ' ').title()}\n"
    summary_text += f"📊 Best Mean Reversion: {best_mr.replace('-', ' ').title()}\n"
    summary_text += f"🚀 Best Momentum:       {best_mom.replace('-', ' ').title()}\n"
    summary_text += f"⚡ Highest Volatility:  {best_vol.replace('-', ' ').title()}\n\n"
    
    # Overall recommendation
    overall_score = {ac: scores[ac]['fat_tails'] * 0.3 + scores[ac]['mean_reversion'] * 0.4 + scores[ac]['momentum'] * 0.3 
                     for ac in asset_classes}
    best_overall = max(overall_score.items(), key=lambda x: x[1])[0]
    
    summary_text += f"🏆 OVERALL WINNER: {best_overall.replace('-', ' ').title()}\n\n"
    summary_text += "See learning/recommendation-asset-class.md for detailed analysis."
    
    ax6.text(0.1, 0.5, summary_text, transform=ax6.transAxes, fontsize=11,
             verticalalignment='center', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='#1a1a2e', edgecolor='#FFD700', alpha=0.8, linewidth=2))
    
    plt.tight_layout()
    plt.savefig('learning/figures/multi-asset-comparison.png', dpi=150, bbox_inches='tight', facecolor='#0d0d1a')
    plt.close()
    print("✓ Charts saved to learning/figures/multi-asset-comparison.png")
    
    return scores, best_overall

def main():
    print("="*60)
    print("🚀 ANALYSE MULTI-ASSET COMPLÈTE - Nuit du 23-24 Mai 2026")
    print("="*60)
    print()
    
    # 1. Fetch Data
    print("📊 ÉTAPE 1: Récupération des données")
    print("-" * 60)
    
    # Crypto from Binance
    crypto_data = fetch_crypto_data(['BTC/USDT', 'ETH/USDT'])
    
    # Forex, Indices, Metals from Yahoo Finance
    forex_tickers = ['EURUSD=X', 'USDJPY=X']
    indices_tickers = ['^NDX', '^GSPC']
    metals_tickers = ['GC=F', 'SI=F']
    
    forex_data = fetch_yfinance_data(forex_tickers, period='1y', interval='1h')
    indices_data = fetch_yfinance_data(indices_tickers, period='1y', interval='1h')
    metals_data = fetch_yfinance_data(metals_tickers, period='1y', interval='1h')
    
    # Aggregate by asset class
    results_dict = {
        'crypto': crypto_data,
        'forex': forex_data,
        'indices': indices_data,
        'metals': metals_data
    }
    
    print()
    print("📊 ÉTAPE 2: Analyse des distributions")
    print("-" * 60)
    
    distribution_results = {}
    all_returns = {}
    
    for asset_class, data_dict in results_dict.items():
        print(f"\n{asset_class.upper()}:")
        for symbol, prices in data_dict.items():
            # Handle MultiIndex columns from yfinance
            if isinstance(prices, pd.DataFrame):
                if 'Close' in prices.columns:
                    prices = prices['Close']
                elif 'Adj Close' in prices.columns:
                    prices = prices['Adj Close']
                else:
                    prices = prices.iloc[:, 0]
            
            returns = calculate_returns(prices)
            all_returns[f"{asset_class}-{symbol}"] = returns
            
            dist_analysis = analyze_distribution(returns, f"{asset_class}-{symbol}")
            distribution_results[f"{asset_class}-{symbol}"] = dist_analysis
            
            print(f"  {symbol}:")
            print(f"    Kurtosis: {dist_analysis['kurtosis']:.3f} (fat tails: {'YES' if abs(dist_analysis['kurtosis']) > 1 else 'NO'})")
            print(f"    Skewness: {dist_analysis['skewness']:.3f}")
            print(f"    Jarque-Bera p-value: {dist_analysis['jarque_bera_pvalue']:.2e}")
            print(f"    Normal distribution: {'YES' if dist_analysis['normal'] else 'NO'}")
    
    print()
    print("📊 ÉTAPE 3: Test de stationnarité (ADF)")
    print("-" * 60)
    
    stationarity_results = {}
    for symbol, returns in all_returns.items():
        stat_result = test_stationarity(returns, symbol)
        stationarity_results[symbol] = stat_result
        print(f"  {symbol}: ADF p-value = {stat_result['adf_pvalue']:.4f} → {'✓ Stationary' if stat_result['stationary'] else '✗ Non-stationary'}")
    
    # Add stationarity to distribution results
    for symbol, stat_result in stationarity_results.items():
        if symbol in distribution_results:
            distribution_results[symbol]['stationary'] = stat_result['stationary']
            distribution_results[symbol]['adf_pvalue'] = stat_result['adf_pvalue']
    
    print()
    print("📊 ÉTAPE 4: Analyse des volatilités")
    print("-" * 60)
    
    volatility_results = {}
    for asset_class, data_dict in results_dict.items():
        print(f"\n{asset_class.upper()}:")
        class_returns = pd.concat([all_returns[f"{asset_class}-{sym}"] for sym in data_dict.keys()], axis=1).mean(axis=1)
        
        vol_metrics = calculate_volatility_metrics(class_returns)
        volatility_results[asset_class] = vol_metrics
        
        print(f"  Avg Daily Vol: {vol_metrics['avg_vol']:.4f} ({vol_metrics['avg_vol']*np.sqrt(252)*100:.2f}% annualized)")
        print(f"  Vol of Vol: {vol_metrics['vol_of_vol']:.4f}")
        print(f"  Vol Clustering: {vol_metrics['vol_clustering']:.2f}")
    
    print()
    print("📊 ÉTAPE 5: Backtest des stratégies")
    print("-" * 60)
    
    backtest_results = {}
    
    for asset_class, data_dict in results_dict.items():
        print(f"\n{asset_class.upper()}:")
        class_prices = pd.concat([prices for prices in data_dict.values()], axis=1).mean(axis=1)
        class_returns = calculate_returns(class_prices)
        
        # Mean Reversion
        mr_results = backtest_mean_reversion(class_prices, class_returns)
        
        # Momentum
        mom_results = backtest_momentum(class_prices, class_returns)
        
        backtest_results[asset_class] = {
            'mean_reversion': mr_results,
            'momentum': mom_results
        }
        
        print(f"  Mean Reversion:")
        print(f"    Total Return: {mr_results['total_return']*100:.2f}%")
        print(f"    Sharpe Ratio: {mr_results['sharpe']:.3f}")
        print(f"    Max Drawdown: {mr_results['max_drawdown']*100:.2f}%")
        print(f"    Win Rate: {mr_results['win_rate']*100:.1f}%")
        
        print(f"  Momentum:")
        print(f"    Total Return: {mom_results['total_return']*100:.2f}%")
        print(f"    Sharpe Ratio: {mom_results['sharpe']:.3f}")
        print(f"    Max Drawdown: {mom_results['max_drawdown']*100:.2f}%")
        print(f"    Win Rate: {mom_results['win_rate']*100:.1f}%")
    
    print()
    print("📊 ÉTAPE 6: Génération des graphiques")
    print("-" * 60)
    
    # Aggregate distribution results by asset class for charting
    class_distribution = {}
    for asset_class in results_dict.keys():
        class_symbols = [k for k in distribution_results.keys() if k.startswith(asset_class)]
        if class_symbols:
            class_distribution[asset_class] = {
                'kurtosis': np.mean([distribution_results[s]['kurtosis'] for s in class_symbols]),
                'skewness': np.mean([distribution_results[s]['skewness'] for s in class_symbols]),
                'stationary': any([distribution_results[s].get('stationary', False) for s in class_symbols]),
                'adf_pvalue': np.mean([distribution_results[s].get('adf_pvalue', 1) for s in class_symbols])
            }
    
    scores, best_overall = create_comparison_charts(
        results_dict, 
        class_distribution, 
        volatility_results, 
        backtest_results
    )
    
    print()
    print("="*60)
    print("✅ ANALYSE TERMINÉE")
    print("="*60)
    print(f"\n🏆 RECOMMANDATION: Concentrer le Système Saiyan sur {best_overall.upper()}")
    print()
    
    return {
        'distribution_results': distribution_results,
        'volatility_results': volatility_results,
        'backtest_results': backtest_results,
        'scores': scores,
        'best_overall': best_overall,
        'class_distribution': class_distribution
    }

if __name__ == '__main__':
    results = main()
