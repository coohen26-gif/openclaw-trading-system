# 💡 Insights Saiyan - Connaissances Actionnables

**Objectif:** Transformer chaque apprentissage en insight actionnable

---

## 📋 Structure d'un Insight

Chaque fichier `XX-topic.md` contient:

1. **📚 Connaissance (Théorie)** - Ce que j'ai appris
2. **💡 Insight (Conclusion)** - Ce que ça signifie pour Saiyan
3. **🛠️ Application (Code)** - Comment je l'utilise
4. **✅ Test (Validation)** - Comment je valide
5. **🎯 Décision** - Priorité et action

---

## 🗂️ Index des Insights

| # | Topic | Source | Priorité | Statut |
|---|-------|--------|----------|--------|
| 01 | Fat Tails = Feature | S01 (Returns BTC) | P0 | ✅ Documenté |
| 02 | Skewness Gate | S01 + S15 | P1 | ⏳ À documenter |
| 03 | GARCH × Sizing | S02 (GARCH) | P1 | ⏳ À documenter |
| 04 | HMM Regime | S15 (HMM) | P0 | ⏳ À documenter |
| 05 | Risk Parity | S17-18 | P1 | ⏳ À documenter |
| 06 | Half-Kelly | S18 (Kelly) | P1 | ⏳ À documenter |
| 07 | VaR/CVaR | S19 (Risk) | P0 | ⏳ À documenter |
| 08 | XGBoost > Heuristics | S10 (ML) | P1 | ⏳ À documenter |
| 09 | Walk-Forward | S12 (Backtest) | P0 | ⏳ À documenter |
| 10 | Stress Testing | S20 (Risk) | P1 | ⏳ À documenter |

---

## 🔄 Workflow: Théorie → Insight → Code → Test

```
1. 📚 Apprentissage (learning/notes/semaine-XX.md)
   ↓
2. 💡 Insight (learning/insights/XX-topic.md)
   ↓
3. 🛠️ Code (saiyan-v1/strategies/*.py)
   ↓
4. ✅ Test (saiyan-v1/backtests/*.py)
   ↓
5. 🎯 Décision (Keep/Iterate/Discard)
```

---

## 📊 Tracking

| Étape | Count | Objectif |
|-------|-------|----------|
| Insights documentés | 1/10 | 10/10 |
| Insights → Code | 0/10 | 10/10 |
| Code → Test | 0/10 | 10/10 |
| Test → Décision | 0/10 | 10/10 |

---

## 🎯 Règles

1. **1 insight = 1 fichier** (atomic)
2. **Toujours inclure application concrète** (code snippet)
3. **Toujours inclure test requis** (métriques, benchmark)
4. **Toujours inclure décision** (P0/P1/P2 + action)
5. **Review hebdomadaire** (dimanche 18h, cron)

---

**Créé:** 24 Mai 2026  
**Review:** Dimanche 18h UTC
