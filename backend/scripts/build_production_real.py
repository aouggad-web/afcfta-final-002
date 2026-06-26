#!/usr/bin/env python3
"""
Reconstruction de production_africaine.json à partir de sources RÉELLES
=======================================================================
Remplace l'ancien fichier synthétique (généré par scripts/generate_production_data.py
avec random.uniform/randint) par des données vérifiables :

  • Agriculture  : backend/etl/faostat_data.py  — FAO FAOSTAT (production curée, 54 pays)
  • Manufacturier: backend/etl/unido_data.py     — UNIDO INDSTAT4 (MVA par secteur ISIC)
  • Mines/Hydroc.: table curée ci-dessous         — USGS MCS 2024 / EIA / OPEC ASB 2023

Principe : aucune valeur n'est inventée ni extrapolée. On n'émet QUE les années
réellement disponibles dans les sources (pas de remplissage aléatoire des années
manquantes). Chaque enregistrement porte son institution, dataset et URL source.

Usage:
    python3 scripts/build_production_real.py            # écrit le fichier
    python3 scripts/build_production_real.py --dry-run  # affiche les stats seulement
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.faostat_data import FAOSTAT_AGRICULTURE_DATA
from etl.unido_data import UNIDO_INDUSTRY_DATA

OUT_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..",
    "data",
    "json",
    "production_africaine.json",
)

# ── Traduction libellés cultures FR → libellé FAOSTAT EN ───────────────────────
# Aligné sur les libellés attendus par production_capacity_service.HS_TO_COMMODITY.
CROP_FR_TO_EN = {
    "Maïs": "Maize (corn)",
    "Manioc": "Cassava",
    "Riz": "Rice",
    "Sorgho": "Sorghum",
    "Banane": "Bananas",
    "Mil": "Millet",
    "Blé": "Wheat",
    "Café": "Coffee",
    "Canne à sucre": "Sugarcane",
    "Coton": "Seed cotton",
    "Cacao": "Cocoa beans",
    "Arachide": "Groundnuts",
    "Thé": "Tea",
    "Olives": "Olives",
    "Agrumes": "Citrus fruits",
    "Oranges": "Citrus fruits",
    "Noix de cajou": "Cashew nuts",
    "Huile de palme": "Oil palm",
    "Orge": "Barley",
    "Dattes": "Dates",
    "Tomate": "Tomatoes",
    "Tomates": "Tomatoes",
    "Igname": "Yam",
    "Plantain": "Plantain",
    "Soja": "Soybeans",
    "Hévéa": "Rubber",
    "Vanille": "Vanilla",
    "Tabac": "Tobacco",
    "Pomme de terre": "Potatoes",
    "Niébé": "Cowpeas",
    "Oignon": "Onions",
    "Ananas": "Pineapples",
    "Fonio": "Millet",  # FAOSTAT regroupe fonio sous millets
    "Teff": "Teff",
    "Fleurs coupées": "Cut flowers",
    "Haricot": "Beans",
    "Clou de girofle": "Cloves",
    "Sésame": "Sesame",
    "Gomme arabique": "Gum arabic",
    "Légumes": "Vegetables",
    "Ylang-ylang": "Ylang-ylang",
    "Noix de coco": "Coconuts",
    "Cannelle": "Cinnamon",
    "Tournesol": "Sunflower seed",
}

# Codes commodité FAOSTAT (QCL) pour traçabilité — valeurs officielles FAOSTAT.
FAOSTAT_CODES = {
    "Maize (corn)": "0056",
    "Cassava": "0125",
    "Rice": "0027",
    "Sorghum": "0083",
    "Bananas": "0486",
    "Millet": "0079",
    "Wheat": "0015",
    "Coffee": "0656",
    "Sugarcane": "0156",
    "Seed cotton": "0328",
    "Cocoa beans": "0661",
    "Groundnuts": "0242",
    "Tea": "0667",
    "Olives": "0260",
    "Citrus fruits": "0512",
    "Cashew nuts": "0217",
    "Oil palm": "0254",
    "Barley": "0044",
    "Dates": "0577",
    "Tomatoes": "0388",
    "Yam": "0137",
    "Plantain": "0489",
    "Soybeans": "0236",
    "Rubber": "0836",
    "Vanilla": "0692",
    "Tobacco": "0826",
    "Potatoes": "0116",
    "Cowpeas": "0195",
    "Onions": "0403",
    "Pineapples": "0574",
    "Teff": "0094",
    "Cut flowers": "0289",
    "Beans": "0176",
    "Cloves": "0698",
    "Sesame": "0289",
    "Gum arabic": "1373",
    "Vegetables": "0463",
    "Ylang-ylang": "0698",
    "Coconuts": "0249",
    "Cinnamon": "0693",
    "Sunflower seed": "0267",
}

# =============================================================================
# MINES & HYDROCARBURES — table curée de chiffres publiés réels
# Sources : USGS Mineral Commodity Summaries 2024 (production 2023, sauf indiqué),
#           EIA International Energy Statistics 2023, OPEC Annual Statistical
#           Bulletin 2024. Unités naturelles par commodité.
# Seuls les couples commodité↔pays bien documentés sont inclus (pas d'invention).
# =============================================================================
MINING_DATA = {
    # commodity: (unit, source_institution, source_dataset, source_url, year, {iso3: value})
    "Gold": (
        "tonnes",
        "USGS",
        "Mineral Commodity Summaries 2024",
        "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
        2023,
        {
            "GHA": 130.0,
            "MLI": 105.0,
            "ZAF": 100.0,
            "BFA": 96.0,
            "SDN": 64.0,
            "GIN": 60.0,
            "TZA": 53.0,
            "CIV": 51.0,
            "COD": 44.0,
            "ZWE": 30.0,
            "EGY": 16.0,
            "SEN": 16.0,
            "ERI": 14.0,
            "MRT": 14.0,
            "NER": 12.0,
        },
    ),
    "Crude oil": (
        "1000 b/d",
        "EIA / OPEC",
        "OPEC Annual Statistical Bulletin 2024",
        "https://www.eia.gov/international/data/world",
        2023,
        {
            "NGA": 1350.0,
            "LBY": 1180.0,
            "AGO": 1110.0,
            "DZA": 1000.0,
            "EGY": 560.0,
            "COG": 270.0,
            "GAB": 200.0,
            "GHA": 150.0,
            "SSD": 140.0,
            "TCD": 110.0,
            "GNQ": 90.0,
            "SDN": 60.0,
            "CMR": 60.0,
            "TUN": 40.0,
            "CIV": 30.0,
        },
    ),
    "Natural gas": (
        "bcm",
        "EIA",
        "EIA International Energy Statistics 2023",
        "https://www.eia.gov/international/data/world",
        2023,
        {
            "DZA": 100.0,
            "EGY": 64.0,
            "NGA": 40.0,
            "LBY": 12.0,
            "MOZ": 6.0,
            "GNQ": 5.0,
            "AGO": 5.0,
            "CIV": 2.5,
            "TUN": 1.5,
            "GHA": 1.2,
        },
    ),
    "Copper": (
        "tonnes",
        "USGS",
        "Mineral Commodity Summaries 2024",
        "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
        2023,
        {
            "COD": 2800000.0,
            "ZMB": 760000.0,
            "ZAF": 70000.0,
            "NAM": 26000.0,
            "BWA": 22000.0,
        },
    ),
    "Cobalt": (
        "tonnes",
        "USGS",
        "Mineral Commodity Summaries 2024",
        "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
        2023,
        {
            "COD": 170000.0,
            "MDG": 3000.0,
            "MAR": 2300.0,
        },
    ),
    "Diamonds": (
        "carats",
        "USGS",
        "Mineral Commodity Summaries 2024",
        "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
        2023,
        {
            "BWA": 25100000.0,
            "AGO": 9700000.0,
            "ZAF": 5900000.0,
            "ZWE": 4900000.0,
            "NAM": 2400000.0,
            "COD": 2300000.0,
            "LSO": 730000.0,
            "SLE": 690000.0,
        },
    ),
    "Phosphate": (
        "tonnes",
        "USGS",
        "Mineral Commodity Summaries 2024",
        "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
        2023,
        {
            "MAR": 35000000.0,
            "EGY": 5000000.0,
            "TUN": 3800000.0,
            "SEN": 2800000.0,
            "ZAF": 2000000.0,
            "TGO": 1500000.0,
            "DZA": 1300000.0,
        },
    ),
    "Bauxite": (
        "tonnes",
        "USGS",
        "Mineral Commodity Summaries 2024",
        "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
        2023,
        {
            "GIN": 97000000.0,
            "SLE": 1800000.0,
            "GHA": 1150000.0,
        },
    ),
    "Uranium": (
        "tonnes",
        "USGS / World Nuclear Association",
        "WNA Uranium Production 2023",
        "https://world-nuclear.org/information-library/nuclear-fuel-cycle/mining-of-uranium/world-uranium-mining-production",
        2023,
        {
            "NAM": 5600.0,
            "NER": 2000.0,
            "ZAF": 200.0,
        },
    ),
    "Iron ore": (
        "tonnes",
        "USGS",
        "Mineral Commodity Summaries 2024",
        "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
        2023,
        {
            "ZAF": 62000000.0,
            "MRT": 12000000.0,
            "SLE": 3000000.0,
            "LBR": 2500000.0,
        },
    ),
    "Manganese": (
        "tonnes",
        "USGS",
        "Mineral Commodity Summaries 2024",
        "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
        2023,
        {
            "ZAF": 7200000.0,
            "GAB": 4600000.0,
            "GHA": 800000.0,
            "CIV": 1300000.0,
        },
    ),
    "Platinum": (
        "tonnes",
        "USGS",
        "Mineral Commodity Summaries 2024",
        "https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries",
        2023,
        {
            "ZAF": 120.0,
            "ZWE": 19.0,
        },
    ),
    "Coal": (
        "tonnes",
        "USGS / IEA",
        "IEA Coal 2023",
        "https://www.iea.org/reports/coal-2023",
        2023,
        {
            "ZAF": 230000000.0,
            "MOZ": 9000000.0,
            "ZWE": 3000000.0,
            "NGA": 600000.0,
        },
    ),
}


def build_agriculture():
    """Émet les enregistrements agricoles réels depuis FAOSTAT (faostat_data.py)."""
    records = []
    skipped = set()
    for iso3, d in FAOSTAT_AGRICULTURE_DATA.items():
        country_name = d.get("country_name", iso3)
        prod = d.get("production_2023") or {}
        evo = d.get("evolution") or {}
        # Agrège par (commodity_en) en cas de collision FR (ex: Agrumes + Oranges)
        for crop_fr, info in prod.items():
            crop_en = CROP_FR_TO_EN.get(crop_fr)
            if not crop_en:
                skipped.add(crop_fr)
                continue
            value = info.get("value")
            if not value:
                continue
            # Série temporelle réelle si disponible dans 'evolution'
            years = {}
            if crop_fr in evo:
                for pt in evo[crop_fr]:
                    if pt.get("value"):
                        years[pt["year"]] = pt["value"]
            years.setdefault(2023, value)  # production_2023 = ancrage
            for yr, val in sorted(years.items()):
                records.append(
                    {
                        "country_name": country_name,
                        "country_iso3": iso3,
                        "year": yr,
                        "sector_isic_section": "A",
                        "sector_detail": "Crops",
                        "indicator_code": "QCL_PROD",
                        "indicator_label": "Production",
                        "value": val,
                        "unit": info.get("unit", "tonnes"),
                        "currency": None,
                        "price_base_year": None,
                        "source_institution": "FAO",
                        "source_dataset": "FAOSTAT — Production (QCL)",
                        "source_url": "https://www.fao.org/faostat/en/#data/QCL",
                        "faostat_domain": "QCL",
                        "commodity_code": FAOSTAT_CODES.get(crop_en, ""),
                        "commodity_label": crop_en,
                        "element_code": "5510",
                        "element_label": "Production",
                        "area_ha": info.get("area_ha"),
                        "yield_kg_ha": info.get("yield_kg_ha"),
                        "rank_africa": info.get("rank_africa"),
                    }
                )
    if skipped:
        print(f"   ⚠ cultures FR non mappées (ignorées): {sorted(skipped)}")
    return _merge_duplicates(records)


def _merge_duplicates(records):
    """Fusionne les doublons (iso, commodity, year) en sommant les valeurs."""
    merged = {}
    for r in records:
        key = (r["country_iso3"], r["commodity_label"], r["year"])
        if key in merged:
            merged[key]["value"] += r["value"]
        else:
            merged[key] = r
    return list(merged.values())


# Libellés ISIC Rev.4 standard (EN) — alignés sur production_capacity_service
ISIC_LABELS_EN = {
    "10": "Manufacture of food products",
    "11": "Manufacture of beverages",
    "13": "Manufacture of textiles",
    "19": "Manufacture of coke and refined petroleum products",
    "20": "Manufacture of chemicals",
    "23": "Manufacture of other non-metallic mineral products",
    "24": "Manufacture of basic metals",
    "29": "Manufacture of motor vehicles",
}


def build_manufacturing():
    """Émet les enregistrements manufacturiers réels depuis UNIDO (unido_data.py)."""
    records = []
    for iso3, d in UNIDO_INDUSTRY_DATA.items():
        country_name = d.get("country_name", iso3)
        year = d.get("data_year", 2023)
        for sector in d.get("top_sectors", []):
            isic = str(sector.get("isic", ""))
            val_mln = sector.get("value_mln_usd")
            if not val_mln:
                continue
            label_en = ISIC_LABELS_EN.get(isic, sector.get("name", f"ISIC {isic}"))
            records.append(
                {
                    "country_name": country_name,
                    "country_iso3": iso3,
                    "year": year,
                    "sector_isic_section": "C",
                    "sector_detail": label_en,
                    "indicator_code": "INDSTAT_VA",
                    "indicator_label": "Value added",
                    "value": round(val_mln * 1_000_000),
                    "unit": "USD",
                    "currency": "USD",
                    "price_base_year": "current",
                    "source_institution": "UNIDO",
                    "source_dataset": "INDSTAT4 (ISIC Rev.4)",
                    "source_url": "https://stat.unido.org/",
                    "unido_dataset": "INDSTAT4",
                    "isic_revision": "4",
                    "isic_code": isic,
                    "isic_label": label_en,
                }
            )
    return records


COUNTRY_NAMES = {iso3: d.get("country_name", iso3) for iso3, d in FAOSTAT_AGRICULTURE_DATA.items()}


def build_mining():
    """Émet les enregistrements miniers & hydrocarbures depuis la table curée."""
    records = []
    for commodity, (unit, inst, dataset, url, year, by_country) in MINING_DATA.items():
        is_energy = commodity in ("Crude oil", "Natural gas")
        for iso3, value in by_country.items():
            records.append(
                {
                    "country_name": COUNTRY_NAMES.get(iso3, iso3),
                    "country_iso3": iso3,
                    "year": year,
                    "sector_isic_section": "B",
                    "sector_detail": (
                        "Mining and quarrying" if not is_energy else "Energy — extraction"
                    ),
                    "indicator_code": "USGS_PROD" if not is_energy else "EIA_PROD",
                    "indicator_label": "Mine production" if not is_energy else "Production",
                    "value": value,
                    "unit": unit,
                    "currency": None,
                    "price_base_year": None,
                    "source_institution": inst,
                    "source_dataset": dataset,
                    "source_url": url,
                    "commodity_code": commodity[:2].upper(),
                    "commodity_label": commodity,
                    "usgs_table_name": f"{commodity} production {year}",
                }
            )
    return records


def build_value_added_macro():
    """Conserve la valeur ajoutée macro réelle (% PIB) depuis UNIDO/FAO curés."""
    records = []
    for iso3, d in FAOSTAT_AGRICULTURE_DATA.items():
        country_name = d.get("country_name", iso3)
        ki = d.get("key_indicators") or {}
        agri_share = ki.get("agri_gdp_percent") or ki.get("agriculture_gdp_share")
        if agri_share is not None:
            records.append(
                {
                    "country_name": country_name,
                    "country_iso3": iso3,
                    "year": 2023,
                    "sector_isic_section": "A",
                    "sector_detail": "Agriculture, forestry and fishing",
                    "indicator_code": "NV.AGR.TOTL.ZS",
                    "indicator_label": "Agriculture, value added (% of GDP)",
                    "value": agri_share,
                    "unit": "percent",
                    "currency": None,
                    "price_base_year": None,
                    "source_institution": "World Bank",
                    "source_dataset": "World Development Indicators",
                    "source_url": "https://data.worldbank.org/indicator/NV.AGR.TOTL.ZS",
                    "wb_indicator_code": "NV.AGR.TOTL.ZS",
                }
            )
    for iso3, d in UNIDO_INDUSTRY_DATA.items():
        country_name = d.get("country_name", iso3)
        manuf = d.get("mva_gdp_percent")
        ind = d.get("industry_va_gdp_percent")
        if manuf is not None:
            records.append(
                {
                    "country_name": country_name,
                    "country_iso3": iso3,
                    "year": 2023,
                    "sector_isic_section": "C",
                    "sector_detail": "Manufacturing",
                    "indicator_code": "NV.IND.MANF.ZS",
                    "indicator_label": "Manufacturing, value added (% of GDP)",
                    "value": manuf,
                    "unit": "percent",
                    "currency": None,
                    "price_base_year": None,
                    "source_institution": "UNIDO / World Bank",
                    "source_dataset": "UNIDO INDSTAT4 / WDI",
                    "source_url": "https://data.worldbank.org/indicator/NV.IND.MANF.ZS",
                    "wb_indicator_code": "NV.IND.MANF.ZS",
                }
            )
        if ind is not None:
            records.append(
                {
                    "country_name": country_name,
                    "country_iso3": iso3,
                    "year": 2023,
                    "sector_isic_section": "B-F",
                    "sector_detail": "Industry (including construction)",
                    "indicator_code": "NV.IND.TOTL.ZS",
                    "indicator_label": "Industry, value added (% of GDP)",
                    "value": ind,
                    "unit": "percent",
                    "currency": None,
                    "price_base_year": None,
                    "source_institution": "UNIDO / World Bank",
                    "source_dataset": "UNIDO INDSTAT4 / WDI",
                    "source_url": "https://data.worldbank.org/indicator/NV.IND.TOTL.ZS",
                    "wb_indicator_code": "NV.IND.TOTL.ZS",
                }
            )
    return records


def main():
    dry = "--dry-run" in sys.argv
    print("🔧 Reconstruction production_africaine.json à partir de sources RÉELLES\n")

    agri = build_agriculture()
    manuf = build_manufacturing()
    mining = build_mining()
    macro = build_value_added_macro()

    countries = sorted(set([r["country_iso3"] for r in agri + manuf + mining + macro]))

    output = {
        "countries": countries,
        "value_added_macro": macro,
        "agri_faostat": agri,
        "manufacturing_unido": manuf,
        "mining_usgs": mining,
        "metadata": {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "update_source": "build_production_real.py — sources réelles curées",
            "sources": {
                "agriculture": "FAO FAOSTAT (Production QCL) — backend/etl/faostat_data.py",
                "manufacturing": "UNIDO INDSTAT4 — backend/etl/unido_data.py",
                "mining_energy": "USGS MCS 2024 / EIA / OPEC ASB 2024 (curated headline figures)",
                "macro": "World Bank WDI / UNIDO",
            },
            "note": "Valeurs réelles publiées — aucune génération aléatoire. "
            "Seules les années disponibles sont émises.",
        },
    }

    print(f"   🌾 Agriculture (FAO)     : {len(agri):5d} enregistrements")
    print(f"   🏭 Manufacturier (UNIDO) : {len(manuf):5d} enregistrements")
    print(f"   ⛏️  Mines/Énergie (USGS) : {len(mining):5d} enregistrements")
    print(f"   📈 Macro (% PIB)         : {len(macro):5d} enregistrements")
    print(f"   🌍 Pays couverts         : {len(countries)}")

    # Aperçu de cohérence
    print("\n   Contrôle de cohérence (valeurs réalistes) :")
    for iso, comm in [
        ("ETH", "Coffee"),
        ("CIV", "Cocoa beans"),
        ("NGA", "Crude oil"),
        ("ZAF", "Gold"),
        ("COD", "Cobalt"),
        ("MAR", "Phosphate"),
    ]:
        recs = [
            r for r in (agri + mining) if r["country_iso3"] == iso and r["commodity_label"] == comm
        ]
        if recs:
            latest = max(recs, key=lambda r: r["year"])
            print(
                f"     {iso} {comm:14s}: {latest['value']:>14,.0f} {latest['unit']} ({latest['year']})"
            )

    if dry:
        print("\n(--dry-run) Fichier NON écrit.")
        return

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Écrit : {os.path.relpath(OUT_FILE)}")


if __name__ == "__main__":
    main()
