#!/usr/bin/env python3
"""
Backtest Mean Reversion v8 - Avec Filtre HMM + Volume
Sur données réelles BTC (2020-2026)

Configuration v8:
- RSI: 30/70
- Bollinger: 2.0σ
- TP: +6%, SL: -3% (R/R 2:1)
- Time Exit: 7j
- Position: 5%
- 🆕 FILTRE HMM: Trader seulement si regime = RANGE (vol basse)
- 🆕 FILTRE VOLUME: Volume > 1.5x MA(20)
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

print("📊 BTC/USDT Daily (2020-2026) + Filtres HMM + Volume")
df = pd.read_csv('data/btc_usdt_daily.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')[['open', 'high', 'low', 'close', 'volume']]
print(f"   {len(df)} rows | ${df['close'].min():.0f} - ${df['close'].max():.0f}")

# Indicators
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
    """
    HMM simplifié: détecte regime par volatilité rolling
    - RANGE: vol basse (std < percentile 40)
    - TREND: vol haute (std > percentile 60)
    - TRANSITION: entre deux
    """
    vol = close.rolling(window).std()
    vol_low = vol.quantile(0.40)
    vol_high = vol.quantile(0.60)
    
    regime = []
    for v in vol:
        if pd.isna(v):
            regime.append('UNKNOWN')
        elif v < vol_low:
            regime.append('RANGE')  # Vol basse = range-bound
        elif v > vol_high:
            regime.append('TREND')  # Vol haute = trending
        else:
            regime.append('TRANSITION')
    return regime

def calc_volume_ma(volume, period=20):
    """Volume MA(20)"""
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

# Distribution des régimes
print(f"\n📊 Distribution Régimes HMM (Test):")
regime_counts = df_test['regime'].value_counts()
for r, c in regime_counts.items():
    pct = c / len(df_test) * 100
    print(f"   {r}: {c} ({pct:.1f}%)")

# Signals v8
def gen_signals_v8(data):
    """Signaux avec filtres HMM + Volume"""
    signals = []
    for i, row in data.iterrows():
        if pd.isna(row['rsi']) or pd.isna(row['bb_l']):
            signals.append(0)
            continue
        
        # FILTRE HMM: Trader seulement en RANGE
        if row['regime'] != 'RANGE':
            signals.append(0)
            continue
        
        # FILTRE VOLUME: Volume > 1.5x MA
        if row['vol_ratio'] < 1.5:
            signals.append(0)
            continue
        
        # Signal Mean Reversion
        if row['rsi'] < 30 or row['close'] < row['bb_l']:
            signals.append(1)  # LONG
        elif row['rsi'] > 70 or row['close'] > row['bb_u']:
            signals.append(-1)  # SHORT
        else:
            signals.append(0)
    
    return signals

print("\n🎯 Signaux v8 (RSI 30/70 + BB 2.0σ + HMM RANGE + Volume >1.5x)")
df_train['signal'] = gen_signals_v8(df_train)
df_test['signal'] = gen_signals_v8(df_test)

n_train = df_train['signal'].abs().sum()
n_test = df_test['signal'].abs().sum()
print(f"   Train: {n_train:.0f} signaux")
print(f"   Test:  {n_test:.0f} signaux")

# Backtest
def backtest_v8(data, pos_size=0.05, tp=0.06, sl=0.03, max_hold=7):
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

print(f"\n🔬 Backtest v8 (TP +6%, SL -3%, Max 7j, Pos 5%)")

cap_t, trades_t, eq_t = backtest_v8(df_train)
ret_t = (cap_t - 10000) / 10000 * 100

cap_s, trades_s, eq_s = backtest_v8(df_test)
ret_s = (cap_s - 10000) / 10000 * 100

print(f"\n{'='*60}")
print("📊 RÉSULTATS V8 (HMM + VOLUME)")
print(f"{'='*60}")

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
    
    # Performance par régime
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
print("🔍 VERDICT")
print(f"{'='*60}")

n = len(trades_s)
wr = len([t for t in trades_s if t['pnl']>0]) / len(trades_s) * 100 if trades_s else 0

print(f"   N Trades: {n} (vs 81 sans filtres)")
print(f"   Win Rate: {wr:.1f}% (cible: ≥55%)")
print(f"   Return: {ret_s:+.2f}% (cible: >0%)")
print(f"   Sharpe: {sharpe(eq_s):.2f} (cible: >0.5)")

if n >= 10 and wr >= 55 and ret_s > 0:
    print(f"\n🟢 V8 VALIDÉE - FILTRES HMM+VOLUME EFFICACES!")
elif n >= 10 and wr >= 50:
    print(f"\n🟡 V8 PROMETTEUSE - {n} trades, WR {wr:.1f}%")
else:
    print(f"\n🔴 V8 ÉCHEC - Filtres trop stricts ou inefficaces")

if trades_s:
    pd.DataFrame(trades_s).to_csv('data/meanreversion_v8_trades_test.csv', index=False)
    print(f"\n💾 data/meanreversion_v8_trades_test.csv")

# Comparaison avec v7 (sans filtres)
print(f"\n{'='*60}")
print("📊 COMPARAISON V7 (sans filtres) vs V8 (avec filtres)")
print(f"{'='*60}")
print(f"   V7 (no filters): 81 trades, WR 40.7%, Return -0.34%")
print(f"   V8 (HMM+Vol):    {n} trades, WR {wr:.1f}%, Return {ret_s:+.2f}%")

if wr > 40.7 and ret_s > -0.34:
    print(f"\n✅ FILTRES AMÉLIORENT PERFORMANCE!")
else:
    print(f"\n⚠️ Filtres réduisent WR ou return")
