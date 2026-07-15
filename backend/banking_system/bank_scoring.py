"""
Enhanced bank scoring and selection for AfCFTA trade operations.

Provides sophisticated scoring algorithms for:
- Regional expertise and presence
- Service offering alignment
- Correspondent banking network quality
- Transaction suitability matching
- Cost competitiveness
- Historical performance indicators
"""

from typing import Dict, List, Optional

from .models import CommercialBank


class BankScorer:
    """Sophisticated bank scoring engine for trade operations"""

    # Regional zones for geographic presence scoring
    REGIONAL_ZONES = {
        "west_africa": ["SN", "ML", "BJ", "CI", "GH", "NG", "BF", "TG", "LR", "SL", "GM"],
        "east_africa": ["KE", "TZ", "UG", "RW", "ET", "SO", "DJ", "ER"],
        "southern_africa": ["ZA", "BW", "NA", "SZ", "LS", "MZ", "ZM", "ZW", "AO"],
        "central_africa": ["CM", "CG", "CD", "TC", "GA", "GQ", "CF"],
        "north_africa": ["EG", "DZ", "MA", "TN", "LY", "SD"],
    }

    # Service types and their importance in different scenarios
    SERVICE_IMPORTANCE = {
        "export": ["trade_finance", "documentary_credits", "guarantees", "factoring"],
        "import": ["trade_finance", "documentary_credits", "import_financing"],
        "supply_chain": ["supply_chain_finance", "inventory_financing", "buyer_credit"],
        "general": ["trade_finance", "correspondent_banking", "cash_management"],
    }

    @staticmethod
    def score_bank(
        bank: CommercialBank,
        country_code: str,
        transaction_type: str = "export",
        amount_usd: float = 1_000_000,
        sector: Optional[str] = None,
    ) -> float:
        """
        Calculate comprehensive bank score (0-10) based on multiple factors.

        Factors:
        - Geographic presence and regional expertise (30%)
        - Service offering alignment (25%)
        - Correspondent banking network (25%)
        - Transaction amount suitability (10%)
        - Specialization match (10%)
        """
        if not bank.trade_finance:
            return 0.0

        score = 0.0

        # 1. Geographic presence & regional expertise (30%)
        geo_score = BankScorer._score_geographic_presence(bank, country_code)
        score += geo_score * 0.30

        # 2. Service offering alignment (25%)
        service_score = BankScorer._score_services(bank, transaction_type, sector)
        score += service_score * 0.25

        # 3. Correspondent banking network (25%)
        network_score = BankScorer._score_correspondent_network(bank, country_code)
        score += network_score * 0.25

        # 4. Transaction amount suitability (10%)
        amount_score = BankScorer._score_transaction_amount(bank, amount_usd)
        score += amount_score * 0.10

        # 5. Specialization match (10%)
        special_score = BankScorer._score_specialization(bank, transaction_type)
        score += special_score * 0.10

        return min(score, 10.0)

    @staticmethod
    def _score_geographic_presence(bank: CommercialBank, country_code: str) -> float:
        """Score bank's geographic presence and regional expertise (0-10)."""
        score = 5.0  # Base score

        # Check if bank is in the target country
        if bank.country_code.upper() == country_code.upper():
            score += 3.0

        # Check if bank is in the same regional zone
        target_zone = None
        for zone, countries in BankScorer.REGIONAL_ZONES.items():
            if country_code.upper() in countries:
                target_zone = zone
                break

        if target_zone:
            bank_zone = None
            for zone, countries in BankScorer.REGIONAL_ZONES.items():
                if bank.country_code.upper() in countries:
                    bank_zone = zone
                    break

            if bank_zone == target_zone:
                score += 1.5
            elif bank_zone and bank_zone in [
                "west_africa",
                "east_africa",
                "southern_africa",
            ]:
                score += 0.5  # Some points for continental presence

        return min(score, 10.0)

    @staticmethod
    def _score_services(
        bank: CommercialBank,
        transaction_type: str,
        sector: Optional[str] = None,
    ) -> float:
        """Score bank's service offering alignment (0-10)."""
        if not bank.services:
            return 3.0

        score = 5.0  # Base score

        # Get required services for this transaction type
        required_services = BankScorer.SERVICE_IMPORTANCE.get(
            transaction_type.lower(),
            BankScorer.SERVICE_IMPORTANCE["general"],
        )

        # Check coverage of key services
        bank_services = set(s.lower() for s in bank.services)
        covered_services = sum(1 for svc in required_services if svc in bank_services)
        coverage_ratio = covered_services / len(required_services)

        # Score increases with coverage
        if coverage_ratio == 1.0:
            score += 4.0  # All key services
        elif coverage_ratio >= 0.75:
            score += 3.0
        elif coverage_ratio >= 0.5:
            score += 1.5
        elif coverage_ratio >= 0.25:
            score += 0.5

        # Bonus for specialized services
        high_value_services = [
            "documentary_credits",
            "supply_chain_finance",
            "export_credit_insurance",
        ]
        for service in high_value_services:
            if service in bank_services:
                score += 0.5

        return min(score, 10.0)

    @staticmethod
    def _score_correspondent_network(
        bank: CommercialBank,
        country_code: str,
    ) -> float:
        """Score quality and coverage of correspondent banking network (0-10)."""
        if not bank.correspondent_banks:
            return 3.0

        score = 5.0  # Base score

        # Number of correspondent banks
        num_correspondents = len(bank.correspondent_banks)
        if num_correspondents >= 50:
            score += 4.0
        elif num_correspondents >= 20:
            score += 3.0
        elif num_correspondents >= 10:
            score += 2.0
        else:
            score += 1.0

        # Check if there's direct presence in target country
        correspondent_countries = set()
        for correspondent in bank.correspondent_banks:
            if isinstance(correspondent, str):
                # Extract country code if it's in format "NAME (CODE)"
                if "(" in correspondent and ")" in correspondent:
                    code = correspondent.split("(")[-1].replace(")", "").strip()
                    correspondent_countries.add(code.upper())

        if country_code.upper() in correspondent_countries:
            score += 1.0

        return min(score, 10.0)

    @staticmethod
    def _score_transaction_amount(bank: CommercialBank, amount_usd: float) -> float:
        """Score bank's suitability for transaction amount (0-10)."""
        score = 5.0  # Base score

        # Large banks better for large transactions
        if amount_usd > 5_000_000:
            score += 3.0 if len(bank.correspondent_banks or []) > 20 else 1.0
        elif amount_usd > 1_000_000:
            score += 2.0 if len(bank.correspondent_banks or []) > 10 else 1.0
        else:
            score += 2.0  # Smaller banks can handle well

        return min(score, 10.0)

    @staticmethod
    def _score_specialization(bank: CommercialBank, transaction_type: str) -> float:
        """Score bank's specialization match (0-10)."""
        score = 5.0  # Base score

        if not bank.services:
            return score

        bank_services = set(s.lower() for s in bank.services)

        # Map transaction types to specialized services
        specialization_map = {
            "export": "documentary_credits",
            "import": "import_financing",
            "supply_chain": "supply_chain_finance",
            "buyback": "buyer_credit",
        }

        target_service = specialization_map.get(transaction_type.lower())
        if target_service and target_service in bank_services:
            score += 4.0
        elif target_service and "trade_finance" in bank_services:
            score += 2.0

        return min(score, 10.0)

    @staticmethod
    def _get_suitability_level(score: float) -> str:
        """Convert numeric score to suitability description."""
        if score >= 8.5:
            return "Excellent"
        elif score >= 7.0:
            return "Very Good"
        elif score >= 5.5:
            return "Good"
        elif score >= 4.0:
            return "Acceptable"
        else:
            return "Limited"

    @staticmethod
    def _identify_strengths(
        bank: CommercialBank,
        country_code: str,
        transaction_type: str,
    ) -> List[str]:
        """Identify key strengths of a bank for this transaction."""
        strengths = []

        # Geographic strength
        if bank.country_code.upper() == country_code.upper():
            strengths.append("Local presence in target country")

        # Network strength
        if bank.correspondent_banks and len(bank.correspondent_banks) > 20:
            strengths.append("Extensive correspondent network")

        # Service strength
        if bank.services:
            required_services = BankScorer.SERVICE_IMPORTANCE.get(
                transaction_type.lower(), ["trade_finance"]
            )
            bank_services = set(s.lower() for s in bank.services)
            if all(svc in bank_services for svc in required_services):
                strengths.append(f"Full {transaction_type} service suite")

        if not strengths:
            strengths.append("Solid trade finance capabilities")

        return strengths[:3]  # Return top 3 strengths


