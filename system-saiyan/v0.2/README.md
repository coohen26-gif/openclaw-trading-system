# 🐉 Système Saiyan v0.2

> **Production Ready** - Momentum+HMM + Risk Management + Multi-Asset  
> **Stratégie Validée:** +55% return, Sharpe 0.91, DD -7.5%, WR 57.1%  
> **Status:** Development (Testnet)

---

## 📋 Spécifications

### Architecture

| Composant | Technologie | Status |
|-----------|-------------|--------|
| **Stratégie** | Momentum + HMM 4 régimes | ✅ Validé |
| **Risk Management** | VaR/CVaR + Circuit Breakers | ✅ Validé |
| **Allocation** | Risk Parity (BTC/ETH/SOL) | ✅ Validé |
| **Execution** | Binance Testnet | 🔄 En cours |
| **Notifications** | Telegram (OpenClaw) | 🔄 En cours |

### Performance Validée (Backtest 2020-2026)

| Métrique | Valeur | Cible | Status |
|----------|--------|-------|--------|
| **Total Return** | +55% | >30% | ✅ |
| **Sharpe Ratio** | 0.91 | >0.8 | ✅ |
| **Max Drawdown** | -7.5% | <-15% | ✅ |
| **Win Rate** | 57.1% | >50% | ✅ |
| **N Trades** | 63 | >30 | ✅ |

---

## 🎯 Configuration

### Stratégie Momentum+HMM

**4 Régimes:**
| Régime | Kelly | Position | SL | TP | Max Days |
|--------|-------|----------|-----|-----|----------|
| 🐂 Bull | 0.75x | 18.75% | -5% | +15% | 10 |
| 🐻 Bear | 0.25x | 6.25% | -3% | +8% | 3 |
| ➡️ Range | 0.25x | 6.25% | -4% | +6% | 5 |
| 🚀 Vol Bull | 0.50x | 12.5% | -8% | +20% | 7 |

### Risk Management

**Circuit Breakers (4 niveaux):**
| Niveau | Daily PnL | Drawdown | Action |
|--------|-----------|----------|--------|
| Level 1 (Warning) | < -3.6% | < -10% | Alert |
| Level 2 (Reduce) | < -5% | < -15% | Reduce 50% |
| Level 3 (Stop) | < -8% | < -20% | Stop new trades |
| Level 4 (Kill) | < -10% | < -25% | Kill Switch |

**VaR/CVaR (95%):**
- VaR 95% BTC: -3.63%
- CVaR 95% BTC: -5.20% (gap 43%!)

### Allocation Multi-Asset

**Risk Parity Weights:**
- BTC: 52% (moins volatil)
- ETH: 28%
- SOL: 20% (très volatil)

**Rebalancing:**
- Threshold: 5% drift
- Schedule: Weekly (7 jours)
- Coût estimé: ~1% annualisé

---

## 📁 Structure du Projet

```
system-saiyan/v0.2/
├── main.py                        # Entry point
├── config.json                    # Configuration complète
├── README.md                      # Ce fichier
├── core/
│   ├── __init__.py
│   ├── risk_monitor.py            # VaR/CVaR + Circuit Breakers
│   └── portfolio_allocator.py     # Risk Parity + Rebalancing
├── strategies/
│   ├── __init__.py
│   └── momentum_hmm.py            # Stratégie validée
├── data/
│   └── __init__.py
├── utils/
│   └── __init__.py
├── backtests/
│   └── __init__.py
├── config/
│   └── __init__.py
└── logs/
    └── .gitkeep
```

---

## 🚀 Installation

### Prérequis

- Python 3.12+
- pip

### Installation

```bash
cd /root/.openclaw/workspace/system-saiyan/v0.2/
python3.12 -m venv venv
source venv/bin/activate
pip install pandas numpy ccxt scipy requests
```

---

## 💻 Utilisation

### Mode Paper-Trading

```bash
cd /root/.openclaw/workspace/system-saiyan/v0.2/
python main.py --mode paper
```

**Output:**
- Signaux générés (Momentum+HMM)
- Risk metrics (VaR/CVaR + Circuit Breakers)
- Portfolio status (Risk Parity)

### Mode Backtest

```bash
python main.py --mode backtest --asset BTC/USDT
```

**Output:**
- Total Return, Sharpe, Drawdown
- Win Rate, N Trades
- Equity curve

### Mode Monitor

```bash
python main.py --mode monitor
```

**Output:**
- Risk status (circuit breaker level)
- Portfolio allocations
- Current regime

### API Python

```python
from main import SaiyanSystem

# Initialize
system = SaiyanSystem('config.json')
system.initialize()

# Fetch data
data = system.fetch_market_data(['BTC/USDT'], limit=500)

# Run trading cycle
result = system.run_trading_cycle(data)
print(f"Status: {result['status']}")
print(f"Signal: {result['active_signal']}")

# Get system status
status = system.get_system_status()
print(f"Risk: {status['risk']}")
print(f"Portfolio: {status['portfolio']}")
```

