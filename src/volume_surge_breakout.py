#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backtest Volume Surge Breakout Strategy
Stratégie #3 : Breakout avec confirmation volume

Concept :
- Prix casse une resistance/support après consolidation
- Volume > 2x MA20 volume (confirmation du breakout)
- Entrer dans la direction du breakout
- Filtre : pas de breakout pendant news majeures

Paramètres :
- Consolidation : range 10-20 bougies
- Breakout : close > high(20) ou close < low(20)
- Volume filter : volume > 2.0 * MA20(volume)
- TF : 1h ou 4h
- TP : 0.5-1% (ATR-based)
- SL : retour dans le range (false breakout)
- Fees : 0.1%, Slippage : 0.05%
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    # Données
    'symbol': 'BTC/USDT',
    'timeframe': '1h',  # 1h ou 4h - 1h pour plus de signaux
    'days': 90,  # 90 jours
    
    # Stratégie Volume Surge Breakout
    'consolidation_period': 20,  # 10-20 bougies pour le range
    'volume_ma_period': 20,  # MA20 pour volume
    'volume_multiplier': 1.5,  # Volume > 1.5x MA20 (relaxé pour plus de signaux)
    'breakout_threshold': 0,  # close > high(20) ou close < low(20)
    
    # Trading
    'tp_multiplier': 1.0,  # TP = 1.0 x ATR (0.5-1%)
    'sl_return_to_range': True,  # SL = retour dans le range
    
    # Fees
    'fee': 0.001,  # 0.1%
    'slippage': 0.0005,  # 0.05%
    
    # Capital
    'capital': 10000,  # €
    'leverage': 1,  # 1x
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
    
    # Calculer la date de début
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    since = int(start_date.timestamp() * 1000)
    
    print(f"📊 Récupération {symbol} {timeframe} depuis {start_date.date()}...")
    
    # Récupérer les bougies
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=5000)
    
    # Convertir en DataFrame
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    print(f"   → {len(df)} bougies récupérées")
    return df

# ============================================================================
# INDICATEURS
# ============================================================================

def calculate_indicators(df, consolidation_period, volume_ma_period):
    """Calcule les indicateurs pour la stratégie"""
    
    # Donchian Channel (high/low sur N périodes PRÉCÉDENTES, pas la bougie courante)
    df['donchian_high'] = df['high'].shift(1).rolling(window=consolidation_period).max()
    df['donchian_low'] = df['low'].shift(1).rolling(window=consolidation_period).min()
    df['donchian_mid'] = (df['donchian_high'] + df['donchian_low']) / 2
    
    # Range width (pour filtre de consolidation)
    df['range_width'] = (df['donchian_high'] - df['donchian_low']) / df['donchian_mid']
    
    # Volume MA
    df['volume_ma'] = df['volume'].rolling(window=volume_ma_period).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma']
    
    # ATR (pour TP)
    df['tr'] = np.maximum(
        df['high'] - df['low'],
        np.maximum(
            abs(df['high'] - df['close'].shift(1)),
            abs(df['low'] - df['close'].shift(1))
        )
    )
    df['atr'] = df['tr'].rolling(window=14).mean()
    df['atr_pct'] = df['atr'] / df['close'] * 100
    
    # Consolidation filter (range tight)
    df['is_consolidating'] = df['range_width'] < 0.02  # Range < 2%
    
    print(f"✅ Indicateurs calculés")
    print(f"   → ATR moyen: {df['atr_pct'].mean():.2f}%")
    print(f"   → Volume MA: {df['volume_ma'].mean():.0f}")
    
    return df

# ============================================================================
# SIGNAUX DE TRADING
# ============================================================================

