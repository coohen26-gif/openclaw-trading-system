# Semaine 25 - Production Systems & Infrastructure

**Date:** 24 Mai 2026  
**Niveau:** Master 5 - Advanced Topics  
**Temps estimé:** 4-5h

---

## 🎯 Objectifs du Module

1. Comprendre l'architecture d'un système de trading production
2. Maîtriser les composants: Data Pipeline, Signal Engine, Execution, Risk
3. Implémenter monitoring, alerting, logging
4. Concevoir des circuit breakers et kill switches
5. Comprendre CI/CD, testing, deployment pour trading systems

---

## 📚 Architecture d'un Système de Trading

### 1. Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRADING SYSTEM ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │   DATA   │───▶│  SIGNAL  │───▶│  RISK    │───▶│ EXECUTION│  │
│  │ PIPELINE │    │  ENGINE  │    │ MANAGER  │    │  ENGINE  │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       │               │               │               │         │
│       ▼               ▼               ▼               ▼         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ Database │    │ Backtest │    │ Circuit  │    │ Exchange │  │
│  │ (Timescale│    │ Engine   │    │ Breakers │    │   API    │  │
│  │  Postgres)│    │          │    │          │    │          │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              MONITORING & ALERTING                       │   │
│  │  (Prometheus, Grafana, PagerDuty, Slack, Telegram)       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Composants Principaux

#### a) Data Pipeline

**Responsabilités:**
- Collecter données (prix, volumes, order book, on-chain, etc.)
- Nettoyer et valider (outliers, gaps, duplicates)
- Stocker (time-series database)
- Servir aux autres composants (low latency)

**Technologies:**
- **Collect:** Python (CCXT, websockets), Kafka, RabbitMQ
- **Store:** TimescaleDB, InfluxDB, ClickHouse, Redis (cache)
- **Process:** Pandas, Polars, NumPy
- **Stream:** Kafka, Redis Streams

**Exemple Architecture:**
```python
# Data collection pipeline
class DataPipeline:
    def __init__(self):
        self.exchanges = ['binance', 'bybit', 'coinbase']
        self.symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
        self.db = TimescaleDBConnection()
        self.cache = RedisConnection()
    
    async def collect_ohlcv(self):
        """Collect OHLCV data from exchanges."""
        for exchange in self.exchanges:
            for symbol in self.symbols:
                ohlcv = await exchange.fetch_ohlcv(symbol, timeframe='1m')
                await self.store_ohlcv(exchange, symbol, ohlcv)
    
    async def collect_orderbook(self):
        """Collect order book snapshots."""
        for exchange in self.exchanges:
            for symbol in self.symbols:
                ob = await exchange.fetch_order_book(symbol, limit=20)
                await self.store_orderbook(exchange, symbol, ob)
    
    async def store_ohlcv(self, exchange, symbol, data):
        """Store OHLCV in timeseries database."""
        # Insert into TimescaleDB
        pass
    
    async def store_orderbook(self, exchange, symbol, data):
        """Store order book snapshot."""
        # Insert into TimescaleDB
        pass
```

#### b) Signal Engine

**Responsabilités:**
- Calculer indicateurs techniques
- Exécuter modèles ML
- Générer signaux de trading
- Score de confiance

**Technologies:**
- **Indicators:** TA-Lib, pandas-ta
- **ML:** scikit-learn, XGBoost, PyTorch
- **Orchestration:** Airflow, Prefect

**Exemple:**
```python
class SignalEngine:
    def __init__(self):
        self.models = {
            'mean_reversion': MeanReversionModel(),
            'momentum': MomentumModel(),
            'ml_classifier': XGBoostClassifier(),
            'hmm_regime': HMMRegimeDetector()
        }
        self.indicators = TechnicalIndicators()
    
    def generate_signals(self, market_data):
        """Generate trading signals from market data."""
        signals = {}
        
        # Technical indicators
        rsi = self.indicators.rsi(market_data['close'])
        macd = self.indicators.macd(market_data['close'])
        bb = self.indicators.bollinger_bands(market_data['close'])
        
        # Mean reversion signal
        mr_signal = self.models['mean_reversion'].signal(rsi, bb)
        
        # Momentum signal
        mom_signal = self.models['momentum'].signal(macd, market_data['volume'])
        
        # ML signal
        features = self.extract_features(market_data)
        ml_signal = self.models['ml_classifier'].predict(features)
        
        # Regime detection
        regime = self.models['hmm_regime'].detect(market_data['returns'])
        
        # Combine signals
        signals = self.combine_signals(
            mr_signal, mom_signal, ml_signal, regime
        )
        
        return signals
    
    def combine_signals(self, *signals, regime):
        """Combine multiple signals with regime-dependent weights."""
        # Regime-dependent weighting
        if regime == 'bull':
            weights = {'momentum': 0.5, 'ml': 0.3, 'mean_rev': 0.2}
        elif regime == 'bear':
            weights = {'momentum': 0.2, 'ml': 0.3, 'mean_rev': 0.5}
        else:  # range
            weights = {'momentum': 0.3, 'ml': 0.4, 'mean_rev': 0.3}
        
        # Weighted combination
        combined_score = (
            signals[0].score * weights['mean_rev'] +
            signals[1].score * weights['momentum'] +
            signals[2].score * weights['ml']
        )
        
        return TradingSignal(
            direction='long' if combined_score > 0.2 else 'short' if combined_score < -0.2 else 'neutral',
            confidence=abs(combined_score),
            regime=regime
        )
```

