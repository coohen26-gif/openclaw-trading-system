# Semaine 12 - Walk-Forward Validation

**Date:** 24 mai 2026  
**Module:** Master 2 - ML pour Trading  
**Statut:** ✅ Complet

---

## 1. Objectif du Module

La **Walk-Forward Validation** est la méthode de validation **la plus robuste** pour les stratégies de trading. Elle simule le déploiement réel d'un modèle en ré-entraînant périodiquement sur des données glissantes.

**Problèmes résolus:**
- Look-ahead bias (fuite d'information du futur)
- Data leakage temporel
- Overfitting sur une période spécifique
- Non-stationnarité des marchés (concept drift)

**Objectifs:**
- Comprendre et implémenter le walk-forward analysis
- Purged K-Fold Cross-Validation
- Éviter tous les types de data leakage
- Évaluer la robustesse temporelle des modèles

---

## 2. Look-Ahead Bias: Le Problème Fondamental

### 2.1 Qu'est-ce que le Look-Ahead Bias?

**Définition:** Utiliser involontairement des informations du futur pour prédire le présent.

**Exemples classiques:**

```python
# ❌ MAUVAIS: Utiliser le close du jour J pour prédire J
df['signal'] = df['close'] > df['close'].shift(1)
df['return'] = df['close'].pct_change()  # Return de J-1 à J
# Le signal utilise close[J] pour "prédire" return[J] qui inclut close[J]!

# ✅ BON: Décaler correctement
df['signal'] = df['close'].shift(1) > df['close'].shift(2)  # Signal à J-1
df['return'] = df['close'].pct_change()  # Return de J-1 à J
# Le signal à J-1 prédit le return de J-1 à J
```

### 2.2 Autres Sources de Look-Ahead

```python
# ❌ Normalisation avant split (fuite du test vers train)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)  # Utilise stats de TOUTES les données!
X_train, X_test = train_test_split(X_scaled, shuffle=False)

# ✅ Normalisation après split
X_train, X_test = train_test_split(X, shuffle=False)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)  # Stats du train uniquement
X_test_scaled = scaler.transform(X_test)  # Applique stats du train au test
```

```python
# ❌ Features avec lookahead
df['ma_20'] = df['close'].rolling(20).mean()  # Inclut le point courant!
df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
# Si on prédit à t, on ne devrait pas avoir ma_20[t] qui inclut close[t]

# ✅ Features lagguées
df['ma_20'] = df['close'].shift(1).rolling(20).mean()  # MA à t-1
df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
```

### 2.3 Checklist Anti Look-Ahead

| Source | Vérification | Correction |
|--------|--------------|------------|
| Features | Utilisent-elles des données futures? | Shift(1) minimum |
| Normalisation | Fit sur train uniquement? | Fit train, transform test |
| Target | Prédit-on le futur ou le présent? | Shift négatif correct |
| Split temporel | Test après train chronologiquement? | shuffle=False |
| Cross-validation | Folds respectent-ils l'ordre temporel? | PurgedKFold |

---

## 3. Walk-Forward Analysis

### 3.1 Principe

**Concept:** Au lieu d'un split train/test unique, on fait glisser une fenêtre d'entraînement dans le temps.

```
Iteration 1: [Train 1][Test 1][......]
Iteration 2: [Train 2][Test 2][......]
Iteration 3: [Train 3][Test 3][......]
```

**Deux variantes:**

1. **Expanding Window:** Le train s'étend (inclut tout le passé)
2. **Rolling Window:** Le train garde taille fixe (glisse)

### 3.2 Implémentation: Expanding Window

```python
def walk_forward_expanding(X, y, train_size=252, test_size=63, step=63):
    """
    Walk-forward avec fenêtre d'entraînement expansible.
    
    Parameters:
    - train_size: Nombre d'observations pour l'entraînement initial
    - test_size: Nombre d'observations pour le test
    - step: Pas de glissement (retrain frequency)
    """
    
    n_samples = len(X)
    results = []
    
    # Premier fold
    train_end = train_size
    test_end = train_end + test_size
    
    fold = 1
    while test_end <= n_samples:
        # Split
        X_train = X.iloc[:train_end]
        X_test = X.iloc[train_end:test_end]
        y_train = y.iloc[:train_end]
        y_test = y.iloc[train_end:test_end]
        
        # Training
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Prediction
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        # Metrics
        accuracy = (y_pred == y_test).mean()
        
        results.append({
            'fold': fold,
            'train_start': 0,
            'train_end': train_end,
            'test_start': train_end,
            'test_end': test_end,
            'accuracy': accuracy,
            'y_pred': y_pred,
            'y_true': y_test.values
        })
        
        # Prochain fold (expanding: train grandit)
        train_end += step
        test_end += step
        fold += 1
    
    return results
```

### 3.3 Implémentation: Rolling Window

```python
def walk_forward_rolling(X, y, train_size=252, test_size=63, step=63):
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
        # Split
        X_train = X.iloc[train_start:train_end]
        X_test = X.iloc[train_end:test_end]
        y_train = y.iloc[train_start:train_end]
        y_test = y.iloc[train_end:test_end]
        
        # Training
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Prediction
        y_pred = model.predict(X_test)
        accuracy = (y_pred == y_test).mean()
        
        results.append({
            'fold': fold,
            'train_start': train_start,
            'train_end': train_end,
            'test_start': train_end,
            'test_end': test_end,
            'accuracy': accuracy
        })
        
        # Prochain fold (rolling: fenêtre glisse)
        train_start += step
        train_end += step
        test_end += step
        fold += 1
    
    return results
```

### 3.4 Comparaison Expanding vs Rolling

| Critère | Expanding Window | Rolling Window |
|---------|------------------|----------------|
| Taille train | Grandit avec le temps | Fixe |
| Adaptabilité | Moins adaptatif (vieux poids) | Plus adaptatif |
| Variance | Plus faible (plus de données) | Plus élevée |
| Concept drift | Peut souffrir si marché change | Mieux géré |
| Usage recommandé | Marchés stables | Marchés changeants |

**Recommandation:**
- **Crypto:** Rolling window (marché très changeant)
- **Forex/Majors:** Expanding window (plus stable)
- **Actions:** Dépend du secteur

---

## 4. Purged K-Fold Cross-Validation

### 4.1 Problème avec K-Fold Standard

```
K-Fold Standard (shuffle=True):
Fold 1: [X X X X O O O O]  ← Mélange temporel!
Fold 2: [O O O O X X X X]

Problème: Les features lagguées créent du leakage
```

**Exemple concret:**
- Feature: `return_5d` (return sur 5 jours laggué)
- Si train contient jour J et test contient jour J+3
- La feature à J+3 utilise des prix de J-2 à J+3
- **Leakage:** Le train (J) influence le test (J+3)!

### 4.2 Solution: Purged K-Fold avec Embargo

```python
from sklearn.model_selection import BaseCrossValidator

class PurgedKFold(BaseCrossValidator):
    """
    K-Fold avec purge et embargo pour time-series.
    
    Parameters:
    - n_splits: Nombre de folds
    - embargo: Fraction de données à exclure entre train et test
               (doit couvrir le lag maximum des features)
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
```

### 4.3 Taille de l'Embargo

**Règle:** `embargo_size >= max_lag_des_features`

```python
# Exemple: Features avec lags maximum de 20 jours
max_lag = 20
n_samples = 2520  # ~10 ans de trading days
fold_size = 2520 / 5 = 504

embargo_ratio = max_lag / fold_size = 20 / 504 ≈ 0.04

# Utiliser embargo = 0.05 (5%) pour être safe
purged_cv = PurgedKFold(n_splits=5, embargo=0.05)
```

**Guidelines:**

| Type de Features | Lag Max | Embargo Recommandé |
|------------------|---------|-------------------|
| Court terme (RSI, MACD) | 5-10 | 2-5% |
| Moyen terme (MA 50, 200) | 20-50 | 5-10% |
| Long terme (trends) | 50-200 | 10-20% |

### 4.4 Utilisation avec GridSearch

```python
from sklearn.model_selection import GridSearchCV

# Purged CV
purged_cv = PurgedKFold(n_splits=5, embargo=0.1)

# Grid search
param_grid = {
    'n_estimators': [100, 200],
    'max_depth': [3, 5, 7],
    'min_samples_split': [2, 5]
}

grid_search = GridSearchCV(
    RandomForestClassifier(random_state=42),
    param_grid,
    cv=purged_cv,  # ← Purged CV ici!
    scoring='f1',
    n_jobs=-1
)

grid_search.fit(X, y)
```

---

## 5. Data Leakage: Types et Prévention

### 5.1 Types de Leakage

| Type | Description | Exemple | Prévention |
|------|-------------|---------|------------|
| Temporel | Futur → Présent | Target mal shiftée | Shift correct |
| Feature | Train → Test | Scaling avant split | Fit train seulement |
| Target | Target dans features | Include target dans X | Vérifier features |
| Split | Test dans train | Shuffle=True | shuffle=False |
| CV | Leakage entre folds | K-fold standard | PurgedKFold |

### 5.2 Audit de Leakage

```python
def audit_leakage(X, y, feature_names=None):
    """
    Audit basique pour détecter leakage potentiel.
    """
    
    if feature_names is None:
        feature_names = X.columns if hasattr(X, 'columns') else range(X.shape[1])
    
    print("=" * 60)
    print("AUDIT DE LEAKAGE")
    print("=" * 60)
    
    # 1. Corrélation features-target (suspicious si trop haute)
    print("\n[1] Corrélation Features-Target:")
    for i, name in enumerate(feature_names):
        corr = np.corrcoef(X[:, i], y)[0, 1]
        if abs(corr) > 0.3:
            print(f"    ⚠️  {name}: {corr:.3f} (SUSPECT!)")
        elif abs(corr) > 0.1:
            print(f"    ⚡ {name}: {corr:.3f}")
    
    # 2. Features avec variance nulle
    print("\n[2] Features à variance nulle:")
    for i, name in enumerate(feature_names):
        if np.std(X[:, i]) == 0:
            print(f"    ❌ {name}: variance = 0")
    
    # 3. Features avec NaN
    print("\n[3] Features avec NaN:")
    for i, name in enumerate(feature_names):
        nan_pct = np.isnan(X[:, i]).sum() / len(X) * 100
        if nan_pct > 0:
            print(f"    ⚠️  {name}: {nan_pct:.1f}% NaN")
    
    # 4. Target leakage check (feature == target shifted)
    print("\n[4] Target leakage check:")
    for i, name in enumerate(feature_names):
        # Check si feature ≈ target shifté
        for shift in [-1, 0, 1]:
            if shift == 0:
                continue
            y_shifted = np.roll(y, shift)
            corr = np.corrcoef(X[:, i], y_shifted)[0, 1]
            if abs(corr) > 0.9:
                print(f"    🚨 {name} ≈ target shifted by {shift} (corr={corr:.3f})")
    
    print("\n" + "=" * 60)
```

---

## 6. Métriques de Performance Walk-Forward

### 6.1 Agrégation des Résultats

```python
def aggregate_walk_forward_results(results):
    """
    Agrège les résultats de walk-forward analysis.
    """
    
    # Concaténer toutes les prédictions
    all_y_true = []
    all_y_pred = []
    all_y_proba = []
    
    for fold_result in results:
        all_y_true.extend(fold_result['y_true'])
        all_y_pred.extend(fold_result['y_pred'])
        if 'y_proba' in fold_result:
            all_y_proba.extend(fold_result['y_proba'])
    
    # Métriques globales
    accuracy = np.mean(np.array(all_y_true) == np.array(all_y_pred))
    
    # Métriques par fold
    fold_accuracies = [r['accuracy'] for r in results]
    
    return {
        'global_accuracy': accuracy,
        'mean_fold_accuracy': np.mean(fold_accuracies),
        'std_fold_accuracy': np.std(fold_accuracies),
        'min_fold_accuracy': np.min(fold_accuracies),
        'max_fold_accuracy': np.max(fold_accuracies),
        'n_folds': len(results),
        'fold_accuracies': fold_accuracies
    }
```

### 6.2 Interprétation

| Métrique | Bonne Valeur | Interprétation |
|----------|--------------|----------------|
| Global Accuracy | > 52% | Modèle performant |
| Mean Fold Accuracy | > 50% | Performance moyenne OK |
| Std Fold Accuracy | < 5% | Performance stable |
| Min Fold Accuracy | > 48% | Pas de fold catastrophique |

**Red Flags:**
- Std > 10%: Performance très instable
- Min < 45%: Certains folds échouent complètement
- Global << Mean: Problème d'agrégation

### 6.3 Visualisation Walk-Forward

```python
def plot_walk_forward_results(results):
    """Visualise les résultats walk-forward"""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Accuracy par fold
    ax1 = axes[0, 0]
    fold_nums = [r['fold'] for r in results]
    accuracies = [r['accuracy'] for r in results]
    
    ax1.bar(fold_nums, accuracies, color='steelblue', alpha=0.7)
    ax1.axhline(np.mean(accuracies), color='red', linestyle='--', 
               label=f'Moyenne: {np.mean(accuracies):.1%}')
    ax1.set_xlabel('Fold')
    ax1.set_ylabel('Accuracy')
    ax1.set_title('Accuracy par Fold')
    ax1.set_xticks(fold_nums)
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # 2. Cumulative accuracy (rolling)
    ax2 = axes[0, 1]
    cumulative_acc = np.cumsum(accuracies) / np.arange(1, len(accuracies) + 1)
    
    ax2.plot(fold_nums, cumulative_acc, 'bo-', linewidth=2, markersize=8)
    ax2.set_xlabel('Fold')
    ax2.set_ylabel('Cumulative Accuracy')
    ax2.set_title('Accuracy Cumulative')
    ax2.grid(True, alpha=0.3)
    
    # 3. Train/Test sizes par fold
    ax3 = axes[1, 0]
    train_sizes = [r['train_end'] - r['train_start'] for r in results]
    test_sizes = [r['test_end'] - r['test_start'] for r in results]
    
    x = np.arange(len(fold_nums))
    ax3.bar(x - 0.2, train_sizes, 0.4, label='Train')
    ax3.bar(x + 0.2, test_sizes, 0.4, label='Test')
    ax3.set_xlabel('Fold')
    ax3.set_ylabel('Samples')
    ax3.set_title('Train/Test Sizes')
    ax3.set_xticks(x)
    ax3.set_xticklabels(fold_nums)
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. Distribution des accuracies
    ax4 = axes[1, 1]
    ax4.hist(accuracies, bins=10, edgecolor='black', alpha=0.7)
    ax4.axvline(np.mean(accuracies), color='red', linestyle='--', 
               label=f'Moyenne: {np.mean(accuracies):.1%}')
    ax4.set_xlabel('Accuracy')
    ax4.set_ylabel('Count')
    ax4.set_title('Distribution des Accuracies')
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('/root/.openclaw/workspace/learning/code/walk_forward_results.png', dpi=150)
    print(f"      → Visualisation sauvegardée: walk_forward_results.png")
```

---

## 7. Code Sample

Voir `learning/code/walk_forward.py` pour l'implémentation complète.

**Fonctionnalités:**
- Walk-forward expanding et rolling window
- Purged K-Fold CV
- Audit de leakage
- Métriques complètes et visualisations

---

## 8. Best Practices

### ✅ DO

1. **Toujours utiliser shuffle=False** pour time-series
2. **Fit scaler sur train uniquement**
3. **Embargo >= max_lag des features**
4. **Vérifier stability** (std fold accuracy < 5%)
5. **Documenter tous les lags** dans les features
6. **Audit de leakage** avant training

### ❌ DON'T

1. **Shuffle les données** temporelles
2. **Scaler avant split**
3. **Ignorer l'embargo** dans CV
4. **Utiliser expanding window** sur marchés très changeants
5. **Oublier de shift** les features et targets

---

## 9. Prochaines Étapes

- [x] Walk-Forward Validation documenté
- [ ] Semaine 13: Mean Reversion Avancée (Ornstein-Uhlenbeck)
- [ ] Semaine 14: Momentum & Breakouts
- [ ] Intégration complète dans pipeline de production

---

**Références:**
- López de Prado, M. (2018). "Advances in Financial Machine Learning" - Chapitres 7, 11
- Bailey, D., López de Prado, M. (2014). "The Deflated Sharpe Ratio"
- Scikit-learn: Cross-validation documentation
- QuantConnect: Walk-forward optimization
