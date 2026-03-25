#!/usr/bin/env bash
# ============================================================
# PHASE 3 — RÉORGANISATION STRUCTURE + SUPPRESSION DOUBLONS
# Supprime backup_before_github_merge/ et src/components/trade/
# Réorganise le projet vers une structure propre
# ============================================================
set -euo pipefail
RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  PHASE 3 — STRUCTURE & DOUBLONS             ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}\n"

# ─── 1. Vérifier et supprimer backup_before_github_merge/ ──
echo -e "${YELLOW}[1/5] Suppression du dossier de backup commité...${NC}"

if [ -d "backup_before_github_merge" ]; then
    echo "    Contenu de backup_before_github_merge/ :"
    find backup_before_github_merge -type f | wc -l | xargs -I{} echo "    {} fichier(s) à supprimer"
    
    # Supprimer du tracking git ET du disque
    git rm -r --cached backup_before_github_merge/ 2>/dev/null || true
    rm -rf backup_before_github_merge/
    echo -e "${GREEN}    ✓ backup_before_github_merge/ supprimé${NC}"
else
    echo -e "${GREEN}    ✓ Dossier backup déjà absent${NC}"
fi

# ─── 2. Supprimer src/components/trade/ (doublon frontend) ─
echo -e "\n${YELLOW}[2/5] Suppression de src/components/trade/ (doublon)...${NC}"

if [ -d "src" ]; then
    echo "    Vérification du contenu de src/ :"
    
    # Comparer avec frontend/src/components avant de supprimer
    if [ -d "frontend/src/components" ]; then
        DIFF_COUNT=$(diff -r src/components/trade frontend/src/components/trade 2>/dev/null | wc -l || echo "N/A")
        if [ "$DIFF_COUNT" = "0" ]; then
            echo -e "${GREEN}    Fichiers identiques — suppression safe${NC}"
        else
            echo -e "${YELLOW}    Différences détectées ($DIFF_COUNT lignes) — fusion manuelle recommandée${NC}"
            echo "    Voir: diff -r src/components/trade frontend/src/components"
        fi
    fi
    
    git rm -r --cached src/ 2>/dev/null || true
    rm -rf src/
    echo -e "${GREEN}    ✓ src/ (doublon) supprimé${NC}"
else
    echo -e "${GREEN}    ✓ src/ déjà absent${NC}"
fi

# ─── 3. Structure cible propre ─────────────────────────────
echo -e "\n${YELLOW}[3/5] Vérification et création de la structure cible...${NC}"

# Structure cible recommandée
declare -A REQUIRED_DIRS=(
    ["backend/routers"]="Routes FastAPI organisées"
    ["backend/services"]="Logique métier"
    ["backend/models"]="Modèles Pydantic"
    ["backend/middleware"]="CORS, auth, rate-limit"
    ["data/json"]="Données JSON"
    ["data/csv"]="Données CSV"
    ["data/xlsx"]="Données Excel"
    ["frontend/src/components"]="Composants React"
    ["frontend/src/hooks"]="Custom hooks"
    ["frontend/src/services"]="Appels API"
    ["engine/crawlers"]="Crawlers TypeScript"
    ["tests/unit"]="Tests unitaires"
    ["tests/integration"]="Tests d'intégration"
    ["scripts"]="Scripts utilitaires"
    ["docs"]="Documentation"
)

for dir in "${!REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        # Créer un .gitkeep pour tracker le dossier vide
        touch "$dir/.gitkeep"
        echo -e "${BLUE}    + Créé : $dir (${REQUIRED_DIRS[$dir]})${NC}"
    else
        echo -e "${GREEN}    ✓ Existe : $dir${NC}"
    fi
done

# ─── 4. Réorganiser le backend ─────────────────────────────
echo -e "\n${YELLOW}[4/5] Réorganisation du backend FastAPI...${NC}"

# Si le backend a tout dans un seul fichier main.py, créer la structure
if [ -f "backend/main.py" ] && [ ! -f "backend/routers/__init__.py" ]; then
    echo "    Création de la structure de routeurs FastAPI..."
    
    # Créer les __init__.py nécessaires
    touch backend/__init__.py
    touch backend/routers/__init__.py
    touch backend/services/__init__.py
    touch backend/models/__init__.py
    touch backend/middleware/__init__.py
    
    # Template du middleware CORS sécurisé
    cat > backend/middleware/cors.py << 'CORS_EOF'
"""
Middleware CORS sécurisé pour l'API ZLECAf.
Remplace l'éventuel allow_origins=["*"] par une liste explicite.
"""
from fastapi.middleware.cors import CORSMiddleware
import os

# Charger depuis .env — NE JAMAIS mettre ["*"] en production
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

def setup_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in ALLOWED_ORIGINS],
        allow_credentials=True,
        allow_methods=["GET", "POST"],  # Uniquement les méthodes nécessaires
        allow_headers=["Content-Type", "Authorization"],
        max_age=600,
    )
    return app
CORS_EOF

    # Template rate limiting
    cat > backend/middleware/rate_limit.py << 'RL_EOF'
"""
Rate limiting simple pour l'API ZLECAf.
Installe : pip install slowapi
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)

def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Trop de requêtes. Réessayez dans 60 secondes."}
    )

# Usage dans les routes :
# @router.get("/calculate-tariff")
# @limiter.limit("30/minute")
# async def calculate_tariff(request: Request, ...):
RL_EOF

    echo -e "${GREEN}    ✓ Structure middleware créée${NC}"
fi

# ─── 5. Ajouter les scripts utilitaires au bon endroit ─────
echo -e "\n${YELLOW}[5/5] Déplacement des scripts utilitaires vers scripts/...${NC}"

# Ces scripts ont leur place dans scripts/, pas à la racine
UTIL_SCRIPTS=(
    "add_missing_countries.py"
    "add_trs_data.py"
    "analyze_validation_file.py"
    "apply_corrections.py"
    "check_missing_csv.py"
    "check_tanger.py"
    "complete_excel_with_ratings.py"
    "country_data_updated.py"
    "create_complete_excel_final.py"
    "create_enhanced_excel_2024.py"
    "create_validation_file.py"
    "delta_engine.py"
    "enhance_airport_aviation_logistics.py"
    "enhance_corridor_logistics_data.py"
    "enhance_maritime_logistics_data.py"
    "export_validation_csv.py"
    "fix_lpi_ranks.py"
    "fix_tangermed_data.py"
    "fix_tariffs_and_stats.py"
    "generate_production_data.py"
)

for f in "${UTIL_SCRIPTS[@]}"; do
    if [ -f "$f" ]; then
        git mv "$f" "scripts/$f" 2>/dev/null || mv "$f" "scripts/$f"
        echo -e "${BLUE}    → scripts/$f${NC}"
    fi
done

# Générer la structure finale pour vérification
echo -e "\n${GREEN}Structure finale du projet :${NC}"
tree -L 2 --dirsfirst 2>/dev/null || find . -maxdepth 2 -type d | sort | grep -v "\.git\|node_modules\|__pycache__"

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  PHASE 3 TERMINÉE                               ║${NC}"
echo -e "${BLUE}║                                                  ║${NC}"
echo -e "${BLUE}║  Commandes à exécuter :                         ║${NC}"
echo -e "${BLUE}║  git add -A                                      ║${NC}"
echo -e "${BLUE}║  git commit -m 'refactor: clean project         ║${NC}"
echo -e "${BLUE}║   structure, remove duplicates'                 ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════╝${NC}"