#### c) Risk Manager

**Responsabilités:**
- Vérifier limits (position, VaR, drawdown)
- Circuit breakers
- Kill switch
- Compliance checks

**Exemple:**
```python
class RiskManager:
    def __init__(self, config):
        self.config = config
        self.positions = {}
        self.daily_pnl = 0.0
        self.peak_equity = config['initial_equity']
        self.current_equity = config['initial_equity']
    
    def check_pre_trade(self, signal, current_price):
        """Pre-trade risk checks."""
        checks = []
        
        # 1. Position limit check
        position_check = self.check_position_limit(signal.symbol)
        checks.append(position_check)
        
        # 2. VaR check
        var_check = self.check_var(signal, current_price)
        checks.append(var_check)
        
        # 3. Daily loss limit
        loss_check = self.check_daily_loss_limit()
        checks.append(loss_check)
        
        # 4. Drawdown check
        dd_check = self.check_drawdown_limit()
        checks.append(dd_check)
        
        # 5. Circuit breaker check
        cb_check = self.check_circuit_breakers()
        checks.append(cb_check)
        
        # All checks must pass
        all_passed = all(check.passed for check in checks)
        
        return RiskApproval(
            approved=all_passed,
            checks=checks,
            max_size=self.calculate_max_size(signal, current_price)
        )
    
    def check_position_limit(self, symbol):
        """Check if new position exceeds limit."""
        current_position = self.positions.get(symbol, 0)
        max_position = self.config['max_position_per_symbol']
        
        if abs(current_position) >= max_position:
            return Check('position_limit', passed=False, reason='Max position reached')
        return Check('position_limit', passed=True)
    
    def check_var(self, signal, price):
        """Check VaR limit."""
        # Calculate incremental VaR
        current_var = self.calculate_portfolio_var()
        incremental_var = self.calculate_incremental_var(signal, price)
        
        max_var = self.config['max_daily_var']
        
        if current_var + incremental_var > max_var:
            return Check('var_limit', passed=False, 
                        reason=f'VaR {current_var + incremental_var:.0f} > max {max_var:.0f}')
        return Check('var_limit', passed=True)
    
    def check_daily_loss_limit(self):
        """Check daily loss limit."""
        daily_loss_limit = self.config['max_daily_loss']  # e.g., -5%
        
        if self.daily_pnl < daily_loss_limit:
            return Check('daily_loss', passed=False, 
                        reason=f'Daily PnL {self.daily_pnl:.2f} < limit {daily_loss_limit:.2f}')
        return Check('daily_loss', passed=True)
    
    def check_drawdown_limit(self):
        """Check maximum drawdown limit."""
        max_drawdown = self.config['max_drawdown']  # e.g., -20%
        current_drawdown = (self.current_equity - self.peak_equity) / self.peak_equity
        
        if current_drawdown < max_drawdown:
            return Check('drawdown', passed=False,
                        reason=f'Drawdown {current_drawdown:.2f} < limit {max_drawdown:.2f}')
        return Check('drawdown', passed=True)
    
    def check_circuit_breakers(self):
        """Check circuit breaker status."""
        # Check if any circuit breaker is triggered
        for cb in self.config['circuit_breakers']:
            if cb.is_triggered():
                return Check('circuit_breaker', passed=False,
                           reason=f'{cb.name} triggered')
        return Check('circuit_breaker', passed=True)
    
    def calculate_max_size(self, signal, price):
        """Calculate maximum allowed position size."""
        # Based on VaR, position limits, etc.
        max_by_var = self.config['max_daily_var'] / self.calculate_signal_var(signal, price)
        max_by_position = self.config['max_position_per_symbol']
        
        return min(max_by_var, max_by_position)
```

#### d) Execution Engine

