#!/usr/bin/env python3
"""
Stress Testing Analysis for BTC
Master 4 - Risk Management Advanced
Semaine 20: Stress Testing & Scenario Analysis
"""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
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

def identify_stress_periods():
    """
    Define historical stress periods for crypto
    Returns dict of (start_date, end_date, description, expected_shock)
    """
    stress_periods = {
        'covid_crash': {
            'start': '2020-03-01',
            'end': '2020-03-31',
            'description': 'COVID-19 Market Crash',
            'type': 'global_risk_off'
        },
        'ftx_collapse': {
            'start': '2022-11-01',
            'end': '2022-11-30',
            'description': 'FTX Exchange Collapse',
            'type': 'crypto_specific'
        },
        'luna_terra': {
            'start': '2022-05-01',
            'end': '2022-05-31',
            'description': 'LUNA/UST Depeg & Collapse',
            'type': 'crypto_specific'
        },
        'china_ban': {
            'start': '2021-05-15',
            'end': '2021-06-15',
            'description': 'China Mining Ban',
            'type': 'regulatory'
        },
        'covid_recovery': {
            'start': '2020-03-13',
            'end': '2020-12-31',
            'description': 'Post-Crash Bull Run',
            'type': 'positive_stress'
        }
    }
    return stress_periods

def apply_historical_scenario(returns, scenario_name, stress_periods):
    """
    Apply historical stress scenario to current returns
    """
    scenario = stress_periods.get(scenario_name)
    if not scenario:
        return None
    
    # For this analysis, we'll use representative shock values
    # based on historical BTC behavior during these periods
    shock_profiles = {
        'covid_crash': {
            'mean_shock': -0.35,  # BTC dropped ~35% in March 2020
            'vol_multiplier': 3.5,
            'correlation_breakdown': True,
            'duration_days': 20,
            'description': scenario['description'],
            'type': scenario['type']
        },
        'ftx_collapse': {
            'mean_shock': -0.25,  # BTC dropped ~25% in Nov 2022
            'vol_multiplier': 2.8,
            'correlation_breakdown': True,
            'duration_days': 15,
            'description': scenario['description'],
            'type': scenario['type']
        },
        'luna_terra': {
            'mean_shock': -0.30,  # BTC dropped ~30% May 2022
            'vol_multiplier': 3.0,
            'correlation_breakdown': True,
            'duration_days': 18,
            'description': scenario['description'],
            'type': scenario['type']
        },
        'china_ban': {
            'mean_shock': -0.50,  # BTC dropped ~50% May-June 2021
            'vol_multiplier': 2.5,
            'correlation_breakdown': False,
            'duration_days': 30,
            'description': scenario['description'],
            'type': scenario['type']
        },
        'covid_recovery': {
            'mean_shock': +0.45,  # BTC gained ~45% from March low to year-end
            'vol_multiplier': 2.0,
            'correlation_breakdown': False,
            'duration_days': 60,
            'description': scenario['description'],
            'type': scenario['type']
        }
    }
    
    return shock_profiles.get(scenario_name)

def simulate_stress_scenario(returns, scenario_name, stress_periods, n_simulations=10000):
    """
    Simulate portfolio performance under stress scenario
    """
    shock = apply_historical_scenario(returns, scenario_name, stress_periods)
    if not shock:
        return None
    
    # Base statistics
    base_mean = returns.mean()
    base_std = returns.std()
    
    # Apply stress
    stressed_mean = base_mean + shock['mean_shock'] / shock['duration_days']
    stressed_std = base_std * shock['vol_multiplier']
    
    # Simulate returns for the duration
    duration = shock['duration_days']
    simulated_paths = np.random.normal(stressed_mean, stressed_std, (n_simulations, duration))
    
    # Calculate cumulative returns
    cumulative_returns = np.prod(1 + simulated_paths, axis=1) - 1
    
    # Calculate max drawdown for each path
    cumulative_wealth = np.cumprod(1 + simulated_paths, axis=1)
    running_max = np.maximum.accumulate(cumulative_wealth, axis=1)
    drawdowns = (cumulative_wealth - running_max) / running_max
    max_drawdowns = np.min(drawdowns, axis=1)
    
    return {
        'scenario_name': scenario_name,
        'description': shock['description'],
        'shock': shock,
        'final_returns': cumulative_returns,
        'max_drawdowns': max_drawdowns,
        'var_95': np.percentile(cumulative_returns, 5),
        'var_99': np.percentile(cumulative_returns, 1),
        'cvar_95': np.mean(cumulative_returns[cumulative_returns <= np.percentile(cumulative_returns, 5)]),
        'expected_return': np.mean(cumulative_returns),
        'median_return': np.median(cumulative_returns),
        'prob_loss_gt_20pct': np.mean(cumulative_returns < -0.20),
        'prob_loss_gt_50pct': np.mean(cumulative_returns < -0.50)
    }