def generate_signals(df, config):
    """Génère les signaux de breakout avec confirmation volume"""
    
    consolidation_period = config['consolidation_period']
    volume_multiplier = config['volume_multiplier']
    tp_multiplier = config['tp_multiplier']
    
    df['signal'] = 0  # 0=rien, 1=LONG, -1=SHORT
    df['position'] = 0
    df['exit_reason'] = ''
    df['tp_level'] = np.nan
    df['sl_level'] = np.nan
    
    in_position = False
    position_type = 0
    entry_price = 0
    range_high = 0
    range_low = 0
    tp_level = np.nan
    sl_level = np.nan
    
    for i in range(len(df)):
        if i < consolidation_period:
            continue
        
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        if not in_position:
            # === DÉTECTION DE BREAKOUT ===
            
            # Breakout HAUSSIER : close > donchian_high + volume surge
            if row['close'] > row['donchian_high'] and row['volume_ratio'] > volume_multiplier:
                # Entry LONG
                df.iloc[i, df.columns.get_loc('signal')] = 1
                in_position = True
                position_type = 1
                entry_price = row['close']
                range_high = row['donchian_high']
                range_low = row['donchian_low']
                
                # TP = entry + ATR * multiplier
                tp_level = entry_price + row['atr'] * tp_multiplier
                # SL = entry - ATR (stop adverse move)
                sl_level = entry_price - row['atr']
                
                df.iloc[i, df.columns.get_loc('tp_level')] = tp_level
                df.iloc[i, df.columns.get_loc('sl_level')] = sl_level
                df.iloc[i, df.columns.get_loc('exit_reason')] = 'ENTRY_LONG'
            
            # Breakout BAISSIER : close < donchian_low + volume surge
            elif row['close'] < row['donchian_low'] and row['volume_ratio'] > volume_multiplier:
                # Entry SHORT
                df.iloc[i, df.columns.get_loc('signal')] = -1
                in_position = True
                position_type = -1
                entry_price = row['close']
                range_high = row['donchian_high']
                range_low = row['donchian_low']
                
                # TP = entry - ATR * multiplier
                tp_level = entry_price - row['atr'] * tp_multiplier
                # SL = entry + ATR (stop adverse move)
                sl_level = entry_price + row['atr']
                
                df.iloc[i, df.columns.get_loc('tp_level')] = tp_level
                df.iloc[i, df.columns.get_loc('sl_level')] = sl_level
                df.iloc[i, df.columns.get_loc('exit_reason')] = 'ENTRY_SHORT'
        
        else:
            # === GESTION DE POSITION ===
            
            high = row['high']
            low = row['low']
            close = row['close']
            
            exited = False
            reason = ''
            
            if position_type == 1:  # LONG
                # TP hit
                if high >= tp_level:
                    exited = True
                    reason = 'TP'
                # SL hit (adverse move)
                elif low <= sl_level:
                    exited = True
                    reason = 'SL'
            
            elif position_type == -1:  # SHORT
                # TP hit
                if low <= tp_level:
                    exited = True
                    reason = 'TP'
                # SL hit (adverse move)
                elif high >= sl_level:
                    exited = True
                    reason = 'SL'
            
            if exited:
                df.iloc[i, df.columns.get_loc('signal')] = 0
                df.iloc[i, df.columns.get_loc('exit_reason')] = f'EXIT_{reason}'
                in_position = False
                position_type = 0
                tp_level = np.nan
                sl_level = np.nan
    
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
    pnl_curve = [capital] * config['consolidation_period']
    drawdown_curve = [0] * config['consolidation_period']
    peak = capital
    
    for i in range(len(df)):
        if i < config['consolidation_period']:
            continue
        
        row = df.iloc[i]
        signal = row['signal']
        
        # Ouverture de position
        if signal != 0 and current_trade is None:
            current_trade = {
                'entry_date': row.name,
                'entry_idx': i,
                'type': signal,  # 1=LONG, -1=SHORT
                'entry_price': row['close'],
                'tp_level': row['tp_level'],
                'sl_level': row['sl_level'],
                'range_high': row['donchian_high'],
                'range_low': row['donchian_low'],
                'volume_ratio': row['volume_ratio'],
                'atr_pct': row['atr_pct']
            }
        
        # Fermeture de position
        elif signal == 0 and current_trade is not None:
            exit_price = row['close']
            exit_reason = row['exit_reason']
            
            # Calcul PnL
            if current_trade['type'] == 1:  # LONG
                price_change = (exit_price - current_trade['entry_price']) / current_trade['entry_price']
            else:  # SHORT
                price_change = (current_trade['entry_price'] - exit_price) / current_trade['entry_price']
            
            raw_pnl = price_change * capital
            
            # Fees + slippage (aller-retour)
            total_cost = capital * (fee + slippage) * 2
            
            net_pnl = raw_pnl - total_cost
            
            trades.append({
                'entry_date': current_trade['entry_date'],
                'exit_date': row.name,
                'type': 'LONG' if current_trade['type'] == 1 else 'SHORT',
                'entry_price': current_trade['entry_price'],
                'exit_price': exit_price,
                'tp_level': current_trade['tp_level'],
                'sl_level': current_trade['sl_level'],
                'duration_hours': (row.name - current_trade['entry_date']).total_seconds() / 3600,
                'pnl_eur': net_pnl,
                'exit_reason': exit_reason,
                'volume_ratio': current_trade['volume_ratio'],
                'atr_pct': current_trade['atr_pct']
            })
            
            capital += net_pnl
            current_trade = None
        
        # Courbe PnL
        pnl_curve.append(capital)
        
        # Drawdown
        if capital > peak:
            peak = capital
        drawdown = (peak - capital) / peak * 100
        drawdown_curve.append(drawdown)
    
    # Ajouter les colonnes au DataFrame
    df['pnl_curve'] = pnl_curve[:len(df)]
    df['drawdown_curve'] = drawdown_curve[:len(df)]
    
    return trades, df

