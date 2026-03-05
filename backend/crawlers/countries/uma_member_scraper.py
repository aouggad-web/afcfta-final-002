"""
UMA Member States Tariff Scraper
==================================
Generates tariff files for all 7 North African (UMA/AMU + extended) countries
using the Morocco UMA reference data as the base, with country-specific
adjustments for local tax structures, preferential agreements, and trade policy.

Countries covered:
  MAR – Morocco   (reference – uses morocco_uma_scraper directly)
  EGY – Egypt     (COMESA + QIZ adjustments)
  TUN – Tunisia   (EU DCFTA + offshore regime)
  DZA – Algeria   (import substitution adjustments)
  LBY – Libya     (reconstruction incentives – waived duties)
  SDN – Sudan     (COMESA integration + transitional)
  MRT – Mauritania (ECOWAS/UMA bridge position)

Usage:
    python uma_member_scraper.py                  # All 7 countries
    python uma_member_scraper.py --countries MAR EGY TUN
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "crawled"

# ── Country-specific configurations ─────────────────────────────────────────

COUNTRY_CONFIGS: Dict[str, Dict[str, Any]] = {
    "EGY": {
        "country": "EGY",
        "country_name": "Egypt",
        "country_name_fr": "Égypte",
        "country_name_ar": "مصر",
        "currency": "EGP",
        "source": "Egyptian Customs Authority (ECA) + WTO schedule",
        "source_url": "https://www.gafinet.org",
        "trade_bloc": "COMESA + GAFTA + QIZ",
        "data_type": "uma_north_africa_derived",
        # Multiply Morocco DD by this factor for each band:
        "dd_factors": {
            "raw_materials": 0.80,      # 2.5% → ~2.0%
            "intermediate_goods": 1.20,  # 10% → ~12%
            "final_goods": 1.20,         # 25% → ~30%
            "agricultural": 0.50,        # 40% → ~20% (food security)
            "luxury_goods": 0.89,        # 45% → ~40%
        },
        "vat": {"standard": 14.0, "reduced": [5.0]},
        "national_taxes": {
            "Dev_Duty": {
                "code": "DD_Dev",
                "name": "Development Duty",
                "rate": 1.5,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "preferential_zero_rate": ["COMESA", "QIZ_US", "GAFTA", "AGADIR"],
        "special_zones": ["SCZONE", "QIZ_Zones", "New_Capital_SEZ"],
        "notes": [
            "COMESA member: up to 100% preference for member-state goods",
            "QIZ: US duty-free access for qualifying manufactured goods",
            "Development duty 1-2% applies to most imports",
            "Source: ECA (Egyptian Customs Authority) / WTO schedule",
        ],
    },
    "TUN": {
        "country": "TUN",
        "country_name": "Tunisia",
        "country_name_fr": "Tunisie",
        "country_name_ar": "تونس",
        "currency": "TND",
        "source": "Direction Générale des Douanes de Tunisie",
        "source_url": "https://www.douane.gov.tn",
        "trade_bloc": "UMA + EU-AA + GAFTA + Agadir",
        "data_type": "uma_north_africa_derived",
        "dd_factors": {
            "raw_materials": 0.0,        # 2.5% → 0% (EU AA largely eliminates)
            "intermediate_goods": 0.80,   # 10% → ~8%
            "final_goods": 0.88,          # 25% → ~22%
            "agricultural": 0.90,         # 40% → ~36%
            "luxury_goods": 0.96,         # 45% → ~43%
        },
        "vat": {"standard": 19.0, "reduced": [7.0, 13.0]},
        "national_taxes": {
            "HDR": {
                "code": "HDR",
                "name": "Droit de Timbre",
                "rate": 1.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "preferential_zero_rate": ["EU_AA", "EFTA", "GAFTA", "AGADIR"],
        "special_zones": ["Bizerte_EDZ", "Sfax_EZ", "Offshore_Regime"],
        "notes": [
            "EU Association Agreement 1998: industrial goods largely duty-free",
            "DCFTA (ALECA) negotiations ongoing for agriculture/services",
            "Offshore regime: 10% CIT for fully export-oriented enterprises",
            "Source: Direction Générale des Douanes de Tunisie",
        ],
    },
    "DZA": {
        "country": "DZA",
        "country_name": "Algeria",
        "country_name_fr": "Algérie",
        "country_name_ar": "الجزائر",
        "currency": "DZD",
        "source": "Direction Générale des Douanes d'Algérie",
        "source_url": "https://www.douane.dz",
        "trade_bloc": "UMA + EU-AA + GAFTA",
        "data_type": "uma_north_africa_derived",
        "dd_factors": {
            "raw_materials": 2.0,        # 2.5% → 5% (import substitution)
            "intermediate_goods": 1.50,   # 10% → 15%
            "final_goods": 1.20,          # 25% → 30%
            "agricultural": 0.75,         # 40% → 30%
            "luxury_goods": 1.33,         # 45% → 60% (luxury excise)
        },
        "vat": {"standard": 19.0, "reduced": [9.0]},
        "national_taxes": {
            "TAP": {
                "code": "TAP",
                "name": "Taxe sur l'Activité Professionnelle",
                "rate": 2.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
            "DCP": {
                "code": "DCP",
                "name": "Droit Complémentaire Provisoire (import substitution)",
                "rate": 30.0,
                "type": "ad_valorem",
                "base": "CIF",
                "applies_to": "selected consumer goods",
            },
        },
        "preferential_zero_rate": ["EU_AA_industrial", "GAFTA"],
        "special_zones": ["Bellara_Industrial_Zone"],
        "notes": [
            "Import substitution policy: DCP 30% on many consumer goods",
            "Local content requirements in automotive, construction sectors",
            "EU AA: industrial goods progressive liberalisation to 2020",
            "WTO observer – not yet a full member",
            "Source: douane.dz",
        ],
    },
    "LBY": {
        "country": "LBY",
        "country_name": "Libya",
        "country_name_fr": "Libye",
        "country_name_ar": "ليبيا",
        "currency": "LYD",
        "source": "Libyan Customs Authority (2010 schedule)",
        "source_url": "https://customs.gov.ly",
        "trade_bloc": "UMA + GAFTA",
        "data_type": "uma_north_africa_derived",
        "dd_factors": {
            "raw_materials": 0.0,        # 2.5% → 0% (reconstruction waiver)
            "intermediate_goods": 0.50,   # 10% → 5%
            "final_goods": 0.60,          # 25% → 15%
            "agricultural": 0.25,         # 40% → 10%
            "luxury_goods": 0.44,         # 45% → 20%
        },
        "vat": {"standard": 0.0, "notes": "No VAT; sales tax ~4%"},
        "national_taxes": {
            "Sales_Tax": {
                "code": "ST",
                "name": "Sales Tax",
                "rate": 4.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
            "Stamp_Duty": {
                "code": "SD",
                "name": "Stamp Duty",
                "rate": 0.5,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "preferential_zero_rate": ["GAFTA", "Reconstruction_Materials"],
        "special_zones": ["Misrata_FZ"],
        "notes": [
            "Post-conflict reconstruction: many tariffs suspended or waived",
            "Dual administration creates enforcement inconsistencies",
            "Data based on 2010 pre-conflict schedule; current application varies",
            "Oil sector: separate NOC fiscal regime",
            "Data reliability: LOW",
        ],
    },
    "SDN": {
        "country": "SDN",
        "country_name": "Sudan",
        "country_name_fr": "Soudan",
        "country_name_ar": "السودان",
        "currency": "SDG",
        "source": "Sudan Customs Administration + COMESA schedule",
        "source_url": "https://www.customs.gov.sd",
        "trade_bloc": "COMESA + GAFTA + AfCFTA",
        "data_type": "uma_north_africa_derived",
        "dd_factors": {
            "raw_materials": 0.0,        # 2.5% → 0%
            "intermediate_goods": 1.00,   # 10% → 10%
            "final_goods": 1.00,          # 25% → 25%
            "agricultural": 0.375,        # 40% → 15% (food security)
            "luxury_goods": 0.89,         # 45% → 40%
        },
        "vat": {"standard": 17.0, "reduced": [0.0]},
        "national_taxes": {
            "Dev_Levy": {
                "code": "DL",
                "name": "Development Levy",
                "rate": 2.5,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "preferential_zero_rate": ["COMESA", "GAFTA"],
        "special_zones": ["Khartoum_FTZ", "PortSudan_TZ"],
        "notes": [
            "COMESA member: preferential tariff elimination schedule",
            "Post-sanctions economy (US sanctions lifted 2017)",
            "Agriculture: gum arabic, cotton, sesame key exports",
            "Data reliability: LOW – political transition ongoing",
        ],
    },
    "MRT": {
        "country": "MRT",
        "country_name": "Mauritania",
        "country_name_fr": "Mauritanie",
        "country_name_ar": "موريتانيا",
        "currency": "MRU",
        "source": "Direction Générale des Douanes de Mauritanie",
        "source_url": "https://www.douane.mr",
        "trade_bloc": "UMA + GAFTA + ECOWAS-Observer + AfCFTA",
        "data_type": "uma_north_africa_derived",
        "dd_factors": {
            "raw_materials": 0.0,        # 2.5% → 0%
            "intermediate_goods": 1.00,   # 10% → 10%
            "final_goods": 0.80,          # 25% → 20%
            "agricultural": 0.50,         # 40% → 20%
            "luxury_goods": 0.67,         # 45% → 30%
        },
        "vat": {"standard": 16.0, "reduced": [0.0]},
        "national_taxes": {
            "Solidarity_Tax": {
                "code": "ST",
                "name": "Solidarity Tax",
                "rate": 1.5,
                "type": "ad_valorem",
                "base": "CIF",
            },
            "Statistical_Tax": {
                "code": "TS",
                "name": "Taxe Statistique",
                "rate": 1.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "preferential_zero_rate": ["UMA_partial", "GAFTA", "ECOWAS_partial"],
        "special_zones": ["Nouakchott_FZ"],
        "notes": [
            "Bridge country between Maghreb (UMA) and West Africa (ECOWAS)",
            "Mining sector: iron ore, gold, copper dominate exports",
            "Atlantic fisheries: major EU and China access agreements",
            "Renewable energy: significant solar/wind potential",
            "Data reliability: LOW",
        ],
    },
}

# ── Band mapping ─────────────────────────────────────────────────────────────

def _get_band(chapter: int) -> str:
    if 1 <= chapter <= 24:
        return "agricultural"
    elif 25 <= chapter <= 27:
        return "raw_materials"
    elif 28 <= chapter <= 49:
        return "intermediate_goods"
    elif 50 <= chapter <= 67:
        return "final_goods"
    elif 68 <= chapter <= 83:
        return "intermediate_goods"
    elif 84 <= chapter <= 92:
        return "final_goods"
    else:
        return "luxury_goods"


# ── Morocco base tariff bands ─────────────────────────────────────────────────
MOROCCO_BASE_BANDS = {
    "raw_materials": 2.5,
    "intermediate_goods": 10.0,
    "final_goods": 25.0,
    "agricultural": 40.0,
    "luxury_goods": 45.0,
}

MOROCCO_TVA_BANDS = {
    "agricultural": 7.0,    # food
    "raw_materials": 20.0,
    "intermediate_goods": 20.0,
    "final_goods": 20.0,
    "luxury_goods": 20.0,
}


def load_morocco_base_positions() -> List[Dict[str, Any]]:
    """
    Load Morocco reference positions from the UMA output file.

    Falls back to generating synthetic positions if the file does not exist.
    """
    mar_file = OUTPUT_DIR / "MAR_uma_tariffs.json"
    if mar_file.exists():
        try:
            with open(mar_file, encoding="utf-8") as f:
                data = json.load(f)
            positions = data.get("positions", [])
            if positions:
                logger.info(f"Loaded {len(positions)} Morocco reference positions from {mar_file}")
                return positions
        except Exception as exc:
            logger.warning(f"Could not load Morocco reference file: {exc}. Generating synthetic base.")

    # Fallback: generate synthetic base positions
    from crawlers.countries.morocco_uma_scraper import generate_reference_positions
    logger.info("Generating Morocco reference positions (fallback)...")
    return generate_reference_positions()


def build_country_position(
    mar_position: Dict[str, Any],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Derive a country-specific tariff position from a Morocco reference position.

    Args:
        mar_position: Morocco base tariff position dict
        config: Country configuration from COUNTRY_CONFIGS

    Returns:
        Country-specific tariff position in UMA schema format
    """
    chapter = int(mar_position.get("chapter", "01"))
    band = _get_band(chapter)

    # Compute DD rate
    mar_dd = MOROCCO_BASE_BANDS.get(band, 10.0)
    factor = config["dd_factors"].get(band, 1.0)
    dd_rate = round(mar_dd * factor, 2)

    # VAT
    vat_standard = config["vat"].get("standard", 0.0)

    # Build taxes dict
    taxes: Dict[str, float] = {"DD": dd_rate, "TVA": vat_standard}
    taxes_detail: Dict[str, Any] = {
        "DD": {
            "rate": dd_rate,
            "name": "Droit d'Importation",
            "base": "CIF",
            "derived_from": f"MAR {mar_dd}% × {factor}",
        },
        "TVA": {
            "rate": vat_standard,
            "name": "Taxe sur la Valeur Ajoutée",
            "base": "CIF + DD",
        },
    }

    for key, ntax in config.get("national_taxes", {}).items():
        code = ntax["code"]
        rate = ntax.get("rate", 0.0)
        taxes[code] = rate
        taxes_detail[code] = {
            "rate": rate,
            "name": ntax["name"],
            "base": ntax.get("base", "CIF"),
        }

    # Preferential rates
    pref: Dict[str, float] = {ag: 0.0 for ag in config.get("preferential_zero_rate", [])}

    code = mar_position.get("code", "")
    designation = mar_position.get("designation", "")

    return {
        "code": code,
        "code_clean": code.replace(".", ""),
        "code_length": len(code.replace(".", "")),
        "designation": designation,
        "chapter": f"{chapter:02d}",
        "band": band,
        "taxes": taxes,
        "taxes_detail": taxes_detail,
        "preferential_rates": pref,
        "source": config["source"],
        "source_url": config["source_url"],
        "data_type": config["data_type"],
        "trade_bloc": config["trade_bloc"],
        "country": config["country"],
        "country_name": config["country_name"],
    }


