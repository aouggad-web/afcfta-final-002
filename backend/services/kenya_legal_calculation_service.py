"""Bridge the public calculator to the dated EAC/Kenya legal-override engine."""

from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional

from engine.kenya_customs_calculation import KenyaFiscalStore, calculate_kenya_customs
from engine.legal_override_engine import load_legal_measures
from engine.schemas.legal_override import OverrideContext, RemissionEligibility

_ROOT = Path(__file__).resolve().parents[2]
_EAC_DATA = _ROOT / "data" / "eac"
_KENYA_DATA = _ROOT / "data" / "kenya"


@lru_cache(maxsize=1)
def _resources():
    measures = load_legal_measures(_EAC_DATA / "legal_overrides.json")
    register = json.loads((_EAC_DATA / "eac_gazette_register.json").read_text(encoding="utf-8"))
    store = KenyaFiscalStore(_KENYA_DATA)
    return measures, store, bool(register.get("coverage_complete", False))


def calculate_kenya_legal_layer(
    *,
    hs_code: str,
    on_date: date,
    customs_value: float,
    base_cet_rate: float,
    origin: Optional[str] = None,
    remission_eligibility: RemissionEligibility = RemissionEligibility.ELIGIBILITY_UNKNOWN,
    authorization_reference: Optional[str] = None,
    authorization_effective_from: Optional[date] = None,
    authorization_effective_to: Optional[date] = None,
    authorization_hs_codes: Optional[Iterable[str]] = None,
    authorization_goods: Optional[Iterable[str]] = None,
    beneficiary: Optional[str] = None,
    import_purpose: Optional[str] = None,
    quantity: Optional[float] = None,
    currency_code: str = "USD",
) -> dict:
    measures, fiscal_store, coverage_complete = _resources()
    context = OverrideContext(
        jurisdiction="KEN",
        origin=origin,
        beneficiary=beneficiary,
        import_purpose=import_purpose,
        quantity=quantity,
        remission_eligibility=remission_eligibility,
        authorization_reference=authorization_reference,
        authorization_effective_from=authorization_effective_from,
        authorization_effective_to=authorization_effective_to,
        authorization_hs_codes=list(authorization_hs_codes or []),
        authorization_goods=list(authorization_goods or []),
    )
    return calculate_kenya_customs(
        hs_code=hs_code,
        on_date=on_date,
        customs_value=customs_value,
        base_cet_rate=base_cet_rate,
        measures=measures,
        fiscal_store=fiscal_store,
        context=context,
        coverage_complete=coverage_complete,
        currency_code=currency_code,
    )
