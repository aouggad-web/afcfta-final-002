"""
Exchange rate data models.
"""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ExchangeRate(BaseModel):
    """A single exchange rate snapshot."""

    base_currency: str = Field(..., description="Base ISO 4217 currency code")
    target_currency: str = Field(..., description="Target ISO 4217 currency code")
    rate: float = Field(..., description="Exchange rate: 1 base = rate target")
    timestamp: datetime = Field(..., description="UTC timestamp of the rate")
    source: str = Field(..., description="Data provider name")


class RateBundle(BaseModel):
    """A set of rates for a given base currency at a point in time."""

    base: str = Field(..., description="Base ISO 4217 currency code")
    timestamp: datetime
    source: str
    rates: Dict[str, float] = Field(default_factory=dict)


class ConversionResult(BaseModel):
    """Result of a currency conversion request."""

    from_currency: str
    to_currency: str
    amount: float
    converted_amount: float
    rate: float
    timestamp: datetime
    source: str


class RateAlert(BaseModel):
    """Rate change alert."""

    currency_pair: str = Field(..., description="E.g. 'USD/NGN'")
    previous_rate: float
    current_rate: float
    change_percent: float
    direction: str = Field(..., description="'up' or 'down'")
    timestamp: datetime


class ConversionRequest(BaseModel):
    """Request body for POST /api/exchange-rates/convert."""

    from_currency: str = Field(..., description="Source ISO 4217 currency code")
    to_currency: str = Field(..., description="Target ISO 4217 currency code")
    amount: float = Field(..., gt=0, description="Amount to convert (must be > 0)")
