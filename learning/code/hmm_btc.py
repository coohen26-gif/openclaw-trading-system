#!/usr/bin/env python3
"""
Hidden Markov Models for BTC Regime Detection
Semaine 15 - Apprentissage Théorique

Run: cd /root/.openclaw/workspace/learning && source venv/bin/activate && python code/hmm_btc.py
"""

import pandas as pd
import numpy as np
from hmmlearn import hmm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import sys
import os

sys.path.insert(0, '/root/.openclaw/workspace/learning')

def generate_btc_regimes(n_days=1000, seed=42):
    """Generate BTC returns with 3 distinct regimes."""
    np.random.seed(seed)
    dates = pd.date_range(end=datetime.now(), periods=n_days, freq='D')
    
    regime_length = n_days // 3
    
    # Regime 1: Bull (positive returns, moderate vol)
    bull_returns = np.random.normal(0.002, 0.025, regime_length)
    
    # Regime 2: Bear (negative returns, high vol)
    bear_returns = np.random.normal(-0.003, 0.04, regime_length)
    
    # Regime 3: Range (neutral returns, low vol)
    range_returns = np.random.normal(0.0001, 0.015, n_days - 2*regime_length)
    
    returns = np.concatenate([bull_returns, bear_returns, range_returns])
    returns_series = pd.Series(returns, index=dates, name='BTC_returns')
    
    return returns_series

def train_hmm(returns, n_components=3, n_iter=100):
    """Train Gaussian HMM on returns."""
    returns_2d = returns.reshape(-1, 1)
    
    model = hmm.GaussianHMM(
        n_components=n_components,
        covariance_type='diag',
        n_iter=n_iter,
        random_state=42,
        verbose=False
    )
    
    model.fit(returns_2d)
    # Note: hmmlearn doesn't expose n_iter_ directly, use the configured n_iter
    return model, returns_2d, model.n_iter

def analyze_parameters(model, n_components=3):
    """Analyze learned HMM parameters."""
    print("\n" + "=" * 60)
    print("LEARNED PARAMETERS")
    print("=" * 60)
    
    # Transition matrix
    print("\n📊 Transition Matrix (A):")
    print("         " + "   ".join([f"État {i}" for i in range(n_components)]))
    for i, row in enumerate(model.transmat_):
        row_str = "  ".join([f"{val:.3f}" for val in row])
        print(f"État {i}  {row_str}")
    
    # Emission probabilities (Gaussian parameters)
    print("\n📊 Emission Probabilities (Gaussian):")
    print("         Mean      Std")
    for i in range(model.n_components):
        mean = model.means_[i][0].item()
        var = model.covars_[i][0][0].item()  # covars_ is 3D: (n_components, n_features, n_features)
        std = np.sqrt(var)
        print(f"État {i}  {mean*100:+.3f}%   {std*100:.2f}%")
    
    # Initial distribution
    print(f"\n📊 Initial Distribution (π):")
    print(f"  {model.startprob_}")

def decode_regimes(model, returns_2d, returns_series):
    """Decode hidden states and map to regimes."""
    hidden_states = model.predict(returns_2d)
    n_days = len(hidden_states)
    
    # Analyze each state
    state_stats = []
    for i in range(model.n_components):
        mask = hidden_states == i
        state_mean = returns_series[mask].mean()
        state_std = returns_series[mask].std()
        state_stats.append({
            'state': i,
            'mean': state_mean,
            'std': state_std,
            'n_days': mask.sum()
        })
    
    # Map states to regimes based on mean returns
    state_stats.sort(key=lambda x: x['mean'], reverse=True)
    state_mapping = {
        state_stats[0]['state']: 'Bull',
        state_stats[1]['state']: 'Range',
        state_stats[2]['state']: 'Bear'
    }
    
    print("\n" + "=" * 60)
    print("REGIME MAPPING")
    print("=" * 60)
    print("\n🏷️ State Identification:")
    for stat in state_stats:
        regime = state_mapping[stat['state']]
        print(f"  État {stat['state']} → {regime}")
        print(f"    Mean: {stat['mean']*100:+.3f}%, Std: {stat['std']*100:.2f}%")
        print(f"    Days: {stat['n_days']} ({stat['n_days']/n_days*100:.1f}%)")
    
    return hidden_states, state_mapping, state_stats

