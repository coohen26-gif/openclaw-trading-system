"""
ML Unsupervised pour Trading - Semaine 11
KMeans (regime detection), DBSCAN (outliers), PCA (dimensionality reduction)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.neighbors import NearestNeighbors

# ============================================================================
# 1. GÉNÉRATION DE DONNÉES AVEC RÉGIMES
# ============================================================================

def generate_regime_data(n_days=500, seed=42):
    """Génère des données avec 3 régimes de marché distincts"""
    np.random.seed(seed)
    
    n_obs = n_days * 24
    
    # Créer 3 régimes séquentiels
    regime_sequence = np.zeros(n_obs)
    regime_length = n_obs // 3
    
    # Régime 1: Bull (returns positifs, vol modérée)
    regime_sequence[:regime_length] = 0
    
    # Régime 2: Bear (returns négatifs, vol élevée)
    regime_sequence[regime_length:2*regime_length] = 1
    
    # Régime 3: Range (returns neutres, vol basse)
    regime_sequence[2*regime_length:] = 2
    
    # Génère returns selon régime
    returns = np.zeros(n_obs)
    volatility = np.zeros(n_obs)
    
    for i in range(n_obs):
        regime = regime_sequence[i]
        
        if regime == 0:  # Bull
            mu, sigma = 0.0003, 0.0015
        elif regime == 1:  # Bear
            mu, sigma = -0.0004, 0.0030
        else:  # Range
            mu, sigma = 0.0000, 0.0010
        
        volatility[i] = sigma
        returns[i] = np.random.randn() * sigma + mu
    
    # Prix
    prices = 50000 * np.cumprod(1 + returns)
    
    # Volume (plus élevé en bear market)
    base_volume = 1e6
    volume = base_volume * np.exp(np.random.randn(n_obs) * 0.5)
    volume *= (1 + regime_sequence * 0.3)  # Volume ↑ en bear
    
    # Features dérivées
    dates = pd.date_range(start='2025-01-01', periods=n_obs, freq='h')
    df = pd.DataFrame({
        'close': prices,
        'volume': volume,
        'true_regime': regime_sequence
    }, index=dates)
    
    # Return rolling
    df['return'] = df['close'].pct_change()
    df['volatility'] = df['return'].rolling(24).std()
    df['skewness'] = df['return'].rolling(48).skew()
    df['volume_change'] = df['volume'].pct_change()
    
    df = df.dropna()
    
    return df

# ============================================================================
# 2. KMEANS REGIME DETECTION
# ============================================================================

def kmeans_regime_detection(df, features, k_range=range(2, 7)):
    """KMeans clustering avec elbow et silhouette analysis"""
    
    print("\n" + "=" * 60)
    print("KMEANS REGIME DETECTION")
    print("=" * 60)
    
    X = df[features].dropna()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Elbow method
    inertias = []
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X_scaled)
        inertias.append(kmeans.inertia_)
    
    # Silhouette scores
    silhouette_scores_list = []
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, labels)
        silhouette_scores_list.append(score)
    
    # Meilleur K
    best_k = k_range[np.argmax(silhouette_scores_list)]
    print(f"\n[1/3] Analyse silhouette...")
    print(f"      → Meilleur K: {best_k}")
    print(f"      → Score: {max(silhouette_scores_list):.3f}")
    
    # Training avec meilleur K
    print(f"\n[2/3] Training KMeans avec K={best_k}...")
    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)
    
    df['kmeans_regime'] = np.nan
    df.loc[X.index, 'kmeans_regime'] = labels
    
    # Stats par régime
    print(f"\n[3/3] Statistiques par régime détecté:")
    regime_stats = df.groupby('kmeans_regime')[features].agg(['mean', 'std', 'count'])
    
    for regime in range(best_k):
        if regime in df['kmeans_regime'].values:
            mask = df['kmeans_regime'] == regime
            count = mask.sum()
            pct = count / len(df) * 100
            ret_mean = df.loc[mask, 'return'].mean()
            vol_mean = df.loc[mask, 'volatility'].mean()
            
            # Label automatique
            if ret_mean > 0.0001 and vol_mean < 0.002:
                label = "Bull"
            elif ret_mean < -0.0001 and vol_mean >= 0.002:
                label = "Bear"
            else:
                label = "Range"
            
            print(f"      → Régime {regime} ({label}): {count} obs ({pct:.1f}%)")
            print(f"         Return mean: {ret_mean:.6f}, Vol mean: {vol_mean:.6f}")
    
    # Visualisation
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Elbow plot
    ax1 = axes[0, 0]
    ax1.plot(k_range, inertias, 'bo-', linewidth=2, markersize=8)
    ax1.set_xlabel('Nombre de Clusters (K)')
    ax1.set_ylabel('Inertie')
    ax1.set_title('Elbow Method')
    ax1.grid(True, alpha=0.3)
    
    # 2. Silhouette plot
    ax2 = axes[0, 1]
    ax2.plot(k_range, silhouette_scores_list, 'ro-', linewidth=2, markersize=8)
    ax2.set_xlabel('Nombre de Clusters (K)')
    ax2.set_ylabel('Silhouette Score')
    ax2.set_title('Silhouette Analysis')
    ax2.axvline(best_k, color='green', linestyle='--', label=f'Best K={best_k}')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Regimes over time
    ax3 = axes[1, 0]
    ax3.plot(df.index, df['kmeans_regime'], linewidth=0.5, alpha=0.7)
    ax3.set_xlabel('Date')
    ax3.set_ylabel('Régime')
    ax3.set_title('Régimes Détectés (KMeans)')
    ax3.set_yticks(range(best_k))
    ax3.grid(True, alpha=0.3)
    
    # 4. Price with regime coloring
    ax4 = axes[1, 1]
    for regime in range(best_k):
        mask = df['kmeans_regime'] == regime
        ax4.scatter(df.loc[mask].index, df.loc[mask, 'close'], 
                   s=1, alpha=0.5, label=f'Régime {regime}')
    ax4.set_xlabel('Date')
    ax4.set_ylabel('Price')
    ax4.set_title('Price par Régime')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/root/.openclaw/workspace/learning/code/kmeans_regime_output.png', dpi=150)
    print(f"\n      → Visualisation sauvegardée: kmeans_regime_output.png")
    
    return kmeans, best_k

# ============================================================================
# 3. DBSCAN OUTLIER DETECTION
# ============================================================================

def dbscan_outlier_detection(df, features, eps=0.5, min_samples=5):
    """DBSCAN pour détection d'outliers"""
    
    print("\n" + "=" * 60)
    print("DBSCAN OUTLIER DETECTION")
    print("=" * 60)
    
    X = df[features].dropna()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # K-distance graph pour eps optimal
    print(f"\n[1/3] K-distance graph pour eps optimal...")
    k = min_samples
    nbrs = NearestNeighbors(n_neighbors=k)
    nbrs.fit(X_scaled)
    distances, indices = nbrs.kneighbors(X_scaled)
    distances = np.sort(distances[:, -1])
    
    # DBSCAN
    print(f"[2/3] Training DBSCAN (eps={eps}, min_samples={min_samples})...")
    dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='euclidean')
    labels = dbscan.fit_predict(X_scaled)
    
    df['dbscan_label'] = np.nan
    df.loc[X.index, 'dbscan_label'] = labels
    
    # Stats
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)
    
    print(f"[3/3] Résultats:")
    print(f"      → Nombre de clusters: {n_clusters}")
    print(f"      → Nombre d'outliers: {n_noise} ({n_noise/len(labels):.1%})")
    
    # Analyse outliers
    if n_noise > 0:
        outliers = df[df['dbscan_label'] == -1]
        print(f"\n      Caractéristiques des outliers:")
        for feat in features:
            outlier_mean = outliers[feat].mean()
            overall_mean = df[feat].mean()
            print(f"         {feat}: {outlier_mean:.6f} (vs {overall_mean:.6f})")
    
    # Visualisation
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # 1. K-distance graph
    ax1 = axes[0]
    ax1.plot(distances)
    ax1.set_xlabel('Points triés')
    ax1.set_ylabel(f'Distance au {k}-ième voisin')
    ax1.set_title('K-Distance Graph (pour eps optimal)')
    ax1.grid(True, alpha=0.3)
    ax1.axhline(eps, color='red', linestyle='--', label=f'eps={eps}')
    ax1.legend()
    
    # 2. Outliers visualization (2D projection)
    ax2 = axes[1]
    
    # PCA pour visualisation 2D
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    # Normal points
    normal_mask = labels != -1
    ax2.scatter(X_pca[normal_mask, 0], X_pca[normal_mask, 1], 
               s=1, alpha=0.3, label='Normal', c='blue')
    
    # Outliers
    outlier_mask = labels == -1
    ax2.scatter(X_pca[outlier_mask, 0], X_pca[outlier_mask, 1], 
               s=5, alpha=0.8, label='Outliers', c='red')
    
    ax2.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%})')
    ax2.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%})')
    ax2.set_title('Outliers Detection (PCA 2D)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/root/.openclaw/workspace/learning/code/dbscan_outliers_output.png', dpi=150)
    print(f"\n      → Visualisation sauvegardée: dbscan_outliers_output.png")
    
    return dbscan, n_noise

