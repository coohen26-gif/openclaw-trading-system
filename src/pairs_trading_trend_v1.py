#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backtest Pairs Trading BTC-ETH — TREND FOLLOWING
Version modifiée : Au lieu de mean-reversion, on suit le trend du ratio

Concept :
- Ratio BTC/ETH = BTC_price / ETH_price
- Z-score = (Ratio - MA20) / StdDev20
- Si Z-score > +2 → Ratio monte → LONG BTC + SHORT ETH (trend following)
- Si Z-score < -2 → Ratio descend → SHORT BTC + LONG ETH
- Sortie : Z-score retour à 0 OU Z-score s'inverse (±0.5)
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
    'timeframe': '4h',
    'days': 90,
    
    # Stratégie - TREND FOLLOWING
    'z_entry': 2.0,    # Entry quand Z > +2 ou Z < -2
    'z_exit': 0.5,     # Exit quand Z revient vers 0 (cross ±0.5)
    'z_stop': 3.5,     # Stop-loss si Z continue contre nous
    
    # Trading
    'capital': 10000,  # €
    'leverage': 1,
    'fee': 0.001,      # 0.1%
    'slippage': 0.0005, # 0.05%
    
    # Moyenne mobile
    'ma_period': 20,
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

def fetch_btc_eth_data(timeframe, days):
    """Récupère BTC et ETH"""
    btc = fetch_ohlcv('BTC/USDT', timeframe, days)
    eth = fetch_ohlcv('ETH/USDT', timeframe, days)
    
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
    df['ratio'] = df['btc_close'] / df['eth_close']
    df['ma'] = df['ratio'].rolling(window=ma_period).mean()
    df['std'] = df['ratio'].rolling(window=ma_period).std()
    df['zscore'] = (df['ratio'] - df['ma']) / df['std']
    df['correlation'] = df['btc_close'].rolling(window=ma_period).corr(df['eth_close'])
    df['volatility'] = df['ratio'].pct_change().rolling(window=10).std()
    df['ma_slope'] = df['ma'].pct_change(periods=5)
    return df

# ============================================================================
# SIGNAUX DE TRADING - TREND FOLLOWING
# ============================================================================

