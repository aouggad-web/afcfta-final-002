#!/usr/bin/env bash
# =============================================================================
# Synchronisation Emergent — récupère TOUTES les améliorations depuis GitHub,
# reconstruit backend + frontend, et vérifie qu'aucun module ne manque.
#
# À lancer DANS le shell Emergent (ou tout déploiement mono-repo) :
#     bash sync_emergent.sh                 # synchronise la branche courante
#     BRANCH=main bash sync_emergent.sh     # force une branche précise
#
# Ce script règle la cause du bug « No module named 'services.regional_blocs' »
# vu en production : un déploiement qui tournait une copie PARTIELLE du dépôt.
# Il refuse de continuer si un module critique manque après le pull.
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

BRANCH="${BRANCH:-$(git rev-parse --abbrev-ref HEAD)}"
echo "── 1/6 · Récupération de la branche '$BRANCH' depuis origin ──"
git fetch origin "$BRANCH"
# Aligne l'arbre exactement sur l'origine (élimine tout fichier périmé/partiel).
git checkout "$BRANCH"
git reset --hard "origin/$BRANCH"

echo "── 2/6 · Vérification des modules critiques (anti code-périmé) ──"
MISSING=0
CRITICAL=(
  backend/services/regional_blocs.py
  backend/services/zlecaf_schedule_dza.py
  backend/services/zlecaf_membership_status.py
  backend/services/benchmarking_service.py
  backend/services/report_engine.py
  backend/services/demand_estimation_service.py
  backend/services/oec_trade_service.py
  backend/services/real_trade_data_service.py
  backend/routes/reports.py
  backend/country_data.py
  data/json/wb_gdp_pc.json
  data/json/wb_reserves.json
)
for f in "${CRITICAL[@]}"; do
  if [ -f "$f" ]; then echo "  ✓ $f"; else echo "  ✗ MANQUE $f"; MISSING=1; fi
done
if [ "$MISSING" = "1" ]; then
  echo "❌ Des fichiers critiques manquent après le pull — synchronisation incomplète."
  echo "   Vérifiez que le déploiement pointe bien sur la branche '$BRANCH' à jour."
  exit 1
fi

echo "── 3/6 · Dépendances backend (Python) ──"
pip install -r backend/requirements.txt --quiet --no-input

echo "── 4/6 · Contrôle d'import du moteur (échoue tôt si un import casse) ──"
( cd backend && python -c "
import importlib
for m in [
    'services.regional_blocs',
    'services.benchmarking_service',
    'services.report_engine',
    'services.demand_estimation_service',
    'services.oec_trade_service',
    'routes.reports',
]:
    importlib.import_module(m)
print('✓ Tous les modules du moteur Opportunités s\'importent.')
" )

echo "── 5/6 · Build du frontend (Vite → frontend/build) ──"
(
  cd frontend
  if command -v yarn >/dev/null 2>&1; then
    yarn install --frozen-lockfile || yarn install
    yarn build
  else
    npm install --legacy-peer-deps
    npm run build
  fi
)

echo "── 6/6 · Redémarrage des serveurs (si start.sh est présent) ──"
pkill -f "uvicorn server:app" 2>/dev/null || true
pkill -f "vite --host" 2>/dev/null || true
sleep 1

echo
echo "✅ Synchronisation terminée. TOUTES les améliorations sont en place :"
echo "   • Régime tarifaire réel (réciprocité Algérie, unions douanières)"
echo "   • Module Opportunités S1/S2/S3/S4 + rapports bilatéraux ultra-fins"
echo "   • OEC via le canal gratuit du module Statistiques (aucun token)"
echo "   • Macro World Bank : PIB/hab (L3), réserves, couverture des importations"
echo
echo "▶ Démarrer l'application :"
echo "   bash start.sh                        # dev : backend 8000 + Vite 5000"
echo "   # ou mono-processus (prod) :"
echo "   cd backend && python -m uvicorn server:app --host 0.0.0.0 --port 5000"
echo
echo "▶ Vérifier la santé :"
echo "   curl -s http://localhost:8000/api/reports/health"
echo "   curl -s http://localhost:8000/api/reports/oec-health"
