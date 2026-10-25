"""Zimbabwe et Seychelles : TVA à l'importation, famille absente du crawl.

Fiche : ZWE_TVA_importation_2026-10-05.json. Taux 15,5 % depuis le
01/01/2026 (ZIMRA Public Notice No. 7 of 2026) ; assiette : valeur en douane
plus les droits du Customs and Excise Act, surtaxe exclue (VAT Act s.12(2)).
"""

import json
import os
import pathlib

import pytest

from routes.calcul import _completer_famille_absente
from services import socle
from services.calcul import calculer

RACINE = pathlib.Path(__file__).resolve().parents[1]


def test_la_table_cite_sa_fiche_et_le_taux_de_2026():
    entree = json.loads((RACINE / "socle" / "tva_nationale.json").read_text(encoding="utf-8"))["pays"]["ZWE"]
    assert entree["taux"] == 15.5 and entree["assiette"] == "CIF+DD+EXC"
    assert (RACINE.parent / entree["fiche"]).exists()


@pytest.mark.skipif(not os.path.exists(RACINE / "socle" / "ZWE.json"), reason="socle absent (gitignoré)")
def test_la_tva_se_liquide_sur_la_valeur_plus_le_droit_cumulatif():
    """Yaourt 0403.20 : DD 40 % + 0,50 USD/L = 405 ; TVA 15,5 % × 1 405."""
    position, provenance = socle.position("ZWE", "04032000")
    position, complements = _completer_famille_absente(position, "ZWE", provenance)
    assert complements
    r = calculer(
        position, 1000, quantite=10, devise_cif="USD",
        devise_position=provenance.get("devise_nationale"), couverture=provenance.get("couverture"),
    )
    tva = next(ligne for ligne in r["npf"]["lignes"] if ligne["code"] == "TVA")
    assert (tva["base"], tva["montant"]) == (1405.0, 217.775)
    assert r["npf"]["etat"] == "COMPLET"


@pytest.mark.skipif(not os.path.exists(RACINE / "socle" / "SYC.json"), reason="socle absent (gitignoré)")
def test_seychelles_la_tva_hors_accise_est_complete_et_incomplete_sous_accise():
    """Fiche SYC_TVA_importation_2026-10-05.json : 15 % sur CIF + DD + accise.
    L'accise n'est pas collectée : sur une position du barème S.I. 110/2023
    (bière 2203.00.31), la TVA se déclare incomplète au lieu d'être sous-estimée."""
    for code, attendu in (("01012100", 150.0), ("22030031", None)):
        position, provenance = socle.position("SYC", code)
        position, _ = _completer_famille_absente(position, "SYC", provenance)
        r = calculer(
            position, 1000, quantite=10, devise_cif="SCR",
            devise_position=provenance.get("devise_nationale"), couverture=provenance.get("couverture"),
        )
        tva = next(ligne for ligne in r["npf"]["lignes"] if ligne["code"] == "TVA")
        assert tva["montant"] == attendu
