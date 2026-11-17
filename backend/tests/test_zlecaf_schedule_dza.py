"""
Tests du calendrier de démantèlement ZLECAf à l'importation en Algérie
(circulaire DGD n°482/2024). Vérifie : éligibilité par pays partenaire,
classement liste (A)/(B)/(C), gel des règles d'origine, et les facteurs de
réduction des deux calendriers (standard vs réciprocité) à des dates clés.
"""

import datetime
import re
from pathlib import Path

import pytest

from services.zlecaf_schedule_dza import (
    ACTIVE_PARTNERS,
    CIRCULAR_482_SCHEDULE,
    DZ_ACTIVE_ORIGINS,
    LIST_B_BASE_RATES_2019,
    LIST_B_CODES,
    ORIGINES_CIRCULAIRE_482,
    ORIGINES_NOMMEES_LISTE_DOUANE_2026_11,
    RECIPROCITY_PARTNERS,
    compute_dza_zlecaf_rate,
    daps_exempt,
    is_frozen,
    tariff_list,
)


def _non_frozen_list_b_code() -> str:
    """LIST_B_CODES is a frozenset: iteration order depends on the hash
    seed of the process, so picking via next(iter(...)) can flakily land
    on a code whose heading is also in FROZEN_HEADINGS. Pick deterministically."""
    for code in sorted(LIST_B_CODES):
        if not is_frozen(code):
            return code
    raise AssertionError("aucun code liste (B) non gelé trouvé")


def test_non_active_partner_gets_npf_rate():
    rate, source = compute_dza_zlecaf_rate("0101211100", "NGA", 0.15)
    assert rate == 0.15
    assert "non encore activé" in source


def test_active_non_reciprocity_partner_list_a_fully_eliminated_2026():
    # TUN n'est pas dans RECIPROCITY_PARTNERS -> calendrier standard.
    # Code hors liste B/C connue -> liste (A), éliminée depuis 1.1.2025.
    rate, source = compute_dza_zlecaf_rate(
        "2901101000", "TUN", 0.15, as_of=datetime.date(2026, 6, 18)
    )
    assert rate == 0.0
    assert "liste (A)" in source


def test_reciprocity_partner_list_a_partial_reduction_2026():
    # CMR est dans RECIPROCITY_PARTNERS -> calendrier plus long.
    # 2026 -> facteur 0.4 (60% de réduction cumulée depuis 2021).
    rate, source = compute_dza_zlecaf_rate(
        "2901101000", "CMR", 0.30, as_of=datetime.date(2026, 6, 18)
    )
    assert abs(rate - 0.12) < 1e-9
    assert "réciprocité" in source


def test_list_b_standard_partner_full_rate_during_transition():
    # Le taux de base officiel 2019 (table détaillée liste (B)/réciprocité)
    # prévaut sur le taux normal transmis, qui peut être obsolète/différent.
    code = _non_frozen_list_b_code()
    base = LIST_B_BASE_RATES_2019[code]
    rate, source = compute_dza_zlecaf_rate(code, "TUN", 0.999, as_of=datetime.date(2024, 6, 18))
    assert rate == base  # transition 2021-2025 : droit commun (taux de base) maintenu
    assert "liste (B)" in source
    assert "taux de base 2019" in source


def test_list_b_standard_partner_reduction_starts_2026():
    code = _non_frozen_list_b_code()
    base = LIST_B_BASE_RATES_2019[code]
    rate, _ = compute_dza_zlecaf_rate(code, "TUN", 0.999, as_of=datetime.date(2026, 6, 18))
    assert abs(rate - base * 0.8) < 1e-9  # 80% du droit de base


def test_list_c_never_reduced():
    code = next(
        iter(__import__("services.zlecaf_schedule_dza", fromlist=["LIST_C_CODES"]).LIST_C_CODES)
    )
    assert tariff_list(code) == "C"
    rate, source = compute_dza_zlecaf_rate(code, "EGY", 0.30, as_of=datetime.date(2030, 1, 1))
    assert rate == 0.30
    assert "liste (c)" in source.lower()


def test_les_lignes_issues_d_une_ligne_de_la_liste_c_en_restent():
    # Tomates (0702.00) et dattes (0804.10) : toutes leurs lignes sont en (C)
    # dans la circulaire ; le tarif DGD les a subdivisées depuis.
    for code in ("0702001100", "0702009900", "0804103000", "0804104242"):
        assert tariff_list(code) == "C", code


