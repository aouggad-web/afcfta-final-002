"""Tunisie : coefficient 2026 du Tarif Web × droit de base 2019 de l'e-Tariff.

Fiche : TUN_droit_de_base_2019_2026-10-03.json. Ce fichier verrouille : le
produit des deux facteurs, le plafond NPF, le refus hors 2026, le refus d'une
origine non publiée, le contrôle par la loi de finances 2019 et le même droit
dans les deux chemins.
"""

from __future__ import annotations

import datetime

import pytest

import services.zlecaf_schedule_tun as module_tun
from services.authentic_tariff_service import calculate_import_taxes
from services.preference import taux_preferentiels
from services.zlecaf_implementation_registry import APPLIED, RECORDS, implementation_decision
from services.zlecaf_schedule_tun import (
    DROIT_DE_BASE_2019,
    ORIGINES_TARIF_WEB,
    compute_tun_zlecaf_rate,
)

#: Primates : NPF 2026 15 %, base 2019 36 %, coefficient liste A 40 % (0 %
#: pour la Tanzanie).
CODE = "01061100003"
EN_2026 = datetime.date(2026, 10, 3)


def _position(npf: float = 15.0) -> dict:
    return {
        "droits": [{"code": "DD", "taux": npf, "assiette": "CIF", "famille": "droit"}],
        "preferentiels": {},
    }


def test_le_registre_sert_les_origines_publiees_par_la_douane():
    record = RECORDS["TUN"]
    assert record.status == APPLIED
    assert record.accepted_origins == ORIGINES_TARIF_WEB
    assert ORIGINES_TARIF_WEB == {"CMR", "GHA", "KEN", "NGA", "ZAF", "TZA", "MUS", "RWA"}
    # Nommée par le texte de 2023, l'Égypte n'a aucune ligne au Tarif Web.
    assert implementation_decision("TUN", "EGY")["applied"] is False


def test_le_droit_est_le_coefficient_applique_au_droit_de_base_2019():
    assert compute_tun_zlecaf_rate(CODE, "CMR", 15.0, as_of=EN_2026)[0] == 14.4
    assert compute_tun_zlecaf_rate(CODE, "TZA", 15.0, as_of=EN_2026)[0] == 0.0


def test_le_droit_ne_depasse_jamais_le_npf():
    taux, libelle = compute_tun_zlecaf_rate(CODE, "CMR", 10.0, as_of=EN_2026)
    assert taux == 10.0
    assert "plafonné au NPF" in libelle


def test_rien_n_est_servi_hors_2026_ni_sans_coefficient():
    assert compute_tun_zlecaf_rate(CODE, "CMR", 15.0, as_of=datetime.date(2027, 1, 1))[0] is None
    # Motocycles : aucun coefficient ZLECAf publié au Tarif Web.
    assert compute_tun_zlecaf_rate("87112010027", "KEN", 43.0, as_of=EN_2026)[0] is None


def test_la_loi_de_finances_2019_confirme_le_droit_de_base():
    # Art. 81 : motocycles relevés à 30 % ; art. 60 : panneaux solaires à 20 %.
    for code in ("871120100", "871120929", "871150000", "871190003"):
        assert DROIT_DE_BASE_2019[code] == 30.0
    assert DROIT_DE_BASE_2019["854140900"] == 20.0


@pytest.mark.skipif(
    datetime.date.today().year != module_tun.ANNEE_DES_COEFFICIENTS,
    reason="coefficients publiés pour 2026 seulement",
)
def test_les_deux_chemins_servent_le_meme_droit():
    socle = taux_preferentiels(_position(), "TUN", "CMR", CODE)
    assert socle["applique"] is True
    historique = calculate_import_taxes("TUN", CODE, 1000.0, origin_country="CMR")
    assert historique["rates"]["effective_zlecaf_rate_pct"] == socle["taux"]["DD"]["taux"] == 14.4


def test_la_franchise_zale_est_signalee_sans_etre_calculee():
    from services.zlecaf_schedule_tun import note_zale

    # 8471.30 : 0 % publié pour l'Égypte (ZALE, Agadir) et l'Algérie (ZALE,
    # accord bilatéral) ; aucune note pour une origine ZLECAf.
    assert "0 %" in note_zale("84713000010", "EGY") and "Agadir" in note_zale("84713000010", "EGY")
    assert "accord bilatéral TUN-DZA" in note_zale("84713000010", "DZA")
    assert note_zale("84713000010", "CMR") is None

    historique = calculate_import_taxes("TUN", "84713000010", 1000.0, origin_country="DZA")
    assert historique["rates"]["effective_zlecaf_rate_pct"] is None
    assert "ZALE (GAFTA)" in historique["trade_regime_note"]
    socle = taux_preferentiels(_position(), "TUN", "EGY", "84713000010")
    assert socle["applique"] is False and "Agadir" in socle["note"]
