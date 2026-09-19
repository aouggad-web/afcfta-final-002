"""Une entrée TVA du détail laissée sans taux ne devient jamais 0 %.

Le garde #472 refuse de servir un total quand une taxe manque. Il lit deux
chemins : le taux agrégé de la ligne (`vat_rate`) et le détail des taxes. Le
second avait perdu son arbitrage : toute entrée reconnue comme TVA et laissée
sans taux y était posée à 0 %, quel que soit le pays, sans rien signaler.

Le symptôme exact que ces tests fixent : une TVA absente et une TVA publiée à
0 % rendaient alors le *même* total, à l'euro près. Rien, dans la sortie, ne
permettait de les distinguer — l'opérateur lisait un montant amputé d'une taxe
que la source n'avait simplement pas publiée.

Le scénario est construit (aucune ligne collectée ne porte aujourd'hui deux
codes TVA, ce qui rend la faille inerte sur les données du jour), mais il
emprunte la branche réelle : `_is_vat_code` reconnaît `TVAI` comme une TVA,
et les deux codes se rejoignent sur la même clé canonique.

L'exonération algérienne reste, elle, un zéro légitime : elle est portée par
le Code des taxes sur le chiffre d'affaires (art. 8/9/10/11 ; art. 214 LF2025
reconduit LF2026), et elle est signalée par `tva_exoneree`.
"""

import currencies.service as currency_service
import pytest
from services import authentic_tariff_service as svc

_PAYS_TESTES = ("GHA", "DZA", "SOM")


def _position(vat_du_detail):
    """Une position dont le détail porte une TVA au taux `vat_du_detail`.

    Le taux agrégé de la ligne, lui, est bien renseigné : c'est ce qui fait que
    seul le détail peut encore révéler le manque.
    """
    return {
        "hs_code": "010121",
        "description": "Position de contrôle",
        "dd_rate": 10.0,
        "vat_rate": 15.0,
        "taxes_detail": [
            {"tax": "TVA", "rate": 15.0, "observation": ""},
            {"tax": "TVAI", "rate": vat_du_detail, "observation": ""},
        ],
    }


@pytest.fixture
def tarif(monkeypatch):
    def _installer(vat_du_detail):
        position = _position(vat_du_detail)
        autre = {
            "hs_code": "010129",
            "description": "Position qui publie bien une TVA",
            "dd_rate": 10.0,
            "vat_rate": 15.0,
            "taxes_detail": [],
        }
        donnees = {"tariff_lines": [autre, position]}
        monkeypatch.setattr(currency_service, "get_by_country", lambda code: None)
        monkeypatch.setattr(svc, "load_country_tariffs", lambda iso3: donnees)
        monkeypatch.setattr(svc, "get_tariff_line", lambda iso3, code: dict(position))
        monkeypatch.setattr(svc, "get_sub_positions", lambda iso3, hs6: [])
        for iso in _PAYS_TESTES:
            svc._country_has_vat_cache.pop(iso, None)

    yield _installer
    for iso in _PAYS_TESTES:
        svc._country_has_vat_cache.pop(iso, None)


def test_une_tva_nulle_dans_le_detail_ne_sort_pas_en_zero(tarif):
    """Le cas que la garde perdue laissait passer.

    Avant correction, le Ghana servait ici 265,00 — exactement le total du
    contrôle négatif ci-dessous, où la TVA du détail est publiée à 0 %.
    """
    tarif(None)
    resultat = svc.calculate_import_taxes("GHA", "010121", 1_000.0, language="fr")

    assert resultat["error_detail"]["code"] == "CALCULATION_UNAVAILABLE"
    assert "TVA" in resultat["error_detail"]["missing_or_non_ad_valorem_taxes"]
    assert "taxes_summary" not in resultat


def test_le_zero_publie_reste_servi(tarif):
    """Contrôle négatif : un 0 % venant de la source n'est pas un manque."""
    tarif(0.0)
    resultat = svc.calculate_import_taxes("GHA", "010121", 1_000.0, language="fr")

    assert "error_detail" not in resultat
    assert resultat["taxes_summary"]["npf"]["total_taxes_et_droits"] == 265.0
    assert resultat["tva_exoneree"] is False


def test_l_exoneration_algerienne_reste_un_zero_legitime(tarif):
    """L'Algérie garde son 0 % : il est porté par un texte, et il est signalé."""
    tarif(None)
    resultat = svc.calculate_import_taxes("DZA", "010121", 1_000.0, language="fr")

    assert "error_detail" not in resultat
    assert resultat["tva_exoneree"] is True


def test_le_sens_de_l_absence_est_qualifie():
    """Les trois lectures d'une TVA manquante sont nommées, jamais confondues."""
    avec_tva = {"tariff_lines": [{"hs_code": "010129", "dd_rate": 10.0, "vat_rate": 15.0}]}
    sans_tva = {"tariff_lines": [{"hs_code": "010121", "dd_rate": 10.0, "vat_rate": None}]}

    for iso in _PAYS_TESTES:
        svc._country_has_vat_cache.pop(iso, None)
    try:
        assert svc._sens_de_la_tva_absente("DZA", avec_tva) == "EXONEREE"
        assert svc._sens_de_la_tva_absente("SOM", sans_tva) == "HORS_TARIF"
        assert svc._sens_de_la_tva_absente("GHA", avec_tva) == "INCONNUE"
    finally:
        for iso in _PAYS_TESTES:
            svc._country_has_vat_cache.pop(iso, None)


def test_la_table_d_exoneration_n_est_pas_un_fourre_tout():
    """Chaque entrée exige une source citée : la table reste courte et explicite."""
    assert svc.EXONERATION_TVA_ETABLIE == {"DZA"}
