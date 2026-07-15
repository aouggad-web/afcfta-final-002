"""
African Banking System Module – ZLECAf

Provides data and logic for:
- Banks registry (central banks, commercial banks, regional banks)
- Foreign-exchange regulations and domiciliation rules
- Trade finance instruments
- Insurance products and pricing
- Regional payment systems
- Country risk assessment
- Insurance products and premium pricing (export credit, political risk)
"""

from .bank_scoring import (
    BankScorer,
    get_bank_suitability_score,
    score_banks_for_transaction,
)
from .banking_recommendations import get_trade_recommendations
from .banks_registry import (
    CENTRAL_BANKS,
    get_banks_register,
    get_central_bank,
    get_country_banks,
    get_regional_banks,
)
from .foreign_exchange import (
    FOREX_PROFILES,
    get_all_currency_meta,
    get_currency_meta,
    get_domiciliation_rules,
    get_export_formalities,
    get_forex_profile,
    get_import_formalities,
)
from .insurance_pricing import (
    batch_calculate_quotes,
    calculate_insurance_quote,
    get_premium_adjustments_for_country,
)
from .insurance_registry import (
<<<<<<< HEAD
    get_available_insurers,
    get_available_products,
    get_country_insurance_profile,
=======
    COUNTRY_INSURANCE_PROFILES,
    get_available_insurers,
    get_available_products,
    get_country_insurance_profile,
    get_insurance_registry,
>>>>>>> origin/main
)
from .payment_systems import get_payment_systems, get_regional_systems
from .regulatory_compliance import check_compliance, get_country_compliance
from .risk_assessment import assess_transaction_risk, get_country_risk
from .trade_finance import get_trade_finance_instruments, recommend_instruments

__all__ = [
    # Banks registry
    "get_central_bank",
    "get_country_banks",
    "get_regional_banks",
    "get_banks_register",
    "CENTRAL_BANKS",
    # Bank scoring (Option 2)
    "BankScorer",
    "score_banks_for_transaction",
    "get_bank_suitability_score",
    # Banking recommendations
    "get_trade_recommendations",
    # Forex / domiciliation
    "get_forex_profile",
    "get_domiciliation_rules",
    "get_import_formalities",
    "get_export_formalities",
    "get_currency_meta",
    "get_all_currency_meta",
    "FOREX_PROFILES",
    # Insurance
    "get_country_insurance_profile",
    "get_available_insurers",
    "get_available_products",
    "calculate_insurance_quote",
    "batch_calculate_quotes",
    "get_premium_adjustments_for_country",
    # Trade finance
    "get_trade_finance_instruments",
    "recommend_instruments",
    # Payment systems
    "get_payment_systems",
    "get_regional_systems",
    # Regulatory compliance
    "get_country_compliance",
    "check_compliance",
    # Risk assessment
    "get_country_risk",
    "assess_transaction_risk",
    # Insurance (NEW)
    "get_country_insurance_profile",
    "get_available_insurers",
    "get_available_products",
    "get_insurance_registry",
    "COUNTRY_INSURANCE_PROFILES",
    "calculate_insurance_quote",
    "get_premium_adjustments_for_country",
    "batch_calculate_quotes",
]
