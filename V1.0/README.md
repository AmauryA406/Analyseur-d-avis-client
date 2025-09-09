# 🔍 Analyseur d'Avis Clients par IA

## Automatisation de l'analyse de sentiment et extraction d'insights business

Un système complet d'analyse automatisé qui transforme les avis clients bruts en recommandations business actionnables grâce aux Large Language Models.

## 📊 Vue d'ensemble du projet

### Problème résolu
Les entreprises collectent des milliers d'avis clients mais manquent d'outils pour extraire automatiquement des insights actionnables. L'analyse manuelle est chronophage et biaisée.

### Solution technique
Pipeline automatisé utilisant l'IA générative pour :
- Découvrir automatiquement les sujets récurrents (zéro biais)
- Analyser le sentiment par aspect avec précision contextuelle
- Générer des priorités business basées sur fréquence × impact
- Produire des recommandations concrètes avec timeline et budgets

## 🏗️ Architecture technique

```
Données brutes → Nettoyage → Discovery IA → Analyse sentiment → Insights business
     (317 avis)      (ETL)    (LLM Phase 1)   (LLM Phase 2)    (Priorités)
```

### Stack technique
- **Language** : Python 3.11+
- **LLM** : Groq Llama-3.1-8B (API gratuite)
- **Data Processing** : Pandas, NumPy
- **Visualisation** : Matplotlib, JSON reports
- **Architecture** : Pipeline modulaire avec gestion d'erreurs

## 🚀 Fonctionnalités principales

### 1. Nettoyage intelligent des données
- Suppression automatique des métadonnées web polluantes
- Pipeline robuste pour données Amazon/e-commerce  
- Validation et normalisation des formats

### 2. Découverte automatique de topics (Innovation clé)
- Analyse LLM sans a priori sur un échantillon stratifié
- Identification des aspects réellement importants pour les clients
- Évite les biais d'analyse traditionnels

### 3. Analyse contextuelle par IA
- Sentiment global + sentiment par aspect découvert
- Analyse des 300 avis avec topics personnalisés
- Gestion robuste des erreurs et formats non-standard

### 4. Priorisation business intelligente
- Matrice impact : (Fréquence × 0.6) + (Gravité × 0.4)
- Classification automatique : Critique/Haute/Moyenne/Basse
- Timeline et budgets estimés par priorité

## 📈 Résultats obtenus

### Dataset analysé
- **317 avis** clients Amazon collectés
- **300 avis** analysables après nettoyage
- **Distribution** : 47% positif, 43% négatif, 10% neutre

### Topics découverts automatiquement
1. **Fonctionnement de la montre** (74.7% des avis, 45.5% négatif)
2. **Fonctionnalités et compatibilité** (79.3% des avis, 35.3% négatif)
3. **Qualité de la montre** (79.3% des avis, 29% négatif)
4. **Connectivité et synchronisation** (58.7% des avis, 52.8% négatif)
5. **Durée de vie et fiabilité** (58.3% des avis, 48% négatif)

### Insights business générés
- **5 priorités haute** identifiées (délai 2-6 semaines)
- **3 priorités moyennes** (délai 1-3 mois)
- **Budget estimé** : €50k-100k R&D
- **ROI projeté** : +200-300% sur 12 mois

## 🔧 Installation et utilisation

### Prérequis
```bash
pip install groq pandas numpy matplotlib
```

### Configuration
```bash
# Clé API Groq (gratuite)
export GROQ_API_KEY=your_key_here
```

### Exécution
```bash
# 1. Nettoyage et fusion des données
python V1.0/src/nettoyage_donnees.py

# 2. Analyse complète par IA (300 avis)
python V1.0/src/analyse_groq_complete.py

# 3. Génération priorités business
python V1.0/src/business_analysis.py
```

## 📁 Structure du projet

```
V1.0/
├── data/
│   ├── raw/                    # Données brutes scrapées
│   └── processed/              # Données nettoyées + analyses
├── src/
│   ├── nettoyage_donnees.py    # Pipeline ETL
│   ├── analyse_groq_complete.py # Analyse IA complète
│   └── business_analysis.py    # Génération insights
├── notebooks/
│   └── business_analysis_report_*.txt # Rapports générés
└── README.md
```

## 📊 Métriques de performance

### Performance technique
- **304 appels API** Groq utilisés (sur 14,400 quotidiens)
- **100% de succès** dans l'analyse des avis
- **25 minutes** de traitement total
- **0€ de coût** (API gratuite)

### Qualité des résultats
- **12 topics** découverts automatiquement sans biais
- **Cohérence sentiment vs notes** : Avis 1⭐ = 96% sentiment négatif
- **Recommandations actionnables** avec impact client quantifié

## 🎯 Innovation et différenciation

### Approche unique en 2 phases
1. **Discovery Phase** : LLM découvre les topics réels sans présupposition
2. **Analysis Phase** : Analyse fine avec vocabulaire contextualisé

### Avantages vs solutions existantes
- **Zéro biais humain** dans la découverte de topics
- **Analyse contextuelle** (pas seulement sentiment global)
- **Priorités business** automatiques (fréquence + gravité)
- **Pipeline industriel** robuste et scalable

## 💼 Cas d'usage et applications

### Pour les entreprises
- **Product Management** : Identifier les features prioritaires
- **Customer Success** : Réduire les sources d'insatisfaction
- **R&D** : Orienter les investissements développement
- **Marketing** : Mettre en avant les points forts réels

### Secteurs applicables
- E-commerce (Amazon, sites marchands)
- SaaS (feedback utilisateurs)
- Applications mobiles (app stores)
- Services (hospitality, restauration)

## 🔮 Évolutions futures

### Fonctionnalités envisagées
- **Multi-sources** : Google Reviews, Trustpilot, réseaux sociaux
- **Temps réel** : Monitoring continu des nouveaux avis
- **Dashboard interactif** : Interface web pour stakeholders
- **Alerting automatique** : Notifications sur problèmes émergents

### Optimisations techniques
- **Cache intelligent** : Éviter re-analyse des avis existants
- **Batch processing** : Traitement de volumes plus importants
- **Multi-langues** : Support international automatique

## 📞 Contact et informations

**Développeur** : Amaury Allemand  
**Spécialité** : Data Science & Intelligence Artificielle  
**LinkedIn** : [https://www.linkedin.com/in/amaury-allemand/]  
**Email** : [amauryallemand8@gmail.com]

---

## 📄 Licence

Ce projet est un portfolio technique démontrant des compétences en Data Science et IA appliquée. 

**Technologies utilisées** : Python, Groq LLM, Pandas, NumPy  
**Domaine d'application** : Business Intelligence, Customer Analytics, NLP