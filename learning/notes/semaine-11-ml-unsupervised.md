# Semaine 11 - ML Unsupervised pour le Trading

**Date:** 24 mai 2026  
**Module:** Master 2 - ML pour Trading  
**Statut:** ✅ Complet

---

## 1. Objectif du Module

Le **Machine Learning Non-Supervisé** permet de découvrir des patterns cachés dans les données **sans labels préalables**. Applications principales en trading:

- **Regime Detection:** Identifier les états de marché (bull, bear, range)
- **Outlier Detection:** Détecter anomalies et événements extrêmes
- **Dimensionality Reduction:** Réduire le bruit, extraire facteurs latents
- **Clustering:** Grouper assets ou périodes similaires

**Algorithmes couverts:**
- KMeans Clustering
- DBSCAN (Density-Based Spatial Clustering)
- PCA (Principal Component Analysis)

---

## 2. KMeans Clustering - Regime Detection

### 2.1 Théorie

**Principe:** Partitionner les données en K clusters où chaque point appartient au cluster avec le centroïde le plus proche.

**Algorithme:**
1. Initialiser K centroïdes aléatoirement
2. Assigner chaque point au centroïde le plus proche
3. Recalculer les centroïdes (moyenne des points assignés)
4. Répéter étapes 2-3 jusqu'à convergence

**Objectif:** Minimiser l'inertie (somme des distances au carré)
```
J = Σᵢ Σⱼ ||xᵢⱼ - μⱼ||²
```

### 2.2 Application: Regime Detection

```python
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Features pour regime detection
features = ['return', 'volatility', 'skewness', 'volume_change']

X = df[features].dropna()

# Scaling (CRUCIAL pour KMeans)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Nombre de clusters (régimes)
# Typiquement 3-4 pour les régimes de marché
k = 3

kmeans = KMeans(
    n_clusters=k,
    init='k-means++',  # Meilleure initialisation
    n_init=10,
    max_iter=300,
    random_state=42
)

# Training
kmeans.fit(X_scaled)

# Labels
df['regime'] = np.nan
df.loc[X.index, 'regime'] = kmeans.labels_

# Interprétation des régimes
regime_stats = df.groupby('regime')[features].agg(['mean', 'std'])
print(regime_stats)
```

### 2.3 Interprétation des Régimes

Exemple de sortie:

```
                return          volatility
                mean    std   mean    std
regime
0 (Bear)       -0.012  0.025   0.035  0.012  ← Returns négatifs, vol élevée
1 (Bull)        0.008  0.015   0.018  0.008  ← Returns positifs, vol modérée
2 (Range)      -0.001  0.008   0.012  0.005  ← Returns neutres, vol basse
```

**Mapping Régime → Stratégie:**

| Régime | Caractéristiques | Stratégie Optimale |
|--------|------------------|-------------------|
| Bull | Returns +, vol modérée | Momentum, trend following |
| Bear | Returns -, vol élevée | Short, hedging, defensive |
| Range | Returns ~0, vol basse | Mean reversion, market making |

### 2.4 Détermination du Nombre Optimal de Clusters

```python
from sklearn.metrics import silhouette_score

# Méthode du coude (elbow method)
inertias = []
K_range = range(2, 10)

for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(X_scaled)
    inertias.append(kmeans.inertia_)

# Plot
plt.plot(K_range, inertias, 'bo-')
plt.xlabel('Nombre de Clusters (K)')
plt.ylabel('Inertie')
plt.title('Elbow Method')
plt.show()

# Silhouette Score (qualité du clustering)
silhouette_scores = []

for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)
    score = silhouette_score(X_scaled, labels)
    silhouette_scores.append(score)

# Plot
plt.plot(K_range, silhouette_scores, 'ro-')
plt.xlabel('K')
plt.ylabel('Silhouette Score')
plt.title('Silhouette Analysis')
plt.show()

print(f"Meilleur K: {K_range[np.argmax(silhouette_scores)]}")
print(f"Score: {max(silhouette_scores):.3f}")
```

