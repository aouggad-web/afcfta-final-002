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

### Phase 1 : Infrastructure de Base (Terminé)
- [x] Base de données HS6 complète bilingue (FR/EN)
- [x] Règles d'Origine (RoO) spécifiques ZLECAf
- [x] Gestion des tarifs douaniers nationaux
- [x] Profils pays détaillés avec indicateurs économiques

### Phase 2 : Intégration API OEC (Terminé)
- [x] Statistiques commerciales en temps réel via API OEC
- [x] Commerce bilatéral entre pays africains
- [x] Top produits exportés/importés par pays
- [x] Mise à jour vers données OEC 2024

### Phase 3 : Analyse de Substitution (Terminé)
- [x] Service d'analyse avec données réelles OEC
- [x] Identification des fournisseurs africains potentiels
- [x] Calcul des potentiels de substitution

### Phase 4 : Intelligence Artificielle Gemini (Terminé)
- [x] Intégration Google Gemini via Emergent LLM Key
- [x] Analyse IA des opportunités d'export/import
- [x] Cache Redis pour performances optimales (550x faster)
- [x] Indicateur de fraîcheur des données

### Phase 5 : Comparaison Multi-Pays (Terminé)
- [x] Radar chart comparatif
- [x] Tableaux d'indicateurs économiques
- [x] Commerce intra-africain vs mondial

### Phase 6 : Données Tarifaires Authentiques (Terminé - 21 Fév 2025)
- [x] **49 fichiers JSON de tarifs nationaux authentiques**
- [x] **~5800 lignes tarifaires HS6 par pays**
- [x] **~16000 sous-positions nationales (HS8-HS10) par pays**
- [x] **Taxes détaillées : DD, TVA, TPI, CEDEAO, CISS, etc.**
- [x] **Avantages fiscaux ZLECAf intégrés**
- [x] **Formalités administratives requises**
- [x] **API complète /api/authentic-tariffs/*

---

## Architecture Technique

### Backend (FastAPI + Python)
```
/app/backend/
├── data/
│   ├── AGO_tariffs.json     # Angola
│   ├── BDI_tariffs.json     # Burundi
│   ├── ... (49 fichiers)
│   └── ZWE_tariffs.json     # Zimbabwe
├── routes/
│   ├── authentic_tariffs.py  # NEW - Endpoints tarifs authentiques
│   ├── gemini_analysis.py    # API IA Gemini
│   ├── oec.py                # API statistiques OEC
│   └── ...
├── services/
│   ├── authentic_tariff_service.py  # NEW - Chargement données JSON
│   ├── redis_cache_service.py       # Cache Redis
│   ├── gemini_trade_service.py
│   └── ...
└── server.py
```

### Frontend (React + Shadcn UI)
```
/app/frontend/src/components/
├── calculator/
│   ├── CalculatorTab.jsx              # UPDATED - Utilise données authentiques
│   └── DetailedCalculationBreakdown.jsx
├── opportunities/
│   ├── AIAnalysis.jsx
│   └── SubstitutionAnalysis.jsx
├── statistics/
│   ├── StatisticsTab.jsx
│   └── MultiCountryComparison.jsx
└── ui/
    └── data-freshness-indicator.jsx
```

---

## Intégrations Tierces

| Service | Utilisation | Clé |
|---------|-------------|-----|
| **Google Gemini** | Analyse IA intelligente | Emergent LLM Key |
| **Redis** | Cache performant | Local |
| **API OEC** | Données commerciales 2024 | Gratuit |
| **MongoDB** | Base de données | Local |

---

## Endpoints API - Tarifs Authentiques (NEW)

### Liste des pays
- `GET /api/authentic-tariffs/countries` - 49 pays avec statistiques

### Calcul de tarifs
- `GET /api/authentic-tariffs/calculate/{country}/{hs_code}?value=X` - Calcul NPF vs ZLECAf

### Données par pays
- `GET /api/authentic-tariffs/country/{iso3}/summary` - Résumé tarifs du pays
- `GET /api/authentic-tariffs/country/{iso3}/line/{hs_code}` - Ligne tarifaire complète
- `GET /api/authentic-tariffs/country/{iso3}/sub-positions/{hs6}` - Sous-positions nationales
- `GET /api/authentic-tariffs/country/{iso3}/taxes/{hs_code}` - Détail des taxes
- `GET /api/authentic-tariffs/country/{iso3}/advantages/{hs_code}` - Avantages fiscaux
- `GET /api/authentic-tariffs/country/{iso3}/formalities/{hs_code}` - Formalités administratives

### Recherche
- `GET /api/authentic-tariffs/search/{country}?q=cacao` - Recherche produits

---

## Structure des Données Authentiques

```json
{
  "country_code": "MAR",
  "data_format": "enhanced_v2",
  "summary": {
    "total_tariff_lines": 5831,
    "total_sub_positions": 16145,
    "vat_rate_pct": 20.0,
    "dd_rate_range": {"min": 0, "max": 40, "avg": 12.01}
  },
  "tariff_lines": [
    {
      "hs6": "180100",
      "description_fr": "Cacao en fèves",
      "description_en": "Cocoa beans",
      "dd_rate": 10.0,
      "vat_rate": 20.0,
      "taxes_detail": [...],
      "fiscal_advantages": [...],
      "administrative_formalities": [...],
      "sub_positions": [...]
    }
  ]
}
```

---

## Backlog

### P0 - Terminé
- [x] Intégration 49 fichiers tarifs authentiques (21 Fév 2025)
- [x] APIs backend /api/authentic-tariffs/*
- [x] Frontend CalculatorTab utilise données authentiques

### P1 - Priorité Moyenne
- [ ] Finaliser refactoring server.py (50+ routes à migrer)
- [ ] Améliorer graphiques dans calculateur
- [ ] Tests e2e complets avec Playwright

### P2 - Priorité Basse
- [ ] Exportation CSV/Excel
- [ ] Intégrer les 5 pays restants (DZA, ETH, SDN, SOM, STP)
- [ ] Plus de sources d'actualités pour l'Algérie

---

## Historique des Versions

### v2.0.0 (21 Février 2025) - MAJOR
- **DONNÉES TARIFAIRES AUTHENTIQUES INTÉGRÉES**
  - 49 fichiers JSON avec tarifs officiels
  - ~5800 lignes HS6 par pays
  - ~16000 sous-positions nationales par pays
  - Taxes détaillées (DD, TVA, TPI, CEDEAO, CISS...)
  - Avantages fiscaux ZLECAf
  - Formalités administratives
- **Nouveaux endpoints API** :
  - `GET /api/authentic-tariffs/countries`
  - `GET /api/authentic-tariffs/calculate/{country}/{hs_code}`
  - `GET /api/authentic-tariffs/country/{iso3}/summary`
  - `GET /api/authentic-tariffs/search/{country}?q=...`
- **Frontend mis à jour** :
  - CalculatorTab utilise données authentiques en priorité
  - Badge "Données Tarifaires Officielles" affiché
  - Détail des taxes et avantages fiscaux
  - Formalités administratives requises

### v1.8.0 (6 Février 2025)
- Calculateur amélioré avec détails NPF vs ZLECAf
- Mise à jour OEC vers données 2024

### v1.7.0 (5 Février 2025)
- Refactoring Frontend StatisticsTab
- Comparaison Multi-Pays avec Radar chart

### v1.6.0 (4 Février 2025)
- Cache Redis intégré (amélioration 550x)
- Indicateur de fraîcheur des données

---

## Contacts

- **Développement** : Emergent AI
- **Données** : Administrations douanières africaines, IMF, UNCTAD, OEC
