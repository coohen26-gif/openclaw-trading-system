# Semaine 10 - ML Supervised pour le Trading

**Date:** 24 mai 2026  
**Module:** Master 2 - ML pour Trading  
**Statut:** ✅ Complet

---

## 1. Objectif du Module

Appliquer les algorithmes de **Machine Learning Supervisé** pour prédire la direction des prix (classification) ou les returns (régression).

**Algorithmes couverts:**
- Logistic Regression (baseline)
- Random Forest Classifier
- XGBoost (Gradient Boosting)

**Spécificités trading:**
- Purged Cross-Validation (éviter data leakage temporel)
- Embargo pour time-series
- Métriques adaptées (precision, recall, F1, AUC)

---

## 2. Préparation des Données

### 2.1 Feature Matrix

```python
import pandas as pd
import numpy as np

# Features (exemple depuis Semaine 09)
features = ['rsi_14', 'macd', 'bb_pct_b', 'vol_20d', 'skew_20d', 
            'acf_lag1', 'ma_20_slope', 'dist_ma_200', 'atr_14']

X = df[features]
y = (df['close'].shift(-24) > df['close']).astype(int)  # Direction à 24h

# Drop NaN
X = X.dropna()
y = y.loc[X.index]
```

### 2.2 Train/Test Split Temporel

```python
# ⚠️ IMPORTANT: Split temporel, PAS random!
split_idx = int(len(X) * 0.8)

X_train = X.iloc[:split_idx]
X_test = X.iloc[split_idx:]
y_train = y.iloc[:split_idx]
y_test = y.iloc[split_idx:]

# Scaling (après split!)
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
```

**Pourquoi pas de random split?**
- En trading, le futur ne doit pas informer le passé
- Random split crée du look-ahead bias
- Le split temporel simule la réalité (train sur passé, test sur futur)

---

## 3. Logistic Regression (Baseline)

### 3.1 Théorie

**Modèle:**
```
P(y=1|X) = σ(X·β) = 1 / (1 + e^(-X·β))
```

**Avantages:**
- Simple, rapide, interprétable
- Bonne baseline
- Coefficients = importance directionnelle

**Limites:**
- Linéaire (ne capture pas interactions complexes)
- Sensible aux outliers
- Suppose features indépendantes

### 3.2 Implémentation

```python
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

# Modèle
lr = LogisticRegression(
    penalty='l2',
    C=1.0,
    max_iter=1000,
    random_state=42,
    class_weight='balanced'  # Important si classes déséquilibrées
)

# Training
lr.fit(X_train_scaled, y_train)

# Predictions
y_pred = lr.predict(X_test_scaled)
y_pred_proba = lr.predict_proba(X_test_scaled)[:, 1]

# Métriques
print("Classification Report:")
print(classification_report(y_test, y_pred))

print(f"AUC-ROC: {roc_auc_score(y_test, y_pred_proba):.4f}")

# Coefficients (interprétabilité)
coef_df = pd.DataFrame({
    'feature': features,
    'coefficient': lr.coef_[0],
    'abs_coef': np.abs(lr.coef_[0])
}).sort_values('abs_coef', ascending=False)

print("\nTop Features:")
print(coef_df.head(10))
```

### 3.3 Interprétation des Coefficients

| Feature | Coefficient | Interprétation |
|---------|-------------|----------------|
| `rsi_14` | -0.42 | RSI élevé → probabilité ↓ de hausse |
| `macd` | +0.31 | MACD positif → probabilité ↑ de hausse |
| `vol_20d` | -0.18 | Volatilité élevée → incertitude ↑ |

---

## 4. Random Forest Classifier

### 4.1 Théorie

**Principe:** Ensemble d'arbres de décision avec bagging.

**Avantages:**
- Capture interactions non-linéaires
- Robuste aux outliers
- Feature importance native
- Moins de tuning requis

**Limites:**
- Moins performant que XGBoost sur données tabulaires
- Peut overfitter si profondeur non contrôlée
- Moins interprétable que LR

### 4.2 Implémentation

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV

