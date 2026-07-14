"""
Lot C: Répercussion vraquier dans Opportunités — tests du coût rendu (landed cost).

Valide que le rapport Opportunités :
  1. Utilise l'affrètement vraquier (USD/t × tonnage) pour un vrac au-dessus du seuil
  2. N'affiche JAMAIS simultanément « conteneurs nécessaires » et « affrètement vrac »
  3. Bascule vers le conteneur sous le seuil (non-régression)
  4. Laisse la marchandise générale strictement inchangée
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services.report_engine import get_opportunity_report


def test_bulk_above_threshold_uses_charter_not_containers():
    # Maïs (HS 100590) — gros lot bien au-dessus du seuil vrac
    rep = get_opportunity_report(
        hs_code="100590",
        origin_iso3="ZAF",
        destination_iso3="DZA",
        goods_value_usd=50_000_000,
    )
    lc = rep["composite_indicators"]["landed_cost"]
    assert lc["available"] is True
    bd = lc["breakdown"]

    # Le fret retenu est l'affrètement vraquier
    assert bd["freight_mode"] == "sea_bulk"
    assert bd.get("vessel_class") in {"handysize", "supramax", "panamax", "capesize"}

    # JAMAIS de conteneurs quand on affrète en vrac (critère d'acceptation Lot C)
    assert "containers_needed" not in bd
    assert "freight_per_container_usd" not in bd

    # Le coût rendu = FOB + affrètement total
    assert bd["best_operational_freight_usd"] > 0
    assert lc["value_usd"] == 50_000_000 + bd["best_operational_freight_usd"]

    # L'option opérationnelle la moins chère est bien le vraquier
    cheapest = rep["logistics"]["profile"]["cheapest_operational_option"]
    assert cheapest["mode"] == "sea_bulk"

    # La note explique l'affrètement, pas le découpage conteneur
    assert "affrètement" in lc["note"].lower()


def test_bulk_below_threshold_falls_back_to_containers():
    # Petit lot de maïs sous le seuil → conteneur (bascule)
    rep = get_opportunity_report(
        hs_code="100590",
        origin_iso3="ZAF",
        destination_iso3="DZA",
        goods_value_usd=50_000,
    )
    lc = rep["composite_indicators"]["landed_cost"]
    bd = lc["breakdown"]

    # Mode conteneur : pas de freight_mode sea_bulk, containers_needed présent
    assert bd.get("freight_mode") != "sea_bulk"
    assert "containers_needed" in bd
    assert bd["containers_needed"] >= 1

    cheapest = rep["logistics"]["profile"]["cheapest_operational_option"]
    assert cheapest["mode"] != "sea_bulk"


def test_general_cargo_unchanged():
    # Café (marchandise générale) — comportement conteneur inchangé
    rep = get_opportunity_report(
        hs_code="0901",
        origin_iso3="ETH",
        destination_iso3="DZA",
        goods_value_usd=500_000,
    )
    lc = rep["composite_indicators"]["landed_cost"]
    bd = lc["breakdown"]

    assert bd.get("freight_mode") != "sea_bulk"
    assert "containers_needed" in bd


def test_no_report_shows_both_containers_and_charter():
    # Garde-fou explicite du critère d'acceptation : jamais les deux ensemble
    for goods_value in (50_000, 5_000_000, 50_000_000):
        rep = get_opportunity_report(
            hs_code="100199",  # Blé
            origin_iso3="ZAF",
            destination_iso3="DZA",
            goods_value_usd=goods_value,
        )
        bd = rep["composite_indicators"]["landed_cost"]["breakdown"]
        is_charter = bd.get("freight_mode") == "sea_bulk"
        has_containers = "containers_needed" in bd
        assert not (
            is_charter and has_containers
        ), f"Rapport affiche affrètement ET conteneurs pour goods_value={goods_value}"


def test_bulk_route_enumerates_all_ports_not_just_default():
    # L'affrètement vraquier doit explorer TOUTES les paires de ports du pays
    # (pas seulement le port par défaut) et retenir la moins chère. On vérifie
    # que la route retenue n'est pas contrainte au port par défaut du pays et
    # que le coût est le minimum atteignable.
    from services.multimodal_freight_service import (
        COUNTRY_DEFAULT_PORT,
        COUNTRY_PORTS,
        _bulk_sea_options,
    )
    from services.shipment_estimator import classify_bulk_commodity

    maize = classify_bulk_commodity("100590")
    opts = _bulk_sea_options("ZAF", "DZA", 273_000_000, maize)
    assert len(opts) == 1
    opt = opts[0]
    assert opt["available"] is True

    # Recalcule le coût minimal sur toutes les paires de ports pour comparaison.
    from services.homogeneous_cargo_service import get_bulk_freight_option

    best = None
    for o_port in COUNTRY_PORTS.get("ZAF", []):
        for d_port in COUNTRY_PORTS.get("DZA", []):
            if o_port == d_port:
                continue
            res = get_bulk_freight_option(o_port, d_port, 273_000_000, maize)
            if res and res.get("total_cost_usd") is not None:
                if best is None or res["total_cost_usd"] < best["total_cost_usd"]:
                    best = res

    assert best is not None
    # La route retenue par _bulk_sea_options est bien la moins chère globale.
    assert opt["total_cost_usd"] == best["total_cost_usd"]
    assert opt["origin_locode"] == best["origin_locode"]
    assert opt["destination_locode"] == best["destination_locode"]
