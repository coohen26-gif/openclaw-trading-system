"""
Tests unitaires pour Gates Bailey - Saiyan v0.3
Couverture: CPCV, DSR, PSR, PBO, Wilson Score
"""

import pytest
import numpy as np
from scipy import stats
import sys
sys.path.insert(0, '/root/.openclaw/workspace/saiyan-v0.3')

from core.gates_bailey import GatesBailey, calculate_dsr, calculate_psr, calculate_wilson


class TestGatesBaileyInit:
    """Tests d'initialisation"""
    
    def test_init_default(self):
        gates = GatesBailey()
        assert gates.risk_free_rate == 0.0
        assert gates.annual_trading_days == 252
    
    def test_init_custom(self):
        gates = GatesBailey(risk_free_rate=0.02, annual_trading_days=365)
        assert gates.risk_free_rate == 0.02
        assert gates.annual_trading_days == 365


class TestSharpeRatio:
    """Tests Sharpe Ratio"""
    
    def test_sharpe_positive_returns(self):
        gates = GatesBailey()
        returns = np.array([0.01, 0.02, 0.015, 0.018, 0.012])
        sr = gates.sharpe_ratio(returns, frequency=252)
        assert sr > 0
    
    def test_sharpe_negative_returns(self):
        gates = GatesBailey()
        returns = np.array([-0.01, -0.02, -0.015, -0.018, -0.012])
        sr = gates.sharpe_ratio(returns, frequency=252)
        assert sr < 0
    
    def test_sharpe_zero_volatility(self):
        gates = GatesBailey()
        returns = np.array([0.01, 0.01, 0.01, 0.01, 0.01])
        sr = gates.sharpe_ratio(returns, frequency=252)
        assert sr == 0.0 or np.isinf(sr)
    
    def test_sharpe_empty_returns(self):
        gates = GatesBailey()
        returns = np.array([])
        sr = gates.sharpe_ratio(returns, frequency=252)
        assert sr == 0.0


class TestCPCV:
    """Tests Combinatorial Purged Cross-Validation"""
    
    def test_cpurged_kfold_splits(self):
        gates = GatesBailey()
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, 100)
        
        splits = gates.cpurged_kfold(X, y, n_splits=5, embargo=0.05)
        
        assert len(splits) == 5
        
        # Vérifier que train et test sont disjoints
        for train_idx, test_idx in splits:
            intersection = set(train_idx).intersection(set(test_idx))
            assert len(intersection) == 0
    
    def test_cpurged_embargo_size(self):
        gates = GatesBailey()
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, 100)
        
        splits_no_embargo = gates.cpurged_kfold(X, y, n_splits=5, embargo=0.0)
        splits_with_embargo = gates.cpurged_kfold(X, y, n_splits=5, embargo=0.1)
        
        # Avec embargo, les train sets devraient être plus petits
        for (train_no, _), (train_emb, _) in zip(splits_no_embargo, splits_with_embargo):
            assert len(train_emb) <= len(train_no)
    
    def test_combinatorial_paths(self):
        gates = GatesBailey()
        
        # C(5, 1) = 5
        assert gates.combinatorial_paths(5, 1) == 5
        
        # C(10, 2) = 45
        assert gates.combinatorial_paths(10, 2) == 45
    
    def test_cpurged_score(self):
        gates = GatesBailey()
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, 100)
        
        splits = gates.cpurged_kfold(X, y, n_splits=5)
        scores = np.array([0.1, 0.15, 0.12, 0.08, 0.11])
        
        result = gates.cpurged_score(scores, splits)
        
        assert 'mean' in result
        assert 'std' in result
        assert 'ci_95' in result
        assert result['mean'] == pytest.approx(np.mean(scores))
        assert result['passed'] == (result['mean'] > 0)


class TestDSR:
    """Tests Deflated Sharpe Ratio"""
    
    def test_dsr_single_strategy(self):
        gates = GatesBailey()
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 252)  # 1 an de daily returns
        
        result = gates.deflated_sharpe_ratio(returns, n_trials=1)
        
        assert 'dsr' in result
        assert 'sr_observed' in result
        assert 'p_value' in result
        assert 'passed' in result
    
    def test_dsr_multiple_trials(self):
        gates = GatesBailey()
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 252)
        sharpe_estimates = np.random.normal(0.5, 0.3, 10)  # 10 stratégies testées
        
        result = gates.deflated_sharpe_ratio(
            returns, 
            sharpe_estimates=sharpe_estimates, 
            n_trials=10
        )
        
        # DSR devrait être plus bas avec multiple testing adjustment
        assert result['dsr'] <= result['sr_observed']
    
    def test_dsr_passed_threshold(self):
        gates = GatesBailey()
        np.random.seed(42)
        # Génère des returns positifs avec bon Sharpe
        returns = np.random.normal(0.002, 0.015, 500)
        
        result = gates.deflated_sharpe_ratio(returns, n_trials=1)
        
        # Devrait passer avec de bons returns
        assert result['sr_observed'] > 0


