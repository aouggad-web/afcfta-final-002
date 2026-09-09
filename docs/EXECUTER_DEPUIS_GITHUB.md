# Exécuter le module Opportunités depuis GitHub

Deux voies, complémentaires : **Codespaces** (environnement interactif complet,
UI comprise) et **GitHub Actions** (exécution en un clic, rapports téléchargeables).
Dans les deux cas le réseau est ouvert : l'API World Bank répond, et l'OEC aussi
(token optionnel) — contrairement aux bacs à sable où ces API sont bloquées.

## 1. GitHub Codespaces (interactif : backend + frontend + UI)

1. Sur GitHub : **Code ▸ Codespaces ▸ Create codespace** sur la branche voulue
   (`claude/opportunites-scenario-s2` tant que la PR #182 n'est pas mergée).
2. Le devcontainer (`.devcontainer/`) prépare tout automatiquement :
   dépendances Python + Node, `backend/.env` (SECRET_KEY aléatoire,
   `PUBLIC_DATA_ACCESS=true`) et `frontend/.env` (backend en même origine via le
   proxy Vite `/api` → `localhost:8000` — fonctionne aussi dans le navigateur
   Codespaces, sans exposer le port 8000).
3. Lancer (deux terminaux) :
   ```bash
   cd backend && python -m uvicorn server:app --reload --port 8000
   cd frontend && yarn start        # port 5000, prévisualisation auto
   ```
4. Ouvrir le port 5000 (onglet *Ports*) → onglet **Opportunités** de l'UI.
   Les appels API prêts à l'emploi sont dans `requests.http` (extension REST
   Client incluse dans le devcontainer).
5. Optionnel — activer L3 + réserves :
   ```bash
   cd backend && python -m etl.fetch_wb_gdp && python -m etl.fetch_wb_reserves
   ```
6. Optionnel — OEC avec token : ajouter `OEC_API_TOKEN=...` dans `backend/.env`
   (ou un secret Codespaces `OEC_API_TOKEN`), puis vérifier via
   `GET /api/reports/oec-health` (attendu `"reachable": true`).

## 2. GitHub Actions (un clic : ETL + smoke-test + rapports en artefacts)

Workflow **« Module Opportunités — Exécution »**
(`.github/workflows/opportunites_module.yml`), déclenchement manuel :

1. Onglet **Actions ▸ Module Opportunités — Exécution ▸ Run workflow**.
2. Choisir la branche et les paramètres (défauts = exemple noix de cajou) :
   - `hs_code` : `080131` (cajou brut en coque ; décortiqué : `080132`)
   - `producer` : `GNB` (Guinée-Bissau)
   - `destination` : `DZA` (Algérie) — vide = meilleur marché classé par S2
   - `top_k` : `5` marchés analysés en profondeur
   - `run_wb_etl` : lance les ETL World Bank (PIB/hab + réserves)
   - `commit_wb_data` : committe les datasets WB produits sur la branche
     (sinon ils ne vivent que dans l'artefact)
3. Le job : installe le backend → ETL WB → démarre l'API → déroule
   `backend/scripts/smoke_opportunites.py` (santé moteur, diagnostic OEC,
   **S2** marchés classés, **S3** besoin national de la destination,
   **rapport bilatéral ultra-fin** producteur → destination).
4. Récupérer l'artefact `opportunites-<hs_code>-<producer>` : les 5 réponses
   JSON complètes, les datasets WB et le log du backend.

Secret optionnel `OEC_API_TOKEN` (Settings ▸ Secrets ▸ Actions) : active la
demande OEC réelle (composante `market_potential` du score, imports observés).
Sans lui, l'OEC tier gratuit est tenté ; s'il ne répond pas, le module dégrade
gracieusement (composante exclue, jamais estimée).

## 3. Le même smoke-test, partout

`backend/scripts/smoke_opportunites.py` est utilisable tel quel en local,
Codespaces ou CI (backend déjà démarré) :

```bash
cd backend
python -m scripts.smoke_opportunites                      # défauts : 080131 / GNB, meilleur marché S2
python -m scripts.smoke_opportunites --destination DZA    # force GNB → Algérie
python -m scripts.smoke_opportunites --hs-code 080132 --producer CIV --top-k 3
```

Sortie : résumé lisible + réponses JSON dans `test_reports/smoke_opportunites/`.
Code retour 0 si tous les appels HTTP passent ; l'OEC injoignable n'est **pas**
un échec (dégradation gracieuse assumée).

Exemple déroulé et commenté : `docs/EXEMPLE_CAJOU_GNB.md`.