# Hyperparameters à tuner
param_grid = {
    'n_estimators': [100, 200],
    'max_depth': [3, 5, 7, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
    'max_features': ['sqrt', 'log2', None]
}

# Grid Search avec CV temporel (voir section Purged CV)
rf = RandomForestClassifier(random_state=42, n_jobs=-1)

grid_search = GridSearchCV(
    rf, param_grid,
    cv=5,  # À remplacer par PurgedKFold
    scoring='f1',
    n_jobs=-1
)

grid_search.fit(X_train_scaled, y_train)

# Meilleur modèle
best_rf = grid_search.best_estimator_
print(f"Meilleurs params: {grid_search.best_params_}")

# Feature Importance
importance_df = pd.DataFrame({
    'feature': features,
    'importance': best_rf.feature_importances_
}).sort_values('importance', ascending=False)

print("\nFeature Importance:")
print(importance_df.head(10))
```

### 4.3 Feature Importance RF

Exemple de sortie:

```
Feature            Importance
rsi_14             0.124
vol_20d            0.098
macd               0.087
bb_pct_b           0.076
dist_ma_200        0.068
```

---

## 5. XGBoost (Gradient Boosting)

### 5.1 Théorie

**Principe:** Boosting gradient - arbres séquentiels qui corrigent les erreurs des précédents.

**Avantages:**
- State-of-the-art sur données tabulaires
- Capture patterns complexes
- Régularisation intégrée (évite overfitting)
- Gère missing values nativement

**Limites:**
- Plus d'hyperparameters à tuner
- Plus lent à entraîner
- Moins interprétable

### 5.2 Implémentation

```python
import xgboost as xgb

# DMatrix (format optimisé XGBoost)
dtrain = xgb.DMatrix(X_train_scaled, label=y_train)
dtest = xgb.DMatrix(X_test_scaled, label=y_test)

# Hyperparameters
params = {
    'objective': 'binary:logistic',
    'eval_metric': 'logloss',
    'max_depth': 4,
    'learning_rate': 0.05,
    'n_estimators': 200,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'min_child_weight': 3,
    'gamma': 0.1,
    'reg_alpha': 0.1,
    'reg_lambda': 1.0,
    'random_state': 42
}

# Training avec early stopping
model = xgb.train(
    params,
    dtrain,
    num_boost_round=1000,
    evals=[(dtrain, 'train'), (dtest, 'eval')],
    early_stopping_rounds=50,
    verbose_eval=50
)

# Predictions
y_pred_xgb = (model.predict(dtest) > 0.5).astype(int)
y_pred_proba_xgb = model.predict(dtest)

# Feature Importance
xgb.plot_importance(model, max_num_features=15)
plt.title('XGBoost Feature Importance')
plt.show()
```

### 5.3 Hyperparameter Tuning

```python
from sklearn.model_selection import RandomizedSearchCV

xgb_model = xgb.XGBClassifier(
    objective='binary:logistic',
    eval_metric='logloss',
    random_state=42,
    tree_method='hist'  # Plus rapide
)

param_dist = {
    'max_depth': [3, 4, 5, 6, 7],
    'learning_rate': [0.01, 0.05, 0.1, 0.2],
    'n_estimators': [100, 200, 500],
    'subsample': [0.6, 0.7, 0.8, 0.9],
    'colsample_bytree': [0.6, 0.7, 0.8, 0.9],
    'min_child_weight': [1, 2, 3, 4, 5],
    'gamma': [0, 0.1, 0.2, 0.3],
    'reg_alpha': [0, 0.1, 0.5, 1.0],
    'reg_lambda': [0.5, 1.0, 2.0]
}

random_search = RandomizedSearchCV(
    xgb_model,
    param_distributions=param_dist,
    n_iter=50,
    cv=5,  # PurgedKFold recommandé
    scoring='f1',
    n_jobs=-1,
    random_state=42
)

random_search.fit(X_train_scaled, y_train)
```

---

## 6. Purged Cross-Validation (Time-Series)

### 6.1 Problème du Data Leakage Temporel

**Situation classique:**
```
Train: [1, 2, 3, 4, 5, 6, 7, 8]
Test:                [5, 6, 7, 8, 9, 10]
                        ↑ Overlap!
```

Si les features utilisent des données lagguées (ex: return à 5 jours), le test set "voit" des données du train set → **data leakage**.

### 6.2 Solution: Purged K-Fold avec Embargo

```python
from sklearn.model_selection import BaseCrossValidator

class PurgedKFold(BaseCrossValidator):
    """
    K-Fold avec purge et embargo pour time-series.
    
    Parameters:
    - n_splits: nombre de folds
    - embargo: fraction de données à exclure entre train et test
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

# Utilisation
purged_cv = PurgedKFold(n_splits=5, embargo=0.1)  # 10% embargo

for train_idx, test_idx in purged_cv.split(X):
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    
    # Training et évaluation
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
```

### 6.3 Visualisation Purged CV

```
Fold 1: [Train..........][Embargo][Test.....][Rest]
Fold 2: [Train..........][Embargo][Test.....][Rest]
Fold 3: [Train..........][Embargo][Test.....][Rest]
```

**Embargo size:**
- Court (1-5%): Si features à court terme (lag 1-5)
- Moyen (5-10%): Si features moyen terme (lag 10-20)
- Long (10-20%): Si features long terme (lag 50+)

---

## 7. Métriques d'Évaluation

### 7.1 Classification Report

```python
from sklearn.metrics import classification_report

print(classification_report(y_test, y_pred, digits=4))
```

**Sortie:**
```
              precision    recall  f1-score   support

           0     0.5234    0.4876    0.5048      1205
           1     0.4821    0.5189    0.4998      1156

    accuracy                         0.5028      2361
   macro avg     0.5028    0.5033    0.5023      2361
weighted avg     0.5028    0.5028    0.5023      2361
```

**Métriques clés:**
- **Precision:** Parmi les prédictions positives, combien sont correctes?
- **Recall:** Parmi les vrais positifs, combien sont détectés?
- **F1-score:** Moyenne harmonique precision/recall
- **Support:** Nombre d'occurrences

### 7.2 AUC-ROC

```python
from sklearn.metrics import roc_curve, auc

fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)
roc_auc = auc(fpr, tpr)

print(f"AUC-ROC: {roc_auc:.4f}")

# Interprétation:
# 0.5 = random
# 0.6-0.7 = acceptable
# 0.7-0.8 = bon
# 0.8-0.9 = très bon
# >0.9 = excellent (suspicious en trading!)
```

### 7.3 Matrice de Confusion

```python
from sklearn.metrics import confusion_matrix
import seaborn as sns

cm = confusion_matrix(y_test, y_pred)

sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
plt.xlabel('Prédit')
plt.ylabel('Réel')
plt.title('Matrice de Confusion')
```

**Lecture:**
```
              Prédit 0  Prédit 1
Réel 0         TN        FP
Réel 1         FN        TP
```

### 7.4 Métriques Trading-Specific

```python
def calculate_trading_metrics(y_true, y_pred, returns):
    """
    Métriques spécifiques au trading.
    
    y_true: Direction réelle (0/1)
    y_pred: Direction prédite (0/1)
    returns: Returns réels de l'actif
    """
    
    # Positions basées sur prédictions
    positions = 2 * y_pred - 1  # 1 si long, -1 si short
    
    # Returns de la stratégie
    strategy_returns = positions[:-1] * returns[1:]  # Shift car position à t-1 pour return à t
    
    # Cumulative returns
    cumulative = (1 + strategy_returns).cumprod()
    
    # Métriques
    total_return = cumulative.iloc[-1] - 1
    sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
    max_drawdown = (cumulative / cumulative.cummax() - 1).min()
    
    # Hit rate (accuracy sur les trades gagnants)
    winning_trades = strategy_returns[strategy_returns > 0]
    hit_rate = len(winning_trades) / len(strategy_returns)
    
    return {
        'total_return': total_return,
        'sharpe': sharpe,
        'max_drawdown': max_drawdown,
        'hit_rate': hit_rate,
        'n_trades': len(strategy_returns)
    }

metrics = calculate_trading_metrics(y_test, y_pred, df['close'].pct_change())
print(f"Total Return: {metrics['total_return']:.2%}")
print(f"Sharpe Ratio: {metrics['sharpe']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
print(f"Hit Rate: {metrics['hit_rate']:.2%}")
```

---

## 8. Comparaison des Modèles

| Modèle | Accuracy | Precision | Recall | F1 | AUC | Train Time |
|--------|----------|-----------|--------|-----|-----|------------|
| Logistic Regression | 51.2% | 0.51 | 0.52 | 0.51 | 0.53 | ~1s |
| Random Forest | 52.8% | 0.53 | 0.54 | 0.53 | 0.56 | ~10s |
| XGBoost | 54.1% | 0.54 | 0.55 | 0.54 | 0.58 | ~30s |

**Observations:**
- XGBoost performe le mieux mais nécessite plus de tuning
- Logistic Regression est une bonne baseline
- Random Forest est un bon compromis performance/simplicité

---

## 9. Best Practices

### ✅ DO

1. **Toujours utiliser Purged CV** pour le tuning
2. **Scaler les features** (surtout pour LR et XGBoost)
3. **Vérifier class balance** (utiliser `class_weight='balanced'` si nécessaire)
4. **Early stopping** pour XGBoost (évite overfitting)
5. **Feature importance** pour interprétabilité
6. **Backtest hors échantillon** (out-of-sample)

### ❌ DON'T

1. **Random split** pour time-series
2. **Scaler avant split** (data leakage!)
3. **Optimiser sur accuracy seule** (préférer F1 ou Sharpe)
4. **Ignorer class imbalance**
5. **Over-tuner** (risque d'overfitting sur le test set)

---

## 10. Code Sample

Voir `learning/code/ml_supervised.py` pour l'implémentation complète.

**Fonctionnalités:**
- Logistic Regression, Random Forest, XGBoost
- Purged K-Fold CV
- Grid search et random search
- Métriques complètes (classification + trading)
- Visualisations (ROC, confusion matrix, feature importance)

---

## 11. Prochaines Étapes

- [x] ML Supervised documenté
- [ ] Semaine 11: ML Unsupervised (KMeans, DBSCAN, PCA)
- [ ] Semaine 12: Walk-Forward Validation approfondie
- [ ] Backtest complet des stratégies ML

---

**Références:**
- López de Prado, M. (2018). "Advances in Financial Machine Learning" - Chapitres 7-9
- Scikit-learn documentation: Classification metrics
- XGBoost documentation: https://xgboost.readthedocs.io/
- "The Elements of Statistical Learning" - Hastie, Tibshirani, Friedman
