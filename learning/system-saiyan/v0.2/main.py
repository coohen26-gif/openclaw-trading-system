#!/usr/bin/env python3
"""
Système Saiyan v0.2 - Production-Ready Quant Trading System

Module: Phase 3 - Production Readiness
Author: Saiyan Autonomous Trading System
Date: May 26, 2026

Architecture:
- Momentum+HMM Strategy (4 régimes)
- Risk Monitor (VaR/CVaR + Circuit Breakers + Derivatives)
- Portfolio Allocator (Risk Parity BTC/ETH/SOL)
- Deribit IV Fetcher (Master 5 - Derivatives)
- Telegram Notifier (Alerts + Signals)
- Binance Data Fetcher (Real-time OHLCV)

Modes:
- monitor: Real-time risk monitoring + signal generation
- backtest: Historical backtesting
- paper: Paper trading with simulated execution
"""

import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import warnings
warnings.filterwarnings('ignore')

# Add parent directories to path
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "code"))
sys.path.insert(0, str(BASE_DIR / "utils"))
sys.path.insert(0, str(BASE_DIR / "data"))

from risk_monitor import RiskMonitor, AlertLevel, CircuitBreakerLevel
from portfolio_allocator import PortfolioAllocator
from momentum_hmm_optimized import MomentumBreakoutOptimized, MarketRegime
from telegram_notifier import TelegramNotifier
from deribit_iv_fetcher import DeribitIVFetcher

# Optional: Binance connector (may not be available in all setups)
try:
    from binance_connector import BinanceConnector
    HAS_BINANCE = True
except ImportError:
    HAS_BINANCE = False
    BinanceConnector = None


