#!/usr/bin/env python3
"""
Backtest Mean Reversion v3 - Optimisée pour plus de signaux
Sur données réelles BTC (2020-2026)

Configuration v3 (plus de signaux):
- RSI: 40/60 (vs 35/65 v2)
- Bollinger: 2.0σ (vs 2.5σ v2)
- TP: +5%, SL: -3% (plus serré)
- Time Exit: 5j max (vs 10j)
- Position: 5% capital (vs 8%)
- Cooldown: 3j après exit
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Load real BTC data
print("📊 Loading REAL BTC/USDT data (2020-2026)...")
df = pd.read_csv('data/btc_usdt_daily.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df = df[['open', 'high', 'low', 'close', 'volume']]

print(f"   Data loaded: {len(df)} rows")
print(f"   Date range: {df.index.min()} to {df.index.max()}")
print(f"   Price range: ${df['close'].min():.2f} to ${df['close'].max():.2f}")

# Calculate indicators
def calculate_rsi(close, period=14):
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_bollinger(close, period=20, std_dev=2.0):
    sma = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    return upper, lower, sma

print("\n📈 Calculating indicators (RSI 14, Bollinger 20 2.0σ)...")
df['rsi'] = calculate_rsi(df['close'], 14)
df['bb_upper'], df['bb_lower'], df['bb_mid'] = calculate_bollinger(df['close'], 20, 2.0)

# Split Train/Test
train_start = '2020-01-01'
train_end = '2023-12-31'
test_start = '2024-01-01'
test_end = '2026-05-25'

df_train = df[train_start:train_end].copy()
df_test = df[test_start:test_end].copy()

print(f"\n📅 Walk-Forward Split:")
print(f"   Train: {train_start} to {train_end} ({len(df_train)} days)")
print(f"   Test:  {test_start} to {test_end} ({len(df_test)} days)")

# Mean Reversion Strategy v3 (plus de signaux)
def generate_signals_v3(data, rsi_lower=40, rsi_upper=60):
    """Generate mean reversion signals (RSI OR BB, with cooldown)"""
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
        
        # LONG: RSI < 40 OR price < lower BB
        if row['rsi'] < rsi_lower or row['close'] < row['bb_lower']:
            if position == 0:
                position = 1
                signals.append(1)
            else:
                signals.append(0)
        
        # SHORT: RSI > 60 OR price > upper BB
        elif row['rsi'] > rsi_upper or row['close'] > row['bb_upper']:
            if position == 0:
                position = -1
                signals.append(-1)
            else:
                signals.append(0)
        
        else:
            signals.append(0)
    
    return signals

def backtest_v3(data, position_size=0.05, tp=0.05, sl=0.03, max_hold=5, cooldown_days=3):
    """Backtest v3 with tighter stops and cooldown"""
    
    capital = 10000
    position = None
    trades = []
    equity_curve = [capital]
    cooldown = 0
    
    for i in range(len(data)):
        row = data.iloc[i]
        current_price = row['close']
        current_date = row.name
        
        # Cooldown check
        if cooldown > 0:
            cooldown -= 1
            equity_curve.append(capital)
            continue
        
        # Enter
        if row['signal'] != 0 and position is None:
            position = {
                'entry_price': current_price,
                'direction': row['signal'],
                'entry_date': current_date,
                'entry_idx': i
            }
        
        # Exit check
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

def calculate_sharpe(equity_curve, risk_free_rate=0.02):
    if len(equity_curve) < 2:
        return 0
    returns = pd.Series(equity_curve).pct_change().dropna()
    if returns.std() == 0:
        return 0
    sharpe = (returns.mean() - risk_free_rate/252) / returns.std() * np.sqrt(252)
    return sharpe

def calculate_max_drawdown(equity_curve):
    peak = equity_curve[0]
    max_dd = 0
    for equity in equity_curve:
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak
        if dd > max_dd:
            max_dd = dd
    return max_dd * 100

print("\n🎯 Generating signals v3 (RSI 40/60 OR BB 2.0σ)...")
df_train['signal'] = generate_signals_v3(df_train)
df_test['signal'] = generate_signals_v3(df_test)

print(f"   Train signals: {df_train['signal'].abs().sum():.0f} trades")
print(f"   Test signals:  {df_test['signal'].abs().sum():.0f} trades")

print("\n🔬 Running backtest v3 (TP +5%, SL -3%, Max 5j, Pos 5%, Cooldown 3j)...")

capital_train, trades_train, equity_train = backtest_v3(df_train)
return_train = (capital_train - 10000) / 10000 * 100
sharpe_train = calculate_sharpe(equity_train)
max_dd_train = calculate_max_drawdown(equity_train)

capital_test, trades_test, equity_test = backtest_v3(df_test)
return_test = (capital_test - 10000) / 10000 * 100
sharpe_test = calculate_sharpe(equity_test)
max_dd_test = calculate_max_drawdown(equity_test)

print(f"\n{'='*60}")
print("📊 RÉSULTATS WALK-FORWARD (DONNÉES RÉELLES) - V3")
print(f"{'='*60}")

print(f"\n🎯 PÉRIODE D'ENTRAÎNEMENT (2020-2023)")
print(f"   Capital final: ${capital_train:,.2f}")
print(f"   Return total:  {return_train:+.2f}%")
print(f"   Sharpe Ratio:  {sharpe_train:.2f}")
print(f"   Max Drawdown:  -{max_dd_train:.2f}%")
print(f"   N trades:      {len(trades_train)}")

if trades_train:
    win_trades = [t for t in trades_train if t['pnl_pct'] > 0]
    win_rate = len(win_trades) / len(trades_train) * 100
    avg_pnl = np.mean([t['pnl_pct'] for t in trades_train])
    best = max([t['pnl_pct'] for t in trades_train])
    worst = min([t['pnl_pct'] for t in trades_train])
    
    print(f"   Win rate:      {win_rate:.1f}%")
    print(f"   Avg PnL:       {avg_pnl:+.2f}%")
    print(f"   Best trade:    {best:+.2f}%")
    print(f"   Worst trade:   {worst:+.2f}%")
    
    exit_reasons = {}
    for t in trades_train:
        exit_reasons[t['exit_reason']] = exit_reasons.get(t['exit_reason'], 0) + 1
    print(f"   Exit reasons:  {exit_reasons}")

print(f"\n🎯 PÉRIODE DE TEST (2024-2026)")
print(f"   Capital final: ${capital_test:,.2f}")
print(f"   Return total:  {return_test:+.2f}%")
print(f"   Sharpe Ratio:  {sharpe_test:.2f}")
print(f"   Max Drawdown:  -{max_dd_test:.2f}%")
print(f"   N trades:      {len(trades_test)}")

if trades_test:
    win_trades = [t for t in trades_test if t['pnl_pct'] > 0]
    win_rate = len(win_trades) / len(trades_test) * 100
    avg_pnl = np.mean([t['pnl_pct'] for t in trades_test])
    best = max([t['pnl_pct'] for t in trades_test])
    worst = min([t['pnl_pct'] for t in trades_test])
    
    print(f"   Win rate:      {win_rate:.1f}%")
    print(f"   Avg PnL:       {avg_pnl:+.2f}%")
    print(f"   Best trade:    {best:+.2f}%")
    print(f"   Worst trade:   {worst:+.2f}%")
    
    exit_reasons = {}
    for t in trades_test:
        exit_reasons[t['exit_reason']] = exit_reasons.get(t['exit_reason'], 0) + 1
    print(f"   Exit reasons:  {exit_reasons}")

print(f"\n{'='*60}")
print("🔍 VERIFICATION DE ROBUSTESSE")
print(f"{'='*60}")

print(f"\n   Return Test/Train:    {return_test:+.2f}% / {return_train:+.2f}%")
if return_test > 0:
    print(f"   ✅ Test positif")
else:
    print(f"   ❌ Test négatif")

print(f"\n   Win Rate Test:        {win_rate:.1f}% (cible: >50%)")
if win_rate > 50:
    print(f"   ✅ Win rate > 50%")
else:
    print(f"   ⚠️ Win rate < 50%")

print(f"\n   N Trades Test:        {len(trades_test)} (cible: >20)")
if len(trades_test) >= 20:
    print(f"   ✅ Suffisant")
else:
    print(f"   ⚠️ Trop peu de signaux")

print(f"\n   Drawdown Max Test:    -{max_dd_test:.2f}% (cible: >-10%)")
if max_dd_test < 10:
    print(f"   ✅ Drawdown acceptable")
else:
    print(f"   ⚠️ Drawdown élevé")

if trades_test:
    trades_df = pd.DataFrame(trades_test)
    trades_df.to_csv('data/meanreversion_v3_trades_test.csv', index=False)
    print(f"\n💾 Trades sauvegardés: data/meanreversion_v3_trades_test.csv")

print(f"\n{'='*60}")
if return_test > 0 and win_rate > 50 and max_dd_test < 10 and len(trades_test) >= 20:
    print("🟢 VERDICT: STRATÉGIE V3 VALIDÉE!")
elif return_test > 0 and win_rate > 50:
    print("🟡 VERDICT: V3 PROMETTEUSE (mais peu de signaux)")
else:
    print("🟠 VERDICT: V3 À OPTIMISER")
print(f"{'='*60}")
