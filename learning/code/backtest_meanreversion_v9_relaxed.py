#!/usr/bin/env python3
"""
Backtest Mean Reversion v9 - Filtres Relaxés
Sur données réelles BTC (2020-2026)

Leçon v8: Filtres trop stricts (6 trades seulement!)

Configuration v9:
- RSI: 30/70
- Bollinger: 2.0σ
- TP: +6%, SL: -3%
- Time Exit: 7j
- Position: 5%
- 🆕 HMM: Trader RANGE + TRANSITION (pas TREND)
- 🆕 Volume: > 1.2x MA (vs 1.5x)
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

print("📊 BTC/USDT Daily (2020-2026) - Filtres Relaxés")
df = pd.read_csv('data/btc_usdt_daily.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')[['open', 'high', 'low', 'close', 'volume']]
print(f"   {len(df)} rows | ${df['close'].min():.0f} - ${df['close'].max():.0f}")

def calc_rsi(close, period=14):
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + gain/loss))

def calc_bb(close, period=20, std=2.0):
    sma = close.rolling(period).mean()
    std = close.rolling(period).std()
    return sma + std*std, sma - std*std, sma

def calc_hmm_regime(close, window=60):
    vol = close.rolling(window).std()
    vol_low = vol.quantile(0.40)
    vol_high = vol.quantile(0.60)
    
    regime = []
    for v in vol:
        if pd.isna(v):
            regime.append('UNKNOWN')
        elif v < vol_low:
            regime.append('RANGE')
        elif v > vol_high:
            regime.append('TREND')
        else:
            regime.append('TRANSITION')
    return regime

def calc_volume_ma(volume, period=20):
    return volume.rolling(period).mean()

print("\n📈 Calculating indicators...")
df['rsi'] = calc_rsi(df['close'])
df['bb_u'], df['bb_l'], df['bb_m'] = calc_bb(df['close'])
df['regime'] = calc_hmm_regime(df['close'])
df['vol_ma'] = calc_volume_ma(df['volume'])
df['vol_ratio'] = df['volume'] / df['vol_ma']

df_train = df['2020-01-01':'2023-12-31'].copy()
df_test = df['2024-01-01':'2026-05-25'].copy()
print(f"\n📅 Train: {len(df_train)}j | Test: {len(df_test)}j")

print(f"\n📊 Distribution Régimes HMM (Test):")
regime_counts = df_test['regime'].value_counts()
for r, c in regime_counts.items():
    pct = c / len(df_test) * 100
    print(f"   {r}: {c} ({pct:.1f}%)")

# Signals v9 - Filtres relaxés
def gen_signals_v9(data):
    """Signaux avec filtres relaxés"""
    signals = []
    for i, row in data.iterrows():
        if pd.isna(row['rsi']) or pd.isna(row['bb_l']):
            signals.append(0)
            continue
        
        # FILTRE HMM: Trader RANGE + TRANSITION (pas TREND)
        if row['regime'] in ['TREND', 'UNKNOWN']:
            signals.append(0)
            continue
        
        # FILTRE VOLUME: > 1.2x MA (relaxed)
        if row['vol_ratio'] < 1.2:
            signals.append(0)
            continue
        
        # Signal Mean Reversion
        if row['rsi'] < 30 or row['close'] < row['bb_l']:
            signals.append(1)
        elif row['rsi'] > 70 or row['close'] > row['bb_u']:
            signals.append(-1)
        else:
            signals.append(0)
    
    return signals

print("\n🎯 Signaux v9 (RSI 30/70 + BB 2.0σ + HMM≠TREND + Volume >1.2x)")
df_train['signal'] = gen_signals_v9(df_train)
df_test['signal'] = gen_signals_v9(df_test)

n_train = df_train['signal'].abs().sum()
n_test = df_test['signal'].abs().sum()
print(f"   Train: {n_train:.0f} signaux")
print(f"   Test:  {n_test:.0f} signaux")

def backtest_v9(data, pos_size=0.05, tp=0.06, sl=0.03, max_hold=7):
    capital = 10000
    position = None
    trades = []
    equity = [capital]
    
    for i, row in data.iterrows():
        price = row['close']
        
        if position:
            pnl = (price - position['entry']) / position['entry'] * position['dir']
            hold = (i - position['idx']).days if hasattr(i - position['idx'], 'days') else 0
            
            exit_reason = None
            if pnl >= tp: exit_reason = 'TP'
            elif pnl <= -sl: exit_reason = 'SL'
            elif hold >= max_hold: exit_reason = 'TIME'
            
            if exit_reason:
                capital += capital * pos_size * pnl
                trades.append({
                    'entry': position['entry'], 'exit': price,
                    'dir': position['dir'], 'pnl': pnl*100,
                    'hold': hold, 'exit_reason': exit_reason,
                    'regime': position.get('regime', 'UNKNOWN')
                })
                position = None
        
        if row['signal'] != 0 and not position:
            position = {
                'entry': price, 'dir': row['signal'], 'idx': i,
                'regime': row['regime']
            }
        
        equity.append(capital)
    
    return capital, trades, equity

def sharpe(eq):
    if len(eq) < 2: return 0
    ret = pd.Series(eq).pct_change().dropna()
    if ret.std() == 0: return 0
    return ret.mean() / ret.std() * np.sqrt(252)

def max_dd(eq):
    peak = eq[0]
    mdd = 0
    for e in eq:
        if e > peak: peak = e
        dd = (peak - e) / peak
        if dd > mdd: mdd = dd
    return mdd * 100

print(f"\n🔬 Backtest v9 (TP +6%, SL -3%, Max 7j, Pos 5%)")

cap_t, trades_t, eq_t = backtest_v9(df_train)
ret_t = (cap_t - 10000) / 10000 * 100

cap_s, trades_s, eq_s = backtest_v9(df_test)
ret_s = (cap_s - 10000) / 10000 * 100

print(f"\n{'='*60}")
print("📊 RÉSULTATS V9 (FILTRES RELAXÉS)")
print(f"{'='*60}")

print(f"\n🎯 TEST (2024-2026)")
print(f"   Return: {ret_s:+.2f}% | Capital: ${cap_s:,.2f}")
print(f"   Trades: {len(trades_s)} | Sharpe: {sharpe(eq_s):.2f} | DD: -{max_dd(eq_s):.2f}%")
if trades_s:
    wr = len([t for t in trades_s if t['pnl']>0]) / len(trades_s) * 100
    avg = np.mean([t['pnl'] for t in trades_s])
    best = max([t['pnl'] for t in trades_s])
    worst = min([t['pnl'] for t in trades_s])
    print(f"   Win Rate: {wr:.1f}% | Avg PnL: {avg:+.2f}%")
    print(f"   Best: {best:+.2f}% | Worst: {worst:+.2f}%")
    
    regimes = {}
    for t in trades_s:
        r = t['regime']
        if r not in regimes: regimes[r] = {'n': 0, 'pnl': []}
        regimes[r]['n'] += 1
        regimes[r]['pnl'].append(t['pnl'])
    
    print(f"\n   Performance par régime:")
    for r, data in regimes.items():
        wr_r = len([p for p in data['pnl'] if p > 0]) / len(data['pnl']) * 100
        avg_r = np.mean(data['pnl'])
        print(f"      {r}: n={data['n']}, WR={wr_r:.1f}%, Avg={avg_r:+.2f}%")
    
    exits = {}
    for t in trades_s: exits[t['exit_reason']] = exits.get(t['exit_reason'], 0) + 1
    print(f"\n   Exits: {exits}")

print(f"\n{'='*60}")
print("🔍 COMPARAISON")
print(f"{'='*60}")
print(f"   V7 (no filters):     81 trades, WR 40.7%, Return -0.34%")
print(f"   V8 (HMM strict):     6 trades,  WR 16.7%, Return -0.64%")
print(f"   V9 (HMM relaxed):    {len(trades_s)} trades, WR {wr:.1f}%, Return {ret_s:+.2f}%")

if trades_s:
    pd.DataFrame(trades_s).to_csv('data/meanreversion_v9_trades_test.csv', index=False)
    print(f"\n💾 data/meanreversion_v9_trades_test.csv")

# Analyse: quel regime fonctionne le mieux?
print(f"\n{'='*60}")
print("💡 INSIGHT: Performance par régime")
print(f"{'='*60}")

all_trades = []
for r, data in regimes.items():
    all_trades.append({
        'regime': r,
        'n_trades': data['n'],
        'win_rate': len([p for p in data['pnl'] if p > 0]) / len(data['pnl']) * 100,
        'avg_pnl': np.mean(data['pnl']),
        'total_pnl': sum(data['pnl'])
    })

analysis_df = pd.DataFrame(all_trades)
print(analysis_df.to_string(index=False))

best_regime = analysis_df.loc[analysis_df['win_rate'].idxmax()]
print(f"\n🏆 Meilleur régime: {best_regime['regime']} (WR {best_regime['win_rate']:.1f}%)")
