# AUDIT COMPLET SAIYAN V0.2 - État des lieux réel

**Date:** 2026-05-26  
**Auditeur:** Subagent OpenClaw  
**Objectif:** Vérité brute avant reconstruction v0.3

---

## 1. FICHIERS QUI EXISTENT VRAIMENT

### v0.2 Core Files
| Fichier | Existe | Lines | Status |
|---------|--------|-------|--------|
| `system-saiyan/v0.2/main.py` | ✅ | ~350 | STUB DATA |
| `system-saiyan/v0.2/strategies/momentum_hmm.py` | ✅ | ~450 | FAUX HMM |
| `system-saiyan/v0.2/core/risk_monitor.py` | ✅ | ~430 | OK |
| `system-saiyan/v0.2/core/portfolio_allocator.py` | ✅ | ~400 | OK |
| `system-saiyan/v0.2/config.json` | ✅ | ~130 | INCOHÉRENT |

### Data Files
| Fichier | Existe | Lines | Period |
|---------|--------|-------|--------|
| `v0.2/data/btc_real_2020_2026.csv` | ✅ | 2301 | 2020-2026 (6 ans) |
| `v0.2/data/btc_realistic_2020_2026.csv` | ✅ | 2338 | 2020-2026 |
| `v0.2/data/btc_real_2020_2026_ohlcv.csv` | ✅ | 2301 | 2020-2026 |
| `v0.2/data/cache/BTC_USDT_1d_50.csv` | ✅ | 51 | 50 jours |
| `v0.2/data/cache/ETH_USDT_1d_50.csv` | ✅ | 51 | 50 jours |
| `v0.2/data/cache/SOL_USDT_1d_50.csv` | ✅ | 51 | 50 jours |
| `v0.2/data/cache/BTC_USDT_1d_100.csv` | ✅ | 101 | 100 jours |

### Learning Files
- **Notes:** 38 fichiers dans `learning/notes/` (semaine-01 à semaine-30)
- **Code:** 50+ fichiers dans `learning/code/`
- **Status reports:** 5 fichiers STATUS-*.md (mai 2026)

---

## 2. BUGS CRITICAL + HIGH

### 🚨 CRITICAL

#### 2.1 `main.py` - fetch_market_data() = FAKE DATA
**Lignes 140-165**
```python
# Generate synthetic data for testing
np.random.seed(hash(asset) % 2**32)
n_bars = limit

# Random walk with drift
returns = np.random.normal(0.0005, 0.03, n_bars)
prices = 50000 * np.cumprod(1 + returns)
```

**Problème:** Utilise `np.random` pour générer des prix synthétiques au lieu de:
1. Charger les CSV réels (`btc_real_2020_2026.csv`)
2. Appeler Binance API

**Impact:** Tous les tests/trades utilisent des données FAUSSES. Le système ne peut PAS fonctionner en production.

---

#### 2.2 `momentum_hmm.py` - PAS DE VRAI HMM
**Lignes 114-170: `detect_regime_simple()`**

```python
def detect_regime_simple(self, prices: pd.Series, volatility: pd.Series) -> Tuple[Regime, float]:
    """
    Simple regime detection based on returns and volatility.
    
    Rules:
    - Bull: momentum > 0, volatility < median
    - Bear: momentum < 0, volatility > median
    ...
    """
```

**Problème:** 
- **Aucun HMM réel** (pas de `hmmlearn`, pas de `GaussianHMM`, pas de fit/predict)
- Juste des **if/else déguisés** basés sur momentum vs median volatility
- Le nom "HMM" est un **mensonge** - c'est un simple rule-based classifier

**Code actuel (lignes 136-155):**
```python
if momentum > 0 and current_vol < vol_median:
    regime = Regime.BULL
    confidence = min(0.9, 0.6 + abs(momentum) * 10)
elif momentum < 0 and current_vol > vol_median:
    regime = Regime.BEAR
    confidence = min(0.9, 0.6 + abs(momentum) * 10)
elif abs(momentum) < momentum_threshold and current_vol < vol_median:
    regime = Regime.RANGE
    confidence = 0.7
elif momentum > 0 and current_vol >= vol_median:
    regime = Regime.VOLATILE_BULL
    confidence = min(0.85, 0.6 + (current_vol / vol_median - 1) * 0.3)
```

