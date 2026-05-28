#!/usr/bin/env python3
"""
Script de validation des Gates Bailey pour Saiyan v0.3

Usage:
    python scripts/run_gates_validation.py --data data/btc_returns.npy --config config/gates_thresholds.json
"""

import argparse
import json
import numpy as np
import sys
from pathlib import Path

# Ajout du path pour import core
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.gates_bailey import GatesBailey


def load_returns(data_path: str) -> np.ndarray:
    """Charge les returns depuis un fichier numpy"""
    return np.load(data_path)


def load_config(config_path: str) -> dict:
    """Charge la configuration des seuils"""
    with open(config_path, 'r') as f:
        return json.load(f)


def generate_synthetic_returns(n_samples: int = 252, 
                               mean: float = 0.001, 
                               std: float = 0.02,
                               seed: int = 42) -> np.ndarray:
    """Génère des returns synthétiques pour test"""
    np.random.seed(seed)
    return np.random.normal(mean, std, n_samples)


def validate_strategy(returns: np.ndarray, config: dict) -> dict:
    """
    Valide une stratégie contre toutes les Gates Bailey
    
    Returns:
        Dict avec résultats détaillés
    """
    gates = GatesBailey()
    
    results = {
        'n_samples': len(returns),
        'mean_return': float(np.mean(returns)),
        'std_return': float(np.std(returns)),
        'sharpe_ratio': float(gates.sharpe_ratio(returns)),
        'gates': {}
    }
    
    # Gate 1: DSR
    dsr_result = gates.deflated_sharpe_ratio(
        returns, 
        n_trials=config['dsr']['default_n_trials']
    )
    results['gates']['dsr'] = {
        'value': float(dsr_result['dsr']),
        'sr_observed': float(dsr_result['sr_observed']),
        'p_value': float(dsr_result['p_value']),
        'threshold': f"DSR>{config['dsr']['min_dsr']}, p<{config['dsr']['max_pvalue']}",
        'passed': dsr_result['passed']
    }
    
    # Gate 2: PSR
    psr_result = gates.probability_sharpe_ratio(
        returns, 
        sr_benchmark=config['psr']['default_sr_benchmark']
    )
    results['gates']['psr'] = {
        'value': float(psr_result['psr']),
        'sr_observed': float(psr_result['sr_observed']),
        'z_statistic': float(psr_result['z_statistic']),
        'threshold': f"PSR>{config['psr']['min_psr']}",
        'passed': psr_result['passed']
    }
    
    # Gate 3: Wilson Score (si on a info trades)
    # Pour démo, on simule n_wins basé sur returns positives
    n_trades = len(returns)
    n_wins = int(np.sum(returns > 0))
    
    wilson_result = gates.wilson_score_interval(
        n_wins=n_wins, 
        n_total=n_trades,
        confidence=config['wilson']['confidence_level']
    )
    results['gates']['wilson'] = {
        'wr_observed': float(wilson_result['wr_observed']),
        'wr_lower': float(wilson_result['wr_lower']),
        'wr_upper': float(wilson_result['wr_upper']),
        'n_trades': n_trades,
        'threshold': f"WR_lower>{config['wilson']['min_wr_lower']}",
        'passed': wilson_result['passed']
    }
    
    # Décision globale
    gates_passed = sum(1 for g in results['gates'].values() if g['passed'])
    gates_total = len(results['gates'])
    
    results['summary'] = {
        'gates_passed': gates_passed,
        'gates_total': gates_total,
        'pass_rate': gates_passed / gates_total if gates_total > 0 else 0,
        'overall_passed': all(g['passed'] for g in results['gates'].values())
    }
    
    return results


def print_results(results: dict):
    """Affiche les résultats de validation"""
    print("\n" + "="*60)
    print("🔍 RÉSULTATS VALIDATION GATES BAILEY")
    print("="*60)
    
    print(f"\n📊 STATISTIQUES DE BASE")
    print(f"   N samples:    {results['n_samples']}")
    print(f"   Mean return:  {results['mean_return']:.4f} ({results['mean_return']*100:.2f}%)")
    print(f"   Std return:   {results['std_return']:.4f} ({results['std_return']*100:.2f}%)")
    print(f"   Sharpe Ratio: {results['sharpe_ratio']:.3f}")
    
    print(f"\n🚪 RÉSULTATS GATES")
    for gate_name, gate_result in results['gates'].items():
        status = "✅ PASS" if gate_result['passed'] else "❌ FAIL"
        print(f"\n   {gate_name.upper()} {status}")
        if 'value' in gate_result:
            print(f"      Valeur:   {gate_result['value']:.4f}")
        if 'sr_observed' in gate_result:
            print(f"      SR obs:   {gate_result['sr_observed']:.3f}")
        if 'p_value' in gate_result:
            print(f"      P-value:  {gate_result['p_value']:.4f}")
        if 'wr_observed' in gate_result:
            print(f"      WR obs:   {gate_result['wr_observed']:.1%}")
            print(f"      WR CI95:  [{gate_result['wr_lower']:.1%}, {gate_result['wr_upper']:.1%}]")
        print(f"      Seuil:    {gate_result['threshold']}")
    
    print(f"\n📋 RÉSUMÉ")
    summary = results['summary']
    print(f"   Gates passées: {summary['gates_passed']}/{summary['gates_total']}")
    print(f"   Pass rate:     {summary['pass_rate']:.1%}")
    
    if summary['overall_passed']:
        print(f"\n🎉 STRATÉGIE VALIDÉE - Prête pour paper-deploy")
    else:
        failed_gates = [k for k, v in results['gates'].items() if not v['passed']]
        print(f"\n⚠️  STRATÉGIE REJETÉE")
        print(f"   Gates échouées: {', '.join(failed_gates)}")
    
    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Validation Gates Bailey Saiyan v0.3')
    parser.add_argument('--data', type=str, help='Chemin vers fichier numpy des returns')
    parser.add_argument('--config', type=str, default='config/gates_thresholds.json',
                       help='Chemin vers fichier config')
    parser.add_argument('--synthetic', action='store_true', 
                       help='Utiliser des données synthétiques pour démo')
    parser.add_argument('--output', type=str, help='Fichier JSON de sortie (optionnel)')
    
    args = parser.parse_args()
    
    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)
    
    config = load_config(str(config_path))
    
    # Load or generate returns
    if args.synthetic or not args.data:
        print("📊 Génération données synthétiques pour démo...")
        returns = generate_synthetic_returns(n_samples=252, mean=0.0015, std=0.02)
    else:
        data_path = Path(args.data)
        if not data_path.exists():
            print(f"❌ Data file not found: {data_path}")
            sys.exit(1)
        print(f"📊 Chargement données: {data_path}")
        returns = load_returns(str(data_path))
    
    # Validate
    results = validate_strategy(returns, config)
    
    # Print
    print_results(results)
    
    # Save if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"💾 Résultats sauvegardés: {output_path}")
    
    # Exit code
    sys.exit(0 if results['summary']['overall_passed'] else 1)


if __name__ == '__main__':
    main()