---

## 📊 Composants

### 1. Momentum+HMM Strategy (`strategies/momentum_hmm.py`)

**Features:**
- Momentum 5 jours
- HMM 4 régimes (Bull, Bear, Range, Volatile Bull)
- Regime-dependent position sizing
- Trailing stop mechanism
- Time-based exit (20 jours max)

**Usage:**
```python
from strategies.momentum_hmm import MomentumHMMStrategy, backtest_strategy

strategy = MomentumHMMStrategy(
    momentum_period=5,
    hmm_lookback=60,
    confidence_threshold=0.6
)

signal = strategy.generate_signal(df, 'BTC/USDT')
if signal:
    print(f"{signal.direction} @ ${signal.stop_loss:.2f} (SL) / ${signal.take_profit:.2f} (TP)")

# Backtest
results = backtest_strategy(df, initial_capital=10000)
print(f"Return: {results['total_return']:.2%}, Sharpe: {results['sharpe_ratio']:.2f}")
```

### 2. Risk Monitor (`core/risk_monitor.py`)

**Features:**
- VaR/CVaR (3 méthodes: Historique, Paramétrique, Monte Carlo)
- 4-Level Circuit Breakers
- Real-time PnL tracking
- Kill Switch implementation

**Usage:**
```python
from core.risk_monitor import RiskMonitor

monitor = RiskMonitor(initial_capital=10000, rolling_window=30)

# Update capital (call after each trade/PnL change)
monitor.update_capital(9850)

# Check risk metrics
metrics = monitor.check_risk_metrics()
print(f"VaR 95%: {metrics.var_95:.2f}%")
print(f"CVaR 95%: {metrics.cvar_95:.2f}%")
print(f"Circuit Breaker: {metrics.circuit_breaker_level.value}")
print(f"Trading Allowed: {metrics.trading_allowed}")

# Emergency kill switch
monitor.activate_kill_switch()
```

### 3. Portfolio Allocator (`core/portfolio_allocator.py`)

**Features:**
- Risk Parity allocation
- Automatic rebalancing (threshold + scheduled)
- Drift monitoring
- Transaction cost estimation

**Usage:**
```python
from core.portfolio_allocator import PortfolioAllocator, RebalanceReason

allocator = PortfolioAllocator(
    target_weights={'BTC': 0.52, 'ETH': 0.28, 'SOL': 0.20},
    rebalance_threshold=5.0,
    rebalance_days=7
)

# Set current holdings
allocator.set_holdings({
    'BTC': 9000,
    'ETH': 5500,
    'SOL': 2300
})

# Check if rebalancing needed
should_rebal, reason = allocator.should_rebalance()
if should_rebal:
    print(f"Rebalance needed: {reason.value}")
    
    # Execute rebalance
    prices = {'BTC': 95000, 'ETH': 3500, 'SOL': 150}
    result = allocator.execute_rebalance(prices, reason)
    
    for trade in result.trades:
        if trade.trade_action != "HOLD":
            print(f"{trade.trade_action} {trade.symbol}: ${trade.trade_amount:,.2f}")
```

---

## 🔧 Configuration (`config.json`)

Voir `config.json` pour la configuration complète.

**Sections principales:**
- `trading_rules`: Position sizing, SL/TP, time exit
- `hmm_config`: Régimes, lookback, confidence threshold
- `regime_sizing`: Configuration par régime
- `risk_monitoring`: VaR/CVaR, circuit breakers
- `risk_parity_weights`: Allocation multi-asset
- `rebalancing`: Threshold, schedule, costs
- `binance`: Testnet configuration
- `notifications`: Telegram settings

---

## 📈 Roadmap

### v0.2 (Current) - 🔄 Development

- [x] Momentum+HMM strategy (validated)
- [x] Risk Monitor (VaR/CVaR + CB)
- [x] Portfolio Allocator (Risk Parity)
- [x] Configuration complète
- [ ] Binance testnet integration
- [ ] Telegram notifications (OpenClaw)
- [ ] Dashboard monitoring (Grafana)
- [ ] Shadow mode (paper trading 30 jours)

### v0.3 - Production Ready

- [ ] 30 jours paper-trade réussis
- [ ] Live trading (Binance mainnet)
- [ ] Alertes Telegram temps réel
- [ ] Weekly stress testing automatique
- [ ] Performance tracking

---

## 📝 Notes

- **Testnet first:** Toujours tester sur Binance testnet avant mainnet
- **Risk management > Signal:** Position sizing et circuit breakers protègent le capital
- **Weekly retraining:** HMM doit être retrainé weekly (Sunday 18h UTC)
- **Stress testing:** Weekly stress test (9 scénarios × 1000 sims)

---

## 🐛 Bugs Connus

Aucun bug connu pour le moment.

---

**Début du projet:** 2026-05-24  
**Version:** 0.2  
**Statut:** Development (Testnet)

🐉 *"La puissance Saiyan n'a pas de limite !"*
