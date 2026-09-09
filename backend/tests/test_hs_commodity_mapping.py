"""
Tests de la table HS -> commodité (HS_TO_COMMODITY / _match_commodity).

Vérifie les corrections de granularité apportées à la résolution du besoin
national estimé (niveau 3) : avant ces correctifs, plusieurs codes HS étaient
soit mal étiquetés (ex. 7106 = argent classé comme "Salt"), soit fusionnés à
tort avec un secteur voisin (ex. moteurs électriques HS 8501 classés comme
"Produits électroniques" au lieu de "Équipements électriques"), soit absents
malgré une correspondance UNIDO réelle (ex. carburants raffinés HS 2710
classés comme pétrole brut, voitures particulières HS 8703 non couvertes).
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services import production_capacity_service as pcs  # noqa: E402


def test_electrical_equipment_split_from_electronics():
    # HS 8501 (moteurs électriques) et HS 8517 (téléphones) sont deux secteurs
    # UNIDO distincts (ISIC 27 vs ISIC 26) : ils ne doivent plus partager le
    # même libellé de commodité, sinon leurs besoins estimés seraient identiques.
    motor = pcs._match_commodity("8501")
    phone = pcs._match_commodity("8517")
    assert motor == ("manufacturing", "Équipements électriques", "HS4")
    assert phone == ("manufacturing", "Produits électroniques", "HS4")
    assert motor[1] != phone[1]


def test_refined_petroleum_distinct_from_crude_oil():
    # HS 2710 (huiles de pétrole raffinées) n'est pas du brut : il doit
    # pointer vers la valeur ajoutée UNIDO du raffinage, pas la production
    # minière de pétrole brut (HS 2709).
    refined = pcs._match_commodity("2710")
    crude = pcs._match_commodity("2709")
    assert refined == (
        "manufacturing",
        "Manufacture of coke and refined petroleum products",
        "HS4",
    )
    assert crude == ("mining", "Crude oil", "HS4")


def test_passenger_cars_covered_by_motor_vehicles():
    # HS 8703 (voitures particulières) est le code véhicule le plus demandé ;
    # il manquait alors que les tracteurs/bus/pièces l'étaient déjà.
    assert pcs._match_commodity("8703") == (
        "manufacturing",
        "Manufacture of motor vehicles",
        "HS4",
    )


def test_diamond_jewelry_distinct_from_raw_diamond_mining():
    # HS 7113 (joaillerie) est une activité de transformation (UNIDO), à
    # distinguer de l'extraction brute de diamants (USGS, HS 7102/7103).
    jewelry = pcs._match_commodity("7113")
    raw = pcs._match_commodity("7102")
    assert jewelry == ("manufacturing", "Autres industries (diamants)", "HS4")
    assert raw == ("mining", "Diamonds", "HS4")


def test_silver_no_longer_mislabelled_as_salt():
    # HS 7106 (argent) était auparavant mappé par erreur vers "Salt" (une
    # collision de repli visiblement non intentionnelle). Il doit désormais
    # retomber sur le même repli de chapitre que le reste du chapitre 71,
    # jamais sur un libellé de commodité sans rapport.
    match = pcs._match_commodity("7106")
    assert match is not None
    assert match[1] != "Salt"
    assert match == ("mining", "Gold", "HS2 (chapitre)")


def test_matched_manufacturing_labels_have_real_production_records():
    # Chaque libellé de commodité "manufacturing" nouvellement introduit ou
    # réaffecté doit exister réellement dans production_africaine.json,
    # sinon get_continental_producers retombe silencieusement sur le proxy
    # d'exportation malgré un match apparent.
    for hs in ("8501", "2710", "7113"):
        match = pcs._match_commodity(hs)
        assert match is not None, f"aucun mapping pour {hs}"
        dataset, label, _ = match
        records = pcs._records_for(dataset, label)
        assert records, f"aucun enregistrement pour {hs} -> {label}"


def test_newly_added_agri_commodities_resolve_at_hs6_with_data():
    # Commodités FAOSTAT qui avaient des données mais aucun code HS pointant
    # vers elles (elles retombaient donc sur le proxy d'exportation) : chacune
    # doit désormais matcher au niveau HS6 et avoir des enregistrements réels.
    expected = {
        "070410": "Cauliflowers",
        "070960": "Chillies and peppers",
        "070970": "Spinach",
        "080550": "Lemons and limes",
    }
    for hs, label in expected.items():
        match = pcs._match_commodity(hs)
        assert match == ("agri", label, "HS6"), (hs, match)
        assert pcs._records_for("agri", label), f"aucun enregistrement pour {label}"


def test_titanium_hs4_and_hs6_resolve_to_enriched_series():
    # HS 2614 (minerais de titane) doit atteindre le libellé réellement présent
    # dans production_africaine.json (« Titanium (ilmenite) ») aux niveaux HS4 ET
    # HS6 : l'ancien mapping pointait vers « Ilmenite » (sans enregistrement), la
    # recherche de capacité renvoyait donc un ensemble vide.
    for hs, level in (("2614", "HS4"), ("261400", "HS6")):
        match = pcs._match_commodity(hs)
        assert match == ("mining", "Titanium (ilmenite)", level), (hs, match)
        assert pcs._records_for("mining", "Titanium (ilmenite)"), f"aucun enregistrement pour {hs}"


def test_no_production_commodity_left_without_hs_mapping():
    # Invariant de couverture : toute commodité (agri FAO, mines USGS, secteur
    # UNIDO) présente dans production_africaine.json doit être atteignable par
    # au moins un code HS — sinon sa donnée réelle est inaccessible au module
    # Opportunités et le besoin national retomberait inutilement sur un proxy.
    from production_data import load_production_data

    data = load_production_data()
    mapped = {label for _, _, label in pcs.HS_TO_COMMODITY}
    mapped |= {label for _, (_, label) in pcs.HS_CHAPTER_FALLBACK.items()}

    orphans = []
    for rec in data.get("agri_faostat", []):
        lbl = rec.get("commodity_label")
        if lbl and lbl not in mapped:
            orphans.append(("agri", lbl))
    for rec in data.get("mining_usgs", []):
        lbl = rec.get("commodity_label")
        if lbl and lbl not in mapped:
            orphans.append(("mining", lbl))
    for rec in data.get("manufacturing_unido", []):
        lbl = rec.get("isic_label") or rec.get("sector_detail")
        if lbl and lbl not in mapped:
            orphans.append(("manufacturing", lbl))

    assert not set(
        orphans
    ), f"commodités avec données mais sans mapping HS : {sorted(set(orphans))}"
