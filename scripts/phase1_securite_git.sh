#!/usr/bin/env bash
# ============================================================
# PHASE 1 — SÉCURITÉ GIT (URGENT — FAIRE EN PREMIER)
# Repo : afcfta-final-002
# Exécuter depuis la RACINE du repo cloné localement
# ============================================================
set -euo pipefail
RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'; NC='\033[0m'

echo -e "${RED}╔══════════════════════════════════════════════╗${NC}"
echo -e "${RED}║  PHASE 1 — AUDIT & SÉCURISATION GIT         ║${NC}"
echo -e "${RED}╚══════════════════════════════════════════════╝${NC}\n"

# ─── 1. Vérifier que git-filter-repo est installé ──────────
echo -e "${YELLOW}[1/6] Vérification des outils requis...${NC}"
if ! command -v git-filter-repo &>/dev/null; then
    echo "    Installation de git-filter-repo..."
    pip install git-filter-repo --break-system-packages 2>/dev/null || \
    pip3 install git-filter-repo || \
    { echo -e "${RED}ERREUR: installez manuellement: pip install git-filter-repo${NC}"; exit 1; }
fi
echo -e "${GREEN}    ✓ git-filter-repo disponible${NC}"

# ─── 2. Chercher des secrets dans l'historique Git ─────────
echo -e "\n${YELLOW}[2/6] Scan de l'historique Git pour secrets exposés...${NC}"
echo "    Recherche de patterns sensibles dans TOUS les commits..."

# Patterns à détecter
PATTERNS=(
    "smtp_password"
    "smtp_user"
    "slack_webhook"
    "mongodb+srv"
    "mongodb://"
    "secret_key"
    "api_key"
    "access_token"
    "private_key"
    "password.*=.*['\"][^'"]{8,}"
)

FOUND_SECRETS=0
for pattern in "${PATTERNS[@]}"; do
    RESULTS=$(git log --all --oneline -p 2>/dev/null | grep -i "$pattern" | head -3 || true)
    if [ -n "$RESULTS" ]; then
        echo -e "${RED}    ⚠ TROUVÉ '$pattern' dans l'historique !${NC}"
        echo "$RESULTS" | head -2 | sed 's/^/      /'
        FOUND_SECRETS=$((FOUND_SECRETS + 1))
    fi
done

if [ $FOUND_SECRETS -eq 0 ]; then
    echo -e "${GREEN}    ✓ Aucun secret évident trouvé dans l'historique${NC}"
else
    echo -e "${RED}    ⚠ $FOUND_SECRETS type(s) de secrets trouvés — purge nécessaire (étape 4)${NC}"
fi

# ─── 3. Vérifier le .env actuel ────────────────────────────
echo -e "\n${YELLOW}[3/6] Vérification du fichier .env...${NC}"
if [ -f ".env" ]; then
    echo -e "${RED}    ⚠ FICHIER .env PRÉSENT À LA RACINE${NC}"
    echo "    Contenu sensible détecté :"
    grep -v "^#\|^$" .env | sed 's/=.*/=***MASQUÉ***/' | head -10 | sed 's/^/      /'
    echo ""
    echo -e "${RED}    ACTION REQUISE : Ce fichier ne doit JAMAIS être commité !${NC}"
else
    echo -e "${GREEN}    ✓ Pas de .env commité (bien)${NC}"
fi

# ─── 4. Purger .env de tout l'historique Git ───────────────
echo -e "\n${YELLOW}[4/6] Purge de .env et fichiers sensibles de l'historique...${NC}"

# Créer un backup local avant toute opération destructive
BACKUP_DIR="../backup_before_cleanup_$(date +%Y%m%d_%H%M%S)"
echo "    Création du backup dans $BACKUP_DIR..."
cp -r . "$BACKUP_DIR" 2>/dev/null && echo -e "${GREEN}    ✓ Backup créé : $BACKUP_DIR${NC}" || \
    echo -e "${YELLOW}    Backup partiel (normal si repo volumineux)${NC}"

# Purger les fichiers sensibles de l'historique
FILES_TO_PURGE=(".env" ".env.local" ".env.production" "*.env")
for f in "${FILES_TO_PURGE[@]}"; do
    if git log --all --oneline -- "$f" 2>/dev/null | head -1 | grep -q .; then
        echo "    Purge de $f de l'historique..."
        git filter-repo --path "$f" --invert-paths --force 2>/dev/null && \
            echo -e "${GREEN}    ✓ $f purgé${NC}" || \
            echo -e "${YELLOW}    Impossible de purger $f (peut-être absent)${NC}"
    fi
done

# ─── 5. Mise à jour du .gitignore ──────────────────────────
echo -e "\n${YELLOW}[5/6] Mise à jour du .gitignore...${NC}"
GITIGNORE_ADDITIONS=(
    ""
    "# ── Secrets & environnement ──────────────────"
    ".env"
    ".env.*"
    "!.env.example"
    ""
    "# ── Données sensibles ─────────────────────────"
    "*.key"
    "*.pem"
    "secrets/"
    ""
    "# ── Artefacts Python parasites ────────────────"
    "__pycache__/"
    "*.pyc"
    "*.pyo"
    ".pytest_cache/"
    "*.egg-info/"
    ""
    "# ── Logs & temp ─────────────────────────────"
    "*.log"
    "logs/"
    "tmp/"
    ".DS_Store"
    "Thumbs.db"
)

for line in "${GITIGNORE_ADDITIONS[@]}"; do
    if [ -z "$line" ] || ! grep -qxF "$line" .gitignore 2>/dev/null; then
        echo "$line" >> .gitignore
    fi
done
echo -e "${GREEN}    ✓ .gitignore mis à jour${NC}"

# ─── 6. Afficher les credentials ────────────────
echo -e "\n${YELLOW}[6/6] Checklist des credentials à révoquer IMMÉDIATEMENT...${NC}"
echo -e "${RED}"
echo "    ┌─────────────────────────────────────────────────────────┐"
echo "    │  ACTIONS MANUELLES OBLIGATOIRES APRÈS CE SCRIPT         │"
echo "    │                                                          │"
echo "    │  1. Gmail SMTP → Révoquer l'App Password actuel         │"
echo "    │     → Créer un nouveau App Password Gmail               │"
echo "    │                                                          │"
echo "    │  2. Slack Webhook → Regénérer l'URL du webhook          │"
echo "    │     → Settings > Incoming Webhooks > Regenerate         │"
echo "    │                                                          │"
echo "    │  3. MongoDB → Changer le mot de passe utilisateur       │"
echo "    │     → Atlas > Database Access > Edit User               │"
echo "    │                                                          │"
echo "    │  4. Git push --force sur toutes les branches            │"
echo "    │     git push origin --force --all                       │"
echo "    │     git push origin --force --tags                      │"
echo "    │  (⚠ Force-push nécessite d'informer les collaborateurs) │"
echo "    └─────────────────────────────────────────────────────────┘"
echo -e "${NC}"

echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  PHASE 1 TERMINÉE — Passez à phase2.sh      ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"