"""L'entrée DZA d'unido_data doit servir les comptes de l'ONS, chiffre par chiffre.

L'entrée algérienne reposait sur la structure INDSTAT de 2015, la dernière
transmise par l'ONS à l'ONUDI : l'écran Manufacture montrait l'Algérie dix
ans en retard sur les autres pays. L'ONS publie pourtant sa valeur ajoutée par
branche jusqu'en 2024 (« Les comptes économiques de 2021 à 2024 », n° 1067),
reprise dans ``data/json/dza_industrie.json`` avec une estimation 2025.

Ces tests verrouillent l'entrée recalculée (``etl/dza_manufacture_ons.py``) :
les totaux retombent sur les chiffres publiés, la structure par branche sur la
VA totale, chaque champ dit sa nature, et l'estimation 2025 garde sa fourchette
et sa confiance. La structure INDSTAT 2015 est conservée à part : elle recoupe
toujours exactement le versement ISIC4 (classes 1910+1920 = division 19) que
l'écran affiche encore au niveau classe.
"""

import csv
import gzip
import json
import os

from etl.unido_data import UNIDO_INDUSTRY_DATA

from scripts.build_production_real import build_manufacturing

DZA = UNIDO_INDUSTRY_DATA["DZA"]

_RACINE = os.path.join(os.path.dirname(__file__), "..", "..")
ONS = json.load(open(os.path.join(_RACINE, "data", "json", "dza_industrie.json"), encoding="utf-8"))

# Valeur ajoutée manufacturière publiée par l'ONS, en millions d'USD (taux de
# change moyen annuel de la Banque mondiale) ; la Banque mondiale (WDI
# NV.IND.MANF.CD) publie les mêmes chiffres au million près.
_VA_2023_MUSD = 22610.7
_VA_2024_MUSD = 25463.0


def test_totals_are_the_published_ons_values():
    assert abs(DZA["mva_2023_mln_usd"] - _VA_2023_MUSD) < 0.05
    assert abs(DZA["mva_2024_mln_usd"] - _VA_2024_MUSD) < 0.05
    # Part du PIB 2023 : 22 610,7 M$ / PIB Banque mondiale = 9,12 % (WDI publie 9,12)
    assert abs(DZA["mva_gdp_percent"] - 9.12) < 0.01
    # Par habitant 2023 : 22 610,7 M$ / 46 164 219 habitants
    assert abs(DZA["mva_per_capita_usd"] - 490) < 1
    assert DZA["data_year"] == 2024


def test_growth_is_aggregated_from_official_branch_volumes():
    """Croissance du total : VA de l'année précédente de chaque branche portée
    par sa croissance en volume publiée, rapportée à leur somme."""
    for annee, cle in ((2023, "growth_rate_2023"), (2024, "growth_rate_2024")):
        num = den = 0.0
        for b in ONS["branches"]:
            v0 = b["annees"][str(annee - 1)]["va_mda"]
            num += v0 * (1 + b["annees"][str(annee)]["croissance_volume_pct"] / 100)
            den += v0
        assert abs(DZA[cle] - round((num / den - 1) * 100, 1)) < 1e-9
    assert DZA["natures"]["growth_rate_2023"] == "calcul_officiel"


def test_structure_is_ons_2024_and_sums_to_the_published_total():
    secteurs = DZA["top_sectors"]
    somme = sum(s["value_mln_usd"] for s in secteurs)
    assert abs(somme - _VA_2024_MUSD) < 0.5  # arrondis au dixième, 13 branches
    assert abs(sum(s["share_mva"] for s in secteurs) - 100) < 0.3
    # Du plus grand au plus petit ; le raffinage pèse 53,6 % en 2024.
    valeurs = [s["value_mln_usd"] for s in secteurs]
    assert valeurs == sorted(valeurs, reverse=True)
    raffinage = {s["isic"]: s for s in secteurs}["19"]
    assert abs(raffinage["value_mln_usd"] - 13647.4) < 0.05
    assert abs(raffinage["share_mva"] - 53.6) < 0.05
    # Les treize branches ONS sont là.
    assert sorted(s["code_ons"] for s in secteurs) == sorted(b["code"] for b in ONS["branches"])
    assert all(s["nature"] == "officiel" for s in secteurs)


def test_grouped_branches_say_how_they_enter_the_rankings():
    par_isic = {s["isic"]: s for s in DZA["top_sectors"]}
    # Rattachement défendable : la VA de la branche est portée sur une division.
    assert par_isic["24"]["rattachement_isic"] == "24"
    assert "24-25" in par_isic["24"]["rattachement_note"]
    # Sans rattachement défendable, ou sans correspondance SH : hors classements.
    for cle in ("16-18", "29-33", "26-bur", "26-com", "15", "28"):
        assert par_isic[cle]["rattachement_isic"] is None
        assert "hors classements" in par_isic[cle]["rattachement_note"]


