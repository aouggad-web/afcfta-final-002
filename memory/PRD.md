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

---

## Architecture Technique

### Backend (FastAPI + Python)
```
/app/backend/
├── data/
│   └── {54 fichiers}_tariffs.json   # Données tarifaires authentiques
├── routes/
│   ├── authentic_tariffs.py          # Endpoints tarifs authentiques
│   ├── hs6_database.py               # Recherche HS6
│   ├── tariffs_calculation.py        # Calculs tarifaires
│   └── ... (17 modules de routes)
├── services/
│   ├── authentic_tariff_service.py   # Chargement données JSON
│   ├── redis_cache_service.py        # Cache Redis
│   └── ...
└── server.py
```

### Frontend (React + Shadcn UI)
```
/app/frontend/src/components/
├── calculator/
│   ├── CalculatorTab.jsx              # Avec onglets et tableau taxes
│   ├── MultiCountryComparison.jsx     # Comparaison multi-pays
│   ├── TaxBreakdownChart.jsx          # Graphiques taxes
│   └── DetailedCalculationBreakdown.jsx
└── ...
```

---

## Endpoints API - Tarifs Authentiques

| Endpoint | Description |
|----------|-------------|
| `GET /api/authentic-tariffs/countries` | 54 pays avec statistiques |
| `GET /api/authentic-tariffs/calculate/{country}/{hs_code}` | Calcul NPF vs ZLECAf avec taxes_detail |
| `GET /api/authentic-tariffs/country/{iso3}/summary` | Résumé tarifs du pays |
| `GET /api/authentic-tariffs/country/{iso3}/taxes/{hs_code}` | Détail des taxes avec intitulés |
| `GET /api/authentic-tariffs/search/{country}?q=` | Recherche produits |

---

## Tests

### Backend : 100% (12/12 tests passés)
- Liste des 54 pays
- Taxes détaillées avec intitulés
- Calculs NPF vs ZLECAf
- Comparaison multi-pays

### Frontend : Fonctionnel
- Comparaison Multi-Pays : ✅ 100%
- Calculateur standard : ✅ Fonctionnel

---

## Backlog

### P0 - Terminé
- [x] Intégration 54 fichiers tarifs authentiques
- [x] Affichage de toutes les taxes avec intitulés
- [x] Comparaison multi-pays

### P1 - Priorité Moyenne
- [ ] Exportation CSV/Excel (feature payante potentielle)
- [ ] Amélioration des graphiques

### P2 - Priorité Basse
- [ ] Plus de sources d'actualités pour l'Algérie
- [ ] Tests e2e complets avec Playwright

---

## Historique des Versions

### v2.1.0 (21 Février 2025) - FEATURE
- **Comparaison Multi-Pays** avec sélection par région
- **Affichage TOUTES les taxes** avec codes et intitulés complets
- **Refactoring routes backend** : hs6_database.py, tariffs_calculation.py
- **Graphiques améliorés** : tableau détaillé NPF vs ZLECAf

### v2.0.0 (21 Février 2025) - MAJOR
- **54 pays africains** avec données tarifaires authentiques
- **~315,000 lignes HS6** + **~871,000 sous-positions**

---

## Contacts

- **Développement** : Emergent AI
- **Données** : Administrations douanières africaines