def generate_signals_trend(df, z_entry, z_exit, z_stop):
    """
    Génère les signaux pour le trend-following du ratio
    
    TREND FOLLOWING LOGIC:
    - Z > +z_entry → Ratio monte fort → LONG BTC / SHORT ETH (on suit la hausse)
    - Z < -z_entry → Ratio descend fort → SHORT BTC / LONG ETH (on suit la baisse)
    - Exit : Z revient vers 0 (cross ±z_exit)
    - SL : Z continue contre nous (> z_stop ou < -z_stop)
    """
    df['signal'] = 0
    df['position'] = 0
    df['exit_reason'] = ''
    
    in_position = False
    position_type = 0
    entry_zscore = 0
    prev_zscore = 0
    
    for i in range(len(df)):
        if i < 20:
            prev_zscore = df['zscore'].iloc[i] if i < len(df) else 0
            continue
        
        z = df['zscore'].iloc[i]
        
        if not in_position:
            # ENTRÉE TREND FOLLOWING
            # Z > +2 → Ratio au-dessus de sa moyenne → trend HAUSSE → LONG BTC/SHORT ETH
            if z > z_entry:
                df.iloc[i, df.columns.get_loc('signal')] = 1
                in_position = True
                position_type = 1
                entry_zscore = z
                df.iloc[i, df.columns.get_loc('exit_reason')] = 'ENTRY_LONG_BTC'
            
            # Z < -2 → Ratio en-dessous de sa moyenne → trend BAISSE → SHORT BTC/LONG ETH
            elif z < -z_entry:
                df.iloc[i, df.columns.get_loc('signal')] = -1
                in_position = True
                position_type = -1
                entry_zscore = z
                df.iloc[i, df.columns.get_loc('exit_reason')] = 'ENTRY_SHORT_BTC'
        
        else:
            # SORTIE TREND FOLLOWING
            crossed_exit = False
            crossed_stop = False
            
            if position_type == 1:  # LONG BTC / SHORT ETH (on parie sur hausse du ratio)
                # Exit : Z redescend vers 0 (cross de +z_exit à < +z_exit)
                if prev_zscore >= z_exit and z < z_exit:
                    crossed_exit = True
                    df.iloc[i, df.columns.get_loc('exit_reason')] = 'EXIT_TREND_WEAKENED'
                
                # Stop-loss : Z devient négatif (inversion complète)
                if z < -z_exit:
                    crossed_exit = True
                    df.iloc[i, df.columns.get_loc('exit_reason')] = 'EXIT_TREND_REVERSED'
                
                # Stop-loss extrême : Z continue de monter trop (adverse pour short)
                # En fait pour LONG BTC, si Z monte encore, c'est bon pour nous
                # Le vrai SL c'est si Z descend trop
                if z < -z_stop:
                    crossed_stop = True
                    df.iloc[i, df.columns.get_loc('exit_reason')] = 'STOP_LOSS'
            
            elif position_type == -1:  # SHORT BTC / LONG ETH (on parie sur baisse du ratio)
                # Exit : Z remonte vers 0 (cross de -z_exit à > -z_exit)
                if prev_zscore <= -z_exit and z > -z_exit:
                    crossed_exit = True
                    df.iloc[i, df.columns.get_loc('exit_reason')] = 'EXIT_TREND_WEAKENED'
                
                # Stop-loss : Z devient positif (inversion complète)
                if z > z_exit:
                    crossed_exit = True
                    df.iloc[i, df.columns.get_loc('exit_reason')] = 'EXIT_TREND_REVERSED'
                
                # Stop-loss extrême
                if z > z_stop:
                    crossed_stop = True
                    df.iloc[i, df.columns.get_loc('exit_reason')] = 'STOP_LOSS'
            
            if crossed_exit or crossed_stop:
                df.iloc[i, df.columns.get_loc('signal')] = 0
                in_position = False
        
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
        
        if signal != 0 and current_trade is None:
            current_trade = {
                'entry_date': row.name,
                'entry_idx': i,
                'type': signal,
                'entry_ratio': row['ratio'],
                'entry_zscore': row['zscore'],
                'btc_price': row['btc_close'],
                'eth_price': row['eth_close']
            }
        
        elif signal == 0 and current_trade is not None:
            exit_ratio = row['ratio']
            exit_zscore = row['zscore']
            
            ratio_change = (exit_ratio - current_trade['entry_ratio']) / current_trade['entry_ratio']
            
            if current_trade['type'] == 1:
                raw_pnl = ratio_change * capital
            else:
                raw_pnl = -ratio_change * capital
            
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
    
    winners = len(trades_df[trades_df['pnl_eur'] > 0])
    win_rate = winners / len(trades_df) * 100
    
    pnl_total = trades_df['pnl_eur'].sum()
    pnl_pct = pnl_total / config['capital'] * 100
    
    if len(trades_df) > 1:
        returns = trades_df['pnl_eur'] / config['capital']
        sharpe = returns.mean() / returns.std() * np.sqrt(252 * 24 / trades_df['duration_hours'].mean()) if trades_df['duration_hours'].mean() > 0 else 0
    else:
        sharpe = 0
    
    max_drawdown = df['drawdown_curve'].max()
    avg_duration = trades_df['duration_hours'].mean()
    
    gross_profit = trades_df[trades_df['pnl_eur'] > 0]['pnl_eur'].sum()
    gross_loss = abs(trades_df[trades_df['pnl_eur'] <= 0]['pnl_eur'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
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
    
    # Critères de succès pour trend-following
    wr_target = 60  # Trend following a typiquement WR plus bas que mean-reversion
    pf_target = 1.2  # Mais PnL plus élevé
    
    wr_pass = metrics['win_rate'] >= wr_target
    pf_pass = metrics['profit_factor'] > pf_target
    overall_pass = wr_pass and pf_pass
    
    status = "✅ PASS" if overall_pass else "❌ FAIL"
    
    # Pré-calcul des textes conditionnels pour éviter les problèmes de f-string
    viable_text = "est viable" if overall_pass else "n'est pas viable"
    wr_emoji = "(objectif ≥60% atteint ✅)" if wr_pass else "(objectif ≥60% non atteint ❌)"
    pf_emoji = "(objectif >1.2 atteint ✅)" if pf_pass else "(objectif >1.2 non atteint ❌)"
    sharpe_emoji = "✅" if metrics['sharpe_ratio'] > 1 else "❌"
    dd_emoji = "✅" if metrics['max_drawdown'] < 20 else "❌"
    wr_pass_emoji = "✅" if wr_pass else "❌"
    pf_pass_emoji = "✅" if pf_pass else "❌"
    dd_pass_emoji = "✅" if metrics['max_drawdown'] < 20 else "❌"
    sharpe_pass_emoji = "✅" if metrics['sharpe_ratio'] > 1 else "❌"
    trend_perf = "Trend following capture mieux les mouvements directionnels que mean-reversion" if metrics['pnl_total_eur'] > -521.52 else "Performance similaire à mean-reversion"
    trend_comp = "performe mieux" if metrics['pnl_total_eur'] > -521.52 else "performe moins bien"
    ratio_fav = "(favorable)" if len(trades) > 0 and pd.DataFrame(trades)[pd.DataFrame(trades)['pnl_eur'] > 0]['pnl_eur'].mean() > abs(pd.DataFrame(trades)[pd.DataFrame(trades)['pnl_eur'] <= 0]['pnl_eur'].mean()) else "(défavorable)"
    rec_text = "✅ POURSUIVRE — Tester en production avec position sizing réduit" if overall_pass else "❌ AJUSTER — Modifier paramètres ou abandonner"
    
    report = f"""# Backtest #4 : Pairs Trading Trend-Following BTC-ETH v1

## 📋 Synthèse Exécutive

**Statut : {status} — Stratégie trend-following du ratio**

| Métrique | Résultat | Objectif | Écart |
|---|---|---|---|
| **Win Rate** | {metrics['win_rate']:.1f}% | ≥{wr_target}% | {metrics['win_rate'] - wr_target:+.1f} pts {wr_pass_emoji} |
| **PnL Total** | {metrics['pnl_total_eur']:+.2f}€ ({metrics['pnl_total_pct']:+.2f}%) | - | - |
| **PnL/jour** | {metrics['pnl_total_eur']/duration_days:+.2f}€/jour | - | - |
| **Sharpe Ratio** | {metrics['sharpe_ratio']:.2f} | >1 | {sharpe_emoji} |
| **Max Drawdown** | -{metrics['max_drawdown']:.2f}% | <20% | {dd_pass_emoji} |
| **Profit Factor** | {metrics['profit_factor']:.2f} | >{pf_target} | {pf_pass_emoji} |

---

## 📊 Données du Backtest

### Période
- **Start** : {start_date}
- **End** : {end_date}
- **Durée** : {duration_days} jours

### Données
- **Timeframe** : {config['timeframe']}
- **Source** : Binance (CCXT)
- **N bougies** : {len(df)}
- **Corrélation BTC-ETH** : {metrics['correlation']:.3f}

### Paramètres (Trend-Following v1)
| Paramètre | Valeur |
|---|---|
| MA | {config['ma_period']} périodes |
| Entry | Z-score > +{config['z_entry']} ou < -{config['z_entry']} |
| Exit | Z-score < +{config['z_exit']} (longs) ou > -{config['z_exit']} (shorts) |
| Stop-loss | Z-score > ±{config['z_stop']} (adverse move) |
| Fees | {config['fee']*100}% |
| Slippage | {config['slippage']*100}% |
| Capital | {config['capital']} € |
| Levier | {config['leverage']}x |

---

## 🔍 Analyse Détaillée

### 1. Concept Trend-Following

Contrairement à la mean-reversion (Backtest #1), cette stratégie **suit le trend** du ratio BTC/ETH :

- **Z > +2** → Ratio monte fort → **LONG BTC + SHORT ETH** (on suit la hausse)
- **Z < -2** → Ratio descend fort → **SHORT BTC + LONG ETH** (on suit la baisse)
- **Sortie** : Quand le trend faiblit (Z retour vers 0)

### 2. Distribution des Trades

"""
    
    if len(trades) > 0:
        trades_df = pd.DataFrame(trades)
        winners = len(trades_df[trades_df['pnl_eur'] > 0])
        losers = len(trades_df[trades_df['pnl_eur'] <= 0])
        avg_win = trades_df[trades_df['pnl_eur'] > 0]['pnl_eur'].mean() if winners > 0 else 0
        avg_loss = abs(trades_df[trades_df['pnl_eur'] <= 0]['pnl_eur'].mean()) if losers > 0 else 0
        
        report += f"""```
Trades winners : {winners}/{len(trades)} ({metrics['win_rate']:.1f}%)
Trades losers  : {losers}/{len(trades)} ({100-metrics['win_rate']:.1f}%)

Gains moyens   : +{avg_win:.2f}€
Pertes moyennes: -{avg_loss:.2f}€
Ratio G/P      : {avg_win/avg_loss:.2f} {ratio_fav}
```
"""
    
    report += f"""
### 3. Comparaison avec Mean-Reversion (Backtest #1)

| Métrique | Mean-Rev v1 | Trend-Follow v1 | Delta |
|---|---|---|---|
| Win Rate | 45.5% | {metrics['win_rate']:.1f}% | {metrics['win_rate'] - 45.5:+.1f} pts |
| PnL Total | -521.52€ | {metrics['pnl_total_eur']:+.2f}€ | {metrics['pnl_total_eur'] + 521.52:+.2f}€ |
| Profit Factor | 0.35 | {metrics['profit_factor']:.2f} | {metrics['profit_factor'] - 0.35:+.2f} |
| Max DD | -5.90% | -{metrics['max_drawdown']:.2f}% | {-(metrics['max_drawdown'] - 5.90):+.2f} pts |

---

## 💡 Observations

### Points forts
- {wr_emoji} Win Rate ≥ 60%
- {pf_emoji} Profit Factor > 1.2
- {dd_emoji} Drawdown maîtrisé (<20%)
- {sharpe_emoji} Sharpe > 1

### Points faibles
- {trend_perf}

### Pistes d'amélioration
- Ajuster Z-entry (±2.5 pour moins de signaux mais meilleure qualité)
- Ajouter filtre de momentum (RSI, ADX)
- Tester trailing stop au lieu de fixed exit
- Explorer timeframe 1D pour réduire le noise

---

## 📈 Détail des Trades

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
---

## ✅ Conclusion

### Verdict : **{status}**

La stratégie de Pairs Trading BTC-ETH par **trend-following** du ratio {viable_text} dans sa forme actuelle.

### Résultats clés :
- **WR** : {metrics['win_rate']:.1f}% {wr_emoji}
- **Profit Factor** : {metrics['profit_factor']:.2f} {pf_emoji}
- **PnL** : {metrics['pnl_total_eur']:+.2f}€ sur {duration_days} jours ({metrics['pnl_total_eur']/duration_days:+.2f}€/jour)
- **Risque** : Max DD -{metrics['max_drawdown']:.2f}%

### Comparaison Mean-Rev vs Trend-Follow :
Le trend-following {trend_comp} que la mean-reversion sur cette période, ce qui confirme que le ratio BTC/ETH est plus **trending** que **mean-reverting**.

### Recommandation :
{rec_text}

---

## 📁 Fichiers Produits

| Fichier | Description |
|---|---|
| `src/pairs_trading_trend_v1.py` | Moteur de backtest trend-following |
| `backtests/pairs-trading-trend-v1.md` | Rapport détaillé |
| `backtests/pairs-trading-trend-v1_data.csv` | Données brutes (OHLCV + signaux + PnL) |

---

*Généré le {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*
*Backtest engine v1.0 — Python 3.12.3*
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
    print("🔬 BACKTEST #4 : PAIRS TRADING TREND-FOLLOWING BTC-ETH")
    print("=" * 60)
    print()
    
    print("📡 Étape 1/5 : Récupération des données...")
    df = fetch_btc_eth_data(CONFIG['timeframe'], CONFIG['days'])
    print()
    
    print("📐 Étape 2/5 : Calcul du ratio et Z-score...")
    df = calculate_ratio_and_zscore(df, CONFIG['ma_period'])
    print(f"   → Ratio moyen : {df['ratio'].mean():.4f}")
    print(f"   → Z-score range : [{df['zscore'].min():.2f}, {df['zscore'].max():.2f}]")
    print()
    
    print("🚦 Étape 3/5 : Génération des signaux (trend-following)...")
    df = generate_signals_trend(df, CONFIG['z_entry'], CONFIG['z_exit'], CONFIG['z_stop'])
    n_entries = (df['exit_reason'].str.contains('ENTRY', na=False)).sum()
    print(f"   → {n_entries} entrées")
    print()
    
    print("💰 Étape 4/5 : Exécution du backtest...")
    trades, df = run_backtest(df, CONFIG)
    print(f"   → {len(trades)} trades exécutés")
    print()
    
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
    
    output_path = '/root/.openclaw/workspace/backtests/pairs-trading-trend-v1.md'
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