**Responsabilités:**
- Recevoir signaux approuvés
- Router vers exchanges
- Gérer order lifecycle (new, partial, filled, cancelled)
- Smart order routing (multi-exchange)
- TWAP/VWAP execution

**Exemple:**
```python
class ExecutionEngine:
    def __init__(self, exchanges):
        self.exchanges = exchanges  # Dict of exchange connections
        self.order_book = {}  # Track all orders
        self.fills = []
    
    async def execute_signal(self, signal, risk_approval):
        """Execute approved trading signal."""
        if not risk_approval.approved:
            return ExecutionResult(success=False, reason='Risk approval failed')
        
        # Determine execution strategy
        if signal.size > self.config['large_order_threshold']:
            # Use TWAP/VWAP for large orders
            return await self.execute_twap(signal, risk_approval.max_size)
        else:
            # Direct execution
            return await self.execute_market_order(signal, risk_approval.max_size)
    
    async def execute_market_order(self, signal, max_size):
        """Execute market order."""
        exchange = self.select_exchange(signal.symbol)
        
        try:
            order = await exchange.create_market_order(
                symbol=signal.symbol,
                side=signal.direction,
                amount=min(signal.size, max_size)
            )
            
            self.order_book[order.id] = order
            
            return ExecutionResult(
                success=True,
                order_id=order.id,
                filled=order.filled,
                avg_price=order.average
            )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))
    
    async def execute_twap(self, signal, total_size, duration_minutes=15):
        """Execute TWAP order."""
        twap = TWAPExecutor(total_size, duration_minutes, self)
        return await twap.execute()
    
    def select_exchange(self, symbol):
        """Select best exchange for execution."""
        # Based on: fees, liquidity, latency
        best_exchange = min(
            self.exchanges.values(),
            key=lambda ex: ex.fees['taker'] * ex.get_liquidity(symbol)
        )
        return best_exchange
    
    async def on_order_update(self, order_id, update):
        """Handle order status updates."""
        order = self.order_book.get(order_id)
        if order:
            order.update(update)
            
            if order.status == 'filled':
                self.fills.append(order)
                await self.on_fill(order)
    
    async def on_fill(self, order):
        """Handle order fill."""
        # Update positions
        # Update PnL
        # Send notification
        pass
```

### 3. Monitoring & Alerting

#### a) Metrics à Tracker

**System Health:**
```
- API latency (p50, p95, p99)
- Order submission latency
- Fill rate
- Error rate
- Uptime
- Memory usage
- CPU usage
- Database connections
- Queue depths
```

**Trading Metrics:**
```
- PnL (realized, unrealized)
- Positions (by symbol, by strategy)
- Exposure (gross, net)
- VaR
- Drawdown
- Win rate
- Sharpe ratio (rolling)
- Slippage
- Transaction costs
```

**Risk Metrics:**
```
- Position sizes vs limits
- Daily PnL vs limits
- Drawdown vs limits
- Circuit breaker status
- VaR vs limits
- Concentration risk
```

#### b) Alerting Rules

```python
ALERT_RULES = {
    # Critical alerts (page immediately)
    'critical_drawdown': {
        'condition': 'drawdown < -0.15',
        'severity': 'critical',
        'channels': ['pagerduty', 'slack', 'telegram'],
        'message': '🚨 CRITICAL: Drawdown exceeded 15% - Kill switch may trigger'
    },
    'exchange_down': {
        'condition': 'exchange_status == "down"',
        'severity': 'critical',
        'channels': ['pagerduty', 'slack'],
        'message': '🚨 CRITICAL: Exchange {exchange} is down'
    },
    'order_rejection_rate': {
        'condition': 'order_rejection_rate > 0.10',  # >10%
        'severity': 'critical',
        'channels': ['pagerduty', 'slack'],
        'message': '🚨 CRITICAL: Order rejection rate {rate:.1f}% - Check API keys/balances'
    },
    
    # Warning alerts (notify, no page)
    'high_daily_loss': {
        'condition': 'daily_pnl < -0.03',  # -3%
        'severity': 'warning',
        'channels': ['slack'],
        'message': '⚠️ WARNING: Daily PnL at {pnl:.2f}% - Approaching limit'
    },
    'position_concentration': {
        'condition': 'max_position_weight > 0.40',
        'severity': 'warning',
        'channels': ['slack'],
        'message': '⚠️ WARNING: Position concentration {weight:.1f}% in {symbol}'
    },
    'latency_spike': {
        'condition': 'p99_latency > 5000',  # >5 seconds
        'severity': 'warning',
        'channels': ['slack'],
        'message': '⚠️ WARNING: High latency p99={latency:.0f}ms'
    },
    
    # Info alerts (log only)
    'daily_summary': {
        'condition': 'time == "18:00 UTC"',
        'severity': 'info',
        'channels': ['telegram'],
        'message': '📊 Daily Summary: PnL {pnl:.2f}%, Trades {trades}, Win Rate {win_rate:.1f}%'
    }
}
```

