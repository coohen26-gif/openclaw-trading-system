"""
Feature Engineering Pipeline pour Trading ML
Semaine 09 - Master 2 ML pour Trading

Génère des features techniques, statistiques, et calcule l'importance (SHAP/Permutation)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 1. GÉNÉRATION DE DONNÉES SIMULÉES (pour démo)
# ============================================================================

def generate_price_data(n_days=500, seed=42):
    """Génère des prix simulés avec caractéristiques réalistes"""
    np.random.seed(seed)
    
    # Prix initial
    initial_price = 50000
    
    # Returns avec clustering de volatilité (GARCH-like)
    n_obs = n_days * 24  # Données hourly
    
    # Volatilité time-varying
    vol_base = 0.002
    vol_persistence = 0.9
    vol_shocks = np.random.randn(n_obs) * 0.0005
    volatility = np.zeros(n_obs)
    volatility[0] = vol_base
    
    for t in range(1, n_obs):
        volatility[t] = vol_persistence * volatility[t-1] + (1 - vol_persistence) * vol_base + vol_shocks[t]
    
    # Returns avec momentum et mean-reversion
    returns = np.random.randn(n_obs) * volatility
    
    # Ajout d'un peu de momentum
    returns += 0.05 * np.roll(returns, 1)
    returns[0] = 0
    
    # Prix
    prices = initial_price * np.cumprod(1 + returns)
    
    # High/Low pour ATR
    high = prices * (1 + np.abs(np.random.randn(n_obs)) * volatility)
    low = prices * (1 - np.abs(np.random.randn(n_obs)) * volatility)
    
    # Volume
    volume = np.random.lognormal(mean=10, sigma=1, size=n_obs) * 1e6
    
    # Create DataFrame
    dates = pd.date_range(start='2025-01-01', periods=n_obs, freq='h')
    df = pd.DataFrame({
        'open': prices,
        'high': high,
        'low': low,
        'close': prices,
        'volume': volume
    }, index=dates)
    
    return df

# ============================================================================
# 2. TECHNICAL FEATURES
# ============================================================================

def calculate_rsi(prices, period=14):
    """Relative Strength Index"""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """MACD avec ligne de signal et histogramme"""
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_atr(high, low, close, period=14):
    """Average True Range"""
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    return atr

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Bandes de Bollinger avec %B et Bandwidth"""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    pct_b = (prices - lower) / (upper - lower)
    bandwidth = (upper - lower) / sma
    return upper, lower, pct_b, bandwidth

def calculate_trend_features(prices):
    """Features de trend basées sur les MAs"""
    ma_20 = prices.rolling(20).mean()
    ma_50 = prices.rolling(50).mean()
    ma_200 = prices.rolling(200).mean()
    
    # Pentes
    ma_20_slope = ma_20.diff(5) / ma_20.shift(5)
    ma_50_slope = ma_50.diff(5) / ma_50.shift(5)
    
    # Distance aux MAs
    dist_ma_20 = (prices - ma_20) / ma_20
    dist_ma_200 = (prices - ma_200) / ma_200
    
    # Alignment
    ma_alignment = ((ma_20 > ma_50) & (ma_50 > ma_200)).astype(int)
    
    return ma_20_slope, ma_50_slope, dist_ma_20, dist_ma_200, ma_alignment

# ============================================================================
# 3. STATISTICAL FEATURES
# ============================================================================

def calculate_statistical_features(prices, windows=[5, 10, 20, 60]):
    """Returns, volatilité, skewness, kurtosis sur fenêtres multiples"""
    features = pd.DataFrame(index=prices.index)
    returns = prices.pct_change()
    
    for w in windows:
        features[f'return_{w}d'] = returns.rolling(w).mean()
        features[f'vol_{w}d'] = returns.rolling(w).std() * np.sqrt(252 * 24)  # Annualisée hourly
        features[f'skew_{w}d'] = returns.rolling(w).skew()
        features[f'kurt_{w}d'] = returns.rolling(w).kurt()
        features[f'sharpe_{w}d'] = features[f'return_{w}d'] / (features[f'vol_{w}d'] / np.sqrt(252 * 24))
    
    return features

