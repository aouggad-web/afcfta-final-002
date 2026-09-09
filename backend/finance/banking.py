"""
Finance.banking – banking sub-module.

Re-exports the banking-related surface of ``banking_system``: banks
registry, forex regulations, trade finance instruments, payment systems,
regulatory compliance, country risk assessment, intelligent
recommendations, bank scoring, FX hedging, and the financing matrix.

Insurance lives in :mod:`finance.insurance`, not here.
"""

from banking_system import (
    CENTRAL_BANKS,
    FOREX_PROFILES,
    BankScorer,
    assess_transaction_risk,
    check_compliance,
    get_all_currency_meta,
    get_bank_suitability_score,
    get_banks_register,
    get_central_bank,
    get_country_banks,
    get_country_compliance,
    get_country_risk,
    get_currency_meta,
    get_domiciliation_rules,
    get_export_formalities,
    get_forex_profile,
    get_import_formalities,
    get_payment_systems,
    get_regional_banks,
    get_regional_systems,
    get_trade_finance_instruments,
    get_trade_recommendations,
    recommend_instruments,
    score_banks_for_transaction,
)
from banking_system.financing_matrix import FinancingMatrix
from banking_system.forex_hedging import (
    get_hedging_cost_comparison,
    recommend_hedging_strategy,
)

__all__ = [
    # Banks registry
    "get_central_bank",
    "get_country_banks",
    "get_regional_banks",
    "get_banks_register",
    "CENTRAL_BANKS",
    # Bank scoring
    "BankScorer",
    "score_banks_for_transaction",
    "get_bank_suitability_score",
    # Intelligent recommendations
    "get_trade_recommendations",
    # Forex / domiciliation
    "get_forex_profile",
    "get_domiciliation_rules",
    "get_import_formalities",
    "get_export_formalities",
    "get_currency_meta",
    "get_all_currency_meta",
    "FOREX_PROFILES",
    # FX hedging
    "recommend_hedging_strategy",
    "get_hedging_cost_comparison",
    # Trade finance
    "get_trade_finance_instruments",
    "recommend_instruments",
    # Financing matrix
    "FinancingMatrix",
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
