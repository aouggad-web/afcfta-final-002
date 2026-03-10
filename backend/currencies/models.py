"""
Currency data models for African currencies.
"""
from typing import Optional
from pydantic import BaseModel, Field


class CurrencyInfo(BaseModel):
    """Complete information about an African currency."""

    country_code: str = Field(..., description="ISO 3166-1 alpha-2 country code")
    country_name_en: str = Field(..., description="Country name in English")
    country_name_fr: str = Field(..., description="Country name in French")
    currency_code: str = Field(..., description="ISO 4217 currency code")
    currency_name_en: str = Field(..., description="Currency name in English")
    currency_name_fr: str = Field(..., description="Currency name in French")
    currency_symbol: str = Field(..., description="Currency symbol")
    subunit: str = Field(..., description="Name of the smallest currency subunit")
    subunit_factor: int = Field(..., description="Number of subunits per main unit")
    central_bank: str = Field(..., description="Name of the central bank")
    central_bank_website: Optional[str] = Field(None, description="Central bank website URL")
    convertible: bool = Field(..., description="Whether the currency is freely convertible")
    monetary_union: Optional[str] = Field(
        None, description="Regional monetary union (e.g. UEMOA, CEMAC, CMA)"
    )
    forex_regulation: str = Field(
        default="moderate",
        description="Forex regulation level: strict | moderate | liberal",
    )
