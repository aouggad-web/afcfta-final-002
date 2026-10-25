"""CEDEAO : offre e-Tariff (TEC 2017) affichée pour une position TEC 2022.

Fiche : CEDEAO_concordance_TEC2022_TEC2017_2026-10-03.json. L'offre reste
informative (aucun calcul) ; ce fichier verrouille les deux voies de
rattachement et le refus quand la table du Mali contredit l'OMD.
"""

from __future__ import annotations

from services.official_preferential_rates import _concordance_cedeao, resolve_published_offer_rate


def test_la_table_du_mali_rattache_une_position_2022_a_sa_ligne_2017():
    # 0309.10 (farines de poisson, TEC 2022) vient de 0305.10.00.00 (TEC 2017).
    offre = resolve_published_offer_rate("NGA", "0309100000", "GHA")
    assert offre["hs_code"] == "0305100000"
    assert offre["concordance_tec2022_tec2017"]["sources_tec2017"] == ["0305100000"]


def test_les_cellules_du_tableau_font_foi():
    """Les codes 2022 sont centrés dans leur cellule : 8525.81 vient de
    8525.80, pas de 8519.50 comme le donnait une lecture par bandes."""
    assert resolve_published_offer_rate("NGA", "8525810000", "GHA")["hs_code"] == "8525800000"


def test_la_table_i_de_l_omd_rattache_un_sh6_absent_de_la_table_du_mali():
    # 0709.52 (truffes, SH 2022) : absent de la table du Mali ; la table I de
    # l'OMD le fait venir de 0709.59.
    assert "0709520000" not in _concordance_cedeao()["par_position_mali"]
    offre = resolve_published_offer_rate("NGA", "0709520000", "GHA")
    assert offre["hs_code"] == "0709590000"
    assert offre["concordance_tec2022_tec2017"]["sources_sh2017"] == ["070959"]


def test_une_paire_du_mali_contredite_par_l_omd_n_est_pas_retenue():
    # Table du Mali : 2518.30 → 2518.20 ; la table I de l'OMD ne donne que 2518.20.
    concordance = _concordance_cedeao()
    assert "2518200000" not in concordance["par_position_mali"]
    assert concordance["_ecartees"]["Mali : contredit par la table I de l'OMD"] == 5


def test_une_position_presente_dans_l_offre_n_utilise_pas_la_concordance():
    offre = resolve_published_offer_rate("NGA", "0101210000", "GHA")
    assert "concordance_tec2022_tec2017" not in offre
