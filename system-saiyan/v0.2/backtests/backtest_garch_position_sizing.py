"""
🐉 GARCH Position Sizing Backtest - A/B Comparison

Compare static position sizing vs dynamic GARCH-based sizing.

Backtest Parameters:
- Data: BTC 2020-2026 (2337 jours)
- Strategy: Momentum+HMM (same for both)
- Base position: 5% capital

A/B Test:
- Arm A (Static): Fixed 5% position size
- Arm B (GARCH Dynamic): size = 5% × (target_vol / predicted_vol)

Expected Results:
- GARCH dynamic should reduce drawdown during high vol periods
- GARCH dynamic should increase returns during low vol periods
- Overall: Better risk-adjusted returns (higher Sharpe)
"""

import numpy as np
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from volatility.garch_model import GARCHVolatilityModel
from strategies.momentum_hmm import MomentumHMMStrategy, Signal


def load_btc_data() -> pd.DataFrame:
    """Load BTC historical data."""
    data_path = Path(__file__).parent.parent.parent / 'learning' / 'data' / 'btc_real_2020_2026.csv'
    
    if data_path.exists():
        df = pd.read_csv(data_path, parse_dates=['Date'], index_col='Date')
        # Standardize column names
        df.columns = df.columns.str.lower()
        if 'close' not in df.columns and 'adj close' in df.columns:
            df['close'] = df['adj close']
        return df[['open', 'high', 'low', 'close', 'volume']]
    else:
        # Generate synthetic data if file not found
        print("⚠️ BTC data file not found, generating synthetic data...")
        np.random.seed(42)
        n_days = 2337
        
        # Simulate BTC-like price series with volatility clustering
        base_vol = 0.03
        vol = np.ones(n_days) * base_vol
        returns = np.zeros(n_days)
        
        for t in range(1, n_days):
            vol[t] = np.sqrt(0.1 * base_vol**2 + 0.1 * returns[t-1]**2 + 0.85 * vol[t-1]**2)
            returns[t] = np.random.normal(0.0005, vol[t])
        
        prices = 10000 * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame({
            'open': prices * (1 + np.random.uniform(-0.01, 0.01, n_days)),
            'high': prices * (1 + np.random.uniform(0, 0.03, n_days)),
            'low': prices * (1 + np.random.uniform(-0.03, 0, n_days)),
            'close': prices,
            'volume': np.random.uniform(1e9, 1e10, n_days)
        })
        df.index = pd.date_range(start='2020-01-01', periods=n_days, freq='D')
        
        return df


def run_backtest_arm_a(df: pd.DataFrame, initial_capital: float = 10000) -> dict:
    """
    Arm A: Static position sizing (fixed 5%).
    
    Returns: backtest results
    """
    print("\n" + "=" * 60)
    print("ARM A: Static Position Sizing (5% fixed)")
    print("=" * 60)
    
    strategy = MomentumHMMStrategy(
        momentum_period=20,
        hmm_lookback=60,
        confidence_threshold=0.6
    )
    
    capital = initial_capital
    position = None
    trades = []
    equity_curve = [initial_capital]
    
    # Warmup for HMM
    warmup = 60
    
    for i in range(warmup, len(df)):
        window = df.iloc[:i+1].copy()
        current_price = window['close'].iloc[-1]
        
        # Generate signal
        signal = strategy.generate_signal(window, 'BTC/USDT')
        
        # Exit logic
        if position is not None:
            exit_reason = None
            exit_price = None
            
            # Check stop loss
            if position['direction'] == 'LONG' and current_price <= position['stop_loss']:
                exit_reason = 'STOP_LOSS'
                exit_price = position['stop_loss']
            elif position['direction'] == 'SHORT' and current_price >= position['stop_loss']:
                exit_reason = 'STOP_LOSS'
                exit_price = position['stop_loss']
            
            # Check take profit
            elif position['direction'] == 'LONG' and current_price >= position['take_profit']:
                exit_reason = 'TAKE_PROFIT'
                exit_price = position['take_profit']
            elif position['direction'] == 'SHORT' and current_price <= position['take_profit']:
                exit_reason = 'TAKE_PROFIT'
                exit_price = position['take_profit']
            
            # Check time exit (max 20 days)
            elif i - position['entry_idx'] >= 20:
                exit_reason = 'TIME_EXIT'
                exit_price = current_price
            
            # Exit position
            if exit_reason:
                if position['direction'] == 'LONG':
                    pnl_pct = (exit_price - position['entry_price']) / position['entry_price']
                else:
                    pnl_pct = (position['entry_price'] - exit_price) / position['entry_price']
                
                pnl = capital * position['size_pct'] * pnl_pct
                capital += pnl
                
                trades.append({
                    'entry_date': df.index[position['entry_idx']],
                    'exit_date': df.index[i],
                    'direction': position['direction'],
                    'entry_price': position['entry_price'],
                    'exit_price': exit_price,
                    'pnl_pct': pnl_pct,
                    'pnl': pnl,
                    'size_pct': position['size_pct'],
                    'exit_reason': exit_reason
                })
                
                position = None
        
        # Enter new position
        if position is None and signal is not None:
            position = {
                'direction': signal.direction,
                'entry_price': current_price,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'size_pct': 0.05,  # FIXED 5%
                'entry_idx': i
            }
        
        equity_curve.append(capital)
    
    # Calculate metrics
    equity = pd.Series(equity_curve)
    returns = equity.pct_change().dropna()
    
    total_return = (equity.iloc[-1] - initial_capital) / initial_capital
    sharpe = returns.mean() / returns.std() * np.sqrt(252) if len(returns) > 0 else 0
    max_dd = ((equity.cummax() - equity) / equity.cummax()).max()
    win_trades = [t for t in trades if t['pnl'] > 0]
    win_rate = len(win_trades) / len(trades) if trades else 0
    
    results = {
        'arm': 'A (Static)',
        'total_return': total_return,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_dd,
        'win_rate': win_rate,
        'n_trades': len(trades),
        'final_capital': equity.iloc[-1],
        'equity_curve': equity_curve,
        'trades': trades
    }
    
    print(f"\nTotal Return: {total_return:.2%}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")
    print(f"Win Rate: {win_rate:.1%}")
    print(f"N Trades: {len(trades)}")
    print(f"Final Capital: ${equity.iloc[-1]:,.2f}")
    
    return results


