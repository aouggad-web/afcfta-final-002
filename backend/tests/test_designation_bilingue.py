"""Une désignation bilingue ne doit jamais atteindre l'interface comme objet.

Six crawls (LBY, MUS, MWI, SYC, ZMB, ZWE) publient leur désignation sous la
forme ``{fr, en, verbatim}``, avec ``fr`` vide. Servie telle quelle, elle
faisait planter l'interface au rendu (« Objects are not valid as a React
child ») : écran vide après le calcul, à Maurice comme en Zambie.
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.designation import texte_designation  # noqa: E402

PAYS_BILINGUES = ["LBY", "MUS", "MWI", "SYC", "ZMB", "ZWE"]
CRAWLS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "crawled"
)


def _hs6_bilingue(iso):
    """Un SH6 dont le crawl porte réellement une désignation {fr, en, verbatim}."""
    with open(os.path.join(CRAWLS, f"{iso}_tariffs.json"), encoding="utf-8") as f:
        donnees = json.load(f)
    lignes = donnees.get("sub_positions") or donnees.get("tariff_lines") or []
    for ligne in lignes.values() if isinstance(lignes, dict) else lignes:
        if isinstance(ligne.get("designation"), dict):
            for cle in ("hs_code", "code", "national_code", "code_raw", "hs6"):
                chiffres = re.sub(r"\D", "", str(ligne.get(cle) or ""))
                if len(chiffres) >= 6:
                    return chiffres[:6]
    raise AssertionError(f"{iso} : aucune désignation bilingue dans le crawl")


def test_la_langue_demandee_si_elle_existe_sinon_le_texte_publie():
    publie = {"en": "-- Of plastics", "fr": "", "verbatim": "-- Of plastics"}
    assert texte_designation(publie, "fr") == "-- Of plastics"  # rien n'est traduit
    assert texte_designation({"en": "x", "fr": "y", "verbatim": "x"}, "fr") == "y"
    assert texte_designation("déjà du texte") == "déjà du texte"


def test_le_moteur_du_socle_rend_une_designation_texte():
    """Le chemin du socle (POST /calcul) portait le même défaut : à Maurice,
    en Zambie et en Libye, `position.designation` sortait en objet."""
    from services.calcul import calculer

    position = {
        "designation": {
            "fr": "",
            "en": "- - - For spectacles",
            "ar": "",
            "verbatim": "- - - For spectacles",
        },
        "droits": [{"code": "DD", "taux": 15.0, "assiette": "CIF", "famille": "droit"}],
    }
    assert calculer(position, 1000)["position"]["designation"] == "- - - For spectacles"
