"""
PPO Training Script for Saiyan Trading System
Master 5: Deep RL - Regime-Aware Trading Agent

Training Configuration:
- Algorithm: PPO (Proximal Policy Optimization)
- Environment: TradingEnv (gymnasium-compatible)
- Features: HMM regimes, volatility, momentum, portfolio state
- Reward: PnL - drawdown penalty - vol penalty + regime bonus
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime
import json
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import (
    BaseCallback, 
    EvalCallback, 
    CheckpointCallback,
    CallbackList
)
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.monitor import Monitor
import warnings
warnings.filterwarnings('ignore')

from rl.env_trading import TradingEnv
from core.hmm_regime_detector import TrueHMMRegimeDetector as HMMRegimeDetector


class TradingCallback(BaseCallback):
    """Custom callback for logging trading metrics during training."""
    
    def __init__(self, verbose=1):
        super().__init__(verbose)
        self.episode_rewards = []
        self.episode_lengths = []
        self.episode_trades = []
        
    def _on_step(self) -> bool:
        return True
    
    def _on_rollout_end(self) -> None:
        """Called at the end of each rollout."""
        if len(self.episode_rewards) > 0:
            mean_reward = np.mean(self.episode_rewards[-10:])
            std_reward = np.std(self.episode_rewards[-10:])
            
            if self.verbose > 0:
                print(f"\n📊 Rollout Complete:")
                print(f"   Mean Reward (last 10): {mean_reward:.4f} ± {std_reward:.4f}")
                print(f"   Total Episodes: {len(self.episode_rewards)}")
        
        return True
    
    def _on_episode_end(self) -> None:
        """Called at the end of each episode."""
        episode_info = self.locals.get('infos', [{}])[0]
        if 'episode' in episode_info:
            self.episode_rewards.append(episode_info['episode']['r'])
            self.episode_lengths.append(episode_info['episode']['l'])


def load_training_data(
    symbol: str = 'BTC',
    start_date: str = '2020-01-01',
    end_date: str = '2026-05-28',
    timeframe: str = '1d'
) -> pd.DataFrame:
    """Load and preprocess training data."""
    print(f"📥 Loading {symbol} data ({start_date} to {end_date})...")
    
    # Use full historical data from learning/data (has OHLCV columns)
    data_file = f'../learning/data/{symbol.lower()}_usdt_daily.csv'
    
    import os
    if os.path.exists(data_file):
        df = pd.read_csv(data_file, parse_dates=['timestamp'], index_col='timestamp')
    else:
        # Fallback to btc_1d.csv
        data_file = f'../learning/data/{symbol.lower()}_1d.csv'
        if os.path.exists(data_file):
            df = pd.read_csv(data_file, parse_dates=['timestamp'], index_col='timestamp')
        else:
            raise FileNotFoundError(f"Data file not found: {data_file}")
    
    # Ensure required columns
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in required_cols:
        if col not in df.columns:
            # Try alternative names
            alt_names = [f'{col}_price', f'{col}Price', f'{col}_usdt']
            for alt in alt_names:
                if alt in df.columns:
                    df = df.rename(columns={alt: col})
                    break
    
    # Filter by date range
    df = df[(df.index >= start_date) & (df.index <= end_date)]
    
    print(f"   Loaded {len(df)} candles ({df.index[0]} to {df.index[-1]})")
    return df


def compute_regime_probs(data: pd.DataFrame, rolling_window: int = 180) -> np.ndarray:
    """Compute HMM regime probabilities with true Baum-Welch algorithm."""
    print(f"🔮 Computing HMM regime probabilities (TRUE HMM)...")
    
    n_samples = len(data)
    
    # Calculate returns and volatility
    returns = np.log(data['close'] / data['close'].shift(1)).values
    volatility = pd.Series(returns).rolling(30).std().values * np.sqrt(252)
    
    # Remove NaN from initial calculations
    valid_mask = ~np.isnan(returns) & ~np.isnan(volatility)
    returns_clean = returns[valid_mask]
    vol_clean = volatility[valid_mask]
    
    if len(returns_clean) < rolling_window + 10:
        print(f"   ⚠️ Insufficient data for HMM ({len(returns_clean)} samples), using uniform")
        return np.ones((n_samples, 4)) / 4
    
    # Initialize HMM detector
    from core.hmm_regime_detector import TrueHMMRegimeDetector
    hmm = TrueHMMRegimeDetector(n_regimes=4, rolling_window=rolling_window)
    
    # Fit on available data
    try:
        hmm.fit_rolling(returns_clean, vol_clean)
        print(f"   ✅ HMM fitted with Baum-Welch algorithm")
    except Exception as e:
        print(f"   ⚠️ HMM fit failed: {e}, using uniform")
        return np.ones((n_samples, 4)) / 4
    
    # Generate regime probabilities for each timestep
    regime_probs = np.ones((n_samples, 4)) / 4  # Default uniform
    
    # Use rolling prediction
    min_idx = int(np.where(valid_mask)[0][0])
    for i in range(min_idx + rolling_window, n_samples):
        try:
            # Get last rolling_window observations
            start_idx = i - rolling_window
            end_idx = i
            
            ret_window = returns[start_idx:end_idx]
            vol_window = volatility[start_idx:end_idx]
            
            # Remove any NaN in window
            valid_window = ~np.isnan(ret_window) & ~np.isnan(vol_window)
            if valid_window.sum() < rolling_window // 2:
                continue
            
            ret_clean = ret_window[valid_window]
            vol_clean_w = vol_window[valid_window]
            
            # Predict regime
            X = np.column_stack([ret_clean, vol_clean_w])
            X_scaled = hmm.scaler.transform(X)
            probs = hmm.model.predict_proba(X_scaled)
            
            # Use last prediction for this timestep
            if len(probs) > 0:
                regime_probs[i] = probs[-1]
        except Exception as e:
            # Keep uniform on error
            pass
    
    # Log regime distribution
    avg_probs = regime_probs.mean(axis=0)
    print(f"   📊 Regime distribution: BULL={avg_probs[0]:.1%}, BEAR={avg_probs[1]:.1%}, "
          f"RANGE={avg_probs[2]:.1%}, VOLATILE={avg_probs[3]:.1%}")
    
    return regime_probs


def create_training_env(
    data: pd.DataFrame,
    regime_probs: np.ndarray,
    train_split: float = 0.8,
    initial_balance: float = 100000.0
) -> tuple:
    """Create training and evaluation environments."""
    
    # Split data
    train_end = int(len(data) * train_split)
    train_data = data.iloc[:train_end].copy()
    eval_data = data.iloc[train_end:].copy()
    
    train_regimes = regime_probs[:train_end]
    eval_regimes = regime_probs[train_end:]
    
    print(f"\n📊 Data Split:")
    print(f"   Training: {len(train_data)} samples ({train_data.index[0]} to {train_data.index[-1]})")
    print(f"   Evaluation: {len(eval_data)} samples ({eval_data.index[0]} to {eval_data.index[-1]})")
    
    # Create environments
    train_env = TradingEnv(
        data=train_data,
        initial_balance=initial_balance,
        action_type='discrete',
        regime_probs=train_regimes,
        seed=42
    )
    
    eval_env = TradingEnv(
        data=eval_data,
        initial_balance=initial_balance,
        action_type='discrete',
        regime_probs=eval_regimes,
        seed=42
    )
    
    # Wrap with Monitor
    train_env = Monitor(train_env)
    eval_env = Monitor(eval_env)
    
    # Vectorize
    train_vec_env = DummyVecEnv([lambda: train_env])
    eval_vec_env = DummyVecEnv([lambda: eval_env])
    
    # Normalize observations and rewards
    train_vec_env = VecNormalize(
        train_vec_env,
        norm_obs=True,
        norm_reward=True,
        clip_obs=10.0,
        clip_reward=10.0
    )
    
    # Also normalize eval env (required for EvalCallback)
    eval_vec_env = VecNormalize(
        eval_vec_env,
        norm_obs=True,
        norm_reward=True,
        clip_obs=10.0,
        clip_reward=10.0,
        training=False  # Don't update stats during eval
    )
    
    return train_vec_env, eval_vec_env, train_data, eval_data


def train_ppo_agent(
    train_env: VecNormalize,
    eval_env: VecNormalize,
    total_timesteps: int = 100000,
    learning_rate: float = 3e-4,
    n_steps: int = 2048,
    batch_size: int = 64,
    n_epochs: int = 10,
    gamma: float = 0.99,
    gae_lambda: float = 0.95,
    clip_range: float = 0.2,
    ent_coef: float = 0.01,
    vf_coef: float = 0.5,
    max_grad_norm: float = 0.5,
    model_path: str = 'saiyan-v0.3/rl/models/ppo_trading.zip'
) -> PPO:
    """Train PPO agent."""
    
    print(f"\n🚀 Starting PPO Training...")
    print(f"   Total timesteps: {total_timesteps:,}")
    print(f"   Learning rate: {learning_rate}")
    print(f"   Batch size: {batch_size}")
    print(f"   N steps: {n_steps}")
    print(f"   N epochs: {n_epochs}")
    
    # Create model (disable tensorboard for now)
    model = PPO(
        policy='MlpPolicy',
        env=train_env,
        learning_rate=learning_rate,
        n_steps=n_steps,
        batch_size=batch_size,
        n_epochs=n_epochs,
        gamma=gamma,
        gae_lambda=gae_lambda,
        clip_range=clip_range,
        ent_coef=ent_coef,
        vf_coef=vf_coef,
        max_grad_norm=max_grad_norm,
        verbose=1,
        tensorboard_log=None  # Disable tensorboard
    )
    
    # Create callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=10000,
        save_path='saiyan-v0.3/rl/checkpoints/',
        name_prefix='ppo_trading'
    )
    
    # Simplified eval callback without normalization sync issues
    eval_callback = EvalCallback(
        eval_env,  # Already VecNormalize-wrapped
        best_model_save_path='saiyan-v0.3/rl/models/',
        log_path='saiyan-v0.3/rl/logs/',
        eval_freq=5000,
        deterministic=True,
        render=False,
        n_eval_episodes=3,
        warn=False
    )
    
    trading_callback = TradingCallback(verbose=1)
    
    callback_list = CallbackList([
        checkpoint_callback,
        eval_callback,
        trading_callback
    ])
    
    # Train
    model.learn(
        total_timesteps=total_timesteps,
        callback=callback_list,
        tb_log_name='ppo_trading_v1'
    )
    
    # Save final model
    model.save(model_path)
    train_env.save('saiyan-v0.3/rl/models/vec_normalize.pkl')
    
    print(f"\n✅ Training complete! Model saved to {model_path}")
    
    return model


def evaluate_agent(
    model: PPO,
    eval_env: VecNormalize,
    eval_data: pd.DataFrame,
    n_episodes: int = 10
) -> dict:
    """Evaluate trained agent."""
    
    print(f"\n📊 Evaluating Agent...")
    
    episode_rewards = []
    episode_returns = []
    episode_drawdowns = []
    
    for i in range(n_episodes):
        obs = eval_env.reset()
        done = False
        episode_reward = 0
        trades = 0
        prev_position = 0
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = eval_env.step(action)
            episode_reward += reward
            
            # Count trades
            current_position = info[0].get('position', 0) if info else 0
            if current_position != prev_position:
                trades += 1
            prev_position = current_position
        
        episode_rewards.append(episode_reward)
        
        if info:
            episode_returns.append(info[0].get('total_return', 0))
            episode_drawdowns.append(info[0].get('max_drawdown', 0))
    
    results = {
        'mean_reward': float(np.mean(episode_rewards)),
        'std_reward': float(np.std(episode_rewards)),
        'mean_return': float(np.mean(episode_returns)),
        'std_return': float(np.std(episode_returns)),
        'mean_drawdown': float(np.mean(episode_drawdowns)),
        'mean_trades': float(np.mean([trades])),
        'n_episodes': n_episodes
    }
    
    print(f"\n📈 Evaluation Results ({n_episodes} episodes):")
    print(f"   Mean Reward: {results['mean_reward']:.4f} ± {results['std_reward']:.4f}")
    print(f"   Mean Return: {results['mean_return']:.2%} ± {results['std_return']:.2%}")
    print(f"   Mean Drawdown: {results['mean_drawdown']:.2%}")
    print(f"   Mean Trades: {results['mean_trades']:.1f}")
    
    return results


def main():
    """Main training pipeline."""
    
    print("=" * 60)
    print("🐉 SAIYAN V0.3 - PPO Training Pipeline")
    print("Master 5: Deep RL for Regime-Aware Trading")
    print("=" * 60)
    
    # Create directories
    os.makedirs('saiyan-v0.3/rl/models', exist_ok=True)
    os.makedirs('saiyan-v0.3/rl/checkpoints', exist_ok=True)
    os.makedirs('saiyan-v0.3/rl/logs', exist_ok=True)
    
    # Load data
    data = load_training_data(
        symbol='BTC',
        start_date='2020-01-01',
        end_date='2026-05-28',
        timeframe='1d'
    )
    
    # Compute regime probabilities
    regime_probs = compute_regime_probs(data, rolling_window=180)
    
    # Create environments
    train_env, eval_env, train_data, eval_data = create_training_env(
        data,
        regime_probs,
        train_split=0.8,
        initial_balance=100000.0
    )
    
    # Train agent
    model = train_ppo_agent(
        train_env,
        eval_env,
        total_timesteps=100000,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        model_path='saiyan-v0.3/rl/models/ppo_trading_final.zip'
    )
    
    # Evaluate agent
    results = evaluate_agent(
        model,
        eval_env,
        eval_data,
        n_episodes=10
    )
    
    # Save evaluation results
    with open('saiyan-v0.3/rl/evaluation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n✅ Training pipeline complete!")
    print(f"   Model: saiyan-v0.3/rl/models/ppo_trading_final.zip")
    print(f"   VecNorm: saiyan-v0.3/rl/models/vec_normalize.pkl")
    print(f"   Results: saiyan-v0.3/rl/evaluation_results.json")
    
    return model, results


if __name__ == '__main__':
    model, results = main()