**Interprétation Silhouette:**
- Score proche de 1: Clusters bien séparés
- Score ~0: Clusters qui se chevauchent
- Score négatif: Mauvais clustering

---

## 3. DBSCAN - Outlier Detection

### 3.1 Théorie

**Principe:** Clustering basé sur la densité. Identifie:
- **Core points:** Points avec ≥ min_samples voisins dans un rayon eps
- **Border points:** Points dans le voisinage d'un core point
- **Noise points:** Points ni core ni border (outliers)

**Avantages vs KMeans:**
- Pas besoin de spécifier le nombre de clusters
- Détecte les outliers nativement
- Gère les clusters de forme arbitraire

### 3.2 Application: Détection d'Anomalies

```python
from sklearn.cluster import DBSCAN

# Features (returns extrêmes, vol spikes)
features = ['return', 'volatility_change', 'volume_spike']

X = df[features].dropna()
X_scaled = scaler.fit_transform(X)

# DBSCAN
# eps: rayon de voisinage (critique!)
# min_samples: nombre minimum de voisins pour être un core point
dbscan = DBSCAN(eps=0.5, min_samples=5, metric='euclidean')

labels = dbscan.fit_predict(X_scaled)

# -1 = noise/outliers
df['dbscan_label'] = np.nan
df.loc[X.index, 'dbscan_label'] = labels

# Statistiques
n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
n_noise = list(labels).count(-1)

print(f"Nombre de clusters: {n_clusters}")
print(f"Nombre d'outliers: {n_noise} ({n_noise/len(labels):.1%})")

# Analyse des outliers
outliers = df[df['dbscan_label'] == -1]
print("\nCaractéristiques des outliers:")
print(outliers[features].describe())
```

### 3.3 Tuning de eps

```python
from sklearn.neighbors import NearestNeighbors

# K-distance graph pour trouver eps optimal
k = 5  # min_samples
nbrs = NearestNeighbors(n_neighbors=k)
nbrs.fit(X_scaled)

distances, indices = nbrs.kneighbors(X_scaled)
distances = np.sort(distances[:, -1])  # Distance au k-ième voisin

plt.plot(distances)
plt.xlabel('Points triés')
plt.ylabel(f'Distance au {k}-ième voisin')
plt.title('K-Distance Graph')
plt.show()

# Le "coude" du graph = eps optimal
# Typiquement entre 0.3 et 1.0 selon les données
```

### 3.4 Trading Applications

**Outliers = Opportunités ou Risques:**

| Type d'Outlier | Cause Possible | Action |
|----------------|----------------|--------|
| Volume spike extrême | News, announcement | Vérifier news, potentiel momentum |
| Volatility spike | Crash, flash crash | Réduire exposition, hedging |
| Return extrême | Liquidation cascade | Opportunité mean reversion |
| Correlation break | Decouplage temporaire | Pairs trading opportunity |

---

## 4. PCA - Dimensionality Reduction

### 4.1 Théorie

**Principe:** Trouver les directions (composantes principales) de variance maximale dans les données.

**Objectifs:**
- Réduire la dimensionnalité (moins de features)
- Éliminer la corrélation entre features
- Extraire les facteurs latents (drivers sous-jacents)

**Mathématiques:**
1. Centrer les données (moyenne = 0)
2. Calculer la matrice de covariance
3. Décomposition en valeurs/vecteurs propres
4. Projeter sur les k premières composantes

### 4.2 Application: Factor Analysis

```python
from sklearn.decomposition import PCA

# Features (potentiellement corrélées)
features = ['rsi', 'macd', 'bb_pct_b', 'vol_20d', 'skew_20d', 
            'return_5d', 'return_10d', 'return_20d']

X = df[features].dropna()
X_scaled = scaler.fit_transform(X)

# PCA
pca = PCA(n_components=0.95)  # Garder 95% de la variance
X_pca = pca.fit_transform(X_scaled)

print(f"Nombre de composantes: {pca.n_components_}")
print(f"Variance expliquée: {pca.explained_variance_ratio_.sum():.1%}")

# Variance expliquée par composante
explained_var = pd.DataFrame({
    'component': range(1, len(pca.explained_variance_ratio_) + 1),
    'variance_explained': pca.explained_variance_ratio_,
    'cumulative': pca.explained_variance_ratio_.cumsum()
})
print(explained_var)
```

