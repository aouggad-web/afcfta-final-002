"""
Tests for the UNIDO-driven discovery service.

Exercises the capacity index derived from real UNIDO value-added (local data,
no network): the right divisions surface products, the evidence is grounded, and
every country with manufacturing capacity yields candidates.
"""

from production_data import get_manufacturing_key_products
from services import unido_discovery_service as disco


def test_algeria_capacity_index_covers_top_sectors():
    idx = disco.capacity_hs4_index("DZA")
    assert idx, "Algérie devrait avoir un index de capacité non vide"
    isic_present = {v["isic_code"] for v in idx.values()}
    # Raffinage (19), alimentaire (10), minéraux non métalliques (23),
    # métallurgie (24), chimie (20) sont les 5 divisions phares algériennes.
    for code in ("19", "10", "23", "24", "20"):
        assert code in isic_present, f"Division {code} attendue dans l'index DZA"


def test_capacity_for_hs_maps_product_to_division():
    # Sucre raffiné (1701) -> alimentaire (10) ; évidence = valeur ajoutée UNIDO.
    sugar = disco.capacity_for_hs("DZA", "170199")
    assert sugar["available"] is True
    assert sugar["isic_code"] == "10"
    assert sugar["value_added_usd"] > 0
    assert sugar["product_label"]
    # Ciment/clinker (2523) -> minéraux non métalliques (23).
    cement = disco.capacity_for_hs("DZA", "252310")
    assert cement["available"] is True and cement["isic_code"] == "23"


def test_capacity_absent_for_uncovered_sector():
    # L'électronique (TV, 8528) n'est PAS une division phare algérienne dans les
    # top-secteurs UNIDO : la découverte auto ne doit rien affirmer (Condor reste
    # porté par la base curée).
    assert disco.capacity_for_hs("DZA", "852872")["available"] is False


def test_capacity_absent_for_non_manufacturable():
    # Minerai de fer brut (2601) : extractif, aucune capacité manufacturière.
    assert disco.capacity_for_hs("DZA", "260111")["available"] is False


def test_discover_returns_ranked_candidates():
    d = disco.discover("MAR")
    assert d["candidate_count"] > 0
    vals = [p["value_added_usd"] for p in d["candidate_products"]]
    assert vals == sorted(vals, reverse=True)  # triés par valeur ajoutée décroissante
    # Produits phares curés remontés depuis le module production.
    assert d["key_products"] == get_manufacturing_key_products("MAR")


def test_all_manufacturing_countries_yield_candidates():
    """Le moteur se déploie sur tous les pays ayant une capacité UNIDO."""
    from production_data import get_manufacturing_production

    countries = {r["country_iso3"] for r in get_manufacturing_production()}
    empty = [c for c in countries if not disco.capacity_hs4_index(c)]
    # Tolérance nulle attendue : chaque pays a au moins un secteur > plancher.
    assert not empty, f"Pays sans candidat malgré une capacité UNIDO: {sorted(empty)}"


def test_dairy_hs4_excluded_without_raw_milk_input():
    """
    Bug réel constaté : le Burundi (VA « alimentaire » 191,6 M$, en réalité
    café/thé) a hérité à tort d'une capacité laitière (0402) sur le seul
    critère de la division ISIC 10, faisant émerger un flux fictif de lait en
    poudre à 246,6 M$ vers l'Algérie — supérieur à TOUT le secteur alimentaire
    burundais. Sa collecte de lait cru réelle (~40 500 t/an FAOSTAT 2024) est
    très en-dessous du plancher de corroboration : les SH4 laitiers doivent
    être exclus de son index de capacité.
    """
    idx = disco.capacity_hs4_index("BDI")
    assert "0402" not in idx, "Lait en poudre : capacité laitière non corroborée par l'intrant"
    assert "0406" not in idx, "Fromages : capacité laitière non corroborée par l'intrant"
    # Les autres candidats de la division alimentaire (café/thé, boissons…)
    # restent légitimement présents.
    assert idx, "Le Burundi garde des candidats hors filière laitière"


def test_dairy_hs4_present_with_sufficient_raw_milk_input():
    # Le Nigeria a une collecte de lait cru réelle (~528 000 t/an FAOSTAT
    # 2024), largement au-dessus du plancher de corroboration : les SH4
    # laitiers restent des candidats légitimes.
    idx = disco.capacity_hs4_index("NGA")
    assert "0402" in idx