def calculate_mean_reversion_features(prices, lags=[1, 5, 10]):
    """Autocorrélation et Hurst exponent"""
    returns = prices.pct_change()
    features = pd.DataFrame(index=prices.index)
    
    for lag in lags:
        # Autocorrélation
        features[f'acf_lag{lag}'] = returns.rolling(60).apply(
            lambda x: x.autocorr(lag=lag) if len(x) > lag else np.nan
        )
    
    return features

# ============================================================================
# 4. FEATURE IMPORTANCE
# ============================================================================

def calculate_permutation_importance(model, X_test, y_test, n_repeats=10, random_state=42):
    """Permutation importance"""
    from sklearn.inspection import permutation_importance
    
    result = permutation_importance(
        model, X_test, y_test,
        n_repeats=n_repeats,
        random_state=random_state,
        scoring='accuracy',
        n_jobs=-1
    )
    
    importance_df = pd.DataFrame({
        'feature': X_test.columns,
        'importance_mean': result.importances_mean,
        'importance_std': result.importances_std
    }).sort_values('importance_mean', ascending=False)
    
    return importance_df

def calculate_shap_importance(model, X_train, X_test, feature_names):
    """SHAP values pour l'importance des features"""
    try:
        import shap
        from sklearn.ensemble import RandomForestClassifier
        
        # Explainer
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test)
        
        # Importance
        shap_importance = pd.DataFrame({
            'feature': feature_names,
            'shap_importance': np.abs(shap_values).mean(axis=0)
        }).sort_values('shap_importance', ascending=False)
        
        return shap_importance, shap_values
    
    except ImportError:
        print("SHAP non installé: pip install shap")
        return None, None

# ============================================================================
# 5. PIPELINE COMPLET
# ============================================================================

