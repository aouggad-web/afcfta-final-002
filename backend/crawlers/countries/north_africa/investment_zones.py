"""
North Africa (UMA/AMU) Special Economic Zones and Investment Areas.

Covers all 7 North African countries: MAR, EGY, TUN, DZA, LBY, SDN, MRT.
Data sourced from official investment agencies and publicly available databases.
"""

from typing import Dict, List, Any, Optional

# ── Special Economic Zone definitions ──────────────────────────────────────

_SEZ_DATA: Dict[str, List[Dict[str, Any]]] = {
    "MAR": [
        {
            "name": "Tanger-Med Free Zone",
            "name_fr": "Zone Franche de Tanger-Med",
            "type": "industrial_free_zone",
            "location": "Tangier",
            "region": "Tanger-Tetouan-Al Hoceima",
            "coordinates": {"lat": 35.85, "lon": -5.55},
            "area_ha": 1000,
            "operational_since": 2007,
            "operator": "Tanger Med Special Agency (TMSA)",
            "port_connected": True,
            "port_name": "Tanger-Med Port",
            "port_capacity_teu_m": 9.0,
            "incentives": [
                "IS (corporate tax) exempt for 5 years, then 8.75%",
                "VAT exempt on imports",
                "No customs duties on goods",
                "Free repatriation of profits",
                "Land available at preferential rates",
            ],
            "target_sectors": ["automotive", "aerospace", "electronics", "logistics", "textiles"],
            "major_tenants": ["Renault", "PSA/Stellantis", "Lear", "Leoni", "Delphi"],
            "employment": 80000,
            "annual_trade_bn_usd": 7.5,
            "eu_access": True,
            "us_access": True,
            "certifications": ["ISO", "AEO"],
            "contact_url": "https://www.tangermed.ma",
        },
        {
            "name": "Casablanca Finance City",
            "name_fr": "Casablanca Finance City",
            "type": "financial_center",
            "location": "Casablanca",
            "region": "Casablanca-Settat",
            "coordinates": {"lat": 33.57, "lon": -7.62},
            "area_ha": 100,
            "operational_since": 2010,
            "operator": "Casablanca Finance City Authority",
            "port_connected": False,
            "incentives": [
                "Corporate tax 15% (vs 26% standard)",
                "No dividend withholding tax for 5 years",
                "Personal income tax cap at 20%",
                "Free profit repatriation",
                "Single-window administrative services",
            ],
            "target_sectors": ["financial_services", "insurance", "consulting", "holding_companies"],
            "major_tenants": ["Aon", "Sanlam", "Société Générale", "BNP Paribas"],
            "employment": 35000,
            "certifications": ["GFCI Top 20 Africa"],
            "contact_url": "https://www.casablancafinancecity.com",
        },
        {
            "name": "Dakhla Offshore City",
            "name_fr": "Cité Mohammed VI Tanger Tech",
            "type": "offshore_tech_city",
            "location": "Dakhla",
            "region": "Dakhla-Oued Ed-Dahab",
            "coordinates": {"lat": 23.69, "lon": -15.94},
            "area_ha": 2000,
            "operational_since": 2022,
            "operator": "Agence Spéciale Tanger-Méditerranée (extension)",
            "port_connected": True,
            "incentives": [
                "Extended tax holidays",
                "Renewable energy access (wind/solar)",
                "Offshore fishing port integration",
                "Special investment incentives for remote areas",
            ],
            "target_sectors": ["fisheries", "renewable_energy", "logistics", "tourism"],
            "employment": 15000,
            "contact_url": "https://www.invest.gov.ma",
        },
        {
            "name": "Kenitra Atlantic Free Zone",
            "name_fr": "Zone Franche Atlantique de Kénitra",
            "type": "industrial_free_zone",
            "location": "Kenitra",
            "region": "Rabat-Salé-Kénitra",
            "coordinates": {"lat": 34.26, "lon": -6.58},
            "area_ha": 344,
            "operational_since": 2014,
            "operator": "Medz",
            "port_connected": False,
            "incentives": [
                "Corporate tax exempt 5 years, then 8.75%",
                "VAT exempt on imports",
                "No customs duties",
            ],
            "target_sectors": ["automotive", "electronics", "aerospace"],
            "major_tenants": ["PSA/Stellantis", "Yazaki"],
            "employment": 25000,
            "contact_url": "https://www.medz.ma",
        },
    ],

    "EGY": [
        {
            "name": "Suez Canal Economic Zone (SCZONE)",
            "name_ar": "منطقة قناة السويس الاقتصادية",
            "type": "special_economic_zone",
            "location": "Suez Canal Corridor",
            "region": "Suez, Ismailia, Port Said",
            "coordinates": {"lat": 30.05, "lon": 32.55},
            "area_ha": 461000,
            "operational_since": 2015,
            "operator": "Suez Canal Economic Zone Authority",
            "port_connected": True,
            "port_name": "Port Said East, Ain Sokhna, Adabiya",
            "incentives": [
                "Corporate tax 22.5% → reduced to 10% for qualifying activities",
                "Customs duty exemptions on equipment and raw materials",
                "Land lease at competitive rates",
                "Single-window clearance (48 hours)",
                "Profit repatriation guarantee",
            ],
            "target_sectors": ["logistics", "manufacturing", "petrochemicals", "textiles", "electronics"],
            "major_tenants": ["Cosco Shipping", "Tianjin Economic Zone", "Samsung"],
            "employment": 120000,
            "annual_trade_bn_usd": 12.0,
            "contact_url": "https://www.sczone.eg",
        },
        {
            "name": "QIZ Zones (Greater Cairo / Alexandria / Delta)",
            "name_ar": "مناطق المؤهلات الصناعية",
            "type": "qualifying_industrial_zone",
            "location": "Greater Cairo, Alexandria, Delta region",
            "region": "Multiple",
            "coordinates": {"lat": 30.06, "lon": 31.24},
            "area_ha": None,
            "operational_since": 2005,
            "operator": "Ministry of Trade and Industry (MTI)",
            "port_connected": False,
            "incentives": [
                "US duty-free access for qualifying products (≥35% value from QIZ)",
                "Israeli component requirement (minimum 10.5% of FOB value)",
                "No Egyptian import duties on inputs",
                "Simplified export procedures",
            ],
            "target_sectors": ["textiles", "garments", "footwear"],
            "employment": 250000,
            "contact_url": "https://www.mti.gov.eg",
        },
        {
            "name": "New Administrative Capital Investment Zone",
            "name_ar": "منطقة العاصمة الإدارية الجديدة",
            "type": "new_city_investment_zone",
            "location": "New Administrative Capital",
            "region": "Cairo Governorate (east)",
            "coordinates": {"lat": 30.01, "lon": 31.70},
            "area_ha": 70000,
            "operational_since": 2021,
            "operator": "Administrative Capital for Urban Development (ACUD)",
            "port_connected": False,
            "incentives": [
                "Investment Law 72/2017 protections",
                "Tax incentives for priority sectors",
                "Single-window services",
            ],
            "target_sectors": ["ict", "financial_services", "government", "real_estate"],
            "contact_url": "https://www.acud.com.eg",
        },
    ],

    "TUN": [
        {
            "name": "Bizerte Economic Development Zone",
            "name_fr": "Zone de Développement Économique de Bizerte",
            "type": "industrial_free_zone",
            "location": "Bizerte",
            "region": "Bizerte Governorate",
            "coordinates": {"lat": 37.27, "lon": 9.87},
            "area_ha": 500,
            "operational_since": 1993,
            "operator": "APAL (Agence de Promotion de l'Industrie et de l'Innovation)",
            "port_connected": True,
            "port_name": "Bizerte Port",
            "incentives": [
                "Corporate tax 10% (standard 15%)",
                "Customs duty exemption on equipment",
                "VAT exemption during construction phase",
                "Social security contributions employer side reduced",
            ],
            "target_sectors": ["logistics", "manufacturing", "chemicals"],
            "contact_url": "https://www.tunisieindustrie.gov.tn",
        },
        {
            "name": "Sfax Economic Zone",
            "name_fr": "Zone Économique de Sfax",
            "type": "offshore_enterprise_zone",
            "location": "Sfax",
            "region": "Sfax Governorate",
            "coordinates": {"lat": 34.74, "lon": 10.76},
            "area_ha": 300,
            "operational_since": 2000,
            "operator": "APII",
            "port_connected": True,
            "port_name": "Sfax Port",
            "incentives": [
                "Offshore regime: 10% CIT for fully export-oriented firms",
                "No restrictions on foreign ownership",
                "Free profit repatriation",
            ],
            "target_sectors": ["textiles", "olive_oil_processing", "ICT", "automotive_components"],
            "contact_url": "https://www.apii.tn",
        },
        {
            "name": "Sousse Technology Park",
            "name_fr": "Parc Technologique de Sousse",
            "type": "technology_park",
            "location": "Sousse",
            "region": "Sousse Governorate",
            "coordinates": {"lat": 35.83, "lon": 10.64},
            "area_ha": 50,
            "operational_since": 2010,
            "operator": "El Ghazala Tech Parks",
            "port_connected": False,
            "incentives": [
                "ICT sector incentives",
                "R&D tax credits",
                "Graduate employment subsidy",
            ],
            "target_sectors": ["ict", "software", "bpo"],
            "contact_url": "https://www.elghazala.tn",
        },
    ],

    "DZA": [
        {
            "name": "Bellara Steel Industrial Zone",
            "name_fr": "Zone Industrielle de Bellara",
            "type": "industrial_zone",
            "location": "El Milia, Jijel",
            "region": "Jijel Wilaya",
            "coordinates": {"lat": 36.74, "lon": 5.90},
            "area_ha": 900,
            "operational_since": 2018,
            "operator": "Tosyali Algeria (private)",
            "port_connected": True,
            "port_name": "Jijel Djen-Djen Port",
            "incentives": [
                "ANDI investment incentives",
                "Import duty exemption on production equipment",
                "Exoneration from VAT for capital goods",
            ],
            "target_sectors": ["steel", "construction_materials"],
            "contact_url": "https://www.andi.dz",
        },
        {
            "name": "Oran Free Zone (Planned)",
            "name_fr": "Zone Franche d'Oran",
            "type": "planned_free_zone",
            "location": "Oran",
            "region": "Oran Wilaya",
            "coordinates": {"lat": 35.70, "lon": -0.63},
            "area_ha": 500,
            "operational_since": None,
            "operator": "ANIREF (future operator)",
            "port_connected": True,
            "port_name": "Oran Port",
            "incentives": [
                "Expected: customs duty exemptions",
                "Expected: corporate tax holidays",
                "Expected: streamlined investor registration",
            ],
            "target_sectors": ["logistics", "manufacturing", "agri-food"],
            "contact_url": "https://www.andi.dz",
            "notes": "Under development as of 2024; not yet operational",
        },
    ],

    "LBY": [
        {
            "name": "Misrata Free Zone",
            "name_ar": "منطقة مصراتة الحرة",
            "type": "free_zone",
            "location": "Misrata",
            "region": "Misrata District",
            "coordinates": {"lat": 32.38, "lon": 15.09},
            "area_ha": 1200,
            "operational_since": 2012,
            "operator": "Misrata Free Zone Authority",
            "port_connected": True,
            "port_name": "Misrata Port",
            "incentives": [
                "Import/export duty exemptions",
                "No corporate tax (reconstruction period)",
                "Free repatriation of capital",
            ],
            "target_sectors": ["steel", "construction", "logistics", "food_processing"],
            "contact_url": "https://www.mfz.ly",
            "notes": "Partially operational; reconstruction projects priority",
        },
        {
            "name": "Tripoli Reconstruction Zone (Planned)",
            "name_ar": "منطقة إعادة الإعمار طرابلس",
            "type": "reconstruction_zone",
            "location": "Tripoli",
            "region": "Tripoli District",
            "coordinates": {"lat": 32.90, "lon": 13.18},
            "area_ha": 2000,
            "operational_since": None,
            "operator": "Libya Investment Authority (planned)",
            "port_connected": True,
            "port_name": "Tripoli Port",
            "incentives": [
                "Post-conflict reconstruction incentives",
                "Infrastructure rebuilding contracts",
            ],
            "target_sectors": ["construction", "infrastructure", "housing"],
            "contact_url": "https://lia.ly",
            "notes": "Framework under development; stability-dependent",
        },
    ],

    "SDN": [
        {
            "name": "Khartoum Free Trade Zone",
            "name_ar": "منطقة الخرطوم الحرة",
            "type": "free_trade_zone",
            "location": "Khartoum North",
            "region": "Khartoum State",
            "coordinates": {"lat": 15.60, "lon": 32.52},
            "area_ha": 400,
            "operational_since": 2003,
            "operator": "Sudan Free Zones and Markets Company",
            "port_connected": False,
            "incentives": [
                "Corporate tax exemption 10 years",
                "Import duty exemptions on inputs",
                "No restrictions on profit repatriation",
            ],
            "target_sectors": ["manufacturing", "agri_processing", "light_industry"],
            "contact_url": "https://www.mof.gov.sd",
        },
        {
            "name": "Port Sudan Trade Zone",
            "name_ar": "منطقة بورتسودان التجارية",
            "type": "port_trade_zone",
            "location": "Port Sudan",
            "region": "Red Sea State",
            "coordinates": {"lat": 19.61, "lon": 37.22},
            "area_ha": 200,
            "operational_since": 2010,
            "operator": "Port Sudan Free Zone Authority",
            "port_connected": True,
            "port_name": "Port Sudan",
            "incentives": [
                "Reduced port fees",
                "Expedited customs clearance",
                "COMESA facilitation",
            ],
            "target_sectors": ["logistics", "transit_trade", "agri_exports"],
            "contact_url": "https://www.customs.gov.sd",
        },
    ],

    "MRT": [
        {
            "name": "Nouakchott Free Zone",
            "name_fr": "Zone Franche de Nouakchott",
            "type": "free_zone",
            "location": "Nouakchott",
            "region": "Nouakchott",
            "coordinates": {"lat": 18.08, "lon": -15.97},
            "area_ha": 150,
            "operational_since": 2008,
            "operator": "APIM (Agence de Promotion des Investissements)",
            "port_connected": True,
            "port_name": "Port Autonome de Nouakchott (Port de l'Amitié)",
            "incentives": [
                "Corporate tax 0% for 5 years",
                "No customs duties on imports/exports",
                "Free capital repatriation",
                "Work permit facilitation",
            ],
            "target_sectors": ["fishing", "agri_processing", "logistics", "mining_services"],
            "contact_url": "https://www.mauritania-invest.mr",
        },
        {
            "name": "Cansado Mining Services Zone",
            "name_fr": "Zone de Services Miniers de Cansado",
            "type": "mining_services_zone",
            "location": "Nouadhibou",
            "region": "Dakhlet Nouadhibou",
            "coordinates": {"lat": 20.94, "lon": -17.03},
            "area_ha": 50,
            "operational_since": 2015,
            "operator": "SNIM + Private operators",
            "port_connected": True,
            "port_name": "Port of Nouadhibou",
            "incentives": [
                "Mining law incentives",
                "Equipment import duty exemptions",
                "Royalty stabilization clauses",
            ],
            "target_sectors": ["iron_ore", "gold", "copper", "mining_services"],
            "contact_url": "https://www.mauritania-invest.mr",
        },
    ],
}