#### c) Dashboard (Grafana)

**Key Panels:**

1. **PnL Overview:**
   - Real-time PnL chart
   - Daily PnL bar chart
   - Drawdown gauge

2. **Positions:**
   - Current positions table
   - Exposure by symbol
   - Exposure by strategy

3. **Risk:**
   - VaR gauge
   - Position limits usage
   - Circuit breaker status

4. **System Health:**
   - API latency (p50, p95, p99)
   - Error rate
   - Order throughput
   - Exchange status

5. **Execution Quality:**
   - Slippage distribution
   - Fill rate
   - Rejection rate by exchange

### 4. Circuit Breakers & Kill Switch

#### a) Circuit Breaker Levels

```python
CIRCUIT_BREAKERS = [
    {
        'name': 'Level 1 - Warning',
        'trigger': 'daily_pnl < -0.03',  # -3%
        'action': 'send_alert',
        'auto_reset': True,
        'reset_condition': 'daily_pnl > -0.02'
    },
    {
        'name': 'Level 2 - Reduce Risk',
        'trigger': 'daily_pnl < -0.05',  # -5%
        'action': 'reduce_positions_50_percent',
        'auto_reset': False,
        'manual_reset_required': True
    },
    {
        'name': 'Level 3 - Stop Trading',
        'trigger': 'daily_pnl < -0.08',  # -8%
        'action': 'stop_new_trades',
        'auto_reset': False,
        'manual_reset_required': True
    },
    {
        'name': 'Level 4 - Kill Switch',
        'trigger': 'daily_pnl < -0.10 or drawdown < -0.20',
        'action': 'close_all_positions_and_stop',
        'auto_reset': False,
        'manual_reset_required': True,
        'escalation': 'notify_management'
    }
]
```

#### b) Kill Switch Implementation

```python
class KillSwitch:
    def __init__(self, config):
        self.config = config
        self.active = False
        self.triggered_at = None
        self.trigger_reason = None
    
    def check_and_trigger(self, risk_metrics):
        """Check if kill switch should be triggered."""
        if self.active:
            return True  # Already triggered
        
        # Check conditions
        if risk_metrics['daily_pnl'] < self.config['kill_switch_daily_loss']:
            return self.trigger('daily_loss', risk_metrics['daily_pnl'])
        
        if risk_metrics['drawdown'] < self.config['kill_switch_drawdown']:
            return self.trigger('drawdown', risk_metrics['drawdown'])
        
        if risk_metrics['var_breach']:
            return self.trigger('var_breach', risk_metrics['var'])
        
        return False
    
    def trigger(self, reason, value):
        """Trigger kill switch."""
        self.active = True
        self.triggered_at = datetime.utcnow()
        self.trigger_reason = reason
        
        # Execute kill switch actions
        actions = [
            self.stop_new_trades,
            self.close_all_positions,
            self.notify_team,
            self.log_event
        ]
        
        for action in actions:
            action(reason, value)
        
        return True
    
    async def close_all_positions(self):
        """Close all open positions immediately."""
        for position in self.get_all_positions():
            await self.close_position(position)
        
        logger.critical(f"Kill switch: Closed all positions, reason={self.trigger_reason}")
    
    def stop_new_trades(self):
        """Block all new trade signals."""
        self.trading_enabled = False
    
    async def reset(self, authorized_by):
        """Reset kill switch (requires authorization)."""
        if not self.is_authorized(authorized_by):
            raise PermissionError("Unauthorized kill switch reset")
        
        self.active = False
        self.trading_enabled = True
        self.trigger_reason = None
        
        logger.info(f"Kill switch reset by {authorized_by}")
```

### 5. Testing & CI/CD

#### a) Testing Pyramid

```
                    ┌─────────────┐
                    │   E2E       │  (10%)
                    │   Tests     │
                   ─┴─────────────┴─
                  ┌─────────────────┐
                  │  Integration    │  (30%)
                  │  Tests          │
                 ─┴─────────────────┴─
                ┌───────────────────┐
                │    Unit Tests     │  (60%)
                │                   │
               ─┴───────────────────┴─
```

