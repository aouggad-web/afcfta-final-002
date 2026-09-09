"""
CEMAC Member States Tariff Scraper
===================================
Generates tariff files for CEMAC member states using the official CEMAC
Common External Tariff (TEC CEMAC) from the Tarif des Douanes PDF, with
country-specific national taxes verified from official government sources.

Reuses the Cameroon CEMAC PDF extraction logic (proven to extract 5,200+
positions) and applies country-specific national taxes.

Country-specific taxes verified from:
  - Gabon: dgi.ga, douanes.ga (TVA 18%)
  - Congo-Brazzaville: finances.gouv.cg, douanes.gouv.cg (TVA 18%)
  - Chad: finances.gouv.td, DGI Tchad (TVA 19.25%)
  - Central African Republic: finances.gouv.cf, edouanes.cf (TVA 19%)
"""

import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "crawled")

COUNTRY_CONFIGS = {
    "GAB": {
        "country": "GAB",
        "country_name": "Gabon",
        "source": "douanes.ga + TEC CEMAC",
        "source_url": "https://douanes.ga/",
        "currency": "XAF (FCFA)",
        "tva_rate": 18.0,
        "tva_name": "Taxe sur la Valeur Ajoutée",
        "tva_base": "CIF + DD + TCI",
        "national_taxes": {
            "TCI": {
                "code": "TCI",
                "name": "Taxe Communautaire d'Intégration (CEMAC)",
                "rate": 1.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
            "CIA": {
                "code": "CIA",
                "name": "Contribution à l'Intégration Africaine",
                "rate": 0.2,
                "type": "ad_valorem",
                "base": "CIF",
            },
            "TS": {
                "code": "TS",
                "name": "Taxe de Solidarité",
                "rate": 1.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "notes": [
            "Nomenclature: TEC CEMAC (Tarif Extérieur Commun) - identique pour les 6 États membres",
            "Droits de douane: TEC CEMAC (4 bandes: 5%, 10%, 20%, 30%)",
            "Taxes CEMAC: TCI (1%), CIA (0.2%), TS (1%) - source douanes.ga",
            "TVA: 18% taux normal (taux réduits 10% et 5% pour certains secteurs) - source dgi.ga",
            "Source officielle: douanes.ga + dgi.ga",
        ],
    },
    "COG": {
        "country": "COG",
        "country_name": "Congo (Brazzaville)",
        "source": "douanes.gouv.cg + TEC CEMAC",
        "source_url": "https://douanes.gouv.cg/",
        "currency": "XAF (FCFA)",
        "tva_rate": 18.0,
        "tva_name": "Taxe sur la Valeur Ajoutée",
        "tva_base": "CIF + DD + TCI",
        "national_taxes": {
            "TCI": {
                "code": "TCI",
                "name": "Taxe Communautaire d'Intégration (CEMAC)",
                "rate": 1.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
            "TS": {
                "code": "TS",
                "name": "Taxe Statistique",
                "rate": 0.2,
                "type": "ad_valorem",
                "base": "CIF",
            },
            "OHADA": {
                "code": "OHADA",
                "name": "Cotisation OHADA",
                "rate": 0.05,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "notes": [
            "Nomenclature: TEC CEMAC (Tarif Extérieur Commun) - identique pour les 6 États membres",
            "Droits de douane: TEC CEMAC (4 bandes: 5%, 10%, 20%, 30%)",
            "Taxes CEMAC: TCI (1%), TS (0.2%), OHADA (0.05%) - source finances.gouv.cg",
            "TVA: 18% taux standard (surtaxe 5% sur certains biens = 18.9% effectif possible) - source douanes.gouv.cg",
            "Source officielle: douanes.gouv.cg + finances.gouv.cg",
        ],
    },
    "TCD": {
        "country": "TCD",
        "country_name": "Tchad",
        "source": "finances.gouv.td + TEC CEMAC",
        "source_url": "https://finances.gouv.td/",
        "currency": "XAF (FCFA)",
        "tva_rate": 19.25,
        "tva_name": "TVA + Centimes Additionnels (17.5% + 10% CAC)",
        "tva_base": "CIF + DD + TCI",
        "national_taxes": {
            "TCI": {
                "code": "TCI",
                "name": "Taxe Communautaire d'Intégration (CEMAC)",
                "rate": 1.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
            "TS": {
                "code": "TS",
                "name": "Taxe Statistique",
                "rate": 2.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
            "PUA": {
                "code": "PUA",
                "name": "Prélèvement Union Africaine",
                "rate": 0.2,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "notes": [
            "Nomenclature: TEC CEMAC (Tarif Extérieur Commun) - identique pour les 6 États membres",
            "Droits de douane: TEC CEMAC (4 bandes: 5%, 10%, 20%, 30%)",
            "Taxes CEMAC: TCI (1%), TS (2%), PUA (0.2%) - source finances.gouv.td",
            "TVA: 19.25% (17.5% base + 10% centimes additionnels) - Loi de Finances 2024",
            "Taux réduit TVA: 9.90% pour produits locaux (sucre, huile, savon, textile)",
            "Source officielle: finances.gouv.td + DGI Tchad",
        ],
    },
    "CAF": {
        "country": "CAF",
        "country_name": "République Centrafricaine",
        "source": "finances.gouv.cf + TEC CEMAC",
        "source_url": "https://www.finances.gouv.cf/",
        "currency": "XAF (FCFA)",
        "tva_rate": 19.0,
        "tva_name": "Taxe sur la Valeur Ajoutée",
        "tva_base": "CIF + DD + TCI",
        "national_taxes": {
            "TCI": {
                "code": "TCI",
                "name": "Taxe Communautaire d'Intégration (CEMAC)",
                "rate": 1.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
            "RS": {
                "code": "RS",
                "name": "Redevance Statistique",
                "rate": 1.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
            "TS": {
                "code": "TS",
                "name": "Taxe de Solidarité",
                "rate": 1.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "notes": [
            "Nomenclature: TEC CEMAC (Tarif Extérieur Commun) - identique pour les 6 États membres",
            "Droits de douane: TEC CEMAC (4 bandes: 5%, 10%, 20%, 30%)",
            "Taxes CEMAC: TCI (1%), RS (1%), TS (1%) - source finances.gouv.cf",
            "TVA: 19% taux standard harmonisé CEMAC - source edouanes.cf",
            "Source officielle: finances.gouv.cf + edouanes.cf",
        ],
    },
    "GNQ": {
        "country": "GNQ",
        "country_name": "Guinée Équatoriale",
        "source": "TEC CEMAC + douanes.gob.gq",
        "source_url": "https://www.cemac.int/",
        "currency": "XAF (FCFA)",
        "tva_rate": 15.0,
        "tva_name": "Taxe sur la Valeur Ajoutée",
        "tva_base": "CIF + DD + TCI",
        "national_taxes": {
            "TCI": {
                "code": "TCI",
                "name": "Taxe Communautaire d'Intégration (CEMAC)",
                "rate": 1.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
            "RI": {
                "code": "RI",
                "name": "Redevance Informatique",
                "rate": 0.45,
                "type": "ad_valorem",
                "base": "CIF",
            },
            "TS": {
                "code": "TS",
                "name": "Taxe de Solidarité",
                "rate": 1.0,
                "type": "ad_valorem",
                "base": "CIF",
            },
        },
        "notes": [
            "Nomenclature: TEC CEMAC (Tarif Extérieur Commun) - identique pour les 6 États membres",
            "Droits de douane: TEC CEMAC (4 bandes: 5%, 10%, 20%, 30%)",
            "Taxes CEMAC: TCI (1%), RI (0.45%), TS (1%) - source cemac.int",
            "TVA: 15% taux standard - source douanes.gob.gq",
            "Source officielle: cemac.int + douanes.gob.gq",
        ],
    },
}


# ── Droit d'Accise (DA) ──
# Le DA est une accise appliquée aux produits sensibles (alcool, tabac,
# pétrole, produits de luxe). Les taux varient par chapitre, par produit
# et par pays. Ils sont publiés dans le Code CEMAC + CGI nationaux.
#
# IMPORTANT : Les taux DA ne sont PAS hardcodés ici. Ils doivent être
# collectés depuis les sources officielles (Code CEMAC + CGI nationaux).
# Pour les chapitres où un DA existe mais n'est pas crawlé, on conserve
# la marque DA = -1 (variable) avec un source_gap — jamais de taux inventé.
DA_CHAPTERS_KNOWN = {"22", "24", "27", "17", "18", "20", "21", "33", "71", "87", "91", "92", "93", "94", "95", "96"}


def build_country_position(cmr_position: dict, config: dict) -> dict:
    cmr_file = os.path.join(OUTPUT_DIR, "CMR_tariffs.json")
    if not os.path.exists(cmr_file):
        logger.info("CMR base data not found, running Cameroon scraper first...")
        from backend.crawlers.countries.cameroon_cemac_scraper import run_scraper as run_cmr

        run_cmr()

    with open(cmr_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    positions = data.get("positions", [])
    logger.info(f"Loaded {len(positions)} base CEMAC positions from CMR data")
    return positions


def build_country_position(cmr_position: dict, config: dict) -> dict:
    code_clean = cmr_position.get("code_clean", "")
    code_dotted = cmr_position.get("code", "")
    designation = cmr_position.get("designation", "")
    chapter = cmr_position.get("chapter", code_clean[:2] if code_clean else "")

    dd_rate = cmr_position.get("taxes", {}).get("DD", 0)

    cmr_tva = cmr_position.get("taxes", {}).get("TVA")
    is_tva_exempt = cmr_tva is not None and cmr_tva == 0.0
    has_tva_field = "TVA" in cmr_position.get("taxes", {})

    cmr_has_accise = "DA" in cmr_position.get("taxes", {})
    chapter = cmr_position.get("chapter", code_clean[:2] if code_clean else "")

    taxes = {"DD": dd_rate}
    taxes_detail = [
        {
            "tax_code": "DD",
            "tax_name": "Droit de Douane (TEC CEMAC)",
            "rate": dd_rate,
            "rate_type": "ad_valorem",
            "base": "CIF",
        }
    ]

    for key, tax_info in config["national_taxes"].items():
        taxes[tax_info["code"]] = tax_info["rate"]
        taxes_detail.append(
            {
                "tax_code": tax_info["code"],
                "tax_name": tax_info["name"],
                "rate": tax_info["rate"],
                "rate_type": tax_info["type"],
                "base": tax_info["base"],
            }
        )

    if is_tva_exempt:
        taxes["TVA"] = 0.0
        taxes_detail.append(
            {
                "tax_code": "TVA",
                "tax_name": config["tva_name"],
                "rate": 0.0,
                "rate_type": "ad_valorem",
                "base": config["tva_base"],
                "note": "Exonéré (EXO dans nomenclature CEMAC)",
            }
        )
    else:
        tva_rate = config["tva_rate"]
        taxes["TVA"] = tva_rate
        taxes_detail.append(
            {
                "tax_code": "TVA",
                "tax_name": config["tva_name"],
                "rate": tva_rate,
                "rate_type": "ad_valorem",
                "base": config["tva_base"],
            }
        )

    # ── Droit d'Accise (DA) : fail-closed — jamais de taux inventé ──
    # Le DA s'applique aux produits sensibles (alcool, tabac, pétrole, luxe).
    # Les taux sont publiés dans le Code CEMAC + CGI nationaux et doivent
    # être collectés depuis ces sources. Ici on signale seulement l'écart.
    if cmr_has_accise or chapter in DA_CHAPTERS_KNOWN:
        taxes["DA"] = -1
        taxes_detail.append(
            {
                "tax_code": "DA",
                "tax_name": "Droit d'Accise",
                "rate": -1,
                "rate_type": "variable",
                "base": "CIF + DD",
                "note": "Taux variable selon produit — collecter depuis CGI national (Loi de Finances). Tant que non crawlé, le calcul sera fail-closed.",
                "source_gap": True,
            }
        )

    return {
        "code": code_dotted,
        "code_clean": code_clean,
        "code_length": len(code_clean),
        "designation": designation,
        "chapter": chapter,
        "unit": cmr_position.get("unit", ""),
        "taxes": taxes,
        "taxes_detail": taxes_detail,
        "source": config["source"],
        "data_type": "regional_cet_with_national_taxes",
        "trade_bloc": "CEMAC",
        "source_verified": config["source_url"],
    }


def save_country_results(country_code: str, positions: List[dict], config: dict):
    output_file = os.path.join(OUTPUT_DIR, f"{country_code}_tariffs.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    tax_legend = {"DD": "Droit de Douane (TEC CEMAC: 5%, 10%, 20%, 30%)"}
    for key, tax_info in config["national_taxes"].items():
        tax_legend[tax_info["code"]] = f"{tax_info['name']} ({tax_info['rate']}%)"
    tax_legend["TVA"] = f"{config['tva_name']} ({config['tva_rate']}%)"

    result = {
        "country": country_code,
        "country_name": config["country_name"],
        "source": config["source"],
        "source_url": config["source_url"],
        "method": "cemac_tec_with_national_taxes",
        "hs_level": "HS8",
        "nomenclature": "CEMAC CET (TEC CEMAC) + National Taxes",
        "data_type": "regional_cet_with_national_taxes",
        "currency": config["currency"],
        "extracted_at": datetime.now().isoformat(),
        "total_positions": len(positions),
        "positions": positions,
        "tax_legend": tax_legend,
        "notes": config["notes"],
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f"  Saved {len(positions)} positions to {output_file}")
    return output_file


def run_scraper(countries: List[str] = None):
    if countries is None:
        countries = list(COUNTRY_CONFIGS.keys())

    logger.info("=" * 60)
    logger.info("CEMAC Member States Tariff Generation")
    logger.info(f"Countries: {', '.join(countries)}")
    logger.info("=" * 60)

    start_time = time.time()

    cmr_positions = load_cmr_base_positions()

    results = {}
    for cc in countries:
        if cc not in COUNTRY_CONFIGS:
            logger.warning(f"Unknown country code: {cc}")
            continue

        config = COUNTRY_CONFIGS[cc]
        logger.info(f"\nGenerating tariffs for {config['country_name']} ({cc})")

        country_positions = [build_country_position(pos, config) for pos in cmr_positions]

        tva_exempt_count = sum(1 for p in country_positions if p["taxes"].get("TVA") == 0.0)
        da_count = sum(1 for p in country_positions if "DA" in p["taxes"])
        logger.info(
            f"  Consistency check: {tva_exempt_count} TVA-exempt positions, {da_count} with Droit d'Accise"
        )

        save_country_results(cc, country_positions, config)

        dd_dist = {}
        tva_dist = {}
        for p in country_positions:
            dd = p["taxes"].get("DD", "N/A")
            dd_dist[dd] = dd_dist.get(dd, 0) + 1
            tva = p["taxes"].get("TVA", "N/A")
            tva_dist[str(tva)] = tva_dist.get(str(tva), 0) + 1

        results[cc] = {
            "positions": len(country_positions),
            "dd_distribution": dict(sorted(dd_dist.items())),
            "tva_distribution": dict(sorted(tva_dist.items())),
        }

    elapsed = time.time() - start_time
    logger.info(f"\nAll CEMAC countries generated in {elapsed:.1f}s")
    for cc, info in results.items():
        logger.info(f"  {cc}: {info['positions']} positions")
        logger.info(f"    DD: {info['dd_distribution']}")
        logger.info(f"    TVA: {info['tva_distribution']}")

    return results


if __name__ == "__main__":
    run_scraper()
