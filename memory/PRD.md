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

### Phase 7-12 : Améliorations Calculateur et UI (Terminé - 22 Fév 2025)
- Affichage de TOUTES les taxes avec leurs intitulés
- Comparaison Multi-Pays avec sélection par région
- Thème sombre professionnel uniforme
- Formalités et Documents Nécessaires

### Phase 13-14 : Amélioration UI Profils Pays et Sankey Diagram (Terminé - 26 Fév 2025)
- Thème sombre appliqué aux indicateurs World Bank Data360
- TradeSankeyDiagram intégré dans l'onglet Substitution

### Phase 15 : Refactoring server.py (Terminé - 27 Fév 2025)
- **Réduction massive** : 2920 lignes → 194 lignes (-93%)
- Architecture modulaire avec tous les endpoints dans `/routes/`

### Phase 16 : Moteur Réglementaire AfCFTA v3 (Terminé - 1 Mars 2025) ✨ NOUVEAU
- **Architecture canonique complète** :
  - `/app/engine/` - Nouveau répertoire du moteur réglementaire
  - `/app/engine/schemas/canonical_model.py` - Modèles Pydantic standardisés
  - `/app/engine/adapters/` - Adaptateurs par pays (DZA implémenté)
  - `/app/engine/api/engine_service.py` - Service haute performance
  - `/app/engine/pipeline.py` - Pipeline de génération de données
- **Données Algérie (DZA)** : 16,569 enregistrements canoniques générés
- **API REST** : 4 nouveaux endpoints `/api/regulatory-engine/*`
- **Performance** : Recherche O(1) via index pré-construits (< 5ms)
- **Bug Fix** : Barre de recherche HS corrigée (paramètre `q` + fichier `hs6_database.json`)

---

## Architecture Technique

### Backend (FastAPI + Python)
```
/app/backend/
├── data/
│   └── {54 fichiers}_tariffs.json   # Données tarifaires authentiques
├── routes/
│   ├── regulatory_engine.py          # ✨ NOUVEAU - API Moteur Réglementaire v3
│   ├── authentic_tariffs.py          # Endpoints tarifs authentiques
│   ├── calculator.py                 # Calculateur principal
│   └── ... (20+ modules de routes)
├── services/
│   └── ... (services métier)
└── server.py                         # Point d'entrée léger (194 lignes)
```

### Engine (Moteur Réglementaire v3) ✨ NOUVEAU
```
/app/engine/
├── adapters/
│   ├── base_adapter.py              # Classe de base abstraite
│   └── dza_adapter.py               # Adaptateur Algérie
├── api/
│   └── engine_service.py            # Service de requêtes haute performance
├── schemas/
│   └── canonical_model.py           # Modèles Pydantic canoniques
├── output/
│   ├── DZA_canonical.jsonl          # 16,569 enregistrements (37 MB)
│   ├── DZA_summary.json             # Résumé du pays
│   └── indexes/
│       ├── DZA_index_national.json  # Index par code national (1 MB)
│       ├── DZA_index_hs6.json       # Index par HS6 (850 KB)
│       └── countries_index.json     # Liste des pays disponibles
└── pipeline.py                      # Script de génération
```

### Frontend (React + Shadcn UI)
```
/app/frontend/src/components/
├── calculator/
│   ├── CalculatorTab.jsx              # Avec onglets et graphiques
│   ├── SmartHSSearch.jsx              # ✅ Bug corrigé (paramètre q)
│   └── MultiCountryComparison.jsx
└── ...
```

---

## API Endpoints - Moteur Réglementaire v3 ✨ NOUVEAU

| Endpoint | Description |
|----------|-------------|
| `GET /api/regulatory-engine/countries` | Liste des pays disponibles |
| `GET /api/regulatory-engine/details?country=DZA&code=0101101000` | Détails complets pour un code national |
| `GET /api/regulatory-engine/details/all?country=DZA&hs6=010110` | Toutes les sous-positions d'un HS6 |
| `GET /api/regulatory-engine/summary/{country}` | Résumé des données d'un pays |

### Exemple de réponse `/api/regulatory-engine/details`
```json
{
  "success": true,
  "country_iso3": "DZA",
  "code": "0101101000",
  "hs6": "010110",
  "commodity": {
    "national_code": "0101101000",
    "description_fr": "Chevaux reproducteurs - Reproduction",
    "digits": 10,
    "chapter": "01"
  },
  "measures": [
    {"code": "D.D", "name_fr": "Droit de Douane", "rate_pct": 5.0, "zlecaf_rate_pct": 0.0},
    {"code": "T.V.A", "name_fr": "Taxe sur la Valeur Ajoutée", "rate_pct": 9.0},
    {"code": "PRCT", "name_fr": "Prélèvement Compensation Transport", "rate_pct": 2.0},
    {"code": "T.C.S", "name_fr": "Taxe de Contrôle Sanitaire", "rate_pct": 3.0}
  ],
  "requirements": [
    {"code": "910", "document_fr": "Déclaration d'Importation", "issuing_authority": "DGD"},
    {"code": "216", "document_fr": "Certificat Sanitaire Vétérinaire", "issuing_authority": "DSV"}
  ],
  "fiscal_advantages": [
    {"tax_code": "D.D", "reduced_rate_pct": 0.0, "condition_fr": "Certificat d'Origine ZLECAf"}
  ],
  "total_npf_pct": 19.0,
  "total_zlecaf_pct": 14.0,
  "savings_pct": 5.0,
  "processing_time_ms": 3.17
}
```

---

## Backlog

### P0 - Terminé ✅
- [x] Intégration 54 fichiers tarifs authentiques
- [x] Moteur Réglementaire v3 - Adaptateur DZA
- [x] Bug fix barre de recherche HS

### P1 - Priorité Haute
- [ ] Adaptateur Maroc (MAR) pour le Moteur Réglementaire
- [ ] Intégration frontend du Moteur Réglementaire (affichage des données canoniques)
- [ ] Étendre le moteur aux 54 pays africains

### P2 - Priorité Moyenne
- [ ] Migration vers PostgreSQL pour le moteur (scalabilité)
- [ ] API de comparaison multi-pays via le moteur réglementaire
- [ ] Exportation CSV/Excel des données canoniques

### P3 - Priorité Basse
- [ ] Tests e2e complets avec Playwright
- [ ] Documentation API OpenAPI complète

---

## Historique des Versions

### v3.1.0 (1 Mars 2025) - MOTEUR RÉGLEMENTAIRE v3 ✨
- **Nouveau Moteur Réglementaire Canonique** :
  - Architecture modulaire avec adaptateurs par pays
  - Pipeline de génération de données JSONL
  - Index haute performance (recherche O(1))
  - 4 nouveaux endpoints API REST
- **Algérie (DZA) implémentée** : 16,569 enregistrements, 98 chapitres HS
- **Bug Fix** : Barre de recherche HS fonctionnelle

### v3.0.0 (27 Février 2025) - REFACTORING MAJEUR
- server.py refactorisé : 2920 → 194 lignes (-93%)
- Architecture modulaire avec `/routes/`

### v2.3.1 (26 Février 2025) - FEATURE
- TradeSankeyDiagram intégré dans Substitution
- Correction OpportunityCard pour modes import/export

### v2.3.0 (26 Février 2025) - UI/UX
- Thème sombre appliqué à tous les indicateurs
- Cohérence visuelle complète

---

## Contacts

- **Développement** : Emergent AI
- **Données** : Administrations douanières africaines
