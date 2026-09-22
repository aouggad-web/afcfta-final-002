"""Tests du versement UNIDO DZA (ISIC 4 chiffres, 2005-2017).

Ces tests portent sur les DONNÉES, pas sur le chargeur : ils relisent le CSV
généré par ``scripts/fetch_unido_indstat.py`` tel que le servira
``etl/isic4_idsb_data.py``, pour garantir que l'Algérie quitte le « payload
estimé » au profit de données réelles sourcées ONS via UNIDO, et que les
classes visées par l'écran (ciment, céramique, TV, machinisme agricole) sont
présentes là où UNIDO en publie.

Le versement socle (2018+) reste intact : les tests qui le mockent
(``test_isic4_idsb_data``) ne dépendent pas de ces lignes.
"""

import csv
import gzip
import os

from etl import isic4_idsb_data

#: chemin du versement, tel qu'interprété depuis le répertoire backend/
DZA_FILE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", isic4_idsb_data._DZA_FILE)
)


def _read_dza_rows():
    with gzip.open(DZA_FILE, mode="rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _by_class(rows):
    out = {}
    for r in rows:
        out.setdefault(r["isic_code"], []).append(r)
    return out


def test_dza_is_served_by_the_loader():
    isic4_idsb_data._load_records.cache_clear()
    isic4_idsb_data.list_covered_countries.cache_clear()
    try:
        assert isic4_idsb_data.is_country_covered("DZA") is True
        # La route /isic4/DZA sert désormais le payload RÉEL, pas l'estimé.
        summary = isic4_idsb_data.get_country_isic4_summary("DZA")
        assert summary is not None
        assert summary["country_iso3"] == "DZA"
    finally:
        isic4_idsb_data._load_records.cache_clear()
        isic4_idsb_data.list_covered_countries.cache_clear()


def test_rows_follow_the_shared_schema():
    rows = _read_dza_rows()
    assert rows, "le versement DZA ne doit pas être vide"
    assert {r["schema_version"] for r in rows} == {"unido_manufacturing_v1"}
    assert {r["country_iso3"] for r in rows} == {"DZA"}
    assert {r["country_un_m49"] for r in rows} == {"012"}
    assert {r["isic_level"] for r in rows} == {"4"}
    # Deux natures : relevés officiels (INDSTAT) et estimations dérivées (IDSB)
    assert {r["data_nature"] for r in rows} == {"OFFICIAL_STATISTICS", "UNIDO_DERIVED_ESTIMATE"}
    # Une ligne par (dataset, classe, année, indicateur) : pas de doublon
    ids = [r["record_id"] for r in rows]
    assert len(ids) == len(set(ids)), "record_id en doublon"
    # Chaque libellé ISIC est renseigné : une classe sans description ne se
    # lit pas à l'écran et ne se vérifie pas.
    for r in rows:
        assert r["isic_description_en"], f"description absente pour {r['isic_code']}"


def test_indstat_money_rows_carry_both_currencies():
    """L'Algérie publie en DZD ET en USD : les deux colonnes doivent être servies."""
    rows = _read_dza_rows()
    va = [r for r in rows if r["dataset_code"] == "INDSTAT_R4" and r["indicator_code"] == "20"]
    assert va, "INDSTAT Value added absent"
    with_local = [r for r in va if r["value_local_currency"]]
    assert with_local, "la valeur en devise nationale doit être conservée"
    assert {r["currency"] for r in va} == {"USD"}
    assert {r["unit"] for r in va} == {"current_USD"}


def test_counts_are_counts_not_money():
    """UNIDO ne rapporte pas d'effectifs par classe pour l'Algérie (les
    comptages ne sont publiés qu'aux niveaux supérieurs) : s'il en existe,
    ils doivent être servis en comptage, jamais en montant."""
    rows = _read_dza_rows()
    counts = [r for r in rows if r["indicator_type"] == "N"]
    assert {r["unit"] for r in counts} <= {"count"}
    assert {r["currency"] for r in counts} <= {""}


def test_target_classes_are_served():
    """Les produits visés par l'écran ont leurs classes, là où UNIDO en publie."""
    rows = _read_dza_rows()
    served = set(_by_class(rows))
    for isic in ("2394", "2395", "2640", "2821"):
        assert isic in served, f"classe {isic} absente du versement"


def test_exchange_rate_stays_in_a_plausible_range():
    """Contrôle d'intégrité croisé : le taux DZD/USD implicite de chaque
    (année, classe) doit rester plausible (60 à 130 DZD/USD entre 2011 et
    2015). Un taux sortant de la fourchette signale une colonne mal lue."""
    rows = _read_dza_rows()
    checked = 0
    for r in rows:
        if r["dataset_code"] != "INDSTAT_R4" or r["indicator_type"] != "M":
            continue
        if not r["value_local_currency"] or not r["value"]:
            continue
        rate = float(r["value_local_currency"]) / float(r["value"])
        assert 60 <= rate <= 130, f"taux DZD/USD suspect {r['year']} {r['isic_code']}: {rate:.1f}"
        checked += 1
    assert checked > 0, "aucun contrôle de taux effectué — colonnes locales vides ?"


def test_provenance_names_the_national_supplier():
    """Le versement doit dire QUI a publié : ONS d'Alger, pas UNIDO seul."""
    rows = _read_dza_rows()
    official = [r for r in rows if r["data_nature"] == "OFFICIAL_STATISTICS"]
    assert official, "l'INDSTAT DZA doit être servi en OFFICIAL_STATISTICS"
    with_note = [r for r in official if "Office national des statistiques" in r["source_note"]]
    assert with_note, "la provenance nationale (ONS) doit être portée par les lignes"


def test_years_match_what_unido_publishes():
    """Fenêtre d'UNIDO pour l'Algérie : INDSTAT 2011-2015 ; l'IDSB commence
    plus tôt (2005). Tout ce qui est dans le fichier doit être dans ces bornes."""
    rows = _read_dza_rows()
    years = {int(r["year"]) for r in rows}
    assert 2005 <= min(years) and max(years) <= 2017
    indstat_years = {int(r["year"]) for r in rows if r["dataset_code"] == "INDSTAT_R4"}
    assert indstat_years <= set(range(2011, 2016))