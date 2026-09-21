"""
Tests du registre des statistiques officielles nationales.

La couche existait mais tenait dans un dictionnaire Python couvrant UN pays.
Elle est désormais un registre piloté par la donnée
(``data/national_stats/<ISO3>.json``), pour qu'ajouter un pays ne demande pas
de toucher au code.

Ce que ces tests verrouillent :
  • la migration de Maurice ne change ni les valeurs servies ni les lignes
    d'ancrage — le texte injecté dans le prompt est identique ;
  • la règle qui ne se négocie pas : un bloc sans éditeur, sans URL, sans
    année ou sans devise est REFUSÉ, pas servi à moitié ;
  • le montant se lit dans un champ générique, faute de quoi chaque pays
    ajouté devrait inventer sa propre clé de devise.
"""

import json
import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import pytest  # noqa: E402
from services import national_official_stats as nos  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_cache():
    nos.load_registry(force=True)
    yield
    nos.load_registry(force=True)


def test_registry_loads_from_disk():
    assert "MUS" in nos.list_covered_countries()
    assert nos.REGISTRY_DIR.is_dir()


def test_lookup_is_case_insensitive_and_absent_countries_stay_absent():
    assert nos.get_official_stats("mus") is not None
    assert nos.get_official_stats("MUS") is not None
    # Aucune statistique inventée pour les pays non couverts.
    assert nos.get_official_stats("KEN") is None
    assert nos.grounding_lines("KEN") == []


def test_amounts_are_generic_and_carry_their_unit():
    stats = nos.get_official_stats("MUS")
    top = stats["top_domestic_export_product"]
    # Générique : pas de clé portant la devise, sinon chaque pays ajouté
    # devrait inventer la sienne (value_kes_mn, value_ngn_mn…).
    assert "value" in top
    assert not any(k.startswith("value_") for k in top)
    assert stats["source"]["currency"] == "MUR"
    assert stats["source"]["unit_short"] == "MUR Mn"


def test_domestic_and_reexport_flows_stay_separate():
    # La distinction qui justifie toute cette couche : une marchandise
    # réexportée n'acquiert pas l'origine locale au sens ZLECAf.
    stats = nos.get_official_stats("MUS")
    assert stats["top_domestic_export_markets"][0]["iso3"] == "ZAF"
    assert stats["top_reexport_markets"][0]["iso3"] == "VNM"
    assert stats["top_domestic_export_markets"] != stats["top_reexport_markets"]


def test_grounding_text_is_unchanged_by_the_migration():
    text = "\n".join(nos.grounding_lines("MUS"))
    assert "OFFICIAL NATIONAL STATISTICS FOR Maurice" in text
    assert "LOCAL CURRENCY, not USD" in text
    assert "11,500 MUR Mn" in text
    assert "does NOT acquire local AfCFTA origin" in text
    assert "RE-EXPORTS are tracked SEPARATELY" in text


@pytest.mark.parametrize("missing", ["publisher", "publication", "url", "data_year", "currency"])
def test_incomplete_entry_is_refused_not_served_half_way(tmp_path, monkeypatch, missing):
    complete = json.loads((nos.REGISTRY_DIR / "MUS.json").read_text(encoding="utf-8"))
    broken = json.loads(json.dumps(complete))
    broken["country_iso3"] = "XXA"
    broken["source"].pop(missing)

    (tmp_path / "XXA.json").write_text(json.dumps(broken), encoding="utf-8")
    monkeypatch.setattr(nos, "REGISTRY_DIR", tmp_path)
    registry = nos.load_registry(force=True)
    assert "XXA" not in registry, f"entrée sans {missing} acceptée"


def test_complete_entry_in_a_temporary_registry_is_accepted(tmp_path, monkeypatch):
    # Contrôle miroir du test précédent : le refus doit venir du champ absent,
    # pas du mécanisme lui-même.
    complete = json.loads((nos.REGISTRY_DIR / "MUS.json").read_text(encoding="utf-8"))
    complete["country_iso3"] = "XXB"
    (tmp_path / "XXB.json").write_text(json.dumps(complete), encoding="utf-8")
    monkeypatch.setattr(nos, "REGISTRY_DIR", tmp_path)
    assert "XXB" in nos.load_registry(force=True)