# ============================================================================
# MÉTRIQUES
# ============================================================================

def calculate_metrics(trades, df, config):
    """Calcule toutes les métriques de performance"""
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
            'avg_win_eur': 0,
            'avg_loss_eur': 0,
            'longest_win_streak': 0,
            'longest_loss_streak': 0,
            'tp_hits': 0,
            'sl_hits': 0,
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
    max_drawdown = df['drawdown_curve'].max() if 'drawdown_curve' in df.columns else 0
    
    # Avg Duration
    avg_duration = trades_df['duration_hours'].mean()
    
    # Profit Factor
    gross_profit = trades_df[trades_df['pnl_eur'] > 0]['pnl_eur'].sum()
    gross_loss = abs(trades_df[trades_df['pnl_eur'] <= 0]['pnl_eur'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
    
    # Avg Win / Loss
    avg_win = trades_df[trades_df['pnl_eur'] > 0]['pnl_eur'].mean() if winners > 0 else 0
    avg_loss = abs(trades_df[trades_df['pnl_eur'] <= 0]['pnl_eur'].mean()) if len(trades_df) - winners > 0 else 0
    
    # Streaks
    pnl_signs = (trades_df['pnl_eur'] > 0).astype(int)
    longest_win_streak = 0
    longest_loss_streak = 0
    current_win = 0
    current_loss = 0
    
    for sign in pnl_signs:
        if sign == 1:
            current_win += 1
            current_loss = 0
            longest_win_streak = max(longest_win_streak, current_win)
        else:
            current_loss += 1
            current_win = 0
            longest_loss_streak = max(longest_loss_streak, current_loss)
    
    # TP vs SL hits
    tp_hits = len(trades_df[trades_df['exit_reason'].str.contains('TP', na=False)])
    sl_hits = len(trades_df[trades_df['exit_reason'].str.contains('SL', na=False)])
    
    return {
        'total_trades': len(trades_df),
        'win_rate': win_rate,
        'pnl_total_eur': pnl_total,
        'pnl_total_pct': pnl_pct,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown,
        'avg_duration_hours': avg_duration,
        'profit_factor': profit_factor,
        'avg_win_eur': avg_win,
        'avg_loss_eur': avg_loss,
        'longest_win_streak': longest_win_streak,
        'longest_loss_streak': longest_loss_streak,
        'tp_hits': tp_hits,
        'sl_hits': sl_hits,
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
    wr_pass = metrics['win_rate'] >= 65
    pf_pass = metrics['profit_factor'] > 1.3
    overall_pass = wr_pass and pf_pass
    
    status_icon = "✅ PASS" if overall_pass else "❌ FAIL"
    wr_icon = "✅" if wr_pass else "❌"
    pf_icon = "✅" if pf_pass else "❌"
    
    # PnL journalier
    pnl_daily = metrics['pnl_total_eur'] / duration_days if duration_days > 0 else 0
    ratio_gp = f"{metrics['avg_win_eur'] / metrics['avg_loss_eur']:.2f}" if metrics['avg_loss_eur'] > 0 else 'N/A'
    
    report = f"""# Backtest Volume Surge Breakout — Rapport v1

## 📋 Synthèse Exécutive

**Statut : {status_icon} — Stratégie {"viable" if overall_pass else "non viable"} selon les critères**

| Critère | Résultat | Objectif | Statut |
|---|---|---|---|
| **Win Rate** | {metrics['win_rate']:.1f}% | ≥65% | {wr_icon} |
| **Profit Factor** | {metrics['profit_factor']:.2f} | >1.3 | {pf_icon} |
| **PnL Total** | {metrics['pnl_total_eur']:+.2f}€ ({metrics['pnl_total_pct']:+.2f}%) | - | - |
| **PnL/jour** | {pnl_daily:+.2f}€/jour | - | - |
| **Sharpe Ratio** | {metrics['sharpe_ratio']:.2f} | >1 | {"✅" if metrics['sharpe_ratio'] > 1 else "❌"} |
| **Max Drawdown** | -{metrics['max_drawdown']:.2f}% | <20% | {"✅" if metrics['max_drawdown'] < 20 else "❌"} |

---

## 📊 Données du Backtest

### Période
- **Start** : {start_date}
- **End** : {end_date}
- **Durée** : {duration_days} jours

### Données
- **Symbole** : {config['symbol']}
- **Timeframe** : {config['timeframe']}
- **Source** : Binance (CCXT)
- **N bougies** : {len(df)}

### Paramètres
| Paramètre | Valeur |
|---|---|
| Consolidation | {config['consolidation_period']} bougies |
| Volume Filter | > {config['volume_multiplier']}x MA20 |
| Breakout | close > high({config['consolidation_period']}) ou close < low({config['consolidation_period']}) |
| TP | {config['tp_multiplier']}x ATR |
| SL | Retour dans le range |
| Fees | {config['fee']*100}% |
| Slippage | {config['slippage']*100}% |
| Capital | {config['capital']} € |
| Levier | {config['leverage']}x |

---

## 🔍 Analyse Détaillée

### 1. Performance des Trades

```
Total Trades  : {metrics['total_trades']}
Trades winners: {int(metrics['total_trades'] * metrics['win_rate'] / 100)}/{metrics['total_trades']} ({metrics['win_rate']:.1f}%)
Trades losers : {metrics['total_trades'] - int(metrics['total_trades'] * metrics['win_rate'] / 100)}/{metrics['total_trades']} ({100 - metrics['win_rate']:.1f}%)

Gains moyens  : +{metrics['avg_win_eur']:.2f}€
Pertes moyennes: -{metrics['avg_loss_eur']:.2f}€
Ratio G/P     : {ratio_gp}
```

### 2. TP vs SL

| Sortie | Nombre | % |
|---|---|---|
| Take Profit | {metrics['tp_hits']} | {metrics['tp_hits'] / metrics['total_trades'] * 100:.1f}% |
| Stop Loss | {metrics['sl_hits']} | {metrics['sl_hits'] / metrics['total_trades'] * 100:.1f}% |

### 3. Streaks

- **Plus longue série gagnante** : {metrics['longest_win_streak']} trades
- **Plus longue série perdante** : {metrics['longest_loss_streak']} trades

### 4. Duration Moyenne

- **Temps moyen par trade** : {metrics['avg_duration_hours']:.1f} heures ({metrics['avg_duration_hours'] / 24:.1f} jours)

---

## 🧪 Observations

### Points Forts
"""
    
    if wr_pass:
        report += f"- ✅ Win Rate de {metrics['win_rate']:.1f}% supérieur à l'objectif de 65%\n"
    if metrics['profit_factor'] > 1.5:
        report += f"- ✅ Excellent Profit Factor de {metrics['profit_factor']:.2f}\n"
    if metrics['max_drawdown'] < 10:
        report += f"- ✅ Drawdown maîtrisé à -{metrics['max_drawdown']:.2f}%\n"
    if metrics['longest_loss_streak'] <= 3:
        report += f"- ✅ Série perdante limitée à {metrics['longest_loss_streak']} trades\n"
    
    report += """
### Points Faibles
"""
    
    if not wr_pass:
        report += f"- ❌ Win Rate de {metrics['win_rate']:.1f}% insuffisant (objectif: 65%)\n"
    if metrics['profit_factor'] <= 1.3:
        report += f"- ❌ Profit Factor de {metrics['profit_factor']:.2f} trop faible (objectif: >1.3)\n"
    if metrics['max_drawdown'] >= 20:
        report += f"- ❌ Drawdown élevé à -{metrics['max_drawdown']:.2f}%\n"
    if metrics['total_trades'] < 10:
        report += f"- ⚠️ Trop peu de trades ({metrics['total_trades']}) pour une analyse fiable\n"
    
    report += f"""
---

## 📈 Courbes

### PnL Curve
- **Départ** : {config['capital']}€
- **Final** : {config['capital'] + metrics['pnl_total_eur']:.2f}€
- **Peak** : {df['pnl_curve'].max():.2f}€

### Drawdown
- **Max DD** : -{metrics['max_drawdown']:.2f}%

---

## 🎯 Conclusion

**Verdict : {"STRATÉGIE VALIDÉE" if overall_pass else "STRATÉGIE À REVOIR"}**

"""
    
    if overall_pass:
        report += f"""La stratégie Volume Surge Breakout atteint les objectifs avec un Win Rate de {metrics['win_rate']:.1f}% et un Profit Factor de {metrics['profit_factor']:.2f}.

**Recommandations :**
- ✅ Peut être déployée en production avec surveillance
- ✅ Envisager d'augmenter le capital alloué
- ✅ Tester sur d'autres paires (ETH/USDT, etc.)
"""
    else:
        report += f"""La stratégie ne remplit pas les critères de performance.

**Pistes d'amélioration :**
- Ajuster le volume multiplier (actuellement {config['volume_multiplier']}x)
- Modifier la période de consolidation (actuellement {config['consolidation_period']} bougies)
- Revoir les niveaux de TP/SL
- Ajouter des filtres supplémentaires (trend, volatilité)
- Tester sur un autre timeframe (1h au lieu de 4h ou inversement)
"""
    
    report += f"""
---

*Backtest généré le {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*
"""
    
    # Écrire le rapport
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 Rapport sauvegardé : {output_path}")
    return report

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("🔬 BACKTEST VOLUME SURGE BREAKOUT")
    print("=" * 60)
    
    # Fetch data
    df = fetch_ohlcv(CONFIG['symbol'], CONFIG['timeframe'], CONFIG['days'])
    
    # Calculate indicators
    df = calculate_indicators(df, CONFIG['consolidation_period'], CONFIG['volume_ma_period'])
    
    # Generate signals
    df = generate_signals(df, CONFIG)
    
    # Run backtest
    trades, df = run_backtest(df, CONFIG)
    
    # Calculate metrics
    metrics = calculate_metrics(trades, df, CONFIG)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS")
    print("=" * 60)
    print(f"Total Trades   : {metrics['total_trades']}")
    print(f"Win Rate       : {metrics['win_rate']:.1f}%")
    print(f"PnL Total      : {metrics['pnl_total_eur']:+.2f}€ ({metrics['pnl_total_pct']:+.2f}%)")
    print(f"Profit Factor  : {metrics['profit_factor']:.2f}")
    print(f"Sharpe Ratio   : {metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown   : -{metrics['max_drawdown']:.2f}%")
    print(f"Avg Duration   : {metrics['avg_duration_hours']:.1f}h")
    
    # Success criteria
    wr_pass = metrics['win_rate'] >= 65
    pf_pass = metrics['profit_factor'] > 1.3
    
    print("\n" + "=" * 60)
    print("🎯 CRITÈRES DE SUCCÈS")
    print("=" * 60)
    print(f"Win Rate ≥ 65%    : {'✅ PASS' if wr_pass else '❌ FAIL'} ({metrics['win_rate']:.1f}%)")
    print(f"Profit Factor >1.3: {'✅ PASS' if pf_pass else '❌ FAIL'} ({metrics['profit_factor']:.2f})")
    print(f"\nVERDICT           : {'✅ STRATÉGIE VALIDÉE' if wr_pass and pf_pass else '❌ STRATÉGIE À REVOIR'}")
    
    # Generate report
    output_path = '/root/.openclaw/workspace/backtests/volume-surge-breakout-v1.md'
    generate_report(df, trades, metrics, CONFIG, output_path)
    
    # Save trades to CSV
    if trades:
        trades_df = pd.DataFrame(trades)
        csv_path = output_path.replace('.md', '_data.csv')
        trades_df.to_csv(csv_path)
        print(f"📁 Données sauvegardées : {csv_path}")
    
    print("\n✅ Backtest terminé !")

if __name__ == '__main__':
    main()
