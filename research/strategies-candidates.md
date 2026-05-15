# Stratégies Candidates pour NOTRE Système

**Objectif :** 500-600 €/jour, WR ≥ 70-80%, scalp 0.2-0.5%, levier élevé  
**Capital :** 10 000 €  
**Marchés :** BTC, ETH, SOL (crypto)  
**TF :** 5-15min (scalp)  
**Contrainte :** Originalité (pas une copie de Yagati v4)

---

## Stratégie 1 : Bollinger-RSI Dual Confirmation Mean Reversion

- **Concept :** Utiliser les bandes de Bollinger pour identifier les extrêmes de prix et le RSI pour confirmer la surachat/survente. Entrer en mean reversion uniquement quand les deux indicateurs sont alignés.
- **Entrée :**
  - Price touche ou dépasse BB upper/lower (2.0-2.5 std dev, 20 périodes)
  - RSI(14) > 70 (short) ou < 30 (long)
  - Optionnel : BB bandwidth < percentile 20 (marché range-bound)
- **Sortie :**
  - TP : Middle band (SMA20) ou opposite band
  - SL : 1.5x ATR(14) au-delà de l'entrée
  - Time-based exit : 30-45 min max
- **Filtres :**
  - ADX(14) < 25 (pas de trend fort)
  - Volume > SMA(volume, 20) * 1.2
  - HMM regime : range-bound seulement
  - Time of day : éviter open/close US (volatilité imprévisible)
- **TF Idéal :** 5min, 15min
- **WR Attendu :** 72-78% (sur n≥50 trades, marché range)
- **Complexité :** Simple
- **Pourquoi c'est prometteur :**
  - Double confirmation réduit les faux signaux
  - Backtestable avec OHLCV standard
  - Bien documenté, facile à implémenter
  - WR réaliste en marché range (70%+)

---

## Stratégie 2 : Volume Surge Breakout avec Retest Confirmation

- **Concept :** Identifier les breakouts de range consolidé avec surge de volume, mais entrer uniquement sur le retest du niveau cassé (pas le breakout initial).
- **Entrée :**
  - Range consolidé détecté (High-Low range < 2% sur 20-40 candles)
  - Breakout : close au-dessus/en-dessous du range
  - Volume surge : volume > SMA(volume, 20) * 2.5
  - **Entrée réelle :** Retest du niveau de breakout avec rejection candle (wick)
- **Sortie :**
  - TP : 1.5x à 2x la hauteur du range
  - SL : Retour dans le range (invalidation)
  - Time-based exit : 1-2h max
- **Filtres :**
  - ADX(14) > 20 (momentum présent)
  - Pas de news majeure dans les 30min (filtrage temporel)
  - HMM regime : trending ou transition
- **TF Idéal :** 5min, 15min
- **WR Attendu :** 68-75% (dépend de la qualité du retest)
- **Complexité :** Moyenne (détection de range + retest pattern)
- **Pourquoi c'est prometteur :**
  - Le retest filtre les faux breakouts (majorité des échecs)
  - Volume surge confirme la conviction
  - R/R favorable (SL serré, TP 1.5-2x)
  - Originalité : la plupart entrent au breakout, pas au retest

---

## Stratégie 3 : Keltner Channel Reverse avec ADX Filter

- **Concept :** Mean reversion sur les extensions extrêmes des Keltner Channels, mais uniquement quand le trend est faible (ADX bas). Contraire du trend-following classique.
- **Entrée :**
  - Price close au-delà de KC upper/lower (2.0-2.5x ATR multiplier)
  - ADX(14) < 20 (trend faible)
  - RSI(14) divergence : price fait nouveau high/low mais RSI ne confirme pas
- **Sortie :**
  - TP : KC middle line (EMA20)
  - SL : 1.8x ATR(14) au-delà de l'entrée
  - Time-based exit : 45 min max
- **Filtres :**
  - BB bandwidth < percentile 30 (volatilité compressée)
  - Volume > médiane(volume, 50)
  - HMM regime : range-bound ou mean-reverting
  - Éviter les premières 30min après open US
- **TF Idéal :** 5min, 15min
- **WR Attendu :** 70-76%
- **Complexité :** Simple-Moyenne
- **Pourquoi c'est prometteur :**
  - KC plus lisse que BB (moins de faux signaux)
  - ADX filter évite les mean reversion dans un trend fort (danger!)
  - Divergence RSI ajoute une couche de confirmation
  - Peu utilisé en crypto (la plupart utilisent KC en trend-following)

---

## Stratégie 4 : Pairs Trading Crypto BTC-ETH Correlation Breakdown

- **Concept :** Stat Arb market-neutral. Trader la divergence temporaire entre BTC et ETH quand leur correlation habituelle se brise, en pariant sur le retour à la normale.
- **Entrée :**
  - Calculer ratio BTC/ETH (ou spread normalisé) sur fenêtre glissante 60min
  - Z-score du ratio > 2.0 ou < -2.0 (divergence extrême)
  - Correlation rolling(20) > 0.7 (historiquement corrélés)
  - **Position :** Long sous-performant + Short sur-performant (dollar-neutral)
- **Sortie :**
  - TP : Z-score retour à 0.5 ou 0
  - SL : Z-score > 3.5 (correlation breakdown permanent)
  - Time-based exit : 4-6h max
- **Filtres :**
  - Volume des deux assets > médiane(20)
  - Éviter les périodes de news majeures (FTX, SEC, etc.)
  - HMM regime : stable (pas de regime shift)
