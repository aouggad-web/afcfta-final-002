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
    run_scraper()
    import sys
    countries_arg = sys.argv[1:] if len(sys.argv) > 1 else None
    run_scraper(countries=countries_arg)