def test_frozen_textile_heading_kept_at_npf():
    assert is_frozen("5111100000")
    rate, source = compute_dza_zlecaf_rate(
        "5111100000", "TUN", 0.30, as_of=datetime.date(2030, 1, 1)
    )
    assert rate == 0.30
    assert "gelée" in source


def test_frozen_vehicle_heading_kept_at_npf():
    assert is_frozen("8703231900")


def test_non_frozen_heading_outside_ranges():
    assert not is_frozen("2901101000")


def test_unknown_code_defaults_to_list_a():
    assert tariff_list("9999999999") == "A"


def test_list_b_uses_authoritative_2019_base_rate_not_stale_normal_rate():
    # 0201.10.11.00 (viande de veau) : taux de base ZLECAf 2019 = 30%, mais
    # la nomenclature tarifaire générale affiche aujourd'hui 5% (réduction
    # postérieure à 2019, hors ZLECAf). Le calendrier ZLECAf doit s'appliquer
    # sur le taux de base figé (30%), pas sur le taux normal courant (5%).
    code = "0201101100"
    assert LIST_B_BASE_RATES_2019[code] == 30.0
    rate, source = compute_dza_zlecaf_rate(code, "TUN", 5.0, as_of=datetime.date(2026, 6, 18))
    assert abs(rate - 30.0 * 0.8) < 1e-9
    assert "taux de base 2019" in source


def test_les_taux_sont_des_pourcentages_de_bout_en_bout():
    """Un taux publié se transporte tel quel, sans conversion.

    Le module attendait autrefois une FRACTION là où tout le reste du moteur
    manie des pourcentages, sans que la convention soit écrite nulle part. Un
    appelant qui l'ignorait se trompait d'un facteur 100 en silence.

    On vérifie les deux bouts : le taux de base est chargé tel que la source
    le publie, et un taux fin — 0,5 % — ressort à 0,5 % et non à 50 % ni à
    0,005 %.
    """
    assert set(LIST_B_BASE_RATES_2019.values()) <= {
        5.0,
        15.0,
        30.0,
        60.0,
    }, "les taux de base doivent rester ceux que la source publie"
    # Position gelée : le taux passé ressort intact, donc l'unité se lit à nu.
    rate, source = compute_dza_zlecaf_rate(
        "5204209100", "TUN", 0.5, as_of=datetime.date(2026, 6, 18)
    )
    assert rate == 0.5, "un taux publié à 0,5 % doit ressortir à 0,5 %"
    assert "gelée" in source


def test_list_a_code_keeps_passed_normal_rate_no_base_override():
    # La table de base 2019 ne couvre que la liste (B) : pour la liste (A),
    # le taux normal transmis par l'appelant reste la seule source.
    rate, _ = compute_dza_zlecaf_rate("2901101000", "TUN", 15.0, as_of=datetime.date(2026, 6, 18))
    assert rate == 0.0


def test_daps_exempt_for_list_a_active_partner():
    assert daps_exempt("2901101000", "TUN") is True


def test_daps_not_exempt_for_inactive_partner():
    assert daps_exempt("2901101000", "NGA") is False


def test_daps_not_exempt_for_frozen_heading():
    assert daps_exempt("5111100000", "TUN") is False


def test_active_partners_count():
    """Neuf origines de la circulaire 482/2024 et douze de la liste actualisée de la Douane (16/11/2026)."""
    assert len(ACTIVE_PARTNERS) == 21
    assert ORIGINES_CIRCULAIRE_482 <= ACTIVE_PARTNERS and len(ORIGINES_CIRCULAIRE_482) == 9
    assert ACTIVE_PARTNERS == DZ_ACTIVE_ORIGINS["origines"]


def test_la_liste_de_la_douane_ajoute_douze_origines_et_pas_le_nigeria_ni_le_mozambique():
    ajoutees = ACTIVE_PARTNERS - ORIGINES_CIRCULAIRE_482
    assert ajoutees == {"BDI", "BWA", "ETH", "SWZ", "GMB", "LSO", "MWI", "MAR", "NAM", "UGA", "SYC", "ZMB"}
    assert not {"NGA", "MOZ"} & ACTIVE_PARTNERS
    # La liste nomme 22 origines étrangères : les neuf de la circulaire et treize autres.
    assert len(ORIGINES_CIRCULAIRE_482 | ORIGINES_NOMMEES_LISTE_DOUANE_2026_11) == 22