**Sortie typique:**
```
   component  variance_explained  cumulative
1          1              0.423       0.423
2          2              0.287       0.710
3          3              0.152       0.862
4          4              0.089       0.951
```

**Interprétation:**
- **PC1 (42.3%):** Facteur "trend" (corrélé avec returns, MACD)
- **PC2 (28.7%):** Facteur "mean reversion" (corrélé avec RSI, BB)
- **PC3 (15.2%):** Facteur "volatility" (corrélé avec vol, skew)
- **PC4 (8.9%):** Facteur "momentum court terme"

### 4.3 Loadings (Interprétation des Composantes)

```python
# Loadings = contribution de chaque feature aux composantes
loadings = pd.DataFrame(
    pca.components_.T,
    columns=[f'PC{i+1}' for i in range(pca.n_components_)],
    index=features
)

print("Loadings:")
print(loadings.round(3))

# Visualisation
plt.figure(figsize=(10, 6))
plt.imshow(loadings, cmap='RdBu', vmin=-1, vmax=1)
plt.colorbar(label='Loading')
plt.xticks(range(len(loadings.columns)), loadings.columns)
plt.yticks(range(len(loadings.index)), loadings.index)
plt.title('PCA Loadings Heatmap')
plt.tight_layout()
plt.show()
```

### 4.4 Application: Réduction de Bruit

```python
# Utiliser les composantes comme features pour ML
from sklearn.ensemble import RandomForestClassifier

# Features originales
X_train, X_test = train_test_split(X_scaled, test_size=0.2, shuffle=False)
y_train, y_test = y.loc[X_train.index], y.loc[X_test.index]

# Avec PCA
pca = PCA(n_components=5)
X_train_pca = pca.fit_transform(X_train)
X_test_pca = pca.transform(X_test)

# Sans PCA (baseline)
rf_original = RandomForestClassifier(n_estimators=100, random_state=42)
rf_original.fit(X_train, y_train)
acc_original = rf_original.score(X_test, y_test)

# Avec PCA
rf_pca = RandomForestClassifier(n_estimators=100, random_state=42)
rf_pca.fit(X_train_pca, y_train)
acc_pca = rf_pca.score(X_test_pca, y_test)

print(f"Accuracy sans PCA: {acc_original:.3f}")
print(f"Accuracy avec PCA: {acc_pca:.3f}")
```

**Avantages PCA:**
- Réduit overfitting (moins de features)
- Élimine multicollinéarité
- Plus rapide à entraîner
- Interprétabilité des facteurs latents

**Inconvénients:**
- Perte d'interprétabilité directe des features
- Composantes = combinaisons linéaires (pas toujours meaningful)
- Suppose relations linéaires

---

## 5. Analyse en Composantes Principales pour Assets

### 5.1 Correlation Matrix et PCA Multi-Assets

```python
# Returns de multiple assets
assets = ['BTC', 'ETH', 'GOLD', 'SPY', 'TLT']
returns_df = pd.DataFrame({asset: prices[asset].pct_change() for asset in assets})

# Matrice de corrélation
corr_matrix = returns_df.corr()

plt.figure(figsize=(8, 6))
sns.heatmap(corr_matrix, annot=True, cmap='RdBu', vmin=-1, vmax=1, center=0)
plt.title('Correlation Matrix')
plt.tight_layout()
plt.show()

# PCA
pca = PCA(n_components=2)
returns_scaled = scaler.fit_transform(returns_df.dropna())
pca_result = pca.fit_transform(returns_scaled)

# Plot des assets dans l'espace PCA
plt.figure(figsize=(8, 6))
for i, asset in enumerate(assets):
    plt.scatter(pca_result[:, 0], pca_result[:, 1], alpha=0.5)
    plt.annotate(asset, (pca_result[i, 0], pca_result[i, 1]))

plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%})')
plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%})')
plt.title('Assets in PCA Space')
plt.grid(True, alpha=0.3)
plt.show()
```

