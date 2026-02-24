# ZLECAf Trade Opportunity Finder - Product Requirements Document

## Résumé du Projet

Application d'analyse commerciale pour l'Afrique sous la Zone de Libre-Échange Continentale Africaine (ZLECAf/AfCFTA).

### Vision
Fournir aux entreprises, décideurs et analystes africains un outil complet pour :
- Identifier les opportunités commerciales intra-africaines
- Analyser les flux d'échanges avec des données fiables
- Évaluer les avantages tarifaires de la ZLECAf
- Découvrir les possibilités de substitution d'importations extra-africaines

### Principe Directeur
**FIABILITÉ DES DONNÉES** : Données tarifaires authentiques issues des administrations douanières nationales.

---

## Fonctionnalités Implémentées

### Phase 1-5 : Infrastructure, OEC, Substitution, IA, Comparaison (Terminé)
- Base de données HS6 bilingue, Règles d'Origine ZLECAf
- Statistiques OEC 2024, Analyse de Substitution
- Intelligence Artificielle Gemini avec Cache Redis
- Comparaison Multi-Pays (statistiques)

### Phase 6 : Données Tarifaires Authentiques (Terminé - 21 Fév 2025)
- **54 fichiers JSON de tarifs nationaux authentiques** pour TOUS les pays africains
- **~315,000 lignes tarifaires HS6** au total
- **~871,000 sous-positions nationales** (HS8-HS10) au total
- **Taxes détaillées** : DD, TVA, TPI, CEDEAO, CISS, PRCT, T.C.S, AIR, etc.
- **Avantages fiscaux ZLECAf** intégrés
- **Formalités administratives** requises