# ============================================================================
# 4. PCA DIMENSIONALITY REDUCTION
# ============================================================================

def pca_analysis(df, features, variance_threshold=0.95):
    """PCA pour réduction de dimensionnalité"""
    
    print("\n" + "=" * 60)
    print("PCA DIMENSIONALITY REDUCTION")
    print("=" * 60)
    
    X = df[features].dropna()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # PCA avec variance threshold
    print(f"\n[1/3] PCA avec {variance_threshold*100:.0f}% de variance à expliquer...")
    pca = PCA(n_components=variance_threshold)
    X_pca = pca.fit_transform(X_scaled)
    
    n_components = pca.n_components_
    total_variance = pca.explained_variance_ratio_.sum()
    
    print(f"[2/3] Résultats:")
    print(f"      → Nombre de composantes: {n_components}")
    print(f"      → Variance expliquée totale: {total_variance:.1%}")
    
    # Variance par composante
    print(f"\n      Variance par composante:")
    for i, var in enumerate(pca.explained_variance_ratio_):
        cum_var = pca.explained_variance_ratio_[:i+1].sum()
        print(f"         PC{i+1}: {var:.1%} (cumul: {cum_var:.1%})")
    
    # Loadings
    print(f"\n[3/3] Loadings (contribution des features):")
    loadings = pd.DataFrame(
        pca.components_.T,
        columns=[f'PC{i+1}' for i in range(n_components)],
        index=features
    )
    
    print(loadings.round(3).to_string())
    
    # Visualisation
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Variance expliquée
    ax1 = axes[0, 0]
    ax1.bar(range(1, n_components+1), pca.explained_variance_ratio_, 
           color='steelblue', alpha=0.7)
    ax1.set_xlabel('Composante Principale')
    ax1.set_ylabel('Variance Expliquée')
    ax1.set_title('Variance Explained by PC')
    ax1.set_xticks(range(1, n_components+1))
    ax1.grid(True, alpha=0.3, axis='y')
    
    # 2. Cumulative variance
    ax2 = axes[0, 1]
    ax2.plot(range(1, n_components+1), pca.explained_variance_ratio_.cumsum(), 
            'bo-', linewidth=2, markersize=8)
    ax2.axhline(variance_threshold, color='red', linestyle='--', 
               label=f'Seuil ({variance_threshold*100:.0f}%)')
    ax2.set_xlabel('Composante Principale')
    ax2.set_ylabel('Variance Cumulée')
    ax2.set_title('Cumulative Variance')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Loadings heatmap
    ax3 = axes[1, 0]
    im = ax3.imshow(loadings, cmap='RdBu', vmin=-1, vmax=1, aspect='auto')
    ax3.set_xticks(range(n_components))
    ax3.set_xticklabels([f'PC{i+1}' for i in range(n_components)])
    ax3.set_yticks(range(len(features)))
    ax3.set_yticklabels(features)
    plt.colorbar(im, ax=ax3, label='Loading')
    ax3.set_title('PCA Loadings Heatmap')
    
    # 4. Data in PCA space
    ax4 = axes[1, 1]
    if n_components >= 2:
        scatter = ax4.scatter(X_pca[:, 0], X_pca[:, 1], 
                             c=df.loc[X.index, 'kmeans_regime'] if 'kmeans_regime' in df.columns else None,
                             alpha=0.5, s=1, cmap='viridis')
        ax4.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%})')
        ax4.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%})')
        ax4.set_title('Data in PCA Space')
        ax4.grid(True, alpha=0.3)
        if 'kmeans_regime' in df.columns:
            plt.colorbar(scatter, ax=ax4, label='Régime')
    else:
        ax4.hist(X_pca[:, 0], bins=50, alpha=0.7)
        ax4.set_xlabel('PC1')
        ax4.set_ylabel('Count')
        ax4.set_title('Distribution PC1')
        ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/root/.openclaw/workspace/learning/code/pca_analysis_output.png', dpi=150)
    print(f"\n      → Visualisation sauvegardée: pca_analysis_output.png")
    
    return pca, loadings

# ============================================================================
# 5. PIPELINE COMPLET
# ============================================================================

def run_unsupervised_pipeline():
    """Exécute le pipeline complet"""
    
    print("=" * 70)
    print("ML UNSUPERVISED POUR TRADING - SEMAINE 11")
    print("=" * 70)
    
    # Données
    print("\n[INIT] Génération des données avec régimes...")
    df = generate_regime_data(n_days=500)
    print(f"      → {len(df)} observations générées")
    
    # Features
    clustering_features = ['return', 'volatility', 'skewness', 'volume_change']
    
    # KMeans
    kmeans, best_k = kmeans_regime_detection(df, clustering_features)
    
    # DBSCAN
    dbscan, n_outliers = dbscan_outlier_detection(df, clustering_features, eps=0.5, min_samples=5)
    
    # PCA
    pca, loadings = pca_analysis(df, clustering_features, variance_threshold=0.95)
    
    print("\n" + "=" * 70)
    print("✅ ML UNSUPERVISED COMPLETE")
    print("=" * 70)
    
    return df, kmeans, dbscan, pca

if __name__ == "__main__":
    df, kmeans, dbscan, pca = run_unsupervised_pipeline()
