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

from typing import Dict, List, Optional, Any
from enum import Enum


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
    UEMOA = "UEMOA"    # West African Economic and Monetary Union
    CEMAC = "CEMAC"    # Economic and Monetary Community of Central Africa
    EAC = "EAC"        # East African Community
    SACU = "SACU"      # Southern African Customs Union
    SADC = "SADC"      # Southern African Development Community
    COMESA = "COMESA"  # Common Market for Eastern and Southern Africa
    AMU = "AMU"        # Arab Maghreb Union
    ECCAS = "ECCAS"    # Economic Community of Central African States
    IGAD = "IGAD"      # Intergovernmental Authority on Development


class Priority(int, Enum):
    """Priority levels for crawling (1=highest, 3=lowest)"""
    HIGH = 1      # Major economies, good data availability
    MEDIUM = 2    # Medium economies or partial data
    LOW = 3       # Small economies or limited data availability


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
        "notes": "Major economy, oil/gas exporter"
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
        "notes": "Oil exporter, SADC member"
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
        "notes": "UEMOA member, Cotonou port hub"
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
        "notes": "SACU member, stable economy"
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
        "notes": "UEMOA member, landlocked"
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
        "notes": "EAC member, landlocked"
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
        "notes": "Island nation, ECOWAS member"
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
        "notes": "CEMAC member, Douala port"
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
        "notes": "CEMAC member, landlocked"
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
        "notes": "CEMAC member, landlocked, oil producer"
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
        "notes": "Island nation, COMESA member"
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
        "notes": "CEMAC member, Pointe-Noire port"
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
        "notes": "Large economy, mineral resources"
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
        "notes": "UEMOA member, Abidjan port hub"
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
        "notes": "Strategic port for Ethiopia trade"
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
        "notes": "Largest North African economy"
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
        "notes": "CEMAC member, oil producer"
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
        "notes": "Limited data availability"
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
        "notes": "SACU member, formerly Swaziland"
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
        "notes": "Large economy, landlocked"
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
        "notes": "CEMAC member, oil producer"
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
        "notes": "ECOWAS member, small economy"
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
        "notes": "ECOWAS member, Tema port"
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
        "notes": "ECOWAS member, bauxite/mining"
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
        "notes": "UEMOA member, small economy"
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
        "notes": "EAC hub, Mombasa port"
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
        "notes": "SACU member, landlocked"
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
        "notes": "ECOWAS member, Monrovia port"
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
        "notes": "No VAT, oil producer, unstable"
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
        "notes": "Island nation, SADC member"
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
        "notes": "SADC member, landlocked"
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
        "notes": "UEMOA member, landlocked"
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
        "notes": "AMU member, mining/fishing"
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
        "notes": "Island nation, financial hub"
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
        "notes": "Major economy, Casablanca/Tangier ports"
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
        "notes": "SADC member, Maputo port"
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
        "notes": "SACU member, Walvis Bay port"
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
        "notes": "UEMOA member, landlocked"
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
        "notes": "Largest African economy, Lagos/Apapa port"
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
        "notes": "EAC member, landlocked, digital leader"
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
        "notes": "Island nation, small economy"
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
        "notes": "UEMOA member, Dakar port hub"
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
        "notes": "Island nation, tourism economy"
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
        "notes": "ECOWAS member, Freetown port"
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
        "notes": "No formal VAT, limited government"
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
        "notes": "Largest SADC economy, Durban/Cape Town ports"
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
        "notes": "EAC member, landlocked, newest nation"
    },
    "SDN": {
        "iso2": "SD",
        "iso3": "SDN",
        "name_en": "Sudan",
        "name_fr": "Soudan",
        "region": Region.NORTH_AFRICA,
        "blocks": [RegionalBlock.COMESA, RegionalBlock.IGAD],
        "vat_rate": 17.0,
        "customs_url": "https://www.customs.gov.sd",
        "priority": Priority.MEDIUM,
        "languages": ["ar", "en"],
        "notes": "Port Sudan gateway"
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
        "notes": "EAC member, Dar es Salaam port"
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
        "notes": "UEMOA member, Lomé port hub"
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
        "notes": "AMU member, Rades port"
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
        "notes": "EAC member, landlocked"
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
        "notes": "SADC member, landlocked, copper"
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
        "notes": "SADC member, landlocked"
    },
}


# Regional blocks membership mapping
REGIONAL_BLOCKS: Dict[str, List[str]] = {
    RegionalBlock.ECOWAS.value: [
        "BEN", "BFA", "CPV", "CIV", "GMB", "GHA", "GIN", "GNB",
        "LBR", "MLI", "NER", "NGA", "SEN", "SLE", "TGO"
    ],
    RegionalBlock.UEMOA.value: [
        "BEN", "BFA", "CIV", "GNB", "MLI", "NER", "SEN", "TGO"
    ],
    RegionalBlock.CEMAC.value: [
        "CMR", "CAF", "TCD", "COG", "GNQ", "GAB"
    ],
    RegionalBlock.EAC.value: [
        "BDI", "KEN", "RWA", "SSD", "TZA", "UGA"
    ],
    RegionalBlock.SACU.value: [
        "BWA", "LSO", "NAM", "ZAF", "SWZ"
    ],
    RegionalBlock.SADC.value: [
        "AGO", "BWA", "COM", "COD", "LSO", "MDG", "MWI", "MUS",
        "MOZ", "NAM", "SYC", "ZAF", "SWZ", "TZA", "ZMB", "ZWE"
    ],
    RegionalBlock.COMESA.value: [
        "BDI", "COM", "COD", "DJI", "EGY", "ERI", "ETH", "KEN",
        "LBY", "MDG", "MWI", "MUS", "RWA", "SYC", "SDN", "SWZ",
        "UGA", "ZMB", "ZWE"
    ],
    RegionalBlock.AMU.value: [
        "DZA", "LBY", "MRT", "MAR", "TUN"
    ],
    RegionalBlock.ECCAS.value: [
        "AGO", "BDI", "CMR", "CAF", "TCD", "COG", "COD", "GNQ",
        "GAB", "RWA", "STP"
    ],
    RegionalBlock.IGAD.value: [
        "DJI", "ERI", "ETH", "KEN", "SOM", "SSD", "SDN", "UGA"
    ]
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
        code for code, config in AFRICAN_COUNTRIES_REGISTRY.items()
        if config["region"] == region
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
        code for code, config in AFRICAN_COUNTRIES_REGISTRY.items()
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
        "missing_data": []
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
    required_fields = ["iso2", "iso3", "name_en", "region", "vat_rate", "customs_url"]
    for code, config in AFRICAN_COUNTRIES_REGISTRY.items():
        for field in required_fields:
            if field not in config or config[field] is None:
                report["missing_data"].append(f"{code}: missing {field}")
    
    return report


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