def save_country_results(
    country_code: str,
    positions: List[Dict[str, Any]],
    config: Dict[str, Any],
    elapsed: float,
) -> str:
    """Save country tariff data to JSON file and return path."""
    out_file = OUTPUT_DIR / f"{country_code}_uma_tariffs.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    tax_legend: Dict[str, str] = {
        "DD": f"Droit d'Importation (MFN, derived from Morocco base × country factor)",
        "TVA": f"Taxe sur la Valeur Ajoutée ({config['vat'].get('standard', 0.0)}%)",
    }
    for key, ntax in config.get("national_taxes", {}).items():
        tax_legend[ntax["code"]] = f"{ntax['name']} ({ntax.get('rate', 0.0)}%)"

    result = {
        "country": country_code,
        "country_name": config["country_name"],
        "country_name_fr": config.get("country_name_fr", ""),
        "country_name_ar": config.get("country_name_ar", ""),
        "currency": config["currency"],
        "trade_bloc": config["trade_bloc"],
        "source": config["source"],
        "source_url": config["source_url"],
        "method": "uma_member_derived_from_morocco_reference",
        "hs_level": "HS8",
        "nomenclature": f"HS8 (derived from Morocco NTS)",
        "data_type": config["data_type"],
        "extracted_at": datetime.utcnow().isoformat() + "Z",
        "total_positions": len(positions),
        "special_zones": config.get("special_zones", []),
        "preferential_agreements": config.get("preferential_zero_rate", []),
        "positions": positions,
        "tax_legend": tax_legend,
        "notes": config.get("notes", []),
        "generation_time_s": round(elapsed, 3),
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f"  Saved {len(positions)} positions → {out_file}")
    return str(out_file)


