#!/usr/bin/env python3
"""
Backtest Mean Reversion v4 - Signaux fréquents
Sur données réelles BTC (2020-2026)

Configuration v4 (très réactive):
- RSI: 45/55 (très sensible)
- Bollinger: 1.5σ (plus fréquent)
- TP: +3%, SL: -2% (scalp)
- Time Exit: 3j max
- Position: 3% capital (scalp)
- Cooldown: 1j seulement
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("📊 Loading REAL BTC/USDT data (2020-2026)...")
df = pd.read_csv('data/btc_usdt_daily.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df = df[['open', 'high', 'low', 'close', 'volume']]

print(f"   Data loaded: {len(df)} rows")

def calculate_rsi(close, period=14):
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_bollinger(close, period=20, std_dev=1.5):
    sma = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    return upper, lower, sma

print("\n📈 Calculating indicators (RSI 14, Bollinger 20 1.5σ)...")
df['rsi'] = calculate_rsi(df['close'], 14)
df['bb_upper'], df['bb_lower'], df['bb_mid'] = calculate_bollinger(df['close'], 20, 1.5)

train_start = '2020-01-01'
train_end = '2023-12-31'
test_start = '2024-01-01'
test_end = '2026-05-25'

df_train = df[train_start:train_end].copy()
df_test = df[test_start:test_end].copy()

print(f"\n📅 Split: Train {len(df_train)}j | Test {len(df_test)}j")

def generate_signals_v4(data, rsi_lower=45, rsi_upper=55):
    """Signaux très fréquents"""
    signals = []
    position = 0
    cooldown = 0
    
    for i in range(len(data)):
        row = data.iloc[i]
        
        if pd.isna(row['rsi']) or pd.isna(row['bb_lower']) or pd.isna(row['bb_upper']):
            signals.append(0)
            if cooldown > 0: cooldown -= 1
            continue
        
        if cooldown > 0:
            signals.append(0)
            cooldown -= 1
            continue
        
        # LONG: RSI < 45 OR price < lower BB
        if row['rsi'] < rsi_lower or row['close'] < row['bb_lower']:
            if position == 0:
                position = 1
                signals.append(1)
            else:
                signals.append(0)
        
        # SHORT: RSI > 55 OR price > upper BB
        elif row['rsi'] > rsi_upper or row['close'] > row['bb_upper']:
            if position == 0:
                position = -1
                signals.append(-1)
            else:
                signals.append(0)
        
        else:
            signals.append(0)
    
    return signals

def backtest_v4(data, position_size=0.03, tp=0.03, sl=0.02, max_hold=3, cooldown_days=1):
    """Scalping mean reversion"""
    
    capital = 10000
    position = None
    trades = []
    equity_curve = [capital]
    cooldown = 0
    
    for i in range(len(data)):
        row = data.iloc[i]
        current_price = row['close']
        current_date = row.name
        
        if cooldown > 0:
            cooldown -= 1
            equity_curve.append(capital)
            continue
        
        if row['signal'] != 0 and position is None:
            position = {
                'entry_price': current_price,
                'direction': row['signal'],
                'entry_date': current_date,
                'entry_idx': i
            }
        
        elif position is not None:
            pnl_pct = (current_price - position['entry_price']) / position['entry_price'] * position['direction']
            hold_days = i - position['entry_idx']
            
            exit_reason = None
            exit_pnl = 0
            
            if pnl_pct >= tp:
                exit_reason = 'TP'
                exit_pnl = pnl_pct
            elif pnl_pct <= -sl:
                exit_reason = 'SL'
                exit_pnl = pnl_pct
            elif hold_days >= max_hold:
                exit_reason = 'TIME'
                exit_pnl = pnl_pct
            
            if exit_reason:
                trade_pnl = capital * position_size * exit_pnl
                capital += trade_pnl
                
                trades.append({
                    'entry_date': position['entry_date'],
                    'exit_date': current_date,
                    'direction': position['direction'],
                    'entry_price': position['entry_price'],
                    'exit_price': current_price,
                    'pnl_pct': exit_pnl * 100,
                    'pnl_usd': trade_pnl,
                    'hold_days': hold_days,
                    'exit_reason': exit_reason
                })
                
                position = None
                cooldown = cooldown_days
        
        equity_curve.append(capital)
    
    return capital, trades, equity_curve

def calculate_sharpe(equity_curve):
    if len(equity_curve) < 2: return 0
    returns = pd.Series(equity_curve).pct_change().dropna()
    if returns.std() == 0: return 0
    return returns.mean() / returns.std() * np.sqrt(252)

def calculate_max_dd(equity_curve):
    peak = equity_curve[0]
    max_dd = 0
    for equity in equity_curve:
        if equity > peak: peak = equity
        dd = (peak - equity) / peak
        if dd > max_dd: max_dd = dd
    return max_dd * 100

print("\n🎯 Generating signals v4 (RSI 45/55 OR BB 1.5σ)...")
df_train['signal'] = generate_signals_v4(df_train)
df_test['signal'] = generate_signals_v4(df_test)

print(f"   Train: {df_train['signal'].abs().sum():.0f} trades")
print(f"   Test:  {df_test['signal'].abs().sum():.0f} trades")

print("\n🔬 Backtest v4 (TP +3%, SL -2%, Max 3j, Pos 3%, Cooldown 1j)...")

cap_train, trades_train, eq_train = backtest_v4(df_train)
ret_train = (cap_train - 10000) / 10000 * 100
sharpe_train = calculate_sharpe(eq_train)
dd_train = calculate_max_dd(eq_train)

cap_test, trades_test, eq_test = backtest_v4(df_test)
ret_test = (cap_test - 10000) / 10000 * 100
sharpe_test = calculate_sharpe(eq_test)
dd_test = calculate_max_dd(eq_test)

print(f"\n{'='*60}")
print("📊 RÉSULTATS V4 (SCALPING)")
print(f"{'='*60}")

print(f"\n🎯 TRAIN (2020-2023)")
print(f"   Return: {ret_train:+.2f}% | Sharpe: {sharpe_train:.2f} | DD: -{dd_train:.2f}%")
print(f"   Trades: {len(trades_train)}")
if trades_train:
    wr = len([t for t in trades_train if t['pnl_pct']>0]) / len(trades_train) * 100
    print(f"   Win Rate: {wr:.1f}%")

print(f"\n🎯 TEST (2024-2026)")
print(f"   Return: {ret_test:+.2f}% | Sharpe: {sharpe_test:.2f} | DD: -{dd_test:.2f}%")
print(f"   Trades: {len(trades_test)}")
if trades_test:
    wr = len([t for t in trades_test if t['pnl_pct']>0]) / len(trades_test) * 100
    avg = np.mean([t['pnl_pct'] for t in trades_test])
    print(f"   Win Rate: {wr:.1f}% | Avg PnL: {avg:+.2f}%")
    
    exits = {}
    for t in trades_test: exits[t['exit_reason']] = exits.get(t['exit_reason'], 0) + 1
    print(f"   Exits: {exits}")

print(f"\n{'='*60}")
print("🔍 VERDICT")
print(f"{'='*60}")

n_trades = len(trades_test)
wr = len([t for t in trades_test if t['pnl_pct']>0]) / len(trades_test) * 100 if trades_test else 0

print(f"   N Trades: {n_trades} (cible: 20+)")
print(f"   Win Rate: {wr:.1f}% (cible: 50%+)")
print(f"   Return: {ret_test:+.2f}% (cible: >0%)")

if n_trades >= 20 and wr >= 50 and ret_test > 0:
    print(f"\n🟢 V4 VALIDÉE - Scalping efficace!")
elif n_trades >= 20:
    print(f"\n🟡 V4 PROMETTEUSE - {n_trades} signaux")
else:
    print(f"\n🔴 V4 ÉCHEC - Trop peu de signaux")

if trades_test:
    pd.DataFrame(trades_test).to_csv('data/meanreversion_v4_trades_test.csv', index=False)
    print(f"\n💾 Sauvegardé: data/meanreversion_v4_trades_test.csv")
