"""
Walk-Forward Validation - Semaine 12
Expanding/Rolling windows, Purged K-Fold, Leakage Audit
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import BaseCrossValidator
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

# ============================================================================
# 1. PURGED K-FOLD CROSS-VALIDATION
# ============================================================================

class PurgedKFold(BaseCrossValidator):
    """
    K-Fold avec purge et embargo pour time-series.
    Évite le data leakage temporel entre folds.
    """
    
    def __init__(self, n_splits=5, embargo=0.05):
        self.n_splits = n_splits
        self.embargo = embargo
    
    def split(self, X, y=None, groups=None):
        n_samples = len(X)
        fold_size = n_samples // self.n_splits
        embargo_size = int(fold_size * self.embargo)
        
        for i in range(self.n_splits):
            # Test set
            test_start = i * fold_size
            test_end = (i + 1) * fold_size if i < self.n_splits - 1 else n_samples
            
            # Train set (avec embargo)
            train_end = test_start - embargo_size if i > 0 else test_start
            train_start = 0
            
            train_idx = np.arange(train_start, train_end)
            test_idx = np.arange(test_start, test_end)
            
            yield train_idx, test_idx
    
    def get_n_splits(self, X=None, y=None, groups=None):
        return self.n_splits

# ============================================================================
# 2. GÉNÉRATION DE DONNÉES
# ============================================================================

def generate_trading_data(n_days=500, seed=42):
    """Génère des données de trading avec features et target"""
    np.random.seed(seed)
    
    n_obs = n_days * 24
    initial_price = 50000
    
    # Prix avec momentum et mean-reversion
    returns = np.random.randn(n_obs) * 0.002
    returns += 0.02 * np.roll(returns, 1)  # Momentum
    returns -= 0.01 * np.roll(returns, 5)  # Mean-reversion court terme
    returns[0] = 0
    
    prices = initial_price * np.cumprod(1 + returns)
    
    # Features
    dates = pd.date_range(start='2025-01-01', periods=n_obs, freq='h')
    df = pd.DataFrame({'close': prices}, index=dates)
    
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema_12 = df['close'].ewm(span=12).mean()
    ema_26 = df['close'].ewm(span=26).mean()
    df['macd'] = ema_12 - ema_26
    
    # Volatility
    df['volatility'] = df['close'].pct_change().rolling(20).std()
    
    # Returns laggués (features)
    for lag in [1, 5, 10]:
        df[f'return_lag{lag}'] = df['close'].pct_change(lag).shift(1)  # Shift pour éviter leakage
    
    # Target: Direction à 24h
    df['target'] = (df['close'].shift(-24) > df['close']).astype(int)
    
    df = df.dropna()
    
    return df

# ============================================================================
# 3. WALK-FORWARD ANALYSIS
# ============================================================================

def walk_forward_expanding(X, y, model_class, train_size=252, test_size=63, step=63):
    """
    Walk-forward avec fenêtre d'entraînement expansible.
    """
    
    n_samples = len(X)
    results = []
    
    train_end = train_size
    test_end = train_end + test_size
    
    fold = 1
    while test_end <= n_samples:
        X_train = X.iloc[:train_end]
        X_test = X.iloc[train_end:test_end]
        y_train = y.iloc[:train_end]
        y_test = y.iloc[train_end:test_end]
        
        # Scaling
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Training
        model = model_class()
        model.fit(X_train_scaled, y_train)
        
        # Prediction
        y_pred = model.predict(X_test_scaled)
        y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
        
        # Metrics
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        try:
            roc_auc = roc_auc_score(y_test, y_pred_proba)
        except:
            roc_auc = 0.5
        
        results.append({
            'fold': fold,
            'train_start': 0,
            'train_end': train_end,
            'test_start': train_end,
            'test_end': test_end,
            'accuracy': accuracy,
            'f1': f1,
            'roc_auc': roc_auc,
            'y_pred': y_pred,
            'y_true': y_test.values,
            'y_proba': y_pred_proba
        })
        
        # Prochain fold (expanding)
        train_end += step
        test_end += step
        fold += 1
    
    return results

def walk_forward_rolling(X, y, model_class, train_size=252, test_size=63, step=63):
    """
    Walk-forward avec fenêtre d'entraînement roulante (taille fixe).
    """
    
    n_samples = len(X)
    results = []
    
    train_start = 0
    train_end = train_size
    test_end = train_end + test_size
    
    fold = 1
    while test_end <= n_samples:
        X_train = X.iloc[train_start:train_end]
        X_test = X.iloc[train_end:test_end]
        y_train = y.iloc[train_start:train_end]
        y_test = y.iloc[train_end:test_end]
        
        # Scaling
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Training
        model = model_class()
        model.fit(X_train_scaled, y_train)
        
        # Prediction
        y_pred = model.predict(X_test_scaled)
        y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
        
        # Metrics
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        try:
            roc_auc = roc_auc_score(y_test, y_pred_proba)
        except:
            roc_auc = 0.5
        
        results.append({
            'fold': fold,
            'train_start': train_start,
            'train_end': train_end,
            'test_start': train_end,
            'test_end': test_end,
            'accuracy': accuracy,
            'f1': f1,
            'roc_auc': roc_auc,
            'y_pred': y_pred,
            'y_true': y_test.values,
            'y_proba': y_pred_proba
        })
        
        # Prochain fold (rolling)
        train_start += step
        train_end += step
        test_end += step
        fold += 1
    
    return results

# ============================================================================
# 4. LEAKAGE AUDIT
# ============================================================================

def audit_leakage(X, y, feature_names=None):
    """
    Audit basique pour détecter leakage potentiel.
    """
    
    if feature_names is None:
        feature_names = X.columns if hasattr(X, 'columns') else [f'Feature {i}' for i in range(X.shape[1])]
    
    print("=" * 60)
    print("AUDIT DE LEAKAGE")
    print("=" * 60)
    
    X_array = X.values if hasattr(X, 'values') else X
    
    # 1. Corrélation features-target
    print("\n[1] Corrélation Features-Target:")
    suspicious_count = 0
    for i, name in enumerate(feature_names):
        corr = np.corrcoef(X_array[:, i], y)[0, 1]
        if abs(corr) > 0.3:
            print(f"    ⚠️  {name}: {corr:.3f} (SUSPECT!)")
            suspicious_count += 1
        elif abs(corr) > 0.1:
            print(f"    ⚡ {name}: {corr:.3f}")
    
    if suspicious_count == 0:
        print("    ✅ Aucune corrélation suspecte détectée")
    
    # 2. Features à variance nulle
    print("\n[2] Features à variance nulle:")
    null_var_count = 0
    for i, name in enumerate(feature_names):
        if np.std(X_array[:, i]) == 0:
            print(f"    ❌ {name}: variance = 0")
            null_var_count += 1
    
    if null_var_count == 0:
        print("    ✅ Toutes les features ont une variance non-nulle")
    
    # 3. Features avec NaN
    print("\n[3] Features avec NaN:")
    nan_count = 0
    for i, name in enumerate(feature_names):
        nan_pct = np.isnan(X_array[:, i]).sum() / len(X) * 100
        if nan_pct > 0:
            print(f"    ⚠️  {name}: {nan_pct:.1f}% NaN")
            nan_count += 1
    
    if nan_count == 0:
        print("    ✅ Aucune valeur NaN")
    
    print("\n" + "=" * 60)
    
    return {
        'suspicious_correlations': suspicious_count,
        'null_variance_features': null_var_count,
        'features_with_nan': nan_count
    }

# ============================================================================
# 5. AGRÉGATION ET VISUALISATION
# ============================================================================

def aggregate_results(results):
    """Agrège les résultats de walk-forward"""
    
    all_y_true = []
    all_y_pred = []
    all_y_proba = []
    
    for fold_result in results:
        all_y_true.extend(fold_result['y_true'])
        all_y_pred.extend(fold_result['y_pred'])
        if 'y_proba' in fold_result:
            all_y_proba.extend(fold_result['y_proba'])
    
    # Métriques globales
    accuracy = accuracy_score(all_y_true, all_y_pred)
    f1 = f1_score(all_y_true, all_y_pred, zero_division=0)
    
    try:
        roc_auc = roc_auc_score(all_y_true, all_y_proba)
    except:
        roc_auc = 0.5
    
    # Métriques par fold
    fold_accuracies = [r['accuracy'] for r in results]
    fold_f1s = [r['f1'] for r in results]
    fold_roc_aucs = [r['roc_auc'] for r in results]
    
    return {
        'global_accuracy': accuracy,
        'global_f1': f1,
        'global_roc_auc': roc_auc,
        'mean_fold_accuracy': np.mean(fold_accuracies),
        'std_fold_accuracy': np.std(fold_accuracies),
        'min_fold_accuracy': np.min(fold_accuracies),
        'max_fold_accuracy': np.max(fold_accuracies),
        'mean_fold_f1': np.mean(fold_f1s),
        'mean_fold_roc_auc': np.mean(fold_roc_aucs),
        'n_folds': len(results),
        'fold_accuracies': fold_accuracies
    }

def plot_walk_forward_results(results, method_name="Walk-Forward"):
    """Visualise les résultats walk-forward"""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    fold_nums = [r['fold'] for r in results]
    accuracies = [r['accuracy'] for r in results]
    f1s = [r['f1'] for r in results]
    
    # 1. Accuracy par fold
    ax1 = axes[0, 0]
    ax1.bar(fold_nums, accuracies, color='steelblue', alpha=0.7)
    ax1.axhline(np.mean(accuracies), color='red', linestyle='--', 
               label=f'Moyenne: {np.mean(accuracies):.1%}')
    ax1.set_xlabel('Fold')
    ax1.set_ylabel('Accuracy')
    ax1.set_title(f'{method_name} - Accuracy par Fold')
    ax1.set_xticks(fold_nums)
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # 2. Accuracy et F1 par fold
    ax2 = axes[0, 1]
    x = np.arange(len(fold_nums))
    width = 0.35
    ax2.bar(x - width/2, accuracies, width, label='Accuracy', color='steelblue', alpha=0.7)
    ax2.bar(x + width/2, f1s, width, label='F1 Score', color='coral', alpha=0.7)
    ax2.set_xlabel('Fold')
    ax2.set_ylabel('Score')
    ax2.set_title(f'{method_name} - Accuracy vs F1')
    ax2.set_xticks(x)
    ax2.set_xticklabels(fold_nums)
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Cumulative accuracy
    ax3 = axes[1, 0]
    cumulative_acc = np.cumsum(accuracies) / np.arange(1, len(accuracies) + 1)
    ax3.plot(fold_nums, cumulative_acc, 'bo-', linewidth=2, markersize=8)
    ax3.set_xlabel('Fold')
    ax3.set_ylabel('Cumulative Accuracy')
    ax3.set_title(f'{method_name} - Accuracy Cumulative')
    ax3.grid(True, alpha=0.3)
    
    # 4. Distribution des accuracies
    ax4 = axes[1, 1]
    ax4.hist(accuracies, bins=8, edgecolor='black', alpha=0.7, color='steelblue')
    ax4.axvline(np.mean(accuracies), color='red', linestyle='--', 
               label=f'Moyenne: {np.mean(accuracies):.1%}')
    ax4.set_xlabel('Accuracy')
    ax4.set_ylabel('Count')
    ax4.set_title(f'{method_name} - Distribution des Accuracies')
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(f'/root/.openclaw/workspace/learning/code/walk_forward_{method_name.lower().replace(" ", "_")}_output.png', dpi=150)
    print(f"      → Visualisation sauvegardée: walk_forward_{method_name.lower()}_output.png")

# ============================================================================
# 6. PIPELINE COMPLET
# ============================================================================

def run_walk_forward_analysis():
    """Exécute l'analyse walk-forward complète"""
    
    print("=" * 70)
    print("WALK-FORWARD VALIDATION - SEMAINE 12")
    print("=" * 70)
    
    # Données
    print("\n[INIT] Génération des données...")
    df = generate_trading_data(n_days=500)
    print(f"      → {len(df)} observations générées")
    
    # Features et target
    feature_cols = ['rsi', 'macd', 'volatility', 'return_lag1', 'return_lag5', 'return_lag10']
    X = df[feature_cols]
    y = df['target']
    
    # Audit de leakage
    print("\n[AUDIT] Vérification de leakage...")
    audit_results = audit_leakage(X, y, feature_cols)
    
    # Walk-Forward Expanding
    print("\n" + "=" * 70)
    print("WALK-FORWARD EXPANDING WINDOW")
    print("=" * 70)
    
    results_expanding = walk_forward_expanding(
        X, y,
        model_class=lambda: RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42),
        train_size=2000,
        test_size=500,
        step=500
    )
    
    print(f"\n      → {len(results_expanding)} folds exécutés")
    
    stats_expanding = aggregate_results(results_expanding)
    print(f"\n      Résultats:")
    print(f"         → Global Accuracy: {stats_expanding['global_accuracy']:.2%}")
    print(f"         → Mean Fold Accuracy: {stats_expanding['mean_fold_accuracy']:.2%}")
    print(f"         → Std Fold Accuracy: {stats_expanding['std_fold_accuracy']:.2%}")
    print(f"         → Min Fold Accuracy: {stats_expanding['min_fold_accuracy']:.2%}")
    print(f"         → Max Fold Accuracy: {stats_expanding['max_fold_accuracy']:.2%}")
    print(f"         → Global F1: {stats_expanding['global_f1']:.3f}")
    print(f"         → Global ROC AUC: {stats_expanding['global_roc_auc']:.3f}")
    
    plot_walk_forward_results(results_expanding, "Expanding")
    
    # Walk-Forward Rolling
    print("\n" + "=" * 70)
    print("WALK-FORWARD ROLLING WINDOW")
    print("=" * 70)
    
    results_rolling = walk_forward_rolling(
        X, y,
        model_class=lambda: RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42),
        train_size=2000,
        test_size=500,
        step=500
    )
    
    print(f"\n      → {len(results_rolling)} folds exécutés")
    
    stats_rolling = aggregate_results(results_rolling)
    print(f"\n      Résultats:")
    print(f"         → Global Accuracy: {stats_rolling['global_accuracy']:.2%}")
    print(f"         → Mean Fold Accuracy: {stats_rolling['mean_fold_accuracy']:.2%}")
    print(f"         → Std Fold Accuracy: {stats_rolling['std_fold_accuracy']:.2%}")
    print(f"         → Min Fold Accuracy: {stats_rolling['min_fold_accuracy']:.2%}")
    print(f"         → Max Fold Accuracy: {stats_rolling['max_fold_accuracy']:.2%}")
    print(f"         → Global F1: {stats_rolling['global_f1']:.3f}")
    print(f"         → Global ROC AUC: {stats_rolling['global_roc_auc']:.3f}")
    
    plot_walk_forward_results(results_rolling, "Rolling")
    
    # Comparaison
    print("\n" + "=" * 70)
    print("COMPARAISON EXPANDING vs ROLLING")
    print("=" * 70)
    
    comparison = pd.DataFrame({
        'Métrique': ['Global Accuracy', 'Mean Fold Accuracy', 'Std Fold Accuracy', 'Global F1', 'Global ROC AUC'],
        'Expanding': [
            stats_expanding['global_accuracy'],
            stats_expanding['mean_fold_accuracy'],
            stats_expanding['std_fold_accuracy'],
            stats_expanding['global_f1'],
            stats_expanding['global_roc_auc']
        ],
        'Rolling': [
            stats_rolling['global_accuracy'],
            stats_rolling['mean_fold_accuracy'],
            stats_rolling['std_fold_accuracy'],
            stats_rolling['global_f1'],
            stats_rolling['global_roc_auc']
        ]
    })
    
    print(comparison.to_string(index=False))
    
    print("\n" + "=" * 70)
    print("✅ WALK-FORWARD VALIDATION COMPLETE")
    print("=" * 70)
    
    return df, results_expanding, results_rolling, stats_expanding, stats_rolling

if __name__ == "__main__":
    df, results_exp, results_roll, stats_exp, stats_roll = run_walk_forward_analysis()
