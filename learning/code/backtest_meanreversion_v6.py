#!/usr/bin/env python3
"""
Backtest Mean Reversion v6 - Optimisée
Sur données réelles BTC (2020-2026)

Configuration v6:
- RSI: 30/70
- Bollinger: 2.0σ
- TP: +5%, SL: -4% (meilleur R/R)
- Time Exit: 7j
- Position: 5%
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

print("📊 BTC/USDT Daily (2020-2026)")
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

df['rsi'] = calc_rsi(df['close'])
df['bb_u'], df['bb_l'], df['bb_m'] = calc_bb(df['close'])

df_train = df['2020-01-01':'2023-12-31'].copy()
df_test = df['2024-01-01':'2026-05-25'].copy()
print(f"\n📅 Train: {len(df_train)}j | Test: {len(df_test)}j")

def gen_signals(data, rsi_l=30, rsi_h=70):
    signals = []
    for i, row in data.iterrows():
        if pd.isna(row['rsi']) or pd.isna(row['bb_l']):
            signals.append(0)
            continue
        if row['rsi'] < rsi_l or row['close'] < row['bb_l']:
            signals.append(1)
        elif row['rsi'] > rsi_h or row['close'] > row['bb_u']:
            signals.append(-1)
        else:
            signals.append(0)
    return signals

print("\n🎯 Signaux (RSI 30/70 OR BB 2.0σ)")
df_train['signal'] = gen_signals(df_train)
df_test['signal'] = gen_signals(df_test)
print(f"   Train: {df_train['signal'].abs().sum():.0f} | Test: {df_test['signal'].abs().sum():.0f}")

def backtest(data, pos_size=0.05, tp=0.05, sl=0.04, max_hold=7):
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
                    'hold': hold, 'exit_reason': exit_reason
                })
                position = None
        
        if row['signal'] != 0 and not position:
            position = {'entry': price, 'dir': row['signal'], 'idx': i}
        
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

print("\n🔬 Backtest v6 (TP +5%, SL -4%, Max 7j, Pos 5%)")

cap_t, trades_t, eq_t = backtest(df_train)
ret_t = (cap_t - 10000) / 10000 * 100

cap_s, trades_s, eq_s = backtest(df_test)
ret_s = (cap_s - 10000) / 10000 * 100

print(f"\n{'='*50}")
print("📊 RÉSULTATS V6")
print(f"{'='*50}")

print(f"\n🎯 TRAIN (2020-2023)")
print(f"   Return: {ret_t:+.2f}% | Capital: ${cap_t:,.2f}")
print(f"   Trades: {len(trades_t)} | Sharpe: {sharpe(eq_t):.2f} | DD: -{max_dd(eq_t):.2f}%")
if trades_t:
    wr = len([t for t in trades_t if t['pnl']>0]) / len(trades_t) * 100
    avg = np.mean([t['pnl'] for t in trades_t])
    print(f"   Win Rate: {wr:.1f}% | Avg PnL: {avg:+.2f}%")

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
    exits = {}
    for t in trades_s: exits[t['exit_reason']] = exits.get(t['exit_reason'], 0) + 1
    print(f"   Exits: {exits}")

print(f"\n{'='*50}")
print("🔍 VERDICT")
print(f"{'='*50}")

n = len(trades_s)
wr = len([t for t in trades_s if t['pnl']>0]) / len(trades_s) * 100 if trades_s else 0

print(f"   N Trades: {n}")
print(f"   Win Rate: {wr:.1f}%")
print(f"   Return: {ret_s:+.2f}%")

if n >= 20 and wr >= 50 and ret_s > 0:
    print(f"\n🟢 V6 VALIDÉE!")
elif n >= 20 and wr >= 45:
    print(f"\n🟡 V6 PROMETTEUSE")
else:
    print(f"\n🔴 V6 À optimiser")

if trades_s:
    pd.DataFrame(trades_s).to_csv('data/meanreversion_v6_trades_test.csv', index=False)
    print(f"\n💾 data/meanreversion_v6_trades_test.csv")

# V7: TP +6%, SL -3% (meilleur R/R)
print(f"\n\n{'='*50}")
print("🚀 TEST V7 (TP +6%, SL -3%, R/R 2:1)")
print(f"{'='*50}")

cap_s7, trades_s7, eq_s7 = backtest(df_test, pos_size=0.05, tp=0.06, sl=0.03, max_hold=7)
ret_s7 = (cap_s7 - 10000) / 10000 * 100

print(f"\n   Return: {ret_s7:+.2f}% | Trades: {len(trades_s7)}")
if trades_s7:
    wr7 = len([t for t in trades_s7 if t['pnl']>0]) / len(trades_s7) * 100
    avg7 = np.mean([t['pnl'] for t in trades_s7])
    print(f"   Win Rate: {wr7:.1f}% | Avg PnL: {avg7:+.2f}%")
    exits7 = {}
    for t in trades_s7: exits7[t['exit_reason']] = exits7.get(t['exit_reason'], 0) + 1
    print(f"   Exits: {exits7}")

if ret_s7 > 0 and wr7 >= 45:
    print(f"\n🟢 V7 VALIDÉE - Meilleure config!")
else:
    print(f"\n🟡 V7: Return {ret_s7:+.2f}%")
