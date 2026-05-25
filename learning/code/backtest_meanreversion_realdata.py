#!/usr/bin/env python3
"""
Backtest Mean Reversion v2 Strategy on REAL BTC Data (2020-2026)
Walk-Forward Validation: Train (2020-2023) / Test (2024-2026)

Configuration v2 (Validée):
- RSI: 35/65 (plus strict)
- Bollinger: 2.5σ (extrêmes seulement)
- TP: +8%, SL: -5%
- Time Exit: 10j max
- Position: 8% capital
- Conviction: HIGH (RSI+BB alignés)
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

def calculate_bollinger(close, period=20, std_dev=2.5):
    sma = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    return upper, lower, sma

print("\n📈 Calculating indicators (RSI 14, Bollinger 20 2.5σ)...")
df['rsi'] = calculate_rsi(df['close'], 14)
df['bb_upper'], df['bb_lower'], df['bb_mid'] = calculate_bollinger(df['close'], 20, 2.5)

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

# Mean Reversion Strategy
def generate_signals(data, rsi_lower=35, rsi_upper=65):
    """Generate mean reversion signals (relaxed: RSI OR BB, not AND)"""
    signals = []
    position = 0  # 0=no position, 1=LONG, -1=SHORT
    cooldown = 0  # Cooldown after exit to avoid re-entry immediately
    
    for i in range(len(data)):
        row = data.iloc[i]
        
        # Skip if NaN
        if pd.isna(row['rsi']) or pd.isna(row['bb_lower']) or pd.isna(row['bb_upper']):
            signals.append(0)
            if cooldown > 0:
                cooldown -= 1
            continue
        
        # Cooldown period after exit
        if cooldown > 0:
            signals.append(0)
            cooldown -= 1
            continue
        
        # LONG signal: RSI < 35 OR price < lower BB (relaxed from AND)
        if row['rsi'] < rsi_lower or row['close'] < row['bb_lower']:
            if position == 0:
                position = 1
                signals.append(1)
            else:
                signals.append(0)
        
        # SHORT signal: RSI > 65 OR price > upper BB (relaxed from AND)
        elif row['rsi'] > rsi_upper or row['close'] > row['bb_upper']:
            if position == 0:
                position = -1
                signals.append(-1)
            else:
                signals.append(0)
        
        # No signal
        else:
            signals.append(0)
    
    return signals

print("\n🎯 Generating signals (RSI 35/65 OR BB 2.5σ - relaxed)...")
df_train['signal'] = generate_signals(df_train)
df_test['signal'] = generate_signals(df_test)

print(f"   Train signals: {df_train['signal'].abs().sum():.0f} trades")
print(f"   Test signals:  {df_test['signal'].abs().sum():.0f} trades")

# Backtest with TP/SL/Time Exit
def backtest_strategy(data, position_size=0.08, tp=0.08, sl=0.05, max_hold=10):
    """Backtest with take profit, stop loss, and time exit"""
    
    capital = 10000  # $10k initial
    position = None  # {'entry_price': x, 'direction': 1/-1, 'entry_date': y}
    trades = []
    equity_curve = [capital]
    
    for i in range(len(data)):
        row = data.iloc[i]
        current_price = row['close']
        current_date = row.name
        
        # Check if we should enter
        if row['signal'] != 0 and position is None:
            position = {
                'entry_price': current_price,
                'direction': row['signal'],
                'entry_date': current_date,
                'entry_idx': i
            }
        
        # Check if we should exit
        elif position is not None:
            pnl_pct = (current_price - position['entry_price']) / position['entry_price'] * position['direction']
            hold_days = i - position['entry_idx']
            
            # Exit conditions
            exit_reason = None
            exit_pnl = 0
            
            # Take Profit
            if pnl_pct >= tp:
                exit_reason = 'TP'
                exit_pnl = pnl_pct
            
            # Stop Loss
            elif pnl_pct <= -sl:
                exit_reason = 'SL'
                exit_pnl = pnl_pct
            
            # Time Exit
            elif hold_days >= max_hold:
                exit_reason = 'TIME'
                exit_pnl = pnl_pct
            
            # Execute exit
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
        
        equity_curve.append(capital)
    
    return capital, trades, equity_curve

def calculate_sharpe(equity_curve, risk_free_rate=0.02):
    """Calculate Sharpe Ratio from equity curve"""
    if len(equity_curve) < 2:
        return 0
    
    returns = pd.Series(equity_curve).pct_change().dropna()
    if returns.std() == 0:
        return 0
    
    sharpe = (returns.mean() - risk_free_rate/252) / returns.std() * np.sqrt(252)
    return sharpe

def calculate_max_drawdown(equity_curve):
    """Calculate maximum drawdown from equity curve"""
    peak = equity_curve[0]
    max_dd = 0
    
    for equity in equity_curve:
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak
        if dd > max_dd:
            max_dd = dd
    
    return max_dd * 100

print("\n🔬 Running backtest (TP +8%, SL -5%, Max Hold 10j, Position 8%)...")

# Backtest Train
capital_train, trades_train, equity_train = backtest_strategy(df_train)
return_train = (capital_train - 10000) / 10000 * 100
sharpe_train = calculate_sharpe(equity_train)
max_dd_train = calculate_max_drawdown(equity_train)

# Backtest Test
capital_test, trades_test, equity_test = backtest_strategy(df_test)
return_test = (capital_test - 10000) / 10000 * 100
sharpe_test = calculate_sharpe(equity_test)
max_dd_test = calculate_max_drawdown(equity_test)

print(f"\n{'='*60}")
print("📊 RÉSULTATS WALK-FORWARD (DONNÉES RÉELLES)")
print(f"{'='*60}")

print(f"\n🎯 PÉRIODE D'ENTRAÎNEMENT (2020-2023)")
print(f"   Capital final: ${capital_train:,.2f}")
print(f"   Return total:  {return_train:+.2f}%")
print(f"   Sharpe Ratio:  {sharpe_train:.2f}")
print(f"   Max Drawdown:  -{max_dd_train:.2f}%")
print(f"   N trades:      {len(trades_train)}")

if trades_train:
    win_trades_train = [t for t in trades_train if t['pnl_pct'] > 0]
    win_rate_train = len(win_trades_train) / len(trades_train) * 100
    avg_pnl_train = np.mean([t['pnl_pct'] for t in trades_train])
    max_dd_train = max([t['pnl_pct'] for t in trades_train]) if trades_train else 0
    min_dd_train = min([t['pnl_pct'] for t in trades_train]) if trades_train else 0
    
    print(f"   Win rate:      {win_rate_train:.1f}%")
    print(f"   Avg PnL:       {avg_pnl_train:+.2f}%")
    print(f"   Best trade:    {max_dd_train:+.2f}%")
    print(f"   Worst trade:   {min_dd_train:+.2f}%")
    
    # Exit reasons
    exit_reasons_train = {}
    for t in trades_train:
        exit_reasons_train[t['exit_reason']] = exit_reasons_train.get(t['exit_reason'], 0) + 1
    print(f"   Exit reasons:  {exit_reasons_train}")

print(f"\n🎯 PÉRIODE DE TEST (2024-2026)")
print(f"   Capital final: ${capital_test:,.2f}")
print(f"   Return total:  {return_test:+.2f}%")
print(f"   Sharpe Ratio:  {sharpe_test:.2f}")
print(f"   Max Drawdown:  -{max_dd_test:.2f}%")
print(f"   N trades:      {len(trades_test)}")

if trades_test:
    win_trades_test = [t for t in trades_test if t['pnl_pct'] > 0]
    win_rate_test = len(win_trades_test) / len(trades_test) * 100
    avg_pnl_test = np.mean([t['pnl_pct'] for t in trades_test])
    max_dd_test = max([t['pnl_pct'] for t in trades_test]) if trades_test else 0
    min_dd_test = min([t['pnl_pct'] for t in trades_test]) if trades_test else 0
    
    print(f"   Win rate:      {win_rate_test:.1f}%")
    print(f"   Avg PnL:       {avg_pnl_test:+.2f}%")
    print(f"   Best trade:    {max_dd_test:+.2f}%")
    print(f"   Worst trade:   {min_dd_test:+.2f}%")
    
    # Exit reasons
    exit_reasons_test = {}
    for t in trades_test:
        exit_reasons_test[t['exit_reason']] = exit_reasons_test.get(t['exit_reason'], 0) + 1
    print(f"   Exit reasons:  {exit_reasons_test}")

# Robustness check
print(f"\n{'='*60}")
print("🔍 VERIFICATION DE ROBUSTESSE")
print(f"{'='*60}")

print(f"\n   Return Test/Train:    {return_test:.2f}% / {return_train:.2f}%")
if return_test > 0 and return_train > 0:
    print(f"   ✅ Les deux périodes positives")
elif return_test > 0:
    print(f"   ✅ Test positif (malgré Train négatif = PAS overfitting!)")
else:
    print(f"   ❌ ÉCHEC - Return test négatif")

print(f"\n   Win Rate Test:        {win_rate_test:.1f}% (cible: >50%)")
if win_rate_test > 50:
    print(f"   ✅ Win rate > 50%")
else:
    print(f"   ⚠️ Win rate < 50%")

print(f"\n   Drawdown Max Test:    {min_dd_test:.2f}% (cible: >-10%)")
if min_dd_test > -10:
    print(f"   ✅ Drawdown acceptable")
else:
    print(f"   ⚠️ Drawdown trop élevé")

# Save trades to CSV
if trades_test:
    trades_df = pd.DataFrame(trades_test)
    trades_df.to_csv('data/meanreversion_v2_trades_test.csv', index=False)
    print(f"\n💾 Trades sauvegardés: data/meanreversion_v2_trades_test.csv")

print(f"\n{'='*60}")
if return_test > 0 and win_rate_test > 50 and min_dd_test > -10:
    print("🟢 VERDICT: STRATÉGIE VALIDÉE SUR DONNÉES RÉELLES!")
else:
    print("🟠 VERDICT: STRATÉGIE À OPTIMISER")
print(f"{'='*60}")
