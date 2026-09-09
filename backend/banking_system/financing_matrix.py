"""
Financing instrument matrix for AfCFTA trade operations.

Provides comparative analysis and selection matrix for:
- Trade finance instruments (LC, D/C, etc.)
- Risk levels (A1 to D)
- Transaction sizes
- Cost vs protection trade-offs
"""

from typing import Dict, List

from .risk_assessment import RISK_PROFILES
from .trade_finance import TRADE_FINANCE_INSTRUMENTS


class FinancingMatrix:
    """Comprehensive instrument matrix for trade finance decisions"""

    @staticmethod
    def get_instrument_comparison(country_code: str = None) -> Dict:
        """
        Get detailed comparison of all trade finance instruments.

        Includes: cost, protection, speed, documentation, suitability.
        """
        instruments_data = []

        for instrument in TRADE_FINANCE_INSTRUMENTS:
            instruments_data.append(
                {
                    "code": instrument.code,
                    "name": instrument.name,
                    "name_fr": instrument.name_fr,
                    "description": instrument.description,
                    "applicable_to": instrument.applicable_to,
                    "cost": {
                        "typical_pct": instrument.typical_cost_pct,
                        "rating": FinancingMatrix._cost_rating(instrument.typical_cost_pct),
                    },
                    "protection": {
                        "coverage": instrument.risk_coverage,
                        "rating": FinancingMatrix._protection_rating(instrument.risk_coverage),
                    },
                    "speed": {
                        "typical_days": instrument.typical_duration_days,
                        "rating": FinancingMatrix._speed_rating(instrument.typical_duration_days),
                    },
                    "requirements": instrument.requirements,
                    "suitability_score": FinancingMatrix._calculate_suitability(instrument),
                }
            )

        return {
            "total_instruments": len(instruments_data),
            "instruments": instruments_data,
        }

    @staticmethod
    def get_risk_based_matrix() -> Dict:
        """
        Get instrument recommendations by country risk rating.

        Shows which instruments work best for each risk level.
        """
        matrix = {}

        for risk_code in ["A1", "A2", "A3", "A4", "B", "C", "D"]:
            # Get example countries for this risk level
            example_countries = [
                code
                for code, profile in RISK_PROFILES.items()
                if profile.country_risk_rating == risk_code
            ][:2]

            # Map recommended instruments
            recommended = []
            if risk_code in ["A1", "A2", "A3", "A4"]:
                recommended = ["DOC_COLLECTION_DP", "LC_IRREVOCABLE"]
            elif risk_code == "B":
                recommended = ["LC_IRREVOCABLE", "DOC_COLLECTION_DP", "LC_CONFIRMED"]
            elif risk_code == "C":
                recommended = ["LC_CONFIRMED", "BANK_GUARANTEE_ADVANCE"]
            else:  # D
                recommended = ["LC_CONFIRMED", "STANDBY_LC"]

            # Get full instrument data
            instruments_list = []
            for code in recommended:
                instr = next((i for i in TRADE_FINANCE_INSTRUMENTS if i.code == code), None)
                if instr:
                    instruments_list.append(
                        {
                            "code": instr.code,
                            "name": instr.name,
                            "cost_pct": instr.typical_cost_pct,
                            "protection": instr.risk_coverage,
                            "duration_days": instr.typical_duration_days,
                        }
                    )

            matrix[risk_code] = {
                "risk_level": risk_code,
                "description": FinancingMatrix._risk_description(risk_code),
                "example_countries": example_countries,
                "recommended_instruments": instruments_list,
                "key_considerations": FinancingMatrix._risk_considerations(risk_code),
            }

        return matrix

    @staticmethod
    def get_transaction_size_matrix() -> Dict:
        """
        Get recommended instruments by transaction size.

        Shows cost-effectiveness for different amounts.
        """
        size_brackets = [
            {"name": "Micro", "min": 0, "max": 50_000},
            {"name": "Small", "min": 50_000, "max": 250_000},
            {"name": "Medium", "min": 250_000, "max": 1_000_000},
            {"name": "Large", "min": 1_000_000, "max": 5_000_000},
            {"name": "Mega", "min": 5_000_000, "max": float("inf")},
        ]

        matrix = {}
        for bracket in size_brackets:
            matrix[bracket["name"]] = {
                "size_range_usd": (
                    f"${bracket['min']:,} - ${bracket['max']:,}"
                    if bracket["max"] != float("inf")
                    else f"${bracket['min']:,}+"
                ),
                "recommended_instruments": FinancingMatrix._instruments_for_size(
                    bracket["min"], bracket["max"]
                ),
                "typical_cost_range_pct": FinancingMatrix._cost_range_for_size(bracket["min"]),
                "key_factors": FinancingMatrix._size_factors(bracket["min"], bracket["max"]),
            }

        return matrix

    @staticmethod
    def get_quick_decision_tree() -> Dict:
        """
        Interactive decision tree for instrument selection.

        Follow yes/no questions to find optimal instrument.
        """
        return {
            "start": {
                "question": "Is this an export or import?",
                "options": {"export": "export_path", "import": "import_path"},
            },
            "export_path": {
                "question": "What is the country risk level?",
                "options": {
                    "low_risk": "export_low_risk",
                    "moderate_risk": "export_moderate_risk",
                    "high_risk": "export_high_risk",
                },
            },
            "export_low_risk": {
                "question": "Do you trust your buyer?",
                "options": {
                    "yes": "recommendation_doc_collection",
                    "no": "recommendation_lc_irrevocable",
                },
            },
            "export_moderate_risk": {
                "recommendation": "LC_IRREVOCABLE",
                "reason": "Moderate risk requires documentary credit.",
            },
            "export_high_risk": {
                "recommendation": "LC_CONFIRMED",
                "reason": "High risk requires confirmed credit with international bank.",
            },
            "import_path": {
                "question": "Are you providing advance payment?",
                "options": {
                    "yes": "recommendation_doc_collection",
                    "no": "recommendation_lc_irrevocable",
                },
            },
            "recommendation_doc_collection": {
                "recommendation": "DOC_COLLECTION_DP",
                "reason": "Cost-effective for trusted partners.",
            },
            "recommendation_lc_irrevocable": {
                "recommendation": "LC_IRREVOCABLE",
                "reason": "Secure payment protection for both parties.",
            },
        }

    @staticmethod
    def get_cost_benefit_analysis(country_code: str, amount_usd: float) -> Dict:
        """
        Cost-benefit analysis of different instruments for specific transaction.

        Shows total cost including premiums, insurance, and risk.
        """
        risk_profile = next(
            (p for p in RISK_PROFILES.values() if p.country_code == country_code.upper()), None
        )

        if not risk_profile:
            return {"error": f"Country {country_code} not found"}

        analysis = {}

        for instrument in TRADE_FINANCE_INSTRUMENTS:
            if "export" not in instrument.applicable_to:
                continue

            # Calculate cost
            banking_cost = amount_usd * (instrument.typical_cost_pct / 100.0)

            # Estimate insurance cost (if not fully covered)
            if instrument.risk_coverage != "full":
                insurance_cost = amount_usd * 0.015  # ~1.5% for gap coverage
            else:
                insurance_cost = 0

            total_cost = banking_cost + insurance_cost

            # Value of protection (reduced by risk)
            risk_level = risk_profile.country_risk_rating
            risk_values = {
                "A1": 0.005,  # 0.5% unmitigated risk
                "A2": 0.01,
                "A3": 0.02,
                "A4": 0.03,
                "B": 0.07,
                "C": 0.15,
                "D": 0.30,
            }
            unmitigated_risk_value = amount_usd * risk_values.get(risk_level, 0.07)

            # Risk reduction provided by instrument
            if instrument.risk_coverage == "full":
                risk_reduction = 0.95  # 95% protection
            elif instrument.risk_coverage == "partial":
                risk_reduction = 0.60  # 60% protection
            else:
                risk_reduction = 0  # No protection

            risk_value_saved = unmitigated_risk_value * risk_reduction
            net_benefit = risk_value_saved - total_cost

            analysis[instrument.code] = {
                "instrument": instrument.name,
                "banking_cost_usd": round(banking_cost, 2),
                "banking_cost_pct": instrument.typical_cost_pct,
                "insurance_cost_usd": round(insurance_cost, 2),
                "total_cost_usd": round(total_cost, 2),
                "total_cost_pct": round((total_cost / amount_usd) * 100, 2),
                "risk_protection_value_usd": round(risk_value_saved, 2),
                "net_benefit_usd": round(net_benefit, 2),
                "net_benefit_pct": round((net_benefit / amount_usd) * 100, 2),
                "roi_pct": round(
                    (risk_value_saved / total_cost - 1) * 100 if total_cost > 0 else 0, 1
                ),
                "recommendation": "Recommended" if net_benefit > 0 else "Consider alternatives",
            }

        # Sort by net benefit
        sorted_analysis = dict(
            sorted(analysis.items(), key=lambda x: x[1]["net_benefit_usd"], reverse=True)
        )

        return {
            "transaction": {"country_code": country_code, "amount_usd": amount_usd},
            "country_risk": risk_level,
            "analysis": sorted_analysis,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # HELPER METHODS
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _cost_rating(cost_pct: float) -> str:
        if cost_pct < 0.5:
            return "Very Low"
        elif cost_pct < 1.0:
            return "Low"
        elif cost_pct < 2.0:
            return "Moderate"
        elif cost_pct < 3.0:
            return "High"
        else:
            return "Very High"

    @staticmethod
    def _protection_rating(coverage: str) -> str:
        if coverage == "full":
            return "Full Protection"
        elif coverage == "partial":
            return "Partial Protection"
        else:
            return "Limited Protection"

    @staticmethod
    def _speed_rating(days: int) -> str:
        if days <= 30:
            return "Fast"
        elif days <= 90:
            return "Moderate"
        else:
            return "Slow"

    @staticmethod
    def _calculate_suitability(instrument) -> float:
        score = 5.0
        if instrument.risk_coverage == "full":
            score += 3
        elif instrument.risk_coverage == "partial":
            score += 1
        if instrument.typical_cost_pct < 1.5:
            score += 1
        if instrument.typical_duration_days <= 90:
            score += 1
        return min(score, 10.0)

    @staticmethod
    def _risk_description(risk_code: str) -> str:
        descriptions = {
            "A1": "Very Low Risk – Highly developed economy",
            "A2": "Low Risk – Stable country",
            "A3": "Satisfactory Risk – Moderate stability",
            "A4": "Acceptable Risk – Some concerns",
            "B": "Uncertain Risk – Significant concerns",
            "C": "High Risk – Major challenges",
            "D": "Very High Risk – Extreme caution required",
        }
        return descriptions.get(risk_code, "Unknown")

    @staticmethod
    def _risk_considerations(risk_code: str) -> List[str]:
        considerations = {
            "A1": ["Minimal insurance needed", "Flexible payment terms acceptable"],
            "A2": [
                "Standard instruments sufficient",
                "Shorter credit terms preferred",
            ],
            "A3": [
                "Documentary credit recommended",
                "Verified buyer information essential",
            ],
            "A4": [
                "Confirmed credit preferred",
                "Strict compliance monitoring required",
            ],
            "B": [
                "Confirmed credit strongly recommended",
                "Insurance coverage advised",
                "Enhanced due diligence required",
            ],
            "C": [
                "Confirmed credit mandatory",
                "Export credit insurance required",
                "Minimal payment terms offered",
            ],
            "D": [
                "Cash in advance preferred",
                "Maximum insurance coverage essential",
                "Avoid extended credit terms",
            ],
        }
        return considerations.get(risk_code, [])

    @staticmethod
    def _instruments_for_size(min_usd: float, max_usd: float) -> List[str]:
        if max_usd <= 50_000:
            return ["DOC_COLLECTION_DP", "LC_IRREVOCABLE"]
        elif max_usd <= 250_000:
            return ["DOC_COLLECTION_DP", "LC_IRREVOCABLE", "EXPORT_FACTORING"]
        elif max_usd <= 1_000_000:
            return ["LC_IRREVOCABLE", "LC_CONFIRMED", "EXPORT_FACTORING"]
        else:
            return ["LC_CONFIRMED", "STANDBY_LC", "SUPPLY_CHAIN_FINANCE"]

    @staticmethod
    def _cost_range_for_size(min_usd: float) -> str:
        if min_usd < 50_000:
            return "0.5% - 2.5%"
        elif min_usd < 250_000:
            return "0.5% - 2.0%"
        elif min_usd < 1_000_000:
            return "1.0% - 2.5%"
        else:
            return "0.75% - 2.0%"

    @staticmethod
    def _size_factors(min_usd: float, max_usd: float) -> List[str]:
        factors = []
        if min_usd < 50_000:
            factors.append("Minimum premiums apply")
            factors.append("Fixed costs significant relative to transaction")
        if min_usd > 1_000_000:
            factors.append("Volume discounts available")
            factors.append("Liquidity and bank capacity important")
        if max_usd > 5_000_000:
            factors.append("Syndication may be required")
            factors.append("Complex documentation needed")
        return factors
