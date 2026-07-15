"""
<<<<<<< HEAD
Insurance premium calculation and pricing analysis for AfCFTA trade.

Provides:
- Premium calculation with risk adjustments
- Cost-benefit analysis for insurance strategies
- Multi-product comparison and recommendations
"""

from typing import Dict, Optional

from .insurance_registry import get_country_insurance_profile
from .models import InsuranceProductType, InsuranceQuote
=======
Insurance premium pricing engine for AfCFTA.

Calculates insurance premiums based on:
- Country risk level (linked to risk_assessment module)
- Contract value and terms
- Product type
- Sector (if available)
- Additional risk factors (forex risk, payment terms, etc.)
"""

from typing import Optional

from . import risk_assessment
from .insurance_registry import get_country_insurance_profile
from .models.insurance_models import (
    InsuranceCoverageScope,
    InsuranceProductType,
    InsuranceQuote,
    InsuranceRiskLevel,
)
>>>>>>> origin/main


def calculate_insurance_quote(
    country_code: str,
    product_type: InsuranceProductType,
<<<<<<< HEAD
    amount_usd: float,
    payment_terms_days: int = 90,
    sector: Optional[str] = None,
    buyer_rating: str = "standard",
) -> InsuranceQuote:
    """
    Calculate insurance premium for a specific transaction.

    Args:
        country_code: ISO2 code of trade partner
        product_type: Type of insurance product
        amount_usd: Transaction value
        payment_terms_days: Payment terms (impacts premium)
        sector: Business sector (some sectors have higher premiums)
        buyer_rating: Buyer credit rating (standard | excellent | poor)

    Returns:
        InsuranceQuote with premium breakdown
    """
    country_code = country_code.upper()
    profile = get_country_insurance_profile(country_code)

    # Find the product
    product = None
    for p in profile.available_products:
        if p.product_type == product_type:
            product = p
            break

    if not product:
        raise ValueError(f"Product {product_type} not available for {country_code}")

    # Calculate base premium
    base_premium_pct = product.premium_rate_basis_points / 100.0
    base_premium_usd = amount_usd * (base_premium_pct / 100.0)

    # Ensure minimum premium
    if base_premium_usd < product.min_premium_usd:
        base_premium_usd = product.min_premium_usd

    # Calculate adjustments
    adjustments = {}

    # 1. Payment terms adjustment (longer terms = higher risk)
    if payment_terms_days > 180:
        if payment_terms_days > 360:
            term_adjustment = 0.03  # +3%
        else:
            term_adjustment = 0.015  # +1.5%
        adjustments["payment_terms_long"] = base_premium_usd * term_adjustment

    # 2. Transaction size adjustment
    if amount_usd > 1_000_000:
        size_adjustment = -0.01  # -1% for volume discount
        adjustments["volume_discount"] = base_premium_usd * size_adjustment
    elif amount_usd < 50_000:
        size_adjustment = 0.005  # +0.5% for small transactions
        adjustments["small_transaction_fee"] = base_premium_usd * size_adjustment

    # 3. Sector adjustment
    high_risk_sectors = ["arms", "weapons", "nuclear", "aerospace"]
    if sector and sector.lower() in high_risk_sectors:
        sector_adjustment = 0.05  # +5%
        adjustments["high_risk_sector"] = base_premium_usd * sector_adjustment

    # 4. Buyer rating adjustment
    buyer_adjustments = {
        "excellent": -0.02,  # -2%
        "standard": 0.0,
        "poor": 0.15,  # +15%
    }
    buyer_adj = buyer_adjustments.get(buyer_rating.lower(), 0.0)
    if buyer_adj != 0:
        adjustments[f"buyer_rating_{buyer_rating}"] = base_premium_usd * buyer_adj

    # Sum all adjustments
    total_adjustments = sum(adjustments.values())
    adjusted_premium_usd = base_premium_usd + total_adjustments

    # Annual premium (assume same as one-time)
    total_annual_premium = adjusted_premium_usd

    return InsuranceQuote(
        country_code=country_code,
        product_type=product_type,
        amount_usd=amount_usd,
        base_premium_usd=round(base_premium_usd, 2),
        adjustments={k: round(v, 2) for k, v in adjustments.items()},
        adjusted_premium_usd=round(adjusted_premium_usd, 2),
        total_annual_premium_usd=round(total_annual_premium, 2),
        coverage_usd=round(amount_usd * (product.coverage_percent / 100.0), 2),
        coverage_percent=product.coverage_percent,
        quote_valid_days=30,
    )


def batch_calculate_quotes(
    country_code: str,
    amount_usd: float,
    payment_terms_days: int = 90,
    sector: Optional[str] = None,
    buyer_rating: str = "standard",
) -> Dict:
    """
    Compare insurance quotes for all products available in a country.

    Returns:
        Dict with all product quotes sorted by net cost
    """
    country_code = country_code.upper()
    profile = get_country_insurance_profile(country_code)

    quotes = []
    for product in profile.available_products:
        quote = calculate_insurance_quote(
            country_code,
            product.product_type,
            amount_usd,
            payment_terms_days=payment_terms_days,
            sector=sector,
            buyer_rating=buyer_rating,
        )
        quotes.append(
            {
                "product_name_en": product.name_en,
                "product_name_fr": product.name_fr,
                "product_type": product.product_type.value,
                "coverage_percent": product.coverage_percent,
                "base_premium_usd": quote.base_premium_usd,
                "adjusted_premium_usd": quote.adjusted_premium_usd,
                "coverage_usd": quote.coverage_usd,
                "cost_per_1k_usd": round((quote.adjusted_premium_usd / amount_usd) * 1000, 2),
            }
        )

    # Sort by adjusted premium (lowest first)
    quotes.sort(key=lambda q: q["adjusted_premium_usd"])

    return {
        "country_code": country_code,
        "country_name": profile.country_name,
        "amount_usd": amount_usd,
=======
    contract_value_usd: float,
    payment_terms_days: int = 90,
    sector: Optional[str] = None,
    buyer_rating: Optional[str] = None,
) -> Optional[InsuranceQuote]:
    """
    Calculate insurance premium quote for a transaction.

    Args:
        country_code: ISO2 code of buyer/counterparty country
        product_type: Type of insurance product
        contract_value_usd: Transaction value in USD
        payment_terms_days: Payment terms in days
        sector: Business sector (optional, for adjustment)
        buyer_rating: Credit rating of specific buyer (optional)

    Returns:
        InsuranceQuote with calculated premium or None if unavailable
    """

    # Get country insurance profile (linked to risk assessment)
    insurance_profile = get_country_insurance_profile(country_code)
    if not insurance_profile:
        return None

    risk_level = insurance_profile.risk_level

    # Find applicable product for this country
    applicable_product = None
    for product in insurance_profile.available_products:
        if product.product_type == product_type:
            applicable_product = product
            break

    if not applicable_product:
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # BASE PREMIUM CALCULATION
    # ─────────────────────────────────────────────────────────────────────────

    base_rate_bps = applicable_product.premium_rate_basis_points
    base_premium = (contract_value_usd * base_rate_bps) / 10_000

    # ─────────────────────────────────────────────────────────────────────────
    # ADJUSTMENTS BASED ON MULTIPLE RISK FACTORS
    # ─────────────────────────────────────────────────────────────────────────

    adjustment_percent = insurance_profile.premium_adjustment_percent

    # Adjustment for payment terms (longer terms = higher risk)
    if payment_terms_days > 180:
        if payment_terms_days <= 360:
            adjustment_percent += 1.5
        else:
            adjustment_percent += 3.0

    # Adjustment for contract value (larger contracts = potentially better terms)
    if contract_value_usd > 1_000_000:
        adjustment_percent -= 1.0  # 1% volume discount
    elif contract_value_usd < 50_000:
        adjustment_percent += 0.5  # Small transaction premium

    # Sector-based adjustments (high-risk sectors cost more)
    high_risk_sectors = ["arms", "tobacco", "weapons", "nuclear"]
    if sector and sector.lower() in high_risk_sectors:
        adjustment_percent += 5.0

    # Buyer-specific adjustment (if credit rating known)
    if buyer_rating:
        rating_adjustment = {
            "AAA": -2.0,
            "AA": -1.5,
            "A": -1.0,
            "BBB": 0.0,
            "BB": 2.0,
            "B": 3.5,
            "CCC": 5.0,
            "CC": 7.5,
            "C": 10.0,
            "D": 15.0,
        }
        adjustment_percent += rating_adjustment.get(buyer_rating, 0.0)

    # ─────────────────────────────────────────────────────────────────────────
    # COVERAGE AND DEDUCTIBLE CALCULATION
    # ─────────────────────────────────────────────────────────────────────────

    coverage_usd = contract_value_usd * (applicable_product.coverage_percent / 100.0)
    deductible_usd = contract_value_usd * (applicable_product.deductible_percent / 100.0)

    # ─────────────────────────────────────────────────────────────────────────
    # FINAL PREMIUM WITH ADJUSTMENTS
    # ─────────────────────────────────────────────────────────────────────────

    adjusted_rate_bps = base_rate_bps * ((100 + adjustment_percent) / 100.0)
    final_premium = (contract_value_usd * adjusted_rate_bps) / 10_000

    # Apply minimum premium if applicable
    if applicable_product.min_premium_usd:
        final_premium = max(final_premium, applicable_product.min_premium_usd)

    # ─────────────────────────────────────────────────────────────────────────
    # BUILD QUOTE OBJECT
    # ─────────────────────────────────────────────────────────────────────────

    quote = InsuranceQuote(
        country_code=country_code,
        product_type=product_type,
        contract_value_usd=contract_value_usd,
        risk_level=risk_level,
        payment_terms_days=payment_terms_days,
        premium_rate_bps=adjusted_rate_bps,
        base_premium_usd=base_premium,
        risk_adjustment_percent=adjustment_percent,
        final_premium_usd=final_premium,
        min_premium_usd=applicable_product.min_premium_usd,
        coverage_usd=coverage_usd,
        deductible_usd=deductible_usd,
        validity_days=365,
        notes=_build_quote_notes(
            country_code,
            risk_level,
            product_type,
            adjustment_percent,
        ),
    )

    return quote


def get_premium_adjustments_for_country(country_code: str) -> dict:
    """
    Get detailed breakdown of premium adjustments for a country.
    Useful for transparency and customer education.
    """
    insurance_profile = get_country_insurance_profile(country_code)
    if not insurance_profile:
        return {"error": "Country not found"}

    risk_profile = risk_assessment.get_country_risk(country_code)

    return {
        "country_code": country_code,
        "country_name": insurance_profile.country_name,
        "insurance_risk_level": insurance_profile.risk_level.value,
        "country_risk_rating": risk_profile.country_risk_rating,
        "base_adjustments": {
            "forex_risk": risk_profile.forex_risk,
            "political_risk": risk_profile.political_risk,
            "transfer_risk": risk_profile.transfer_risk,
        },
        "total_premium_adjustment_percent": insurance_profile.premium_adjustment_percent,
        "market_confidence": insurance_profile.market_confidence,
        "available_insurers_count": len(insurance_profile.available_insurers),
        "available_products_count": len(insurance_profile.available_products),
        "notes": insurance_profile.notes,
    }


def batch_calculate_quotes(
    country_code: str,
    contract_value_usd: float,
    product_types: Optional[list] = None,
) -> dict:
    """
    Calculate quotes for all applicable products in a country.
    Useful for comparison shopping.
    """
    if product_types is None:
        product_types = [
            InsuranceProductType.EXPORT_CREDIT,
            InsuranceProductType.POLITICAL_RISK,
            InsuranceProductType.PERFORMANCE_GUARANTEE,
        ]

    quotes = {}
    for product_type in product_types:
        quote = calculate_insurance_quote(
            country_code=country_code,
            product_type=product_type,
            contract_value_usd=contract_value_usd,
        )
        if quote:
            quotes[product_type.value] = quote.model_dump()

    return {
        "country_code": country_code,
        "contract_value_usd": contract_value_usd,
>>>>>>> origin/main
        "quotes": quotes,
    }


<<<<<<< HEAD
def get_premium_adjustments_for_country(
    country_code: str,
) -> Dict:
    """
    Get breakdown of premium adjustment factors for a country.

    Useful for understanding what drives pricing.
    """
    profile = get_country_insurance_profile(country_code)

    return {
        "country_code": country_code,
        "country_name": profile.country_name,
        "risk_level": profile.risk_level.value,
        "base_premium_rate_pct": profile.base_premium_rate_pct,
        "adjustment_factors": {
            "payment_terms": "Long-term (>180 days) adds 1.5-3% to premium",
            "transaction_size": "Large amounts (>$1M) get 1% discount; small (<$50k) add 0.5%",
            "sector": "High-risk sectors (arms, nuclear, aerospace) add 5%",
            "buyer_rating": "Rating ranges from -2% (excellent) to +15% (poor)",
        },
        "typical_cost_per_1k_usd": round(profile.base_premium_rate_pct / 10, 2),
        "market_confidence": profile.market_confidence,
    }
=======
def _build_quote_notes(
    country_code: str,
    risk_level: InsuranceRiskLevel,
    product_type: InsuranceProductType,
    adjustment_percent: float,
) -> str:
    """Build explanatory notes for the insurance quote."""
    notes_map = {
        InsuranceRiskLevel.VERY_LOW: "Very low risk country with favorable insurance terms.",
        InsuranceRiskLevel.LOW: "Low risk country with standard insurance terms.",
        InsuranceRiskLevel.MODERATE: "Moderate risk country with average premium adjustment.",
        InsuranceRiskLevel.HIGH: (
            "High risk country. Insurance premiums elevated due to elevated political/forex risks."
        ),
        InsuranceRiskLevel.VERY_HIGH: (
            "Very high risk country. Limited insurance availability. "
            "Consider risk mitigation strategies."
        ),
    }

    base_note = notes_map.get(risk_level, "Standard terms apply.")

    if adjustment_percent < -1:
        base_note += f" Volume discount: {abs(adjustment_percent):.1f}%"
    elif adjustment_percent > 1:
        base_note += f" Risk premium: +{adjustment_percent:.1f}%"

    return base_note
>>>>>>> origin/main
