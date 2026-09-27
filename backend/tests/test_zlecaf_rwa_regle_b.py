"""Le Rwanda sert la préférence ZLECAf de la règle B — et rien qu'elle.

Règle B (propriétaire, 27/09/2026) : pour un État de l'EAC, le taux ZLECAf est
servi si quatre conditions sont réunies (ratification, TEC + EACCMA,
participation au GTI selon le Secrétariat, aucune source contraire). Pour le
Rwanda, elles sont documentées dans RWA_application_2026-09-25.json (PR #534).

Ces tests verrouillent les obligations de l'étape Rwanda :
(a) une origine admise hors EAC lit le même taux dans les deux chemins ;
(b) une origine intra-EAC relève de l'union douanière, jamais de la ZLECAf ;
(c) une origine hors Annexe 1 reste au NPF ;
(d) le plancher NPF : le socle rwandais peut être PLUS BAS que le barème
    (dérogation nationale) — c'est alors le NPF qui est servi, dans les deux
    chemins.

Les tests de la Tanzanie (test_zlecaf_tza_regle_b.py, PR #531) portent les
mêmes vérifications pour TZA ; ce fichier les adapte au Rwanda.
"""

import datetime
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import socle  # noqa: E402
from services.authentic_tariff_service import calculate_import_taxes  # noqa: E402
from services.preference import taux_preferentiels  # noqa: E402
from services.zlecaf_schedule_ken import compute_ken_zlecaf_rate  # noqa: E402

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle")

besoin_socle = pytest.mark.skipif(
    not (
        os.path.exists(os.path.join(SOCLE, "RWA.json"))
        and os.path.exists(os.path.join(SOCLE, "KEN.json"))
    ),
    reason="socle absent (gitignoré) : reconstruire avec scripts/build_socle.py",
)

EN_2026 = datetime.date(2026, 9, 27)


@besoin_socle
@pytest.mark.parametrize("code", ["02011000", "25232100"])
def test_a_une_origine_admie_lit_le_meme_taux_dans_les_deux_chemins(code):
    """Rwanda ← Ghana (hors EAC, Annexe 1) : le socle et le chemin historique
    servent le même taux, lu dans la même colonne du barème."""
    position, _ = socle.position("RWA", code)
    soc = taux_preferentiels(position, "RWA", "GHA", code)
    assert soc["applique"] is True
    assert soc["regime"] == "ZLECAF"

    hist = calculate_import_taxes("RWA", code, 10000, apply_zlecaf=True, origin_country="GHA")
    assert hist["zlecaf_preference_applied"] is True

    taux_socle = soc["taux"]["DD"]["taux"]
    taux_historique = hist["rates"]["effective_zlecaf_rate_pct"]
    assert taux_socle == taux_historique > 0.0

    # Et ce taux est bien celui que le barème publie pour 2026.
    attendu, _ = compute_ken_zlecaf_rate(code, "GHA", EN_2026)
    assert taux_socle == attendu


@besoin_socle
@pytest.mark.parametrize("origine", ["KEN", "TZA", "UGA"])
def test_b_une_origine_intra_eac_releve_de_l_union_jamais_de_la_zlecaf(origine):
    """Rwanda ← Kenya, Tanzanie, Ouganda : libre circulation intra-union EAC
    (0 %), jamais la préférence continentale — même si l'origine figure dans
    l'Annexe 1."""
    position, _ = socle.position("RWA", "02011000")
    decision = taux_preferentiels(position, "RWA", origine, "02011000")
    assert decision["regime"] == "UNION_DOUANIERE"
    assert decision["taux"]["DD"]["taux"] == 0.0
    assert "ZLECAF" not in decision["note"]


@besoin_socle
def test_c_une_origine_hors_annexe_1_rest_au_npf():
    """Rwanda ← Brésil : hors Annexe 1, aucun taux préférentiel — NPF."""
    position, _ = socle.position("RWA", "02011000")
    decision = taux_preferentiels(position, "RWA", "BRA", "02011000")
    assert decision["applique"] is False
    assert decision["taux"] == {}
    assert "ne figure pas dans la liste" in decision["note"]


@besoin_socle
def test_d_le_plancher_npf_sert_le_socle_quand_il_est_plus_bas():
    """2106.90.20 : dérogation nationale — le NPF rwandais du socle est
    0 % pour une base de barème de 10 %. En 2026 (sixième annuité) le barème
    porterait encore un taux positif : c'est le NPF qui est servi, dans les
    deux chemins."""
    position, _ = socle.position("RWA", "21069020")
    npf_socle = position["droits"][0]["taux"]
    assert npf_socle == 0.0  # la dérogation nationale, lue dans le socle

    # Le barème, lui, porterait un taux positif en 2026 — sans le plancher,
    # le socle l'aurait servi tel quel.
    taux_bareme, _ = compute_ken_zlecaf_rate("21069020", "GHA", EN_2026)
    assert taux_bareme is not None and taux_bareme > npf_socle

    soc = taux_preferentiels(position, "RWA", "GHA", "21069020")
    assert soc["taux"]["DD"]["taux"] == npf_socle
    assert "plancher NPF du socle" in soc["perimetre"]["DD"]

    hist = calculate_import_taxes("RWA", "21069020", 10000, apply_zlecaf=True, origin_country="GHA")
    assert hist["rates"]["effective_zlecaf_rate_pct"] == npf_socle


@besoin_socle
def test_d_bis_le_kenya_rest_sur_le_meme_plancher():
    """Le plancher est commun aux destinations règle B : la même position
    rwandaise sert 0 % au Kenya aussi — les deux chemins concordent."""
    position, _ = socle.position("KEN", "21069020")
    soc = taux_preferentiels(position, "KEN", "GHA", "21069020")
    assert soc["taux"]["DD"]["taux"] == 0.0

    hist = calculate_import_taxes("KEN", "21069020", 10000, apply_zlecaf=True, origin_country="GHA")
    assert hist["rates"]["effective_zlecaf_rate_pct"] == 0.0