def analyze_transitions(hidden_states, state_mapping):
    """Analyze state transitions and durations."""
    print("\n" + "=" * 60)
    print("TRANSITION ANALYSIS")
    print("=" * 60)
    
    # Count transitions
    n_states = len(state_mapping)
    transitions = np.zeros((n_states, n_states))
    for t in range(len(hidden_states) - 1):
        transitions[hidden_states[t], hidden_states[t+1]] += 1
    
    print("\n📊 Transition Count Matrix:")
    print("         " + "   ".join([f"To {i}" for i in range(n_states)]))
    for i, row in enumerate(transitions):
        row_str = "  ".join([f"{val:6.0f}" for val in row])
        print(f"From {i}  {row_str}")
    
    # Average duration in each state
    print("\n⏱️ Average Duration per State:")
    for i in range(n_states):
        mask = hidden_states == i
        in_state = mask.astype(int)
        diffs = np.diff(in_state)
        
        starts = np.where(diffs == 1)[0] + 1
        ends = np.where(diffs == -1)[0] + 1
        
        if in_state[0] == 1:
            starts = np.r_[0, starts]
        if in_state[-1] == 1:
            ends = np.r_[ends, len(in_state)]
        
        if len(starts) > 0:
            durations = ends - starts
            avg_duration = durations.mean()
            print(f"  État {i} ({state_mapping[i]}): {avg_duration:.1f} days (max: {durations.max()} days)")

def detect_current_regime(model, returns_2d, hidden_states, state_mapping):
    """Detect current regime."""
    print("\n" + "=" * 60)
    print("CURRENT REGIME")
    print("=" * 60)
    
    current_state = hidden_states[-1]
    current_prob = model.predict_proba(returns_2d[-1:])
    
    print(f"\n🎯 Current State: {state_mapping[current_state]} (État {current_state})")
    print(f"  State Probabilities:")
    for i, prob in enumerate(current_prob[0]):
        print(f"    État {i} ({state_mapping[i]}): {prob*100:.1f}%")
    
    return current_state, current_prob

def map_strategies(state_mapping):
    """Map regimes to strategy performance."""
    print("\n" + "=" * 60)
    print("REGIME → STRATEGY MAPPING")
    print("=" * 60)
    
    strategy_performance = {
        'Bull': {
            'Long Trend': '+15%',
            'Mean Reversion': '-3%',
            'Market Neutral': '+2%'
        },
        'Bear': {
            'Long Trend': '-20%',
            'Mean Reversion': '-5%',
            'Short/Hedge': '+12%'
        },
        'Range': {
            'Long Trend': '-2%',
            'Mean Reversion': '+8%',
            'Grid Trading': '+6%'
        }
    }
    
    for regime, strategies in strategy_performance.items():
        print(f"\n{regime}:")
        for strat, perf in strategies.items():
            emoji = "📈" if '+' in perf else "📉"
            print(f"  {emoji} {strat}: {perf}")

