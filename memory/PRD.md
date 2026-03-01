# ZLECAf Trade Opportunity Finder - Product Requirements Document

## Résumé du Projet

Application d'analyse commerciale pour l'Afrique sous la Zone de Libre-Échange Continentale Africaine (ZLECAf/AfCFTA).

### Vision
Fournir aux entreprises, décideurs et analystes africains un outil complet pour identifier les opportunités commerciales intra-africaines et évaluer les avantages tarifaires de la ZLECAf.

---

## Fonctionnalités Implémentées

### Phase 1-15 : Infrastructure complète (Terminé)
- Base de données HS6 bilingue, Règles d'Origine ZLECAf
- Statistiques OEC 2024, Analyse de Substitution avec Sankey Diagram
- Intelligence Artificielle Gemini, Comparaison Multi-Pays
- 54 fichiers JSON de tarifs nationaux authentiques (~875,000 positions)
- Refactoring backend modulaire (server.py réduit de 93%)

### Phase 16 : Moteur Réglementaire AfCFTA v3 (Terminé - 1 Mars 2025) ✨

**Architecture canonique complète :**
- `/app/engine/` - Nouveau répertoire du moteur réglementaire
- `/app/engine/schemas/canonical_model.py` - Modèles Pydantic standardisés
- `/app/engine/adapters/dza_adapter.py` - Adaptateur Algérie avec méthode de calcul conforme à la Circulaire 419
- `/app/engine/api/engine_service.py` - Service haute performance (< 1ms)
- `/app/engine/pipeline.py` - Pipeline de génération de données

**Données Algérie (DZA) :**
- 16,569 enregistrements canoniques
- Intitulés exacts des taxes : D.D, PRCT, T.C.S (Taxe de Contribution de Solidarité), T.V.A
- Formalités avec autorités émettrices (Ministère du Commerce, Direction des Services Vétérinaires, etc.)
- Avantages fiscaux ZLECAf (exonération DD)

**Nouvel onglet "Réglementation" dans le Calculateur :**
- Interface utilisateur claire avec 3 onglets : Calculateur | Réglementation | Comparaison Multi-Pays
- Affichage des mesures tarifaires avec taux NPF et ZLECAf
- Liste des formalités administratives avec documents et autorités
- Synthèse visuelle : Total NPF, Total ZLECAf, Économies

---

## Architecture Technique

### Backend (FastAPI)
```
/app/backend/
├── data/               # Données tarifaires (54 pays)
│   └── DZA_tariffs.json  # Corrigé : T.C.S = Taxe de Contribution de Solidarité
├── routes/
│   └── regulatory_engine.py  # API Moteur Réglementaire v3
└── server.py           # Point d'entrée (194 lignes)
```

### Engine (Moteur Réglementaire v3)
```
/app/engine/
├── adapters/
│   ├── base_adapter.py     # Classe abstraite
│   └── dza_adapter.py      # Algérie - Conforme Circulaire 419
├── api/
│   └── engine_service.py   # Service O(1) avec index
├── schemas/
│   └── canonical_model.py  # Modèles Pydantic
├── output/
│   ├── DZA_canonical.jsonl # 16,569 enregistrements
│   └── indexes/            # Index pour recherche rapide
└── pipeline.py             # Génération des données
```

### Frontend (React + Shadcn UI)
```
/app/frontend/src/components/calculator/
├── CalculatorTab.jsx           # 3 onglets (Calculateur, Réglementation, Comparaison)
└── RegulatoryDetailsPanel.jsx  # Affichage des données réglementaires
```

---

## API Endpoints - Moteur Réglementaire v3

| Endpoint | Description |
|----------|-------------|
| `GET /api/regulatory-engine/countries` | Liste des pays disponibles (DZA) |
| `GET /api/regulatory-engine/details?country=DZA&code=0101101000` | Détails complets |
| `GET /api/regulatory-engine/details/all?country=DZA&hs6=010110` | Toutes sous-positions |
| `GET /api/regulatory-engine/summary/DZA` | Résumé du pays |

---

## Corrections appliquées (Session actuelle)

1. **T.C.S** : "Taxe de Contrôle Sanitaire" → **"Taxe de Contribution de Solidarité"** ✅
2. **Code 910** : DGD → **Ministère du Commerce** ✅
3. **Code 902** : DGD → **Ministère du Commerce - Inspection du Contrôle aux Frontières** ✅
4. **Nomenclature complète** : 80+ codes documents algériens ajoutés à l'adaptateur

---

## Backlog

### P1 - Priorité Haute
- [ ] Affiner les autorités émettrices par type de produit (agricole vs industriel)
- [ ] Adaptateur Maroc (MAR) pour le Moteur Réglementaire
- [ ] Intégration des données réglementaires dans le calculateur principal

### P2 - Priorité Moyenne
- [ ] Extension aux 54 pays africains
- [ ] Migration vers PostgreSQL pour scalabilité
- [ ] Export CSV/Excel des données canoniques

### P3 - Priorité Basse
- [ ] Tests e2e complets avec Playwright
- [ ] Documentation API OpenAPI

---

## Historique des Versions

### v3.1.1 (1 Mars 2025) - CORRECTIONS INTITULÉS
- T.C.S corrigé : Taxe de Contribution de Solidarité
- Autorités émettrices corrigées (codes 910, 902)
- Nomenclature complète des codes documents DZA

### v3.1.0 (1 Mars 2025) - MOTEUR RÉGLEMENTAIRE v3
- Nouveau Moteur Réglementaire Canonique
- Algérie (DZA) : 16,569 enregistrements
- Nouvel onglet "Réglementation" dans le Calculateur
- Performance < 1ms par requête

### v3.0.0 (27 Février 2025) - REFACTORING MAJEUR
- server.py refactorisé : 2920 → 194 lignes (-93%)

---

## Contact
- **Développement** : Emergent AI
- **Données** : Administrations douanières africaines (Circulaire 419 DGD Algérie)