class TestPSR:
    """Tests Probability of Sharpe Ratio"""
    
    def test_psr_basic(self):
        gates = GatesBailey()
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 252)
        
        result = gates.probability_sharpe_ratio(returns, sr_benchmark=0.0)
        
        assert 'psr' in result
        assert 'sr_observed' in result
        assert 'z_statistic' in result
        assert 0 <= result['psr'] <= 1
    
    def test_psr_with_skewness_kurtosis(self):
        gates = GatesBailey()
        np.random.seed(42)
        # Returns avec skewness négative (typique trading)
        from scipy.stats import chi2
        returns = np.random.normal(0.001, 0.02, 252) - 0.005 * chi2.rvs(3, size=252)
        
        result = gates.probability_sharpe_ratio(returns, sr_benchmark=0.0)
        
        assert result['skewness'] < 0  # Skewness négative
        assert result['kurtosis'] > 0  # Excess kurtosis positive
    
    def test_psr_high_confidence(self):
        gates = GatesBailey()
        np.random.seed(42)
        # Très bons returns
        returns = np.random.normal(0.003, 0.01, 500)
        
        result = gates.probability_sharpe_ratio(returns, sr_benchmark=0.5)
        
        # Devrait avoir haute PSR contre benchmark modéré
        assert result['psr'] > 0.5


class TestPBO:
    """Tests Probability of Backtest Overfitting"""
    
    def test_pbo_single_strategy(self):
        gates = GatesBailey()
        np.random.seed(42)
        returns_matrix = np.random.normal(0.001, 0.02, (1, 252))
        
        result = gates.probability_backtest_overfitting(returns_matrix)
        
        assert 'pbo_estimate' in result
        assert 'sr_star' in result
        assert result['n_strategies'] == 1
    
    def test_pbo_multiple_strategies(self):
        gates = GatesBailey()
        np.random.seed(42)
        # 10 stratégies, 252 périodes
        returns_matrix = np.random.normal(0.001, 0.02, (10, 252))
        
        result = gates.probability_backtest_overfitting(returns_matrix)
        
        assert result['n_strategies'] == 10
        assert 'pbo_estimate' in result
        assert 'pbo_gumbel' in result
    
    def test_pbo_best_strategy(self):
        gates = GatesBailey()
        np.random.seed(42)
        # Crée une stratégie clairement meilleure
        returns_matrix = np.random.normal(0.001, 0.02, (5, 252))
        returns_matrix[0] = np.random.normal(0.005, 0.015, 252)  # Meilleure stratégie
        
        result = gates.probability_backtest_overfitting(returns_matrix)
        
        # La meilleure stratégie devrait avoir rank 1
        assert result['rank_star'] == 1


class TestWilsonScore:
    """Tests Wilson Score Interval"""
    
    def test_wilson_basic(self):
        gates = GatesBailey()
        
        result = gates.wilson_score_interval(n_wins=70, n_total=100)
        
        assert result['wr_observed'] == 0.70
        assert 'wr_lower' in result
        assert 'wr_upper' in result
        assert result['wr_lower'] < result['wr_observed']
        assert result['wr_upper'] > result['wr_observed']
    
    def test_wilson_zero_trades(self):
        gates = GatesBailey()
        
        result = gates.wilson_score_interval(n_wins=0, n_total=0)
        
        assert result['wr_observed'] == 0.0
        assert result['passed'] == False
        assert result['reason'] == 'No trades'
    
    def test_wilson_passed(self):
        gates = GatesBailey()
        
        # 70 wins sur 100 trades
        result = gates.wilson_score_interval(n_wins=70, n_total=100)
        
        # Borne inférieure devrait être > 0.50
        assert result['wr_lower'] > 0.50
        assert result['passed'] == True
    
    def test_wilson_failed(self):
        gates = GatesBailey()
        
        # 45 wins sur 100 trades (WR < 50%)
        result = gates.wilson_score_interval(n_wins=45, n_total=100)
        
        # Borne inférieure devrait être < 0.50
        assert result['wr_lower'] < 0.50
        assert result['passed'] == False
    
    def test_wilson_minimum_trades(self):
        gates = GatesBailey()
        
        n_min = gates.wilson_score_minimum_trades(
            wr_target=0.60,
            wr_observed=0.70,
            confidence=0.95
        )
        
        assert n_min > 0
        assert isinstance(n_min, int)


class TestStandaloneFunctions:
    """Tests fonctions standalone"""
    
    def test_calculate_dsr(self):
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 252)
        
        result = calculate_dsr(returns, n_trials=1)
        
        assert 'dsr' in result
        assert 'sr_observed' in result
    
    def test_calculate_psr(self):
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 252)
        
        result = calculate_psr(returns, sr_benchmark=0.0)
        
        assert 'psr' in result
    
    def test_calculate_wilson(self):
        result = calculate_wilson(n_wins=70, n_total=100)
        
        assert result['wr_observed'] == 0.70
        assert 'wr_lower' in result


class TestRunAllGates:
    """Tests fonction run_all_gates"""
    
    def test_run_all_gates_complete(self):
        gates = GatesBailey()
        np.random.seed(42)
        
        returns = np.random.normal(0.001, 0.02, 252)
        returns_matrix = np.random.normal(0.001, 0.02, (5, 252))
        
        result = gates.run_all_gates(
            returns=returns,
            returns_matrix=returns_matrix,
            n_wins=70,
            n_trades=100
        )
        
        assert 'overall_passed' in result
        assert 'gates_passed' in result
        assert 'gates_failed' in result
        assert 'details' in result
    
    def test_run_all_gates_partial(self):
        gates = GatesBailey()
        np.random.seed(42)
        
        returns = np.random.normal(0.001, 0.02, 252)
        
        # Sans returns_matrix ni n_wins/n_trades
        result = gates.run_all_gates(returns=returns)
        
        # Certaines gates devraient être skippées
        assert result['gates_skipped'] is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=core/gates_bailey', '--cov-report=term-missing'])