### 5.2 Facteurs de Risque Latents

**Interprétation typique:**
- **PC1:** "Risk-on / Risk-off" (tous les assets risqués corrélés)
- **PC2:** "Inflation hedge" (or vs autres assets)
- **PC3:** "Duration" (bonds vs equities)

---

## 6. Combinaison avec ML Supervised

### 6.1 Pipeline: Unsupervised → Supervised

```python
# Étape 1: Regime detection (KMeans)
kmeans = KMeans(n_clusters=3, random_state=42)
df['regime'] = kmeans.fit_predict(X_scaled)

# Étape 2: Entraîner un modèle par régime
models_by_regime = {}

for regime in range(3):
    regime_mask = df['regime'] == regime
    X_regime = df.loc[regime_mask, features]
    y_regime = y.loc[regime_mask]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X_regime, y_regime, test_size=0.2, shuffle=False
    )
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    models_by_regime[regime] = {
        'model': model,
        'train_acc': model.score(X_train, y_train),
        'test_acc': model.score(X_test, y_test),
        'n_samples': len(y_regime)
    }
    
    print(f"Régime {regime}: Train={model.score(X_train, y_train):.2%}, "
          f"Test={model.score(X_test, y_test):.2%}, "
          f"N={len(y_regime)}")

# Étape 3: Prédiction adaptative
# 1. Identifier le régime actuel
current_regime = kmeans.predict(X_scaled[-1].reshape(1, -1))[0]

# 2. Utiliser le modèle du régime actuel
model_current = models_by_regime[current_regime]['model']
prediction = model_current.predict(X_scaled[-1].reshape(1, -1))
```

### 6.2 Performance par Régime

| Régime | % du temps | Accuracy Modèle | Stratégie Optimale |
|--------|------------|-----------------|-------------------|
| Bull | 35% | 58% | Momentum |
| Bear | 30% | 52% | Defensive / Short |
| Range | 35% | 61% | Mean Reversion |

**Insight:** Les modèles spécialisés par régime surpassent un modèle global.

---

## 7. Best Practices

### ✅ DO

1. **Toujours scaler** les données avant KMeans/PCA
2. **Valider le nombre de clusters** (elbow + silhouette)
3. **Interpréter les régimes** a posteriori (stats descriptives)
4. **Combiner avec supervised ML** pour meilleures performances
5. **Monitor regime shifts** en production (changement de stratégie)

### ❌ DON'T

1. **Utiliser KMeans sur données non-scalées** (features dominent par scale)
2. **Choisir K arbitrairement** (toujours tester elbow/silhouette)
3. **Ignorer les outliers** (DBSCAN peut les identifier)
4. **Over-interpréter les composantes PCA** (ce sont des combinaisons linéaires)
5. **Utiliser PCA sur données non-linéaires** (considérer Kernel PCA)

---

## 8. Code Sample

Voir `learning/code/ml_unsupervised.py` pour l'implémentation complète.

**Fonctionnalités:**
- KMeans regime detection avec silhouette analysis
- DBSCAN outlier detection
- PCA avec loadings et variance expliquée
- Visualisations complètes (elbow, heatmap, PCA scatter)

---

## 9. Prochaines Étapes

- [x] ML Unsupervised documenté
- [ ] Semaine 12: Walk-Forward Validation (approfondissement)
- [ ] Semaine 13: Mean Reversion Avancée (Ornstein-Uhlenbeck)
- [ ] Intégration regime detection dans pipeline de trading

---

**Références:**
- López de Prado, M. (2018). "Advances in Financial Machine Learning" - Chapitre 10
- Scikit-learn: Clustering and Decomposition documentation
- "Pattern Recognition and Machine Learning" - Bishop
- Quantitative Researcher's Toolkit: Regime Detection
