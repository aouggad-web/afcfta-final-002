#!/usr/bin/env bash
# Scraper Algeria conformepro.dz — chapitres 30-76, 78-98
# Lance depuis l'onglet Shell Replit (pas depuis l'agent)
# Usage: bash run_dza_scraper.sh [CHAPITRES]
#   ex: bash run_dza_scraper.sh "30-76,78-98"   (défaut)
#   ex: bash run_dza_scraper.sh "40-50"          (test partiel)

CHAPTERS="${1:-30-76,78-98}"
LOG="/tmp/dza_scraper_$(date +%Y%m%d_%H%M%S).log"

echo "=============================================="
echo "  Scraper Algeria conformepro.dz"
echo "  Chapitres : $CHAPTERS"
echo "  Log       : $LOG"
echo "  PID file  : /tmp/dza_scraper.pid"
echo "=============================================="

cd /home/runner/workspace/backend

# Lancement détaché (setsid = session indépendante du terminal)
setsid python3 crawlers/countries/algeria_conformepro_scraper.py \
  --chapters "$CHAPTERS" \
  >> "$LOG" 2>&1 &

PID=$!
echo $PID > /tmp/dza_scraper.pid
echo ""
echo "Scraper lancé (PID=$PID)"
echo "Suivre la progression :"
echo "  tail -f $LOG"
echo ""
echo "Vérifier que le processus tourne encore :"
echo "  ps aux | grep algeria"
echo ""
echo "Arrêter le scraper :"
echo "  kill \$(cat /tmp/dza_scraper.pid)"
