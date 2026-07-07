#!/usr/bin/env bash
# =============================================================================
# Synchronisation Emergent — applique la branche GitHub TELLE QUELLE.
#
# PRINCIPE : GitHub est la source de vérité. Ce script n'analyse PAS et
# n'audite PAS le code local d'Emergent avant d'appliquer : il aligne
# l'arbre de travail exactement sur origin/<branche> (reset --hard + clean),
# écrasant toute divergence locale. Toute modification faite directement
# dans le shell Emergent et non poussée sur GitHub est PERDUE — c'est voulu.
#
# À lancer DANS le shell Emergent (ou tout déploiement mono-repo) :
#     bash sync_emergent.sh                                    # branche courante
#     BRANCH=claude/setup-github-cli-EngUf bash sync_emergent.sh
#     BRANCH=main bash sync_emergent.sh                        # après merge
#
# Les contrôles des étapes 2 et 4 ne comparent JAMAIS avec l'état local
# antérieur : ils vérifient uniquement que la copie fraîchement appliquée
# est complète et importable (anti copie-partielle, cause du bug
# « No module named 'services.regional_blocs' » vu en production).
#
# PORTS : backend/frontend lisent BACKEND_PORT / FRONTEND_PORT (défauts 8000 /
# 5000) — vite.config.js, package.json et start.sh sont maintenant paramétrés
# par variable d'environnement, donc PLUS BESOIN de patcher ces fichiers après
# un `git reset`. Fixez vos ports une fois dans l'environnement Emergent
# (ex. export BACKEND_PORT=8001 FRONTEND_PORT=3000 dans le profil du
# supervisor), pas dans les fichiers du dépôt.
#     BACKEND_PORT=8001 FRONTEND_PORT=3000 bash sync_emergent.sh
#
# BUILD : le supervisor Emergent lance généralement `yarn start` (serveur Vite
# de dev), pas le build de production — l'étape 5/6 est donc sautable :
#     SKIP_BUILD=1 bash sync_emergent.sh
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-${VITE_PORT:-5000}}"
BRANCH="${BRANCH:-$(git rev-parse --abbrev-ref HEAD)}"
echo "── 1/6 · Application de origin/'$BRANCH' (écrase l'état local) ──"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
# Aligne les fichiers suivis exactement sur l'origine, puis supprime les
# fichiers non suivis périmés (caches .pyc, artefacts de build obsolètes...).
# Les exclusions protègent uniquement la config d'environnement et les
# dépendances installées — jamais du code applicatif.
git reset --hard "origin/$BRANCH"
git clean -fd \
  -e .env -e "*.env" -e .emergent \
  -e node_modules -e frontend/node_modules \
  -e venv -e .venv
echo "  ✓ Arbre aligné sur origin/$BRANCH ($(git rev-parse --short HEAD))"

