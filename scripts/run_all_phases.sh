#!/usr/bin/env bash
# ============================================================
# SCRIPT MAÎTRE — ZLECAf Cleanup & Security
# Lance les 4 phases dans l'ordre avec confirmation
# 
# UTILISATION :
#   chmod +x run_all_phases.sh
#   ./run_all_phases.sh
#
# PRÉREQUIS :
#   - Être à la RACINE du dépôt cloné localement
#   - Avoir git configuré avec accès push
#   - pip / pip3 disponible
# ============================================================
set -euo pipefail
RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; NC='\033[0m'

echo -e "${RED}"
echo "  ╔═══════════════════════════════════════════════════════╗"
echo "  ║   ZLECAF — PLAN D'URGENCE · CORRECTIONS & SÉCURITÉ   ║"
echo "  ║   4 phases · ~1h30 d'exécution                       ║"
echo "  ╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ─── Vérifications préalables ──────────────────────────
echo -e "${YELLOW}Vérifications préalables...${NC}"

# Vérifier qu'on est dans un repo git
if ! git rev-parse --git-dir &>/dev/null; then
    echo -e "${RED}ERREUR : Ce script doit être exécuté depuis la racine d'un dépôt git.${NC}"
    echo "  Clonez d'abord : git clone https://github.com/aouggad-web/afcfta-final-002.git"
    exit 1
fi

# Vérifier les changements non committés
if ! git diff --quiet HEAD 2>/dev/null; then
    echo -e "${YELLOW}⚠ Changements non committés détectés.${NC}"
    read -p "  Continuer quand même ? (o/N) : " confirm
    [[ "$confirm" =~ ^[oO]$ ]] || exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

run_phase() {
    local num="$1"
    local name="$2"
    local script="$3"
    local color="$4"
    
    echo ""
    echo -e "${color}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╜${NC}"
    echo -e "${color}  PHASE $num — $name${NC}"
    echo -e "${color}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╜${NC}"
    read -p "  Lancer la phase $num ? (o/N) : " confirm
    if [[ "$confirm" =~ ^[oO]$ ]]; then
        chmod +x "$SCRIPT_DIR/$script"
        bash "$SCRIPT_DIR/$script"
        echo ""
        echo -e "${GREEN}  ✓ Phase $num terminée${NC}"
        read -p "  Créer un commit pour cette phase ? (o/N) : " do_commit
        if [[ "$do_commit" =~ ^[oO]$ ]]; then
            git add -A
            git commit -m "chore(phase$num): $name" --allow-empty
            echo -e "${GREEN}  ✓ Commit créé${NC}"
        fi
    else
        echo -e "${YELLOW}  Phase $num ignorée${NC}"
    fi
}

# Lancer les 4 phases
run_phase 1 "Sécurité Git & secrets"      "phase1_securite_git.sh"      "$RED"
run_phase 2 "Nettoyage racine du repo"    "phase2_nettoyage_racine.sh"  "$YELLOW"
run_phase 3 "Structure & doublons"        "phase3_structure_doublons.sh" "$BLUE"
run_phase 4 "Hardening sécurité backend" "phase4_hardening_securite.sh" "$GREEN"

# ─── Push final ────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╜${NC}"
echo -e "${GREEN}  TOUTES LES PHASES TERMINÉES${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━🚀━━━━━━━━━━━━━━━━━━━━╜${NC}"
echo ""
echo -e "${YELLOW}Pour pousser sur GitHub :${NC}"
echo "  git push origin main"
echo ""
echo -e "${YELLOW}Si vous avez utilisé git-filter-repo (purge secrets) :${NC}"
echo "  git push origin --force --all"
echo "  git push origin --force --tags"
echo "  (⚠ Force-push nécessite d'informer les collaborateurs)${NC}"
echo ""
echo -e "${YELLOW}Vérifications post-déploiement :${NC}"
echo "  1. docker-compose up --build"
echo "  2. curl https://votre-domaine/api/health"
echo "  3. Ouvrir SECURITY_CHECKLIST.md et cocher chaque item"
echo ""
echo -e "${GREEN}Bonne continuation !${NC}"
