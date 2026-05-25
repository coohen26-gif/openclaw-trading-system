# 🔄 Révisions Saiyan - Consolidation des Connaissances

**Créé:** 24 Mai 2026  
**Objectif:** Ancrer les connaissances par révision espacée  
**Méthode:** Spaced Repetition + Active Recall + Feynman Technique

---

## 📋 Pourquoi Réviser ?

**Problème:** 20 modules appris en 2 jours → informations "fraîches" mais pas "ancrées"

**Solution:**
1. **Pause après chaque module** (W's advice)
2. **Révision espacée** (1j, 3j, 7j, 30j)
3. **Active recall** (je teste ma mémoire)
4. **Feynman** (j'explique comme si j'enseignais)

---

## 🗂️ Structure des Révisions

```
learning/revisions/
├── README.md (ce fichier)
├── revision-01-master1-4-consolidation.md ✅
├── revision-02-post-module-XX.md (à venir)
└── quiz/
    ├── quiz-01-returns-btc.md
    ├── quiz-02-garch.md
    └── ...
```

---

## 🔄 Cycle de Révision

### Après Chaque Module (Pause Révision)

**Durée:** 30-60min  
**Tâches:**
1. ✅ Relire insights précédents (learning/insights/)
2. ✅ Vérifier knowledge-base.md (tout est classé ?)
3. ✅ Active recall: Sans regarder, je récite les insights clés
4. ✅ Quiz personnel: 5-10 questions sur le module
5. ✅ Feynman: J'explique le concept comme à un débutant
6. ✅ Mise à jour: Insights manquants ajoutés

**Notification W:** ✅ "Pause révision en cours (30-60min)"

---

### Révision Espacée (Spaced Repetition)

**Schedule:**
- **J+1:** Revoir module (lendemain)
- **J+3:** Revoir module (3 jours après)
- **J+7:** Revoir module (semaine suivante)
- **J+30:** Revoir module (mois suivant)

**Méthode:**
1. Quiz rapide (5 questions)
2. Active recall (je récite sans regarder)
3. Vérification (je compare avec notes)
4. Correction (j'ajuste si erreur)

---

## 📊 Tracking des Révisions

| Module | Date Appris | J+1 | J+3 | J+7 | J+30 | Statut |
|--------|-------------|-----|-----|-----|------|--------|
| Master 1-4 | 24 Mai | ✅ | ⏳ | ⏳ | ⏳ | En cours |
| Master 5 | À venir | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |

---

## 🧠 Techniques Utilisées

### 1. Active Recall
**Principe:** Tester sa mémoire activement, pas juste relire

**Mise en œuvre:**
- Quiz après chaque module
- Questions: "Qu'est-ce que X ?", "Comment appliquer Y ?"
- Sans regarder les notes d'abord

### 2. Spaced Repetition
**Principe:** Réviser à intervalles croissants

**Mise en œuvre:**
- J+1, J+3, J+7, J+30
- Cron jobs automatiques pour rappels

### 3. Feynman Technique
**Principe:** Expliquer comme si j'enseignais à un débutant

**Mise en œuvre:**
- Après chaque insight: "Explique ça simplement"
- Si je bloque → je n'ai pas vraiment compris

### 4. Interleaving
**Principe:** Mélanger les sujets pour mieux apprendre

**Mise en œuvre:**
- Quiz mélangés (pas par module)
- Connections entre insights (cross-links)

---

## 📝 Template de Quiz

```markdown
# Quiz - [Nom du Module]

**Date:** YYYY-MM-DD  
**Module:** Semaine XX

---

## Questions

1. [Question concept clé]
   <details><summary>Réponse</summary>
   [Réponse]
   </details>

2. [Question application]
   <details><summary>Réponse</summary>
   [Réponse]
   </details>

3. [Question insight]
   <details><summary>Réponse</summary>
   [Réponse]
   </details>

---

## Score

- Correct: X/5
- À revoir: [topics]
- Prochaine révision: J+X
```

---

## 🎯 Règles

1. **Pause obligatoire** après chaque module (30-60min)
2. **Quiz personnel** créé pour chaque module
3. **Révision espacée** programmée (J+1, J+3, J+7, J+30)
4. **Notification W** si pause révision >30min
5. **Tracking** dans ce fichier (mise à jour auto)

---

**Créé:** 24 Mai 2026  
**Prochaine révision:** J+1 (25 Mai 2026)  
**Review hebdo:** Dimanche 18h UTC (cron)