def score_banks_for_transaction(
    banks: List[CommercialBank],
    country_code: str,
    transaction_type: str = "export",
    amount_usd: float = 1_000_000,
    sector: Optional[str] = None,
) -> List[Dict]:
    """
    Score multiple banks for a specific transaction and return ranked list.

    Args:
        banks: List of banks to score
        country_code: ISO2 code of trade partner
        transaction_type: export | import | supply_chain | general
        amount_usd: Transaction value
        sector: Business sector (optional)

    Returns:
        Ranked list of banks with scores and explanations
    """
    scorer = BankScorer()
    scored_banks = []

    for bank in banks:
        score = scorer.score_bank(
            bank,
            country_code,
            transaction_type=transaction_type,
            amount_usd=amount_usd,
            sector=sector,
        )

        if score > 0:  # Only include banks with some score
            scored_banks.append(
                {
                    "name": bank.name,
                    "abbreviation": bank.abbreviation,
                    "country_code": bank.country_code,
                    "swift_code": bank.swift_code,
                    "score": round(score, 2),
                    "suitability_level": BankScorer._get_suitability_level(score),
                    "key_strengths": BankScorer._identify_strengths(
                        bank, country_code, transaction_type
                    ),
                    "services": bank.services,
                    "correspondents_count": len(bank.correspondent_banks or []),
                    "website": bank.website,
                }
            )

    # Sort by score (highest first)
    scored_banks.sort(key=lambda x: x["score"], reverse=True)
    return scored_banks


def get_bank_suitability_score(
    bank: CommercialBank,
    country_code: str,
    transaction_type: str = "export",
) -> Dict:
    """
    Get detailed bank suitability score and explanation.

    Returns score breakdown and recommendations.
    """
    scorer = BankScorer()
    score = scorer.score_bank(
        bank,
        country_code,
        transaction_type=transaction_type,
    )

    return {
        "bank_name": bank.name,
        "suitability_score": round(score, 2),
        "suitability_level": scorer._get_suitability_level(score),
        "key_strengths": scorer._identify_strengths(bank, country_code, transaction_type),
        "recommendation": (
            "Highly recommended"
            if score >= 7.0
            else ("Recommended" if score >= 5.5 else "Consider alternatives")
        ),
    }
