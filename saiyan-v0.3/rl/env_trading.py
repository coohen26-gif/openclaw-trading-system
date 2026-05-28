"""
Gymnasium-compatible Trading Environment for Deep RL
Supports PPO, SAC, A2C with Stable-Baselines3

Référence: Semaine 35 - Deep RL Research
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional, List
from datetime import datetime
import json


class TradingEnv(gym.Env):
    """
    Environment de trading pour Deep RL (PPO/SAC/A2C).
    
    Action Space:
    - Discret: 0=SELL, 1=HOLD, 2=BUY
    - Ou Continu: [-1.0, 1.0] pour position sizing
    
    Observation Space:
    - Prix normalisés (log returns, 5j window)
    - Volatilité rolling (30j GARCH)
    - Régime HMM (probabilités 4 états)
    - Momentum indicators (RSI, MACD)
    - État portfolio (balance, position, PnL unrealized)
    
    Reward Function:
    - PnL net fees
    - Drawdown penalty
    - Volatility penalty (Sharpe-like)
    - Regime bonus (action appropriée au régime)
    - Trading penalty (excessive trading)
    """
    
    metadata = {'render_modes': ['human', 'rgb_array']}
    
    def __init__(
        self,
        data: pd.DataFrame,
        initial_balance: float = 10000.0,
        transaction_cost: float = 0.001,  # 10 bps
        action_type: str = 'discrete',  # 'discrete' or 'continuous'
        lookback_window: int = 60,
        fee_per_trade: float = 0.0005,
        reward_scaling: float = 100.0,
        max_steps: Optional[int] = None,
        regime_probs: Optional[np.ndarray] = None,  # (n_steps, 4) HMM probabilities
        seed: Optional[int] = None
    ):
        super().__init__()
        
        self.data = data.copy()
        self.initial_balance = initial_balance
        self.transaction_cost = transaction_cost
        self.action_type = action_type
        self.lookback_window = lookback_window
        self.fee_per_trade = fee_per_trade
        self.reward_scaling = reward_scaling
        self.max_steps = max_steps or len(data) - lookback_window
        self.regime_probs = regime_probs
        
        if seed is not None:
            self.seed(seed)
        
        # Validate data
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_cols):
            raise ValueError(f"Data must have columns: {required_cols}")
        
        # Calculate additional features
        self._preprocess_data()
        
        # Action space
        if action_type == 'discrete':
            self.action_space = spaces.Discrete(3)  # SELL, HOLD, BUY
        else:  # continuous
            self.action_space = spaces.Box(
                low=-1.0, high=1.0, shape=(1,), dtype=np.float32
            )  # -1=full short, 0=flat, +1=full long
        
        # Observation space
        # Features: returns(lookback) + vol(lookback) + rsi(lookback) + regime(4) + portfolio(3)
        n_features = lookback_window * 3 + 4 + 3  # price features + regime + portfolio
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf,
            shape=(n_features,), dtype=np.float32
        )
        
        print(f"[TradingEnv] Observation space: {n_features} features (lookback={lookback_window})")
        
        # State variables
        self.current_step = 0
        self.balance = initial_balance
        self.position = 0.0  # Number of shares
        self.position_value = 0.0
        self.total_fees = 0.0
        self.trades_count = 0
        self.peak_balance = initial_balance
        self.max_drawdown = 0.0
        self.daily_returns: List[float] = []
        
        # For rendering
        self.render_mode = None
        
    def _preprocess_data(self):
        """Calculer features techniques"""
        df = self.data
        
        # Log returns
        df['returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Rolling volatility (30j)
        df['volatility'] = df['returns'].rolling(30).std() * np.sqrt(252)
        
        # RSI (14j)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-9)
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        
        # Normalize returns for stability
        df['returns_norm'] = (df['returns'] - df['returns'].mean()) / (df['returns'].std() + 1e-9)
        
        # Fill NaN with 0
        df = df.fillna(0)
        
        self.data = df
        
    def _get_observation(self) -> np.ndarray:
        """Construire observation vector"""
        # Price features (lookback window)
        start_idx = max(0, self.current_step - self.lookback_window)
        end_idx = self.current_step + 1
        
        returns_window = self.data['returns_norm'].iloc[start_idx:end_idx].values
        vol_window = self.data['volatility'].iloc[start_idx:end_idx].values
        rsi_window = self.data['rsi'].iloc[start_idx:end_idx].values / 100.0  # Normalize to [0,1]
        
        # Pad if necessary to ensure exact lookback_window size
        if len(returns_window) < self.lookback_window:
            pad_len = self.lookback_window - len(returns_window)
            returns_window = np.pad(returns_window, (pad_len, 0), mode='constant')
            vol_window = np.pad(vol_window, (pad_len, 0), mode='constant')
            rsi_window = np.pad(rsi_window, (pad_len, 0), mode='constant')
        
        # Ensure exact size (truncate if somehow larger)
        returns_window = returns_window[:self.lookback_window]
        vol_window = vol_window[:self.lookback_window]
        rsi_window = rsi_window[:self.lookback_window]
        
        # Regime probabilities (if available)
        if self.regime_probs is not None:
            if self.current_step < len(self.regime_probs):
                regime_probs = self.regime_probs[self.current_step].copy().flatten()
            else:
                # Use last available if step exceeds probs length
                regime_probs = self.regime_probs[-1].copy().flatten()
        else:
            regime_probs = np.array([0.25, 0.25, 0.25, 0.25], dtype=np.float32)  # Uniform prior
        
        # Ensure regime_probs is exactly 4 elements
        if len(regime_probs) != 4:
            regime_probs = np.ones(4, dtype=np.float32) / 4
        else:
            regime_probs = regime_probs[:4]  # Truncate to 4 if larger
        
        # Portfolio state
        current_price = self.data['close'].iloc[self.current_step]
        position_value = self.position * current_price
        unrealized_pnl = position_value - self.position_value if self.position != 0 else 0
        portfolio_state = np.array([
            self.balance / self.initial_balance,  # Normalized balance
            self.position / (self.initial_balance / current_price),  # Normalized position
            unrealized_pnl / self.initial_balance  # Normalized unrealized PnL
        ], dtype=np.float32)
        
        # Concatenate all features
        observation = np.concatenate([
            returns_window.astype(np.float32),
            vol_window.astype(np.float32),
            rsi_window.astype(np.float32),
            regime_probs.astype(np.float32),
            portfolio_state
        ])
        
        # Debug: verify size
        expected_size = self.lookback_window * 3 + 4 + 3
        if len(observation) != expected_size:
            print(f"[DEBUG] Obs size mismatch: got {len(observation)}, expected {expected_size}")
            print(f"  returns: {len(returns_window)}, vol: {len(vol_window)}, rsi: {len(rsi_window)}")
            print(f"  regime: {len(regime_probs)}, portfolio: {len(portfolio_state)}")
        
        return observation.astype(np.float32)
    
    def _calculate_reward(
        self,
        pnl: float,
        fees: float,
        drawdown: float,
        volatility: float,
        regime_probs: np.ndarray,
        action: int
    ) -> float:
        """
        Reward shaping risk-adjusted.
        
        Reward = PnL_net - drawdown_penalty - vol_penalty + regime_bonus - trading_penalty
        """
        # Base: PnL net fees (normalized by capital)
        base_reward = (pnl - fees) / self.initial_balance
        
        # Penalty: Drawdown aversion (risk management)
        drawdown_penalty = 0.5 * max(0, drawdown)  # Penalize large DD
        
        # Penalty: Volatility (Sharpe-like component)
        vol_penalty = 0.1 * volatility / (abs(base_reward) + 1e-6)
        
        # Bonus: Regime-aware (reward appropriate actions)
        regime_bonus = 0.0
        # Find dominant regime
        dominant_regime = np.argmax(regime_probs)
        
        if dominant_regime == 0:  # BULL
            if action == 2 or self.position > 0:  # BUY or LONG
                regime_bonus = 0.05
        elif dominant_regime == 1:  # BEAR
            if action == 1 or self.position == 0:  # HOLD or FLAT
                regime_bonus = 0.05
        elif dominant_regime == 2:  # RANGE
            if abs(self.position) < 0.02 * (self.initial_balance / self.data['close'].iloc[self.current_step]):
                regime_bonus = 0.03  # Reward small positions
        elif dominant_regime == 3:  # VOLATILE
            if abs(self.position) < 0.01 * (self.initial_balance / self.data['close'].iloc[self.current_step]):
                regime_bonus = 0.05  # Reward very small positions
        
        # Penalty: Excessive trading (transaction costs)
        trading_penalty = -0.001 * (1 if action != 1 else 0)  # Penalty for non-HOLD
        
        total_reward = (
            base_reward
            - drawdown_penalty
            - vol_penalty
            + regime_bonus
            + trading_penalty
        )
        
        # Clip to avoid extreme rewards
        total_reward = np.clip(total_reward, -1.0, 1.0)
        
        return total_reward * self.reward_scaling
    
    def step(self, action) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Exécuter une étape de trading.
        
        Args:
            action: 
                - Discret: 0=SELL, 1=HOLD, 2=BUY
                - Continu: [-1.0, 1.0] position sizing
        
        Returns:
            observation, reward, terminated, truncated, info
        """
        self.current_step += 1
        
        # Terminated if we reached end of data
        terminated = self.current_step >= len(self.data) - 1
        
        # Truncated if max_steps reached
        truncated = self.max_steps is not None and (self.current_step - self.lookback_window) >= self.max_steps
        
        if terminated or truncated:
            # Final liquidation
            current_price = self.data['close'].iloc[self.current_step]
            self.balance += self.position * current_price * (1 - self.transaction_cost)
            self.position = 0.0
            self.position_value = 0.0
        
        # Get current metrics before action
        prev_balance = self.balance
        prev_position_value = self.position_value
        current_price = self.data['close'].iloc[self.current_step]
        
        # Execute action
        fees = 0.0
        pnl = 0.0
        
        if self.action_type == 'discrete':
            if action == 0:  # SELL
                if self.position > 0:
                    sell_value = self.position * current_price
                    fees = sell_value * self.fee_per_trade
                    self.balance += sell_value * (1 - self.transaction_cost) - fees
                    pnl = sell_value - self.position_value
                    self.position = 0.0
                    self.position_value = 0.0
                    self.trades_count += 1
                    
            elif action == 2:  # BUY
                buy_amount = self.balance * 0.95  # Use 95% of balance
                shares = buy_amount / current_price
                fees = buy_amount * self.fee_per_trade
                self.balance -= buy_amount + fees
                self.position += shares
                self.position_value += buy_amount
                self.trades_count += 1
                
            # action == 1: HOLD - do nothing
            
        else:  # continuous
            # action in [-1.0, 1.0]
            target_position = action * (self.balance / current_price)
            
            if target_position > self.position:  # BUY
                diff = target_position - self.position
                buy_value = diff * current_price
                fees = buy_value * self.fee_per_trade
                self.balance -= buy_value + fees
                self.position = target_position
                self.position_value += buy_value
                self.trades_count += 1
                
            elif target_position < self.position:  # SELL
                diff = self.position - target_position
                sell_value = diff * current_price
                fees = sell_value * self.fee_per_trade
                self.balance += sell_value * (1 - self.transaction_cost) - fees
                pnl = sell_value - (diff * current_price)  # Simplified
                self.position = target_position
                self.position_value -= diff * current_price
                self.trades_count += 1
        
        # Update peak balance and drawdown
        total_value = self.balance + self.position * current_price
        self.peak_balance = max(self.peak_balance, total_value)
        self.max_drawdown = min(0, (total_value - self.peak_balance) / self.peak_balance)
        
        # Calculate daily return
        if len(self.daily_returns) > 0:
            daily_return = (total_value - self.daily_returns[-1]) / self.daily_returns[-1]
        else:
            daily_return = 0.0
        self.daily_returns.append(total_value)
        
        # Get current volatility
        current_vol = self.data['volatility'].iloc[self.current_step]
        
        # Get regime probabilities
        if self.regime_probs is not None and self.current_step < len(self.regime_probs):
            regime_probs = self.regime_probs[self.current_step]
        else:
            regime_probs = np.array([0.25, 0.25, 0.25, 0.25])
        
        # Calculate reward
        reward = self._calculate_reward(
            pnl=pnl,
            fees=fees,
            drawdown=abs(self.max_drawdown),
            volatility=current_vol,
            regime_probs=regime_probs,
            action=action if self.action_type == 'discrete' else (2 if action > 0.5 else (0 if action < -0.5 else 1))
        )
        
        # Build info dict
        info = {
            'balance': self.balance,
            'position': self.position,
            'total_value': total_value,
            'pnl': pnl,
            'fees': fees,
            'total_fees': self.total_fees + fees,
            'trades_count': self.trades_count,
            'drawdown': self.max_drawdown,
            'daily_return': daily_return,
            'current_price': current_price,
            'sharpe': np.mean(self.daily_returns) / (np.std(self.daily_returns) + 1e-9) * np.sqrt(252) if len(self.daily_returns) > 10 else 0
        }
        
        self.total_fees += fees
        
        # Get next observation
        observation = self._get_observation()
        
        return observation, reward, terminated, truncated, info
    
    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict] = None
    ) -> Tuple[np.ndarray, Dict]:
        """Reset environment to initial state"""
        super().reset(seed=seed)
        
        self.current_step = self.lookback_window
        self.balance = self.initial_balance
        self.position = 0.0
        self.position_value = 0.0
        self.total_fees = 0.0
        self.trades_count = 0
        self.peak_balance = self.initial_balance
        self.max_drawdown = 0.0
        self.daily_returns = []
        
        observation = self._get_observation()
        info = {
            'balance': self.balance,
            'position': self.position,
            'total_value': self.initial_balance,
            'pnl': 0.0,
            'fees': 0.0,
            'trades_count': 0,
            'drawdown': 0.0,
            'current_price': self.data['close'].iloc[self.current_step]
        }
        
        return observation, info
    
    def render(self, mode='human'):
        """Render environment (for debugging)"""
        if mode == 'human':
            total_value = self.balance + self.position * self.data['close'].iloc[self.current_step]
            print(f"Step {self.current_step}: "
                  f"Balance=${self.balance:.2f}, "
                  f"Position={self.position:.4f}, "
                  f"Total=${total_value:.2f}, "
                  f"PnL={total_value - self.initial_balance:.2f} "
                  f"({(total_value - self.initial_balance) / self.initial_balance:.2%})")
    
    def seed(self, seed=None):
        """Set random seed"""
        self.np_random, seed = gym.utils.seeding.np_random(seed)
        return [seed]


