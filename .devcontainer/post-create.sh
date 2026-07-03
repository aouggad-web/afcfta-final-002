#!/usr/bin/env bash
# Prépare le Codespace / devcontainer : dépendances backend + frontend, et
# fichiers .env prêts à l'emploi (le module Opportunités tourne sans autre config).
set -euo pipefail

echo "── Backend : dépendances Python ──"
pip install -r backend/requirements.txt

echo "── Frontend : dépendances Node (yarn, même méthode que la CI) ──"
(cd frontend && (yarn install --frozen-lockfile || yarn install))

# backend/.env — chargé explicitement par backend/server.py (load_dotenv).
# SECRET_KEY aléatoire par Codespace ; jamais committé (.env est git-ignoré).
if [ ! -f backend/.env ]; then
  echo "── Génération de backend/.env ──"
  {
    echo "SECRET_KEY=$(openssl rand -hex 32)"
    echo "PUBLIC_DATA_ACCESS=true"
    echo "# OEC : token optionnel (tier gratuit sans token) :"
    echo "# OEC_API_TOKEN=ton_token_oec"
  } > backend/.env
fi

# frontend/.env — VITE_BACKEND_URL vide = même origine : le proxy Vite
# (/api → localhost:8000) fonctionne en local COMME dans le navigateur Codespaces.
if [ ! -f frontend/.env ]; then
  echo "── Génération de frontend/.env ──"
  echo "VITE_BACKEND_URL=" > frontend/.env
fi

echo
echo "✅ Devcontainer prêt. Pour lancer le module Opportunités :"
echo "   Terminal 1 : cd backend && python -m uvicorn server:app --reload --port 8000"
echo "   Terminal 2 : cd frontend && yarn start          # http://localhost:5000"
echo "   Smoke-test : cd backend && python -m scripts.smoke_opportunites --destination DZA"