echo "── 2/6 · Vérification des modules critiques (anti copie-partielle) ──"
MISSING=0
CRITICAL=(
  # Moteur Opportunités / Rapports (sessions précédentes)
  backend/services/regional_blocs.py
  backend/services/zlecaf_schedule_dza.py
  backend/services/zlecaf_schedule_zaf.py
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
  # Session courante — réciprocité ZLECAf par application réelle
  backend/services/zlecaf_active_implementers.py
  # Session courante — calculateur (fix IVA/VAT + normaliseur 13 pays WITS)
  backend/services/authentic_tariff_service.py
  backend/services/crawled_data_service.py
  # Session courante — Opportunités branchées calculateur + logistique
  backend/services/real_comparison_service.py
  backend/services/logistics_opportunity_adapter.py
  # Session courante — données tarifaires (TUN/GHA réparés, 13 pays WITS
  # enrichis TVA nationale + surcharges produit)
  backend/data/GHA_tariffs.json
  backend/data/crawled/GHA_tariffs.json
  backend/data/crawled/TUN_tariffs.json
  backend/data/crawled/AGO_tariffs.json
  backend/data/crawled/MDG_tariffs.json
  backend/data/crawled/ZWE_tariffs.json
  backend/scripts/enrich_wits_national_vat.py
  backend/scripts/enrich_wits_product_overrides.py
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

echo "── 4/6 · Contrôle d'import + données de la copie appliquée ──"
( cd backend && python -c "
import importlib
for m in [
    'services.regional_blocs',
    'services.benchmarking_service',
    'services.report_engine',
    'services.demand_estimation_service',
    'services.oec_trade_service',
    'services.zlecaf_active_implementers',
    'services.crawled_data_service',
    'services.authentic_tariff_service',
    'services.real_comparison_service',
    'services.logistics_opportunity_adapter',
    'routes.reports',
]:
    importlib.import_module(m)
print('✓ Tous les modules (moteur + session courante) s importent.')

# Contrôles de fraîcheur des données de CETTE session : échoue si Emergent a
# encore les anciennes versions des fichiers (préférences TUN absentes, TVA
# des pays WITS absente...). Vérifie la copie appliquée, pas l état antérieur.
import json
tun = json.load(open('data/crawled/TUN_tariffs.json'))
assert tun['sub_positions'][0].get('preferences'), 'TUN_tariffs.json périmé (préférences absentes)'
mdg = json.load(open('data/crawled/MDG_tariffs.json'))
assert 'TVA' in mdg['sub_positions'][0].get('taxes', {}), 'MDG_tariffs.json périmé (TVA nationale absente)'
from services.zlecaf_active_implementers import is_active_implementer
assert is_active_implementer('ETH') and not is_active_implementer('MOZ'), 'registre application réelle ZLECAf incohérent'
from services.crawled_data_service import CrawledDataService
svc = CrawledDataService(); svc.load(force=True)
assert svc.lookup('AGO', '010121'), 'normaliseur WITS absent (AGO illisible)'
assert svc.lookup('GHA', '010121'), 'GHA_tariffs.json absent de data/crawled'
print('✓ Données de la session appliquées (TUN préférences, TVA WITS, réciprocité, GHA).')
" )

if [ "${SKIP_BUILD:-0}" = "1" ]; then
  echo "── 5/6 · Build du frontend SAUTÉ (SKIP_BUILD=1 — supervisor en mode dev) ──"
  ( cd frontend; if command -v yarn >/dev/null 2>&1; then yarn install --frozen-lockfile || yarn install; else npm install --legacy-peer-deps; fi )
else
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
fi

echo "── 6/6 · Redémarrage des serveurs (si start.sh est présent) ──"
pkill -f "uvicorn server:app" 2>/dev/null || true
pkill -f "vite --host" 2>/dev/null || true
sleep 1

echo
echo "✅ Synchronisation terminée — la branche GitHub est appliquée telle quelle."
echo "   Mises à jour de cette session incluses :"
echo "   • Réciprocité ZLECAf généralisée (préférence = application réelle prouvée,"
echo "     pas simple ratification — principe DGD 482/2024 étendu à tous les pays)"
echo "   • Calculateur : TVA IVA/VAT enfin reconnue (AGO/MOZ/STP/ZWE/MUS/MWI/SDN/SYC/ZMB),"
echo "     normaliseur des 13 pays WITS (70 744 positions visibles), fix TUN"
echo "     (17 512 préférences + formalités restaurées), fix GHA (chemin de données)"
echo "   • 13 pays WITS enrichis : TVA nationale sourcée + surcharges par produit"
echo "     (traçées loi vs estimation_ia)"
echo "   • Opportunités : économies tarifaires réelles + profil logistique branchés"
echo
echo "▶ Démarrer l'application (ports actuels : backend $BACKEND_PORT, frontend $FRONTEND_PORT) :"
echo "   BACKEND_PORT=$BACKEND_PORT FRONTEND_PORT=$FRONTEND_PORT bash start.sh"
echo "   # ou mono-processus (prod, FastAPI sert aussi le frontend buildé) :"
echo "   cd backend && python -m uvicorn server:app --host 0.0.0.0 --port \$BACKEND_PORT"
echo
echo "▶ Vérifier la santé :"
echo "   curl -s http://localhost:$BACKEND_PORT/api/reports/health"
echo "   curl -s http://localhost:$BACKEND_PORT/api/reports/oec-health"
