"""
Calculator routes - Main tariff calculation endpoint
Extracted from server.py for better maintainability
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
import requests

from constants import AFRICAN_COUNTRIES
from models import TariffCalculationRequest, TariffCalculationResponse
from data_loader import get_tariff_corrections
from etl.country_hs6_tariffs import get_country_hs6_tariff
from etl.country_tariffs_complete import (
    get_tariff_rate_for_country,
    get_vat_rate_for_country,
    get_other_taxes_for_country,
    get_product_category,
    get_zlecaf_reduction_factor
)
from etl.country_hs6_detailed import (
    get_sub_position_rate,
    get_all_sub_positions,
    has_varying_rates
)
from services.tariff_data_service import tariff_service
from services.crawled_data_service import crawled_service

router = APIRouter(tags=["Calculator"])

# API Clients for external data
class WorldBankAPIClient:
    def __init__(self):
        self.base_url = "https://api.worldbank.org/v2"
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ZLECAf-API/1.0'})

    async def get_country_data(self, country_codes: List[str], indicators: List[str] = None) -> Dict[str, Any]:
        """Fetch economic data from World Bank"""
        if indicators is None:
            indicators = ['NY.GDP.MKTP.CD', 'SP.POP.TOTL', 'NY.GDP.PCAP.CD', 'FP.CPI.TOTL.ZG']
        
        try:
            all_data = {}
            for country in country_codes:
                country_data = {}
                for indicator in indicators:
                    url = f"{self.base_url}/country/{country}/indicator/{indicator}"
                    params = {'format': 'json', 'date': '2020:2023', 'per_page': 10}
                    
                    response = self.session.get(url, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if len(data) > 1 and data[1]:
                            latest_data = data[1][0] if data[1] else None
                            if latest_data and latest_data['value']:
                                country_data[indicator] = {
                                    'value': latest_data['value'],
                                    'date': latest_data['date']
                                }
                
                all_data[country] = country_data
            
            return all_data
        except Exception as e:
            logging.error(f"World Bank API error: {e}")
            return {}


class OECAPIClient:
    def __init__(self):
        self.base_url = "https://api-v2.oec.world"
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ZLECAf-API/1.0'})

    async def get_top_producers(self, hs_code: str, year: int = 2021) -> List[Dict[str, Any]]:
        """Get top 5 African producers for an HS code"""
        try:
            endpoint = "tesseract/data.jsonrecords"
            params = {
                'cube': 'trade_i_hs4_eci',
                'drilldowns': 'Reporter',
                'measures': 'Export Value',
                'Product': hs_code[:4] if len(hs_code) > 4 else hs_code,
                'time': str(year),
                'Trade Flow': '2'
            }
            
            response = self.session.get(f"{self.base_url}/{endpoint}", params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    african_codes = [country['iso3'] for country in AFRICAN_COUNTRIES]
                    african_exports = []
                    
                    for item in data['data']:
                        if item.get('Reporter') in african_codes:
                            african_exports.append({
                                'country_code': item.get('Reporter'),
                                'country_name': next((c['name'] for c in AFRICAN_COUNTRIES if c['iso3'] == item.get('Reporter')), item.get('Reporter')),
                                'export_value': item.get('Export Value', 0),
                                'year': year
                            })
                    
                    african_exports.sort(key=lambda x: x['export_value'], reverse=True)
                    return african_exports[:5]
            
            return []
        except Exception as e:
            logging.error(f"OEC API error: {e}")
            return []


# Global API clients
wb_client = WorldBankAPIClient()
oec_client = OECAPIClient()

# Database reference (will be set by server.py)
db = None

def set_database(database):
    """Set the database reference from server.py"""
    global db
    db = database


@router.post("/calculate-tariff", response_model=TariffCalculationResponse)
async def calculate_comprehensive_tariff(request: TariffCalculationRequest):
    """Calculate complete tariffs with collected and verified tariff data
    
    Accepts ISO2 (e.g., DZ) or ISO3 (e.g., DZA) country codes
    Supports HS codes from 6 to 12 digits for more precision
    
    DATA SOURCES:
    - Primary: Collected tariff data (1.18M positions, 54 countries)
    - Fallback: ETL modules if collected data unavailable
    
    TARIFF PRIORITY ORDER:
    1. National sub-position (8-12 digits) if provided
    2. Country-specific HS6 tariff
    3. Country chapter tariff
    """
    
    # Find country by ISO3 first, then ISO2 (backward compatibility)
    origin_country = next((c for c in AFRICAN_COUNTRIES if c['iso3'] == request.origin_country.upper()), None)
    if not origin_country:
        origin_country = next((c for c in AFRICAN_COUNTRIES if c['code'] == request.origin_country.upper()), None)
    
    dest_country = next((c for c in AFRICAN_COUNTRIES if c['iso3'] == request.destination_country.upper()), None)
    if not dest_country:
        dest_country = next((c for c in AFRICAN_COUNTRIES if c['code'] == request.destination_country.upper()), None)
    
    if not origin_country or not dest_country:
        raise HTTPException(status_code=400, detail="L'un des pays sélectionnés n'est pas membre de la ZLECAf")
    
    # Use ISO3 for calculations
    dest_iso3 = dest_country['iso3']
    # origin_iso3 available if needed for bilateral calculations
    
    # Clean and normalize HS code
    hs_code_clean = request.hs_code.replace(".", "").replace(" ", "")
    hs6_code = hs_code_clean[:6].zfill(6)
    sector_code = hs6_code[:2]
    
    tariff_precision = "chapter"
    sub_position_used = None
    sub_position_description = None
    data_source = "etl_fallback"
    
    collected_taxes_detail = []
    collected_fiscal_advantages = []
    collected_admin_formalities = []
    crawled_raw_taxes = []
    other_taxes_detail = {}

    # ============================================================
    # PRIORITY 1: Authentic crawled data (official sources)
    # ============================================================
    if crawled_service.is_loaded():
        crawled_result = crawled_service.lookup(dest_iso3, hs_code_clean)
        if crawled_result:
            data_source = "crawled_authentic"
            sub_position_used = crawled_result["code_raw"]
            sub_position_description = crawled_result["designation"]
            tariff_precision = "national_position"
            crawled_raw_taxes = crawled_result["taxes"]
            raw_advantages = crawled_result.get("fiscal_advantages", [])
            collected_fiscal_advantages = [
                item if isinstance(item, dict) else {"description": item, "source": crawled_result["source"]}
                for item in raw_advantages
            ]
            raw_formalities = crawled_result.get("administrative_formalities", [])
            collected_admin_formalities = [
                item if isinstance(item, dict) else {"description": item, "source": crawled_result["source"]}
                for item in raw_formalities
            ]

            dd_tax = next((t for t in crawled_raw_taxes if t["code"] in ("DD", "DI", "DDDROIT", "ID", "GENERAL", "Droit d'Importation (DI)") or "Import Duty" in t.get("name", "") or "Customs Duty" in t.get("name", "")), None)
            if dd_tax and dd_tax.get("rate_pct") is not None:
                normal_rate = dd_tax["rate_pct"] / 100.0
            else:
                normal_rate = 0.0
            npf_source = f"Source officielle: {crawled_result['source']}"

            vat_tax = next((t for t in crawled_raw_taxes if t["code"] in ("TVA", "TVA/APTAXE", "VAT") or "TVA" in t.get("name", "").upper() or "VAT" in t.get("name", "").upper() or "Valeur Ajoutée" in t.get("name", "") or "Value Added Tax" in t.get("name", "")), None)
            if vat_tax and vat_tax.get("rate_pct") is not None:
                vat_rate = vat_tax["rate_pct"] / 100.0
                vat_source = f"{vat_tax['name']} ({crawled_result['source']})"
            else:
                vat_rate, vat_source = get_vat_rate_for_country(dest_iso3)

            other_taxes_rate = 0.0
            dd_codes = ("DD", "DI", "DDDROIT", "ID", "GENERAL", "Droit d'Importation (DI)")
            for t in crawled_raw_taxes:
                is_dd = t["code"] in dd_codes or "Import Duty" in t.get("name", "") or "Customs Duty" in t.get("name", "")
                is_vat = t["code"] in ("TVA", "TVA/APTAXE", "VAT") or "TVA" in t.get("code", "").upper() or "VAT" in t.get("name", "").upper() or "Valeur Ajoutée" in t.get("name", "") or "Value Added Tax" in t.get("name", "")
                is_preferential = t.get("is_preferential", False)
                if not is_dd and not is_vat and not is_preferential:
                    if t.get("rate_pct") is not None:
                        other_taxes_rate += t["rate_pct"] / 100.0
                        other_taxes_detail[t["code"]] = t["rate_pct"]

            collected_taxes_detail = [
                {
                    "tax": t["name"],
                    "rate": t["rate_pct"] if t.get("rate_pct") is not None else 0,
                    "raw_value": t.get("raw_value", ""),
                    "observation": f"Source: {t.get('source', crawled_result['source'])}",
                }
                for t in crawled_raw_taxes
            ]

            product_category = get_product_category(hs6_code)
            reduction_factor = get_zlecaf_reduction_factor(dest_iso3, product_category)
            zlecaf_rate = normal_rate * reduction_factor
            zlecaf_source = f"ZLECAf ({product_category})"

    # ============================================================
    # PRIORITY 2: Collected ETL enriched data
    # ============================================================
    if data_source != "crawled_authentic" and tariff_service.is_loaded():
        tariff_info = tariff_service.get_tariff_precision_info(dest_iso3, hs_code_clean)
        if tariff_info:
            normal_rate = tariff_info["rate"]
            npf_source = tariff_info["source"]
            tariff_precision = tariff_info["precision"]
            sub_position_used = tariff_info.get("sub_position_code")
            sub_position_description = tariff_info.get("sub_position_description")
            data_source = "collected_verified"

            collected_taxes_detail = tariff_info.get("taxes_detail", [])
            collected_fiscal_advantages = tariff_info.get("fiscal_advantages", [])
            collected_admin_formalities = tariff_info.get("administrative_formalities", [])

            zlecaf_rate_val, zlecaf_source = tariff_service.get_zlecaf_rate(dest_iso3, hs6_code)
            if zlecaf_rate_val is not None:
                zlecaf_rate = zlecaf_rate_val
            else:
                product_category = get_product_category(hs6_code)
                reduction_factor = get_zlecaf_reduction_factor(dest_iso3, product_category)
                zlecaf_rate = normal_rate * reduction_factor
                zlecaf_source = f"ZLECAf ({product_category})"

            vat_rate, vat_source = tariff_service.get_vat_rate(dest_iso3)

            if collected_taxes_detail:
                product_other = sum(
                    t["rate"] for t in collected_taxes_detail
                    if t["tax"] not in ("D.D", "T.V.A")
                ) / 100.0
                other_taxes_rate = product_other
                other_taxes_detail = {
                    t["tax"].lower().replace(".", ""): t["rate"]
                    for t in collected_taxes_detail
                    if t["tax"] not in ("D.D", "T.V.A")
                }
                vat_from_detail = next((t["rate"] for t in collected_taxes_detail if t["tax"] == "T.V.A"), None)
                if vat_from_detail is not None:
                    vat_rate = vat_from_detail / 100.0
            else:
                other_taxes_rate, other_taxes_detail = tariff_service.get_other_taxes(dest_iso3)
    
    # ============================================================
    # PRIORITY 3: ETL modules (fallback)
    # ============================================================
    if data_source not in ("crawled_authentic", "collected_verified"):
        if len(hs_code_clean) > 6:
            rate, description, source = get_sub_position_rate(dest_iso3, hs_code_clean)
            if rate is not None:
                normal_rate = rate
                npf_source = f"Sous-position nationale {dest_iso3} ({hs_code_clean})"
                tariff_precision = "sub_position"
                sub_position_used = hs_code_clean
                sub_position_description = description

        if tariff_precision == "chapter":
            hs6_tariff = get_country_hs6_tariff(dest_iso3, hs6_code)
            if hs6_tariff:
                normal_rate = hs6_tariff["dd"]
                npf_source = f"Tarif SH6 {dest_iso3} ({hs6_code})"
                tariff_precision = "hs6_country"
            else:
                normal_rate, npf_source = get_tariff_rate_for_country(dest_iso3, hs6_code)
                tariff_precision = "chapter"

        product_category = get_product_category(hs6_code)
        reduction_factor = get_zlecaf_reduction_factor(dest_iso3, product_category)
        zlecaf_rate = normal_rate * reduction_factor
        zlecaf_source = f"ZLECAf ({product_category})"

        vat_rate, vat_source = get_vat_rate_for_country(dest_iso3)
        other_taxes_rate, other_taxes_detail = get_other_taxes_for_country(dest_iso3)
    
    # Source for display
    rate_source = f"Tarif officiel {dest_iso3} - {npf_source}"
    
    # Transition period by sector
    tariff_corrections = get_tariff_corrections()
    transition_periods = tariff_corrections.get('transition_periods', {})
    transition_period = transition_periods.get(sector_code, 'immediate')
    
    # ============================================================
    # AMOUNT CALCULATIONS
    # ============================================================
    
    # Customs duties
    normal_customs = request.value * normal_rate
    zlecaf_customs = request.value * zlecaf_rate
    
    # Other taxes (on CIF value)
    other_taxes_amount = request.value * other_taxes_rate
    
    # VAT calculated on (Value + DD + Other taxes)
    normal_vat_base = request.value + normal_customs + other_taxes_amount
    zlecaf_vat_base = request.value + zlecaf_customs + other_taxes_amount
    
    normal_vat_amount = normal_vat_base * vat_rate
    zlecaf_vat_amount = zlecaf_vat_base * vat_rate
    
    # Totals
    normal_total = request.value + normal_customs + other_taxes_amount + normal_vat_amount
    zlecaf_total = request.value + zlecaf_customs + other_taxes_amount + zlecaf_vat_amount
    
    # Savings
    savings = normal_customs - zlecaf_customs
    savings_percentage = (savings / normal_customs) * 100 if normal_customs > 0 else 0
    total_savings_with_taxes = normal_total - zlecaf_total
    total_savings_percentage = (total_savings_with_taxes / normal_total) * 100 if normal_total > 0 else 0
    
    legal_refs = {
        "cif": {"ref": "Incoterms 2020 - CIF", "url": "https://iccwbo.org/resources-for-business/incoterms-rules/incoterms-2020/"},
        "dd": {"ref": f"Tarif douanier {dest_iso3}", "url": None},
        "rs": {"ref": "Règlement UEMOA 02/97/CM", "url": None},
        "pcs": {"ref": "Règlement UEMOA 01/2019", "url": None},
        "cedeao": {"ref": "Protocole CEDEAO A/P1/1/03", "url": None},
        "tci": {"ref": "Règlement CEMAC 02/01", "url": None},
        "vat": {"ref": f"Code Général des Impôts {dest_iso3}", "url": None},
        "zlecaf": {"ref": "Accord ZLECAf Art. 8", "url": "https://au.int/en/treaties/agreement-establishing-african-continental-free-trade-area"},
        "daps": {"ref": f"Décret exécutif - DAPS {dest_iso3}", "url": None},
        "prct": {"ref": f"Loi de Finances {dest_iso3}", "url": None},
        "tcs": {"ref": f"Réglementation sanitaire {dest_iso3}", "url": None},
    }

    normal_journal = [
        {"step": 1, "component": "Valeur CIF", "base": request.value, "rate": "-", "amount": request.value, "cumulative": request.value, "legal_ref": legal_refs["cif"]["ref"], "legal_ref_url": legal_refs["cif"]["url"]},
    ]
    step = 2
    cumulative = request.value

    if collected_taxes_detail:
        for tax_item in collected_taxes_detail:
            tax_name = tax_item["tax"]
            tax_rate_pct = tax_item["rate"]
            tax_rate_dec = tax_rate_pct / 100.0
            tax_amount = round(request.value * tax_rate_dec, 2) if tax_name != "T.V.A" else round(normal_vat_amount, 2)

            if tax_name == "T.V.A":
                tax_base = round(normal_vat_base, 2)
                cumulative = round(normal_total, 2)
            else:
                tax_base = request.value
                cumulative += tax_amount

            ref_key = tax_name.lower().replace(".", "").replace(" ", "")
            ref = legal_refs.get(ref_key, {"ref": tax_item.get("observation", ""), "url": None})

            normal_journal.append({
                "step": step,
                "component": f"{tax_name} ({tax_item.get('observation', '')})" if tax_item.get("observation") else tax_name,
                "base": tax_base,
                "rate": f"{tax_rate_pct:.1f}%",
                "amount": tax_amount,
                "cumulative": round(cumulative, 2),
                "legal_ref": ref["ref"],
                "legal_ref_url": ref.get("url"),
            })
            step += 1
    else:
        normal_journal.append({"step": step, "component": "Droits de douane (DD)", "base": request.value, "rate": f"{normal_rate*100:.1f}%", "amount": round(normal_customs, 2), "cumulative": round(request.value + normal_customs, 2), "legal_ref": legal_refs["dd"]["ref"], "legal_ref_url": legal_refs["dd"]["url"]})
        step = 3
        cumulative = request.value + normal_customs

        rs_rate = other_taxes_detail.get('rs', 0) / 100 if other_taxes_detail.get('rs') else 0
        pcs_rate = other_taxes_detail.get('pcs', 0) / 100 if other_taxes_detail.get('pcs') else 0
        cedeao_rate = other_taxes_detail.get('cedeao', 0) / 100 if other_taxes_detail.get('cedeao') else 0
        tci_rate = other_taxes_detail.get('tci', 0) / 100 if other_taxes_detail.get('tci') else 0

        if rs_rate > 0:
            rs_amount = round(request.value * rs_rate, 2)
            cumulative += rs_amount
            normal_journal.append({"step": step, "component": "Redevance statistique (RS)", "base": request.value, "rate": f"{rs_rate*100:.1f}%", "amount": rs_amount, "cumulative": round(cumulative, 2), "legal_ref": legal_refs["rs"]["ref"], "legal_ref_url": legal_refs["rs"]["url"]})
            step += 1
        if pcs_rate > 0:
            pcs_amount = round(request.value * pcs_rate, 2)
            cumulative += pcs_amount
            normal_journal.append({"step": step, "component": "PCS UEMOA", "base": request.value, "rate": f"{pcs_rate*100:.1f}%", "amount": pcs_amount, "cumulative": round(cumulative, 2), "legal_ref": legal_refs["pcs"]["ref"], "legal_ref_url": legal_refs["pcs"]["url"]})
            step += 1
        if cedeao_rate > 0:
            cedeao_amount = round(request.value * cedeao_rate, 2)
            cumulative += cedeao_amount
            normal_journal.append({"step": step, "component": "Prélèvement CEDEAO (PC)", "base": request.value, "rate": f"{cedeao_rate*100:.1f}%", "amount": cedeao_amount, "cumulative": round(cumulative, 2), "legal_ref": legal_refs["cedeao"]["ref"], "legal_ref_url": legal_refs["cedeao"]["url"]})
            step += 1
        if tci_rate > 0:
            tci_amount = round(request.value * tci_rate, 2)
            cumulative += tci_amount
            normal_journal.append({"step": step, "component": "TCI CEMAC", "base": request.value, "rate": f"{tci_rate*100:.1f}%", "amount": tci_amount, "cumulative": round(cumulative, 2), "legal_ref": legal_refs["tci"]["ref"], "legal_ref_url": legal_refs["tci"]["url"]})
            step += 1
        normal_journal.append({"step": step, "component": "TVA", "base": round(normal_vat_base, 2), "rate": f"{vat_rate*100:.1f}%", "amount": round(normal_vat_amount, 2), "cumulative": round(normal_total, 2), "legal_ref": legal_refs["vat"]["ref"], "legal_ref_url": legal_refs["vat"]["url"]})
    
    # Create detailed calculation journal for ZLECAf with legal references
    zlecaf_journal = [
        {"step": 1, "component": "Valeur CIF", "base": request.value, "rate": "-", "amount": request.value, "cumulative": request.value, "legal_ref": legal_refs["cif"]["ref"], "legal_ref_url": legal_refs["cif"]["url"]},
        {"step": 2, "component": "Droits de douane ZLECAf (DD)", "base": request.value, "rate": f"{zlecaf_rate*100:.1f}%", "amount": round(zlecaf_customs, 2), "cumulative": round(request.value + zlecaf_customs, 2), "legal_ref": legal_refs["zlecaf"]["ref"], "legal_ref_url": legal_refs["zlecaf"]["url"]},
    ]
    step = 3
    zlecaf_cumulative = request.value + zlecaf_customs
    if other_taxes_rate > 0:
        zlecaf_cumulative += other_taxes_amount
        zlecaf_journal.append({"step": step, "component": "Autres taxes", "base": request.value, "rate": f"{other_taxes_rate*100:.1f}%", "amount": round(other_taxes_amount, 2), "cumulative": round(zlecaf_cumulative, 2), "legal_ref": "Taxes communautaires", "legal_ref_url": None})
        step += 1
    zlecaf_journal.append({"step": step, "component": "TVA", "base": round(zlecaf_vat_base, 2), "rate": f"{vat_rate*100:.1f}%", "amount": round(zlecaf_vat_amount, 2), "cumulative": round(zlecaf_total, 2), "legal_ref": legal_refs["vat"]["ref"], "legal_ref_url": legal_refs["vat"]["url"]})
    
    # Rules of origin - Use official AfCFTA Annex II rules
    from etl.afcfta_rules_of_origin import get_rule_of_origin
    roo_data = get_rule_of_origin(hs6_code, "fr")
    
    # Build rules_of_origin object for calculator
    if roo_data.get("status") == "UNKNOWN":
        rules = {
            "rule": "Règle non définie",
            "requirement": "Consulter le Secrétariat ZLECAf",
            "regional_content": 0,
            "status": "UNKNOWN",
            "source": "AfCFTA Annex II - Appendix IV"
        }
    else:
        primary_rule = roo_data.get("primary_rule", {})
        rule_name = primary_rule.get("name", "")
        rule_code = primary_rule.get("code", "")
        regional_content = roo_data.get("regional_content", 40)
        status = roo_data.get("status", "AGREED")
        chapter_desc = roo_data.get("chapter_description", "")
        
        # Build requirement based on rule type
        if rule_code == "WO":
            requirement = "Entièrement obtenu dans la ZLECAf (100%)"
        elif rule_code in ["CTH", "CTSH"]:
            requirement = f"Changement de position tarifaire ({rule_code}) avec {regional_content}% minimum de contenu régional"
        elif rule_code == "VA":
            requirement = f"{regional_content}% minimum de valeur ajoutée africaine"
        elif rule_code == "SP":
            requirement = f"Processus spécifique requis avec {regional_content}% minimum de contenu régional"
        else:
            requirement = f"{regional_content}% valeur ajoutée africaine"
        
        # Add alternative if available
        alt_rule = roo_data.get("alternative_rule", {})
        if alt_rule:
            requirement += f" OU {alt_rule.get('name', '')}"
        
        rules = {
            "rule": rule_name,
            "rule_code": rule_code,
            "requirement": requirement,
            "regional_content": regional_content,
            "status": status,
            "status_label": "Convenu" if status == "AGREED" else "En négociation",
            "chapter_description": chapter_desc,
            "notes": roo_data.get("notes", ""),
            "source": "AfCFTA Protocol on Trade in Goods - Annex II, Appendix IV",
            "reference_url": "https://au.int/sites/default/files/treaties/36437-ax-AfCFTA_RULES_OF_ORIGIN_MANUAL.pdf"
        }
    
    # Get top African producers
    top_producers = await oec_client.get_top_producers(request.hs_code)
    
    # Get country economic data
    wb_data = await wb_client.get_country_data([origin_country['wb_code'], dest_country['wb_code']])
    
    # Check if alternative sub-positions exist for this HS6
    if tariff_service.is_loaded() and data_source == "collected_verified":
        collected_subs = tariff_service.get_sub_positions_for_hs6(dest_iso3, hs6_code)
        if collected_subs:
            sub_positions_available = collected_subs
            rates = [sp.get("dd", 0) / 100.0 for sp in collected_subs]
            has_varying = len(set(rates)) > 1
            min_rate = min(rates) if rates else 0
            max_rate = max(rates) if rates else 0
        else:
            sub_positions_available = get_all_sub_positions(dest_iso3, hs6_code)
            has_varying, min_rate, max_rate = has_varying_rates(dest_iso3, hs6_code)
    else:
        sub_positions_available = get_all_sub_positions(dest_iso3, hs6_code)
        has_varying, min_rate, max_rate = has_varying_rates(dest_iso3, hs6_code)
    
    # Build warning and details if varying rates
    rate_warning = None
    sub_positions_details = None
    
    if has_varying and len(sub_positions_available) > 0:
        rate_warning = {
            "has_variation": True,
            "message_fr": f"⚠️ Attention: Ce code SH6 ({hs6_code}) a des taux de droits de douane variables selon les sous-positions nationales. Le taux peut varier de {min_rate*100:.1f}% à {max_rate*100:.1f}%.",
            "message_en": f"⚠️ Warning: This HS6 code ({hs6_code}) has varying duty rates depending on national sub-headings. Rates range from {min_rate*100:.1f}% to {max_rate*100:.1f}%.",
            "min_rate": min_rate,
            "max_rate": max_rate,
            "min_rate_pct": f"{min_rate*100:.1f}%",
            "max_rate_pct": f"{max_rate*100:.1f}%",
            "rate_used": normal_rate,
            "rate_used_pct": f"{normal_rate*100:.1f}%",
            "recommendation_fr": "Pour un calcul plus précis, veuillez spécifier la sous-position nationale complète (8-12 chiffres).",
            "recommendation_en": "For a more accurate calculation, please specify the complete national sub-heading (8-12 digits)."
        }
        sub_positions_details = sub_positions_available
    
    # Create complete response with all taxes
    result = TariffCalculationResponse(
        origin_country=request.origin_country,
        destination_country=request.destination_country,
        hs_code=request.hs_code,
        hs6_code=hs6_code,
        value=request.value,
        # Customs tariffs
        normal_tariff_rate=normal_rate,
        normal_tariff_amount=round(normal_customs, 2),
        zlecaf_tariff_rate=zlecaf_rate,
        zlecaf_tariff_amount=round(zlecaf_customs, 2),
        normal_vat_rate=vat_rate,
        normal_vat_amount=round(normal_vat_amount, 2),
        normal_statistical_fee=round(request.value * other_taxes_detail.get('rs', 0) / 100, 2) if other_taxes_detail.get('rs') else 0,
        normal_community_levy=round(request.value * other_taxes_detail.get('pcs', 0) / 100, 2) if other_taxes_detail.get('pcs') else 0,
        normal_ecowas_levy=round(request.value * other_taxes_detail.get('cedeao', 0) / 100, 2) if other_taxes_detail.get('cedeao') else 0,
        normal_other_taxes_total=round(other_taxes_amount, 2),
        normal_total_cost=round(normal_total, 2),
        zlecaf_vat_rate=vat_rate,
        zlecaf_vat_amount=round(zlecaf_vat_amount, 2),
        zlecaf_statistical_fee=round(request.value * other_taxes_detail.get('rs', 0) / 100, 2) if other_taxes_detail.get('rs') else 0,
        zlecaf_community_levy=round(request.value * other_taxes_detail.get('pcs', 0) / 100, 2) if other_taxes_detail.get('pcs') else 0,
        zlecaf_ecowas_levy=round(request.value * other_taxes_detail.get('cedeao', 0) / 100, 2) if other_taxes_detail.get('cedeao') else 0,
        zlecaf_other_taxes_total=round(other_taxes_amount, 2),
        zlecaf_total_cost=round(zlecaf_total, 2),
        # Savings
        savings=round(savings, 2),
        savings_percentage=round(savings_percentage, 1),
        total_savings_with_taxes=round(total_savings_with_taxes, 2),
        total_savings_percentage=round(total_savings_percentage, 1),
        # Calculation journal and traceability
        normal_calculation_journal=normal_journal,
        zlecaf_calculation_journal=zlecaf_journal,
        computation_order_ref="Codes douaniers nationaux + Directives CEDEAO/UEMOA/CEMAC/EAC/SACU",
        last_verified="2025-01",
        confidence_level="high" if data_source == "collected_verified" or tariff_precision in ["sub_position", "hs6_country", "hs6_collected"] else "medium",
        tariff_precision=tariff_precision,
        sub_position_used=sub_position_used,
        sub_position_description=sub_position_description,
        has_varying_sub_positions=has_varying,
        available_sub_positions_count=len(sub_positions_available),
        rate_warning=rate_warning,
        sub_positions_details=sub_positions_details,
        taxes_detail=collected_taxes_detail if collected_taxes_detail else None,
        fiscal_advantages=collected_fiscal_advantages if collected_fiscal_advantages else None,
        administrative_formalities=collected_admin_formalities if collected_admin_formalities else None,
        data_source=data_source,
        rules_of_origin=rules,
        top_african_producers=top_producers,
        origin_country_data=wb_data.get(origin_country['wb_code'], {}),
        destination_country_data=wb_data.get(dest_country['wb_code'], {})
    )
    
    if db is not None:
        await db.comprehensive_calculations.insert_one(result.dict())
    
    return result
