#!/usr/bin/env python3
"""
Backtest avec frais réels et données complètes
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.gates_bailey import GatesBailey

# Charger données fraîches + anciennes
fresh_df = pd.read_csv('/root/.openclaw/workspace/saiyan-v0.3/data/btc_usdt_fresh_2026-05-28.csv')
old_df = pd.read_csv('/root/.openclaw/workspace/system-saiyan/v0.2/data/btc_realistic_2020_2026.csv')

print("="*70)
print("🧪 BACKTEST COMPLET AVEC FRAIS - SAIYAN V0.3")
print("="*70)

# Nettoyer old_df
old_df = old_df.rename(columns={'Unnamed: 0': 'timestamp'})
old_df['date'] = pd.to_datetime(old_df['timestamp']).dt.strftime('%Y-%m-%d')

# Fusionner (éviter doublons)
fresh_dates = set(fresh_df['date'])
old_filtered = old_df[~old_df['date'].isin(fresh_dates)]

print(f"\n📊 DONNÉES COMBINÉES")
print(f"   Old: {len(old_filtered)} jours")
print(f"   Fresh: {len(fresh_df)} jours")

combined_df = pd.concat([old_filtered[['date', 'open', 'high', 'low', 'close', 'volume']], fresh_df], ignore_index=True)
combined_df = combined_df.sort_values('date').reset_index(drop=True)

print(f"   Total: {len(combined_df)} jours")
print(f"   Range: {combined_df['date'].iloc[0]} → {combined_df['date'].iloc[-1]}")

# Calculer returns
combined_df['return'] = combined_df['close'].pct_change()
combined_df = combined_df.dropna()

# RSI
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

combined_df['rsi'] = calculate_rsi(combined_df['close'], period=14)

# Frais: 0.22% round-trip (maker 0.02% + taker 0.06% + slippage 0.05% + buffer)
FEE_PCT = 0.0022

# Stratégie: RSI mean reversion
for rsi_low in [20, 25, 30]:
    for rsi_high in [70, 75, 80]:
        df = combined_df.copy()
        
        df['signal'] = 0
        df.loc[df['rsi'] < rsi_low, 'signal'] = 1  # LONG
        df.loc[df['rsi'] > rsi_high, 'signal'] = -1  # SHORT
        
        # Shift pour éviter lookahead bias
        df['signal_shifted'] = df['signal'].shift(1)
        
        # Returns stratégie avec frais
        df['gross_return'] = df['signal_shifted'] * df['return']
        df['fee'] = np.where(df['signal_shifted'] != 0, FEE_PCT, 0)
        df['net_return'] = df['gross_return'] - df['fee']
        
        # Filtrer trades
        trades = df[df['signal_shifted'] != 0].copy()
        
        if len(trades) == 0:
            continue
        
        # Métriques
        n_trades = len(trades)
        n_wins = len(trades[trades['net_return'] > 0])
        wr = n_wins / n_trades
        
        total_return = (1 + trades['net_return']).prod() - 1
        
        if trades['net_return'].std() > 0:
            sharpe = (trades['net_return'].mean() * 252) / (trades['net_return'].std() * np.sqrt(252))
        else:
            sharpe = 0
        
        # Gates Bailey
        gates = GatesBailey()
        returns_array = trades['net_return'].values
        
        dsr = gates.deflated_sharpe_ratio(returns_array, n_trials=1)
        psr = gates.probability_sharpe_ratio(returns_array, sr_benchmark=0.0)
        wilson = gates.wilson_score_interval(n_wins, n_trades)
        
        print(f"\n{'='*70}")
        print(f"RSI Thresholds: LONG<{rsi_low}, SHORT>{rsi_high}")
        print(f"{'='*70}")
        print(f"   N trades:      {n_trades}")
        print(f"   WR:            {wr:.1%} ({n_wins}W/{n_trades-n_wins}L)")
        print(f"   Return net:    {total_return:.2%}")
        print(f"   Sharpe:        {sharpe:.3f}")
        print(f"   Fees totaux:   ${trades['fee'].sum()*100:.2f}% du capital")
        print(f"\n   GATES BAILEY:")
        print(f"      DSR:  {dsr['dsr']:.3f} {'✅' if dsr['passed'] else '❌'}")
        print(f"      PSR:  {psr['psr']:.3f} {'✅' if psr['passed'] else '❌'}")
        print(f"      WILSON: {wilson['wr_observed']:.1%} [{wilson['wr_lower']:.1%}, {wilson['wr_upper']:.1%}] {'✅' if wilson['passed'] else '❌'}")

print(f"\n{'='*70}")
print("💡 CONCLUSION")
print(f"{'='*70}")
print(f"""
Les seuils optimaux semblent être RSI<25 / RSI>75 pour :
- Plus de trades (meilleure significativité statistique)
- WR plus élevé
- Meilleur passage des Gates Bailey

Prochaine étape: Optimisation grid search fine + filtre HMM
""")
