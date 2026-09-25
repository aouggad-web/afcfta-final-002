"""L'Égypte réduit la liste A pour 19 origines — jamais plus que le NPF.

Les circulaires n° 38 de 2024 et n° 44 de 2025 nomment les origines admises,
ne réduisent que la liste A, et reportent les chapitres 50 à 63 et 87. La carte
d'origines de l'e-Tariff Book de l'UA en contredit 15 sur 19, et ses barèmes
publient des réductions sur les chapitres reportés : le taux servi vient du NPF
et du calendrier national, jamais de l'offre. Voir
EGY_rapprochement_baremes_2026-09-24.json.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

from services.authentic_tariff_service import resolve_zlecaf_context
from services.official_preferential_rates import (
    published_offer_category,
    resolve_official_preferential_rate,
    resolve_published_offer_rate,
)
from services.preference import taux_preferentiels
from services.zlecaf_implementation_registry import APPLIED, RECORDS, implementation_decision
from services.zlecaf_schedule_egy import (
    ORIGINES_PAR_GROUPE,
    categorie_produit,
    compute_egy_zlecaf_rate,
    origine_admise,
)

RACINE = Path(__file__).resolve().parents[2]
FICHE = (
    RACINE
    / "backend"
    / "data"
    / "legal_refs"
    / "zlecaf_application"
    / "EGY_application_2026-09-14.json"
)

A_10_ANS = "ZAF"
A_5_ANS = "TUN"
LIGNE_A = "0101210000"
LIGNE_B = "8537209010"
LIGNE_C = "0406300010"
LIGNE_87_A = "8701100010"
LIGNE_50_A = "5004000010"


def _position(npf: float) -> dict:
    return {
        "droits": [{"code": "DD", "taux": npf, "assiette": "CIF"}],
        "preferentiels": {},
    }


def test_les_19_origines_sont_lues_dans_la_fiche():
    """La liste n'est pas recopiée dans le code : elle vient de la fiche."""
    fiche = json.loads(FICHE.read_text(encoding="utf-8"))
    attendus = {
        iso: int(groupe["dismantling_years"])
        for cle, groupe in fiche["accepted_origins"].items()
        if cle.startswith("groupe_")
        for iso in groupe["iso3"]
    }

    assert ORIGINES_PAR_GROUPE == attendus
    assert len(ORIGINES_PAR_GROUPE) == 19
    assert sum(1 for ans in attendus.values() if ans == 10) == 8
    assert sum(1 for ans in attendus.values() if ans == 5) == 11
    assert RECORDS["EGY"].accepted_origins == frozenset(attendus)
    assert RECORDS["EGY"].status == APPLIED


def test_le_taux_de_2026_est_lu_dans_la_circulaire_44():
    """Le 60 % du 1/1/2026 est imprimé dans la n° 44, pas déduit d'un chiffre."""
    fiche = json.loads(FICHE.read_text(encoding="utf-8"))
    groupe = fiche["accepted_origins"]["groupe_10_ans"]

    assert groupe["count"] == 8
    assert {"NAM", "NGA"} <= set(groupe["iso3"])
    assert groupe["reduction_rate_at_2026_01_01_pct"] == 60
    assert "60%" in groupe["verbatim_ar"]


def test_le_groupe_a_10_ans_n_est_pas_elimine_en_2026():
    """50 % de réduction au 1/1/2025, 60 % au 1/1/2026 : il reste 40 % du droit."""
    taux_2025, _ = compute_egy_zlecaf_rate(LIGNE_A, A_10_ANS, 5.0, datetime.date(2025, 1, 1))
    taux_2026, motif = compute_egy_zlecaf_rate(LIGNE_A, A_10_ANS, 5.0, datetime.date(2026, 1, 1))

    assert taux_2025 == 2.5
    assert taux_2026 == 2.0
    assert "groupe 10" in motif


def test_le_groupe_a_5_ans_est_elimine_des_2025():
    for origine in ("TUN", "MAR", "DZA"):
        for annee in (2025, 2026):
            taux, motif = compute_egy_zlecaf_rate(LIGNE_A, origine, 5.0, datetime.date(annee, 6, 1))
            assert taux == 0.0, (origine, annee)
            assert "groupe 5" in motif


