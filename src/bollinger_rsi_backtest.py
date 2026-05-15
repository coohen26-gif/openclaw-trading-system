#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backtest Bollinger-RSI Dual Strategy
Mean reversion sur prix avec confirmation RSI

LONG: Prix touche BB inférieure + RSI < 30
SHORT: Prix touche BB supérieure + RSI > 70
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    # Données
    'symbol': 'BTC/USDT',
    'timeframe': '4h',
    'days': 90,
    
    # Bollinger Bands
    'bb_period': 20,
    'bb_std': 2.0,
    
    # RSI
    'rsi_period': 14,
    'rsi_long': 30,
    'rsi_short': 70,
    
    # Trading - Best config found
    'tp_type': 'percent',
    'tp_percent': 0.008,   # 0.8%
    'sl_percent': 0.02,    # 2%
    'sl_rsi': False,
    
    # Fees
    'fee': 0.001,
    'slippage': 0.0005,
    
    # Capital
    'capital': 10000,
    'leverage': 1,
}

# ============================================================================
# RÉCUPÉRATION DES DONNÉES
# ============================================================================

def fetch_ohlcv(symbol, timeframe, days):
    """Récupère les données OHLCV depuis Binance"""
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    since = int(start_date.timestamp() * 1000)
    
    print(f"📊 Récupération {symbol} {timeframe} depuis {start_date.date()}...")
    
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=5000)
    
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    print(f"   → {len(df)} bougies récupérées")
    return df

# ============================================================================
# INDICATEURS TECHNIQUES
# ============================================================================

def calculate_bollinger_bands(df, period=20, std_dev=2.0):
    """Calcule Bollinger Bands"""
    df['bb_middle'] = df['close'].rolling(window=period).mean()
    df['bb_std'] = df['close'].rolling(window=period).std()
    df['bb_upper'] = df['bb_middle'] + (std_dev * df['bb_std'])
    df['bb_lower'] = df['bb_middle'] - (std_dev * df['bb_std'])
    return df

def calculate_rsi(df, period=14):
    """Calcule RSI"""
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi'] = df['rsi'].fillna(50)
    
    return df

