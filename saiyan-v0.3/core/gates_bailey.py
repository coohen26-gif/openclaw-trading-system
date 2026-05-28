"""
Gates Bailey - 5 Gates de Robustesse pour Saiyan v0.3
Implémentation basée sur "Advances in Financial Machine Learning" (López de Prado)
et les papers de Bailey et al. (2017)

5 Gates :
1. CPCV - Combinatorial Purged Cross-Validation
2. DSR - Deflated Sharpe Ratio
3. PSR - Probability of Sharpe Ratio
4. PBO - Probability of Backtest Overfitting
5. Wilson Score - Confidence intervals pour Win Rate
"""

import numpy as np
from scipy import stats
from scipy.special import comb, binom
from typing import Tuple, Dict, Optional, List
import warnings


class GatesBailey:
    """
    Implémentation des 5 gates de robustesse Bailey/López de Prado
    """
    
    def __init__(self, risk_free_rate: float = 0.0, annual_trading_days: int = 252):
        self.risk_free_rate = risk_free_rate
        self.annual_trading_days = annual_trading_days
    
    # =========================================================================
    # GATE 1: CPCV - Combinatorial Purged Cross-Validation
    # =========================================================================
    
    def cpurged_kfold(self, X: np.ndarray, y: np.ndarray, n_splits: int = 5, 
                      embargo: float = 0.05) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Combinatorial Purged Cross-Validation avec embargo
        
        Args:
            X: Features (n_samples, n_features)
            y: Labels (n_samples,)
            n_splits: Nombre de splits
            embargo: Fraction d'échantillons à exclure autour du split (évite lookahead bias)
        
        Returns:
            Liste de tuples (train_idx, test_idx)
        
        Reference: López de Prado Ch.7
        """
        n_samples = len(X)
        indices = np.arange(n_samples)
        
        # Taille des folds
        fold_size = n_samples // n_splits
        
        splits = []
        for i in range(n_splits):
            # Test set
            test_start = i * fold_size
            test_end = (i + 1) * fold_size if i < n_splits - 1 else n_samples
            test_idx = indices[test_start:test_end]
            
            # Embargo: exclure les échantillons autour du test set
            embargo_size = int(fold_size * embargo)
            
            # Train set: tout sauf test + embargo
            train_mask = np.ones(n_samples, dtype=bool)
            train_start = max(0, test_start - embargo_size)
            train_end = min(n_samples, test_end + embargo_size)
            train_mask[train_start:train_end] = False
            
            train_idx = indices[train_mask]
            splits.append((train_idx, test_idx))
        
        return splits
    
    def combinatorial_paths(self, n_splits: int, n_test_sets: int = 1) -> int:
        """
        Calcule le nombre de chemins combinatoires possibles
        
        Args:
            n_splits: Nombre total de splits
            n_test_sets: Nombre de test sets par chemin
        
        Returns:
            Nombre de chemins combinatoires
        """
        return int(comb(n_splits, n_test_sets))
    
    def cpurged_score(self, scores: np.ndarray, split_indices: List[Tuple[np.ndarray, np.ndarray]]) -> Dict:
        """
        Calcule le score CPCV à partir des scores sur chaque split
        
        Args:
            scores: Array des scores pour chaque split
            split_indices: Indices des splits
        
        Returns:
            Dict avec mean, std, et nombre de chemins
        """
        n_splits = len(split_indices)
        
        # Score moyen sur tous les splits
        mean_score = np.mean(scores)
        std_score = np.std(scores, ddof=1)
        
        # Nombre de chemins combinatoires
        n_paths = self.combinatorial_paths(n_splits)
        
        # Intervalle de confiance
        ci_lower = mean_score - 1.96 * std_score / np.sqrt(n_splits)
        ci_upper = mean_score + 1.96 * std_score / np.sqrt(n_splits)
        
        return {
            'mean': mean_score,
            'std': std_score,
            'n_splits': n_splits,
            'n_paths': n_paths,
            'ci_95': (ci_lower, ci_upper),
            'passed': mean_score > 0  # Gate passe si score moyen > 0
        }
    
    # =========================================================================
    # GATE 2: DSR - Deflated Sharpe Ratio
    # =========================================================================
    
    def deflated_sharpe_ratio(self, returns: np.ndarray, sharpe_estimates: Optional[np.ndarray] = None,
                              n_trials: int = 1, frequency: int = 252) -> Dict:
        """
        Deflated Sharpe Ratio - ajuste le Sharpe Ratio pour le multiple testing bias
        
        Args:
            returns: Série de returns
            sharpe_estimates: Sharpe ratios des N stratégies testées (si None, utilise returns)
            n_trials: Nombre de stratégies testées (multiple testing)
            frequency: Fréquence annualisation (252 pour daily)
        
        Returns:
            Dict avec DSR, p-value, et décision gate
        
        Reference: Bailey & López de Prado (2014) "The Deflated Sharpe Ratio"
        """
        n = len(returns)
        
        # Sharpe Ratio observé
        sr_observed = self.sharpe_ratio(returns, frequency=frequency)
        
        # Si on a plusieurs stratégies, ajuster pour multiple testing
        if n_trials > 1 and sharpe_estimates is not None:
            # Estimation du biais de multiple testing
            # E[max(SR)] ≈ μ + σ * Φ^(-1)((N-0.375)/(N+0.25))
            sr_mean = np.mean(sharpe_estimates)
            sr_std = np.std(sharpe_estimates, ddof=1)
            
            # Approximation de l'espérance du max
            from scipy.stats import norm
            expected_max = sr_mean + sr_std * norm.ppf((n_trials - 0.375) / (n_trials + 0.25))
            
            # DSR = SR observé - E[max(SR)]
            dsr = sr_observed - expected_max
        else:
            # Version simple sans adjustment multiple testing
            dsr = sr_observed
        
        # P-value sous H0: DSR = 0
        # SE(DSR) ≈ sqrt((1 + 0.5*SR^2) / n)
        se_dsr = np.sqrt((1 + 0.5 * sr_observed**2) / n)
        z_stat = dsr / se_dsr if se_dsr > 0 else 0
        p_value = 1 - stats.norm.cdf(z_stat)
        
        # Gate passe si DSR > 0 et p-value < 0.05
        passed = (dsr > 0) and (p_value < 0.05)
        
        return {
            'dsr': dsr,
            'sr_observed': sr_observed,
            'p_value': p_value,
            'z_statistic': z_stat,
            'n_trials': n_trials,
            'passed': passed
        }
    
    # =========================================================================
    # GATE 3: PSR - Probability of Sharpe Ratio
    # =========================================================================
    
    def probability_sharpe_ratio(self, returns: np.ndarray, sr_benchmark: float = 0.0,
                                 skewness: Optional[float] = None, kurtosis: Optional[float] = None,
                                 frequency: int = 252) -> Dict:
        """
        Probability of Sharpe Ratio - probabilité que le vrai SR > benchmark
        
        Args:
            returns: Série de returns
            sr_benchmark: Sharpe Ratio de référence (ex: 0, ou SR d'un benchmark)
            skewness: Skewness des returns (si None, calculée)
            kurtosis: Kurtosis des returns (si None, calculée)
            frequency: Fréquence annualisation
        
        Returns:
            Dict avec PSR et décision gate
        
        Reference: Bailey & López de Prado (2012)
        """
        n = len(returns)
        
        # Moments statistiques
        if skewness is None:
            skewness = stats.skew(returns)
        if kurtosis is None:
            kurtosis = stats.kurtosis(returns)  # Excess kurtosis
        
        # Sharpe Ratio observé
        sr_observed = self.sharpe_ratio(returns, frequency=frequency)
        
        # Variance ajustée pour skewness et kurtosis
        # Var(SR) ≈ (1 + 0.5*SR^2 - κ*SR*γ + (κ-1)*SR^2/4) / n
        # où γ = skewness, κ = kurtosis
        var_sr = (1 + 0.5 * sr_observed**2 - kurtosis * sr_observed * skewness 
                  + (kurtosis - 1) * sr_observed**2 / 4) / n
        
        se_sr = np.sqrt(var_sr)
        
        # Z-score: (SR_obs - SR_benchmark) / SE
        z_stat = (sr_observed - sr_benchmark) / se_sr if se_sr > 0 else 0
        
        # PSR = Prob(SR_vrai > SR_benchmark) = Φ(Z)
        psr = stats.norm.cdf(z_stat)
        
        # Gate passe si PSR > 0.95 (95% confiance que SR > benchmark)
        passed = psr > 0.95
        
        return {
            'psr': psr,
            'sr_observed': sr_observed,
            'sr_benchmark': sr_benchmark,
            'z_statistic': z_stat,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'se_sharpe': se_sr,
            'passed': passed
        }
    
    # =========================================================================
    # GATE 4: PBO - Probability of Backtest Overfitting
    # =========================================================================
    
    def probability_backtest_overfitting(self, returns_matrix: np.ndarray, 
                                        sr_star: Optional[float] = None) -> Dict:
        """
        Probability of Backtest Overfitting - probabilité que la meilleure stratégie
        soit due au hasard
        
        Args:
            returns_matrix: Matrix (N stratégies × T périodes) des returns
            sr_star: Sharpe Ratio de la meilleure stratégie (si None, calculée)
        
        Returns:
            Dict avec PBO et décision gate
        
        Reference: Bailey et al. (2017) "The Probability of Backtest Overfitting"
        """
        n_strategies, n_periods = returns_matrix.shape
        
        # Calculer Sharpe Ratios pour toutes les stratégies
        sharpes = np.array([self.sharpe_ratio(returns_matrix[i]) for i in range(n_strategies)])
        
        # Meilleur Sharpe Ratio observé
        if sr_star is None:
            sr_star = np.max(sharpes)
        
        # Rang de la meilleure stratégie
        rank_star = np.sum(sharpes >= sr_star)
        
        # PBO ≈ (N - rank_star) / N
        # Version simplifiée: proportion de stratégies aussi bonnes ou meilleures
        pbo_estimate = (n_strategies - rank_star + 1) / n_strategies
        
        # Version plus sophistiquée avec distribution théorique
        # Sous H0 (toutes stratégies équivalentes), E[max(SR)] suit une distribution
        if n_strategies > 1:
            # Approximation Fisher-Tippett pour le max
            mu_n = np.mean(sharpes)
            sigma_n = np.std(sharpes, ddof=1)
            
            # Paramètres de la distribution Gumbel
            from scipy.stats import gumbel_r
            if sigma_n > 0:
                # Fit Gumbel aux Sharpe Ratios
                gumbel_params = gumbel_r.fit(sharpes)
                # PBO = Prob(max(SR) >= sr_star | H0)
                pbo_gumbel = 1 - gumbel_r.cdf(sr_star, *gumbel_params)
            else:
                pbo_gumbel = 0.5
        else:
            pbo_gumbel = 1.0  # Une seule stratégie = overfitting certain
        
        # Gate passe si PBO < 0.10 (moins de 10% chance d'overfitting)
        passed = pbo_estimate < 0.10
        
        return {
            'pbo_estimate': pbo_estimate,
            'pbo_gumbel': pbo_gumbel,
            'sr_star': sr_star,
            'n_strategies': n_strategies,
            'n_periods': n_periods,
            'rank_star': rank_star,
            'sharpes_mean': np.mean(sharpes),
            'sharpes_std': np.std(sharpes),
            'passed': passed
        }
    
    # =========================================================================
    # GATE 5: Wilson Score - Confidence Interval pour Win Rate
    # =========================================================================
    
    def wilson_score_interval(self, n_wins: int, n_total: int, 
                             confidence: float = 0.95) -> Dict:
        """
        Wilson Score Interval pour estimer la vraie Win Rate avec confiance
        
        Args:
            n_wins: Nombre de trades gagnants
            n_total: Nombre total de trades
            confidence: Niveau de confiance (défaut 95%)
        
        Returns:
            Dict avec WR observée, intervalle de confiance, et décision gate
        
        Reference: Wilson (1927), utilisé en A/B testing et trading
        """
        if n_total == 0:
            return {
                'wr_observed': 0.0,
                'wr_lower': 0.0,
                'wr_upper': 0.0,
                'ci_width': 0.0,
                'n_trades': 0,
                'passed': False,
                'reason': 'No trades'
            }
        
        # Win Rate observée
        wr_observed = n_wins / n_total
        
        # Z-score pour le niveau de confiance
        z = stats.norm.ppf((1 + confidence) / 2)
        
        # Wilson score interval
        denominator = 1 + z**2 / n_total
        centre_adj = (wr_observed + z**2 / (2 * n_total)) / denominator
        margin = z * np.sqrt((wr_observed * (1 - wr_observed) + z**2 / (4 * n_total)) / n_total) / denominator
        
        wr_lower = max(0, centre_adj - margin)
        wr_upper = min(1, centre_adj + margin)
        
        ci_width = wr_upper - wr_lower
        
        # Gate passe si borne inférieure > 0.50 (confiance que WR > 50%)
        # Pour objectif W (WR ≥70%), on peut utiliser threshold plus haut
        wr_threshold = 0.50  # Minimum absolu
        passed = wr_lower > wr_threshold
        
        return {
            'wr_observed': wr_observed,
            'wr_lower': wr_lower,
            'wr_upper': wr_upper,
            'ci_95': (wr_lower, wr_upper),
            'ci_width': ci_width,
            'n_wins': n_wins,
            'n_losses': n_total - n_wins,
            'n_trades': n_total,
            'confidence_level': confidence,
            'passed': passed,
            'wr_threshold': wr_threshold
        }
    
    def wilson_score_minimum_trades(self, wr_target: float = 0.70, 
                                   wr_observed: float = 0.70,
                                   confidence: float = 0.95) -> int:
        """
        Calcule le nombre minimum de trades nécessaires pour atteindre
        une certaine confiance que WR > target
        
        Args:
            wr_target: Win Rate cible
            wr_observed: Win Rate observée
            confidence: Niveau de confiance
        
        Returns:
            Nombre minimum de trades requis
        """
        z = stats.norm.ppf((1 + confidence) / 2)
        
        # Approximation: n ≈ (z^2 * p * (1-p)) / E^2
        # où E = marge d'erreur acceptable
        p = wr_observed
        E = wr_observed - wr_target  # Marge au-dessus du target
        
        if E <= 0:
            return np.inf  # Impossible d'atteindre le target
        
        n_min = (z**2 * p * (1 - p)) / (E**2)
        
        return int(np.ceil(n_min))
    
    # =========================================================================
    # UTILITAIRES
    # =========================================================================
    
    def sharpe_ratio(self, returns: np.ndarray, frequency: int = 252,
                    risk_free_rate: Optional[float] = None) -> float:
        """
        Calcule le Sharpe Ratio annualisé
        
        Args:
            returns: Série de returns
            frequency: Fréquence pour annualisation (252=daily, 12=monthly)
            risk_free_rate: Taux sans risque (annualisé)
        
        Returns:
            Sharpe Ratio annualisé
        """
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0
        
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        # Return moyen annualisé
        mean_return = np.mean(returns) * frequency
        
        # Volatilité annualisée
        vol_annualized = np.std(returns, ddof=1) * np.sqrt(frequency)
        
        # Sharpe Ratio
        sr = (mean_return - risk_free_rate) / vol_annualized
        
        return sr
    
    def run_all_gates(self, returns: np.ndarray, returns_matrix: Optional[np.ndarray] = None,
                     n_wins: Optional[int] = None, n_trades: Optional[int] = None,
                     sr_benchmark: float = 0.0, n_trials: int = 1) -> Dict:
        """
        Exécute les 5 gates et retourne un rapport complet
        
        Args:
            returns: Série de returns de la stratégie
            returns_matrix: Matrix des returns pour PBO (optionnel)
            n_wins: Nombre de wins pour Wilson (optionnel)
            n_trades: Nombre total de trades pour Wilson (optionnel)
            sr_benchmark: Benchmark pour PSR
            n_trials: Nombre de stratégies testées pour DSR
        
        Returns:
            Dict avec résultats de toutes les gates et décision globale
        """
        results = {}
        
        # Gate 1: CPCV (nécessite features/labels, skip si pas fournis)
        results['cpcv'] = {'status': 'skipped', 'reason': 'Requires features/labels'}
        
        # Gate 2: DSR
        results['dsr'] = self.deflated_sharpe_ratio(returns, n_trials=n_trials)
        
        # Gate 3: PSR
        results['psr'] = self.probability_sharpe_ratio(returns, sr_benchmark=sr_benchmark)
        
        # Gate 4: PBO (nécessite returns_matrix)
        if returns_matrix is not None:
            results['pbo'] = self.probability_backtest_overfitting(returns_matrix)
        else:
            results['pbo'] = {'status': 'skipped', 'reason': 'Requires returns_matrix'}
        
        # Gate 5: Wilson Score
        if n_wins is not None and n_trades is not None:
            results['wilson'] = self.wilson_score_interval(n_wins, n_trades)
        else:
            results['wilson'] = {'status': 'skipped', 'reason': 'Requires n_wins and n_trades'}
        
        # Décision globale: toutes les gates non-skippées doivent passer
        gates_passed = [k for k, v in results.items() 
                       if isinstance(v, dict) and v.get('passed') is True]
        gates_failed = [k for k, v in results.items() 
                       if isinstance(v, dict) and v.get('passed') is False]
        gates_skipped = [k for k, v in results.items() 
                        if isinstance(v, dict) and v.get('status') == 'skipped']
        
        overall_passed = len(gates_failed) == 0 and len(gates_passed) > 0
        
        return {
            'overall_passed': overall_passed,
            'gates_passed': gates_passed,
            'gates_failed': gates_failed,
            'gates_skipped': gates_skipped,
            'details': results
        }


# =============================================================================
# FONCTIONS STANDALONE (pour usage rapide)
# =============================================================================

def calculate_dsr(returns: np.ndarray, n_trials: int = 1) -> Dict:
    """Calcule DSR rapidement"""
    gates = GatesBailey()
    return gates.deflated_sharpe_ratio(returns, n_trials=n_trials)


def calculate_psr(returns: np.ndarray, sr_benchmark: float = 0.0) -> Dict:
    """Calcule PSR rapidement"""
    gates = GatesBailey()
    return gates.probability_sharpe_ratio(returns, sr_benchmark=sr_benchmark)


def calculate_wilson(n_wins: int, n_total: int, confidence: float = 0.95) -> Dict:
    """Calcule Wilson Score Interval rapidement"""
    gates = GatesBailey()
    return gates.wilson_score_interval(n_wins, n_total, confidence)
