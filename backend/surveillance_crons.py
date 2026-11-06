"""Contrôle horaire des crons du pod Emergent (point 17 de l'audit de sécurité).

Le backend relance toutes les heures scripts/controle_crons_emergent.sh, le
même contrôle que l'étape 1bis de sync_emergent.sh : une ligne de cron
plantée, un fichier ajouté dans /etc/cron.d ou un script de la plateforme
modifié n'attend plus la prochaine synchronisation pour être vu.

Le verdict est journalisé (CRITICAL pour une anomalie) et exposé sans détail
par /api/health/status (``components.crons``), que lit la tâche GitHub
planifiée .github/workflows/surveillance_securite.yml pour alerter par
e-mail. Hors du pod (CI, Docker, poste de développement), rien ne tourne.
"""

import logging
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "controle_crons_emergent.sh"
REPERTOIRE_POD = Path("/app/.emergent/cron")
# .emergent/cron est versionné : une copie du dépôt montée en /app ailleurs
# l'aurait aussi. Ce lanceur de supervisord n'existe que sur le pod.
MARQUEUR_POD = Path("/etc/supervisor/emergent-env-exec")
INTERVALLE_S = 3600
# Premier passage tout de suite : sans verdict, /api/health/status n'a pas de
# « crons » et la tâche GitHub conclurait à une surveillance arrêtée.
DELAI_INITIAL_S = 0
# Environnement fermé : les chemins réglables du script (EMERGENT_DIR,
# CRON_D…) ne doivent pas venir de backend/.env, chargé dans os.environ.
_ENV_SCRIPT = {
    "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    "LC_ALL": "C",
}

# Dernier verdict : None hors du pod ; sinon {"status": ..., "a": horodatage UTC}.
etat = None
_fil = None


def controler(script: Path = SCRIPT) -> str:
    """Lance le contrôle une fois : « ok », « anomalie » ou « non_verifie »."""
    try:
        resultat = subprocess.run(
            ["bash", str(script)],
            env=_ENV_SCRIPT,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=120,
        )
    except Exception as exc:
        logger.error("Contrôle des crons impossible : %s", type(exc).__name__)
        return "non_verifie"
    sortie = (resultat.stdout + resultat.stderr).strip()
    if resultat.returncode == 0:
        return "ok"
    if resultat.returncode == 1:
        # La sortie du script masque déjà les valeurs des lignes signalées.
        logger.critical("Crons du pod : anomalie, compromission possible.\n%s", sortie)
        return "anomalie"
    logger.error("Crons du pod : contrôle incomplet (code %s).\n%s", resultat.returncode, sortie)
    return "non_verifie"


def _passage(script: Path = SCRIPT) -> None:
    global etat
    try:
        statut = controler(script)
    except Exception:
        logger.exception("Contrôle des crons : erreur inattendue")
        statut = "non_verifie"
    etat = {"status": statut, "a": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def _boucle(arret: threading.Event, script: Path = SCRIPT) -> None:
    if arret.wait(DELAI_INITIAL_S):
        return
    while True:
        _passage(script)
        if arret.wait(INTERVALLE_S):
            return


def demarrer(repertoire_pod: Path = REPERTOIRE_POD, marqueur: Path = MARQUEUR_POD) -> bool:
    """Lance le contrôle horaire sur le pod Emergent ; ne fait rien ailleurs."""
    global _fil
    if not (repertoire_pod.is_dir() and marqueur.exists()):
        return False
    if _fil is not None and _fil.is_alive():
        return False
    _fil = threading.Thread(
        target=_boucle, args=(threading.Event(),), name="surveillance-crons", daemon=True
    )
    _fil.start()
    logger.info("Contrôle horaire des crons du pod démarré")
    return True
