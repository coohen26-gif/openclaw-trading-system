"""
Vrai HMM Regime Detector avec Baum-Welch Algorithm
Implémentation rolling 180j pour adaptation continue

Référence: Semaine 35 - Deep RL Research
"""

import numpy as np
import pandas as pd
from hmmlearn import hmm
from sklearn.preprocessing import StandardScaler
from enum import Enum
from typing import Tuple, Dict, Optional, List
import json
from datetime import datetime


class Regime(Enum):
    BULL = "BULL"
    BEAR = "BEAR"
    RANGE = "RANGE"
    VOLATILE_TRANSITION = "VOLATILE_TRANSITION"


class TrueHMMRegimeDetector:
    """
    Hidden Markov Model avec Baum-Welch algorithm.
    Rolling window 180 jours pour adaptation continue.
    
    Features:
    - Returns (log returns daily)
    - Volatility (rolling 30j std ou GARCH)
    
    Sorties:
    - Régime actuel (BULL/BEAR/RANGE/VOLATILE)
    - Probabilités par état
    - Matrice de transition
    - Persistance moyenne par régime
    """
    
    def __init__(
        self,
        n_regimes: int = 4,
        rolling_window: int = 180,
        random_state: int = 42,
        covariance_type: str = 'diag'
    ):
        self.n_regimes = n_regimes
        self.rolling_window = rolling_window
        self.random_state = random_state
        self.covariance_type = covariance_type
        
        self.model: Optional[hmm.GaussianHMM] = None
        self.scaler: Optional[StandardScaler] = None
        self.regime_map: Dict[int, Regime] = {}
        
        # Buffer pour données rolling
        self.data_buffer: List[Dict] = []
        
    def prepare_features(
        self,
        returns: np.ndarray,
        volatility: np.ndarray
    ) -> Tuple[np.ndarray, StandardScaler]:
        """
        Préparer et standardiser features pour HMM.
        
        Args:
            returns: Log returns daily
            volatility: Rolling volatility (30j std ou GARCH)
            
        Returns:
            X_scaled: Features standardisées
            scaler: StandardScaler fitted
        """
        X = np.column_stack([returns, volatility])
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        return X_scaled, scaler
    
    def fit_rolling(
        self,
        returns: np.ndarray,
        volatility: np.ndarray
    ) -> 'TrueHMMRegimeDetector':
        """
        Fit HMM sur fenêtre rolling 180 jours avec Baum-Welch.
        
        Baum-Welch algorithm:
        1. Initialize parameters (π, A, μ, Σ)
        2. E-step: Calculate posterior probabilities
        3. M-step: Update parameters to maximize likelihood
        4. Repeat until convergence
        
        Args:
            returns: Array de log returns
            volatility: Array de volatilités
        """
        if len(returns) != len(volatility):
            raise ValueError("returns et volatility doivent avoir même longueur")
        
        if len(returns) < self.rolling_window:
            raise ValueError(
                f"Need at least {self.rolling_window} observations, "
                f"got {len(returns)}"
            )
        
        # Prendre dernières 180 observations
        returns_window = returns[-self.rolling_window:]
        volatility_window = volatility[-self.rolling_window:]
        
        # Préparer features
        X_scaled, self.scaler = self.prepare_features(
            returns_window,
            volatility_window
        )
        
        # GaussianHMM avec covariance diagonale (plus stable)
        self.model = hmm.GaussianHMM(
            n_components=self.n_regimes,
            covariance_type=self.covariance_type,
            n_iter=100,
            tol=1e-4,
            random_state=self.random_state,
            init_params='stmc',
            params='stmc'
        )
        
        # Fit avec Baum-Welch
        self.model.fit(X_scaled)
        
        # Calibration automatique des labels
        self.regime_map = self._calibrate_regime_labels()
        
        return self
    
    def _calibrate_regime_labels(self) -> Dict[int, Regime]:
        """
        Mapper les états HMM vers labels interprétables.
        
        Heuristique:
        - BULL: Haut returns, basse volatilité
        - BEAR: Bas/négatifs returns, haute volatilité
        - RANGE: Returns neutres, vol moyenne
        - VOLATILE_TRANSITION: Vol extrême
        """
        if self.model is None:
            raise ValueError("Must fit model first")
        
        means = self.model.means_  # Shape: (n_regimes, 2)
        
        # Score pour chaque état
        scores = {}
        for i in range(self.n_regimes):
            ret_mean = means[i, 0]
            vol_mean = means[i, 1]
            
            scores[i] = {
                'bull': ret_mean - vol_mean,
                'bear': -ret_mean + vol_mean,
                'volatile': vol_mean,
                'ret': ret_mean,
                'vol': vol_mean
            }
        
        # Assigner labels
        regime_map = {}
        assigned = set()
        
        # 1. Plus haut bull_score → BULL
        bull_state = max(scores.keys(), key=lambda k: scores[k]['bull'])
        regime_map[bull_state] = Regime.BULL
        assigned.add(bull_state)
        
        # 2. Plus haut bear_score → BEAR
        bear_state = max(
            [k for k in scores.keys() if k not in assigned],
            key=lambda k: scores[k]['bear']
        )
        regime_map[bear_state] = Regime.BEAR
        assigned.add(bear_state)
        
        # 3. Plus haute vol → VOLATILE_TRANSITION
        if len(assigned) < self.n_regimes:
            volatile_state = max(
                [k for k in scores.keys() if k not in assigned],
                key=lambda k: scores[k]['volatile']
            )
            regime_map[volatile_state] = Regime.VOLATILE_TRANSITION
            assigned.add(volatile_state)
        
        # 4. État restant → RANGE
        remaining = set(range(self.n_regimes)) - assigned
        if remaining:
            regime_map[list(remaining)[0]] = Regime.RANGE
        
        return regime_map
    
    def predict_regime(
        self,
        current_return: float,
        current_volatility: float
    ) -> Tuple[Regime, float, np.ndarray]:
        """
        Prédire régime actuel.
        
        Args:
            current_return: Log return quotidien
            current_volatility: Volatilité actuelle
            
        Returns:
            regime_label: Label du régime (BULL/BEAR/RANGE/VOLATILE)
            confidence: Confiance (max probabilité)
            probabilities: Probabilités pour tous les régimes
        """
        if self.model is None:
            raise ValueError("Must fit model first with fit_rolling()")
        
        # Prepare observation
        X_obs = np.array([[current_return, current_volatility]])
        X_scaled = self.scaler.transform(X_obs)
        
        # Predict state
        state = self.model.predict(X_scaled)[0]
        
        # Get posterior probabilities
        log_prob = self.model.score_samples(X_scaled)[0]
        probabilities = np.exp(log_prob)
        
        # Confidence = max probability
        confidence = float(probabilities.max())
        
        # Map to label
        regime_label = self.regime_map.get(state, Regime.RANGE)
        
        return regime_label, confidence, probabilities
    
    def get_transition_matrix(self) -> Optional[np.ndarray]:
        """
        Retourne matrice de transition A (n_regimes x n_regimes).
        
        A[i,j] = Probabilité de transition état i → état j
        """
        if self.model is None:
            return None
        return self.model.transmat_
    
    def get_regime_persistence(self) -> Optional[Dict[str, float]]:
        """
        Calculer persistance moyenne de chaque régime.
        
        Persistence = 1 / (1 - A[i,i])
        Durée moyenne dans régime i avant transition.
        """
        if self.model is None:
            return None
        
        transmat = self.model.transmat_
        persistence = {}
        
        for state, label in self.regime_map.items():
            prob_stay = transmat[state, state]
            avg_duration = 1 / (1 - prob_stay + 1e-9)
            persistence[label.value] = round(avg_duration, 2)
        
        return persistence
    
    def add_daily_observation(
        self,
        date: datetime,
        close_price: float,
        volume: float = None
    ) -> Optional[Dict]:
        """
        Ajouter observation quotidienne et mettre à jour HMM.
        
        Args:
            date: Date d'observation
            close_price: Prix de clôture
            volume: Volume (optionnel)
            
        Returns:
            Dict avec régime prédit si buffer plein, None sinon
        """
        # Calculer return daily
        if len(self.data_buffer) > 0:
            prev_close = self.data_buffer[-1]['close']
            daily_return = np.log(close_price / prev_close)
        else:
            daily_return = 0.0
        
        # Calculer volatilité rolling 30j
        closes = [d['close'] for d in self.data_buffer[-30:]] + [close_price]
        if len(closes) > 1:
            returns_30j = [np.log(closes[i]/closes[i-1]) for i in range(1, len(closes))]
            volatility = float(np.std(returns_30j) * np.sqrt(252))
        else:
            volatility = 0.1
        
        # Ajouter au buffer
        self.data_buffer.append({
            'date': date,
            'close': close_price,
            'return': daily_return,
            'volatility': volatility
        })
        
        # Garder buffer à 180 jours max
        if len(self.data_buffer) > self.rolling_window:
            self.data_buffer.pop(0)
        
        # Re-fit HMM si buffer plein
        if len(self.data_buffer) >= self.rolling_window:
            returns = np.array([d['return'] for d in self.data_buffer])
            volatility = np.array([d['volatility'] for d in self.data_buffer])
            
            self.fit_rolling(returns, volatility)
            
            # Prédire régime actuel
            current_regime, confidence, probs = self.predict_regime(
                daily_return, volatility
            )
            
            return {
                'date': date.isoformat(),
                'regime': current_regime.value,
                'confidence': confidence,
                'probabilities': probs.tolist(),
                'persistence': self.get_regime_persistence(),
                'transition_matrix': self.get_transition_matrix().tolist() if self.get_transition_matrix() is not None else None
            }
        
        return None
    
    def save_state(self, filepath: str):
        """Sauvegarder état HMM dans fichier JSON"""
        if self.model is None:
            raise ValueError("No model to save")
        
        # Extract diagonal for 'diag' covariance type
        covars = self.model.covars_
        if self.covariance_type == 'diag' and covars.ndim == 3:
            # Extract diagonal elements only - shape should be (n_components, n_features)
            covars = np.array([np.diag(c) for c in covars])
        
        state = {
            'n_regimes': self.n_regimes,
            'rolling_window': self.rolling_window,
            'covariance_type': self.covariance_type,
            'regime_map': {str(k): v.value for k, v in self.regime_map.items()},
            'model_params': {
                'means': self.model.means_.tolist(),
                'covars': covars.tolist(),
                'transmat': self.model.transmat_.tolist(),
                'startprob': self.model.startprob_.tolist()
            },
            'scaler_params': {
                'mean': self.scaler.mean_.tolist(),
                'scale': self.scaler.scale_.tolist()
            } if self.scaler else None,
            'data_buffer': self.data_buffer[-10:]  # Last 10 for context
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def load_state(self, filepath: str) -> 'TrueHMMRegimeDetector':
        """Charger état HMM depuis fichier JSON"""
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        self.n_regimes = state['n_regimes']
        self.rolling_window = state['rolling_window']
        self.covariance_type = state.get('covariance_type', 'diag')
        self.regime_map = {int(k): Regime(v) for k, v in state['regime_map'].items()}
        
        # Reconstituer modèle
        self.model = hmm.GaussianHMM(
            n_components=self.n_regimes,
            covariance_type=self.covariance_type,
            random_state=self.random_state
        )
        self.model.means_ = np.array(state['model_params']['means'])
        
        # Fix covars shape for 'diag' covariance type
        covars = np.array(state['model_params']['covars'])
        # covars should be (n_components, n_features) for 'diag'
        if self.covariance_type == 'diag' and covars.ndim == 2:
            pass  # Already correct shape
        elif covars.ndim == 1:
            covars = covars.reshape(1, -1)
        self.model.covars_ = covars
        
        self.model.transmat_ = np.array(state['model_params']['transmat'])
        self.model.startprob_ = np.array(state['model_params']['startprob'])
        
        # Reconstituer scaler
        if state['scaler_params']:
            self.scaler = StandardScaler()
            self.scaler.mean_ = np.array(state['scaler_params']['mean'])
            self.scaler.scale_ = np.array(state['scaler_params']['scale'])
        
        # Restaurer buffer
        self.data_buffer = state['data_buffer']
        
        return self


def validate_hmm_predictive_power(
    historical_data: pd.DataFrame,
    hmm_detector: TrueHMMRegimeDetector,
    forward_window: int = 20
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Valider que les régimes HMM ont pouvoir prédictif.
    
    Test: Si régime=BULL aujourd'hui, returns J+1 à J+20 sont-ils supérieurs?
    
    Args:
        historical_data: DataFrame avec columns ['return', 'volatility']
        hmm_detector: HMM detector instance
        forward_window: Fenêtre de forward return (jours)
        
    Returns:
        df_results: Résultats par jour
        analysis: Analyse agrégée par régime
    """
    results = []
    
    for day in range(hmm_detector.rolling_window, len(historical_data) - forward_window):
        # Fit HMM sur 180j glissants
        window = historical_data.iloc[day-hmm_detector.rolling_window:day]
        hmm_detector.fit_rolling(
            window['return'].values,
            window['volatility'].values
        )
        
        # Prédire régime jour J
        current_return = historical_data.iloc[day]['return']
        current_vol = historical_data.iloc[day]['volatility']
        
        regime, confidence, _ = hmm_detector.predict_regime(
            current_return, current_vol
        )
        
        # Calculer forward returns (J+1 à J+20)
        future_returns = historical_data.iloc[day+1:day+forward_window+1]['return']
        forward_return = float(future_returns.sum())
        forward_sharpe = float(
            future_returns.mean() / (future_returns.std() + 1e-9)
        )
        
        results.append({
            'date': historical_data.index[day],
            'regime': regime.value,
            'confidence': confidence,
            'forward_return': forward_return,
            'forward_sharpe': forward_sharpe
        })
    
    df_results = pd.DataFrame(results)
    
    # Analyser par régime
    analysis = df_results.groupby('regime').agg({
        'forward_return': ['mean', 'std', 'count'],
        'forward_sharpe': 'mean',
        'confidence': 'mean'
    }).round(4)
    
    return df_results, analysis


if __name__ == "__main__":
    # Test avec données synthétiques
    print("=== Test True HMM Regime Detector ===\n")
    
    np.random.seed(42)
    n_days = 200
    
    # Générer données synthétiques avec 4 régimes
    regimes = ['BULL'] * 50 + ['RANGE'] * 50 + ['BEAR'] * 50 + ['VOLATILE'] * 50
    
    returns = []
    volatility = []
    
    for regime in regimes:
        if regime == 'BULL':
            ret = np.random.normal(0.002, 0.015)
            vol = abs(np.random.normal(0.015, 0.005))
        elif regime == 'BEAR':
            ret = np.random.normal(-0.002, 0.03)
            vol = abs(np.random.normal(0.03, 0.01))
        elif regime == 'RANGE':
            ret = np.random.normal(0.0, 0.015)
            vol = abs(np.random.normal(0.015, 0.005))
        else:  # VOLATILE
            ret = np.random.normal(0.0, 0.05)
            vol = abs(np.random.normal(0.05, 0.015))
        
        returns.append(ret)
        volatility.append(vol)
    
    returns = np.array(returns)
    volatility = np.array(volatility)
    
    # Initialiser HMM
    hmm_detector = TrueHMMRegimeDetector(
        n_regimes=4,
        rolling_window=180,
        random_state=42
    )
    
    # Fit
    print("Fit HMM avec Baum-Welch...")
    hmm_detector.fit_rolling(returns, volatility)
    
    # Afficher paramètres
    print(f"\nMatrice de transition:")
    print(hmm_detector.get_transition_matrix())
    
    print(f"\nPersistance par régime:")
    persistence = hmm_detector.get_regime_persistence()
    for regime, duration in persistence.items():
        print(f"  {regime}: {duration:.1f} jours")
    
    # Prédire dernier jour
    last_return = returns[-1]
    last_vol = volatility[-1]
    
    regime, confidence, probs = hmm_detector.predict_regime(last_return, last_vol)
    
    print(f"\nDernier jour:")
    print(f"  Régime: {regime.value}")
    print(f"  Confiance: {confidence:.1%}")
    print(f"  Probabilités: {probs}")
    
    # Sauvegarder état
    hmm_detector.save_state('/tmp/hmm_state.json')
    print("\nÉtat sauvegardé dans /tmp/hmm_state.json")
    
    # Tester chargement
    hmm_detector2 = TrueHMMRegimeDetector()
    hmm_detector2.load_state('/tmp/hmm_state.json')
    print("État chargé avec succès ✅")
    
    print("\n=== Test terminé ===")