def test_le_soudan_du_sud_est_nomme_mais_pas_servi_faute_de_ratification():
    """Le statut continental du dépôt le tient pour non ratifiant : il entrera à sa ratification."""
    from services.zlecaf_membership_status import SIGNED_NOT_RATIFIED

    assert "SSD" in ORIGINES_NOMMEES_LISTE_DOUANE_2026_11 and "SSD" in SIGNED_NOT_RATIFIED
    assert "SSD" not in ACTIVE_PARTNERS
    assert DZ_ACTIVE_ORIGINS["origines_nommees_non_servies"] == frozenset({"SSD"})
    taux, libelle = compute_dza_zlecaf_rate("0204501100", "SSD", 30.0, datetime.date(2026, 11, 17))
    assert taux == 30.0 and "non encore activé" in libelle


def test_la_table_dit_ce_qu_elle_ne_sait_pas():
    assert DZ_ACTIVE_ORIGINS["date_derniere_revision"] is None
    assert DZ_ACTIVE_ORIGINS["version"] == "2026-11-16"
    assert DZ_ACTIVE_ORIGINS["origines_circulaire_482"].isdisjoint(DZ_ACTIVE_ORIGINS["origines_liste_douane_2026_11"])


@pytest.mark.parametrize("origine,calendrier", [
    ("BWA", "réciprocité"), ("SWZ", "réciprocité"), ("NAM", "réciprocité"),
    ("BDI", "standard"), ("ETH", "standard"), ("MAR", "standard"), ("UGA", "standard"), ("ZMB", "standard"),
])
def test_les_origines_ajoutees_suivent_le_calendrier_de_leur_groupe(origine, calendrier):
    """Les membres de la liste de réciprocité de l'article 5 (i) ont le calendrier long."""
    taux, libelle = compute_dza_zlecaf_rate("0204501100", origine, 30.0, datetime.date(2026, 11, 17))
    assert f"calendrier {calendrier}" in libelle
    assert ("réciprocité" in libelle) == (origine in RECIPROCITY_PARTNERS)
    assert taux is not None and taux < 30.0


def test_les_facteurs_de_2026_sont_ceux_du_relevé_de_veille():
    """Liste A standard 0 %, réciprocité A 40 % ; liste B standard 80 %, réciprocité B 87,5 % (2026)."""
    le = datetime.date(2026, 11, 17)
    a = "0204501100"
    assert tariff_list(a) == "A" and not is_frozen(a)
    assert compute_dza_zlecaf_rate(a, "UGA", 30.0, le)[0] == 0.0
    assert compute_dza_zlecaf_rate(a, "NAM", 30.0, le)[0] == pytest.approx(12.0)
    b = next(c for c in sorted(LIST_B_BASE_RATES_2019) if c in LIST_B_CODES and not is_frozen(c))
    base = LIST_B_BASE_RATES_2019[b]
    assert compute_dza_zlecaf_rate(b, "UGA", 99.0, le)[0] == pytest.approx(base * 0.8)
    assert compute_dza_zlecaf_rate(b, "NAM", 99.0, le)[0] == pytest.approx(base * 0.875)


def test_le_taux_d_une_origine_ajoutee_dit_sa_source():
    _, ajoutee = compute_dza_zlecaf_rate("0204501100", "UGA", 30.0, datetime.date(2026, 11, 17))
    _, circulaire = compute_dza_zlecaf_rate("0204501100", "TUN", 30.0, datetime.date(2026, 11, 17))
    assert "article805" in ajoutee and "17/11/2026" in ajoutee and "date de révision inconnue" in ajoutee
    assert "article805" not in circulaire


def test_le_daps_est_exonere_pour_les_origines_ajoutees_sur_les_listes_a_et_b():
    assert daps_exempt("2901101000", "UGA") is True
    assert daps_exempt("2901101000", "SSD") is False
    assert daps_exempt("2901101000", "MOZ") is False


def test_reciprocity_partners_count():
    assert len(RECIPROCITY_PARTNERS) == 13


def test_circular_482_source_record_is_primary_and_traceable():
    assert CIRCULAR_482_SCHEDULE["source_id"] == "DZA-DGD-CIRC-482-2024"
    assert CIRCULAR_482_SCHEDULE["issuing_authority"] == (
        "Direction générale des douanes algériennes"
    )
    assert CIRCULAR_482_SCHEDULE["legal_date"] == "2024-10-22"
    assert CIRCULAR_482_SCHEDULE["verification_status"] == "DOCUMENTED"
    assert CIRCULAR_482_SCHEDULE["provided_extract_sha256"] == (
        "483e8d2cf6f8769eb7d3bbfc9dda1a3df2132b6fe504bbd554f7bab1c80bdc99"
    )