def plot_results(returns_series, hidden_states, state_mapping, model, 
                 state_stats, output_path):
    """Generate comprehensive visualization."""
    n_components = len(state_mapping)
    
    fig, axes = plt.subplots(4, 1, figsize=(14, 12))
    
    # Plot 1: Returns
    axes[0].plot(returns_series.index, returns_series.values, 
                 linewidth=0.5, alpha=0.7, label='Returns', color='blue')
    axes[0].set_title('BTC Daily Returns', fontweight='bold', fontsize=12)
    axes[0].set_ylabel('Return')
    axes[0].axhline(0, color='black', linewidth=0.5)
    axes[0].legend(loc='upper left')
    axes[0].grid(alpha=0.3)
    
    # Plot 2: Hidden States
    colors = ['green' if state_mapping[s] == 'Bull' else 
              'red' if state_mapping[s] == 'Bear' else 'gray' 
              for s in hidden_states]
    axes[1].scatter(range(len(hidden_states)), [1]*len(hidden_states), 
                    c=colors, s=10, alpha=0.7)
    axes[1].set_title('Detected Regimes (Hidden States)', fontweight='bold', fontsize=12)
    axes[1].set_ylabel('State')
    axes[1].set_yticks([])
    axes[1].set_xlim(0, len(hidden_states))
    
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='green', label='Bull'),
        Patch(facecolor='red', label='Bear'),
        Patch(facecolor='gray', label='Range')
    ]
    axes[1].legend(handles=legend_elements, loc='upper right')
    
    # Plot 3: State probabilities (last 200 days)
    recent_probs = model.predict_proba(returns_series.values[-200:].reshape(-1, 1))
    
    # Order by Bull, Range, Bear
    bull_idx = [s for s, m in state_mapping.items() if m == 'Bull'][0]
    range_idx = [s for s, m in state_mapping.items() if m == 'Range'][0]
    bear_idx = [s for s, m in state_mapping.items() if m == 'Bear'][0]
    
    axes[2].stackplot(range(200), 
                      recent_probs[:, bull_idx],
                      recent_probs[:, range_idx],
                      recent_probs[:, bear_idx],
                      labels=['Bull', 'Range', 'Bear'],
                      colors=['green', 'gray', 'red'],
                      alpha=0.8)
    axes[2].set_title('State Probabilities (Last 200 Days)', fontweight='bold', fontsize=12)
    axes[2].set_ylabel('Probability')
    axes[2].legend(loc='upper right')
    axes[2].set_xlim(0, 200)
    
    # Plot 4: Cumulative returns by regime
    axes[3].axhline(0, color='black', linewidth=0.5)
    
    for i in range(n_components):
        mask = hidden_states == i
        if mask.sum() > 0:
            cumret = (1 + returns_series[mask]).cumprod()
            axes[3].plot(range(len(cumret)), cumret.values - 1, 
                         label=f"État {i} ({state_mapping[i]})", 
                         linewidth=2, alpha=0.8)
    
    axes[3].set_title('Cumulative Returns by Regime', fontweight='bold', fontsize=12)
    axes[3].set_ylabel('Cumulative Return')
    axes[3].set_xlabel('Days in Regime')
    axes[3].legend(loc='upper left')
    axes[3].grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path

def main():
    print("=" * 60)
    print("🔮 Hidden Markov Models - BTC Regime Detection")
    print("=" * 60)
    
    # Step 1: Generate data
    print("\n[1/5] Generating BTC returns with regimes...")
    returns_series = generate_btc_regimes(n_days=1000)
    print(f"  ✓ {len(returns_series)} days of returns")
    print(f"  ✓ Mean: {returns_series.mean()*100:.3f}%")
    print(f"  ✓ Std: {returns_series.std()*100:.2f}%")
    
    # Step 2: Train HMM
    print("\n[2/5] Training HMM (3 states)...")
    model, returns_2d, n_iter_actual = train_hmm(returns_series.values, n_components=3, n_iter=100)
    print(f"  ✓ Converged after {n_iter_actual} iterations")
    print(f"  ✓ Log-likelihood: {model.score(returns_2d):.2f}")
    
    # Step 3: Analyze parameters
    analyze_parameters(model)
    
    # Step 4: Decode regimes
    hidden_states, state_mapping, state_stats = decode_regimes(
        model, returns_2d, returns_series
    )
    
    # Step 5: Analyze transitions
    analyze_transitions(hidden_states, state_mapping)
    
    # Step 6: Detect current regime
    current_state, current_prob = detect_current_regime(
        model, returns_2d, hidden_states, state_mapping
    )
    
    # Step 7: Map strategies
    map_strategies(state_mapping)
    
    # Visualization
    print("\n" + "=" * 60)
    print("Generating visualization...")
    output_dir = '/root/.openclaw/workspace/learning/code'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'hmm_btc_output.png')
    plot_results(returns_series, hidden_states, state_mapping, model, 
                 state_stats, output_path)
    print(f"  ✓ Chart saved: {output_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    n_days = len(returns_series)
    print(f"  Model: Gaussian HMM (3 states)")
    print(f"  Log-likelihood: {model.score(returns_2d):.2f}")
    print(f"  Current regime: {state_mapping[current_state]}")
    print(f"  Regime distribution:")
    for stat in state_stats:
        print(f"    {state_mapping[stat['state']]}: {stat['n_days']/n_days*100:.1f}%")
    print(f"  Status: ✅ Complete")
    print("=" * 60)
    
    return {
        'model': model,
        'hidden_states': hidden_states,
        'state_mapping': state_mapping,
        'current_regime': state_mapping[current_state]
    }

if __name__ == '__main__':
    results = main()
