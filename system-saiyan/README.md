# 🐉 Système Saiyan v0.1

> **Prototype Paper-Trade** - Metals (60%) + Crypto (25%)  
> **Stratégies :** Mean Reversion (prioritaire) + Momentum  
> **Timeframes :** 1h, 4h, daily  
> **Signaux → Telegram vers W (exécution manuelle)**

---

## 📋 Spécifications

### Architecture

| Composant | Allocation |
|-----------|------------|
| **Metals** | 60% (Gold, Silver) |
| **Crypto** | 25% (BTC, ETH, SOL) |
| **Reserve** | 15% |

### Stratégies

1. **Mean Reversion** (prioritaire - 75%)
   - RSI oversold/overbought + Bollinger Bands
   - Seuils : RSI <25/>75, BB 2.5σ

2. **Momentum** (à corriger - 25%)
   - Breakout + volume surge
   - Momentum >2% + Volume >1.5x moyenne

### Configuration Trading

| Paramètre | Valeur |
|-----------|--------|
| **Confidence min** | 60/100 |
| **Position sizing** | 2-5% par trade |
| **Stop-loss** | 2-3% |
| **Take-profit** | 0.5-1.5% |
| **Max trades/jour** | 2-5 |
| **Fees** | 0.1% (Binance) |
| **Slippage** | 0.05% |

---

## 📁 Structure du Projet

```
system-saiyan/
└── v0.1/
    ├── main.py                    # Entry point
    ├── config.json                # Configuration
    ├── data/
    │   └── data_pipeline.py       # Binance + yfinance
    ├── core/
    │   ├── feature_engineering.py # RSI, BB, vol, etc.
    │   ├── signal_generator.py    # Confidence score 0-100
    │   └── risk_manager.py        # Position sizing, SL, TP
    ├── backtests/
    │   └── backtester.py          # Backtest + walk-forward
    └── utils/
        └── telegram_notifier.py   # Notifications Telegram
```

---

## 🚀 Installation

### Prérequis

- Python 3.12+
- pip

### Installation

```bash
cd /root/.openclaw/workspace/system-saiyan/v0.1/
python3.12 -m venv venv
source venv/bin/activate
pip install pandas numpy ccxt yfinance scikit-learn requests
```

---

## 💻 Utilisation

### Paper-Trading Cycle

```bash
cd /root/.openclaw/workspace/system-saiyan/v0.1/
python main.py
```

**Output :**
- Signaux générés → Telegram (vers W)
- Backtest avec walk-forward validation
- Metrics : Sharpe, Win Rate, Drawdown

### API Python

```python
from main import SaiyanSystem

# Initialize
system = SaiyanSystem('config.json')

# Paper-trading cycle
signals = system.run_paper_trading_cycle(
    assets=['BTC/USDT', 'ETH/USDT', 'GC=F'],
    timeframe='1h',
    strategy='mean_reversion'
)

# Backtest
metrics = system.run_backtest(
    asset='BTC/USDT',
    timeframe='1h',
    strategy='mean_reversion',
    walk_forward=True
)

print(f"Win Rate: {metrics['avg_win_rate']:.1f}%")
print(f"Sharpe: {metrics['avg_sharpe']:.2f}")
print(f"Max DD: {metrics['avg_max_drawdown']:.1f}%")
```

---

## 📊 Composants

### 1. Data Pipeline (`data/data_pipeline.py`)

**Sources :**
- **Crypto :** Binance API (via ccxt)
- **Metals :** Yahoo Finance (via yfinance)

**Timeframes supportés :** 1h, 4h, 1d

```python
from data.data_pipeline import DataPipeline

pipeline = DataPipeline()

# Crypto
btc_data = pipeline.fetch_crypto_data('BTC/USDT', '1h', 1000)

# Metals (Gold)
gold_data = pipeline.fetch_metals_data('GC=F', '3mo', '1h')
```

### 2. Feature Engineering (`core/feature_engineering.py`)

**Indicateurs calculés :**
- RSI (Relative Strength Index)
- Bollinger Bands (2.5σ)
- Volatilité (annualisée)
- Momentum (Rate of Change)
- Volume Surge
- ATR (Average True Range)

```python
from core.feature_engineering import FeatureEngineer

fe = FeatureEngineer()
df = fe.calculate_all_features(ohlcv_df)
```

### 3. Signal Generator (`core/signal_generator.py`)

**Confidence Score (0-100) :**
- Technical (RSI, BB) : 40%
- Momentum : 25%
- Volume : 20%
- Volatility : 15%

**Seuil minimum :** 60/100 pour exécution

```python
from core.signal_generator import SignalGenerator

sg = SignalGenerator()
signals = sg.generate_signals(df, strategy='mean_reversion')

for signal in signals:
    print(f"{signal['direction']} @ {signal['entry_price']} (conf: {signal['confidence']})")
```

### 4. Risk Manager (`core/risk_manager.py`)

**Position Sizing (confidence-based) :**

