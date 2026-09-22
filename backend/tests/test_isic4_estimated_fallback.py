"""Les 54 pays doivent être servis, et l'estimation doit se dire estimation.

Le jeu UNIDO au niveau de la classe ISIC 4 chiffres ne couvre que 20 pays
africains. Pour les 34 autres, la route renvoyait un 404 et l'écran restait
vide alors qu'une structure ISIC 2 chiffres réelle existait. Le repli comble ce
vide — mais un repli qui se ferait passer pour une mesure serait pire que le
vide qu'il comble, d'où les vérifications de nature ci-dessous.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BACKEND = REPO_ROOT / "backend"


@pytest.fixture(scope="module")
def production_routes():
    # Import direct : le paquet routes charge toute l'application au passage.
    for path in (str(BACKEND), str(REPO_ROOT)):
        if path not in sys.path:
            sys.path.insert(0, path)
    spec = importlib.util.spec_from_file_location(
        "production_routes_under_test", BACKEND / "routes" / "production.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def countries():
    sys.path.insert(0, str(BACKEND))
    from etl.unido_data import UNIDO_INDUSTRY_DATA

    return sorted(UNIDO_INDUSTRY_DATA)


def test_tous_les_pays_sont_servis(production_routes, countries):
    """Aucun pays du référentiel ne doit retomber sur un 404.

    L'assertion de cardinalité vient d'abord : sans elle, ce test dériverait sa
    population du référentiel lui-même et resterait vert si celui-ci perdait des
    pays — il vérifierait alors « tous les pays présents sont servis », ce qui
    n'est pas la couverture annoncée.
    """
    assert len(countries) == 54, (
        f"le référentiel ne contient plus 54 pays mais {len(countries)} : "
        "la couverture annoncée n'est plus vérifiable"
    )
    echecs = []
    for iso in countries:
        try:
            production_routes.get_isic4_country_data(iso)
        except Exception as exc:  # noqa: BLE001 — on veut le nom du pays en échec
            echecs.append(f"{iso}: {type(exc).__name__}")
    assert not echecs, f"pays sans réponse : {echecs}"


def test_la_nature_de_la_donnee_est_toujours_declaree(production_routes, countries):
    natures = {production_routes.get_isic4_country_data(iso)["data_basis"] for iso in countries}
    assert natures == {"UNIDO_MEASURED", "ESTIMATED_FROM_ISIC2"}


def test_un_pays_mesure_reste_mesure(production_routes):
    """Le repli ne doit pas s'appliquer à un pays réellement couvert."""
    payload = production_routes.get_isic4_country_data("KEN")
    assert payload["data_basis"] == "UNIDO_MEASURED"
    assert payload["total_sectors"] > 100


def test_le_libelle_de_classe_est_servi(production_routes):
    """La route renvoyait `description` quand le composant lit `isic_description`.

    La colonne « Libellé » était donc vide à l'écran pour les 20 pays couverts.
    """
    for iso in ("KEN", "DZA"):
        payload = production_routes.get_isic4_country_data(iso)
        premier = payload["sectors"][0]
        assert premier["isic_description"], f"{iso}: libellé de classe vide"


def test_une_estimation_se_declare_comme_telle(production_routes):
    """Exemple choisi : BEN, absent du socle 2018+ comme du versement DZA
    2005-2017 — le pays reste au repli estimé. (DZA, qui portait cet exemple
    depuis que son détail ONS via UNIDO a été versé, est désormais MESURÉ.)"""
    payload = production_routes.get_isic4_country_data("BEN")
    assert payload["data_basis"] == "ESTIMATED_FROM_ISIC2"
    assert payload["data_quality"]["is_fully_estimated"] is True
    assert payload["data_quality"]["official_indicators"] == 0
    assert payload["methodology"] and payload["coverage"]
    for sector in payload["sectors"]:
        for indicator in sector["indicators"].values():
            assert indicator["data_nature"] == "STRUCTURAL_ESTIMATE_FROM_ISIC2"


def test_une_valeur_absente_n_est_jamais_servie_comme_zero(production_routes, countries):
    """`value_mln_usd` manque pour une partie des divisions.

    Le code le remplaçait par 0, ce qui produisait une valeur ajoutée nulle là
    où il n'y a pas de donnée — exactement le no_missing_as_zero que le registre
    des sources interdit.
    """
    for iso in countries:
        payload = production_routes.get_isic4_country_data(iso)
        if payload["data_basis"] != "ESTIMATED_FROM_ISIC2":
            continue
        for sector in payload["sectors"]:
            valeur = sector["indicators"].get("value_added_usd")
            assert valeur is None or valeur["value"] != 0, (
                f"{iso}/{sector['isic4']}: valeur ajoutée à 0 — absence servie comme zéro"
            )


def test_un_pays_estime_n_a_pas_de_serie_temporelle(production_routes):
    """L'absence de série doit être une absence, pas une erreur. Exemple : BEN
    (repli estimé) — DZA est désormais mesuré et porte des séries réelles."""
    reponse = production_routes.get_all_isic4_timeseries_data("BEN")
    assert reponse["data_basis"] == "ESTIMATED_FROM_ISIC2"
    assert reponse["classes"] == {}
    assert reponse["note"]


def test_le_detail_groupe_couvre_toutes_les_classes_d_un_pays_mesure(production_routes):
    """L'export PDF a besoin du détail complet en une requête."""
    payload = production_routes.get_isic4_country_data("KEN")
    groupe = production_routes.get_all_isic4_timeseries_data("KEN")
    assert groupe["total_classes"] == payload["total_sectors"]
    une = groupe["classes"][payload["sectors"][0]["isic4"]]
    assert une["series"], "aucune série pour la première classe"


def test_un_iso_inconnu_ne_passe_pas_pour_un_pays_estime(production_routes):
    """Deux routes, une même absence, deux comportements — corrigé.

    /isic4/{pays} renvoyait 404 sur un ISO inconnu, tandis que la route groupée
    le qualifiait ESTIMATED_FROM_ISIC2 et renvoyait 200 avec un résultat vide.
    Un code invalide n'est pas un pays dont les données seraient estimées.
    """
    from fastapi import HTTPException

    for route in (
        production_routes.get_all_isic4_timeseries_data,
        production_routes.get_isic4_country_data,
    ):
        with pytest.raises(HTTPException) as exc:
            route("ZZZ")
        assert exc.value.status_code == 404
