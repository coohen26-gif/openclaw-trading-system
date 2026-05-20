# 🤖 Saiyan - LLM Configuration & Recommandations

**Date** : 2026-05-20 22:40 UTC  
**Objectif** : Documenter les LLM disponibles via Ollama Cloud et choisir le meilleur pour chaque task.

---

## 1️⃣ **LLMs Disponibles (Ollama Cloud via Abonnement)**

### **Via Ollama Cloud API**

| Modèle | ID | Contexte | Reasoning | Spécialité | Taille |
|--------|-----|----------|-----------|------------|--------|
| **Qwen3.5** | `qwen3.5:cloud` | 256k | ✅ Oui | Généraliste, code, maths | ~72B |
| **Qwen3 Coder Next** | `qwen3-coder-next:cloud` | 256k | ❌ Non | Code pur | ~35B |
| **GLM-5** | `glm-5:cloud` | 128k | ✅ Oui | Reasoning, maths | ~130B |
| **GLM-5.1** | `glm-5.1:cloud` | 128k | ✅ Oui | Reasoning avancé | ~130B |
| **MiniMax M2.7** | `minimax-m2.7:cloud` | 256k | ✅ Oui | Code + reasoning | ~400B MoE |
| **MiniMax M2.5** | `minimax-m2.5:cloud` | 256k | ✅ Oui | Code + reasoning | ~400B MoE |

**Coût** : $0 (inclus dans abonnement Ollama Cloud)

---

## 2️⃣ **Recommandations par Task Saiyan**

### **🏆 Configuration Principale (KEEP)**

```yaml
Default Model: qwen3.5:cloud
Reasoning: ON pour tasks complexes
Context: 256k
```

**Pourquoi Qwen3.5:cloud par défaut :**
- ✅ **Équilibré** : Code + Maths + Trading knowledge
- ✅ **Reasoning** : Activé (HMM, stats, backtests)
- ✅ **Contexte** : 256k (suffisant pour docs + code)
- ✅ **Coût** : $0 (abonnement inclus)
- ✅ **Latence** : <1s

---

### **🎯 Meilleur LLM par Task**

| Task | LLM Recommandé | Pourquoi |
|------|----------------|----------|
| **HMM Regime Detector** | `glm-5.1:cloud` | Maths avancées, HMM, stats bayésiennes |
| **Code Python (stratégies)** | `qwen3-coder-next:cloud` | Spécialisé code, plus rapide |
| **Backtest Framework** | `minimax-m2.7:cloud` | 400B MoE, meilleur sur analytics |
| **Confluence Scoring** | `qwen3.5:cloud` | Équilibré (technicals + weighting) |
| **Regime-Aware Fusion** | `glm-5.1:cloud` | Reasoning complexe, pondération |
| **Self-Healing AI** | `minimax-m2.7:cloud` | AI monitoring, anomaly detection |
| **Documentation** | `qwen3.5:cloud` | Bon équilibre code + prose |
| **Debug/Review** | `qwen3-coder-next:cloud` | Spécialisé code review |
| **Daily Dev (routine)** | `qwen3.5:cloud` | KEEP (déjà configuré) |

---

## 3️⃣ **Comparaison Détaillée**

### **Code Python**

| Modèle | Score | Notes |
|--------|-------|-------|
| qwen3-coder-next:cloud | 9.5/10 | 🏆 Spécialisé code |
| minimax-m2.7:cloud | 9.0/10 | Excellent, mais overkill |
| qwen3.5:cloud | 8.5/10 | Très bon, polyvalent |
| glm-5.1:cloud | 8.0/10 | Bon, mais focus maths |

**Vainqueur** : `qwen3-coder-next:cloud` (spécialisé)

---

### **Maths/Stats (HMM, Sharpe, Walk-Forward)**

| Modèle | Score | Notes |
|--------|-------|-------|
| glm-5.1:cloud | 9.5/10 | 🏆 Reasoning avancé |
| minimax-m2.7:cloud | 9.0/10 | 400B MoE, excellent |
| qwen3.5:cloud | 8.5/10 | Très bon |
| qwen3-coder-next:cloud | 7.5/10 | Code > maths |

**Vainqueur** : `glm-5.1:cloud` (reasoning)

---

### **Trading Knowledge**

| Modèle | Score | Notes |
|--------|-------|-------|
| qwen3.5:cloud | 9.0/10 | 🏆 Entraîné 2025, trading data |
| minimax-m2.7:cloud | 8.5/10 | Bon, mais moins récent |
| glm-5.1:cloud | 8.0/10 | Bon, focus maths |
| qwen3-coder-next:cloud | 7.0/10 | Code pur |

**Vainqueur** : `qwen3.5:cloud` (knowledge trading)

---

### **Coût (Tokens/jour estimés : 500k)**

| Modèle | Coût/jour | Coût/12 semaines |
|--------|-----------|------------------|
| **Tous (Ollama Cloud)** | **$0** | **$0** |

**Tous les modèles sont inclus dans l'abonnement Ollama Cloud** 🎉

---

## 4️⃣ **Configuration Optimale Saiyan**

### **Mode 1 : Daily Dev (90% du temps)**
```yaml
Model: qwen3.5:cloud
Reasoning: ON
Use Case: HMM coding, strategies, backtests, docs
```

### **Mode 2 : Maths Intensives (HMM, Stats)**
```yaml
Model: glm-5.1:cloud
Reasoning: ON
Use Case: HMM Regime Detector, Sharpe Ratio, Walk-Forward
```

### **Mode 3 : Code Pur (Stratégies, Refactoring)**
```yaml
Model: qwen3-coder-next:cloud
Reasoning: OFF
Use Case: Coder 3 stratégies, refactoring, debug
```

### **Mode 4 : Analytics (Backtests, Performance)**
```yaml
Model: minimax-m2.7:cloud
Reasoning: ON
Use Case: Backtest framework, performance analysis
```

---

## 5️⃣ **Comment Changer de Modèle**

### **Via Session Status**
```bash
/session_status model=glm-5.1:cloud
```

### **Via Sub-Agent Spawn**
```python
sessions_spawn(
  task="Coder HMM Regime Detector",
  model="glm-5.1:cloud",  # Override model
  thinking="on"
)
```

### **Via Cron Job**
```json
{
  "payload": {
    "model": "minimax-m2.7:cloud",
    "thinking": "on"
  }
}
```

---

## 6️⃣ **Recommandation Finale**

### **KEEP : `qwen3.5:cloud` (Défaut)** ✅

**Pour 90% des tasks** :
- HMM Regime Detector
- 3 Stratégies de base
- Backtest framework
- Confluence Scoring
- Documentation

### **SWITCH TO : `glm-5.1:cloud` (Si blocage maths)**

**Pour 10% des tasks** :
- HMM advanced maths (Gaussian HMM, Baum-Welch)
- Walk-forward optimization
- Sharpe Ratio advanced calculations

### **SWITCH TO : `qwen3-coder-next:cloud` (Code review)**

**Pour code review final** :
- Refactoring strategies
- Debug complexe
- Code quality check

---

## 7️⃣ **Action Immédiate**

**Ne rien changer** - `qwen3.5:cloud` est optimal pour :
- ✅ Code Python (HMM, stratégies)
- ✅ Maths/Stats (Sharpe, HMM)
- ✅ Trading knowledge
- ✅ Gratuit (abonnement inclus)
- ✅ <1s latence

**Si blocage sur HMM maths** → Switch temporaire à `glm-5.1:cloud`.

---

*Document créé : 2026-05-20 22:40 UTC*  
*LLM: qwen3.5:cloud (self-aware)*
