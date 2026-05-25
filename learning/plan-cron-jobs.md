# 🤖 Cron Jobs - Cursus Quant Trader

## Configuration des Automatisations

### Weekly Checkpoint (Samedi 18h UTC)
- **ID:** `quant-trader-weekly-checkpoint`
- **Schedule:** `0 18 * * SAT` (UTC)
- **Objectif:** Bilan hebdomadaire, mise à jour progression, rapport à W

### Daily Study Reminder (Optionnel)
- **Schedule:** `0 20 * * *` (UTC)
- **Objectif:** Rappel pour avancer module en cours (si besoin)

---

## Progression du Cursus

### 🎒 Licence 1-2 (Maths Fondamentales)
- [x] Semaine 1: Analyse des returns BTC
- [ ] Semaine 2: GARCH Volatility Modeling
- [ ] Semaine 3: ARIMA Time Series
- [ ] Semaine 4: Portfolio Theory (Markowitz)

### 🎓 Master 1 (Finance Quantitative)
- [ ] Module 5: Options Pricing (Black-Scholes)
- [ ] Module 6: Market Microstructure
- [ ] Module 7: Risk Management (VaR, ES)
- [ ] Module 8: Cointégration & Pairs Trading

### 🔬 Master 2 (Trading Algorithmique)
- [ ] Module 9: ML Supervised (Random Forest, XGBoost)
- [ ] Module 10: ML Unsupervised (Clustering, PCA)
- [ ] Module 11: Deep Learning (LSTM, Transformers)
- [ ] Module 12: Walk-Forward Validation
- [ ] Module 13: Mean Reversion (Ornstein-Uhlenbeck)
- [ ] Module 14: Momentum & Breakouts
- [ ] Module 15: HMM Regime Detection ⭐
- [ ] Module 16: Multi-Factor Models

### 🎖️ Doctorat (Recherche)
- [ ] Module 17: Reinforcement Learning (PPO)
- [ ] Module 18: LLM + Trading
- [ ] Module 19: Multi-Agent Systems
- [ ] Module 20: Adaptive Strategies
- [ ] Module 21: Système Saiyan Complet (Thèse)

---

## Règles d'Auto-Formation

1. **1 module/semaine** minimum (rythme soutenu mais réaliste)
2. **Chaque module =** théorie + pratique + backtest + documentation
3. **Checkpoint samedi:** bilan + rapport à W
4. **Shadow mode:** Tester les stratégies validées en paper-trade
5. **Intégration progressive:** Les concepts validés → système Saiyan

---

## Notes

- Les cron jobs sont configurés dans `gateway` via l'API cron
- Progression tracée dans `learning/quant-trading-curriculum.md`
- Journal quotidien dans `learning/journal.md`
