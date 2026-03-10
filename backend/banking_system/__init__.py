"""
African Banking System Module – ZLECAf

Provides data and logic for:
- Banks registry (central banks, commercial banks, regional banks)
- Foreign-exchange regulations and domiciliation rules
- Trade finance instruments
- Regional payment systems
- Country risk assessment
"""

from .banks_registry import get_central_bank, get_country_banks, get_regional_banks, CENTRAL_BANKS
from .foreign_exchange import get_forex_profile, get_domiciliation_rules, FOREX_PROFILES
from .trade_finance import get_trade_finance_instruments, recommend_instruments
from .payment_systems import get_payment_systems, get_regional_systems
from .regulatory_compliance import get_country_compliance, check_compliance
from .risk_assessment import get_country_risk, assess_transaction_risk

__all__ = [
    # Banks registry
    "get_central_bank",
    "get_country_banks",
    "get_regional_banks",
    "CENTRAL_BANKS",
    # Forex / domiciliation
    "get_forex_profile",
    "get_domiciliation_rules",
    "FOREX_PROFILES",
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
]