class SaiyanSystem:
    """
    Main entry point for Saiyan Trading System v0.2.
    
    Integrates:
    - Strategy: Momentum+HMM (4 régimes)
    - Risk: VaR/CVaR + Circuit Breakers + Greeks monitoring
    - Portfolio: Risk Parity multi-asset
    - Data: Binance (OHLCV) + Deribit (IV)
    - Notifications: Telegram alerts
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize Saiyan System.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        
        # Initialize components
        print("🐉 Initializing Saiyan System v0.2...\n")
        
        # Risk Monitor
        self.risk_monitor = RiskMonitor(
            initial_capital=self.config.get("initial_capital", 10000),
            var_confidence=self.config.get("var_confidence", 0.95),
            lookback_days=self.config.get("lookback_days", 30)
        )
        
        # Portfolio Allocator
        self.allocator = PortfolioAllocator(
            assets=self.config.get("assets", ["BTC", "ETH", "SOL"]),
            rebalance_threshold=self.config.get("rebalance_threshold", 0.05)
        )
        
        # Strategy (lazy init - will be created when needed)
        self._strategy = None
        
        # Data Fetchers
        if HAS_BINANCE:
            self.binance = BinanceConnector()
            print("   ✅ Binance connector initialized")
        else:
            self.binance = None
            print("   ⚠️  Binance connector not available")
        
        self.deribit_fetcher = DeribitIVFetcher(
            cache_dir=str(BASE_DIR / "data" / "iv_cache")
        )
        
        # Notifier (lazy init)
        self._notifier = None
        
        # State
        self.portfolio_vega = 0.0
        self.portfolio_delta = 0.0
        self.last_rebalance = datetime.now()
        
        print("✅ System initialized successfully\n")
    
    @property
    def strategy(self):
        """Lazy init strategy"""
        if self._strategy is None:
            self._strategy = MomentumBreakoutOptimized(
                n_regimes=self.config.get("hmm_states", 4),
                lookback_days=self.config.get("hmm_lookback", 60)
            )
        return self._strategy
    
    @property
    def notifier(self):
        """Lazy init notifier"""
        if self._notifier is None:
            self._notifier = TelegramNotifier(
                state_file=str(BASE_DIR / "data" / "telegram_state.json")
            )
        return self._notifier
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        
        # Default configuration
        return {
            "initial_capital": 10000,
            "var_confidence": 0.95,
            "lookback_days": 30,
            "assets": ["BTC", "ETH", "SOL"],
            "rebalance_threshold": 0.05,
            "momentum_period": 20,
            "hmm_states": 4,
            "hmm_lookback": 60,
            "telegram_enabled": True,
            "trading_allowed": True
        }
    
    def run_monitor(self):
        """
        Run real-time monitoring mode.
        
        - Fetch live data from Binance (if available)
        - Fetch IV data from Deribit
        - Calculate risk metrics
        - Check for trading signals
        - Send Telegram alerts if needed
        """
        print("🔍 Running Monitor Mode...\n")
        
        # Fetch live prices (if Binance available)
        print("📊 Fetching market data...")
        if HAS_BINANCE and self.binance:
            try:
                prices = self.binance.fetch_multi_asset(['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])
                print(f"   BTC: ${prices.get('BTCUSDT', 0):,.2f}")
                print(f"   ETH: ${prices.get('ETHUSDT', 0):,.2f}")
                print(f"   SOL: ${prices.get('SOLUSDT', 0):,.2f}")
            except Exception as e:
                print(f"   ⚠️  Binance fetch failed: {e}")
        else:
            print("   ⚠️  Binance not available, using cached data")
        
        # Fetch IV data
        print("\n📊 Fetching IV data from Deribit...")
        iv_data = self.deribit_fetcher.get_multi_asset_iv(["BTC", "ETH"])
        for asset, data in iv_data.items():
            print(f"   {asset}: {data['iv_25d']:.1f}% (p{data['iv_percentile']:.0f})")
            if data.get('iv_skew'):
                print(f"      Skew: {data['iv_skew']:.2f}")
        
        # Update derivatives risk metrics
        if iv_data.get('BTC'):
            self.risk_monitor.update_derivatives_metrics(
                iv_25d=iv_data['BTC']['iv_25d'],
                iv_skew=iv_data['BTC'].get('iv_skew')
            )
        
        # Check derivatives alerts
        print("\n🛡️  Checking derivatives risk...")
        if iv_data.get('BTC'):
            iv_alert = self.risk_monitor.check_iv_percentile(
                iv_current=iv_data['BTC']['iv_25d'],
                iv_percentile=iv_data['BTC']['iv_percentile']
            )
            if iv_alert:
                print(f"   ⚠️  {iv_alert.message}")
                self.notifier.send_alert(
                    level="WARNING",
                    message=iv_alert.message,
                    metric="iv_percentile",
                    value=iv_alert.value,
                    threshold=iv_alert.threshold
                )
            
            skew_alert = self.risk_monitor.check_iv_skew(
                put_call_skew=iv_data['BTC'].get('iv_skew', 1.0)
            )
            if skew_alert:
                print(f"   ℹ️  {skew_alert.message}")
        
        # Get risk metrics
        print("\n🛡️  Risk Metrics:")
        metrics = self.risk_monitor.get_risk_metrics()
        print(f"   VaR 95%: {metrics.var_95*100:.2f}%")
        print(f"   CVaR 95%: {metrics.cvar_95*100:.2f}%")
        print(f"   Drawdown: {metrics.drawdown*100:.2f}%")
        print(f"   Circuit Breaker: {metrics.circuit_breaker_level.value}")
        
        # Check trading allowed
        allowed, reason = self.risk_monitor.check_trading_allowed()
        status = "✅ ALLOWED" if allowed else "❌ BLOCKED"
        print(f"\n   Trading: {status}")
        print(f"   Reason: {reason}")
        
        # Portfolio check
        print("\n💼 Portfolio Allocation:")
        # Use default Risk Parity weights from config
        weights = self.config.get("portfolio", {}).get("risk_parity", {
            "BTC": 0.52, "ETH": 0.28, "SOL": 0.20
        })
        for asset, weight in weights.items():
            print(f"   {asset}: {weight*100:.1f}%")
        
        print("\n✅ Monitor cycle complete")
        return metrics
    
    def run_backtest(self, asset: str = "BTC/USDT", start_date: str = "2020-01-01"):
        """
        Run backtest mode.
        
        Args:
            asset: Trading pair (e.g., BTC/USDT)
            start_date: Backtest start date
        """
        print(f"🧪 Running Backtest Mode: {asset}\n")
        
        # Load cached data
        data_file = BASE_DIR / "data" / "btc_usdt_daily_2020_2026.csv"
        if not data_file.exists():
            print(f"   ❌ Data file not found: {data_file}")
            return
        
        import pandas as pd
        df = pd.read_csv(data_file)
        print(f"   📊 {len(df)} candles loaded from cache")
        
        # Run strategy backtest
        print("\n📈 Running Momentum+HMM strategy...")
        # Use the run_comparison function from momentum_hmm_optimized
        from momentum_hmm_optimized import run_comparison
        results = run_comparison()
        
        print("\n📊 Backtest Results:")
        if 'optimized' in results:
            opt = results['optimized']
            print(f"   Return: {opt.get('total_return', 0)*100:+.2f}%")
            print(f"   Sharpe: {opt.get('sharpe_ratio', 0):.2f}")
            print(f"   Max DD: {opt.get('max_drawdown', 0)*100:.2f}%")
            print(f"   Win Rate: {opt.get('win_rate', 0)*100:.1f}%")
            print(f"   Trades: {opt.get('n_trades', 0)}")
        
        return results
    
    def run_paper(self, symbol: str = "BTC/USDT"):
        """
        Run paper trading mode.
        
        Args:
            symbol: Trading pair
        """
        print(f"📝 Running Paper Trading Mode: {symbol}\n")
        
        # Load cached data
        import pandas as pd
        data_file = BASE_DIR / "data" / "btc_usdt_daily_2020_2026.csv"
        if not data_file.exists():
            print(f"   ❌ Data file not found: {data_file}")
            return
        
        df = pd.read_csv(data_file)
        print(f"   📊 {len(df)} candles loaded from cache")
        
        # Generate signal
        print("\n📈 Generating trading signal...")
        prices = df['close']
        high = df['high']
        low = df['low']
        
        signal = self.strategy.generate_signal(prices, high, low)
        
        if signal['signal'] == 0:
            print("   ⏸️  NO SIGNAL - Waiting for better setup")
            return
        
        direction = "LONG" if signal['signal'] > 0 else "SHORT"
        print(f"   Signal: {direction}")
        print(f"   Confidence: {signal['confidence']*100:.1f}%")
        print(f"   Regime: {signal.get('regime', 'Unknown')}")
        
        # Check risk limits
        allowed, reason = self.risk_monitor.check_trading_allowed()
        if not allowed:
            print(f"\n   ❌ Trade BLOCKED: {reason}")
            self.notifier.send_alert(
                level="CRITICAL",
                message=f"Trade blocked: {reason}",
                metric="circuit_breaker",
                value=0,
                threshold=0
            )
            return
        
        # Calculate position size
        base_size = self.config.get("initial_capital", 10000) * 0.10  # 10% base
        max_size = self.risk_monitor.get_position_size_limit(base_size)
        
        print(f"\n💰 Position Sizing:")
        print(f"   Base: ${base_size:,.2f}")
        print(f"   Max allowed: ${max_size:,.2f}")
        
        # Send signal to Telegram
        self.notifier.send_signal(
            asset=symbol,
            direction=direction,
            entry=prices.iloc[-1],
            stop_loss=signal.get('stop_loss', 0),
            take_profit=signal.get('take_profit', 0),
            position_size=max_size,
            regime=signal.get('regime', 'Unknown'),
            confidence=signal['confidence']
        )
        
        print("\n✅ Paper trade signal sent")
        return signal
    
    def print_status(self):
        """Print full system status"""
        print("\n" + "="*60)
        print("🐉 SAIYAN SYSTEM v0.2 - STATUS")
        print("="*60)
        
        # Risk status
        metrics = self.risk_monitor.get_risk_metrics()
        print(f"\n🛡️  RISK")
        print(f"   Capital: ${self.risk_monitor.current_capital:,.2f}")
        print(f"   VaR 95%: {metrics.var_95*100:.2f}%")
        print(f"   CVaR 95%: {metrics.cvar_95*100:.2f}%")
        print(f"   Circuit Breaker: {metrics.circuit_breaker_level.value}")
        
        # Derivatives risk
        if metrics.portfolio_vega is not None:
            print(f"\n📊 DERIVATIVES")
            print(f"   Vega: ${metrics.portfolio_vega:,.2f}")
            print(f"   Delta: ${metrics.portfolio_delta:,.2f}")
            if metrics.iv_25d:
                print(f"   IV 25d: {metrics.iv_25d:.1f}%")
            if metrics.iv_skew:
                print(f"   Skew: {metrics.iv_skew:.2f}")
        
        # Portfolio
        print(f"\n💼 PORTFOLIO")
        # Use default Risk Parity weights from config
        weights = self.config.get("portfolio", {}).get("risk_parity", {
            "BTC": 0.52, "ETH": 0.28, "SOL": 0.20
        })
        for asset, weight in weights.items():
            print(f"   {asset}: {weight*100:.1f}%")
        
        # Trading status
        allowed, reason = self.risk_monitor.check_trading_allowed()
        status = "✅ ALLOWED" if allowed else "❌ BLOCKED"
        print(f"\n📈 TRADING: {status}")
        print(f"   {reason}")
        
        print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(description="Saiyan Trading System v0.2")
    parser.add_argument(
        "--mode",
        choices=["monitor", "backtest", "paper", "status"],
        default="monitor",
        help="Operating mode"
    )
    parser.add_argument(
        "--asset",
        default="BTC/USDT",
        help="Trading pair (for backtest/paper)"
    )
    parser.add_argument(
        "--start-date",
        default="2020-01-01",
        help="Backtest start date"
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Configuration file path"
    )
    
    args = parser.parse_args()
    
    # Initialize system
    system = SaiyanSystem(config_path=args.config)
    
    # Run mode
    if args.mode == "monitor":
        system.run_monitor()
    elif args.mode == "backtest":
        system.run_backtest(args.asset, args.start_date)
    elif args.mode == "paper":
        system.run_paper(args.asset)
    elif args.mode == "status":
        system.print_status()


if __name__ == "__main__":
    main()
