"""
Tariff Calculation Routes
Routes for calculating customs tariffs
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tariffs")

# Load tariff data
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# Models
class TariffCalculationRequest(BaseModel):
    origin_country: str
    destination_country: str
    hs_code: str
    value: float

class TariffCalculationResponse(BaseModel):
    origin_country: str
    destination_country: str
    hs_code: str
    hs6_code: str
    value: float
    normal_tariff_rate: float
    normal_tariff_amount: float
    zlecaf_tariff_rate: float
    zlecaf_tariff_amount: float
    savings: float
    savings_percentage: float
    normal_vat_rate: float
    normal_vat_amount: float
    zlecaf_vat_rate: float
    zlecaf_vat_amount: float
    normal_total_cost: float
    zlecaf_total_cost: float
    total_savings_with_taxes: float
    total_savings_percentage: float
    normal_other_taxes_total: float = 0
    zlecaf_other_taxes_total: float = 0
    tariff_precision: str = "estimated"
    sub_position_used: Optional[str] = None
    sub_position_description: Optional[str] = None
    rate_warning: Optional[Dict] = None
    sub_positions_details: Optional[List[Dict]] = None
    normal_calculation_journal: Optional[List[Dict]] = None
    zlecaf_calculation_journal: Optional[List[Dict]] = None
    rules_of_origin: Optional[Dict] = None
    data_source: str = "calculated"
    computation_order_ref: Optional[str] = None
    last_verified: Optional[str] = None
    confidence_level: str = "medium"


# Helper functions
def get_chapter_rate(chapter: str) -> float:
    """Get the tariff rate for a chapter"""
    # Default rates by chapter (simplified)
    chapter_rates = {
        "01": 0.05, "02": 0.10, "03": 0.10, "04": 0.15, "05": 0.05,
        "06": 0.10, "07": 0.10, "08": 0.10, "09": 0.10, "10": 0.05,
        "11": 0.10, "12": 0.05, "13": 0.10, "14": 0.05, "15": 0.10,
        "16": 0.15, "17": 0.15, "18": 0.10, "19": 0.15, "20": 0.15,
        "21": 0.15, "22": 0.20, "23": 0.05, "24": 0.25, "25": 0.05,
        "26": 0.05, "27": 0.05, "28": 0.05, "29": 0.05, "30": 0.05,
        "31": 0.05, "32": 0.10, "33": 0.15, "34": 0.10, "35": 0.10,
        "36": 0.10, "37": 0.10, "38": 0.10, "39": 0.10, "40": 0.10,
        "41": 0.10, "42": 0.15, "43": 0.15, "44": 0.10, "45": 0.10,
        "46": 0.15, "47": 0.05, "48": 0.10, "49": 0.05, "50": 0.10,
        "51": 0.10, "52": 0.10, "53": 0.10, "54": 0.10, "55": 0.10,
        "56": 0.10, "57": 0.15, "58": 0.15, "59": 0.10, "60": 0.10,
        "61": 0.20, "62": 0.20, "63": 0.20, "64": 0.20, "65": 0.15,
        "66": 0.15, "67": 0.15, "68": 0.10, "69": 0.10, "70": 0.10,
        "71": 0.10, "72": 0.10, "73": 0.10, "74": 0.10, "75": 0.10,
        "76": 0.10, "78": 0.10, "79": 0.10, "80": 0.10, "81": 0.10,
        "82": 0.10, "83": 0.15, "84": 0.05, "85": 0.10, "86": 0.05,
        "87": 0.20, "88": 0.05, "89": 0.05, "90": 0.05, "91": 0.15,
        "92": 0.15, "93": 0.20, "94": 0.20, "95": 0.15, "96": 0.15,
        "97": 0.05
    }
    return chapter_rates.get(chapter, 0.10)


def get_vat_rate(country_code: str) -> float:
    """Get VAT rate for a country"""
    vat_rates = {
        "DZA": 0.19, "AGO": 0.14, "BEN": 0.18, "BWA": 0.12, "BFA": 0.18,
        "BDI": 0.18, "CMR": 0.1925, "CPV": 0.15, "CAF": 0.19, "TCD": 0.18,
        "COM": 0.10, "COG": 0.18, "COD": 0.16, "CIV": 0.18, "DJI": 0.10,
        "EGY": 0.14, "GNQ": 0.15, "ERI": 0.05, "SWZ": 0.15, "ETH": 0.15,
        "GAB": 0.18, "GMB": 0.15, "GHA": 0.125, "GIN": 0.18, "GNB": 0.17,
        "KEN": 0.16, "LSO": 0.15, "LBR": 0.10, "LBY": 0.00, "MDG": 0.20,
        "MWI": 0.165, "MLI": 0.18, "MRT": 0.16, "MUS": 0.15, "MAR": 0.20,
        "MOZ": 0.17, "NAM": 0.15, "NER": 0.19, "NGA": 0.075, "RWA": 0.18,
        "STP": 0.15, "SEN": 0.18, "SYC": 0.15, "SLE": 0.15, "SOM": 0.00,
        "ZAF": 0.15, "SSD": 0.18, "SDN": 0.17, "TZA": 0.18, "TGO": 0.18,
        "TUN": 0.19, "UGA": 0.18, "ZMB": 0.16, "ZWE": 0.15
    }
    # Try both ISO2 and ISO3
    iso3_to_iso2 = {
        'DZA': 'DZ', 'AGO': 'AO', 'BEN': 'BJ', 'BWA': 'BW', 'BFA': 'BF',
        'BDI': 'BI', 'CMR': 'CM', 'CPV': 'CV', 'CAF': 'CF', 'TCD': 'TD',
        'COM': 'KM', 'COG': 'CG', 'COD': 'CD', 'CIV': 'CI', 'DJI': 'DJ',
        'EGY': 'EG', 'GNQ': 'GQ', 'ERI': 'ER', 'SWZ': 'SZ', 'ETH': 'ET',
        'GAB': 'GA', 'GMB': 'GM', 'GHA': 'GH', 'GIN': 'GN', 'GNB': 'GW',
        'KEN': 'KE', 'LSO': 'LS', 'LBR': 'LR', 'LBY': 'LY', 'MDG': 'MG',
        'MWI': 'MW', 'MLI': 'ML', 'MRT': 'MR', 'MUS': 'MU', 'MAR': 'MA',
        'MOZ': 'MZ', 'NAM': 'NA', 'NER': 'NE', 'NGA': 'NG', 'RWA': 'RW',
        'STP': 'ST', 'SEN': 'SN', 'SYC': 'SC', 'SLE': 'SL', 'SOM': 'SO',
        'ZAF': 'ZA', 'SSD': 'SS', 'SDN': 'SD', 'TZA': 'TZ', 'TGO': 'TG',
        'TUN': 'TN', 'UGA': 'UG', 'ZMB': 'ZM', 'ZWE': 'ZW'
    }
    if country_code in vat_rates:
        return vat_rates[country_code]
    iso3 = next((k for k, v in iso3_to_iso2.items() if v == country_code), None)
    if iso3:
        return vat_rates.get(iso3, 0.15)
    return 0.15


# Routes
@router.get("/detailed/{country_code}/{hs_code}")
async def get_detailed_tariff(
    country_code: str,
    hs_code: str,
    language: str = Query(default="fr")
):
    """Get detailed tariff information for a specific country and HS code"""
    clean_hs = hs_code.replace(".", "").replace(" ", "")
    hs6 = clean_hs[:6]
    chapter = clean_hs[:2]
    
    # Try to find in HS6 database
    hs6_file = os.path.join(DATA_DIR, "hs6_tariffs.json")
    country_data = None
    
    if os.path.exists(hs6_file):
        try:
            with open(hs6_file, 'r', encoding='utf-8') as f:
                hs6_data = json.load(f)
                if hs6 in hs6_data:
                    country_data = hs6_data[hs6]
        except Exception as e:
            logger.error(f"Error loading HS6 data: {e}")
    
    # Get rate from chapter if no specific data
    rate = get_chapter_rate(chapter)
    vat_rate = get_vat_rate(country_code)
    
    return {
        "country_code": country_code,
        "hs_code": clean_hs,
        "hs6_code": hs6,
        "chapter": chapter,
        "dd_rate": rate,
        "vat_rate": vat_rate,
        "description": country_data.get("description_fr" if language == "fr" else "description_en") if country_data else f"Code HS {hs6}",
        "data_source": "hs6_database" if country_data else "chapter_estimate"
    }


@router.get("/sub-position/{country_code}/{full_code}")
async def get_sub_position_tariff(
    country_code: str,
    full_code: str,
    language: str = Query(default="fr")
):
    """Get tariff for a specific sub-position code"""
    clean_code = full_code.replace(".", "").replace(" ", "")
    hs6 = clean_code[:6]
    
    # Check authentic tariffs first
    from ..services.authentic_tariff_service import get_tariff_line
    
    authentic_data = get_tariff_line(country_code, clean_code)
    if authentic_data:
        return authentic_data
    
    # Fallback to chapter rate
    chapter = clean_code[:2]
    rate = get_chapter_rate(chapter)
    vat_rate = get_vat_rate(country_code)
    
    return {
        "country_code": country_code,
        "code": clean_code,
        "hs6_code": hs6,
        "dd_rate": rate,
        "vat_rate": vat_rate,
        "data_source": "chapter_estimate"
    }


@router.get("/sub-positions/{country_code}/{hs6_code}")
async def get_sub_positions(
    country_code: str,
    hs6_code: str,
    language: str = Query(default="fr")
):
    """Get all sub-positions for an HS6 code in a country"""
    clean_hs6 = hs6_code.replace(".", "").replace(" ", "")[:6]
    
    # Check authentic tariffs
    from ..services.authentic_tariff_service import get_sub_positions as get_auth_sub_pos
    
    authentic_data = get_auth_sub_pos(country_code, clean_hs6, language)
    if authentic_data and authentic_data.get("sub_positions"):
        return authentic_data
    
    return {
        "country_code": country_code,
        "hs6_code": clean_hs6,
        "sub_positions": [],
        "total": 0,
        "data_source": "no_data"
    }


@router.get("/detailed-countries")
async def get_detailed_tariff_countries():
    """Get list of countries with detailed tariff data"""
    from ..services.authentic_tariff_service import get_available_countries
    
    countries = get_available_countries()
    return {
        "countries": countries,
        "total": len(countries)
    }
