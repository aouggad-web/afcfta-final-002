#!/usr/bin/env bash
# =============================================================================
# Synchronisation Emergent — applique la branche main de GitHub TELLE QUELLE.
#
# PRINCIPE : GitHub est la source de vérité. Ce script n'analyse PAS et
# n'audite PAS le code local d'Emergent avant d'appliquer : il aligne
# l'arbre de travail exactement sur origin/main (reset --hard + clean),
# écrasant toute divergence locale. Toute modification faite directement
# dans le shell Emergent et non poussée sur GitHub est PERDUE — c'est voulu.
#
# À lancer DANS le shell Emergent (ou tout déploiement mono-repo) :
#     bash sync_emergent.sh
#
# SEULE main SE DÉPLOIE (audit de sécurité, constat C3). Ce pod est la
# production : le déploiement installe les dépendances, construit et importe
# le code de la branche avec les secrets de backend/.env. Une branche non
# fusionnée — notamment celles des agents IA, construites à partir de contenus
# web non fiables — y exécuterait son code sans revue. main est protégée sur
# GitHub (PR, CI) : fusionnez d'abord, puis synchronisez. BRANCH=<autre> est
# refusé ; pour essayer une branche, utilisez un environnement sans secrets
# de production.
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
# SUPERVISOR (cas Emergent) : si `supervisorctl` est présent, le script
# RECONSTRUIT toujours le frontend (obligatoire car `vite preview` sert
# frontend/build, ignoré par git — sans rebuild, les mises à jour ne
# s'affichent jamais) et redémarre les services PAR supervisord
# (`supervisorctl restart all`), sans pkill ni start.sh : aucun conflit de
# port, le terminal n'est pas bloqué. SKIP_BUILD est alors ignoré. C'est le
# réglage DÉFINITIF du « les mises à jour ne s'affichent pas ».
#
# BUILD (hors supervisor, dev local) : SKIP_BUILD=1 saute le build.
#     SKIP_BUILD=1 bash sync_emergent.sh
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-${VITE_PORT:-5000}}"
DEPLOY_BRANCH="main"
BRANCH="${BRANCH:-$DEPLOY_BRANCH}"
if [ "$BRANCH" != "$DEPLOY_BRANCH" ]; then
  echo "❌ Déploiement refusé : seule la branche '$DEPLOY_BRANCH' se déploie (demandé : '$BRANCH')."
  echo "   Fusionnez d'abord la PR dans '$DEPLOY_BRANCH' (revue + CI), puis relancez : bash sync_emergent.sh"
  exit 1
fi
echo "── 1/6 · Application de origin/'$BRANCH' (écrase l'état local) ──"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
# Aligne les fichiers suivis exactement sur l'origine, puis supprime les
# fichiers non suivis périmés (caches .pyc, artefacts de build obsolètes...).
# Les exclusions protègent uniquement la config d'environnement, les dépendances
# installées et les données téléchargées sur le serveur — jamais du code
# applicatif.
#
# `data/geoip` : la base MaxMind n'est pas versionnée (binaire volumineux,
# licence restrictive) mais elle est téléchargée sur le pod. Sans cette
# exclusion, chaque déploiement l'effacerait et la détection de pays
# retomberait silencieusement sur le pays déclaré par le client — le verrou
# Algérie serait alors contournable.
git reset --hard "origin/$BRANCH"
git clean -fd \
  -e .env -e "*.env" -e .emergent \
  -e node_modules -e frontend/node_modules \
  -e venv -e .venv \
  -e data/geoip -e backend/data/geoip
echo "  ✓ Arbre aligné sur origin/$BRANCH ($(git rev-parse --short HEAD))"