def build_feature_pipeline(df):
    """Construit toutes les features"""
    features = pd.DataFrame(index=df.index)
    
    # Technical
    features['rsi_14'] = calculate_rsi(df['close'], 14)
    macd, signal, hist = calculate_macd(df['close'])
    features['macd'] = macd
    features['macd_histogram'] = hist
    features['atr_14'] = calculate_atr(df['high'], df['low'], df['close'], 14)
    
    bb_upper, bb_lower, pct_b, bandwidth = calculate_bollinger_bands(df['close'])
    features['bb_pct_b'] = pct_b
    features['bb_bandwidth'] = bandwidth
    
    ma_20_slope, ma_50_slope, dist_20, dist_200, alignment = calculate_trend_features(df['close'])
    features['ma_20_slope'] = ma_20_slope
    features['ma_50_slope'] = ma_50_slope
    features['dist_ma_20'] = dist_20
    features['dist_ma_200'] = dist_200
    features['ma_alignment'] = alignment
    
    # Statistical
    stat_features = calculate_statistical_features(df['close'], windows=[5, 10, 20])
    for col in stat_features.columns:
        features[col] = stat_features[col]
    
    # Mean reversion
    mr_features = calculate_mean_reversion_features(df['close'], lags=[1, 5])
    for col in mr_features.columns:
        features[col] = mr_features[col]
    
    # Volume features
    features['volume_ma_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
    features['volume_change'] = df['volume'].pct_change()
    
    # Target: Direction future (return à 24h)
    features['target'] = (df['close'].shift(-24) > df['close']).astype(int)
    
    return features

def run_feature_engineering():
    """Exécute le pipeline complet"""
    print("=" * 60)
    print("FEATURE ENGINEERING PIPELINE - SEMAINE 09")
    print("=" * 60)
    
    # Génération données
    print("\n[1/4] Génération des données simulées...")
    df = generate_price_data(n_days=500)
    print(f"      → {len(df)} observations générées ({df.index[0].date()} → {df.index[-1].date()})")
    
    # Feature engineering
    print("\n[2/4] Calcul des features...")
    features = build_feature_pipeline(df)
    
    # Drop NaN
    features = features.dropna()
    print(f"      → {len(features.columns)} features créées")
    print(f"      → {len(features)} observations après cleanup")
    
    # Split train/test
    print("\n[3/4] Split train/test (80/20)...")
    split_idx = int(len(features) * 0.8)
    
    feature_cols = [c for c in features.columns if c != 'target']
    X = features[feature_cols]
    y = features['target']
    
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    print(f"      → Train: {len(X_train)} samples")
    print(f"      → Test: {len(X_test)} samples")
    
    # Model training
    print("\n[4/4] Training Random Forest + Feature Importance...")
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    
    # Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    X_train_scaled = pd.DataFrame(X_train_scaled, columns=feature_cols, index=X_train.index)
    X_test_scaled = pd.DataFrame(X_test_scaled, columns=feature_cols, index=X_test.index)
    
    # Model
    rf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42, n_jobs=-1)
    rf.fit(X_train_scaled, y_train)
    
    # Performance
    train_acc = rf.score(X_train_scaled, y_train)
    test_acc = rf.score(X_test_scaled, y_test)
    print(f"\n      → Train Accuracy: {train_acc:.2%}")
    print(f"      → Test Accuracy: {test_acc:.2%}")
    
    # Feature Importance (built-in)
    print("\n" + "=" * 60)
    print("TOP 15 FEATURES BY IMPORTANCE (Random Forest)")
    print("=" * 60)
    
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': rf.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for i, row in importance_df.head(15).iterrows():
        print(f"  {row['feature']:<25} {row['importance']:.4f}")
    
    # Permutation importance
    print("\n" + "=" * 60)
    print("PERMUTATION IMPORTANCE (TOP 10)")
    print("=" * 60)
    
    perm_importance = calculate_permutation_importance(rf, X_test_scaled, y_test, n_repeats=5)
    for i, row in perm_importance.head(10).iterrows():
        print(f"  {row['feature']:<25} {row['importance_mean']:.4f} (±{row['importance_std']:.4f})")
    
    # Visualisation
    print("\n" + "=" * 60)
    print("GÉNÉRATION DES VISUALISATIONS...")
    print("=" * 60)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Feature importance
    ax1 = axes[0, 0]
    top_features = importance_df.head(15)
    ax1.barh(range(len(top_features)), top_features['importance'].values)
    ax1.set_yticks(range(len(top_features)))
    ax1.set_yticklabels(top_features['feature'].values)
    ax1.invert_yaxis()
    ax1.set_xlabel('Importance')
    ax1.set_title('Top 15 Features (Random Forest)')
    
    # 2. Price evolution
    ax2 = axes[0, 1]
    ax2.plot(df.index, df['close'], label='Price', linewidth=0.5)
    ax2.set_title('Price Evolution (Simulated)')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Price')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. RSI evolution
    ax3 = axes[1, 0]
    ax3.plot(features.index, features['rsi_14'], label='RSI(14)', color='purple', linewidth=0.5)
    ax3.axhline(70, color='red', linestyle='--', alpha=0.5, label='Overbought')
    ax3.axhline(30, color='green', linestyle='--', alpha=0.5, label='Oversold')
    ax3.set_title('RSI Evolution')
    ax3.set_xlabel('Date')
    ax3.set_ylabel('RSI')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Volatility
    ax4 = axes[1, 1]
    ax4.plot(features.index, features['vol_20d'], label='Volatility (20d)', color='orange', linewidth=0.5)
    ax4.set_title('Rolling Volatility (Annualized)')
    ax4.set_xlabel('Date')
    ax4.set_ylabel('Volatility')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/root/.openclaw/workspace/learning/code/feature_engineering_output.png', dpi=150)
    print(f"      → Visualisation sauvegardée: feature_engineering_output.png")
    
    print("\n" + "=" * 60)
    print("✅ FEATURE ENGINEERING COMPLETE")
    print("=" * 60)
    
    return features, importance_df, rf

if __name__ == "__main__":
    features, importance, model = run_feature_engineering()
