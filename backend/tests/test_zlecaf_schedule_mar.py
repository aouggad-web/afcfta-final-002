"""Maroc : la liste A est démantelée sur le DI **et** la TPI (6530/223, III).

La circulaire ADII n° 6530/223 du 22/01/2024 soumet la liste A au démantèlement
du droit d'importation et de la taxe parafiscale à l'importation, sur le même
calendrier — 5 ans pour P1, 10 ans pour P2 à compter du 01/01/2021. L'avenant
n° 6627/223 du 09/01/2025 actualise les codes de la liste A et répète la règle.
Ce fichier verrouille : les 40 origines lues dans la fiche, le calendrier, la
réduction de la TPI dans les deux chemins de calcul, l'assiette de TVA
(CIF+DD+TPI, CGI Maroc art. 96) et le plafond NPF.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

import pytest

from services.authentic_tariff_service import (
    calculate_import_taxes,
    resolve_zlecaf_context,
)
from services.calcul import calculer
from services.preference import taux_preferentiels
from services.zlecaf_implementation_registry import APPLIED, RECORDS, implementation_decision
from services.zlecaf_schedule_mar import (
    ORIGINES_PAR_GROUPE,
    origine_admise,
    part_restante,
    tpi_preferentielle,
)

RACINE = Path(__file__).resolve().parents[2]
FICHE = (
    RACINE
    / "backend"
    / "data"
    / "legal_refs"
    / "zlecaf_application"
    / "MAR_application_2026-09-13.json"
)

P1 = "TUN"
P2 = "ZAF"
HORS_LISTE = "AGO"
#: Ligne réelle de la liste A : DD 10 %, TPI 0,25 %, TVA 20 % (socle MAR).
CODE = "0101291000"
#: Ligne réelle absente de la liste A publiée : la TPI y reste pleine.
CODE_HORS_LISTE_A = "0102293100"


def _position() -> dict:
    return {
        "droits": [
            {"code": "DD", "taux": 10.0, "assiette": "CIF", "famille": "droit"},
            {"code": "TPI", "taux": 0.25, "assiette": "CIF", "famille": "redevance"},
            {"code": "TVA", "taux": 20.0, "assiette": "CIF+DD+TPI", "famille": "tva"},
        ],
        "preferentiels": {},
    }


def test_les_40_origines_sont_lues_dans_la_fiche():
    """La liste n'est pas recopiée dans le code : elle vient de la fiche."""
    fiche = json.loads(FICHE.read_text(encoding="utf-8"))
    attendus = {
        iso: int(fiche["accepted_origins"][cle]["dismantling_years"])
        for cle in ("P1", "P2")
        for iso in fiche["accepted_origins"][cle]["iso3"]
    }

    assert ORIGINES_PAR_GROUPE == attendus
    assert len(ORIGINES_PAR_GROUPE) == 40
    assert sum(1 for ans in attendus.values() if ans == 5) == 27
    assert sum(1 for ans in attendus.values() if ans == 10) == 13
    assert RECORDS["MAR"].accepted_origins == frozenset(attendus)
    assert RECORDS["MAR"].status == APPLIED
    assert implementation_decision("MAR", P1)["applied"] is True
    assert implementation_decision("MAR", HORS_LISTE)["applied"] is False


def test_le_calendrier_est_celui_des_listes_p1_p2():
    """Annuités égales depuis le 1/1/2021 : P1 éteint en 2025, P2 à 40 % en 2026."""
    assert part_restante(P1, datetime.date(2024, 6, 1)) == pytest.approx(0.2)
    assert part_restante(P1, datetime.date(2025, 1, 1)) == 0.0
    assert part_restante(P2, datetime.date(2025, 1, 1)) == pytest.approx(0.5)
    assert part_restante(P2, datetime.date(2026, 1, 1)) == pytest.approx(0.4)
    assert part_restante(P2, datetime.date(2030, 1, 1)) == 0.0
    assert part_restante(P2, datetime.date(2020, 6, 1)) == 1.0
    assert part_restante(HORS_LISTE) is None


def test_la_tpi_suit_le_meme_calendrier_que_le_di():
    """Le texte démantèle le DI et la TPI ensemble — pas d'exonération binaire."""
    taux_p2, reference = tpi_preferentielle(0.25, P2, datetime.date(2026, 1, 1))
    taux_p1, _ = tpi_preferentielle(0.25, P1, datetime.date(2026, 1, 1))
    hors, _ = tpi_preferentielle(0.25, HORS_LISTE)

    assert taux_p2 == 0.1  # 0,25 × 40 %
    assert taux_p1 == 0.0
    assert hors is None
    assert "6530/223" in reference and "6627/223" in reference
    assert origine_admise(P2) and not origine_admise(HORS_LISTE)


