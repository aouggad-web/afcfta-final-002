"""
Banking system enhancements API routes – 4 new modules

Endpoints:
  POST /banking/recommendations                  ← Option 1: Intelligent recommendations
  POST /banking/banks/score                      ← Option 2: Enhanced bank scoring
  POST /banking/forex/hedging-strategy           ← Option 3: FX hedging strategies
  GET  /banking/finance/matrix/{matrix_type}     ← Option 4: Financing matrix
"""

import logging
from typing import List, Optional

from banking_system import (
    get_country_banks,
    get_trade_recommendations,
)
from banking_system.bank_scoring import (
    score_banks_for_transaction,
)
from banking_system.financing_matrix import FinancingMatrix
from banking_system.forex_hedging import (
    get_hedging_cost_comparison,
    recommend_hedging_strategy,
)
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/banking")


# ---------------------------------------------------------------------------
# REQUEST/RESPONSE MODELS
# ---------------------------------------------------------------------------


class TradeRecommendationRequest(BaseModel):
    """Request for intelligent trade recommendations (Option 1)"""

    country_code: str = Field(..., description="ISO2 code of trade partner")
    amount_usd: float = Field(..., description="Transaction value in USD", ge=10000)
    sector: Optional[str] = Field(
        None, description="Business sector (e.g., manufacturing, agriculture)"
    )
    transaction_type: str = Field(
        default="export",
        description="export | import | supply_chain",
    )


class BankScoringRequest(BaseModel):
    """Request for bank scoring (Option 2)"""

    country_code: str = Field(..., description="ISO2 code of trade partner")
    amount_usd: float = Field(..., description="Transaction value in USD")
    transaction_type: str = Field(
        default="export",
        description="export | import | supply_chain | general",
    )
    sector: Optional[str] = Field(None, description="Business sector")
    limit: int = Field(default=5, description="Max banks to return", ge=1, le=20)


class FXHedgingRequest(BaseModel):
    """Request for FX hedging strategy (Option 3)"""

    country_code: str = Field(..., description="ISO2 code of counterparty")
    amount_usd: float = Field(..., description="Transaction value in USD")
    transaction_days: int = Field(default=90, description="Horizon in days", ge=1, le=730)
    transaction_type: str = Field(default="export", description="export | import")


# ---------------------------------------------------------------------------
# OPTION 1: INTELLIGENT BANKING RECOMMENDATIONS
# ---------------------------------------------------------------------------


