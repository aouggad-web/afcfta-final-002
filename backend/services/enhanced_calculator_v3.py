"""
Enhanced Calculator v3 - Regional African Trade Calculator.

Extends the existing tariff calculator with regional features:
- Best trade route finder (DZA, MAR, EGY, TUN; CMR, CAF, TCD, COG, GNQ, GAB)
- Cross-border transit optimization
- Preferential agreement stacking
- Free zone arbitrage analysis
- Regional total cost calculation
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from config.regional_config import (
    NORTH_AFRICA_COUNTRIES,
    NORTH_AFRICA_VAT_RATES,
    CEMAC_COUNTRIES,
    CEMAC_VAT_RATES,
)

logger = logging.getLogger(__name__)

# Regional tariff context - approximate DD rate bands used for route analysis
COUNTRY_DD_PROFILES: Dict[str, Dict[str, Any]] = {
    "DZA": {
        "country_name": "Algeria",
        "vat_rate": 19.0,
        "dd_bands": [0, 5, 15, 30],
        "special_taxes": ["PRCT", "TCS", "DAPS"],
        "eu_agreement": False,
        "comesa": False,
        "qiz": False,
    },
    "MAR": {
        "country_name": "Morocco",
        "vat_rate": 20.0,
        "dd_bands": [2.5, 10, 17.5, 25, 32.5, 40],
        "special_taxes": ["PI", "TIC", "TPCE"],
        "eu_agreement": True,
        "efta_agreement": True,
        "agadir": True,
        "us_fta": True,
        "free_zones": ["Tanger-Med", "Casablanca Finance City"],
    },
    "EGY": {
        "country_name": "Egypt",
        "vat_rate": 14.0,
        "dd_bands": [0, 5, 10, 20, 40, 60],
        "special_taxes": ["SD", "DT", "ST"],
        "eu_agreement": True,
        "comesa": True,
        "qiz": True,
        "free_zones": ["SCZONE", "Port Said SEZ"],
    },
    "TUN": {
        "country_name": "Tunisia",
        "vat_rate": 19.0,
        "dd_bands": [0, 10, 20, 30, 36],
        "special_taxes": ["FODEC", "TCL", "DC"],
        "eu_agreement": True,
        "agadir": True,
        "eu_integration": "most_advanced",
        "offshore_regime": True,
    },
    # CEMAC countries
    "CMR": {
        "country_name": "Cameroon",
        "vat_rate": CEMAC_VAT_RATES["CMR"],
        "dd_bands": [5, 10, 20, 30],  # CEMAC CET: 5/10/20/30%
        "special_taxes": ["CAC", "EC"],
        "cemac": True,
        "eccas": True,
        "free_zones": ["Kribi Free Trade Zone"],
    },
    "CAF": {
        "country_name": "Central African Republic",
        "vat_rate": CEMAC_VAT_RATES["CAF"],
        "dd_bands": [5, 10, 20, 30],
        "special_taxes": ["EC"],
        "cemac": True,
        "eccas": True,
        "free_zones": [],
    },
    "TCD": {
        "country_name": "Chad",
        "vat_rate": CEMAC_VAT_RATES["TCD"],
        "dd_bands": [5, 10, 20, 30],
        "special_taxes": ["EC"],
        "cemac": True,
        "eccas": True,
        "free_zones": [],
    },
    "COG": {
        "country_name": "Republic of the Congo",
        "vat_rate": CEMAC_VAT_RATES["COG"],
        "dd_bands": [5, 10, 20, 30],
        "special_taxes": ["EC"],
        "cemac": True,
        "eccas": True,
        "free_zones": ["Pointe-Noire Free Zone"],
    },
    "GNQ": {
        "country_name": "Equatorial Guinea",
        "vat_rate": CEMAC_VAT_RATES["GNQ"],
        "dd_bands": [5, 10, 20, 30],
        "special_taxes": ["EC"],
        "cemac": True,
        "eccas": True,
        "free_zones": [],
    },
    "GAB": {
        "country_name": "Gabon",
        "vat_rate": CEMAC_VAT_RATES["GAB"],
        "dd_bands": [5, 10, 20, 30],
        "special_taxes": ["EC"],
        "cemac": True,
        "eccas": True,
        "free_zones": ["Nkok Special Economic Zone"],
    },
}

# Trade route definitions for optimization
TRADE_ROUTES: List[Dict[str, Any]] = [
    {
        "route_id": "DZA_DIRECT",
        "label": "Algeria Direct",
        "path": ["DZA"],
        "target_market": "DZA",
        "notes": "Direct import to Algeria",
    },
    {
        "route_id": "MAR_EU_GATEWAY",
        "label": "Morocco → EU Gateway",
        "path": ["MAR", "EU"],
        "target_market": "EU",
        "notes": "Use Morocco EU Association Agreement for EU market access",
    },
    {
        "route_id": "TUN_EU_DEEP",
        "label": "Tunisia → EU (Deep Integration)",
        "path": ["TUN", "EU"],
        "target_market": "EU",
        "notes": "Tunisia's most advanced EU association; best for EU-destination goods",
    },
    {
        "route_id": "EGY_US_QIZ",
        "label": "Egypt QIZ → US",
        "path": ["EGY", "US"],
        "target_market": "US",
        "notes": "Egypt QIZ zones for preferential US market access",
    },
    {
        "route_id": "EGY_COMESA",
        "label": "Egypt → COMESA",
        "path": ["EGY", "COMESA"],
        "target_market": "COMESA",
        "notes": "Egypt COMESA preferential rates for East/Southern Africa",
    },
    {
        "route_id": "MAR_AGADIR",
        "label": "Morocco → Agadir (Arab countries)",
        "path": ["MAR", "AGADIR"],
        "target_market": "ARAB_COUNTRIES",
        "notes": "Morocco Agadir Agreement for Arab countries access",
    },
    {
        "route_id": "NORTH_AFRICA_REGIONAL",
        "label": "North Africa Regional (all 4 countries)",
        "path": ["DZA", "MAR", "EGY", "TUN"],
        "target_market": "NORTH_AFRICA",
        "notes": "Comprehensive regional market coverage",
    },
    {
        "route_id": "CEMAC_REGIONAL",
        "label": "CEMAC Regional (all 6 countries)",
        "path": ["CMR", "CAF", "TCD", "COG", "GNQ", "GAB"],
        "target_market": "CEMAC",
        "notes": "CEMAC Customs Union – harmonised external tariff (CET)",
    },
    {
        "route_id": "CMR_GATEWAY",
        "label": "Cameroon → Central Africa Gateway",
        "path": ["CMR"],
        "target_market": "CMR",
        "notes": "Cameroon: largest CEMAC economy and main Atlantic gateway",
    },
    {
        "route_id": "GAB_NKOK_SEZ",
        "label": "Gabon → Nkok SEZ",
        "path": ["GAB"],
        "target_market": "GAB",
        "notes": "Nkok Special Economic Zone for manufacturing and timber processing",
    },
]


class EnhancedCalculatorV3:
    """
    Enhanced tariff calculator with African regional intelligence.

    Provides:
    - Regional route comparison (North Africa: DZA/MAR/EGY/TUN; CEMAC: CMR/CAF/TCD/COG/GNQ/GAB)
    - Preferential agreement detection and stacking
    - Free zone arbitrage analysis
    - Total landed cost calculation per country
    - Investment decision support metrics
    """

    def __init__(self):
        self.country_profiles = COUNTRY_DD_PROFILES
        self.trade_routes = TRADE_ROUTES

    def calculate_country_taxes(
        self,
        country_code: str,
        hs_code: str,
        cif_value: float,
        dd_rate: Optional[float] = None,
        apply_vat: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculate total import taxes for a given country.

        Args:
            country_code: ISO3 country code (DZA/MAR/EGY/TUN)
            hs_code: HS tariff code
            cif_value: CIF value in USD
            dd_rate: Override DD rate (if known from crawled data)
            apply_vat: Whether to include VAT in calculation

        Returns:
            Dict with tax breakdown and total cost
        """
        profile = self.country_profiles.get(country_code, {})
        vat_rate = profile.get("vat_rate", NORTH_AFRICA_VAT_RATES.get(country_code, 0.0))

        if dd_rate is None:
            # Use middle of DD band as estimate
            bands = profile.get("dd_bands", [0])
            dd_rate = bands[len(bands) // 2] if bands else 0.0

        dd_amount = cif_value * dd_rate / 100
        taxable_base = cif_value + dd_amount
        vat_amount = taxable_base * vat_rate / 100 if apply_vat else 0.0

        total_taxes = dd_amount + vat_amount
        total_landed = cif_value + total_taxes

        return {
            "country_code": country_code,
            "country_name": profile.get("country_name", country_code),
            "hs_code": hs_code,
            "cif_value": cif_value,
            "dd_rate_pct": dd_rate,
            "dd_amount": round(dd_amount, 2),
            "vat_rate_pct": vat_rate,
            "vat_amount": round(vat_amount, 2),
            "total_taxes": round(total_taxes, 2),
            "total_landed_cost": round(total_landed, 2),
            "effective_rate_pct": round(total_taxes / cif_value * 100, 2) if cif_value else 0,
            "preferential_agreements": self._get_relevant_agreements(country_code),
            "special_zones": profile.get("free_zones", []),
        }

    def find_best_route(
        self,
        hs_code: str,
        cif_value: float,
        target_market: str = "NORTH_AFRICA",
        dd_rates: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Find the optimal trade route for the given target market.

        Args:
            hs_code: HS tariff code
            cif_value: CIF value in USD
            target_market: Target destination market (NORTH_AFRICA, CEMAC, or ISO3 code)
            dd_rates: Known DD rates per country from crawled data

        Returns:
            Dict with route ranking and cost comparison
        """
        dd_rates = dd_rates or {}

        if target_market == "CEMAC":
            countries = CEMAC_COUNTRIES
        else:
            countries = NORTH_AFRICA_COUNTRIES

        results = []
        for country_code in countries:
            dd_rate = dd_rates.get(country_code)
            calc = self.calculate_country_taxes(
                country_code=country_code,
                hs_code=hs_code,
                cif_value=cif_value,
                dd_rate=dd_rate,
            )
            results.append(calc)

        results.sort(key=lambda x: x["total_landed_cost"])

        return {
            "hs_code": hs_code,
            "cif_value": cif_value,
            "target_market": target_market,
            "rankings": results,
            "best_route": results[0] if results else None,
            "savings_vs_worst": (
                round(results[-1]["total_taxes"] - results[0]["total_taxes"], 2)
                if len(results) >= 2 else 0
            ),
        }

    def analyze_free_zone_arbitrage(
        self,
        hs_code: str,
        cif_value: float,
    ) -> List[Dict[str, Any]]:
        """
        Identify free zone arbitrage opportunities across North Africa.

        Args:
            hs_code: HS tariff code
            cif_value: CIF value in USD

        Returns:
            List of free zone opportunities with potential savings
        """
        opportunities = []
        for country_code, profile in self.country_profiles.items():
            zones = profile.get("free_zones", [])
            if not zones:
                continue
            for zone in zones:
                opportunities.append({
                    "country": country_code,
                    "country_name": profile.get("country_name", country_code),
                    "zone_name": zone,
                    "hs_code": hs_code,
                    "estimated_benefit": "Reduced or zero customs duties within zone",
                    "notes": f"Verify specific rates for HS {hs_code} in {zone}",
                })

        return opportunities

    def get_preferential_rates(
        self,
        hs_code: str,
        origin_country: str,
        destination: str,
    ) -> List[Dict[str, Any]]:
        """
        Get available preferential rates for a trade lane.

        Args:
            hs_code: HS tariff code
            origin_country: ISO3 origin country code
            destination: Destination market identifier

        Returns:
            List of applicable preferential agreements
        """
        rates = []
        dest_upper = destination.upper()

        for country_code, profile in self.country_profiles.items():
            if country_code != origin_country:
                continue

            if dest_upper == "EU" and profile.get("eu_agreement"):
                rates.append({
                    "agreement": "EU Association Agreement",
                    "origin": origin_country,
                    "destination": "EU",
                    "type": "preferential",
                    "note": f"{profile.get('country_name')} EU Association Agreement",
                })

            if dest_upper == "US" and profile.get("qiz"):
                rates.append({
                    "agreement": "QIZ (Qualified Industrial Zones)",
                    "origin": origin_country,
                    "destination": "US",
                    "type": "preferential",
                    "note": "Egypt QIZ zones - special US market access",
                })

            if dest_upper in ("COMESA", "EAST_AFRICA") and profile.get("comesa"):
                rates.append({
                    "agreement": "COMESA Preferential Rates",
                    "origin": origin_country,
                    "destination": "COMESA",
                    "type": "preferential",
                    "note": "Common Market for Eastern and Southern Africa rates",
                })

            if dest_upper in ("ARAB", "ARAB_COUNTRIES", "GAFTA") and profile.get("agadir"):
                rates.append({
                    "agreement": "Arab Free Trade Area (GAFTA)",
                    "origin": origin_country,
                    "destination": "Arab Countries",
                    "type": "preferential",
                    "note": "Pan-Arab Free Trade Area",
                })
            elif dest_upper in ("ARAB", "ARAB_COUNTRIES", "GAFTA") and not profile.get("agadir"):
                # GAFTA is broader than Agadir — applies to all North African countries
                rates.append({
                    "agreement": "Arab Free Trade Area (GAFTA)",
                    "origin": origin_country,
                    "destination": "Arab Countries",
                    "type": "preferential",
                    "note": "Pan-Arab Free Trade Area (GAFTA)",
                })

        return rates

    def _get_relevant_agreements(self, country_code: str) -> List[str]:
        """Get preferential agreements for a country."""
        profile = self.country_profiles.get(country_code, {})
        agreements = ["AFCFTA", "GAFTA"]
        if profile.get("eu_agreement"):
            agreements.append("EU Association Agreement")
        if profile.get("efta_agreement"):
            agreements.append("EFTA Agreement")
        if profile.get("agadir"):
            agreements.append("Agadir Agreement")
        if profile.get("us_fta"):
            agreements.append("US FTA")
        if profile.get("qiz"):
            agreements.append("QIZ (US market access)")
        if profile.get("comesa"):
            agreements.append("COMESA")
        return agreements

    def compare_regional_supply_chain(
        self,
        hs_codes: List[str],
        production_country: str,
        target_countries: Optional[List[str]] = None,
        unit_value: float = 1000.0,
    ) -> Dict[str, Any]:
        """
        Multi-country supply chain optimization analysis.

        Compares manufacturing/sourcing costs across North African countries
        for a set of HS codes, helping identify the best production base.

        Args:
            hs_codes: List of HS codes for components/products
            production_country: Country where manufacturing would occur
            target_countries: Countries to compare (defaults to all N. Africa)
            unit_value: Per-unit CIF value in USD

        Returns:
            Supply chain optimization report
        """
        target_countries = target_countries or NORTH_AFRICA_COUNTRIES

        total_by_country: Dict[str, float] = {c: 0.0 for c in target_countries}
        details_by_hs: Dict[str, Dict] = {}

        for hs_code in hs_codes:
            hs_results = []
            for country in target_countries:
                calc = self.calculate_country_taxes(
                    country_code=country,
                    hs_code=hs_code,
                    cif_value=unit_value,
                )
                total_by_country[country] += calc["total_taxes"]
                hs_results.append({
                    "country": country,
                    "total_taxes": calc["total_taxes"],
                    "landed_cost": calc["total_landed_cost"],
                })
            details_by_hs[hs_code] = sorted(hs_results, key=lambda x: x["total_taxes"])

        ranked = sorted(total_by_country.items(), key=lambda x: x[1])

        return {
            "production_country": production_country,
            "hs_codes_analyzed": hs_codes,
            "unit_value": unit_value,
            "total_tax_burden_by_country": dict(ranked),
            "optimal_country": ranked[0][0] if ranked else None,
            "savings_vs_worst": (
                round(ranked[-1][1] - ranked[0][1], 2) if len(ranked) >= 2 else 0
            ),
            "details_by_hs_code": details_by_hs,
        }


# Module-level singleton
_calculator: Optional[EnhancedCalculatorV3] = None


def get_enhanced_calculator() -> EnhancedCalculatorV3:
    """Get or create the singleton EnhancedCalculatorV3."""
    global _calculator
    if _calculator is None:
        _calculator = EnhancedCalculatorV3()
    return _calculator
