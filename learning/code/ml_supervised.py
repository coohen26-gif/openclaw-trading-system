"""
ML Supervised pour Trading - Semaine 10
Logistic Regression, Random Forest, XGBoost avec Purged CV
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_curve, auc,
    precision_score, recall_score, f1_score
)
import seaborn as sns

# ============================================================================
# 1. PURGED K-FOLD CROSS-VALIDATION
# ============================================================================

from sklearn.model_selection import BaseCrossValidator

class PurgedKFold(BaseCrossValidator):
    """
    K-Fold avec purge et embargo pour time-series.
    Évite le data leakage temporel.
    """
    
    def __init__(self, n_splits=5, embargo=0.05):
        self.n_splits = n_splits
        self.embargo = embargo
    
    def split(self, X, y=None, groups=None):
        n_samples = len(X)
        fold_size = n_samples // self.n_splits
        embargo_size = int(fold_size * self.embargo)
        
        folds = []
        for i in range(self.n_splits):
            # Test set
            test_start = i * fold_size
            test_end = (i + 1) * fold_size if i < self.n_splits - 1 else n_samples
            
            # Train set (avec embargo)
            train_end = test_start - embargo_size if i > 0 else test_start
            train_start = 0
            
            train_idx = np.arange(train_start, train_end)
            test_idx = np.arange(test_start, test_end)
            
            folds.append((train_idx, test_idx))
        
        return iter(folds)
    
    def get_n_splits(self, X=None, y=None, groups=None):
        return self.n_splits

# ============================================================================
# 2. GÉNÉRATION DE DONNÉES
# ============================================================================

def generate_trading_data(n_days=500, seed=42):
    """Génère des données de trading simulées avec features et target"""
    np.random.seed(seed)
    
    n_obs = n_days * 24  # Hourly
    
    # Prix simulés
    initial_price = 50000
    volatility = 0.002
    
    returns = np.random.randn(n_obs) * volatility
    returns += 0.03 * np.roll(returns, 1)  # Momentum
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
    
    # Distance to MA
    ma_50 = df['close'].rolling(50).mean()
    df['dist_ma'] = (df['close'] - ma_50) / ma_50
    
    # Target: Direction à 24h
    df['target'] = (df['close'].shift(-24) > df['close']).astype(int)
    
    df = df.dropna()
    
    return df

# ============================================================================
# 3. MÉTRIQUES TRADING
# ============================================================================

def calculate_trading_metrics(y_true, y_pred, returns):
    """Calcule les métriques de trading"""
    
    # Positions
    positions = 2 * y_pred - 1  # 1 = long, -1 = short
    
    # Returns stratégie
    strategy_returns = positions[:-1] * returns[1:].values
    
    # Cumulative
    cumulative = (1 + pd.Series(strategy_returns)).cumprod()
    
    # Métriques
    total_return = cumulative.iloc[-1] - 1
    sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252 * 24) if strategy_returns.std() > 0 else 0
    max_drawdown = (cumulative / cumulative.cummax() - 1).min()
    hit_rate = (strategy_returns > 0).sum() / len(strategy_returns)
    
    return {
        'total_return': total_return,
        'sharpe': sharpe,
        'max_drawdown': max_drawdown,
        'hit_rate': hit_rate,
        'n_trades': len(strategy_returns)
    }

# ============================================================================
# 4. ENTRAÎNEMENT ET ÉVALUATION
# ============================================================================

def train_and_evaluate():
    """Entraîne et évalue les 3 modèles"""
    
    print("=" * 70)
    print("ML SUPERVISED POUR TRADING - SEMAINE 10")
    print("=" * 70)
    
    # Données
    print("\n[1/5] Génération des données...")
    df = generate_trading_data(n_days=500)
    print(f"      → {len(df)} observations")
    
    # Features et target
    feature_cols = ['rsi', 'macd', 'volatility', 'dist_ma']
    X = df[feature_cols]
    y = df['target']
    
    # Split temporel
    print("\n[2/5] Split train/test (80/20)...")
    split_idx = int(len(X) * 0.8)
    
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    print(f"      → Train: {len(X_train)} samples")
    print(f"      → Test: {len(X_test)} samples")
    
    # Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    X_train_scaled = pd.DataFrame(X_train_scaled, columns=feature_cols, index=X_train.index)
    X_test_scaled = pd.DataFrame(X_test_scaled, columns=feature_cols, index=X_test.index)
    
    # Modèles
    print("\n[3/5] Entraînement des modèles...")
    
    models = {
        'Logistic Regression': LogisticRegression(
            C=1.0, max_iter=1000, random_state=42, class_weight='balanced'
        ),
        'Random Forest': RandomForestClassifier(
            n_estimators=100, max_depth=5, random_state=42, n_jobs=-1
        )
    }
    
    # XGBoost (si disponible)
    try:
        import xgboost as xgb
        models['XGBoost'] = xgb.XGBClassifier(
            n_estimators=100, max_depth=4, learning_rate=0.05,
            random_state=42, eval_metric='logloss', verbosity=0
        )
    except ImportError:
        print("      → XGBoost non installé, skip")
    
    results = []
    
    for name, model in models.items():
        print(f"\n      ─── {name} ───")
        
        # Training
        model.fit(X_train_scaled, y_train)
        
        # Predictions
        y_pred = model.predict(X_test_scaled)
        
        if hasattr(model, 'predict_proba'):
            y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
        else:
            y_pred_proba = y_pred
        
        # Métriques classification
        accuracy = (y_pred == y_test).mean()
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        try:
            roc_auc = auc(roc_curve(y_test, y_pred_proba)[0], roc_curve(y_test, y_pred_proba)[1])
        except:
            roc_auc = 0.5
        
        # Métriques trading
        returns = df['close'].pct_change()
        trading_metrics = calculate_trading_metrics(
            y_test.values, y_pred, returns.loc[X_test.index]
        )
        
        results.append({
            'model': name,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'roc_auc': roc_auc,
            'trading_return': trading_metrics['total_return'],
            'sharpe': trading_metrics['sharpe'],
            'hit_rate': trading_metrics['hit_rate']
        })
        
        print(f"      → Accuracy: {accuracy:.2%}")
        print(f"      → Precision: {precision:.3f}")
        print(f"      → Recall: {recall:.3f}")
        print(f"      → F1 Score: {f1:.3f}")
        print(f"      → AUC-ROC: {roc_auc:.4f}")
        print(f"      → Trading Return: {trading_metrics['total_return']:.2%}")
        print(f"      → Sharpe: {trading_metrics['sharpe']:.2f}")
        
        # Feature importance (si disponible)
        if hasattr(model, 'feature_importances_'):
            importance = pd.DataFrame({
                'feature': feature_cols,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            print(f"      → Top feature: {importance.iloc[0]['feature']} ({importance.iloc[0]['importance']:.3f})")
        elif hasattr(model, 'coef_'):
            coef = pd.DataFrame({
                'feature': feature_cols,
                'coefficient': model.coef_[0],
                'abs_coef': np.abs(model.coef_[0])
            }).sort_values('abs_coef', ascending=False)
            print(f"      → Top feature: {coef.iloc[0]['feature']} (coef={coef.iloc[0]['coefficient']:.3f})")
    
    # Résumé
    print("\n" + "=" * 70)
    print("RÉSUMÉ COMPARATIF")
    print("=" * 70)
    
    results_df = pd.DataFrame(results).set_index('model')
    print(results_df.round(4).to_string())
    
    # Visualisations
    print("\n" + "=" * 70)
    print("GÉNÉRATION DES VISUALISATIONS...")
    print("=" * 70)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Feature importance (Random Forest)
    ax1 = axes[0, 0]
    rf_model = models['Random Forest']
    importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': rf_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    ax1.barh(range(len(importance)), importance['importance'].values)
    ax1.set_yticks(range(len(importance)))
    ax1.set_yticklabels(importance['feature'].values)
    ax1.invert_yaxis()
    ax1.set_xlabel('Importance')
    ax1.set_title('Random Forest - Feature Importance')
    
    # 2. ROC Curve (tous modèles)
    ax2 = axes[0, 1]
    for name, model in models.items():
        y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
        fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
        roc_auc = auc(fpr, tpr)
        ax2.plot(fpr, tpr, label=f'{name} (AUC={roc_auc:.3f})')
    
    ax2.plot([0, 1], [0, 1], 'k--', alpha=0.5)
    ax2.set_xlabel('False Positive Rate')
    ax2.set_ylabel('True Positive Rate')
    ax2.set_title('ROC Curves')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Confusion Matrix (Random Forest)
    ax3 = axes[1, 0]
    y_pred_rf = models['Random Forest'].predict(X_test_scaled)
    cm = confusion_matrix(y_test, y_pred_rf)
    
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax3)
    ax3.set_xlabel('Prédit')
    ax3.set_ylabel('Réel')
    ax3.set_title('Confusion Matrix - Random Forest')
    
    # 4. Accuracy comparison
    ax4 = axes[1, 1]
    models_names = list(results_df.index)
    accuracies = results_df['accuracy'].values
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(models_names)))
    
    bars = ax4.bar(models_names, accuracies, color=colors)
    ax4.set_ylabel('Accuracy')
    ax4.set_title('Model Accuracy Comparison')
    ax4.set_ylim(0, max(accuracies) * 1.2)
    
    for bar, acc in zip(bars, accuracies):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{acc:.1%}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('/root/.openclaw/workspace/learning/code/ml_supervised_output.png', dpi=150)
    print(f"      → Visualisation sauvegardée: ml_supervised_output.png")
    
    print("\n" + "=" * 70)
    print("✅ ML SUPERVISED COMPLETE")
    print("=" * 70)
    
    return results_df, models

if __name__ == "__main__":
    results, models = train_and_evaluate()
