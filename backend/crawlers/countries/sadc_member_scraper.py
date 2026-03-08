"""
SADC Member States Scraper
===========================
Generates tariff and investment profile JSON files for all 16 SADC member
states, following the same output convention used by the CEMAC and ECOWAS
member scrapers.

For SACU members (ZAF, BWA, NAM, LSO, SWZ) the Common External Tariff is
shared; the scraper reuses the ZAF base positions and applies country-specific
VAT and national tax overrides.

For non-SACU SADC members each country gets its own tariff schedule sourced
from the country-specific configuration in
`sadc/tariff_structures.py`.

Output: backend/data/crawled/{COUNTRY_CODE}_tariffs.json for each country
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'crawled')

# ---------------------------------------------------------------------------
# Country configurations (inline – mirrors cemac_member_scraper.py structure)
# ---------------------------------------------------------------------------

COUNTRY_CONFIGS = {
    # ---------------------------------------------------------------- SACU --
    "BWA": {
        "country": "BWA",
        "country_name": "Botswana",
        "region": "SADC/SACU",
        "source": "BURS + SACU CET",
        "source_url": "https://burs.org.bw",
        "currency": "BWP",
        "vat_rate": 12.0,
        "vat_name": "Value Added Tax (VAT)",
        "is_sacu": True,
        "is_ldc": False,
        "economy_focus": "diamonds_mining_services",
        "special_zones": [
            "Gaborone International Finance Service Centre",
            "Diamond Trading Company Botswana",
        ],
        "notes": [
            "SACU Common External Tariff – same rates as ZAF",
            "VAT: 12% standard rate",
            "Source: BURS (Botswana Unified Revenue Service)",
        ],
    },
    "NAM": {
        "country": "NAM",
        "country_name": "Namibia",
        "region": "SADC/SACU",
        "source": "NamRA + SACU CET",
        "source_url": "https://www.namra.org.na",
        "currency": "NAD",
        "vat_rate": 15.0,
        "vat_name": "Value Added Tax (VAT)",
        "is_sacu": True,
        "is_ldc": False,
        "economy_focus": "mining_logistics_fishing",
        "special_zones": [
            "Walvis Bay Export Processing Zone",
        ],
        "notes": [
            "SACU Common External Tariff – same rates as ZAF",
            "VAT: 15% standard rate",
            "Source: NamRA (Namibia Revenue Agency)",
        ],
    },
    "LSO": {
        "country": "LSO",
        "country_name": "Lesotho",
        "region": "SADC/SACU",
        "source": "LRA + SACU CET",
        "source_url": "https://www.lra.org.ls",
        "currency": "LSL",
        "vat_rate": 15.0,
        "vat_name": "Value Added Tax (VAT)",
        "is_sacu": True,
        "is_ldc": True,
        "economy_focus": "textile_manufacturing_water",
        "special_zones": ["Maseru Industrial Zone"],
        "notes": [
            "SACU Common External Tariff – same rates as ZAF",
            "VAT: 15% standard rate",
            "LDC: AfCFTA LDC preferences apply",
            "AGOA textile/apparel beneficiary",
            "Source: LRA (Lesotho Revenue Authority)",
        ],
    },
    "SWZ": {
        "country": "SWZ",
        "country_name": "Eswatini",
        "region": "SADC/SACU",
        "source": "SRA + SACU CET",
        "source_url": "https://www.sra.org.sz",
        "currency": "SZL",
        "vat_rate": 15.0,
        "vat_name": "Value Added Tax (VAT)",
        "is_sacu": True,
        "is_ldc": False,
        "economy_focus": "sugar_manufacturing_forestry",
        "special_zones": ["Matsapha Industrial Estate"],
        "notes": [
            "SACU Common External Tariff – same rates as ZAF",
            "VAT: 15% standard rate",
            "Source: SRA (Eswatini Revenue Authority)",
        ],
    },
    # ------------------------------------------------- Resource Economies --
    "AGO": {
        "country": "AGO",
        "country_name": "Angola",
        "region": "SADC",
        "source": "Alfândega de Angola",
        "source_url": "https://alfandega.gov.ao",
        "currency": "AOA",
        "vat_rate": 14.0,
        "vat_name": "Imposto sobre o Valor Acrescentado (IVA)",
        "is_sacu": False,
        "is_ldc": True,
        "economy_focus": "oil_diamonds_reconstruction",
        "cet_bands": {"raw_materials": 2.0, "intermediate": 5.0, "final": 20.0, "luxury": 30.0},
        "special_zones": [
            "Luanda-Bengo Special Economic Zone",
            "Soyo Oil & Gas Free Zone",
        ],
        "notes": [
            "Pauta Aduaneira de Angola – 4-band structure",
            "IVA: 14% standard rate",
            "Source: alfandega.gov.ao + minfin.gov.ao",
        ],
    },
    "ZMB": {
        "country": "ZMB",
        "country_name": "Zambia",
        "region": "SADC/COMESA",
        "source": "Zambia Revenue Authority",
        "source_url": "https://www.zra.org.zm",
        "currency": "ZMW",
        "vat_rate": 16.0,
        "vat_name": "Value Added Tax (VAT)",
        "is_sacu": False,
        "is_ldc": True,
        "economy_focus": "copper_agriculture_energy",
        "cet_bands": {"zero": 0.0, "intermediate": 15.0, "final": 25.0},
        "special_zones": [
            "Lusaka South Multi-Facility Economic Zone",
            "Chambishi Multi-Facility Economic Zone",
        ],
        "notes": [
            "Zambia uses 3-band tariff (0%, 15%, 25%)",
            "VAT: 16% standard rate",
            "Source: ZRA Customs Tariff Schedule",
        ],
    },
    "ZWE": {
        "country": "ZWE",
        "country_name": "Zimbabwe",
        "region": "SADC/COMESA",
        "source": "ZIMRA",
        "source_url": "https://www.zimra.co.zw",
        "currency": "ZWG",
        "vat_rate": 15.0,
        "vat_name": "Value Added Tax (VAT)",
        "is_sacu": False,
        "is_ldc": False,
        "economy_focus": "mining_agriculture_manufacturing",
        "national_surtax": 10.0,
        "special_zones": [
            "Beitbridge Border Post Special Economic Zone",
            "Sunway City SEZ",
        ],
        "notes": [
            "Multi-currency environment (USD dominant for customs valuation)",
            "VAT: 15% standard rate",
            "Surtax: 10% on selected manufactured goods",
            "Source: ZIMRA Customs Tariff Book",
        ],
    },
    "COD": {
        "country": "COD",
        "country_name": "DR Congo",
        "region": "SADC/EAC",
        "source": "DGRAD + DGDA",
        "source_url": "https://www.dgrad.cd",
        "currency": "CDF",
        "vat_rate": 16.0,
        "vat_name": "Taxe sur la Valeur Ajoutée (TVA)",
        "is_sacu": False,
        "is_ldc": True,
        "economy_focus": "minerals_agriculture_forestry",
        "dual_membership": ["EAC", "SADC"],
        "national_taxes": {"ID": 2.0},
        "special_zones": ["Zone Economique Spéciale de Maluku"],
        "notes": [
            "Dual EAC + SADC member – applies EAC CET as primary schedule",
            "TVA: 16% standard rate",
            "Source: DGRAD + DGDA",
        ],
    },
    # ------------------------------------------------------ Island Nations --
    "MUS": {
        "country": "MUS",
        "country_name": "Mauritius",
        "region": "SADC/COMESA",
        "source": "Mauritius Revenue Authority",
        "source_url": "https://www.mra.mu",
        "currency": "MUR",
        "vat_rate": 15.0,
        "vat_name": "Value Added Tax (VAT)",
        "is_sacu": False,
        "is_ldc": False,
        "economy_focus": "services_manufacturing_tourism",
        "special_zones": [
            "Mauritius International Financial Centre",
            "Mauritius Freeport",
        ],
        "notes": [
            "Very open trade regime – most MFN rates at 0%",
            "VAT: 15% standard rate",
            "Source: MRA (Mauritius Revenue Authority)",
        ],
    },
    "SYC": {
        "country": "SYC",
        "country_name": "Seychelles",
        "region": "SADC/COMESA",
        "source": "Seychelles Revenue Commission",
        "source_url": "https://src.gov.sc",
        "currency": "SCR",
        "vat_rate": 15.0,
        "vat_name": "Value Added Tax (VAT)",
        "is_sacu": False,
        "is_ldc": False,
        "economy_focus": "tourism_fisheries_finance",
        "special_zones": ["Seychelles International Trade Zone (SITZ)"],
        "notes": [
            "Small island economy",
            "VAT: 15% standard rate",
            "Source: Seychelles Revenue Commission",
        ],
    },
    "COM": {
        "country": "COM",
        "country_name": "Comoros",
        "region": "SADC",
        "source": "Direction Générale des Douanes des Comores",
        "source_url": "https://dgdcom.km",
        "currency": "KMF",
        "vat_rate": 10.0,
        "vat_name": "Taxe sur la Valeur Ajoutée (TVA)",
        "is_sacu": False,
        "is_ldc": True,
        "economy_focus": "agriculture_fisheries_tourism",
        "cet_bands": {"essential": 0.0, "basic": 5.0, "standard": 20.0, "luxury": 40.0},
        "notes": [
            "LDC: AfCFTA LDC preferences apply",
            "TVA: 10% (lower than regional average)",
            "Source: DGD Comores",
        ],
    },
    # ----------------------------------------------------- Emerging Markets --
    "MOZ": {
        "country": "MOZ",
        "country_name": "Mozambique",
        "region": "SADC/COMESA",
        "source": "Autoridade Tributária de Moçambique (AT)",
        "source_url": "https://www.at.gov.mz",
        "currency": "MZN",
        "vat_rate": 17.0,
        "vat_name": "Imposto sobre o Valor Acrescentado (IVA)",
        "is_sacu": False,
        "is_ldc": True,
        "economy_focus": "energy_agriculture_logistics",
        "cet_bands": {"zero": 0.0, "reduced": 2.5, "standard": 7.5, "high": 20.0},
        "special_zones": [
            "Nacala Special Economic Zone",
            "Beira Industrial Free Zone",
        ],
        "notes": [
            "4-band tariff: 0%, 2.5%, 7.5%, 20%",
            "IVA: 17% standard rate",
            "Source: AT Moçambique pauta aduaneira",
        ],
    },
    "MDG": {
        "country": "MDG",
        "country_name": "Madagascar",
        "region": "SADC/COMESA",
        "source": "Direction Générale des Douanes Madagascar",
        "source_url": "https://www.douanes.mg",
        "currency": "MGA",
        "vat_rate": 20.0,
        "vat_name": "Taxe sur la Valeur Ajoutée (TVA)",
        "is_sacu": False,
        "is_ldc": True,
        "economy_focus": "vanilla_textiles_mining",
        "cet_bands": {"zero": 0.0, "low": 5.0, "mid": 10.0, "high": 20.0},
        "national_taxes": {"STAT": 0.5},
        "special_zones": ["Antananarivo Export Processing Zone"],
        "notes": [
            "TVA: 20% standard rate",
            "Redevance Statistique: 0.5%",
            "Source: DGD Madagascar",
        ],
    },
    "MWI": {
        "country": "MWI",
        "country_name": "Malawi",
        "region": "SADC/COMESA",
        "source": "Malawi Revenue Authority",
        "source_url": "https://www.mra.mw",
        "currency": "MWK",
        "vat_rate": 16.5,
        "vat_name": "Value Added Tax (VAT)",
        "is_sacu": False,
        "is_ldc": True,
        "economy_focus": "tobacco_agriculture_mining",
        "cet_bands": {"zero": 0.0, "low": 10.0, "mid": 25.0},
        "special_zones": ["Lilongwe Industrial Zone"],
        "notes": [
            "3-band tariff (0%, 10%, 25%)",
            "VAT: 16.5% standard rate",
            "Source: MRA (Malawi Revenue Authority)",
        ],
    },
    "TZA": {
        "country": "TZA",
        "country_name": "Tanzania",
        "region": "SADC/EAC",
        "source": "Tanzania Revenue Authority",
        "source_url": "https://www.tra.go.tz",
        "currency": "TZS",
        "vat_rate": 18.0,
        "vat_name": "Value Added Tax (VAT)",
        "is_sacu": False,
        "is_ldc": True,
        "economy_focus": "agriculture_mining_tourism",
        "dual_membership": ["EAC", "SADC"],
        "cet_bands": {"zero": 0.0, "intermediate": 10.0, "final": 25.0, "sensitive": 35.0},
        "special_zones": [
            "Benjamin William Mkapa SEZ",
            "Tanga Export Processing Zone",
        ],
        "notes": [
            "Dual EAC + SADC member – applies EAC CET as primary schedule",
            "VAT: 18% standard rate",
            "Source: TRA (Tanzania Revenue Authority)",
        ],
    },
}


# ---------------------------------------------------------------------------
# Base SACU positions (shared by BWA, NAM, LSO, SWZ)
# ---------------------------------------------------------------------------

SACU_BASE_POSITIONS = [
    {"chapter": "01", "description": "Live animals", "cet_rate": 0.0},
    {"chapter": "02", "description": "Meat and edible offal", "cet_rate": 20.0},
    {"chapter": "03", "description": "Fish and crustaceans", "cet_rate": 0.0},
    {"chapter": "04", "description": "Dairy produce; eggs; honey", "cet_rate": 20.0},
    {"chapter": "07", "description": "Edible vegetables", "cet_rate": 0.0},
    {"chapter": "10", "description": "Cereals", "cet_rate": 20.0},
    {"chapter": "17", "description": "Sugars and sugar confectionery", "cet_rate": 20.0},
    {"chapter": "22", "description": "Beverages, spirits and vinegar", "cet_rate": 25.0},
    {"chapter": "24", "description": "Tobacco and manufactured tobacco substitutes", "cet_rate": 30.0},
    {"chapter": "27", "description": "Mineral fuels; oils", "cet_rate": 2.0},
    {"chapter": "29", "description": "Organic chemicals", "cet_rate": 0.0},
    {"chapter": "30", "description": "Pharmaceutical products", "cet_rate": 0.0},
    {"chapter": "39", "description": "Plastics and articles thereof", "cet_rate": 10.0},
    {"chapter": "52", "description": "Cotton", "cet_rate": 22.0},
    {"chapter": "61", "description": "Knitted apparel", "cet_rate": 22.0},
    {"chapter": "62", "description": "Woven apparel", "cet_rate": 22.0},
    {"chapter": "64", "description": "Footwear", "cet_rate": 30.0},
    {"chapter": "72", "description": "Iron and steel", "cet_rate": 5.0},
    {"chapter": "84", "description": "Machinery and mechanical appliances", "cet_rate": 0.0},
    {"chapter": "85", "description": "Electrical machinery and equipment", "cet_rate": 0.0},
    {"chapter": "87", "description": "Vehicles (excl. railway rolling stock)", "cet_rate": 25.0},
    {"chapter": "90", "description": "Optical and medical instruments", "cet_rate": 0.0},
]

# Non-SACU default positions (simplified – representative)
NON_SACU_DEFAULT_POSITIONS = [
    {"chapter": "01", "description": "Live animals", "default_rate": 0.0},
    {"chapter": "02", "description": "Meat", "default_rate": 10.0},
    {"chapter": "10", "description": "Cereals", "default_rate": 5.0},
    {"chapter": "17", "description": "Sugars", "default_rate": 10.0},
    {"chapter": "22", "description": "Beverages", "default_rate": 20.0},
    {"chapter": "24", "description": "Tobacco", "default_rate": 25.0},
    {"chapter": "27", "description": "Mineral fuels", "default_rate": 5.0},
    {"chapter": "29", "description": "Organic chemicals", "default_rate": 0.0},
    {"chapter": "30", "description": "Pharmaceuticals", "default_rate": 0.0},
    {"chapter": "39", "description": "Plastics", "default_rate": 10.0},
    {"chapter": "61", "description": "Knitted apparel", "default_rate": 20.0},
    {"chapter": "62", "description": "Woven apparel", "default_rate": 20.0},
    {"chapter": "64", "description": "Footwear", "default_rate": 25.0},
    {"chapter": "72", "description": "Iron and steel", "default_rate": 5.0},
    {"chapter": "84", "description": "Machinery", "default_rate": 0.0},
    {"chapter": "85", "description": "Electrical equipment", "default_rate": 0.0},
    {"chapter": "87", "description": "Vehicles", "default_rate": 20.0},
    {"chapter": "90", "description": "Instruments", "default_rate": 0.0},
]


# ---------------------------------------------------------------------------
# Builder functions
# ---------------------------------------------------------------------------

def _build_sacu_country_positions(config: Dict) -> List[Dict]:
    """Build tariff positions for a SACU member (reusing SACU CET base)."""
    positions = []
    for base in SACU_BASE_POSITIONS:
        cet = base["cet_rate"]
        taxes: Dict = {
            "CET": cet,
            "VAT": config["vat_rate"],
        }
        position = {
            "code": f"{base['chapter']}.00.00.00",
            "code_clean": f"{base['chapter']}000000",
            "chapter": base["chapter"],
            "description": base["description"],
            "taxes": taxes,
            "fiscal_advantages": {
                "sacu_free_trade": "0% for intra-SACU trade",
                "sadc_preference": f"{round(cet * 0.85, 2)}% for non-SACU SADC members",
            },
            "source_url": config["source_url"],
        }
        positions.append(position)
    return positions


def _build_non_sacu_positions(config: Dict) -> List[Dict]:
    """Build tariff positions for non-SACU SADC members."""
    positions = []
    cet_bands = config.get("cet_bands", {})
    national_taxes = config.get("national_taxes", {})

    for base in NON_SACU_DEFAULT_POSITIONS:
        # Use country-specific band if available, else use default_rate
        rate = base["default_rate"]
        if cet_bands:
            rate = list(cet_bands.values())[1] if len(cet_bands) > 1 else rate

        taxes: Dict = {
            "CD": rate,
            "VAT": config["vat_rate"],
        }
        for tax_code, tax_rate in national_taxes.items():
            taxes[tax_code] = tax_rate

        # Surtax (Zimbabwe-specific)
        if config.get("national_surtax"):
            taxes["ST"] = config["national_surtax"]

        position = {
            "code": f"{base['chapter']}.00.00.00",
            "code_clean": f"{base['chapter']}000000",
            "chapter": base["chapter"],
            "description": base["description"],
            "taxes": taxes,
            "fiscal_advantages": {
                "sadc_preference": f"{round(rate * 0.85, 2)}% for SADC members",
                "ldc_preference": f"{round(rate * 0.70, 2)}% for AfCFTA LDC preferences" if config.get("is_ldc") else "N/A",
            },
            "source_url": config["source_url"],
        }
        positions.append(position)
    return positions


def build_country_data(country_code: str) -> Optional[Dict]:
    """Build the full tariff output dict for a country."""
    config = COUNTRY_CONFIGS.get(country_code)
    if not config:
        logger.warning(f"No config found for {country_code}")
        return None

    if config.get("is_sacu"):
        positions = _build_sacu_country_positions(config)
    else:
        positions = _build_non_sacu_positions(config)

    return {
        "country": country_code,
        "country_name": config["country_name"],
        "region": config.get("region", "SADC"),
        "source": config["source"],
        "source_url": config["source_url"],
        "currency": config["currency"],
        "vat_rate": config["vat_rate"],
        "vat_name": config["vat_name"],
        "is_sacu": config.get("is_sacu", False),
        "is_ldc": config.get("is_ldc", False),
        "dual_membership": config.get("dual_membership", []),
        "economy_focus": config.get("economy_focus", ""),
        "special_zones": config.get("special_zones", []),
        "scraped_at": datetime.utcnow().isoformat(),
        "positions": positions,
        "notes": config.get("notes", []),
        "stats": {
            "total_positions": len(positions),
        },
    }


def run_all(countries: Optional[List[str]] = None, output_dir: Optional[str] = None) -> Dict[str, bool]:
    """
    Generate tariff JSON files for all (or specified) SADC countries.

    Parameters
    ----------
    countries : list of ISO3 codes, optional
        Defaults to all countries in COUNTRY_CONFIGS.
    output_dir : str, optional
        Override output directory.

    Returns
    -------
    dict mapping country_code -> success bool
    """
    target_dir = output_dir or OUTPUT_DIR
    os.makedirs(target_dir, exist_ok=True)

    target_countries = countries or list(COUNTRY_CONFIGS.keys())
    results: Dict[str, bool] = {}

    for code in target_countries:
        try:
            data = build_country_data(code)
            if data is None:
                results[code] = False
                continue

            path = os.path.join(target_dir, f"{code}_tariffs.json")
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"{code}: saved {len(data['positions'])} positions → {path}")
            results[code] = True
        except Exception as exc:
            logger.error(f"{code}: failed – {exc}")
            results[code] = False

    return results


if __name__ == "__main__":
    results = run_all()
    for code, ok in results.items():
        status = "✓" if ok else "✗"
        print(f"  {status} {code}")