def test_une_origine_hors_liste_reste_au_npf():
    for origine in ("FRA", "SEN", "BFA"):
        assert not origine_admise(origine)
        taux, motif = compute_egy_zlecaf_rate(LIGNE_A, origine, 5.0, datetime.date(2026, 6, 1))
        assert taux == 5.0
        assert "non notifié" in motif
        assert implementation_decision("EGY", origine)["applied"] is False

    contexte = resolve_zlecaf_context("EGY", "FRA", LIGNE_A, 5.0, None)
    assert contexte["trade_regime"] != "ZLECAF"
    assert contexte["dd_rate_pct"] == 5.0


def test_une_ligne_de_liste_b_ou_c_reste_au_npf():
    """La circulaire ne réduit que la liste A ; une ligne B ou C ne l'est pas."""
    for code in (LIGNE_B, LIGNE_C):
        assert categorie_produit(code) in ("B", "C")
        taux, motif = compute_egy_zlecaf_rate(code, A_10_ANS, 10.0, datetime.date(2026, 6, 1))
        assert taux == 10.0, code
        assert "hors liste A" in motif

    contexte = resolve_zlecaf_context("EGY", A_10_ANS, LIGNE_B, 10.0, None)
    assert contexte["trade_regime"] == "ZLECAF"
    assert contexte["dd_rate_pct"] == 10.0
    assert contexte["preference_applied"] is False


def test_les_chapitres_50_a_63_et_87_restent_au_npf():
    """La n° 44 reporte ces chapitres, même pour une ligne de liste A."""
    for code in (LIGNE_87_A, LIGNE_50_A):
        assert categorie_produit(code) == "A", code
        taux, motif = compute_egy_zlecaf_rate(code, A_10_ANS, 5.0, datetime.date(2026, 6, 1))
        assert taux == 5.0, code
        assert "reportée" in motif


def test_le_taux_preferentiel_n_est_jamais_au_dessus_du_npf():
    for origine in (A_10_ANS, A_5_ANS, "XOF"):
        for code in (LIGNE_A, LIGNE_87_A, LIGNE_B):
            for npf in (0.0, 2.0, 25.0):
                for annee in (2024, 2025, 2026, 2031):
                    taux, _ = compute_egy_zlecaf_rate(
                        code, origine, npf, datetime.date(annee, 6, 1)
                    )
                    assert 0.0 <= taux <= npf, (origine, code, npf, annee)


def test_le_chemin_historique_sert_le_calendrier_national():
    attendu, _ = compute_egy_zlecaf_rate(LIGNE_A, A_10_ANS, 5.0)
    contexte = resolve_zlecaf_context("EGY", A_10_ANS, LIGNE_A, 5.0, None)

    assert contexte["trade_regime"] == "ZLECAF"
    assert contexte["dd_rate_pct"] == attendu
    assert contexte["preference_applied"] == (attendu < 5.0)
    assert contexte["plancher_npf"] is None


def test_le_chemin_socle_sert_le_meme_taux_que_le_chemin_historique():
    attendu, _ = compute_egy_zlecaf_rate(LIGNE_A, A_10_ANS, 5.0)
    resultat = taux_preferentiels(_position(5.0), "EGY", A_10_ANS, LIGNE_A)

    assert resultat["applique"] is True
    assert resultat["taux"]["DD"]["taux"] == attendu

    bloque = taux_preferentiels(_position(10.0), "EGY", A_10_ANS, LIGNE_B)
    assert bloque["applique"] is True
    assert bloque["taux"]["DD"]["taux"] == 10.0


def test_l_offre_de_l_ua_ne_sert_jamais_l_egypte():
    """La carte de l'UA contredit la circulaire : son barème n'est pas servi."""
    assert resolve_official_preferential_rate("EGY", LIGNE_A, A_10_ANS) is None
    assert resolve_official_preferential_rate("EGY", LIGNE_A, A_5_ANS) is None
    assert resolve_published_offer_rate("EGY", LIGNE_A, A_10_ANS) is None


def test_la_categorie_est_lue_a_la_maille_publiee_de_l_offre():
    assert published_offer_category("EGY", LIGNE_A) == "A"
    assert published_offer_category("EGY", LIGNE_B) == "B"
    assert published_offer_category("EGY", LIGNE_C) == "C"
    assert published_offer_category("EGY", "9999999999") is None
    assert published_offer_category("XYZ", LIGNE_A) is None
