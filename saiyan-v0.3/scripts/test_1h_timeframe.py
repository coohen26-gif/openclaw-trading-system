#!/usr/bin/env python3
"""
Test stratégies sur timeframe 1H (plus de trades)
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.gates_bailey import GatesBailey

# Charger données 1h
df = pd.read_csv('/root/.openclaw/workspace/saiyan-v0.3/data/btc_usdt_1h_fresh.csv')

print("="*80)
print("🧪 TEST STRATÉGIES 1H TIMEFRAME - SAIYAN V0.3")
print("="*80)

print(f"\n📊 DONNÉES")
print(f"   Range: {df['date'].iloc[0]} → {df['date'].iloc[-1]}")
print(f"   N candles: {len(df)}")

# Returns
df['return'] = df['close'].pct_change()
df = df.dropna()

# RSI
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

df['rsi'] = calculate_rsi(df['close'], period=14)

# BB
df['bb_mid'] = df['close'].rolling(20).mean()
df['bb_std'] = df['close'].rolling(20).std()
df['bb_upper'] = df['bb_mid'] + 2.5 * df['bb_std']
df['bb_lower'] = df['bb_mid'] - 2.5 * df['bb_std']

# Frais (mêmes 0.22%)
FEE_PCT = 0.0022

print(f"\n{'='*80}")
print("📈 STRATÉGIE: BB WALK (2.5σ) + VOLUME FILTER")
print(f"{'='*80}")

# Volume filter
df['volume_ma20'] = df['volume'].rolling(20).mean()

strat_df = df.copy()
strat_df['signal'] = 0
# LONG si prix < BB lower ET volume > MA
long_cond = (strat_df['close'] < strat_df['bb_lower']) & (strat_df['volume'] > strat_df['volume_ma20'])
strat_df.loc[long_cond, 'signal'] = 1
# SHORT si prix > BB upper ET volume > MA
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
    
    if trades['net_return'].std() > 0:
        sharpe = (trades['net_return'].mean() * 252 * 24) / (trades['net_return'].std() * np.sqrt(252 * 24))
    else:
        sharpe = 0
    
    # Gates Bailey
    gates = GatesBailey()
    returns_array = trades['net_return'].values
    dsr = gates.deflated_sharpe_ratio(returns_array, n_trials=1)
    psr = gates.probability_sharpe_ratio(returns_array, sr_benchmark=0.0)
    wilson = gates.wilson_score_interval(n_wins, n_trades)
    
    print(f"   N trades:      {n_trades}")
    print(f"   WR:            {wr:.1%} ({n_wins}W/{n_trades-n_wins}L)")
    print(f"   Return net:    {total_return:.2%}")
    print(f"   Sharpe:        {sharpe:.3f}")
    print(f"   Fees totaux:   ${trades['fee'].sum()*100:.2f}%" if 'fee' in trades.columns else "")
    print(f"\n   GATES BAILEY:")
    print(f"      DSR:  {dsr['dsr']:.3f} (p={dsr['p_value']:.4f}) {'✅ PASS' if dsr['passed'] else '❌ FAIL'}")
    print(f"      PSR:  {psr['psr']:.3f} {'✅ PASS' if psr['passed'] else '❌ FAIL'}")
    print(f"      WILSON: {wilson['wr_observed']:.1%} CI=[{wilson['wr_lower']:.1%}, {wilson['wr_upper']:.1%}] {'✅ PASS' if wilson['passed'] else '❌ FAIL'}")
    
    # Distribution P&L
    avg_win = trades[trades['net_return'] > 0]['net_return'].mean()
    avg_loss = trades[trades['net_return'] <= 0]['net_return'].mean()
    
    print(f"\n   DISTRIBUTION P&L:")
    print(f"      Avg Win:   {avg_win:.4f} ({avg_win*100:.2f}%)")
    print(f"      Avg Loss:  {avg_loss:.4f} ({avg_loss*100:.2f}%)")
    print(f"      Ratio:     {abs(avg_win/avg_loss):.2f}x" if avg_loss != 0 else "N/A")

print(f"\n{'='*80}")
print("💡 CONCLUSION")
print(f"{'='*80}")

if wr >= 0.70 and wilson['passed']:
    print(f"\n🎉 STRATÉGIE VALIDE ! WR {wr:.1%} passe Wilson Gate")
    print(f"   → Prête pour Shadow Mode paper-deploy")
elif wr >= 0.60:
    print(f"\n🟡 PROCHE DU BUT ! WR {wr:.1%}")
    print(f"   → Optimiser thresholds pour gagner quelques %")
    print(f"   → Ajouter filtre HMM pour éviter faux signaux")
else:
    print(f"\n🔴 WR {wr:.1%} INSUFFISANT")
    print(f"   → Tester autres stratégies (momentum, arbitrage)")
    print(f"   → Explorer multi-asset (ETH, SOL)")
    print(f"   → Timeframe inférieur (15min) ?")
