#!/usr/bin/env bash
# ============================================================
# PHASE 2 — NETTOYAGE DES FICHIERS PARASITES
# Supprime les ~80 fichiers accidentellement committés
# et réorganise les données en racine dans data/
# ============================================================
set -euo pipefail
RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; NC='\033[0m'

echo -e "${YELLOW}╔══════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  PHASE 2 — NETTOYAGE RACINE DU REPO         ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════╝${NC}\n"

# ─── 1. Fichiers parasites Python/Shell connus ─────────────
echo -e "${YELLOW}[1/4] Suppression des fichiers parasites identifiés...${NC}"

# Liste exacte des fichiers parasites visibles dans le repo
PARASITES=(
    # Résidus de commandes shell exécutées accidentellement
    "for"
    "from"
    "df"
    "except"
    "continue"
    "PY"
    "EOF"
    "UNIT_OK"
    # Variables Python accidentellement committées
    "cands=[]"
    "current_heading"
    "description:"
    "duty_rate_pct:"
    "heading_ctx:"
    "hs_code:"
    "PYTHONPATH=."
    # Fichiers de debug/test temporaires sans extension
    "backend_test.py"
    "backend_test_2024_data.py"
    "backend_test_review_validation.py"
    "detailed_verification.py"
    "analyze_validation_file.py"
    "apply_corrections.py"
    "check_missing_csv.py"
    "check_tanger.py"
    "fix_lpi_ranks.py"
    "fix_tangermed_data.py"
    "fix_tariffs_and_stats.py"
    "complete_excel_with_ratings.py"
    "create_complete_excel_final.py"
    "create_enhanced_excel_2024.py"
    "create_validation_file.py"
    "export_validation_csv.py"
    "generate_production_data.py"
    "enhance_airport_aviation_logistics.py"
    "enhance_corridor_logistics_data.py"
    "enhance_maritime_logistics_data.py"
    "add_missing_countries.py"
    "add_trs_data.py"
    "country_data_updated.py"
    "delta_engine.py"
    "cost_engine.py"
    "conftest.py"
    "backend_test.py"
    "backend_test_2024_data.py"
    "backend_test_review_validation.py"
)

DELETED=0
SKIPPED=0

for f in "${PARASITES[@]}"; do
    if [ -f "$f" ]; then
        git rm --cached "$f" 2>/dev/null || true
        rm -f "$f"
        echo -e "${GREEN}    ✓ Supprimé : $f${NC}"
        DELETED=$((DELETED+1))
    else
        SKIPPED=$((SKIPPED+1))
    fi
done

# Détection automatique des fichiers sans extension ou avec noms invalides
echo -e "\n${YELLOW}    Scan automatique des fichiers suspects supplémentaires...${NC}"

# Fichiers sans extension à la racine qui ne devraient pas être là
while IFS= read -r -d '' file; do
    basename_file=$(basename "$file")
    # Fichiers sans extension qui ne sont pas des fichiers connus légitimes
    case "$basename_file" in
        README|LICENSE|CNAME|Makefile|Dockerfile|Procfile|Jenkinsfile) continue ;;
        *) 
            # Si le nom contient des caractères spéciaux (=, :, []) → parasite
            if echo "$basename_file" | grep -qE '[=:\[\]]'; then
                git rm --cached "$file" 2>/dev/null || true
                rm -f "$file"
                echo -e "${RED}    ✓ Parasite détecté et supprimé : $basename_file${NC}"
                DELETED=$((DELETED+1))
            fi
            ;;
    esac
done < <(find . -maxdepth 1 -type f -print0 2>/dev/null)

echo -e "${GREEN}\n    Total supprimés : $DELETED fichiers${NC}"

# ─── 2. Déplacer les données brutes vers data/ ─────────────
echo -e "\n${YELLOW}[2/4] Réorganisation des données — création du dossier data/...${NC}"

mkdir -p data/csv data/json data/xlsx data/backup

# Déplacer les CSV de données
for f in *.csv; do
    [ -f "$f" ] || continue
    # Garder les fichiers de config à la racine, déplacer les données
    case "$f" in
        *.csv.backup)
            git mv "$f" "data/backup/$f" 2>/dev/null || mv "$f" "data/backup/$f"
            echo -e "${BLUE}    → data/backup/$f${NC}"
            ;;
        *)
            git mv "$f" "data/csv/$f" 2>/dev/null || mv "$f" "data/csv/$f"
            echo -e "${BLUE}    → data/csv/$f${NC}"
            ;;
    esac