def create_trading_env(
    data_path: str,
    initial_balance: float = 10000.0,
    action_type: str = 'discrete',
    seed: int = 42
) -> TradingEnv:
    """
    Factory function to create trading environment from CSV.
    
    Args:
        data_path: Path to CSV with OHLCV data
        initial_balance: Starting capital
        action_type: 'discrete' or 'continuous'
        seed: Random seed
        
    Returns:
        TradingEnv instance
    """
    df = pd.read_csv(data_path)
    
    # Ensure required columns
    required = ['date', 'open', 'high', 'low', 'close', 'volume']
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    return TradingEnv(
        data=df,
        initial_balance=initial_balance,
        action_type=action_type,
        seed=seed
    )


if __name__ == "__main__":
    # Test environment with synthetic data
    print("=== Test Trading Environment ===\n")
    
    # Generate synthetic data
    np.random.seed(42)
    n_days = 500
    
    dates = pd.date_range('2024-01-01', periods=n_days, freq='D')
    prices = 100 * np.cumprod(1 + np.random.normal(0.0005, 0.02, n_days))
    
    df = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.normal(0, 0.001, n_days)),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.01, n_days))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.01, n_days))),
        'close': prices,
        'volume': np.random.normal(1e6, 2e5, n_days)
    })
    
    # Create environment
    env = TradingEnv(
        data=df,
        initial_balance=10000.0,
        action_type='discrete',
        seed=42
    )
    
    print(f"Action space: {env.action_space}")
    print(f"Observation space: {env.observation_space}")
    print(f"Max steps: {env.max_steps}")
    print()
    
    # Reset and test
    obs, info = env.reset()
    print(f"Initial observation shape: {obs.shape}")
    print(f"Initial info: {info}")
    print()
    
    # Run random actions
    total_reward = 0.0
    for step in range(100):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        
        if step % 20 == 0:
            env.render()
            print(f"  Reward: {reward:.4f}, Total: {total_reward:.4f}")
        
        if terminated or truncated:
            break
    
    print()
    print(f"Final balance: ${info['balance']:.2f}")
    print(f"Total value: ${info['total_value']:.2f}")
    print(f"Total PnL: ${info['total_value'] - 10000:.2f} ({(info['total_value'] / 10000 - 1):.2%})")
    print(f"Total reward: {total_reward:.4f}")
    print(f"Trades: {info['trades_count']}")
    print(f"Sharpe: {info['sharpe']:.3f}")
    
    print("\n=== Test terminé ✅ ===")
