"""L'entrée DZA curée d'unido_data doit être celle que publie UNIDO.

L'Algérie portait des valeurs dérivées (mva × part) présentées comme des
montants publiés, sur une structure (raffinage à 28,5 %) que les publications
ONS/UNIDO contredisent : le raffinage pèse 80 % de la VA manufacturière dans
INDSTAT. Ces tests verrouillent l'entrée sur les valeurs réelles collectées
via l'API du portail UNIDO le 2026-09-22, et — le point important — vérifient
la cohérence croisée entre l'entrée curée et le versement ISIC4 committé
(``unido_idsb_indstat_isic4_dza_2005_2017.csv.gz``) : la division 19 doit y
valoir exactement la somme de ses classes 1910+1920.
"""

import csv
import gzip
import os

from etl.unido_data import UNIDO_INDUSTRY_DATA
from scripts.build_production_real import build_manufacturing

DZA = UNIDO_INDUSTRY_DATA["DZA"]

# Valeurs de référence — collectées le 2026-09-22 via l'API stat.unido.org :
# National Accounts (dataset 140) pour les totaux, INDSTAT 2026 (dataset 148)
# pour les divisions, MTD (163) pour le commerce manufacturier, CIP (165)
# pour le rang. Les fichiers bruts sont archivés hors dépôt.
_MVA_2023_MLN = 23017.840702  # MvaCud 2023
_MVA_2024_MLN = 25318.547003  # MvaCud 2024
_MVA_2015_MLN = 13330.846087  # MvaCud 2015 (base National Accounts, plus étroite)


def test_totals_match_unido_national_accounts():
    assert abs(DZA["mva_2024_mln_usd"] - _MVA_2024_MLN) < 0.05  # curée au 1/10 de mln
    assert abs(DZA["mva_2023_mln_usd"] - _MVA_2023_MLN) < 0.05
    # Part du PIB 2024 : 25,318.547 / 266,972.276 = 9.48 %
    assert abs(DZA["mva_gdp_percent"] - 9.48) < 0.01
    # MVA par habitant 2024 courant : 25,318.5 M / 46,814,308 hab.
    assert abs(DZA["mva_per_capita_usd"] - 541) < 1


def test_structure_is_indstat_2015_with_refining_at_its_real_weight():
    """La structure divisée vient d'INDSTAT (ONS, « Comptes Économiques »),
    qui inclut le raffinage : 80,3 % de la VA manufacturière — pas les 28,5 %
    de l'ancienne entrée, dont les montants étaient dérivés d'un total au
    périmètre différent (National Accounts)."""
    by_isic = {s["isic"]: s for s in DZA["top_sectors"]}
    assert set(by_isic) == {"19", "10", "23", "24", "20"}
    assert abs(by_isic["19"]["value_mln_usd"] - 29221.36) < 0.05
    assert abs(by_isic["19"]["share_mva"] - 80.3) < 0.1


def test_division_19_cross_checks_against_the_class_level_versement():
    """Le versement ISIC4 committé donne 1910+1920 (VA 2015) ; leur somme doit
    retomber EXACTEMENT sur la division 19 portée par l'entrée curée."""
    rows = []
    with gzip.open(
        os.path.join(
            os.path.dirname(__file__), "..", "data", "unido",
            "unido_idsb_indstat_isic4_dza_2005_2017.csv.gz",
        ),
        mode="rt", encoding="utf-8", newline="",
    ) as f:
        for r in csv.DictReader(f):
            if (
                r["dataset_code"] == "INDSTAT_R4"
                and r["indicator_code"] == "20"
                and r["year"] == "2015"
                and r["isic_code"] in ("1910", "1920")
            ):
                rows.append(float(r["value"]))
    assert len(rows) == 2, "les classes 1910/1920 doivent être dans le versement"
    division_19 = sum(rows) / 1e6
    curate = {s["isic"]: s for s in DZA["top_sectors"]}["19"]["value_mln_usd"]
    assert abs(division_19 - curate) < 0.05, (
        f"division 19 curée ({curate}) ≠ versement ISIC4 ({division_19})"
    )


def test_top_sectors_share_sums_to_the_indstat_base():
    """share_mva est calculée sur la SOMME des divisions INDSTAT (36,4 Md$),
    pas sur le MVA National Accounts (13,3 Md$) — deux périmètres, un seul
    dénominateur valide par base."""
    somme = sum(s["value_mln_usd"] for s in DZA["top_sectors"])
    part = sum(s["share_mva"] for s in DZA["top_sectors"])
    # Les cinq premières divisions portent la quasi-totalité du manufacturier
    # hors hydrocarbures annexes ; leur somme (34,5 Md$) est un sous-ensemble
    # de la base INDSTAT (36,4 Md$), qui domine la base réharmonisée (13,3 Md$)
    # par construction — deux périmètres, ne jamais les additionner.
    assert 34_000 < somme < 35_000  # mln USD : somme des CINQ divisions
    assert 90 < part < 100  # ~94,8 % : le reste est dispersé sur 17 divisions


def test_manufacturing_records_carry_the_published_2015_values():
    records = [r for r in build_manufacturing() if r["country_iso3"] == "DZA"]
    assert len(records) == 5
    by_isic = {r["isic_code"]: r for r in records}
    # INDSTAT publie 29,221,364,138 USD pour la division 19 en 2015 —
    # le module curé l'arrondit au cent-milliard de dollar le plus proche.
    assert by_isic["19"]["value"] == 29_221_360_000
    assert by_isic["19"]["year"] == 2015
    # Des valeurs publiées : PAS des estimations dérivées.
    assert all(r["is_estimation"] is False for r in records)
    # Les libellés ISIC restent mappés vers le SH (invariant du pont).
    assert {r["isic_code"] for r in records} == {"19", "10", "23", "24", "20"}


def test_cip_and_trade_metadata_match_the_published_editions():
    assert DZA["cip_index_rank"] == 93  # CIP 2024
    assert abs(DZA["mht_share_mva"] - 2.69) < 0.01  # MHVAsh 2024 / ODD 9.b.1 2015
    assert abs(DZA["exports_manuf_mln_usd"] - 17544.63) < 0.01  # MTD X_Manuf 2025
    assert abs(DZA["manuf_share_exports"] - 36.6) < 0.1  # X_Manuf / X_T 2025
    assert DZA["data_year"] == 2015  # la structure, pas les totaux