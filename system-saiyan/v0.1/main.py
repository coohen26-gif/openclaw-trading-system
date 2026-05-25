#!/usr/bin/env python3
"""
Système Saiyan v0.1 - Main Entry Point
Prototype Paper-Trade : Metals (60%) + Crypto (25%)
Stratégies : Mean Reversion (prioritaire) + Momentum
TF : 1h, 4h, daily
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data.data_pipeline import DataPipeline
from core.feature_engineering import FeatureEngineer
from core.signal_generator import SignalGenerator
from core.risk_manager import RiskManager
from backtests.backtester import Backtester, BacktestConfig
from utils.telegram_notifier import TelegramNotifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SaiyanSystem:
    """
    Système Saiyan v0.1 - Prototype Paper-Trade
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialise le système
        
        Args:
            config_path: Chemin vers config.json
        """
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.pipeline = DataPipeline()
        self.feature_engineer = FeatureEngineer()
        self.signal_generator = SignalGenerator()
        self.risk_manager = RiskManager(total_capital=self.config['capital'])
        self.notifier = TelegramNotifier(use_openclaw=True)
        
        logger.info("🐉 Système Saiyan v0.1 initialized")
    
    def _load_config(self, config_path: str = None) -> Dict:
        """Charge la configuration"""
        if config_path is None:
            config_path = Path(__file__).parent / 'config.json'
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"✓ Loaded config from {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Config not found, using defaults")
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """Configuration par défaut"""
        return {
            'capital': 10000,
            'trading_rules': {
                'min_confidence': 60,
                'position_size_min': 2.0,
                'position_size_max': 5.0,
                'stop_loss_pct': 2.5,
                'take_profit_pct': 1.0,
                'max_trades_per_day': 5,
                'trading_fee_pct': 0.1,
                'slippage_pct': 0.05
            },
            'assets': {
                'crypto': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
                'metals': ['GC=F', 'SI=F']
            },
            'timeframes': ['1h', '4h', '1d'],
            'strategies': ['mean_reversion', 'momentum']
        }
    
    def run_paper_trading_cycle(self,
                                 assets: List[str] = None,
                                 timeframe: str = '1h',
                                 strategy: str = 'mean_reversion') -> List[Dict]:
        """
        Exécute un cycle complet de paper-trading
        
        Args:
            assets: Liste des assets à analyser
            timeframe: Timeframe ('1h', '4h', '1d')
            strategy: Stratégie ('mean_reversion' ou 'momentum')
        
        Returns:
            Liste des signaux générés
        """
        logger.info(f"🚀 Starting paper-trading cycle: {strategy} on {timeframe}")
        
        all_signals = []
        
        # Assets par défaut
        if assets is None:
            assets = self.config['assets']['crypto'][:2] + self.config['assets']['metals'][:1]
        
        for asset in assets:
            logger.info(f"\n📊 Analyzing {asset}...")
            
            # 1. Fetch data
            if '/' in asset:  # Crypto
                df = self.pipeline.fetch_crypto_data(asset, timeframe, limit=500)
            else:  # Metals
                df = self.pipeline.fetch_metals_data(asset, period='3mo', interval='1h')
            
            if df.empty:
                logger.warning(f"No data for {asset}, skipping")
                continue
            
            df.attrs['symbol'] = asset
            
            # 2. Feature engineering
            df = self.feature_engineer.calculate_all_features(df)
            
            # 3. Signal generation
            signals = self.signal_generator.generate_signals(df, strategy)
            
            # 4. Risk management + notification
            for signal in signals:
                if self.signal_generator.should_execute_signal(signal):
                    # Calculate position
                    params = self.risk_manager.calculate_position_size(signal)
                    trade_summary = self.risk_manager.get_trade_summary(params)
                    
                    # Add to signal
                    signal['trade_params'] = trade_summary
                    
                    # Send to Telegram
                    self.notifier.send_signal(signal, trade_summary)
                    
                    # Record
                    self.signal_generator.record_signal(signal)
                    all_signals.append(signal)
        
        logger.info(f"\n✓ Cycle completed: {len(all_signals)} signals generated")
        
        return all_signals
    
    def run_backtest(self,
                     asset: str = 'BTC/USDT',
                     timeframe: str = '1h',
                     strategy: str = 'mean_reversion',
                     walk_forward: bool = True) -> Dict:
        """
        Exécute un backtest
        
        Args:
            asset: Asset à backtester
            timeframe: Timeframe
            strategy: Stratégie
            walk_forward: Activer walk-forward validation
        
        Returns:
            Dict avec résultats
        """
        logger.info(f"📊 Running backtest: {asset} {timeframe} {strategy}")
        
        # 1. Fetch data
        if '/' in asset:
            df = self.pipeline.fetch_crypto_data(asset, timeframe, limit=2000)
        else:
            df = self.pipeline.fetch_metals_data(asset, period='1y', interval='1h')
        
        if df.empty:
            return {'error': 'No data'}
        
        df.attrs['symbol'] = asset
        
        # 2. Feature engineering
        df = self.feature_engineer.calculate_all_features(df)
        
        # 3. Generate signals (no daily limit for backtest)
        signals = self.signal_generator.generate_signals(df, strategy, apply_daily_limit=False)
        
        if not signals:
            return {'error': 'No signals generated'}
        
        # 4. Run backtest
        config = BacktestConfig(
            initial_capital=self.config['capital'],
            trading_fee_pct=self.config['trading_rules']['trading_fee_pct'],
            slippage_pct=self.config['trading_rules']['slippage_pct'],
            position_size_pct=self.config['trading_rules']['position_size_min'],
            stop_loss_pct=self.config['trading_rules']['stop_loss_pct'],
            take_profit_pct=self.config['trading_rules']['take_profit_pct'],
            min_confidence=self.config['trading_rules']['min_confidence']
        )
        
        backtester = Backtester(config)
        
        if walk_forward:
            metrics = backtester.walk_forward_validation(df, signals, n_splits=3)
        else:
            metrics = backtester.run_backtest(df, signals)
        
        logger.info(f"✓ Backtest completed")
        
        return metrics


def main():
    """Main entry point"""
    print("=" * 60)
    print("🐉 SYSTÈME SAIYAN v0.1 - Paper-Trade Prototype")
    print("=" * 60)
    
    # Initialize system
    config_path = Path(__file__).parent / 'config.json'
    system = SaiyanSystem(config_path)
    
    print("\n📋 Configuration loaded:")
    print(f"  Capital: ${system.config['capital']:,}")
    print(f"  Min Confidence: {system.config['trading_rules']['min_confidence']}/100")
    print(f"  Position Size: {system.config['trading_rules']['position_size_min']}-{system.config['trading_rules']['position_size_max']}%")
    print(f"  Stop Loss: {system.config['trading_rules']['stop_loss_pct']}%")
    print(f"  Take Profit: {system.config['trading_rules']['take_profit_pct']}%")
    
    # Run paper-trading cycle
    print("\n" + "=" * 60)
    print("🚀 Running Paper-Trading Cycle")
    print("=" * 60)
    
    signals = system.run_paper_trading_cycle(
        assets=['BTC/USDT', 'ETH/USDT', 'GC=F'],
        timeframe='1h',
        strategy='mean_reversion'
    )
    
    print(f"\n✓ Generated {len(signals)} signals")
    
    # Run backtest
    print("\n" + "=" * 60)
    print("📊 Running Backtest")
    print("=" * 60)
    
    metrics = system.run_backtest(
        asset='BTC/USDT',
        timeframe='1h',
        strategy='mean_reversion',
        walk_forward=True
    )
    
    print("\n📈 Backtest Results:")
    for key, value in metrics.items():
        if key != 'splits':
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ Système Saiyan v0.1 Ready for Paper-Trading!")
    print("=" * 60)


if __name__ == "__main__":
    main()
