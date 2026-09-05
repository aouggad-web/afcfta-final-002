"""
Complete registry of all 54 African countries with their customs data configurations.

This module provides comprehensive configuration data for all African countries including:
- Country codes (ISO2, ISO3)
- Regional classifications
- Regional economic blocks (ECOWAS, CEMAC, EAC, SACU, etc.)
- VAT rates and tax information
- Customs website URLs
- Priority levels for crawling
- Data source configurations

Last updated: February 2025
"""

from enum import Enum
from typing import Any, Dict, List, Optional


class Region(str, Enum):
    """African regions classification"""

    NORTH_AFRICA = "North Africa"
    WEST_AFRICA = "West Africa"
    CENTRAL_AFRICA = "Central Africa"
    EAST_AFRICA = "East Africa"
    SOUTHERN_AFRICA = "Southern Africa"


class RegionalBlock(str, Enum):
    """African regional economic communities"""

    ECOWAS = "ECOWAS"  # Economic Community of West African States
    CEDEAO = "CEDEAO"  # Same as ECOWAS (French)
    UEMOA = "UEMOA"  # West African Economic and Monetary Union
    CEMAC = "CEMAC"  # Economic and Monetary Community of Central Africa
    EAC = "EAC"  # East African Community
    SACU = "SACU"  # Southern African Customs Union
    SADC = "SADC"  # Southern African Development Community
    COMESA = "COMESA"  # Common Market for Eastern and Southern Africa
    AMU = "AMU"  # Arab Maghreb Union
    ECCAS = "ECCAS"  # Economic Community of Central African States
    IGAD = "IGAD"  # Intergovernmental Authority on Development


class Priority(int, Enum):
    """Priority levels for crawling (1=highest, 3=lowest)"""

    HIGH = 1  # Major economies, good data availability
    MEDIUM = 2  # Medium economies or partial data
    LOW = 3  # Small economies or limited data availability


class CustomsPlatform(str, Enum):
    """
    Customs management software / clearance platform used by each country's
    customs administration.

    Note: IMPDEC/VETCERT/PHYTOCERT/… formality codes in africa_formalities.py are
    UNCTAD NTM-aligned functional codes describing the TYPE of document required.
    They are platform-agnostic and do NOT imply the country uses ASYCUDA.
    """

    ASYCUDA_WORLD = "ASYCUDA World"  # UNCTAD ASYCUDA World (most common)
    ASYCUDA_PP = "ASYCUDA++"  # Older ASYCUDA++ (some legacy installs)
    GCNET = "GCNET"  # Ghana Community Network (Ghana Revenue Authority)
    NICIS = "NICIS/CuCMS"  # Nigeria Customs Integrated System (NCS)
    ICMS = "iCMS"  # Integrated Customs Mgmt System (Kenya, KRA)
    SIMBA = "SIMBA"  # Single Import Billing Manifest & Assessment (Tanzania)
    BADR = "BADR"  # Base Automatisée des Douanes en Réseau (Morocco)
    SINDA = "SINDA"  # Système Informatique des Douanes (Tunisia)
    NAFEZA = "NAFEZA"  # National Single Window (Egypt)
    ECTS = "ECTS"  # Ethiopian Customs Tax System (Ethiopia ECC)
    TRADENET = "TradeNet"  # TradeNet / TradeLinkMU (Mauritius)
    SARS_EDI = "SARS EDI"  # South Africa Revenue Service EDI/RAS
    GAINDE = "GAINDE"  # Guichet Automatisé d'Info. pour le Négoce (Senegal)
    SYDONIA = "SYDONIA/ASYCUDA"  # SYDONIA (DRC — ASYCUDA-derived variant)
    UNKNOWN = "Unknown"  # Limited digitization / data unavailable


# =============================================================================
# CUSTOMS PLATFORM INFORMATION
# Reference data for each platform: vendor, deployment countries, notes.
# =============================================================================

CUSTOMS_PLATFORM_INFO: Dict[str, Dict] = {
    "ASYCUDA World": {
        "vendor": "UNCTAD (United Nations Conference on Trade and Development)",
        "url": "https://asycuda.org",
        "decl_form_en": "Customs Declaration (SAD — Single Administrative Document)",
        "decl_form_fr": "Déclaration en Douane (DAU — Document Administratif Unique)",
        "notes": "Most widely deployed customs platform in Africa. Used by 30+ AU members.",
    },
    "ASYCUDA++": {
        "vendor": "UNCTAD",
        "url": "https://asycuda.org",
        "decl_form_en": "Customs Declaration (SAD — Single Administrative Document)",
        "decl_form_fr": "Déclaration en Douane (DAU — Document Administratif Unique)",
        "notes": "Legacy version; most countries have migrated or are migrating to ASYCUDA World.",
    },
    "GCNET": {
        "vendor": "GCNet (Ghana Community Network Services Ltd) / GRA",
        "url": "https://www.gra.gov.gh",
        "decl_form_en": "Customs Declaration Form (CUSDEC)",
        "decl_form_fr": "Déclaration en Douane (CUSDEC)",
        "notes": "Ghana-specific customs and port management platform. Interfaces with ASYCUDA "
        "but is a separate national system.",
    },
    "NICIS/CuCMS": {
        "vendor": "Nigeria Customs Service (NCS) / in-house / WIPRO",
        "url": "https://www.customs.gov.ng",
        "decl_form_en": "Single Goods Declaration (SGD)",
        "decl_form_fr": "Déclaration Unique de Marchandises (SGD)",
        "notes": "Nigeria Customs Integrated System (NICIS II), now migrating to CuCMS. "
        "Replaced manual processing; separate from ASYCUDA.",
    },
    "iCMS": {
        "vendor": "Kenya Revenue Authority (KRA) / in-house",
        "url": "https://www.kra.go.ke",
        "decl_form_en": "Import Declaration Form (IDF)",
        "decl_form_fr": "Formulaire de Déclaration d'Importation (IDF)",
        "notes": "Integrated Customs Management System. Replaced SIMBA in Kenya in 2022. "
        "End-to-end digitized process.",
    },
    "SIMBA": {
        "vendor": "Tanzania Revenue Authority (TRA) / WiseTech Global (CargoWise)",
        "url": "https://www.tra.go.tz",
        "decl_form_en": "Customs Entry / Customs Declaration (TANCIS)",
        "decl_form_fr": "Déclaration en Douane (TANCIS)",
        "notes": "Single Import Billing, Manifest and Assessment system. Tanzania-specific. "
        "Not ASYCUDA.",
    },
    "BADR": {
        "vendor": "Administration des Douanes et Impôts Indirects (ADII) / in-house",
        "url": "https://www.douane.gov.ma",
        "decl_form_en": "Customs Declaration — DUM (Déclaration Unique de Marchandises)",
        "decl_form_fr": "Déclaration Unique de Marchandises (DUM) — BADR",
        "notes": "Base Automatisée des Douanes en Réseau. Morocco's fully national customs "
        "platform; uses national codes C01-C11, 910 etc. Not ASYCUDA.",
    },
    "SINDA": {
        "vendor": "Direction Générale des Douanes (DGD-TN) / in-house (ASYCUDA-derived)",
        "url": "https://www.douane.finances.tn",
        "decl_form_en": "Customs Declaration — DUM (Déclaration Unique de Marchandises) via SINDA",
        "decl_form_fr": "Déclaration Unique de Marchandises (DUM) — SINDA / GUCE",
        "notes": "Système Informatique des Douanes et Accises. Evolved from ASYCUDA++ "
        "with heavy Tunisian customisation; uses national codes 910, 101-109 etc.",
    },
    "NAFEZA": {
        "vendor": "Egyptian Customs Authority (ECA) / Misr Technology Services",
        "url": "https://www.nafeza.gov.eg",
        "decl_form_en": "Electronic Import Notice (EIN) + Customs Declaration via ACS",
        "decl_form_fr": "Avis d'Importation Électronique (EIN) + Déclaration Douanière via ACS",
        "notes": "National Single Window for Foreign Trade Facilitation. Integrated "
        "with GOEIC, ACS and bank channels. Mandatory for all shipments to Egypt "
        "since 2022.",
    },
    "ECTS": {
        "vendor": "Ethiopian Customs Commission (ECC) / in-house",
        "url": "https://www.customs.gov.et",
        "decl_form_en": "Customs Declaration (CD) — Ethiopian Customs Tax System (ECTS)",
        "decl_form_fr": "Déclaration en Douane (CD) — Système ECTS",
        "notes": "Ethiopian Customs Tax System. National platform; not ASYCUDA World. "
        "Uses ETHPERMIT (MoTRI) as a mandatory pre-clearance step.",
    },
    "TradeNet": {
        "vendor": "Mauritius Network Services (MNS) / TradeLinkMU",
        "url": "https://www.tradenet.intnet.mu",
        "decl_form_en": "Import Declaration (TradeNet / TradeLinkMU)",
        "decl_form_fr": "Déclaration d'Importation (TradeNet / TradeLinkMU)",
        "notes": "Mauritius TradeNet (now TradeLinkMU). Single-window platform covering "
        "customs, port, and regulatory agencies. Interfaces with ASYCUDA++.",
    },
    "SARS EDI": {
        "vendor": "South African Revenue Service (SARS) / in-house",
        "url": "https://www.sars.gov.za",
        "decl_form_en": "Bill of Entry (DA 306 / DA 306A) — SARS eFiling",
        "decl_form_fr": "Déclaration en Douane (DA 306 / DA 306A) — SARS eFiling",
        "notes": "SARS Customs EDI / Risk Assessment System (RAS). South Africa's fully "
        "national customs platform; not ASYCUDA.",
    },
    "GAINDE": {
        "vendor": "GAINDE 2000 (GIE Douanes-Secteur Privé) / Senegal",
        "url": "https://www.gainde2000.sn",
        "decl_form_en": "Customs Declaration (Déclaration en Douane) via GAINDE 2000",
        "decl_form_fr": "Déclaration en Douane — Guichet GAINDE 2000",
        "notes": "Guichet Automatisé d'Information pour le Négoce et le Dédouanement "
        "des Exportateurs. Senegal's single-window platform; interfaces with "
        "ASYCUDA World (GAINDE 2000 acts as front-end).",
    },
    "SYDONIA/ASYCUDA": {
        "vendor": "UNCTAD / DGDA DRC (adapted)",
        "url": "https://www.douanes.cd",
        "decl_form_en": "Customs Declaration (SYDONIA / ASYCUDA-DRC)",
        "decl_form_fr": "Déclaration en Douane (SYDONIA / ASYCUDA-RDC)",
        "notes": "DRC uses a heavily customised ASYCUDA-derived system (historically called "
        "SYDONIA). OCC integration is unique to DRC (OCCDECL mandatory for all imports).",
    },
    "Unknown": {
        "vendor": "N/A",
        "url": None,
        "decl_form_en": "Import Declaration",
        "decl_form_fr": "Déclaration d'Importation",
        "notes": "Customs management platform not confirmed / limited digitization.",
    },
}


