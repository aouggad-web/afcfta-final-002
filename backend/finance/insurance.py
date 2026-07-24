"""
Finance.insurance – insurance sub-module.

Re-exports the insurance surface of ``banking_system``: country
insurance profiles, the insurer directory, and premium pricing (export
credit, political risk, performance guarantee, etc.), all linked to the
same country risk assessment used by :mod:`finance.banking`.
"""

from banking_system import (
    COUNTRY_INSURANCE_PROFILES,
    batch_calculate_quotes,
    calculate_insurance_quote,
    get_available_insurers,
    get_available_products,
    get_country_insurance_profile,
    get_insurance_registry,
    get_premium_adjustments_for_country,
)
from banking_system.insurance_registry import MAJOR_INSURERS

__all__ = [
    "get_country_insurance_profile",
    "get_available_insurers",
    "get_available_products",
    "get_insurance_registry",
    "COUNTRY_INSURANCE_PROFILES",
    "MAJOR_INSURERS",
    "calculate_insurance_quote",
    "batch_calculate_quotes",
    "get_premium_adjustments_for_country",
]