def calculate_portfolio_var_under_stress(returns, stress_periods, portfolio_value=100000):
    """
    Calculate VaR/CVaR under different stress scenarios
    """
    results = []
    
    # Normal conditions (baseline)
    baseline = {
        'scenario': 'Normal Conditions',
        'var_95': np.percentile(returns, 5),
        'var_99': np.percentile(returns, 1),
        'cvar_95': np.mean(returns[returns <= np.percentile(returns, 5)]),
        'cvar_99': np.mean(returns[returns <= np.percentile(returns, 1)]),
        'daily_vol': returns.std(),
        'shock_type': 'baseline'
    }
    results.append(baseline)
    
    # Stress scenarios
    for scenario_name in ['covid_crash', 'ftx_collapse', 'luna_terra', 'china_ban']:
        sim = simulate_stress_scenario(returns, scenario_name, stress_periods)
        if sim:
            stress_result = {
                'scenario': sim['description'],
                'var_95': sim['var_95'],
                'var_99': sim['var_99'],
                'cvar_95': sim['cvar_95'],
                'cvar_99': np.percentile(sim['final_returns'], 1) if len(sim['final_returns']) > 0 else None,
                'daily_vol': returns.std() * sim['shock']['vol_multiplier'],
                'expected_loss': sim['expected_return'],
                'max_drawdown_expected': np.mean(sim['max_drawdowns']),
                'shock_type': sim['shock']['type']
            }
            results.append(stress_result)
    
    return results

def design_circuit_breakers(returns, stress_results):
    """
    Design circuit breakers based on stress test results
    """
    circuit_breakers = []
    
    # Level 1: Warning threshold (based on normal VaR)
    normal_var_95 = np.percentile(returns, 5)
    circuit_breakers.append({
        'level': 1,
        'name': 'Warning',
        'trigger': f"Daily loss > {abs(normal_var_95)*100:.1f}%",
        'action': 'Alert sent, review positions',
        'threshold': normal_var_95
    })
    
    # Level 2: Reduce risk (based on stress scenario mild)
    mild_stress_var = stress_results[1]['var_95'] if len(stress_results) > 1 else -0.10
    circuit_breakers.append({
        'level': 2,
        'name': 'Risk Reduction',
        'trigger': f"Daily loss > {abs(mild_stress_var)*100:.1f}%",
        'action': 'Reduce position size by 50%',
        'threshold': mild_stress_var
    })
    
    # Level 3: Emergency stop (based on severe stress)
    severe_stress_var = stress_results[2]['var_95'] if len(stress_results) > 2 else -0.20
    circuit_breakers.append({
        'level': 3,
        'name': 'Emergency Stop',
        'trigger': f"Daily loss > {abs(severe_stress_var)*100:.1f}%",
        'action': 'Close all positions, halt trading',
        'threshold': severe_stress_var
    })
    
    # Level 4: Portfolio-level circuit breaker (drawdown)
    circuit_breakers.append({
        'level': 4,
        'name': 'Max Drawdown',
        'trigger': 'Portfolio drawdown > 20% from peak',
        'action': 'Delever to 25% exposure, risk review required',
        'threshold': -0.20
    })
    
    return circuit_breakers

