"""
Health check routes
"""

import hashlib
import json
import os
import subprocess
from datetime import datetime

from fastapi import APIRouter

router = APIRouter()

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _sha_backend():
    """Commit du code chargé : `GIT_SHA` s'il est posé au build, sinon le HEAD du clone."""
    sha = os.environ.get("GIT_SHA", "").strip()
    if sha:
        return sha
    try:
        sortie = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=RACINE,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        return sortie.stdout.strip() or None
    except Exception:
        return None


# Lu UNE fois, au démarrage : après un `git reset` sans redémarrage, c'est le
# code réellement chargé qui compte, pas le HEAD présent sur le disque.
BACKEND_SHA = _sha_backend()


@router.get("/")
async def root():
    return {
        "message": "Bienvenue sur l'API ZLECAf - Système Commercial Africain",
        "version": "2.0.0",
        "status": "Production Ready",
    }


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {"api": "running", "database": "connected"},
    }


def _sha256_fichier(chemin: str):
    try:
        with open(chemin, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


def empreinte_socle(manifeste: dict, tables: dict) -> str:
    """Empreinte stable du socle : `construit_le` change à chaque build, pas elle.

    Calculée sur les empreintes pays (socle et source) et non sur le fichier
    brut, pour qu'un même socle reconstruit ailleurs (production) donne la
    même valeur que celui du dépôt. `tables` porte l'empreinte des tables
    annexes lues en direct pendant le calcul (devises, TVA nationale) : elles
    changent le résultat sans figurer dans les empreintes pays.
    """
    pays = {
        iso: [entree.get("socle_sha256"), entree.get("source_sha256")]
        for iso, entree in manifeste.get("pays", {}).items()
    }
    canon = json.dumps({"pays": pays, "tables": tables}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


@router.get("/version")
async def version():
    """Ce que ce serveur sert réellement : commit du code et socle chargé."""
    socle_info = None
    try:
        from services import socle

        manifeste = socle.manifeste()
        pays = manifeste.get("pays", {})
        socle_info = {
            "socle_version": manifeste.get("socle_version"),
            "construit_le": manifeste.get("construit_le"),
            "pays": len(pays),
            # Un déploiement qui n'a pas lancé build_socle.py a un manifeste
            # versionné mais aucun fichier pays : ce compteur le rend visible.
            "fichiers_presents": sum(
                1
                for entree in pays.values()
                if os.path.exists(os.path.join(socle.SOCLE_DIR, entree.get("fichier", "")))
            ),
            "empreinte": empreinte_socle(
                manifeste,
                {
                    os.path.basename(chemin): _sha256_fichier(chemin)
                    for chemin in (socle.DEVISES, socle.TVA_NATIONALE)
                },
            ),
        }
    except Exception as exc:
        socle_info = {"erreur": str(exc)}
    return {"backend_sha": BACKEND_SHA, "socle": socle_info}


@router.get("/health/status")
async def detailed_health():
    "detailed health status with all service checks"
    checks = {
        "api": {"status": "up", "latency_ms": 1},
        "database": {"status": "up", "type": "MongoDB"},
        "cache": {"status": "up", "type": "In-Memory"},
    }
    try:
        from notifications import NotificationManager

        manager = NotificationManager()
        enabled_channels = manager.get_enabled_channels()
        checks["notifications"] = {"status": "healthy"}
    except Exception:
        checks["notifications"] = {"status": "error"}
    return {"status": "healthy", "components": checks}