| Confidence | Position |
|------------|----------|
| 60-70 | 2% |
| 70-80 | 3% |
| 80-90 | 4% |
| 90+ | 5% |

**Risk Management :**
- Stop-loss : 2.5%
- Take-profit : 1.0%
- Max daily loss : 5%

```python
from core.risk_manager import RiskManager

rm = RiskManager(total_capital=10000)
params = rm.calculate_position_size(signal)
summary = rm.get_trade_summary(params)
```

### 5. Backtester (`backtests/backtester.py`)

**Features :**
- Transaction costs (fees 0.1% + slippage 0.05%)
- Walk-forward validation (3 splits)
- Metrics complets

**Metrics calculés :**
- Win Rate (%)
- Total PnL (USDT)
- Sharpe Ratio
- Max Drawdown (%)
- Profit Factor
- Avg Trade Duration

```python
from backtests.backtester import Backtester, BacktestConfig

config = BacktestConfig(
    initial_capital=10000,
    trading_fee_pct=0.1,
    slippage_pct=0.05
)

backtester = Backtester(config)
metrics = backtester.run_backtest(df, signals)
```

### 6. Telegram Notifier (`utils/telegram_notifier.py`)

**Envoi vers W pour exécution manuelle**

```python
from utils.telegram_notifier import TelegramNotifier

notifier = TelegramNotifier(use_openclaw=True)
notifier.send_signal(signal, trade_params)
```

**Message format :**
```
🐉 SYSTÈME SAIYAN v0.1 - SIGNAL 🟢

Symbol: BTC/USDT
Direction: LONG
Strategy: Mean Reversion

Entry Price: $95,000.00
Confidence: 78.5/100

💰 Risk Management:
• Position: 3.0% ($300.00)
• Stop Loss: $92,625.00 (-2.5%)
• Take Profit: $95,950.00 (+1.0%)

Expected PnL: +$3.00 / -$7.50
Risk/Reward: 0.40

📊 Indicators:
• RSI: 22.3
• BB Position: 0.15
• Volume Surge: 1.8x
• Momentum: 2.5%

⚠️ Exécution Manuelle - Vérifier avant d'entrer
```

---

## 📈 Backtest Report

Le rapport de backtest est généré dans :
`learning/backtests/saiyan-v0.1-report.md`

**Objectifs :**
- Win Rate ≥70%
- Sharpe Ratio >1
- Max Drawdown <15%
- Profit Factor >1.5

---

## 🔧 Configuration (`config.json`)

```json
{
  "capital": 10000,
  "trading_rules": {
    "min_confidence": 60,
    "max_trades_per_day": 5,
    "position_size_min": 2.0,
    "position_size_max": 5.0,
    "stop_loss_pct": 2.5,
    "take_profit_pct": 1.0
  },
  "strategies": {
    "primary": "mean_reversion",
    "secondary": "momentum"
  }
}
```

---

## 🎯 KPIs Cibles

| Métrique | Cible | Statut |
|----------|-------|--------|
| Win Rate | ≥70% | ⏳ À valider |
| Sharpe Ratio | >1 | ⏳ À valider |
| Max Drawdown | <15% | ⏳ À valider |
| Profit Factor | >1.5 | ⏳ À valider |
| n_signaux/jour | 2-5 | ✅ Configuré |
| Confidence min | 60/100 | ✅ Configuré |

---

## 📝 Notes

- **Exécution manuelle** : Les signaux sont envoyés vers W sur Telegram
- **Paper-trade first** : 30 jours minimum avant go-live
- **Mean Reversion prioritaire** : 75% des signaux
- **Momentum à corriger** : Bug connu sur les faux breakouts

---

## 🐛 Bugs Connus

### Momentum Strategy

**Problème :** Trop de faux signaux sur breakouts sans volume

**Solution prévue :**
- Augmenter volume surge threshold (1.5 → 2.0)
- Ajouter filtre de tendance (MA 50/200)
- Réduire poids momentum (25% → 15%)

---

## 📅 Roadmap

### v0.1 (Current) - ✅ Prototype Paper-Trade
- [x] Data pipeline (Binance + yfinance)
- [x] Feature engineering
- [x] Signal generation (confidence 0-100)
- [x] Risk management
- [x] Telegram notifications
- [x] Backtest avec transaction costs
- [ ] Backtest report >70% WR

### v0.2 - Amélivements
- [ ] Corriger bug momentum
- [ ] Ajouter filtre de régime (HMM)
- [ ] Optimiser paramètres mean reversion
- [ ] Tests sur données out-of-sample

### v0.3 - Production Ready
- [ ] 30 jours paper-trade réussis
- [ ] Monitoring dashboard
- [ ] Alertes performance
- [ ] Go-live signal-only

---

## 📄 License

Projet personnel - Système Saiyan

---

**Début du projet :** 2026-05-24  
**Version :** 0.1  
**Statut :** Prototype Paper-Trade

🐉 *"La puissance Saiyan n'a pas de limite !"*