**Impact:** La stratégie s'appelle "Momentum+HMM" mais **HMM n'existe pas**. Les performances claimées (+55%, Sharpe 0.91) sont basées sur un fake HMM.

---

#### 2.3 `config.json` - INCOHÉRENCE Bear Regime
**Lignes 65-94 vs Lignes 200-206 dans momentum_hmm.py**

**Config dit (ligne 73-78):**
```json
"Bear": {
  "kelly_multiplier": 0.25,
  "position_pct": 6.25,    ← AUTORISE 6.25%
  "stop_loss_pct": 3.0,
  "take_profit_pct": 8.0,
  "max_holding_days": 3
}
```

**Code dit (lignes 200-206):**
```python
if regime == Regime.BEAR:
    # BEAR REGIME: NO TRADING (validated parameter)
    direction = "FLAT"
    confidence = 0.0
```

**Problème:** 
- Config autorise 6.25% position en Bear
- Code **interdit totalement** trading en Bear (FLAT)
- **Incohérence directe** entre config et implémentation

**Impact:** Si un utilisateur change la config pour autoriser Bear trading, **rien ne se passe** car le code hardcode FLAT.

---

### ⚠️ HIGH

#### 2.4 `risk_monitor.py` - VaR/CVaR fenêtre 30j VÉRIFIÉE ✅
**Lignes 105-142**

```python
def __init__(self, initial_capital: float, rolling_window: int = 30, ...):
    self.rolling_window = rolling_window
    ...
    if len(self.returns_history) > self.rolling_window:
        self.returns_history = self.returns_history[-self.rolling_window:]
```

**Status:** ✅ **CORRECT** - Utilise bien rolling_window=30 jours par défaut.

**Config (ligne 112):** `"rolling_window_days": 30` → **Respecté**

---

#### 2.5 `portfolio_allocator.py` - Risk Parity HARDCODÉ
**Lignes 64-68**

```python
DEFAULT_WEIGHTS = {
    'BTC': 0.52,
    'ETH': 0.28,
    'SOL': 0.20
}
```

**Problème:** 
- Les weights sont **hardcodés** dans le code
- La fonction `optimize_risk_parity()` (lignes 280-330) **existe mais n'est JAMAIS APPELÉE**
- Le système utilise les weights par défaut, pas une vraie optimisation Risk Parity

**Code qui n'est jamais utilisé (lignes 280-330):**
```python
def optimize_risk_parity(cov_matrix: pd.DataFrame) -> Dict[str, float]:
    """Calculate Risk Parity weights from covariance matrix."""
    # ... 50 lignes de code d'optimisation ...
```

**Impact:** Se dit "Risk Parity" mais utilise des weights **statiques** (52/28/20). Pas d'optimisation dynamique basée sur la covariance réelle des assets.

---

#### 2.6 `config.json` - Fees configurés vs appliqués
**Ligne 19:** `"trading_fee_pct": 0.1`  
**Ligne 89:** `"transaction_cost_bps": 10` (dans portfolio_allocator)

**Problème:**
- Config: 0.1% = 10 bps → **OK cohérent**
- MAIS: `transaction_cost_bps=10` est **hardcodé** dans `PortfolioAllocator.__init__()` (ligne 89 du code)
- La config **n'est pas lue** pour ce paramètre

**Code (ligne 89):**
```python
self.transaction_cost_bps = transaction_cost_bps  # Default 10, pas lu depuis config
```

**Impact:** Si utilisateur change `transaction_cost_bps` dans config.json, **rien ne se passe**.

---

## 3. FONCTIONS QUI SONT STUBS

| Fonction | Fichier | Type de STUB | Lignes |
|----------|---------|--------------|--------|
| `fetch_market_data()` | main.py | `np.random` fake data | 140-165 |
| `detect_regime_simple()` | momentum_hmm.py | if/else déguisé en HMM | 114-170 |
| `optimize_risk_parity()` | portfolio_allocator.py | Existe mais jamais appelée | 280-330 |
| `execute_rebalance()` | portfolio_allocator.py | Simulation mode uniquement | 220-250 |