def run_scraper(
    countries: Optional[List[str]] = None,
    include_morocco: bool = True,
) -> Dict[str, Any]:
    """
    Generate UMA-compatible tariff data for all 7 North African countries.

    Args:
        countries: ISO-3 list to generate. Defaults to all 7 countries.
        include_morocco: Also (re-)generate the Morocco reference file.

    Returns:
        Dict mapping country codes to result summaries.
    """
    logging.basicConfig(level=logging.INFO)

    if countries is None:
        countries = list(COUNTRY_CONFIGS.keys())
        if include_morocco:
            countries = ["MAR"] + countries

    logger.info("=" * 60)
    logger.info("UMA North Africa Member States Tariff Generator")
    logger.info(f"Countries: {', '.join(countries)}")
    logger.info("=" * 60)

    overall_start = time.time()
    results: Dict[str, Any] = {}

    # Step 1: Generate / load Morocco reference
    if "MAR" in countries:
        from crawlers.countries.morocco_uma_scraper import run_scraper as mar_run
        logger.info("\n[1/2] Generating Morocco reference tariffs...")
        mar_result = mar_run()
        results["MAR"] = {
            "positions": mar_result["total_positions"],
            "file": str(OUTPUT_DIR / "MAR_uma_tariffs.json"),
            "elapsed_s": mar_result.get("generation_time_s", 0.0),
        }

    # Step 2: Load Morocco base for derivation
    logger.info("\n[2/2] Generating derived country tariffs...")
    mar_positions = load_morocco_base_positions()

    for cc in countries:
        if cc == "MAR":
            continue
        if cc not in COUNTRY_CONFIGS:
            logger.warning(f"  Unknown country code: {cc} – skipping")
            continue

        config = COUNTRY_CONFIGS[cc]
        t0 = time.time()
        logger.info(f"\n  Processing {config['country_name']} ({cc})...")

        country_positions = [
            build_country_position(pos, config) for pos in mar_positions
        ]
        elapsed = time.time() - t0
        saved_path = save_country_results(cc, country_positions, config, elapsed)

        # Distribution check
        dd_dist: Dict[str, int] = {}
        for p in country_positions:
            dd = str(p["taxes"].get("DD", "N/A"))
            dd_dist[dd] = dd_dist.get(dd, 0) + 1

        results[cc] = {
            "positions": len(country_positions),
            "file": saved_path,
            "elapsed_s": round(elapsed, 3),
            "dd_distribution": dict(sorted(dd_dist.items())),
        }
        logger.info(f"  {cc}: {len(country_positions)} positions in {elapsed:.2f}s")
        logger.info(f"  DD distribution: {results[cc]['dd_distribution']}")

    total_elapsed = round(time.time() - overall_start, 2)
    logger.info("\n" + "=" * 60)
    logger.info(f"UMA North Africa generation complete in {total_elapsed}s")
    for cc, info in results.items():
        logger.info(f"  {cc}: {info['positions']} positions")

    return results


if __name__ == "__main__":
    import sys
    countries_arg = sys.argv[1:] if len(sys.argv) > 1 else None
    run_scraper(countries=countries_arg)
