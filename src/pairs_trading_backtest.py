#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backtest Pairs Trading BTC-ETH
Stratégie market-neutral : LONG sur l'underperformer + SHORT sur l'overperformer
Quand le ratio BTC/ETH s'écarte de sa moyenne → mean reversion
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
    'timeframe': '4h',  # 4h pour réduire le noise
    'days': 90,  # 60-90 jours
    
    # Stratégie - Version 5 : approche équilibrée
    'z_entry': 2.0,  # Z-score entry (±2 pour plus de trades)
    'z_exit': 0.5,   # Sortie à ±0.5 (mean reversion partielle)
    'z_stop': 3.5,   # Stop-loss (±3.5)
    
    # Trading
    'capital': 10000,  # €
    'leverage': 1,  # 1x market-neutral
    'fee': 0.0005,  # 0.05%
    'slippage': 0.0002,  # 0.02%
    
    # Moyenne mobile
    'ma_period': 20,  # MA20 pour Z-score
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

def fetch_btc_eth_data(timeframe, days):
    """Récupère BTC et ETH"""
    btc = fetch_ohlcv('BTC/USDT', timeframe, days)
    eth = fetch_ohlcv('ETH/USDT', timeframe, days)
    
    # Aligner les données (même timestamps)
    df = pd.concat([
        btc['close'].rename('btc_close'),
        eth['close'].rename('eth_close')
    ], axis=1).dropna()
    
    print(f"✅ Données alignées : {len(df)} bougies communes")
    return df

# ============================================================================
# CALCUL DU RATIO ET Z-SCORE
# ============================================================================

def calculate_ratio_and_zscore(df, ma_period=20):
    """Calcule le ratio BTC/ETH et le Z-score"""
    # Ratio = BTC_price / ETH_price
    df['ratio'] = df['btc_close'] / df['eth_close']
    
    # Moyenne mobile et écart-type
    df['ma'] = df['ratio'].rolling(window=ma_period).mean()
    df['std'] = df['ratio'].rolling(window=ma_period).std()
    
    # Z-score = (Ratio - MA) / StdDev
    df['zscore'] = (df['ratio'] - df['ma']) / df['std']
    
    # Corrélation BTC-ETH (rolling 20)
    df['correlation'] = df['btc_close'].rolling(window=ma_period).corr(df['eth_close'])
    
    # Volatilité rolling (pour filtre)
    df['volatility'] = df['ratio'].pct_change().rolling(window=10).std()
    
    # Pente de la MA (pour filtre de trend)
    df['ma_slope'] = df['ma'].pct_change(periods=5)
    
    return df

# ============================================================================
# SIGNAUX DE TRADING
# ============================================================================