**Unit Tests:**
```python
# test_signal_engine.py
def test_rsi_signal():
    """Test RSI-based signal generation."""
    prices = [50, 51, 52, 53, 54, 55, 56, 57, 58, 59]  # Uptrend
    rsi = calculate_rsi(prices, period=14)
    
    assert rsi > 70, "RSI should be overbought in strong uptrend"

def test_mean_reversion_signal():
    """Test mean reversion signal."""
    # Create oversold scenario
    prices = [100, 90, 80, 70, 60, 50, 45, 40, 38, 37]
    
    signal = mean_reversion_strategy(prices)
    
    assert signal.direction == 'long'
    assert signal.confidence > 0.5
```

**Integration Tests:**
```python
# test_pipeline_integration.py
@pytest.mark.integration
def test_full_pipeline():
    """Test full trading pipeline."""
    # Setup
    data_pipeline = DataPipeline()
    signal_engine = SignalEngine()
    risk_manager = RiskManager(config)
    execution_engine = ExecutionEngine(exchanges)
    
    # Run pipeline
    market_data = data_pipeline.get_latest_data()
    signal = signal_engine.generate_signals(market_data)
    approval = risk_manager.check_pre_trade(signal, market_data['price'])
    
    if approval.approved:
        result = execution_engine.execute_signal(signal, approval)
        assert result.success
```

**E2E Tests:**
```python
# test_e2e.py
@pytest.mark.e2e
def test_full_trading_day():
    """Simulate full trading day."""
    # Replay historical data
    # Run entire system
    # Verify PnL, positions, risk metrics
    pass
```

#### b) CI/CD Pipeline

```yaml
# .github/workflows/trading-system.yml
name: Trading System CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Lint
        run: |
          flake8 .
          black --check .
          mypy .
      
      - name: Unit tests
        run: pytest tests/unit -v
      
      - name: Integration tests
        run: pytest tests/integration -v
      
      - name: Build Docker image
        run: docker build -t trading-system:${{ github.sha }} .
  
  deploy-staging:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    steps:
      - name: Deploy to staging
        run: |
          kubectl apply -f k8s/staging/
          kubectl rollout status deployment/trading-system-staging
  
  deploy-production:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          kubectl apply -f k8s/production/
          kubectl rollout status deployment/trading-system
```

### 6. Deployment Architecture

#### a) Kubernetes Deployment

```yaml
# k8s/production/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trading-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: trading-system
  template:
    metadata:
      labels:
        app: trading-system
    spec:
      containers:
      - name: trading-system
        image: trading-system:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: trading-secrets
              key: database-url
        - name: EXCHANGE_API_KEYS
          valueFrom:
            secretKeyRef:
              name: trading-secrets
              key: exchange-api-keys
        resources:
          limits:
            memory: "2Gi"
            cpu: "1000m"
          requests:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### b) Disaster Recovery

**RTO (Recovery Time Objective):** < 5 minutes  
**RPO (Recovery Point Objective):** < 1 minute

**Backup Strategy:**
```
- Database: Continuous replication + hourly snapshots
- Config: Git version control
- Secrets: Encrypted backup (Vault)
- Logs: Shipped to central logging (ELK/Splunk)
```

**Failover:**
```
- Multi-region deployment (primary + standby)
- Automatic failover on health check failure
- Manual failback after incident resolution
```

---

## ✅ Checklist de Compréhension

- [ ] Comprendre architecture complète (data → signal → risk → execution)
- [ ] Connaître composants: Data Pipeline, Signal Engine, Risk Manager, Execution Engine
- [ ] Savoir designer monitoring & alerting (metrics, dashboards)
- [ ] Comprendre circuit breakers et kill switch
- [ ] Connaître testing pyramid (unit, integration, E2E)
- [ ] Comprendre CI/CD pour trading systems
- [ ] Connaître deployment patterns (Kubernetes, failover)
- [ ] Comprendre disaster recovery (RTO, RPO)

---

## 📚 Références

1. **Quantitative Trading: How to Build Your Own Algorithmic Trading Business** - Chan
2. **Algorithmic Trading: Winning Strategies and Their Rationale** - Chan
3. **Building Low Latency Applications with C++** - Raymundo
4. **Site Reliability Engineering** - Google SRE Team
5. **Designing Data-Intensive Applications** - Kleppmann

---

## 🎯 Prochaines Étapes

**Master 5+ Suite:**
- [ ] Semaine 26: Reinforcement Learning pour Trading

**Phase 2 - Intégration Saiyan:**
- [ ] Architecture review du système actuel
- [ ] Implémenter monitoring (Prometheus + Grafana)
- [ ] Circuit breakers + kill switch
- [ ] CI/CD pipeline
- [ ] Testing framework

---

*Module Master 5 - Production Systems complété ✅*
