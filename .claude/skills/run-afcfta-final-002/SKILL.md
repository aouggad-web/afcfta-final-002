---
name: run-afcfta-final-002
description: Build, run, test and drive the AfCFTA tariff calculator (FastAPI backend + Vite/React frontend). Use when asked to start/run/launch the app or the backend, call POST /api/calcul, take a screenshot of the calculator, drive a calculation in the browser, or run its tests. Lancer, démarrer, tester, capturer le calculateur.
---

Le backend FastAPI (`backend/`, port 8000) se teste avec `smoke.sh` (curl, jeton CSRF compris) ; l'écran (Vite, port 5000, qui relaie `/api` vers 8000) se pilote avec `driver.mjs` (Playwright, Chromium sans écran). Les deux sont dans `.claude/skills/run-afcfta-final-002/`. Tous les chemins sont relatifs à la racine du dépôt.

## Prérequis

Python 3.11, Node 22 et yarn 1.22 ; Playwright et Chromium sont préinstallés dans ce conteneur (Playwright global, `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`) : `driver.mjs` charge l'installation globale. Ne lancez pas `playwright install`.

## Installation (une fois par clone, ~3 min 30)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt && .venv/bin/pip install pytest feedparser aiohttp pandas numpy
.venv/bin/python scripts/normalize_crawled.py   # couche normalisée, 2,2 Go
.venv/bin/python scripts/build_socle.py         # socle de calcul, 385 Mo — les deux : ~2 min 30
git checkout backend/socle/MANIFESTE.json       # clone non modifié : seule la date de construction a changé
(cd frontend && yarn install --frozen-lockfile)
```

Ces données dérivées ne sont pas versionnées (`.gitignore`) ; la CI les régénère de la même façon. À refaire après toute modification de `backend/data/crawled/` — et alors **ne restaurez pas** `MANIFESTE.json` (voir Pièges).

## Lancer et piloter (chemin agent)

```bash
(cd backend && nohup ../.venv/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8000 > /tmp/afcfta-backend.log 2>&1 &)
timeout 180 bash -c 'until curl -sf http://127.0.0.1:8000/api/health >/dev/null; do sleep 1; done'
.claude/skills/run-afcfta-final-002/smoke.sh                       # DZA 0201101100, origine TUN
.claude/skills/run-afcfta-final-002/smoke.sh TUN 0201100001 MAR    # destination code origine [cif]
```

`smoke.sh` affiche le statut HTTP, la désignation, l'état NPF (COMPLET, INDICATIF, PARTIEL ou INDISPONIBLE), le total des droits et le total à payer, les lignes NPF et les manques ; sans bloc `npf`, les 600 premiers caractères de la réponse. Il sort en erreur si HTTP ≠ 200.

```bash
(cd frontend && nohup yarn dev > /tmp/afcfta-frontend.log 2>&1 &)
timeout 120 bash -c 'until curl -sf http://127.0.0.1:5000/ >/dev/null; do sleep 1; done'
node .claude/skills/run-afcfta-final-002/driver.mjs calcul                                  # Tunisie → Algérie, 0201101100
node .claude/skills/run-afcfta-final-002/driver.mjs calcul Maroc Tunisie 0201100001 10000   # origine destination code cif
node .claude/skills/run-afcfta-final-002/driver.mjs page dashboard                          # capture d'un onglet
```

| commande | effet |
|---|---|
| `calcul [origine] [destination] [code] [cif]` | onglet Calculateur, choisit les pays (début du nom affiché), saisit le code en « Mode simple », calcule, attend la fin de tous les appels ; captures `saisie.png` (fenêtre 1400×1000) et `resultat.png` (pleine page) |
| `page [onglet]` | capture pleine page d'un onglet (`dashboard`, `calculator`, `stats`, `tools`, `roo`, …) → `page.png` |

Captures dans `/tmp/afcfta-shots/` (variable `SHOTS`). Le script imprime ensuite les réponses `/api` reçues avec leur statut, puis les erreurs de la console. **Ouvrez la capture** : un calcul en échec s'affiche aussi.

Arrêt :

```bash
lsof -ti:5000 -sTCP:LISTEN | xargs -r kill
lsof -ti:8000 -sTCP:LISTEN | xargs -r kill
git checkout backend/data/news_cache.json   # réécrit par le tableau de bord (voir Pièges)
```

## Appel direct, sans serveur

La route `/calcul` est une fonction : on l'appelle depuis `backend/`, sans middleware ni jeton (~4 s, chargement du socle compris). L'import imprime une quinzaine de lignes de journal (Redis refusé, `ANTHROPIC_API_KEY` absente, PostgreSQL indisponible) : seule la dernière ligne est le résultat.

```bash
(cd backend && PYTHONPATH=.. ../.venv/bin/python -c "
from routes.calcul import calcul, DemandeCalcul
r = calcul(DemandeCalcul(destination='DZA', origine='TUN', code_sh='0201101100', valeur_cif=10000, devise_cif='USD'))
print(r['position']['designation'], r['npf']['etat'], r['npf']['total_droits'], [(l['code'], l['taux_pct']) for l in r['npf']['lignes']])
")
```

## Tests

```bash
.venv/bin/python -m pytest backend/tests/test_calcul_moteur.py -q -p no:cacheprovider     # moteur, < 1 s
lsof -ti:8000 -sTCP:LISTEN | xargs -r kill                                                 # la suite de la CI se lance backend arrêté
.venv/bin/python -m pytest tests/test_health_endpoint.py tests/test_north_africa_uma.py backend/tests/ -q -p no:cacheprovider --ignore=backend/tests/test_notifications.py   # suite de la CI, ~11 min
(cd frontend && yarn test)                                                                  # vitest, ~30 s
.venv/bin/pip install flake8==7.3.0 && .venv/bin/python -m flake8 .                        # porte lint de la CI
```

Attendu : 3480 passed, 437 skipped, 0 failed pour la suite de la CI ; 365 tests vitest.

## Pièges

- **La suite de la CI échoue si un backend écoute sur 8000 ou 8001.** `backend/tests/conftest.py` sonde `REACT_APP_BACKEND_URL`, puis `localhost:8001` et `localhost:8000` : si un serveur répond, une douzaine de modules d'intégration (`test_hs6_extended_api`, `test_regulatory_engine`, `test_rules_of_origin`…) tournent contre lui au lieu d'être sautés comme en CI, et échouent (~129 échecs en 429, 503 et 404).
- **L'écran ne liquide pas tous les pays par le même chemin.** Les pays de `SOCLE_EN_PREMIER` (`CalculatorTab.jsx`, aujourd'hui `TUN` et `MUS`) passent d'abord par `POST /api/calcul`, avec repli sur `GET /api/authentic-tariffs/calculate/<ISO>/<code>` si le socle répond 404 ou 503. Les autres, Algérie comprise, passent d'abord par ce GET, et ne retombent sur `POST /api/calcul` que sur un 404 ou un 422 `CALCULATION_UNAVAILABLE`, `VALEUR_FOB_REQUISE` ou `PAYS_EXPEDITION_REQUIS`. Une modification de `services/calcul.py` ne se voit donc à l'écran, pour ces pays-là, que dans ces cas : vérifiez-la avec `smoke.sh` ou l'appel direct. La liste des réponses imprimée par `driver.mjs` dit quel chemin a servi.
- **Toute requête non sûre (POST, PUT, PATCH, DELETE) exige un jeton CSRF** (double soumission), sauf quelques chemins exemptés (`/api/health`, webhooks de paiement) : le cookie `csrf_token`, posé par un GET qui n'en porte pas encore, doit revenir à l'identique dans l'en-tête `X-CSRF-Token`. Un `curl -X POST` nu sur `/api/calcul` répond 403 `{"detail":"CSRF token missing"}`. `smoke.sh` fait l'aller-retour.
- **Attendre la fin du calcul, pas le premier résultat.** Sur le chemin `POST /api/calcul`, le résultat s'affiche avant que les formalités soient demandées (`GET /api/authentic-tariffs/country/<ISO>/formalities/<code>`) : une capture trop tôt montre « Formalités non établies » là où la position en porte. `driver.mjs` attend que le bouton « Calculer » se réactive.
- **La recherche intelligente ne retrouve presque rien ici** : son moteur lit `tariff_engine/normalized/*.csv`, absent du dépôt et non produit par l'installation. Seuls répondent les codes nationaux algériens de 8 chiffres ou plus (`backend/data/DZA_nomenclature_map.json`), quel que soit le pays choisi. `driver.mjs` passe donc en « Mode simple », qui accepte tout code de 6 à 12 chiffres.
- **Ne définissez ni `VITE_BACKEND_URL` ni `REACT_APP_BACKEND_URL` en local** (shell ou `frontend/.env` : ne copiez pas `frontend/.env.example`). Sans elles, le navigateur appelle `/api` sur le port 5000 et Vite relaie vers 8000 (même origine, aucun réglage CORS). Avec elles, le navigateur appelle le backend directement, et CORS refuse toute origine absente de `ALLOWED_ORIGINS` (par défaut `localhost` sur 3000, 5000 et 8000 seulement) : la liste des pays reste vide.
- **`build_socle.py` réécrit tout `MANIFESTE.json`** (date, empreintes, compteurs). Sur un clone non modifié, seule la date change : restaurez-le. Après une modification de `backend/data/crawled/`, gardez le manifeste reconstruit : restauré, il porterait les anciennes empreintes, et le backend refuserait de servir ces pays (503 `SocleIndisponible`).
- **Sans `MONGO_URL`, le backend tourne sans base**, mais `/api/health` répond quand même `"database":"connected"` (le journal dit `MONGO_URL not set. Running without database.`). Les comptes sont indisponibles : `GET /api/auth/me` répond 503.
- **`backend/data/news_cache.json`, fichier versionné, est réécrit** au premier `GET /api/news…` dès que son `last_update` a plus de 24 h : c'est ce que fait le tableau de bord, donc toute ouverture de l'écran, `driver.mjs` compris (`smoke.sh` seul ne le touche pas). Restaurez-le avant de committer.
- **Bruit attendu dans la console**, sans lien avec un calcul : `fonts.googleapis.com` en `ERR_CERT_AUTHORITY_INVALID` (proxy du conteneur), 503 sur `/api/auth/me`, 403 `upgrade_required` sur `/api/tariff-data/<ISO>` (formule « free ») et son écho `Error fetching country tariff profile`. En « Recherche intelligente » seulement : 404 sur `/api/hs6/suggestions/<code>` (route absente du backend).
- **`start.sh` n'est pas utilisé ici** : il attend un venv dans `backend/.venv311` et tue les serveurs par `pkill -f`.
- **La capture pleine page** montre la barre latérale (fixe) seulement en haut : c'est attendu.

## Dépannage

- **`ModuleNotFoundError: No module named 'engine'`** à l'appel direct : `engine/` est à la racine du dépôt. Lancez depuis `backend/` avec `PYTHONPATH=..`.
- **HTTP 404 `<ISO>/<code> : position absente du socle (N positions servies)`** : ni ce code, ni (pour un code national) son parent SH6 ne sont au socle de ce pays — le socle tunisien n'a pas de clé `020110`, seulement des codes nationaux. Pour lister des codes servis :
  ```bash
  .venv/bin/python -c "import json; p=json.load(open('backend/socle/TUN.json'))['positions']; print([c for c in p if c.startswith('020110')][:5])"
  ```
- **`driver.mjs` : `page.waitForResponse: Timeout`** : aucune réponse de liquidation n'est arrivée en 60 s. Le plus souvent l'appel n'est pas parti (champ manquant, toast « Champs manquants », code hors 6-12 chiffres) ; plus rarement le backend n'a pas répondu à temps. Lisez la liste imprimée, les erreurs `échec …` et `saisie.png`.