def test_circular_482_line_counts_match_archived_lists():
    counts = CIRCULAR_482_SCHEDULE["tariff_line_counts"]
    assert counts == {
        "total": 17322,
        "list_a": 15703,
        "list_a_frozen_for_missing_origin_rules": 1136,
        "list_b": 1163,
        "list_b_frozen_for_missing_origin_rules": 322,
        "list_c": 456,
    }
    assert len(LIST_B_CODES) == counts["list_b"]
    assert len(LIST_B_BASE_RATES_2019) == counts["list_b"]
    assert (
        len(__import__("services.zlecaf_schedule_dza", fromlist=["LIST_C_CODES"]).LIST_C_CODES)
        == counts["list_c"]
    )


def test_list_a_full_elimination_after_2030_reciprocity():
    rate, _ = compute_dza_zlecaf_rate("2901101000", "ZAF", 0.30, as_of=datetime.date(2031, 1, 1))
    assert rate == 0.0


def test_list_a_full_rate_before_agreement_entry():
    rate, _ = compute_dza_zlecaf_rate("2901101000", "TUN", 0.30, as_of=datetime.date(2020, 1, 1))
    assert rate == 0.30


# ── La page officielle de la Douane (article805), texte archivé ───────────────────────────────

PAGE = (
    Path(__file__).resolve().parents[1] / "data" / "legal_refs" / "zlecaf_application" / "sources"
    / "DZA_douane_article805_zlecaf.texte-fourni.txt"
)
ISO3 = {
    "Algérie": "DZA", "Afrique du Sud": "ZAF", "Burundi": "BDI", "Botswana": "BWA", "Égypte": "EGY",
    "Cameroun": "CMR", "Éthiopie": "ETH", "Eswatini": "SWZ", "Gambie": "GMB", "Ghana": "GHA",
    "Lesotho": "LSO", "Kenya": "KEN", "Malawi": "MWI", "Namibie": "NAM", "Maurice": "MUS", "Maroc": "MAR",
    "Ouganda": "UGA", "Rwanda": "RWA", "Seychelles": "SYC", "Soudan du sud": "SSD", "Tanzanie": "TZA",
    "Tunisie": "TUN", "Zambie": "ZMB", "Cap-Vert": "CPV", "République du Congo": "COG",
    "Côte d’Ivoire": "CIV", "Gabon": "GAB", "Guinée équatoriale": "GNQ", "Nigeria": "NGA",
}


def _noms(texte):
    return [ISO3[nom.strip()] for nom in re.split(r",| et ", texte.rstrip(". ")) if nom.strip()]


def _page():
    return PAGE.read_text(encoding="utf-8")


def test_la_liste_de_la_page_est_celle_de_la_table_des_origines():
    """Section III de la page : les parties « ayant lancé l'application », Algérie comprise. La table
    du code porte les mêmes pays, à une exception nommée : le Soudan du Sud, non ratifiant."""
    section = _page().split("III- Parties contractantes ayant lancées l’application de l’Accord :")[1]
    liste = section.split("NB :")[0].strip()
    parties = set(_noms(liste))

    assert len(parties) == 23 and "DZA" in parties
    assert "actualisée périodiquement" in section.split("IV-")[0]
    servies = ACTIVE_PARTNERS | DZ_ACTIVE_ORIGINS["origines_nommees_non_servies"] | {"DZA"}
    assert parties == servies
    assert not {"NGA", "MOZ"} & parties


def test_la_liste_de_reciprocite_de_la_page_est_celle_du_code():
    page = _page()
    texte = page.split("concernés par ce traitement sont les suivants :")[1].split("\n")[0]
    assert set(_noms(texte)) == RECIPROCITY_PARTNERS and len(RECIPROCITY_PARTNERS) == 13


def test_le_calendrier_de_la_page_est_celui_du_calendrier_du_code():
    """Régime général : liste A éliminée au 01/01/2025, liste B de 2026 à 2030 ; réciprocité : liste A
    jusqu'en 2030, liste B de 2026 à 2033."""
    page = _page()
    assert "exonération totale prévue au 1er janvier 2025" in page
    assert "élimination totale des droits de douane prévue au 1er janvier 2030" in page
    assert "élimination complète au 1er janvier 2033" in page
    standard = CIRCULAR_482_SCHEDULE["standard_schedule"]
    assert (standard["list_a_zero_from"], standard["list_b_reduction_from"], standard["list_b_zero_from"]) == (2025, 2026, 2030)
    reciprocite = CIRCULAR_482_SCHEDULE["reciprocity_schedule"]
    assert (reciprocite["list_a_zero_from"], reciprocite["list_b_reduction_from"], reciprocite["list_b_zero_from"]) == (2030, 2026, 2033)
