# État de l'application — à déployer sur Emergent

> Document de passation : décrit l'état **actuel de `main`** sur GitHub et la
> procédure pour l'envoyer sur Emergent. À jour au commit de merge de ce fichier.

## 1. Où récupérer le code

- **Dépôt** : `aouggad-web/afcfta-final-002`
- **Branche à déployer** : `main`
- Tout le travail (module Opportunités complet, macro World Bank, OEC gratuit,
  correctifs) est **mergé dans `main`** (PR #181, #182, #187).

## 2. Déploiement Emergent — une commande

Dans le **Shell Emergent** du projet :

```bash
BRANCH=main bash sync_emergent.sh
```

Ce script (à la racine) : aligne le déploiement **exactement** sur `main`
(`git reset --hard` — supprime tout fichier périmé), **vérifie la présence des
modules critiques** (refuse de démarrer s'il en manque un), réinstalle le
backend, contrôle les imports du moteur, reconstruit le frontend, arrête
proprement les serveurs. → règle le bug `No module named 'services.regional_blocs'`
(qui venait d'un déploiement partiel, pas du code).

Puis démarrer :

```bash
bash start.sh                 # dev : backend 8000 + Vite 5000 (aperçu web)
# ou production mono-processus (FastAPI sert l'API ET le frontend buildé) :
cd backend && python -m uvicorn server:app --host 0.0.0.0 --port 5000
```

Vérifier :

```bash
curl -s http://localhost:8000/api/reports/health      # sources du moteur
curl -s http://localhost:8000/api/reports/oec-health   # → statistics_free.reachable: true
```

## 3. Modules — tous présents et vérifiés live

| Module | Endpoint principal | État |
|---|---|---|
| Calculateur | `POST /api/calculate-tariff` | ✅ ZLECAf réel (réciprocité, unions douanières) |
| Statistiques | `/api/statistics/*`, recherche SH2/4/6 OEC | ✅ canal OEC gratuit |
| Production | `/api/production/*` (FAOSTAT/USGS/UNIDO) | ✅ |
| Logistique | `/api/logistics/*` (ports, corridors, fret) | ✅ |
| Règles d'origine | `/api/rules-of-origin/*` | ✅ 96 chapitres |
| Dashboard / Profils Pays | `/api/country-profile/{iso3}` | ✅ WDI 2024 |
| **Opportunités** | `/api/reports/*` | ✅ S1/S2/S3/S4 + bilatéral ultra-fin |

## 4. Module Opportunités — interconnexion (le cœur métier)

Pour l'import comme l'export, il combine tous les modules :

- **S1** transformation : `/api/reports/transformation`
- **S2** export direct (marchés classés pour un producteur) : `/api/reports/direct-export`
- **S3** besoin national : `/api/reports/national-need`
- **S4** opportunités d'importation (quels produits sourcer, de qui, avec quel
  avantage ZLECAf) : `/api/reports/import-opportunities`
- **Bilatéral ultra-fin** : `/api/reports/opportunity?...&mode=ultra_fine`

Sources réelles branchées : tarif = moteur du **Calculateur** ; demande = **OEC
gratuit** (Statistiques) ; offre = **Production** ; logistique = corridors/fret ;
PIB/hab (L3) + réserves + couverture imports = **Profils Pays** + datasets World
Bank committés. Discipline zéro-fabrication : estimations étiquetées, données
manquantes marquées indisponibles (jamais inventées).

## 5. Points de configuration

- **OEC** : aucun token requis (canal gratuit du module Statistiques). Un
  `OEC_API_TOKEN` optionnel active la demande OEC premium mais n'est pas nécessaire.
- **Réseau** : Emergent a le réseau ouvert → OEC et World Bank répondent.
- **Cache** : Redis si disponible, sinon mémoire (dégradation automatique).
- **World Bank** : datasets `data/json/wb_gdp_pc.json` / `wb_reserves.json` déjà
  committés ; rafraîchissables via le workflow Actions « Module Opportunités ».

## 6. Qualité

- **67 tests** backend verts (`backend/tests/test_report_engine.py`).
- CI GitHub verte (lint, tests, build frontend, marqueurs de conflit).
- Guides : `docs/DEPLOYER_SUR_EMERGENT.md`, `docs/ESSAYER_SUR_REPLIT.md`,
  `docs/EXECUTER_DEPUIS_GITHUB.md` ; appels prêts dans `requests.http`.