@router.post(
    "/recommendations",
    summary="Option 1: Intelligent trade finance recommendations",
    tags=["Enhancements", "Recommendations"],
)
async def get_intelligent_recommendations(request: TradeRecommendationRequest):
    """
    Get complete trade finance recommendations for a transaction.

    Includes:
    - Recommended trade finance instruments (ranked by suitability)
    - Suitable insurance products (with cost estimates)
    - Recommended banks (scored by capability)
    - Compliance requirements specific to country/sector

    **Example:**
    ```json
    {
      "country_code": "DZ",
      "amount_usd": 2000000,
      "sector": "manufacturing",
      "transaction_type": "export"
    }
    ```
    """
    try:
        recommendations = get_trade_recommendations(
            request.country_code,
            request.amount_usd,
            request.sector,
        )

        return {
            "success": True,
            "transaction": {
                "country_code": request.country_code,
                "amount_usd": request.amount_usd,
                "sector": request.sector,
            },
            "risk_profile": {
                "rating": recommendations["risk_assessment"]["country_risk_rating"],
                "forex_risk": recommendations["risk_assessment"]["forex_risk"],
                "political_risk": recommendations["risk_assessment"]["political_risk"],
            },
            "instruments": recommendations["recommended_instruments"],
            "insurance": recommendations["recommended_insurance"],
            "banks": recommendations["recommended_banks"],
            "compliance": recommendations["compliance_requirements"],
        }
    except Exception as exc:
        logger.error("Recommendation error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# OPTION 2: ENHANCED BANK SCORING
# ---------------------------------------------------------------------------


@router.post(
    "/banks/score",
    summary="Option 2: Score banks for suitability",
    tags=["Enhancements", "Banks"],
)
async def score_banks(request: BankScoringRequest):
    """
    Score and rank banks for a specific transaction.

    Scoring factors (weighted):
    - Geographic presence & regional expertise (30%)
    - Service offering alignment (25%)
    - Correspondent network quality (25%)
    - Transaction amount suitability (10%)
    - Specialization match (10%)

    **Example:**
    ```json
    {
      "country_code": "NG",
      "amount_usd": 1500000,
      "transaction_type": "export",
      "limit": 5
    }
    ```
    """
    try:
        banking_info = get_country_banks(request.country_code)
        if not banking_info or not banking_info.commercial_banks:
            raise HTTPException(
                status_code=404,
                detail=f"No banks found for {request.country_code}",
            )

        scored_banks = score_banks_for_transaction(
            banking_info.commercial_banks,
            request.country_code,
            transaction_type=request.transaction_type,
            amount_usd=request.amount_usd,
            sector=request.sector,
        )

        # Limit results
        scored_banks = scored_banks[: request.limit]

        return {
            "success": True,
            "country": {
                "code": request.country_code,
                "name": banking_info.country_name,
            },
            "transaction": {
                "type": request.transaction_type,
                "amount_usd": request.amount_usd,
            },
            "banks_scored": len(scored_banks),
            "banks": scored_banks,
            "summary": {
                "top_bank": scored_banks[0]["name"] if scored_banks else None,
                "avg_score": (
                    sum(b["score"] for b in scored_banks) / len(scored_banks) if scored_banks else 0
                ),
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Bank scoring error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# OPTION 3: FX HEDGING STRATEGIES
# ---------------------------------------------------------------------------


@router.post(
    "/forex/hedging-strategy",
    summary="Option 3: FX hedging strategy recommendations",
    tags=["Enhancements", "Forex"],
)
async def get_hedging_strategy(request: FXHedgingRequest):
    """
    Get FX hedging strategy recommendation with cost-benefit analysis.

    Evaluates hedging necessity (low/moderate/high/critical) based on:
    - Currency convertibility
    - Forex risk profile
    - Transaction horizon
    - Transaction amount

    Returns 6 ranked strategies with cost/effectiveness/net benefit.

    **Example:**
    ```json
    {
      "country_code": "DZ",
      "amount_usd": 2000000,
      "transaction_days": 120,
      "transaction_type": "export"
    }
    ```
    """
    try:
        recommendation = recommend_hedging_strategy(
            request.country_code,
            request.amount_usd,
            transaction_days=request.transaction_days,
            transaction_type=request.transaction_type,
        )

        # Also get cost comparison
        cost_comparison = get_hedging_cost_comparison(
            request.country_code,
            request.amount_usd,
            transaction_days=request.transaction_days,
        )

        return {
            "success": True,
            "transaction": {
                "country_code": request.country_code,
                "amount_usd": request.amount_usd,
                "horizon_days": request.transaction_days,
            },
            "risk_factors": recommendation["risk_factors"],
            "recommended_strategy": recommendation["recommended_strategy"],
            "explanation": recommendation["explanation"],
            "all_strategies": recommendation["all_strategies_ranked"],
            "cost_comparison": cost_comparison["strategies"],
        }
    except Exception as exc:
        logger.error("Hedging strategy error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# OPTION 4: FINANCING MATRIX
# ---------------------------------------------------------------------------


@router.get(
    "/finance/matrix/instruments",
    summary="Option 4a: Instrument comparison matrix",
    tags=["Enhancements", "Financing"],
)
async def get_instruments_matrix():
    """
    Get detailed comparison of all trade finance instruments.

    Shows for each instrument:
    - Cost (typical %)
    - Protection level (full/partial/limited)
    - Speed (fast/moderate/slow)
    - Suitability score (0-10)
    - Requirements & documentation
    """
    try:
        matrix = FinancingMatrix.get_instrument_comparison()
        return {
            "success": True,
            "total_instruments": matrix["total_instruments"],
            "instruments": matrix["instruments"],
        }
    except Exception as exc:
        logger.error("Instruments matrix error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/finance/matrix/by-risk",
    summary="Option 4b: Instruments recommended by country risk level",
    tags=["Enhancements", "Financing"],
)
async def get_risk_matrix():
    """
    Get instrument recommendations by country risk rating (A1-D).

    Shows for each risk level:
    - Example countries
    - Recommended instruments
    - Key considerations for that risk level
    """
    try:
        matrix = FinancingMatrix.get_risk_based_matrix()
        return {
            "success": True,
            "risk_levels": len(matrix),
            "matrix": matrix,
        }
    except Exception as exc:
        logger.error("Risk matrix error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/finance/matrix/by-size",
    summary="Option 4c: Instruments by transaction size",
    tags=["Enhancements", "Financing"],
)
async def get_size_matrix():
    """
    Get recommended instruments by transaction size bracket.

    Brackets: Micro ($0-50k), Small ($50k-250k), Medium ($250k-1M),
    Large ($1M-5M), Mega ($5M+)

    Shows cost range and key factors for each size.
    """
    try:
        matrix = FinancingMatrix.get_transaction_size_matrix()
        return {
            "success": True,
            "brackets": len(matrix),
            "matrix": matrix,
        }
    except Exception as exc:
        logger.error("Size matrix error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/finance/matrix/decision-tree",
    summary="Option 4d: Interactive decision tree for instrument selection",
    tags=["Enhancements", "Financing"],
)
async def get_decision_tree():
    """
    Get interactive decision tree for trade finance instrument selection.

    Follow the yes/no questions to navigate to optimal instrument:
    - Start: Is this export or import?
    - Then: What is country risk level?
    - Then: Do you trust your counterparty?
    - Result: Recommended instrument

    Useful for building interactive UI/chatbot flows.
    """
    try:
        tree = FinancingMatrix.get_quick_decision_tree()
        return {
            "success": True,
            "decision_tree": tree,
        }
    except Exception as exc:
        logger.error("Decision tree error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/finance/matrix/cost-benefit",
    summary="Option 4e: Cost-benefit analysis for specific transaction",
    tags=["Enhancements", "Financing"],
)
async def get_cost_benefit_analysis(
    country_code: str = Query(..., description="ISO2 code"),
    amount_usd: float = Query(..., description="Transaction value", ge=10000),
):
    """
    Analyze cost-benefit for each instrument in a specific transaction.

    Returns for each instrument:
    - Banking cost (commission %)
    - Insurance cost (if needed for gap coverage)
    - Total cost (combined)
    - Risk protection value (unmitigated risk × instrument protection)
    - Net benefit (protection value - total cost)
    - ROI (return on investment %)
    - Recommendation
    """
    try:
        analysis = FinancingMatrix.get_cost_benefit_analysis(country_code, amount_usd)
        return {
            "success": True,
            "transaction": analysis["transaction"],
            "country_risk": analysis["country_risk"],
            "analysis": analysis["analysis"],
            "summary": {
                "best_option": (
                    next(iter(analysis["analysis"].values()))["instrument"]
                    if analysis["analysis"]
                    else None
                ),
                "best_net_benefit": (
                    max(
                        (v["net_benefit_usd"] for v in analysis["analysis"].values()),
                        default=0,
                    )
                ),
            },
        }
    except Exception as exc:
        logger.error("Cost-benefit error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