def run_backtest_arm_b(df: pd.DataFrame, initial_capital: float = 10000) -> dict:
    """
    Arm B: Dynamic GARCH-based position sizing.
    
    Formula: size = base_size × (target_vol / predicted_vol)
    
    Returns: backtest results
    """
    print("\n" + "=" * 60)
    print("ARM B: Dynamic GARCH Position Sizing")
    print("=" * 60)
    
    strategy = MomentumHMMStrategy(
        momentum_period=20,
        hmm_lookback=60,
        confidence_threshold=0.6
    )
    
    garch = GARCHVolatilityModel()
    garch_target_vol = 2.5  # Target daily vol %
    
    capital = initial_capital
    position = None
    trades = []
    equity_curve = [initial_capital]
    
    # Warmup for HMM and GARCH
    warmup = 100  # Need more data for GARCH
    
    for i in range(warmup, len(df)):
        window = df.iloc[:i+1].copy()
        current_price = window['close'].iloc[-1]
        
        # Fit GARCH on rolling window (cache avoids refit)
        try:
            prices_array = window['close'].values[-200:]  # Last 200 days for GARCH
            garch.fit(prices=pd.Series(prices_array), force_refit=False)
            vol_forecast = garch.forecast()
            
            # Calculate dynamic position size
            multiplier = garch.get_position_size_multiplier(target_vol=garch_target_vol)
            size_pct = 0.05 * multiplier  # Base 5% adjusted by vol
            size_pct = min(size_pct, 0.10)  # Cap at 10%
            size_pct = max(size_pct, 0.02)  # Floor at 2%
            
        except Exception as e:
            # Fallback to base size if GARCH fails
            size_pct = 0.05
        
        # Generate signal
        signal = strategy.generate_signal(window, 'BTC/USDT')
        
        # Exit logic (same as Arm A)
        if position is not None:
            exit_reason = None
            exit_price = None
            
            if position['direction'] == 'LONG' and current_price <= position['stop_loss']:
                exit_reason = 'STOP_LOSS'
                exit_price = position['stop_loss']
            elif position['direction'] == 'SHORT' and current_price >= position['stop_loss']:
                exit_reason = 'STOP_LOSS'
                exit_price = position['stop_loss']
            elif position['direction'] == 'LONG' and current_price >= position['take_profit']:
                exit_reason = 'TAKE_PROFIT'
                exit_price = position['take_profit']
            elif position['direction'] == 'SHORT' and current_price <= position['take_profit']:
                exit_reason = 'TAKE_PROFIT'
                exit_price = position['take_profit']
            elif i - position['entry_idx'] >= 20:
                exit_reason = 'TIME_EXIT'
                exit_price = current_price
            
            if exit_reason:
                if position['direction'] == 'LONG':
                    pnl_pct = (exit_price - position['entry_price']) / position['entry_price']
                else:
                    pnl_pct = (position['entry_price'] - exit_price) / position['entry_price']
                
                pnl = capital * position['size_pct'] * pnl_pct
                capital += pnl
                
                trades.append({
                    'entry_date': df.index[position['entry_idx']],
                    'exit_date': df.index[i],
                    'direction': position['direction'],
                    'entry_price': position['entry_price'],
                    'exit_price': exit_price,
                    'pnl_pct': pnl_pct,
                    'pnl': pnl,
                    'size_pct': position['size_pct'],
                    'exit_reason': exit_reason,
                    'garch_vol': position.get('garch_vol', None),
                    'multiplier': position.get('multiplier', None)
                })
                
                position = None
        
        # Enter new position
        if position is None and signal is not None:
            position = {
                'direction': signal.direction,
                'entry_price': current_price,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'size_pct': size_pct,
                'entry_idx': i,
                'garch_vol': vol_forecast.daily_volatility if 'vol_forecast' in dir() else None,
                'multiplier': multiplier if 'multiplier' in dir() else None
            }
        
        equity_curve.append(capital)
    
    # Calculate metrics
    equity = pd.Series(equity_curve)
    returns = equity.pct_change().dropna()
    
    total_return = (equity.iloc[-1] - initial_capital) / initial_capital
    sharpe = returns.mean() / returns.std() * np.sqrt(252) if len(returns) > 0 else 0
    max_dd = ((equity.cummax() - equity) / equity.cummax()).max()
    win_trades = [t for t in trades if t['pnl'] > 0]
    win_rate = len(win_trades) / len(trades) if trades else 0
    
    results = {
        'arm': 'B (GARCH Dynamic)',
        'total_return': total_return,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_dd,
        'win_rate': win_rate,
        'n_trades': len(trades),
        'final_capital': equity.iloc[-1],
        'equity_curve': equity_curve,
        'trades': trades
    }
    
    print(f"\nTotal Return: {total_return:.2%}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")
    print(f"Win Rate: {win_rate:.1%}")
    print(f"N Trades: {len(trades)}")
    print(f"Final Capital: ${equity.iloc[-1]:,.2f}")
    
    return results


