"""
Ventilation exportations domestiques / réexportations, dérivée d'UN Comtrade.

CE QUE CES TESTS VERROUILLENT
------------------------------
La couche des offices nationaux existait sur une affirmation : « aucune source
internationale ne publie cette ventilation ». Elle est fausse — Comtrade la
publie, sans clé. Mais la remplacer naïvement serait pire que de s'en passer :
neuf pays africains publient les trois flux SANS qu'ils se recomposent.

La règle d'admission est donc la RÉCONCILIATION, pas la présence. Ces tests la
tiennent, et tiennent aussi ce qu'elle ne remplace pas.
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import pytest  # noqa: E402
from etl.comtrade_export_split import (  # noqa: E402
    COMTRADE_EXPORT_SPLIT,
    COMTRADE_SPLIT_REJECTED,
)


def test_every_admitted_country_reconciles():
    # LA règle. Une décomposition qui ne retombe pas sur son total n'est pas
    # une décomposition — c'est deux mesures de couverture différente servies
    # côte à côte.
    for row in COMTRADE_EXPORT_SPLIT:
        x = row["total_exports_usd"]
        somme = row["domestic_exports_usd"] + row["reexports_usd"]
        tolerance = max(abs(x) * 1e-6, 1.0)
        assert abs(x - somme) <= tolerance, (row["country_iso3"], x, somme)


def test_rejected_countries_are_not_served_anyway():
    # Contrôle miroir : l'existence d'une liste de rejets ne prouve rien si
    # les rejetés figurent quand même dans les données servies.
    admitted = {r["country_iso3"] for r in COMTRADE_EXPORT_SPLIT}
    assert admitted.isdisjoint(COMTRADE_SPLIT_REJECTED)
    # Et la liste des rejets n'est pas vide : si elle l'était, le test
    # ci-dessus passerait sans rien vérifier.
    assert COMTRADE_SPLIT_REJECTED


def test_shares_are_derived_from_the_published_values_not_asserted():
    for row in COMTRADE_EXPORT_SPLIT:
        attendu = round(
            row["reexports_usd"] / row["total_exports_usd"] * 100.0, 1
        )
        assert row["reexport_share_pct"] == attendu, row["country_iso3"]


def test_no_flow_is_completed_when_the_source_is_silent():
    # On ne déduit jamais DX = X au motif que les réexportations seraient
    # « probablement faibles ». Chaque pays admis porte ses trois flux, tous
    # strictement positifs — un zéro signalerait une déduction.
    for row in COMTRADE_EXPORT_SPLIT:
        assert row["total_exports_usd"] > 0
        assert row["domestic_exports_usd"] > 0
        assert row["reexports_usd"] > 0


def test_one_year_per_country_never_a_mix():
    # Mélanger deux années donnerait une part de réexportation qui ne
    # correspond à aucun exercice réel.
    for row in COMTRADE_EXPORT_SPLIT:
        assert isinstance(row["year"], int)
        assert 2018 <= row["year"] <= 2024


def test_kenya_matches_the_values_published_by_the_un():
    """Repère vérifié À LA MAIN contre l'endpoint public le 2026-09-22.

    Si une régénération fait bouger l'année, ce test tombe — et c'est voulu.
    Un module dérivé d'une source vivante doit forcer une re-vérification
    humaine quand son contenu change, plutôt que d'absorber le changement en
    silence. Recontrôler alors les trois flux à la main et recaler ici.
    """
    ken = next(
        (r for r in COMTRADE_EXPORT_SPLIT if r["country_iso3"] == "KEN"), None
    )
    assert ken is not None, "le Kenya doit être couvert : sa ventilation réconcilie"
    assert ken["year"] == 2024
    assert ken["total_exports_usd"] == pytest.approx(8_255_797_029.967, rel=1e-9)
    assert ken["domestic_exports_usd"] == pytest.approx(6_920_553_939.227, rel=1e-9)
    assert ken["reexports_usd"] == pytest.approx(1_335_243_090.739, rel=1e-9)


def test_each_country_carries_its_own_year_and_the_spread_is_visible():
    """Les années diffèrent d'un pays à l'autre, et ça doit se voir.

    La règle « année la plus récente qui RÉCONCILIE » fait cohabiter 2018 et
    2024 dans le même module : un pays dont la dernière année est incohérente
    est servi sur une année antérieure plutôt qu'écarté. C'est le bon
    arbitrage, mais il serait trompeur s'il était tu — comparer une part de
    réexportation de 2018 à une de 2024 n'a pas de sens sans le savoir.
    """
    annees = {r["country_iso3"]: r["year"] for r in COMTRADE_EXPORT_SPLIT}
    assert len(set(annees.values())) > 1, (
        "si toutes les années étaient identiques, ce test ne garderait rien — "
        "vérifier que la règle de repli fonctionne encore"
    )
    # Chaque ligne porte son année : aucun appelant ne peut l'ignorer.
    for row in COMTRADE_EXPORT_SPLIT:
        assert "year" in row


def test_this_layer_does_not_replace_the_national_offices():
    """Maurice est la démonstration que les deux couches sont complémentaires.

    Son office publie la ventilation jusqu'au produit et au marché. Comtrade,
    lui, ne réconcilie pas pour elle (43,9 % d'écart) : elle est donc écartée
    ici et couverte là-bas. Retirer la collecte nationale sous prétexte que
    « l'ONU publie la ventilation » perdrait Maurice ET tout le détail par
    produit que Comtrade ne porte pas à ce niveau.
    """
    from services import national_official_stats as nos

    admitted = {r["country_iso3"] for r in COMTRADE_EXPORT_SPLIT}
    assert "MUS" not in admitted
    assert "MUS" in nos.list_covered_countries()
