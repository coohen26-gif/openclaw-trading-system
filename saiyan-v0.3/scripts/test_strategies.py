#!/usr/bin/env python3
"""
Test multiple stratégies pour trouver celle qui passe les Gates Bailey
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.gates_bailey import GatesBailey

# Charger données combinées
old_df = pd.read_csv('/root/.openclaw/workspace/system-saiyan/v0.2/data/btc_realistic_2020_2026.csv')
fresh_df = pd.read_csv('/root/.openclaw/workspace/saiyan-v0.3/data/btc_usdt_fresh_2026-05-28.csv')

old_df = old_df.rename(columns={'Unnamed: 0': 'timestamp'})
old_df['date'] = pd.to_datetime(old_df['timestamp']).dt.strftime('%Y-%m-%d')

fresh_dates = set(fresh_df['date'])
old_filtered = old_df[~old_df['date'].isin(fresh_dates)]

df = pd.concat([old_filtered[['date', 'open', 'high', 'low', 'close', 'volume']], fresh_df], ignore_index=True)
df = df.sort_values('date').reset_index(drop=True)

# Calculer returns et indicateurs
df['return'] = df['close'].pct_change()
df = df.dropna()

# Moving averages
df['ma20'] = df['close'].rolling(20).mean()
df['ma50'] = df['close'].rolling(50).mean()
df['ma200'] = df['close'].rolling(200).mean()

# Bollinger Bands
df['bb_mid'] = df['close'].rolling(20).mean()
df['bb_std'] = df['close'].rolling(20).std()
df['bb_upper'] = df['bb_mid'] + 2 * df['bb_std']
df['bb_lower'] = df['bb_mid'] - 2 * df['bb_std']

# RSI
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

df['rsi'] = calculate_rsi(df['close'], period=14)

# Momentum
df['momentum_10'] = df['close'].pct_change(10)
df['momentum_20'] = df['close'].pct_change(20)

FEE_PCT = 0.0022

print("="*80)
print("🧪 TEST MULTI-STRATÉGIES - SAIYAN V0.3")
print("="*80)

strategies_results = []

# =============================================================================
# STRATÉGIE 1: Momentum Breakout
# =============================================================================
print("\n📈 STRATÉGIE 1: MOMENTUM BREAKOUT")
strat_df = df.copy()
strat_df['signal'] = 0
strat_df.loc[strat_df['momentum_10'] > 0.05, 'signal'] = 1  # LONG si momentum fort
strat_df.loc[strat_df['momentum_10'] < -0.05, 'signal'] = -1  # SHORT si momentum négatif fort
strat_df['signal_shifted'] = strat_df['signal'].shift(1)
strat_df['net_return'] = (strat_df['signal_shifted'] * strat_df['return']) - np.where(strat_df['signal_shifted'] != 0, FEE_PCT, 0)

trades = strat_df[strat_df['signal_shifted'] != 0]
if len(trades) > 0:
    n_trades = len(trades)
    n_wins = len(trades[trades['net_return'] > 0])
    wr = n_wins / n_trades
    total_return = (1 + trades['net_return']).prod() - 1
    sharpe = (trades['net_return'].mean() * 252) / (trades['net_return'].std() * np.sqrt(252)) if trades['net_return'].std() > 0 else 0
    
    gates = GatesBailey()
    wilson = gates.wilson_score_interval(n_wins, n_trades)
    
    print(f"   N trades:   {n_trades}")
    print(f"   WR:         {wr:.1%}")
    print(f"   Return:     {total_return:.2%}")
    print(f"   Sharpe:     {sharpe:.3f}")
    print(f"   Wilson:     {wilson['wr_lower']:.1%} (min requis: 50%) {'✅' if wilson['passed'] else '❌'}")
    
    strategies_results.append(('Momentum Breakout', wr, total_return, sharpe, wilson['passed']))

# =============================================================================
# STRATÉGIE 2: Trend Following (MA Crossover)
# =============================================================================
print("\n📈 STRATÉGIE 2: TREND FOLLOWING (MA CROSSOVER)")
strat_df = df.copy()
strat_df['signal'] = 0
strat_df.loc[strat_df['ma20'] > strat_df['ma50'], 'signal'] = 1  # LONG si MA20 > MA50
strat_df.loc[strat_df['ma20'] < strat_df['ma50'], 'signal'] = -1  # SHORT si MA20 < MA50
strat_df['signal_shifted'] = strat_df['signal'].shift(1)
strat_df['net_return'] = (strat_df['signal_shifted'] * strat_df['return']) - np.where(strat_df['signal_shifted'] != 0, FEE_PCT, 0)

trades = strat_df[strat_df['signal_shifted'] != 0]
if len(trades) > 0:
    n_trades = len(trades)
    n_wins = len(trades[trades['net_return'] > 0])
    wr = n_wins / n_trades
    total_return = (1 + trades['net_return']).prod() - 1
    sharpe = (trades['net_return'].mean() * 252) / (trades['net_return'].std() * np.sqrt(252)) if trades['net_return'].std() > 0 else 0
    
    gates = GatesBailey()
    wilson = gates.wilson_score_interval(n_wins, n_trades)
    
    print(f"   N trades:   {n_trades}")
    print(f"   WR:         {wr:.1%}")
    print(f"   Return:     {total_return:.2%}")
    print(f"   Sharpe:     {sharpe:.3f}")
    print(f"   Wilson:     {wilson['wr_lower']:.1%} (min requis: 50%) {'✅' if wilson['passed'] else '❌'}")
    
    strategies_results.append(('Trend Following MA', wr, total_return, sharpe, wilson['passed']))

# =============================================================================
# STRATÉGIE 3: Bollinger Bands Mean Reversion (avec filtre volume)
# =============================================================================
print("\n📈 STRATÉGIE 3: BOLLINGER BANDS MEAN REVERSION + VOLUME")
strat_df = df.copy()
strat_df['volume_ma20'] = strat_df['volume'].rolling(20).mean()
strat_df['signal'] = 0
# LONG si prix < BB lower ET volume > MA20
long_cond = (strat_df['close'] < strat_df['bb_lower']) & (strat_df['volume'] > strat_df['volume_ma20'])
strat_df.loc[long_cond, 'signal'] = 1
# SHORT si prix > BB upper ET volume > MA20
short_cond = (strat_df['close'] > strat_df['bb_upper']) & (strat_df['volume'] > strat_df['volume_ma20'])
strat_df.loc[short_cond, 'signal'] = -1
strat_df['signal_shifted'] = strat_df['signal'].shift(1)
strat_df['net_return'] = (strat_df['signal_shifted'] * strat_df['return']) - np.where(strat_df['signal_shifted'] != 0, FEE_PCT, 0)

trades = strat_df[strat_df['signal_shifted'] != 0]
if len(trades) > 0:
    n_trades = len(trades)
    n_wins = len(trades[trades['net_return'] > 0])
    wr = n_wins / n_trades
    total_return = (1 + trades['net_return']).prod() - 1
    sharpe = (trades['net_return'].mean() * 252) / (trades['net_return'].std() * np.sqrt(252)) if trades['net_return'].std() > 0 else 0
    
    gates = GatesBailey()
    wilson = gates.wilson_score_interval(n_wins, n_trades)
    
    print(f"   N trades:   {n_trades}")
    print(f"   WR:         {wr:.1%}")
    print(f"   Return:     {total_return:.2%}")
    print(f"   Sharpe:     {sharpe:.3f}")
    print(f"   Wilson:     {wilson['wr_lower']:.1%} (min requis: 50%) {'✅' if wilson['passed'] else '❌'}")
    
    strategies_results.append(('BB Mean Rev + Vol', wr, total_return, sharpe, wilson['passed']))

# =============================================================================
# STRATÉGIE 4: HMM Regime Filter + Momentum (simulé)
# =============================================================================
print("\n📈 STRATÉGIE 4: HMM REGIME FILTER + MOMENTUM (SIMULÉ)")
# Simulation: on utilise volatilité comme proxy de régime HMM
strat_df = df.copy()
strat_df['volatility'] = strat_df['return'].rolling(20).std()
vol_median = strat_df['volatility'].median()

strat_df['signal'] = 0
# LONG seulement en low vol + momentum positif
long_cond = (strat_df['volatility'] < vol_median) & (strat_df['momentum_10'] > 0.03)
strat_df.loc[long_cond, 'signal'] = 1
# FLAT en high vol (on évite les trades)
strat_df['signal_shifted'] = strat_df['signal'].shift(1)
strat_df['net_return'] = (strat_df['signal_shifted'] * strat_df['return']) - np.where(strat_df['signal_shifted'] != 0, FEE_PCT, 0)

trades = strat_df[strat_df['signal_shifted'] != 0]
if len(trades) > 0:
    n_trades = len(trades)
    n_wins = len(trades[trades['net_return'] > 0])
    wr = n_wins / n_trades
    total_return = (1 + trades['net_return']).prod() - 1
    sharpe = (trades['net_return'].mean() * 252) / (trades['net_return'].std() * np.sqrt(252)) if trades['net_return'].std() > 0 else 0
    
    gates = GatesBailey()
    wilson = gates.wilson_score_interval(n_wins, n_trades)
    
    print(f"   N trades:   {n_trades}")
    print(f"   WR:         {wr:.1%}")
    print(f"   Return:     {total_return:.2%}")
    print(f"   Sharpe:     {sharpe:.3f}")
    print(f"   Wilson:     {wilson['wr_lower']:.1%} (min requis: 50%) {'✅' if wilson['passed'] else '❌'}")
    
    strategies_results.append(('HMM Filter + Mom', wr, total_return, sharpe, wilson['passed']))

# =============================================================================
# RÉSULTATS COMPARATIFS
# =============================================================================
print("\n" + "="*80)
print("🏆 CLASSEMENT DES STRATÉGIES")
print("="*80)

results_df = pd.DataFrame(strategies_results, columns=['Stratégie', 'WR', 'Return', 'Sharpe', 'Wilson_Pass'])
results_df = results_df.sort_values('WR', ascending=False)

for idx, row in results_df.iterrows():
    status = "✅" if row['Wilson_Pass'] else "❌"
    print(f"{status} {row['Stratégie']:25s} | WR: {row['WR']:5.1%} | Return: {row['Return']:7.2%} | Sharpe: {row['Sharpe']:6.3f}")

best_strategy = results_df.iloc[0]
print(f"\n💡 MEILLEURE STRATÉGIE: {best_strategy['Stratégie']}")
print(f"   WR: {best_strategy['WR']:.1%}, Return: {best_strategy['Return']:.2%}, Sharpe: {best_strategy['Sharpe']:.3f}")

if not best_strategy['Wilson_Pass']:
    print(f"\n⚠️  AUCUNE STRATÉGIE NE PASSE WILSON !")
    print(f"   → Besoin de plus de trades OU meilleure WR")
    print(f"   → Explorer: multi-asset, timeframe inférieur, autres stratégies")