# Complete registry of all 54 African countries
AFRICAN_COUNTRIES_REGISTRY: Dict[str, Dict[str, Any]] = {
    "DZA": {
        "iso2": "DZ",
        "iso3": "DZA",
        "name_en": "Algeria",
        "name_fr": "Algérie",
        "region": Region.NORTH_AFRICA,
        "blocks": [RegionalBlock.AMU],
        "vat_rate": 19.0,
        "customs_url": "https://www.douane.gov.dz",
        "priority": Priority.HIGH,
        "languages": ["fr", "ar"],
        "notes": "Major economy, oil/gas exporter",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "AGO": {
        "iso2": "AO",
        "iso3": "AGO",
        "name_en": "Angola",
        "name_fr": "Angola",
        "region": Region.SOUTHERN_AFRICA,
        "blocks": [RegionalBlock.SADC, RegionalBlock.ECCAS],
        "vat_rate": 14.0,
        "customs_url": "https://www.agtsaduaneiro.ao",
        "priority": Priority.HIGH,
        "languages": ["pt"],
        "notes": "Oil exporter, SADC member",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "BEN": {
        "iso2": "BJ",
        "iso3": "BEN",
        "name_en": "Benin",
        "name_fr": "Bénin",
        "region": Region.WEST_AFRICA,
        "blocks": [RegionalBlock.ECOWAS, RegionalBlock.UEMOA],
        "vat_rate": 18.0,
        "customs_url": "https://www.douanes.bj",
        "priority": Priority.HIGH,
        "languages": ["fr"],
        "notes": "UEMOA member, Cotonou port hub",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "BWA": {
        "iso2": "BW",
        "iso3": "BWA",
        "name_en": "Botswana",
        "name_fr": "Botswana",
        "region": Region.SOUTHERN_AFRICA,
        "blocks": [RegionalBlock.SACU, RegionalBlock.SADC],
        "vat_rate": 14.0,
        "customs_url": "https://www.burs.org.bw",
        "priority": Priority.MEDIUM,
        "languages": ["en"],
        "notes": "SACU member, stable economy",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "BFA": {
        "iso2": "BF",
        "iso3": "BFA",
        "name_en": "Burkina Faso",
        "name_fr": "Burkina Faso",
        "region": Region.WEST_AFRICA,
        "blocks": [RegionalBlock.ECOWAS, RegionalBlock.UEMOA],
        "vat_rate": 18.0,
        "customs_url": "https://www.douanes.gov.bf",
        "priority": Priority.MEDIUM,
        "languages": ["fr"],
        "notes": "UEMOA member, landlocked",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "BDI": {
        "iso2": "BI",
        "iso3": "BDI",
        "name_en": "Burundi",
        "name_fr": "Burundi",
        "region": Region.EAST_AFRICA,
        "blocks": [RegionalBlock.EAC, RegionalBlock.COMESA],
        "vat_rate": 18.0,
        "customs_url": "https://www.obr.bi",
        "priority": Priority.LOW,
        "languages": ["fr", "en"],
        "notes": "EAC member, landlocked",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "CPV": {
        "iso2": "CV",
        "iso3": "CPV",
        "name_en": "Cape Verde",
        "name_fr": "Cap-Vert",
        "region": Region.WEST_AFRICA,
        "blocks": [RegionalBlock.ECOWAS],
        "vat_rate": 15.0,
        "customs_url": "https://www.dnre.cv",
        "priority": Priority.LOW,
        "languages": ["pt"],
        "notes": "Island nation, ECOWAS member",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "CMR": {
        "iso2": "CM",
        "iso3": "CMR",
        "name_en": "Cameroon",
        "name_fr": "Cameroun",
        "region": Region.CENTRAL_AFRICA,
        "blocks": [RegionalBlock.CEMAC, RegionalBlock.ECCAS],
        "vat_rate": 19.25,
        "customs_url": "https://www.douanes.cm",
        "priority": Priority.HIGH,
        "languages": ["fr", "en"],
        "notes": "CEMAC member, Douala port",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "CAF": {
        "iso2": "CF",
        "iso3": "CAF",
        "name_en": "Central African Republic",
        "name_fr": "République Centrafricaine",
        "region": Region.CENTRAL_AFRICA,
        "blocks": [RegionalBlock.CEMAC, RegionalBlock.ECCAS],
        "vat_rate": 19.0,
        "customs_url": "https://www.douanes.cf",
        "priority": Priority.LOW,
        "languages": ["fr"],
        "notes": "CEMAC member, landlocked",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "TCD": {
        "iso2": "TD",
        "iso3": "TCD",
        "name_en": "Chad",
        "name_fr": "Tchad",
        "region": Region.CENTRAL_AFRICA,
        "blocks": [RegionalBlock.CEMAC, RegionalBlock.ECCAS],
        "vat_rate": 18.0,
        "customs_url": "https://www.douanes.td",
        "priority": Priority.MEDIUM,
        "languages": ["fr", "ar"],
        "notes": "CEMAC member, landlocked, oil producer",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "COM": {
        "iso2": "KM",
        "iso3": "COM",
        "name_en": "Comoros",
        "name_fr": "Comores",
        "region": Region.EAST_AFRICA,
        "blocks": [RegionalBlock.COMESA],
        "vat_rate": 10.0,
        "customs_url": "https://www.douanes.km",
        "priority": Priority.LOW,
        "languages": ["fr", "ar"],
        "notes": "Island nation, COMESA member",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "COG": {
        "iso2": "CG",
        "iso3": "COG",
        "name_en": "Republic of the Congo",
        "name_fr": "République du Congo",
        "region": Region.CENTRAL_AFRICA,
        "blocks": [RegionalBlock.CEMAC, RegionalBlock.ECCAS],
        "vat_rate": 18.0,
        "customs_url": "https://www.douanes.cg",
        "priority": Priority.MEDIUM,
        "languages": ["fr"],
        "notes": "CEMAC member, Pointe-Noire port",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "COD": {
        "iso2": "CD",
        "iso3": "COD",
        "name_en": "Democratic Republic of the Congo",
        "name_fr": "République Démocratique du Congo",
        "region": Region.CENTRAL_AFRICA,
        "blocks": [RegionalBlock.SADC, RegionalBlock.COMESA, RegionalBlock.ECCAS],
        "vat_rate": 16.0,
        "customs_url": "https://www.dgda.cd",
        "priority": Priority.HIGH,
        "languages": ["fr"],
        "notes": "Large economy, mineral resources",
        "customs_platform": CustomsPlatform.SYDONIA,
    },
    "CIV": {
        "iso2": "CI",
        "iso3": "CIV",
        "name_en": "Ivory Coast",
        "name_fr": "Côte d'Ivoire",
        "region": Region.WEST_AFRICA,
        "blocks": [RegionalBlock.ECOWAS, RegionalBlock.UEMOA],
        "vat_rate": 18.0,
        "customs_url": "https://www.douanes.ci",
        "priority": Priority.HIGH,
        "languages": ["fr"],
        "notes": "UEMOA member, Abidjan port hub",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "DJI": {
        "iso2": "DJ",
        "iso3": "DJI",
        "name_en": "Djibouti",
        "name_fr": "Djibouti",
        "region": Region.EAST_AFRICA,
        "blocks": [RegionalBlock.COMESA, RegionalBlock.IGAD],
        "vat_rate": 10.0,
        "customs_url": "https://www.douane.dj",
        "priority": Priority.MEDIUM,
        "languages": ["fr", "ar"],
        "notes": "Strategic port for Ethiopia trade",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "EGY": {
        "iso2": "EG",
        "iso3": "EGY",
        "name_en": "Egypt",
        "name_fr": "Égypte",
        "region": Region.NORTH_AFRICA,
        "blocks": [RegionalBlock.COMESA, RegionalBlock.AMU],
        "vat_rate": 14.0,
        "customs_url": "https://www.customs.gov.eg",
        "priority": Priority.HIGH,
        "languages": ["ar", "en"],
        "notes": "Largest North African economy",
        "customs_platform": CustomsPlatform.NAFEZA,
    },
    "GNQ": {
        "iso2": "GQ",
        "iso3": "GNQ",
        "name_en": "Equatorial Guinea",
        "name_fr": "Guinée Équatoriale",
        "region": Region.CENTRAL_AFRICA,
        "blocks": [RegionalBlock.CEMAC, RegionalBlock.ECCAS],
        "vat_rate": 15.0,
        "customs_url": "https://www.douanes.gq",
        "priority": Priority.LOW,
        "languages": ["es", "fr"],
        "notes": "CEMAC member, oil producer",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "ERI": {
        "iso2": "ER",
        "iso3": "ERI",
        "name_en": "Eritrea",
        "name_fr": "Érythrée",
        "region": Region.EAST_AFRICA,
        "blocks": [RegionalBlock.COMESA, RegionalBlock.IGAD],
        "vat_rate": 5.0,
        "customs_url": "https://www.customs.gov.er",
        "priority": Priority.LOW,
        "languages": ["ar", "en"],
        "notes": "Limited data availability",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "SWZ": {
        "iso2": "SZ",
        "iso3": "SWZ",
        "name_en": "Eswatini",
        "name_fr": "Eswatini",
        "region": Region.SOUTHERN_AFRICA,
        "blocks": [RegionalBlock.SACU, RegionalBlock.SADC],
        "vat_rate": 15.0,
        "customs_url": "https://www.sra.org.sz",
        "priority": Priority.LOW,
        "languages": ["en"],
        "notes": "SACU member, formerly Swaziland",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "ETH": {
        "iso2": "ET",
        "iso3": "ETH",
        "name_en": "Ethiopia",
        "name_fr": "Éthiopie",
        "region": Region.EAST_AFRICA,
        "blocks": [RegionalBlock.COMESA, RegionalBlock.IGAD],
        "vat_rate": 15.0,
        "customs_url": "https://www.erca.gov.et",
        "priority": Priority.HIGH,
        "languages": ["am", "en"],
        "notes": "Large economy, landlocked",
        "customs_platform": CustomsPlatform.ECTS,
    },
    "GAB": {
        "iso2": "GA",
        "iso3": "GAB",
        "name_en": "Gabon",
        "name_fr": "Gabon",
        "region": Region.CENTRAL_AFRICA,
        "blocks": [RegionalBlock.CEMAC, RegionalBlock.ECCAS],
        "vat_rate": 18.0,
        "customs_url": "https://www.douanes.ga",
        "priority": Priority.MEDIUM,
        "languages": ["fr"],
        "notes": "CEMAC member, oil producer",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "GMB": {
        "iso2": "GM",
        "iso3": "GMB",
        "name_en": "Gambia",
        "name_fr": "Gambie",
        "region": Region.WEST_AFRICA,
        "blocks": [RegionalBlock.ECOWAS],
        "vat_rate": 15.0,
        "customs_url": "https://www.gra.gm",
        "priority": Priority.LOW,
        "languages": ["en"],
        "notes": "ECOWAS member, small economy",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "GHA": {
        "iso2": "GH",
        "iso3": "GHA",
        "name_en": "Ghana",
        "name_fr": "Ghana",
        "region": Region.WEST_AFRICA,
        "blocks": [RegionalBlock.ECOWAS],
        "vat_rate": 15.0,
        "customs_url": "https://www.gra.gov.gh",
        "priority": Priority.HIGH,
        "languages": ["en"],
        "notes": "ECOWAS member, Tema port",
        "customs_platform": CustomsPlatform.GCNET,
    },
    "GIN": {
        "iso2": "GN",
        "iso3": "GIN",
        "name_en": "Guinea",
        "name_fr": "Guinée",
        "region": Region.WEST_AFRICA,
        "blocks": [RegionalBlock.ECOWAS],
        "vat_rate": 18.0,
        "customs_url": "https://www.douanes.gov.gn",
        "priority": Priority.MEDIUM,
        "languages": ["fr"],
        "notes": "ECOWAS member, bauxite/mining",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "GNB": {
        "iso2": "GW",
        "iso3": "GNB",
        "name_en": "Guinea-Bissau",
        "name_fr": "Guinée-Bissau",
        "region": Region.WEST_AFRICA,
        "blocks": [RegionalBlock.ECOWAS, RegionalBlock.UEMOA],
        "vat_rate": 17.0,
        "customs_url": "https://www.alfandegas.gw",
        "priority": Priority.LOW,
        "languages": ["pt"],
        "notes": "UEMOA member, small economy",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "KEN": {
        "iso2": "KE",
        "iso3": "KEN",
        "name_en": "Kenya",
        "name_fr": "Kenya",
        "region": Region.EAST_AFRICA,
        "blocks": [RegionalBlock.EAC, RegionalBlock.COMESA, RegionalBlock.IGAD],
        "vat_rate": 16.0,
        "customs_url": "https://www.kra.go.ke",
        "priority": Priority.HIGH,
        "languages": ["en", "sw"],
        "notes": "EAC hub, Mombasa port",
        "customs_platform": CustomsPlatform.ICMS,
    },
    "LSO": {
        "iso2": "LS",
        "iso3": "LSO",
        "name_en": "Lesotho",
        "name_fr": "Lesotho",
        "region": Region.SOUTHERN_AFRICA,
        "blocks": [RegionalBlock.SACU, RegionalBlock.SADC],
        "vat_rate": 15.0,
        "customs_url": "https://www.lra.org.ls",
        "priority": Priority.LOW,
        "languages": ["en"],
        "notes": "SACU member, landlocked",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "LBR": {
        "iso2": "LR",
        "iso3": "LBR",
        "name_en": "Liberia",
        "name_fr": "Libéria",
        "region": Region.WEST_AFRICA,
        "blocks": [RegionalBlock.ECOWAS],
        "vat_rate": 10.0,
        "customs_url": "https://www.lra.gov.lr",
        "priority": Priority.MEDIUM,
        "languages": ["en"],
        "notes": "ECOWAS member, Monrovia port",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "LBY": {
        "iso2": "LY",
        "iso3": "LBY",
        "name_en": "Libya",
        "name_fr": "Libye",
        "region": Region.NORTH_AFRICA,
        "blocks": [RegionalBlock.AMU],
        "vat_rate": 0.0,
        "customs_url": "https://www.customs.gov.ly",
        "priority": Priority.LOW,
        "languages": ["ar"],
        "notes": "No VAT, oil producer, unstable",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "MDG": {
        "iso2": "MG",
        "iso3": "MDG",
        "name_en": "Madagascar",
        "name_fr": "Madagascar",
        "region": Region.EAST_AFRICA,
        "blocks": [RegionalBlock.SADC, RegionalBlock.COMESA],
        "vat_rate": 20.0,
        "customs_url": "https://www.douanes.gov.mg",
        "priority": Priority.MEDIUM,
        "languages": ["fr", "mg"],
        "notes": "Island nation, SADC member",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "MWI": {
        "iso2": "MW",
        "iso3": "MWI",
        "name_en": "Malawi",
        "name_fr": "Malawi",
        "region": Region.SOUTHERN_AFRICA,
        "blocks": [RegionalBlock.SADC, RegionalBlock.COMESA],
        "vat_rate": 16.5,
        "customs_url": "https://www.mra.mw",
        "priority": Priority.LOW,
        "languages": ["en"],
        "notes": "SADC member, landlocked",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "MLI": {
        "iso2": "ML",
        "iso3": "MLI",
        "name_en": "Mali",
        "name_fr": "Mali",
        "region": Region.WEST_AFRICA,
        "blocks": [RegionalBlock.ECOWAS, RegionalBlock.UEMOA],
        "vat_rate": 18.0,
        "customs_url": "https://www.douanes.gouv.ml",
        "priority": Priority.MEDIUM,
        "languages": ["fr"],
        "notes": "UEMOA member, landlocked",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "MRT": {
        "iso2": "MR",
        "iso3": "MRT",
        "name_en": "Mauritania",
        "name_fr": "Mauritanie",
        "region": Region.WEST_AFRICA,
        "blocks": [RegionalBlock.AMU],
        "vat_rate": 16.0,
        "customs_url": "https://www.douanes.gov.mr",
        "priority": Priority.MEDIUM,
        "languages": ["ar", "fr"],
        "notes": "AMU member, mining/fishing",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "MUS": {
        "iso2": "MU",
        "iso3": "MUS",
        "name_en": "Mauritius",
        "name_fr": "Maurice",
        "region": Region.EAST_AFRICA,
        "blocks": [RegionalBlock.SADC, RegionalBlock.COMESA],
        "vat_rate": 15.0,
        "customs_url": "https://www.mra.mu",
        "priority": Priority.HIGH,
        "languages": ["en", "fr"],
        "notes": "Island nation, financial hub",
        "customs_platform": CustomsPlatform.TRADENET,
    },
    "MAR": {
        "iso2": "MA",
        "iso3": "MAR",
        "name_en": "Morocco",
        "name_fr": "Maroc",
        "region": Region.NORTH_AFRICA,
        "blocks": [RegionalBlock.AMU],
        "vat_rate": 20.0,
        "customs_url": "https://www.douane.gov.ma",
        "priority": Priority.HIGH,
        "languages": ["ar", "fr"],
        "notes": "Major economy, Casablanca/Tangier ports",
        "customs_platform": CustomsPlatform.BADR,
    },
    "MOZ": {
        "iso2": "MZ",
        "iso3": "MOZ",
        "name_en": "Mozambique",
        "name_fr": "Mozambique",
        "region": Region.SOUTHERN_AFRICA,
        "blocks": [RegionalBlock.SADC],
        "vat_rate": 17.0,
        "customs_url": "https://www.at.gov.mz",
        "priority": Priority.MEDIUM,
        "languages": ["pt"],
        "notes": "SADC member, Maputo port",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "NAM": {
        "iso2": "NA",
        "iso3": "NAM",
        "name_en": "Namibia",
        "name_fr": "Namibie",
        "region": Region.SOUTHERN_AFRICA,
        "blocks": [RegionalBlock.SACU, RegionalBlock.SADC],
        "vat_rate": 15.0,
        "customs_url": "https://www.customs.gov.na",
        "priority": Priority.MEDIUM,
        "languages": ["en"],
        "notes": "SACU member, Walvis Bay port",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "NER": {
        "iso2": "NE",
        "iso3": "NER",
        "name_en": "Niger",
        "name_fr": "Niger",
        "region": Region.WEST_AFRICA,
        "blocks": [RegionalBlock.ECOWAS, RegionalBlock.UEMOA],
        "vat_rate": 19.0,
        "customs_url": "https://www.douanes.ne",
        "priority": Priority.MEDIUM,
        "languages": ["fr"],
        "notes": "UEMOA member, landlocked",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "NGA": {
        "iso2": "NG",
        "iso3": "NGA",
        "name_en": "Nigeria",
        "name_fr": "Nigéria",
        "region": Region.WEST_AFRICA,
        "blocks": [RegionalBlock.ECOWAS],
        "vat_rate": 7.5,
        "customs_url": "https://customs.gov.ng",
        "priority": Priority.HIGH,
        "languages": ["en"],
        "notes": "Largest African economy, Lagos/Apapa port",
        "customs_platform": CustomsPlatform.NICIS,
    },
    "RWA": {
        "iso2": "RW",
        "iso3": "RWA",
        "name_en": "Rwanda",
        "name_fr": "Rwanda",
        "region": Region.EAST_AFRICA,
        "blocks": [RegionalBlock.EAC, RegionalBlock.COMESA],
        "vat_rate": 18.0,
        "customs_url": "https://www.rra.gov.rw",
        "priority": Priority.MEDIUM,
        "languages": ["en", "fr", "rw"],
        "notes": "EAC member, landlocked, digital leader",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "STP": {
        "iso2": "ST",
        "iso3": "STP",
        "name_en": "São Tomé and Príncipe",
        "name_fr": "São Tomé-et-Príncipe",
        "region": Region.CENTRAL_AFRICA,
        "blocks": [RegionalBlock.ECCAS],
        "vat_rate": 15.0,
        "customs_url": "https://www.alfandega.st",
        "priority": Priority.LOW,
        "languages": ["pt"],
        "notes": "Island nation, small economy",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "SEN": {
        "iso2": "SN",
        "iso3": "SEN",
        "name_en": "Senegal",
        "name_fr": "Sénégal",
        "region": Region.WEST_AFRICA,
        "blocks": [RegionalBlock.ECOWAS, RegionalBlock.UEMOA],
        "vat_rate": 18.0,
        "customs_url": "https://www.douanes.sn",
        "priority": Priority.HIGH,
        "languages": ["fr"],
        "notes": "UEMOA member, Dakar port hub",
        "customs_platform": CustomsPlatform.GAINDE,
    },
    "SYC": {
        "iso2": "SC",
        "iso3": "SYC",
        "name_en": "Seychelles",
        "name_fr": "Seychelles",
        "region": Region.EAST_AFRICA,
        "blocks": [RegionalBlock.SADC, RegionalBlock.COMESA],
        "vat_rate": 15.0,
        "customs_url": "https://www.src.gov.sc",
        "priority": Priority.LOW,
        "languages": ["en", "fr"],
        "notes": "Island nation, tourism economy",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "SLE": {
        "iso2": "SL",
        "iso3": "SLE",
        "name_en": "Sierra Leone",
        "name_fr": "Sierra Leone",
        "region": Region.WEST_AFRICA,
        "blocks": [RegionalBlock.ECOWAS],
        "vat_rate": 15.0,
        "customs_url": "https://www.nra.gov.sl",
        "priority": Priority.LOW,
        "languages": ["en"],
        "notes": "ECOWAS member, Freetown port",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "SOM": {
        "iso2": "SO",
        "iso3": "SOM",
        "name_en": "Somalia",
        "name_fr": "Somalie",
        "region": Region.EAST_AFRICA,
        "blocks": [RegionalBlock.IGAD],
        "vat_rate": 0.0,
        "customs_url": "https://www.customs.gov.so",
        "priority": Priority.LOW,
        "languages": ["so", "ar"],
        "notes": "No formal VAT, limited government",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "ZAF": {
        "iso2": "ZA",
        "iso3": "ZAF",
        "name_en": "South Africa",
        "name_fr": "Afrique du Sud",
        "region": Region.SOUTHERN_AFRICA,
        "blocks": [RegionalBlock.SACU, RegionalBlock.SADC],
        "vat_rate": 15.0,
        "customs_url": "https://www.sars.gov.za",
        "priority": Priority.HIGH,
        "languages": ["en", "af", "zu", "xh"],
        "notes": "Largest SADC economy, Durban/Cape Town ports",
        "customs_platform": CustomsPlatform.SARS_EDI,
    },
    "SSD": {
        "iso2": "SS",
        "iso3": "SSD",
        "name_en": "South Sudan",
        "name_fr": "Soudan du Sud",
        "region": Region.EAST_AFRICA,
        "blocks": [RegionalBlock.EAC, RegionalBlock.IGAD],
        "vat_rate": 18.0,
        "customs_url": "https://www.customs.gov.ss",
        "priority": Priority.LOW,
        "languages": ["en"],
        "notes": "EAC member, landlocked, newest nation",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "SDN": {
        "iso2": "SD",
        "iso3": "SDN",
        "name_en": "Sudan",
        "name_fr": "Soudan",
        "region": Region.NORTH_AFRICA,
        "blocks": [RegionalBlock.AMU, RegionalBlock.COMESA, RegionalBlock.IGAD],
        "vat_rate": 17.0,
        "customs_url": "https://www.customs.gov.sd",
        "priority": Priority.MEDIUM,
        "languages": ["ar", "en"],
        "notes": "Port Sudan gateway, North Africa UMA regional system",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "TZA": {
        "iso2": "TZ",
        "iso3": "TZA",
        "name_en": "Tanzania",
        "name_fr": "Tanzanie",
        "region": Region.EAST_AFRICA,
        "blocks": [RegionalBlock.EAC, RegionalBlock.SADC],
        "vat_rate": 18.0,
        "customs_url": "https://www.tra.go.tz",
        "priority": Priority.HIGH,
        "languages": ["sw", "en"],
        "notes": "EAC member, Dar es Salaam port",
        "customs_platform": CustomsPlatform.SIMBA,
    },
    "TGO": {
        "iso2": "TG",
        "iso3": "TGO",
        "name_en": "Togo",
        "name_fr": "Togo",
        "region": Region.WEST_AFRICA,
        "blocks": [RegionalBlock.ECOWAS, RegionalBlock.UEMOA],
        "vat_rate": 18.0,
        "customs_url": "https://www.douanes.gouv.tg",
        "priority": Priority.HIGH,
        "languages": ["fr"],
        "notes": "UEMOA member, Lomé port hub",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "TUN": {
        "iso2": "TN",
        "iso3": "TUN",
        "name_en": "Tunisia",
        "name_fr": "Tunisie",
        "region": Region.NORTH_AFRICA,
        "blocks": [RegionalBlock.AMU],
        "vat_rate": 19.0,
        "customs_url": "https://www.douane.gov.tn",
        "priority": Priority.HIGH,
        "languages": ["ar", "fr"],
        "notes": "AMU member, Rades port",
        "customs_platform": CustomsPlatform.SINDA,
    },
    "UGA": {
        "iso2": "UG",
        "iso3": "UGA",
        "name_en": "Uganda",
        "name_fr": "Ouganda",
        "region": Region.EAST_AFRICA,
        "blocks": [RegionalBlock.EAC, RegionalBlock.COMESA],
        "vat_rate": 18.0,
        "customs_url": "https://www.ura.go.ug",
        "priority": Priority.HIGH,
        "languages": ["en", "sw"],
        "notes": "EAC member, landlocked",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "ZMB": {
        "iso2": "ZM",
        "iso3": "ZMB",
        "name_en": "Zambia",
        "name_fr": "Zambie",
        "region": Region.SOUTHERN_AFRICA,
        "blocks": [RegionalBlock.SADC, RegionalBlock.COMESA],
        "vat_rate": 16.0,
        "customs_url": "https://www.zra.org.zm",
        "priority": Priority.MEDIUM,
        "languages": ["en"],
        "notes": "SADC member, landlocked, copper",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
    "ZWE": {
        "iso2": "ZW",
        "iso3": "ZWE",
        "name_en": "Zimbabwe",
        "name_fr": "Zimbabwe",
        "region": Region.SOUTHERN_AFRICA,
        "blocks": [RegionalBlock.SADC, RegionalBlock.COMESA],
        "vat_rate": 15.0,
        "customs_url": "https://www.zimra.co.zw",
        "priority": Priority.MEDIUM,
        "languages": ["en"],
        "notes": "SADC member, landlocked",
        "customs_platform": CustomsPlatform.ASYCUDA_WORLD,
    },
}


# Regional blocks membership mapping
REGIONAL_BLOCKS: Dict[str, List[str]] = {
    RegionalBlock.ECOWAS.value: [
        "BEN",
        "BFA",
        "CPV",
        "CIV",
        "GMB",
        "GHA",
        "GIN",
        "GNB",
        "LBR",
        "MLI",
        "NER",
        "NGA",
        "SEN",
        "SLE",
        "TGO",
    ],
    RegionalBlock.UEMOA.value: ["BEN", "BFA", "CIV", "GNB", "MLI", "NER", "SEN", "TGO"],
    RegionalBlock.CEMAC.value: ["CMR", "CAF", "TCD", "COG", "GNQ", "GAB"],
    RegionalBlock.EAC.value: ["BDI", "KEN", "RWA", "SSD", "TZA", "UGA"],
    RegionalBlock.SACU.value: ["BWA", "LSO", "NAM", "ZAF", "SWZ"],
    RegionalBlock.SADC.value: [
        "AGO",
        "BWA",
        "COM",
        "COD",
        "LSO",
        "MDG",
        "MWI",
        "MUS",
        "MOZ",
        "NAM",
        "SYC",
        "ZAF",
        "SWZ",
        "TZA",
        "ZMB",
        "ZWE",
    ],
    RegionalBlock.COMESA.value: [
        "BDI",
        "COM",
        "COD",
        "DJI",
        "EGY",
        "ERI",
        "ETH",
        "KEN",
        "LBY",
        "MDG",
        "MWI",
        "MUS",
        "RWA",
        "SYC",
        "SDN",
        "SWZ",
        "UGA",
        "ZMB",
        "ZWE",
    ],
    RegionalBlock.AMU.value: ["DZA", "EGY", "LBY", "MRT", "MAR", "TUN", "SDN"],
    RegionalBlock.ECCAS.value: [
        "AGO",
        "BDI",
        "CMR",
        "CAF",
        "TCD",
        "COG",
        "COD",
        "GNQ",
        "GAB",
        "RWA",
        "STP",
    ],
    RegionalBlock.IGAD.value: ["DJI", "ERI", "ETH", "KEN", "SOM", "SSD", "SDN", "UGA"],
}


# Utility functions
def get_country_config(country_code: str) -> Optional[Dict[str, Any]]:
    """
    Get configuration for a specific country.

    Args:
        country_code: ISO3 country code (e.g., 'GHA', 'NGA')

    Returns:
        Country configuration dict or None if not found
    """
    return AFRICAN_COUNTRIES_REGISTRY.get(country_code.upper())


def get_countries_by_region(region: Region) -> List[str]:
    """
    Get all country codes for a specific region.

    Args:
        region: Region enum value

    Returns:
        List of ISO3 country codes
    """
    return [
        code for code, config in AFRICAN_COUNTRIES_REGISTRY.items() if config["region"] == region
    ]


def get_countries_by_block(block: RegionalBlock) -> List[str]:
    """
    Get all country codes for a specific regional economic block.

    Args:
        block: RegionalBlock enum value

    Returns:
        List of ISO3 country codes
    """
    return REGIONAL_BLOCKS.get(block.value, [])


def get_priority_countries(priority: Priority) -> List[str]:
    """
    Get all country codes with a specific priority level.

    Args:
        priority: Priority enum value (HIGH, MEDIUM, LOW)

    Returns:
        List of ISO3 country codes
    """
    return [
        code
        for code, config in AFRICAN_COUNTRIES_REGISTRY.items()
        if config["priority"] == priority
    ]


def get_all_countries_by_priority() -> Dict[str, List[str]]:
    """
    Get all countries grouped by priority level.

    Returns:
        Dict with priority levels as keys and lists of country codes as values
    """
    return {
        "HIGH": get_priority_countries(Priority.HIGH),
        "MEDIUM": get_priority_countries(Priority.MEDIUM),
        "LOW": get_priority_countries(Priority.LOW),
    }


def get_country_count() -> int:
    """
    Get total number of African countries in registry.

    Returns:
        Total count of countries (should be 54)
    """
    return len(AFRICAN_COUNTRIES_REGISTRY)


def validate_registry() -> Dict[str, Any]:
    """
    Validate the registry data structure and completeness.

    Returns:
        Validation report with statistics and any issues
    """
    report = {
        "total_countries": get_country_count(),
        "expected_countries": 54,
        "is_complete": get_country_count() == 54,
        "by_region": {},
        "by_priority": {},
        "missing_data": [],
    }

    # Count by region
    for region in Region:
        count = len(get_countries_by_region(region))
        report["by_region"][region.value] = count

    # Count by priority
    for priority in Priority:
        count = len(get_priority_countries(priority))
        report["by_priority"][priority.name] = count

    # Check for missing required fields
    required_fields = [
        "iso2",
        "iso3",
        "name_en",
        "region",
        "vat_rate",
        "customs_url",
        "customs_platform",
    ]
    for code, config in AFRICAN_COUNTRIES_REGISTRY.items():
        for field in required_fields:
            if field not in config or config[field] is None:
                report["missing_data"].append(f"{code}: missing {field}")

    return report


def get_country_platform(country_code: str) -> "Optional[CustomsPlatform]":
    """
    Return the customs management platform for a given country.

    Args:
        country_code: ISO3 country code (e.g. 'GHA', 'KEN', 'ZAF')

    Returns:
        CustomsPlatform enum value, or None if country not found.

    Examples:
        >>> get_country_platform('GHA')
        <CustomsPlatform.GCNET: 'GCNET'>
        >>> get_country_platform('DZA')
        <CustomsPlatform.ASYCUDA_WORLD: 'ASYCUDA World'>
        >>> get_country_platform('KEN')
        <CustomsPlatform.ICMS: 'iCMS'>
    """
    config = AFRICAN_COUNTRIES_REGISTRY.get(country_code.upper())
    if config is None:
        return None
    return config.get("customs_platform")


def get_country_declaration_form(country_code: str, lang: str = "en") -> str:
    """
    Return the country-specific import declaration form name.

    This is the actual name of the customs entry document used in the
    country's customs management system — e.g. 'Bill of Entry (DA 306)' for
    South Africa, 'Import Declaration Form (IDF)' for Kenya, 'CUSDEC' for
    Ghana, rather than the generic 'Import Declaration'.

    Args:
        country_code: ISO3 country code.
        lang: 'en' for English (default) or 'fr' for French.

    Returns:
        Localised form name string.  Falls back to generic 'Import Declaration'
        if the platform or country is unknown.
    """
    platform = get_country_platform(country_code)
    if platform is None:
        return "Import Declaration" if lang == "en" else "Déclaration d'Importation"
    info = CUSTOMS_PLATFORM_INFO.get(platform.value, {})
    key = "decl_form_en" if lang == "en" else "decl_form_fr"
    return info.get(key, "Import Declaration" if lang == "en" else "Déclaration d'Importation")


def get_countries_by_platform(platform: "CustomsPlatform") -> List[str]:
    """
    Return all country codes that use the specified customs platform.

    Args:
        platform: CustomsPlatform enum value.

    Returns:
        Sorted list of ISO3 country codes.

    Examples:
        >>> get_countries_by_platform(CustomsPlatform.GCNET)
        ['GHA']
        >>> get_countries_by_platform(CustomsPlatform.ASYCUDA_WORLD)
        ['AGO', 'BDI', ...]  # 42 countries
    """
    return sorted(
        code
        for code, config in AFRICAN_COUNTRIES_REGISTRY.items()
        if config.get("customs_platform") == platform
    )


# Run validation on import
_validation_report = validate_registry()
if not _validation_report["is_complete"]:
    import logging

    logger = logging.getLogger(__name__)
    logger.warning(
        f"Registry incomplete: {_validation_report['total_countries']}/54 countries registered"
    )


# Scraper class mapping for all 54 countries
def get_scraper_class_mapping() -> Dict[str, Any]:
    """
    Get scraper class mapping for all 54 African countries.

    Returns:
        Dict mapping country codes to scraper class references and configuration
    """
    # Lazy import to avoid circular dependency
    from backend.crawlers.countries.generic_scraper import GenericScraper

    # Initialize mapping with GenericScraper for all countries
    scraper_mapping = {}

    for country_code, config in AFRICAN_COUNTRIES_REGISTRY.items():
        # Determine regional tariff
        regional_tariff = None
        blocks = config.get("blocks", [])

        # Priority order for regional tariff assignment
        if RegionalBlock.ECOWAS in blocks or RegionalBlock.UEMOA in blocks:
            regional_tariff = "TEC CEDEAO"
        elif RegionalBlock.EAC in blocks:
            regional_tariff = "CET EAC"
        elif RegionalBlock.CEMAC in blocks:
            regional_tariff = "TDC CEMAC"
        elif RegionalBlock.SACU in blocks:
            regional_tariff = "SACU Common Tariff"

        scraper_mapping[country_code] = {
            "class": GenericScraper,
            "name": config.get("name_en"),
            "name_fr": config.get("name_fr"),
            "vat": config.get("vat_rate", 18.0),
            "regional_tariff": regional_tariff,
            "priority": config.get("priority"),
            "region": config.get("region"),
            "customs_url": config.get("customs_url"),
        }

    return scraper_mapping


# Cache for scraper mapping (initialized on first access)
_scraper_mapping_cache = None


def get_all_scrapers() -> Dict[str, Any]:
    """
    Get all scraper configurations with lazy initialization.

    Returns:
        Dict mapping country codes to scraper configurations
    """
    global _scraper_mapping_cache
    if _scraper_mapping_cache is None:
        _scraper_mapping_cache = get_scraper_class_mapping()
    return _scraper_mapping_cache


def get_scraper_config(country_code: str) -> Optional[Dict[str, Any]]:
    """
    Get scraper configuration for a specific country.

    Args:
        country_code: ISO3 country code (e.g., 'GHA', 'NGA')

    Returns:
        Scraper configuration dict or None if not found
    """
    return get_all_scrapers().get(country_code.upper())


def create_scraper_instance(country_code: str, config: Optional[Dict[str, Any]] = None):
    """
    Create a scraper instance for a specific country.

    Args:
        country_code: ISO3 country code
        config: Optional configuration overrides

    Returns:
        Scraper instance or None if country not found
    """
    scraper_config = get_scraper_config(country_code)
    if not scraper_config:
        return None

    scraper_class = scraper_config["class"]
    merged_config = {**scraper_config, **(config or {})}

    return scraper_class(country_code, merged_config)


# =============================================================================
# NATIONAL TAX SOURCES — Complétion tarifaire au-delà du TEC régional
# =============================================================================
# Contexte : les TEC régionaux (CEDEAO, CEMAC, EAC, SACU) ne publient que les
# droits de douane (DD). Les droits et taxes d'effet équivalent (DTE) et les
# taxes intérieures à l'importation (TVA, accises, redevances nationales) sont
# énoncés par les administrations nationales (douanes, directions des impôts,
# lois de finances), PAS par le TEC.
#
# IMPORTANT — source de vérité : la TVA de 31 pays et les accises de 7 pays
# sont DÉJÀ documentés dans les datasets existants data/{pays}/vat_measures.json
# et excise_measures.json (statuts VERIFIED_PRIMARY_TEXT / VERIFIED_CONSOLIDATED_HTML,
# PDF officiels archivés sous data/sources/{pays}/official/). Ce registre déclare
# les sources officielles pour les FAMILLES ENCORE MANQUANTES (DTE, accises
# nationales, redevances) et pour les pays sans aucun dataset national
# (BDI, BWA, COM, DJI, ERI, GNQ, LBY, LSO, MDG, MOZ, MWI, NAM, SDN, SOM, SSD,
# STP, SWZ, SYC, ZMB, ZWE). L'état autoritaire par pays/famille est calculé à
# l'exécution par etl.national_tax_completion (découverte des datasets).
#
# Doctrine (MISSION_TARIFS_AFRICAINS.md) : aucune donnée mock, hallucinée ou
# extrapolée. Ce registre déclare UNIQUEMENT des sources officielles à collecter.
# Il ne contient AUCUN taux. Un pays reste PENDING_OFFICIAL_COLLECTION tant
# qu'aucun document officiel n'a été archivé (raw + SHA-256) et validé par les
# validators du framework crawlers.
#
# url_status:
#   VERIFIED_200               — portail vérifié joignable (vérification HTTP du 2026-09-05)
#   REGISTRY_EXISTING_UNVERIFIED — URL déjà déclarée dans AFRICAN_COUNTRIES_REGISTRY,
#                                non joignable depuis l'environnement de vérification
#   UNVERIFIED                 — institution identifiée, URL à confirmer
#   NONE_IDENTIFIED            — portail officiel non identifié à ce jour
# =============================================================================

NATIONAL_TAX_SOURCES: Dict[str, Dict[str, Any]] = {
    # ── CEDEAO / UEMOA (15) ──────────────────────────────────────────────
    "BEN": {
        "tax_authority": {"name": "Direction Générale des Impôts (Bénin)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Code Général des Impôts (Bénin) en vigueur", "Loi de finances en vigueur"],
        "documented_levies": ["CEDEAO/PCC", "RS", "PCS", "PUA"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "BFA": {
        "tax_authority": {"name": "Direction Générale des Impôts (Burkina Faso)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Code Général des Impôts (Burkina Faso) en vigueur", "Loi de finances en vigueur"],
        "documented_levies": ["CEDEAO/PCC", "RS", "PCS", "PC_AES"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "CPV": {
        "tax_authority": {"name": "Direcção Geral das Contribuições e Impostos (Cabo Verde)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Código do IVA (Cabo Verde)", "Código do Imposto Especial de Consumo"],
        "documented_levies": [],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "CIV": {
        "tax_authority": {"name": "Direction Générale des Impôts (Côte d'Ivoire)", "url": "https://www.impots.gouv.ci", "url_status": "UNVERIFIED"},
        "instruments_to_collect": ["Code Général des Impôts (Côte d'Ivoire) en vigueur", "Loi de finances en vigueur"],
        "documented_levies": ["CEDEAO/PCC", "RS", "PCS", "PUA"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "GMB": {
        "tax_authority": {"name": "Gambia Revenue Authority (GRA)", "url": "https://www.gra.gm", "url_status": "VERIFIED_200", "verified_at": "2026-09-05"},
        "instruments_to_collect": ["Gambia Revenue Authority Act", "Income and VAT Act en vigueur", "Finance Act en vigueur"],
        "documented_levies": ["CEDEAO/PCC"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "GHA": {
        "tax_authority": {"name": "Ghana Revenue Authority (GRA)", "url": "https://www.gra.gov.gh", "url_status": "VERIFIED_200", "verified_at": "2026-09-05"},
        "instruments_to_collect": ["Value Added Tax Act, 2025 (Act 1151)", "Customs Act 2015 (Act 891)", "Finance Act en vigueur (GETFUND, NHIL, CPL)"],
        "documents_to_collect": [
            {
                "instrument": "GRA — page officielle TVA (réforme Act 1151 en vigueur au 01/01/2026)",
                "url": "https://gra.gov.gh/domestic-tax/tax-types/vat/",
                "source_type": "OFFICIAL_CURRENT_PAGE",
            }
        ],
        "documented_levies": ["GETFUND", "NHIL", "CPL", "CEDEAO/PCC"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "GIN": {
        "tax_authority": {"name": "Direction Générale des Impôts (Guinée)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Code Général des Impôts (Guinée) en vigueur", "Loi de finances en vigueur"],
        "documented_levies": ["CEDEAO/PCC"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "GNB": {
        "tax_authority": {"name": "Direction Générale des Impôts (Guinée-Bissau)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Code Général des Impôts (Guinée-Bissau) en vigueur"],
        "documented_levies": ["CEDEAO/PCC"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "LBR": {
        "tax_authority": {"name": "Liberia Revenue Authority (LRA)", "url": "https://www.lra.gov.lr", "url_status": "VERIFIED_200", "verified_at": "2026-09-05"},
        "instruments_to_collect": ["LRA Act", "Consolidated Tax Law en vigueur", "Finance Act en vigueur"],
        "documented_levies": ["CEDEAO/PCC"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "MLI": {
        "tax_authority": {"name": "Direction Générale des Impôts (Mali)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Code Général des Impôts (Mali) en vigueur", "Loi de finances en vigueur"],
        "documented_levies": ["CEDEAO/PCC", "RS", "PCS", "PC_AES"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "NER": {
        "tax_authority": {"name": "Direction Générale des Impôts (Niger)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Code Général des Impôts (Niger) en vigueur", "Loi de finances en vigueur"],
        "documented_levies": ["CEDEAO/PCC", "RS", "PCS", "PC_AES"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "NGA": {
        "tax_authority": {"name": "Federal Inland Revenue Service (FIRS)", "url": "https://www.firs.gov.ng", "url_status": "REGISTRY_EXISTING_UNVERIFIED"},
        "instruments_to_collect": ["VAT Act (Nigeria)", "Customs & Excise Tariff etc. (Consolidation) Act", "Finance Act en vigueur"],
        "documented_levies": ["CISS", "NAC", "FORMM"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "SEN": {
        "tax_authority": {"name": "Direction Générale des Impôts et des Domaines (DGID, Sénégal)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Code Général des Impôts (Sénégal) en vigueur", "Loi de finances en vigueur"],
        "documented_levies": ["CEDEAO/PCC", "RS", "PCS", "PUA"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "SLE": {
        "tax_authority": {"name": "National Revenue Authority (NRA, Sierra Leone)", "url": "https://www.nra.gov.sl", "url_status": "VERIFIED_200", "verified_at": "2026-09-05"},
        "instruments_to_collect": ["Goods and Services Tax Act", "Finance Act en vigueur", "Customs Act en vigueur"],
        "documented_levies": ["CEDEAO/PCC"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "TGO": {
        "tax_authority": {"name": "Office Togolais des Recettes (OTRF)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Code Général des Impôts (Togo) en vigueur", "Loi de finances en vigueur"],
        "documented_levies": ["CEDEAO/PCC", "RS", "PCS", "PUA"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    # ── CEMAC (6) ────────────────────────────────────────────────────────
    "CMR": {
        "tax_authority": {"name": "Direction Générale des Impôts (Cameroun)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Code Général des Impôts (Cameroun) en vigueur", "Loi de finances en vigueur"],
        "documented_levies": ["TCI", "RI", "CAC", "ECTN"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "CAF": {
        "tax_authority": {"name": "Direction Générale des Impôts (Centrafrique)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Code Général des Impôts (Centrafrique) en vigueur", "Loi de finances en vigueur"],
        "documented_levies": ["TCI", "RI", "ECTN"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "COG": {
        "tax_authority": {"name": "Direction Générale des Impôts (Congo)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Code Général des Impôts (Congo) en vigueur", "Loi de finances en vigueur"],
        "documented_levies": ["TCI", "RI", "ECTN"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "GAB": {
        "tax_authority": {"name": "Direction Générale des Impôts (Gabon)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Code Général des Impôts (Gabon) en vigueur", "Loi de finances en vigueur"],
        "documented_levies": ["TCI", "RI", "ECTN"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "GNQ": {
        "tax_authority": {"name": "Dirección General de Impuestos (Guinée équatoriale)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Ley General de Impuestos (Guinée équatoriale) en vigueur"],
        "documented_levies": ["TCI", "RI", "ECTN"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "TCD": {
        "tax_authority": {"name": "Direction Générale des Impôts (Tchad)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Code Général des Impôts (Tchad) en vigueur", "Loi de finances en vigueur"],
        "documented_levies": ["TCI", "RI", "ECTN"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    # ── EAC (7) ──────────────────────────────────────────────────────────
    "BDI": {
        "tax_authority": {"name": "Office Burundais des Recettes (OBR)", "url": "https://www.obr.bi", "url_status": "VERIFIED_200", "verified_at": "2026-09-05"},
        "instruments_to_collect": ["Code des Impôts (Burundi) en vigueur", "Loi de finances en vigueur"],
        "documented_levies": [],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "KEN": {
        "tax_authority": {"name": "Kenya Revenue Authority (KRA)", "url": "https://www.kra.go.ke", "url_status": "VERIFIED_200", "verified_at": "2026-09-05"},
        "instruments_to_collect": ["VAT Act 2013 et aménagements", "Excise Duty Act 2013 et tarifs en vigueur", "EACCMA et amendements (EACCMA 2025 — SOURCE_PENDING au 24/07)"],
        "documented_levies": ["IDF", "RDL", "PVoC"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "RWA": {
        "tax_authority": {"name": "Rwanda Revenue Authority (RRA)", "url": "https://www.rra.gov.rw", "url_status": "VERIFIED_200", "verified_at": "2026-09-05"},
        "instruments_to_collect": ["VAT Law (Rwanda) en vigueur", "Excise Duty Law en vigueur", "Loi de finances en vigueur"],
        "documented_levies": [],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "SSD": {
        "tax_authority": {"name": "Ministry of Finance and Planning (South Sudan) — Direction des impôts", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Taxation Act (South Sudan) en vigueur", "Financial Act en vigueur"],
        "documented_levies": [],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "TZA": {
        "tax_authority": {"name": "Tanzania Revenue Authority (TRA)", "url": "https://www.tra.go.tz", "url_status": "VERIFIED_200", "verified_at": "2026-09-05"},
        "instruments_to_collect": ["VAT Act 2014 et aménagements", "Excise Management and Tariff Act en vigueur", "Finance Act en vigueur"],
        "documented_levies": ["PDL", "PVoC TBS"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "UGA": {
        "tax_authority": {"name": "Uganda Revenue Authority (URA)", "url": "https://www.ura.go.ug", "url_status": "VERIFIED_200", "verified_at": "2026-09-05"},
        "instruments_to_collect": ["VAT Act Cap 349 (compendium URA) et amendements", "Excise Duty Act 2014", "Finance Act en vigueur (INFRALVY)"],
        "documents_to_collect": [
            {
                "instrument": "URA — Compendium for various Domestic Tax Laws (loi TVA consolidée, juillet 2021)",
                "url": "https://ura.go.ug/storage/2023/08/10580_DT_LAWS_JULY_2021.pdf",
                "source_type": "OFFICIAL_PDF",
            }
        ],
        "documented_levies": ["INFRALVY", "PVoC UNBS"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "COD": {
        "tax_authority": {"name": "Direction Générale des Impôts (DGI, RDC)", "url": "https://www.impots.gouv.cd", "url_status": "REGISTRY_EXISTING_UNVERIFIED"},
        "instruments_to_collect": ["Ordonnance-loi TVA (RDC)", "Loi de finances en vigueur"],
        "documented_levies": ["OCC", "OCCDECL"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    # ── SACU (5) ─────────────────────────────────────────────────────────
    "BWA": {
        "tax_authority": {"name": "Botswana Unified Revenue Service (BURS)", "url": "https://www.burs.org.bw", "url_status": "VERIFIED_200", "verified_at": "2026-09-05"},
        "instruments_to_collect": ["VAT Act (Botswana) en vigueur", "Excise Duty Act en vigueur"],
        "documented_levies": [],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "LSO": {
        "tax_authority": {"name": "Lesotho Revenue Authority (LRA)", "url": "https://www.lra.org.ls", "url_status": "REGISTRY_EXISTING_UNVERIFIED"},
        "instruments_to_collect": ["VAT Act (Lesotho) en vigueur", "Excise Act en vigueur"],
        "documented_levies": [],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "NAM": {
        "tax_authority": {"name": "Namibia Revenue Agency (NamRA)", "url": "https://www.namra.gov.na", "url_status": "REGISTRY_EXISTING_UNVERIFIED"},
        "instruments_to_collect": ["VAT Act (Namibie) en vigueur", "Excise Tax Act en vigueur"],
        "documented_levies": [],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "SWZ": {
        "tax_authority": {"name": "Eswatini Revenue Authority (ERA)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["VAT Act (Eswatini) en vigueur", "Excise Tax Act en vigueur"],
        "documented_levies": [],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "ZAF": {
        "tax_authority": {"name": "South African Revenue Service (SARS)", "url": "https://www.sars.gov.za", "url_status": "VERIFIED_200", "verified_at": "2026-09-05"},
        "instruments_to_collect": ["Customs & Excise Act 91/1964 — Schedules (accises déjà archivées: 288 lignes)", "VAT Act 89/1991 + liste zéro-rated (SOURCE_PENDING)", "Rates Notices SARS en vigueur"],
        "documented_levies": [],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    # ── Pays hors TEC (complétion identique requise) ─────────────────────
    "MUS": {
        "tax_authority": {"name": "Mauritius Revenue Authority (MRA)", "url": "https://www.mra.mu", "url_status": "REGISTRY_EXISTING_UNVERIFIED"},
        "instruments_to_collect": ["VAT Act 1998 et aménagements", "Excise Act (Maurice) en vigueur"],
        "documented_levies": [],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "SYC": {
        "tax_authority": {"name": "Seychelles Revenue Commission (SRC)", "url": "https://www.src.gov.sc", "url_status": "VERIFIED_200", "verified_at": "2026-09-05"},
        "instruments_to_collect": ["VAT Act (Seychelles) en vigueur"],
        "documented_levies": [],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "MWI": {
        "tax_authority": {"name": "Malawi Revenue Authority (MRA)", "url": "https://www.mra.mw", "url_status": "VERIFIED_200", "verified_at": "2026-09-05"},
        "instruments_to_collect": ["VAT Act (Malawi) en vigueur", "Excise Tariff Act en vigueur"],
        "documented_levies": ["COMLEV"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "ZMB": {
        "tax_authority": {"name": "Zambia Revenue Authority (ZRA)", "url": "https://www.zra.org.zm", "url_status": "VERIFIED_200", "verified_at": "2026-09-05"},
        "instruments_to_collect": ["VAT Act (Zambie) en vigueur", "Excise Duty Act en vigueur"],
        "documented_levies": ["COMLEV"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "ZWE": {
        "tax_authority": {"name": "Zimbabwe Revenue Authority (ZIMRA)", "url": "https://www.zimra.co.zw", "url_status": "VERIFIED_200", "verified_at": "2026-09-05"},
        "instruments_to_collect": ["VAT Act (Zimbabwe) en vigueur", "Excise Tariff Act en vigueur", "Finance Act en vigueur"],
        "documented_levies": ["COMLEV", "CBCA"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "MOZ": {
        "tax_authority": {"name": "Autoridade Tributária de Moçambique (AT)", "url": "https://www.at.gov.mz", "url_status": "REGISTRY_EXISTING_UNVERIFIED"},
        "instruments_to_collect": ["Código do IVA (Moçambique)", "Código do Imposto sobre o Valor Acrescentado em vigueur", "Lei de Finanças en vigueur"],
        "documented_levies": ["TRA"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "AGO": {
        "tax_authority": {"name": "Administração Geral Tributária (AGT, Angola)", "url": "https://www.agt.minfin.gov.ao", "url_status": "REGISTRY_EXISTING_UNVERIFIED"},
        "instruments_to_collect": ["Código do IVA (Angola)", "Código do Imposto Especial de Consumo en vigueur"],
        "documented_levies": ["IE"],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "MDG": {
        "tax_authority": {"name": "Direction Générale des Impôts (Madagascar)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Code Général des Impôts (Madagascar) en vigueur", "Loi de finances en vigueur"],
        "documented_levies": [],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "MRT": {
        "tax_authority": {"name": "Direction Générale des Impôts (Mauritanie)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Code Général des Impôts (Mauritanie) en vigueur", "Loi de finances en vigueur"],
        "documented_levies": [],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "COM": {
        "tax_authority": {"name": "Direction Générale des Impôts (Comores)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Code Général des Impôts (Comores) en vigueur", "Loi de finances en vigueur"],
        "documented_levies": [],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "STP": {
        "tax_authority": {"name": "Direcção Geral das Contribuições e Impostos (São Tomé e Príncipe)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Código do IVA (São Tomé e Príncipe) en vigueur"],
        "documented_levies": [],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "SDN": {
        "tax_authority": {"name": "Taxation Chamber (Sudan) — Ministry of Finance", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Taxation Act (Sudan) en vigueur"],
        "documented_levies": [],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "LBY": {
        "tax_authority": {"name": "Ministère des Finances (Libye) — Direction des impôts", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Loi TVA (Libye) en vigueur"],
        "documented_levies": [],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "DJI": {
        "tax_authority": {"name": "Direction Générale des Impôts (Djibouti)", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Code Général des Impôts (Djibouti) en vigueur", "Loi de finances en vigueur"],
        "documented_levies": [],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
    "ERI": {
        "tax_authority": {"name": "Ministry of Finance (Eritrea) — Inland Revenue", "url": None, "url_status": "NONE_IDENTIFIED"},
        "instruments_to_collect": ["Tax Proclamation (Eritrea) en vigueur"],
        "documented_levies": [],
        "tax_families_targeted": ["VAT", "EXCISE", "DTE"],
        "collection_status": "PENDING_OFFICIAL_COLLECTION",
    },
}

# Pays déjà complétés au niveau national 8–11 chiffres ( taxes nationales déjà
# embarquées dans les fichiers canoniques — pas de collecte TEC requise) :
# DZA, TUN, EGY, MAR, MUS (tarif national complet), ETH (partiel).
NATIONAL_TAX_COMPLETED = {"DZA", "TUN", "EGY", "MAR"}


def get_national_tax_source(country_code: str) -> Optional[Dict[str, Any]]:
    """
    Configuration de complétion fiscale nationale d'un pays (sources officielles
    à collecter pour DTE/TVA/accises/redevances au-delà du TEC régional).

    Args:
        country_code: ISO3 (ex. 'KEN', 'SEN')

    Returns:
        Dict de configuration ou None si pays inconnu / déjà complété.
    """
    iso3 = (country_code or "").upper().strip()
    if iso3 in NATIONAL_TAX_COMPLETED:
        return None
    return NATIONAL_TAX_SOURCES.get(iso3)


def get_pending_national_tax_countries() -> List[str]:
    """ISO3 des pays dont les taxes nationales restent à collecter (statut trié)."""
    return sorted(
        code
        for code, cfg in NATIONAL_TAX_SOURCES.items()
        if cfg.get("collection_status") == "PENDING_OFFICIAL_COLLECTION"
    )
