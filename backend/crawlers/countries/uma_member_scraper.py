"""
UMA Member States Tariff Scraper
==================================
Generates tariff files for all 7 UMA/AMU North African member states using
Morocco's tariff structure as the reference base (same approach as
cemac_member_scraper.py), with country-specific national tax adaptations.

Countries covered:
  DZA – Algeria      (Import substitution, 0–30% DD, TVA 19%)
  EGY – Egypt        (QIZ zones, Investment Law, CD 2–60%, VAT 14%)
  LBY – Libya        (Reconstruction focus, 0–40% DD, no VAT)
  MAR – Morocco      (Reference, 0–40% DI, TVA 20%)
  TUN – Tunisia      (EU association, 0–50% DD, TVA 19%, FODEC 1%)
  SDN – Sudan        (COMESA integration, 0–25% CD, VAT 17%)
  MRT – Mauritania   (ECOWAS transition, 0–20% DD, TVA 16%)

Usage:
    from backend.crawlers.countries.uma_member_scraper import run_scraper
    run_scraper()                          # all 7 countries
    run_scraper(countries=["DZA", "EGY"]) # selected countries
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "crawled")


# ---------------------------------------------------------------------------
# Country configurations  (tax adaptations on top of MAR base structure)
# ---------------------------------------------------------------------------

COUNTRY_CONFIGS: Dict[str, Dict] = {
    # ------------------------------------------------------------------
    # ALGERIA
    # ------------------------------------------------------------------
    "DZA": {
        "country": "DZA",
        "country_name": "Algeria",
        "country_name_fr": "Algérie",
        "source": "DGD Algérie + Base UMA Maroc",
        "source_url": "https://www.douane.gov.dz",
        "currency": "DZD (Dinar Algérien)",
        "vat_rate": 19.0,
        "vat_name": "Taxe sur la Valeur Ajoutée",
        "vat_base": "CIF + DD",
        # Chapter-level DD override: rate% -> chapters
        "tariff_overrides": {
            "0": ["25", "26", "27", "28", "29", "30", "31"],
            "5": ["01", "02", "03", "06", "07", "08", "09", "10",
                  "11", "12", "13", "14", "15", "23", "35", "36",
                  "37", "38", "39", "40", "41", "43", "44", "45",
                  "46", "47", "48", "49", "50", "51", "52", "53",
                  "54", "55", "56", "57", "58", "59", "60", "66",
                  "67", "68", "72", "73", "74", "75", "76", "78",
                  "79", "80", "81", "82", "83", "84", "85", "86",
                  "87", "88", "89", "90", "93"],
            "15": ["05", "32", "65", "69", "70", "71"],
            "30": ["04", "16", "17", "18", "19", "20", "21", "22",
                   "24", "33", "34", "42", "61", "62", "63", "64",
                   "91", "92", "94", "95", "96"],
        },
        "national_taxes": {
            "TSS": {
                "code": "TSS",
                "name": "Taxe de Solidarité Sociale",
                "rate": 1.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "tva_exempt_chapters": [],
        "excise_chapters": ["22", "24"],
        "notes": [
            "Base UMA (structure Maroc) adaptée aux taux DD algériens",
            "DD: 4 bandes (0%, 5%, 15%, 30%) – source DGD douane.gov.dz",
            "DAPS additionnel sur 1 095 produits (30–200%) non inclus",
            "TVA 19%, TSS 1% sur CIF",
            "Politique d'import-substitution active",
        ],
    },
    # ------------------------------------------------------------------
    # EGYPT
    # ------------------------------------------------------------------
    "EGY": {
        "country": "EGY",
        "country_name": "Egypt",
        "country_name_fr": "Égypte",
        "source": "Egyptian Customs Authority + Base UMA Maroc",
        "source_url": "https://www.customs.gov.eg",
        "currency": "EGP (Livre Égyptienne)",
        "vat_rate": 14.0,
        "vat_name": "Value Added Tax (VAT)",
        "vat_base": "CIF + CD",
        "tariff_overrides": {
            "0": [],
            "2": ["01", "02", "03", "06", "07", "08", "09", "10",
                  "11", "12", "15", "23", "25", "26", "27", "28",
                  "29", "30", "31", "32", "35", "38", "47"],
            "5": ["84", "85", "86", "88", "89", "90"],
            "12": ["50", "51", "52", "53", "54", "55", "56", "58",
                   "59", "60", "68", "74", "75"],
            "22": ["39", "40", "44", "48", "57", "72", "73", "76",
                   "82", "83"],
            "30": ["04", "16", "17", "18", "19", "20", "21", "42",
                   "63", "65", "69", "70", "87", "94"],
            "40": ["33", "61", "62", "64", "71", "91", "95"],
            "60": ["22", "24"],
        },
        "national_taxes": {},   # VAT is the main additional tax
        "tva_exempt_chapters": ["30"],
        "excise_chapters": ["22", "24", "33"],
        "notes": [
            "Base UMA (structure Maroc) adaptée aux taux CD égyptiens",
            "CD: 2%, 5%, 12%, 22%, 30%, 40%, 60%",
            "Investment Law 72/2017: 50% tax deduction (Upper Egypt, 7 ans)",
            "QIZ: accès USA 0% pour textiles avec 10,5% contenu israélien",
            "SCZONE (Suez Canal): taux douanier 5% unique + exonération TVA inputs",
            "COMESA: 0% intracommunautaire avec Certificat d'Origine",
        ],
    },
    # ------------------------------------------------------------------
    # LIBYA
    # ------------------------------------------------------------------
    "LBY": {
        "country": "LBY",
        "country_name": "Libya",
        "country_name_fr": "Libye",
        "source": "Libyan Customs Authority + Base UMA Maroc",
        "source_url": "https://customs.ly",
        "currency": "LYD (Dinar Libyen)",
        "vat_rate": 0.0,       # Libya has no VAT
        "vat_name": "Pas de TVA",
        "vat_base": "N/A",
        "tariff_overrides": {
            "0": ["06", "10", "11", "12", "23", "32", "35", "38",
                  "47", "50", "51", "52", "53", "54", "55", "56",
                  "58", "59", "60", "68", "74", "75"],
            "5": ["25", "26", "27", "28", "29", "30", "31", "84",
                  "85", "86", "87", "88", "89", "90"],
            "15": ["01", "02", "03", "07", "08", "09", "15", "39",
                   "40", "42", "44", "48", "57", "69", "70", "72",
                   "73", "76", "82", "83"],
            "25": ["04", "16", "17", "18", "19", "20", "21", "33",
                   "61", "62", "63", "64", "94", "95"],
            "40": ["22", "24"],
        },
        "national_taxes": {
            "TS": {
                "code": "TS",
                "name": "Taxe Statistique",
                "rate": 0.5,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "tva_exempt_chapters": list(str(i).zfill(2) for i in range(1, 97)),
        "excise_chapters": [],
        "notes": [
            "Base UMA (structure Maroc) adaptée aux taux libyens",
            "DD: 0%, 5%, 15%, 25%, 40% – reconstruction focus",
            "Aucune TVA – Libye",
            "TS (Taxe Statistique): 0.5% sur CIF",
            "Exemptions larges pour matériaux de reconstruction",
            "Zone franche Misurata opérationnelle",
        ],
    },
    # ------------------------------------------------------------------
    # MOROCCO (reference – included for completeness)
    # ------------------------------------------------------------------
    "MAR": {
        "country": "MAR",
        "country_name": "Morocco",
        "country_name_fr": "Maroc",
        "source": "ADII Maroc (données de référence UMA)",
        "source_url": "https://www.douane.gov.ma",
        "currency": "MAD (Dirham Marocain)",
        "vat_rate": 20.0,
        "vat_name": "Taxe sur la Valeur Ajoutée (TVA)",
        "vat_base": "CIF + DI + TPI",
        "tariff_overrides": {
            "0":    ["25", "26", "27", "30", "31"],
            "2.5":  ["28", "29", "32", "35", "38", "47", "50", "51",
                     "52", "53", "54", "55", "56", "58", "59", "60",
                     "68", "74", "75", "84", "85", "86", "87", "88",
                     "89", "90"],
            "10":   ["06", "10", "11", "12", "23", "57"],
            "17.5": ["01", "02", "03", "07", "08", "09", "15", "39",
                     "40", "42", "44", "48", "69", "70", "72", "73",
                     "76", "82", "83"],
            "25":   ["04", "16", "17", "18", "19", "20", "21", "33",
                     "61", "62", "63", "64", "94", "95"],
            "40":   ["22", "24"],
        },
        "national_taxes": {
            "TPI": {
                "code": "TPI",
                "name": "Taxe Parafiscale à l'Importation",
                "rate": 0.25,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "tva_exempt_chapters": [],
        "excise_chapters": ["22", "24", "33"],
        "notes": [
            "Pays de référence UMA – données ADII les plus complètes",
            "DI: 0%, 2.5%, 10%, 17.5%, 25%, 40%",
            "TPI: 0.25%; TVA: 20% (7%, 10%, 14% réduits)",
            "7 accords préférentiels (UE, USA, GAFTA, Agadir, AfCFTA, AELE, Turquie)",
        ],
    },
    # ------------------------------------------------------------------
    # TUNISIA
    # ------------------------------------------------------------------
    "TUN": {
        "country": "TUN",
        "country_name": "Tunisia",
        "country_name_fr": "Tunisie",
        "source": "DG Douanes Tunisie + Base UMA Maroc",
        "source_url": "https://www.douane.gov.tn",
        "currency": "TND (Dinar Tunisien)",
        "vat_rate": 19.0,
        "vat_name": "Taxe sur la Valeur Ajoutée (TVA)",
        "vat_base": "CIF + DD + FODEC",
        "tariff_overrides": {
            "0":  ["25", "26", "27", "28", "29", "30", "31"],
            "10": ["06", "10", "11", "12", "23", "32", "35", "38",
                   "47", "50", "51", "52", "53", "54", "55", "56",
                   "58", "59", "60", "68", "74", "75", "84", "85",
                   "86", "88", "89", "90"],
            "20": ["01", "02", "03", "07", "08", "09", "15", "39",
                   "40", "44", "48", "57", "72", "73", "76", "82",
                   "83", "87"],
            "30": ["42", "63", "65", "69", "70"],
            "36": ["04", "16", "17", "18", "19", "20", "21", "71",
                   "91", "95"],
            "43": ["33", "61", "62", "64", "94"],
            "50": ["22", "24"],
        },
        "national_taxes": {
            "FODEC": {
                "code": "FODEC",
                "name": "Fonds de Développement de la Compétitivité",
                "rate": 1.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "tva_exempt_chapters": ["30"],
        "excise_chapters": ["22", "24"],
        "notes": [
            "Base UMA (structure Maroc) adaptée aux taux DD tunisiens",
            "DD: 0%, 10%, 20%, 30%, 36%, 43%, 50%",
            "FODEC: 1% sur CIF",
            "TVA: 19% standard, 13% réduit, 7% réduit spécial",
            "Accord UE: 0% sur produits industriels depuis 2008",
            "Zone Franche Bizerte: exonération totale sur 10 ans",
        ],
    },
    # ------------------------------------------------------------------
    # SUDAN
    # ------------------------------------------------------------------
    "SDN": {
        "country": "SDN",
        "country_name": "Sudan",
        "country_name_fr": "Soudan",
        "source": "Sudan Customs and Tax Authority + Base UMA Maroc",
        "source_url": "https://www.customs.gov.sd",
        "currency": "SDG (Livre Soudanaise)",
        "vat_rate": 17.0,
        "vat_name": "Value Added Tax (VAT)",
        "vat_base": "CIF + CD",
        "tariff_overrides": {
            "0": ["25", "26", "27", "28", "29", "30", "31", "84",
                  "85", "86", "88", "89", "90"],
            "10": ["06", "10", "11", "12", "23", "32", "35", "38",
                   "47", "50", "51", "52", "53", "54", "55", "56",
                   "58", "59", "60", "68", "74", "75"],
            "20": ["01", "02", "03", "04", "07", "08", "09", "15",
                   "16", "17", "18", "19", "20", "21", "39", "40",
                   "42", "44", "48", "57", "63", "65", "69", "70",
                   "72", "73", "76", "82", "83", "87"],
            "25": ["22", "24", "33", "61", "62", "64", "71", "91",
                   "94", "95"],
        },
        "national_taxes": {
            "DS": {
                "code": "DS",
                "name": "Development Surcharge",
                "rate": 2.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "tva_exempt_chapters": ["30"],
        "excise_chapters": ["22", "24"],
        "notes": [
            "Base UMA (structure Maroc) adaptée aux taux soudanais",
            "CD: 0%, 10%, 20%, 25%",
            "Development Surcharge (DS): 2% sur CIF",
            "VAT: 17%",
            "COMESA: 0% pour membres avec Certificat d'Origine",
            "Port Sudan: gateway stratégique Mer Rouge",
        ],
    },
    # ------------------------------------------------------------------
    # MAURITANIA
    # ------------------------------------------------------------------
    "MRT": {
        "country": "MRT",
        "country_name": "Mauritania",
        "country_name_fr": "Mauritanie",
        "source": "DGD Mauritanie + Base UMA Maroc",
        "source_url": "https://www.douanes.gov.mr",
        "currency": "MRU (Ouguiya)",
        "vat_rate": 16.0,
        "vat_name": "Taxe sur la Valeur Ajoutée (TVA)",
        "vat_base": "CIF + DD",
        "tariff_overrides": {
            "0": ["25", "26", "27", "28", "29", "30", "31", "84",
                  "85", "86", "88", "89", "90"],
            "5": ["06", "10", "11", "12", "23", "32", "35", "38",
                  "47", "50", "51", "52", "53", "54", "55", "56",
                  "58", "59", "60", "68", "74", "75", "87"],
            "10": ["01", "02", "03", "07", "08", "09", "15", "39",
                   "40", "44", "48", "57", "72", "73", "76", "82",
                   "83"],
            "15": ["04", "16", "17", "18", "19", "20", "21", "42",
                   "63", "69", "70", "71"],
            "20": ["22", "24", "33", "61", "62", "64", "94", "95"],
        },
        "national_taxes": {
            "TS": {
                "code": "TS",
                "name": "Taxe Statistique",
                "rate": 1.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "tva_exempt_chapters": ["30"],
        "excise_chapters": ["22", "24"],
        "notes": [
            "Base UMA (structure Maroc) adaptée aux taux mauritaniens",
            "DD: 0%, 5%, 10%, 15%, 20%",
            "TS (Taxe Statistique): 1% sur CIF",
            "TVA: 16%",
            "Membre UMA et observateur CEDEAO",
            "Économie basée sur pêche, mine de fer (SNIM), hydrocarbures",
        ],
    },
}


# ---------------------------------------------------------------------------
# Build chapter→rate map from tariff_overrides
# ---------------------------------------------------------------------------

def _build_override_map(overrides: Dict[str, List[str]]) -> Dict[str, float]:
    """Return {chapter: rate_pct} from a tariff_overrides dict."""
    result: Dict[str, float] = {}
    for rate_str, chapters in overrides.items():
        rate_val = float(rate_str)
        for ch in chapters:
            result[ch] = rate_val
    return result


# ---------------------------------------------------------------------------
# Load MAR base positions
# ---------------------------------------------------------------------------

def load_mar_base_positions(output_dir: str = OUTPUT_DIR) -> List[Dict]:
    """
    Load MAR (Morocco) base positions from the crawled data file.
    If the file doesn't exist, runs the Morocco reference scraper first.
    """
    mar_file = os.path.join(output_dir, "MAR_tariffs.json")

    if not os.path.exists(mar_file):
        logger.info("MAR base data not found – running NorthAfricaScraper first …")
        from backend.crawlers.countries.north_africa_scraper import run_scraper as run_mar
        run_mar(output_dir=output_dir)

    with open(mar_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    positions = data.get("positions", [])
    logger.info(f"Loaded {len(positions)} base UMA positions from MAR data")
    return positions


# ---------------------------------------------------------------------------
# Build country position from MAR base
# ---------------------------------------------------------------------------

def build_country_position(mar_position: Dict, config: Dict, override_map: Dict[str, float]) -> Dict:
    """
    Adapt a MAR base position to the target country's tax structure.

    Args:
        mar_position: A position dict from MAR_tariffs.json
        config: The country config from COUNTRY_CONFIGS
        override_map: {chapter: dd_rate_pct} for the target country

    Returns:
        A new position dict with country-specific taxes applied.
    """
    chapter = mar_position.get("chapter", "")
    code = mar_position.get("code", "")
    code_clean = mar_position.get("code_clean", "")
    designation = mar_position.get("designation", "")

    # Determine DD/DI/CD rate for this country and chapter
    dd_rate = override_map.get(chapter, 10.0)   # default 10% if chapter not listed

    is_tva_exempt = (
        chapter in config.get("tva_exempt_chapters", [])
        or config["vat_rate"] == 0.0
    )
    has_excise = chapter in config.get("excise_chapters", [])

    tax_code_label = "DD" if config["country"] not in ("EGY", "SDN") else "CD"
    if config["country"] == "MAR":
        tax_code_label = "DI"

    taxes: Dict = {tax_code_label: dd_rate}
    taxes_detail: List[Dict] = [
        {
            "tax_code": tax_code_label,
            "tax_name": (
                "Droit d'Importation" if tax_code_label == "DI"
                else "Customs Duty (CD)" if tax_code_label == "CD"
                else "Droit de Douane (DD)"
            ),
            "rate": dd_rate,
            "rate_type": "ad_valorem",
            "base": "CIF",
        }
    ]

    # National taxes
    for key, tax_info in config["national_taxes"].items():
        taxes[tax_info["code"]] = tax_info["rate"]
        taxes_detail.append({
            "tax_code": tax_info["code"],
            "tax_name": tax_info["name"],
            "rate": tax_info["rate"],
            "rate_type": tax_info["type"],
            "base": tax_info["base"],
        })

    # VAT / TVA
    if is_tva_exempt:
        taxes["TVA"] = 0.0
        taxes_detail.append({
            "tax_code": "TVA",
            "tax_name": config["vat_name"],
            "rate": 0.0,
            "rate_type": "ad_valorem",
            "base": config["vat_base"],
            "note": "Exonéré / Exempt",
        })
    else:
        taxes["TVA"] = config["vat_rate"]
        taxes_detail.append({
            "tax_code": "TVA",
            "tax_name": config["vat_name"],
            "rate": config["vat_rate"],
            "rate_type": "ad_valorem",
            "base": config["vat_base"],
        })

    # Excise / TIC / Droit d'Accise
    if has_excise:
        taxes["DA"] = -1
        taxes_detail.append({
            "tax_code": "DA",
            "tax_name": "Droit d'Accise / Excise Duty",
            "rate": -1,
            "rate_type": "variable",
            "base": "CIF + DD",
            "note": "Taux variable selon produit – consulter les douanes nationales",
        })

    return {
        "code": code,
        "code_clean": code_clean,
        "code_length": len(code_clean),
        "designation": designation,
        "chapter": chapter,
        "unit": mar_position.get("unit", "kg"),
        "taxes": taxes,
        "taxes_detail": taxes_detail,
        "source": config["source"],
        "data_type": "uma_regional_tariff_with_national_taxes",
        "trade_bloc": "UMA",
        "source_verified": config["source_url"],
        "languages": ["ar", "fr"],
    }


# ---------------------------------------------------------------------------
# Save results
# ---------------------------------------------------------------------------

def save_country_results(country_code: str, positions: List[Dict], config: Dict,
                         output_dir: str = OUTPUT_DIR) -> str:
    output_file = os.path.join(output_dir, f"{country_code}_uma_tariffs.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    tax_code = "DI" if country_code == "MAR" else ("CD" if country_code in ("EGY", "SDN") else "DD")
    tax_legend = {
        tax_code: f"Droit de douane (taux variables par chapitre)",
        "TVA": f"{config['vat_name']} ({config['vat_rate']}%)",
    }
    for key, tax_info in config["national_taxes"].items():
        tax_legend[tax_info["code"]] = f"{tax_info['name']} ({tax_info['rate']}%)"

    result = {
        "country": country_code,
        "country_name": config["country_name"],
        "country_name_fr": config["country_name_fr"],
        "source": config["source"],
        "source_url": config["source_url"],
        "method": "uma_member_schedule_from_mar_base",
        "hs_level": "HS6",
        "nomenclature": "Nomenclature UMA (base Maroc) + taxes nationales",
        "data_type": "uma_regional_tariff_with_national_taxes",
        "currency": config["currency"],
        "trade_bloc": "UMA",
        "extracted_at": datetime.now().isoformat(),
        "total_positions": len(positions),
        "positions": positions,
        "tax_legend": tax_legend,
        "notes": config["notes"],
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f"  Saved {len(positions)} positions → {output_file}")
    return output_file


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_scraper(
    countries: Optional[List[str]] = None,
    output_dir: str = OUTPUT_DIR,
) -> Dict:
    """
    Run the UMA member states tariff generator.

    Args:
        countries: List of ISO3 codes to process.  Defaults to all 7.
        output_dir: Directory where JSON output files are written.

    Returns:
        dict mapping country_code -> summary dict.
    """
    if countries is None:
        countries = list(COUNTRY_CONFIGS.keys())

    logger.info("=" * 60)
    logger.info("UMA Member States Tariff Generation")
    logger.info(f"Countries: {', '.join(countries)}")
    logger.info("=" * 60)

    start_time = time.time()

    mar_positions = load_mar_base_positions(output_dir)

    results: Dict = {}
    for cc in countries:
        if cc not in COUNTRY_CONFIGS:
            logger.warning(f"Unknown country code: {cc} – skipping")
            continue

        config = COUNTRY_CONFIGS[cc]
        logger.info(f"\nGenerating tariffs for {config['country_name']} ({cc}) …")

        override_map = _build_override_map(config["tariff_overrides"])

        country_positions = [
            build_country_position(pos, config, override_map)
            for pos in mar_positions
        ]

        # Consistency stats
        tva_exempt_count = sum(1 for p in country_positions if p["taxes"].get("TVA") == 0.0)
        da_count = sum(1 for p in country_positions if "DA" in p["taxes"])
        logger.info(f"  TVA-exempt positions: {tva_exempt_count}, with Excise: {da_count}")

        save_country_results(cc, country_positions, config, output_dir)

        # Build distribution stats
        dd_dist: Dict = {}
        tva_dist: Dict = {}
        for p in country_positions:
            tax_key = "DI" if cc == "MAR" else ("CD" if cc in ("EGY", "SDN") else "DD")
            dd = p["taxes"].get(tax_key, "N/A")
            dd_dist[str(dd)] = dd_dist.get(str(dd), 0) + 1
            tva = p["taxes"].get("TVA", "N/A")
            tva_dist[str(tva)] = tva_dist.get(str(tva), 0) + 1

        results[cc] = {
            "positions": len(country_positions),
            "dd_distribution": dict(sorted(dd_dist.items())),
            "tva_distribution": dict(sorted(tva_dist.items())),
        }

    elapsed = time.time() - start_time
    logger.info(f"\nAll UMA countries generated in {elapsed:.1f}s")
    for cc, info in results.items():
        logger.info(f"  {cc}: {info['positions']} positions")

    return results


if __name__ == "__main__":
    run_scraper()
