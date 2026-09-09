"""Compatibility helpers backed by the strict bilateral implementation registry.

Do not use this module to decide a calculation: destination-only status cannot
prove reciprocity. New code must call implementation_decision(destination,
origin) from zlecaf_implementation_registry.
"""

from __future__ import annotations

from services.zlecaf_implementation_registry import APPLIED, RECORDS

DEDICATED_MODULE = frozenset({"DZA", "ZAF"})
ACTIVE_IMPLEMENTERS = (
    frozenset(code for code, record in RECORDS.items() if record.status == APPLIED)
    | DEDICATED_MODULE
)


def is_active_implementer(iso3: str) -> bool:
    """Compatibility-only destination check; never proves a bilateral rate."""
    return (iso3 or "").upper() in ACTIVE_IMPLEMENTERS


def implementation_evidence(iso3: str) -> str:
    code = (iso3 or "").upper()
    if code in DEDICATED_MODULE:
        return "module bilatéral dédié"
    record = RECORDS.get(code)
    if record:
        return f"{record.instrument_id} — statut {record.status}"
    return "aucune preuve d'application réelle vérifiée"