echo "── 1bis/6 · Contrôle des crons Emergent (avertissement, non bloquant) ──"
# Persistance (audit de sécurité, C3) : webhook_crond.sh — script de la
# plateforme, non modifié ici — recopie à chaque démarrage du pod
# .emergent/cron/webhook-crons (épargné par le `git clean -e .emergent`) dans
# /etc/cron.d et lance cron en root : une ligne plantée une fois survit aux
# synchronisations. On SIGNALE toute ligne hors de la grammaire rendue par
# Emergent (forme relevée dans l'historique git, commits 92d07699, f5a14932).
# L'expression étant stricte, tout chaînage (; | & $ ` % ( ) …) est hors
# grammaire. Les valeurs VAR=… ne sont jamais affichées.
_check_emergent_crons() (
  set +eu
  export LC_ALL=C  # plages [A-Za-z] au sens octet, quelle que soit la locale du pod
  local env_ok='^(SHELL=/bin/sh|PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin|JOB_ID=[0-9a-f-]{36}|WEBHOOK_ENV_FILE=/app/backend/\.env|CRON_API_URL=https://[a-z0-9.-]+\.emergentagent\.com)$'
  # Séparateurs : espaces et tabulations seulement (un CR n'est pas un rendu Emergent).
  local b=$'[ \t]' f n line host suspects=0
  local s="$b+"
  local job_ok="^(@(hourly|daily|weekly|monthly|yearly|annually|midnight)|[0-9A-Za-z*/,-]+($s[0-9A-Za-z*/,-]+){4})${s}root"
  job_ok+="($s(CRON_NAME|METHOD|ENDPOINT_URL_B64|JOB_ID|AT_DATE|END_DATE|WEBHOOK_ENV_FILE|CRON_API_URL)=[A-Za-z0-9_.,:/+=@-]*)*"
  job_ok+="($s/bin/sh)?$s/app/\\.emergent/cron/(dispatch_webhook|watch_crons)\\.sh"
  job_ok+="($s>>?$b*(/var/log/webhook-cron\\.log|/dev/null)(${s}2>&1)?)?$b*\$"
  for f in /app/.emergent/cron/webhook-crons /etc/cron.d/webhook-crons; do
    [ -f "$f" ] || { echo "  · $f : absent"; continue; }
    n=0
    while IFS= read -r line || [ -n "$line" ]; do
      n=$((n + 1))
      [[ $line =~ ^[[:space:]]*(#.*)?$ || $line =~ $env_ok ]] && continue
      if [[ $line =~ $job_ok ]]; then
        # Une ligne bien formée peut viser un hôte tiers (le dispatch y envoie
        # WEBHOOK_CRON_SECRET) : on vérifie l'hôte, jamais l'URL complète.
        [[ $line =~ ENDPOINT_URL_B64=([^[:space:]]+) ]] || continue
        host="$(printf '%s' "${BASH_REMATCH[1]}" | base64 -d 2>/dev/null | head -c 300 \
          | sed -nE 's#^https?://([A-Za-z0-9.-]+).*#\1#p')"
        [[ $host =~ (^|\.)emergentagent\.com$ ]] && continue
        line="dispatch vers un hôte hors emergentagent.com : ${host:-illisible}"
      fi
      suspects=$((suspects + 1))
      printf '  ⚠ %s:%d : %s\n' "$f" "$n" "$(printf '%s' "$line" \
        | sed -E 's/([A-Za-z_][A-Za-z0-9_]*)=[^[:space:]]*/\1=***/g; s/[A-Za-z0-9+_-]{20,}=*/***/g' \
        | tr -d '\000-\037\177' | cut -c1-200)"
    done < "$f"
  done
  if [ -f /app/.emergent/cron/webhook-crons ] && [ -f /etc/cron.d/webhook-crons ] \
    && ! cmp -s /app/.emergent/cron/webhook-crons /etc/cron.d/webhook-crons; then
    suspects=$((suspects + 1))
    echo "  ⚠ /etc/cron.d/webhook-crons diffère de la copie persistante d'Emergent."
  fi
  if [ "$suspects" -gt 0 ]; then
    echo "  ⚠ $suspects anomalie(s) : compromission possible du pod. Ne pas se contenter"
    echo "     de re-synchroniser : faire reconstruire le pod ET son volume par Emergent."
  else
    echo "  ✓ Aucune entrée cron hors forme Emergent."
  fi
)
_check_emergent_crons || true

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
  # Session du 2026-07-19 — sous-module substitution (bornage par
  # substituabilité, granularité produit HS4, positionnement prix) + export
  # PDF natif (Statistiques + tous les sous-modules Opportunités). Ces
  # fichiers ont concrètement été le symptôme du bug "PR mergées mais pas
  # affichées" : une copie Emergent sans eux tourne sur l'ancien module
  # substitution (chapitre SH2, pas de prix) sans que rien ne le signale
  # côté UI (champs absents = simplement pas rendus).
  backend/services/substitution_feasibility_service.py
  frontend/src/utils/tradeReportPdf.js
  frontend/src/utils/opportunityPdf.js
  frontend/src/components/opportunities/OpportunityPdfExport.jsx
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

echo "── 3bis/6 · Base GeoIP (facultatif — verrou pays de facturation) ──"
# Détection : GEOIP_DB_PATH est le chemin cible ; s'il pointe déjà vers un
# fichier présent, rien à faire — la base précédente a survécu au `git clean`
# (protection ajoutée à l'étape 1). Sinon on la retélécharge SI on a une clé
# de licence MaxMind, en défaut mou : la panne d'un téléchargement ne doit pas
# planter le déploiement. Sans base, le sélecteur pays manuel prend le relais
# et le backend écrit un logger.error explicite.
#
# On lit ces deux variables directement dans le .env du pod plutôt que
# l'environnement shell : ce script n'est pas invoqué via `dotenv`, or
# c'est backend/.env qui porte la configuration runtime.
_extract_env() {
  # $1 = nom de variable ; imprime la valeur (ligne KEY=... du .env), sans
  # espaces ni guillemets superflus. Aucune interprétation shell : plus sûr
  # que `source .env` (qui échouerait sur les caractères spéciaux avec set -e).
  local key="$1"
  local envfile="backend/.env"
  # L'absence du fichier ou de la clé est un cas normal : la fonction doit
  # toujours réussir pour rester compatible avec `set -euo pipefail`.
  [ -f "$envfile" ] || return 0
  grep -E "^[[:space:]]*${key}[[:space:]]*=" "$envfile" | tail -1 \
    | sed -E "s/^[[:space:]]*${key}[[:space:]]*=[[:space:]]*//; s/^['\"]//; s/['\"][[:space:]]*$//" \
    || true
}
GEOIP_TARGET="${GEOIP_DB_PATH:-$(_extract_env GEOIP_DB_PATH)}"
GEOIP_TARGET="${GEOIP_TARGET:-/app/data/geoip/GeoLite2-Country.mmdb}"
MAXMIND_KEY="${MAXMIND_LICENSE_KEY:-$(_extract_env MAXMIND_LICENSE_KEY)}"

if [ -s "$GEOIP_TARGET" ]; then
  echo "  ✓ base déjà présente : $GEOIP_TARGET"
elif [ -n "$MAXMIND_KEY" ]; then
  GEOIP_DIR="$(dirname "$GEOIP_TARGET")"
  mkdir -p "$GEOIP_DIR"
  if MAXMIND_LICENSE_KEY="$MAXMIND_KEY" python scripts/geoip_update.py --dest "$GEOIP_DIR" 2>&1 | sed 's/^/    /'; then
    echo "  ✓ base téléchargée dans $GEOIP_DIR"
  else
    echo "  ⚠ téléchargement échoué — le verrou Algérie sera inactif jusqu'à réparation"
  fi
else
  echo "  ⏭ MAXMIND_LICENSE_KEY absente : téléchargement automatique désactivé."
  echo "     Pour installer manuellement : python scripts/geoip_update.py --from-file <archive>"
fi

echo "── 3ter/6 · Régénération des données normalisées (data/crawled_normalized, gitignoré) ──"
# CRAWLED_DIR (services/crawled_data_service.py) ne lit que ce dossier dérivé,
# jamais versionné : le `git clean -fd` de l'étape 1 l'efface systématiquement
# (aucune exclusion ne le protège), et sans cette régénération l'étape 4
# échoue immédiatement sur l'assertion AGO/WITS — avant même d'atteindre le
# build frontend. Même étape que le workflow CI (.github/workflows/ci.yml).
python scripts/normalize_crawled.py

echo "── 3quater/6 · Régénération du socle de calcul (backend/socle/*.json, gitignoré) ──"
# Même raison : le manifeste versionné décrit 54 pays sans qu'aucun fichier
# n'existe sur disque tant que ce script n'a pas tourné (voir CI, même étape).
python scripts/build_socle.py

echo "── 4/6 · Contrôle d'import + données de la copie appliquée ──"
( cd backend && PYTHONPATH="$(pwd)/..:$(pwd)" python -c "
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
    'services.substitution_feasibility_service',
    'services.real_substitution_service',
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
assert is_active_implementer('KEN') and not is_active_implementer('ETH') and not is_active_implementer('MOZ'), 'registre application réelle ZLECAf incohérent'
from services.zlecaf_implementation_registry import PARTNER_NOTICE_REQUIRED, implementation_decision
assert implementation_decision('ETH', 'KEN')['status'] == PARTNER_NOTICE_REQUIRED, 'garde juridique ETH périmée'
from services.crawled_data_service import CrawledDataService
svc = CrawledDataService(); svc.load(force=True)
assert svc.lookup('AGO', '010121'), 'normaliseur WITS absent (AGO illisible)'
assert svc.lookup('GHA', '010121'), 'GHA_tariffs.json absent de data/crawled'

# Session du 2026-07-19 — vérifie le COMPORTEMENT, pas seulement la présence
# du fichier : une copie Emergent peut importer substitution_feasibility_service
# sans avoir le calcul attendu si un ancien .pyc/cache a survécu. Le
# coefficient à 0703 doit se résoudre au préfixe SH4 (0,5), pas être dilué au
# chapitre SH2 (0,45, l'ancien comportement) — la preuve la plus directe que
# la granularité produit est bien celle de cette session.
from services.substitution_feasibility_service import substitutability_for_hs
coef = substitutability_for_hs('8703')['coefficient']
assert coef == 0.5, f'substitutability_for_hs périmé : 8703 -> {coef} (attendu 0.5, résolution SH4)'

# Le cache substitution est PERSISTANT (Redis/disque, TTL 24h) et survit aux
# redémarrages — sans ce numéro de schéma, une release qui enrichit le
# payload (positionnement prix, granularité produit) continue de servir les
# anciens payloads en cache jusqu'à 24h après le déploiement : exactement le
# symptôme « PR mergée mais rien ne s'affiche » qui a motivé cette vérification.
from services.real_substitution_service import RealSubstitutionService
assert RealSubstitutionService._CACHE_SCHEMA_VERSION >= 3, (
    'real_substitution_service périmé : _CACHE_SCHEMA_VERSION < 3 — '
    'les anciens payloads en cache masqueront les nouveaux champs jusqu à 24h'
)
print('✓ Données de la session appliquées (TUN préférences, TVA WITS, réciprocité, GHA, substitution HS4+cache v3).')
" )

# Détection du superviseur (cas Emergent : services gérés par supervisord, le
# frontend servi par `vite preview` depuis frontend/build). En mode supervisor,
# le build du frontend est OBLIGATOIRE (frontend/build est ignoré par git ; sans
# rebuild, `vite preview` continue de servir l'ancienne version — les nouveautés
# n'apparaissent jamais). SKIP_BUILD est donc IGNORÉ quand supervisord gère le
# frontend, pour régler définitivement le « les mises à jour ne s'affichent pas ».
HAS_SUPERVISOR=0
# `supervisorctl status` (sans argument) sort en erreur si UN SEUL programme
# n'est pas RUNNING (ex: code-server, sans rapport avec cette app) — on
# vérifie donc un programme précis et géré par supervisor (backend).
if command -v supervisorctl >/dev/null 2>&1 && supervisorctl status backend >/dev/null 2>&1; then
  HAS_SUPERVISOR=1
fi

if [ "${SKIP_BUILD:-0}" = "1" ] && [ "$HAS_SUPERVISOR" = "0" ]; then
  echo "── 5/6 · Build du frontend SAUTÉ (SKIP_BUILD=1, pas de supervisor) ──"
  ( cd frontend; if command -v yarn >/dev/null 2>&1; then yarn install --frozen-lockfile --ignore-scripts; else npm install --legacy-peer-deps; fi )
else
  if [ "${SKIP_BUILD:-0}" = "1" ]; then
    echo "── 5/6 · Build du frontend (SKIP_BUILD ignoré : supervisor sert frontend/build) ──"
  else
    echo "── 5/6 · Build du frontend (Vite → frontend/build) ──"
  fi
  (
    cd frontend
    if command -v yarn >/dev/null 2>&1; then
      # Lockfile strict, sans repli ni scripts d'installation des paquets
      # (audit, C3) : un yarn.lock périmé arrête le déploiement au lieu de
      # re-résoudre les versions en silence. Build vérifié identique à l'octet
      # (seuls core-js et esbuild ont des scripts, sans effet sur le build).
      yarn install --frozen-lockfile --ignore-scripts
      yarn build
    else
      npm install --legacy-peer-deps
      npm run build
    fi
  )
fi

if [ "$HAS_SUPERVISOR" = "1" ]; then
  echo "── 6/6 · Redémarrage PROPRE via supervisord (pas de pkill/start.sh) ──"
  # On redémarre par le superviseur : il relance les services avec LEUR config
  # (ports, vite preview, --reload-exclude). Aucun conflit de port, le terminal
  # n'est pas bloqué. 'all' couvre backend + frontend quel que soit leur nom.
  supervisorctl restart all || {
    echo "  ⚠ 'supervisorctl restart all' a échoué — redémarrez manuellement :"
    echo "     supervisorctl restart backend frontend"
  }
else
  echo "── 6/6 · Pas de supervisor détecté — arrêt des serveurs de dev périmés ──"
  pkill -f "uvicorn server:app" 2>/dev/null || true
  pkill -f "vite" 2>/dev/null || true
  sleep 1
fi

echo
echo "✅ Synchronisation terminée — la branche GitHub est appliquée telle quelle,"
echo "   le frontend est reconstruit, et les services sont relancés proprement."
echo
if [ "$HAS_SUPERVISOR" = "1" ]; then
  echo "▶ Rien d'autre à lancer : supervisord gère les processus. État :"
  echo "   supervisorctl status"
else
  echo "▶ Démarrer l'application (backend $BACKEND_PORT, frontend $FRONTEND_PORT) :"
  echo "   BACKEND_PORT=$BACKEND_PORT FRONTEND_PORT=$FRONTEND_PORT VITE_HMR=off bash start.sh"
fi
echo
echo "▶ Vérifier la santé :"
echo "   curl -s http://localhost:$BACKEND_PORT/api/reports/health"
echo "   curl -s http://localhost:$BACKEND_PORT/api/reports/oec-health"
