"""
Insurance premium calculation and pricing analysis for AfCFTA trade.

Provides:
- Premium calculation with risk adjustments
- Cost-benefit analysis for insurance strategies
- Multi-product comparison and recommendations
"""

from typing import Dict, List, Optional

from .insurance_registry import get_available_products, get_country_insurance_profile
from .models import InsuranceProductType, InsuranceQuote
from .risk_assessment import get_country_risk


def calculate_insurance_quote(
    country_code: str,
    product_type: InsuranceProductType,
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
        "quotes": quotes,
    }


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