def test_le_chemin_socle_sert_le_di_et_la_tpi_reduits():
    position = _position()
    part = part_restante(P2)
    assert part is not None

    for origine, facteur in ((P2, part), (P1, 0.0)):
        resultat = taux_preferentiels(position, "MAR", origine, CODE)
        assert resultat["applique"] is True, origine
        assert resultat["taux"]["TPI"]["taux"] == round(0.25 * facteur, 6), origine
        assert resultat["taux"]["DD"]["taux"] < 10.0, origine
        assert "6530/223" in resultat["perimetre"]["TPI"]


def test_une_origine_hors_liste_ne_reduit_ni_di_ni_tpi():
    position = _position()
    resultat = taux_preferentiels(position, "MAR", HORS_LISTE, CODE)

    assert resultat["applique"] is False
    assert resultat["taux"] == {}

    historique = calculate_import_taxes("MAR", CODE, 1000.0, origin_country=HORS_LISTE)
    # Aucun régime préférentiel n'est calculé : le bloc ZLECAf reste vide et la
    # TPI pleine (0,25 % → 2,50 sur 1 000).
    assert historique["zlecaf_calculation"] is None
    npf = historique["npf_calculation"]
    assert npf["other_taxes"]["rate_pct"] == 0.25
    assert npf["other_taxes"]["amount"] == 2.5
    assert npf["total_to_pay"] == 1323.0


def test_une_ligne_hors_liste_a_ne_reduit_ni_di_ni_tpi():
    """La TPI ne se réduit que sur une ligne de la liste A effectivement servie."""
    position = _position()
    resultat = taux_preferentiels(position, "MAR", P2, CODE_HORS_LISTE_A)

    assert resultat["applique"] is False
    assert resultat["taux"] == {}

    historique = calculate_import_taxes("MAR", CODE_HORS_LISTE_A, 1000.0, origin_country=P2)
    assert historique["zlecaf_calculation"] is None
    npf = historique["npf_calculation"]
    assert npf["other_taxes"]["amount"] == 2.5
    assert npf["dd"]["rate_pct"] == 200.0


def test_les_deux_chemins_servent_le_meme_taux_et_le_meme_total():
    """Socle et historique lisent le même calendrier : même DI, même TPI, même total."""
    table = taux_preferentiels(_position(), "MAR", P2, CODE)["taux"]
    socle = calculer(_position(), 1000.0, taux_preferentiels=table)["preference"]
    historique = calculate_import_taxes("MAR", CODE, 1000.0, origin_country=P2)

    assert socle is not None and socle["total_a_payer"] == 1249.2
    assert historique["zlecaf_calculation"]["total_to_pay"] == 1249.2
    assert socle["total_a_payer"] == historique["zlecaf_calculation"]["total_to_pay"]

    par_code = {ligne["code"]: ligne for ligne in socle["lignes"]}
    zlecaf = historique["zlecaf_calculation"]
    assert par_code["DD"]["taux_pct"] == zlecaf["dd"]["rate_pct"] == 4.0
    assert par_code["TPI"]["taux_pct"] == zlecaf["other_taxes"]["rate_pct"] == 0.1


def test_la_tva_est_assise_sur_le_di_et_la_tpi_reduits():
    """CGI Maroc art. 96 : TVA = CIF + DD + TPI, recalculée quand la TPI baisse."""
    resultat = calculate_import_taxes("MAR", CODE, 1000.0, origin_country=P2)

    npf = resultat["npf_calculation"]
    zlecaf = resultat["zlecaf_calculation"]
    assert npf["vat"]["base"] == 1000.0 + 100.0 + 2.5
    assert npf["vat"]["amount"] == 220.5
    assert zlecaf["dd"]["amount"] == 40.0
    assert zlecaf["other_taxes"]["amount"] == 1.0
    assert zlecaf["vat"]["base"] == 1000.0 + 40.0 + 1.0
    assert zlecaf["vat"]["amount"] == 208.2
    assert zlecaf["total_to_pay"] < npf["total_to_pay"]


def test_le_taux_servi_n_est_jamais_au_dessus_du_npf():
    for origine in (P1, P2, HORS_LISTE):
        contexte = resolve_zlecaf_context("MAR", origine, CODE, 10.0, None)
        assert contexte["dd_rate_pct"] is not None
        assert contexte["dd_rate_pct"] <= 10.0
        assert contexte["plancher_npf"] is None
