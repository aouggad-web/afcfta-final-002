# ZLECAf Trade Opportunity Finder - Product Requirements Document

## 📋 Résumé du Projet

Application d'analyse commerciale pour l'Afrique sous la Zone de Libre-Échange Continentale Africaine (ZLECAf/AfCFTA).

### Vision
Fournir aux entreprises, décideurs et analystes africains un outil complet pour :
- Identifier les opportunités commerciales intra-africaines
- Analyser les flux d'échanges avec des données fiables
- Évaluer les avantages tarifaires de la ZLECAf
- Découvrir les possibilités de substitution d'importations extra-africaines

### Principe Directeur
**FIABILITÉ DES DONNÉES** : Pas d'estimations sauf dans des cas extrêmes et justifiés, et ces estimations doivent être clairement marquées comme "ESTIMATION".

---

## 🎯 Fonctionnalités Implémentées

### ✅ Phase 1 : Infrastructure de Base (Terminé)
- [x] Base de données HS6 complète bilingue (FR/EN)
- [x] Règles d'Origine (RoO) spécifiques ZLECAf
- [x] Gestion des tarifs douaniers nationaux
- [x] Profils pays détaillés avec indicateurs économiques

### ✅ Phase 2 : Intégration API OEC (Terminé)
- [x] Statistiques commerciales en temps réel via API OEC
- [x] Commerce bilatéral entre pays africains
- [x] Top produits exportés/importés par pays
- [x] Correction de l'affichage des codes HS

### ✅ Phase 3 : Analyse de Substitution (Terminé)
- [x] Service d'analyse avec données réelles OEC
- [x] Identification des fournisseurs africains potentiels
- [x] Calcul des potentiels de substitution
- [x] Interface utilisateur dédiée

### ✅ Phase 4 : Intelligence Artificielle Gemini (Terminé - 31 Jan 2025)
- [x] Intégration Google Gemini via Emergent LLM Key
- [x] Analyse IA des opportunités d'export
- [x] Analyse IA de substitution d'import
- [x] Analyse IA des chaînes de valeur industrielles
- [x] Profil économique IA des pays
- [x] Balance commerciale historique avec analyse de tendance
- [x] **Indicateurs ESTIMATION** clairement affichés

### ✅ Phase 5 : Visualisation Sankey (Terminé - 31 Jan 2025)
- [x] Diagramme Sankey des flux commerciaux
- [x] Filtrage interactif par nœud
- [x] Adaptation de l'app AI Studio de l'utilisateur
- [x] Intégration avec données réelles

---

## 🏗️ Architecture Technique

### Backend (FastAPI + Python)
```
/app/backend/
├── routes/
│   ├── gemini_analysis.py    # API IA Gemini (/api/ai/*)
│   ├── comtrade.py           # API UN COMTRADE (NEW)
│   ├── substitution.py       # API substitution
│   ├── oec.py                # API statistiques OEC
│   ├── countries.py          # API profils pays
│   └── ...
├── services/
│   ├── gemini_trade_service.py      # Service Gemini (IMPROVED)
│   ├── comtrade_service.py          # Service UN COMTRADE v1 (NEW)
│   ├── wto_service.py               # Service WTO tarifs (NEW)
│   ├── data_source_selector.py      # Sélecteur intelligent (NEW)
│   ├── real_trade_data_service.py   # Service OEC
│   ├── real_substitution_service.py # Service substitution
│   └── oec_trade_service.py         # Helper OEC
└── server.py
```

### Frontend (React + Shadcn UI)
```
/app/frontend/src/components/
├── opportunities/
│   ├── AIAnalysis.jsx          # Analyse IA principale
│   ├── TradeSankeyDiagram.jsx  # Diagramme Sankey
│   ├── OpportunitySummary.jsx  # Vue d'ensemble (AI-CONNECTED)
│   ├── ValueChains.jsx         # Chaînes de valeur (AI-CONNECTED)
│   ├── ProductAnalysisView.jsx # Par Produit (AI-CONNECTED)
│   ├── SubstitutionAnalysis.jsx
│   ├── OpportunitiesTab.jsx
│   └── ...
├── profiles/
│   ├── AITradeSummary.jsx      # Résumé IA dans profils
│   └── CountryProfilesTab.jsx
└── ...
```

---

## 🔌 Intégrations Tierces

| Service | Utilisation | Clé |
|---------|-------------|-----|
| **Google Gemini** | Analyse IA intelligente | Emergent LLM Key |
| **UN COMTRADE v1** | Données commerciales récentes | Public (limité) ou clé API |
| **API OEC** | Données commerciales historiques | Gratuit |
| **WTO API** | Données tarifaires | Public |
| **MongoDB** | Base de données | Local |

---

## 📊 Endpoints API Principaux

### AI Analysis
- `GET /api/ai/health` - Statut du service Gemini
- `GET /api/ai/summary` - **Vue d'ensemble commerce africain (NEW)**
- `GET /api/ai/value-chains` - **Analyse chaînes de valeur (NEW)**
- `GET /api/ai/opportunities/{country}?mode=export|import|industrial` - Opportunités IA
- `GET /api/ai/profile/{country}` - Profil économique IA
- `GET /api/ai/balance/{country}` - Balance commerciale historique
- `GET /api/ai/product/{hs_code}` - Analyse produit par code HS

### COMTRADE (NEW)
- `GET /api/comtrade/status` - Statut service COMTRADE
- `GET /api/comtrade/bilateral/{reporter}` - Données commerciales bilatérales
- `GET /api/comtrade/latest-period/{country}` - Dernière période disponible

### Substitution
- `GET /api/substitution/opportunities/import/{country_iso3}` - Opportunités import
- `GET /api/substitution/opportunities/export/{country_iso3}` - Opportunités export
- `GET /api/substitution/countries` - Liste des pays

