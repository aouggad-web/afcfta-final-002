"""
Insurance API routes – ZLECAf (finance.insurance sub-module)

Endpoints:
  GET  /insurance/insurers                                ← global insurer directory
  GET  /insurance/countries/{country_code}/profile         ← country insurance profile
  GET  /insurance/countries/{country_code}/premium-adjustments
  POST /insurance/quote                                    ← single product quote
  POST /insurance/quotes/batch                              ← compare quotes across products
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from finance.insurance import (
    MAJOR_INSURERS,
    batch_calculate_quotes,
    calculate_insurance_quote,
    get_country_insurance_profile,
    get_premium_adjustments_for_country,
)
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/insurance")


class InsuranceQuoteRequest(BaseModel):
    """Request for a single insurance premium quote"""

    country_code: str = Field(..., description="ISO2 code of buyer/counterparty country")
    product_type: str = Field(
        ...,
        description=(
            "export_credit | political_risk | performance_guarantee | "
            "advance_payment | tender | transport"
        ),
    )
    contract_value_usd: float = Field(..., description="Transaction value in USD", gt=0)
    payment_terms_days: int = Field(default=90, description="Payment terms in days", ge=1)
    sector: Optional[str] = Field(None, description="Business sector (optional)")
    buyer_rating: Optional[str] = Field(None, description="Buyer credit rating: AAA..D (optional)")


class BatchQuoteRequest(BaseModel):
    """Request comparing quotes across multiple insurance products"""

    country_code: str = Field(..., description="ISO2 code of buyer/counterparty country")
    contract_value_usd: float = Field(..., description="Transaction value in USD", gt=0)
    product_types: Optional[List[str]] = Field(
        None,
        description="Product types to compare; defaults to export_credit, political_risk, "
        "performance_guarantee",
    )


@router.get(
    "/insurers",
    summary="Global directory of major insurers active in Africa",
    tags=["Insurance"],
)
async def list_insurers(
    country_code: Optional[str] = Query(None, description="Filter by ISO2 code")
):
    """
    List major credit/political-risk insurers (COFACE, SMAEX, SARA, COTUNACE,
    Atradius, Zurich, UK Export Finance) operating in African markets.

    - **country_code**: optional ISO2 filter — only insurers active in that country
    """
    insurers = list(MAJOR_INSURERS.values())
    if country_code:
        code = country_code.upper()
        insurers = [ins for ins in insurers if code in (ins.active_countries or [])]

    return {
        "success": True,
        "total": len(insurers),
        "insurers": [ins.model_dump() for ins in insurers],
    }


@router.get(
    "/countries/{country_code}/profile",
    summary="Insurance profile for a country",
    tags=["Insurance"],
)
async def get_country_profile(country_code: str):
    """
    Get the full insurance profile for a country: risk level, available
    insurers, available products, and market confidence.

    Linked to the same country risk assessment used by trade finance.
    """
    profile = get_country_insurance_profile(country_code.upper())
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"No insurance profile available for {country_code}",
        )
    return {"success": True, "profile": profile.model_dump()}


@router.get(
    "/countries/{country_code}/premium-adjustments",
    summary="Premium adjustment breakdown for a country",
    tags=["Insurance"],
)
async def get_premium_adjustments(country_code: str):
    """
    Get a transparent breakdown of what drives insurance pricing for a
    country: base risk factors, total adjustment %, market confidence.
    """
    result = get_premium_adjustments_for_country(country_code.upper())
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return {"success": True, **result}


@router.post(
    "/quote",
    summary="Calculate an insurance premium quote",
    tags=["Insurance"],
)
async def get_quote(request: InsuranceQuoteRequest):
    """
    Calculate an insurance premium quote for a specific transaction.

    Adjustments applied: country risk, payment terms, contract value,
    sector, and buyer credit rating (all optional except country + amount).

    **Example:**
    ```json
    {
      "country_code": "DZ",
      "product_type": "export_credit",
      "contract_value_usd": 500000,
      "payment_terms_days": 120,
      "sector": "manufacturing"
    }
    ```
    """
    try:
        from banking_system.models import InsuranceProductType

        try:
            product_type = InsuranceProductType(request.product_type)
        except ValueError:
            valid = [p.value for p in InsuranceProductType]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid product_type '{request.product_type}'. Valid: {valid}",
            )

        quote = calculate_insurance_quote(
            country_code=request.country_code.upper(),
            product_type=product_type,
            contract_value_usd=request.contract_value_usd,
            payment_terms_days=request.payment_terms_days,
            sector=request.sector,
            buyer_rating=request.buyer_rating,
        )

        if not quote:
            raise HTTPException(
                status_code=404,
                detail=f"Product '{request.product_type}' not available for "
                f"{request.country_code}",
            )

        return {"success": True, "quote": quote.model_dump()}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Insurance quote error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/quotes/batch",
    summary="Compare insurance quotes across products",
    tags=["Insurance"],
)
async def get_batch_quotes(request: BatchQuoteRequest):
    """
    Compare insurance premium quotes across multiple product types for
    the same transaction — useful for comparison shopping.

    Defaults to comparing export_credit, political_risk, and
    performance_guarantee if `product_types` is omitted.
    """
    try:
        from banking_system.models import InsuranceProductType

        product_types = None
        if request.product_types:
            try:
                product_types = [InsuranceProductType(p) for p in request.product_types]
            except ValueError:
                valid = [p.value for p in InsuranceProductType]
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid product_types. Valid values: {valid}",
                )

        result = batch_calculate_quotes(
            country_code=request.country_code.upper(),
            contract_value_usd=request.contract_value_usd,
            product_types=product_types,
        )

        return {"success": True, **result}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Batch quote error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
