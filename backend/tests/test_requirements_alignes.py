"""requirements.txt (Docker, CI) et backend/requirements.txt (Emergent) ne divergent pas (audit, INFO-10)."""

import re
from pathlib import Path

_DEPOT = Path(__file__).resolve().parents[2]
# Absents d'Emergent à dessein : aucun code servi ne les importe.
_RACINE_SEULEMENT = {"aiosmtplib", "apscheduler", "pytest-cov"}


def _lire(chemin):
    paquets = {}
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        ligne = ligne.split("#", 1)[0].strip()
        if ligne:
            nom, version = re.fullmatch(r"([A-Za-z0-9._-]+)(?:\[[^\]]*\])?==(\S+)", ligne).groups()
            paquets[re.sub(r"[-_.]+", "-", nom).lower()] = version
    return paquets


def test_requirements_racine_et_emergent_alignes():
    racine = _lire(_DEPOT / "requirements.txt")
    emergent = _lire(_DEPOT / "backend" / "requirements.txt")
    manquants = sorted(set(racine) - set(emergent) - _RACINE_SEULEMENT)
    assert not manquants, f"absents de backend/requirements.txt : {manquants}"
    ecarts = {
        n: (racine[n], emergent[n]) for n in racine.keys() & emergent if racine[n] != emergent[n]
    }
    assert not ecarts, f"versions différentes (racine, backend) : {ecarts}"
