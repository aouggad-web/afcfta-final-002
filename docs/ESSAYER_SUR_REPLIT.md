# Essayer l'application sur Replit

Le dépôt est déjà outillé pour Replit (`.replit`, `start.sh`, `scripts/post-merge.sh`).
Cette page décrit le chemin le plus court pour essayer l'application complète —
calculateur, statistiques (OEC) et module **Opportunités** (S1/S2/S3, rapports
bilatéraux ultra-fins) — avec le réseau ouvert de Replit : l'API World Bank et
l'OEC répondent (token optionnel), contrairement aux bacs à sable.

## 1. Importer le dépôt

1. Sur Replit : **Create Repl ▸ Import from GitHub** → `aouggad-web/afcfta-final-002`.
2. Choisir la **branche à essayer** (par ex. celle de cette PR tant qu'elle n'est
   pas mergée sur `main`). Sur un Repl existant : onglet *Git* ▸ changer de branche
   (le hook `postMerge` réinstalle les dépendances automatiquement).

## 2. Lancer (mode développement — bouton Run)

Le bouton **Run** exécute `start.sh` :

- backend FastAPI sur le port **8000** (exposé en externe sur le port 80),
- frontend Vite sur le port **5000** (aperçu web Replit), proxy `/api` → 8000.

Premier démarrage : les dépendances s'installent (`pip` + `npm`), compter
quelques minutes. Ensuite l'aperçu s'ouvre sur l'UI ; l'onglet **Opportunités**
et la recherche **SH2/4/6** des Statistiques sont opérationnels.

## 3. Déployer (mode production — un seul processus)

Le bloc `[deployment]` du `.replit` (cible VM) :

1. **Build** : `cd frontend && npm install --legacy-peer-deps && npm run build`
   (Vite → `frontend/build/`).
2. **Run** : `python -m uvicorn server:app --host 0.0.0.0 --port 5000`
   (le `--host 0.0.0.0` est indispensable pour être joignable sur Replit) —
   FastAPI sert alors **l'API et le frontend buildé sur le même port**
   (`backend/server.py` supporte les layouts CRA `build/static` et Vite
   `build/assets`).

## 4. Optionnel — activer toutes les données

```bash
# L3 + réserves (World Bank, réseau ouvert sur Replit) :
cd backend && python -m etl.fetch_wb_gdp && python -m etl.fetch_wb_reserves

# OEC avec token (sinon tier gratuit) — Secrets Replit :
#   OEC_API_TOKEN=ton_token
# Vérifier : GET /api/reports/oec-health  → attendu "reachable": true

# Déroulé complet du module Opportunités :
cd backend && python -m scripts.smoke_opportunites --destination DZA
```

## Repères

| Quoi | Où |
|---|---|
| Santé moteur Opportunités | `GET /api/reports/health` |
| Diagnostic OEC | `GET /api/reports/oec-health` |
| Appels prêts à l'emploi | `requests.http` (racine du dépôt) |
| Exemple déroulé (cajou GNB→DZA) | `docs/EXEMPLE_CAJOU_GNB.md` |
| Exécution depuis GitHub (Actions/Codespaces) | `docs/EXECUTER_DEPUIS_GITHUB.md` |