def calculate_indicators(df, config):
    """Calcule tous les indicateurs"""
    df = calculate_bollinger_bands(df, config['bb_period'], config['bb_std'])
    df = calculate_rsi(df, config['rsi_period'])
    
    # Pourcentage depuis les bands
    df['pct_b'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    
    return df

# ============================================================================
# SIGNAUX DE TRADING
# ============================================================================

def generate_signals(df, config):
    """Génère les signaux LONG/SHORT"""
    df['signal'] = 0  # 0=rien, 1=LONG, -1=SHORT
    df['position'] = 0
    df['exit_reason'] = ''
    
    in_position = False
    position_type = 0
    entry_price = 0
    entry_rsi = 0
    
    for i in range(len(df)):
        if i < config['bb_period'] + config['rsi_period']:
            continue
        
        row = df.iloc[i]
        prev_row = df.iloc[i-1] if i > 0 else row
        
        if not in_position:
            # LONG: Prix touche BB inférieure + RSI < 30
            if row['close'] <= row['bb_lower'] and row['rsi'] < config['rsi_long']:
                df.iloc[i, df.columns.get_loc('signal')] = 1
                in_position = True
                position_type = 1
                entry_price = row['close']
                entry_rsi = row['rsi']
                df.iloc[i, df.columns.get_loc('exit_reason')] = 'ENTRY_LONG'
            
            # SHORT: Prix touche BB supérieure + RSI > 70
            elif row['close'] >= row['bb_upper'] and row['rsi'] > config['rsi_short']:
                df.iloc[i, df.columns.get_loc('signal')] = -1
                in_position = True
                position_type = -1
                entry_price = row['close']
                entry_rsi = row['rsi']
                df.iloc[i, df.columns.get_loc('exit_reason')] = 'ENTRY_SHORT'
        
        else:
            exit_signal = False
            reason = ''
            
            if position_type == 1:  # LONG
                # TP: retour à la moyenne (BB middle)
                if config['tp_type'] == 'middle' and row['close'] >= row['bb_middle']:
                    exit_signal = True
                    reason = 'TP_MIDDLE'
                
                # TP: pourcentage fixe
                elif config['tp_type'] == 'percent':
                    tp_price = entry_price * (1 + config['tp_percent'])
                    if row['close'] >= tp_price:
                        exit_signal = True
                        reason = 'TP_PERCENT'
                
                # SL: pourcentage
                sl_price = entry_price * (1 - config['sl_percent'])
                if row['close'] <= sl_price:
                    exit_signal = True
                    reason = 'SL_PERCENT'
                
                # SL: RSI continue dans mauvaise direction (RSI remonte > 50)
                if config['sl_rsi'] and row['rsi'] > 50 and entry_rsi < 30:
                    exit_signal = True
                    reason = 'SL_RSI'
            
            elif position_type == -1:  # SHORT
                # TP: retour à la moyenne
                if config['tp_type'] == 'middle' and row['close'] <= row['bb_middle']:
                    exit_signal = True
                    reason = 'TP_MIDDLE'
                
                # TP: pourcentage fixe
                elif config['tp_type'] == 'percent':
                    tp_price = entry_price * (1 - config['tp_percent'])
                    if row['close'] <= tp_price:
                        exit_signal = True
                        reason = 'TP_PERCENT'
                
                # SL: pourcentage
                sl_price = entry_price * (1 + config['sl_percent'])
                if row['close'] >= sl_price:
                    exit_signal = True
                    reason = 'SL_PERCENT'
                
                # SL: RSI continue dans mauvaise direction (RSI descend < 50)
                if config['sl_rsi'] and row['rsi'] < 50 and entry_rsi > 70:
                    exit_signal = True
                    reason = 'SL_RSI'
            
            if exit_signal:
                df.iloc[i, df.columns.get_loc('signal')] = 0
                in_position = False
                df.iloc[i, df.columns.get_loc('exit_reason')] = f'EXIT_{reason}'
    
    return df

# ============================================================================
# BACKTEST
# ============================================================================

def run_backtest(df, config):
    """Exécute le backtest"""
    capital = config['capital']
    fee = config['fee']
    slippage = config['slippage']
    
    trades = []
    current_trade = None
    pnl_curve = []
    drawdown_curve = []
    peak = capital
    
    for i in range(len(df)):
        if i < config['bb_period'] + config['rsi_period']:
            pnl_curve.append(capital)
            drawdown_curve.append(0)
            continue
        
        row = df.iloc[i]
        signal = row['signal']
        
        # Ouverture de position
        if signal != 0 and current_trade is None:
            current_trade = {
                'entry_date': row.name,
                'entry_idx': i,
                'type': signal,
                'entry_price': row['close'],
                'entry_rsi': row['rsi'],
                'bb_upper': row['bb_upper'],
                'bb_lower': row['bb_lower'],
                'bb_middle': row['bb_middle']
            }
        
        # Fermeture de position
        elif signal == 0 and current_trade is not None:
            exit_price = row['close']
            exit_rsi = row['rsi']
            
            # Calcul PnL
            if current_trade['type'] == 1:  # LONG
                price_change = (exit_price - current_trade['entry_price']) / current_trade['entry_price']
                raw_pnl = price_change * capital
            else:  # SHORT
                price_change = (current_trade['entry_price'] - exit_price) / current_trade['entry_price']
                raw_pnl = price_change * capital
            
            # Fees + slippage
            total_cost = capital * (fee + slippage) * 2
            net_pnl = raw_pnl - total_cost
            
            trades.append({
                'entry_date': current_trade['entry_date'],
                'exit_date': row.name,
                'type': 'LONG' if current_trade['type'] == 1 else 'SHORT',
                'entry_price': current_trade['entry_price'],
                'exit_price': exit_price,
                'entry_rsi': current_trade['entry_rsi'],
                'exit_rsi': exit_rsi,
                'entry_bb_upper': current_trade['bb_upper'],
                'entry_bb_lower': current_trade['bb_lower'],
                'entry_bb_middle': current_trade['bb_middle'],
                'exit_bb_middle': row['bb_middle'],
                'duration_hours': (row.name - current_trade['entry_date']).total_seconds() / 3600,
                'pnl_eur': net_pnl,
                'pnl_pct': net_pnl / capital * 100,
                'exit_reason': row['exit_reason']
            })
            
            capital += net_pnl
            current_trade = None
        
        pnl_curve.append(capital)
        
        if capital > peak:
            peak = capital
        drawdown = (peak - capital) / peak * 100
        drawdown_curve.append(drawdown)
    
    df['pnl_curve'] = pnl_curve
    df['drawdown_curve'] = drawdown_curve
    
    return trades, df

# ============================================================================
# MÉTRIQUES
# ============================================================================

def calculate_metrics(trades, df, config):
    """Calcule les métriques de performance"""
    if len(trades) == 0:
        return {
            'total_trades': 0,
            'win_rate': 0,
            'pnl_total_eur': 0,
            'pnl_total_pct': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'avg_duration_hours': 0,
            'profit_factor': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'long_trades': 0,
            'short_trades': 0,
            'long_wr': 0,
            'short_wr': 0
        }
    
    trades_df = pd.DataFrame(trades)
    
    # Win Rate
    winners = len(trades_df[trades_df['pnl_eur'] > 0])
    win_rate = winners / len(trades_df) * 100
    
    # PnL Total
    pnl_total = trades_df['pnl_eur'].sum()
    pnl_pct = pnl_total / config['capital'] * 100
    
    # Sharpe Ratio (annualisé)
    if len(trades_df) > 1 and trades_df['duration_hours'].mean() > 0:
        returns = trades_df['pnl_eur'] / config['capital']
        sharpe = returns.mean() / returns.std() * np.sqrt(365 * 24 / trades_df['duration_hours'].mean())
    else:
        sharpe = 0
    
    # Max Drawdown
    max_drawdown = df['drawdown_curve'].max()
    
    # Avg Duration
    avg_duration = trades_df['duration_hours'].mean()
    
    # Profit Factor
    gross_profit = trades_df[trades_df['pnl_eur'] > 0]['pnl_eur'].sum()
    gross_loss = abs(trades_df[trades_df['pnl_eur'] <= 0]['pnl_eur'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    # Avg Win/Loss
    avg_win = trades_df[trades_df['pnl_eur'] > 0]['pnl_eur'].mean() if len(trades_df[trades_df['pnl_eur'] > 0]) > 0 else 0
    avg_loss = abs(trades_df[trades_df['pnl_eur'] <= 0]['pnl_eur'].mean()) if len(trades_df[trades_df['pnl_eur'] <= 0]) > 0 else 0
    
    # Long vs Short
    long_trades = trades_df[trades_df['type'] == 'LONG']
    short_trades = trades_df[trades_df['type'] == 'SHORT']
    
    long_wr = len(long_trades[long_trades['pnl_eur'] > 0]) / len(long_trades) * 100 if len(long_trades) > 0 else 0
    short_wr = len(short_trades[short_trades['pnl_eur'] > 0]) / len(short_trades) * 100 if len(short_trades) > 0 else 0
    
    return {
        'total_trades': len(trades_df),
        'win_rate': win_rate,
        'pnl_total_eur': pnl_total,
        'pnl_total_pct': pnl_pct,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown,
        'avg_duration_hours': avg_duration,
        'profit_factor': profit_factor,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'long_trades': len(long_trades),
        'short_trades': len(short_trades),
        'long_wr': long_wr,
        'short_wr': short_wr
    }

# ============================================================================
# RAPPORT
# ============================================================================

def generate_report(df, trades, metrics, config, output_path):
    """Génère le rapport markdown"""
    
    start_date = df.index[0].strftime('%Y-%m-%d')
    end_date = df.index[-1].strftime('%Y-%m-%d')
    duration_days = (df.index[-1] - df.index[0]).days
    
    # Critères de succès
    wr_pass = metrics['win_rate'] >= 70
    pf_pass = metrics['profit_factor'] > 1.5
    overall_pass = wr_pass and pf_pass
    
    status = '✅ PASS' if overall_pass else '❌ FAIL'
    
    report = f"""# Backtest #2 : Bollinger-RSI Dual

## 📋 Synthèse Exécutive

**Statut : {status} — Mean reversion sur prix avec confirmation RSI**

| Métrique | Résultat | Objectif | Écart |
|---|---|---|---|
| **Win Rate** | {metrics['win_rate']:.1f}% | ≥70% | {metrics['win_rate'] - 70:+.1f} pts {'✅' if wr_pass else '❌'} |
| **PnL Total** | {metrics['pnl_total_eur']:+.2f}€ ({metrics['pnl_total_pct']:+.2f}%) | - | - |
| **PnL/jour** | {metrics['pnl_total_eur']/duration_days:+.2f}€/jour | - | - |
| **Sharpe Ratio** | {metrics['sharpe_ratio']:.2f} | >1 | {'✅' if metrics['sharpe_ratio'] > 1 else '❌'} |
| **Max Drawdown** | -{metrics['max_drawdown']:.2f}% | <20% | {'✅' if metrics['max_drawdown'] < 20 else '❌'} |
| **Profit Factor** | {metrics['profit_factor']:.2f} | >1.5 | {'✅' if pf_pass else '❌'} |

---

## 📊 Données du Backtest

### Période
- **Start** : {start_date}
- **End** : {end_date}
- **Durée** : {duration_days} jours

### Données
- **Symbol** : {config['symbol']}
- **Timeframe** : {config['timeframe']}
- **Source** : Binance (CCXT)
- **N bougies** : {len(df)}

### Paramètres
| Paramètre | Valeur |
|---|---|
| **Bollinger Bands** | {config['bb_period']} périodes, {config['bb_std']}σ |
| **RSI** | {config['rsi_period']} périodes |
| **Thresholds RSI** | LONG < {config['rsi_long']}, SHORT > {config['rsi_short']} |
| **Take Profit** | {config['tp_type']} ({config['tp_percent']*100:.1f}% si percent) |
| **Stop Loss** | {config['sl_percent']*100:.1f}% {'+ RSI' if config['sl_rsi'] else ''} |
| **Fees** | {config['fee']*100}% |
| **Slippage** : {config['slippage']*100}% |
| **Capital** | {config['capital']} € |
| **Levier** | {config['leverage']}x |

---

## 🔍 Analyse Détaillée

### 1. Performance par Type de Trade

| Type | N Trades | Win Rate | PnL Total |
|---|---|---|---|
| LONG | {metrics['long_trades']} | {metrics['long_wr']:.1f}% | {sum([t['pnl_eur'] for t in trades if t['type']=='LONG']):+.2f}€ |
| SHORT | {metrics['short_trades']} | {metrics['short_wr']:.1f}% | {sum([t['pnl_eur'] for t in trades if t['type']=='SHORT']):+.2f}€ |

### 2. Distribution des Trades

```
Trades winners : {len([t for t in trades if t['pnl_eur'] > 0])}/{metrics['total_trades']} ({metrics['win_rate']:.1f}%)
Trades losers  : {len([t for t in trades if t['pnl_eur'] <= 0])}/{metrics['total_trades']} ({100-metrics['win_rate']:.1f}%)

Gains moyens   : +{metrics['avg_win']:.2f}€
Pertes moyennes: -{metrics['avg_loss']:.2f}€
Ratio G/P      : {metrics['avg_win']/metrics['avg_loss']:.2f} {'(favorable)' if metrics['avg_win']/metrics['avg_loss'] > 1 else '(défavorable)'}
```

### 3. Analyse par Exit Reason

"""
    
    # Analyse par raison de sortie
    if len(trades) > 0:
        exit_reasons = {}
        for t in trades:
            reason = t['exit_reason'].replace('EXIT_', '')
            if reason not in exit_reasons:
                exit_reasons[reason] = {'count': 0, 'pnl': 0}
            exit_reasons[reason]['count'] += 1
            exit_reasons[reason]['pnl'] += t['pnl_eur']
        
        report += "| Exit Reason | N Trades | PnL Total | Avg PnL |\n"
        report += "|---|---|---|---|\n"
        for reason, data in sorted(exit_reasons.items(), key=lambda x: x[1]['count'], reverse=True):
            avg_pnl = data['pnl'] / data['count']
            report += f"| {reason} | {data['count']} | {data['pnl']:+.2f}€ | {avg_pnl:+.2f}€ |\n"
    
    report += f"""
### 4. Points Forts
- {'✅ Win Rate ≥ 70%' if wr_pass else '❌ Win Rate < 70%'}
- {'✅ Profit Factor > 1.5' if pf_pass else '❌ Profit Factor ≤ 1.5'}
- {'✅ Drawdown maîtrisé (<20%)' if metrics['max_drawdown'] < 20 else '⚠️ Drawdown élevé'}
- {'✅ Sharpe Ratio > 1' if metrics['sharpe_ratio'] > 1 else '❌ Sharpe Ratio < 1'}

### 5. Points Faibles
- {'PnL quotidien à optimiser' if metrics['pnl_total_eur']/duration_days < 50 else 'RAS'}
- {'Durée moyenne des trades élevée' if metrics['avg_duration_hours'] > 24 else 'RAS'}

### 6. Ajustements Recommandés
- Tester BB à {config['bb_std'] + 0.5}σ pour réduire les faux signaux
- Ajuster thresholds RSI (25/75 au lieu de 30/70)
- Tester TP à 0.5% au lieu du retour à la moyenne
- Ajouter filtre de volume

---

## 📈 Détail des Trades

"""
    
    if len(trades) > 0:
        report += "| # | Entry Date | Exit Date | Type | Entry Price | Exit Price | Entry RSI | Exit RSI | Duration | PnL (€) | Exit Reason |\n"
        report += "|---|---|---|---|---|---|---|---|---|---|---|\n"
        
        for idx, trade in enumerate(trades):
            entry_date = trade['entry_date'].strftime('%m-%d %H:%M')
            exit_date = trade['exit_date'].strftime('%m-%d %H:%M')
            pnl_emoji = '🟢' if trade['pnl_eur'] > 0 else '🔴'
            report += f"| {idx+1} | {entry_date} | {exit_date} | {trade['type']} | {trade['entry_price']:.2f} | {trade['exit_price']:.2f} | {trade['entry_rsi']:.1f} | {trade['exit_rsi']:.1f} | {trade['duration_hours']:.1f}h | {pnl_emoji} {trade['pnl_eur']:+.2f} | {trade['exit_reason']} |\n"
    else:
        report += "*Aucun trade généré*\n"
    
    report += f"""
---

## 🎯 Conclusion

{'✅ PASS — Stratégie viable, prête pour production' if overall_pass else '❌ FAIL — Ajustements nécessaires avant production'}

### Résumé
- **Win Rate** : {metrics['win_rate']:.1f}% {'(objectif ✅)' if wr_pass else '(objectif ❌)'}
- **Profit Factor** : {metrics['profit_factor']:.2f} {'(objectif ✅)' if pf_pass else '(objectif ❌)'}
- **PnL Total** : {metrics['pnl_total_eur']:+.2f}€ sur {duration_days} jours
- **Risque** : Max DD -{metrics['max_drawdown']:.2f}%

### Prochaines Étapes
{'1. Optimiser paramètres (BB σ, RSI thresholds)' if not overall_pass else '1. Développer version production'}
{'2. Backtest sur période plus longue' if overall_pass else '2. Tester sur données out-of-sample'}
3. Ajouter gestion de position sizing dynamique
4. Implémenter surveillance temps réel

---
*Généré le {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*
"""
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 Rapport généré : {output_path}")
    
    data_path = output_path.replace('.md', '_data.csv')
    df.to_csv(data_path)
    print(f"📊 Données sauvegardées : {data_path}")
    
    return overall_pass

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("🔬 BACKTEST #2 : BOLLINGER-RSI DUAL")
    print("=" * 60)
    print()
    
    # 1. Récupérer données
    print("📡 Étape 1/5 : Récupération des données...")
    df = fetch_ohlcv(CONFIG['symbol'], CONFIG['timeframe'], CONFIG['days'])
    print()
    
    # 2. Calcul indicateurs
    print("📐 Étape 2/5 : Calcul Bollinger Bands + RSI...")
    df = calculate_indicators(df, CONFIG)
    print(f"   → BB Middle (fin) : {df['bb_middle'].iloc[-1]:.2f}")
    print(f"   → RSI (fin) : {df['rsi'].iloc[-1]:.1f}")
    print()
    
    # 3. Générer signaux
    print("🚦 Étape 3/5 : Génération des signaux...")
    df = generate_signals(df, CONFIG)
    n_entries = (df['exit_reason'].str.contains('ENTRY', na=False)).sum()
    print(f"   → {n_entries} entrées potentielles")
    print()
    
    # 4. Backtest
    print("💰 Étape 4/5 : Exécution du backtest...")
    trades, df = run_backtest(df, CONFIG)
    print(f"   → {len(trades)} trades exécutés")
    print()
    
    # 5. Métriques
    print("📊 Étape 5/5 : Calcul des métriques...")
    metrics = calculate_metrics(trades, df, CONFIG)
    
    print()
    print("=" * 60)
    print("📈 RÉSULTATS")
    print("=" * 60)
    print(f"Total Trades     : {metrics['total_trades']}")
    print(f"Win Rate         : {metrics['win_rate']:.1f}%")
    print(f"PnL Total        : {metrics['pnl_total_eur']:+.2f}€ ({metrics['pnl_total_pct']:+.2f}%)")
    print(f"PnL/jour         : {metrics['pnl_total_eur']/((df.index[-1] - df.index[0]).days):+.2f}€")
    print(f"Sharpe Ratio     : {metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown     : -{metrics['max_drawdown']:.2f}%")
    print(f"Profit Factor    : {metrics['profit_factor']:.2f}")
    print(f"Avg Duration     : {metrics['avg_duration_hours']:.1f}h")
    print(f"Avg Win/Loss     : +{metrics['avg_win']:.2f}€ / -{metrics['avg_loss']:.2f}€")
    print(f"LONG Trades      : {metrics['long_trades']} (WR: {metrics['long_wr']:.1f}%)")
    print(f"SHORT Trades     : {metrics['short_trades']} (WR: {metrics['short_wr']:.1f}%)")
    print()
    
    # 6. Rapport
    output_path = '/root/.openclaw/workspace/backtests/bollinger-rsi-dual-v1.md'
    passed = generate_report(df, trades, metrics, CONFIG, output_path)
    
    print()
    print("=" * 60)
    if passed:
        print("✅ BACKTEST PASS — WR ≥ 70% et PF > 1.5")
    else:
        print("❌ BACKTEST FAIL — Critères non atteints")
    print("=" * 60)
    
    return passed, metrics

if __name__ == '__main__':
    main()