def test_unreadable_file_is_skipped_without_bringing_the_registry_down(tmp_path, monkeypatch):
    (tmp_path / "XXC.json").write_text("{ pas du JSON", encoding="utf-8")
    complete = json.loads((nos.REGISTRY_DIR / "MUS.json").read_text(encoding="utf-8"))
    (tmp_path / "MUS.json").write_text(json.dumps(complete), encoding="utf-8")
    monkeypatch.setattr(nos, "REGISTRY_DIR", tmp_path)
    registry = nos.load_registry(force=True)
    assert "XXC" not in registry
    assert "MUS" in registry


def test_every_registered_country_has_a_source_register_document():
    # Une donnée sans registre documentaire n'est pas vérifiable par un
    # lecteur : la discipline des registres juridiques du dépôt est étendue
    # ici, et tenue par un test plutôt que par l'usage.
    docs = nos.REGISTRY_DIR.parent.parent / "docs" / "data-sources"
    for iso3 in nos.list_covered_countries():
        assert (docs / f"{iso3}_STATS_REGISTER.md").is_file(), iso3


# ---------------------------------------------------------------------------
# Togo — le cas où la ventilation N'EXISTE PAS, et où le dire est la donnée
# ---------------------------------------------------------------------------
# Maurice publie la séparation domestique/réexportation jusqu'au produit et au
# marché. Le Togo, dont la zone franche est très active, ne la publie qu'au
# niveau du régime douanier (Tableau 83) — jamais par produit ni par client —
# et ce tableau ne se réconcilie pas avec le total d'exportations publié : la
# somme des régimes d'exportation et de réexportation donne 311 490,1 millions
# de FCFA au 2025T4 contre 258 434,7 publiés, et aucun sous-ensemble des
# régimes de réexportation ne reproduit le total sur les cinq trimestres.
# Reconstituer un « export domestique togolais » serait donc une agrégation
# maison contredite par la source elle-même.
#
# Ce qui est servi à la place est ce qui est vrai et vérifiable : un
# avertissement daté, sa définition citée, et les régimes de zone franche
# repris tels que publiés.


def test_togo_is_registered_and_carries_no_invented_split():
    stats = nos.get_official_stats("TGO")
    assert stats is not None
    # L'invariant qui ne se négocie pas : puisque la source ne publie pas la
    # ventilation, aucun champ de ventilation ne doit apparaître ici. Les
    # remplir depuis OEC ou Comtrade serait exactement la fabrication que
    # cette couche existe pour empêcher.
    for field in (
        "top_domestic_export_product",
        "domestic_export_products",
        "top_domestic_export_markets",
        "top_reexport_markets",
    ):
        assert field not in stats, field


def test_togo_grounding_warns_that_the_flows_are_not_separable():
    text = "\n".join(nos.grounding_lines("TGO"))
    assert "the two flows are NOT separable for Togo" in text
    assert "258,434.7 FCFA M" in text  # total publié, tel que publié
    assert "2025T4" in text
    assert "no split by product or by market" in text
    # La définition de la source est citée, pas paraphrasée : c'est elle qui
    # établit que le total inclut les réexportations.
    assert "L'exportation regroupe l'exportation simple et la réexportation." in text


def test_togo_free_zone_regimes_are_published_values_not_totals():
    stats = nos.get_official_stats("TGO")
    zones = {z["code"]: z["value"] for z in stats["free_zone_regimes"]}
    # Repris ligne à ligne du Tableau 83, colonne 2025T4.
    assert zones["9300"] == 100527.6  # entrées en zone franche industrielle
    assert zones["1093"] == 84248.9  # exportations en suite de zone franche
    text = "\n".join(nos.grounding_lines("TGO"))
    assert "100,527.6 FCFA M" in text
    assert "do not by themselves establish local origin" in text
    # Aucun total de zone franche n'est servi : la source n'en publie pas.
    assert str(round(sum(zones.values()), 1)) not in text


def test_a_caveat_and_a_published_split_are_mutually_exclusive():
    # Un pays ne peut pas à la fois déclarer la ventilation impossible et
    # servir une ventilation : l'un des deux serait faux.
    for iso3 in nos.list_covered_countries():
        stats = nos.get_official_stats(iso3)
        if "export_flow_caveat" in stats:
            assert "top_reexport_markets" not in stats, iso3


def test_mauritius_grounding_gains_no_line_from_the_togo_fields():
    text = "\n".join(nos.grounding_lines("MUS"))
    assert "NOT separable" not in text
    assert "Free-zone customs regimes" not in text