done

# Déplacer les XLSX de données
for f in *.xlsx; do
    [ -f "$f" ] || continue
    git mv "$f" "data/xlsx/$f" 2>/dev/null || mv "$f" "data/xlsx/$f"
    echo -e "${BLUE}    → data/xlsx/$f${NC}"
done

# Déplacer les JSON de données africaines (logistique, aéroports, etc.)
DATA_JSON_PATTERNS=(
    "airports_africains*.json"
    "ports_africains*.json"
    "corridors_terrestres*.json"
    "african_countries*.json"
    "currencies_african*.json"
    "enhanced_african*.json"
    "douanes_africaines.json"
    "gold_reserves*.json"
    "classement_infrastructure*.json"
    "digital_readiness*.json"
    "afcfta_compliance.json"
    "airports_africains_original.json"
)

for pattern in "${DATA_JSON_PATTERNS[@]}"; do
    for f in $pattern; do
        [ -f "$f" ] || continue
        git mv "$f" "data/json/$f" 2>/dev/null || mv "$f" "data/json/$f"
        echo -e "${BLUE}    → data/json/$f${NC}"
    done
done

# Créer un README dans data/
cat > data/README.md << 'EOF'
# Données ZLECAf

Ce dossier contient toutes les données de référence du projet.

## Structure

```
data/
├── csv/        # Données pays, tarifs, validations (CSV)
├── json/       # Aéroports, ports, corridors, devises (JSON)
├── xlsx/       # Données Excel enrichies
└── backup/     # Sauvegardes
```

## Mise à jour

Les données sont mises à jour automatiquement via GitHub Actions (02:00 UTC).
Sources : World Bank, WTO, OEC, AfDB, IMF.
EOF

echo -e "${GREEN}    ✓ Dossier data/ créé et organisé${NC}"

# ─── 3. Déplacer les crawlers TypeScript orphelins ─────────
echo -e "\n${YELLOW}[3/4] Déplacement des crawlers TypeScript...${NC}"

mkdir -p engine/crawlers

for f in crawlQueue.ts crawlWorker.ts csrf.ts; do
    if [ -f "$f" ]; then
        git mv "$f" "engine/crawlers/$f" 2>/dev/null || mv "$f" "engine/crawlers/$f"
        echo -e "${BLUE}    → engine/crawlers/$f${NC}"
    fi
done

# ─── 4. Mettre à jour les imports Python ───────────────────
echo -e "\n${YELLOW}[4/4] Mise à jour des imports Python pour le nouveau chemin data/...${NC}"

# Chercher et remplacer les chemins dans les fichiers Python du backend
if find backend/ -name "*.py" 2>/dev/null | head -1 | grep -q .; then
    echo "    Correction des chemins dans backend/..."
    
    # Patterns de remplacement les plus courants
    find backend/ -name "*.py" -exec sed -i \
        -e 's|"airports_africains|"data/json/airports_africains|g' \
        -e 's|"ports_africains|"data/json/ports_africains|g' \
        -e 's|"corridors_terrestres|"data/json/corridors_terrestres|g' \
        -e 's|"african_countries|"data/json/african_countries|g' \
        -e 's|"currencies_african|"data/json/currencies_african|g' \
        -e 's|"afcfta_compliance.json"|"data/json/afcfta_compliance.json"|g' \
        -e 's|pd\.read_csv("\([A-Z_]*\.csv\)")|pd.read_csv("data/csv/\1")|g' \
        {} \; 2>/dev/null && echo -e "${GREEN}    ✓ Imports backend mis à jour${NC}" || \
        echo -e "${YELLOW}    Vérifiez manuellement les imports dans backend/${NC}"
fi

# Générer un rapport des changements
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  PHASE 2 TERMINÉE                               ║${NC}"
echo -e "${GREEN}║                                                  ║${NC}"
echo -e "${GREEN}║  Prochaine étape :                               ║${NC}"
echo -e "${GREEN}║  git add -A && git commit -m                     ║${NC}"
echo -e "${GREEN}║  'chore: clean root, reorganise data/ folder'   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