### Phase 7 : Améliorations Calculateur (Terminé - 21 Fév 2025)
- **Affichage de TOUTES les taxes avec leurs intitulés** :
  - D.D (Droit de Douane)
  - T.V.A (Taxe sur la Valeur Ajoutée)
  - CEDEAO (Prélèvement Communautaire)
  - CISS (Contribution CEDEAO)
  - TPI (Taxe Parafiscale à l'Importation)
  - PRCT (Prélèvement à la Compensation du Transport)
  - T.C.S (Taxe de Contrôle Sanitaire)
  - AIR (Acompte Impôt sur le Revenu)
  - Et plus...

### Phase 8 : Comparaison Multi-Pays (Terminé - 21 Fév 2025)
- **Sélection par région** : Afrique du Nord, Ouest, Centrale, Est, Australe
- **Comparaison instantanée** de plusieurs pays pour un même produit
- **Tableau détaillé** avec toutes les taxes par pays
- **Meilleur choix** mis en évidence (coût ZLECAf le plus bas)
- **Graphiques** : Barres comparatives et Radar chart

### Phase 9 : Corrections et Améliorations (Terminé - 21 Fév 2025)
- ✅ **Bug Select corrigé** : Les menus déroulants du calculateur fonctionnent correctement
- ✅ **Graphiques améliorés** : Ajout des graphiques en camembert (TaxDistributionPieChart) pour la répartition NPF vs ZLECAf
- ✅ **Intégration API FAOSTAT 2024** : Données de production agricole en temps réel
- ✅ **Bug DetailedCalculationBreakdown corrigé** : Exclusion du composant pour les données authentiques
- ✅ **Mode simple HS amélioré** : Input direct pour le code HS (sans recherche obligatoire)

### Phase 10 : Formalités et Documents (Terminé - 22 Fév 2025)
- ✅ **Section "Formalités et Documents Nécessaires"** ajoutée au calculateur
- ✅ **Documents obligatoires affichés** :
  - Facture Commerciale
  - Liste de Colisage
  - Connaissement / LTA
  - Déclaration en Douane
- ✅ **Documents ZLECAf affichés** :
  - Certificat d'Origine ZLECAf
  - Déclaration du Fournisseur
- ✅ **Documents spécifiques au pays** depuis l'API
- ✅ **Avantages fiscaux** listés avec les bénéfices obtenus
- ✅ **Règles d'origine** avec critères à respecter

### Phase 11 : Recherche Intuitive et Sous-positions Nationales (Terminé - 22 Fév 2025)
- ✅ **Recherche par préfixe** : Taper "76" affiche uniquement le chapitre 76 (Aluminium)
- ✅ **En-tête de chapitre** : "📦 Chapitre 76: Aluminium et ouvrages" affiché en haut des résultats
- ✅ **Sous-positions nationales (HS8-HS12)** affichées pour chaque code HS6 :
  - Code complet (ex: 7601102000)
  - Type de position (HS10)
  - Description en français
  - Taux DD
  - Bouton "Utiliser" pour sélection directe
- ✅ **Mode simple amélioré** : Input direct pour le code HS sans recherche obligatoire

### Phase 12 : Refonte Thème Sombre et Contraste (Terminé - 22 Fév 2025)
- ✅ **Thème sombre professionnel** avec accents cuivre (#C17A2B) et or (#D4AF37)
- ✅ **Contraste texte adaptatif** :
  - Texte blanc (#F5F5F5) sur fond sombre (#1B232C)
  - Texte secondaire (#A0AAB4) pour les descriptions
  - Couleurs d'accent pour les titres (or pour standard, vert pour ZLECAf, rouge pour NPF)
- ✅ **Composants Card** adaptés au thème sombre
- ✅ **Formulaires natifs stylisés** :
  - Éléments `<select>` et `<input>` avec fond sombre
  - Bordures dorées au focus
  - Flèche de dropdown personnalisée
- ✅ **Tableaux de taxes** avec bon contraste (texte blanc, fonds semi-transparents)
- ✅ **Graphiques en camembert** avec tooltips adaptés au thème
- ✅ **Section Formalités** avec cartes bien visibles
- ✅ **Toutes les sections de résultats** avec fond sombre uniforme :
  - Tableaux NPF vs ZLECAf
  - Section économies
  - Graphiques en barres et camembert
  - Documents et Formalités
  - Règles d'origine
  - Journal de calcul détaillé

---

## Architecture Technique

### Backend (FastAPI + Python)
```
/app/backend/
├── data/
│   └── {54 fichiers}_tariffs.json   # Données tarifaires authentiques
├── routes/
│   ├── authentic_tariffs.py          # Endpoints tarifs authentiques
│   ├── faostat.py                    # Endpoints FAOSTAT 2024
│   ├── hs6_database.py               # Recherche HS6
│   ├── tariffs_calculation.py        # Calculs tarifaires
│   └── ... (17 modules de routes)
├── services/
│   ├── authentic_tariff_service.py   # Chargement données JSON
│   ├── faostat_service.py            # Service FAOSTAT
│   └── redis_cache_service.py        # Cache Redis
└── server.py
```

### Frontend (React + Shadcn UI)
```
/app/frontend/src/components/
├── calculator/
│   ├── CalculatorTab.jsx              # Avec onglets, Select corrigé, graphiques améliorés
│   ├── MultiCountryComparison.jsx     # Comparaison multi-pays
│   ├── TaxBreakdownChart.jsx          # Graphiques taxes (camembert, barres)
│   └── DetailedCalculationBreakdown.jsx
└── statistics/
    └── ProductionTab.jsx              # Données FAO 2024
```

---

## Endpoints API - Tarifs Authentiques

| Endpoint | Description |
|----------|-------------|
| `GET /api/authentic-tariffs/countries` | 54 pays avec statistiques |
| `GET /api/authentic-tariffs/calculate/{country}/{hs_code}` | Calcul NPF vs ZLECAf avec taxes_detail |
| `GET /api/authentic-tariffs/country/{iso3}/summary` | Résumé tarifs du pays |
| `GET /api/authentic-tariffs/country/{iso3}/taxes/{hs_code}` | Détail des taxes avec intitulés |
| `GET /api/faostat/production` | Données production agricole 2024 |

---

## Tests

### Backend : 100% (12/12 tests passés)
- Liste des 54 pays
- Taxes détaillées avec intitulés
- Calculs NPF vs ZLECAf
- Comparaison multi-pays

### Frontend : 100% (iteration_17 - 22 Fév 2025)
- ✅ Bug Select corrigé - État React mis à jour correctement
- ✅ Calculateur fonctionnel avec tous les champs
- ✅ Comparaison Multi-Pays fonctionnelle
- ✅ Thème sombre avec bon contraste (texte blanc/or sur fond sombre)
- ✅ Tableaux NPF vs ZLECAf bien lisibles
- ✅ Graphiques en camembert avec légendes visibles
- ✅ Section Formalités et Documents complète

---

## Backlog

### P0 - Terminé
- [x] Intégration 54 fichiers tarifs authentiques
- [x] Affichage de toutes les taxes avec intitulés
- [x] Comparaison multi-pays
- [x] Correction bug Select components

### P1 - Priorité Moyenne
- [ ] Finaliser refactoring server.py (supprimer routes dupliquées)
- [ ] Exportation CSV/Excel (feature payante potentielle)

### P2 - Priorité Basse
- [ ] Plus de sources d'actualités pour l'Algérie
- [ ] Tests e2e complets avec Playwright

---

## Historique des Versions

### v2.2.0 (21 Février 2025) - BUG FIX & ENHANCEMENT
- **Bug Fix P0** : Correction des composants Select (menus déroulants) dans CalculatorTab
- **Graphiques améliorés** : Ajout TaxDistributionPieChart pour NPF vs ZLECAf
- **Tests passés** : 100% backend et frontend (iteration_14)

### v2.1.0 (21 Février 2025) - FEATURE
- **Comparaison Multi-Pays** avec sélection par région
- **Affichage TOUTES les taxes** avec codes et intitulés complets
- **Intégration FAOSTAT 2024** pour données production agricole

### v2.0.0 (21 Février 2025) - MAJOR
- **54 pays africains** avec données tarifaires authentiques
- **~315,000 lignes HS6** + **~871,000 sous-positions**

---

## Contacts

- **Développement** : Emergent AI
- **Données** : Administrations douanières africaines