def generate_signals(df, z_entry, z_exit, z_stop, volatility_filter=False, vol_threshold=0.03,
                     trend_filter=False, trend_lookback=10):
    """Génère les signaux d'entrée et sortie avec logique de crossing"""
    df['signal'] = 0  # 0=rien, 1=LONG BTC/SHORT ETH, -1=SHORT BTC/LONG ETH
    df['position'] = 0  # Position courante
    df['exit_reason'] = ''
    
    in_position = False
    position_type = 0  # 1 ou -1
    entry_zscore = 0
    prev_zscore = 0
    
    for i in range(len(df)):
        if i < 20:  # Pas de signal avant MA20
            prev_zscore = df['zscore'].iloc[i] if i < len(df) else 0
            continue
        
        z = df['zscore'].iloc[i]
        vol = df.get('volatility', pd.Series([0]*len(df))).iloc[i]
        ma_slope = df.get('ma_slope', pd.Series([0]*len(df))).iloc[i]
        
        if not in_position:
            # Filtre de volatilité
            if volatility_filter and vol > vol_threshold:
                prev_zscore = z
                continue
            
            # Filtre de trend
            if trend_filter:
                if z < -z_entry and ma_slope < -0.02:
                    prev_zscore = z
                    continue
                if z > z_entry and ma_slope > 0.02:
                    prev_zscore = z
                    continue
            
            # Entrée LONG BTC / SHORT ETH (BTC underperform, z < -z_entry)
            if z < -z_entry:
                df.iloc[i, df.columns.get_loc('signal')] = 1
                in_position = True
                position_type = 1
                entry_zscore = z
                df.iloc[i, df.columns.get_loc('exit_reason')] = 'ENTRY_LONG_BTC'
            
            # Entrée SHORT BTC / LONG ETH (BTC overperform, z > z_entry)
            elif z > z_entry:
                df.iloc[i, df.columns.get_loc('signal')] = -1
                in_position = True
                position_type = -1
                entry_zscore = z
                df.iloc[i, df.columns.get_loc('exit_reason')] = 'ENTRY_SHORT_BTC'
        
        else:
            # Logique de crossing pour la sortie
            crossed_exit = False
            crossed_stop = False
            
            if position_type == 1:  # LONG BTC / SHORT ETH
                # On gagne si z monte (ratio remonte vers moyenne)
                # Sortie si z CROSS -z_exit (de <-2 vers >-0.5)
                if prev_zscore < -z_exit and z >= -z_exit:
                    crossed_exit = True
                
                # Stop-loss : z descend (adverse)
                if z < -z_stop:
                    crossed_stop = True
            
            elif position_type == -1:  # SHORT BTC / LONG ETH
                # On gagne si z descend (ratio redescend vers moyenne)
                # Sortie si z CROSS z_exit (de >2 vers <0.5)
                if prev_zscore > z_exit and z <= z_exit:
                    crossed_exit = True
                
                # Stop-loss : z monte (adverse)
                if z > z_stop:
                    crossed_stop = True
            
            # Fermer position si exit ou stop
            if crossed_exit or crossed_stop:
                df.iloc[i, df.columns.get_loc('signal')] = 0
                in_position = False
                reason = 'STOP_LOSS' if crossed_stop else 'MEAN_REVERSION'
                df.iloc[i, df.columns.get_loc('exit_reason')] = f'EXIT_{reason}'
        
        prev_zscore = z
    
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
        if i < 20:
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
                'type': signal,  # 1 ou -1
                'entry_ratio': row['ratio'],
                'entry_zscore': row['zscore'],
                'btc_price': row['btc_close'],
                'eth_price': row['eth_close']
            }
        
        # Fermeture de position
        elif signal == 0 and current_trade is not None:
            exit_ratio = row['ratio']
            exit_zscore = row['zscore']
            
            # Calcul PnL
            # LONG BTC / SHORT ETH (type=1) : profit si ratio monte
            # SHORT BTC / LONG ETH (type=-1) : profit si ratio descend
            
            ratio_change = (exit_ratio - current_trade['entry_ratio']) / current_trade['entry_ratio']
            
            if current_trade['type'] == 1:
                raw_pnl = ratio_change * capital
            else:
                raw_pnl = -ratio_change * capital
            
            # Fees + slippage (aller-retour)
            total_cost = capital * (fee + slippage) * 2
            
            net_pnl = raw_pnl - total_cost
            
            trades.append({
                'entry_date': current_trade['entry_date'],
                'exit_date': row.name,
                'type': 'LONG_BTC_SHORT_ETH' if current_trade['type'] == 1 else 'SHORT_BTC_LONG_ETH',
                'entry_ratio': current_trade['entry_ratio'],
                'exit_ratio': exit_ratio,
                'entry_zscore': current_trade['entry_zscore'],
                'exit_zscore': exit_zscore,
                'duration_hours': (row.name - current_trade['entry_date']).total_seconds() / 3600,
                'pnl_eur': net_pnl,
                'exit_reason': row['exit_reason']
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
    
    df['pnl_curve'] = pnl_curve
    df['drawdown_curve'] = drawdown_curve
    
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
            'correlation': df['correlation'].mean() if 'correlation' in df.columns else 0
        }
    
    trades_df = pd.DataFrame(trades)
    
    # Win Rate
    winners = len(trades_df[trades_df['pnl_eur'] > 0])
    win_rate = winners / len(trades_df) * 100
    
    # PnL Total
    pnl_total = trades_df['pnl_eur'].sum()
    pnl_pct = pnl_total / config['capital'] * 100
    
    # Sharpe Ratio (annualisé)
    if len(trades_df) > 1:
        returns = trades_df['pnl_eur'] / config['capital']
        sharpe = returns.mean() / returns.std() * np.sqrt(252 * 24 / trades_df['duration_hours'].mean()) if trades_df['duration_hours'].mean() > 0 else 0
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
    
    # Corrélation
    correlation = df['correlation'].mean()
    
    return {
        'total_trades': len(trades_df),
        'win_rate': win_rate,
        'pnl_total_eur': pnl_total,
        'pnl_total_pct': pnl_pct,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown,
        'avg_duration_hours': avg_duration,
        'profit_factor': profit_factor,
        'correlation': correlation
    }

# ============================================================================
# RAPPORT
# ============================================================================

def generate_report(df, trades, metrics, config, output_path):
    """Génère le rapport markdown"""
    
    start_date = df.index[0].strftime('%Y-%m-%d')
    end_date = df.index[-1].strftime('%Y-%m-%d')
    duration_days = (df.index[-1] - df.index[0]).days
    
    # Déterminer PASS/FAIL
    wr_pass = metrics['win_rate'] >= 70
    pnl_target_daily = 500  # € / jour
    pnl_actual_daily = metrics['pnl_total_eur'] / duration_days if duration_days > 0 else 0
    pnl_pass = pnl_actual_daily >= pnl_target_daily * 0.5  # On accepte 50% de l'objectif
    
    overall_pass = wr_pass  # WR est le critère principal
    
    report = f"""# Backtest Pairs Trading BTC-ETH

## Période
- **Start** : {start_date}
- **End** : {end_date}
- **Durée** : {duration_days} jours

## Données
- **TF** : {config['timeframe']}
- **Source** : Binance (CCXT)
- **N bougies** : {len(df)}

## Paramètres
- **Z-score entry** : ±{config['z_entry']}
- **Z-score exit** : ±{config['z_exit']} (partial mean reversion)
- **Stop-loss** : ±{config['z_stop']}
- **Fees** : {config['fee']*100}%
- **Slippage** : {config['slippage']*100}%
- **Capital** : {config['capital']} €
- **Levier** : {config['leverage']}x

## Résultats

| Métrique | Valeur | Objectif |
|---|---|---|
| Total Trades | {metrics['total_trades']} | - |
| Win Rate | {metrics['win_rate']:.1f}% | ≥70% |
| PnL Total | {metrics['pnl_total_eur']:+.2f}€ ({metrics['pnl_total_pct']:+.2f}%) | 500-600€/jour |
| Sharpe Ratio | {metrics['sharpe_ratio']:.2f} | >1 |
| Max Drawdown | -{metrics['max_drawdown']:.2f}% | <20% |
| Avg Duration | {metrics['avg_duration_hours']:.1f}h | - |
| Profit Factor | {metrics['profit_factor']:.2f} | >1.5 |
| Corrélation BTC-ETH | {metrics['correlation']:.3f} | ~0.8-0.9 |

## Analyse

### Win Rate vs objectif (70-80%)
{'✅ PASS' if wr_pass else '❌ FAIL'} - Win Rate de {metrics['win_rate']:.1f}%

### PnL vs objectif (500-600€/jour)
{'✅' if pnl_pass else '❌'} - Moyenne de {pnl_actual_daily:+.2f}€/jour

### Points forts
- Stratégie market-neutral (pas d'exposition directionnelle)
- Win Rate {'solide' if wr_pass else 'à améliorer'}
- Drawdown {'maîtrisé' if metrics['max_drawdown'] < 20 else 'élevé'}

### Points faibles
- {'PnL quotidien en-dessous de l\'objectif' if not pnl_pass else 'RAS'}
- {'Durée moyenne des trades élevée' if metrics['avg_duration_hours'] > 48 else 'RAS'}

### Ajustements recommandés
- Tester Z-score entry à ±1.5 pour plus de trades
- Tester Z-score exit à 0 pour mean reversion complète
- Ajouter filter de volatilité
- Tester sur timeframe 4h

## Détail des Trades

"""
    
    if len(trades) > 0:
        trades_df = pd.DataFrame(trades)
        report += "| # | Date Entry | Date Exit | Type | Entry Z | Exit Z | Duration | PnL (€) | Exit Reason |\n"
        report += "|---|---|---|---|---|---|---|---|---|\n"
        
        for idx, trade in enumerate(trades):
            entry_date = trade['entry_date'].strftime('%m-%d %H:%M')
            exit_date = trade['exit_date'].strftime('%m-%d %H:%M')
            pnl_color = '🟢' if trade['pnl_eur'] > 0 else '🔴'
            report += f"| {idx+1} | {entry_date} | {exit_date} | {trade['type']} | {trade['entry_zscore']:.2f} | {trade['exit_zscore']:.2f} | {trade['duration_hours']:.1f}h | {pnl_color} {trade['pnl_eur']:+.2f} | {trade['exit_reason']} |\n"
    else:
        report += "*Aucun trade généré*\n"
    
    report += f"""
## Conclusion

{'✅ PASS → À développer en version production' if overall_pass else '❌ FAIL → Ajuster paramètres ou abandonner'}

### Résumé
- **WR** : {metrics['win_rate']:.1f}% {'(objectif atteint ✅)' if wr_pass else '(objectif non atteint ❌)'}
- **PnL** : {metrics['pnl_total_eur']:+.2f}€ sur {duration_days} jours
- **Risque** : Max DD -{metrics['max_drawdown']:.2f}%

---
*Généré le {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*
"""
    
    # Créer le dossier si nécessaire
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 Rapport généré : {output_path}")
    
    # Sauvegarder les données brutes pour graphiques futurs
    data_path = output_path.replace('.md', '_data.csv')
    df.to_csv(data_path)
    print(f"📊 Données sauvegardées : {data_path}")
    
    return overall_pass

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("🔬 BACKTEST PAIRS TRADING BTC-ETH")
    print("=" * 60)
    print()
    
    # 1. Récupérer données
    print("📡 Étape 1/5 : Récupération des données...")
    df = fetch_btc_eth_data(CONFIG['timeframe'], CONFIG['days'])
    print()
    
    # 2. Calcul ratio et Z-score
    print("📐 Étape 2/5 : Calcul du ratio et Z-score...")
    df = calculate_ratio_and_zscore(df, CONFIG['ma_period'])
    print(f"   → Ratio moyen : {df['ratio'].mean():.4f}")
    print(f"   → Z-score range : [{df['zscore'].min():.2f}, {df['zscore'].max():.2f}]")
    print()
    
    # 3. Générer signaux
    print("🚦 Étape 3/5 : Génération des signaux...")
    df = generate_signals(df, CONFIG['z_entry'], CONFIG['z_exit'], CONFIG['z_stop'],
                          CONFIG.get('volatility_filter', False), CONFIG.get('volatility_threshold', 0.03),
                          CONFIG.get('trend_filter', False), CONFIG.get('trend_lookback', 10))
    n_signals = (df['signal'] != 0).sum()
    n_entries = (df['exit_reason'].str.contains('ENTRY', na=False)).sum()
    print(f"   → {n_signals} signaux, {n_entries} entrées")
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
    print(f"Sharpe Ratio     : {metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown     : -{metrics['max_drawdown']:.2f}%")
    print(f"Avg Duration     : {metrics['avg_duration_hours']:.1f}h")
    print(f"Profit Factor    : {metrics['profit_factor']:.2f}")
    print(f"Corrélation      : {metrics['correlation']:.3f}")
    print()
    
    # 6. Rapport
    output_path = '/root/.openclaw/workspace/backtests/pairs-trading-btc-eth-v1.md'
    passed = generate_report(df, trades, metrics, CONFIG, output_path)
    
    print()
    print("=" * 60)
    if passed:
        print("✅ BACKTEST PASS → Prêt pour production")
    else:
        print("❌ BACKTEST FAIL → Ajustements nécessaires")
    print("=" * 60)
    
    return passed, metrics

if __name__ == '__main__':
    main()