def get_investment_zones(country_code: str) -> List[Dict[str, Any]]:
    """
    Return all special economic zones for a North African country.

    Args:
        country_code: ISO-3 code (MAR, EGY, TUN, DZA, LBY, SDN, MRT)

    Returns:
        List of SEZ dicts; empty list if country not found.
    """
    return _SEZ_DATA.get(country_code.upper(), [])


def get_all_sez_data() -> Dict[str, List[Dict[str, Any]]]:
    """Return all SEZ data across all 7 North African countries."""
    return dict(_SEZ_DATA)


def get_zone_summary() -> Dict[str, Any]:
    """
    Return a high-level summary of investment zones across the region.

    Returns a dict containing:
    - total_zones: count of all zones
    - by_country: per-country zone count and types
    - operational_zones: count of live zones
    - port_connected_zones: count of port-connected zones
    """
    total = 0
    operational = 0
    port_connected = 0
    by_country: Dict[str, Dict[str, Any]] = {}

    for country, zones in _SEZ_DATA.items():
        country_total = len(zones)
        country_operational = sum(
            1 for z in zones if z.get("operational_since") is not None
        )
        country_port = sum(1 for z in zones if z.get("port_connected", False))
        types = list({z["type"] for z in zones})

        by_country[country] = {
            "total": country_total,
            "operational": country_operational,
            "port_connected": country_port,
            "types": types,
        }
        total += country_total
        operational += country_operational
        port_connected += country_port

    return {
        "total_zones": total,
        "operational_zones": operational,
        "port_connected_zones": port_connected,
        "by_country": by_country,
    }