def test_estimation_2025_keeps_its_range_and_confidence():
    e = DZA["estimation_2025"]
    total = ONS["total"]["2025"]
    assert e["va_mln_usd"] == total["va_musd"]
    assert e["va_mln_usd"]["bas"] <= e["va_mln_usd"]["central"] <= e["va_mln_usd"]["haut"]
    assert e["croissance_volume_pct"] == total["croissance_volume_pct"]
    # Part de la VA 2024 portée par des branches notées B, puis C.
    assert set(e["confiance_part_va_pct"]) <= {"B", "C"}
    assert abs(sum(e["confiance_part_va_pct"].values()) - 100) < 0.2
    assert e["methode"] and e["base_prix"]


def test_division_19_cross_checks_against_the_class_level_versement():
    """Le versement ISIC4 committé donne 1910+1920 (VA 2015) ; leur somme doit
    retomber EXACTEMENT sur la division 19 de la structure INDSTAT 2015."""
    rows = []
    with gzip.open(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "data",
            "unido",
            "unido_idsb_indstat_isic4_dza_2005_2017.csv.gz",
        ),
        mode="rt",
        encoding="utf-8",
        newline="",
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
    indstat = {s["isic"]: s for s in DZA["structure_indstat_2015"]}["19"]["value_mln_usd"]
    assert (
        abs(division_19 - indstat) < 0.05
    ), f"division 19 INDSTAT 2015 ({indstat}) ≠ versement ISIC4 ({division_19})"


def test_manufacturing_records_carry_the_ons_source_and_nature():
    records = [r for r in build_manufacturing() if r["country_iso3"] == "DZA"]
    par_isic = {r["isic_code"]: r for r in records}
    assert set(par_isic) == {"19", "10", "20", "13", "23", "24", "27"}
    assert all(r["year"] == 2024 and r["source_institution"] == "ONS Algérie" for r in records)
    assert par_isic["19"]["value"] == 13_647_400_000
    # Branche d'une seule division : valeur publiée. Branche groupée portée sur
    # une division : majorant, donc estimation, et la note le dit.
    assert par_isic["19"]["is_estimation"] is False
    assert par_isic["24"]["is_estimation"] is True and "24-25" in par_isic["24"]["note"]
    # Le libellé CITI standard reste la clé de correspondance SH.
    assert par_isic["24"]["isic_label"] == "Manufacture of basic metals"


def test_unido_only_fields_are_kept_and_labelled():
    assert DZA["cip_index_rank"] == 93  # CIP 2024
    assert abs(DZA["mht_share_mva"] - 2.69) < 0.01  # MHVAsh 2024 / ODD 9.b.1 2015
    assert abs(DZA["exports_manuf_mln_usd"] - 17544.63) < 0.01  # MTD X_Manuf 2025
    assert abs(DZA["manuf_share_exports"] - 36.6) < 0.1  # X_Manuf / X_T 2025
    for cle in ("cip_index_rank", "exports_manuf_mln_usd", "industry_employment"):
        assert DZA["natures"][cle] == "unido"


def test_comptes_ons_replace_the_isic4_detail_on_screen():
    """L'écran remplace, pour l'Algérie, le détail ISIC4 d'UNIDO (2005-2017)
    par les treize branches des comptes économiques, millésime par
    millésime, avec le statut ONS de chacun."""
    c = DZA["comptes_ons"]
    assert c["statuts"] == {"2021": "définitif", "2022": "définitif", "2023": "semi-définitif", "2024": "provisoire"}
    assert "n° 1067" in c["source"]
    assert len(c["branches"]) == 13
    for annee in ("2021", "2022", "2023", "2024"):
        somme = sum(b["va_musd"][annee] for b in c["branches"])
        # Branches et total convertis séparément en dollars : écart d'arrondi.
        assert abs(somme - c["total"]["va_musd"][annee]) < 3.0
    assert c["total"]["va_musd"]["2024"] == _VA_2024_MUSD
    raffinage = c["branches"][0]
    assert raffinage["code"] == "19" and raffinage["va_musd"]["2024"] == 13647.4
    for b in c["branches"]:
        e = b["estimation_2025"]
        assert e["confiance"] in ("B", "C")
        assert e["va_musd"]["bas"] <= e["va_musd"]["central"] <= e["va_musd"]["haut"]
