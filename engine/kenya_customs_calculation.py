"""Compatibilité rétroactive — alias Kenya du moteur national générique.

Le calcul douanier Kenya a été généralisé dans
``engine.national_customs_calculation`` afin d'être réutilisable par
d'autres juridictions EAC (Tanzanie, Ouganda, Rwanda). Ce module ne fait
plus que ré-exporter les noms historiques pour ne pas casser les
appelants existants ; le comportement du Kenya (devise KES par défaut,
tables de prélèvements IDF/RDL) est préservé à l'identique.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable, Optional

from engine.national_customs_calculation import (
    NationalFiscalStore,
    _active,  # noqa: F401 — ré-exporté pour compatibilité
    _hs_match,  # noqa: F401 — ré-exporté pour compatibilité
    _pct,  # noqa: F401 — ré-exporté pour compatibilité
    calculate_national_customs,
)
from engine.schemas.legal_override import LegalOverrideMeasure, OverrideContext

# Alias historique.
KenyaFiscalStore = NationalFiscalStore


def calculate_kenya_customs(
    *,
    hs_code: str,
    on_date: date,
    customs_value: float,
    base_cet_rate: float,
    measures: Iterable[LegalOverrideMeasure],
    fiscal_store: NationalFiscalStore,
    context: Optional[OverrideContext] = None,
    coverage_complete: bool = False,
    currency_code: str = "KES",
) -> dict:
    return calculate_national_customs(
        jurisdiction="KEN",
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