- **TF Idéal :** 15min, 1h (plus lent que les autres)
- **WR Attendu :** 75-82% (market-neutral, moins de risque directionnel)
- **Complexité :** Complexe (nécessite données de 2 assets, calcul de ratio/z-score)
- **Pourquoi c'est prometteur :**
  - **WR le plus élevé** (market-neutral, moins exposé au bruit)
  - BTC-ETH correlation historiquement forte (0.8-0.9)
  - Scalpable sur les micro-divergences (5-15min)
  - Très original pour un système retail (plutôt institutional)
  - **Inconvénient :** Nécessite short/futures pour les deux assets

---

## Stratégie 5 : Order Book Imbalance Scalp (Microstructure)

- **Concept :** Exploiter les déséquilibres temporaires dans le order book pour anticiper les mouvements de prix à très court terme (1-5min).
- **Entrée :**
  - Order Book Imbalance (OBI) = (Bid Volume - Ask Volume) / (Bid + Ask Volume)
  - OBI > 0.6 (strong bid pressure) ou < -0.6 (strong ask pressure)
  - Sur les 3-5 niveaux de depth (pas juste le top)
  - Price n'a pas encore bougé (anticipation)
- **Sortie :**
  - TP : 0.2-0.4% (scalp rapide)
  - SL : 0.15-0.2% (très serré)
  - Time-based exit : 5-10 min max
- **Filtres :**
  - Spread < 0.05% (liquide)
  - Volume last trade > médiane(100)
  - Éviter les périodes de faible liquidité (weekend, nuit)
  - HMM regime : high-frequency oscillating
- **TF Idéal :** 1min, 5min
- **WR Attendu :** 65-72% (dépend de la qualité des données OB)
- **Complexité :** Complexe (nécessite données order book en temps réel, pas juste OHLCV)
- **Pourquoi c'est prometteur :**
  - **Le plus original** (peu de retail traders ont accès/comprennent OB)
  - Scalp pur, compatible avec 0.2-0.5% target
  - Edge informationnel (données sous-utilisées)
  - **Inconvénient majeur :** Nécessite données order book (API WebSocket, plus complexe que OHLCV)

---

## Top 3 Recommandées

### 1. 🥇 Pairs Trading BTC-ETH Correlation Breakdown
**Pourquoi en #1 :**
- **WR le plus élevé** (75-82%) grâce à l'approche market-neutral
- Moins exposé au bruit directionnel du marché
- Originalité maximale (peu de systèmes retail font du stat arb)
- Compatible avec l'objectif 500-600 €/jour (levier + WR élevé)
- **Risque principal :** Nécessite de short/long simultanément (futures/perp)

### 2. 🥈 Bollinger-RSI Dual Confirmation Mean Reversion
**Pourquoi en #2 :**
- **La plus simple à implémenter** (BB + RSI, indicateurs standards)
- WR solide (72-78%) en marché range
- Backtestable immédiatement avec OHLCV
- Facile à combiner avec HMM regime filter
- **Risque principal :** Performance dégradée en trend fort (nécessite ADX filter)

### 3. 🥉 Volume Surge Breakout avec Retest Confirmation
**Pourquoi en #3 :**
- Originalité : la plupart entrent au breakout, pas au retest
- Filtre naturel des faux breakouts (majorité des échecs)
- R/R favorable (SL serré, TP 1.5-2x)
- WR réaliste 68-75%
- **Risque principal :** Le retest peut ne jamais arriver (missed opportunities)

---

## Prochaines Étapes

1. **Backtester [Pairs Trading BTC-ETH] en priorité**
   - Collecter données historiques BTC/ETH (1-2 ans, 5min TF)
   - Implémenter calcul de ratio, z-score, correlation rolling
   - Backtest avec frais de trading (important pour stat arb!)
   - Objectif : valider WR ≥ 75% sur n≥100 trades

2. **Backtester [Bollinger-RSI Dual] en parallèle**
   - Plus rapide à implémenter (proof of concept)
   - Tester différents paramètres (BB std dev, RSI thresholds)
   - Ajouter ADX filter et HMM regime
   - Objectif : valider WR ≥ 70% sur n≥100 trades

3. **Évaluer la faisabilité [Order Book Imbalance]**
   - Vérifier disponibilité des données OB (Binance, Bybit WebSocket)
   - Estimer la complexité d'implémentation
   - Décider si worth the effort (peut être V2 du système)

4. **Sélection finale après backtests**
   - Choisir 1-2 stratégies pour production
   - Optimiser paramètres (éviter overfitting!)
   - Implémenter risk management (position sizing, drawdown limits)

---

## Notes d'Originalité (vs Yagati v4)

**Yagati utilise :** `ma_distance_revert`, `bb_walk`, `ma_ribbon`

**NOTRE système utilise :**
- ✅ Pairs trading (stat arb) → **Pas dans Yagati**
- ✅ Retest confirmation (pas breakout direct) → **Pas dans Yagati**
- ✅ KC Reverse + ADX filter → **Différent de bb_walk**
- ✅ Order Book Imbalance → **Pas dans Yagati** (retail vs institutional)
- ✅ Dual confirmation BB+RSI → **Plus simple, différent de ma_ribbon**

**Conclusion :** Aucune des 5 stratégies n'est une copie de Yagati. Toutes sont originales et complémentaires.