def compare_results(arm_a: dict, arm_b: dict) -> None:
    """Print comparison summary."""
    print("\n" + "=" * 60)
    print("📊 A/B COMPARISON SUMMARY")
    print("=" * 60)
    
    print(f"\n{'Metric':<20} | {'Arm A (Static)':<15} | {'Arm B (GARCH)':<15} | {'Delta':<10}")
    print("-" * 70)
    
    metrics = ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate', 'n_trades']
    
    for metric in metrics:
        val_a = arm_a[metric]
        val_b = arm_b[metric]
        delta = val_b - val_a
        
        if metric == 'max_drawdown':
            # For DD, improvement is negative (lower is better)
            delta_str = f"{delta:+.2%}" if delta < 0 else f"{delta:+.2%}"
        elif metric == 'n_trades':
            delta_str = f"{int(delta):+d}"
        else:
            delta_str = f"{delta:+.2%}" if isinstance(val_a, float) and val_a < 2 else f"{delta:+.2f}"
        
        # Format display values properly
        if metric == 'n_trades':
            print(f"{metric:<20} | {int(val_a):>15} | {int(val_b):>15} | {delta_str:<10}")
        else:
            print(f"{metric:<20} | {val_a:>14.2%} | {val_b:>14.2%} | {delta_str:<10}")
    
    print("\n" + "=" * 60)
    
    # Verdict
    if arm_b['sharpe_ratio'] > arm_a['sharpe_ratio']:
        print("✅ VERDICT: GARCH Dynamic improves risk-adjusted returns!")
    else:
        print("⚠️ VERDICT: GARCH Dynamic needs tuning (lower Sharpe)")
    
    if arm_b['max_drawdown'] < arm_a['max_drawdown']:
        print("✅ Drawdown reduction achieved!")
    else:
        print("⚠️ Drawdown not improved")


def main():
    """Run A/B backtest comparison."""
    print("🐉 GARCH Position Sizing A/B Backtest")
    print("=" * 60)
    print(f"Started: {datetime.now().isoformat()}")
    
    # Load data
    df = load_btc_data()
    print(f"\nLoaded {len(df)} days of BTC data")
    print(f"Date range: {df.index[0].date()} to {df.index[-1].date()}")
    print(f"Price range: ${df['close'].min():,.2f} to ${df['close'].max():,.2f}")
    
    # Run Arm A (Static)
    results_a = run_backtest_arm_a(df)
    
    # Run Arm B (GARCH Dynamic)
    results_b = run_backtest_arm_b(df)
    
    # Compare
    compare_results(results_a, results_b)
    
    print(f"\nCompleted: {datetime.now().isoformat()}")
    print("\n✅ A/B Backtest Complete!")


if __name__ == "__main__":
    main()
