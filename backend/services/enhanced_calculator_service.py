"""
Enhanced Tariff Calculator Service
Provides detailed calculation breakdown for NPF vs ZLECAf tariffs
Shows step-by-step calculation with all tax components

Tax Components (Algeria example):
- DD (Droit de Douane): Customs duty on CIF value
- TVA (Taxe sur la Valeur Ajoutée): VAT on (CIF + DD)
- DAPS (Droit Additionnel Provisoire de Sauvegarde): Safeguard duty
- TIC (Taxe Intérieure de Consommation): Excise tax
- PRCT (Prélèvement pour la Régulation du Commerce): Trade regulation levy
- TCS (Taxe sur le Chiffre d'affaires Spécifique): Specific turnover tax
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

# Tax configuration per country (Algeria as reference)
COUNTRY_TAX_CONFIG = {
    "DZA": {
        "name_fr": "Algérie",
        "name_en": "Algeria",
        "currency": "DZD",
        "vat_base": "cif_plus_dd",  # TVA is calculated on CIF + DD
        "taxes": {
            "DD": {"name_fr": "Droit de Douane", "name_en": "Customs Duty", "base": "cif", "order": 1},
            "TVA": {"name_fr": "TVA", "name_en": "VAT", "base": "cif_plus_dd", "order": 2},
            "DAPS": {"name_fr": "Droit Additionnel Provisoire", "name_en": "Additional Provisional Duty", "base": "cif", "order": 3},
            "TIC": {"name_fr": "Taxe Intérieure Consommation", "name_en": "Excise Tax", "base": "cif", "order": 4},
            "PRCT": {"name_fr": "Prélèvement Régulation Commerce", "name_en": "Trade Regulation Levy", "base": "cif", "order": 5},
        },
        "default_rates": {
            "DD": 0.30,  # 30% default
            "TVA": 0.19,  # 19% VAT
            "DAPS": 0.0,
            "TIC": 0.0,
            "PRCT": 0.0,
        }
    },
    "NGA": {
        "name_fr": "Nigéria",
        "name_en": "Nigeria",
        "currency": "NGN",
        "vat_base": "cif_plus_dd",
        "taxes": {
            "DD": {"name_fr": "Droit de Douane", "name_en": "Customs Duty", "base": "cif", "order": 1},
            "TVA": {"name_fr": "TVA", "name_en": "VAT", "base": "cif_plus_dd", "order": 2},
            "CISS": {"name_fr": "CISS", "name_en": "Comprehensive Import Supervision Scheme", "base": "cif", "order": 3},
            "ETLS": {"name_fr": "CEDEAO", "name_en": "ECOWAS Trade Liberalization Scheme", "base": "cif", "order": 4},
            "NAC": {"name_fr": "NAC", "name_en": "Nigerian Automotive Council", "base": "cif", "order": 5},
        },
        "default_rates": {
            "DD": 0.20,
            "TVA": 0.075,  # 7.5%
            "CISS": 0.01,
            "ETLS": 0.005,
            "NAC": 0.0,
        }
    },
    "MAR": {
        "name_fr": "Maroc",
        "name_en": "Morocco",
        "currency": "MAD",
        "vat_base": "cif_plus_dd",
        "taxes": {
            "DD": {"name_fr": "Droit d'Importation", "name_en": "Import Duty", "base": "cif", "order": 1},
            "TVA": {"name_fr": "TVA", "name_en": "VAT", "base": "cif_plus_dd", "order": 2},
            "TIC": {"name_fr": "Taxe Intérieure Consommation", "name_en": "Excise Tax", "base": "cif", "order": 3},
            "PFI": {"name_fr": "Prélèvement Fiscal Import", "name_en": "Import Fiscal Levy", "base": "cif", "order": 4},
        },
        "default_rates": {
            "DD": 0.25,
            "TVA": 0.20,
            "TIC": 0.0,
            "PFI": 0.0025,
        }
    },
    # Default for other countries
    "DEFAULT": {
        "name_fr": "Pays Africain",
        "name_en": "African Country",
        "currency": "USD",
        "vat_base": "cif_plus_dd",
        "taxes": {
            "DD": {"name_fr": "Droit de Douane", "name_en": "Customs Duty", "base": "cif", "order": 1},
            "TVA": {"name_fr": "TVA", "name_en": "VAT", "base": "cif_plus_dd", "order": 2},
            "OTHER": {"name_fr": "Autres Taxes", "name_en": "Other Taxes", "base": "cif", "order": 3},
        },
        "default_rates": {
            "DD": 0.20,
            "TVA": 0.18,
            "OTHER": 0.0,
        }
    }
}


@dataclass
class TaxLine:
    """Single tax line in calculation breakdown"""
    code: str
    name_fr: str
    name_en: str
    rate: float  # As decimal (0.19 for 19%)
    rate_pct: str  # Human readable "19%"
    base_type: str  # 'cif', 'cif_plus_dd', 'quantity'
    base_value: float
    amount: float
    is_zlecaf_exempt: bool = False
    notes: Optional[str] = None


@dataclass 
class CalculationBreakdown:
    """Complete calculation breakdown"""
    regime: str  # 'NPF' or 'ZLECAf'
    regime_name_fr: str
    regime_name_en: str
    fob_value: float
    freight: float
    insurance: float
    cif_value: float
    tax_lines: List[TaxLine]
    total_taxes: float
    total_to_pay: float
    currency: str


@dataclass
class ComparisonResult:
    """NPF vs ZLECAf comparison"""
    hs_code: str
    hs_code_description_fr: str
    hs_code_description_en: str
    country_iso3: str
    country_name_fr: str
    country_name_en: str
    npf_calculation: CalculationBreakdown
    zlecaf_calculation: CalculationBreakdown
    savings_amount: float
    savings_percent: float
    sub_positions: Optional[List[Dict]] = None
    data_source: str = "official_tariff"
    data_confidence: float = 0.9


class EnhancedTariffCalculator:
    """
    Enhanced calculator with detailed breakdown for NPF vs ZLECAf
    """
    
    def __init__(self):
        # Import here to avoid circular imports
        from etl.country_tariffs_complete import (
            get_tariff_rate_for_country,
            get_zlecaf_tariff_rate,
            get_vat_rate_for_country,
            get_other_taxes_for_country
        )
        from etl.country_hs6_tariffs import get_country_hs6_tariff
        from etl.country_hs6_detailed import get_detailed_tariff, get_all_sub_positions
        from etl.hs6_database import get_hs6_info
        
        self.get_tariff_rate = get_tariff_rate_for_country
        self.get_zlecaf_rate = get_zlecaf_tariff_rate
        self.get_vat_rate = get_vat_rate_for_country
        self.get_other_taxes = get_other_taxes_for_country
        self.get_hs6_tariff = get_country_hs6_tariff
        self.get_detailed = get_detailed_tariff
        self.get_sub_positions = get_all_sub_positions
        self.get_hs6_info = get_hs6_info
    
    def _round_currency(self, value: float, decimals: int = 2) -> float:
        """Round to currency precision"""
        return float(Decimal(str(value)).quantize(Decimal(f'0.{"0" * decimals}'), rounding=ROUND_HALF_UP))
    
    def _get_country_config(self, country_iso3: str) -> Dict:
        """Get tax configuration for a country"""
        return COUNTRY_TAX_CONFIG.get(country_iso3, COUNTRY_TAX_CONFIG["DEFAULT"])
    
    def _get_tax_rates(self, country_iso3: str, hs_code: str) -> Dict[str, float]:
        """Get all applicable tax rates for a product in a country"""
        config = self._get_country_config(country_iso3)
        rates = dict(config["default_rates"])
        
        # Try to get specific HS6 tariff
        hs6 = hs_code[:6]
        try:
            specific = self.get_hs6_tariff(country_iso3, hs6)
            if specific and isinstance(specific, dict):
                rates["DD"] = specific.get("dd", rates["DD"])
        except Exception:
            pass
        
        # Try detailed tariff (with sub-positions)
        try:
            detailed = self.get_detailed(country_iso3, hs_code)
            if detailed and isinstance(detailed, dict):
                rates["DD"] = detailed.get("dd_rate", rates["DD"])
                # Add any specific taxes
                other_taxes = detailed.get("other_taxes", {})
                if isinstance(other_taxes, dict):
                    for tax_code, tax_rate in other_taxes.items():
                        rates[tax_code] = tax_rate
        except Exception:
            pass
        
        # Get country-level rates (these return tuples (rate, source))
        chapter = hs_code[:2]
        try:
            result = self.get_tariff_rate(country_iso3, chapter)
            if result:
                country_rate = result[0] if isinstance(result, tuple) else result
                if country_rate is not None:
                    rates["DD"] = country_rate
        except Exception:
            pass
        
        try:
            result = self.get_vat_rate(country_iso3)
            if result:
                vat = result[0] if isinstance(result, tuple) else result
                if vat is not None:
                    rates["TVA"] = vat
        except Exception:
            pass
        
        try:
            result = self.get_other_taxes(country_iso3)
            if result:
                other = result[0] if isinstance(result, tuple) else result
                if other and isinstance(other, (int, float)):
                    rates["OTHER"] = other
        except Exception:
            pass
        
        return rates
    
    def _calculate_regime(
        self, 
        regime: str,
        country_iso3: str,
        hs_code: str,
        fob_value: float,
        freight: float,
        insurance: float,
        tax_rates: Dict[str, float],
        zlecaf_exempt_taxes: List[str] = None
    ) -> CalculationBreakdown:
        """Calculate taxes for a specific regime (NPF or ZLECAf)"""
        
        config = self._get_country_config(country_iso3)
        zlecaf_exempt = zlecaf_exempt_taxes or ["DD"]  # By default, DD is exempt under ZLECAf
        
        cif_value = fob_value + freight + insurance
        tax_lines = []
        
        # Build ordered tax calculation
        taxes_config = config["taxes"]
        sorted_taxes = sorted(taxes_config.items(), key=lambda x: x[1].get("order", 99))
        
        cumulative = {"cif": cif_value, "dd": 0, "cif_plus_dd": cif_value}
        
        for tax_code, tax_info in sorted_taxes:
            rate = tax_rates.get(tax_code, 0)
            
            # Check if this tax is exempt under ZLECAf
            is_exempt = regime == "ZLECAf" and tax_code in zlecaf_exempt
            effective_rate = 0 if is_exempt else rate
            
            # Determine base value
            base_type = tax_info.get("base", "cif")
            if base_type == "cif":
                base_value = cumulative["cif"]
            elif base_type == "cif_plus_dd":
                base_value = cumulative["cif_plus_dd"]
            else:
                base_value = cumulative["cif"]
            
            amount = self._round_currency(base_value * effective_rate)
            
            # Update cumulative values
            if tax_code == "DD":
                cumulative["dd"] = amount
                cumulative["cif_plus_dd"] = cif_value + amount
            
            tax_lines.append(TaxLine(
                code=tax_code,
                name_fr=tax_info["name_fr"],
                name_en=tax_info["name_en"],
                rate=effective_rate,
                rate_pct=f"{effective_rate * 100:.1f}%",
                base_type=base_type,
                base_value=self._round_currency(base_value),
                amount=amount,
                is_zlecaf_exempt=is_exempt,
                notes="Exonéré ZLECAf" if is_exempt else None
            ))
        
        total_taxes = sum(tl.amount for tl in tax_lines)
        total_to_pay = self._round_currency(cif_value + total_taxes)
        
        regime_names = {
            "NPF": ("Régime NPF (Nation la Plus Favorisée)", "MFN Regime (Most Favored Nation)"),
            "ZLECAf": ("Régime ZLECAf (Zone de Libre-Échange)", "AfCFTA Regime (Free Trade Area)")
        }
        
        return CalculationBreakdown(
            regime=regime,
            regime_name_fr=regime_names[regime][0],
            regime_name_en=regime_names[regime][1],
            fob_value=self._round_currency(fob_value),
            freight=self._round_currency(freight),
            insurance=self._round_currency(insurance),
            cif_value=self._round_currency(cif_value),
            tax_lines=tax_lines,
            total_taxes=self._round_currency(total_taxes),
            total_to_pay=total_to_pay,
            currency=config.get("currency", "USD")
        )
    
    def calculate_comparison(
        self,
        country_iso3: str,
        hs_code: str,
        fob_value: float,
        freight: float = 0,
        insurance: float = 0,
        language: str = "fr"
    ) -> ComparisonResult:
        """
        Calculate detailed comparison between NPF and ZLECAf regimes
        
        Args:
            country_iso3: ISO3 country code (e.g., "DZA", "NGA")
            hs_code: HS code (6-12 digits)
            fob_value: FOB value in USD
            freight: Freight cost in USD
            insurance: Insurance cost in USD
            language: Language for descriptions ("fr" or "en")
        
        Returns:
            ComparisonResult with detailed breakdowns
        """
        hs6 = hs_code[:6]
        
        # Get product description
        hs_info = self.get_hs6_info(hs6, language)
        desc_fr = hs_info.get("description_fr", "") if hs_info else ""
        desc_en = hs_info.get("description_en", "") if hs_info else ""
        
        # Get country info
        config = self._get_country_config(country_iso3)
        
        # Get tax rates
        tax_rates = self._get_tax_rates(country_iso3, hs_code)
        
        # Calculate NPF regime
        npf_calc = self._calculate_regime(
            regime="NPF",
            country_iso3=country_iso3,
            hs_code=hs_code,
            fob_value=fob_value,
            freight=freight,
            insurance=insurance,
            tax_rates=tax_rates
        )
        
        # Calculate ZLECAf regime (DD exempt)
        zlecaf_calc = self._calculate_regime(
            regime="ZLECAf",
            country_iso3=country_iso3,
            hs_code=hs_code,
            fob_value=fob_value,
            freight=freight,
            insurance=insurance,
            tax_rates=tax_rates,
            zlecaf_exempt_taxes=["DD", "DAPS"]  # Customs duty and additional duties exempt
        )
        
        # Calculate savings
        savings_amount = self._round_currency(npf_calc.total_to_pay - zlecaf_calc.total_to_pay)
        savings_percent = self._round_currency(
            (savings_amount / npf_calc.total_to_pay * 100) if npf_calc.total_to_pay > 0 else 0,
            1
        )
        
        # Get sub-positions if available
        sub_positions = self.get_sub_positions(country_iso3, hs6)
        
        return ComparisonResult(
            hs_code=hs_code,
            hs_code_description_fr=desc_fr,
            hs_code_description_en=desc_en,
            country_iso3=country_iso3,
            country_name_fr=config["name_fr"],
            country_name_en=config["name_en"],
            npf_calculation=npf_calc,
            zlecaf_calculation=zlecaf_calc,
            savings_amount=savings_amount,
            savings_percent=savings_percent,
            sub_positions=sub_positions,
            data_source="official_tariff",
            data_confidence=0.9
        )
    
    def to_dict(self, result: ComparisonResult) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization"""
        def convert(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return {k: convert(v) for k, v in asdict(obj).items()}
            elif isinstance(obj, list):
                return [convert(item) for item in obj]
            else:
                return obj
        
        return convert(result)


# Singleton instance
enhanced_calculator = EnhancedTariffCalculator()


def calculate_detailed_tariff(
    country_iso3: str,
    hs_code: str,
    fob_value: float,
    freight: float = 0,
    insurance: float = 0,
    language: str = "fr"
) -> Dict[str, Any]:
    """
    Main function to calculate detailed tariff comparison
    
    Returns:
        Dictionary with NPF vs ZLECAf breakdown
    """
    result = enhanced_calculator.calculate_comparison(
        country_iso3=country_iso3,
        hs_code=hs_code,
        fob_value=fob_value,
        freight=freight,
        insurance=insurance,
        language=language
    )
    return enhanced_calculator.to_dict(result)