def plot_stress_scenarios(stress_results, save_path=None):
    """Plot stress scenario comparisons"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. VaR Comparison Across Scenarios
    ax1 = axes[0, 0]
    scenarios = [r['scenario'] for r in stress_results]
    var_95_values = [r['var_95'] for r in stress_results]
    var_99_values = [r['var_99'] for r in stress_results]
    
    x = np.arange(len(scenarios))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, [abs(v)*100 for v in var_95_values], width, label='VaR 95%', color='steelblue')
    bars2 = ax1.bar(x + width/2, [abs(v)*100 for v in var_99_values], width, label='VaR 99%', color='darkblue')
    
    ax1.set_xlabel('Scenario')
    ax1.set_ylabel('VaR (%)')
    ax1.set_title('VaR Comparison Across Stress Scenarios')
    ax1.set_xticks(x)
    ax1.set_xticklabels([s[:15] + '...' if len(s) > 15 else s for s in scenarios], rotation=45, ha='right')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # 2. Expected Loss Distribution (histogram for worst scenario)
    ax2 = axes[0, 1]
    if len(stress_results) > 1:
        worst_scenario = stress_results[2]  # FTX or similar
        # Simulate for visualization
        sim = simulate_stress_scenario(load_btc_data()['returns'], 'ftx_collapse', identify_stress_periods())
        if sim:
            ax2.hist(sim['final_returns'] * 100, bins=50, alpha=0.7, color='red', edgecolor='black')
            ax2.axvline(sim['var_95'] * 100, color='blue', linestyle='--', linewidth=2, label=f"VaR 95%: {sim['var_95']*100:.1f}%")
            ax2.axvline(sim['cvar_95'] * 100, color='darkred', linestyle='-', linewidth=2, label=f"CVaR 95%: {sim['cvar_95']*100:.1f}%")
            ax2.set_xlabel('Portfolio Return During Stress (%)')
            ax2.set_ylabel('Frequency')
            ax2.set_title(f"Return Distribution: {worst_scenario['scenario']}")
            ax2.legend()
            ax2.grid(alpha=0.3)
    
    # 3. Max Drawdown Comparison
    ax3 = axes[1, 0]
    if len(stress_results) > 1:
        mdd_values = [r.get('max_drawdown_expected', 0) for r in stress_results]
        colors = ['green'] + ['red'] * (len(mdd_values) - 1)
        bars = ax3.bar(range(len(scenarios)), [abs(m)*100 for m in mdd_values], color=colors, alpha=0.7)
        ax3.set_xlabel('Scenario')
        ax3.set_ylabel('Expected Max Drawdown (%)')
        ax3.set_title('Expected Maximum Drawdown by Scenario')
        ax3.set_xticks(range(len(scenarios)))
        ax3.set_xticklabels([s[:15] + '...' if len(s) > 15 else s for s in scenarios], rotation=45, ha='right')
        ax3.grid(axis='y', alpha=0.3)
    
    # 4. Circuit Breaker Levels
    ax4 = axes[1, 1]
    circuit_breakers = design_circuit_breakers(load_btc_data()['returns'], stress_results)
    thresholds = [abs(cb['threshold'])*100 for cb in circuit_breakers]
    colors_cb = ['yellow', 'orange', 'red', 'darkred']
    
    bars = ax4.barh(range(len(circuit_breakers)), thresholds, color=colors_cb, alpha=0.7)
    ax4.set_yticks(range(len(circuit_breakers)))
    ax4.set_yticklabels([f"Level {cb['level']}: {cb['name']}" for cb in circuit_breakers])
    ax4.set_xlabel('Trigger Threshold (%)')
    ax4.set_title('Circuit Breaker Design')
    ax4.invert_yaxis()
    ax4.grid(axis='x', alpha=0.3)
    
    # Add threshold values on bars
    for i, (bar, cb) in enumerate(zip(bars, circuit_breakers)):
        ax4.text(bar.get_width() + 1, i, f"{bar.get_width():.1f}%", va='center', fontsize=9)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    plt.close()

def plot_scenario_paths(n_paths=50, save_path=None):
    """Plot simulated price paths under stress"""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    returns = load_btc_data()['returns']
    stress_periods = identify_stress_periods()
    
    # Normal scenario
    normal_paths = np.cumprod(1 + np.random.normal(returns.mean(), returns.std(), (n_paths, 30)), axis=1)
    for i in range(n_paths):
        ax.plot(normal_paths[i], color='green', alpha=0.1, linewidth=1)
    
    # Stress scenario (FTX)
    sim = simulate_stress_scenario(returns, 'ftx_collapse', stress_periods)
    if sim:
        stress_paths = np.cumprod(1 + np.random.normal(sim['shock']['mean_shock']/sim['shock']['duration_days'], 
                                                        returns.std() * sim['shock']['vol_multiplier'], 
                                                        (n_paths, sim['shock']['duration_days'])), axis=1)
        for i in range(n_paths):
            ax.plot(stress_paths[i], color='red', alpha=0.2, linewidth=1.5)
    
    # Averages
    ax.plot(np.mean(normal_paths, axis=0), color='green', linewidth=3, label='Normal (avg)')
    if sim:
        ax.plot(np.mean(stress_paths, axis=0), color='red', linewidth=3, label='FTX Stress (avg)')
    
    ax.set_xlabel('Days')
    ax.set_ylabel('Cumulative Return (1 = initial value)')
    ax.set_title('Simulated Price Paths: Normal vs FTX Stress Scenario')
    ax.legend()
    ax.grid(alpha=0.3)
    ax.axhline(1.0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    plt.close()

def main():
    print("=" * 70)
    print("Stress Testing Analysis - BTC")
    print("Master 4 - Risk Management Advanced")
    print("=" * 70)
    
    # Load data
    df = load_btc_data()
    returns = df['returns']
    stress_periods = identify_stress_periods()
    
    print(f"\nData period: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Number of observations: {len(returns)}")
    
    # Calculate stress test results
    print("\n" + "=" * 70)
    print("STRESS TEST RESULTS")
    print("=" * 70)
    
    stress_results = calculate_portfolio_var_under_stress(returns, stress_periods)
    
    for i, result in enumerate(stress_results):
        print(f"\n{i+1}. {result['scenario']}")
        print(f"   Type: {result.get('shock_type', 'N/A')}")
        print(f"   Daily Volatility: {result['daily_vol']*100:.2f}%")
        if 'var_95' in result:
            print(f"   VaR 95%: {result['var_95']*100:.2f}%")
            print(f"   VaR 99%: {result['var_99']*100:.2f}%")
        if 'cvar_95' in result and result['cvar_95']:
            print(f"   CVaR 95%: {result['cvar_95']*100:.2f}%")
        if 'expected_loss' in result:
            print(f"   Expected Loss: {result['expected_loss']*100:.2f}%")
        if 'max_drawdown_expected' in result:
            print(f"   Expected Max Drawdown: {result['max_drawdown_expected']*100:.2f}%")
    
    # Dollar terms
    print("\n" + "=" * 70)
    print("PORTFOLIO IMPACT ($100,000 Portfolio)")
    print("=" * 70)
    
    portfolio_value = 100000
    for result in stress_results:
        if 'var_95' in result:
            var_dollar = abs(result['var_95']) * portfolio_value
            print(f"\n{result['scenario']}:")
            print(f"   VaR 95% Loss: ${var_dollar:,.2f}")
            if 'cvar_95' in result and result['cvar_95']:
                cvar_dollar = abs(result['cvar_95']) * portfolio_value
                print(f"   CVaR 95% Loss: ${cvar_dollar:,.2f}")
    
    # Circuit breakers
    print("\n" + "=" * 70)
    print("CIRCUIT BREAKER DESIGN")
    print("=" * 70)
    
    circuit_breakers = design_circuit_breakers(returns, stress_results)
    for cb in circuit_breakers:
        print(f"\nLevel {cb['level']} - {cb['name']}:")
        print(f"   Trigger: {cb['trigger']}")
        print(f"   Action: {cb['action']}")
    
    # Generate visualizations
    print("\n" + "=" * 70)
    print("GENERATING VISUALIZATIONS")
    print("=" * 70)
    
    plot_stress_scenarios(stress_results, '/root/.openclaw/workspace/learning/figures/stress-scenarios-comparison.png')
    plot_scenario_paths(save_path='/root/.openclaw/workspace/learning/figures/stress-scenario-paths.png')
    
    # Additional: Drawdown analysis
    fig, ax = plt.subplots(figsize=(14, 6))
    cumulative = np.cumprod(1 + returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - running_max) / running_max
    
    ax.fill_between(range(len(drawdown)), drawdown * 100, 0, alpha=0.5, color='red')
    ax.set_xlabel('Days')
    ax.set_ylabel('Drawdown (%)')
    ax.set_title('Historical Drawdown Analysis')
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/root/.openclaw/workspace/learning/figures/historical-drawdown.png', dpi=150, bbox_inches='tight')
    print("Saved: /root/.openclaw/workspace/learning/figures/historical-drawdown.png")
    plt.close()
    
    print("\n" + "=" * 70)
    print("Stress Testing Analysis Complete!")
    print("=" * 70)
    
    return {
        'stress_results': stress_results,
        'circuit_breakers': circuit_breakers
    }

if __name__ == "__main__":
    main()
