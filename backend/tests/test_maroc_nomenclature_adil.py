"""Maroc : le socle suit la nomenclature que le portail ADIL publie.

Le relevé des droits date du 11/02/2026. Depuis, le tarif a redécoupé 85
positions SH6 : la nomenclature ADIL relevée le 21/10/2026 porte 292 positions
que le relevé ignore et ne porte plus 163 des siennes. Une position retirée ne
se liquide plus ; une position nouvelle est servie sans droit connu, et le
calcul refuse son total au lieu de l'inventer."""

import json
import os

import pytest

from services import socle
from services.calcul import calculer

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NOMENCLATURE = os.path.join(RACINE, "data", "morocco", "adil_nomenclature_2026-10-21.json")
MUETTES = os.path.join(RACINE, "data", "morocco", "verification_positions_muettes.json")

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(socle.SOCLE_DIR, "MAR.json")),
    reason="socle absent : python3 scripts/build_socle.py",
)


@pytest.fixture(scope="module")
def positions():
    return socle.charger("MAR")["positions"]


def test_les_positions_servies_sont_celles_que_publie_l_adil(positions):
    with open(NOMENCLATURE, encoding="utf-8") as f:
        publiees = json.load(f)["positions"]
    assert set(positions) == set(publiees)
    assert len(positions) == 13243


def test_les_positions_muettes_etaient_des_positions_supprimees(positions):
    """Les 142 positions sans aucune taxe du relevé ne sont plus au tarif."""
    with open(MUETTES, encoding="utf-8") as f:
        muettes = json.load(f)["positions"]
    assert len(muettes) == 142
    assert not set(muettes) & set(positions)


def test_une_position_nouvelle_est_servie_sans_droit_invente(positions):
    nouvelle = positions["0902100010"]
    (dd,) = nouvelle["droits"]
    assert dd["code"] == "DD" and dd["taux"] is None
    assert "à compléter" in dd["note"]
    assert calculer(nouvelle, 1000.0)["npf"]["etat"] == "INDISPONIBLE"


def test_le_sh6_redecoupe_propose_les_nouvelles_positions():
    codes = [p["code"] for p in socle.positions_nationales("MAR", "090210")]
    assert codes == ["0902100010", "0902100090"]


def test_la_designation_d_une_position_nouvelle_dit_la_marchandise(positions):
    """« autres » seul ne dit pas qu'il s'agit de thé : la désignation remonte
    les titres publiés, et un libellé SH6 emprunté porte sa source."""
    designation = positions["0902100090"]["designation"]
    assert designation["fr"].startswith("Thé, même aromatisé — Thé vert")
    assert designation["fr"].endswith("— autres")
    titre, sh6, ligne = designation["hierarchie"]
    assert (titre["code"], ligne["code"]) == ("0902", "0902100090")
    assert titre["source"] == ligne["source"] == "douane.gov.ma/adil — nomenclature"
    assert sh6["code"] == "090210" and sh6["source"].startswith("libellé SH6 emprunté")
    # Un titre à huit chiffres publié tient lieu de titre SH6 : rien d'emprunté.
    beurre = positions["0405100091"]["designation"]["hierarchie"]
    assert [n["code"] for n in beurre] == ["0405", "04051000", "0405100091"]


def test_la_provenance_distingue_la_date_des_codes_de_celle_des_taux():
    _, nouvelle = socle.position("MAR", "0902100090")
    assert nouvelle["dates"] == {"codes": "2026-10-21", "taux": None}
    assert nouvelle["nomenclature"]["releve_le"] == "2026-10-21"
    _, ancienne = socle.position("MAR", "0101210000")
    assert ancienne["dates"] == {"codes": "2026-10-21", "taux": "2026-02-11"}
