#!/usr/bin/env python3
"""
Analyse approfondie du backtest v0.3 - Pourquoi WR=33% ?

Objectif: Comprendre pourquoi le backtest a échoué et identifier les fixes
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.gates_bailey import GatesBailey

# Charger données fraîches
data_path = Path('/root/.openclaw/workspace/saiyan-v0.3/data/btc_usdt_fresh_2026-05-28.csv')
df = pd.read_csv(data_path)

print("="*70)
print("🔍 ANALYSE BACKTEST SAIYAN V0.3 - POURQUOI WR=33% ?")
print("="*70)

print(f"\n📊 DONNÉES FRAÎCHES")
print(f"   Range: {df['date'].iloc[0]} → {df['date'].iloc[-1]}")
print(f"   N jours: {len(df)}")
print(f"   Prix actuel: ${df['close'].iloc[-1]:.2f}")

# Calculer returns daily
df['return'] = df['close'].pct_change()
df = df.dropna()

print(f"\n📈 STATISTIQUES RETURNS")
print(f"   Mean daily:   {df['return'].mean():.4f} ({df['return'].mean()*100:.2f}%)")
print(f"   Std daily:    {df['return'].std():.4f} ({df['return'].std()*100:.2f}%)")
print(f"   Skewness:     {df['return'].skew():.3f}")
print(f"   Kurtosis:     {df['return'].kurtosis():.3f}")
print(f"   Min return:   {df['return'].min():.4f} ({df['return'].min()*100:.2f}%)")
print(f"   Max return:   {df['return'].max():.4f} ({df['return'].max()*100:.2f}%)")

# Sharpe Ratio annualisé
sharpe = (df['return'].mean() * 252) / (df['return'].std() * np.sqrt(252))
print(f"\n💹 SHARPE RATIO (Buy&Hold): {sharpe:.3f}")

# Buy & Hold performance
buy_hold_return = (df['close'].iloc[-1] / df['close'].iloc[0]) - 1
print(f"💰 BUY & HOLD: {buy_hold_return:.2%} sur {len(df)} jours")

# Simulation stratégie simple (mean reversion RSI)
print(f"\n" + "="*70)
print("🧪 SIMULATION STRATÉGIE MEAN REVERSION (RSI)")
print("="*70)

# Calcul RSI
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

df['rsi'] = calculate_rsi(df['close'], period=14)

# Signaux: RSI < 30 → LONG, RSI > 70 → SHORT
df['signal'] = 0
df.loc[df['rsi'] < 30, 'signal'] = 1  # LONG
df.loc[df['rsi'] > 70, 'signal'] = -1  # SHORT

# Shift signal pour éviter lookahead bias (signal today → trade tomorrow)
df['signal_shifted'] = df['signal'].shift(1)

# Returns stratégie
df['strategy_return'] = df['signal_shifted'] * df['return']

# Filtrer seulement les jours avec position
trades_df = df[df['signal_shifted'] != 0].copy()

print(f"\n📊 SIGNAUX GÉNÉRÉS")
print(f"   Total signaux: {len(trades_df)}")
print(f"   LONG (RSI<30):  {(trades_df['signal_shifted']==1).sum()}")
print(f"   SHORT (RSI>70): {(trades_df['signal_shifted']==-1).sum()}")

# Win Rate
winning_trades = trades_df[trades_df['strategy_return'] > 0]
wr = len(winning_trades) / len(trades_df) if len(trades_df) > 0 else 0

print(f"\n🎯 WIN RATE")
print(f"   Wins:  {len(winning_trades)}")
print(f"   Losses: {len(trades_df) - len(winning_trades)}")
print(f"   WR:    {wr:.1%}")

# Sharpe Ratio stratégie
if len(trades_df) > 0 and trades_df['strategy_return'].std() > 0:
    strategy_sharpe = (trades_df['strategy_return'].mean() * 252) / (trades_df['strategy_return'].std() * np.sqrt(252))
else:
    strategy_sharpe = 0

print(f"\n💹 SHARPE RATIO (Stratégie): {strategy_sharpe:.3f}")

# Return cumulé
cumulative_return = (1 + trades_df['strategy_return']).prod() - 1
print(f"💰 RETURN CUMULÉ: {cumulative_return:.2%}")

# Gates Bailey
print(f"\n" + "="*70)
print("🚪 GATES BAILEY VALIDATION")
print("="*70)

gates = GatesBailey()

returns_array = trades_df['strategy_return'].values if len(trades_df) > 0 else np.array([])

if len(returns_array) > 0:
    # DSR
    dsr_result = gates.deflated_sharpe_ratio(returns_array, n_trials=1)
    print(f"\nDSR: {dsr_result['dsr']:.3f} (p-value: {dsr_result['p_value']:.4f}) {'✅ PASS' if dsr_result['passed'] else '❌ FAIL'}")
    
    # PSR
    psr_result = gates.probability_sharpe_ratio(returns_array, sr_benchmark=0.0)
    print(f"PSR: {psr_result['psr']:.3f} {'✅ PASS' if psr_result['passed'] else '❌ FAIL'}")
    
    # Wilson Score
    n_wins = len(winning_trades)
    n_trades = len(trades_df)
    wilson_result = gates.wilson_score_interval(n_wins, n_trades)
    print(f"WILSON: WR={wilson_result['wr_observed']:.1%}, CI95=[{wilson_result['wr_lower']:.1%}, {wilson_result['wr_upper']:.1%}] {'✅ PASS' if wilson_result['passed'] else '❌ FAIL'}")
else:
    print("⚠️  Pas assez de trades pour validation Gates")

# Diagnostic
print(f"\n" + "="*70)
print("🔍 DIAGNOSTIC ROOT CAUSE")
print("="*70)

if wr < 0.50:
    print(f"\n⚠️  PROBLÈME: WR {wr:.1%} < 50% (pire que coin flip)")
    print(f"\nCauses possibles:")
    print(f"   1. Stratégie mean reversion inadaptée au régime actuel")
    print(f"   2. Thresholds RSI (30/70) trop stricts ou trop lâches")
    print(f"   3. Pas de filtre de régime (HMM) pour éviter trades en trend fort")
    print(f"   4. Frais de trading non-inclus (0.22% round-trip)")
    
    # Analyser distribution des gains/pertes
    if len(trades_df) > 0:
        avg_win = winning_trades['strategy_return'].mean() if len(winning_trades) > 0 else 0
        losing_trades = trades_df[trades_df['strategy_return'] <= 0]
        avg_loss = losing_trades['strategy_return'].mean() if len(losing_trades) > 0 else 0
        
        print(f"\n📊 DISTRIBUTION P&L:")
        print(f"   Avg Win:  {avg_win:.4f} ({avg_win*100:.2f}%)")
        print(f"   Avg Loss: {avg_loss:.4f} ({avg_loss*100:.2f}%)")
        print(f"   Ratio:    {abs(avg_win / avg_loss):.2f}x" if avg_loss != 0 else "   Ratio: N/A")
        
        if abs(avg_win) < abs(avg_loss):
            print(f"\n⚠️  PROBLÈME: Les gains moyens sont PLUS PETITS que les pertes !")
            print(f"   → Même avec WR 50%, la stratégie perdrait de l'argent")
            print(f"   → Solution: Améliorer le ratio gain/perte ou augmenter WR")

if sharpe > strategy_sharpe:
    print(f"\n⚠️  SOUS-PERFORMANCE vs Buy&Hold")
    print(f"   Sharpe B&H: {sharpe:.3f}")
    print(f"   Sharpe Strat: {strategy_sharpe:.3f}")
    print(f"   → La stratégie complique les choses sans améliorer risk-adjusted returns")
    print(f"   → Solution: Simplifier ou changer complètement d'approche")

print(f"\n" + "="*70)
print("💡 RECOMMANDATIONS")
print("="*70)

recommendations = [
    "1. Ajouter filtre HMM: éviter mean reversion en régime trending",
    "2. Optimiser thresholds RSI (backtest grid search 20-80)",
    "3. Inclure frais 0.22% dans le backtest",
    "4. Tester autres stratégies: momentum breakout, BB walk",
    "5. Position sizing adaptif (Kelly ou fractionnaire)",
    "6. Stop-loss dynamique pour limiter les grosses pertes"
]

for rec in recommendations:
    print(f"   ✅ {rec}")

print(f"\n" + "="*70)