### OEC Trade
- `GET /api/oec/bilateral/{reporter}/{partner}` - Commerce bilatéral
- `GET /api/oec/products/{country}` - Top produits

---

## 📝 Backlog

### P0 - Haute Priorité
- [x] **Bug corrigé (4 Fév 2025)**: Sélecteurs de pays vides dans Substitution et Vue d'ensemble
- [ ] Tests e2e complets avec Playwright

### P1 - Priorité Moyenne 
- [x] **Cache Redis pour les appels Gemini** (4 Fév) - TTL 6h, amélioration 550x
- [x] **Indicateur de fraîcheur des données** (4 Fév) - Badge "Données en direct"
- [x] **Refactoring frontend StatisticsTab** (5 Fév) - 4 sous-onglets
- [x] **Comparaison multi-pays** (5 Fév) - Radar chart + tableaux
- [x] **Calculateur amélioré avec détails NPF vs ZLECAf** (6 Fév)
  - Affichage étape par étape du calcul
  - Détail de chaque taxe (DD, TVA, DAPS, etc.)
  - Économies ZLECAf clairement affichées
- [x] **Mise à jour OEC vers données 2024** (6 Fév)
- [ ] Recherche/filtre pour le fil d'actualités
- [ ] Intégration complète des données fiscales algériennes (crawler douane.gov.dz)

### P2 - Priorité Basse
- [ ] Exportation CSV/Excel
- [ ] Extension du crawler fiscal aux autres pays africains
- [ ] Sauvegarde des recherches HS fréquentes

---

## 📅 Historique des Versions

### v1.8.0 (6 Février 2025)
- **Calculateur amélioré avec détails NPF vs ZLECAf** :
  - Nouveau service `enhanced_calculator_service.py`
  - Affichage étape par étape : CIF → DD → TVA → Autres
  - Base de calcul explicite (CIF vs CIF+DD)
  - Comparaison côte à côte NPF / ZLECAf
  - Bannière d'économies avec montant et pourcentage
  - Endpoint: `GET /api/calculate/detailed/{country}/{hs_code}`
- **Mise à jour OEC vers données 2024** :
  - `DEFAULT_YEAR = 2024` dans oec_trade_service.py
  - Toutes les requêtes OEC utilisent 2024 par défaut
  - Données fraîches disponibles pour tous les pays africains
- **Crawler fiscal algérien** (script prêt) :
  - `etl/dza_tariff_connector.py` - Crawl douane.gov.dz
  - Parse les sous-positions nationales (HS10)
  - Extrait DD, TVA, TCS, PRCT, avantages fiscaux
- **Nouveaux fichiers** :
  - `/app/backend/services/enhanced_calculator_service.py`
  - `/app/backend/etl/dza_tariff_connector.py`
  - `/app/frontend/src/components/calculator/DetailedCalculationBreakdown.jsx`

### v1.7.0 (5 Février 2025)
- **Refactoring Frontend StatisticsTab** - 4 sous-onglets
- **Comparaison Multi-Pays** - Radar chart + tableaux comparatifs

### v1.6.0 (4 Février 2025)
- **Cache Redis intégré** - Mise en cache des appels Gemini (TTL 6h)
  - Premier appel: ~27s, appels suivants: <0.1s (amélioration 550x)
  - Endpoint de stats: `GET /api/ai/cache/stats`
  - Invalidation: `DELETE /api/ai/cache/clear`
- **Indicateur de fraîcheur des données** - Composant DataFreshnessIndicator
  - Affiche "Données en direct" pour données fraîches
  - Affiche "Il y a Xh/Xmin" pour données en cache
- **Refactoring backend** - Extraction de routes depuis server.py
  - `routes/rules_of_origin.py` - Règles d'Origine ZLECAf
  - `routes/hs6_database.py` - Base de données HS6

### v1.5.0 (3 Février 2025)
- **Intégration UN COMTRADE v1 API** - Données commerciales plus récentes
- **Data Source Selector intelligent** - Sélection automatique COMTRADE > OEC > WTO
- **Optimisation des prompts Gemini** - Meilleure qualité des données
- **Nouvelles APIs AI** :
  - `GET /api/ai/summary` - Vue d'ensemble commerce africain
  - `GET /api/ai/value-chains` - Analyse des chaînes de valeur
- **Composants Frontend connectés aux données AI réelles** :
  - Vue d'ensemble - Statistiques commerciales africaines
  - Chaînes de Valeur - 6 secteurs clés (café, cacao, coton, pétrole, minéraux, automobile)
  - Par Produit - Analyse IA par code HS
- **Badges "Données générées par IA"** sur tous les composants utilisant Gemini

### v1.4.0 (31 Janvier 2025)
- **Intégration Gemini AI** avec Emergent LLM Key
- **Diagramme Sankey** pour visualisation des flux
- **Indicateurs ESTIMATION** obligatoires
- Nettoyage des fichiers obsolètes
- Tests complets (23/23 passés)

### v1.3.0 (30 Janvier 2025)
- Analyse de substitution avec données réelles OEC
- Correction de l'affichage des codes HS
- Onglet Opportunités restructuré

### v1.2.0 (29 Janvier 2025)
- Intégration API OEC
- Commerce bilatéral
- Top produits par pays

### v1.1.0 (28 Janvier 2025)
- Profils pays détaillés
- Indicateurs World Bank
- Projets structurants

### v1.0.0 (Janvier 2025)
- MVP initial
- Base de données HS6
- Règles d'origine ZLECAf

---

## 👥 Contacts

- **Développement** : Emergent AI
- **Design** : Basé sur l'app AI Studio de l'utilisateur
- **Données** : IMF, UNCTAD, OEC, World Bank