---

## 4. ÉTAT RÉEL DES DONNÉES

### CSV Disponibles
| Fichier | Format | Période | Qualité |
|---------|--------|---------|---------|
| `btc_real_2020_2026.csv` | date,close | 2020-01-01 → 2026-05-26 | ✅ Réel |
| `btc_realistic_2020_2026.csv` | OHLCV | 2020-2026 | ✅ Réel |
| `btc_real_2020_2026_ohlcv.csv` | OHLCV | 2020-2026 | ✅ Réel |
| `cache/BTC_USDT_1d_50.csv` | OHLCV | 50 derniers jours | ✅ Binance |
| `cache/ETH_USDT_1d_50.csv` | OHLCV | 50 derniers jours | ✅ Binance |
| `cache/SOL_USDT_1d_50.csv` | OHLCV | 50 derniers jours | ✅ Binance |

**Qualité:** 
- Données historiques BTC: **6 ans complets** (2301 jours)
- Données récentes multi-asset: **50-100 jours** via Binance API
- **Aucune donnée manquante** détectée

---

## 5. RECOMMANDATIONS PRIORITAIRES POUR V0.3

### 🔥 P0 - CRITICAL (Bloquant production)

1. **Remplacer `fetch_market_data()`**
   - Charger vrais CSV depuis `data/btc_real_2020_2026.csv`
   - OU appeler Binance API via `binance_data_fetcher.py`
   - **Supprimer `np.random` définitivement**

2. **Implémenter VRAI HMM**
   - Installer `hmmlearn`: `pip install hmmlearn`
   - Remplacer `detect_regime_simple()` par vrai `GaussianHMM`
   - Fit sur 60 jours, predict regime actuel
   - OU renommer stratégie "Momentum+RuleBased" (plus honnête)

3. **Fix incohérence Bear Regime**
   - Soit mettre à jour config: `"position_pct": 0.0` pour Bear
   - Soit implémenter vrai trading Bear dans le code
   - **Documenter la décision**

---

### ⚡ P1 - HIGH (Amélioration majeure)

4. **Activer `optimize_risk_parity()`**
   - Calculer covariance matrix sur données récentes (50j)
   - Appeler `optimize_risk_parity()` au lieu de weights hardcodés
   - Rebalancer weights weekly

5. **Lire config.json complètement**
   - `transaction_cost_bps` doit venir de config
   - `rebalance_threshold` doit venir de config
   - Ajouter validation config au startup

6. **Ajouter integration tests**
   - Test avec données réelles (pas fake)
   - Test chaque regime detection
   - Test circuit breaker triggers

---

### 📋 P2 - MEDIUM (Nettoyage)

7. **Supprimer code mort**
   - `optimize_risk_parity()` si pas utilisé
   - OU l'intégrer vraiment

8. **Documenter limitations**
   - "HMM" = rule-based (pas vrai HMM)
   - "Risk Parity" = static weights (pas optimisé)
   - Data fetch = synthetic (pas production)

---

## 6. VERDICT FINAL

**Système Saiyan v0.2 = PROTOTYPE DE RECHERCHE, PAS PRODUCTION**

| Component | Status | Production Ready? |
|-----------|--------|-------------------|
| Data Fetch | ❌ FAKE | NON |
| Strategy (HMM) | ❌ FAUX NOM | NON |
| Risk Monitor | ✅ OK | OUI |
| Portfolio Allocator | ⚠️ HARDCODÉ | PARTIEL |
| Config | ⚠️ INCOHÉRENT | NON |

**Conclusion:** v0.2 est un **exercice académique** avec des claims de performance non-validées sur données réelles. **Aucun argent réel ne doit être engagé** avant:
1. Vrai data fetching
2. Vrai HMM ou renommage honnête
3. Tests sur données historiques complètes (6 ans)

---

**Fichier d'audit créé:** `system-saiyan/v0.3/AUDIT-V0.2.md`  
**Prochaine étape:** Reconstruction v0.3 avec corrections P0
